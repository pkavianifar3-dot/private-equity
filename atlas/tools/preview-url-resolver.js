(function (global) {
    "use strict";

    // This file is loaded by temporary preview pages only.
    const publicURL = global.PrivateCapitalURL;
    if (!publicURL || typeof publicURL.entityURL !== "function") return;

    const PREVIEW_ROUTES = {
        Project: { namespace: "project", segment: "project" },
        OrganizationUnit: { namespace: "organization", segment: "organization-unit" }
    };

    global.PrivateCapitalURL = {
        ...publicURL,
        entityURL(entityId, entityType, context) {
            if (typeof entityType === "string" &&
                Object.prototype.hasOwnProperty.call(PREVIEW_ROUTES, entityType)) {
                if (typeof entityId !== "string") return null;
                const { namespace, segment } = PREVIEW_ROUTES[entityType];
                const prefix = namespace + ":";
                const slug = entityId.startsWith(prefix) ? entityId.slice(prefix.length) : "";
                return slug ? `/atlas/_preview/${segment}/${encodeURIComponent(slug)}/` : null;
            }
            return publicURL.entityURL(entityId, entityType, context);
        }
    };
})(window);
