"""Independent emergency output; never a subset/rebuild of the canonical site."""
from pathlib import Path
from urllib.parse import urlsplit
import re
import site_release as site

TEMPLATES = 'tools/release/emergency-site'
FILES = {'index.html', '404.html', 'CNAME', 'robots.txt'}


def check(root, output):
    files = {p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file()}
    if files != FILES or any(p.is_symlink() for p in output.rglob('*')):
        raise ValueError('Emergency package must contain exactly four approved files, without links')
    for name in sorted(FILES):
        expected = site.safe_file(root / TEMPLATES, name).read_bytes().replace(b'\r\n', b'\n')
        if site.safe_file(output, name).read_bytes() != expected:
            raise ValueError('Emergency bytes differ from approved source: ' + name)
    for name in ('index.html', '404.html'):
        text = (output / name).read_text(encoding='utf-8')
        page = site.Page(text)
        if page.assets or page.research_sources or re.search(r'<(?:script|iframe|form|object|embed)\b', text, re.I):
            raise ValueError('Emergency page has executable/data/asset dependencies')
        if 'data-emergency-site="true"' not in text or 'noindex' not in ','.join(page.robots):
            raise ValueError('Emergency page must identify emergency mode and prohibit indexing')
        if 'width=device-width' not in text or 'dir="rtl"' not in text:
            raise ValueError('Emergency mobile/RTL contract missing')
        if re.search(r'url\s*\(|@import|atlas/|research/|entityRefs|REVIEW', text, re.I):
            raise ValueError('Emergency page has a forbidden dependency/reference')
        if any(link not in ('/', '#main') for link in page.links):
            raise ValueError('Emergency page links outside standalone surface')
        expected_canonical = [site.ORIGIN + '/'] if name == 'index.html' else []
        if page.canonicals != expected_canonical:
            raise ValueError('Emergency canonical mismatch')
    if (output / 'CNAME').read_text().strip() != urlsplit(site.ORIGIN).netloc:
        raise ValueError('Emergency domain mismatch')
    if (output / 'robots.txt').read_text() != 'User-agent: *\nDisallow: /\n':
        raise ValueError('Emergency robots policy mismatch')
    return dict(files=4, pages=2, sitemap_urls=0, publication='passed', kind='emergency')


def build(root, output):
    if output.exists():
        raise ValueError('Emergency output must be a fresh isolated directory')
    if output.resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(output.resolve()):
        raise ValueError('Emergency output must be outside the repository')
    output.mkdir(parents=True)
    for name in sorted(FILES):
        (output / name).write_bytes(site.safe_file(root / TEMPLATES, name).read_bytes().replace(b'\r\n', b'\n'))
    return check(root, output)
