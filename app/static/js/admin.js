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

document.addEventListener("DOMContentLoaded", initAdminForms);
