"""Inspect the exact candidate locally; never build or publish another site.

The files stay unchanged. HTTP responses suppress production SEO signals and
all routes are noindex. Only the loopback interface is available. REVIEW content
in this compatibility candidate must never be uploaded to a public service.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse
import io
import re
import site_release as site


class CandidateHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        target = Path(path)
        if target.is_symlink() or not target.resolve().is_relative_to(Path(self.directory).resolve()):
            self.send_error(404)
            return None
        if target.is_dir():
            if not urlsplit(self.path).path.endswith("/"):
                return super().send_head()
            target = target / "index.html"
            if not target.is_file():
                self.send_error(404)  # no directory listings
                return None
        if urlsplit(self.path).path == "/robots.txt":
            body = b"User-agent: *\nDisallow: /\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        if not target.is_file():
            self.send_error(404)
            return None
        if target.suffix == ".html":
            body = preview_html(target.read_text(encoding="utf-8")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        # Read before sending headers and compute length from those same bytes.
        # This keeps transfer length exact and avoids slow per-chunk disk reads.
        body = target.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", self.guess_type(str(target)))
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        return io.BytesIO(body)

    def send_error(self, code, message=None, explain=None):
        error_page = Path(self.directory) / "404.html"
        if code != 404 or not error_page.is_file():
            return super().send_error(code, message, explain)
        body = preview_html(error_page.read_text(encoding="utf-8")).encode("utf-8")
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)


def preview_html(text):
    # Local HTTP presentation only, no mutation of the verified artifact. This
    # also covers dynamic Atlas applyPageSEO() calls without changing its code.
    text = re.sub(r'<link\b[^>]*\brel=[\'\"]canonical[\'\"][^>]*>', "", text, flags=re.I)
    text = re.sub(r'https?://privatecapital\.ir(?=[/\'\"<\s])', "", text)
    guard = '<meta name="robots" content="noindex,nofollow,noarchive">'
    # A small end-of-head observer strips canonical tags inserted by legacy JS.
    guard += '<script>new MutationObserver(function(){document.querySelectorAll(\'link[rel="canonical"]\').forEach(function(n){n.remove()})}).observe(document.documentElement,{childList:true,subtree:true});</script>'
    return re.sub(r"</head>", guard + "</head>", text, count=1, flags=re.I)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8780)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose an unprivileged local port (1024–65535)")
    if not args.artifact.is_dir():
        parser.error("Artifact directory does not exist")
    site.check_artifact(site.ROOT, args.artifact)
    handler = partial(CandidateHandler, directory=str(args.artifact.resolve()))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    print(f"Local candidate inspection: http://127.0.0.1:{args.port}/ (noindex, loopback only)", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
