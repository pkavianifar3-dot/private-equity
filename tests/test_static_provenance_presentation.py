import importlib.util
import unittest
from html.parser import HTMLParser


SPEC = importlib.util.spec_from_file_location(
    "build_static_pages",
    "atlas/tools/build-static-pages.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ProvenanceLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.source_anchors = []
        self.source_refs = []
        self.claim_anchors = []
        self.claim_refs = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        anchor = attributes.get("id", "")
        href = attributes.get("href", "")
        if anchor.startswith("source-"):
            self.source_anchors.append(anchor)
        if anchor.startswith("claim-"):
            self.claim_anchors.append(anchor)
        if href.startswith("#source-"):
            self.source_refs.append(href[1:])
        if href.startswith("#claim-"):
            self.claim_refs.append(href[1:])


class StaticProvenancePresentationTests(unittest.TestCase):
    def setUp(self):
        self.claims = [
            {
                "id": "claim:test",
                "subject": "concept:a",
                "predicate": "INCLUDES",
                "object": "concept:b",
                "status": "SUPPORTED",
                "confidence": "HIGH",
                "evidenceRefs": ["evidence:test", "evidence:third"],
            },
            {
                "id": "claim:second",
                "subject": "concept:a",
                "predicate": "INCLUDES",
                "object": "concept:c",
                "status": "SUPPORTED",
                "evidenceRefs": ["evidence:second"],
            },
        ]
        self.evidence = {
            ref: {
                "id": ref,
                "claimRef": claim_id,
                "sourceRef": "source:test",
                "evidenceType": "authoritative_publication",
                "strength": "strong",
            }
            for ref, claim_id in (
                ("evidence:test", "claim:test"),
                ("evidence:third", "claim:test"),
                ("evidence:second", "claim:second"),
            )
        }
        self.sources = {
            "source:test": {
                "id": "source:test",
                "title_fa": "مرجع مشترک",
                "publisher": "ناشر",
                "url": "https://example.com/source",
            },
            "source:content": {
                "id": "source:content",
                "title_fa": "منبع متن",
                "url": "https://example.com/content",
            },
        }
        self.entities = {
            "concept:a": {"name": {"fa": "سرمایه خصوصی"}},
            "concept:b": {"name": {"fa": "سهام خصوصی"}},
            "concept:c": {"name": {"fa": "اعتبار خصوصی"}},
        }
        self.contract = {
            "relations": {
                "INCLUDES": {
                    "forward_label_fa": "شامل می‌شود",
                    "reverse_label_fa": "بخشی از",
                    "reverse_display_allowed": True,
                }
            }
        }
        self.content = {
            "sections": [
                {"paragraphs": [{"sourceRefs": ["source:content", "source:test"]}]}
            ]
        }
        self.source_index = MODULE.build_source_index(
            self.sources, self.claims, self.evidence, self.content
        )

    def render(self, claims=None):
        return MODULE.render_provenance(
            self.claims if claims is None else claims,
            self.evidence,
            self.sources,
            self.source_index,
            self.entities,
            "concept:a",
            self.contract,
        )

    def overview(self, claims=None):
        return MODULE.render_claims(
            self.claims if claims is None else claims,
            "concept:a",
            self.entities,
            self.contract,
            self.evidence,
            self.sources,
        )

    def test_claim_summary_links_to_compact_evidence_and_unique_source(self):
        overview = self.overview()
        detail = self.render()
        self.assertIn('href="#claim-claim:test"', overview)
        self.assertIn("۲ شاهد · ۱ منبع", overview)
        self.assertNotIn("SUPPORTED", overview)
        self.assertNotIn("HIGH", overview)
        self.assertEqual(
            detail.count('class="atlas-section atlas-provenance-section"'), 1
        )
        self.assertEqual(detail.count("atlas-provenance-card"), 2)
        self.assertEqual(
            detail.count("سرمایه خصوصی شامل می‌شود سهام خصوصی"), 1,
            "claim title must appear once in the detail card",
        )
        self.assertNotIn("شاهد برای", detail)
        self.assertIn("شاهد ۱", detail)
        self.assertIn("شاهد ۲", detail)
        self.assertIn(
            f'<a class="atlas-source-ref" href="#source-source:test" '
            f'aria-label="رفتن به منبع شماره {self.source_index["source:test"]}">'
            f'<bdi dir="ltr">[{self.source_index["source:test"]}]</bdi></a>'
            '<strong>شاهد ۱</strong>',
            detail,
        )
        self.assertNotIn("منبع [", detail)
        self.assertEqual(detail.count('class="atlas-provenance-source-heading"'), 3)
        self.assertIn(
            '</a></div><span class="atlas-source-number">'
            f'<bdi dir="ltr">[{self.source_index["source:test"]}]</bdi></span>',
            detail,
        )
        self.assertIn(
            'id="source-source:content"',
            detail,
            "content-only source keeps its citation target",
        )
        self.assertIn("نوع شاهد: انتشار مرجع معتبر", detail)
        self.assertIn("اعتبار: اعتبار بالا", detail)
        self.assertIn("پشتیبانی‌شده · اطمینان بالا", detail)
        self.assertEqual(detail.count("مرجع مشترک"), 2,
                         "shared source appears once per claim")
        self.assertIn("<summary>جزئیات فنی</summary>", detail)
        self.assertIn('شناسه شاهد: <bdi dir="ltr">evidence:test</bdi>', detail)
        self.assertIn('شناسه منبع: <bdi dir="ltr">source:test</bdi>', detail)
        self.assertNotIn("authoritative_publication", detail)

        links = ProvenanceLinks()
        links.feed(overview + detail)
        self.assertEqual(len(links.source_anchors), len(set(links.source_anchors)))
        self.assertEqual(len(links.claim_anchors), len(set(links.claim_anchors)))
        self.assertTrue(set(links.source_refs) <= set(links.source_anchors))
        self.assertTrue(set(links.claim_refs) <= set(links.claim_anchors))
        self.assertEqual(
            set(links.source_anchors),
            {"source-source:test", "source-source:content"},
        )
        self.assertIn("منابع متن", detail)
        self.assertIn('class="provenance-card-divider"', detail)

    def test_source_only_and_claim_without_evidence(self):
        detail = self.render(claims=[])
        self.assertIn('id="source-source:content"', detail)
        self.assertNotIn("atlas-provenance-card", detail)
        unsupported = dict(
            self.claims[0], id="claim:without-evidence", evidenceRefs=[]
        )
        overview = self.overview(claims=[unsupported])
        self.assertNotIn("href=\"#claim-claim:without-evidence\"", overview)
        self.assertIn("پشتیبانی‌شده", overview)
        self.assertIn("اطمینان: بالا", overview)

    def test_reverse_title_uses_current_entity_as_subject(self):
        title, label = MODULE.provenance_claim_title(
            self.claims[0], "concept:b", self.entities, self.contract
        )
        self.assertEqual(title, "سهام خصوصی بخشی از سرمایه خصوصی")
        self.assertEqual(label, "بخشی از")

    def test_real_page_citations_resolve_on_every_generated_entity(self):
        entities = MODULE.load_entities()
        claims = MODULE.load_claims()
        evidence = MODULE.load_evidence()
        sources = MODULE.load_sources()
        contract = MODULE.load_relation_contract()
        for entity_id, entity in entities.items():
            if entity.get("type") not in MODULE.ROUTES:
                continue
            with self.subTest(entity=entity_id):
                page = MODULE.render_entity(
                    entity, claims, evidence, sources, entities, contract
                )
                links = ProvenanceLinks()
                links.feed(page)
                self.assertEqual(
                    len(links.source_anchors), len(set(links.source_anchors))
                )
                self.assertEqual(
                    len(links.claim_anchors), len(set(links.claim_anchors))
                )
                self.assertTrue(
                    set(links.source_refs) <= set(links.source_anchors),
                    f"{entity_id}: unresolvable source",
                )
                self.assertTrue(
                    set(links.claim_refs) <= set(links.claim_anchors),
                    f"{entity_id}: unresolvable claim detail",
                )
                self.assertEqual(
                    page.count('class="atlas-section atlas-provenance-section"'),
                    int(bool(links.source_anchors)),
                )


if __name__ == "__main__":
    unittest.main()
