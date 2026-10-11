"""Contract tests for preview presentation over canonical graph and editorial refs."""

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / f"atlas/tools/{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


exploration = load("exploration")
static = load("build-static-pages")


class ExplorationTests(unittest.TestCase):
    def test_preview_styles_scope_sticky_focus_and_mobile(self):
        css = (ROOT / "assets/css/exploration.css").read_text(encoding="utf-8")
        self.assertIn(".explore-rail-inner{position:sticky", css)
        self.assertIn("@media(max-width:980px)", css)
        self.assertIn("@media(max-width:700px)", css)
        self.assertIn(":focus-visible", css)
        self.assertIn(".explore-mobile-toc nav{display:block}", css)

    def test_shared_research_layout_is_repeatable_and_public_filtered(self):
        article = {"id":"research:test", "entityRefs":["concept:review","concept:public"]}
        catalog = [{"id":"concept:"+key,"type":"Concept","lifecycleStatus":status,"name":{"fa":key}}
                   for key,status in [("review","REVIEW"),("public","PUBLISHED")]]
        page = '<html><head></head><body><article><h2>آغاز</h2><p>محتوا</p>' + \
               '<div data-research-connections></div><!-- research-connections --></article></body></html>'
        resolver = lambda ref,kind: '/atlas/concept/'+ref.split(':')[1]+'/'
        editorial = lambda article,root: []
        public = exploration.research_page(page,article,catalog,ROOT,resolver,editorial)
        self.assertNotIn('href="/atlas/concept/review/"',public)
        self.assertIn('href="/atlas/concept/public/"',public)
        self.assertEqual(exploration.research_page(public,article,catalog,ROOT,resolver,editorial),public)
        local = exploration.research_page(public,article,catalog,ROOT,resolver,editorial,preview=True)
        self.assertIn('href="/atlas/concept/review/"',local)
        self.assertEqual(local.count('data-research-exploration'),1)
        self.assertNotIn('data-research-connections',local)

    def test_toc_uses_actual_headings_and_stable_targets(self):
        content = '<h2>سرمایه خصوصی چیست؟</h2><p>بدنه</p><h3>دامنه <em>بازار</em></h3>'
        anchored, headings = exploration.article_toc(content)
        changed, shifted = exploration.article_toc('<h2>مقدمه</h2>' + content)
        self.assertEqual([row[2] for row in headings], ["سرمایه خصوصی چیست؟", "دامنه بازار"])
        self.assertEqual([row[1] for row in headings], [row[1] for row in shifted[1:]])
        self.assertIn(f'id="{headings[0][1]}"', anchored)
        self.assertIn(f'href="#{headings[1][1]}"', exploration.toc_nav(headings))
        self.assertIn('<details', exploration.toc_nav(headings, mobile=True))
        self.assertEqual(exploration.article_toc(anchored)[1], headings)

    def test_editorial_entity_selection_and_disclosure(self):
        catalog = [
            {"id": f"concept:{i}", "type": "Concept", "lifecycleStatus": "PUBLISHED",
             "name": {"fa": f"مفهوم {i}"}} for i in range(6)
        ]
        catalog.append({"id": "concept:review", "type": "Concept",
                        "lifecycleStatus": "REVIEW", "name": {"fa": "بازبینی"}})
        refs = ["concept:0", "concept:0", "concept:review", "concept:missing"] + [
            f"concept:{i}" for i in range(1, 6)
        ]
        resolver = lambda ref, _type: "/atlas/concept/" + ref.split(":")[1] + "/"
        public = exploration.pick_article_entities({"entityRefs": refs}, catalog, resolver)
        self.assertEqual(len(public), 6)
        self.assertEqual(public[0]["title"], "مفهوم 0")
        self.assertNotIn("بازبینی", str(public))
        preview = exploration.pick_article_entities({"entityRefs": refs}, catalog, resolver,
                                                    preview=True)
        self.assertEqual(len(preview), 7)
        card = exploration.card("کاوش در اطلس", public, "/atlas/")
        self.assertEqual(card.count('href="/atlas/concept/'), 12)  # desktop and mobile
        self.assertIn('<details class="explore-more">', card)
        self.assertIn('نمایش 2 مورد دیگر', card)
        self.assertIn('href="/atlas/"', card)
        self.assertIn('class="explore-empty"', exploration.card("کاوش", [], "/atlas/"))
        many = [{"url": f"/atlas/{n}/", "title": str(n)} for n in range(10)]
        capped = exploration.card("کاوش در اطلس", many, "/atlas/")
        self.assertIn('نمایش 4 مورد دیگر', capped)
        self.assertNotIn('href="/atlas/8/"', capped)
        self.assertIn('>08</span>', capped)

    def test_direct_relation_respects_reverse_policy_publication_and_route(self):
        root = "concept:root"
        entities = {
            name: {"id": name, "type": "Concept", "lifecycleStatus": status,
                   "name": {"fa": name}}
            for name, status in (("concept:one", "PUBLISHED"), ("concept:two", "PUBLISHED"),
                                 ("concept:review", "REVIEW"), ("concept:no-route", "PUBLISHED"))
        }
        claims = [
            {"id": "claim:1", "subject": root, "object": "concept:one", "predicate": "FORWARD"},
            {"id": "claim:2", "subject": root, "object": "concept:one", "predicate": "FORWARD"},
            {"id": "claim:3", "subject": "concept:two", "object": root, "predicate": "REVERSE_OK"},
            {"id": "claim:4", "subject": "concept:review", "object": root, "predicate": "REVERSE_NO"},
            {"id": "claim:5", "subject": root, "object": "concept:review", "predicate": "FORWARD"},
            {"id": "claim:6", "subject": root, "object": "concept:no-route", "predicate": "FORWARD"},
        ]
        contract = {"relations": {
            "FORWARD": {"forward_label_fa": "شامل", "reverse_display_allowed": False},
            "REVERSE_OK": {"reverse_display_allowed": True, "reverse_label_fa": "مرتبط با"},
            "REVERSE_NO": {"reverse_display_allowed": False, "reverse_label_fa": "نباید"},
        }}
        resolver = lambda ref, _type: None if ref == "concept:no-route" else "/atlas/" + ref.split(":")[1] + "/"
        public = exploration.pick_related_entities(
            root, claims, entities, contract, resolver, static.render_claim_relation,
        )
        self.assertEqual([row["title"] for row in public], ["concept:one", "concept:two"])
        self.assertEqual([row["meta"] for row in public], ["شامل", "مرتبط با"])
        preview = exploration.pick_related_entities(
            root, claims, entities, contract, resolver, static.render_claim_relation,
            preview=True,
        )
        self.assertEqual(len(preview), 3)
        self.assertNotIn("نباید", str(preview))


if __name__ == "__main__":
    unittest.main()
