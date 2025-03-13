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
from models.Pedido import Pedido  # Importar la clase Pedido

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

@app.route('/contacto', methods=["GET"])
def contacto():
    return render_template('views/contactos.html')

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

@app.route('/usuarios', methods=['GET'])
def obtener_usuarios():
    try:
        # Obtener usuarios de la base de datos
        usuarios = db.users.find({})
        lista_usuarios = []
        for usuario in usuarios:
            usuario["_id"] = str(usuario["_id"])  # Convertir ObjectId a string
            lista_usuarios.append(usuario)
        return jsonify({"data": lista_usuarios}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

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
    payphone={"token":os.getenv("token"),"storeid":os.getenv("storeid")}
    return render_template('views/checkout.html', payphone=payphone)

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


# Pedidos para el Administrador

@app.route('/obtener_pedidos_pendientes', methods=['GET'])
def obtener_pedidos_pendientes():
    try:
        pedidos = db.pedidos_temporales.find({"estado": "pendiente"})
        lista_pedidos = []
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            lista_pedidos.append(pedido)
        return jsonify({"data": lista_pedidos}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/obtener_pedidos_transcurso', methods=['GET'])
def obtener_pedidos_transcurso():
    try:
        pedidos = db.pedidos.find({"estado": "en transcurso"})
        lista_pedidos = []
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            lista_pedidos.append(pedido)
        return jsonify({"data": lista_pedidos}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    
    

@app.route('/obtener_pedidos_finalizados', methods=['GET'])
def obtener_pedidos_finalizados():
    try:
        pedidos = db.pedidos.find({"estado": "finalizado"})
        lista_pedidos = []
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            lista_pedidos.append(pedido)
        return jsonify({"data": lista_pedidos}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/obtener_pedidos_cancelados', methods=['GET'])
def obtener_pedidos_cancelados():
    try:
        # Buscar los pedidos cancelados en la colección de pedidos
        pedidos = db.pedidos.find({"estado": "cancelado"})
        lista_pedidos = []
        for pedido in pedidos:
            # Convertir ObjectId a string
            pedido["_id"] = str(pedido["_id"])
            
            # Asegurarse de que los campos opcionales tengan valores por defecto
            pedido["cancelado_por"] = pedido.get("cancelado_por", "Sistema")
            pedido["rol_cancelado"] = pedido.get("rol_cancelado", "Desconocido")
            pedido["fecha_cancelacion"] = pedido.get("fecha_cancelacion", "Fecha no disponible")
            
            # Verificar el formato de la fecha
            if isinstance(pedido["fecha_cancelacion"], datetime):
                pedido["fecha_cancelacion"] = pedido["fecha_cancelacion"].isoformat()  # Convertir a ISO 8601
            
            lista_pedidos.append(pedido)
        
        return jsonify({"data": lista_pedidos}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    


@app.route('/finalizar_pedido/<pedido_id>', methods=['POST'])  # Cambia GET a POST
def finalizar_pedido(pedido_id):
    return ped.finalizar_pedido(pedido_id)


@app.route('/obtener_detalles_pedido/<pedido_id>', methods=['GET'])
def obtener_detalles_pedido_route(pedido_id):
    return ped.obtener_detalles_pedido(pedido_id)

@app.route('/cancelar_pedido_admin/<pedido_id>', methods=['POST'])
def cancelar_pedido_admin(pedido_id):
    return ped.cancelar_pedido_admin(pedido_id)


@app.route('/cancelar_pedido_asist/<pedido_id>', methods=['POST'])
def cancelar_pedido_asist(pedido_id):
    return ped.cancelar_pedido_asist(pedido_id)

@app.route('/estado_pedido/<pedido_id>', methods=['GET'])
def estado_pedido(pedido_id):
    try:
        print(f"Buscando pedido con ID: {pedido_id}")  # Log para verificar el ID recibido

        # Buscar el pedido en la colección de pedidos temporales
        pedido_temporal = db.pedidos_temporales.find_one({"_id": ObjectId(pedido_id)})
        if pedido_temporal:
            print("Pedido encontrado en pedidos_temporales")  # Log para verificar la colección
            return jsonify({
                "success": True,
                "estado": pedido_temporal.get("estado", "pendiente"),
                "tiempo_estimado": "",
                "cancelado_por": None
            }), 200

        # Si no se encuentra en pedidos temporales, buscar en pedidos confirmados o cancelados
        pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id)})
        if pedido:
            print("Pedido encontrado en pedidos")  # Log para verificar la colección
            return jsonify({
                "success": True,
                "estado": pedido.get("estado", "en transcurso"),
                "tiempo_estimado": pedido.get("tiempo_estimado", ""),
                "cancelado_por": pedido.get("cancelado_por", None)
            }), 200

        # Si no se encuentra en ninguna colección, devolver error
        print("Pedido no encontrado en ninguna colección")  # Log para verificar el error
        return jsonify({"success": False, "message": "Pedido no encontrado"}), 404
    except Exception as e:
        print(f"Error en la ruta /estado_pedido: {str(e)}")  # Log para capturar excepciones
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/cancelar_pedido_cliente/<pedido_id>', methods=['POST'])
def cancelar_pedido_cliente(pedido_id):
    return ped.cancelar_pedido_cliente(pedido_id)

@app.route('/confirmar_pedido_cliente/<pedido_id>', methods=['POST'])
def confirmar_pedido_cliente(pedido_id):
    return ped.confirmar_pedido_cliente(pedido_id)

@app.route('/aceptar_pedido/<pedido_id>', methods=['POST'])
def aceptar_pedido(pedido_id):
    return ped.aceptar_pedido(pedido_id)

@app.route('/obtener_numero_pedidos_pendientes', methods=['GET'])
def obtener_numero_pedidos_pendientes():
    try:
        # Contar los pedidos pendientes
        count = db.pedidos_temporales.count_documents({"estado": "pendiente"})
        return jsonify({"success": True, "count": count}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))