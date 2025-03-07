from flask import jsonify, session, request
from bson.objectid import ObjectId
from database.mongodb import Mongodb
from datetime import datetime, timedelta
from models.PedidoTemporal import PedidoTemporal
from models.Pedido import Pedido
import pymongo

db = Mongodb().db()

def procesar_pedido(request):
    if 'usuario_id' not in session:
        return jsonify({"success": False, "message": "Usuario no autenticado"}), 401

    data = request.json

    try:
        # Crear el pedido temporal
        pedido_temporal = PedidoTemporal(
            numero_pedido=data['purchaseNumber'],
            usuario_id=session['usuario_id'],
            productos=data['cart'],
            nombre=data['nombre'],
            celular=data['celular'],
            ciudad=data['ciudad'],
            direccion=data['direccion'],
            referencia=data['referencia'],
            total=data['total']
        )
        pedido_temporal.createPedidoTemporal()

        # Insertar en la base de datos
        result = db.pedidos_temporales.insert_one(pedido_temporal.getPedidoTemporal())

        if result.inserted_id:
            return jsonify({
                "success": True,
                "message": "Pedido procesado con éxito",
                "order_id": str(result.inserted_id)  # Devuelve el _id del pedido temporal
            }), 200
        else:
            return jsonify({"success": False, "message": "Error al procesar el pedido"}), 500

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def confirmar_pedido(order_id):
    try:
        data = request.get_json()
        tiempo_estimado = data.get("tiempo_estimado")  # Tiempo estimado en minutos

        # Buscar el pedido temporal
        pedido_temporal_doc = db.pedidos_temporales.find_one({"_id": ObjectId(order_id)})

        if not pedido_temporal_doc:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Verificar si el pedido ha expirado
        if datetime.now() > pedido_temporal_doc['expireDateTime']:
            # Devolver el stock y eliminar el pedido temporal
            with db.client.start_session() as db_session:
                with db_session.start_transaction():
                    for item in pedido_temporal_doc['productos']:
                        db.productos.update_one(
                            {"_id": ObjectId(item['id'])},
                            {"$inc": {"cantidad": item['quantity']}},
                            session=db_session
                        )
                    db.pedidos_temporales.delete_one({"_id": ObjectId(order_id)}, session=db_session)
            return jsonify({"success": False, "message": "El pedido ha expirado"}), 400

        # Crear un pedido confirmado a partir del pedido temporal
        pedido_temporal = PedidoTemporal.from_dict(pedido_temporal_doc)
        pedido_confirmado = Pedido.from_pedido_temporal(pedido_temporal.getPedidoTemporal())
        pedido_confirmado.estado = "en transcurso"  # Cambiar el estado a "en transcurso"
        pedido_confirmado.tiempo_estimado = tiempo_estimado  # Establecer el tiempo estimado

        # Insertar el pedido confirmado en la colección permanente
        result = db.pedidos.insert_one(pedido_confirmado.getPedido())

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500

        # Eliminar el pedido temporal
        db.pedidos_temporales.delete_one({"_id": ObjectId(order_id)})

        return jsonify({"success": True, "message": "Pedido confirmado con éxito"}), 200

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



def cancelar_pedido(pedido_id):
    try:
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
                {"$set": {"estado": "cancelado", "cancelado_por": "cliente"}}
            )

            return jsonify({"success": True, "message": "Pedido cancelado con éxito"}), 200

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
            "cancelado_por": "cliente",  # Especificar que fue cancelado por el cliente
            "fecha_cancelacion": datetime.now()  # Agregar la fecha de cancelación
        }

        # Insertar el pedido cancelado en la colección permanente
        result = db.pedidos.insert_one(pedido_cancelado)

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al cancelar el pedido"}), 500

        # Devolver el stock de los productos
        with db.client.start_session() as db_session:
            with db_session.start_transaction():
                for item in pedido_temporal['productos']:
                    db.productos.update_one(
                        {"_id": ObjectId(item['id'])},
                        {"$inc": {"cantidad": item['quantity']}},  # Incrementar el stock
                        session=db_session
                    )
                # Eliminar el pedido temporal
                db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)}, session=db_session)

        return jsonify({"success": True, "message": "Pedido cancelado con éxito"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    


def cancelar_pedido_admin(pedido_id):
    try:
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
                {"$set": {"estado": "cancelado", "cancelado_por": "admin"}}
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

            return jsonify({"success": True, "message": "Pedido cancelado por el administrador"}), 200

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
            "cancelado_por": "admin",  # Especificar que fue cancelado por el administrador
            "fecha_cancelacion": datetime.now()  # Agregar la fecha de cancelación
        }

        # Insertar el pedido cancelado en la colección permanente
        result = db.pedidos.insert_one(pedido_cancelado)

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al cancelar el pedido"}), 500

        # Eliminar el pedido temporal
        db.pedidos_temporales.delete_one({"_id": ObjectId(pedido_id)})

        return jsonify({"success": True, "message": "Pedido cancelado por el administrador"}), 200

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
            "metodo_pago": pedido.get("metodo_pago", "No especificado"),  # Campo opcional
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