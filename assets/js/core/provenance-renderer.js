(function (global) {
    "use strict";

    function buildSourceIndex(sourceData) {
        const sourceIndex = {};

        (sourceData?.sources || []).forEach(source => {
            sourceIndex[source.id] = source;
        });

        return sourceIndex;
    }

    function buildSourceReferenceIndex(sourceData) {
        const sourceIndex = {};
        const sourceNumbers = {};

        (sourceData?.sources || []).forEach((source, index) => {
            sourceIndex[source.id] = source;
            sourceNumbers[source.id] = index + 1;
        });

        return {
            sourceIndex,
            sourceNumbers
        };
    }

    const evidenceTypeLabels = Object.freeze({
        explicit_self_statement: "اظهار صریح شخص",
        corporate_identity: "سند هویت سازمانی",
        explicit_corporate_statement: "بیانیه صریح سازمان",
        explicit_media_report: "گزارش صریح رسانه",
        investment_announcement: "اعلام سرمایه‌گذاری",
        historical_corporate_record: "سابقه تاریخی سازمان",
        explicit_title_statement: "اظهار صریح عنوان سمت",
        independent_media_report: "گزارش رسانه مستقل",
        historical_board_record: "سابقه تاریخی هیئت‌مدیره",
        project_statement: "اظهار درباره پروژه",
        authoritative_publication: "انتشار مرجع معتبر"
    });

    const strengthLabels = Object.freeze({
        strong: "اعتبار بالا",
        moderate: "اعتبار متوسط",
        weak: "اعتبار پایین"
    });

    function evidenceTypeLabel(value) {
        return evidenceTypeLabels[value] || "نوع شاهد نامشخص";
    }

    function strengthLabel(value) {
        return strengthLabels[value] || "اعتبار نامشخص";
    }

    function collectSourceIds(evidenceList, content) {
        const ids = [];
        const add = id => {
            if (id && !ids.includes(id)) {
                ids.push(id);
            }
        };

        (content?.sections || []).forEach(section => {
            (section.paragraphs || []).forEach(paragraph => {
                (paragraph.sourceRefs || []).forEach(add);
            });
        });
        (evidenceList || []).forEach(evidence => add(evidence.sourceRef));

        return ids;
    }

    global.PrivateCapitalProvenanceRenderer = {
        buildSourceIndex,
        buildSourceReferenceIndex,
        collectSourceIds,
        evidenceTypeLabel,
        strengthLabel
    };
})(window);
