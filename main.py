from flask import Flask, request, render_template
import controllers.index as indx
from dotenv import load_dotenv
import os

# Cargar las variables de entorno
load_dotenv()

# Configuración de la aplicación Flask
app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = os.getenv("KEY")  # Clave secreta desde el archivo .env

@app.after_request
def after_request(response):
    response.headers["cache-control"]= "no-cache, no-store, must-revalidate"
    return response

@app.route('/',methods=["GET", "POST"])
def index():
    return indx.inicio(request)



@app.route('/principal',methods=["GET"])
def principal():
    return indx.principal()
    


if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))
