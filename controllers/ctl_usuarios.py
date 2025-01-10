from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
import controllers.ctl_encrypt as ctl_encrypt
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId
from models.user import User

import re

db = Mongodb().db()

def save_user(request):
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
                jsonify({"message":"Usuario Existente"}), 404
                return redirect(url_for("registro_usuarios"))

            # Encriptar la clave
            clave_encriptada = ctl_encrypt.encrypt(clave)

            # Crear el objeto del usuario
            usuario = User(nombreUsuario, correo, clave_encriptada, rol="usuario", status="activo")

            usuario.crear_usuario()

            # Guardar en la base de datos
            db.users.insert_one(usuario.obtener_user())

            # Mensaje de éxito y redirección
            jsonify({"message":"Usuario creado correctamente"}), 200
            return redirect(url_for("index"))

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al crear el usuario: {e}")
            return redirect(url_for("save_user"))

    # Si el método no es GET ni POST, devolver error 405
    return jsonify({"message": "Método no permitido"}), 405



def login_user(request):
    # Si es una solicitud GET, renderizar la página de inicio de sesión
    if request.method == 'GET':
        return render_template("views/usuarios/login_usuarios.html")

    # Si es una solicitud POST, procesar el inicio de sesión del usuario
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombreUsuario = request.form["u_nombreUsuario"]
            clave = request.form["u_clave"]

            # Buscar al usuario por nombreUsuario
            usuario = db.users.find_one({"nombreUsuario": nombreUsuario})

            if usuario:
                # Verificar la contraseña desencriptando
                clave_encriptada = usuario["clave"]
                if ctl_encrypt.decrypt(clave_encriptada) == clave:
                    # Guardar los datos del usuario en la sesión
                    session["usuario_id"] = str(usuario["_id"])
                    session["nombreUsuario"] = usuario["nombreUsuario"]
                    

                    # Mensaje de éxito y redirección al panel principal
                    jsonify("Inicio de sesión exitoso.", "success")
                    return redirect(url_for("index"))
                else:
                    # Contraseña incorrecta
                    jsonify("Contraseña incorrecta.", "error")
                    return redirect(url_for("login_usuarios"))
            else:
                # Usuario no encontrado
                jsonify("El nombre de usuario no existe.", "error")
                return redirect(url_for("login_usuarios"))

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            jsonify(f"Error al iniciar sesión: {e}", "error")
            return redirect(url_for("login_usuarios"))

    # Si el método no es GET ni POST, devolver error 405
    return jsonify({"message": "Método no permitido"}), 405
