"""Negative provenance/content fixtures and real public-bundle rehearsal; no deploy."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import recovery as rec
import site_release as site


class RecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory()
        cls.site = Path(cls.base.name) / 'site'
        site.package(ROOT, cls.site, public=True)
        cls.sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
        cls.report = Path(cls.base.name) / 'report.json'
        cls.report.write_text(json.dumps(dict(commit=cls.sha, working_tree_dirty=False,
            files=site.digest_files(cls.site, site.package_paths(ROOT, public=True)))), encoding='utf-8')
        cls.env = dict(GITHUB_REPOSITORY=rec.REPOSITORY, GITHUB_SHA=cls.sha, GITHUB_RUN_ID='101',
                       GITHUB_RUN_ATTEMPT='1', GITHUB_REF='refs/heads/main', GITHUB_EVENT_NAME='push')
        cls.bundle = Path(cls.base.name) / 'bundle'
        with patch.dict(os.environ, cls.env):
            cls.m = rec.create(ROOT, cls.site, cls.bundle, cls.report)

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.bundle = Path(self.temp.name) / 'bundle'
        shutil.copytree(self.bundle_base(), self.bundle)
        self.output = Path(self.temp.name) / 'recovered'
        self.m = deepcopy(type(self).m)

    @classmethod
    def bundle_base(cls):
        return cls.bundle

    def write_manifest(self):
        (self.bundle / 'manifest.json').write_text(json.dumps(self.m), encoding='utf-8')

    def origin(self):
        run = dict(id=101, run_attempt=1, head_sha=self.sha, head_branch='main', event='push',
                   status='completed', conclusion='success', repository={'full_name': rec.REPOSITORY},
                   head_repository={'full_name': rec.REPOSITORY},
                   workflow_id=55, path=rec.WORKFLOW)
        now = datetime.now(timezone.utc)
        artifact = dict(id=77, name=self.m['artifact_name'], expired=False,
            created_at=now.isoformat(), expires_at=(now+timedelta(days=30)).isoformat(),
            workflow_run=dict(id=101, head_sha=self.sha, head_branch='main'))
        workflow = dict(id=55, path=rec.WORKFLOW)
        jobs = {'jobs': [dict(name='validate-atlas', conclusion='success')]}
        return run, artifact, workflow, jobs

    def check_origin(self, run=None, artifact=None, workflow=None, jobs=None, sha=None):
        originals = self.origin()
        return rec.check_origin(ROOT, self.m, run or originals[0], artifact or originals[1],
            workflow or originals[2], jobs or originals[3], sha or self.sha, 77)

    def test_real_public_bundle_recovery_and_pages_format(self):
        self.check_origin()
        result = rec.restore(ROOT, self.bundle, self.output, ROOT)
        self.assertEqual(result['files'], self.m['file_count'])
        self.assertEqual(site.digest_files(self.site, self.m['files']), site.digest_files(self.output, self.m['files']))
        self.assertFalse((self.output/'manifest.json').exists())
        self.assertFalse((self.output/'research/content').exists())
        rec.pages_tar(self.output, Path(self.temp.name)/'artifact.tar')
        self.assertTrue((Path(self.temp.name)/'artifact.tar').is_file())

    def test_tampered_archive(self):
        with open(self.bundle/'site.zip', 'ab') as archive: archive.write(b'corruption')
        with self.assertRaisesRegex(ValueError, 'Archive SHA'): rec.restore(ROOT,self.bundle,self.output)

    def test_file_hash_mismatch(self):
        self.m['files']['index.html'] = '0'*64; self.write_manifest()
        with self.assertRaisesRegex(ValueError, 'File SHA'): rec.restore(ROOT,self.bundle,self.output)

    def test_missing_and_corrupt_manifest(self):
        (self.bundle/'manifest.json').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing'): rec.manifest(self.bundle)
        (self.bundle/'manifest.json').write_text('{broken')
        with self.assertRaises(ValueError): rec.manifest(self.bundle)

    def test_source_identity_negative_matrix(self):
        for field, value in [('id',102),('run_attempt',2),('head_sha','0'*40),('head_branch','feature'),
                             ('event','pull_request'),('conclusion','failure'),('status','in_progress'),
                             ('path','.github/workflows/untrusted.yml'),('workflow_id',66)]:
            with self.subTest(field=field):
                run=self.origin()[0];run[field]=value
                with self.assertRaises(ValueError): self.check_origin(run=run)
        with self.assertRaisesRegex(ValueError,'Run/SHA'): self.check_origin(sha='0'*40)
        run=self.origin()[0];run['repository']['full_name']='attacker/repo'
        with self.assertRaisesRegex(ValueError,'repository'): self.check_origin(run=run)
        run=self.origin()[0];run['head_repository']['full_name']='attacker/fork'
        with self.assertRaisesRegex(ValueError,'Fork'):self.check_origin(run=run)

    def test_artifact_identity_negative_matrix(self):
        for field,value in [('id',78),('name','arbitrary'),('expired',True),
                             ('expires_at',(datetime.now(timezone.utc)-timedelta(days=1)).isoformat())]:
            with self.subTest(field=field):
                artifact=self.origin()[1];artifact[field]=value
                with self.assertRaises(ValueError): self.check_origin(artifact=artifact)
        artifact=self.origin()[1];artifact['workflow_run']['head_branch']='feature'
        with self.assertRaisesRegex(ValueError,'source'): self.check_origin(artifact=artifact)
        artifact=self.origin()[1];artifact['expires_at']=(datetime.now(timezone.utc)+timedelta(days=1)).isoformat()
        with self.assertRaisesRegex(ValueError,'retention'): self.check_origin(artifact=artifact)

    def test_unapproved_workflow_and_validation(self):
        self.m['workflow_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'implementation'):self.check_origin()
        self.m['workflow_sha256']=rec.workflow_hash(ROOT)
        with self.assertRaisesRegex(ValueError,'validation'):self.check_origin(jobs={'jobs':[]})

    def test_unavailable_artifact_api_fails_closed(self):
        with patch.object(rec,'api',side_effect=OSError('404 unavailable')):
            with self.assertRaisesRegex(OSError,'unavailable'):
                rec.fetch(ROOT,101,77,self.sha,Path(self.temp.name)/'fetch')

    def test_api_archive_digest_mismatch(self):
        run,artifact,_,_=self.origin();artifact['digest']='sha256:'+'0'*64
        with patch.object(rec,'api',side_effect=[run,artifact,b'not the artifact']):
            with self.assertRaisesRegex(ValueError,'GitHub artifact digest'):
                rec.fetch(ROOT,101,77,self.sha,Path(self.temp.name)/'fetch')

    def test_api_download_roundtrip_prepares_only_public_files(self):
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            for name in ('site.zip','manifest.json'):archive.writestr(name,(self.bundle/name).read_bytes())
        raw=stream.getvalue();run,artifact,workflow,jobs=self.origin()
        artifact['digest']='sha256:'+sha256(raw).hexdigest()
        destination=Path(self.temp.name)/'downloaded'
        with patch.object(rec,'api',side_effect=[run,artifact,raw,workflow,jobs]):
            m=rec.fetch(ROOT,101,77,self.sha,destination)
        self.assertEqual(m['sha'],self.sha)
        rec.restore(ROOT,destination,self.output,ROOT)
        self.assertFalse((self.output/'manifest.json').exists())

    def test_manifest_run_sha_and_workflow_tampering(self):
        for field,value in [('run_id',102),('run_attempt',2),('sha','0'*40),('workflow','untrusted.yml'),
                            ('publication','failed'),('file_count',0),('repository','attacker/repo')]:
            with self.subTest(field=field):
                self.m=deepcopy(type(self).m);self.m[field]=value;self.write_manifest()
                with self.assertRaises(ValueError):
                    m=rec.manifest(self.bundle)
                    run,artifact,workflow,jobs=self.origin()
                    rec.check_origin(ROOT,m,run,artifact,workflow,jobs,self.sha,77)

    def test_publication_gate_and_context_matrix(self):
        rec.authorize('true','refs/heads/main','workflow',self.sha,self.sha)
        for args in [('false','refs/heads/main','workflow',self.sha,self.sha),
                     ('','refs/heads/main','workflow',self.sha,self.sha),
                     ('true','refs/heads/feature','workflow',self.sha,self.sha),
                     ('true','refs/heads/main','legacy',self.sha,self.sha),
                     ('true','refs/heads/main','workflow','0'*40,self.sha)]:
            with self.subTest(args=args):
                with self.assertRaises(ValueError):rec.authorize(*args)
        with patch.dict(os.environ,{'PAGES_RELEASE_ENABLED':'false'}), patch.object(rec,'api') as api:
            with self.assertRaisesRegex(ValueError,'OFF'):rec.gate()
            api.assert_not_called()

    def test_no_implicit_manual_authorization(self):
        with patch.dict(os.environ,{'PAGES_RELEASE_ENABLED':'true','RELEASE_AUTHORIZED':'false'}), \
             patch.object(rec,'api',side_effect=[{'build_type':'workflow'},{'object':{'sha':self.sha}}]):
            with self.assertRaisesRegex(ValueError,'manual'):rec.gate()

    def rezip(self, mutate):
        with zipfile.ZipFile(self.bundle/'site.zip') as archive:
            values={i.filename:archive.read(i) for i in archive.infolist()}
        mutate(values)
        with zipfile.ZipFile(self.bundle/'site.zip','w') as archive:
            for name,data in values.items():archive.writestr(name,data)
        self.m['files']={name:sha256(data).hexdigest() for name,data in values.items()}
        self.m['file_count']=len(values)
        self.m['archive_sha256']=sha256((self.bundle/'site.zip').read_bytes()).hexdigest()
        self.write_manifest()

    def test_forbidden_file_even_with_recomputed_hashes(self):
        self.rezip(lambda values:values.update({'research/editorial-review.json':b'{}'}))
        with self.assertRaisesRegex(ValueError,'extra='):rec.restore(ROOT,self.bundle,self.output)

    def test_forbidden_relation_even_with_recomputed_hashes(self):
        def mutate(values):
            name='atlas/claims/stage-5-reviewed.json';data=json.loads(values[name])
            data['claims'][0]['object']='project:dadman'
            values[name]=json.dumps(data).encode()
        self.rezip(mutate)
        with self.assertRaises(ValueError):rec.restore(ROOT,self.bundle,self.output)

    def test_failed_content_validation_and_unapproved_checkout(self):
        with patch.object(site,'check_artifact',side_effect=ValueError('invalid links')):
            with self.assertRaisesRegex(ValueError,'invalid links'):rec.restore(ROOT,self.bundle,self.output)
        self.m['sha']='0'*40
        self.m['artifact_name']=rec.artifact_name(self.m['sha'],101,1)
        self.write_manifest()
        with self.assertRaisesRegex(ValueError,'checkout SHA'):rec.restore(ROOT,self.bundle,self.output)

    def test_zip_traversal_and_symlinks(self):
        self.rezip(lambda values:values.update({'../outside':b'bad'}))
        with self.assertRaisesRegex(ValueError,'Unsafe'):rec.restore(ROOT,self.bundle,self.output)
        self.assertFalse((Path(self.temp.name)/'outside').exists())
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w') as archive:
            info=zipfile.ZipInfo('link');info.external_attr=(0o120777)<<16;archive.writestr(info,'target')
        with zipfile.ZipFile(io.BytesIO(stream.getvalue())) as archive:
            with self.assertRaisesRegex(ValueError,'links'):rec.safe_names(archive)

    def test_current_publication_revocation_blocks_historical_package(self):
        with patch.object(site,'publication_blockers',side_effect=[[],['Entity is now REVIEW']]):
            with self.assertRaisesRegex(ValueError,'now REVIEW'):rec.restore(ROOT,self.bundle,self.output,ROOT)

    def test_workflow_deployment_and_retention_contract(self):
        text=(ROOT/rec.WORKFLOW).read_text(encoding='utf-8')
        self.assertIn('retention-days: 30',text)
        self.assertNotIn('retention-days: 1\n',text)
        self.assertIn('inputs.release_authorized',text)
        self.assertIn('!inputs.recovery_dry_run',text)
        self.assertIn('environment:\n      name: github-pages',text)
        self.assertGreaterEqual(text.count('python tools/recovery.py gate'),3)
        self.assertIn('path: ${{ runner.temp }}/recovered-site',text)

    def test_environment_and_main_protection(self):
        controls=dict(protection_rules=[{'type':'required_reviewers'}],can_admins_bypass=False,
                      deployment_branch_policy={'custom_branch_policies':True})
        branches={'branch_policies':[{'name':'main','type':'branch'}]}
        rec.protection(controls,branches,{'protected':True})
        with self.assertRaisesRegex(ValueError,'Main'):rec.protection(controls,branches,{'protected':False})
        for field,value in [('protection_rules',[]),('can_admins_bypass',True),('deployment_branch_policy',{})]:
            with self.subTest(field=field):
                bad=deepcopy(controls);bad[field]=value
                with self.assertRaises(ValueError):rec.protection(bad,branches,{'protected':True})
        with self.assertRaisesRegex(ValueError,'main only'):
            rec.protection(controls,{'branch_policies':[{'name':'main','type':'tag'}]},{'protected':True})


if __name__=='__main__': unittest.main()
