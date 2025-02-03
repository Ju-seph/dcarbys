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

async function updateQuantity(index, change) {
  const item = cart[index]
  const newQuantity = item.quantity + change

  if (newQuantity <= 0) {
    return removeFromCart(index, item.id, item.quantity)
  }

  // Check available quantity
  const quantityElement = document.querySelector(`.product-quantity[data-id="${item.id}"]`)
  const availableQuantity = quantityElement ? Number.parseInt(quantityElement.textContent) : 0

  if (change > 0 && availableQuantity <= 0) {
    alert("No hay más unidades disponibles de este producto.")
    return
  }

  try {
    const response = await fetch("/update_quantity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ productId: item.id, quantity: change }),
    })

    const result = await response.json()

    if (result.success) {
      item.quantity = newQuantity
      updateCart()

      // Update available quantity
      if (quantityElement) {
        quantityElement.textContent = result.newQuantity
      }

      // Enable or disable the add button based on available quantity
      const addButton = document.querySelector(`.add-to-cart[data-id="${item.id}"]`)
      if (addButton) {
        addButton.disabled = result.newQuantity <= 0
      }
    } else {
      alert(result.message)
    }
  } catch (error) {
    console.error("Error:", error)
    alert("Hubo un error al actualizar la cantidad del producto")
  }
}

async function removeFromCart(index, productId, quantity) {
  try {
    const response = await fetch("/update_quantity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ productId: productId, quantity: -quantity }),
    })

    const result = await response.json()

    if (result.success) {
      cart.splice(index, 1)
      updateCart()

      // Actualizar la cantidad mostrada en la página si estamos en la página de productos
      const quantityElement = document.querySelector(`.product-quantity[data-id="${productId}"]`)
      if (quantityElement) {
        quantityElement.textContent = result.newQuantity
      }

      // Habilitar el botón si la cantidad es mayor que cero
      const addButton = document.querySelector(`.add-to-cart[data-id="${productId}"]`)
      if (addButton) {
        addButton.disabled = result.newQuantity <= 0
      }
    } else {
      alert(result.message)
    }
  } catch (error) {
    console.error("Error:", error)
    alert("Hubo un error al eliminar el producto del carrito")
  }
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
        const productId = target.getAttribute("data-id")
        const quantity = Number.parseInt(target.getAttribute("data-quantity"))
        removeFromCart(index, productId, quantity)
      } else if (target.classList.contains("increase-quantity")) {
        updateQuantity(index, 1)
      } else if (target.classList.contains("decrease-quantity")) {
        updateQuantity(index, -1)
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

async function addToCart(button) {
  const id = button.getAttribute("data-id")
  const name = button.getAttribute("data-name")
  const price = Number.parseFloat(button.getAttribute("data-price"))
  const imageUrl = button.getAttribute("data-image")
  const quantity = 1

  const quantityElement = document.querySelector(`.product-quantity[data-id="${id}"]`)
  const availableQuantity = quantityElement ? Number.parseInt(quantityElement.textContent) : 0

  if (availableQuantity <= 0) {
    alert("No hay más unidades disponibles de este producto.")
    return
  }

  try {
    const response = await fetch("/update_quantity", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ productId: id, quantity: quantity }),
    })

    const result = await response.json()

    if (result.success) {
      const existingItem = cart.find((item) => item.id === id)
      if (existingItem) {
        existingItem.quantity += quantity
      } else {
        cart.push({ id, name, price, imageUrl, quantity })
      }
      updateCart()

      if (quantityElement) {
        quantityElement.textContent = result.newQuantity
      }

      button.disabled = result.newQuantity <= 0

      alert("Producto agregado al carrito")
    } else {
      alert(result.message)
    }
  } catch (error) {
    console.error("Error:", error)
    alert("Hubo un error al agregar el producto al carrito")
  }
}

document.addEventListener("DOMContentLoaded", initCart)

