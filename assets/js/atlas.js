(function () {
    "use strict";

    const ATLAS_ROOT =
    window.location.pathname.includes("/atlas/")
        ? "."
        : "atlas";

    async function loadJSON(path) {
        const response = await fetch(path, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Atlas data load failed: ${path}`);
        }

        return response.json();
    }

    function escapeHTML(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getEntityIdFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get("id");
    }

    function entityFilePath(entityId) {
        const parts = entityId.split(":");
        const type = parts[0];
        const slug = parts.slice(1).join(":");

        if (!type || !slug) {
            throw new Error("Invalid Atlas entity ID.");
        }

        switch (type) {
            case "person":
                return `${ATLAS_ROOT}/entities/persons/${slug}.json`;

            case "organization":
                return `${ATLAS_ROOT}/entities/organizations/${slug}.json`;

            default:
                throw new Error(`Unsupported entity type: ${type}`);
        }
    }

    function claimsFilePath(entityId) {
        const parts = entityId.split(":");

        if (parts[0] !== "person") {
            throw new Error("Claims currently support Person entities only.");
        }

        const slug = parts.slice(1).join(":");
        return `${ATLAS_ROOT}/claims/${slug}.json`;
    }

    function relationLabel(predicate) {
        const labels = {
            CEO_OF: "مدیرعامل",
            EXECUTIVE_ROLE_AT: "سمت اجرایی",
            BOARD_MEMBER_OF: "عضو هیئت‌مدیره",
            CHAIR_OF: "رئیس",
            VICE_CHAIR_OF: "نایب‌رئیس",
            BOARD_SECRETARY_OF: "دبیر هیئت‌مدیره",
            WORKED_AT: "فعالیت در",
            REPRESENTED: "نمایندگی",
            SUBSIDIARY_OF: "زیرمجموعه",
            PART_OF: "بخشی از",
            INVESTED_IN: "سرمایه‌گذاری",
            INVESTMENT_EXECUTIVE_OF: "مدیر سرمایه‌گذاری در",
            MANAGES: "مدیریت",
            HAS_PROJECT: "پروژه",
            PROJECT_OF: "پروژه متعلق به",
            OPERATES_IN: "فعالیت در حوزه",
            TARGETS_SECTOR: "هدف‌گذاری حوزه",
            TARGETS_INVESTOR_CATEGORY: "هدف‌گذاری نوع سرمایه‌گذار",
            SUPPORTED_BY: "پشتیبانی‌شده توسط"
        };

        return labels[predicate] || predicate;
    }

    function statusLabel(status) {
        const labels = {
            VERIFIED: "تأییدشده",
            SUPPORTED: "پشتیبانی‌شده",
            REPORTED: "گزارش‌شده",
            DISPUTED: "مورد اختلاف"
        };

        return labels[status] || status;
    }

    function confidenceLabel(confidence) {
        const labels = {
            HIGH: "اطمینان بالا",
            MEDIUM: "اطمینان متوسط",
            LOW: "اطمینان پایین",
            UNKNOWN: "نامشخص"
        };

        return labels[confidence] || confidence;
    }

    function formatTemporal(temporal) {
        if (!temporal) {
            return "";
        }

        const start = temporal.start || "";
        let end = temporal.end || "";

        if (!end && temporal.status === "current") {
            end = "اکنون";
        }

        if (!start && !end) {
            return "";
        }

        if (start && end) {
            return `${escapeHTML(start)} — ${escapeHTML(end)}`;
        }

        return escapeHTML(start || end);
    }

    function getEntityName(entityIndex, id) {
        const entity = entityIndex[id];

        if (!entity) {
            return id;
        }

        return entity.name?.fa || entity.name?.en || id;
    }

    function getEntityEnglishName(entityIndex, id) {
        const entity = entityIndex[id];

        if (!entity) {
            return "";
        }

        return entity.name?.en || "";
    }

    function renderClaimCard(claim, entityIndex) {
        const object = entityIndex[claim.object];

        if (!object) {
            return "";
        }

        const temporal = formatTemporal(claim.temporal);

        return `
            <article class="card atlas-claim">

                <div class="atlas-claim-label">
                    ${escapeHTML(relationLabel(claim.predicate))}
                </div>

                <h3>
                    ${escapeHTML(getEntityName(entityIndex, claim.object))}
                </h3>

                ${
                    getEntityEnglishName(entityIndex, claim.object)
                        ? `<p>${escapeHTML(getEntityEnglishName(entityIndex, claim.object))}</p>`
                        : ""
                }

                ${
                    claim.role
                        ? `
                            <p class="atlas-meta">
                                <strong>نقش:</strong>
                                ${escapeHTML(claim.role)}
                            </p>
                        `
                        : ""
                }

                ${
                    temporal
                        ? `
                            <p class="atlas-meta">
                                <strong>دوره:</strong>
                                ${temporal}
                            </p>
                        `
                        : ""
                }

                <div class="atlas-status">
                    ${escapeHTML(statusLabel(claim.status))}
                    ${claim.confidence ? ` · ${escapeHTML(confidenceLabel(claim.confidence))}` : ""}
                </div>

            </article>
        `;
    }

    function renderCurrentRole(claim, entityIndex) {
        if (!claim) {
            return "";
        }

        const organizationName = getEntityName(entityIndex, claim.object);

        return `
            <div class="card atlas-current-role">

                <div class="atlas-kicker">
                    سمت فعلی
                </div>

                <h2>
                    ${escapeHTML(relationLabel(claim.predicate))}
                </h2>

                <p class="atlas-current-organization">
                    ${escapeHTML(organizationName)}
                </p>

                ${
                    getEntityEnglishName(entityIndex, claim.object)
                        ? `<p>${escapeHTML(getEntityEnglishName(entityIndex, claim.object))}</p>`
                        : ""
                }

                <div class="atlas-status">
                    ${escapeHTML(statusLabel(claim.status))}
                </div>

            </div>
        `;
    }

    function renderSummary(content) {
        if (!content?.summary) {
            return "";
        }

        return `
            <section class="atlas-section">

                <div class="container">

                    <h2>معرفی</h2>

                    <div class="card atlas-summary">
                        <p>
                            ${escapeHTML(content.summary)}
                        </p>
                    </div>

                </div>

            </section>
        `;
    }

    function renderContentSections(content) {
    if (!content?.sections?.length) {
        return "";
    }

    return `
        <section class="atlas-section">

            <div class="container">

                <h2>متن دانشنامه‌ای</h2>

                ${content.sections
                    .map(section => `
                        <article class="card atlas-content-section">

                            <h3>
                                ${escapeHTML(section.title_fa)}
                            </h3>

                            ${
                                section.title_en
                                    ? `
                                        <div class="atlas-section-en">
                                            ${escapeHTML(section.title_en)}
                                        </div>
                                    `
                                    : ""
                            }

                            ${
                                section.paragraphs?.length
                                    ? section.paragraphs
                                        .map(paragraph => `
                                            <p class="atlas-content-paragraph">
                                                ${escapeHTML(paragraph.text)}

                                                ${
                                                    paragraph.source_refs?.length
    ? `
        <span class="atlas-inline-sources">
            ${paragraph.source_refs
                .map(ref => `
                    <a
                        href="#source-${escapeHTML(ref)}"
                        class="atlas-source-ref"
                    >
                        [${escapeHTML(ref)}]
                    </a>
                `)
                .join(" ")
            }
        </span>
    `
    : ""
                                                }
                                            </p>
                                        `)
                                        .join("")
                                    : ""
                            }

                        </article>
                    `)
                    .join("")}

            </div>

        </section>
    `;
}
function renderTimelineSection(claims, entityIndex) {
    const datedClaims = claims
        .filter(claim => {
            return (
                claim.subject &&
                claim.temporal &&
                (
                    claim.temporal.start ||
                    claim.temporal.end
                )
            );
        })
        .sort((a, b) => {
            const aDate =
                a.temporal?.start ||
                a.temporal?.end ||
                "";

            const bDate =
                b.temporal?.start ||
                b.temporal?.end ||
                "";

            return bDate.localeCompare(aDate);
        });

    if (!datedClaims.length) {
        return "";
    }

    return `
        <section class="atlas-section">

            <div class="container">

                <h2>خط زمانی حرفه‌ای</h2>

                <div class="atlas-timeline">

                    ${datedClaims
                        .map(claim => {

                            const entityName =
                                getEntityName(
                                    entityIndex,
                                    claim.object
                                );

                            const period =
                                formatTemporal(
                                    claim.temporal
                                );

                            return `
                                <article
                                    class="card atlas-timeline-item"
                                >

                                    <div class="atlas-timeline-date">
                                        ${period}
                                    </div>

                                    <div class="atlas-timeline-content">

                                        <div class="atlas-claim-label">
                                            ${escapeHTML(
                                                relationLabel(
                                                    claim.predicate
                                                )
                                            )}
                                        </div>

                                        <h3>
                                            ${escapeHTML(
                                                entityName
                                            )}
                                        </h3>

                                        ${
                                            claim.role
                                                ? `
                                                    <p class="atlas-meta">
                                                        <strong>نقش:</strong>
                                                        ${escapeHTML(
                                                            claim.role
                                                        )}
                                                    </p>
                                                `
                                                : ""
                                        }

                                        <div class="atlas-status">
                                            ${escapeHTML(
                                                statusLabel(
                                                    claim.status
                                                )
                                            )}
                                        </div>

                                    </div>

                                </article>
                            `;
                        })
                        .join("")}

                </div>

            </div>

        </section>
    `;
}
    function renderClaimsSection(title, claims, entityIndex) {
        if (!claims.length) {
            return "";
        }

        return `
            <section class="atlas-section">

                <div class="container">

                    <h2>${escapeHTML(title)}</h2>

                    <div class="grid atlas-claims-grid">

                        ${claims
                            .map(claim => renderClaimCard(claim, entityIndex))
                            .join("")}

                    </div>

                </div>

            </section>
        `;
    }

function renderEvidenceSection(
    claims,
    evidenceData,
    sourceData,
    entityIndex
) {
    if (!evidenceData?.evidence?.length) {
        return "";
    }

    const evidenceByClaim = {};

    evidenceData.evidence.forEach(item => {
        if (!evidenceByClaim[item.claim]) {
            evidenceByClaim[item.claim] = [];
        }

        evidenceByClaim[item.claim].push(item);
    });

    const sourceIndex = {};

    (sourceData?.sources || []).forEach(source => {
        sourceIndex[source.id] = source;
    });

    const sourceMap = {};

    evidenceData.evidence.forEach(evidence => {
        const source = sourceIndex[evidence.source];

        if (!source) {
            return;
        }

        if (!sourceMap[source.id]) {
            sourceMap[source.id] = {
                source: source,
                claims: []
            };
        }

        if (!sourceMap[source.id].claims.includes(evidence.claim)) {
            sourceMap[source.id].claims.push(evidence.claim);
        }
    });

    const sources = Object.values(sourceMap);

    if (!sources.length) {
        return "";
    }

    return `
        <section class="atlas-section">

            <div class="container">

                <h2>منابع و شواهد</h2>

                <div class="atlas-sources-list">

                    ${sources
                        .map(item => {

                            const source = item.source;

                            const citationRefs =
                                source.citation_refs || [];

                            const citationLabel =
                                citationRefs.length
                                    ? citationRefs
                                        .map(
                                            ref =>
                                                `[${escapeHTML(ref)}]`
                                        )
                                        .join(" ")
                                    : "";

                            const anchorId =
                                citationRefs.length
                                    ? `source-${escapeHTML(
                                        citationRefs[0]
                                    )}`
                                    : `source-${escapeHTML(
                                        source.id
                                    )}`;

                            return `
                                <article
                                    class="card atlas-evidence-card"
                                >

                                    <div
                                        class="atlas-source-item"
                                        id="${anchorId}"
                                    >

                                        <div>
                                            ${
                                                citationLabel
                                                    ? `
                                                        <strong>
                                                            ${citationLabel}
                                                        </strong>
                                                    `
                                                    : ""
                                            }

                                            ${escapeHTML(
                                                source.title_fa
                                            )}
                                        </div>

                                        ${
                                            source.publisher
                                                ? `
                                                    <small>
                                                        ${escapeHTML(
                                                            source.publisher
                                                        )}
                                                    </small>
                                                `
                                                : ""
                                        }

                                        ${
                                            source.url
                                                ? `
                                                    <a
                                                        href="${escapeHTML(
                                                            source.url
                                                        )}"
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                    >
                                                        مشاهده منبع
                                                    </a>
                                                `
                                                : `
                                                    <small>
                                                        لینک منبع هنوز ثبت نشده است.
                                                    </small>
                                                `
                                        }

                                    </div>

                                </article>
                            `;
                        })
                        .join("")}

                </div>

            </div>

        </section>
    `;
}

    function renderIdentity(entity) {
        return `
            <section class="atlas-section">

                <div class="container">

                    <div class="card atlas-identity-card">

                        <div class="atlas-kicker">
                            شناسه
                        </div>

                        <div class="atlas-identity-row">
                            <strong>نام فارسی</strong>
                            <span>${escapeHTML(entity.name?.fa)}</span>
                        </div>

                        <div class="atlas-identity-row">
                            <strong>نام انگلیسی</strong>
                            <span>${escapeHTML(entity.name?.en)}</span>
                        </div>

                        ${
                            entity.honorific?.fa
                                ? `
                                    <div class="atlas-identity-row">
                                        <strong>عنوان</strong>
                                        <span>
                                            ${escapeHTML(entity.honorific.fa)}
                                        </span>
                                    </div>
                                `
                                : ""
                        }

                        <div class="atlas-identity-row">
                            <strong>ID</strong>
                            <span>${escapeHTML(entity.id)}</span>
                        </div>

                    </div>

                </div>

            </section>
        `;
    }

    function renderError(message) {
        const root = document.getElementById("atlas-root");

        if (!root) {
            return;
        }

        root.innerHTML = `
            <div class="card">
                <h3>خطا در بارگذاری اطلس</h3>
                <p>${escapeHTML(message)}</p>
            </div>
        `;
    }

    async function renderPerson(entityId) {
        const [
            entity,
            claimsData,
            registry,
            content,
            evidenceData,
            sourceData
        ] = await Promise.all([
            loadJSON(entityFilePath(entityId)),
            loadJSON(claimsFilePath(entityId)),
            loadJSON(`${ATLAS_ROOT}/entities/index.json`),
            loadJSON(`${ATLAS_ROOT}/content/persons/${entityId.split(":").slice(1).join(":")}.json`),
            loadJSON(`${ATLAS_ROOT}/evidence/${entityId.split(":").slice(1).join(":")}.json`),
            loadJSON(`${ATLAS_ROOT}/sources/${entityId.split(":").slice(1).join(":")}.json`)
        ]);

        const entityIndex = {};

        registry.entities.forEach(item => {
            entityIndex[item.id] = item;
        });

        const allClaims = claimsData.claims || [];

        const personClaims = allClaims.filter(
            claim => claim.subject === entityId
        );

        const currentRoleClaim = personClaims.find(
            claim =>
                claim.predicate === "CEO_OF" &&
                claim.temporal?.status === "current"
        );

        const executiveClaims = personClaims.filter(claim =>
            [
                "WORKED_AT",
                "EXECUTIVE_ROLE_AT",
                "CEO_OF",
                "INVESTMENT_EXECUTIVE_OF"
            ].includes(claim.predicate)
        );

        const boardClaims = personClaims.filter(claim =>
            [
                "BOARD_MEMBER_OF",
                "CHAIR_OF",
                "VICE_CHAIR_OF",
                "BOARD_SECRETARY_OF",
                "REPRESENTED"
            ].includes(claim.predicate)
        );

        const investmentClaims = personClaims.filter(claim =>
    [
        "INVESTED_IN",
        "INVESTMENT_EXECUTIVE_OF",
        "MANAGES"
    ].includes(claim.predicate)
);

        const relatedOrganizationClaims = allClaims.filter(
            claim =>
                claim.subject !== entityId &&
                (
                    claim.predicate === "SUBSIDIARY_OF" ||
                    claim.predicate === "PART_OF"
                )
        );

        const root = document.getElementById("atlas-root");

        if (!root) {
            throw new Error("Atlas root element not found.");
        }

        root.innerHTML = `

            <section class="page-hero">

                <div class="container">

                    <h1>
                        ${escapeHTML(entity.name.fa)}
                    </h1>

                    ${
                        entity.name.en
                            ? `
                                <p>
                                    ${escapeHTML(entity.name.en)}
                                </p>
                            `
                            : ""
                    }

                </div>

            </section>

            <section class="atlas-section">

                <div class="container">

                    <div class="grid atlas-top-grid">

                        ${renderCurrentRole(currentRoleClaim, entityIndex)}

                        ${renderIdentity(entity)}

                    </div>

                </div>

            </section>

            ${renderSummary(content)}

${renderTimelineSection(
    personClaims,
    entityIndex
)}

${renderClaimsSection(
    "سوابق اجرایی و مدیریتی",
    executiveClaims,
    entityIndex
)}

${renderClaimsSection(
    "عضویت‌ها و نقش‌های هیئت‌مدیره",
    boardClaims,
    entityIndex
)}

${renderClaimsSection(
    "فعالیت‌های سرمایه‌گذاری",
    investmentClaims,
    entityIndex
)}

${
    relatedOrganizationClaims.length
        ? renderClaimsSection(
            "ساختار سازمانی مرتبط",
            relatedOrganizationClaims,
            entityIndex
        )
        : ""
}

${renderContentSections(content)}

${renderEvidenceSection(
    allClaims,
    evidenceData,
    sourceData,
    entityIndex
)}

        `;
    }

    async function initAtlas() {
        try {
            const entityId = getEntityIdFromURL();

            if (!entityId) {
                return;
            }

            if (entityId.startsWith("person:")) {
                await renderPerson(entityId);
                return;
            }

            throw new Error(
                "این نوع Entity هنوز توسط Renderer پشتیبانی نمی‌شود."
            );

        } catch (error) {
            console.error("Atlas Renderer Error:", error);
            renderError(error.message);
        }
    }

    window.Atlas = {
        init: initAtlas
    };

})();
