from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId
import re


def inicio_usuarios(request):
    return render_template("views/usuarios/registro_usuarios.html")




def registrar_usuario(request):
    if request.method == 'POST':
        # Recibir los datos del formulario
        nombre = request.form.get('nombre')
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')
        confirmar_contraseña = request.form.get('confirmar_contraseña')
        
        # Validación básica
        if not nombre or not correo or not contraseña or not confirmar_contraseña:
            flash("Por favor complete todos los campos.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro

        if contraseña != confirmar_contraseña:
            flash("Las contraseñas no coinciden.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro
        
        # Validar formato de correo electrónico
        email_regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
        if not re.match(email_regex, correo):
            flash("El correo electrónico no tiene un formato válido.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro

        # Conectar a la base de datos con MongoDB
        db = Mongodb()  # Instanciar la clase Mongodb
        coleccion_usuarios = db['usuarios']  # Acceder a la colección "usuarios"

        # Verificar si el correo ya existe
        usuario_existente = coleccion_usuarios.find_one({"correo": correo})
        if usuario_existente:
            flash("Ya existe un usuario con ese correo.", "error")
            return redirect(url_for('registrar_usuario'))  # Redirigir al formulario de registro

        # Encriptar la contraseña
        contraseña_encriptada = encrypt(contraseña)

        # Crear el nuevo usuario
        nuevo_usuario = {
            "nombre": nombre,
            "correo": correo,
            "contraseña": contraseña_encriptada,
            "activo": True  # Establecer el estado del usuario como activo
        }

        # Insertar el usuario en la base de datos
        coleccion_usuarios.insert_one(nuevo_usuario)
        flash("Usuario registrado con éxito.", "success")

        # Redirigir a la página de inicio de sesión
        return redirect(url_for('/index.html'))  # Redirigir a la página de login

    # Si la solicitud no es POST, simplemente renderiza el formulario de registro
    return render_template("views/usuarios/registro_usuarios.html")


def iniciar_sesion(request):
    if request.method == 'POST':
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')

        if not correo or not contraseña:
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
        contraseña_encriptada = encrypt(contraseña)  # Encriptar la contraseña ingresada
        if usuario['contrasena'] != contraseña_encriptada:
            flash("Contraseña incorrecta.", "error")
            return redirect(url_for('inicio_usuarios'))  # Redirigir al formulario de login

        # Si el usuario y contraseña son correctos, se inicia sesión
        session['user_id'] = str(usuario['_id'])
        session['nombre'] = usuario['nombre']
        session['correo'] = usuario['correo']

        flash("Inicio de sesión exitoso.", "success")

        # Redirigir a la página principal (o donde sea necesario)
        return redirect(url_for('/index.html'))  # Redirigir a la página principal después de iniciar sesión

    # Si no es un POST, simplemente renderiza el formulario de login
    return render_template("views/usuarios/login_usuarios.html")
