from flask import Flask, request, render_template, jsonify, session, redirect, url_for
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import controllers.index as indx
import controllers.ctl_usuarios as usu
import controllers.ctl_productos as prod
from database.mongodb import Mongodb
from dotenv import load_dotenv
import os
import json
from datetime import datetime

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

# -- Index renderiza los productos y la cantidad de producto--
@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    try:
        data = request.json
        product_id = data['productId']
        quantity = data['quantity']

        # Actualizar la cantidad en la base de datos
        result = db.productos.update_one(
            {"_id": ObjectId(product_id)},
            {"$inc": {"cantidad": -quantity}}
        )

        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Cantidad actualizada correctamente"}), 200
        else:
            return jsonify({"success": False, "message": "No se pudo actualizar la cantidad"}), 400

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Manejo de session 
@app.route('/registro_usuarios', methods=["GET", "POST"])
def save_user():
    return usu.save_user(request)

@app.route('/login_usuarios', methods=["GET", "POST"])
def login_user():
    if request.method == 'POST':
        result = usu.login_user(request)
        if isinstance(result, tuple) and result[1] == 200:  # Si el login fue exitoso
            next_page = session.pop('next', url_for('begin'))
            return redirect(next_page)
        return result
    return usu.login_user(request)

@app.route('/logout', methods=["GET"])
def logout_user():
    return usu.logout_user()

# ADMINISTRADOR
@app.route('/ver_usuarios', methods=["POST"])
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
    
    cart = json.loads(request.cookies.get('cart', '[]'))
    return render_template('views/checkout.html', cart=cart)

# Nueva ruta para procesar el pedido
@app.route('/procesar_pedido', methods=['POST'])
def procesar_pedido():
    if 'usuario_id' not in session:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

    data = request.json
    cart = data['cart']
    direccion = data['direccion']
    ciudad = data['ciudad']
    codigo_postal = data['codigo_postal']

    try:
        pedido = {
            "usuario_id": session['usuario_id'],
            "productos": cart,
            "direccion": direccion,
            "ciudad": ciudad,
            "codigo_postal": codigo_postal,
            "fecha": datetime.now(),
            "estado": "pendiente"
        }
        db.pedidos.insert_one(pedido)

        # Actualizar inventario
        for item in cart:
            db.productos.update_one(
                {"_id": ObjectId(item['id'])},
                {"$inc": {"cantidad": -item['quantity']}}
            )

        return jsonify({"success": True, "message": "Pedido procesado con éxito"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))

