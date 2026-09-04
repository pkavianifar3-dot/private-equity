const assert = require("assert");
const fs = require("fs");
const vm = require("vm");

const rendererSource = fs.readFileSync(
    "assets/js/article-renderer.js",
    "utf8"
);

const context = {
    console,
};

vm.createContext(context);
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
    1,
    "Research renderer must render 1 subheading"
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
        "articles/private-capital.html",
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
        "articles/private-capital.html",
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
        "articles/private-capital.html",
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
        "articles/private-capital.html",
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
