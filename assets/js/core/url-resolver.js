(function (global) {
    "use strict";

    const SITE_ORIGIN = "https://privatecapital.ir";

    const ROUTES = {
        person: "person.html",
        organization: "organization.html",
        investment: "investment.html",
        concept: "concept.html"
    };

    function resolveRoute(entityId) {
        if (typeof entityId !== "string" || !entityId.includes(":")) {
            return null;
        }

        const [type] = entityId.split(":");
        const route = ROUTES[type];

        if (!route) {
            return null;
        }

        return route + "?id=" + encodeURIComponent(entityId);
    }

    function entityURL(entityId, context) {
        const route = resolveRoute(entityId);

        if (!route) {
            return null;
        }

        const prefix = context === "research" ? "../atlas/" : "";
        return prefix + route;
    }

    function entityCanonicalURL(entityId) {
        const route = resolveRoute(entityId);

        if (!route) {
            return null;
        }

        return SITE_ORIGIN + "/atlas/" + route;
    }

    global.PrivateCapitalURL = {
        entityURL,
        entityCanonicalURL
    };
})(window);
