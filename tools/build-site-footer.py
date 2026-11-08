"""Apply the shared footer to maintained policy pages, leaving exact aliases intact."""
from pathlib import Path
import json
import re
import site_release as site
ROOT=Path(__file__).resolve().parents[1]
def build():
    config=json.loads((ROOT/'tools/release/site-policy.json').read_text(encoding='utf-8'))
    footer=(ROOT/'tools/templates/site-footer.html').read_text(encoding='utf-8').strip()
    for relative in site.package_paths(ROOT,public=True,include_search=False):
        if not relative.endswith('.html'):continue
        url=site.page_url(relative)
        path=ROOT/relative
        text=path.read_text(encoding='utf-8')
        if url in config['canonical_aliases'] and not re.search(r'<footer\b',text):continue
        if re.search(r'<footer\b',text):
            text=re.sub(r'<footer\b[^>]*>[\s\S]*?</footer>',lambda _:footer,text)
        else:
            text=text.replace('</body>',footer+'\n</body>')
        if url=='/copyright.html':
            text=re.sub(r'<div class="footer">[\s\S]*?</div>','',text)
            text=re.sub(r'(?m)^[ \t]+$', '', text)
        if 'href="/assets/css/site-footer.css"' not in text:
            text=text.replace('</head>','<link rel="stylesheet" href="/assets/css/site-footer.css">\n</head>')
        if text!=path.read_text(encoding='utf-8'):path.write_text(text,encoding='utf-8',newline='\n')
if __name__=='__main__':build()
