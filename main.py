from flask import Flask, request, render_template
import controllers.index as indx
import controllers.ctl_usuarios as usu
import controllers.ctl_productos as prod
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = os.getenv("KEY")  # Clave secreta desde el archivo .env

@app.after_request
def after_request(response):
    response.headers["cache-control"]= "no-cache, no-store, must-revalidate"
    return response

@app.route('/',methods=["GET", "POST"])
def begin():
    return indx.begin(request)

@app.route('/registro_usuarios', methods=["GET", "POST"])
def save_user():
    return usu.save_user(request)


@app.route('/login_usuarios',methods=["GET", "POST"])
def login_user():
    return usu.login_user(request)

@app.route('/logout', methods=["GET"])
def logout_user():
    return usu.logout_user()

# ADMINISTRADOR

# --Ver usuarios desde la administracion--

@app.route('/ver_usuarios',methods=["POST"])
def ver_usuarios():
    return usu.ver_usuarios(request)

# --Crear usuarios desde la administracion--

@app.route('/save_usuarios',methods=["POST"])
def create_user():
    return usu.create_user(request)



# PRODUCTOS

@app.route('/productos',methods=["POST"])
def ver_productos():
    return prod.ver_productos(request)

@app.route('/save_productos',methods=["POST"])
def save_product():
    return prod.save_product(request)


@app.route('/edit_productos',methods=["POST"])
def edit_product():
    return prod.edit_product(request)


if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))
