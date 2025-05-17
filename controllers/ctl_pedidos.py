from flask import jsonify, session, request, json
from bson.objectid import ObjectId
from database.mongodb import Mongodb
from datetime import datetime, timedelta
from models.PedidoTemporal import PedidoTemporal
from models.Pedido import Pedido
from timezone_utils import get_ecuador_time
import pymongo
import re
from pymongo import MongoClient
import pytz



db = Mongodb().db()


def procesar_pedido(request):
    if 'usuario_id' not in session:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

    data = request.json
    print("Datos recibidos en procesar_pedido:", json.dumps(data))  # Log para depuración

    # Validar el número de celular
    celular = data.get('celular')
    if not re.match(r'^09\d{8}$', celular):
        return jsonify({"success": False, "message": "Número de celular no válido. Debe tener 10 dígitos y comenzar con 09."}), 400

    try:
        # Verificar si hay una reserva asociada
        reserva_id = data.get('reserva_id')
        reserva = None
        
        if reserva_id:
            reserva = db.reservas_stock.find_one({"_id": ObjectId(reserva_id), "estado": "activa"})
            
            if not reserva:
                return jsonify({"success": False, "message": "La reserva ha expirado o no es válida. Por favor, intenta nuevamente."}), 400
            
            # Marcar la reserva como utilizada
            db.reservas_stock.update_one(
                {"_id": ObjectId(reserva_id)},
                {"$set": {"estado": "utilizada", "fecha_utilizacion": datetime.now()}}
            )
        
        # Crear el pedido temporal
        pedido_temporal = PedidoTemporal(
            numero_pedido=str(data['purchaseNumber']),  # Convertir a string para asegurar compatibilidad
            usuario_id=session['usuario_id'],
            productos=data['cart'],
            nombre=data['nombre'],
            celular=celular,
            ciudad=data['ciudad'],
            direccion=data['direccion'],
            referencia=data['referencia'],
            total=data['total'],
            metodo_pago=data['metodo_pago']  # Método de pago (efectivo o payphone)
        )
        
        # Usar la hora de Ecuador
        pedido_temporal.createPedidoTemporal(get_ecuador_time())
        pedido_dict = pedido_temporal.getPedidoTemporal()
        
        # Si hay una reserva, agregar el ID de la reserva al pedido
        if reserva:
            pedido_dict['reserva_id'] = str(reserva['_id'])
        
        # Insertar en la base de datos
        result = db.pedidos_temporales.insert_one(pedido_dict)
        
        if not result.inserted_id:
            print("Error al insertar el pedido temporal")
            return jsonify({"success": False, "message": "Error al insertar el pedido temporal"}), 500
            
        print("Pedido temporal insertado con ID:", str(result.inserted_id))
        
        # Para pagos en efectivo, simplemente devolver el ID del pedido temporal
        return jsonify({
            "success": True,
            "message": "Pedido procesado con éxito",
            "order_id": str(result.inserted_id)
        }), 200

    except Exception as e:
        print("Error al procesar pedido:", str(e))  # Log para depuración
        import traceback
        traceback.print_exc()  # Imprimir el stack trace completo
        return jsonify({"success": False, "message": str(e)}), 500



    


    
def aceptar_pedido(pedido_id):
    try:
        # Get the request data - don't check if it's JSON first
        data = request.get_json(force=True, silent=True)  # Use force=True and silent=True to avoid errors
        
        print(f"Datos recibidos en aceptar_pedido: {data}")  # Log for debugging
        
        # If data is None or not a dictionary, initialize it as an empty dict
        if data is None or not isinstance(data, dict):
            data = {}
            print("Warning: No se recibieron datos JSON válidos, usando valores predeterminados")
        
        # Get tiempo_estimado with a default value if not present
        tiempo_estimado = data.get("tiempo_estimado", 30)  # Default to 30 minutes if not provided
        
        # Convert to integer safely
        try:
            tiempo_estimado = int(tiempo_estimado)
        except (ValueError, TypeError):
            print(f"Error: Tiempo estimado no es un número válido: {tiempo_estimado}, usando valor predeterminado")
            tiempo_estimado = 30  # Default to 30 minutes if conversion fails
        
        # Ensure tiempo_estimado is positive
        if tiempo_estimado <= 0:
            tiempo_estimado = 30  # Default to 30 minutes if negative or zero
            print(f"Warning: Tiempo estimado inválido, usando valor predeterminado: {tiempo_estimado}")

        # Buscar el pedido temporal
        pedido_temporal = db.pedidos_temporales.find_one({"_id": ObjectId(pedido_id)})

        if not pedido_temporal:
            print(f"Pedido no encontrado con ID: {pedido_id}")
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Usar UTC para comparar fechas
        now_utc = datetime.now(pytz.UTC)
      
        # Convertir expireDateTime a UTC si no tiene zona horaria
        expire_time = pedido_temporal.get('expireDateTime')
        if expire_time:
            # Si la fecha no tiene información de zona horaria, asumir que es UTC
            if expire_time.tzinfo is None:
                expire_time = pytz.UTC.localize(expire_time)
      
        # Solo verificar expiración si la fecha es más de 24 horas en el pasado
        if expire_time and now_utc > expire_time + timedelta(hours=24):
            print(f"Pedido realmente expirado (más de 24 horas): {pedido_id}")
            # Devolver el stock y eliminar el pedido temporal
            with db.client.start_session() as db_session:
                with db_session.start_transaction():
                    for item in pedido_temporal['productos']:
                        db.productos.update_one(
                            {"_id": ObjectId(item['id'])},
                            {"$inc": {"cantidad": item['quantity']}},  # Devolver el stock
                            session=db_session
                        )
                    db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)}, session=db_session)
            return jsonify({"success": False, "message": "El pedido ha expirado (más de 24 horas)"}), 400

        # Verificar si hay una reserva asociada al pedido
        reserva_id = pedido_temporal.get('reserva_id')
        if reserva_id:
            # Si hay una reserva, marcarla como utilizada
            db.reservas_stock.update_one(
                {"_id": ObjectId(reserva_id)},
                {"$set": {"estado": "utilizada", "fecha_utilizacion": now_utc}}
            )
        else:
            # Si no hay reserva, verificar el stock de los productos antes de aceptar el pedido
            with db.client.start_session() as db_session:
                with db_session.start_transaction():
                    insufficient_stock = []
                    for item in pedido_temporal['productos']:
                        producto = db.productos.find_one({"_id": ObjectId(item['id'])}, session=db_session)
                        if not producto or producto['cantidad'] < item['quantity']:
                            insufficient_stock.append(item['name'])

                    if insufficient_stock:
                        db_session.abort_transaction()
                        return jsonify({
                            "success": False,
                            "message": f"No hay suficiente stock para: {', '.join(insufficient_stock)}"
                        }), 400

                    # Si hay suficiente stock, proceder con la actualización del inventario
                    for item in pedido_temporal['productos']:
                        db.productos.update_one(
                            {"_id": ObjectId(item['id'])},
                            {"$inc": {"cantidad": -item['quantity']}},  # Reducir el stock
                            session=db_session
                        )

        # Usar la hora de Ecuador
        ecuador_time = get_ecuador_time()

        # Crear un pedido confirmado a partir del pedido temporal
        pedido_confirmado = {
            "_id": ObjectId(pedido_id),  # Mantener el mismo _id
            "numero_pedido": pedido_temporal['numero_pedido'],
            "usuario_id": pedido_temporal['usuario_id'],
            "productos": pedido_temporal['productos'],
            "nombre": pedido_temporal['nombre'],
            "celular": pedido_temporal['celular'],
            "direccion": pedido_temporal['direccion'],
            "ciudad": pedido_temporal['ciudad'],
            "referencia": pedido_temporal['referencia'],
            "total": pedido_temporal['total'],
            "metodo_pago": pedido_temporal['metodo_pago'],  # Incluir el método de pago
            "estado": "en transcurso",  # Cambiar el estado a "en transcurso"
            "tiempo_estimado": tiempo_estimado,  # Establecer el tiempo estimado
            "fecha_confirmacion": ecuador_time  # Agregar la fecha de confirmación con hora de Ecuador
        }

        # Si había una reserva, incluir su ID en el pedido confirmado
        if reserva_id:
            pedido_confirmado['reserva_id'] = reserva_id

        # Insertar el pedido confirmado en la colección permanente
        result = db.pedidos.insert_one(pedido_confirmado)

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500

        # Eliminar el pedido temporal
        db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)})

        return jsonify({"success": True, "message": "Pedido confirmado con éxito"}), 200

    except Exception as e:
        print(f"Error en aceptar_pedido: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500












def cancelar_pedido_admin(pedido_id):
    try:
        # Verificar si el usuario está autenticado
        if 'nombreUsuario' not in session or 'rol' not in session:
            return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

        # Obtener el nombre de usuario y el rol de la sesión
        nombre_usuario = session['nombreUsuario']
        rol_usuario = session['rol']

        # Usar la hora de Ecuador
        ecuador_time = get_ecuador_time()

        # Buscar el pedido en la colección de pedidos temporales
        pedido_temporal = db.pedidos_temporales.find_one({"_id": ObjectId(pedido_id)})

        if not pedido_temporal:
            # Si no se encuentra en pedidos temporales, buscar en pedidos confirmados o cancelados
            pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id)})
            if not pedido:
                return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

            # Si el pedido ya está en la colección de pedidos, cambiar su estado a "cancelado"
            db.pedidos.update_one(
                {"_id": ObjectId(pedido_id)},
                {
                    "$set": {
                        "estado": "cancelado",
                        "cancelado_por": nombre_usuario,  # Registrar quién canceló
                        "rol_cancelado": rol_usuario,  # Registrar el rol del usuario
                        "fecha_cancelacion": ecuador_time  # Registrar la fecha de cancelación con hora de Ecuador
                    }
                }
            )

            # Restaurar el stock de los productos (siempre, independientemente del estado)
            # Esto asegura que el stock se devuelva incluso si el pedido estaba en otro estado
            with db.client.start_session() as db_session:
                with db_session.start_transaction():
                    for item in pedido['productos']:
                        db.productos.update_one(
                            {"_id": ObjectId(item['id'])},
                            {"$inc": {"cantidad": item['quantity']}},  # Incrementar el stock
                            session=db_session
                        )

            return jsonify({"success": True, "message": f"Pedido cancelado por {nombre_usuario} ({rol_usuario})"}), 200

        # Verificar si hay una reserva asociada al pedido temporal
        reserva_id = pedido_temporal.get('reserva_id')
        if reserva_id:
            # Si hay una reserva, marcarla como cancelada
            db.reservas_stock.update_one(
                {"_id": ObjectId(reserva_id)},
                {"$set": {"estado": "cancelada", "fecha_cancelacion": ecuador_time}}
            )
            
            # Devolver el stock de los productos reservados
            reserva = db.reservas_stock.find_one({"_id": ObjectId(reserva_id)})
            if reserva:
                with db.client.start_session() as db_session:
                    with db_session.start_transaction():
                        for producto in reserva['productos']:
                            db.productos.update_one(
                                {"_id": ObjectId(producto['id'])},
                                {"$inc": {"cantidad": producto['cantidad']}},
                                session=db_session
                            )
        else:
            # Si no hay reserva, devolver el stock de los productos
            with db.client.start_session() as db_session:
                with db_session.start_transaction():
                    for item in pedido_temporal['productos']:
                        db.productos.update_one(
                            {"_id": ObjectId(item['id'])},
                            {"$inc": {"cantidad": item['quantity']}},  # Incrementar el stock
                            session=db_session
                        )

        # Si el pedido está en la colección de pedidos temporales, moverlo a la colección de pedidos con estado "cancelado"
        pedido_cancelado = {
            "_id": ObjectId(pedido_id),  # Mantener el mismo _id
            "numero_pedido": pedido_temporal['numero_pedido'],
            "usuario_id": pedido_temporal['usuario_id'],
            "productos": pedido_temporal['productos'],
            "nombre": pedido_temporal['nombre'],
            "celular": pedido_temporal['celular'],
            "direccion": pedido_temporal['direccion'],
            "ciudad": pedido_temporal['ciudad'],
            "referencia": pedido_temporal['referencia'],
            "total": pedido_temporal['total'],
            "estado": "cancelado",  # Cambiar el estado a "cancelado"
            "cancelado_por": nombre_usuario,  # Registrar quién canceló
            "rol_cancelado": rol_usuario,  # Registrar el rol del usuario
            "fecha_cancelacion": ecuador_time  # Agregar la fecha de cancelación con hora de Ecuador
        }

        # Si había una reserva, incluir su ID en el pedido cancelado
        if reserva_id:
            pedido_cancelado['reserva_id'] = reserva_id

        # Insertar el pedido cancelado en la colección permanente
        result = db.pedidos.insert_one(pedido_cancelado)

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al cancelar el pedido"}), 500

        # Eliminar el pedido temporal
        db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)})

        return jsonify({"success": True, "message": f"Pedido cancelado por {nombre_usuario} ({rol_usuario})"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


    


def cancelar_pedido_cliente(pedido_id):
    try:
        # Obtener la hora actual con zona horaria
        ecuador_time = get_ecuador_time()
        
        # Buscar el pedido en la colección de pedidos
        pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id)})

        if not pedido:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Verificar si el pedido está en estado "en transcurso"
        if pedido.get('estado') != "en transcurso":
            return jsonify({
                "success": False, 
                "message": "Solo se pueden cancelar pedidos en transcurso"
            }), 400

        # Verificar que no hayan pasado más de 10 segundos desde la confirmación
        if 'fecha_confirmacion' in pedido:
            fecha_confirmacion = pedido['fecha_confirmacion']
            if fecha_confirmacion.tzinfo is None:
                fecha_confirmacion = fecha_confirmacion.replace(tzinfo=pytz.UTC)
            
            tiempo_transcurrido = (ecuador_time - fecha_confirmacion).total_seconds()
            if tiempo_transcurrido > 10:
                return jsonify({
                    "success": False,
                    "message": "El tiempo para cancelar ha expirado (máximo 10 segundos)"
                }), 400

        # Determinar quién está cancelando el pedido
        cancelado_por = "cliente"
        rol_cancelado = "cliente"
        nombre_cancelador = pedido.get('nombre')  # Nombre del cliente por defecto

        # Si hay un usuario en sesión (asistente o admin)
        if 'nombreUsuario' in session:
            cancelado_por = session['nombreUsuario']
            rol_cancelado = session.get('rol', 'usuario')  # 'admin', 'asistente', etc.
            nombre_cancelador = cancelado_por  # Usamos el nombre del usuario que canceló

        # Cambiar el estado a "cancelado" y guardar quién lo canceló
        db.pedidos.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {
                "estado": "cancelado", 
                "cancelado_por": cancelado_por,
                "rol_cancelado": rol_cancelado,
                "nombre_cancelador": nombre_cancelador,  # Nuevo campo para mostrar nombre
                "fecha_cancelacion": ecuador_time,
                "notificado": False  # Marcamos como no notificado para la alerta
            }}
        )

        # Restaurar el stock de los productos
        with db.client.start_session() as db_session:
            with db_session.start_transaction():
                for item in pedido['productos']:
                    db.productos.update_one(
                        {"_id": ObjectId(item['id'])},
                        {"$inc": {"cantidad": item['quantity']}},
                        session=db_session
                    )

        return jsonify({
            "success": True, 
            "message": f"Pedido cancelado por {nombre_cancelador} ({rol_cancelado})",
            "pedido_id": str(pedido_id),
            "numero_pedido": pedido.get('numero_pedido'),
            "nombre_cliente": pedido.get('nombre'),
            "total": pedido.get('total'),
            "fecha_cancelacion": ecuador_time.isoformat(),
            "cancelado_por": cancelado_por,
            "rol_cancelado": rol_cancelado,
            "nombre_cancelador": nombre_cancelador
        }), 200

    except Exception as e:
        print(f"Error en cancelar_pedido_cliente: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


    
def confirmar_pedido_cliente(pedido_id):
    try:
        # Buscar el pedido en la colección de pedidos
        pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id)})

        if not pedido:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Cambiar el estado a "confirmado por el cliente"
        db.pedidos.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"estado": "confirmado por el cliente"}}
        )

        return jsonify({"success": True, "message": "Pedido confirmado por el cliente"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

# OBTENER LOS PEDIDOS COMO IMAGEN

def obtener_detalles_pedido(pedido_id):
    try:
        # Buscar el pedido en la colección de pedidos
        pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id)})

        if not pedido:
            # Si no se encuentra en pedidos, buscar en pedidos temporales
            pedido = db.pedidos_temporales.find_one({"_id": ObjectId(pedido_id)})
            if not pedido:
                return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Formatear los datos del pedido para el ticket
        detalles_pedido = {
            "numero_pedido": pedido.get("numero_pedido"),
            "nombre": pedido.get("nombre"),
            "celular": pedido.get("celular"),
            "ciudad": pedido.get("ciudad"),
            "direccion": pedido.get("direccion"),
            "referencia": pedido.get("referencia"),
            "metodo_pago": pedido.get("metodo_pago", "No especificado"),  # Incluir el método de pago
            "total": pedido.get("total"),
            "productos": pedido.get("productos", [])  # Lista de productos
        }

        return jsonify({"success": True, "pedido": detalles_pedido}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    


def finalizar_pedido(pedido_id):
    try:
        # Buscar el pedido en la colección de pedidos en tránsito
        pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id), "estado": "en transcurso"})

        if not pedido:
            return jsonify({"success": False, "message": "Pedido no encontrado o ya finalizado"}), 404

        # Usar la hora de Ecuador
        ecuador_time = get_ecuador_time()

        # Cambiar el estado del pedido a "finalizado"
        db.pedidos.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"estado": "finalizado", "fecha_finalizacion": ecuador_time}}
        )

        return jsonify({"success": True, "message": "Pedido finalizado con éxito"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500




def get_format_for_agrupacion(agrupacion):
    """Devuelve el formato de fecha según la agrupación seleccionada."""
    if agrupacion == "dia":
        return "%Y-%m-%d"  # Agrupar por día
    elif agrupacion == "semana":
        return "%Y-%U"  # Agrupar por semana (año y número de semana)
    elif agrupacion == "mes":
        return "%Y-%m"  # Agrupar por mes
    else:
        return "%Y-%m-%d"  # Por defecto, agrupar por día




def procesar_pago_payphone(request):
    try:
        # Get the payment data from PayPhone webhook
        data = request.json
        print("Datos recibidos en webhook de PayPhone:", json.dumps(data))
        
        # Extract the important fields
        client_transaction_id = data.get('clientTransactionId')
        transaction_id = data.get('id')  # This is the PayPhone transaction ID
        transaction_status = data.get('transactionStatus')
        
        if not client_transaction_id or not transaction_id:
            print("Error: Faltan parámetros en el webhook de PayPhone")
            return jsonify({"success": False, "message": "Faltan parámetros"}), 400
        
        # Find the order using the clientTransactionId (which is your purchaseNumber)
        pedido_temporal = db.pedidos_temporales.find_one({"numero_pedido": client_transaction_id})
        
        # Usar la hora de Ecuador
        ecuador_time = get_ecuador_time()
        
        if pedido_temporal:
            print(f"Pedido temporal encontrado: {pedido_temporal['_id']}")
            
            # Verificar si hay una reserva asociada al pedido
            reserva_id = pedido_temporal.get('reserva_id')
            if reserva_id:
                # Si hay una reserva, marcarla como utilizada
                db.reservas_stock.update_one(
                    {"_id": ObjectId(reserva_id)},
                    {"$set": {"estado": "utilizada", "fecha_utilizacion": ecuador_time}}
                )
            
            # Update the temporary order with payment details
            db.pedidos_temporales.update_one(
                {"_id": pedido_temporal["_id"]},
                {"$set": {
                    "payphone_id": transaction_id,
                    "payphone_status": transaction_status,
                    "estado": "confirmado" if transaction_status == "Approved" else "pago_fallido"
                }}
            )
            
            if transaction_status == "Approved":
                print("Pago aprobado, creando pedido confirmado")
                
                # Create a confirmed order from the temporary order
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
                    "payphone_id": transaction_id,
                    "payphone_status": transaction_status,
                    "estado": "en transcurso",
                    "fecha_confirmacion": ecuador_time,
                    "fecha_pago": ecuador_time,
                    "notificado": False
                }
                
                # Si había una reserva, incluir su ID en el pedido confirmado
                if reserva_id:
                    pedido_confirmado['reserva_id'] = reserva_id
                
                # Insert the confirmed order
                result = db.pedidos.insert_one(pedido_confirmado)
                
                if result.inserted_id:
                    print(f"Pedido confirmado creado con ID: {result.inserted_id}")
                    
                    # Delete the temporary order
                    db.pedidos_temporales.delete_one({"_id": pedido_temporal["_id"]})
                    
                    return jsonify({"success": True, "message": "Pago procesado correctamente"}), 200
                else:
                    print("Error al insertar el pedido confirmado")
                    return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500
            else:
                print(f"Pago rechazado: {transaction_status}")
                
                # Si el pago fue rechazado y hay una reserva, cancelarla y devolver el stock
                if reserva_id:
                    # Marcar la reserva como cancelada
                    db.reservas_stock.update_one(
                        {"_id": ObjectId(reserva_id)},
                        {"$set": {"estado": "cancelada", "fecha_cancelacion": ecuador_time}}
                    )
                    
                    # Devolver el stock de los productos
                    reserva = db.reservas_stock.find_one({"_id": ObjectId(reserva_id)})
                    if reserva:
                        with db.client.start_session() as db_session:
                            with db_session.start_transaction():
                                for producto in reserva['productos']:
                                    db.productos.update_one(
                                        {"_id": ObjectId(producto['id'])},
                                        {"$inc": {"cantidad": producto['cantidad']}},
                                        session=db_session
                                    )
                
                return jsonify({"success": False, "message": "Pago rechazado"}), 200
        else:
            # Check if the order is already in the confirmed orders
            pedido = db.pedidos.find_one({"numero_pedido": client_transaction_id})
            
            if pedido:
                print(f"Pedido ya confirmado encontrado: {pedido['_id']}")
                
                # Update the payment status
                db.pedidos.update_one(
                    {"_id": pedido["_id"]},
                    {"$set": {
                        "payphone_id": transaction_id,
                        "payphone_status": transaction_status,
                        "fecha_pago": ecuador_time if transaction_status == "Approved" else None,
                        "fecha_pago_fallido": ecuador_time if transaction_status != "Approved" else None
                    }}
                )
                
                return jsonify({"success": True, "message": "Información de pago actualizada"}), 200
            else:
                print(f"Pedido no encontrado para clientTransactionId: {client_transaction_id}")
                
                # Si no se encuentra el pedido, crear un registro de pago pendiente
                pago_pendiente = {
                    "numero_pedido": client_transaction_id,
                    "payphone_id": transaction_id,
                    "payphone_status": transaction_status,
                    "fecha_registro": ecuador_time,
                    "procesado": False
                }
                
                db.pagos_pendientes.insert_one(pago_pendiente)
                
                return jsonify({"success": True, "message": "Pago registrado, pendiente de asociar a un pedido"}), 200
            
    except Exception as e:
        print(f"Error procesando pago de PayPhone: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500




def reservar_stock_pedido(request):
    """
    Reserva el stock de los productos en un pedido temporal
    para evitar que otros clientes puedan comprar los mismos productos
    """
    try:
        data = request.json
        productos = data.get('productos', [])
        
        if not productos:
            return jsonify({"success": False, "message": "No hay productos para reservar"}), 400
        
        # Crear un ID único para la reserva
        reserva_id = str(ObjectId())
        
        # Verificar y reservar el stock de cada producto
        with db.client.start_session() as db_session:
            with db_session.start_transaction():
                productos_sin_stock = []
                productos_reservados = []
                
                for producto_carrito in productos:
                    producto_id = producto_carrito.get('id')
                    cantidad_solicitada = producto_carrito.get('quantity', 0)
                    
                    # Buscar el producto en la base de datos
                    producto_db = db.productos.find_one(
                        {"_id": ObjectId(producto_id)}, 
                        session=db_session
                    )
                    
                    if not producto_db:
                        productos_sin_stock.append({
                            "id": producto_id,
                            "name": "Producto no encontrado",
                            "stockActual": 0,
                            "stockSolicitado": cantidad_solicitada
                        })
                        continue
                    
                    # Verificar si hay suficiente stock
                    if producto_db.get('cantidad', 0) < cantidad_solicitada:
                        productos_sin_stock.append({
                            "id": producto_id,
                            "name": producto_db.get('nombreProducto', 'Producto'),
                            "stockActual": producto_db.get('cantidad', 0),
                            "stockSolicitado": cantidad_solicitada
                        })
                        continue
                    
                    # Reservar el stock (reducir la cantidad disponible)
                    db.productos.update_one(
                        {"_id": ObjectId(producto_id)},
                        {"$inc": {"cantidad": -cantidad_solicitada}},
                        session=db_session
                    )
                    
                    # Guardar información del producto reservado
                    productos_reservados.append({
                        "id": producto_id,
                        "cantidad": cantidad_solicitada,
                        "nombre": producto_db.get('nombreProducto', 'Producto')
                    })
                
                # Si hay productos sin suficiente stock, abortar la transacción
                if productos_sin_stock:
                    db_session.abort_transaction()
                    return jsonify({
                        "success": False,
                        "message": "Algunos productos no tienen suficiente stock",
                        "productosNoDisponibles": productos_sin_stock
                    }), 200
                
                # Guardar la reserva en la base de datos
                reserva = {
                    "_id": ObjectId(reserva_id),
                    "productos": productos_reservados,
                    "fecha_creacion": datetime.now(),
                    "fecha_expiracion": datetime.now() + timedelta(minutes=15),
                    "estado": "activa"
                }
                
                db.reservas_stock.insert_one(reserva, session=db_session)
        
        # Si todos los productos tienen suficiente stock, devolver éxito
        return jsonify({
            "success": True, 
            "message": "Stock reservado correctamente",
            "reserva_id": reserva_id
        }), 200
    
    except Exception as e:
        print(f"Error al reservar stock: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error al reservar stock: {str(e)}"}), 500
    

# Añadir esta función para cancelar reservas
def cancelar_reserva_stock(reserva_id):
    """
    Cancela una reserva de stock y devuelve los productos al inventario
    """
    try:
        # Buscar la reserva
        reserva = db.reservas_stock.find_one({"_id": ObjectId(reserva_id), "estado": "activa"})
        
        if not reserva:
            return jsonify({"success": False, "message": "Reserva no encontrada o ya cancelada"}), 404
        
        # Devolver el stock de cada producto
        with db.client.start_session() as db_session:
            with db_session.start_transaction():
                for producto in reserva['productos']:
                    db.productos.update_one(
                        {"_id": ObjectId(producto['id'])},
                        {"$inc": {"cantidad": producto['cantidad']}},
                        session=db_session
                    )
                
                # Marcar la reserva como cancelada
                db.reservas_stock.update_one(
                    {"_id": ObjectId(reserva_id)},
                    {"$set": {"estado": "cancelada", "fecha_cancelacion": datetime.now()}},
                    session=db_session
                )
        
        return jsonify({"success": True, "message": "Reserva cancelada correctamente"}), 200
    
    except Exception as e:
        print(f"Error al cancelar reserva: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "message": f"Error al cancelar reserva: {str(e)}"}), 500
    


def limpiar_reservas_expiradas():
    """
    Limpia las reservas expiradas y devuelve el stock al inventario
    """
    try:
        # Buscar reservas expiradas
        reservas_expiradas = db.reservas_stock.find({
            "estado": "activa",
            "fecha_expiracion": {"$lt": datetime.now()}
        })
        
        count = 0
        for reserva in reservas_expiradas:
            # Devolver el stock de cada producto
            with db.client.start_session() as db_session:
                with db_session.start_transaction():
                    for producto in reserva['productos']:
                        db.productos.update_one(
                            {"_id": ObjectId(producto['id'])},
                            {"$inc": {"cantidad": producto['cantidad']}},
                            session=db_session
                        )
                    
                    # Marcar la reserva como expirada
                    db.reservas_stock.update_one(
                        {"_id": reserva['_id']},
                        {"$set": {"estado": "expirada", "fecha_expiracion_real": datetime.now()}},
                        session=db_session
                    )
                    
                    count += 1
        
        print(f"Se limpiaron {count} reservas expiradas")
        return True
    except Exception as e:
        print(f"Error al limpiar reservas expiradas: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def limpiar_pedidos_expirados():
    try:
        # Usar la hora de Ecuador
        ecuador_time = get_ecuador_time()
        
        # Encontrar todos los pedidos expirados
        pedidos_expirados = db.pedidos_temporales.find({"expireDateTime": {"$lt": ecuador_time}})

        for pedido in pedidos_expirados:
            # Devolver el stock de cada producto
            for item in pedido['productos']:
                db.productos.update_one(
                    {"_id": ObjectId(item['id'])},
                    {"$inc": {"cantidad": item['quantity']}}
                )
            
            # Eliminar el pedido temporal
            db.pedidos_temporales.delete_one({"_id": pedido['_id']})

        return jsonify({"success": True, "message": "Pedidos expirados limpiados con éxito"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
