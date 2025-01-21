$(document).ready(function () {
    var tabla = $('#table_usuario').DataTable({
        "ajax": {
            "url": "/usuarios",
            "method": "post"
        },
        "columns": [
            { "data": "_id", "className": "text-center" }, // Usar "_id" para el identificador
            { "data": "nombreUsuario", "className": "text-center" },
            { "data": "correo", "className": "text-center" },
            { "data": "clave", "className": "text-center" },
            { "data": "rol", "className": "text-center" },
            { "data": null }
        ],
        "columnDefs": [
            {
                target: 0,
                visible: false, // Ocultar el ID si no es necesario mostrarlo
                searchable: false
            },
            {
                "target": -1,
                "data": null,
                "defaultContent": `
                    <button type="button" class="btn btn-primary btn-editar-usuario"><i class="bi bi-pencil"></i></button> <button type="button" class="btn btn-danger btn-eliminar-usuario"><i class="bi bi-trash"></i></button> 
                `
            }
        ],
        "language": { "url": "https://cdn.datatables.net/plug-ins/1.10.15/i18n/Spanish.json" },
        "pageLength": 30,
        "lengthMenu": [10, 20, 30]
    });

    // Botón Eliminar Usuario
    $('#table_usuario tbody').on("click", ".btn-eliminar-usuario", function () {
        var datos = tabla.row($(this).parents("tr")).data();

        var pregunta = confirm("¿Estás seguro de eliminar el usuario " + datos.nombreUsuario + "?");

        if (pregunta) {
            $.ajax({
                url: "/del_usuarios",
                type: "POST",
                data: { u_id: datos._id } // Usar "_id" para identificar al usuario
            }).done(function () {
                alert("El Usuario " + datos.nombreUsuario + " eliminado correctamente");
                $("#table_usuario").DataTable().ajax.reload();
            }).fail(function (e) {
                alert("Error: " + e.responseJSON.message);
            });
        }
    });

    // Botón Editar Usuario
    $('#table_usuario tbody').on("click", ".btn-editar-usuario", function () {
        var datos = tabla.row($(this).parents("tr")).data();

        $("#userModal").modal("show");

        var form = document.getElementById("form_usuario");

        document.getElementById("btn-editar-usuario").style.display = "inline";
        document.getElementById("btn-guardar-usuario").style.display = "none";

        document.getElementById("u_nombreUsuario").value = datos.nombreUsuario;
        document.getElementById("u_correo").value = datos.correo;
        document.getElementById("u_clave").value = datos.clave;
        document.getElementById("u_rol").value = datos.rol;

        form.setAttribute("url", "/edit_usuarios");
    });

    // Manejo del Formulario
    $('#form_usuario').submit(function (e) {
        e.preventDefault();

        var form = $("#form_usuario")[0];

        $.ajax({
            url: form.getAttribute("url"),
            type: 'POST',
            data: new FormData(form),
            processData: false,
            contentType: false,
            cache: false
        }).done(function (e) {
            if (e.message !== "Usuario Actualizado correctamente") {
                alert("Usuario creado correctamente");
            } else {
                alert("Usuario Actualizado correctamente");
            }
            $("#userModal").modal("hide");
            $("#table_usuario").DataTable().ajax.reload();
        }).fail(function (e) {
            alert("Error: " + e.responseJSON.message);
        });
    });

    $("#userModal").on("show.bs.modal", function (event) {
        var form = document.getElementById("form_usuario");
        form.reset();

        document.getElementById("btn-guardar-usuario").style.display = "inline";
        document.getElementById("btn-editar-usuario").style.display = "none";

        form.setAttribute("url", "/save_usuarios");
    });
});
