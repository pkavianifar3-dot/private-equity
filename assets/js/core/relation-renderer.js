(function (global) {
    "use strict";

    function renderRelation(claim, currentEntityId, relationTypes, relationRules, relationRendering) {
        if (!claim || !currentEntityId) return null;

        const subject = claim.subject;
        const object = claim.object;

        if (typeof subject !== "string" || !subject ||
            typeof object !== "string" || !object || subject === object) return null;

        const rules = Array.isArray(relationRules?.rules) ? relationRules.rules : [];
        const rule = rules.find(item => item && item.relation === claim.predicate);

        if (!rule) return null;

        const types = Array.isArray(relationTypes?.relation_types) ? relationTypes.relation_types : [];
        const relationType = types.find(item => item && item.id === claim.predicate);

        if (!relationType) return null;

        const rendering = relationRendering && relationRendering.relations
            ? relationRendering.relations[claim.predicate]
            : null;

        if (!rendering) return null;

        const forwardLabel = rendering.forward_label_fa;

        if (subject === currentEntityId) {
            if (typeof forwardLabel !== "string" || !forwardLabel.trim()) return null;

            return {
                predicate: claim.predicate,
                direction: "forward",
                targetId: object,
                label: forwardLabel
            };
        }

        if (object === currentEntityId) {
            if (rendering.reverse_display_allowed !== true) return null;

            const reverseLabel = rendering.reverse_label_fa;

            if (typeof reverseLabel !== "string" || !reverseLabel.trim()) return null;

            return {
                predicate: claim.predicate,
                direction: "reverse",
                targetId: subject,
                label: reverseLabel
            };
        }

        return null;
    }

    global.PrivateCapitalRelationRenderer = { renderRelation };
})(window);
