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

    global.PrivateCapitalProvenanceRenderer = {
        buildSourceIndex,
        buildSourceReferenceIndex
    };
})(window);
