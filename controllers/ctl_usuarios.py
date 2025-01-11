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
            usuario = User(nombreUsuario, correo, clave, rol="usuario", status="activo")
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

                    # Redirigir al panel principal
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


