from flask import render_template, session, redirect, url_for, abort
from database.mongodb import Mongodb
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId

# Inicializar conexión a MongoDB
db = Mongodb().db()

def begin(request):
    return render_template("views/index.html")

def inicio(request):
    """
    Función para manejar la página de inicio.
    """
    try:
        if request.method == "GET":
            # Si hay una sesión activa, redirige a la página principal
            if "id" in session:
                return redirect(url_for("principal"))

            # Si no hay sesión activa, muestra la página de inicio
            return render_template("views/login.html")
        
        elif request.method == "POST":
            # Procesa los datos enviados en el formulario
            usuario = request.form.get("usuario", "").strip()
            clave = request.form.get("clave", "").strip()

            if usuario and clave:
                # Verifica si el usuario es el administrador
                if usuario == "admin" and clave == "123":  # Credenciales de prueba
                    session["id"] = "admin_id"
                    session["rol"] = "Administrador"
                    session["usuario"] = "admin"
                    return redirect(url_for("principal"))
                
                # Buscar usuario en la base de datos
                user = db.users.find_one({"usuario": usuario})
                if user:
                    # Verifica la contraseña desencriptada
                    if decrypt(user["clave"]) == clave:
                        session["id"] = str(user["_id"])
                        session["rol"] = user["rol"]
                        session["usuario"] = user["usuario"]
                        return redirect(url_for("principal"))
                    else:
                        mensaje_error = "Contraseña incorrecta."
                else:
                    mensaje_error = "El usuario no existe."
            else:
                mensaje_error = "Debes completar todos los campos."

            # Si hay errores, recarga la página con un mensaje
            return render_template("views/index.html", error=mensaje_error)

    except Exception as e:
        print(f"Error en inicio: {e}")
        return "Se produjo un error en la aplicación.", 500


def principal():

    if "id" in session:
        return render_template("views/principal.html")
    else:
        return redirect(url_for("index"))


def salir():

    if "id" in session:
        session.pop("id", None)
        session.pop("rol", None)
        session.pop("usuario", None)
        return redirect(url_for("index"))
    else:
        abort(403)
