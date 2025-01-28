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
                ${item.name} - $${item.price.toFixed(2)}
                <button class="btn btn-sm btn-danger remove-from-cart" data-index="${index}" data-id="${item.id}" data-quantity="${item.quantity}">Eliminar</button>
            `
      cartItems.appendChild(li)
      total += item.price * item.quantity
    })

    cartTotal.textContent = total.toFixed(2)
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
        const currentQuantity = Number.parseInt(quantityElement.textContent)
        quantityElement.textContent = currentQuantity + quantity
      }

      // Habilitar el botón si la cantidad es mayor que cero
      const addButton = document.querySelector(`.add-to-cart[data-id="${productId}"]`)
      if (addButton) {
        addButton.disabled = false
      }

      alert("Producto eliminado del carrito")
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
      if (e.target.classList.contains("remove-from-cart")) {
        const index = Number.parseInt(e.target.getAttribute("data-index"))
        const productId = e.target.getAttribute("data-id")
        const quantity = Number.parseInt(e.target.getAttribute("data-quantity"))
        removeFromCart(index, productId, quantity)
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
  const quantity = 1

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
        cart.push({ id, name, price, quantity })
      }
      updateCart()

      const quantityElement = document.querySelector(`.product-quantity[data-id="${id}"]`)
      if (quantityElement) {
        const currentQuantity = Number.parseInt(quantityElement.textContent)
        quantityElement.textContent = currentQuantity - quantity
      }

      if (Number.parseInt(quantityElement.textContent) <= 0) {
        button.disabled = true
      }

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

