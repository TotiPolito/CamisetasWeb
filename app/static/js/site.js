function normalizeText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

function initCatalogFilters() {
    const searchInput = document.querySelector("#catalog-search");
    const filterButtons = document.querySelectorAll("[data-filter]");
    const cards = document.querySelectorAll(".product-card[data-category]");

    if (!searchInput || cards.length === 0) {
        return;
    }

    let activeFilter = "Todos";

    function applyFilters() {
        const searchTerm = normalizeText(searchInput.value);

        cards.forEach((card) => {
            const cardCategory = card.dataset.category || "";
            const cardSearch = normalizeText(card.dataset.search || "");
            const matchesFilter = activeFilter === "Todos" || cardCategory === activeFilter;
            const matchesSearch = searchTerm === "" || cardSearch.includes(searchTerm);
            card.hidden = !(matchesFilter && matchesSearch);
        });
    }

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeFilter = button.dataset.filter || "Todos";
            filterButtons.forEach((item) => item.classList.remove("is-active"));
            button.classList.add("is-active");
            applyFilters();
        });
    });

    searchInput.addEventListener("input", applyFilters);
    applyFilters();
}

function initMediaProtection() {
    const protectedBlocks = document.querySelectorAll("[data-protected-media]");

    protectedBlocks.forEach((block) => {
        block.addEventListener("contextmenu", (event) => {
            event.preventDefault();
        });
    });

    document.querySelectorAll("img, video").forEach((media) => {
        media.setAttribute("draggable", "false");
        media.addEventListener("dragstart", (event) => {
            event.preventDefault();
        });
    });

    document.addEventListener("keydown", (event) => {
        const key = event.key.toLowerCase();
        const isShortcut = event.ctrlKey || event.metaKey;
        if (isShortcut && (key === "s" || key === "u")) {
            event.preventDefault();
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initCatalogFilters();
    initMediaProtection();
});
