"""Real candidate regressions for the release boundary and URL/asset closure."""
import importlib.util
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import urlopen
from http.server import ThreadingHTTPServer
from functools import partial

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import site_release as site
import release as runner
spec = importlib.util.spec_from_file_location("release_preview", ROOT / "tools/preview-release.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class ReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.TemporaryDirectory()
        cls.candidate = Path(cls.base.name) / "site"
        cls.paths = site.package(ROOT, cls.candidate)

    @classmethod
    def tearDownClass(cls):
        cls.base.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "site"
        shutil.copytree(self.candidate, self.output)

    def test_real_candidate_preserves_old_pages_and_excludes_editorial_inputs(self):
        result = site.check_artifact(ROOT, self.output)
        self.assertGreater(result["pages"], 30)
        self.assertTrue((self.output / "atlas/concept/private-capital/index.html").is_file())
        self.assertTrue((self.output / "atlas/person.html").is_file())
        self.assertFalse((self.output / "research/content").exists())
        self.assertFalse((self.output / "tests").exists())
        self.assertFalse((self.output / "atlas/tools").exists())
        self.assertFalse((self.output / "atlas/discovery").exists())
        self.assertFalse((self.output / "atlas/schemas").exists())
        self.assertGreater(len(site.publication_blockers(ROOT, self.output)), 20)

    def test_two_packages_have_identical_bytes(self):
        second = Path(self.temp.name) / "second"
        site.package(ROOT, second)
        self.assertEqual(site.digest_files(self.output, self.paths), site.digest_files(second, self.paths))

    def test_missing_font_fails_with_owner_path(self):
        (self.output / "assets/Vazirmatn-Regular.woff2").unlink()
        with self.assertRaisesRegex(ValueError, "Vazirmatn-Regular"):
            site.check_artifact(ROOT, self.output)

    def test_missing_legacy_runtime_source_is_rejected(self):
        (self.output / "atlas/sources/ali-sanginian.json").unlink()
        with self.assertRaisesRegex(ValueError, "atlas/sources/ali-sanginian.json"):
            site.check_artifact(ROOT, self.output)

    def test_editorial_file_cannot_enter_artifact(self):
        path = self.output / "research/editorial-review.json"
        path.parent.mkdir()
        path.write_text('{"comments": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "extra=.*editorial-review"):
            site.check_artifact(ROOT, self.output)

    def test_preview_url_leak_is_rejected(self):
        path = self.output / "articles/private-capital-research.html"
        path.write_text(path.read_text(encoding="utf-8").replace('</body>', '<a href="/atlas/_preview/project/dadman/">test</a></body>'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "preview-only"):
            site.check_artifact(ROOT, self.output)

    def test_production_noindex_leak_is_rejected(self):
        path = self.output / "watch.html"
        path.write_text(path.read_text(encoding="utf-8").replace('</head>', '<meta name="robots" content="noindex"></head>'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "watch.html: preview/noindex"):
            site.check_artifact(ROOT, self.output)

    def test_wrong_canonical_is_rejected(self):
        path = self.output / "articles/private-capital.html"
        path.write_text(path.read_text(encoding="utf-8").replace('https://privatecapital.ir/articles/private-capital.html', 'https://privatecapital.ir/articles/wrong.html'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "private-capital.html: canonical mismatch"):
            site.check_artifact(ROOT, self.output)

    def test_broken_anchor_and_link_are_rejected(self):
        path = self.output / "contact.html"
        path.write_text(path.read_text(encoding="utf-8").replace('</body>', '<a href="/articles/private-capital.html#absent">test</a><a href="/missing.html">test</a></body>'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "missing anchor"):
            site.check_artifact(ROOT, self.output)

    def test_duplicate_sitemap_url_is_rejected(self):
        path = self.output / "sitemap.xml"
        path.write_text(path.read_text(encoding="utf-8").replace('</urlset>', '<url><loc>https://privatecapital.ir/</loc></url></urlset>'), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate https://privatecapital.ir/"):
            site.check_artifact(ROOT, self.output)

    def test_unsafe_index_filename_is_rejected(self):
        path = self.output / "atlas/sources/index.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data['sources']['source:bad'] = '../../research/editorial-review.json'
        path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsafe runtime filename"):
            site.check_artifact(ROOT, self.output)

    def test_package_refuses_nonempty_or_repository_root(self):
        with self.assertRaisesRegex(ValueError, "not empty"):
            site.package(ROOT, self.output)
        with self.assertRaisesRegex(ValueError, "isolated"):
            site.package(ROOT, ROOT)
        with self.assertRaisesRegex(ValueError, "isolated"):
            site.package(ROOT, ROOT / "assets/new-release")

    def test_sitemap_uses_public_registry_and_published_entity_routes(self):
        text = site.sitemap_text(ROOT)
        self.assertIn('https://privatecapital.ir/articles/private-capital-research.html', text)
        self.assertIn('https://privatecapital.ir/atlas/person/ali-sanginian/', text)
        self.assertIn('/atlas/concept/private-capital/', text)
        self.assertNotIn('/atlas/concept/lender/', text)
        self.assertNotIn('/resources.html', text)
        self.assertNotIn('/atlas/person.html', text)
        self.assertIn('/copyright.html', text)
        self.assertIn('2026-08-13', text)
        self.assertEqual(text, site.sitemap_text(ROOT))
        doc = site.ET.fromstring(text)
        record = next(x for x in doc if x.findtext(f'{{{site.NS}}}loc').endswith('/private-capital-research.html'))
        self.assertIsNone(record.find(f'{{{site.NS}}}lastmod'))

    def test_publication_gate_rejects_review_draft_archived_and_unsupported_types(self):
        for status in ('REVIEW', 'DRAFT', 'ARCHIVED', 'PUBLISHED'):
            with self.subTest(status=status):
                fixture = {'entities': [{'id': 'concept:test', 'type': 'Concept', 'lifecycleStatus': status}]}
                for path in ('atlas/entities/index.json', 'atlas/catalog/index.json'):
                    (self.output / path).write_text(json.dumps(fixture), encoding="utf-8")
                blockers = site.publication_blockers(ROOT, self.output)
                self.assertEqual(any('migration approval required' in b for b in blockers), status != 'PUBLISHED')
                # Replacing an index with a fake identity cannot authorize the remaining graph.
                self.assertTrue(blockers)
        fixture = {'entities': [{'id': 'project:test', 'type': 'Project', 'lifecycleStatus': 'PUBLISHED'}]}
        (self.output / 'atlas/entities/index.json').write_text(json.dumps(fixture), encoding="utf-8")
        self.assertTrue(any('no approved public' in b for b in site.publication_blockers(ROOT, self.output)))

    def test_inventory_captures_old_inline_inbound_references_and_query_routes(self):
        rows = site.inventory(ROOT)
        pc = next(x for x in rows if x['url'] == '/atlas/concept/private-capital/')
        self.assertEqual(pc['status'], 'PUBLISHED')
        self.assertIn('/articles/private-capital.html', pc['inbound_links'])
        self.assertTrue(pc['in_sitemap'])
        query = next(x for x in rows if x['url'] == '/atlas/person.html?id=person:ali-sanginian')
        self.assertEqual(query['canonical'], site.ORIGIN + '/atlas/person/ali-sanginian/')

    def source_fixture(self):
        fixture = Path(self.temp.name) / "source"
        shutil.copytree(self.candidate, fixture)
        for relative in ('tools/release/site-policy.json', 'research/index.json'):
            target = fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        return fixture

    def test_new_review_record_cannot_expand_legacy_exposure(self):
        root = self.source_fixture()
        path = root / 'atlas/entities/index.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        data['entities'].append({'id': 'concept:unapproved-new', 'type': 'Concept', 'lifecycleStatus': 'REVIEW'})
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'concept:unapproved-new: new non-public'):
            site.package_paths(root)

    def test_missing_approved_catalog_route_fails_without_inventing_url(self):
        root = self.source_fixture()
        path = root / 'atlas/catalog/index.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        record = next(x for x in data['entities'] if x['id'] == 'person:ali-sanginian')
        record.pop('route')
        path.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'person:ali-sanginian: missing or invalid approved catalog route'):
            site.package_paths(root)

    def test_http_smoke_does_not_use_system_proxies_for_loopback(self):
        # Exercise the proxy boundary on real HTML/script/font responses. The
        # pipeline separately exercises every file; this regression needs six
        # requests, not another full-site network run inside the unit suite.
        with patch.dict('os.environ', {'http_proxy':'http://127.0.0.1:9', 'https_proxy':'http://127.0.0.1:9', 'no_proxy':''}), patch.object(site, 'package_paths', return_value=['index.html','assets/js/atlas.js','assets/Vazirmatn-Regular.woff2']):
            self.assertEqual(runner.http_smoke(ROOT, self.output), 6)

    def test_transient_transport_retry_is_recorded_and_exhaustion_fails(self):
        # Inject transport outcomes deterministically; real loopback traffic is
        # covered by the proxy regression and the complete candidate smoke run.
        candidate = self.output
        class FixtureResponse(io.BytesIO):
            def __init__(self, body, status=200):
                super().__init__(body)
                self.status = status
                self.headers = {'Content-Length': str(len(body)), 'X-Robots-Tag': 'noindex'}
        class FlakyOpener:
            def __init__(self, persistent):
                self.failures = 0
                self.persistent = persistent
            def open(self, url, **kwargs):
                if url.endswith('/assets/js/atlas.js') and (self.persistent or self.failures == 0):
                    self.failures += 1
                    raise ConnectionResetError('fixture connection reset')
                if url.endswith('/assets/js/atlas.js'):
                    return FixtureResponse((candidate / 'assets/js/atlas.js').read_bytes())
                return FixtureResponse((candidate / '404.html').read_bytes(), status=404)
        for persistent in (False, True):
            with self.subTest(persistent=persistent):
                diagnostics = []
                with patch.object(runner, 'build_opener', return_value=FlakyOpener(persistent)), patch.object(site, 'package_paths', return_value=['assets/js/atlas.js']):
                    if persistent:
                        with self.assertRaisesRegex(ValueError, 'request failed for /assets/js/atlas.js'):
                            runner.http_smoke(ROOT, self.output, diagnostics)
                    else:
                        self.assertEqual(runner.http_smoke(ROOT, self.output, diagnostics), 3)
                self.assertTrue(any(x['url'] == '/assets/js/atlas.js' and x['retry'] == 1 for x in diagnostics))

    def test_internal_research_fetch_is_rejected_before_packaging(self):
        root = self.source_fixture()
        path = root / 'articles/private-capital-research.html'
        text = path.read_text(encoding='utf-8').replace('<article ', '<article data-research-source="../research/content/private-markets/private-capital-research/research.json" ', 1)
        self.assertIn('data-research-source', text)
        path.write_text(text, encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'public article fetches internal Research'):
            site.package_paths(root)

    def test_unpublished_research_cannot_be_selected_for_packaging(self):
        root = self.source_fixture()
        path = root / 'research/index.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        record = next(x for x in data['research'] if x['id'] == 'research:private-capital-research')
        record['status'] = 'REVIEW'
        path.write_text(json.dumps(data), encoding='utf-8')
        self.assertNotIn('articles/private-capital-research.html', site.package_paths(root))
        blockers = site.publication_blockers(root, self.output)
        self.assertTrue(any('research:private-capital-research: unpublished Research' in b for b in blockers))

    def test_loopback_preview_preserves_bytes_and_suppresses_production_seo(self):
        before = site.digest_files(self.output, self.paths)
        server = ThreadingHTTPServer(('127.0.0.1', 0), partial(preview.CandidateHandler, directory=str(self.output)))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            origin = f'http://127.0.0.1:{server.server_port}'
            with urlopen(origin + '/articles/private-capital-research.html') as response:
                body = response.read().decode()
                self.assertEqual(response.status, 200)
                self.assertIn('noindex', response.headers['X-Robots-Tag'])
                self.assertEqual(site.Page(body).canonicals, [])
                self.assertNotIn('https://privatecapital.ir', body)
            with urlopen(origin + '/robots.txt') as response:
                self.assertIn(b'Disallow: /', response.read())
            with self.assertRaises(HTTPError) as raised:
                urlopen(origin + '/absent-route')
            self.assertEqual(raised.exception.code, 404)
            self.assertIn('صفحه پیدا نشد', raised.exception.read().decode())
            raised.exception.close()
            with self.assertRaises(HTTPError) as raised:
                urlopen(origin + '/assets/')
            self.assertEqual(raised.exception.code, 404)
            raised.exception.close()
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
        self.assertEqual(before, site.digest_files(self.output, self.paths))


if __name__ == '__main__':
    unittest.main()
