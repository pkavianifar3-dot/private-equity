(function () {
    "use strict";

    const ATLAS_ROOT = "atlas";

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

    function formatDate(date) {
        if (!date) return "";

        if (date === "present") {
            return "اکنون";
        }

        return escapeHTML(date);
    }

    function getEntityIdFromURL() {
        const params = new URLSearchParams(window.location.search);
        return params.get("id");
    }

    function entityFilePath(entityId) {
        const [type, slug] = entityId.split(":");

        if (!type || !slug) {
            throw new Error("Invalid Atlas entity ID.");
        }

        switch (type) {
            case "person":
                return `${ATLAS_ROOT}/entities/persons/${slug}.json`;

            case "organization":
                return `${ATLAS_ROOT}/entities/organizations/${slug}.json`;

            default:
                throw new Error(`Unsupported Atlas entity type: ${type}`);
        }
    }

    function claimsFilePath(entityId) {
        const [type, slug] = entityId.split(":");

        if (type !== "person") {
            throw new Error("Claim loading currently supports Person entities only.");
        }

        return `${ATLAS_ROOT}/claims/${slug}.json`;
    }

    function renderError(message) {
        const root = document.getElementById("atlas-root");

        if (!root) return;

        root.innerHTML = `
            <div class="card">
                <h3>خطا در بارگذاری اطلس</h3>
                <p>${escapeHTML(message)}</p>
            </div>
        `;
    }

    function relationLabel(predicate) {
        const labels = {
            "CEO_OF": "مدیرعامل",
            "EXECUTIVE_ROLE_AT": "سمت اجرایی",
            "BOARD_MEMBER_OF": "عضو هیئت‌مدیره",
            "CHAIR_OF": "رئیس",
            "VICE_CHAIR_OF": "نایب‌رئیس",
            "BOARD_SECRETARY_OF": "دبیر هیئت‌مدیره",
            "WORKED_AT": "فعالیت در",
            "SUBSIDIARY_OF": "زیرمجموعه",
            "OPERATES_IN": "فعالیت در حوزه",
            "HAS_PROJECT": "پروژه"
        };

        return labels[predicate] || predicate;
    }

    function statusLabel(status) {
        const labels = {
            "VERIFIED": "تأییدشده",
            "SUPPORTED": "پشتیبانی‌شده",
            "REPORTED": "گزارش‌شده",
            "DISPUTED": "مورد اختلاف"
        };

        return labels[status] || status;
    }

    function renderClaim(claim, entityIndex) {
        const object = entityIndex[claim.object];

        if (!object) {
            return "";
        }

        let meta = "";

        if (claim.temporal) {
            const start = formatDate(claim.temporal.start);
            const end = claim.temporal.end
                ? formatDate(claim.temporal.end)
                : (claim.temporal.status === "current" ? "اکنون" : "");

            if (start || end) {
                meta = `
                    <div class="atlas-claim-meta">
                        ${start}${start && end ? " — " : ""}${end}
                    </div>
                `;
            }
        }

        return `
            <div class="card atlas-claim">
                <h3>${escapeHTML(relationLabel(claim.predicate))}</h3>

                <p class="atlas-object-name">
                    ${escapeHTML(object.name.fa)}
                </p>

                ${claim.role ? `
                    <p>
                        <strong>نقش:</strong>
                        ${escapeHTML(claim.role)}
                    </p>
                ` : ""}

                ${meta}

                <p class="atlas-claim-status">
                    ${escapeHTML(statusLabel(claim.status))}
                </p>
            </div>
        `;
    }

    async function renderPerson(entityId) {
        const entity = await loadJSON(entityFilePath(entityId));
        const claimsData = await loadJSON(claimsFilePath(entityId));
        const registry = await loadJSON(`${ATLAS_ROOT}/entities/index.json`);

        const entityIndex = {};

        registry.entities.forEach(item => {
            entityIndex[item.id] = item;
        });

        const root = document.getElementById("atlas-root");

        if (!root) {
            throw new Error("Atlas root element not found.");
        }

        const claimsHTML = claimsData.claims
            .map(claim => renderClaim(claim, entityIndex))
            .filter(Boolean)
            .join("");

        root.innerHTML = `
            <section class="page-hero">
                <div class="container">
                    <h1>${escapeHTML(entity.name.fa)}</h1>
                    <p>${escapeHTML(entity.name.en)}</p>
                </div>
            </section>

            <section>
                <div class="container">

                    <div class="card atlas-identity-card">

                        <h2>شناسه</h2>

                        <p>
                            <strong>نام:</strong>
                            ${escapeHTML(entity.name.fa)}
                        </p>

                        <p>
                            <strong>نام انگلیسی:</strong>
                            ${escapeHTML(entity.name.en)}
                        </p>

                        ${entity.honorific && entity.honorific.fa ? `
                            <p>
                                <strong>عنوان:</strong>
                                ${escapeHTML(entity.honorific.fa)}
                            </p>
                        ` : ""}

                    </div>

                </div>
            </section>

            <section>
                <div class="container">

                    <h2>سوابق و روابط</h2>

                    <div class="grid">
                        ${claimsHTML || `
                            <div class="card">
                                <p>هنوز داده‌ای برای نمایش ثبت نشده است.</p>
                            </div>
                        `}
                    </div>

                </div>
            </section>
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

            throw new Error("Entity type is not supported yet.");

        } catch (error) {
            console.error("Atlas Renderer Error:", error);
            renderError(error.message);
        }
    }

    window.Atlas = {
        init: initAtlas
    };
})();
