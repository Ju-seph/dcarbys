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
        # Iniciar una sesión de transacción
        with db.client.start_session() as db_session:
            with db_session.start_transaction():
                insufficient_stock = []
                
                # Verificar y reservar productos
                for item in data['cart']:
                    producto = db.productos.find_one({"_id": ObjectId(item['id'])}, session=db_session)
                    if not producto or producto['cantidad'] < item['quantity']:
                        insufficient_stock.append(item['name'])
                
                if insufficient_stock:
                    db_session.abort_transaction()
                    return jsonify({
                        "success": False, 
                        "message": f"No hay suficiente stock para: {', '.join(insufficient_stock)}"
                    }), 400

                # Si hay suficiente stock, proceder con la actualización
                for item in data['cart']:
                    db.productos.update_one(
                        {"_id": ObjectId(item['id'])},
                        {"$inc": {"cantidad": -item['quantity']}},
                        session=db_session
                    )

                # Crear el pedido temporal
                pedido_temporal = PedidoTemporal(
                    numero_pedido=data['purchaseNumber'],
                    usuario_id=session['usuario_id'],
                    productos=data['cart'],
                    nombre=data['nombre'],
                    telefono=data['telefono'],
                    direccion=data['direccion'],
                    ciudad=data['ciudad'],
                    codigo_postal=data['codigo_postal'],
                    total=data['total']
                )
                pedido_temporal.createPedidoTemporal()
                
                # Insertar en la base de datos
                result = db.pedidos_temporales.insert_one(pedido_temporal.getPedidoTemporal(), session=db_session)

        if result.inserted_id:
            return jsonify({"success": True, "message": "Pedido procesado con éxito", "order_id": str(result.inserted_id)}), 200
        else:
            return jsonify({"success": False, "message": "Error al procesar el pedido"}), 500

    except pymongo.errors.PyMongoError as e:
        return jsonify({"success": False, "message": f"Error de base de datos: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def confirmar_pedido(order_id):
    try:
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

        # Insertar el pedido confirmado en la colección permanente
        result = db.pedidos.insert_one(pedido_confirmado.getPedido())

        if not result.inserted_id:
            return jsonify({"success": False, "message": "Error al confirmar el pedido"}), 500

        # Eliminar el pedido temporal
        db.pedidos_temporales.delete_one({"_id": ObjectId(order_id)})

        return jsonify({"success": True, "message": "Pedido confirmado con éxito"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def cancelar_pedido(order_id):
    try:
        # Buscar el pedido temporal
        pedido_temporal = db.pedidos_temporales.find_one({"_id": ObjectId(order_id)})

        if not pedido_temporal:
            return jsonify({"success": False, "message": "Pedido no encontrado"}), 404

        # Iniciar una sesión de transacción
        with db.client.start_session() as session:
            with session.start_transaction():
                # Devolver el stock de los productos
                for item in pedido_temporal['productos']:
                    db.productos.update_one(
                        {"_id": ObjectId(item['id'])},
                        {"$inc": {"cantidad": item['quantity']}},
                        session=session
                    )

                # Eliminar el pedido temporal
                db.pedidos_temporales.delete_one({"_id": ObjectId(order_id)}, session=session)

        return jsonify({"success": True, "message": "Pedido cancelado con éxito"}), 200

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

