document.addEventListener('DOMContentLoaded', function () {
    // Inicializar DataTable
    var tabla = $('#table_producto').DataTable({
        ajax: {
            url: '/productos',
            method: 'POST',
            dataSrc: function (json) {
                return json.data || [];
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'No se pudieron cargar los datos. Por favor, recargue la página.',
                });
            }
        },
        columns: [
            { data: "id", className: "text-center" }, // ID (oculto)
            { data: "nombreProducto", className: "text-center" },
            { data: "precio", className: "text-center" },
            { data: "cantidad", className: "text-center" },
            { data: "categoria", className: "text-center" },
            { data: "descripcion", className: "text-center" },
            {
                data: "imagen_path",
                className: "text-center",
                render: function (data) {
                    return data
                        ? `<img src="${data}" alt="Imagen Producto" style="width: 60px; height: 60px; object-fit: cover;">`
                        : "No disponible";
                }
            },
            { data: "tiempo_preparacion", className: "text-center" },
            {
                data: null,
                className: "text-center",
                defaultContent: `
                    <button type="button" class="btn btn-primary btn-editar-producto">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="btn btn-danger btn-eliminar-producto">
                        <i class="bi bi-trash"></i>
                    </button>`
            }
        ],
        columnDefs: [
            {
                targets: 0,
                visible: false,
                searchable: false
            }
        ],
        order: [[0, "asc"]],
        language: { url: "https://cdn.datatables.net/plug-ins/1.10.15/i18n/Spanish.json" },
        pageLength: 30,
        lengthMenu: [10, 20, 30]
    });

    // Botón para abrir el modal de agregar producto
    document.getElementById('btn-add-producto').addEventListener('click', function () {
        // Limpiar el formulario
        document.getElementById('form_producto').reset();
        document.getElementById('productoModalLabel').textContent = 'Agregar Producto';
        document.getElementById('form_producto').setAttribute('data-action', 'save');

        // Ocultar la vista previa de la imagen
        document.getElementById('imagen-preview').style.display = 'none';

        // Eliminar cualquier campo oculto de ID
        const hiddenIdField = document.querySelector('input[name="u_id"]');
        if (hiddenIdField) hiddenIdField.remove();

        // Mostrar el modal usando JavaScript puro
        const productoModal = new bootstrap.Modal(document.getElementById('productoModal'));
        productoModal.show();
    });

    // Eliminar producto
    document.querySelector('#table_producto tbody').addEventListener('click', function (e) {
        if (e.target.closest('.btn-eliminar-producto')) {
            const row = e.target.closest('tr');
            const data = tabla.row(row).data();

            Swal.fire({
                title: '¿Estás seguro?',
                text: `¿Deseas eliminar el producto "${data.nombreProducto}"?`,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, eliminar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (result.isConfirmed) {
                    // Crear FormData para enviar
                    const formData = new FormData();
                    formData.append('u_id', data.id);

                    // Enviar solicitud AJAX
                    fetch('/del_productos', {
                        method: 'POST',
                        body: formData
                    })
                        .then(response => response.json())
                        .then(data => {
                            Swal.fire(
                                '¡Eliminado!',
                                'El producto ha sido eliminado correctamente.',
                                'success'
                            );
                            tabla.ajax.reload(null, false);
                        })
                        .catch(error => {
                            Swal.fire(
                                'Error',
                                'Ha ocurrido un error al eliminar el producto.',
                                'error'
                            );
                            console.error('Error:', error);
                        });
                }
            });
        }
    });

    // Editar producto
    document.querySelector('#table_producto tbody').addEventListener('click', function (e) {
        if (e.target.closest('.btn-editar-producto')) {
            const row = e.target.closest('tr');
            const data = tabla.row(row).data();

            // Eliminar cualquier campo oculto de ID previo
            const hiddenIdField = document.querySelector('input[name="u_id"]');
            if (hiddenIdField) hiddenIdField.remove();

            // Establecer valores del formulario
            document.getElementById('productoModalLabel').textContent = 'Editar Producto';
            document.getElementById('u_nombreProducto').value = data.nombreProducto;
            document.getElementById('u_precio').value = data.precio;
            document.getElementById('u_cantidad').value = data.cantidad;
            document.getElementById('u_categoria').value = data.categoria;
            document.getElementById('u_descripcion').value = data.descripcion;
            document.getElementById('u_tiempo_preparacion').value = data.tiempo_preparacion;

            // Mostrar la imagen actual si existe
            if (data.imagen_path) {
                document.getElementById('current-image').src = data.imagen_path;
                document.getElementById('imagen-preview').style.display = 'block';
            } else {
                document.getElementById('imagen-preview').style.display = 'none';
            }

            // Establecer acción del formulario y agregar campo oculto de ID
            document.getElementById('form_producto').setAttribute('data-action', 'edit');
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'u_id';
            hiddenInput.value = data.id;
            document.getElementById('form_producto').appendChild(hiddenInput);

            // Mostrar el modal
            const productoModal = new bootstrap.Modal(document.getElementById('productoModal'));
            productoModal.show();
        }
    });

    // Manejar envío del formulario
    document.getElementById('form_producto').addEventListener('submit', function (e) {
        e.preventDefault();

        // Deshabilitar el botón de envío para evitar múltiples envíos
        document.getElementById('btn-submit-producto').disabled = true;

        // Determinar la URL basada en la acción
        const action = this.getAttribute('data-action');
        const url = action === 'edit' ? '/edit_productos' : '/save_productos';

        // Crear FormData para enviar
        const formData = new FormData(this);

        // Enviar solicitud AJAX usando Fetch API
        fetch(url, {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                // Cerrar el modal manualmente
                const modalElement = document.getElementById('productoModal');
                const modalInstance = bootstrap.Modal.getInstance(modalElement);
                modalInstance.hide();

                // Esperar a que se cierre el modal antes de mostrar la alerta
                setTimeout(() => {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Éxito!',
                        text: data.message || 'Operación completada con éxito',
                    });

                    // Recargar la tabla después de un breve retraso
                    setTimeout(() => {
                        tabla.ajax.reload(null, false);
                    }, 300);
                }, 300);
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Ha ocurrido un error. Por favor, inténtelo de nuevo.',
                });
            })
            .finally(() => {
                // Habilitar el botón de envío nuevamente
                document.getElementById('btn-submit-producto').disabled = false;
            });
    });

    // Limpiar el modal cuando se cierra
    document.getElementById('productoModal').addEventListener('hidden.bs.modal', function () {
        document.getElementById('form_producto').reset();
        document.getElementById('imagen-preview').style.display = 'none';
    });
});