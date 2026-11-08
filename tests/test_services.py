"""Services navigation, generated pages and public boundaries."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import site_release as site

class Document(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.headers=0;self.feed(text)
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if attrs.get('id'):self.ids.append(attrs['id'])
        if tag=='a':self.links.append(attrs['href'])
        if tag=='header':self.headers+=1

def paths():
    content=json.loads((ROOT/'corporate/content.json').read_text(encoding='utf-8'))
    return ['corporate/index.html']+[f'corporate/{slug}/index.html' for slug in ['partners','team','solutions','collaboration']]+[f"corporate/{r['slug']}/index.html" for r in content['solutions']]

class ServicesTests(unittest.TestCase):
    def test_navigation_and_nested_anchors(self):
        self.assertEqual(len(paths()),9)
        for relative in paths():
            with self.subTest(page=relative):
                text=(ROOT/relative).read_text(encoding='utf-8');doc=Document(text)
                self.assertEqual(doc.headers,1)
                self.assertEqual(len(doc.ids),len(set(doc.ids)))
                for url in ['/corporate/team/','/corporate/partners/','/corporate/solutions/','/corporate/collaboration/','https://xsynplatform.ir/']:
                    self.assertIn(url,doc.links)
                self.assertIn('class="svc-primary-nav"',text)
                self.assertNotIn('class="svc-mobile-nav"',text)
                self.assertIn('class="svc-solutions-menu"',text)
                self.assertIn('class="svc-lightning"',text)
                self.assertNotIn('برای مطالعهٔ بیشتر',text)
                self.assertNotIn('پشتوانهٔ تصمیم',text)
                for ref in doc.links:
                    target=urlsplit(ref)
                    if target.scheme or target.netloc:continue
                    self.assertTrue(target.path.startswith('/') or target.fragment,ref)
                    file=ROOT/site.url_file(target.path) if target.path else ROOT/relative
                    self.assertTrue(file.is_file(),ref)
                    if target.fragment:self.assertIn(target.fragment,Document(file.read_text(encoding='utf-8')).ids,ref)
                expected='/corporate/' if relative=='corporate/index.html' else '/'+relative.removesuffix('index.html')
                self.assertEqual(site.Page(text).canonicals,[site.ORIGIN+expected])

    def test_landing_search_and_empty_team(self):
        text=(ROOT/'corporate/index.html').read_text(encoding='utf-8')
        self.assertEqual(text.count('role="search"'),1)
        self.assertIn('action="/corporate/solutions/"',text)
        self.assertNotIn('id="knowledge"',text)
        self.assertNotIn('class="svc-process"',text)
        self.assertNotIn('data-service-card',text)
        self.assertEqual(text.count('class="svc-decision"'),1)
        team=(ROOT/'corporate/team/index.html').read_text(encoding='utf-8')
        self.assertIn('class="svc-team-empty"',team)
        self.assertNotIn('class="svc-team-member"',team)
        collaboration=(ROOT/'corporate/collaboration/index.html').read_text(encoding='utf-8')
        self.assertIn('/contact.html',Document(collaboration).links)
        self.assertEqual(collaboration.count('role="search"'),1)
        self.assertIn('class="kaavosh-form kaavosh-form-compact"',collaboration)

    def test_services_rails_search_scope_and_partner_directory(self):
        for relative in paths():
            with self.subTest(page=relative):
                text=(ROOT/relative).read_text(encoding='utf-8')
                self.assertEqual(text.count('role="search"'),1)
                self.assertIn('action="/corporate/solutions/"',text)
                if relative=='corporate/index.html':
                    self.assertNotIn('class="explore-rail"',text)
                else:
                    self.assertIn('class="explore-rail svc-guide-rail"',text)
                    self.assertIn('data-service-guide>',text)
                    self.assertNotIn('explore-mobile-toc',text)
                    self.assertNotIn('explore-card',text)
                    self.assertNotIn('راهکار 0',text)
                    self.assertNotIn('<p class="svc-kicker">خدمات سرمایه، مالکیت و رشد</p>',text)
                    self.assertNotIn('<p class="svc-kicker">شرکای تجاری ما</p>',text)
                    if relative=='corporate/solutions/index.html':
                        self.assertNotIn('kaavosh-form-compact',text)
                        self.assertNotIn('موقعیت‌های شما',text)
                    else:self.assertIn('kaavosh-form-compact',text)
        partners=(ROOT/'corporate/partners/index.html').read_text(encoding='utf-8')
        self.assertIn('svc-directory-empty',partners)
        self.assertNotIn('یک مسئلهٔ مشترک؛ نقش‌های روشن',partners)
        self.assertNotIn('class="svc-partner"',partners)

    def test_shared_footer_for_every_public_destination(self):
        template=(ROOT/'tools/templates/site-footer.html').read_text(encoding='utf-8').strip()
        config=site.policy(ROOT)
        for relative in site.package_paths(ROOT,public=True,include_search=False):
            if not relative.endswith('.html') or site.page_url(relative) in config['canonical_aliases']:continue
            with self.subTest(page=relative):
                text=(ROOT/relative).read_text(encoding='utf-8')
                self.assertEqual(text.count(template),1)
                self.assertEqual(text.count('<footer'),1)
                self.assertIn('href="/assets/css/site-footer.css"',text)

    def test_package_allowlist_and_research_separation(self):
        public=set(site.package_paths(ROOT,public=True,include_search=False))
        for relative in paths():self.assertIn(relative,public)
        self.assertNotIn('corporate/content.json',public)
        self.assertIn('assets/css/services.css',public)
        self.assertIn('assets/js/services-ui.js',public)
        registry=json.loads((ROOT/'research/index.json').read_text(encoding='utf-8'))['research']
        self.assertFalse(any(r['url'].startswith(('/services','/corporate')) for r in registry))
        self.assertNotIn('/corporate/',(ROOT/'atlas/discovery/research-by-entity.json').read_text(encoding='utf-8'))

if __name__=='__main__':unittest.main()
