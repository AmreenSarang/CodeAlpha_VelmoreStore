
document.addEventListener("DOMContentLoaded", function () {
    const nameInput = document.getElementById("id_name");
    const descriptionInput = document.getElementById("id_description");
    const priceInput = document.getElementById("id_price");
    const imageInput = document.getElementById("id_image");

    const previewName = document.getElementById("velmorePreviewName");
    const previewDescription = document.getElementById(
        "velmorePreviewDescription"
    );
    const previewPrice = document.getElementById("velmorePreviewPrice");
    const previewImage = document.getElementById("velmorePreviewImage");
    const placeholder = document.getElementById("velmorePlaceholder");

    function updateText(input, element, fallback) {
        if (!input || !element) return;

        input.addEventListener("input", function () {
            element.textContent = input.value.trim() || fallback;
        });
    }

    updateText(nameInput, previewName, "Your Product Name");
    updateText(priceInput, previewPrice, "0.00");

    if (descriptionInput && previewDescription) {
        descriptionInput.addEventListener("input", function () {
            const text = descriptionInput.value.trim();

            if (!text) {
                previewDescription.textContent =
                    "Your product description will appear here.";
                return;
            }

            previewDescription.textContent =
                text.length > 130 ? text.slice(0, 130) + "..." : text;
        });
    }

    if (imageInput && previewImage) {
        imageInput.addEventListener("change", function () {
            const file = imageInput.files && imageInput.files[0];

            if (!file) return;

            const allowedTypes = [
                "image/png",
                "image/jpeg",
                "image/webp",
            ];

            if (!allowedTypes.includes(file.type)) {
                alert("Please choose a PNG, JPG, JPEG, or WebP image.");
                imageInput.value = "";
                return;
            }

            if (file.size > 5 * 1024 * 1024) {
                alert("Please choose an image smaller than 5 MB.");
                imageInput.value = "";
                return;
            }

            const reader = new FileReader();

            reader.onload = function (event) {
                previewImage.src = event.target.result;
                previewImage.hidden = false;

                if (placeholder) {
                    placeholder.style.display = "none";
                }
            };

            reader.readAsDataURL(file);
        });
    }
});
