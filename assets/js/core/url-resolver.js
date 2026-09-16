(function (global) {
    "use strict";

    const SITE_ORIGIN = "https://privatecapital.ir";

    const ROUTES = {
        Person: "person",
        Organization: "organization",
        Investment: "investment",
        Concept: "concept"
    };

    function resolveRoute(entityId, entityType) {
        if (
            typeof entityId !== "string" ||
            !entityId.includes(":") ||
            typeof entityType !== "string"
        ) {
            return null;
        }

        const [, ...slugParts] = entityId.split(":");
        const slug = slugParts.join(":");

        if (!slug) {
            return null;
        }

        const route = ROUTES[entityType];

        if (!route) {
            return null;
        }

        return `${route}/${encodeURIComponent(slug)}/`;
    }

    function entityURL(entityId, entityType, context) {
        const route = resolveRoute(entityId, entityType);

        if (!route) {
            return null;
        }

        return "/atlas/" + route;
    }

    function entityCanonicalURL(entityId, entityType) {
        const route = resolveRoute(entityId, entityType);

        if (!route) {
            return null;
        }

        return `${SITE_ORIGIN}/atlas/${route}`;
    }

    global.PrivateCapitalURL = {
        entityURL,
        entityCanonicalURL
    };
})(window);
