(function (global) {
    "use strict";

    const SITE_ORIGIN = "https://privatecapital.ir";

    const ROUTES = {
        person: "person",
        organization: "organization",
        investment: "investment",
        concept: "concept"
    };

    function resolveRoute(entityId) {
        if (typeof entityId !== "string" || !entityId.includes(":")) {
            return null;
        }

        const [type, ...slugParts] = entityId.split(":");
        const slug = slugParts.join(":");

        if (!type || !slug) {
            return null;
        }

        const route = ROUTES[type];

        if (!route) {
            return null;
        }

        return `${route}/${encodeURIComponent(slug)}/`;
    }

    function entityURL(entityId, context) {
        const route = resolveRoute(entityId);

        if (!route) {
            return null;
        }

        return "/atlas/" + route;
    }

    function entityCanonicalURL(entityId) {
        const route = resolveRoute(entityId);

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
