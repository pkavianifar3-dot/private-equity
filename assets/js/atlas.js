(function () {
    "use strict";

    const entityURL = (entityId, entityType) =>
        window.PrivateCapitalURL.entityURL(entityId, entityType);

    const ATLAS_ROOT =
    window.location.pathname.includes("/atlas/")
        ? "."
        : "atlas";

    const dataLoader = window.PrivateCapitalDataLoader.create(ATLAS_ROOT);
    const loadJSON = dataLoader.loadJSON;
    const loadCachedJSON = dataLoader.loadCachedJSON;
    const loadRelationContract = dataLoader.loadRelationContract;
    let relationContract = null;

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
            "url": window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
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
            "url": window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
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
        const atlasRoot = document.getElementById("atlas-root");

        if (atlasRoot) {
            const entityId = atlasRoot.dataset.entityId;

            if (entityId) {
                return entityId;
            }
        }

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
        await loadCachedJSON(
            `${ATLAS_ROOT}/claims/index.json`
        );

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
            loadCachedJSON(
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
            await loadCachedJSON(
                `${ATLAS_ROOT}/claims/index.json`
            );
    
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
                loadCachedJSON(
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
            await loadCachedJSON(
                `${ATLAS_ROOT}/evidence/index.json`
            );
    
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
                loadCachedJSON(
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
    
    
    async function loadSourcesForProvenance(evidenceList, content = null) {
        const sourceIndex =
            await loadCachedJSON(
                `${ATLAS_ROOT}/sources/index.json`
            );

        const sourceIds =
            window.PrivateCapitalProvenanceRenderer.collectSourceIds(
                evidenceList,
                content
            );

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
                loadCachedJSON(
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
        const relationTypes = relationContract?.relationTypes?.relation_types || [];
        const relation = relationTypes.find(item => item.id === predicate);

        return relation?.label_fa || predicate;
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

    function renderClaimStatus(claim) {
        return `<div class="atlas-status">
            ${escapeHTML(statusLabel(claim.status))}
            ${claim.confidence
                ? ` · ${escapeHTML(confidenceLabel(claim.confidence))}`
                : ""}
        </div>`;
    }

    function renderOverviewLink(claim, evidenceList, sourceList) {
        const refs = new Set(claim.evidenceRefs || []);
        const items = (evidenceList || []).filter(
            item => refs.has(item.id) && item.claimRef === claim.id
        );
        if (!items.length) {
            return "";
        }
        const knownSources = new Set(
            (sourceList || []).map(source => source.id)
        );
        const sourceCount = new Set(
            items.map(item => item.sourceRef).filter(id => knownSources.has(id))
        ).size;
        const digits = number => new Intl.NumberFormat("fa-IR").format(number);
        return `<a class="atlas-overview-link"
            href="#claim-${escapeHTML(claim.id)}">
            ${digits(items.length)} شاهد · ${digits(sourceCount)} منبع
        </a>`;
    }
    function renderClaimCard(
        claim,
        entityIndex,
        investmentIndex = {},
        overview = null
    ) {
        if (!claim || typeof claim !== "object") {
            return "";
        }
    
        if (!entityIndex || typeof entityIndex !== "object") {
            return "";
        }
    
        const renderedRelation = overview?.entityId &&
            window.PrivateCapitalRelationRenderer &&
            relationContract
                ? window.PrivateCapitalRelationRenderer.renderRelation(
                    claim,
                    overview.entityId,
                    relationContract.relationTypes,
                    relationContract.relationRules,
                    relationContract.relationRendering
                )
                : null;
        const displayId = renderedRelation?.targetId || claim.object;
        const displayLabel = renderedRelation?.label ||
            relationLabel(claim.predicate);
        const object = displayId ? entityIndex[displayId] : null;
        
        const linkedInvestment =
            claim.predicate === "INVESTED_IN"
                ? Object.values(investmentIndex).find(
                    investment =>
                        investment.metadata?.investor === claim.subject &&
                        investment.metadata?.target === claim.object
                )
                : null;
        
        const objectURL =
            displayId
                ? entityURL(
                    displayId,
                    entityIndex[displayId]?.type
                )
                : null;
        
        const investmentURL =
            linkedInvestment
                ? entityURL(
                    linkedInvestment.id,
                    linkedInvestment.type
                )
                : null;
        
        const temporal =
            formatTemporal(claim.temporal);
        
        const objectName =
            displayId
                ? getEntityName(
                    entityIndex,
                    displayId
                )
                : "";
        
        const objectEnglishName =
            displayId
                ? getEntityEnglishName(
                    entityIndex,
                    displayId
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
    
        const overviewLink = overview
            ? renderOverviewLink(claim, overview.evidenceList, overview.sourceList)
            : "";
        return `
            <article class="card atlas-claim${overview ? " atlas-overview-item" : ""}">
    
                <div class="atlas-claim-label">
                    ${escapeHTML(displayLabel)}
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
    
${overviewLink || renderClaimStatus(claim)}
    
            </article>
        `;
    }

    function renderCurrentRole(claim, entityIndex) {
        if (!claim) {
            return "";
        }

        const organizationName = getEntityName(entityIndex, claim.object);
        const organizationURL =
            entityURL(
                claim.object,
                entityIndex[claim.object]?.type
            );
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

    function renderContentSections(content, sourceData) {
        const sourceIndex =
            window.PrivateCapitalProvenanceRenderer.buildSourceIndex(sourceData);
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
                                                    paragraph.sourceRefs?.length
                                                        ? `
                                                            <span class="atlas-inline-sources">
                                                                ${paragraph.sourceRefs
                                                                    .map(sourceId => {
                                                                        const source = sourceIndex[sourceId];
                                                                        if (!source) {
                                                                            return "";
                                                                        }
                                                                        return `
                                                                            <a
                                                                                href="#source-${escapeHTML(sourceId)}"
                                                                                class="atlas-source-ref"
                                                                            >
                                                                                [${escapeHTML(source.title_fa || "منبع")}]
                                                                            </a>
                                                                        `;
                                                                    })
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
                                entityURL(
                                    claim.object,
                                    entityIndex[claim.object]?.type
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
        investmentIndex = {},
        overview = null
    ) {
    
        if (!claims.length) {
            return "";
        }

        return `
            <section class="atlas-section${overview ? " atlas-relations-overview" : ""}">

                <div class="container">

                    <h2>${escapeHTML(title)}</h2>

                    <div class="grid atlas-claims-grid">

                        ${claims

                            .map(
                                claim =>
                                    renderClaimCard(
                                        claim,
                                        entityIndex,
                                        investmentIndex,
                                        overview
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
    function renderSourceDetails(source, sourceNumber, withAnchor, showId = true) {
        const title =
            source.title_fa ||
            source.title_en ||
            source.publisher ||
            source.id;
        const titleHTML = source.url
            ? `<a href="${escapeHTML(source.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(title)}</a>`
            : escapeHTML(title);
        const anchor = withAnchor
            ? `id="source-${escapeHTML(source.id)}"`
            : "";

        return `
            <div class="atlas-provenance-source" ${anchor}>
                <div class="atlas-provenance-source-heading">
                    <div class="atlas-provenance-source-title">${titleHTML}</div>
                    <span class="atlas-source-number"><bdi dir="ltr">[${escapeHTML(String(sourceNumber))}]</bdi></span>
                </div>
                ${source.publisher
                    ? `<small>${escapeHTML(source.publisher)}</small>`
                    : ""}
                ${showId
                    ? `<small class="atlas-source-id">${escapeHTML(source.id)}</small>`
                    : ""}
            </div>
        `;
    }

    function renderSourcesSection(sourceData, sourceNumbers, anchoredSources) {
        const sources = Array.isArray(sourceData)
            ? sourceData
            : (sourceData?.sources || []);
        const remaining = sources.filter(source => !anchoredSources.has(source.id));

        if (!remaining.length) {
            return "";
        }

        return `
            <div class="atlas-provenance-extras">
                <h3>منابع متن</h3>
                <div class="atlas-sources-list">
                    ${remaining.map(source => `
                        <article class="card atlas-source">
                            ${renderSourceDetails(source, sourceNumbers[source.id], true)}
                        </article>
                    `).join("")}
                </div>
            </div>
        `;
    }

    function renderEvidenceSection(
        claims,
        evidenceData,
        sourceData,
        entityIndex,
        entityId = null
    ) {
        const sources = Array.isArray(sourceData)
            ? sourceData
            : (sourceData?.sources || []);
        const provRenderer = window.PrivateCapitalProvenanceRenderer;
        const provenanceRefs =
            provRenderer.buildSourceReferenceIndex({ sources });
        const sourceIndex = provenanceRefs.sourceIndex;
        const sourceNumbers = provenanceRefs.sourceNumbers;
        const anchoredSources = new Set();

        const allEvidence = Array.isArray(evidenceData)
            ? evidenceData
            : (evidenceData?.evidence || []);
        const evidenceMap = {};
        allEvidence.forEach(evidence => {
            if (!evidenceMap[evidence.claimRef]) {
                evidenceMap[evidence.claimRef] = [];
            }
            evidenceMap[evidence.claimRef].push(evidence);
        });

        const relationRenderer = window.PrivateCapitalRelationRenderer;
        const sections = (claims || [])
            .map(claim => {
                const refs = new Set(claim.evidenceRefs || []);
                const evidenceItems = (evidenceMap[claim.id] || [])
                    .filter(item => refs.has(item.id));
                if (!evidenceItems.length) {
                    return "";
                }

                let relation = relationLabel(claim.predicate);
                let targetEntity = null;
                if (relationRenderer &&
                    typeof relationRenderer.renderRelation === "function" &&
                    relationContract
                ) {
                    const rendered = relationRenderer.renderRelation(
                        claim,
                        entityId,
                        relationContract.relationTypes,
                        relationContract.relationRules,
                        relationContract.relationRendering
                    );
                    if (rendered) {
                        relation = rendered.label || relation;
                        targetEntity = rendered.targetId
                            ? { id: rendered.targetId }
                            : null;
                    }
                }
                const ownerId = targetEntity && claim.object === entityId
                    ? entityId
                    : claim.subject;
                const objectId = targetEntity?.id || claim.object || null;
                const ownerName = ownerId
                    ? getEntityName(entityIndex, ownerId)
                    : "";
                const objectName = objectId
                    ? getEntityName(entityIndex, objectId)
                    : "";
                const claimTitle = [ownerName, relation, objectName]
                    .filter(Boolean).join(" ");

                const claimSources = new Map();
                const technical = [];
                const digits = number =>
                    new Intl.NumberFormat("fa-IR").format(number);
                const evidenceHTML = evidenceItems.map((evidence, index) => {
                    const source = sourceIndex[evidence.sourceRef];
                    if (source) {
                        claimSources.set(source.id, source);
                    }
                    const metaParts = [];
                    if (evidence.evidenceType) {
                        metaParts.push(`نوع شاهد: ${escapeHTML(
                            provRenderer.evidenceTypeLabel(evidence.evidenceType)
                        )}`);
                    }
                    if (evidence.strength) {
                        metaParts.push(`اعتبار: ${escapeHTML(
                            provRenderer.strengthLabel(evidence.strength)
                        )}`);
                    }
                    if (evidence.note) {
                        metaParts.push(`توضیح: ${escapeHTML(evidence.note)}`);
                    }
                    technical.push(
                        `<li>شناسه شاهد: <bdi dir="ltr">${escapeHTML(evidence.id)}</bdi></li>`
                    );
                    const sourceLink = source
                        ? `<a class="atlas-source-ref" href="#source-${escapeHTML(source.id)}" aria-label="رفتن به منبع شماره ${escapeHTML(String(sourceNumbers[source.id]))}"><bdi dir="ltr">[${escapeHTML(String(sourceNumbers[source.id]))}]</bdi></a>`
                        : evidence.sourceRef
                            ? '<span class="atlas-meta">منبع در دسترس نیست</span>'
                            : "";
                    return `
                        <div class="atlas-evidence-item">
                            <div class="atlas-evidence-header">
                                ${sourceLink}
                                <strong>شاهد ${digits(index + 1)}</strong>
                            </div>
                            ${metaParts.length
                                ? `<p class="atlas-meta">${metaParts.join(" | ")}</p>`
                                : ""}
                        </div>
                    `;
                }).join("");

                const sourceHTML = Array.from(claimSources.values())
                    .map(source => {
                        const first = !anchoredSources.has(source.id);
                        anchoredSources.add(source.id);
                        technical.push(
                            `<li>شناسه منبع: <bdi dir="ltr">${escapeHTML(source.id)}</bdi></li>`
                        );
                        return renderSourceDetails(
                            source,
                            sourceNumbers[source.id],
                            first,
                            false
                        );
                    }).join("");
                const status = [
                    claim.status && statusLabel(claim.status),
                    claim.confidence &&
                        confidenceLabel(claim.confidence)
                ].filter(Boolean).join(" · ");

                return `
                    <article class="card atlas-evidence-group atlas-provenance-card"
                        id="claim-${escapeHTML(claim.id)}">
                        <h3>${escapeHTML(claimTitle || relation)}</h3>
                        ${claim.value
                            ? `<div class="atlas-value"><strong>مقدار:</strong> ${formatClaimValue(claim.value)}</div>`
                            : ""}
                        ${status
                            ? `<div class="atlas-status">${escapeHTML(status)}</div>`
                            : ""}
                        <div class="atlas-evidence-list">${evidenceHTML}</div>
                        ${sourceHTML
                            ? `
                                <div class="provenance-card-divider"></div>
                                <div class="atlas-provenance-sources">
                                    <h4>منابع این ادعا</h4>
                                    ${sourceHTML}
                                </div>
                            `
                            : ""}
                        <details class="atlas-provenance-technical">
                            <summary>جزئیات فنی</summary>
                            <ul>${technical.join("")}</ul>
                        </details>
                    </article>
                `;
            })
            .filter(Boolean)
            .join("");

        const otherSources = renderSourcesSection(
            sources,
            sourceNumbers,
            anchoredSources
        );
        if (!sections && !otherSources) {
            return "";
        }

        return `
            <section class="atlas-section atlas-provenance-section">
                <div class="container">
                    <h2>شواهد و منابع</h2>
                    ${sections
                        ? `<div class="grid atlas-claims-grid">${sections}</div>`
                        : ""}
                    ${otherSources}
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
        loadCachedJSON(
            `${ATLAS_ROOT}/entities/index.json`
        )
        
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
        await loadSourcesForProvenance(evidenceList);
    
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
                                            item.investment.id,
                                            item.investment.type
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
                                            entity.organization_type
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
            "روابط در یک نگاه",
            claims,
            entityIndex,
            investmentIndex,
            { evidenceList, sourceList, entityId }
        )}
        ${investmentSummaryHTML}
        ${renderEvidenceSection(
            organizationClaims,
            evidenceData,
            sourceData,
            entityIndex,
            entityId
        )}
    `;

    applyPageSEO({
        title: `${entity.name?.fa || ""} | اطلس | Private Capital`,
        description: `صفحه اطلس ${entity.name?.fa || ""} در Private Capital.`,
        url: window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
    });

    injectJSONLD(
        buildOrganizationJSONLD(entity, entityIndex, entityId)
    );
}
function renderConceptRelationSection(
    title,
    claims,
    entityIndex,
    entityId,
    relationContract,
    evidenceList = [],
    sourceList = []
) {
    if (!Array.isArray(claims) || !claims.length) {
        return "";
    }

    if (!entityIndex || typeof entityIndex !== "object") {
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
        <section class="atlas-section atlas-relations-overview">

            <div class="container">

                <h2>${escapeHTML(title)}</h2>

                <div class="grid atlas-claims-grid">

                    ${uniqueClaims
                        .map(claim => {
                            const renderedRelation =
                                PrivateCapitalRelationRenderer.renderRelation(
                                    claim,
                                    entityId,
                                    relationContract.relationTypes,
                                    relationContract.relationRules,
                                    relationContract.relationRendering
                                );
                            if (!renderedRelation) {
                                return "";
                            }

                            const objectId =
                                renderedRelation.targetId;
                            if (!objectId || objectId === entityId) {
                                return "";
                            }
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
                                    ? entityURL(
                                        objectId,
                                        entityIndex[objectId]?.type
                                    )
                                    : null;

                            return `
                                <article class="card atlas-claim atlas-overview-item">

                                    <div class="atlas-claim-label">
                                        ${escapeHTML(
                                            renderedRelation.label
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

${renderOverviewLink(claim, evidenceList, sourceList) || renderClaimStatus(claim)}

                                </article>
                            `;
                        })
                        .filter(Boolean)
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
    if (!entity || typeof entity !== "object") {
        return "";
    }

    if (!Array.isArray(allConceptClaims)) {
        return "";
    }

    if (!entityIndex || typeof entityIndex !== "object") {
        return "";
    }
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
                entityURL(
                    id,
                    entityIndex[id]?.type
                );

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
    function buildConceptJSONLD(
        entity,
        entityId
    ) {
        const data = {
            "@context": "https://schema.org",
            "@type": "DefinedTerm",
            "name": entity.name?.fa || "",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "PrivateCapitalAtlasID",
                "value": entity.id
            },
            "url": window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
        };
    
        if (entity.name?.en) {
            data.alternateName = entity.name.en;
        }
    
        if (entity.aliases?.length) {
            data.alternateName = entity.aliases;
        }
    
        return data;
    }
    async function renderConcept(entityId) {
        const [
            entity,
            conceptClaims,
            registry,
            relationContract
        ] = await Promise.all([
            loadCachedJSON(entityFilePath(entityId)),
            loadClaimsForEntity(entityId),
            loadCachedJSON(
                `${ATLAS_ROOT}/entities/index.json`
            ),
            loadRelationContract()
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
            await loadSourcesForProvenance(evidenceList);
    
        const evidenceData = {
            evidence: evidenceList
        };
    
        const sourceData = {
            sources: sourceList
        };
        const broaderClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "BROADER_THAN" &&
                    claim.subject === entityId
            );
        
        const broaderThanClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "BROADER_THAN" &&
                    claim.object === entityId
            );
        
        const relatedClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "RELATED_TO"
            );
        
        const includesClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "INCLUDES" &&
                    claim.subject === entityId
            );
        
        const includedInClaims =
            conceptClaims.filter(
                claim =>
                    claim.predicate === "INCLUDES" &&
                    claim.object === entityId
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
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            ${renderConceptRelationSection(
                "مفهوم بالاتر",
                broaderThanClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            ${renderConceptRelationSection(
                "مرتبط با",
                relatedClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            
            ${renderConceptRelationSection(
                "شامل",
                includesClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            ${renderConceptRelationSection(
                "بخشی از",
                includedInClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            ${renderConceptRelationSection(
                "طبقه‌بندی",
                classificationClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            
            ${renderConceptRelationSection(
                "مشخصه‌ها",
                characterizedByClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            
            ${renderConceptRelationSection(
                "ارتباط با",
                linkedToClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            
            ${renderConceptRelationSection(
                "جایگاه سرمایه‌گذار",
                investorPositionClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            
            ${renderConceptRelationSection(
                "وابستگی بازده",
                returnDependsOnClaims,
                entityIndex,
                entityId,
                relationContract,
                evidenceList,
                sourceList
            )}
            
            ${renderEvidenceSection(
                conceptClaims,
                evidenceData,
                sourceData,
                entityIndex,
                entityId
            )}
        `;
    
        applyPageSEO({
            title:
                `${entity.name?.fa || ""} | اطلس | Private Capital`,
    
            description:
                `صفحه مفهوم ${entity.name?.fa || ""} در Private Capital.`,
    
            url: window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
        });
        injectJSONLD(
            buildConceptJSONLD(
                entity,
                entityId
            )
        );
    }
    function buildInvestmentJSONLD(
        entity,
        entityIndex,
        entityId,
        investmentClaims
    ) {
        const data = {
            "@context": "https://schema.org",
            "@type": "InvestmentOrDeposit",
            "name": entity.name?.fa || "",
            "identifier": {
                "@type": "PropertyValue",
                "propertyID": "PrivateCapitalAtlasID",
                "value": entity.id
            },
            "url": window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
        };
    
        if (entity.name?.en) {
            data.alternateName = entity.name.en;
        }
    
        const investorId =
            entity.metadata?.investor || null;
    
        const targetId =
            entity.metadata?.target || null;
    
        const investorName =
            investorId
                ? getEntityName(entityIndex, investorId)
                : "";
    
        const targetName =
            targetId
                ? getEntityName(entityIndex, targetId)
                : "";
    
        if (investorName) {
            data.provider = {
                "@type": "Organization",
                "name": investorName
            };
        }
    
        if (targetName) {
            data.recipient = {
                "@type": "Organization",
                "name": targetName
            };
        }
    
        const publishableAmountClaim =
            investmentClaims.find(
                claim =>
                    claim.predicate === "INVESTMENT_AMOUNT" &&
                    STRUCTURED_DATA_STATUSES.includes(
                        claim.status
                    ) &&
                    claim.value?.unit === "amount" &&
                    Number.isFinite(
                        Number(claim.value.amount)
                    )
            );
    
        if (publishableAmountClaim) {
            data.amount = {
                "@type": "MonetaryAmount",
                "value": Number(
                    publishableAmountClaim.value.amount
                ),
                "currency":
                    publishableAmountClaim.value.currency || ""
            };
        }
    
        return data;
    }
    async function renderInvestment(entityId) {
        const [
            entity,
            investmentClaims,
            registry
        ] = await Promise.all([
            loadCachedJSON(entityFilePath(entityId)),
            loadClaimsForEntity(entityId),
            loadCachedJSON(
                `${ATLAS_ROOT}/entities/index.json`
            )
            
        ]);
    
        const entityIndex = {};
    
        registry.entities.forEach(item => {
            entityIndex[item.id] = item;
        });
    
        const evidenceList =
            await loadEvidenceForClaims(investmentClaims);
    
        const sourceList =
            await loadSourcesForProvenance(evidenceList);
    
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
                ? entityURL(
                    investorId,
                    entityIndex[investorId]?.type
                )
                : null;
        
        const targetName =
            targetId
                ? getEntityName(entityIndex, targetId)
                : "";
        
        const targetURL =
            targetId
                ? entityURL(
                    targetId,
                    entityIndex[targetId]?.type
                )
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
                                                    entity.investment_status
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
    
            ${
                investmentClaims.filter(
                    claim =>
                        claim.predicate !== "INVESTMENT_AMOUNT"
                ).length
                    ? renderClaimsSection(
                        "روابط در یک نگاه",
                        investmentClaims.filter(
                            claim =>
                                claim.predicate !== "INVESTMENT_AMOUNT"
                        ),
                        entityIndex,
                        {},
                        { evidenceList, sourceList, entityId }
                    )
                    : ""
            }
    
            ${renderEvidenceSection(
                investmentClaims,
                evidenceData,
                sourceData,
                entityIndex,
                entityId
            )}
        `;
    
        applyPageSEO({
            title:
                `${entity.name?.fa || ""} | اطلس | Private Capital`,
    
            description:
                `صفحه سرمایه‌گذاری ${entity.name?.fa || ""} در Private Capital.`,
    
            url: window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
        });
        injectJSONLD(
            buildInvestmentJSONLD(
                entity,
                entityIndex,
                entityId,
                investmentClaims
            )
        );
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
            loadCachedJSON(
                `${ATLAS_ROOT}/entities/index.json`
            ),
            loadCachedJSON(
                `${ATLAS_ROOT}/content/persons/${entityId.split(":").slice(1).join(":")}.json`
            )
        ]);
        
        const evidenceList =
            await loadEvidenceForClaims(allClaims);
        
        const sourceList =
            await loadSourcesForProvenance(evidenceList, content);
        
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
    entityIndex,
    {},
    { evidenceList, sourceList, entityId }
)}

${renderClaimsSection(
    "سوابق اجرایی و مدیریتی",
    executiveClaims,
    entityIndex,
    {},
    { evidenceList, sourceList, entityId }
)}

${renderClaimsSection(
    "عضویت‌ها و نقش‌های هیئت‌مدیره",
    boardClaims,
    entityIndex,
    {},
    { evidenceList, sourceList, entityId }
)}

${renderClaimsSection(
    "فعالیت‌های سرمایه‌گذاری",
    investmentClaims,
    entityIndex,
    {},
    { evidenceList, sourceList, entityId }
)}

${
    relatedOrganizationClaims.length
        ? renderClaimsSection(
            "ساختار سازمانی مرتبط",
            relatedOrganizationClaims,
            entityIndex,
            {},
            { evidenceList, sourceList, entityId }
        )
        : ""
}

${renderContentSections(content, sourceData)}

${renderDataQualitySection(
    content,
    allClaims
)}

${renderEvidenceSection(
    allClaims,
    evidenceData,
    sourceData,
    entityIndex,
    entityId
)}

        `;
        applyPageSEO({
            title: `${entity.name?.fa || ""} | اطلس | Private Capital`,
            description: currentRoleClaim
                ? `${entity.name?.fa || ""}؛ ${relationLabel(currentRoleClaim.predicate)} ${getEntityName(entityIndex, currentRoleClaim.object)}.`
                : `صفحه اطلس ${entity.name?.fa || ""} در Private Capital.`,
            url: window.PrivateCapitalURL.entityCanonicalURL(entityId, entity.type)
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
            const atlasRoot = document.getElementById("atlas-root");

            if (atlasRoot?.dataset.staticRendered === "true") {
                return;
            }
            relationContract = await loadRelationContract();
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
