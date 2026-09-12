(function (global) {
    "use strict";

    function createEntityResolver(registry, urlResolver) {
        const entities = Array.isArray(registry?.entities)
            ? registry.entities
            : [];

        const entityById = new Map(
            entities
                .filter(entity => entity && typeof entity.id === "string")
                .map(entity => [entity.id, entity])
        );

        function resolve(entityRef, context) {
            if (typeof entityRef !== "string") {
                return null;
            }

            const entity = entityById.get(entityRef);
            if (!entity) {
                return null;
            }

            const url =
                urlResolver &&
                typeof urlResolver.entityURL === "function"
                    ? urlResolver.entityURL(entityRef, context)
                    : null;

            if (!url) {
                return null;
            }

            return {
                entity,
                url
            };
        }

        return {
            resolve
        };
    }

    global.PrivateCapitalEntityResolver = {
        create: createEntityResolver
    };
})(window);
