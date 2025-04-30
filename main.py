from flask import Flask, request, render_template, jsonify, session, redirect, url_for, flash, send_from_directory
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import controllers.index as indx
import controllers.ctl_usuarios as usu
import controllers.ctl_productos as prod
import controllers.ctl_pedidos as ped
import controllers.ctl_reportes as rep
from database.mongodb import Mongodb
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta
from timezone_utils import get_ecuador_time, format_ecuador_time
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
# Configurar el planificador para limpiar pedidos y reservas expiradas
scheduler = BackgroundScheduler()
scheduler.add_job(func=ped.limpiar_pedidos_expirados, trigger="interval", minutes=5)
scheduler.add_job(func=ped.limpiar_reservas_expiradas, trigger="interval", minutes=15)  # Ejecutar cada 15 minutos
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
        pedidos = db.pedidos.find({"estado": "cancelado"})
        lista_pedidos = []
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            lista_pedidos.append(pedido)
        return jsonify({"data": lista_pedidos}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/finalizar_pedido/<pedido_id>', methods=['POST']) 
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

# Añadir la ruta para cancelar pedido por el cliente
@app.route('/cancelar_pedido_cliente/<pedido_id>', methods=['POST'])
def cancelar_pedido_cliente_route(pedido_id):
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
        return render_template('views/confirmacion_pedido.html', 
                              pedido=pedido, 
                              payment_id=payment_id, 
                              client_transaction_id=client_transaction_id)
    
    # Renderizar la plantilla para confirmar la transacción
    return render_template('views/confirmar_transaccion.html', 
                          payment_id=payment_id, 
                          client_transaction_id=client_transaction_id)



@app.route('/procesar_pago_payphone_manual', methods=['POST'])
def procesar_pago_payphone_manual():
    try:
        payment_id = request.form.get('payment_id')
        client_transaction_id = request.form.get('client_transaction_id')
        cart_json = request.form.get('cart')
        
        # Obtener datos de envío del formulario
        nombre = request.form.get('nombre')
        celular = request.form.get('celular')
        ciudad = request.form.get('ciudad')
        direccion = request.form.get('direccion')
        referencia = request.form.get('referencia')
        
        print(f"Procesando pago manual: payment_id={payment_id}, clientTransactionId={client_transaction_id}")
        print(f"Cart JSON: {cart_json}")
        print(f"Datos de envío: nombre={nombre}, celular={celular}, ciudad={ciudad}, direccion={direccion}")
        
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
            return render_template('views/confirmacion_pedido.html', 
                                  pedido=pedido, 
                                  payment_id=payment_id, 
                                  client_transaction_id=client_transaction_id,
                                  format_time=format_ecuador_time)
        
        # Parsear el carrito
        try:
            cart = json.loads(cart_json) if cart_json else []
        except json.JSONDecodeError as e:
            print(f"Error al decodificar JSON: {str(e)}")
            cart = []
        
        if not cart:
            flash("No hay productos en el carrito", "warning")
            return redirect(url_for('begin'))
        
        # Calcular el total
        total = sum(item.get('price', 0) * item.get('quantity', 0) for item in cart)
        
        # Reducir el stock de los productos
        try:
            for item in cart:
                if 'id' in item:
                    # Actualizar el stock del producto
                    db.productos.update_one(
                        {"_id": ObjectId(item['id'])},
                        {"$inc": {"cantidad": -item['quantity']}}
                    )
        except Exception as e:
            print(f"Error al actualizar el stock: {str(e)}")
        
        # Usar la hora de Ecuador
        ecuador_time = get_ecuador_time()
        
        # Crear un pedido confirmado directamente
        pedido_confirmado = {
            "numero_pedido": client_transaction_id,
            "usuario_id": session['usuario_id'],
            "productos": cart,
            "nombre": nombre or session.get('nombreUsuario', 'Usuario'),
            "celular": celular or session.get('celular', ''),
            "direccion": direccion or session.get('direccion', ''),
            "ciudad": ciudad or session.get('ciudad', ''),
            "referencia": referencia or '',
            "total": total,
            "metodo_pago": 'payphone',
            "payphone_id": payment_id,
            "payphone_status": 'Approved',
            "estado": "en transcurso",
            "fecha_confirmacion": ecuador_time,
            "fecha_pago": ecuador_time,
            "notificado": False
        }
        
        # Insertar el pedido confirmado
        result = db.pedidos.insert_one(pedido_confirmado)
        
        if result.inserted_id:
            print(f"Pedido confirmado insertado con ID: {result.inserted_id}")
            # Limpiar el carrito
            flash("¡Tu pedido ha sido confirmado con éxito!", "success")
            
            # Redirigir a la página de confirmación
            return render_template('views/confirmacion_pedido.html', 
                                  pedido=pedido_confirmado, 
                                  payment_id=payment_id, 
                                  client_transaction_id=client_transaction_id,
                                  format_time=format_ecuador_time)
        else:
            print("Error al insertar el pedido confirmado")
            flash("Error al confirmar el pedido", "danger")
            return redirect(url_for('begin'))
            
    except Exception as e:
        print(f"Error al procesar pago manual: {str(e)}")
        import traceback
        traceback.print_exc()
        flash("Error al procesar el pedido", "danger")
        return redirect(url_for('begin'))





@app.route('/confirmar_transaccion_payphone', methods=['POST'])
def confirmar_transaccion_payphone():
    try:
        # Obtener los datos del JSON
        data = request.json
        payment_id = data.get('id')
        client_transaction_id = data.get('clientTransactionId')
        
        print(f"Confirmando transacción PayPhone: payment_id={payment_id}, clientTransactionId={client_transaction_id}")
        
        # Verificar si ya existe un pedido con este ID de transacción
        pedido = db.pedidos.find_one({"payphone_id": payment_id})
        if pedido:
            return jsonify({"success": True, "message": "Pedido ya confirmado"}), 200
        
        # Hacer una solicitud a la API de PayPhone para confirmar la transacción
        import requests
        
        url = "https://pay.payphonetodoesposible.com/api/button/V2/Confirm"
        headers = {
            "Authorization": f"Bearer {os.getenv('token')}",
            "Content-Type": "application/json"
        }
        data = {
            "id": int(payment_id),
            "clientTxId": client_transaction_id
        }
        
        print(f"Enviando solicitud a PayPhone: {json.dumps(data)}")
        
        response = requests.post(url, headers=headers, json=data)
        
        print(f"Respuesta de PayPhone: {response.status_code}")
        print(f"Contenido de la respuesta: {response.text}")
        
        if response.status_code == 200:
            transaction_data = response.json()
            print(f"Datos de la transacción: {json.dumps(transaction_data)}")
            
            # Buscar el pedido temporal
            pedido_temporal = db.pedidos_temporales.find_one({"numero_pedido": client_transaction_id})
            
            if not pedido_temporal:
                # Si no existe un pedido temporal, crear uno nuevo con los datos del carrito
                # Esto se manejará en procesar_pago_payphone_manual
                return jsonify({"success": True, "message": "No se encontró pedido temporal, se procesará manualmente"}), 200
            
            # Crear un pedido confirmado
            pedido_confirmado = {
                "numero_pedido": pedido_temporal['numero_pedido'],
                "usuario_id": pedido_temporal['usuario_id'],
                "productos": pedido_temporal['productos'],
                "nombre": pedido_temporal['nombre'],
                "celular": pedido_temporal['celular'],
                "direccion": pedido_temporal['direccion'],
                "ciudad": pedido_temporal['ciudad'],
                "referencia": pedido_temporal['referencia'],
                "total": pedido_temporal['total'],
                "metodo_pago": "payphone",
                "payphone_id": payment_id,
                "payphone_status": "Approved",
                "estado": "en transcurso",
                "fecha_confirmacion": datetime.now(),
                "fecha_pago": datetime.now(),
                "notificado": False
            }
            
            # Insertar el pedido confirmado
            result = db.pedidos.insert_one(pedido_confirmado)
            
            if result.inserted_id:
                # Eliminar el pedido temporal
                db.pedidos_temporales.delete_one({"_id": pedido_temporal["_id"]})
                
                return jsonify({"success": True, "message": "Pedido confirmado correctamente"}), 200
            else:
                return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500
        else:
            print(f"Error al confirmar transacción con PayPhone: {response.status_code} - {response.text}")
            return jsonify({"success": False, "message": f"Error al confirmar la transacción con PayPhone: {response.text}"}), 500
            
    except Exception as e:
        print(f"Error al confirmar transacción PayPhone: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/confirmacion_pedido', methods=['GET'])
def confirmacion_pedido():
    # Capturar los parámetros de la URL
    payment_id = request.args.get('id')
    client_transaction_id = request.args.get('clientTransactionId')
    
    print(f"Confirmación de pedido: payment_id={payment_id}, clientTransactionId={client_transaction_id}")
    
    if not payment_id or not client_transaction_id:
        flash("Error en el proceso de pago. Parámetros incompletos.", "danger")
        return redirect(url_for('begin'))
    
    # Buscar el pedido en la base de datos
    pedido = db.pedidos.find_one({"payphone_id": payment_id})
    
    if not pedido:
        flash("No se encontró el pedido en la base de datos.", "danger")
        return redirect(url_for('begin'))
    
    # Renderizar la plantilla de confirmación
    return render_template('views/confirmacion_pedido.html', 
                          pedido=pedido, 
                          payment_id=payment_id, 
                          client_transaction_id=client_transaction_id)




@app.route('/verificar_stock', methods=['POST'])
def verificar_stock():
    try:
        data = request.json
        productos = data.get('productos', [])
        
        if not productos:
            return jsonify({"success": True, "message": "No hay productos para verificar"}), 200
        
        productos_no_disponibles = []
        
        # Verificar el stock de cada producto
        for producto_carrito in productos:
            producto_id = producto_carrito.get('id')
            cantidad_solicitada = producto_carrito.get('quantity', 0)
            
            # Buscar el producto en la base de datos
            producto_db = db.productos.find_one({"_id": ObjectId(producto_id)})
            
            if not producto_db:
                productos_no_disponibles.append({
                    "id": producto_id,
                    "name": "Producto no encontrado",
                    "stockActual": 0,
                    "stockSolicitado": cantidad_solicitada
                })
                continue
            
            # Verificar si hay suficiente stock
            if producto_db.get('cantidad', 0) < cantidad_solicitada:
                productos_no_disponibles.append({
                    "id": producto_id,
                    "name": producto_db.get('nombreProducto', 'Producto'),
                    "stockActual": producto_db.get('cantidad', 0),
                    "stockSolicitado": cantidad_solicitada
                })
        
        # Si hay productos sin suficiente stock, devolver error
        if productos_no_disponibles:
            return jsonify({
                "success": False,
                "message": "Algunos productos no tienen suficiente stock",
                "productosNoDisponibles": productos_no_disponibles
            }), 200
        
        # Si todos los productos tienen suficiente stock, devolver éxito
        return jsonify({"success": True, "message": "Stock verificado correctamente"}), 200
    
    except Exception as e:
        print(f"Error al verificar stock: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error al verificar stock: {str(e)}"}), 500



@app.route('/reservar_stock', methods=['POST'])
def reservar_stock():
    """
    Endpoint para reservar el stock de los productos en un pedido
    """
    # Verificar si el usuario está autenticado
    if 'usuario_id' not in session:
        # Redirigir al login con un mensaje
        flash("Debes iniciar sesión para reservar productos", "warning")
        # Guardar la URL actual para redirigir después del login
        session['next'] = url_for('checkout')
        # Devolver respuesta JSON con redirección
        return jsonify({
            "success": False, 
            "message": "Debes iniciar sesión para reservar productos",
            "redirect": url_for('login_user')
        }), 401
    
    # Si el usuario está autenticado, proceder con la reserva
    return ped.reservar_stock_pedido(request)

@app.route('/cancelar_reserva/<reserva_id>', methods=['POST'])
def cancelar_reserva(reserva_id):
    """
    Endpoint para cancelar una reserva de stock
    """
    return ped.cancelar_reserva_stock(reserva_id)




@app.route('/debug_payphone', methods=['GET'])
def debug_payphone():
    """
    Ruta para depurar la integración de PayPhone.
    Muestra los parámetros de la URL y la sesión.
    """
    # Obtener todos los parámetros de la URL
    params = {key: value for key, value in request.args.items()}
    
    # Obtener todos los datos de la sesión
    session_data = {key: session.get(key) for key in session}
    
    # Mostrar los datos
    return jsonify({
        "url_params": params,
        "session_data": session_data,
        "message": "Esta es una ruta de depuración para PayPhone"
    })

@app.route('/test_payphone_redirect', methods=['GET'])
def test_payphone_redirect():
    """
    Ruta para probar la redirección de PayPhone.
    Simula una redirección de PayPhone con parámetros de prueba.
    """
    # Simular parámetros de PayPhone
    payment_id = "12345"
    client_transaction_id = "67890"
    
    # Redirigir a la ruta payphone_return con los parámetros simulados
    return redirect(url_for('payphone_return', id=payment_id, clientTransactionId=client_transaction_id))




# Ruta para servir el archivo de sonido
@app.route('/static/sound/notification.mp3')
def serve_notification_sound():
    """Sirve el archivo de sonido desde static/sound/"""
    return send_from_directory('static/sound', 'notification.mp3')


@app.route('/generar_reporte_ventas', methods=['GET'])
def get_reporte_ventas():
    return rep.generar_reporte_ventas()

@app.route('/generar_pdf_reporte', methods=['GET'])
def get_pdf_reporte():
    return rep.generar_pdf_reporte()

@app.route('/obtener_pedidos_cancelados_recientes', methods=['GET'])
def obtener_pedidos_cancelados_recientes():
    try:
        # Obtener pedidos cancelados en los últimos 5 minutos y no notificados
        desde = datetime.now() - timedelta(minutes=5)
        
        pedidos = list(db.pedidos.find({
            "estado": "cancelado",
            "fecha_cancelacion": {"$gte": desde},
            "notificado": False
        }).sort("fecha_cancelacion", -1).limit(5))
        
        # Convertir ObjectId a string y formatear fechas
        for pedido in pedidos:
            pedido["_id"] = str(pedido["_id"])
            if 'fecha_cancelacion' in pedido:
                pedido["fecha_cancelacion"] = pedido["fecha_cancelacion"].isoformat()
        
        return jsonify({
            "success": True,
            "data": pedidos
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":
    # Ejecutar la aplicación Flask
    app.run(host=os.getenv("HOST", "0.0.0.0"), port=int(os.getenv("PORT", 5000)))
