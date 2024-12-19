from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId
import re


def inicio_usuarios(request):
    return render_template("views/usuarios/usuarios_login.html")




def registrar_usuario(request):
    if request.method == 'POST':
        # Recibir los datos del formulario
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')
        confirmar_contrasena = request.form.get('confirmar_contrasena')
        
        # Validación básica
        if not nombre or not correo or not contrasena or not confirmar_contrasena:
            flash("Por favor complete todos los campos.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro

        if contrasena != confirmar_contrasena:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro
        
        # Validar formato de correo electrónico
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, correo):
            flash("El correo electrónico no tiene un formato válido.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro

        # Encriptar la contraseña
        contrasena_encriptada = encrypt(contrasena)

        # Conectar a la base de datos
        db = Mongodb()
        coleccion_usuarios = db.get_collection('usuarios')

        # Verificar si el correo ya existe
        usuario_existente = coleccion_usuarios.find_one({"correo": correo})
        if usuario_existente:
            flash("Ya existe un usuario con ese correo.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro

        # Crear el nuevo usuario
        nuevo_usuario = {
            "nombre": nombre,
            "correo": correo,
            "contrasena": contrasena_encriptada,
            "activo": True  # Establecer el estado del usuario como activo
        }

        # Insertar el usuario en la base de datos
        coleccion_usuarios.insert_one(nuevo_usuario)
        flash("Usuario registrado con éxito.", "success")

        # Redirigir a la página de inicio de sesión
        return redirect(url_for('inicio_usuarios'))  # Redirigir a la página de login
    
    # Si la solicitud no es POST, simplemente renderiza el formulario de registro
    return render_template("views/usuarios/usuarios_login.html")


def iniciar_sesion(request):
    if request.method == 'POST':
        correo = request.form.get('correo')
        contrasena = request.form.get('contrasena')

        if not correo or not contrasena:
            flash("Por favor complete ambos campos.", "error")
            return redirect(url_for('inicio_usuarios'))  # Redirigir al formulario de login

        # Conectar a la base de datos
        db = Mongodb()
        coleccion_usuarios = db.get_collection('usuarios')

        # Buscar el usuario en la base de datos por correo
        usuario = coleccion_usuarios.find_one({"correo": correo})
        if not usuario:
            flash("Correo no encontrado.", "error")
            return redirect(url_for('inicio_usuarios'))  # Redirigir al formulario de login

        # Comparar la contraseña encriptada
        contrasena_encriptada = encrypt(contrasena)  # Encriptar la contraseña ingresada
        if usuario['contrasena'] != contrasena_encriptada:
            flash("Contraseña incorrecta.", "error")
            return redirect(url_for('inicio_usuarios'))  # Redirigir al formulario de login

        # Si el usuario y contraseña son correctos, se inicia sesión
        session['user_id'] = str(usuario['_id'])
        session['nombre'] = usuario['nombre']
        session['correo'] = usuario['correo']

        flash("Inicio de sesión exitoso.", "success")

        # Redirigir a la página principal (o donde sea necesario)
        return redirect(url_for('pagina_principal'))  # Redirigir a la página principal después de iniciar sesión

    # Si no es un POST, simplemente renderiza el formulario de login
    return render_template("views/usuarios/usuarios_login.html")
