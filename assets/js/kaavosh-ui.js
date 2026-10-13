/* Kaavosh controls stay mounted; only the results region changes. */
(function () {
    "use strict";
    const core = window.KaavoshCore;
    const esc = value => String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
    const number = n => n.toLocaleString("fa-IR");
    const labels = { Concept: "مفهوم", Person: "شخص", Organization: "سازمان", Investment: "سرمایه‌گذاری", Research: "پژوهش" };
    const matches = { exact: "تطبیق نام", prefix: "تطبیق عنوان", tokens: "تطبیق واژه‌ها", partial: "تطبیق جزئی", body: "در متن", browse: "" };
    const client = core.createClient({ fetchDocuments: async () => {
        const r = await fetch("/search/documents.json"); if (!r.ok) throw Error("دادهٔ کاوش در دسترس نیست."); return r.json();
    }, loadPagefind: () => import("/search/pagefind/pagefind.js") });
    function mount(form) {
        if (form.dataset.mounted) return;
        form.dataset.mounted = "true";
        const input = form.elements.q;
        document.addEventListener("keydown", e => { if (e.key === "/" && !e.target.closest?.("input,textarea,select,[contenteditable]")) { e.preventDefault(); input.focus(); } });
        const panel = document.getElementById(form.dataset.results);
        if (!panel) return; // Atlas home submits a native, shareable search URL.
        const scope = form.elements.scope;
        const defaults = form.dataset.defaultScope || "atlas";
        const status = document.getElementById(form.dataset.status);
        const filters = document.getElementById(form.dataset.filters);
        const discovery = document.querySelector("[data-discovery-content]");
        const feature = document.querySelector("[data-discovery-feature]");
        function showDiscovery(show) { if (discovery) discovery.hidden = !show; if (feature) feature.hidden = !show; }
        let state = core.stateFromURL(location.search, defaults), sequence = 0, timer;
        function sync() { input.value = state.query; scope.value = state.scope; }
        function url(replace = false) {
            const q = core.queryString(state, defaults), target = location.pathname + (q ? "?" + q : "");
            if (target !== location.pathname + location.search) history[replace ? "replaceState" : "pushState"]({}, "", target);
        }
        function typeFilters(docs) {
            if (!filters) return;
            const types = [...new Set(docs.filter(d => state.scope === "all" || state.scope === d.scope).map(d => d.type))];
            filters.innerHTML = [{ type: "", label: "همهٔ نتایج" }, ...types.map(type => ({ type, label: labels[type] }))]
                .map(d => `<button type="button" data-type="${esc(d.type)}" aria-pressed="${state.type === d.type}">${esc(d.label)}</button>`).join("");
        }
        async function render(focusPage = false, focusType = null) {
            const request = ++sequence, requested = { ...state };
            const isResearchHome = !!discovery;
            if (isResearchHome && !core.normalize(requested.query) && !requested.type && !requested.group) {
                showDiscovery(true); panel.hidden = true; status.textContent = ""; if (filters) filters.hidden = true; return;
            }
            showDiscovery(false);
            panel.hidden = false; if (filters) filters.hidden = false;
            panel.setAttribute("aria-busy", "true"); status.textContent = "در حال کاوش…";
            try {
                const rows = await client.search(requested.query, requested);
                if (request !== sequence) return;
                const docs = await client.documents();
                const pages = Math.max(1, Math.ceil(rows.length / 12));
                state.page = Math.min(state.page, pages); url(true);
                const visible = rows.slice((state.page - 1) * 12, state.page * 12);
                const snippets = await Promise.all(visible.map(async r => {
                    if (r.matchType !== "body" || !r.loadExcerpt) return r.summary;
                    try { const result = await r.loadExcerpt(); return new DOMParser().parseFromString(result.excerpt, "text/html").body.textContent || r.summary; }
                    catch { return r.summary; }
                }));
                if (request !== sequence) return;
                typeFilters(docs);
                panel.innerHTML = rows.length ? `<div class="kaavosh-result-grid">${visible.map((r, i) => `<a class="discovery-card search-result" href="${esc(r.url)}" data-result-id="${esc(r.id)}"><span class="discovery-card-meta">${esc(labels[r.type])}<span>${esc(matches[r.matchType])}</span></span><h2>${esc(r.title)}</h2><p>${esc(snippets[i])}</p><span class="discovery-card-link">${r.scope === "research" ? "مطالعه پژوهش" : "شناخت این مدخل"} <span aria-hidden="true">←</span></span></a>`).join("")}</div>` :
                    '<div class="kaavosh-empty"><h2>نتیجه‌ای پیدا نشد</h2><p>عبارت کوتاه‌تر یا دامنهٔ دیگری را امتحان کنید.</p><a href="/atlas/">مرور اطلس</a> · <a href="/articles.html">مرور پژوهش‌ها</a></div>';
                if (pages > 1) panel.innerHTML += `<nav class="kaavosh-pagination" aria-label="صفحه‌های نتایج">${core.pageWindow(state.page, pages).map(p => p === null ? '<span aria-hidden="true">…</span>' : `<button type="button" data-page="${p}" ${state.page === p ? 'aria-current="page"' : ""}>${number(p)}</button>`).join("")}</nav>`;
                status.textContent = `${number(rows.length)} نتیجه${core.normalize(state.query) ? " برای «" + state.query + "»" : ""}`;
                if (focusPage) panel.querySelector(`[data-page="${state.page}"]`)?.focus();
                if (focusType !== null) filters?.querySelector(`[data-type="${focusType}"]`)?.focus();
            } catch (error) {
                if (request !== sequence) return;
                status.textContent = "کاوش در دسترس نیست.";
                panel.innerHTML = '<div class="kaavosh-empty"><h2>بارگذاری کاوش کامل نشد</h2><p>دوباره تلاش کنید. مسیرهای مطالعه همچنان در دسترس‌اند.</p><button type="button" data-retry>تلاش دوباره</button></div>';
                showDiscovery(true);
                console.error("Kaavosh:", error);
            } finally { if (request === sequence) panel.setAttribute("aria-busy", "false"); }
        }
        function search() { clearTimeout(timer); state = { query: input.value.trim(), scope: scope.value, type: "", group: "", page: 1 }; url(); render(); }
        form.addEventListener("submit", e => { e.preventDefault(); search(); });
        input.addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(search, 300); });
        input.addEventListener("keydown", e => { if (e.key === "Escape") { e.preventDefault(); input.value = ""; search(); input.focus(); } });
        scope.addEventListener("change", search);
        filters?.addEventListener("click", e => { const b = e.target.closest("[data-type]"); if (!b) return; state.type = b.dataset.type; state.group = ""; state.page = 1; url(); render(false, b.dataset.type); });
        panel.addEventListener("click", e => { const b = e.target.closest("[data-page]"); if (b) { state.page = Number(b.dataset.page); url(); render(true); } if (e.target.closest("[data-retry]")) render(); });
        window.addEventListener("popstate", () => { clearTimeout(timer); state = core.stateFromURL(location.search, defaults); sync(); render(); });
        sync(); render();
    }
    window.KaavoshUI = { mount };
    document.querySelectorAll("form[data-kaavosh]").forEach(mount);
})();
