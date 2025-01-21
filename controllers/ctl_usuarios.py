from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
import controllers.ctl_encrypt as ctl_encrypt
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId
from models.user import User

import re

db = Mongodb().db()

def save_user(request):
    # Inicializar el diccionario de alertas
    alertas = {"tipo": "", "message": ""}

    # Si es una solicitud GET, renderizar la página de registro
    if request.method == 'GET':
        return render_template("views/usuarios/registro_usuarios.html")

    # Si es una solicitud POST, procesar el registro del usuario
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombreUsuario = request.form["u_nombreUsuario"]
            correo = request.form["u_correo"]
            clave = request.form["u_clave"]

            # Comprobar si el usuario ya existe
            existe = db.users.find_one({"$and": [{"correo": correo}, {"nombreUsuario": nombreUsuario}]})

            if existe:
                # Usuario existente, enviar mensaje de error
                alertas["tipo"] = "danger"
                alertas["message"] = "El usuario ya existe. Por favor, elige un nombre de usuario o correo diferente."
                return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)

            # Encriptar la clave
            clave = ctl_encrypt.encrypt(clave)

            # Crear el objeto del usuario
            usuario = User(nombreUsuario, correo, clave, rol="cliente", status="activo")
            usuario.createUser()

            # Guardar en la base de datos
            db.users.insert_one(usuario.getUser())

            # Usuario creado exitosamente
            alertas["tipo"] = "success"
            alertas["message"] = "Usuario creado correctamente. Ahora puedes iniciar sesión."
            return render_template("views/usuarios/login_usuarios.html", alertas=alertas)

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al crear el usuario: {e}")
            alertas["tipo"] = "danger"
            alertas["message"] = f"Ocurrió un error al crear el usuario: {e}"
            return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)

    # Si el método no es GET ni POST, devolver error 405
    alertas["tipo"] = "warning"
    alertas["message"] = "Método no permitido."
    return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)




def login_user(request):
    alertas = {"tipo": "", "message": ""}

    if request.method == 'GET':
        return render_template("views/usuarios/login_usuarios.html")

    if request.method == 'POST':
        try:
            nombreUsuario = request.form["u_nombreUsuario"]
            clave = request.form["u_clave"]

            # Buscar usuario en la base de datos
            usuario = db.users.find_one({"nombreUsuario": nombreUsuario})

            if usuario:
                # Verificar la contraseña
                clave_encriptada = usuario["clave"]
                if ctl_encrypt.decrypt(clave_encriptada) == clave:
                    # Guardar datos del usuario en la sesión
                    session["usuario_id"] = str(usuario["_id"])
                    session["nombreUsuario"] = usuario["nombreUsuario"]
                    session["rol"] = usuario.get("rol", "nombreUsuario")  # Asegurar que el rol está definido
                    alertas["tipo"] = "success"
                    alertas["message"] = "Sesión iniciada correctamente."

                    # Redirigir según el rol
                    if session["rol"] == "Administrador":
                        return render_template("views/principal.html", alertas=alertas)
                    else:
                        return render_template("views/index.html", alertas=alertas)
                else:
                    # Contraseña incorrecta
                    alertas["tipo"] = "danger"
                    alertas["message"] = "Contraseña incorrecta."
            else:
                # Usuario no encontrado
                alertas["tipo"] = "danger"
                alertas["message"] = "El nombre de usuario no existe."

        except Exception as e:
            # Error general
            alertas["tipo"] = "danger"
            alertas["message"] = f"Error al iniciar sesión: {e}"

        return render_template("views/usuarios/login_usuarios.html", alertas=alertas)

    return abort(405)




def logout_user():
    # Eliminar las variables de sesión
    session.clear()
    # Redirigir al inicio
    return redirect(url_for('begin'))


# Funciones Dentro de principal.html

def ver_usuarios(request):
    try:
        # Verificar si el método es POST
        if request.method == 'POST':
            # Obtener el usuario actual de la sesión
            usuario_actual = session.get("nombreUsuario")
            rol_actual = session.get("rol")
            
            if not usuario_actual or rol_actual != "Administrador":
                # Validar que el usuario esté autenticado y sea administrador
                return jsonify({"message": "Acceso no autorizado."}), 403

            # Consultar usuarios excluyendo al actual y a otros administradores
            usuarios = db.users.find({
                "$and": [
                    {"nombreUsuario": {"$ne": usuario_actual}},  # Excluir al usuario en sesión
                    {"rol": {"$ne": "Administrador"}}  # Excluir administradores
                ]
            })

            datos_usuarios = []

            # Procesar los usuarios
            for user in usuarios:
                try:
                    # Desencriptar la clave
                    user["clave"] = ctl_encrypt.decrypt(user["clave"])
                except Exception as e:
                    print(f"Error al desencriptar clave para el usuario {user.get('nombreUsuario', 'Desconocido')}: {e}")
                    user["clave"] = "Error al desencriptar"

                # Convertir ObjectId a string y agregar a la lista
                user["_id"] = str(user["_id"])
                datos_usuarios.append(user)

            # Preparar respuesta para DataTables
            datos = {"data": datos_usuarios}
            return json.dumps(datos, default=str), 200

        # Si el método no es POST, devolver error 405
        return jsonify({"message": "Método no permitido."}), 405

    except Exception as e:
        # Manejar errores generales
        print(f"Error al obtener usuarios: {e}")
        return jsonify({"message": f"Error interno del servidor: {e}"}), 500





def create_user(request):
    # Inicializar el diccionario de alertas
    alertas = {"tipo": "", "message": ""}

    
    # Si es una solicitud POST, procesar el registro del usuario
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombreUsuario = request.form["u_nombreUsuario"]
            correo = request.form["u_correo"]
            clave = request.form["u_clave"]
            rol = request.form["u_rol"]

            # Comprobar si el usuario ya existe
            existe = db.users.find_one({"$and": [{"correo": correo}, {"nombreUsuario": nombreUsuario}]})

            if existe:
                # Usuario existente, enviar mensaje de error
                alertas["tipo"] = "danger"
                alertas["message"] = "El usuario ya existe. Por favor, elige un nombre de usuario o correo diferente."
                return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)

            # Encriptar la clave
            clave = ctl_encrypt.encrypt(clave)

            # Crear el objeto del usuario
            usuario = User(nombreUsuario, correo, clave, rol, status="activo")
            usuario.createUser()

            # Guardar en la base de datos
            db.users.insert_one(usuario.getUser())

            # Usuario creado exitosamente
            alertas["tipo"] = "success"
            alertas["message"] = "Usuario creado correctamente."
            

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al crear el usuario: {e}")
            alertas["tipo"] = "danger"
            alertas["message"] = f"Ocurrió un error al crear el usuario: {e}"
            

    # Si el método no es GET ni POST, devolver error 405
    alertas["tipo"] = "warning"
    alertas["message"] = "Método no permitido."
    