const cart = JSON.parse(localStorage.getItem("cart")) || [];

// Función para mostrar alertas con SweetAlert2
function showAlert(message, type = "success", imageUrl = null) {
    Swal.fire({
        icon: type,
        text: message,
        toast: true,
        position: "top", // Cambiamos a "top" para que aparezca en la parte superior
        showConfirmButton: false,
        timer: 2000,
        timerProgressBar: true,
        customClass: {
            popup: "custom-swal-popup", // Clase personalizada para el marco
        },
        imageUrl: imageUrl, // URL de la imagen (opcional)
        imageWidth: 80, // Ancho de la imagen (opcional)
        imageHeight: 80, // Alto de la imagen (opcional)
        imageAlt: "Imagen personalizada", // Texto alternativo (opcional)
    });
}

// Función para actualizar el carrito
function updateCart() {
    const cartCount = document.getElementById("cart-count");
    if (cartCount) {
        cartCount.textContent = cart.reduce((sum, item) => sum + item.quantity, 0);
    }

    localStorage.setItem("cart", JSON.stringify(cart));

    const cartItems = document.getElementById("cart-items");
    const cartTotal = document.getElementById("cart-total");

    if (cartItems && cartTotal) {
        cartItems.innerHTML = "";
        let total = 0;

        cart.forEach((item, index) => {
            const li = document.createElement("li");
            li.className = "list-group-item cart-item";
            li.innerHTML = `
                <div class="d-flex align-items-center">
                    <img src="${item.imageUrl}" alt="${item.name}" class="me-3" style="width: 80px; height: 80px; object-fit: cover; border-radius: 8px;">
                    <div class="cart-item-details">
                        <span class="cart-item-name">${item.name}</span>
                        <div class="cart-item-quantity mt-2">
                            <button class="btn btn-sm btn-outline-secondary decrease-quantity" data-index="${index}">-</button>
                            <span class="btn btn-outline-secondary px-3">${item.quantity}</span>
                            <button class="btn btn-sm btn-outline-secondary increase-quantity" data-index="${index}">+</button>
                        </div>
                    </div>
                </div>
                <div class="d-flex align-items-center">
                    <span class="me-3 cart-item-price">$${(item.price * item.quantity).toFixed(2)}</span>
                    <button class="btn btn-sm btn-danger remove-from-cart" data-index="${index}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>
            `;
            cartItems.appendChild(li);
            total += item.price * item.quantity;
        });

        cartTotal.textContent = total.toFixed(2);
    }
}

// Función para eliminar un producto del carrito
function removeFromCart(index) {
    const itemName = cart[index].name;
    cart.splice(index, 1);
    updateCart();
    showAlert(`${itemName} eliminado del carrito`, "info");
}

// Función para aumentar la cantidad de un producto en el carrito
function increaseQuantity(index) {
    const item = cart[index];
    const availableQuantity = Number.parseInt(
        document.querySelector(`.product-quantity[data-id="${item.id}"]`).textContent,
    );

    if (item.quantity < availableQuantity) {
        item.quantity++;
        updateCart();
        showAlert(`Cantidad de ${item.name} aumentada a ${item.quantity}`, "success");
    } else {
        showAlert("No hay más stock disponible para este producto.", "error");
    }
}

// Función para disminuir la cantidad de un producto en el carrito
function decreaseQuantity(index) {
    if (cart[index].quantity > 1) {
        cart[index].quantity--;
        updateCart();
        showAlert(`Cantidad de ${cart[index].name} reducida a ${cart[index].quantity}`, "warning");
    } else {
        removeFromCart(index);
    }
}

// Función para agregar un producto al carrito
function addToCart(button) {
    const id = button.getAttribute("data-id");
    const name = button.getAttribute("data-name");
    const price = Number.parseFloat(button.getAttribute("data-price"));
    const imageUrl = button.getAttribute("data-image");
    const availableQuantity = Number.parseInt(button.parentElement.querySelector(".product-quantity").textContent);

    const existingItem = cart.find((item) => item.id === id);
    if (existingItem) {
        if (existingItem.quantity < availableQuantity) {
            existingItem.quantity++;
            showAlert(`${name} agregado al carrito`, "success");
        } else {
            showAlert("No hay más stock disponible para este producto.", "error");
            return;
        }
    } else {
        cart.push({ id, name, price, imageUrl, quantity: 1 });
        showAlert(`${name} agregado al carrito`, "success");
    }
    updateCart();
}

// Función para procesar el pedido
function processOrder() {
    if (cart.length === 0) {
        showAlert("Tu carrito está vacío. Agrega productos antes de procesar el pedido.", "warning");
        return;
    }

    // Redirigir directamente a la página de checkout
    window.location.href = "/checkout";
}

// Función para inicializar el carrito
function initCart() {
    updateCart();

    const cartItems = document.getElementById("cart-items");
    if (cartItems) {
        cartItems.addEventListener("click", (e) => {
            const target = e.target.closest("[data-index]");
            if (!target) return;

            const index = Number.parseInt(target.getAttribute("data-index"));

            if (target.classList.contains("remove-from-cart")) {
                removeFromCart(index);
            } else if (target.classList.contains("increase-quantity")) {
                increaseQuantity(index);
            } else if (target.classList.contains("decrease-quantity")) {
                decreaseQuantity(index);
            }
        });
    }

    const addToCartButtons = document.querySelectorAll(".add-to-cart");
    addToCartButtons.forEach((button) => {
        button.addEventListener("click", function () {
            addToCart(this);
        });
    });

    const processOrderButton = document.querySelector("#process-order-button");
    if (processOrderButton) {
        processOrderButton.addEventListener("click", processOrder);
    }
}

// Inicializar el carrito cuando el documento esté listo
document.addEventListener("DOMContentLoaded", initCart);