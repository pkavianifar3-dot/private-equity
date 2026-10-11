"""Verified public bundles. Archival/rehearsal never grants deployment permission."""
import argparse
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import tarfile
from urllib.request import Request, build_opener, HTTPRedirectHandler
import zipfile

import site_release as site
import emergency_release as emergency

REPOSITORY = 'pkavianifar3-dot/private-equity'
WORKFLOW = '.github/workflows/validate-atlas.yml'
MAX_BYTES = 256 * 1024 * 1024
HEX = re.compile(r'^[0-9a-f]{40}$')


def require(value, message):
    if not value:
        raise ValueError(message)


def workflow_hash(root):
    return sha256((root / WORKFLOW).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def artifact_name(sha, run, attempt, kind='public'):
    require(kind in ('public', 'emergency'), 'Unknown bundle kind')
    return f'{kind}-recovery-{sha}-{run}-{attempt}'


def publication(root, output, current_root=None, kind='public'):
    require(kind in ('public', 'emergency'), 'Unknown bundle kind')
    if kind == 'emergency':
        return emergency.check(root, output)
    result = site.check_artifact(root, output, public=True)
    blockers = site.publication_blockers(root, output)
    if current_root is not None:
        # Historical approval cannot restore an Entity/Research revoked today.
        blockers += site.publication_blockers(current_root, output)
        now_entities = {e['id'] for e in site.read_json(current_root / 'atlas/entities/index.json')['entities']
                        if e.get('lifecycleStatus') == 'PUBLISHED' and e.get('type') in site.ROUTES}
        old_entities = {e['id'] for e in site.read_json(output / 'atlas/entities/index.json')['entities']}
        if not old_entities <= now_entities:
            blockers.append('Historical package contains Entities no longer public')
        _, approved_claims, _, approved_sources, _ = site.public_projection.snapshot(current_root)
        old_claims, _ = site.public_projection.records(output, 'claims')
        old_sources, _ = site.public_projection.records(output, 'sources')
        if not old_claims.keys() <= approved_claims.keys() or not old_sources.keys() <= approved_sources.keys():
            blockers.append('Historical Claim/Source approval is no longer current')
        allowed_articles = {site.url_file(r['url']) for r in site.articles(current_root)}
        for path in output.glob('articles/*.html'):
            if path.relative_to(output).as_posix() not in allowed_articles:
                blockers.append('Historical Research page no longer public: ' + path.name)
    require(not blockers, 'PUBLICATION BLOCKED: ' + '; '.join(blockers))
    return result


def create(root, output, bundle, report_path=None, kind='public'):
    require(not bundle.exists(), 'Bundle destination already exists')
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    if kind == 'emergency':
        require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip(),
                'Emergency bundle requires a clean source checkout')
        emergency.build(root, output)
        report = dict(commit=sha, working_tree_dirty=False,
                      files=site.digest_files(output, sorted(emergency.FILES)))
    else:
        report = site.read_json(report_path)
    require(report.get('commit') == sha and HEX.fullmatch(sha), 'Build SHA mismatch')
    require(not report.get('working_tree_dirty'), 'Dirty-source reports cannot become recovery bundles')
    result = publication(root, output, kind=kind)
    paths = sorted(emergency.FILES) if kind == 'emergency' else site.package_paths(root, public=True)
    files = site.digest_files(output, paths)
    require(files == report.get('files'), 'Build manifest/file hash mismatch')
    run = os.environ.get('GITHUB_RUN_ID', '')
    attempt = os.environ.get('GITHUB_RUN_ATTEMPT', '')
    require(run.isdecimal() and attempt.isdecimal(), 'CI run identity required')
    require(os.environ.get('GITHUB_REPOSITORY') == REPOSITORY, 'Repository mismatch')
    require(os.environ.get('GITHUB_SHA') == sha, 'CI SHA mismatch')
    bundle.mkdir(parents=True)
    with zipfile.ZipFile(bundle / 'site.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            archive.writestr(info, site.safe_file(output, name).read_bytes())
    manifest = dict(version=1, kind=kind, repository=REPOSITORY, workflow=WORKFLOW,
                    workflow_sha256=workflow_hash(root), sha=sha, run_id=int(run), run_attempt=int(attempt),
                    ref=os.environ.get('GITHUB_REF'), event=os.environ.get('GITHUB_EVENT_NAME'),
                    artifact_name=artifact_name(sha, run, attempt, kind), retention_days=30,
                    publication='passed', file_count=len(files), files=files, checks=result,
                    archive_sha256=sha256((bundle / 'site.zip').read_bytes()).hexdigest(),
                    created_at=datetime.now(timezone.utc).isoformat())
    (bundle / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def safe_names(archive):
    infos = archive.infolist()
    names = [i.filename for i in infos]
    require(len(names) == len(set(names)), 'Duplicate archive members')
    require(sum(i.file_size for i in infos) <= MAX_BYTES, 'Archive exceeds recovery size limit')
    for info in infos:
        name = info.filename
        require(name and not info.is_dir() and '\\' not in name and ':' not in name
                and not name.startswith('/') and all(p and p not in ('..', '.') and p.rstrip(' .') == p
                    and p.split('.')[0].upper() not in ('CON', 'PRN', 'AUX', 'NUL', *[f'COM{i}' for i in range(1, 10)],
                                                      *[f'LPT{i}' for i in range(1, 10)]) for p in name.split('/'))
                and not (info.flag_bits & 1), 'Unsafe archive path/member: ' + name)
        mode = info.external_attr >> 16
        require(not mode or stat.S_IFMT(mode) in (0, stat.S_IFREG), 'Archive links/special files forbidden')
    return names


def manifest(bundle):
    require({p.name for p in bundle.iterdir()} == {'site.zip', 'manifest.json'}, 'Missing/extra bundle files')
    require(not any(p.is_symlink() for p in bundle.iterdir()), 'Bundle symlink forbidden')
    require((bundle / 'manifest.json').stat().st_size <= 2 * 1024 * 1024, 'Manifest too large')
    require((bundle / 'site.zip').stat().st_size <= MAX_BYTES, 'Bundle archive too large')
    m = site.read_json(bundle / 'manifest.json')
    require(m.get('version') == 1 and m.get('repository') == REPOSITORY and m.get('workflow') == WORKFLOW,
            'Invalid manifest identity')
    require(isinstance(m.get('sha'), str) and HEX.fullmatch(m['sha']), 'Invalid manifest SHA')
    require(type(m.get('run_id')) is int and m['run_id'] > 0 and type(m.get('run_attempt')) is int and m['run_attempt'] > 0,
            'Invalid manifest run identity')
    require(m.get('publication') == 'passed' and m.get('retention_days', 0) >= 30, 'Manifest publication/retention invalid')
    kind = m.get('kind', 'public')
    require(m.get('artifact_name') == artifact_name(m['sha'], m['run_id'], m['run_attempt'], kind), 'Artifact name/kind mismatch')
    require(isinstance(m.get('files'), dict) and m.get('file_count') == len(m['files']) and m['files'], 'Invalid manifest files')
    require(sha256((bundle / 'site.zip').read_bytes()).hexdigest() == m.get('archive_sha256'), 'Archive SHA-256 mismatch')
    return m


def restore(root, bundle, output, current_root=None):
    m = manifest(bundle)
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    require(sha == m['sha'], 'Historical checkout SHA mismatch')
    require(m['workflow_sha256'] == workflow_hash(root), 'Source workflow mismatch')
    require(not output.exists(), 'Recovery destination must be fresh')
    with zipfile.ZipFile(bundle / 'site.zip') as archive:
        names = safe_names(archive)
        require(set(names) == set(m['files']), 'Manifest/archive file list mismatch')
        payloads = {}
        for name in names:
            data = archive.read(name)
            require(sha256(data).hexdigest() == m['files'][name], 'File SHA-256 mismatch: ' + name)
            payloads[name] = data
        output.mkdir(parents=True)
        for name, data in payloads.items():
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    return publication(root, output, current_root, kind=m.get('kind', 'public'))


def authorize(flag, ref, source, head, expected_head):
    require(flag == 'true', 'Publication gate is OFF')
    require(ref == 'refs/heads/main', 'Recovery/release must execute on main')
    require(source == 'workflow', 'Pages Source must be GitHub Actions')
    require(head == expected_head and HEX.fullmatch(head), 'Current main SHA changed')


class NoCredentialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        require(newurl.startswith('https://'), 'Insecure artifact redirect')
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        redirected.remove_header('Authorization')
        return redirected


def api(path, binary=False):
    require(path.startswith('/repos/' + REPOSITORY + '/'), 'API outside approved repository')
    token = os.environ.get('GH_TOKEN')
    require(token, 'Authenticated Actions token required')
    req = Request('https://api.github.com' + path, headers={'Authorization': 'Bearer ' + token,
                  'Accept': 'application/vnd.github+json', 'X-GitHub-Api-Version': '2022-11-28', 'User-Agent': 'privatecapital-recovery'})
    with build_opener(NoCredentialRedirect()).open(req, timeout=60) as response:
        data = response.read(MAX_BYTES + 1)
    require(len(data) <= MAX_BYTES, 'API response too large')
    return data if binary else json.loads(data)


def check_origin(root, m, run, artifact, workflow, jobs, sha, artifact_id):
    require(HEX.fullmatch(sha or '') and m['sha'] == sha == run.get('head_sha'), 'Run/SHA mismatch')
    require(run.get('repository', {}).get('full_name') == REPOSITORY, 'Run repository mismatch')
    require(run.get('head_repository', {}).get('full_name') == REPOSITORY, 'Fork source forbidden')
    require(run.get('head_branch') == 'main' and run.get('event') in ('push', 'workflow_dispatch')
            and m.get('ref') == 'refs/heads/main' and m.get('event') == run['event'], 'Unapproved source branch/event')
    require(run.get('status') == 'completed' and run.get('conclusion') == 'success', 'Source run not successful')
    require(run.get('id') == m['run_id'] and run.get('run_attempt') == m['run_attempt'], 'Run ID/attempt mismatch')
    require(workflow.get('path') == WORKFLOW and workflow.get('id') == run.get('workflow_id')
            and run.get('path') == WORKFLOW, 'Unapproved workflow')
    require(m.get('workflow_sha256') == workflow_hash(root), 'Source workflow is not the approved implementation')
    require(any(j.get('name') == 'validate-atlas' and j.get('conclusion') == 'success' for j in jobs.get('jobs', [])),
            'Successful validation job missing')
    require(artifact.get('id') == artifact_id and artifact.get('name') == m['artifact_name'], 'Artifact ID/name mismatch')
    require(artifact.get('workflow_run', {}).get('id') == run['id']
            and artifact['workflow_run'].get('head_sha') == sha
            and artifact['workflow_run'].get('head_branch') == 'main', 'Artifact source mismatch')
    check_retention(artifact)


def check_retention(artifact):
    now = datetime.now(timezone.utc)
    expires = datetime.fromisoformat(artifact['expires_at'].replace('Z', '+00:00'))
    created = datetime.fromisoformat(artifact['created_at'].replace('Z', '+00:00'))
    require(not artifact.get('expired') and expires > now, 'Recovery artifact expired')
    require(expires - created >= timedelta(days=30) - timedelta(minutes=5), 'Actual artifact retention below 30 days')


def unpack_download(artifact, raw, bundle):
    require(not bundle.exists(), 'Bundle destination already exists')
    require(artifact.get('digest') == 'sha256:' + sha256(raw).hexdigest(), 'GitHub artifact digest mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(set(safe_names(archive)) == {'manifest.json', 'site.zip'}, 'Artifact is not a recovery bundle')
        bundle.mkdir(parents=True)
        for name in ('manifest.json', 'site.zip'):
            (bundle / name).write_bytes(archive.read(name))
    return manifest(bundle)


def fetch(root, run_id, artifact_id, sha, bundle, kind='public'):
    require(run_id > 0 and artifact_id > 0 and HEX.fullmatch(sha or ''), 'Invalid requested source identity')
    base = '/repos/' + REPOSITORY
    run = api(f'{base}/actions/runs/{run_id}')
    artifact = api(f'{base}/actions/artifacts/{artifact_id}')
    raw = api(f'{base}/actions/artifacts/{artifact_id}/zip', binary=True)
    m = unpack_download(artifact, raw, bundle)
    require(m.get('kind', 'public') == kind, 'Requested bundle kind mismatch')
    workflow = api(f'{base}/actions/workflows/{run["workflow_id"]}')
    jobs = api(f'{base}/actions/runs/{run_id}/attempts/{run["run_attempt"]}/jobs?per_page=100')
    check_origin(root, m, run, artifact, workflow, jobs, sha, artifact_id)
    require(m['run_id'] == run_id, 'Requested run ID mismatch')
    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as out:
            out.write(f'source-sha={sha}\n')
    return m


def pages_tar(output, target):
    """Local rehearsal of the file-only Pages tar; hosted upload uses the official action."""
    with tarfile.open(target, 'w') as archive:
        for path in sorted(output.rglob('*')):
            require(not path.is_symlink(), 'Pages symlink forbidden')
            if path.is_file():
                archive.add(path, arcname=path.relative_to(output).as_posix(), recursive=False)
    with tarfile.open(target) as archive:
        require(all(i.isfile() for i in archive.getmembers()), 'Invalid Pages tar members')


def gate():
    base = '/repos/' + REPOSITORY
    require(os.environ.get('PAGES_RELEASE_ENABLED') == 'true', 'Publication gate is OFF')
    source = api(base + '/pages')['build_type']
    head = api(base + '/git/ref/heads/main')['object']['sha']
    require(os.environ.get('RELEASE_AUTHORIZED') == 'true' and os.environ.get('GITHUB_EVENT_NAME') == 'workflow_dispatch',
            'Explicit manual release authorization required')
    authorize(os.environ.get('PAGES_RELEASE_ENABLED'), os.environ.get('GITHUB_REF'), source, head, os.environ.get('GITHUB_SHA'))
    controls = api(base + '/environments/github-pages')
    branches = api(base + '/environments/github-pages/deployment-branch-policies')
    main = api(base + '/branches/main')
    protection(controls, branches, main)


def protection(controls, branches, main):
    require(main.get('protected') is True, 'Main branch protection required')
    require(any(r.get('type') == 'required_reviewers' for r in controls.get('protection_rules', [])),
            'Manual Environment review required')
    require(controls.get('can_admins_bypass') is False, 'Environment admin bypass must be disabled')
    require(controls.get('deployment_branch_policy', {}).get('custom_branch_policies') is True,
            'Selected main-only Environment policy required')
    require([(b.get('name'), b.get('type')) for b in branches.get('branch_policies', [])] == [('main', 'branch')],
            'Environment must allow main only, without tags')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=('create', 'restore', 'fetch', 'rehearse', 'gate', 'retention'))
    p.add_argument('--root', type=Path, default=site.ROOT)
    p.add_argument('--source-root', type=Path)
    p.add_argument('--output', type=Path)
    p.add_argument('--bundle', type=Path)
    p.add_argument('--report', type=Path)
    p.add_argument('--run-id', type=int)
    p.add_argument('--artifact-id', type=int)
    p.add_argument('--sha')
    p.add_argument('--kind', choices=('public', 'emergency'), default='public')
    a = p.parse_args()
    try:
        if a.command == 'gate': gate()
        elif a.command == 'retention':
            artifact = api(f'/repos/{REPOSITORY}/actions/artifacts/{a.artifact_id}')
            m = manifest(a.bundle)
            require(artifact.get('name') == m['artifact_name'] and artifact.get('workflow_run', {}).get('id') == m['run_id'],
                    'Archived bundle/run identity mismatch')
            check_retention(artifact)
            downloaded = a.bundle.with_name(a.bundle.name + '-download-check')
            raw = api(f'/repos/{REPOSITORY}/actions/artifacts/{a.artifact_id}/zip', binary=True)
            copied = unpack_download(artifact, raw, downloaded)
            require(copied == m, 'Downloaded manifest differs from archived candidate')
            restored = a.bundle.with_name(a.bundle.name + '-hosted-rehearsal')
            restore(a.root, downloaded, restored, a.root)
            pages_tar(restored, restored.with_suffix('.tar'))
            print(json.dumps(dict(artifact_id=artifact['id'], expires_at=artifact['expires_at'],
                                  retention_verified=True, hosted_download_rehearsal=True, deploy_authorized=False)))
        elif a.command == 'create':
            print(json.dumps(create(a.root, a.output, a.bundle, a.report, a.kind)['checks']))
        elif a.command == 'fetch':
            fetch(a.root, a.run_id, a.artifact_id, a.sha, a.bundle, a.kind)
        else:
            result = restore(a.source_root or a.root, a.bundle, a.output, a.root)
            if a.command == 'rehearse':
                pages_tar(a.output, a.output.with_suffix('.tar'))
            print(json.dumps(dict(checks=result, deploy_authorized=False)))
    except (ValueError, KeyError, TypeError, OSError, zipfile.BadZipFile, subprocess.CalledProcessError) as error:
        p.exit(1, 'RECOVERY BLOCKED: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
