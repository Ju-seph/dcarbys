$(document).ready( function () {
    var tabla = $('#table_usuario').DataTable({
        "ajax":{
            "url":"/usuarios",
            "method":"post"
        },
        "columns":[
            {"data": "_id", "className": "text-center"},
            {"data":"cedula", "className": "text-center"},
            {"data":"nombre", "className": "text-center"},
            {"data":"usuario", "className": "text-center"},
            {"data":"rol", "className": "text-center"},
            {"data": null}

        ],
        "columnDefs":[
            {
                target:0,
                visible:false,
                searchable:false
            },
            {
                "target": -1,
                "data": null,
                "defaultContent": '<button type="button" class="btn btn-primary btn-editar-usuario">Editar</button> <button type="button" class="btn btn-danger btn-eliminar-usuario">Eliminar</button> ' 
                
            }

        ],
        "language":{"url":"https://cdn.datatables.net/plug-ins/1.10.15/i18n/Spanish.json"},
        "pageLength": 30,
        "lengthMenu": [10,20,30]
    });

    $('#table_usuario tbody').on("click", ".btn-eliminar-usuario",function(){
        var datos = tabla.row($(this).parents("tr")).data();

        var pregunta = confirm("¿Estas seguro de eliminar el usuario "+ datos.nombre+" ?");

        if(pregunta){
            $.ajax({
                url:"/del_usuarios",
                type:"POST",
                data:{u_cedula:datos.cedula}
            }).done(function(){
                alert("El Usuario " + datos.nombre + " Eliminado correctamente")
                $("#table_usuario").DataTable().ajax.reload();
            }).fail(function(e){
                alert("Error:" + e.responseJSON.message )
            })
        }
    })


    $('#table_usuario tbody').on("click", ".btn-editar-usuario",function(){
        var datos = tabla.row($(this).parents("tr")).data();
    
        $("#userModal").modal("show");

        var form = document.getElementById("form_usuario")

        document.getElementById("btn-editar-usuario").style = "display:visible"
        document.getElementById("btn-guardar-usuario").style = "display:none"

        document.getElementById("u_cedula").value = datos.cedula
        document.getElementById("u_nombre").value = datos.nombre
        document.getElementById("u_usuario").value = datos.usuario
        document.getElementById("u_clave").value = datos.clave
        document.getElementById("u_rol").value = datos.rol

        form.setAttribute("url","/edit_usuarios")

    })
} );

$('#form_usuario').submit(function(e){

    e.preventDefault();

    var form = $("#form_usuario")[0]

    $.ajax({
        url: form.getAttribute("url"),
        type: 'POST',
        data: new FormData(form),
        processData: false,
        contentType: false,
        cache: false

    }).done(function(e){

        if(e.message != "Usuario Actualizado correctamente"){
            alert("Usuario creado correctamente")
        }else{
            alert("Usuario Actualizado correctamente")
        }
        $("#userModal").modal("hide")
        $("#table_usuario").DataTable().ajax.reload();
    }).fail(function(e){
        alert("Error:" + e.responseJSON.message) 
    });

    
})


$("#userModal").on("show.bs.modal", function(event){
    var form = document.getElementById("form_usuario")
    form.reset();

    document.getElementById("btn-guardar-usuario").style = "display:visible"
    document.getElementById("btn-editar-usuario").style = "display:none"

    form.setAttribute("url","/save_usuarios")
})