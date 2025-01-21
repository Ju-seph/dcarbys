$(document).ready(function () {
    var tabla = $('#table_producto').DataTable({
        "ajax": {
            "url": "/productos",
            "method": "post"
        },
        "columns": [
            { "data": "id", "className": "text-center" },
            { "data": "nombreProducto", "className": "text-center" },
            { "data": "precio", "className": "text-center" },
            { "data": "cantidad", "className": "text-center" },
            { "data": "categoria", "className": "text-center" },
            { "data": "descripcion", "className": "text-center" },
            { "data": "tiempoPreparacion", "className": "text-center" },
            { 
                "data": "destacado",
                "className": "text-center",
                "render": function(data) {
                    return data ? '<i class="bi bi-star-fill text-warning"></i>' : '<i class="bi bi-star"></i>';
                }
            },
            { "data": null }
        ],
        "columnDefs": [
            {
                "targets": 0,
                "visible": false,
                "searchable": false
            },
            {
                "targets": -1,
                "data": null,
                "defaultContent": '<button type="button" class="btn btn-primary btn-editar-producto"><i class="bi bi-pencil"></i></button> <button type="button" class="btn btn-danger btn-eliminar-producto"><i class="bi bi-trash"></i></button>'
            }
        ],
        "language": { "url": "https://cdn.datatables.net/plug-ins/1.10.15/i18n/Spanish.json" },
        "pageLength": 30,
        "lengthMenu": [10, 20, 30]
    });

    // Eliminar producto
    $('#table_producto tbody').on("click", ".btn-eliminar-producto", function () {
        var datos = tabla.row($(this).parents("tr")).data();

        var pregunta = confirm("¿Estás seguro de eliminar el producto " + datos.nombre + "?");

        if (pregunta) {
            $.ajax({
                url: "/del_productos",
                type: "POST",
                data: { u_id: datos.id }
            }).done(function () {
                alert("El producto " + datos.nombre + " fue eliminado correctamente");
                $("#table_producto").DataTable().ajax.reload();
            }).fail(function (e) {
                alert("Error: " + e.responseJSON.message);
            });
        }
    });

    // Editar producto
    $('#table_producto tbody').on("click", ".btn-editar-producto", function () {
        var datos = tabla.row($(this).parents("tr")).data();

        $("#productoModal").modal("show");

        var form = document.getElementById("form_producto");

        document.getElementById("btn-editar-producto").style = "display:visible";
        document.getElementById("btn-guardar-producto").style = "display:none";

        document.getElementById("u_nombreProducto").value = datos.nombre;
        document.getElementById("u_precio").value = datos.precio;
        document.getElementById("u_cantidad").value = datos.cantidad;
        document.getElementById("u_categoria").value = datos.categoria;
        document.getElementById("u_descripcion").value = datos.descripcion;
        document.getElementById("u_tiempo_preparacion").value = datos.tiempoPreparacion;
        document.getElementById("u_destacado").checked = datos.destacado;

        form.setAttribute("url", "/edit_productos");
    });

    // Guardar producto
    $('#form_producto').submit(function (e) {
        e.preventDefault();

        var form = $("#form_producto")[0];

        $.ajax({
            url: form.getAttribute("url"),
            type: 'POST',
            data: new FormData(form),
            processData: false,
            contentType: false,
            cache: false
        }).done(function (e) {
            if (e.message !== "Producto actualizado correctamente") {
                alert("Producto creado correctamente");
            } else {
                alert("Producto actualizado correctamente");
            }
            $("#productoModal").modal("hide");
            $("#table_producto").DataTable().ajax.reload();
        }).fail(function (e) {
            alert("Error: " + e.responseJSON.message);
        });
    });

    // Modal para agregar nuevo producto
    $("#productoModal").on("show.bs.modal", function (event) {
        var form = document.getElementById("form_producto");
        form.reset();

        document.getElementById("btn-guardar-producto").style = "display:visible";
        document.getElementById("btn-editar-producto").style = "display:none";

        form.setAttribute("url", "/save_productos");
    });
});
