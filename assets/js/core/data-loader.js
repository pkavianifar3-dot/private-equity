(function (global) {
    "use strict";

    function createDataLoader(atlasRoot) {
        const jsonCache = new Map();
        let relationContractCache = null;

        async function loadJSON(path) {
            const response = await fetch(path, {
                cache: "no-store"
            });

            if (!response.ok) {
                throw new Error(`Atlas data load failed: ${path}`);
            }

            return response.json();
        }

        function loadCachedJSON(path) {
            if (jsonCache.has(path)) {
                return jsonCache.get(path);
            }

            const promise = loadJSON(path).catch(error => {
                jsonCache.delete(path);
                throw error;
            });

            jsonCache.set(path, promise);

            return promise;
        }

        async function loadRelationContract() {
            if (relationContractCache) {
                return relationContractCache;
            }

            relationContractCache = Promise.all([
                loadCachedJSON(`${atlasRoot}/taxonomies/relation-types.json`),
                loadCachedJSON(`${atlasRoot}/taxonomies/relation-rules.json`),
                loadCachedJSON(`${atlasRoot}/taxonomies/relation-rendering.json`)
            ]).then(([relationTypes, relationRules, relationRendering]) => ({
                relationTypes,
                relationRules,
                relationRendering
            }));

            return relationContractCache;
        }

        return {
            loadJSON,
            loadCachedJSON,
            loadRelationContract
        };
    }

    global.PrivateCapitalDataLoader = {
        create: createDataLoader
    };
})(window);
