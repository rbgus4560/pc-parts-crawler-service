document.addEventListener("DOMContentLoaded", () => {
    const categorySelect = document.getElementById("categoryFilter");

    if (!categorySelect) {
        return;
    }

    const categoryFields = [
        ...document.querySelectorAll("[data-category-field]"),
    ];

    function updateCategoryFields() {
        const selectedCategory = categorySelect.value;

        categoryFields.forEach((field) => {
            const isActive =
                selectedCategory !== ""
                && field.dataset.categoryField === selectedCategory;

            field.hidden = !isActive;

            field
                .querySelectorAll("[data-category-input]")
                .forEach((input) => {
                    input.disabled = !isActive;

                    if (!isActive) {
                        input.value = "";
                    }
                });
        });
    }

    categorySelect.addEventListener(
        "change",
        updateCategoryFields,
    );

    updateCategoryFields();
});
