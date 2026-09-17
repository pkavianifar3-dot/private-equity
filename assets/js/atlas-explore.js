(function () {
    "use strict";

    const CATALOG_URL = "/atlas/catalog/index.json";
    const PAGE_SIZE = 12;

    const BROWSE_GROUPS = {
        actors: {
            label: "بازیگران",
            types: ["Person", "Organization", "OrganizationUnit"]
        },
        "capital-transactions": {
            label: "سرمایه و معاملات",
            types: ["Investment", "Fund"]
        },
        "business-projects": {
            label: "کسب‌وکار و پروژه‌ها",
            types: ["Organization", "Project"]
        },
        "concepts-domains": {
            label: "مفاهیم و حوزه‌ها",
            types: ["Concept", "Sector"]
        }
    };
    const TYPE_LABELS = {
        Person: "شخص",
        Organization: "سازمان",
        OrganizationUnit: "واحد سازمانی",
        Project: "پروژه",
        Investment: "سرمایه‌گذاری",
        Fund: "صندوق",
        Sector: "بخش",
        Concept: "مفهوم",
        InvestorCategory: "دسته سرمایه‌گذار"
    };

    const root = document.getElementById("atlas-explore-root");

    let catalog = [];
    let state = {
        query: "",
        type: "",
        group: "",
        page: 1
    };

    function escapeHTML(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function getStateFromURL() {
        const params = new URLSearchParams(window.location.search);

        const requestedPage = Number.parseInt(
            params.get("page") || "1",
            10
        );

        return {
            query: params.get("q") || "",
            type: params.get("type") || "",
            group: params.get("group") || "",
            page: Number.isInteger(requestedPage) && requestedPage > 0
                ? requestedPage
                : 1
        };
    }

    function updateURL() {
        const params = new URLSearchParams();

        if (state.query) {
            params.set("q", state.query);
        }

        if (state.type) {
            params.set("type", state.type);
        }

        if (state.group) {
            params.set("group", state.group);
        }

        if (state.page > 1) {
            params.set("page", String(state.page));
        }

        const queryString = params.toString();
        const url = queryString
            ? `${window.location.pathname}?${queryString}`
            : window.location.pathname;

        const currentURL =
            window.location.pathname + window.location.search;

        if (url !== currentURL) {
            window.history.pushState({}, "", url);
        }
    }

    function typeLabel(type) {
        return TYPE_LABELS[type] || type;
    }

    function matchesQuery(entity, query) {
        if (!query) {
            return true;
        }

        const normalizedQuery = query.toLocaleLowerCase();

        const fa = entity.name?.fa || "";
        const en = entity.name?.en || "";

        return (
            fa.toLocaleLowerCase().includes(normalizedQuery) ||
            en.toLocaleLowerCase().includes(normalizedQuery)
        );
    }

    function getFilteredEntities() {
        const group = BROWSE_GROUPS[state.group];

        return catalog.filter((entity) => {
            const matchesGroup =
                !group || group.types.includes(entity.type);

            const matchesType =
                !state.type || entity.type === state.type;

            const matchesSearch =
                matchesQuery(entity, state.query);

            return (
                matchesGroup &&
                matchesType &&
                matchesSearch
            );
        });
    }

    function renderSearch() {
        return `
            <div class="atlas-explore-search">
                <form id="atlas-explore-search-form">
                    <label for="atlas-explore-search-input">
                        جست‌وجو در اطلس
                    </label>

                    <div class="atlas-explore-search-row">
                        <input
                            id="atlas-explore-search-input"
                            name="q"
                            type="search"
                            value="${escapeHTML(state.query)}"
                            placeholder="نام فارسی یا انگلیسی را وارد کنید"
                            autocomplete="off"
                        >

                        <button type="submit">
                            جست‌وجو
                        </button>
                    </div>
                </form>
            </div>
        `;
    }

    function renderGroupFilters() {
        const groups = Object.entries(BROWSE_GROUPS);

        return `
            <div class="atlas-explore-groups">
                <div class="atlas-explore-groups-label">
                    فیلتر بر اساس گروه‌بندی کلی
                </div>

                <div class="atlas-explore-group-list">
                    <button
                        type="button"
                        class="${state.group === "" ? "is-active" : ""}"
                        data-group=""
                    >
                        همه
                    </button>

                    ${groups.map(([key, group]) => `
                        <button
                            type="button"
                            class="${state.group === key ? "is-active" : ""}"
                            data-group="${escapeHTML(key)}"
                        >
                            ${escapeHTML(group.label)}
                        </button>
                    `).join("")}
                </div>
            </div>
        `;
    }

    function renderTypeFilters() {
        const types = [...new Set(catalog.map((entity) => entity.type))];

        return `
            <div class="atlas-explore-type-filter">
                <div class="atlas-explore-type-filter-label">
                    فیلتر بر اساس نوع
                </div>

                <div class="atlas-explore-filters">
                    <button
                        type="button"
                        class="${state.type === "" ? "is-active" : ""}"
                        data-type=""
                    >
                        همه
                    </button>

                    ${types.map((type) => `
                        <button
                            type="button"
                            class="${state.type === type ? "is-active" : ""}"
                            data-type="${escapeHTML(type)}"
                        >
                            ${escapeHTML(typeLabel(type))}
                        </button>
                    `).join("")}
                </div>
            </div>
        `;
    }

    function renderActiveFilters() {
        const activeFilters = [];

        if (state.group && BROWSE_GROUPS[state.group]) {
            activeFilters.push(BROWSE_GROUPS[state.group].label);
        }

        if (state.type) {
            activeFilters.push(typeLabel(state.type));
        }

        if (!activeFilters.length) {
            return "";
        }

        return `
            <div class="atlas-explore-active-filters" aria-live="polite">
                <span class="atlas-explore-active-filters-label">
                    فیلترهای فعال:
                </span>
                <span class="atlas-explore-active-filters-value">
                    ${activeFilters.map(escapeHTML).join(" + ")}
                </span>
            </div>
        `;
    }

    function renderEntity(entity) {
        const nameFa = entity.name?.fa || entity.name?.en || entity.id;
        const nameEn = entity.name?.en || "";

        const content = `
            <article class="atlas-explore-result">
                <div class="atlas-explore-result-meta">
                    <span>${escapeHTML(typeLabel(entity.type))}</span>
                    <span>${escapeHTML(entity.lifecycleStatus)}</span>
                </div>

                <h3>
                    ${entity.route
                        ? `<a href="${escapeHTML(entity.route)}">${escapeHTML(nameFa)}</a>`
                        : escapeHTML(nameFa)
                    }
                </h3>

                ${nameEn ? `
                    <p class="atlas-explore-result-en">
                        ${escapeHTML(nameEn)}
                    </p>
                ` : ""}

                ${entity.route ? "" : `
                    <p class="atlas-explore-result-note">
                        صفحه جزئیات این نوع موجودیت هنوز در اطلس تعریف نشده است.
                    </p>
                `}
            </article>
        `;

        return content;
    }

    function renderPagination(totalPages, currentPage) {
        if (totalPages <= 1) {
            return "";
        }

        const previousPage = currentPage - 1;
        const nextPage = currentPage + 1;

        return `
            <nav class="atlas-explore-pagination" aria-label="صفحه‌بندی">
                <button
                    type="button"
                    data-page="${previousPage}"
                    ${currentPage === 1 ? "disabled" : ""}
                >
                    قبلی
                </button>

                <span>
                    صفحه ${currentPage} از ${totalPages}
                </span>

                <button
                    type="button"
                    data-page="${nextPage}"
                    ${currentPage === totalPages ? "disabled" : ""}
                >
                    بعدی
                </button>
            </nav>
        `;
    }

    function renderResults() {
        const entities = getFilteredEntities();

        if (!entities.length) {
            return `
                <div class="atlas-explore-empty">
                    <h2>نتیجه‌ای پیدا نشد</h2>
                    <p>
                        با تغییر عبارت جست‌وجو یا فیلتر نوع موجودیت دوباره تلاش کنید.
                    </p>
                </div>
            `;
        }

        const totalPages = Math.ceil(entities.length / PAGE_SIZE);
        const currentPage = Math.min(
            Math.max(state.page, 1),
            totalPages
        );

        state.page = currentPage;

        const startIndex = (currentPage - 1) * PAGE_SIZE;
        const visibleEntities = entities.slice(
            startIndex,
            startIndex + PAGE_SIZE
        );

        return `
            <div class="atlas-explore-summary">
                ${entities.length} نتیجه
            </div>

            <div class="atlas-explore-results">
                ${visibleEntities.map(renderEntity).join("")}
            </div>

            ${renderPagination(totalPages, currentPage)}
        `;
    }

    function render() {
        if (!root) {
            return;
        }

        root.innerHTML = `
            ${renderSearch()}
            ${renderGroupFilters()}
            ${renderTypeFilters()}
            ${renderActiveFilters()}
            ${renderResults()}
        `;

        bindEvents();
    }

    function bindEvents() {
        const form = document.getElementById(
            "atlas-explore-search-form"
        );

        const input = document.getElementById(
            "atlas-explore-search-input"
        );

        input?.addEventListener("input", () => {
            state.query = input.value.trim();
        });

        form?.addEventListener("submit", (event) => {
            event.preventDefault();

            state.query = input?.value.trim() || "";
            state.page = 1;
            updateURL();
            render();
        });

        root.querySelectorAll("[data-type]").forEach((button) => {
            button.addEventListener("click", () => {
                state.type = button.dataset.type || "";
                state.page = 1;
                updateURL();
                render();
            });
        });

        root.querySelectorAll("[data-group]").forEach((button) => {
            button.addEventListener("click", () => {
                state.group = button.dataset.group || "";

                const group = BROWSE_GROUPS[state.group];

                if (
                    state.type &&
                    group &&
                    !group.types.includes(state.type)
                ) {
                    state.type = "";
                }

                state.page = 1;
                updateURL();
                render();
            });
        });

        root.querySelectorAll("[data-page]").forEach((button) => {
            button.addEventListener("click", () => {
                const page = Number.parseInt(
                    button.dataset.page || "",
                    10
                );

                if (!Number.isInteger(page) || page < 1) {
                    return;
                }

                state.page = page;
                updateURL();
                render();
            });
        });
    }

    async function loadCatalog() {
        if (!root) {
            return;
        }

        try {
            const response = await fetch(CATALOG_URL, {
                cache: "no-store"
            });

            if (!response.ok) {
                throw new Error(
                    `Catalog request failed: ${response.status}`
                );
            }

            const data = await response.json();

            if (!Array.isArray(data.entities)) {
                throw new Error("Catalog format is invalid.");
            }

            catalog = data.entities;
            state = getStateFromURL();

            render();
        } catch (error) {
            console.error("Atlas Explore Error:", error);

            root.innerHTML = `
                <div class="atlas-explore-error">
                    <h2>اطلس در دسترس نیست</h2>
                    <p>
                        در بارگذاری فهرست اطلس مشکلی رخ داد.
                        لطفاً بعداً دوباره تلاش کنید.
                    </p>
                </div>
            `;
        }
    }

    window.AtlasExplore = {
        init: loadCatalog
    };

    window.addEventListener("popstate", () => {
        state = getStateFromURL();

        if (catalog.length) {
            render();
        }
    });

    loadCatalog();
})();
