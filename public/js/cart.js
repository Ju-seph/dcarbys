const cart = JSON.parse(localStorage.getItem("cart")) || []

function updateCart() {
  const cartCount = document.getElementById("cart-count")
  if (cartCount) {
    cartCount.textContent = cart.reduce((sum, item) => sum + item.quantity, 0)
  }

  localStorage.setItem("cart", JSON.stringify(cart))

  const cartItems = document.getElementById("cart-items")
  const cartTotal = document.getElementById("cart-total")

  if (cartItems && cartTotal) {
    cartItems.innerHTML = ""
    let total = 0

    cart.forEach((item, index) => {
      const li = document.createElement("li")
      li.className = "list-group-item d-flex justify-content-between align-items-center"
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
          <button class="btn btn-sm btn-danger remove-from-cart" data-index="${index}" data-id="${item.id}" data-quantity="${item.quantity}">
            <i class="bi bi-trash"></i>
          </button>
        </div>
      `
      cartItems.appendChild(li)
      total += item.price * item.quantity
    })

    cartTotal.textContent = total.toFixed(2)
  }
}

function removeFromCart(index) {
  cart.splice(index, 1)
  updateCart()
}

function initCart() {
  updateCart()

  const cartItems = document.getElementById("cart-items")
  if (cartItems) {
    cartItems.addEventListener("click", (e) => {
      const target = e.target.closest("[data-index]")
      if (!target) return

      const index = Number.parseInt(target.getAttribute("data-index"))

      if (target.classList.contains("remove-from-cart")) {
        removeFromCart(index)
      } else if (target.classList.contains("increase-quantity")) {
        cart[index].quantity++
        updateCart()
      } else if (target.classList.contains("decrease-quantity")) {
        if (cart[index].quantity > 1) {
          cart[index].quantity--
          updateCart()
        } else {
          removeFromCart(index)
        }
      }
    })
  }

  const addToCartButtons = document.querySelectorAll(".add-to-cart")
  addToCartButtons.forEach((button) => {
    button.addEventListener("click", function () {
      addToCart(this)
    })
  })
}

function addToCart(button) {
  const id = button.getAttribute("data-id")
  const name = button.getAttribute("data-name")
  const price = Number.parseFloat(button.getAttribute("data-price"))
  const imageUrl = button.getAttribute("data-image")
  const quantity = 1

  const existingItem = cart.find((item) => item.id === id)
  if (existingItem) {
    existingItem.quantity += quantity
  } else {
    cart.push({ id, name, price, imageUrl, quantity })
  }
  updateCart()

  alert("Producto agregado al carrito")
}

document.addEventListener("DOMContentLoaded", initCart)

