// Build-time references reuse the canonical resolvers; publication is an extra gate.
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const context = {window: {}};
for (const file of ['url-resolver.js', 'entity-resolver.js']) {
    vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../../assets/js/core', file), 'utf8'), context);
}
const escape = value => String(value).replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));

function createReferences({entities, research, exists, structured = new Map()}) {
    const resolver = context.window.PrivateCapitalEntityResolver.create({entities}, context.window.PrivateCapitalURL);
    function approvedURL(url) {
        if (typeof url !== 'string' || !url.startsWith('/') || url.startsWith('//') || /[?#\\]/.test(url) || url.split('/').some(s => s === '..' || s === '.')) return null;
        return exists(url) ? url : null;
    }
    function resolve(ref) {
        if (ref.entityRef) {
            const target = resolver.resolve(ref.entityRef);
            return target?.entity.lifecycleStatus === 'PUBLISHED' ? approvedURL(target.url) : null;
        }
        const record = research.find(row => row.id === ref.researchRef);
        if (!record || record.status !== 'PUBLISHED') return null;
        const content = structured.get(record.id);
        if (content ? content.status !== 'PUBLISHED' || content.url !== record.url : record.sourceMode !== 'legacy-html') return null;
        return record.url.startsWith('/articles/') && record.url.endsWith('.html') ? approvedURL(record.url) : null;
    }
    function inline(value) {
        return (Array.isArray(value) ? value : [value]).map(part => {
            if (typeof part === 'string') return escape(part);
            const label = escape(part.label);
            const url = resolve(part);
            return url ? `<a href="${escape(url)}">${label}</a>` : label;
        }).join('');
    }
    return {resolve, inline};
}
module.exports = {createReferences, escape};
