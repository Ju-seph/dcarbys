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

@app.route('/edit_usuarios', methods=['POST'])
def edit_user_route():
    return usu.edit_user(request)

@app.route('/del_usuarios', methods=['POST'])
def delete_user_route():
    return usu.delete_user(request)

@app.route('/obtener_usuario', methods=['POST'])
def get_user_route():
    return usu.get_user(request)

    

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

@app.route('/generar_reporte_ventas', methods=['GET'])
def generar_reporte_ventas_route():
    return ped.generar_reporte_ventas()

#payphone funcion//

@app.route('/payphone_webhook', methods=['POST'])
def payphone_webhook():
    return ped.procesar_pago_payphone(request)

@app.route('/marcar_notificado/<pedido_id>', methods=['POST'])
def marcar_notificado(pedido_id):
    try:
        db.pedidos.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"notificado": True}}
        )
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route('/payphone_return', methods=['GET'])
def payphone_return():
    # Capturar los parámetros de la URL
    payment_id = request.args.get('id')
    client_transaction_id = request.args.get('clientTransactionId')
    
    print(f"PayPhone redirect: payment_id={payment_id}, clientTransactionId={client_transaction_id}")
    
    if not payment_id or not client_transaction_id:
        flash("Error en el proceso de pago. Parámetros incompletos.", "danger")
        return redirect(url_for('begin'))
    
    # Verificar si el usuario está autenticado
    if 'usuario_id' not in session:
        # Guardar los parámetros en la sesión para procesarlos después del login
        session['payment_id'] = payment_id
        session['client_transaction_id'] = client_transaction_id
        session['next'] = url_for('payphone_return')
        flash("Por favor inicia sesión para completar tu pedido", "info")
        return redirect(url_for('login_user'))
    
    # Buscar si ya existe un pedido con este ID de transacción
    pedido = db.pedidos.find_one({"payphone_id": payment_id})
    if pedido:
        flash("Tu pedido ya ha sido procesado correctamente", "success")
        return redirect(url_for('begin'))
    
    # Buscar el pedido temporal por el número de pedido (clientTransactionId)
    pedido_temporal = db.pedidos_temporales.find_one({"numero_pedido": client_transaction_id})
    
    if not pedido_temporal:
        # Si no existe un pedido temporal, crear uno nuevo
        try:
            # Recuperar el carrito del localStorage
            cart = json.loads(request.cookies.get('cart', '[]'))
            
            if not cart:
                # Intentar recuperar el carrito de localStorage a través de JavaScript
                return render_template('views/recuperar_carrito.html', 
                                      payment_id=payment_id, 
                                      client_transaction_id=client_transaction_id)
            
            # Calcular el total
            total = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart)
            
            # Crear un nuevo pedido temporal
            nuevo_pedido = {
                "numero_pedido": client_transaction_id,
                "usuario_id": session['usuario_id'],
                "productos": cart,
                "nombre": session.get('nombreUsuario', 'Usuario'),
                "celular": session.get('celular', ''),
                "direccion": session.get('direccion', ''),
                "ciudad": session.get('ciudad', ''),
                "referencia": '',
                "total": total,
                "metodo_pago": 'payphone',
                "payphone_id": payment_id,
                "payphone_status": 'Approved',
                "estado": "confirmado",
                "fecha_confirmacion": datetime.now(),
                "createDateTime": datetime.now()
            }
            
            # Insertar el pedido temporal
            result = db.pedidos_temporales.insert_one(nuevo_pedido)
            pedido_temporal = nuevo_pedido
            pedido_temporal['_id'] = result.inserted_id
            
        except Exception as e:
            print(f"Error al crear pedido temporal: {str(e)}")
            import traceback
            traceback.print_exc()
            flash("Error al procesar el pedido", "danger")
            return redirect(url_for('begin'))
    
    # Crear un pedido confirmado a partir del pedido temporal
    try:
        pedido_confirmado = {
            "numero_pedido": pedido_temporal['numero_pedido'],
            "usuario_id": pedido_temporal['usuario_id'],
            "productos": pedido_temporal['productos'],
            "nombre": pedido_temporal.get('nombre', session.get('nombreUsuario', 'Usuario')),
            "celular": pedido_temporal.get('celular', ''),
            "direccion": pedido_temporal.get('direccion', ''),
            "ciudad": pedido_temporal.get('ciudad', ''),
            "referencia": pedido_temporal.get('referencia', ''),
            "total": pedido_temporal['total'],
            "metodo_pago": 'payphone',
            "payphone_id": payment_id,
            "payphone_status": 'Approved',
            "estado": "en transcurso",
            "fecha_confirmacion": datetime.now(),
            "fecha_pago": datetime.now(),
            "notificado": False
        }
        
        # Insertar el pedido confirmado
        result = db.pedidos.insert_one(pedido_confirmado)
        
        if result.inserted_id:
            # Eliminar el pedido temporal si existe
            if '_id' in pedido_temporal:
                db.pedidos_temporales.delete_one({"_id": pedido_temporal['_id']})
            
            # Mostrar mensaje de éxito
            flash("¡Tu pedido ha sido confirmado con éxito!", "success")
            
            # Redirigir a una página de confirmación o a la página principal
            return render_template('views/confirmacion_pedido.html', 
                                  pedido=pedido_confirmado, 
                                  payment_id=payment_id, 
                                  client_transaction_id=client_transaction_id)
        else:
            flash("Error al confirmar el pedido", "danger")
            return redirect(url_for('begin'))
            
    except Exception as e:
        print(f"Error al confirmar pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        flash("Error al confirmar el pedido", "danger")
        return redirect(url_for('begin'))



@app.route('/procesar_pago_payphone_manual', methods=['POST'])
def procesar_pago_payphone_manual():
    try:
        payment_id = request.form.get('payment_id')
        client_transaction_id = request.form.get('client_transaction_id')
        cart_json = request.form.get('cart')
        payphone_response_json = request.form.get('payphone_response')
        
        print(f"Procesando pago manual: payment_id={payment_id}, clientTransactionId={client_transaction_id}")
        
        if not payment_id or not client_transaction_id:
            flash("Error en el proceso de pago. Parámetros incompletos.", "danger")
            return redirect(url_for('begin'))
        
        # Verificar si el usuario está autenticado
        if 'usuario_id' not in session:
            session['payment_id'] = payment_id
            session['client_transaction_id'] = client_transaction_id
            session['next'] = url_for('payphone_return')
            flash("Por favor inicia sesión para completar tu pedido", "info")
            return redirect(url_for('login_user'))
        
        # Verificar si ya existe un pedido con este ID de transacción
        pedido = db.pedidos.find_one({"payphone_id": payment_id})
        if pedido:
            flash("Tu pedido ya ha sido procesado correctamente", "success")
            return redirect(url_for('begin'))
        
        # Parsear el carrito y la respuesta de PayPhone
        cart = json.loads(cart_json) if cart_json else []
        payphone_response = json.loads(payphone_response_json) if payphone_response_json else {}
        
        if not cart:
            flash("No hay productos en el carrito", "warning")
            return redirect(url_for('begin'))
        
        # Calcular el total
        total = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart)
        
        # Crear un pedido confirmado directamente
        pedido_confirmado = {
            "numero_pedido": client_transaction_id,
            "usuario_id": session['usuario_id'],
            "productos": cart,
            "nombre": session.get('nombreUsuario', 'Usuario'),
            "celular": session.get('celular', ''),
            "direccion": session.get('direccion', ''),
            "ciudad": session.get('ciudad', ''),
            "referencia": '',
            "total": total,
            "metodo_pago": 'payphone',
            "payphone_id": payment_id,
            "payphone_status": 'Approved',
            "estado": "en transcurso",
            "fecha_confirmacion": datetime.now(),
            "fecha_pago": datetime.now(),
            "notificado": False
        }
        
        # Insertar el pedido confirmado
        result = db.pedidos.insert_one(pedido_confirmado)
        
        if result.inserted_id:
            # Limpiar el carrito
            flash("¡Tu pedido ha sido confirmado con éxito!", "success")
            
            # Redirigir a la página de confirmación
            return render_template('views/confirmacion_pedido.html', 
                                  pedido=pedido_confirmado, 
                                  payment_id=payment_id, 
                                  client_transaction_id=client_transaction_id)
        else:
            flash("Error al confirmar el pedido", "danger")
            return redirect(url_for('begin'))
            
    except Exception as e:
        print(f"Error al procesar pago manual: {str(e)}")
        import traceback
        traceback.print_exc()
        flash("Error al procesar el pedido", "danger")
        return redirect(url_for('begin'))




if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))