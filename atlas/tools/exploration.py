"""Shared exploration presentation over existing Research/Atlas contracts.

The selectors are pure and can be reused when a public presentation is approved.
Navigation uses explicit editorial links and confirmed primary Entity equality;
no title inference or similarity-based association is created here.
"""

import hashlib
import html
import re
import importlib.util
from pathlib import Path

_search_spec = importlib.util.spec_from_file_location("kaavosh_markup", Path(__file__).resolve().parents[2] / "tools/kaavosh_markup.py")
search_markup = importlib.util.module_from_spec(_search_spec)
_search_spec.loader.exec_module(search_markup)
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


def pick_research(index, entity_id, *, preview=False):
    """The generated reverse index already enforces publication and routes."""
    return [
        {"url": row["url"], "title": row["title"],
         "meta": "نمونهٔ نمایشی؛ فقط در preview" if row.get("previewFixture") else ""}
        for row in (index or {}).get("entities", {}).get(entity_id, [])
        if preview or not row.get("previewFixture")
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
            '<li><a href="' + esc(item["url"]) + '">'
            + (f'<small class="explore-item-relation">{esc(item["meta"])}</small>' if item.get("meta") else '')
            + '<span class="explore-item-title">' + esc(item["title"]) + '</span>'
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
            '<div class="explore-rail-inner">' + search_markup.search_form(compact=True) + '<div class="explore-toc">'
            '<h2>راهنمای مطالعه</h2>' + toc_nav(headings) + '</div>'
            + toc_nav(headings, mobile=True) + ''.join(cards) + '</div></aside>')


def research_rail(article, catalog, root, resolver, editorial_related, headings, *, preview=False):
    atlas = pick_article_entities(article, catalog, resolver, preview=preview)
    related = pick_editorial(article, root, editorial_related)
    return rail(headings, [
        card("کاوش در پژوهش‌ها", related, "/articles.html",
             empty="پژوهش مرتبطی ثبت نشده است."),
        card("کاوش در اطلس", atlas, "/atlas/",
             empty="مدخل مرتبطی ثبت نشده است."),
    ], context="این پژوهش")


def atlas_rail(entity_id, claims, entities, relation_contract, resolver,
               render_relation, research_index, headings, *, preview=False):
    research = pick_research(research_index, entity_id, preview=preview)
    related = pick_related_entities(entity_id, claims, entities, relation_contract,
                                    resolver, render_relation, preview=preview)
    return rail(headings, [
        card("کاوش در اطلس", related, "/atlas/",
             empty="رابطهٔ قابل نمایش ثبت نشده است."),
        card("کاوش در پژوهش‌ها", research, "/articles.html",
             empty="پژوهش مرتبطی ثبت نشده است."),
    ], context="اطلس")


def research_page(page, article, catalog, root, resolver, editorial_related, *, preview=False):
    """Build a shared reading layout; public cards always filter unpublished Entities.

    Explicit layout markers allow a repeat build or an isolated preview to replace
    the generated rail without wrapping the article a second time.
    """
    layout = re.compile(
        r'<div class="explore-reading-layout" data-research-exploration>'
        r'<article class="explore-reading">(.*?)</article>'
        r'.*?</div><!-- research-exploration -->', re.S,
    )
    page = layout.sub(lambda match: '<article>' + match.group(1) + '</article>', page)
    connections = re.compile(
        r'<div data-research-connections>.*?</div><!-- research-connections -->', re.S,
    )
    page = connections.sub('', page)
    start, end = page.find('<article>'), page.find('</article>')
    if start < 0 or end < start:
        raise ValueError(f"{article['id']}: article element missing")
    body, headings = article_toc(page[start + len('<article>'):end])
    cards = research_rail(article, catalog, root, resolver, editorial_related, headings, preview=preview)
    if not preview:
        cards = '<div data-research-connections>' + cards + '</div><!-- research-connections -->'
    composed = ('<div class="explore-reading-layout" data-research-exploration>'
                '<article class="explore-reading">' + body + '</article>' + cards
                + '</div><!-- research-exploration -->')
    page = page[:start] + composed + page[end + len('</article>'):]
    search_style = '<link rel="stylesheet" href="/assets/css/kaavosh.css">'
    if search_style not in page:page=page.replace('</head>',search_style+'\n</head>',1)
    style = '<link rel="stylesheet" href="/assets/css/exploration.css">'
    if style not in page:
        page = page.replace('</head>', style + '\n</head>', 1)
    return page


def atlas_page(page, entity_id, claims, entities, relation_contract, resolver,
               render_relation, research_index, *, preview=False):
    """Compose the same Entity layout for public builds and isolated previews."""
    layout = re.compile(
        r'<div class="explore-reading-layout atlas-reading-layout" data-atlas-exploration>'
        r'<div class="atlas-primary">(.*?)</div><aside.*?</div><!-- atlas-exploration -->',
        re.S,
    )
    page = layout.sub(lambda match: match.group(1), page)
    hero = page.find('<section class="page-hero">')
    hero_end = page.find('</section>', hero)
    root_end = page.find('\n</div>\n\n</main>', hero_end)
    if hero < 0 or hero_end < 0 or root_end < 0:
        raise ValueError(f"{entity_id}: Atlas root/hero contract missing")
    hero_end += len('</section>')
    content, headings = article_toc(page[hero_end:root_end], levels=(2,), prefix="atlas")
    cards = atlas_rail(entity_id, claims, entities, relation_contract, resolver,
                       render_relation, research_index, headings, preview=preview)
    composed = ('<div class="explore-reading-layout atlas-reading-layout" data-atlas-exploration>'
                '<div class="atlas-primary">' + content + '</div>' + cards
                + '</div><!-- atlas-exploration -->')
    page = page[:hero_end] + composed + page[root_end:]
    search_style = '<link rel="stylesheet" href="/assets/css/kaavosh.css">'
    if search_style not in page:page=page.replace('</head>',search_style+'\n</head>',1)
    style = '<link rel="stylesheet" href="/assets/css/exploration.css">'
    if style not in page:
        page = page.replace('</head>', style + '\n</head>', 1)
    return page
