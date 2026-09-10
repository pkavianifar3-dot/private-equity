(function (global) {
    "use strict";

    function buildSourceIndex(sourceData) {
        const sourceIndex = {};

        (sourceData?.sources || []).forEach(source => {
            sourceIndex[source.id] = source;
        });

        return sourceIndex;
    }

    global.PrivateCapitalProvenanceRenderer = {
        buildSourceIndex
    };
})(window);
