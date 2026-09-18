(() => {
    const CATALOG_URL = "/atlas/catalog/index.json";
    const CONCEPT_LIMIT = 6;

    const root = document.getElementById("atlas-home-concepts-root");

    if (!root) {
        return;
    }

    function escapeHtml(value) {
        return String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function renderConcepts(items) {
        if (!items.length) {
            root.innerHTML = `
                <div class="atlas-explore-empty">
                    <h2>مفهومی برای نمایش وجود ندارد</h2>
                </div>
            `;
            return;
        }

        root.innerHTML = items
            .map((item) => {
                const nameFa = item.name?.fa || item.id;
                const nameEn = item.name?.en || "";

                if (item.route) {
                    return `
                        <a
                            class="atlas-home-concept"
                            href="${escapeHtml(item.route)}"
                        >
                            <span class="atlas-home-concept-name">
                                ${escapeHtml(nameFa)}
                            </span>

                            ${
                                nameEn
                                    ? `<span class="atlas-home-concept-en">${escapeHtml(nameEn)}</span>`
                                    : ""
                            }
                        </a>
                    `;
                }

                return `
                    <div class="atlas-home-concept">
                        <span class="atlas-home-concept-name">
                            ${escapeHtml(nameFa)}
                        </span>

                        ${
                            nameEn
                                ? `<span class="atlas-home-concept-en">${escapeHtml(nameEn)}</span>`
                                : ""
                        }
                    </div>
                `;
            })
            .join("");
    }

    async function loadConcepts() {
        try {
            const response = await fetch(CATALOG_URL, {
                cache: "no-store"
            });

            if (!response.ok) {
                throw new Error(`Catalog request failed: ${response.status}`);
            }

            const catalog = await response.json();

            const items = Array.isArray(catalog)
                ? catalog
                : Array.isArray(catalog.entities)
                    ? catalog.entities
                    : [];

            const concepts = items.filter(
                (item) => item.type === "Concept"
            );

            concepts.sort((a, b) => {
                const aName = a.name?.fa || a.name?.en || a.id || "";
                const bName = b.name?.fa || b.name?.en || b.id || "";

                return aName.localeCompare(bName, "fa");
            });

            renderConcepts(concepts.slice(0, CONCEPT_LIMIT));
        } catch (error) {
            console.error("Atlas Home: failed to load concepts.", error);

            root.innerHTML = `
                <div class="atlas-explore-error">
                    <h2>بارگذاری مفاهیم انجام نشد</h2>
                    <p>
                        فهرست مفاهیم در حال حاضر در دسترس نیست.
                    </p>
                </div>
            `;
        }
    }

    loadConcepts();
})();
