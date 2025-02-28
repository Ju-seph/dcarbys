const cart = JSON.parse(localStorage.getItem("cart")) || [];

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
      li.className = "list-group-item d-flex justify-content-between align-items-center";
      li.innerHTML = `
        <div class="d-flex align-items-center">
          <img src="${item.imageUrl}" alt="${item.name}" class="me-2" style="width: 50px; height: 50px; object-fit: cover;">
          <div>
            <span class="fw-bold">${item.name}</span>
            <div class="btn-group btn-group-sm mt-1" role="group">
              <button type="button" class="btn btn-outline-secondary decrease-quantity" data-index="${index}">-</button>
              <span class="btn btn-outline-secondary px-2">${item.quantity}</span>
              <button type="button" class="btn btn-outline-secondary increase-quantity" data-index="${index}">+</button>
            </div>
          </div>
        </div>
        <div class="d-flex align-items-center">
          <span class="me-2">$${(item.price * item.quantity).toFixed(2)}</span>
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
  cart.splice(index, 1);
  updateCart();
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
  } else {
    alert("No hay más stock disponible para este producto.");
  }
}

// Función para disminuir la cantidad de un producto en el carrito
function decreaseQuantity(index) {
  if (cart[index].quantity > 1) {
    cart[index].quantity--;
    updateCart();
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
    } else {
      alert("No hay más stock disponible para este producto.");
      return;
    }
  } else {
    cart.push({ id, name, price, imageUrl, quantity: 1 });
  }
  updateCart();

  alert("Producto agregado al carrito");
}

// Función para procesar el pedido
function processOrder() {
  // Validar si el carrito está vacío
  if (cart.length === 0) {
    alert("Tu carrito está vacío. Agrega productos antes de procesar el pedido.");
    return; // Detener la función si el carrito está vacío
  }

  // Si el carrito no está vacío, redirigir a la página de checkout
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

  // Agregar evento al botón de procesar pedido
  const processOrderButton = document.querySelector("#process-order-button");
  if (processOrderButton) {
    processOrderButton.addEventListener("click", processOrder);
  }
}

// Inicializar el carrito cuando el documento esté listo
document.addEventListener("DOMContentLoaded", initCart);