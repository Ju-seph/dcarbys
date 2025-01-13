from flask import Flask, request, render_template
import controllers.index as indx
import controllers.ctl_usuarios as usu
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





if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))
