const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const urlResolverSource = fs.readFileSync(
    "assets/js/core/url-resolver.js",
    "utf8"
);

const citationRendererSource = fs.readFileSync("assets/js/research/citation-renderer.js", "utf8");
const entityResolverSource = fs.readFileSync(
    "assets/js/core/entity-resolver.js",
    "utf8"
);

const rendererSource = fs.readFileSync(
    "assets/js/article-renderer.js",
    "utf8"
);

const context = {
    console,
};
context.window = context;

vm.createContext(context);
vm.runInContext(urlResolverSource, context);
vm.runInContext(entityResolverSource, context);
vm.runInContext(citationRendererSource, context);
vm.runInContext(rendererSource, context);

const { renderArticleContent } = context;

assert.strictEqual(
    typeof renderArticleContent,
    "function",
    "renderArticleContent must be a function"
);

const html = renderArticleContent([
    {
        id: "test-section",
        title: { fa: "بخش آزمون" },
        content: [
            {
                id: "paragraph-01",
                type: "paragraph",
                text: "متن آزمون"
            },
            {
                id: "subheading-01",
                type: "subheading",
                text: "زیرعنوان آزمون"
            },
            {
                id: "figure-01",
                type: "figure",
                src: "../assets/images/test.png",
                alt: "تصویر آزمون",
                caption: "شرح تصویر"
            },
            {
                id: "list-01",
                type: "list",
                items: ["مورد اول", "مورد دوم"]
            },
            {
                id: "table-01",
                type: "table",
                rows: [
                    ["عنوان", "مقدار"],
                    ["الف", "۱"]
                ]
            }
        ]
    }
]);

assert(html.includes("<p>متن آزمون</p>"));
assert(html.includes("<h3>زیرعنوان آزمون</h3>"));
assert(html.includes('src="../assets/images/test.png"'));
assert(html.includes("<figcaption>شرح تصویر</figcaption>"));
assert(html.includes("<li>مورد اول</li>"));
assert(html.includes("<li>مورد دوم</li>"));
assert(html.includes("<table>"));
assert(html.includes("<td>عنوان</td>"));
assert(html.includes("<td>۱</td>"));

console.log("Article Renderer behavior PASSED");

const research = JSON.parse(
    fs.readFileSync(
        "research/content/private-capital.json",
        "utf8"
    )
);
const entityRegistry = JSON.parse(
    fs.readFileSync(
        "atlas/entities/index.json",
        "utf8"
    )
);

const realEntityResolver =
    context.PrivateCapitalEntityResolver.create(
        entityRegistry,
        context.PrivateCapitalURL
    );
const renderedResearchContent = renderArticleContent(
    research.sections
);

const expectedBlockCount = research.sections.reduce(
    (total, section) => total + section.content.length,
    0
);

const renderedParagraphCount =
    (renderedResearchContent.match(/<p>/g) || []).length;

const renderedFigureCount =
    (renderedResearchContent.match(/<figure>/g) || []).length;

const renderedSubheadingCount =
    (renderedResearchContent.match(/<h3>/g) || []).length;

assert.strictEqual(
    renderedParagraphCount,
    23,
    "Research renderer must render 23 paragraphs"
);

assert.strictEqual(
    renderedFigureCount,
    2,
    "Research renderer must render 2 figures"
);

assert.strictEqual(
    renderedSubheadingCount,
    5,
    "Research renderer must render 5 subheadings"
);

assert.strictEqual(
    renderedParagraphCount +
        renderedFigureCount +
        renderedSubheadingCount,
    expectedBlockCount,
    "Rendered block count must match Research block count"
);

assert(
    renderedResearchContent.indexOf(
        "intro-paragraph-01"
    ) === -1,
    "Block IDs must not leak into rendered HTML"
);

console.log("Article Renderer Research E2E contract PASSED");

assert(
    renderedResearchContent.startsWith("<p>"),
    "Rendered Research content must start with the first content block"
);

assert(
    renderedResearchContent.includes(
        "../assets/images/private-capital.png"
    ),
    "Rendered Research content must include the Research hero figure"
);

assert(
    renderedResearchContent.includes(
        "../assets/images/2026-08-13-private-capital-structure.png.png"
    ),
    "Rendered Research content must include the Research structure figure"
);

assert(
    renderedResearchContent.indexOf(
        "<p>از آنجا که سرمایه خصوصی"
    ) >
    renderedResearchContent.indexOf(
        "<p>«سرمایه خصوصی»"
    ),
    "Research block order must be preserved"
);

console.log("Article Renderer ordering and asset contract PASSED");

const introduction = research.sections.find(
    section => section.id === "introduction"
);

assert(introduction, "Research introduction section must exist");

const introductionHtml = renderArticleContent([introduction]);

assert.strictEqual(
    (introductionHtml.match(/<p>/g) || []).length,
    2,
    "Introduction must render exactly 2 paragraphs"
);

assert.strictEqual(
    (introductionHtml.match(/<figure>/g) || []).length,
    1,
    "Introduction must render exactly 1 figure"
);

assert(
    introductionHtml.indexOf(
        "<p>«سرمایه خصوصی» (Private Capital)"
    ) !== -1,
    "Introduction first paragraph must come from Research"
);

assert(
    introductionHtml.indexOf(
        "<p>«سرمایه خصوصی» (Private Capital)"
    ) <
    introductionHtml.indexOf(
        "<p>از آنجا که سرمایه خصوصی"
    ),
    "Introduction paragraph order must follow Research"
);

assert(
    introductionHtml.indexOf(
        "<figure>"
    ) >
    introductionHtml.indexOf(
        "<p>از آنجا که سرمایه خصوصی"
    ),
    "Introduction figure must follow Research block order"
);

console.log("Article Renderer introduction pilot contract PASSED");

{
    const definition = research.sections.find(
        section => section.id === "definition-and-scope"
    );

    assert(definition, "Research definition-and-scope section must exist");

    const definitionHtml = renderArticleContent([definition]);

    assert.strictEqual(
        (definitionHtml.match(/<h3>/g) || []).length,
        1,
        "definition-and-scope pilot must render exactly one subheading"
    );

    assert.strictEqual(
        (definitionHtml.match(/<p>/g) || []).length,
        3,
        "definition-and-scope pilot must render exactly three paragraphs"
    );

    assert.strictEqual(
        (definitionHtml.match(/<figure>/g) || []).length,
        1,
        "definition-and-scope pilot must render exactly one figure"
    );

    assert(
        definitionHtml.includes("تعریف و دامنه سرمایه خصوصی"),
        "definition-and-scope pilot must render the Research subheading"
    );

    const headingIndex = definitionHtml.indexOf("<h3>");
    const firstParagraphIndex = definitionHtml.indexOf("<p>");
    const figureIndex = definitionHtml.indexOf("<figure>");

    assert(
        headingIndex < firstParagraphIndex &&
        firstParagraphIndex < figureIndex,
        "definition-and-scope block order must follow Research"
    );

    assert(
        !definitionHtml.includes('class="cta"'),
        "definition-and-scope pilot must not absorb the CTA"
    );

    assert(
        !definitionHtml.includes("بلوک‌های اصلی سرمایه خصوصی"),
        "definition-and-scope pilot must not absorb the next section"
    );
}

console.log("Article Renderer definition-and-scope pilot contract PASSED");

{
    const mainBlocks = research.sections.find(
        section => section.id === "main-blocks"
    );

    assert(mainBlocks, "Research main-blocks section must exist");

    const mainBlocksHtml = renderArticleContent([mainBlocks]);

    assert.strictEqual(
        (mainBlocksHtml.match(/<p>/g) || []).length,
        1,
        "main-blocks pilot must render exactly one paragraph"
    );

    assert(
        mainBlocksHtml.includes(
            "در یک طبقه‌بندی عملیاتی، «سرمایه خصوصی» را می‌توان در پنج بلوک اصلی دید"
        ),
        "main-blocks pilot must render the Research paragraph"
    );

    assert(
        !mainBlocksHtml.includes("سرمایه‌گذاری خصوصی (Private Equity)</h3>"),
        "main-blocks pilot must not absorb the next section"
    );
}

console.log("Article Renderer main-blocks pilot contract PASSED");

{
    const mainBlocks = research.sections.find(
        section => section.id === "main-blocks"
    );

    assert(mainBlocks, "Research main-blocks section must exist");

    const mainBlocksText = mainBlocks.content
        .filter(block => block.type === "paragraph")
        .map(block => block.text)
        .join("\n");

    assert.strictEqual(
        mainBlocksText.trim(),
        `در یک طبقه‌بندی عملیاتی، «سرمایه خصوصی» را می‌توان در پنج بلوک اصلی دید: «سرمایه‌گذاری خصوصی»، «سرمایه‌گذاری خطرپذیر»، «سرمایه رشد»، «اعتبار خصوصی» و «دارایی‌های واقعی». مرزبندی دقیق میان این بلوک‌ها در منابع مختلف یکسان نیست و برخی منابع، از جمله در موضوع «اعتبار خصوصی»، دامنه متفاوتی از وام‌دهی مستقیم تا اعتبارات مبتنی بر دارایی را در گزارش‌های خود منظور می‌کنند.`,
        "main-blocks Research content must match the legacy paragraph exactly"
    );
}

console.log("Article Renderer main-blocks legacy parity PASSED");


{
    const privateEquity = research.sections.find(
        section => section.id === "private-equity"
    );

    assert(privateEquity, "Research private-equity section must exist");

    const privateCapitalHtml = fs.readFileSync(
        "tests/fixtures/private-capital-legacy.html",
        "utf8"
    );

    const start = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="private-equity">'
    );
    const end = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="private-credit">',
        start
    );

    assert(start >= 0, "Legacy private-equity section wrapper must exist");
    assert(end > start, "Legacy private-equity section boundary must be valid");

    const legacySection = privateCapitalHtml.slice(start, end);
    const legacyTexts = [...legacySection.matchAll(/<p>\s*([\s\S]*?)\s*<\/p>/g)]
        .map(match => match[1].trim());

    const researchTexts = privateEquity.content
        .filter(block => block.type === "paragraph")
        .map(block => block.text);

    assert.strictEqual(
        legacyTexts.length,
        researchTexts.length,
        "private-equity legacy and Research paragraph counts must match"
    );

    assert.deepStrictEqual(
        legacyTexts,
        researchTexts,
        "private-equity Research content must match the legacy paragraphs exactly"
    );
}

{
    const privateCredit = research.sections.find(
        section => section.id === "private-credit"
    );

    assert(privateCredit, "Research private-credit section must exist");

    const privateCapitalHtml = fs.readFileSync(
        "tests/fixtures/private-capital-legacy.html",
        "utf8"
    );

    const start = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="private-credit">'
    );
    const end = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="real-assets">',
        start
    );

    assert(start >= 0, "Legacy private-credit section wrapper must exist");
    assert(end > start, "Legacy private-credit section boundary must be valid");

    const legacySection = privateCapitalHtml.slice(start, end);
    const legacyTexts = [...legacySection.matchAll(/<p>\s*([\s\S]*?)\s*<\/p>/g)]
        .map(match => match[1].trim());

    const researchTexts = privateCredit.content
        .filter(block => block.type === "paragraph")
        .map(block => block.text);

    assert.strictEqual(
        legacyTexts.length,
        researchTexts.length,
        "private-credit legacy and Research paragraph counts must match"
    );

    assert.deepStrictEqual(
        legacyTexts,
        researchTexts,
        "private-credit Research content must match the legacy paragraphs exactly"
    );
}

{
    const realAssets = research.sections.find(
        section => section.id === "real-assets"
    );

    assert(realAssets, "Research real-assets section must exist");

    const privateCapitalHtml = fs.readFileSync(
        "tests/fixtures/private-capital-legacy.html",
        "utf8"
    );

    const start = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="real-assets">'
    );
    const end = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="conclusion">',
        start
    );

    assert(start >= 0, "Legacy real-assets section wrapper must exist");
    assert(end > start, "Legacy real-assets section boundary must be valid");

    const legacySection = privateCapitalHtml.slice(start, end);
    const legacyTexts = [...legacySection.matchAll(/<p>\s*([\s\S]*?)\s*<\/p>/g)]
        .map(match => match[1].trim());

    const researchTexts = realAssets.content
        .filter(block => block.type === "paragraph")
        .map(block => block.text);

    assert.strictEqual(
        legacyTexts.length,
        researchTexts.length,
        "real-assets legacy and Research paragraph counts must match"
    );

    assert.deepStrictEqual(
        legacyTexts,
        researchTexts,
        "real-assets Research content must match the legacy paragraphs exactly"
    );
}

console.log("Article Renderer real-assets legacy parity PASSED");

console.log("Article Renderer private-credit legacy parity PASSED");

console.log("Article Renderer private-equity legacy parity PASSED");

{
    const conclusion = research.sections.find(
        section => section.id === "conclusion"
    );

    assert(conclusion, "Research conclusion section must exist");

    const privateCapitalHtml = fs.readFileSync(
        "tests/fixtures/private-capital-legacy.html",
        "utf8"
    );

    const start = privateCapitalHtml.indexOf(
        '<div data-article-renderer-section="conclusion">'
    );
    const end = privateCapitalHtml.indexOf(
        '<div class="cta"',
        start
    );

    assert(start >= 0, "Legacy conclusion section wrapper must exist");
    assert(end > start, "Legacy conclusion section boundary must be valid");

    const legacySection = privateCapitalHtml.slice(start, end);
    const legacyTexts = [...legacySection.matchAll(/<p>\s*([\s\S]*?)\s*<\/p>/g)]
        .map(match => match[1].trim());

    const researchTexts = conclusion.content
        .filter(block => block.type === "paragraph")
        .map(block => block.text);

    assert.strictEqual(
        legacyTexts.length,
        researchTexts.length,
        "conclusion legacy and Research paragraph counts must match"
    );

    assert.deepStrictEqual(
        legacyTexts,
        researchTexts,
        "conclusion Research content must match the legacy paragraphs exactly"
    );
}

console.log("Article Renderer conclusion legacy parity PASSED");

{
    const introduction = research.sections.find(
        section => section.id === "introduction"
    );

    assert(introduction, "Research introduction section must exist");

    const mentionHtml = renderArticleContent(
        [introduction],
        introduction.mentions,
        [],
        [],
        null,
        realEntityResolver
    );

    assert(
        mentionHtml.includes(
            '<a href="/atlas/concept/private-equity/">سرمایه‌گذاری خصوصی</a>'
        ),
        "Resolved Research Mention must link to the canonical Atlas concept"
    );

    assert.strictEqual(
        (mentionHtml.match(/<a href=/g) || []).length,
        3,
        "Introduction pilot must render exactly three resolved entity links"
    );

    console.log("Article Renderer resolved Mention contract PASSED");
}

{
    const section = {
        id: "mention-status-test",
        content: [
            {
                id: "paragraph-resolved",
                type: "paragraph",
                text: "سرمایه‌گذاری خصوصی"
            },
            {
                id: "paragraph-unresolved",
                type: "paragraph",
                text: "سرمایه‌گذاری خطرپذیر"
            },
            {
                id: "paragraph-rejected",
                type: "paragraph",
                text: "اعتبار خصوصی"
            }
        ],
        mentions: [
            {
                id: "mention-resolved",
                text: "سرمایه‌گذاری خصوصی",
                entityRef: "concept:private-equity",
                contentBlockId: "paragraph-resolved",
                start: 0,
                end: 18,
                resolutionStatus: "RESOLVED"
            },
            {
                id: "mention-unresolved",
                text: "سرمایه‌گذاری خطرپذیر",
                entityRef: "concept:venture-capital",
                contentBlockId: "paragraph-unresolved",
                start: 0,
                end: 21,
                resolutionStatus: "UNRESOLVED"
            },
            {
                id: "mention-rejected",
                text: "اعتبار خصوصی",
                entityRef: "concept:private-credit",
                contentBlockId: "paragraph-rejected",
                start: 0,
                end: 13,
                resolutionStatus: "REJECTED"
            }
        ]
    };

    const html = renderArticleContent(
        [section],
        section.mentions,
        [],
        [],
        null,
        realEntityResolver
    );

    assert.strictEqual(
        (html.match(/<a href=/g) || []).length,
        1,
        "Only RESOLVED supported Mentions must become links"
    );

    assert(
        html.includes("سرمایه‌گذاری خطرپذیر</p>"),
        "UNRESOLVED Mention must remain plain text"
    );

    assert(
        html.includes("اعتبار خصوصی</p>"),
        "REJECTED Mention must remain plain text"
    );

    console.log("Article Renderer Mention status contract PASSED");
}

{
    const section = {
        id: "mention-safety-test",
        content: [
            {
                id: "paragraph-invalid-range",
                type: "paragraph",
                text: "<b>سرمایه‌گذاری خصوصی</b>"
            }
        ],
        mentions: [
            {
                id: "mention-invalid-range",
                text: "سرمایه‌گذاری خصوصی",
                entityRef: "concept:private-equity",
                contentBlockId: "paragraph-invalid-range",
                start: 999,
                end: 1018,
                resolutionStatus: "RESOLVED"
            }
        ]
    };

    const html = renderArticleContent(
        [section],
        section.mentions
    );

    assert(
        html.includes(
            "&lt;b&gt;سرمایه‌گذاری خصوصی&lt;/b&gt;"
        ),
        "Invalid Mention range must preserve escaped text"
    );

    assert.strictEqual(
        (html.match(/<a href=/g) || []).length,
        0,
        "Invalid Mention range must not create a link"
    );

    console.log("Article Renderer Mention safety contract PASSED");
}

{
    const section = {
        id: "mention-resolver-injection-test",
        content: [
            {
                id: "paragraph-resolver-injection",
                type: "paragraph",
                text: "سرمایه‌گذاری خصوصی"
            }
        ],
        mentions: [
            {
                id: "mention-resolver-injection",
                text: "سرمایه‌گذاری خصوصی",
                entityRef: "concept:private-equity",
                contentBlockId: "paragraph-resolver-injection",
                start: 0,
                end: 18,
                resolutionStatus: "RESOLVED"
            }
        ]
    };

    const injectedResolver = {
        resolve(entityRef, contextName) {
            assert.strictEqual(
                entityRef,
                "concept:private-equity"
            );
            assert.strictEqual(
                contextName,
                "research"
            );

            return {
                entity: {
                    id: entityRef
                },
                url: "../atlas/injected-entity.html?id=concept%3Aprivate-equity"
            };
        }
    };

    const html = renderArticleContent(
        [section],
        section.mentions,
        [],
        [],
        null,
        injectedResolver
    );

    assert(
        html.includes(
            '<a href="../atlas/injected-entity.html?id=concept%3Aprivate-equity">سرمایه‌گذاری خصوصی</a>'
        ),
        "Renderer must use the injected Entity Resolver URL"
    );

    console.log("Article Renderer Entity Resolver injection PASSED");
}
{
    const resolvedMentions = research.sections.flatMap(
        section =>
            (Array.isArray(section.mentions)
                ? section.mentions
                : []
            ).filter(
                mention =>
                    mention &&
                    mention.resolutionStatus === "RESOLVED"
            )
    );

    assert(
        resolvedMentions.length > 0,
        "Research must contain at least one RESOLVED Mention for F7 E2E"
    );

    for (const mention of resolvedMentions) {
        const section = research.sections.find(
            item =>
                Array.isArray(item.mentions) &&
                item.mentions.some(
                    candidate => candidate.id === mention.id
                )
        );

        assert(
            section,
            `${mention.id}: owning Research section must exist`
        );

        const block = (section.content || []).find(
            contentBlock =>
                contentBlock &&
                contentBlock.id === mention.contentBlockId
        );

        assert(
            block,
            `${mention.id}: contentBlockId must resolve to a Research content block`
        );

        assert.strictEqual(
            typeof block.text,
            "string",
            `${mention.id}: Mention content block must contain text`
        );

        const matchedText = block.text.slice(
            mention.start,
            mention.end
        );

        assert.strictEqual(
            matchedText,
            mention.text,
            `${mention.id}: Mention range must match its text`
        );

        const resolved =
            realEntityResolver.resolve(
                mention.entityRef,
                "research"
            );

        assert(
            resolved,
            `${mention.id}: Entity Resolver must resolve ${mention.entityRef}`
        );

        assert.strictEqual(
            resolved.entity.id,
            mention.entityRef,
            `${mention.id}: Resolver must return the canonical Entity`
        );

        assert(
            resolved.url,
            `${mention.id}: Resolver must return a canonical route URL`
        );

        const html = renderArticleContent(
            [section],
            section.mentions,
            [],
            [],
            null,
            realEntityResolver
        );

        const expectedLink =
            `<a href="${resolved.url}">${mention.text}</a>`;

        assert(
            html.includes(expectedLink),
            `${mention.id}: RESOLVED Mention must render as a canonical semantic link`
        );
    }

    console.log(
        `Article Renderer real Research → Mention → Entity → URL → Link E2E PASSED (${resolvedMentions.length} resolved mention${resolvedMentions.length === 1 ? "" : "s"})`
    );
}

{
    const section = {
        id: "mention-unknown-entity-test",
        content: [
            {
                id: "paragraph-unknown-entity",
                type: "paragraph",
                text: "Unknown Entity"
            }
        ],
        mentions: [
            {
                id: "mention-unknown-entity",
                text: "Unknown Entity",
                entityRef: "concept:does-not-exist",
                contentBlockId: "paragraph-unknown-entity",
                start: 0,
                end: 14,
                resolutionStatus: "RESOLVED"
            }
        ]
    };

    const html = renderArticleContent(
        [section],
        section.mentions,
        [],
        [],
        null,
        realEntityResolver
    );

    assert(
        html.includes("<p>Unknown Entity</p>"),
        "Unknown resolved Entity must remain plain text"
    );

    assert.strictEqual(
        (html.match(/<a href=/g) || []).length,
        0,
        "Unknown resolved Entity must not create a link"
    );

    console.log("Article Renderer unknown Entity safety PASSED");
}

{
    const section = {
        id: "mention-escaping-test",
        content: [
            {
                id: "paragraph-escaping",
                type: "paragraph",
                text: "<strong>Tag</strong>"
            }
        ],
        mentions: [
            {
                id: "mention-escaping",
                text: "<strong>Tag</strong>",
                entityRef: "concept:private-equity",
                contentBlockId: "paragraph-escaping",
                start: 0,
                end: 20,
                resolutionStatus: "RESOLVED"
            }
        ]
    };

    const injectedResolver = {
        resolve(entityRef, contextName) {
            assert.strictEqual(entityRef, "concept:private-equity");
            assert.strictEqual(contextName, "research");

            return {
                entity: {
                    id: entityRef
                },
                url: "/atlas/test?x=1&y=2"
            };
        }
    };

    const html = renderArticleContent(
        [section],
        section.mentions,
        [],
        [],
        null,
        injectedResolver
    );

    assert(
        html.includes(
            '<a href="/atlas/test?x=1&amp;y=2">&lt;strong&gt;Tag&lt;/strong&gt;</a>'
        ),
        "Mention text and URL must be HTML-escaped"
    );

    console.log("Article Renderer Mention escaping PASSED");
}

{
    const section = {
        id: "mention-overlap-test",
        content: [
            {
                id: "paragraph-overlap",
                type: "paragraph",
                text: "ABCDEFGH"
            }
        ],
        mentions: [
            {
                id: "mention-overlap-first",
                text: "ABCD",
                entityRef: "concept:first",
                contentBlockId: "paragraph-overlap",
                start: 0,
                end: 4,
                resolutionStatus: "RESOLVED"
            },
            {
                id: "mention-overlap-second",
                text: "CDEF",
                entityRef: "concept:second",
                contentBlockId: "paragraph-overlap",
                start: 2,
                end: 6,
                resolutionStatus: "RESOLVED"
            }
        ]
    };

    const injectedResolver = {
        resolve(entityRef) {
            return {
                entity: {
                    id: entityRef
                },
                url: `/atlas/test/${entityRef}`
            };
        }
    };

    const html = renderArticleContent(
        [section],
        section.mentions,
        [],
        [],
        null,
        injectedResolver
    );

    assert(
        html.includes(
            '<p><a href="/atlas/test/concept:first">ABCD</a>EFGH</p>'
        ),
        "Overlapping Mentions must render deterministically without corrupting text"
    );

    assert.strictEqual(
        (html.match(/<a href=/g) || []).length,
        1,
        "Overlapping Mentions must not create duplicate overlapping links"
    );

    console.log("Article Renderer Mention overlap safety PASSED");
}


{
    const researchCitations = [
        {
            id: "citation:test-primary",
            sourceRef: "source:test-primary",
            evidenceRef: null,
            contentBlockId: "citation-v2-paragraph",
            start: 0,
            end: 14
        }
    ];

    const section = {
        id: "citation-v2-test",
        content: [
            {
                id: "citation-v2-paragraph",
                type: "paragraph",
                text: "متن دارای citation"
            }
        ]
    };

    const sources = [
        {
            id: "source:test-primary",
            title_fa: "منبع Citation v2",
            publisher: "ناشر آزمون",
            url: "https://example.com/citation-v2"
        }
    ];

    const html = renderArticleContent(
        [section],
        [],
        [],
        researchCitations
    );

    assert(
        html.includes("[1]"),
        "Research v2 Citation must render an inline citation marker"
    );

    assert(
        html.includes("#citation-source-1"),
        "Research v2 Citation must link to its document-level citation anchor"
    );

    console.log("Article Renderer Research v2 Citation contract PASSED");
}
