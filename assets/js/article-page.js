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

    const dataLoader = global.PrivateCapitalDataLoader.create("../atlas");
    const loadJSON = dataLoader.loadJSON;

    function getResearchPath() {
        return `../research/content/${getArticleSlug()}.json`;
    }

    async function loadResearch(path) {
        return loadJSON(path);
    }

    async function loadSources(sourceRefs) {
        if (!Array.isArray(sourceRefs) || !sourceRefs.length) {
            return [];
        }

        const index = await loadJSON("../atlas/sources/index.json");
        const sources = [];

        for (const sourceRef of sourceRefs) {
            const fileName = index.sources?.[sourceRef];

            if (!fileName) {
                continue;
            }

            const data = await loadJSON(
                `../atlas/sources/${fileName}`
            );

            const source = (data.sources || [])
                .find(item => item.id === sourceRef);

            if (source) {
                sources.push(source);
            }
        }

        return sources;
    }

    async function renderSection(
        section,
        citations,
        citationIndex,
        entityResolver
    ) {
        const target = document.querySelector(
            `[data-article-renderer-section="${section.id}"]`
        );

        if (!target) {
            throw new Error(
                `Article render target not found: ${section.id}`
            );
        }

        const sectionBlockIds = new Set(
            (Array.isArray(section.content) ? section.content : [])
                .map(block => block && block.id)
                .filter(Boolean)
        );

        const citationSourceRefs = Array.isArray(citations)
            ? [
                ...new Set(
                    citations
                        .filter(
                            citation =>
                                citation &&
                                sectionBlockIds.has(citation.contentBlockId)
                        )
                        .map(citation => citation.sourceRef)
                        .filter(Boolean)
                )
            ]
            : [];
        const sectionSourceRefs = Array.isArray(section.sourceRefs)
            ? section.sourceRefs
            : [];
        const sourceRefs = [
            ...new Set([...sectionSourceRefs, ...citationSourceRefs])
        ];
        const sources = await loadSources(sourceRefs);

        const html = global.renderArticleContent(
            [section],
            Array.isArray(section.mentions) ? section.mentions : [],
            sources,
            citations,
            citationIndex,
            entityResolver
        );

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

        const entityRegistry =
            await loadJSON("../atlas/entities/index.json");

        const entityResolver =
            global.PrivateCapitalEntityResolver.create(
                entityRegistry,
                global.PrivateCapitalURL
            );

        const citationIndex =
            global.PrivateCapitalCitationRenderer.buildCitationIndex(
                research.sections,
                research.citations
            );

        for (const section of research.sections) {
            await renderSection(
                section,
                research.citations,
                citationIndex,
                entityResolver
            );
        }

        const citationTarget = document.querySelector(
            "[data-article-renderer-citations]"
        );

        if (citationTarget) {
            const citationSourceRefs = Array.isArray(research.citations)
                ? [
                    ...new Set(
                        research.citations
                            .map(citation => citation && citation.sourceRef)
                            .filter(Boolean)
                    )
                ]
                : [];

            const citationSources = await loadSources(citationSourceRefs);

            citationTarget.innerHTML =
                global.PrivateCapitalCitationRenderer.renderCitationBibliographyHtml(
                    research.citations,
                    citationSources,
                    citationIndex
                );
        }
    }

    renderArticleSections().catch(error => {
        console.error("Article Research rendering failed:", error);
    });
})(window);
