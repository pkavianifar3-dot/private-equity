(function (global) {
    "use strict";

    const RESEARCH_PATH = "../research/content/private-capital.json";
    const SECTION_ID = "main-blocks";
    const TARGET_SELECTOR =
        '[data-article-renderer-section="main-blocks"]';

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

    async function renderMainBlocks() {
        const target = document.querySelector(TARGET_SELECTOR);

        if (!target) {
            throw new Error("Main-blocks render target not found");
        }

        const research = await loadResearch(RESEARCH_PATH);
        const section = getSection(research, SECTION_ID);
        const html = global.renderArticleContent([section]);

        const template = document.createElement("template");
        template.innerHTML = html;

        target.replaceWith(template.content);
    }

    renderMainBlocks().catch(error => {
        console.error("Article Research rendering failed:", error);
    });
})(window);
