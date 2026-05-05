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

document.addEventListener("DOMContentLoaded", () => {
    initAdminForms();
    initAdminFolders();
});
