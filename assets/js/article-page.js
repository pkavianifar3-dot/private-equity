(function (global) {
    "use strict";

    const RESEARCH_PATH = "../research/content/private-capital.json";
    const SECTION_IDS = ["introduction", "definition-and-scope", "main-blocks", "private-equity", "private-credit"];

    async function loadResearch(path) {
        const response = await fetch(path, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Research data load failed: ${path}`);
        }

        return response.json();
    }

    function getSection(research, sectionId) {
        if (!research || !Array.isArray(research.sections)) {
            throw new TypeError("Research sections must be an array");
        }

        const section = research.sections.find(
            item => item.id === sectionId
        );

        if (!section) {
            throw new Error(`Research section not found: ${sectionId}`);
        }

        return section;
    }

    function renderSection(section) {
        const target = document.querySelector(
            `[data-article-renderer-section="${section.id}"]`
        );

        if (!target) {
            throw new Error(
                `Article render target not found: ${section.id}`
            );
        }

        const html = global.renderArticleContent([section]);

        const template = document.createElement("template");
        template.innerHTML = html;

        target.replaceWith(template.content);
    }

    async function renderArticleSections() {
        const research = await loadResearch(RESEARCH_PATH);

        SECTION_IDS.forEach(sectionId => {
            renderSection(getSection(research, sectionId));
        });
    }

    renderArticleSections().catch(error => {
        console.error("Article Research rendering failed:", error);
    });
})(window);
