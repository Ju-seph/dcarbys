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

// Función para verificar el stock antes de procesar el pedido
async function verificarStockDisponible() {
    try {
        // Si el carrito está vacío, no hay nada que verificar
        if (cart.length === 0) {
            return { success: true, message: "Carrito vacío" };
        }

        // Crear un objeto con los productos y cantidades del carrito
        const productosCarrito = cart.map(item => ({
            id: item.id,
            quantity: item.quantity
        }));

        // Enviar la solicitud al servidor para verificar el stock
        const response = await fetch('/verificar_stock', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ productos: productosCarrito })
        });

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error al verificar el stock:', error);
        return {
            success: false,
            message: "Error al verificar el stock. Por favor, intenta nuevamente."
        };
    }
}

// Función para procesar el pedido
async function processOrder() {
    if (cart.length === 0) {
        showAlert("Tu carrito está vacío. Agrega productos antes de procesar el pedido.", "warning");
        return;
    }

    // Mostrar un indicador de carga
    Swal.fire({
        title: 'Verificando disponibilidad...',
        text: 'Por favor espera mientras verificamos el stock de los productos',
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    // Verificar el stock antes de proceder al checkout
    const verificacion = await verificarStockDisponible();

    // Si la verificación es exitosa, intentar reservar el stock
    if (verificacion.success) {
        // Crear un objeto con los productos y cantidades del carrito
        const productosCarrito = cart.map(item => ({
            id: item.id,
            quantity: item.quantity
        }));

        try {
            // Reservar el stock
            const reservaResponse = await fetch('/reservar_stock', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ productos: productosCarrito })
            });

            const reservaData = await reservaResponse.json();

            // Cerrar el indicador de carga
            Swal.close();

            if (reservaData.success) {
                // Si la reserva es exitosa, guardar el ID de reserva y redirigir al checkout
                if (reservaData.reserva_id) {
                    localStorage.setItem('reserva_id', reservaData.reserva_id);
                }
                window.location.href = "/checkout";
            } else {
                // Si hay problemas al reservar, mostrar mensaje de error
                if (reservaData.productosNoDisponibles && reservaData.productosNoDisponibles.length > 0) {
                    // Mostrar los productos que no tienen suficiente stock
                    let mensaje = "Los siguientes productos no tienen suficiente stock:<br><ul>";
                    reservaData.productosNoDisponibles.forEach(producto => {
                        mensaje += `<li>${producto.name} (Disponible: ${producto.stockActual}, Solicitado: ${producto.stockSolicitado})</li>`;
                    });
                    mensaje += "</ul>";

                    Swal.fire({
                        icon: 'error',
                        title: 'Stock insuficiente',
                        html: mensaje,
                        confirmButtonText: 'Actualizar carrito'
                    }).then((result) => {
                        if (result.isConfirmed) {
                            // Actualizar el carrito con las cantidades disponibles
                            actualizarCarritoConStockDisponible(reservaData.productosNoDisponibles);
                        }
                    });
                } else {
                    // Mensaje genérico si no hay detalles específicos
                    showAlert(reservaData.message || "No hay suficiente stock para completar tu pedido.", "error");
                }
            }
        } catch (error) {
            console.error('Error al reservar el stock:', error);
            Swal.close();
            showAlert("Error al procesar tu pedido. Por favor, intenta nuevamente.", "error");
        }
    } else {
        // Cerrar el indicador de carga
        Swal.close();

        // Si hay problemas de stock, mostrar mensaje de error
        if (verificacion.productosNoDisponibles && verificacion.productosNoDisponibles.length > 0) {
            // Mostrar los productos que no tienen suficiente stock
            let mensaje = "Los siguientes productos no tienen suficiente stock:<br><ul>";
            verificacion.productosNoDisponibles.forEach(producto => {
                mensaje += `<li>${producto.name} (Disponible: ${producto.stockActual}, Solicitado: ${producto.stockSolicitado})</li>`;
            });
            mensaje += "</ul>";

            Swal.fire({
                icon: 'error',
                title: 'Stock insuficiente',
                html: mensaje,
                confirmButtonText: 'Actualizar carrito'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Actualizar el carrito con las cantidades disponibles
                    actualizarCarritoConStockDisponible(verificacion.productosNoDisponibles);
                }
            });
        } else {
            // Mensaje genérico si no hay detalles específicos
            showAlert(verificacion.message || "No hay suficiente stock para completar tu pedido.", "error");
        }
    }
}

// Función para actualizar el carrito con el stock disponible
function actualizarCarritoConStockDisponible(productosNoDisponibles) {
    let carritoActualizado = false;

    // Actualizar las cantidades en el carrito según el stock disponible
    productosNoDisponibles.forEach(producto => {
        const itemIndex = cart.findIndex(item => item.id === producto.id);
        if (itemIndex !== -1) {
            if (producto.stockActual > 0) {
                // Si hay algo de stock, actualizar la cantidad
                cart[itemIndex].quantity = producto.stockActual;
                carritoActualizado = true;
            } else {
                // Si no hay stock, eliminar el producto del carrito
                cart.splice(itemIndex, 1);
                carritoActualizado = true;
            }
        }
    });

    // Actualizar el carrito en la interfaz
    if (carritoActualizado) {
        updateCart();
        showAlert("Tu carrito ha sido actualizado con las cantidades disponibles.", "info");
    }
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