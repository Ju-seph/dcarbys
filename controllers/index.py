from flask import render_template, session, redirect, url_for

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
            return render_template("views/index.html")
        
        elif request.method == "POST":
            # Procesa los datos enviados en el formulario (ejemplo)
            usuario = request.form.get("usuario", "").strip()
            clave = request.form.get("clave", "").strip()

            if usuario and clave:
                # Validar usuario y clave aquí
                if usuario == "admin" and clave == "123":  # Ejemplo de autenticación básica
                    session["id"] = "admin_id"
                    session["rol"] = "Administrador"
                    return redirect(url_for("principal"))
                else:
                    mensaje_error = "Usuario o contraseña incorrectos."
            else:
                mensaje_error = "Debes completar todos los campos."

            # Si hay errores, recarga la página con un mensaje
            return render_template("views/index.html", error=mensaje_error)

    except Exception as e:
        print(f"Error en inicio: {e}")
        return "Se produjo un error en la aplicación.", 500


def principal():
   if "id" in session:
      return render_template("/views/principal.html")
   else:
      return redirect(url_for("index"))