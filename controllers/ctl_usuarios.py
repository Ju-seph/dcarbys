from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
import controllers.ctl_encrypt as ctl_encrypt
from controllers.ctl_encrypt import encrypt, decrypt
from datetime import datetime
from bson.objectid import ObjectId
from models.user import User

import re

db = Mongodb().db()

def save_user(request):
    alertas = {"tipo": "", "message": ""}

    if request.method == 'GET':
        return render_template("views/usuarios/registro_usuarios.html")

    if request.method == 'POST':
        try:
            # Normalizar los datos del formulario
            nombreUsuario = request.form["u_nombreUsuario"].strip().lower()  # Eliminar espacios y convertir a minúsculas
            correo = request.form["u_correo"].strip().lower()  # Eliminar espacios y convertir a minúsculas
            clave = request.form["u_clave"].strip()  # Eliminar espacios

            # Validar el formato del correo electrónico
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', correo):
                alertas["tipo"] = "danger"
                alertas["message"] = "El correo electrónico no es válido."
                return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)

            # Validar la seguridad de la contraseña (sin caracteres especiales)
            if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[A-Za-z\d]{8,}$', clave):
                alertas["tipo"] = "danger"
                alertas["message"] = "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número."
                return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)

            # Comprobar si el usuario ya existe
            existe = db.users.find_one({"$and": [{"correo": correo}, {"nombreUsuario": nombreUsuario}]})

            if existe:
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

            alertas["tipo"] = "success"
            alertas["message"] = "Usuario creado correctamente. Ahora puedes iniciar sesión."
            return render_template("views/usuarios/login_usuarios.html", alertas=alertas)

        except Exception as e:
            print(f"Error al crear el usuario: {e}")
            alertas["tipo"] = "danger"
            alertas["message"] = f"Ocurrió un error al crear el usuario: {e}"
            return render_template("views/usuarios/registro_usuarios.html", alertas=alertas)

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
                clave_encriptada = usuario["clave"]
                if ctl_encrypt.decrypt(clave_encriptada) == clave:
                    session["usuario_id"] = str(usuario["_id"])
                    session["nombreUsuario"] = usuario["nombreUsuario"]
                    session["rol"] = usuario.get("rol", "cliente")

                    alertas["tipo"] = "success"
                    alertas["message"] = "Sesión iniciada correctamente."

                    # Redirigir según el rol
                    if session["rol"] == "Administrador":
                        return render_template("views/principal.html", alertas=alertas)
                    elif session["rol"] == "Asistente":
                        return render_template("views/principal.html", alertas=alertas)
                    else:
                        return redirect(url_for('begin'))
                else:
                    alertas["tipo"] = "danger"
                    alertas["message"] = "Contraseña incorrecta."
            else:
                alertas["tipo"] = "danger"
                alertas["message"] = "El nombre de usuario no existe."

        except Exception as e:
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
    if request.method == 'POST':
        try:
            # Obtener todos los usuarios de la base de datos
            usuarios = db.users.find()
            lista_usuarios = list(usuarios)

            # Procesar cada usuario
            for usuario in lista_usuarios:
                usuario["_id"] = str(usuario["_id"])  # Convertir ObjectId a cadena
                usuario["id"] = usuario["_id"]        # Agregar un alias "id"

                # Desencriptar la clave (si es necesario)
                try:
                    usuario["clave"] = ctl_encrypt.decrypt(usuario["clave"])
                except Exception as e:
                    print(f"Error al desencriptar clave para el usuario {usuario.get('nombreUsuario', 'Desconocido')}: {e}")
                    usuario["clave"] = "Error al desencriptar"

            # Estructura esperada por DataTables
            datos = {"data": lista_usuarios}
            return jsonify(datos), 200  # Usar jsonify directamente para JSON válido

        except Exception as e:
            print(f"Error al obtener los usuarios: {e}")
            return jsonify({"message": f"Error al obtener los usuarios: {e}"}), 500

    return jsonify({"message": "Petición Incorrecta"}), 405






def create_user(request):
    alertas = {"tipo": "", "message": ""}

    if request.method == 'POST':
        try:
            # Normalizar los datos del formulario
            nombreUsuario = request.form["u_nombreUsuario"].strip().lower()  # Eliminar espacios y convertir a minúsculas
            correo = request.form["u_correo"].strip().lower()  # Eliminar espacios y convertir a minúsculas
            clave = request.form["u_clave"].strip()  # Eliminar espacios
            rol = request.form["u_rol"]

            # Validar el formato del correo electrónico
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', correo):
                alertas["tipo"] = "danger"
                alertas["message"] = "El correo electrónico no es válido."
                return jsonify(alertas), 400

            # Validar la seguridad de la contraseña (sin caracteres especiales)
            if not re.match(r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)[A-Za-z\d]{8,}$', clave):
                alertas["tipo"] = "danger"
                alertas["message"] = "La contraseña debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número."
                return jsonify(alertas), 400

            # Comprobar si el usuario ya existe
            existe = db.users.find_one({"$and": [{"correo": correo}, {"nombreUsuario": nombreUsuario}]})

            if existe:
                alertas["tipo"] = "danger"
                alertas["message"] = "El usuario ya existe. Por favor, elige un nombre de usuario o correo diferente."
                return jsonify(alertas), 400

            # Encriptar la clave
            clave = ctl_encrypt.encrypt(clave)

            # Crear el objeto del usuario
            usuario = User(nombreUsuario, correo, clave, rol, status="activo")
            usuario.createUser()

            # Guardar en la base de datos
            db.users.insert_one(usuario.getUser())

            alertas["tipo"] = "success"
            alertas["message"] = "Usuario creado correctamente."
            return jsonify(alertas), 201

        except Exception as e:
            print(f"Error al crear el usuario: {e}")
            alertas["tipo"] = "danger"
            alertas["message"] = f"Ocurrió un error al crear el usuario: {e}"
            return jsonify(alertas), 500

    alertas["tipo"] = "warning"
    alertas["message"] = "Método no permitido."
    return jsonify(alertas), 405



def edit_user(request):
    alertas = {"tipo": "", "message": ""}

    if request.method == 'POST':
        try:
            # Obtener los datos del formulario
            user_id = request.form["u_id"]
            nombreUsuario = request.form["u_nombreUsuario"].strip().lower()
            correo = request.form["u_correo"].strip().lower()
            rol = request.form["u_rol"]

            # Validar el formato del correo electrónico
            if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', correo):
                alertas["tipo"] = "danger"
                alertas["message"] = "El correo electrónico no es válido."
                return jsonify(alertas), 400

            # Actualizar el usuario en la base de datos
            db.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {
                    "nombreUsuario": nombreUsuario,
                    "correo": correo,
                    "rol": rol,
                    "updateDateTime": datetime.now()
                }}
            )

            alertas["tipo"] = "success"
            alertas["message"] = "Usuario actualizado correctamente."
            return jsonify(alertas), 200

        except Exception as e:
            print(f"Error al editar el usuario: {e}")
            alertas["tipo"] = "danger"
            alertas["message"] = f"Ocurrió un error al editar el usuario: {e}"
            return jsonify(alertas), 500

    alertas["tipo"] = "warning"
    alertas["message"] = "Método no permitido."
    return jsonify(alertas), 405



def delete_user(request):
    alertas = {"tipo": "", "message": ""}

    if request.method == 'POST':
        try:
            # Obtener el ID del usuario a eliminar
            user_id = request.form["u_id"]

            # Eliminar el usuario de la base de datos
            db.users.delete_one({"_id": ObjectId(user_id)})

            alertas["tipo"] = "success"
            alertas["message"] = "Usuario eliminado correctamente."
            return jsonify(alertas), 200

        except Exception as e:
            print(f"Error al eliminar el usuario: {e}")
            alertas["tipo"] = "danger"
            alertas["message"] = f"Ocurrió un error al eliminar el usuario: {e}"
            return jsonify(alertas), 500

    alertas["tipo"] = "warning"
    alertas["message"] = "Método no permitido."
    return jsonify(alertas), 405


def get_user(request):
    if request.method == 'POST':
        try:
            user_id = request.form["u_id"]
            usuario = db.users.find_one({"_id": ObjectId(user_id)})
            if usuario:
                # Convertir ObjectId a cadena
                usuario["_id"] = str(usuario["_id"])

                # Desencriptar la clave (opcional)
                if "clave" in usuario:
                    try:
                        usuario["clave"] = ctl_encrypt.decrypt(usuario["clave"])
                    except Exception as e:
                        print(f"Error al desencriptar la clave: {e}")
                        usuario["clave"] = ""  # Dejar vacío si hay un error

                return jsonify({"success": True, "usuario": usuario}), 200
            else:
                return jsonify({"success": False, "message": "Usuario no encontrado."}), 404
        except Exception as e:
            return jsonify({"success": False, "message": str(e)}), 500
    return jsonify({"success": False, "message": "Método no permitido."}), 405