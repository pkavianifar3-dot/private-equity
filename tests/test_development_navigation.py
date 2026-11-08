"""Development notices, shared section shell and exact Corporate route migration."""
from pathlib import Path
from urllib.parse import urlsplit
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import search
import site_release as site

class DevelopmentNavigationTests(unittest.TestCase):
    def test_public_navigation_uses_shared_menu(self):
        template=(ROOT/'tools/templates/development-menu.html').read_text(encoding='utf-8').strip()
        self.assertIn('>شتابدهنده زایا</a>',template)
        self.assertNotIn('شتابدهنده و ونچرز',template)
        paths=[ROOT/'index.html',ROOT/'articles.html',ROOT/'atlas/index.html',ROOT/'atlas/explore/index.html',ROOT/'atlas/concept/private-capital/index.html',ROOT/'articles/private-capital.html']
        for path in paths:
            with self.subTest(path=path):
                source=path.read_text(encoding='utf-8');self.assertIn(template,source)
                header=search.Tree(source).root.find(lambda e:e.tag=='header')[0]
                nav=header.find(lambda e:e.tag=='nav')[0]
                self.assertEqual(len([e for e in nav.children if not isinstance(e,str)]),8)
                menu=nav.find(lambda e:e.tag=='details' and e.attrs.get('class')=='development-menu')[0]
                self.assertEqual([a.attrs['href'] for a in menu.find(lambda e:e.tag=='a')],['/corporate/','/ventures/','/developers/'])

    def test_shared_scroll_controller_reaches_every_public_header(self):
        for relative in site.package_paths(ROOT,public=True,include_search=False):
            if not relative.endswith('.html'):continue
            source=(ROOT/relative).read_text(encoding='utf-8')
            tree=search.Tree(source).root
            headers=tree.find(lambda element:element.tag=='header')
            if not headers or not headers[0].find(lambda element:element.tag=='nav'):continue
            with self.subTest(page=relative):
                scripts=tree.find(lambda element:element.tag=='script' and element.attrs.get('src')=='/assets/js/site-navigation.js')
                self.assertEqual(len(scripts),1)
                self.assertIn('defer',scripts[0].attrs)

    def test_section_home_links_keep_complete_names_and_decorative_icons(self):
        for url,title in [('/corporate/','خدمات شرکتی'),('/ventures/','شتابدهنده زایا'),('/developers/','پلتفرم توسعه‌دهندگان')]:
            with self.subTest(url=url):
                tree=search.Tree((ROOT/site.url_file(url)).read_text(encoding='utf-8')).root
                home=tree.find(lambda element:element.tag=='a' and element.attrs.get('class')=='svc-home')[0]
                self.assertEqual(home.attrs['href'],url)
                self.assertEqual(home.attrs['aria-label'],'خانهٔ '+title)
                label=home.find(lambda element:element.attrs.get('class')=='svc-home-text')[0]
                self.assertEqual(' '.join(label.text().split()),title)
                icon=home.find(lambda element:element.tag=='svg')[0]
                self.assertEqual(icon.attrs['aria-hidden'],'true')

    def test_corporate_canonical_and_exact_legacy_aliases(self):
        config=site.policy(ROOT)
        aliases={source:target for source,target in config['canonical_aliases'].items() if source=='/services.html' or source.startswith('/services/')}
        self.assertEqual(len(aliases),9)
        self.assertNotIn('/services/',aliases)
        self.assertNotIn('/services/',config['pages'])
        self.assertFalse((ROOT/'services/index.html').exists())
        for source,target in aliases.items():
            with self.subTest(source=source):
                self.assertTrue(target.startswith('/corporate/'))
                self.assertNotIn(target,aliases)
                html=(ROOT/site.url_file(source)).read_text(encoding='utf-8')
                self.assertEqual(site.Page(html).canonicals,[site.ORIGIN+target])
                self.assertIn('location.search+location.hash',html)
                self.assertIn(f'content="0;url={target}"',html)
                self.assertNotIn(source,config['sitemap_pages'])
                self.assertEqual(site.Page((ROOT/site.url_file(target)).read_text(encoding='utf-8')).canonicals,[site.ORIGIN+target])

    def test_development_pages_share_section_navigation_and_explicit_notice(self):
        config=site.policy(ROOT)
        for url,title in [('/ventures/','شتابدهنده زایا'),('/developers/','پلتفرم توسعه‌دهندگان')]:
            with self.subTest(url=url):
                self.assertIn(url,config['development_pages']);self.assertNotIn(url,config['sitemap_pages'])
                source=(ROOT/site.url_file(url)).read_text(encoding='utf-8');tree=search.Tree(source).root
                self.assertTrue(any('noindex' in value for value in site.Page(source).robots))
                self.assertIn('class="services-page platform-development"',source)
                self.assertIn('href="/assets/css/services.css"',source)
                self.assertFalse(tree.find(lambda e:e.attrs.get('class')=='development-menu'))
                nav=tree.find(lambda e:e.attrs.get('class')=='svc-primary-nav')[0]
                self.assertEqual(len([e for e in nav.children if not isinstance(e,str)]),5)
                self.assertIn('/corporate/partners/',[a.attrs.get('href') for a in nav.find(lambda e:e.tag=='a')])
                main=tree.find(lambda e:e.tag=='main')[0]
                self.assertEqual(main.find(lambda e:e.tag=='h1')[0].text().replace('“','').strip(),title)
                self.assertIn('در حال توسعه',main.text())
                self.assertTrue(main.find(lambda e:e.attrs.get('data-development-status')=='in-progress'))
                forms=main.find(lambda e:e.tag=='form')
                self.assertEqual(len(forms),1)
                self.assertEqual(forms[0].attrs['action'],'/corporate/solutions/')
                self.assertIn('جست‌وجوی خدمات شرکتی',source)

    def test_active_pages_never_link_to_legacy_services_routes(self):
        config=site.policy(ROOT);aliases=config['canonical_aliases']
        for url in config['pages']:
            if url in aliases:continue
            page=site.Page((ROOT/site.url_file(url)).read_text(encoding='utf-8'))
            for ref in page.links:
                path=urlsplit(ref).path
                self.assertFalse(path=='/services.html' or path.startswith('/services/'),(url,ref))

if __name__=='__main__':unittest.main()
