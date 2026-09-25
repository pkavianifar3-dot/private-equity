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
RELATION_RENDERING_PATH = ROOT / "taxonomies" / "relation-rendering.json"

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


def load_relation_contract():
    return load_json(RELATION_RENDERING_PATH)


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


def render_claim_relation(claim, entity_id, relation_contract):
    subject_id = claim.get("subject")
    object_id = claim.get("object")
    predicate = claim.get("predicate")

    if not subject_id or not object_id or subject_id == object_id:
        return None

    relation = (
        relation_contract.get("relations", {}).get(predicate)
        if isinstance(relation_contract, dict)
        else None
    )

    if not isinstance(relation, dict):
        return None

    if subject_id == entity_id:
        label = relation.get("forward_label_fa")
        if not isinstance(label, str) or not label.strip():
            return None

        return {
            "direction": "forward",
            "target_id": object_id,
            "label": label,
        }

    if object_id == entity_id:
        if relation.get("reverse_display_allowed") is not True:
            return None

        label = relation.get("reverse_label_fa")
        if not isinstance(label, str) or not label.strip():
            return None

        return {
            "direction": "reverse",
            "target_id": subject_id,
            "label": label,
        }

    return None


def claim_evidence_items(claim, evidence):
    return [
        item for ref in claim.get("evidenceRefs", [])
        if (item := evidence.get(ref)) and item.get("claimRef") == claim.get("id")
    ]


def fa_number(number):
    return str(number).translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


def render_claims(
    claims, entity_id, entities, relation_contract, evidence=None, sources=None
):
    if not claims:
        return ""
    evidence = evidence or {}
    sources = sources or {}
    items = []
    for claim in claims:
        relation = render_claim_relation(claim, entity_id, relation_contract)
        if not relation:
            continue
        target = claim_value_html(claim, entity_id, entities)
        if not target:
            continue
        supported = claim_evidence_items(claim, evidence)
        if supported:
            source_ids = {
                item.get("sourceRef") for item in supported
                if item.get("sourceRef") in sources
            }
            evidence_count = fa_number(len(supported))
            source_count = fa_number(len(source_ids))
            summary = (
                f'<a class="atlas-overview-link" href="#claim-{esc(claim["id"])}">'
                f"{evidence_count} شاهد · {source_count} منبع"
                "</a>"
            )
        else:
            meta = []
            if claim.get("status"):
                meta.append("وضعیت: " + esc(STATUS_LABELS.get(
                    claim["status"], "وضعیت نامشخص"
                )))
            if claim.get("confidence"):
                meta.append("اطمینان: " + esc(CONFIDENCE_LABELS.get(
                    claim["confidence"], "نامشخص"
                )))
            summary = (
                '<p class="atlas-claim-meta">' + " · ".join(meta) + "</p>"
                if meta else ""
            )
        temporal = claim.get("temporal")
        temporal_html = ""
        if isinstance(temporal, dict):
            parts = []
            if temporal.get("start") and temporal.get("end"):
                parts.append(
                    f'بازه: {esc(temporal["start"])} تا {esc(temporal["end"])}'
                )
            elif temporal.get("start"):
                parts.append(f'از: {esc(temporal["start"])}')
            if temporal.get("status"):
                parts.append(
                    "وضعیت زمانی: " + esc(TEMPORAL_STATUS_LABELS.get(
                        temporal["status"], temporal["status"]
                    ))
                )
            if parts:
                temporal_html = (
                    '<p class="atlas-claim-meta">' + " · ".join(parts) + "</p>"
                )
        items.append(
            '<article class="card atlas-claim atlas-overview-item">'
            f'<div class="atlas-claim-label">{esc(relation["label"])}</div>'
            f"<h3>{target}</h3>"
            + temporal_html
            + summary
            + "</article>"
        )
    if not items:
        return ""
    return (
        '<section class="atlas-section atlas-relations-overview">'
        '<div class="container"><h2>روابط در یک نگاه</h2>'
        '<div class="grid atlas-claims-grid">'
        + "".join(items)
        + "</div></div></section>"
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


EVIDENCE_TYPE_LABELS = {
    "explicit_self_statement": "اظهار صریح شخص",
    "corporate_identity": "سند هویت سازمانی",
    "explicit_corporate_statement": "بیانیه صریح سازمان",
    "explicit_media_report": "گزارش صریح رسانه",
    "investment_announcement": "اعلام سرمایه‌گذاری",
    "historical_corporate_record": "سابقه تاریخی سازمان",
    "explicit_title_statement": "اظهار صریح عنوان سمت",
    "independent_media_report": "گزارش رسانه مستقل",
    "historical_board_record": "سابقه تاریخی هیئت‌مدیره",
    "project_statement": "اظهار درباره پروژه",
    "authoritative_publication": "انتشار مرجع معتبر",
}
STRENGTH_LABELS = {
    "strong": "اعتبار بالا",
    "moderate": "اعتبار متوسط",
    "weak": "اعتبار پایین",
}
STATUS_LABELS = {
    "VERIFIED": "تأییدشده",
    "SUPPORTED": "پشتیبانی‌شده",
    "REPORTED": "گزارش‌شده",
    "DISPUTED": "مورد اختلاف",
}
CONFIDENCE_LABELS = {
    "HIGH": "بالا",
    "MEDIUM": "متوسط",
    "LOW": "پایین",
    "UNKNOWN": "نامشخص",
}
TEMPORAL_STATUS_LABELS = {
    "current": "فعلی",
    "former": "پیشین",
}


def render_source_details(source, number, with_anchor=False, show_id=True):
    source_id = source["id"]
    title = (
        source.get("title_fa")
        or source.get("title_en")
        or source.get("publisher")
        or source_id
    )
    url = source.get("url")
    body = (
        f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">'
        f"{esc(title)}</a>"
        if url else esc(title)
    )
    anchor = f' id="source-{esc(source_id)}"' if with_anchor else ""
    publisher = source.get("publisher")
    return (
        f'<div class="atlas-provenance-source"{anchor}>'
        '<div class="atlas-provenance-source-heading">'
        f'<div class="atlas-provenance-source-title">{body}</div>'
        f'<span class="atlas-source-number"><bdi dir="ltr">[{number}]</bdi></span>'
        '</div>'
        + (f"<small>{esc(publisher)}</small>" if publisher else "")
        + (f'<small class="atlas-source-id">{esc(source_id)}</small>'
           if show_id else "")
        + "</div>"
    )


def provenance_claim_title(claim, entity_id, entities, relation_contract):
    relation = render_claim_relation(claim, entity_id, relation_contract)
    forward = (
        relation_contract.get("relations", {})
        .get(claim.get("predicate"), {})
        .get("forward_label_fa")
        if isinstance(relation_contract, dict) else None
    )
    label = relation["label"] if relation else forward or "گزاره مستند"
    subject_id = claim.get("subject")
    object_id = claim.get("object")
    target_id = relation["target_id"] if relation else object_id
    owner_id = entity_id if relation else subject_id
    owner = entity_name(entities[owner_id]) if owner_id in entities else ""
    target = entity_name(entities[target_id]) if target_id in entities else ""
    value = claim.get("value")
    if not target and isinstance(value, dict):
        target = value.get("raw") or ""
    elif not target and value is not None:
        target = str(value)
    return " ".join(part for part in (owner, label, target) if part), label


def render_provenance(
    claims, evidence, sources, source_index, entities, entity_id, relation_contract
):
    cards = []
    anchored = set()
    seen_evidence = set()
    for claim in claims:
        supported = [
            item for item in claim_evidence_items(claim, evidence)
            if item["id"] not in seen_evidence
        ]
        if not supported:
            continue
        for item in supported:
            seen_evidence.add(item["id"])
        title, _ = provenance_claim_title(
            claim, entity_id, entities, relation_contract
        )
        evidence_rows = []
        claim_sources = {}
        technical = []
        for index, item in enumerate(supported, start=1):
            details = []
            if item.get("evidenceType"):
                details.append(
                    "نوع شاهد: " + esc(EVIDENCE_TYPE_LABELS.get(
                        item["evidenceType"], "نوع شاهد نامشخص"
                    ))
                )
            if item.get("strength"):
                details.append(
                    "اعتبار: " + esc(STRENGTH_LABELS.get(
                        item["strength"], "اعتبار نامشخص"
                    ))
                )
            if item.get("note"):
                details.append("توضیح: " + esc(item["note"]))
            source_id = item.get("sourceRef")
            source = sources.get(source_id)
            if source and source_id in source_index:
                claim_sources[source_id] = source
                source_link = (
                    f'<a class="atlas-source-ref" '
                    f'href="#source-{esc(source_id)}" '
                    f'aria-label="رفتن به منبع شماره {source_index[source_id]}">'
                    f'<bdi dir="ltr">[{source_index[source_id]}]</bdi></a>'
                )
            elif source_id:
                source_link = '<span class="atlas-meta">منبع در دسترس نیست</span>'
            else:
                source_link = ""
            evidence_rows.append(
                '<div class="atlas-evidence-item">'
                '<div class="atlas-evidence-header">'
                + source_link
                + f'<strong>شاهد {fa_number(index)}</strong>'
                + "</div>"
                + (f'<p class="atlas-meta">{" | ".join(details)}</p>'
                   if details else "")
                + "</div>"
            )
            technical.append(
                '<li>شناسه شاهد: <bdi dir="ltr">'
                f'{esc(item["id"])}</bdi></li>'
            )
        source_rows = []
        for source_id, source in claim_sources.items():
            first = source_id not in anchored
            anchored.add(source_id)
            source_rows.append(
                render_source_details(
                    source, source_index[source_id], first, show_id=False
                )
            )
            technical.append(
                '<li>شناسه منبع: <bdi dir="ltr">'
                f'{esc(source_id)}</bdi></li>'
            )
        source_html = (
            '<div class="atlas-provenance-sources">'
            '<h4>منابع این ادعا</h4>'
            + "".join(source_rows)
            + "</div>"
            if source_rows else ""
        )
        status_parts = []
        if claim.get("status"):
            status_parts.append(STATUS_LABELS.get(
                claim["status"], "وضعیت نامشخص"
            ))
        if claim.get("confidence"):
            status_parts.append(
                "اطمینان " + CONFIDENCE_LABELS.get(
                    claim["confidence"], "نامشخص"
                )
            )
        cards.append(
            '<article class="card atlas-evidence-group atlas-provenance-card"'
            f' id="claim-{esc(claim["id"])}">'
            f"<h3>{esc(title)}</h3>"
            + (f'<div class="atlas-status">{esc(" · ".join(status_parts))}</div>'
               if status_parts else "")
            + '<div class="atlas-evidence-list">'
            + "".join(evidence_rows)
            + "</div>"
            + ('<div class="provenance-card-divider"></div>' if source_rows else "")
            + source_html
            + '<details class="atlas-provenance-technical">'
              '<summary>جزئیات فنی</summary><ul>'
            + "".join(technical)
            + "</ul></details></article>"
        )
    remaining = []
    for source_id, number in source_index.items():
        source = sources.get(source_id)
        if source and source_id not in anchored:
            remaining.append(
                '<article class="card atlas-source">'
                + render_source_details(source, number, True)
                + "</article>"
            )
    extra_html = (
        '<div class="atlas-provenance-extras"><h3>منابع متن</h3>'
        '<div class="atlas-sources-list">'
        + "".join(remaining)
        + "</div></div>"
        if remaining else ""
    )
    if not cards and not extra_html:
        return ""
    cards_html = (
        '<div class="grid atlas-claims-grid">'
        + "".join(cards)
        + "</div>"
        if cards else ""
    )
    return (
        '<section class="atlas-section atlas-provenance-section">'
        '<div class="container"><h2>شواهد و منابع</h2>'
        + cards_html
        + extra_html
        + "</div></section>"
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


def render_entity(entity, claims, evidence, sources, entities, relation_contract):
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

{render_claims(entity_claims, entity_id, entities, relation_contract, evidence, sources)}

{render_data_quality(content)}

{render_provenance(entity_claims, evidence, sources, source_index, entities, entity_id, relation_contract)}

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
    relation_contract = load_relation_contract()

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
            relation_contract,
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
