(function (global) {
    "use strict";

    function renderRelation(claim, currentEntityId, relationTypes, relationRules, relationRendering) {
        if (!claim || !currentEntityId) return null;

        const subject = claim.subject;
        const object = claim.object;

        if (!subject || !object || subject === object) return null;

        const rule = (relationRules && relationRules.rules || [])
            .find(item => item.relation === claim.predicate);

        if (!rule) return null;

        const relationType = (relationTypes && relationTypes.relation_types || [])
            .find(item => item.id === claim.predicate);

        if (!relationType) return null;

        const rendering = relationRendering && relationRendering.relations
            ? relationRendering.relations[claim.predicate]
            : null;

        if (!rendering) return null;

        const forwardLabel = rendering.forward_label_fa;

        if (subject === currentEntityId) {
            if (!forwardLabel || !forwardLabel.trim()) return null;

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

            if (!reverseLabel || !reverseLabel.trim()) return null;

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
