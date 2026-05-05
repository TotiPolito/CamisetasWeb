const CART_STORAGE_KEY = "toti-camisetas-cart";
const THEME_STORAGE_KEY = "toti-theme";

function normalizeText(value) {
    return String(value || "")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase();
}

function escapeHtml(value) {
    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function readCart() {
    try {
        const rawValue = localStorage.getItem(CART_STORAGE_KEY);
        const parsed = JSON.parse(rawValue || "[]");
        return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
        return [];
    }
}

function writeCart(items) {
    localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
    renderCart();
}

function buildWhatsAppUrl(items) {
    const rawNumber = document.body.dataset.whatsappNumber || "";
    const phoneNumber = rawNumber.replace(/\D/g, "");

    if (!phoneNumber || items.length === 0) {
        return "#";
    }

    const lines = [
        "Hola Toti, quiero pedir estas camisetas:",
        "",
    ];

    items.forEach((item, index) => {
        lines.push(`${index + 1}. ${item.name} | SKU ${item.sku} | Talle ${item.size} | Cantidad ${item.quantity}`);
    });

    lines.push("");
    lines.push("Quedo atento para confirmar stock y coordinacion.");

    return `https://wa.me/${phoneNumber}?text=${encodeURIComponent(lines.join("\n"))}`;
}

function renderCart() {
    const items = readCart();
    const itemsContainer = document.querySelector("[data-cart-items]");
    const emptyState = document.querySelector("[data-cart-empty]");
    const cartCount = document.querySelectorAll("[data-cart-count]");
    const whatsappButton = document.querySelector("[data-cart-whatsapp]");

    const totalUnits = items.reduce((sum, item) => sum + item.quantity, 0);
    cartCount.forEach((node) => {
        node.textContent = String(totalUnits);
    });

    if (whatsappButton) {
        whatsappButton.href = buildWhatsAppUrl(items);
        whatsappButton.classList.toggle("is-disabled", items.length === 0);
        whatsappButton.setAttribute("aria-disabled", items.length === 0 ? "true" : "false");
        if (items.length === 0) {
            whatsappButton.removeAttribute("target");
            whatsappButton.removeAttribute("rel");
        } else {
            whatsappButton.setAttribute("target", "_blank");
            whatsappButton.setAttribute("rel", "noreferrer");
        }
    }

    if (!itemsContainer || !emptyState) {
        return;
    }

    emptyState.hidden = items.length > 0;
    itemsContainer.innerHTML = "";

    items.forEach((item) => {
        const card = document.createElement("article");
        card.className = "cart-item";
        card.innerHTML = `
            <div class="cart-item__copy">
                <a class="cart-item__title" href="/camiseta/${escapeHtml(item.slug)}">${escapeHtml(item.name)}</a>
                <p>SKU ${escapeHtml(item.sku)} | Talle ${escapeHtml(item.size)}</p>
            </div>
            <div class="cart-item__controls">
                <div class="quantity-stepper quantity-stepper--small">
                    <button class="quantity-stepper__button" type="button" data-cart-action="decrease" data-cart-key="${escapeHtml(item.key)}">-</button>
                    <input class="quantity-stepper__input" type="text" readonly value="${escapeHtml(item.quantity)}">
                    <button class="quantity-stepper__button" type="button" data-cart-action="increase" data-cart-key="${escapeHtml(item.key)}">+</button>
                </div>
                <button class="link-button" type="button" data-cart-action="remove" data-cart-key="${escapeHtml(item.key)}">Quitar</button>
            </div>
        `;
        itemsContainer.appendChild(card);
    });
}

function openCart() {
    const layer = document.querySelector("[data-cart-layer]");
    if (!layer) {
        return;
    }

    layer.hidden = false;
    document.body.classList.add("cart-open");
}

function closeCart() {
    const layer = document.querySelector("[data-cart-layer]");
    if (!layer) {
        return;
    }

    layer.hidden = true;
    document.body.classList.remove("cart-open");
}

function updateCartItemQuantity(itemKey, nextQuantity) {
    const items = readCart()
        .map((item) => {
            if (item.key !== itemKey) {
                return item;
            }

            const maxStock = Number(item.maxStock || nextQuantity);
            return {
                ...item,
                quantity: Math.max(1, Math.min(nextQuantity, maxStock)),
            };
        });

    writeCart(items);
}

function removeCartItem(itemKey) {
    const nextItems = readCart().filter((item) => item.key !== itemKey);
    writeCart(nextItems);
}

function addItemToCart(item) {
    const items = readCart();
    const existingItem = items.find((entry) => entry.key === item.key);

    if (existingItem) {
        const nextQuantity = Math.min(existingItem.quantity + item.quantity, item.maxStock);
        existingItem.quantity = nextQuantity;
        existingItem.maxStock = item.maxStock;
        writeCart(items);
        return;
    }

    items.push(item);
    writeCart(items);
}

function initCatalogFilters() {
    const searchInput = document.querySelector("#catalog-search");
    const filterButtons = document.querySelectorAll("[data-filter]");
    const sizeFilterButtons = document.querySelectorAll("[data-size-filter]");
    const cards = document.querySelectorAll(".product-card[data-category]");
    const emptyState = document.querySelector("#catalog-empty");

    if (!searchInput || cards.length === 0) {
        return;
    }

    let activeFilter = "Todos";
    let activeSizeFilter = "Todos";

    function applyFilters() {
        const rawTerm = normalizeText(searchInput.value).trim();
        const searchTerm = rawTerm.length >= 3 ? rawTerm : "";
        let visibleCards = 0;

        cards.forEach((card) => {
            const cardCategory = normalizeText(card.dataset.category || "");
            const cardTitle = normalizeText(card.dataset.title || "");
            const cardSizes = String(card.dataset.sizes || "")
                .split(",")
                .map((value) => normalizeText(value.trim()))
                .filter(Boolean);
            const matchesFilter = activeFilter === "Todos" || cardCategory === normalizeText(activeFilter);
            const matchesSize = activeSizeFilter === "Todos" || cardSizes.includes(normalizeText(activeSizeFilter));
            const matchesSearch = searchTerm === "" || cardTitle.includes(searchTerm);
            const shouldShow = matchesFilter && matchesSize && matchesSearch;
            card.hidden = !shouldShow;
            if (shouldShow) {
                visibleCards += 1;
            }
        });

        if (emptyState) {
            emptyState.hidden = visibleCards !== 0;
        }
    }

    filterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeFilter = button.dataset.filter || "Todos";
            filterButtons.forEach((item) => item.classList.remove("is-active"));
            button.classList.add("is-active");
            applyFilters();
        });
    });

    sizeFilterButtons.forEach((button) => {
        button.addEventListener("click", () => {
            activeSizeFilter = button.dataset.sizeFilter || "Todos";
            sizeFilterButtons.forEach((item) => item.classList.remove("is-active"));
            button.classList.add("is-active");
            applyFilters();
        });
    });

    searchInput.addEventListener("input", applyFilters);
    searchInput.addEventListener("search", applyFilters);
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

    document.querySelectorAll("video[autoplay]").forEach((video) => {
        video.muted = true;
        const playAttempt = video.play();
        if (playAttempt && typeof playAttempt.catch === "function") {
            playAttempt.catch(() => {});
        }
    });

    document.addEventListener("keydown", (event) => {
        const key = event.key.toLowerCase();
        const isShortcut = event.ctrlKey || event.metaKey;
        if (isShortcut && (key === "s" || key === "u")) {
            event.preventDefault();
        }

        if (key === "escape") {
            closeCart();
        }
    });
}

function applyTheme(theme) {
    const nextTheme = theme === "dark" ? "dark" : "light";
    document.documentElement.dataset.theme = nextTheme;
    localStorage.setItem(THEME_STORAGE_KEY, nextTheme);

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        button.setAttribute("aria-pressed", nextTheme === "dark" ? "true" : "false");
        button.setAttribute(
            "aria-label",
            nextTheme === "dark" ? "Pasar a modo claro" : "Pasar a modo oscuro"
        );
    });
}

function initThemeToggle() {
    const initialTheme = document.documentElement.dataset.theme || "light";
    applyTheme(initialTheme);

    document.querySelectorAll("[data-theme-toggle]").forEach((button) => {
        button.addEventListener("click", () => {
            const currentTheme = document.documentElement.dataset.theme || "light";
            applyTheme(currentTheme === "dark" ? "light" : "dark");
        });
    });
}

function initCart() {
    renderCart();

    document.querySelectorAll("[data-cart-toggle]").forEach((button) => {
        button.addEventListener("click", openCart);
    });

    document.querySelectorAll("[data-cart-close]").forEach((button) => {
        button.addEventListener("click", closeCart);
    });

    const itemsContainer = document.querySelector("[data-cart-items]");

    if (itemsContainer) {
        itemsContainer.addEventListener("click", (event) => {
            const trigger = event.target.closest("[data-cart-action]");
            if (!trigger) {
                return;
            }

            const action = trigger.dataset.cartAction;
            const itemKey = trigger.dataset.cartKey || "";
            const currentItem = readCart().find((item) => item.key === itemKey);

            if (!currentItem) {
                return;
            }

            if (action === "increase") {
                updateCartItemQuantity(itemKey, currentItem.quantity + 1);
            }

            if (action === "decrease") {
                updateCartItemQuantity(itemKey, currentItem.quantity - 1);
            }

            if (action === "remove") {
                removeCartItem(itemKey);
            }
        });
    }

    window.addEventListener("storage", renderCart);
}

function initProductPurchase() {
    const purchaseRoot = document.querySelector("[data-product-purchase]");
    if (!purchaseRoot) {
        return;
    }

    const sizeButtons = Array.from(purchaseRoot.querySelectorAll("[data-size-option]"));
    const decreaseButton = purchaseRoot.querySelector("[data-qty-decrease]");
    const increaseButton = purchaseRoot.querySelector("[data-qty-increase]");
    const quantityInput = purchaseRoot.querySelector("[data-qty-input]");
    const addToCartButton = purchaseRoot.querySelector("[data-add-to-cart]");
    const feedback = purchaseRoot.querySelector("[data-purchase-feedback]");

    let selectedSize = null;
    let quantity = 1;

    function syncPurchaseState() {
        quantityInput.value = String(quantity);
        decreaseButton.disabled = quantity <= 1;
        increaseButton.disabled = !selectedSize || quantity >= selectedSize.stock;
        addToCartButton.disabled = !selectedSize || selectedSize.stock < 1;
    }

    sizeButtons.forEach((button) => {
        button.addEventListener("click", () => {
            sizeButtons.forEach((item) => item.classList.remove("is-selected"));
            button.classList.add("is-selected");

            selectedSize = {
                label: button.dataset.sizeLabel || "",
                stock: Number(button.dataset.sizeStock || "0"),
            };
            quantity = 1;
            feedback.textContent = `${selectedSize.stock} disponibles en talle ${selectedSize.label}.`;
            syncPurchaseState();
        });
    });

    decreaseButton.addEventListener("click", () => {
        quantity = Math.max(1, quantity - 1);
        syncPurchaseState();
    });

    increaseButton.addEventListener("click", () => {
        if (!selectedSize) {
            return;
        }
        quantity = Math.min(selectedSize.stock, quantity + 1);
        syncPurchaseState();
    });

    addToCartButton.addEventListener("click", () => {
        if (!selectedSize || selectedSize.stock < 1) {
            return;
        }

        addItemToCart({
            key: `${purchaseRoot.dataset.productId}:${selectedSize.label}`,
            productId: purchaseRoot.dataset.productId,
            slug: purchaseRoot.dataset.productSlug,
            sku: purchaseRoot.dataset.productSku,
            name: purchaseRoot.dataset.productName,
            size: selectedSize.label,
            quantity,
            maxStock: selectedSize.stock,
        });

        feedback.textContent = `${purchaseRoot.dataset.productName} talle ${selectedSize.label} agregado al carrito.`;
        openCart();
    });

    if (sizeButtons.every((button) => button.disabled)) {
        feedback.textContent = "No hay stock disponible en este momento.";
    }

    syncPurchaseState();
}

document.addEventListener("DOMContentLoaded", () => {
    initCatalogFilters();
    initMediaProtection();
    initThemeToggle();
    initCart();
    initProductPurchase();
});
