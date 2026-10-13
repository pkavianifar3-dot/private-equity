"""Search presentation contracts independently of ranking and canonical content."""
import sys
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'atlas/tools'))
import kaavosh_markup as markup
import search
import exploration

class SearchPresentationTests(unittest.TestCase):
    def test_native_search_signature_and_scope_across_surfaces(self):
        for path,scope,action in [('index.html','all','/articles.html'),('atlas/index.html','all','/atlas/'),('articles.html','research','/articles.html'),('atlas/explore/index.html','all','/atlas/explore/')]:
            with self.subTest(path=path):
                tree=search.Tree((ROOT/path).read_text(encoding='utf-8')).root
                forms=tree.find(lambda e:e.tag=='form' and e.attrs.get('role')=='search')
                self.assertEqual(len(forms),1)
                form=forms[0];self.assertEqual(form.attrs['action'],action)
                self.assertEqual(form.attrs['method'],'get')
                expected=markup.search_form(action=action,scope=scope,home=path=='index.html',results=path!='index.html')
                self.assertEqual(re.search(r'<form[^>]*>.*?</form>',(ROOT/path).read_text(encoding='utf-8'),re.S).group(),expected)
                options=form.find(lambda e:e.tag=='option' and 'selected' in e.attrs)
                if path=='index.html':
                    self.assertFalse(form.find(lambda e:e.tag in {'select','label'}))
                    self.assertEqual(form.find(lambda e:e.tag=='input' and e.attrs.get('name')=='scope')[0].attrs['value'],'all')
                else:
                    self.assertEqual(options[0].attrs['value'],scope)
                self.assertTrue(form.find(lambda e:e.tag=='input' and e.attrs.get('type')=='search')[0].attrs.get('aria-label'))
                self.assertEqual(len(form.find(lambda e:e.tag=='svg')),1)
                self.assertEqual(form.find(lambda e:e.tag=='button')[0].attrs['aria-label'],'جست‌وجو')
                self.assertIn('href="/assets/css/kaavosh.css"',(ROOT/path).read_text(encoding='utf-8'))

    def test_global_home_link_and_navigation_contract(self):
        paths=list(ROOT.glob('*.html'))+list((ROOT/'articles').glob('*.html'))+list((ROOT/'atlas').glob('*/*/index.html'))+[ROOT/'atlas/index.html',ROOT/'atlas/explore/index.html']
        for path in paths:
            with self.subTest(path=path):
                source=path.read_text(encoding='utf-8')
                tree=search.Tree(source).root
                headers=tree.find(lambda e:e.tag=='header')
                if not headers:continue
                brands=headers[0].find(lambda e:e.tag=='a' and e.attrs.get('class')=='logo')
                self.assertEqual(len(brands),1)
                self.assertEqual(brands[0].attrs['href'],'/')
                self.assertTrue(brands[0].attrs.get('aria-label'))
                self.assertEqual(len(brands[0].find(lambda e:e.tag=='img')),1)
                nav=headers[0].find(lambda e:e.tag=='nav')
                if nav:
                    labels=[''.join(c for c in e.children if isinstance(c,str)).strip() for e in nav[0].find(lambda e:e.tag=='a')]
                    self.assertEqual(labels[:4],['خانه','دیده‌بان','پژوهش‌ها','اطلس'])

    def test_compact_is_independent_of_brand_visibility(self):
        self.assertNotIn('kaavosh-form-compact',markup.search_form())
        self.assertNotIn('kaavosh-brand',markup.search_form())
        self.assertIn('kaavosh-form-compact',markup.search_form(compact=True))

    def test_lens_titles_and_feature_order(self):
        for path,title,heading in [('articles.html','کاوش در پژوهش‌ها','فهم عمیق‌تر، نگاه دقیق‌تر'),('atlas/index.html','کاوش در اطلس','کشف مفاهیم و روابط کلیدی')]:
            source=(ROOT/path).read_text(encoding='utf-8')
            self.assertIn(title,source)
            self.assertIn(heading,source)
            self.assertNotIn('class="kaavosh-brand"',source)
            self.assertLess(source.index('-hero-intro'),source.index('data-discovery-feature'))

    def test_rail_search_has_no_brand_or_filter_and_precedes_toc(self):
        rail=exploration.rail([(2,'intro','Introduction')],[],context='Atlas')
        tree=search.Tree(rail).root
        form=tree.find(lambda e:e.tag=='form')[0]
        self.assertEqual(form.attrs['action'],'/articles.html')
        self.assertEqual(form.find(lambda e:e.tag=='input' and e.attrs.get('name')=='scope')[0].attrs['value'],'all')
        self.assertFalse(form.find(lambda e:e.tag in {'select','label'}))
        self.assertLess(rail.index('<form'),rail.index('class="explore-toc"'))

    def test_relation_label_precedes_target_without_losing_name_or_url(self):
        card=exploration.card('کاوش در اطلس',[{'title':'سرمایه رشد','meta':'شامل می‌شود','url':'/atlas/concept/growth-capital/'}],'/atlas/')
        self.assertLess(card.index('شامل می‌شود'),card.index('سرمایه رشد'))
        self.assertEqual(card.count('href="/atlas/concept/growth-capital/"'),2)

    def test_signature_escaping_and_accessible_submit(self):
        form=markup.search_form(action='/atlas/?bad="<x>')
        self.assertNotIn('bad="<x>',form)
        self.assertIn('&quot;&lt;x&gt;',form)
        self.assertIn('aria-label="جست‌وجو"',form)
        self.assertIn('focusable="false"',form)

    def test_editorial_feature_heading_precedes_uncropped_image(self):
        config=search.read(ROOT/'tools/search-home.json')
        docs=[{'id':config['featuredResearchRef'],'kind':'research','scope':'research','type':'Research','title':'Research','url':'/articles/example.html','summary':'Summary','cover':'/assets/images/private-capital.png'}, {'id':config['featuredConceptRef'],'kind':'concept','scope':'atlas','type':'Concept','title':'Concept','url':'/atlas/concept/private-capital/','summary':'Summary'}]
        rendered=search.home_html(ROOT,docs)['articles.html'].decode()
        self.assertLess(rendered.index('پژوهش برتر · انتخاب تحریریه'),rendered.index('class="research-feature-cover"'))
        self.assertNotIn('discovery-bridge-card',rendered)
        self.assertIn('discovery-crosslinks',rendered)

if __name__=='__main__':unittest.main()
