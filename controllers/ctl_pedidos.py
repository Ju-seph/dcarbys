from flask import jsonify, session, request, json
from bson.objectid import ObjectId
from database.mongodb import Mongodb
from datetime import datetime, timedelta
from models.PedidoTemporal import PedidoTemporal
from models.Pedido import Pedido
import pymongo
import re


db = Mongodb().db()


def procesar_pedido(request):
    if 'usuario_id' not in session:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

    data = request.json

    # Validar el número de celular
    celular = data.get('celular')
    if not re.match(r'^09\d{8}$', celular):
        return jsonify({"success": False, "message": "Número de celular no válido. Debe tener 10 dígitos y comenzar con 09."}), 400

    try:
        # Crear el pedido temporal
        pedido_temporal = PedidoTemporal(
            numero_pedido=data['purchaseNumber'],
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
        
        # Si es un pago con PayPhone, agregar los detalles del pago
        if data['metodo_pago'] == 'payphone' and 'payphone_id' in data:
            pedido_temporal.payphone_id = data['payphone_id']
            pedido_temporal.payphone_status = 'Approved'
            
            # Para pagos con PayPhone aprobados, podemos confirmar el pedido inmediatamente
            # en lugar de esperar la confirmación del administrador
            pedido_temporal.estado = 'confirmado'
            pedido_temporal.estado_administrador = 'aceptado'
            pedido_temporal.estado_cliente = 'confirmado'
        
        pedido_temporal.createPedidoTemporal()

        # Insertar en la base de datos
        result = db.pedidos_temporales.insert_one(pedido_temporal.getPedidoTemporal())

        if result.inserted_id:
            # Si es un pago con PayPhone aprobado, mover directamente a pedidos confirmados
            if data['metodo_pago'] == 'payphone' and 'payphone_id' in data:
                # Crear un pedido confirmado a partir del pedido temporal
                pedido_confirmado = Pedido.from_pedido_temporal(pedido_temporal.getPedidoTemporal())
                
                # Agregar los detalles del pago
                pedido_confirmado.payphone_id = data['payphone_id']
                pedido_confirmado.payphone_status = 'Approved'
                pedido_confirmado.fecha_pago = datetime.now()
                
                # Insertar el pedido confirmado
                db.pedidos.insert_one(pedido_confirmado.getPedido())
                
                # Eliminar el pedido temporal
                db.pedidos_temporales.delete_one({"_id": result.inserted_id})
                
                return jsonify({
                    "success": True,
                    "message": "Pedido confirmado automáticamente con pago PayPhone",
                    "order_id": str(pedido_confirmado._id)
                }), 200
            else:
                return jsonify({
                    "success": True,
                    "message": "Pedido procesado con éxito",
                    "order_id": str(result.inserted_id)
                }), 200
        else:
            return jsonify({"success": False, "message": "Error al procesar el pedido"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

    
def aceptar_pedido(pedido_id):
    try:
        data = request.get_json()
        tiempo_estimado = data.get("tiempo_estimado")  # Tiempo estimado en minutos

        # Buscar el pedido temporal
        pedido_temporal = db.pedidos_temporales.find_one({"_id": ObjectId(pedido_id)})

        if not pedido_temporal:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Verificar si el pedido ha expirado
        if datetime.now() > pedido_temporal['expireDateTime']:
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
            return jsonify({"success": False, "message": "El pedido ha expirado"}), 400

        # Verificar el stock de los productos antes de aceptar el pedido
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
            "fecha_confirmacion": datetime.now()  # Agregar la fecha de confirmación
        }

        # Insertar el pedido confirmado en la colección permanente
        result = db.pedidos.insert_one(pedido_confirmado)

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500

        # Eliminar el pedido temporal
        db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)})

        return jsonify({"success": True, "message": "Pedido confirmado con éxito"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500




def cancelar_pedido_admin(pedido_id):
    try:
        # Verificar si el usuario está autenticado
        if 'nombreUsuario' not in session or 'rol' not in session:
            return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

        # Obtener el nombre de usuario y el rol de la sesión
        nombre_usuario = session['nombreUsuario']
        rol_usuario = session['rol']

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
                        "fecha_cancelacion": datetime.now()  # Registrar la fecha de cancelación
                    }
                }
            )

            # Restaurar el stock de los productos (solo si el pedido estaba en "en transcurso")
            if pedido['estado'] == "en transcurso":
                with db.client.start_session() as db_session:
                    with db_session.start_transaction():
                        for item in pedido['productos']:
                            db.productos.update_one(
                                {"_id": ObjectId(item['id'])},
                                {"$inc": {"cantidad": item['quantity']}},  # Incrementar el stock
                                session=db_session
                            )

            return jsonify({"success": True, "message": f"Pedido cancelado por {nombre_usuario} ({rol_usuario})"}), 200

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
            "fecha_cancelacion": datetime.now()  # Agregar la fecha de cancelación
        }

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
        # Buscar el pedido en la colección de pedidos
        pedido = db.pedidos.find_one({"_id": ObjectId(pedido_id)})

        if not pedido:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Cambiar el estado a "cancelado" y guardar quién lo canceló
        db.pedidos.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"estado": "cancelado", "cancelado_por": "cliente"}}
        )

        return jsonify({"success": True, "message": "Pedido cancelado por el cliente"}), 200

    except Exception as e:
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

        # Cambiar el estado del pedido a "finalizado"
        db.pedidos.update_one(
            {"_id": ObjectId(pedido_id)},
            {"$set": {"estado": "finalizado", "fecha_finalizacion": datetime.now()}}
        )

        return jsonify({"success": True, "message": "Pedido finalizado con éxito"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



def generar_reporte_ventas():
    try:
        fecha_inicio = request.args.get('fechaInicio')
        fecha_fin = request.args.get('fechaFin')
        agrupacion = request.args.get('agrupacion', 'dia')  # Por defecto, agrupar por día

        # Convertir las fechas a objetos datetime
        fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d') if fecha_inicio else None
        fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d') if fecha_fin else None

        # Consulta para obtener los productos más y menos vendidos
        pipeline = [
            {"$match": {"estado": "finalizado"}},
            {"$unwind": "$productos"},
            {"$group": {
                "_id": "$productos.id",
                "nombre": {"$first": "$productos.name"},
                "cantidad": {"$sum": "$productos.quantity"}
            }},
            {"$sort": {"cantidad": 1}}
        ]

        if fecha_inicio and fecha_fin:
            pipeline[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio, "$lte": fecha_fin}

        productos = list(db.pedidos.aggregate(pipeline))

        if not productos:
            return jsonify({"success": False, "message": "No hay datos de ventas en el rango de fechas seleccionado"}), 404

        producto_mas_vendido = productos[-1]
        producto_menos_vendido = productos[0]

        # Consulta para agrupar las ventas por día, semana o mes
        pipeline_agrupacion = [
            {"$match": {"estado": "finalizado"}},
            {"$unwind": "$productos"},
            {"$group": {
                "_id": {
                    "$dateToString": {
                        "format": get_format_for_agrupacion(agrupacion),
                        "date": "$fecha_confirmacion"
                    }
                },
                "total_ventas": {"$sum": "$productos.quantity"}
            }},
            {"$sort": {"_id": 1}}
        ]

        if fecha_inicio and fecha_fin:
            pipeline_agrupacion[0]["$match"]["fecha_confirmacion"] = {"$gte": fecha_inicio, "$lte": fecha_fin}

        ventas_agrupadas = list(db.pedidos.aggregate(pipeline_agrupacion))

        # Preparar datos para el gráfico
        labels = [venta["_id"] for venta in ventas_agrupadas]
        data = [venta["total_ventas"] for venta in ventas_agrupadas]

        return jsonify({
            "success": True,
            "productoMasVendido": producto_mas_vendido,
            "productoMenosVendido": producto_menos_vendido,
            "graficoVentas": {
                "labels": labels,
                "data": data
            }
        }), 200

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
        
        # Extract the important fields
        client_transaction_id = data.get('clientTransactionId')
        transaction_id = data.get('id')  # This is the PayPhone transaction ID
        transaction_status = data.get('transactionStatus')
        
        # Log the payment notification
        print(f"Received PayPhone payment notification: {json.dumps(data)}")
        
        # Find the order using the clientTransactionId (which is your purchaseNumber)
        pedido_temporal = db.pedidos_temporales.find_one({"numero_pedido": client_transaction_id})
        
        if pedido_temporal:
            # If found in temporary orders, update it
            pedido_id = pedido_temporal["_id"]
            
            if transaction_status == "Approved":
                # Create a confirmed order from the temporary order
                pedido_confirmado = {
                    "_id": pedido_id,
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
                    "fecha_confirmacion": datetime.now(),
                    "fecha_pago": datetime.now()
                }
                
                # Insert the confirmed order
                result = db.pedidos.insert_one(pedido_confirmado)
                
                if not result.inserted_id:
                    return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500
                
                # Delete the temporary order
                db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)})
                
                return jsonify({"success": True, "message": "Pago procesado correctamente"}), 200
            else:
                # If payment failed, update the temporary order
                db.pedidos_temporales.update_one(
                    {"_id": ObjectId(pedido_id)},
                    {"$set": {
                        "estado": "pago_fallido",
                        "payphone_id": transaction_id,
                        "payphone_status": transaction_status,
                        "fecha_pago_fallido": datetime.now()
                    }}
                )
                
                return jsonify({"success": False, "message": "Pago rechazado"}), 200
        else:
            # Check if the order is already in the confirmed orders
            pedido = db.pedidos.find_one({"numero_pedido": client_transaction_id})
            
            if pedido:
                # Update the payment status
                db.pedidos.update_one(
                    {"_id": pedido["_id"]},
                    {"$set": {
                        "payphone_id": transaction_id,
                        "payphone_status": transaction_status,
                        "fecha_pago": datetime.now() if transaction_status == "Approved" else None,
                        "fecha_pago_fallido": datetime.now() if transaction_status != "Approved" else None
                    }}
                )
                
                return jsonify({"success": True, "message": "Información de pago actualizada"}), 200
            else:
                return jsonify({"success": False, "message": "Pedido no encontrado"}), 404
            
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500



def procesar_pago_payphone():
    try:
        # Get the payment data from PayPhone webhook
        data = request.json
        
        # Extract the important fields
        client_transaction_id = data.get('clientTransactionId')
        transaction_id = data.get('id')  # This is the PayPhone transaction ID
        transaction_status = data.get('transactionStatus')
        
        print(f"Received PayPhone payment notification: {json.dumps(data)}")
        
        # Find the order using the clientTransactionId (which is your purchaseNumber)
        pedido = db.pedidos_temporales.find_one({"numero_pedido": client_transaction_id})
        
        if not pedido:
            # If not found in temporary orders, check confirmed orders
            pedido = db.pedidos.find_one({"numero_pedido": client_transaction_id})
            
        if not pedido:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404
        
        # Update the order with payment information
        if transaction_status == "Approved":
            # If the payment was approved, move the order to confirmed status
            pedido_id = pedido["_id"]
            
            # Update the order with payment details
            db.pedidos.update_one(
                {"_id": ObjectId(pedido_id)},
                {"$set": {
                    "estado": "en transcurso",
                    "payphone_id": transaction_id,
                    "payphone_status": transaction_status,
                    "fecha_pago": datetime.now()
                }}
            )
            
            # You could also send a notification to the admin dashboard here
            # This could be done via WebSockets or by setting a flag in the database
            
            return jsonify({"success": True, "message": "Pago procesado correctamente"}), 200
        else:
            # If the payment failed, update the order status
            pedido_id = pedido["_id"]
            db.pedidos.update_one(
                {"_id": ObjectId(pedido_id)},
                {"$set": {
                    "estado": "pago_fallido",
                    "payphone_id": transaction_id,
                    "payphone_status": transaction_status,
                    "fecha_pago_fallido": datetime.now()
                }}
            )
            
            return jsonify({"success": False, "message": "Pago rechazado"}), 200
            
    except Exception as e:
        print(f"Error processing PayPhone payment: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    

def limpiar_pedidos_expirados():
    try:
        # Encontrar todos los pedidos expirados
        pedidos_expirados = db.pedidos_temporales.find({"expireDateTime": {"$lt": datetime.now()}})

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