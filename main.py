from flask import Flask, request, render_template, jsonify, session, redirect, url_for, flash
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import controllers.index as indx
import controllers.ctl_usuarios as usu
import controllers.ctl_productos as prod
import controllers.ctl_pedidos as ped
from database.mongodb import Mongodb
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

db = Mongodb().db()

# Cargar variables de entorno
load_dotenv()

# Configuración de la aplicación Flask
app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = os.getenv("KEY")  # Clave secreta desde el archivo .env

# Configuración del directorio de imágenes
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'public/img')  # Directorio para guardar imágenes
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Crear el directorio de imágenes si no existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configurar el planificador
scheduler = BackgroundScheduler()
scheduler.add_job(func=ped.limpiar_pedidos_expirados, trigger="interval", minutes=5)
scheduler.start()

# Asegurarse de que el planificador se detenga cuando la aplicación se cierre
atexit.register(lambda: scheduler.shutdown())

@app.after_request
def after_request(response):
    response.headers["cache-control"] = "no-cache, no-store, must-revalidate"
    return response

# Rutas principales

# -- Index renderiza los productos--
@app.route('/', methods=["GET", "POST"])
def begin():
    productos = list(db.productos.find({"status": "activo"}))
    return render_template('views/index.html', productos=productos)


# Manejo de session 
@app.route('/registro_usuarios', methods=["GET", "POST"])
def save_user():
    return usu.save_user(request)

@app.route('/login_usuarios', methods=["GET", "POST"])
def login_user():
    return usu.login_user(request)

@app.route('/logout', methods=["GET"])
def logout_user():
    return usu.logout_user()

# ADMINISTRADOR
@app.route('/ver_usuarios', methods=["GET", "POST"])
def ver_usuarios():
    return usu.ver_usuarios(request)

@app.route('/save_usuarios', methods=["POST"])
def create_user():
    return usu.create_user(request)

# PRODUCTOS
@app.route('/productos', methods=["POST"])
def ver_productos():
    return prod.ver_productos(request)

@app.route('/save_productos', methods=["POST"])
def save_product():
    return prod.save_product(request)

@app.route('/edit_productos', methods=["GET", "POST"])
def edit_product():
    return prod.edit_product(request)

@app.route('/del_productos', methods=["GET", "POST"])
def del_product():
    return prod.del_product(request)

# Nueva ruta para el checkout
@app.route('/checkout', methods=['GET'])
def checkout():
    if 'usuario_id' not in session:
        session['next'] = url_for('checkout')
        return redirect(url_for('login_user'))
    
    return render_template('views/checkout.html')

# Nueva ruta para procesar el pedido
@app.route('/procesar_pedido', methods=['POST'])
def procesar_pedido():
    return ped.procesar_pedido(request)

@app.route('/confirmar_pedido/<order_id>', methods=['POST'])
def confirmar_pedido(order_id):
    return ped.confirmar_pedido(order_id)

@app.route('/cancelar_pedido/<order_id>', methods=['POST'])
def cancelar_pedido(order_id):
    return ped.cancelar_pedido(order_id)

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('rol') != 'Administrador':
        flash("Acceso no autorizado.", "danger")
        return redirect(url_for('begin'))
    return render_template("views/principal.html")

if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))

