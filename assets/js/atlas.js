(function () {
    "use strict";

    const ATLAS_ROOT =
    window.location.pathname.includes("/atlas/")
        ? "."
        : "atlas";
    let entitiesIndexCache = null;
    let claimsIndexCache = null;
    let evidenceIndexCache = null;
    let sourcesIndexCache = null;
    const jsonCache = new Map();
    async function loadJSON(path) {
        const response = await fetch(path, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Atlas data load failed: ${path}`);
        }

        return response.json();
    }
    async function loadCachedJSON(path) {
        if (jsonCache.has(path)) {
            return jsonCache.get(path);
        }
    
        const data = await loadJSON(path);
    
        jsonCache.set(path, data);
    
        return data;
    }
    async function loadEntitiesIndex() {
        if (entitiesIndexCache) {
            return entitiesIndexCache;
        }

        entitiesIndexCache =
            await loadJSON(
                `${ATLAS_ROOT}/entities/index.json`
            );
    
        return entitiesIndexCache;
    }
    
    
    async function loadClaimsIndex() {
        if (claimsIndexCache) {
            return claimsIndexCache;
        }
    
        claimsIndexCache =
            await loadJSON(
                `${ATLAS_ROOT}/claims/index.json`
            );
    
        return claimsIndexCache;
    }
    
    
    async function loadEvidenceIndex() {
        if (evidenceIndexCache) {
            return evidenceIndexCache;
        }
    
        evidenceIndexCache =
            await loadJSON(
                `${ATLAS_ROOT}/evidence/index.json`
            );
    
        return evidenceIndexCache;
    }
    
    
    async function loadSourcesIndex() {
        if (sourcesIndexCache) {
            return sourcesIndexCache;
        }
    
        sourcesIndexCache =
            await loadJSON(
                `${ATLAS_ROOT}/sources/index.json`
            );
    
        return sourcesIndexCache;
    }
    function escapeHTML(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    const SITE_ORIGIN = "https://privatecapital.ir";

    // Claim statuses allowed to appear in public structured data (JSON-LD).
    // REPORTED / DISPUTED claims stay visible on the page but are kept out
    // of machine-readable data until independently verified or supported.
    const STRUCTURED_DATA_STATUSES = ["VERIFIED", "SUPPORTED"];
    function setMeta(name, content) {
        if (!content) {
            return;
        }

        let el = document.querySelector(`meta[name="${name}"]`);

        if (!el) {
            el = document.createElement("meta");
            el.setAttribute("name", name);
            document.head.appendChild(el);
        }

        el.setAttribute("content", content);
    }

    function setMetaProperty(property, content) {
        if (!content) {
            return;
        }

        let el = document.querySelector(`meta[property="${property}"]`);

        if (!el) {
            el = document.createElement("meta");
            el.setAttribute("property", property);
            document.head.appendChild(el);
        }

        el.setAttribute("content", content);
    }

    function setCanonical(url) {
        let el = document.querySelector('link[rel="canonical"]');

        if (!el) {
            el = document.createElement("link");
            el.setAttribute("rel", "canonical");
            document.head.appendChild(el);
        }

        el.setAttribute("href", url);
    }

    function injectJSONLD(data) {
        let el = document.getElementById("atlas-jsonld");

        if (!el) {
            el = document.createElement("script");
            el.type = "application/ld+json";
            el.id = "atlas-jsonld";
            document.head.appendChild(el);
        }

        el.textContent = JSON.stringify(data, null, 2);
    }

    function applyPageSEO({ title, description, url }) {
        if (title) {
            document.title = title;
        }

        setMeta("description", description);
        setCanonical(url);
        setMetaProperty("og:type", "profile");
        setMetaProperty("og:title", title);
        setMetaProperty("og:description", description);
        setMetaProperty("og:url", url);
    }

    function buildRoleEntry(claim, entityIndex, roleProperty) {
        const objectName =
            getEntityEnglishName(entityIndex, claim.object) ||
            getEntityName(entityIndex, claim.object);

        if (!objectName) {
            return null;
        }

        const role = {
            "@type": "Role",
            roleName: relationLabel(claim.predicate)
        };

        if (claim.temporal?.start) {
            role.startDate = claim.temporal.start;
        }

        if (claim.temporal?.end) {
            role.endDate = claim.temporal.end;
        }

        role[roleProperty] = {
            "@type": "Organization",
            name: objectName
        };

        return role;
    }

    function buildPersonJSONLD(entity, personClaims, entityIndex, entityId) {
        const publishable = personClaims.filter(claim =>
            STRUCTURED_DATA_STATUSES.includes(claim.status)
        );

        const worksFor = publishable
            .filter(claim =>
                [
                    "CEO_OF",
                    "EXECUTIVE_ROLE_AT",
                    "WORKED_AT",
                    "INVESTMENT_EXECUTIVE_OF"
                ].includes(claim.predicate)
            )
            .map(claim => buildRoleEntry(claim, entityIndex, "worksFor"))
            .filter(Boolean);

        const memberOf = publishable
            .filter(claim =>
                [
                    "BOARD_MEMBER_OF",
                    "CHAIR_OF",
                    "VICE_CHAIR_OF",
                    "BOARD_SECRETARY_OF"
                ].includes(claim.predicate)
            )
            .map(claim => buildRoleEntry(claim, entityIndex, "memberOf"))
            .filter(Boolean);

        const data = {
            "@context": "https://schema.org",
            "@type": "Person",
            "name": entity.name?.fa || "",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "PrivateCapitalAtlasID",
                "value": entity.id
            },
            "url": `${SITE_ORIGIN}/atlas/person.html?id=${encodeURIComponent(entityId)}`
        };

        if (entity.name?.en) {
            data.alternateName = entity.name.en;
        }

        if (worksFor.length) {
            data.worksFor = worksFor;
        }

        if (memberOf.length) {
            data.memberOf = memberOf;
        }

        return data;
    }

    function buildOrganizationJSONLD(entity, entityIndex, entityId) {
        const parentId = entity.metadata?.parent || entity.parent || null;

        const data = {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": entity.name?.fa || "",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "PrivateCapitalAtlasID",
                "value": entity.id
            },
            "url": `${SITE_ORIGIN}/atlas/organization.html?id=${encodeURIComponent(entityId)}`
        };

        if (entity.name?.en) {
            data.alternateName = entity.name.en;
        }

        if (entity.metadata?.national_id) {
            data.identifier = [
                data.identifier,
                {
                    "@type": "PropertyValue",
                    "propertyID": "IranNationalID",
                    "value": entity.metadata.national_id
                }
            ];
        }

        if (parentId) {
            const parentName =
                getEntityEnglishName(entityIndex, parentId) ||
                getEntityName(entityIndex, parentId);

            if (parentName) {
                data.parentOrganization = {
                    "@type": "Organization",
                    name: parentName
                };
            }
        }

        return data;
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
        
            case "investment":
                return `${ATLAS_ROOT}/entities/investments/${slug}.json`;
            
            case "concept":
                return `${ATLAS_ROOT}/entities/concepts/${slug}.json`;
            
            default:
                throw new Error(`Unsupported entity type: ${type}`);
        }
    }
    async function loadInvestmentEntities(registry) {
        const investmentEntries =
            (registry.entities || [])
                .filter(entity => entity.type === "Investment");
    
        if (!investmentEntries.length) {
            return {};
        }
    
        const investments = await Promise.all(
            investmentEntries.map(entry =>
                loadCachedJSON(
                    entityFilePath(entry.id)
                )
            )
        );
    
        const investmentIndex = {};
    
        investments.forEach(investment => {
            investmentIndex[investment.id] = investment;
        });
    
        return investmentIndex;
    }
    async function loadClaimsForEntity(entityId) {
    const claimsIndex =
        await loadClaimsIndex();

    const claimIds =
        claimsIndex.entities?.[entityId] || [];

    if (!claimIds.length) {
        return [];
    }

    const claimFileNames = [];

    for (const claimId of claimIds) {
        const fileName =
            claimsIndex.claims?.[claimId];

        if (!fileName) {
            throw new Error(
                `Claim index is missing source file for: ${claimId}`
            );
        }

        if (!claimFileNames.includes(fileName)) {
            claimFileNames.push(fileName);
        }
    }

    const claimDatasets = await Promise.all(
        claimFileNames.map(fileName =>
            loadJSON(
                `${ATLAS_ROOT}/claims/${fileName}`
            )
        )
    );

    const claimsById = {};

    claimDatasets.forEach(data => {
        (data.claims || []).forEach(claim => {
            claimsById[claim.id] = claim;
        });
    });

    return claimIds
        .map(claimId => claimsById[claimId])
        .filter(Boolean);
}
    let allConceptClaimsCache = null;
    
    async function loadAllConceptClaims() {
        if (allConceptClaimsCache) {
            return allConceptClaimsCache;
        }
        const claimsIndex =
            await loadClaimsIndex();
    
        const conceptIds = Object.keys(
            claimsIndex.entities || {}
        ).filter(id =>
            id.startsWith("concept:")
        );
    
        if (!conceptIds.length) {
            return [];
        }
    
        const claimIds = [];
    
        conceptIds.forEach(entityId => {
            const ids =
                claimsIndex.entities?.[entityId] || [];
    
            ids.forEach(claimId => {
                if (!claimIds.includes(claimId)) {
                    claimIds.push(claimId);
                }
            });
        });
    
        const claimFileNames = [];
    
        claimIds.forEach(claimId => {
            const fileName =
                claimsIndex.claims?.[claimId];
    
            if (
                fileName &&
                !claimFileNames.includes(fileName)
            ) {
                claimFileNames.push(fileName);
            }
        });
    
        const datasets = await Promise.all(
            claimFileNames.map(fileName =>
                loadJSON(
                    `${ATLAS_ROOT}/claims/${fileName}`
                )
            )
        );
    
        const claimsById = {};
    
        datasets.forEach(data => {
            (data.claims || []).forEach(claim => {
                claimsById[claim.id] = claim;
            });
        });
    
        allConceptClaimsCache =
            claimIds
                .map(claimId => claimsById[claimId])
                .filter(Boolean);
        
        return allConceptClaimsCache;
        }
    async function loadEvidenceForClaims(claims) {
        const evidenceIndex =
            await loadEvidenceIndex();
    
        const evidenceIds = [];
    
        claims.forEach(claim => {
            const claimEvidence =
                evidenceIndex.claims?.[claim.id] || [];
    
            claimEvidence.forEach(evidenceId => {
                if (!evidenceIds.includes(evidenceId)) {
                    evidenceIds.push(evidenceId);
                }
            });
        });
    
        if (!evidenceIds.length) {
            return [];
        }
    
        const evidenceFiles = [];
    
        evidenceIds.forEach(evidenceId => {
            const fileName =
                evidenceIndex.evidence?.[evidenceId];
    
            if (!fileName) {
                throw new Error(
                    `Evidence index is missing source file for: ${evidenceId}`
                );
            }
    
            if (!evidenceFiles.includes(fileName)) {
                evidenceFiles.push(fileName);
            }
        });
    
        const datasets = await Promise.all(
            evidenceFiles.map(fileName =>
                loadJSON(
                    `${ATLAS_ROOT}/evidence/${fileName}`
                )
            )
        );
    
        const evidenceById = {};
    
        datasets.forEach(data => {
            (data.evidence || []).forEach(item => {
                evidenceById[item.id] = item;
            });
        });
    
        return evidenceIds
            .map(evidenceId => evidenceById[evidenceId])
            .filter(Boolean);
    }
    
    
    async function loadSourcesForEvidence(evidenceList) {
        const sourceIndex =
            await loadSourcesIndex();
    
        const sourceIds = [];
    
        evidenceList.forEach(evidence => {
            const sourceId = evidence.source;
    
            if (
                sourceId &&
                !sourceIds.includes(sourceId)
            ) {
                sourceIds.push(sourceId);
            }
        });
    
        if (!sourceIds.length) {
            return [];
        }
    
        const sourceFiles = [];
    
        sourceIds.forEach(sourceId => {
            const fileName =
                sourceIndex.sources?.[sourceId];
    
            if (!fileName) {
                throw new Error(
                    `Source index is missing source file for: ${sourceId}`
                );
            }
    
            if (!sourceFiles.includes(fileName)) {
                sourceFiles.push(fileName);
            }
        });
    
        const datasets = await Promise.all(
            sourceFiles.map(fileName =>
                loadJSON(
                    `${ATLAS_ROOT}/sources/${fileName}`
                )
            )
        );
    
        const sourcesById = {};
    
        datasets.forEach(data => {
            (data.sources || []).forEach(item => {
                sourcesById[item.id] = item;
            });
        });
    
        return sourceIds
            .map(sourceId => sourcesById[sourceId])
            .filter(Boolean);
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
            SUPPORTED_BY: "پشتیبانی‌شده توسط",
            BROADER_THAN: "کلی‌تر از",
            RELATED_TO: "مرتبط با",
            INCLUDES: "شامل",
            HAS_NON_UNIFORM_CLASSIFICATION: "طبقه‌بندی یکنواخت ندارد",
            CHARACTERIZED_BY: "مشخص‌شده با",
            LINKED_TO: "مرتبط با",
            HAS_INVESTOR_POSITION: "دارای جایگاه سرمایه‌گذاری",
            RETURN_DEPENDS_ON: "بازده وابسته به",
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
    function investmentStatusLabel(status) {
        const labels = {
            announced: "اعلام‌شده",
            completed: "تکمیل‌شده",
            cancelled: "لغوشده",
            pending: "در انتظار",
            unknown: "نامشخص"
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
    function formatClaimValue(value) {
        if (!value || typeof value !== "object") {
            return "";
        }
    
        if (value.unit === "amount") {
            const amount = Number(value.amount);
    
            if (!Number.isFinite(amount)) {
                return escapeHTML(value.raw || "");
            }
    
            const formattedAmount =
                new Intl.NumberFormat("fa-IR").format(amount);
    
            const currencyLabels = {
                IRR: "ریال",
                USD: "دلار",
                EUR: "یورو"
            };
    
            const currency =
                currencyLabels[value.currency] ||
                value.currency ||
                "";
    
            if (currency) {
                return `${formattedAmount} ${escapeHTML(currency)}`;
            }
    
            return formattedAmount;
        }
    
        if (value.unit === "percentage") {
            return `${escapeHTML(value.raw || value.amount)}٪`;
        }
    
        if (value.unit === "count") {
            return escapeHTML(value.raw || String(value.amount));
        }
    
        if (value.unit === "ratio") {
            return escapeHTML(value.raw || String(value.amount));
        }
    
        return escapeHTML(value.raw || "");
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
function entityURL(entityId) {
    const parts = entityId.split(":");
    const type = parts[0];

    switch (type) {
        case "organization":
            return `organization.html?id=${encodeURIComponent(entityId)}`;

        case "investment":
            return `investment.html?id=${encodeURIComponent(entityId)}`;

        case "concept":
            return `concept.html?id=${encodeURIComponent(entityId)}`;

        default:
            return null;
    }
}

    function renderClaimCard(
        claim,
        entityIndex,
        investmentIndex = {}
    ) {        const object =
            claim.object
                ? entityIndex[claim.object]
                : null;
        
        const linkedInvestment =
            claim.predicate === "INVESTED_IN"
                ? Object.values(investmentIndex).find(
                    investment =>
                        investment.metadata?.investor === claim.subject &&
                        investment.metadata?.target === claim.object
                )
                : null;
        
        const objectURL =
            claim.object
                ? entityURL(claim.object)
                : null;
        
        const investmentURL =
            linkedInvestment
                ? entityURL(linkedInvestment.id)
                : null;
        
        const temporal =
            formatTemporal(claim.temporal);
        
        const objectName =
            claim.object
                ? getEntityName(
                    entityIndex,
                    claim.object
                )
                : "";
        
        const objectEnglishName =
            claim.object
                ? getEntityEnglishName(
                    entityIndex,
                    claim.object
                )
                : "";
    
        const valueHTML =
            claim.value
                ? `
                    <div class="atlas-value">
                        <strong>مقدار:</strong>
                        ${formatClaimValue(claim.value)}
                    </div>
                `
                : "";
    
        return `
            <article class="card atlas-claim">
    
                <div class="atlas-claim-label">
                    ${escapeHTML(relationLabel(claim.predicate))}
                </div>
    
                ${
                    claim.object && object
                        ? `
                            <h3>
                                ${
                                    objectURL
                                        ? `
                                            <a href="${objectURL}">
                                                ${escapeHTML(objectName)}
                                            </a>
                                        `
                                        : `
                                            ${escapeHTML(objectName)}
                                        `
                                }
                            </h3>
                        `
                        : ""
                }

                ${
                    linkedInvestment && investmentURL
                        ? `
                            <p class="atlas-meta">
                                <a href="${investmentURL}">
                                    مشاهده جزئیات سرمایه‌گذاری
                                </a>
                            </p>
                        `
                        : ""
                }
                ${
                    claim.object && objectEnglishName
                        ? `
                            <p class="atlas-english">
                                ${
                                    objectURL
                                        ? `
                                            <a href="${objectURL}">
                                                ${escapeHTML(objectEnglishName)}
                                            </a>
                                        `
                                        : `
                                            ${escapeHTML(objectEnglishName)}
                                        `
                                }
                            </p>
                        `
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
    
                ${valueHTML}
    
                <div class="atlas-status">
                    ${escapeHTML(statusLabel(claim.status))}
                    ${
                        claim.confidence
                            ? ` · ${escapeHTML(confidenceLabel(claim.confidence))}`
                            : ""
                    }
                </div>
    
            </article>
        `;
    }

    function renderCurrentRole(claim, entityIndex) {
        if (!claim) {
            return "";
        }

        const organizationName = getEntityName(entityIndex, claim.object);
const organizationURL = entityURL(claim.object);
        return `
            <div class="card atlas-current-role">

                <div class="atlas-kicker">
                    سمت فعلی
                </div>

                <h2>
                    ${escapeHTML(relationLabel(claim.predicate))}
                </h2>

                <p class="atlas-current-organization">
    ${
        organizationURL
            ? `
                <a href="${organizationURL}">
                    ${escapeHTML(organizationName)}
                </a>
            `
            : escapeHTML(organizationName)
    }
</p>

                ${
                    getEntityEnglishName(entityIndex, claim.object)
                        ? `<p class="atlas-english">
    ${escapeHTML(getEntityEnglishName(entityIndex, claim.object))}
</p>`
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
const objectURL =
    entityURL(claim.object);
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
    ${
        objectURL
            ? `
                <a href="${objectURL}">
                    ${escapeHTML(entityName)}
                </a>
            `
            : escapeHTML(entityName)
    }
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
    function renderClaimsSection(
        title,
        claims,
        entityIndex,
        investmentIndex = {}
    ) {
    
        if (!claims.length) {
            return "";
        }

        return `
            <section class="atlas-section">

                <div class="container">

                    <h2>${escapeHTML(title)}</h2>

                    <div class="grid atlas-claims-grid">

                        ${claims

                            .map(
                                claim =>
                                    renderClaimCard(
                                        claim,
                                        entityIndex,
                                        investmentIndex
                                    )
                            )
                          
                            .join("")}

                    </div>

                </div>

            </section>
        `;
    }
function renderDataQualitySection(content, claims) {
    const dataQuality = content?.data_quality;

    if (!dataQuality && !content?.last_reviewed) {
        return "";
    }

    const statusCounts = {
        VERIFIED: 0,
        SUPPORTED: 0,
        REPORTED: 0,
        DISPUTED: 0
    };

    claims.forEach(claim => {
        if (statusCounts[claim.status] !== undefined) {
            statusCounts[claim.status]++;
        }
    });

    return `
        <section class="atlas-section">

            <div class="container">

                <h2>وضعیت داده</h2>

                <div class="card atlas-data-quality">

                    ${
                        dataQuality?.text
                            ? `
                                <p class="atlas-content-paragraph">
                                    ${escapeHTML(dataQuality.text)}
                                </p>
                            `
                            : ""
                    }

                    ${
                        content?.last_reviewed
                            ? `
                                <div class="atlas-identity-row">
                                    <strong>آخرین بازبینی</strong>
                                    <span>
                                        ${escapeHTML(content.last_reviewed)}
                                    </span>
                                </div>
                            `
                            : ""
                    }

                    <div class="atlas-quality-stats">

                        ${
                            statusCounts.VERIFIED
                                ? `
                                    <div class="atlas-quality-stat">
                                        <strong>
                                            ${statusCounts.VERIFIED}
                                        </strong>
                                        <span>تأییدشده</span>
                                    </div>
                                `
                                : ""
                        }

                        ${
                            statusCounts.SUPPORTED
                                ? `
                                    <div class="atlas-quality-stat">
                                        <strong>
                                            ${statusCounts.SUPPORTED}
                                        </strong>
                                        <span>پشتیبانی‌شده</span>
                                    </div>
                                `
                                : ""
                        }

                        ${
                            statusCounts.REPORTED
                                ? `
                                    <div class="atlas-quality-stat">
                                        <strong>
                                            ${statusCounts.REPORTED}
                                        </strong>
                                        <span>گزارش‌شده</span>
                                    </div>
                                `
                                : ""
                        }

                        ${
                            statusCounts.DISPUTED
                                ? `
                                    <div class="atlas-quality-stat">
                                        <strong>
                                            ${statusCounts.DISPUTED}
                                        </strong>
                                        <span>مورد اختلاف</span>
                                    </div>
                                `
                                : ""
                        }

                    </div>

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
    const evidenceList =
        evidenceData?.evidence || [];

    const sourceList =
        sourceData?.sources || [];

    if (!evidenceList.length) {
        return "";
    }

    const sourceIndex = {};

    sourceList.forEach(source => {
        sourceIndex[source.id] = source;
    });

    const claimIndex = {};

    claims.forEach(claim => {
        claimIndex[claim.id] = claim;
    });

    const groupedByClaim = {};

    evidenceList.forEach(evidence => {
        const claimId = evidence.claim;

        if (!claimId) {
            return;
        }

        if (!groupedByClaim[claimId]) {
            groupedByClaim[claimId] = [];
        }

        groupedByClaim[claimId].push(evidence);
    });

    const sections = Object.entries(groupedByClaim)
        .map(([claimId, evidenceItems]) => {
            const claim = claimIndex[claimId];

            if (!claim) {
                return "";
            }

            const relation =
                relationLabel(claim.predicate);

            const objectName =
                claim.object
                    ? getEntityName(
                        entityIndex,
                        claim.object
                    )
                    : "";

            const objectEnglishName =
                claim.object
                    ? getEntityEnglishName(
                        entityIndex,
                        claim.object
                    )
                    : "";

            const evidenceHTML =
                evidenceItems
                    .map(evidence => {
                        const source =
                            sourceIndex[evidence.source];

                        if (!source) {
                            return `
                                <div class="atlas-evidence-item">

                                    <div class="atlas-claim-label">
                                        شاهد
                                    </div>

                                    <p>
                                        ${escapeHTML(
                                            evidence.id
                                        )}
                                    </p>

                                </div>
                            `;
                        }

                        return `
                            <div class="atlas-evidence-item">

                                <div class="atlas-claim-label">
                                    منبع پشتیبان
                                </div>

                                <div class="atlas-source-item">

                                    ${
                                        source.citation_refs?.length
                                            ? `
                                                <strong>
                                                    ${source.citation_refs
                                                        .map(
                                                            ref =>
                                                                `[${escapeHTML(ref)}]`
                                                        )
                                                        .join(" ")}
                                                </strong>
                                            `
                                            : ""
                                    }

                                    <div>
                                        ${escapeHTML(
                                            source.title_fa || ""
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

                                ${
                                    evidence.note
                                        ? `
                                            <p class="atlas-meta">
                                                ${escapeHTML(
                                                    evidence.note
                                                )}
                                            </p>
                                        `
                                        : ""
                                }

                            </div>
                        `;
                    })
                    .join("");

            return `
                <article class="card atlas-evidence-group">

                    <div class="atlas-claim-label">
                        ${escapeHTML(relation)}
                    </div>

                    ${
                        objectName
                            ? `
                                <h3>
                                    ${escapeHTML(objectName)}
                                </h3>
                            `
                            : ""
                    }

                    ${
                        objectEnglishName
                            ? `
                                <p class="atlas-english">
                                    ${escapeHTML(
                                        objectEnglishName
                                    )}
                                </p>
                            `
                            : ""
                    }

                    ${
                        claim.value
                            ? `
                                <div class="atlas-value">
                                    <strong>مقدار:</strong>
                                    ${formatClaimValue(
                                        claim.value
                                    )}
                                </div>
                            `
                            : ""
                    }

                    <div class="atlas-status">
                        ${escapeHTML(
                            statusLabel(claim.status)
                        )}
                        ${
                            claim.confidence
                                ? ` · ${escapeHTML(
                                    confidenceLabel(
                                        claim.confidence
                                    )
                                )}`
                                : ""
                        }
                    </div>

                    <div class="atlas-evidence-list">
                        ${evidenceHTML}
                    </div>

                </article>
            `;
        })
        .filter(Boolean)
        .join("");

    if (!sections) {
        return "";
    }

    return `
        <section class="atlas-section">

            <div class="container">

                <h2>شواهد و منابع</h2>

                <div class="atlas-sources-list">
                    ${sections}
                </div>

            </div>

        </section>
    `;
}
    function renderIdentity(entity) {
    return `
        <div class="card atlas-identity-card">

            <div class="atlas-kicker">
                شناسه
            </div>

            <div class="atlas-identity-row">
                <strong>نام فارسی</strong>
                <span>${escapeHTML(entity.name?.fa || "")}</span>
            </div>

            <div class="atlas-identity-row">
                <strong>نام انگلیسی</strong>
                <span>${escapeHTML(entity.name?.en || "")}</span>
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
                <span>${escapeHTML(entity.id || "")}</span>
            </div>

        </div>
    `;
}
async function renderOrganization(entityId) {
    const [
        entity,
        organizationClaims,
        registry
    ] = await Promise.all([
        loadCachedJSON(entityFilePath(entityId)),
        loadClaimsForEntity(entityId),
        loadEntitiesIndex()
    ]);
    
    const investmentIndex =
        await loadInvestmentEntities(registry);
    const investmentSummaries = [];
    
    for (const claim of organizationClaims) {
        if (claim.predicate !== "INVESTED_IN") {
            continue;
        }
    
        const investment =
            Object.values(investmentIndex).find(
                item =>
                    item.metadata?.investor === claim.subject &&
                    item.metadata?.target === claim.object
            );
    
        if (!investment) {
            continue;
        }
    
        const investmentClaims =
            await loadClaimsForEntity(investment.id);
    
        const amountClaim =
            investmentClaims.find(
                item =>
                    item.predicate === "INVESTMENT_AMOUNT"
            );
    
        investmentSummaries.push({
            claim,
            investment,
            amountClaim
        });
    }
    const evidenceList =
        await loadEvidenceForClaims(organizationClaims);
    
    const sourceList =
        await loadSourcesForEvidence(evidenceList);
    
    const evidenceData = {
        evidence: evidenceList
    };
    
    const sourceData = {
        sources: sourceList
    };

    const entityIndex = {};

    registry.entities.forEach(item => {
        entityIndex[item.id] = item;
    });

    const claims = organizationClaims.filter(
        claim =>
            claim.subject === entityId ||
            claim.object === entityId
    );

    const root = document.getElementById("atlas-root");

    if (!root) {
        throw new Error("Atlas root element not found.");
    }

    const parentId =
        entity.metadata?.parent ||
        entity.parent ||
        null;

    const parentName =
        parentId
            ? getEntityName(entityIndex, parentId)
            : "";
    const investmentSummaryHTML =
        investmentSummaries.length
            ? `
                <section class="atlas-section">
    
                    <div class="container">
    
                        <h2>
                            سرمایه‌گذاری‌ها
                        </h2>
    
                        <div class="grid atlas-claims-grid">
    
                            ${investmentSummaries
                                .map(item => {
                                    const investmentURL =
                                        entityURL(
                                            item.investment.id
                                        );
    
                                    const targetName =
                                        getEntityName(
                                            entityIndex,
                                            item.claim.object
                                        );
    
                                    return `
                                        <article class="card atlas-claim">
    
                                            <div class="atlas-claim-label">
                                                سرمایه‌گذاری
                                            </div>
    
                                            <h3>
                                                ${escapeHTML(
                                                    targetName
                                                )}
                                            </h3>
    
                                            ${
                                                item.amountClaim
                                                    ? `
                                                        <div class="atlas-value">
                                                            <strong>
                                                                مبلغ:
                                                            </strong>
    
                                                            ${formatClaimValue(
                                                                item.amountClaim.value
                                                            )}
                                                        </div>
    
                                                        <div class="atlas-status">
                                                            ${escapeHTML(
                                                                statusLabel(
                                                                    item.amountClaim.status
                                                                )
                                                            )}
                                                        </div>
                                                    `
                                                    : ""
                                            }
    
                                            ${
                                                investmentURL
                                                    ? `
                                                        <p class="atlas-meta">
                                                            <a href="${investmentURL}">
                                                                مشاهده جزئیات سرمایه‌گذاری
                                                            </a>
                                                        </p>
                                                    `
                                                    : ""
                                            }
    
                                        </article>
                                    `;
                                })
                                .join("")}
    
                        </div>
    
                    </div>
    
                </section>
            `
            : "";
    root.innerHTML = `
        <section class="page-hero">

            <div class="container">

                <h1>
                    ${escapeHTML(entity.name?.fa || "")}
                </h1>

                ${
                    entity.name?.en
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

                <div class="card atlas-identity-card">

                    <div class="atlas-kicker">
                        سازمان
                    </div>

                    <div class="atlas-identity-row">
                        <strong>نام فارسی</strong>
                        <span>
                            ${escapeHTML(entity.name?.fa || "")}
                        </span>
                    </div>

                    ${
                        entity.name?.en
                            ? `
                                <div class="atlas-identity-row">
                                    <strong>نام انگلیسی</strong>
                                    <span class="atlas-english">
                                        ${escapeHTML(entity.name.en)}
                                    </span>
                                </div>
                            `
                            : ""
                    }

                    ${
                        entity.metadata?.organization_type
                            ? `
                                <div class="atlas-identity-row">
                                    <strong>نوع سازمان</strong>
                                    <span>
                                        ${escapeHTML(
                                            entity.metadata.organization_type
                                        )}
                                    </span>
                                </div>
                            `
                            : ""
                    }

                    ${
                        entity.metadata?.national_id
                            ? `
                                <div class="atlas-identity-row">
                                    <strong>شناسه ملی</strong>
                                    <span>
                                        ${escapeHTML(
                                            entity.metadata.national_id
                                        )}
                                    </span>
                                </div>
                            `
                            : ""
                    }

                    ${
                        parentId
                            ? `
                                <div class="atlas-identity-row">
                                    <strong>ارتباط سازمانی</strong>
                                    <span>
                                        ${escapeHTML(parentName)}
                                    </span>
                                </div>
                            `
                            : ""
                    }

                    <div class="atlas-identity-row">
                        <strong>ID</strong>
                        <span>
                            ${escapeHTML(entity.id)}
                        </span>
                    </div>

                </div>

            </div>

        </section>

        ${renderClaimsSection(
            "روابط و ادعاها",
            claims,
            entityIndex,
            investmentIndex
        )}
        ${investmentSummaryHTML}
        ${renderEvidenceSection(
            organizationClaims,
            evidenceData,
            sourceData,
            entityIndex
        )}
    `;

    applyPageSEO({
        title: `${entity.name?.fa || ""} | اطلس | Private Capital`,
        description: `صفحه اطلس ${entity.name?.fa || ""} در Private Capital.`,
        url: `${SITE_ORIGIN}/atlas/organization.html?id=${encodeURIComponent(entityId)}`
    });

    injectJSONLD(
        buildOrganizationJSONLD(entity, entityIndex, entityId)
    );
}
function renderConceptRelationSection(
    title,
    claims,
    entityIndex
) {
    if (!claims.length) {
        return "";
    }
    const uniqueClaims = Array.from(
        new Map(
            claims.map(claim => [
                `${claim.predicate}|${claim.object || ""}|${claim.value?.raw || ""}`,
                claim
            ])
        ).values()
    );
    return `
        <section class="atlas-section">

            <div class="container">

                <h2>${escapeHTML(title)}</h2>

                <div class="grid atlas-claims-grid">

                    ${uniqueClaims
                        .map(claim => {
                            const objectId =
                                claim.object || null;

                            const objectName =
                                objectId
                                    ? getEntityName(
                                        entityIndex,
                                        objectId
                                    )
                                    : "";

                            const objectEnglishName =
                                objectId
                                    ? getEntityEnglishName(
                                        entityIndex,
                                        objectId
                                    )
                                    : "";

                            const objectURL =
                                objectId
                                    ? entityURL(objectId)
                                    : null;

                            return `
                                <article class="card atlas-claim">

                                    <div class="atlas-claim-label">
                                        ${escapeHTML(
                                            relationLabel(
                                                claim.predicate
                                            )
                                        )}
                                    </div>

                                    ${
                                        objectName
                                            ? `
                                                <h3>
                                                    ${
                                                        objectURL
                                                            ? `
                                                                <a href="${objectURL}">
                                                                    ${escapeHTML(
                                                                        objectName
                                                                    )}
                                                                </a>
                                                            `
                                                            : escapeHTML(
                                                                objectName
                                                            )
                                                    }
                                                </h3>
                                            `
                                            : ""
                                    }

                                    ${
                                        objectEnglishName
                                            ? `
                                                <p class="atlas-english">
                                                    ${
                                                        objectURL
                                                            ? `
                                                                <a href="${objectURL}">
                                                                    ${escapeHTML(
                                                                        objectEnglishName
                                                                    )}
                                                                </a>
                                                            `
                                                            : escapeHTML(
                                                                objectEnglishName
                                                            )
                                                    }
                                                </p>
                                            `
                                            : ""
                                    }

                                    ${
                                        claim.role
                                            ? `
                                                <p class="atlas-meta">
                                                    <strong>
                                                        نقش:
                                                    </strong>
                                                    ${escapeHTML(
                                                        claim.role
                                                    )}
                                                </p>
                                            `
                                            : ""
                                    }

                                    ${
                                        claim.value
                                            ? `
                                                <div class="atlas-value">
                                                    <strong>
                                                        مقدار:
                                                    </strong>
                                                    ${formatClaimValue(
                                                        claim.value
                                                    )}
                                                </div>
                                            `
                                            : ""
                                    }

                                    <div class="atlas-status">
                                        ${escapeHTML(
                                            statusLabel(
                                                claim.status
                                            )
                                        )}
                                        ${
                                            claim.confidence
                                                ? ` · ${escapeHTML(
                                                    confidenceLabel(
                                                        claim.confidence
                                                    )
                                                )}`
                                                : ""
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
function renderConceptBreadcrumbs(
    entity,
    allConceptClaims,
    entityIndex
) {
    const parentMap = {};

    allConceptClaims.forEach(claim => {
        if (
            claim.predicate !== "BROADER_THAN" ||
            !claim.subject ||
            !claim.object
        ) {
            return;
        }

        if (!parentMap[claim.object]) {
            parentMap[claim.object] = [];
        }

        parentMap[claim.object].push(
            claim.subject
        );
    });

    const chain = [];
    const visited = new Set();

    let currentId = entity.id;

    while (
        parentMap[currentId]?.length &&
        !visited.has(currentId)
    ) {
        visited.add(currentId);

        const parentId =
            parentMap[currentId][0];

        if (
            !parentId ||
            visited.has(parentId)
        ) {
            break;
        }

        chain.unshift(parentId);

        currentId = parentId;
    }

    if (!chain.length) {
        return "";
    }

    const items = chain
        .map(id => {
            const name =
                getEntityName(
                    entityIndex,
                    id
                );

            const url =
                entityURL(id);

            return {
                name,
                url
            };
        })
        .filter(item => item.name);

    if (!items.length) {
        return "";
    }

    items.push({
        name:
            entity.name?.fa || "",
        url: null
    });

    return `
        <nav
            class="atlas-breadcrumbs"
            aria-label="مسیر مفهومی"
        >
            ${items
                .map((item, index) => `
                    ${
                        item.url
                            ? `
                                <a href="${item.url}">
                                    ${escapeHTML(
                                        item.name
                                    )}
                                </a>
                            `
                            : `
                                <span
                                    aria-current="${
                                        index === items.length - 1
                                            ? "page"
                                            : ""
                                    }"
                                >
                                    ${escapeHTML(
                                        item.name
                                    )}
                                </span>
                            `
                    }

                    ${
                        index < items.length - 1
                            ? " / "
                            : ""
                    }
                `)
                .join("")}
        </nav>
    `;
}
    
    async function renderConcept(entityId) {
        const [
            entity,
            conceptClaims,
            registry
        ] = await Promise.all([
            loadCachedJSON(entityFilePath(entityId)),
            loadClaimsForEntity(entityId),
            loadEntitiesIndex()
        ]);
    
        const entityIndex = {};
    
        registry.entities.forEach(item => {
            entityIndex[item.id] = item;
        });
        const allConceptClaims =
            await loadAllConceptClaims();
        const evidenceList =
            await loadEvidenceForClaims(conceptClaims);
    
        const sourceList =
            await loadSourcesForEvidence(evidenceList);
    
        const evidenceData = {
            evidence: evidenceList
        };
    
        const sourceData = {
            sources: sourceList
        };
        const broaderClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "BROADER_THAN"
            );
        
        const relatedClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "RELATED_TO"
            );
        
        const includesClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "INCLUDES"
            );
        const classificationClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "HAS_NON_UNIFORM_CLASSIFICATION"
            );
        
        const characterizedByClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "CHARACTERIZED_BY"
            );
        
        const linkedToClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "LINKED_TO"
            );
        
        const investorPositionClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "HAS_INVESTOR_POSITION"
            );
        
        const returnDependsOnClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "RETURN_DEPENDS_ON"
            );
        const breadcrumbsHTML =
            renderConceptBreadcrumbs(
                entity,
                allConceptClaims,
                entityIndex
            );
        const root =
            document.getElementById("atlas-root");
    
        if (!root) {
            throw new Error(
                "Atlas root element not found."
            );
        }
    
        root.innerHTML = `
            <section class="page-hero">
    
                <div class="container">
                    ${breadcrumbsHTML}
                    <h1>
                        ${escapeHTML(
                            entity.name?.fa || ""
                        )}
                    </h1>
    
                    ${
                        entity.name?.en
                            ? `
                                <p>
                                    ${escapeHTML(
                                        entity.name.en
                                    )}
                                </p>
                            `
                            : ""
                    }
    
                </div>
    
            </section>
    
            <section class="atlas-section">
    
                <div class="container">
    
                    <div class="card atlas-identity-card">
    
                        <div class="atlas-kicker">
                            مفهوم
                        </div>
    
                        <div class="atlas-identity-row">
                            <strong>
                                نام فارسی
                            </strong>
    
                            <span>
                                ${escapeHTML(
                                    entity.name?.fa || ""
                                )}
                            </span>
                        </div>
    
                        ${
                            entity.name?.en
                                ? `
                                    <div class="atlas-identity-row">
                                        <strong>
                                            نام انگلیسی
                                        </strong>
    
                                        <span class="atlas-english">
                                            ${escapeHTML(
                                                entity.name.en
                                            )}
                                        </span>
                                    </div>
                                `
                                : ""
                        }
    
                        ${
                            entity.aliases?.length
                                ? `
                                    <div class="atlas-identity-row">
                                        <strong>
                                            نام‌های دیگر
                                        </strong>
    
                                        <span>
                                            ${entity.aliases
                                                .map(
                                                    alias =>
                                                        escapeHTML(alias)
                                                )
                                                .join("، ")}
                                        </span>
                                    </div>
                                `
                                : ""
                        }
    
                        <div class="atlas-identity-row">
                            <strong>
                                ID
                            </strong>
    
                            <span>
                                ${escapeHTML(
                                    entity.id
                                )}
                            </span>
                        </div>
    
                    </div>
    
                </div>
    
            </section>
    
            ${renderConceptRelationSection(
                "کلی‌تر از",
                broaderClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "مرتبط با",
                relatedClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "شامل",
                includesClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "طبقه‌بندی",
                classificationClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "مشخصه‌ها",
                characterizedByClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "ارتباط با",
                linkedToClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "جایگاه سرمایه‌گذار",
                investorPositionClaims,
                entityIndex
            )}
            
            ${renderConceptRelationSection(
                "وابستگی بازده",
                returnDependsOnClaims,
                entityIndex
            )}
            
            ${renderEvidenceSection(
                conceptClaims,
                evidenceData,
                sourceData,
                entityIndex
            )}
        `;
    
        applyPageSEO({
            title:
                `${entity.name?.fa || ""} | اطلس | Private Capital`,
    
            description:
                `صفحه مفهوم ${entity.name?.fa || ""} در Private Capital.`,
    
            url:
                `${SITE_ORIGIN}/atlas/concept.html?id=${encodeURIComponent(
                    entityId
                )}`
        });
    }
    async function renderInvestment(entityId) {
        const [
            entity,
            investmentClaims,
            registry
        ] = await Promise.all([
            loadCachedJSON(entityFilePath(entityId)),
            loadClaimsForEntity(entityId),
            loadEntitiesIndex()
        ]);
    
        const entityIndex = {};
    
        registry.entities.forEach(item => {
            entityIndex[item.id] = item;
        });
    
        const evidenceList =
            await loadEvidenceForClaims(investmentClaims);
    
        const sourceList =
            await loadSourcesForEvidence(evidenceList);
    
        const evidenceData = {
            evidence: evidenceList
        };
    
        const sourceData = {
            sources: sourceList
        };
    
        const investorId =
            entity.metadata?.investor || null;
    
        const targetId =
            entity.metadata?.target || null;
    
        const investorName =
            investorId
                ? getEntityName(entityIndex, investorId)
                : "";
        
        const investorURL =
            investorId
                ? entityURL(investorId)
                : null;
        
        const targetName =
            targetId
                ? getEntityName(entityIndex, targetId)
                : "";
        
        const targetURL =
            targetId
                ? entityURL(targetId)
                : null;
        const investmentRelationshipHTML =
            investorName && targetName
                ? `
                    <section class="atlas-section">
        
                        <div class="container">
        
                            <h2>
                                رابطه معامله
                            </h2>
        
                            <div class="card atlas-claim">
        
                                <div class="atlas-claim-label">
                                    سرمایه‌گذاری
                                </div>
        
                                <div class="atlas-identity-row">
                                    <strong>
                                        سرمایه‌گذار
                                    </strong>
        
                                    <span>
                                        ${
                                            investorURL
                                                ? `
                                                    <a href="${investorURL}">
                                                        ${escapeHTML(
                                                            investorName
                                                        )}
                                                    </a>
                                                `
                                                : escapeHTML(
                                                    investorName
                                                )
                                        }
                                    </span>
                                </div>
        
                                <div class="atlas-identity-row">
                                    <strong>
                                        هدف
                                    </strong>
        
                                    <span>
                                        ${
                                            targetURL
                                                ? `
                                                    <a href="${targetURL}">
                                                        ${escapeHTML(
                                                            targetName
                                                        )}
                                                    </a>
                                                `
                                                : escapeHTML(
                                                    targetName
                                                )
                                        }
                                    </span>
                                </div>
        
                            </div>
        
                        </div>
        
                    </section>
                `
                : "";
        const amountClaim =
            investmentClaims.find(
                claim =>
                    claim.predicate === "INVESTMENT_AMOUNT"
            );

        const investmentRelationClaim =
            investmentClaims.find(
                claim =>
                    claim.predicate === "INVESTED_IN"
            );
        
        const root =
            document.getElementById("atlas-root");
    
        if (!root) {
            throw new Error(
                "Atlas root element not found."
            );
        }
    
        root.innerHTML = `
            <section class="page-hero">
    
                <div class="container">
    
                    <h1>
                        ${escapeHTML(
                            entity.name?.fa || ""
                        )}
                    </h1>
    
                    ${
                        entity.name?.en
                            ? `
                                <p>
                                    ${escapeHTML(
                                        entity.name.en
                                    )}
                                </p>
                            `
                            : ""
                    }
    
                </div>
    
            </section>
    
            <section class="atlas-section">
    
                <div class="container">
    
                    <div class="card atlas-identity-card">
    
                        <div class="atlas-kicker">
                            سرمایه‌گذاری
                        </div>
    
                        ${
                            investorName
                                ? `
                                    <div class="atlas-identity-row">
                                        <strong>
                                            سرمایه‌گذار
                                        </strong>
                                        <span>
                                            ${
                                                investorURL
                                                    ? `
                                                        <a href="${investorURL}">
                                                            ${escapeHTML(
                                                                investorName
                                                            )}
                                                        </a>
                                                    `
                                                    : escapeHTML(
                                                        investorName
                                                    )
                                            }
                                        </span>
                                    </div>
                                `
                                : ""
                        }
    
                        ${
                            targetName
                                ? `
                                    <div class="atlas-identity-row">
                                        <strong>
                                            هدف سرمایه‌گذاری
                                        </strong>
                                        <span>
                                            ${
                                                targetURL
                                                    ? `
                                                        <a href="${targetURL}">
                                                            ${escapeHTML(
                                                                targetName
                                                            )}
                                                        </a>
                                                    `
                                                    : escapeHTML(
                                                        targetName
                                                    )
                                            }
                                        </span>
                                    </div>
                                `
                                : ""
                        }
    
                        ${
                            entity.metadata?.investment_status
                                ? `
                                    <div class="atlas-identity-row">
                                        <strong>
                                            وضعیت
                                        </strong>
                                        <span>
                                            
                                            ${escapeHTML(
                                                investmentStatusLabel(
                                                    entity.metadata.investment_status
                                                )
                                            )}

                                            
                                        </span>
                                    </div>
                                `
                                : ""
                        }
    
                        <div class="atlas-identity-row">
                            <strong>
                                ID
                            </strong>
                            <span>
                                ${escapeHTML(
                                    entity.id
                                )}
                            </span>
                        </div>
    
                    </div>
    
                </div>
    
            </section>
            ${investmentRelationshipHTML}
            ${
                amountClaim
                    ? `
                        <section class="atlas-section">
    
                            <div class="container">
    
                                <h2>
                                    مبلغ سرمایه‌گذاری
                                </h2>
    
                                <div class="card atlas-claim">
    
                                    <div class="atlas-claim-label">
                                        ${escapeHTML(
                                            relationLabel(
                                                amountClaim.predicate
                                            )
                                        )}
                                    </div>
    
                                    <div class="atlas-value">
                                        <strong>
                                            مقدار:
                                        </strong>
    
                                        ${formatClaimValue(
                                            amountClaim.value
                                        )}
                                    </div>
    
                                    <div class="atlas-status">
                                        ${escapeHTML(
                                            statusLabel(
                                                amountClaim.status
                                            )
                                        )}
                                        ${
                                            amountClaim.confidence
                                                ? ` · ${escapeHTML(
                                                    confidenceLabel(
                                                        amountClaim.confidence
                                                    )
                                                )}`
                                                : ""
                                        }
                                    </div>
    
                                </div>
    
                            </div>
    
                        </section>
                    `
                    : ""
            }
    
            ${renderClaimsSection(
                "ادعاها و روابط",
                investmentClaims,
                entityIndex
            )}
    
            ${renderEvidenceSection(
                investmentClaims,
                evidenceData,
                sourceData,
                entityIndex
            )}
        `;
    
        applyPageSEO({
            title:
                `${entity.name?.fa || ""} | اطلس | Private Capital`,
    
            description:
                `صفحه سرمایه‌گذاری ${entity.name?.fa || ""} در Private Capital.`,
    
            url:
                `${SITE_ORIGIN}/atlas/investment.html?id=${encodeURIComponent(
                    entityId
                )}`
        });
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
            allClaims,
            registry,
            content
        ] = await Promise.all([
            loadCachedJSON(entityFilePath(entityId)),
            loadClaimsForEntity(entityId),
            loadEntitiesIndex(),
            loadJSON(
                `${ATLAS_ROOT}/content/persons/${entityId.split(":").slice(1).join(":")}.json`
            )
        ]);
        
        const evidenceList =
            await loadEvidenceForClaims(allClaims);
        
        const sourceList =
            await loadSourcesForEvidence(evidenceList);
        
        const evidenceData = {
            evidence: evidenceList
        };
        
        const sourceData = {
            sources: sourceList
};
        
        const entityIndex = {};
        
        registry.entities.forEach(item => {
            entityIndex[item.id] = item;
        });
        
        const personClaims = allClaims.filter(
            claim =>
                claim.subject === entityId ||
                claim.object === entityId
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

${renderDataQualitySection(
    content,
    allClaims
)}

${renderEvidenceSection(
    allClaims,
    evidenceData,
    sourceData,
    entityIndex
)}

        `;
        applyPageSEO({
            title: `${entity.name?.fa || ""} | اطلس | Private Capital`,
            description: currentRoleClaim
                ? `${entity.name?.fa || ""}؛ ${relationLabel(currentRoleClaim.predicate)} ${getEntityName(entityIndex, currentRoleClaim.object)}.`
                : `صفحه اطلس ${entity.name?.fa || ""} در Private Capital.`,
            url: `${SITE_ORIGIN}/atlas/person.html?id=${encodeURIComponent(entityId)}`
        });

        injectJSONLD(
            buildPersonJSONLD(entity, personClaims, entityIndex, entityId)
        );
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

if (entityId.startsWith("organization:")) {
    await renderOrganization(entityId);
    return;
}

if (entityId.startsWith("investment:")) {
    await renderInvestment(entityId);
    return;
}

if (entityId.startsWith("concept:")) {
    await renderConcept(entityId);
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
