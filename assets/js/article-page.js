(function (global) {
    "use strict";

    function getArticleSlug() {
        const pathname = global.location && global.location.pathname
            ? global.location.pathname
            : "";

        const filename = pathname.split("/").pop() || "";
        const slug = filename.replace(/\.html$/, "");

        if (!slug) {
            throw new Error("Article slug could not be determined from URL");
        }

        return slug;
    }

    function getResearchPath() {
        return `../research/content/${getArticleSlug()}.json`;
    }

    async function loadResearch(path) {
        const response = await fetch(path, {
            cache: "no-store"
        });

        if (!response.ok) {
            throw new Error(`Research data load failed: ${path}`);
        }

        return response.json();
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
        const researchPath = getResearchPath();
        const research = await loadResearch(researchPath);

        if (!research || !Array.isArray(research.sections)) {
            throw new TypeError("Research sections must be an array");
        }

        research.sections.forEach(renderSection);
    }

    renderArticleSections().catch(error => {
        console.error("Article Research rendering failed:", error);
    });
})(window);
