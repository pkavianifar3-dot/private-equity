"""Portable release gates shared by local verification and GitHub Actions."""
import argparse
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import sys
import site_release as site
import importlib.util
from http.server import ThreadingHTTPServer
from functools import partial
from urllib.request import build_opener, ProxyHandler
from urllib.error import HTTPError
import threading

BUILD_COMMANDS = [
    [sys.executable, "atlas/tools/build-index.py"],
    [sys.executable, "atlas/tools/build-catalog.py"],
    ["node", "atlas/tools/build-research-pages.js"],
    [sys.executable, "atlas/tools/build-research-connections.py"],
    [sys.executable, "atlas/tools/build-static-pages.py"],
]
GENERATED = ["atlas/entities/index.json", "atlas/claims/index.json", "atlas/evidence/index.json", "atlas/sources/index.json",
             "atlas/discovery", "atlas/catalog", "atlas/person", "atlas/organization", "atlas/investment", "atlas/concept", "articles", "assets/images/research", "sitemap.xml", "docs/stage-5-url-disposition.md"]


def run(args, root):
    print("+ " + " ".join(args), flush=True)
    subprocess.run(args, cwd=root, check=True)


def generated_snapshot(root):
    files = set()
    for name in GENERATED:
        p = root / name
        if p.is_file():
            files.add(p)
        elif p.is_dir():
            files.update(x for x in p.rglob("*") if x.is_file())
    return {p.relative_to(root).as_posix(): sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest() for p in files}


def http_smoke(root, output, diagnostics=None, public=False):
    spec = importlib.util.spec_from_file_location("release_smoke_preview", root / "tools/preview-release.py")
    preview = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preview)
    class QuietHandler(preview.CandidateHandler):
        def log_message(self, format, *args):
            pass
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(QuietHandler, directory=str(output.resolve())))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    checks = 0
    # Never send loopback verification through system/environment proxies.
    opener = build_opener(ProxyHandler({}))
    diagnostics = diagnostics if diagnostics is not None else []
    def fetch(origin, url):
        for attempt in range(2):
            try:
                try:
                    response = opener.open(origin + url, timeout=15)
                except HTTPError as error:
                    response = error
                with response:
                    # Bound each receive buffer; validate framing explicitly so
                    # a short stream can never look like a successful response.
                    chunks = []
                    while chunk := response.read(16384):
                        chunks.append(chunk)
                    body = b"".join(chunks)
                    length = response.headers.get("Content-Length")
                    if length is None or len(body) != int(length):
                        raise ValueError(f"HTTP smoke: incomplete body for {url}: {len(body)} bytes; expected {length}")
                    return response.status, response.headers, body
            except OSError as error:
                cause = getattr(error, "reason", error)
                transient = isinstance(cause, (TimeoutError, ConnectionResetError, ConnectionAbortedError))
                if attempt == 0 and transient:
                    diagnostics.append(dict(url=url, error=type(cause).__name__, retry=1))
                    print(f"HTTP transport retry (1/1): {url}: {type(cause).__name__}", flush=True)
                    continue
                raise ValueError(f"HTTP smoke: request failed for {url}: {type(error).__name__}: {error}") from error
    try:
        origin = f"http://127.0.0.1:{server.server_port}"
        for relative in site.package_paths(root, public=public):
            url = site.page_url(relative) if relative.endswith(".html") else "/" + relative
            status, headers, body = fetch(origin, url)
            if status != 200 or not body:
                raise ValueError(f"HTTP smoke: {url} returned {status} or empty data")
            if "noindex" not in headers.get("X-Robots-Tag", ""):
                raise ValueError(f"HTTP smoke: local inspection lacks noindex: {url}")
            if relative.endswith(".html"):
                document = site.Page(body.decode("utf-8"))
                if document.canonicals:
                    raise ValueError(f"HTTP smoke: production canonical leaked to preview: {url}")
            elif relative != "robots.txt" and body != (output / relative).read_bytes():
                raise ValueError(f"HTTP smoke: asset/runtime body differs: {url}")
            checks += 1
        # Filename aliases and canonical directory addresses both exist today.
        for relative in site.package_paths(root, public=public):
            if not relative.endswith("index.html"):
                continue
            url = "/" + relative
            status, headers, body = fetch(origin, url)
            document = site.Page(body.decode("utf-8"))
            if status != 200 or document.canonicals:
                raise ValueError(f"HTTP smoke: invalid filename alias {url}")
            checks += 1
        missing_urls = ["/release-missing-route-test", "/assets/"]
        if public:
            _, private_paths = site.public_projection.private_paths(root)
            for relative in sorted(private_paths):
                if relative.endswith("index.html"):
                    missing_urls.extend((site.page_url(relative), "/" + relative))
                else:
                    missing_urls.append("/" + relative)
        for url in missing_urls:
            status, headers, body = fetch(origin, url)
            if status != 404 or "صفحه پیدا نشد" not in body.decode("utf-8"):
                raise ValueError(f"HTTP smoke: invalid 404 for {url}")
            checks += 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join()
    return checks


def verify(root, output, ci=False):
    before = generated_snapshot(root)
    run([sys.executable, "atlas/tools/validate-atlas.py"], root)
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], root)
    test_files = sorted((root / "tests").glob("*.test.js"))
    if not test_files:
        raise ValueError("No JavaScript tests found")
    for p in sorted((root / "assets/js").rglob("*.js")):
        run(["node", "--check", str(p)], root)
    for p in test_files:
        run(["node", str(p)], root)
    for args in BUILD_COMMANDS:
        run(args, root)
    text = site.sitemap_text(root)
    (root / "sitemap.xml").write_text(text, encoding="utf-8", newline="\n")
    matrix = root / "docs/stage-5-url-disposition.md"
    if not matrix.is_file() or matrix.read_text(encoding="utf-8") != site.inventory_markdown(root):
        raise ValueError("URL disposition matrix drift; regenerate with: python tools/release.py inventory --output docs/stage-5-url-disposition.md")
    after = generated_snapshot(root)
    if before != after:
        changed = sorted(k for k in before.keys() | after.keys() if before.get(k) != after.get(k))
        raise ValueError("Generated artifact drift: " + ", ".join(changed))
    if ci:
        run(["git", "diff", "--exit-code", "--", *GENERATED], root)
        extra = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard", "--", *GENERATED], cwd=root, text=True).strip()
        if extra:
            raise ValueError("Untracked generated output: " + extra)
        dirty = subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip()
        if dirty:
            raise ValueError("CI source tree changed during verification:\n" + dirty)
    site.package(root, output, public=True)
    result = site.check_artifact(root, output, public=True)
    transport_retries = []
    result["http_checks"] = http_smoke(root, output, transport_retries, public=True)
    result["http_transport_retries"] = transport_retries
    files = site.digest_files(output, site.package_paths(root, public=True))
    blockers = site.publication_blockers(root, output)
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    report = dict(commit=sha, candidate_kind="local-compatibility-only" if blockers else "public-eligible",
                  artifact_sha256=sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), files=files,
                  checks=result, publication_blockers=blockers,
                  python=sys.version.split()[0], node=subprocess.check_output(["node", "--version"], text=True).strip(),
                  github_run_id=os.getenv("GITHUB_RUN_ID"), github_sha=os.getenv("GITHUB_SHA"))
    report["working_tree_dirty"] = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=root, text=True).strip())
    report["worktree_diff_sha256"] = sha256(subprocess.check_output(["git", "diff", "HEAD", "--binary"], cwd=root)).hexdigest()
    output.with_name(output.name + ".manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(dict(result, artifact_sha256=report["artifact_sha256"], publication_blockers=len(blockers)), ensure_ascii=False), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("verify", "build", "check", "publication", "sitemap", "inventory", "smoke"))
    parser.add_argument("--root", type=Path, default=site.ROOT)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--ci", action="store_true")
    parser.add_argument("--check", action="store_true", help="check sitemap drift without writing")
    args = parser.parse_args()
    root = args.root.resolve()
    try:
        if args.command in ("verify", "build", "check", "publication", "smoke") and not args.output:
            parser.error("--output is required")
        if args.command == "verify":
            verify(root, args.output, args.ci)
        elif args.command == "build":
            site.package(root, args.output, public=True)
            print(site.check_artifact(root, args.output, public=True))
        elif args.command == "check":
            print(site.check_artifact(root, args.output, public=True))
        elif args.command == "smoke":
            site.check_artifact(root, args.output, public=True)
            print(f"HTTP checks passed: {http_smoke(root, args.output, public=True)}")
        elif args.command == "publication":
            site.check_artifact(root, args.output, public=True)
            blockers = site.publication_blockers(root, args.output)
            if blockers:
                raise ValueError("PUBLICATION BLOCKED; local candidate only:\n" + "\n".join(blockers))
            print("PUBLICATION ELIGIBILITY PASSED")
        elif args.command == "sitemap":
            text = site.sitemap_text(root)
            if args.check:
                if (root / "sitemap.xml").read_text(encoding="utf-8") != text:
                    raise ValueError("sitemap.xml drift")
            else:
                (root / "sitemap.xml").write_text(text, encoding="utf-8", newline="\n")
        elif args.command == "inventory":
            if not args.output:
                parser.error("--output is required")
            args.output.write_text(site.inventory_markdown(root), encoding="utf-8", newline="\n")
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
