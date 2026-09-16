import html
import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[1]

ENTITIES_DIR = ROOT / "entities"
CLAIMS_DIR = ROOT / "claims"
EVIDENCE_DIR = ROOT / "evidence"
SOURCES_DIR = ROOT / "sources"
CONTENT_DIR = ROOT / "content"

OUTPUT_ROOT = ROOT

SITE_ORIGIN = "https://privatecapital.ir"

ROUTES = {
    "Person": "person",
    "Organization": "organization",
    "Investment": "investment",
    "Concept": "concept",
}


def load_json(path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def esc(value):
    return html.escape("" if value is None else str(value), quote=True)


def entity_url(entity_id, entity_type=None):
    if not entity_id or ":" not in entity_id:
        return None

    _, slug = entity_id.split(":", 1)

    if not slug or not entity_type:
        return None

    route = ROUTES.get(entity_type)

    if not route:
        return None

    return f"/atlas/{route}/{quote(slug, safe='')}/"


def entity_canonical_url(entity_id, entity_type=None):
    url = entity_url(entity_id, entity_type)

    if not url:
        return None

    return f"{SITE_ORIGIN}{url}"


def load_entities():
    entities = {}

    for path in sorted(ENTITIES_DIR.rglob("*.json")):
        if path == ENTITIES_DIR / "index.json":
            continue

        data = load_json(path)
        entity_id = data.get("id")

        if entity_id:
            entities[entity_id] = data

    return entities


def load_claims():
    claims = []

    for path in sorted(CLAIMS_DIR.glob("*.json")):
        if path.name == "index.json":
            continue

        data = load_json(path)

        for claim in data.get("claims", []):
            claims.append(claim)

    return claims


def load_evidence():
    evidence = {}

    for path in sorted(EVIDENCE_DIR.glob("*.json")):
        if path.name == "index.json":
            continue

        data = load_json(path)

        for item in data.get("evidence", []):
            if item.get("id"):
                evidence[item["id"]] = item

    return evidence


def load_sources():
    sources = {}

    for path in sorted(SOURCES_DIR.glob("*.json")):
        if path.name == "index.json":
            continue

        data = load_json(path)

        for item in data.get("sources", []):
            if item.get("id"):
                sources[item["id"]] = item

    return sources


def load_content(entity):
    entity_id = entity.get("id", "")

    if not entity_id.startswith("person:"):
        return None

    slug = entity_id.split(":", 1)[1]
    path = CONTENT_DIR / "persons" / f"{slug}.json"

    if not path.exists():
        return None

    return load_json(path)


def entity_name(entity):
    name = entity.get("name", {})

    if isinstance(name, dict):
        return name.get("fa") or name.get("en") or entity.get("id", "")

    return str(name)


def entity_name_en(entity):
    name = entity.get("name", {})

    if isinstance(name, dict):
        return name.get("en")

    return None

def build_source_index(sources, claims, evidence, content=None):
    ordered_ids = []

    def add_source(source_id):
        if source_id in sources and source_id not in ordered_ids:
            ordered_ids.append(source_id)

    if content:
        for section in content.get("sections", []):
            for paragraph in section.get("paragraphs", []):
                for source_ref in paragraph.get("sourceRefs", []):
                    add_source(source_ref)

    for claim in claims:
        for evidence_ref in claim.get("evidenceRefs", []):
            item = evidence.get(evidence_ref)

            if not item:
                continue

            source_ref = item.get("sourceRef")

            if source_ref:
                add_source(source_ref)

    return {
        source_id: index
        for index, source_id in enumerate(ordered_ids, start=1)
    }

def relation_label(predicate):
    labels = {
        "CEO_OF": "مدیرعامل",
        "EXECUTIVE_ROLE_AT": "نقش اجرایی در",
        "WORKED_AT": "سابقه فعالیت در",
        "BOARD_MEMBER_OF": "عضو هیئت‌مدیره",
        "CHAIR_OF": "رئیس هیئت‌مدیره",
        "VICE_CHAIR_OF": "نایب‌رئیس هیئت‌مدیره",
        "BOARD_SECRETARY_OF": "دبیر هیئت‌مدیره",
        "REPRESENTED": "نماینده",
        "INVESTED_IN": "سرمایه‌گذاری در",
        "INVESTMENT_EXECUTIVE_OF": "مدیر سرمایه‌گذاری در",
        "MANAGES": "مدیریت",
        "SUBSIDIARY_OF": "زیرمجموعه",
        "PART_OF": "بخشی از",
        "BROADER_THAN": "مفهوم بالاتر",
        "RELATED_TO": "مرتبط با",
        "INCLUDES": "شامل",
        "HAS_NON_UNIFORM_CLASSIFICATION": "طبقه‌بندی",
        "CHARACTERIZED_BY": "مشخصه",
        "LINKED_TO": "ارتباط با",
        "HAS_INVESTOR_POSITION": "جایگاه سرمایه‌گذار",
        "RETURN_DEPENDS_ON": "وابستگی بازده",
        "INVESTMENT_AMOUNT": "مبلغ سرمایه‌گذاری",
    }

    return labels.get(predicate, predicate.replace("_", " "))


def claim_value_html(claim, entity_id, entities):
    subject_id = claim.get("subject")
    object_id = claim.get("object")

    if subject_id == entity_id:
        target_id = object_id
    elif object_id == entity_id:
        target_id = subject_id
    else:
        return ""

    if target_id and target_id in entities:
        target = entities[target_id]
        url = entity_url(target_id, target.get("type"))

        if url:
            return (
                f'<a href="{esc(url)}">'
                f'{esc(entity_name(target))}'
                f"</a>"
            )

        return esc(entity_name(target))

    value = claim.get("value")

    if value is None:
        return ""

    if isinstance(value, dict):
        raw = value.get("raw")

        if raw is not None:
            return esc(raw)

        return esc(json.dumps(value, ensure_ascii=False))

    return esc(value)


def render_claims(claims, entity_id, entities):
    if not claims:
        return ""

    items = []

    for claim in claims:
        predicate = claim.get("predicate", "")
        target = claim_value_html(claim, entity_id, entities)

        if not target:
            continue

        meta = []

        status = claim.get("status")
        confidence = claim.get("confidence")

        if status:
            meta.append(f"وضعیت: {esc(status)}")

        if confidence:
            meta.append(f"اطمینان: {esc(confidence)}")

        temporal = claim.get("temporal")

        if isinstance(temporal, dict):
            start = temporal.get("start")
            end = temporal.get("end")
            temporal_status = temporal.get("status")

            if start and end:
                meta.append(f"بازه: {esc(start)} تا {esc(end)}")
            elif start:
                meta.append(f"از: {esc(start)}")

            if temporal_status:
                meta.append(f"وضعیت زمانی: {esc(temporal_status)}")

        meta_html = ""

        if meta:
            meta_html = (
                '<p class="atlas-claim-meta">'
                + " | ".join(meta)
                + "</p>"
            )

        items.append(
            '<article class="card atlas-claim">'
            f'<div class="atlas-claim-label">'
            f'{esc(relation_label(predicate))}'
            "</div>"
            f"<h3>{target}</h3>"
            f"{meta_html}"
            "</article>"
        )

    if not items:
        return ""

    return (
        '<section class="atlas-section">'
        '<div class="container">'
        "<h2>ادعاها و روابط</h2>"
        '<div class="grid atlas-claims-grid">'
        + "".join(items)
        + "</div>"
        "</div>"
        "</section>"
    )


def render_content(content, source_index):
    if not content:
        return ""

    sections = []

    summary = content.get("summary")

    if summary:
        sections.append(
            '<section class="atlas-section">'
            '<div class="container">'
            '<div class="card atlas-summary">'
            f"<p>{esc(summary)}</p>"
            "</div>"
            "</div>"
            "</section>"
        )

    for section in content.get("sections", []):
        paragraphs = []

        for paragraph in section.get("paragraphs", []):
            text = paragraph.get("text", "")
            source_links = []

            for source_id in paragraph.get("sourceRefs", []):
                number = source_index.get(source_id)

                if not number:
                    continue

                source_links.append(
                    f'<a href="#source-{esc(source_id)}" '
                    f'class="atlas-source-ref" '
                    f'aria-label="ارجاع به منبع {number}">'
                    f'[{number}]</a>'
                )

            source_html = ""

            if source_links:
                source_html = (
                    '<span class="atlas-inline-sources">'
                    + " ".join(source_links)
                    + "</span>"
                )

            paragraphs.append(
                '<p class="atlas-content-paragraph">'
                f"{esc(text)}"
                f"{source_html}"
                "</p>"
            )

        if not paragraphs:
            continue

        title_fa = section.get("title_fa", "")
        title_en = section.get("title_en")

        title_html = ""

        if title_fa:
            title_html += f"<h2>{esc(title_fa)}</h2>"

        if title_en:
            title_html += (
                '<div class="atlas-section-en">'
                f"{esc(title_en)}"
                "</div>"
            )

        sections.append(
            '<section class="atlas-section">'
            '<div class="container">'
            '<article class="card atlas-content-section">'
            f"{title_html}"
            + "".join(paragraphs)
            + "</article>"
            "</div>"
            "</section>"
        )

    return "".join(sections)


def render_data_quality(content):
    if not content:
        return ""

    quality = content.get("data_quality")

    if not quality:
        return ""

    title = quality.get("title_fa", "وضعیت اعتبار اطلاعات")
    text = quality.get("text")

    if not text:
        return ""

    return (
        '<section class="atlas-section">'
        '<div class="container">'
        '<article class="card atlas-data-quality">'
        f"<h2>{esc(title)}</h2>"
        f"<p>{esc(text)}</p>"
        "</article>"
        "</div>"
        "</section>"
    )


def render_evidence(claims, evidence, sources):
    rows = []

    seen = set()

    for claim in claims:
        for ref in claim.get("evidenceRefs", []):
            if ref in seen:
                continue

            seen.add(ref)

            item = evidence.get(ref)

            if not item:
                continue

            source_ref = item.get("sourceRef")
            source = sources.get(source_ref) if source_ref else None

            details = []

            evidence_type = item.get("evidenceType")
            strength = item.get("strength")

            if evidence_type:
                details.append(
                    f"نوع: {esc(evidence_type)}"
                )

            if strength:
                details.append(
                    f"قدرت: {esc(strength)}"
                )

            if source:
                title = (
                    source.get("title_fa")
                    or source.get("title_en")
                    or source.get("publisher")
                    or source.get("id")
                )

                source_url = source.get("url")

                if source_url:
                    source_html = (
                        f'<a href="{esc(source_url)}" '
                        f'rel="noopener noreferrer">'
                        f"{esc(title)}</a>"
                    )
                else:
                    source_html = esc(title)

                details.append(
                    f"منبع: {source_html}"
                )

            rows.append(
                '<article class="card atlas-evidence">'
                '<div class="atlas-claim-label">'
                f"{esc(item.get('id', ref))}"
                "</div>"
                + (
                    "<p>" + " | ".join(details) + "</p>"
                    if details
                    else ""
                )
                + "</article>"
            )

    if not rows:
        return ""

    return (
        '<section class="atlas-section">'
        '<div class="container">'
        "<h2>شواهد و منابع</h2>"
        '<div class="grid atlas-claims-grid">'
        + "".join(rows)
        + "</div>"
        "</div>"
        "</section>"
    )


def render_sources(sources, claims, evidence, content=None):
    used_source_ids = []

    if content:
        for section in content.get("sections", []):
            for paragraph in section.get("paragraphs", []):
                for source_ref in paragraph.get("sourceRefs", []):
                    if source_ref in sources and source_ref not in used_source_ids:
                        used_source_ids.append(source_ref)

    for claim in claims:
        for evidence_ref in claim.get("evidenceRefs", []):
            item = evidence.get(evidence_ref)

            if not item:
                continue

            source_ref = item.get("sourceRef")

            if source_ref and source_ref in sources:
                if source_ref not in used_source_ids:
                    used_source_ids.append(source_ref)

    if not used_source_ids:
        return ""

    items = []

    for number, source_id in enumerate(used_source_ids, start=1):
        source = sources[source_id]

        title = (
            source.get("title_fa")
            or source.get("title_en")
            or source.get("publisher")
            or source_id
        )

        source_url = source.get("url")

        if source_url:
            source_body = (
                f'<a href="{esc(source_url)}" '
                f'rel="noopener noreferrer">'
                f"{esc(title)}</a>"
            )
        else:
            source_body = esc(title)

        items.append(
            '<article class="card atlas-source" '
            f'id="source-{esc(source_id)}">'
            f'<div class="atlas-source-number">[{number}]</div>'
            f"<h3>{source_body}</h3>"
            f'<p><span class="atlas-source-id">'
            f"{esc(source_id)}</span></p>"
            "</article>"
        )

    return (
        '<section class="atlas-section">'
        '<div class="container">'
        "<h2>منابع</h2>"
        '<div class="atlas-sources-list">'
        + "".join(items)
        + "</div>"
        "</div>"
        "</section>"
    )


def render_identity(entity):
    rows = []

    name_fa = entity_name(entity)
    name_en = entity_name_en(entity)

    rows.append(
        f"<div><strong>نام فارسی:</strong> {esc(name_fa)}</div>"
    )

    if name_en:
        rows.append(
            f"<div><strong>نام انگلیسی:</strong> {esc(name_en)}</div>"
        )

    aliases = entity.get("aliases") or []

    if aliases:
        rows.append(
            "<div><strong>نام‌های دیگر:</strong> "
            + ", ".join(esc(alias) for alias in aliases)
            + "</div>"
        )

    entity_id = entity.get("id")

    if entity_id:
        rows.append(
            f'<div><strong>شناسه:</strong> '
            f"<code>{esc(entity_id)}</code></div>"
        )

    lifecycle = entity.get("lifecycleStatus")

    if lifecycle:
        rows.append(
            f"<div><strong>وضعیت:</strong> {esc(lifecycle)}</div>"
        )

    return (
        '<section class="atlas-section">'
        '<div class="container">'
        '<div class="card atlas-identity-card">'
        + "".join(rows)
        + "</div>"
        "</div>"
        "</section>"
    )


def build_jsonld(entity, entity_claims):
    entity_id = entity["id"]
    entity_type = entity.get("type")
    name_fa = entity_name(entity)
    name_en = entity_name_en(entity)
    canonical = entity_canonical_url(entity_id, entity_type)

    if entity_type == "Person":
        schema_type = "Person"
    elif entity_type == "Organization":
        schema_type = "Organization"
    elif entity_type == "Investment":
        schema_type = "InvestmentOrDeposit"
    elif entity_type == "Concept":
        schema_type = "DefinedTerm"
    else:
        schema_type = "Thing"

    data = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": name_fa,
        "identifier": entity_id,
        "url": canonical,
    }

    if name_en:
        data["alternateName"] = name_en

    if entity_type == "Concept":
        data["inDefinedTermSet"] = f"{SITE_ORIGIN}/atlas/"

    if entity_type == "Person":
        roles = []

        for claim in entity_claims:
            if claim.get("subject") != entity_id:
                continue

            predicate = claim.get("predicate")

            if predicate in {
                "CEO_OF",
                "EXECUTIVE_ROLE_AT",
                "BOARD_MEMBER_OF",
                "CHAIR_OF",
                "VICE_CHAIR_OF",
                "BOARD_SECRETARY_OF",
            }:
                roles.append(predicate)

        if roles:
            data["description"] = (
                f"{name_fa} در حوزه‌های بازار سرمایه، "
                "مدیریت و سرمایه‌گذاری فعالیت داشته است."
            )

    return data


def render_entity(entity, claims, evidence, sources, entities):
    entity_id = entity["id"]
    name_fa = entity_name(entity)
    name_en = entity_name_en(entity)
    entity_type = entity.get("type")

    canonical_url = entity_canonical_url(entity_id, entity_type)

    entity_claims = [
        claim
        for claim in claims
        if claim.get("subject") == entity_id
        or claim.get("object") == entity_id
    ]

    content = load_content(entity)
    source_index = build_source_index(
        sources,
        entity_claims,
        evidence,
        content,
    )
    title = f"{name_fa} | اطلس | Private Capital"

    if name_en:
        title = (
            f"{name_fa} ({name_en}) | اطلس | Private Capital"
        )

    description = name_fa

    if content and content.get("summary"):
        description = content["summary"]

    jsonld = build_jsonld(entity, entity_claims)

    return f"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>{esc(title)}</title>

<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical_url)}">

<link rel="stylesheet" href="/assets/css/style.css">

<link rel="icon" type="image/x-icon" href="/assets/images/favicon.ico">
<link rel="icon" type="image/png" sizes="96x96" href="/assets/images/favicon-96x96.png">
<link rel="apple-touch-icon" href="/assets/images/apple-touch-icon.png">
<link rel="manifest" href="/assets/images/site.webmanifest">

<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=2)}
</script>
</head>

<body class="atlas-page">

<header>
<div class="container">

<div class="logo">
    Private Capital
</div>

<nav>
<a href="/">خانه</a>
<a href="/watch.html">دیده‌بان</a>
<a href="/articles.html">پژوهش‌ها</a>
<a href="/resources.html">اطلس</a>
<a href="/services.html">خدمات</a>
<a href="/membership.html">عضویت ویژه</a>
<a href="/about.html">درباره ما</a>
<a href="/contact.html">تماس</a>
</nav>

</div>
</header>

<main>

<div
    id="atlas-root"
    data-entity-id="{esc(entity_id)}"
    data-static-rendered="true"
>

<section class="page-hero">
<div class="container">
<h1>{esc(name_fa)}</h1>
{f'<p>{esc(name_en)}</p>' if name_en else ''}
</div>
</section>

{render_identity(entity)}

{render_content(content, source_index)}

{render_claims(entity_claims, entity_id, entities)}

{render_data_quality(content)}

{render_evidence(entity_claims, evidence, sources)}

{render_sources(sources, entity_claims, evidence, content)}

</div>

</main>

<footer>
<div class="container">

<p>Private Capital</p>

<p>مرجع تخصصی سرمایه خصوصی در ایران</p>

<p>
<a href="mailto:info@privatecapital.ir">
    info@privatecapital.ir
</a>
</p>

<p>
<a href="tel:+982165512094">
    021-6551-2094
</a>
</p>

<p>© 2026 Private Capital</p>

<p>
<a href="/copyright.html">حقوق محتوا و شرایط استفاده</a>
</p>

</div>
</footer>

<script src="/assets/js/main.js"></script>
<script src="/assets/js/core/url-resolver.js"></script>
<script src="/assets/js/core/relation-renderer.js"></script>
<script src="/assets/js/core/data-loader.js"></script>
<script src="/assets/js/core/provenance-renderer.js"></script>
<script src="/assets/js/atlas.js"></script>

<script>
    Atlas.init();
</script>

</body>
</html>
"""


def generate():
    entities = load_entities()
    claims = load_claims()
    evidence = load_evidence()
    sources = load_sources()

    generated = []

    for entity_id in sorted(entities):
        entity = entities[entity_id]
        entity_type = entity.get("type")
        route = ROUTES.get(entity_type)

        if not route:
            continue

        entity_slug = entity_id.split(":", 1)[1]

        output_dir = OUTPUT_ROOT / route / entity_slug
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / "index.html"

        html_content = render_entity(
            entity,
            claims,
            evidence,
            sources,
            entities,
        )

        output_path.write_text(
            html_content,
            encoding="utf-8",
        )

        generated.append(output_path)

    print(f"Generated {len(generated)} static Atlas pages.")

    for path in generated:
        print(f"  {path.relative_to(ROOT.parent)}")


if __name__ == "__main__":
    generate()
