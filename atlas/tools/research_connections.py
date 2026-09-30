"""Publication-aware, article-level Research ↔ Atlas projections.

Research content owns entityRefs; relatedResearchRefs is an independent,
editorial Research → Research reference. Mentions are text occurrences and do
not contribute to this index. Preview projections are never written publicly.
"""

import html
import json
from pathlib import PurePosixPath
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "atlas/discovery/research-by-entity.json"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value):
    return html.escape(str(value or ""), quote=True)


def article_path(root, url, owner):
    """Resolve an existing public article URL without escaping the site tree."""
    if (
        not isinstance(url, str)
        or not url.startswith("/articles/")
        or not url.endswith(".html")
        or ".." in PurePosixPath(url).parts
        or "\\" in url
        or "?" in url
        or "#" in url
    ):
        raise ValueError(f"{owner}: invalid Research URL {url}")
    target = (root / url.lstrip("/")).resolve()
    if not target.is_relative_to((root / "articles").resolve()):
        raise ValueError(f"{owner}: Research URL escapes articles: {url}")
    if not target.is_file():
        raise ValueError(f"{owner}: Research page missing: {url}")
    return target


def published_registry(root):
    entries = read_json(root / "research/index.json")["research"]
    by_id = {}
    for entry in entries:
        if entry["id"] in by_id:
            raise ValueError(f"research/index.json: duplicate {entry['id']}")
        by_id[entry["id"]] = entry
    return by_id


def structured_articles(root):
    articles = {}
    for path in sorted((root / "research/content").glob("*.json")):
        article = read_json(path)
        article_id = article["id"]
        if article_id in articles:
            raise ValueError(f"{path}: duplicate Research ID {article_id}")
        articles[article_id] = article
    return articles


def eligible_articles(root):
    registry = published_registry(root)
    articles = structured_articles(root)
    for article_id, article in sorted(articles.items()):
        entry = registry.get(article_id)
        if entry is None:
            raise ValueError(f"research/content/{article_id}: missing registry entry")
        if article.get("status") != "PUBLISHED" or entry.get("status") != "PUBLISHED":
            continue
        url = article.get("url")
        if url != entry.get("url"):
            raise ValueError(f"{article_id}: published Research URL differs from registry")
        article_path(root, url, article_id)
        yield article


def entity_route(entity, preview=False, preview_resolver=None):
    if entity.get("lifecycleStatus") != "PUBLISHED" and not preview:
        return None
    if preview and preview_resolver:
        return preview_resolver(entity["id"], entity["type"])
    return entity.get("route")


def reverse_index(root, catalog, *, preview=False, preview_resolver=None):
    by_id = {item["id"]: item for item in catalog}
    result = {}
    for article in eligible_articles(root):
        article_id = article["id"]
        item = {
            "id": article_id,
            "url": article["url"],
            "title": article["title"]["fa"],
            "datePublished": article["publication"]["datePublished"],
        }
        for entity_id in sorted(set(article.get("entityRefs", []))):
            entity = by_id.get(entity_id)
            if entity is None:
                raise ValueError(f"{article_id}: entityRefs has missing Entity {entity_id}")
            if entity_route(entity, preview, preview_resolver):
                result.setdefault(entity_id, []).append(item)
    return {
        "version": "1.0",
        "entities": {
            entity_id: sorted(items, key=lambda item: item["id"])
            for entity_id, items in sorted(result.items())
        },
    }


def render_atlas_research(entity_id, index):
    articles = index["entities"].get(entity_id, [])
    if not articles:
        return ""
    entries = "\n".join(
        f'<li><a href="{esc(item["url"])}">{esc(item["title"])}</a>'
        '<span class="knowledge-connection-meta">پژوهش و تحلیل</span></li>'
        for item in articles
    )
    return (
        '<section class="atlas-section atlas-research-section" aria-labelledby="related-research-heading">'
        '<div class="container"><div class="knowledge-connection">'
        '<p class="atlas-kicker">پژوهش</p><h2 id="related-research-heading">تحلیل‌های مرتبط</h2>'
        '<p>روایت و بررسی پژوهشی درباره این موجودیت</p>'
        f'<ul class="knowledge-connection-list">{entries}</ul>'
        '</div></div></section>'
    )


class FirstHeading(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inside = False
        self.parts = []
        self.done = False

    def handle_starttag(self, tag, attrs):
        if tag == "h1" and not self.done:
            self.inside = True

    def handle_endtag(self, tag):
        if tag == "h1" and self.inside:
            self.inside = False
            self.done = True

    def handle_data(self, data):
        if self.inside:
            self.parts.append(data)


def editorial_related(article, root):
    """Curated Research → Research links; never feed the Entity reverse index."""
    registry = published_registry(root)
    structured = structured_articles(root)
    result = []
    for ref in dict.fromkeys(article.get("relatedResearchRefs", [])):
        target = registry.get(ref)
        if target is None:
            raise ValueError(f"{article['id']}: relatedResearchRefs missing {ref}")
        if target.get("status") != "PUBLISHED":
            continue
        other = structured.get(ref)
        if other and other.get("status") != "PUBLISHED":
            continue
        url = target.get("url", "")
        path = article_path(root, url, article["id"])
        if other and other.get("url") != url:
            raise ValueError(f"{article['id']}: related Research URL differs from {ref}")
        if other:
            title = other["title"]["fa"]
        else:
            parser = FirstHeading()
            parser.feed(path.read_text(encoding="utf-8"))
            title = "".join(parser.parts).strip()
            if not title:
                raise ValueError(f"{article['id']}: related Research page has no title {url}")
        result.append({"url": url, "title": title})
    return result


def render_article_context(article, catalog, root, *, preview=False, preview_resolver=None):
    by_id = {item["id"]: item for item in catalog}
    entities = []
    for entity_id in dict.fromkeys(article.get("entityRefs", [])):
        entity = by_id.get(entity_id)
        if entity is None:
            raise ValueError(f"{article['id']}: entityRefs has missing Entity {entity_id}")
        route = entity_route(entity, preview, preview_resolver)
        if route:
            entities.append((entity, route))
    related = editorial_related(article, root)
    if not entities and not related:
        return ""
    blocks = []
    if entities:
        items = "\n".join(
            f'<li><a href="{esc(route)}">{esc(entity["name"]["fa"])}</a>'
            f'<span class="knowledge-connection-meta">{esc(entity["name"].get("en"))}</span></li>'
            for entity, route in entities
        )
        blocks.append('<div class="knowledge-connection"><p class="atlas-kicker">اطلس</p>'
                      '<h2 id="research-atlas-heading">موجودیت‌های این پژوهش</h2>'
                      '<p>مدخل‌های مرجع برای شناخت مفاهیم و موجودیت‌های این مقاله</p>'
                      f'<ul class="knowledge-connection-list">{items}</ul></div>')
    if related:
        items = "\n".join(
            f'<li><a href="{esc(item["url"])}">{esc(item["title"])}</a></li>'
            for item in related
        )
        blocks.append('<div class="knowledge-connection"><p class="atlas-kicker">ادامه مطالعه</p>'
                      '<h2 id="research-related-heading">پژوهش‌های مرتبط</h2>'
                      f'<ul class="knowledge-connection-list">{items}</ul></div>')
    return '<aside class="research-connections" aria-label="مسیرهای مطالعه مرتبط">' + "\n".join(blocks) + '</aside>'
