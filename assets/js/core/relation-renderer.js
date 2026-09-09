(function (global) {
    "use strict";

    function renderRelation(claim, currentEntityId, relationTypes, relationRules, relationRendering) {
        if (!claim || !currentEntityId) return null;

        const subject = claim.subject;
        const object = claim.object;
        if (!subject || !object || subject === object) return null;

        const rule = (relationRules && relationRules.rules || []).find(item => item.relation === claim.predicate);
        if (!rule) return null;

        const relationType = (relationTypes && relationTypes.relation_types || []).find(item => item.id === claim.predicate);
        const rendering = relationRendering && relationRendering.relations
            ? relationRendering.relations[claim.predicate]
            : null;
        const forwardLabel = relationType && relationType.labels && relationType.labels.fa;

        if (subject === currentEntityId) {
            return { predicate: claim.predicate, direction: "forward", targetId: object, label: forwardLabel || null };
        }

        if (object === currentEntityId) {
            return { predicate: claim.predicate, direction: "reverse", targetId: subject, label: rendering && rendering.reverse_label_fa ? rendering.reverse_label_fa : forwardLabel || null };
        }

        return null;
    }

    global.PrivateCapitalRelationRenderer = { renderRelation };
})(window);
