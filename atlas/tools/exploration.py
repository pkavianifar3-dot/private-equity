"""Preview-only exploration presentation over existing Research/Atlas contracts.

The selectors are pure and can be reused when a public presentation is approved.
No inferred or similarity-based association is created here.
"""

import hashlib
import html
import re
from html.parser import HTMLParser


def esc(value):
    return html.escape(str(value or ""), quote=True)


class HeadingText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


def article_toc(article_html, *, levels=(2, 3), prefix="research"):
    """Anchor actual rendered headings with stable text-derived IDs."""
    headings = []
    seen = set()
    pattern = re.compile(r"<h([23])(?P<attrs>[^>]*)>(?P<body>.*?)</h\1>", re.S | re.I)

    def anchor(match):
        level, attrs, body = match.group(1), match.group("attrs"), match.group("body")
        if int(level) not in levels:
            return match.group(0)
        parser = HeadingText()
        parser.feed(body)
        label = " ".join("".join(parser.parts).split())
        if not label:
            return match.group(0)
        existing = re.search(r'\bid="([^"]+)"', attrs)
        if existing:
            anchor_id = existing.group(1)
        else:
            digest = hashlib.sha1(f"{level}:{label}".encode("utf-8")).hexdigest()[:10]
            anchor_id = f"{prefix}-section-{digest}"
            while anchor_id in seen:
                anchor_id += "-2"
            attrs += f' id="{anchor_id}"'
        seen.add(anchor_id)
        headings.append((int(level), anchor_id, label))
        return f"<h{level}{attrs}>{body}</h{level}>"

    return pattern.sub(anchor, article_html), headings


def toc_nav(headings, *, mobile=False):
    links = "".join(
        f'<li class="explore-toc-level-{level}"><a href="#{esc(anchor_id)}">{esc(label)}</a></li>'
        for level, anchor_id, label in headings
    )
    nav = f'<nav aria-label="راهنمای مطالعه"><ol>{links}</ol></nav>'
    if mobile:
        return f'<details class="explore-mobile-toc"><summary>راهنمای مطالعه <span>{len(headings)} بخش</span></summary>{nav}</details>'
    return nav


def pick_article_entities(article, catalog, resolver, *, preview=False):
    """Author order; dedupe; keep only resolvable, publication-eligible refs."""
    by_id = {entry["id"]: entry for entry in catalog}
    items = []
    for ref in dict.fromkeys(article.get("entityRefs", [])):
        entity = by_id.get(ref)
        if not entity or (not preview and entity.get("lifecycleStatus") != "PUBLISHED"):
            continue
        url = resolver(ref, entity["type"])
        if not url:
            continue
        items.append({"url": url, "title": entity["name"]["fa"]})
    return items


def pick_related_entities(entity_id, claims, entities, relation_contract, resolver,
                          render_relation, *, preview=False):
    """Direct canonical edges; forward first; respect reverse display policy."""
    candidates = []
    for claim in claims:
        relation = render_relation(claim, entity_id, relation_contract)
        if not relation:
            continue
        target_id = relation["target_id"]
        entity = entities.get(target_id)
        if not entity or (not preview and entity.get("lifecycleStatus") != "PUBLISHED"):
            continue
        url = resolver(target_id, entity["type"])
        if url:
            candidates.append((relation["direction"] != "forward", claim.get("id", ""),
                               target_id, {"url": url, "title": entity["name"]["fa"],
                                           "meta": relation["label"]}))
    selected = {}
    for _, _, target_id, item in sorted(candidates, key=lambda row: row[:3]):
        selected.setdefault(target_id, item)
    return list(selected.values())


def pick_research(index, entity_id):
    """The generated reverse index already enforces publication and routes."""
    return [
        {"url": row["url"], "title": row["title"],
         "meta": "نمونهٔ نمایشی؛ فقط در preview" if row.get("previewFixture") else ""}
        for row in index["entities"].get(entity_id, [])
    ]


def pick_editorial(article, root, editorial_related):
    return [
        {"url": row["url"], "title": row["title"]}
        for row in editorial_related(article, root)
    ]


def card(title, items, all_url, *, empty="هنوز موردی ثبت نشده است."):
    """Shared card: up to four visible and four disclosed, then the directory."""
    items = items[:8]
    limit = 4
    def rows(values):
        return '<ul class="explore-items">' + "".join(
            '<li><a href="' + esc(item["url"]) + '"><span class="explore-item-title">'
            + esc(item["title"]) + '</span>'
            + (f'<small>{esc(item["meta"])}</small>' if item.get("meta") else '')
            + '</a></li>' for item in values
        ) + '</ul>'

    body = rows(items[:limit]) if items else f'<p class="explore-empty">{esc(empty)}</p>'
    if len(items) > limit:
        rest = len(items) - limit
        body += (f'<details class="explore-more"><summary>نمایش {rest} مورد دیگر</summary>'
                 + rows(items[limit:]) + '</details>')
    heading = (f'<span class="explore-card-title">{esc(title)}</span>'
               f'<span class="explore-count">{len(items):02d}</span>')
    footer = f'<a class="explore-all" href="{esc(all_url)}">{esc(title)}</a>'
    return (f'<section class="explore-card explore-desktop-card"><div class="explore-card-heading">'
            f'{heading}</div>{body}{footer}</section>'
            f'<details class="explore-card explore-mobile-card"><summary>{heading}</summary>'
            f'{body}{footer}</details>')


def rail(headings, cards, *, context):
    return (f'<aside class="explore-rail" aria-label="کاوش در {esc(context)}">'
            '<div class="explore-rail-inner"><div class="explore-toc">'
            '<h2>راهنمای مطالعه</h2>' + toc_nav(headings) + '</div>'
            + toc_nav(headings, mobile=True) + ''.join(cards) + '</div></aside>')


def research_rail(article, catalog, root, resolver, editorial_related, headings):
    atlas = pick_article_entities(article, catalog, resolver, preview=True)
    related = pick_editorial(article, root, editorial_related)
    return rail(headings, [
        card("کاوش در پژوهش‌ها", related, "/articles.html",
             empty="پژوهش مرتبطی ثبت نشده است."),
        card("کاوش در اطلس", atlas, "/atlas/",
             empty="مدخل مرتبطی ثبت نشده است."),
    ], context="این پژوهش")


def atlas_rail(entity_id, claims, entities, relation_contract, resolver,
               render_relation, research_index, headings):
    research = pick_research(research_index, entity_id)
    related = pick_related_entities(entity_id, claims, entities, relation_contract,
                                    resolver, render_relation, preview=True)
    return rail(headings, [
        card("کاوش در اطلس", related, "/atlas/",
             empty="رابطهٔ قابل نمایش ثبت نشده است."),
        card("کاوش در پژوهش‌ها", research, "/articles.html",
             empty="پژوهش مرتبطی ثبت نشده است."),
    ], context="اطلس")
