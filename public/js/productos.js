$(document).ready(function () {
    var tabla = $('#table_producto').DataTable({
        "ajax": {
            "url": "/productos",
            "method": "POST"
        },
        "columns": [
            { "data": "id", "className": "text-center" }, // ID (oculto)
            { "data": "nombreProducto", "className": "text-center" },
            { "data": "precio", "className": "text-center" },
            { "data": "cantidad", "className": "text-center" },
            { "data": "categoria", "className": "text-center" },
            { "data": "descripcion", "className": "text-center" },
            {
                "data": "imagen_path",
                "className": "text-center",
                "render": function (data) {
                    return data
                        ? `<img src="${data}" alt="Imagen Producto" style="width: 60px; height: 60px; object-fit: cover;">`
                        : "No disponible";
                }
            },
            { "data": "tiempo_preparacion", "className": "text-center" },
            {
                "data": "destacado",
                "className": "text-center",
                "render": function (data) {
                    return data ? '<i class="bi bi-star-fill text-warning"></i>' : '<i class="bi bi-star"></i>';
                }
            },
            {
                "data": null,
                "className": "text-center",
                "defaultContent": `
                    <button type="button" class="btn btn-primary btn-editar-producto">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="btn btn-danger btn-eliminar-producto">
                        <i class="bi bi-trash"></i>
                    </button>`
            }
        ],
        "columnDefs": [
            {
                "targets": 0,
                "visible": false,
                "searchable": false
            }
        ],
        "order": [[0, "asc"]],
        "language": { "url": "https://cdn.datatables.net/plug-ins/1.10.15/i18n/Spanish.json" },
        "pageLength": 30,
        "lengthMenu": [10, 20, 30]
    });

    // Eliminar producto
    $('#table_producto tbody').on("click", ".btn-eliminar-producto", function () {
        var datos = tabla.row($(this).parents("tr")).data();

        if (confirm(`¿Estás seguro de eliminar el producto "${datos.nombreProducto}"?`)) {
            $.ajax({
                url: "/del_productos",
                type: "POST",
                data: { u_id: datos.id }
            }).done(function () {
                alert(`El producto "${datos.nombreProducto}" fue eliminado correctamente`);
                tabla.ajax.reload();
            }).fail(function (e) {
                alert(`Error: ${e.responseJSON.message}`);
            });
        }
    });

    // Editar producto
    $('#table_producto tbody').on("click", ".btn-editar-producto", function () {
        var datos = tabla.row($(this).parents("tr")).data();

        $("#productoModal").modal("show");

        // Llenar campos del modal con datos del producto
        $("#u_nombreProducto").val(datos.nombreProducto);
        $("#u_precio").val(datos.precio);
        $("#u_cantidad").val(datos.cantidad);
        $("#u_categoria").val(datos.categoria);
        $("#u_descripcion").val(datos.descripcion);
        $("#u_tiempo_preparacion").val(datos.tiempo_preparacion);
        $("#u_destacado").prop("checked", datos.destacado);

        // Asegurarse de que el ID del producto se incluya
        // Si ya existe, actualízalo; si no, créalo
        if ($("#u_id").length === 0) {
            $("#form_producto").append(`<input type="hidden" id="u_id" name="u_id" value="${datos.id}">`);
        } else {
            $("#u_id").val(datos.id);
        }

        // Configurar el formulario para enviar al endpoint de edición
        $("#form_producto").attr("action", "/edit_productos");

        // Cambiar botones
        $("#btn-guardar-producto").hide();
        $("#btn-editar-producto").show();
    });

    // Guardar producto (crear o editar)
    $('#form_producto').submit(function (e) {
        e.preventDefault();

        var form = $(this);
        var url = form.attr("action");

        $.ajax({
            url: url,
            type: 'POST',
            data: new FormData(this),
            processData: false,
            contentType: false,
            cache: false
        }).done(function (e) {
            alert(e.message);
            $("#productoModal").modal("hide");
            tabla.ajax.reload();
        }).fail(function (e) {
            alert(`Error: Ocurrió un error al actualizar el producto: ${e.responseJSON.message}`);
        });
    });

    // Modal para agregar nuevo producto
    $("#productoModal").on("show.bs.modal", function () {
        $("#form_producto")[0].reset();
        $("#u_id").remove(); // Eliminar campo ID si existe

        // Configurar para creación
        $("#form_producto").attr("action", "/save_productos");
        $("#btn-guardar-producto").show();
        $("#btn-editar-producto").hide();
    });
});
