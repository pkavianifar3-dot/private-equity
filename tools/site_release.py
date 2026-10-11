"""Build and inspect a compatibility candidate; never grant publication permission.

Canonical inputs remain in Atlas/Research. The site policy is a packaging and
URL inventory, not another content store. REVIEW survives locally while ADR-004
cutover is deferred; the separate publication gate refuses those bytes.
"""
from collections import Counter, defaultdict
from datetime import datetime
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET
import json
import re
import public_projection

ORIGIN = "https://privatecapital.ir"
ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ROUTES = {"Person": "person", "Organization": "organization", "Investment": "investment", "Concept": "concept"}
DATA_DIRS = {"Person": "persons", "Organization": "organizations", "Investment": "investments", "Concept": "concepts"}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def policy(root):
    return read_json(root / "tools/release/site-policy.json")


def safe_file(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative or ".." in PurePosixPath(relative).parts or relative.startswith("/"):
        raise ValueError(f"Unsafe package path: {relative!r}")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or any(p.is_symlink() for p in (path, *path.parents) if p.is_relative_to(root)):
        raise ValueError(f"Package path escapes root or is a symlink: {relative}")
    if not path.is_file():
        raise ValueError(f"Required runtime file missing: {relative}")
    return path


def url_file(url):
    path = unquote(urlsplit(url).path)
    if not path.startswith("/") or ".." in PurePosixPath(path).parts or "\\" in path:
        raise ValueError(f"Unsafe site URL: {url!r}")
    return path.lstrip("/") + ("index.html" if path.endswith("/") else "")


def page_url(relative):
    return "/" + (relative[:-10] if relative.endswith("index.html") else relative)


def local_url(reference, owner):
    absolute = urlsplit(urljoin(ORIGIN + owner, reference))
    if absolute.netloc != urlsplit(ORIGIN).netloc or absolute.scheme not in ("http", "https"):
        return None
    return absolute.path + ("?" + absolute.query if absolute.query else "") + ("#" + absolute.fragment if absolute.fragment else "")


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.canonicals, self.robots, self.links, self.assets, self.ids, self.research_sources = [], [], [], [], [], []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.append(a["id"])
        if tag == "link" and "canonical" in a.get("rel", "").split():
            self.canonicals.append(a.get("href", ""))
        if tag == "meta" and a.get("name", "").lower() in ("robots", "googlebot"):
            self.robots.append(a.get("content", "").lower())
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        if tag in ("img", "script", "source", "iframe") and a.get("src"):
            self.assets.append(a["src"])
        if tag in ("img", "source") and a.get("srcset"):
            self.assets.extend(x.strip().split()[0] for x in a["srcset"].split(",") if x.strip())
        if tag == "link" and a.get("href") and "canonical" not in a.get("rel", ""):
            self.assets.append(a["href"])
        if tag == "meta" and a.get("property") in ("og:image", "og:video") and a.get("content"):
            self.assets.append(a["content"])
        if a.get("data-research-source"):
            self.research_sources.append(a["data-research-source"])


def articles(root):
    records = read_json(root / "research/index.json")["research"]
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("research/index.json: duplicate Research IDs")
    result = [r for r in records if r["status"] == "PUBLISHED"]
    if len({r["url"] for r in result}) != len(result):
        raise ValueError("research/index.json: duplicate published URLs")
    for record in result:
        path = url_file(record["url"])
        if not path.startswith("articles/") or not path.endswith(".html") or urlsplit(record["url"]).query or urlsplit(record["url"]).fragment:
            raise ValueError(f"{record['id']}: invalid public Research URL {record['url']}")
        safe_file(root, path)
    return result


def runtime_paths(root, config):
    """Exact index closure for the existing legacy JS Entity renderer.

    These complete indexes intentionally contain REVIEW until an approved
    projection/cutover. Source/Claim/Evidence file names come from generated
    indexes, not a recursive directory copy.
    """
    result = {"atlas/catalog/index.json", "atlas/entities/index.json"}
    entities = read_json(root / "atlas/entities/index.json")["entities"]
    for entity in entities:
        if entity["type"] in ROUTES:
            slug = entity["id"].split(":", 1)[1]
            result.add(f"atlas/entities/{DATA_DIRS[entity['type']]}/{slug}.json")
            if entity["type"] == "Person":
                result.add(f"atlas/content/persons/{slug}.json")
    for family in ("claims", "evidence", "sources"):
        index_path = f"atlas/{family}/index.json"
        result.add(index_path)
        index = read_json(root / index_path)
        for filename in index[family].values():
            if not isinstance(filename, str) or PurePosixPath(filename).name != filename or not filename.endswith(".json"):
                raise ValueError(f"{index_path}: unsafe runtime filename {filename!r}")
            result.add(f"atlas/{family}/{filename}")
    result.update(f"atlas/taxonomies/{name}.json" for name in ("relation-types", "relation-rules", "relation-rendering"))
    for relative in result:
        safe_file(root, relative)
    return result


def asset_allowed(relative):
    p = PurePosixPath(relative)
    if relative.startswith("assets/css/"):
        return p.suffix == ".css"
    if relative.startswith("assets/js/"):
        return p.suffix == ".js"
    if relative.startswith("assets/images/"):
        return p.suffix.lower() in (".png", ".jpg", ".jpeg", ".svg", ".webp", ".ico", ".webmanifest")
    return relative in ("assets/Vazirmatn-Regular.woff2", "assets/Vazirmatn-Bold.woff2")


def package_paths(root, public=False):
    config = policy(root)
    indexed = read_json(root / "atlas/entities/index.json")["entities"]
    for entity in indexed:
        if not public and entity["lifecycleStatus"] != "PUBLISHED" and entity["id"] not in config["legacy_review_entity_ids"]:
            raise ValueError(f"{entity['id']}: new non-public Entity exposure is not allowed in the compatibility candidate")
    result = {url_file(u) for u in config["pages"]}
    result.update(url_file(r["url"]) for r in articles(root))
    # Consume the actual catalog route; never invent a parallel release URL.
    for entity in read_json(root / "atlas/catalog/index.json")["entities"]:
        if entity["type"] in ROUTES and (entity["lifecycleStatus"] == "PUBLISHED" or entity["id"] in config["legacy_review_entity_ids"]):
            route = entity.get("route")
            if not route or not route.startswith(f"/atlas/{ROUTES[entity['type']]}/") or not route.endswith("/") or urlsplit(route).query or urlsplit(route).fragment:
                raise ValueError(f"{entity['id']}: missing or invalid approved catalog route {route!r}")
            result.add(url_file(route))
    result.update(runtime_paths(root, config))
    result.update(("CNAME", "robots.txt", "sitemap.xml"))
    queue = list(sorted(result))
    while queue:
        relative = queue.pop()
        path = safe_file(root, relative)
        refs = []
        if path.suffix == ".html":
            document = Page(path.read_text(encoding="utf-8"))
            if document.research_sources:
                raise ValueError(f"{relative}: public article fetches internal Research source {document.research_sources}")
            refs = document.assets
        elif path.suffix == ".css":
            text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
            refs = re.findall(r"url\(\s*['\"]?([^)'\"\s]+)", text)
            refs += re.findall(r"@import\s+['\"]([^'\"]+)", text)
        elif path.suffix == ".webmanifest":
            refs = [icon["src"] for icon in read_json(path).get("icons", [])]
        for ref in refs:
            url = local_url(ref, "/" + relative)
            if url is None:
                continue
            asset = url_file(url)
            if not asset_allowed(asset):
                raise ValueError(f"{relative}: runtime reference outside asset allowlist: {ref}")
            safe_file(root, asset)
            if asset not in result:
                result.add(asset)
                queue.append(asset)
    if public:
        overrides = public_projection.overrides(root)
        _, excluded = public_projection.private_paths(root)
        result.difference_update(excluded)
        # Each family index and file is regenerated as a closed snapshot.
        result = {p for p in result if not any(p.startswith('atlas/'+f+'/') for f in ('claims','evidence','sources'))}
        result.update(overrides)
    return sorted(result)


def digest_files(root, paths):
    return {p: sha256(safe_file(root, p).read_bytes()).hexdigest() for p in sorted(paths)}


def package(root, output, public=False):
    output = output.resolve()
    if output.is_relative_to(root.resolve()) or root.resolve().is_relative_to(output) or output.is_symlink():
        raise ValueError("Artifact directory must be isolated from the repository root")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Artifact directory is not empty; use a fresh directory: {output}")
    paths = package_paths(root, public=public)
    overrides = public_projection.overrides(root) if public else {}
    output.mkdir(parents=True, exist_ok=True)
    for relative in paths:
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        # Text line endings must not depend on Git's Windows checkout settings.
        data = overrides.get(relative)
        if data is None:
            data = safe_file(root, relative).read_bytes()
        if Path(relative).suffix in (".html", ".css", ".js", ".json", ".xml", ".txt", ".webmanifest") or relative == "CNAME":
            data = data.replace(b"\r\n", b"\n")
        target.write_bytes(data)
    return paths


def content_dates(root):
    dates = {}
    for path in sorted((root / "research/content").rglob("research.json")):
        record = read_json(path)
        seo = record.get("publication", {})
        raw = seo.get("dateModified") or seo.get("datePublished")
        if raw:
            try:
                dates[record["id"]] = datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
            except ValueError as error:
                raise ValueError(f"{path}: invalid editorial date {raw}") from error
    return dates


def sitemap_text(root):
    config = policy(root)
    urls = {u: None for u in config["sitemap_pages"]}
    dates = content_dates(root)
    for article in articles(root):
        if article.get("sourceMode") == "legacy-html":
            text = safe_file(root, url_file(article["url"])).read_text(encoding="utf-8")
            for raw in re.findall(r'<script[^>]+type=[\'\"]application/ld\+json[\'\"][^>]*>(.*?)</script>', text, re.S):
                data = json.loads(raw)
                date = data.get("dateModified") or data.get("datePublished") if isinstance(data, dict) else None
                if date:
                    dates[article["id"]] = datetime.fromisoformat(date.replace("Z", "+00:00")).date().isoformat()
        urls[article["url"]] = dates.get(article["id"])
    for entity in read_json(root / "atlas/catalog/index.json")["entities"]:
        if entity["lifecycleStatus"] == "PUBLISHED" and entity.get("route"):
            if entity.get("type") not in ROUTES:
                raise ValueError(f"{entity['id']}: no approved public Entity type for sitemap")
            urls[entity["route"]] = None
    ET.register_namespace("", NS)
    document = ET.Element(f"{{{NS}}}urlset")
    for url, date in sorted(urls.items()):
        target = safe_file(root, url_file(url))
        page = Page(target.read_text(encoding="utf-8"))
        if any("noindex" in r for r in page.robots) or page.canonicals != [ORIGIN + url]:
            raise ValueError(f"{target.relative_to(root)}: sitemap target must be indexable and self-canonical: {page.canonicals}")
        element = ET.SubElement(document, f"{{{NS}}}url")
        ET.SubElement(element, f"{{{NS}}}loc").text = ORIGIN + url
        if date:
            ET.SubElement(element, f"{{{NS}}}lastmod").text = date
    ET.indent(document, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(document, encoding="unicode") + "\n"


def check_artifact(root, output, public=False):
    """Check the actual bytes to be uploaded, including link/asset closure."""
    expected = set(package_paths(root, public=public))
    overrides = public_projection.overrides(root) if public else {}
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()}
    errors = []
    if actual != expected:
        errors.append(f"Artifact allowlist differs: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}")
    for path in output.rglob("*"):
        if path.is_symlink():
            errors.append(f"Artifact symlink is forbidden: {path.relative_to(output)}")
    pages = {p: Page((output / p).read_text(encoding="utf-8")) for p in sorted(actual) if p.endswith(".html")}
    config = policy(root)
    dynamic = set(config["dynamic_templates"])
    aliases = config["canonical_aliases"]
    checks = 0
    for relative, page in pages.items():
        url = page_url(relative)
        if relative == "404.html":
            if not any("noindex" in r for r in page.robots):
                errors.append("404.html: error document must be noindex")
        elif url not in dynamic:
            target = aliases.get(url, url)
            if page.canonicals != [ORIGIN + target]:
                errors.append(f"{relative}: canonical mismatch: {page.canonicals}; expected {ORIGIN+target}")
        if relative != "404.html" and any("noindex" in r for r in page.robots):
            errors.append(f"{relative}: preview/noindex leaked into production candidate")
        if len(page.ids) != len(set(page.ids)):
            errors.append(f"{relative}: duplicate HTML IDs")
        if page.research_sources:
            errors.append(f"{relative}: runtime requests internal Research package")
        for reference in page.links + page.assets:
            local = local_url(reference, "/" + relative)
            if local is None:
                continue
            parsed = urlsplit(local)
            target_file = url_file(local)
            checks += 1
            if target_file not in actual:
                errors.append(f"{relative}: missing internal target {reference} -> {target_file}")
            elif parsed.fragment and target_file in pages and parsed.fragment not in pages[target_file].ids:
                # Empty '#' is already ignored; legacy query pages generate their IDs in JS.
                if "/" + target_file not in dynamic:
                    errors.append(f"{relative}: missing anchor {reference}")
    if (output / "CNAME").read_text(encoding="utf-8").strip() != urlsplit(ORIGIN).netloc:
        errors.append("CNAME differs from the approved custom domain")
    robots = (output / "robots.txt").read_text(encoding="utf-8")
    if f"Sitemap: {ORIGIN}/sitemap.xml" not in robots or re.search(r"(?im)^Disallow:\s*/\s*$", robots):
        errors.append("robots.txt is inconsistent with the production site")
    if (output / "sitemap.xml").read_text(encoding="utf-8") != sitemap_text(root):
        errors.append("sitemap.xml: deterministic output drift")
    seen = set()
    for element in ET.fromstring((output / "sitemap.xml").read_text(encoding="utf-8")).findall(f"{{{NS}}}url"):
        loc = element.findtext(f"{{{NS}}}loc")
        if loc in seen:
            errors.append(f"sitemap.xml: duplicate {loc}")
        seen.add(loc)
        parsed = urlsplit(loc)
        file = url_file(loc)
        if parsed.scheme != "https" or parsed.netloc != urlsplit(ORIGIN).netloc or file not in pages or pages[file].canonicals != [loc]:
            errors.append(f"sitemap.xml: missing/wrong canonical target {loc}")
        elif any("noindex" in r for r in pages[file].robots):
            errors.append(f"sitemap.xml: non-indexable URL {loc}")
    for relative in actual:
        if "_preview" in relative or "__preview" in relative or "editorial-review" in relative:
            errors.append(f"Forbidden preview/editorial artifact: {relative}")
        if relative.endswith(".html"):
            text = (output / relative).read_text(encoding="utf-8")
            if re.search(r"(?:/__preview/|/atlas/_preview/|preview-url-resolver\.js|data-exploration-preview)", text):
                errors.append(f"{relative}: preview-only route/component leaked")
    # JSON closure is recomputed from the indexes INSIDE the artifact, so index
    # corruption cannot be hidden by the source repository's valid data.
    try:
        for relative in runtime_paths(output, config):
            checks += 1
            if relative not in actual:
                errors.append(f"Runtime dependency missing: {relative}")
    except (ValueError, KeyError, FileNotFoundError) as error:
        errors.append(str(error))
    # Detect tampering between verification and upload. This is also useful on
    # Windows, where the source checkout may use CRLF and the artifact uses LF.
    for relative in sorted(expected & actual):
        source = overrides.get(relative)
        if source is None:
            source = safe_file(root, relative).read_bytes()
        if Path(relative).suffix in (".html", ".css", ".js", ".json", ".xml", ".txt", ".webmanifest") or relative == "CNAME":
            source = source.replace(b"\r\n", b"\n")
        if (output / relative).read_bytes() != source:
            errors.append(f"Artifact bytes differ from validated source: {relative}")
    if errors:
        raise ValueError("Release checks failed:\n" + "\n".join(sorted(set(errors))))
    return dict(files=len(actual), pages=len(pages), sitemap_urls=len(seen), link_and_runtime_checks=checks)


def publication_blockers(root, output):
    """Fail closed. A compatibility allowlist is never publication approval."""
    blockers = []
    for relative in ("atlas/entities/index.json", "atlas/catalog/index.json"):
        for entity in read_json(output / relative)["entities"]:
            if entity.get("lifecycleStatus") != "PUBLISHED":
                blockers.append(f"{relative}: {entity['id']} is {entity.get('lifecycleStatus')}; ADR-004 migration approval required")
            if entity.get("type") not in ROUTES:
                blockers.append(f"{relative}: {entity['id']} ({entity.get('type')}) has no approved public Entity route")
    for article in read_json(root / "research/index.json")["research"]:
        if article.get("status") != "PUBLISHED" and (output / url_file(article["url"])).exists():
            blockers.append(f"{article['id']}: unpublished Research page in artifact")
    blockers.extend(public_projection.check(root, output))
    return sorted(set(blockers))


def inventory(root):
    config = policy(root)
    paths = package_paths(root)
    pages = {p: Page((root / p).read_text(encoding="utf-8")) for p in paths if p.endswith(".html")}
    inbound = defaultdict(set)
    for relative, page in pages.items():
        for ref in page.links:
            url = local_url(ref, "/" + relative)
            if url:
                inbound[page_url(url_file(url))].add(page_url(relative))
    sitemap_urls = {e.text for e in ET.fromstring(sitemap_text(root)).findall(f".//{{{NS}}}loc")}
    by_route = {e.get("route"): e for e in read_json(root / "atlas/catalog/index.json")["entities"] if e.get("route")}
    for route in by_route:
        inbound[route].update(("/atlas/ (catalog runtime)", "/atlas/explore/ (catalog runtime)"))
    result = []
    for relative, page in sorted(pages.items()):
        url = page_url(relative)
        entity = by_route.get(url)
        review = entity and entity["lifecycleStatus"] == "REVIEW"
        result.append(dict(url=url, file=relative, entity=entity["id"] if entity else None,
                           status=entity["lifecycleStatus"] if entity else "existing-public-page",
                           canonical=page.canonicals[0] if page.canonicals else "runtime-only" if url in config["dynamic_templates"] else None,
                           inbound_links=sorted(inbound[url]), in_sitemap=ORIGIN+url in sitemap_urls,
                           indexability="noindex" if any("noindex" in x for x in page.robots) else "indexable (legacy boundary deferred)",
                           proposal="REMOVE from public artifact / 404; retain canonical and local review page" if review else "KEEP",
                           risk="Existing Research/Atlas links and JSON consumers depend on this address" if review else "Preserve canonical and navigation",
                           required_test="HTTP + canonical + inbound links + runtime + publication gate"))
    # Query entry points still work and set canonical SEO in Atlas JS. They are
    # compatibility addresses, not another static Entity route map.
    for route, entity in sorted(by_route.items()):
        kind = ROUTES[entity["type"]]
        result.append(dict(url=f"/atlas/{kind}.html?id={entity['id']}", file=f"atlas/{kind}.html",
                           entity=entity["id"], status=entity["lifecycleStatus"], canonical=ORIGIN+route,
                           inbound_links=[], in_sitemap=False, indexability="runtime canonical",
                           proposal="SAFE NOT-FOUND / noindex; HTTP 200 shell limitation" if entity["lifecycleStatus"] != "PUBLISHED" else "KEEP legacy query compatibility",
                           risk="Shared shell may return HTTP 200; no Entity data or canonical is delivered" if entity["lifecycleStatus"] != "PUBLISHED" else "Reuses reviewed static content from the closed public index",
                           required_test="Browser query render and canonical -> static Entity URL"))
    return result


def inventory_markdown(root):
    rows = inventory(root)
    lines = ["# Stage 5 URL disposition matrix", "", "Generated from canonical/local routes. Public projection is approved locally; deployment remains disabled. REVIEW static routes and aliases are omitted from the public artifact, not deleted from canonical data.", "",
             "The sitemap includes PUBLISHED routed Entities only. REVIEW pages remain local; their static URLs return 404 in the isolated public artifact. Shared legacy query shells return a safe not-found view with noindex; their HTTP response can remain 200.", "",
             "| URL / Entity | Current status | Canonical / destination | Inbound pages | Sitemap / indexing | Proposal | Compatibility risk / required test |",
             "| --- | --- | --- | --- | --- | --- | --- |"]
    for row in rows:
        inbound = ", ".join(row["inbound_links"]) or "—"
        alias = f"<br>Existing file alias: `/{row['file']}`" if row["file"].endswith("index.html") else ""
        lines.append(f"| `{row['url']}`{alias}<br>{row['entity'] or '—'} | {row['status']} | {row['canonical'] or '—'} | {inbound} | {'yes' if row['in_sitemap'] else 'no'} / {row['indexability']} | {row['proposal']} | {row['risk']}<br>{row['required_test']} |")
    lines += ["", "## Local projection implemented; production activation pending", "",
              "1. Selective editorial approval is implemented locally: 12 PUBLISHED Entities; 15 REVIEW records remain internal.",
              "2. Existing approved URLs are preserved; withheld static URLs and aliases are omitted / 404. No redirects are introduced.",
              "3. Research links and reverse indexes use approved Entities; legacy private queries show a generic noindex not-found view.",
              "4. The release CLI builds a closed public projection; canonical data and historical revisions remain complete internally.",
              "5. Local validation, tests, link checks, drift, publication gate and HTTP checks passed; current-change remote CI and production activation remain pending.",
              "6. Atlas exploration rail stays local-only unless explicitly approved for public use.", ""]
    return "\n".join(lines)
