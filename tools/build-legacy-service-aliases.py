"""Exact legacy redirects only; /services/ itself remains available for future use."""
from pathlib import Path
from html import escape
import json

ROOT=Path(__file__).resolve().parents[1]

def build():
    config=json.loads((ROOT/'tools/release/site-policy.json').read_text(encoding='utf-8'))
    aliases={source:target for source,target in config['canonical_aliases'].items()
             if source=='/services.html' or source.startswith('/services/')}
    for source,target in aliases.items():
        if not target.startswith('/corporate/') or any(token in source+target for token in ['..','\\','?','#','"',"'"]):
            raise ValueError('Legacy Services aliases must resolve directly to a safe Corporate URL')
        destination=ROOT/(target.lstrip('/')+'index.html' if target.endswith('/') else target.lstrip('/'))
        if not destination.is_file():raise ValueError(f'Missing legacy redirect destination: {target}')
        relative=source.lstrip('/')+('index.html' if source.endswith('/') else '')
        output=ROOT/relative
        output.parent.mkdir(parents=True,exist_ok=True)
        encoded=json.dumps(target)
        html=f'''<!DOCTYPE html>
<!-- Generated exact compatibility alias; canonical content lives under /corporate/. -->
<html lang="fa" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>انتقال به خدمات شرکتی | Private Capital</title><link rel="canonical" href="https://privatecapital.ir{escape(target)}"><script>location.replace({encoded}+location.search+location.hash);</script><noscript><meta http-equiv="refresh" content="0;url={escape(target)}"></noscript></head><body><a href="{escape(target)}">ادامه در خدمات شرکتی</a></body></html>
'''
        output.write_text(html,encoding='utf-8',newline='\n')
    print(f'Generated {len(aliases)} exact legacy Services aliases.')

if __name__=='__main__':build()
