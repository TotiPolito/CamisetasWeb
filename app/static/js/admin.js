function initAdminForms() {
    const forms = document.querySelectorAll("[data-admin-form]");

    forms.forEach((form) => {
        const submitButton = form.querySelector("[data-submit-label]");
        const fields = form.querySelectorAll("input, textarea, select");

        fields.forEach((field) => {
            field.addEventListener("input", () => {
                form.classList.add("is-dirty");
                if (submitButton) {
                    submitButton.textContent = "Guardar cambios";
                }
            });

            field.addEventListener("change", () => {
                form.classList.add("is-dirty");
                if (submitButton) {
                    submitButton.textContent = "Guardar cambios";
                }
            });
        });

        form.addEventListener("submit", () => {
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.textContent = "Guardando...";
            }
        });
    });
}

function initAdminFolders() {
    const folders = document.querySelectorAll(".admin-folder");
    const productDetails = document.querySelectorAll(".admin-product");

    folders.forEach((folder) => {
        const toggle = folder.querySelector(".admin-folder__toggle");
        const syncToggle = () => {
            if (toggle) {
                toggle.textContent = folder.open ? "Cerrar" : "Abrir";
            }
        };
        syncToggle();
        folder.addEventListener("toggle", syncToggle);
    });

    productDetails.forEach((details) => {
        const summary = details.querySelector(".admin-product__summary");
        if (!summary) {
            return;
        }

        summary.addEventListener("click", () => {
            productDetails.forEach((other) => {
                if (other !== details) {
                    other.removeAttribute("open");
                }
            });
        });
    });
}

function initColorPickers() {
    const pickers = document.querySelectorAll("[data-color-picker]");

    pickers.forEach((picker) => {
        const field = picker.closest(".field--color");
        const valueNode = field ? field.querySelector("[data-color-value]") : null;

        const syncValue = () => {
            if (valueNode) {
                valueNode.textContent = picker.value;
            }
        };

        syncValue();
        picker.addEventListener("input", syncValue);
        picker.addEventListener("change", syncValue);
    });
}

function initDeleteConfirmations() {
    const deleteForms = document.querySelectorAll("[data-product-delete]");

    deleteForms.forEach((form) => {
        form.addEventListener("submit", (event) => {
            const productName = form.dataset.productName || "este modelo";
            const productSku = form.dataset.productSku || "Sin SKU";
            const productCategory = form.dataset.productCategory || "Sin categoria";
            const confirmationMessage = [
                `Estas seguro que deseas borrar la camiseta ${productName}?`,
                "",
                `Categoria: ${productCategory}`,
                `SKU: ${productSku}`,
            ].join("\n");

            if (!window.confirm(confirmationMessage)) {
                event.preventDefault();
            }
        });
    });
}

document.addEventListener("DOMContentLoaded", () => {
    initAdminForms();
    initAdminFolders();
    initColorPickers();
    initDeleteConfirmations();
});
