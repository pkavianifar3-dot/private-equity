(function () {
    "use strict";
    function revealHash() {
        const id = decodeURIComponent(window.location.hash.slice(1));
        if (!id) return;
        const target = document.getElementById(id);
        const notes = target && target.closest("details.research-endmatter");
        if (notes) notes.open = true;
    }
    document.addEventListener("click", function (event) {
        const link = event.target.closest("a[href^='#']");
        if (!link) return;
        const target = document.getElementById(decodeURIComponent(link.getAttribute("href").slice(1)));
        const notes = target && target.closest("details.research-endmatter");
        if (notes) notes.open = true;
    });
    window.addEventListener("hashchange", revealHash);
    revealHash();
})();
