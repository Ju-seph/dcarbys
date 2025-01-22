from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
import controllers.ctl_encrypt as ctl_encrypt
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId
from models.Producto import Producto

import re

db = Mongodb().db()

def ver_productos(request):
    if request.method == 'POST':
        try:
            # Obtener todos los productos desde la base de datos
            productos = db.productos.find()
            lista_productos = list(productos)

            # Formatear los datos para ser compatibles con DataTables
            for producto in lista_productos:
                producto["_id"] = str(producto["_id"])  # Convertir ObjectId a string

            datos = {"data": lista_productos}
            return json.dumps(datos, default=str), 200

        except Exception as e:
            # Manejar errores y devolver un mensaje
            print(f"Error al obtener los productos: {e}")
            return jsonify({"message": f"Error al obtener los productos: {e}"}), 500
    else:
        return jsonify({"message": "Petición Incorrecta"}), 405





def save_product(request):
    # Inicializar el diccionario de respuesta
    response = {"status": "error", "message": "", "data": None}

    # Verificar si el método de la solicitud es POST
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombreProducto = request.form.get("u_nombreProducto")
            precio = request.form.get("u_precio")
            cantidad = request.form.get("u_cantidad")
            status = request.form.get("u_status")
            categoria = request.form.get("u_categoria")
            descripcion = request.form.get("u_descripcion")
            imagen_url = request.form.get("u_imagen_url")
            tiempo_preparacion = request.form.get("u_tiempo_preparacion")
            destacado = request.form.get("u_destacado") == 'true'

            # Validar que los campos requeridos no estén vacíos
            if not (nombreProducto and precio and cantidad):
                response["message"] = "Nombre del producto, precio y cantidad son obligatorios."
                return jsonify(response), 400

            # Validar que el precio sea decimal y la cantidad un entero
            try:
                precio = float(precio)
                cantidad = int(cantidad)
            except ValueError:
                response["message"] = "El precio debe ser un número decimal y la cantidad un número entero."
                return jsonify(response), 400

            # Verificar si el producto ya existe en la base de datos
            existe = db.productos.find_one({"nombreProducto": nombreProducto})
            if existe:
                response["message"] = f"El producto '{nombreProducto}' ya existe."
                return jsonify(response), 409

            # Crear objeto Producto
            producto = Producto(
                nombreProducto=nombreProducto,
                precio=precio,
                cantidad=cantidad,
                status="activo" if not status else status,
                categoria=categoria,
                descripcion=descripcion,
                imagen_url=imagen_url,
                tiempo_preparacion=tiempo_preparacion,
                destacado=destacado
            )
            producto.createProducto()

            # Guardar el producto en la base de datos
            db.productos.insert_one(producto.getProducto())

            # Producto creado exitosamente
            response["status"] = "success"
            response["message"] = "Producto creado correctamente."
            return jsonify(response), 201

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al guardar el producto: {e}")
            response["message"] = f"Ocurrió un error al guardar el producto: {e}"
            return jsonify(response), 500

    # Si el método no es POST, devolver error 405
    response["message"] = "Método no permitido."
    return jsonify(response), 405


def edit_product(request):
    # Inicializar el diccionario de respuesta
    response = {"status": "error", "message": "", "data": None}

    # Verificar si el método de la solicitud es POST
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombreProducto = request.form.get("u_nombreProducto")
            precio = request.form.get("u_precio")
            cantidad = request.form.get("u_cantidad")
            status = request.form.get("u_status")
            categoria = request.form.get("u_categoria")
            descripcion = request.form.get("u_descripcion")
            imagen_url = request.form.get("u_imagen_url")
            tiempo_preparacion = request.form.get("u_tiempo_preparacion")
            destacado = request.form.get("u_destacado") == 'true'

            # Validar que los campos requeridos no estén vacíos
            if not (nombreProducto and precio and cantidad):
                response["message"] = "Nombre del producto, precio y cantidad son obligatorios."
                return jsonify(response), 400

            # Validar que el precio sea decimal y la cantidad un entero
            try:
                precio = float(precio)
                cantidad = int(cantidad)
            except ValueError:
                response["message"] = "El precio debe ser un número decimal y la cantidad un número entero."
                return jsonify(response), 400

            # Verificar si el producto ya existe en la base de datos
            existe = db.productos.find_one({"nombreProducto": nombreProducto})
            if existe:
                 producto = Producto(
                nombreProducto=nombreProducto,
                precio=precio,
                cantidad=cantidad,
                status="activo" if not status else status,
                categoria=categoria,
                descripcion=descripcion,
                imagen_url=imagen_url,
                tiempo_preparacion=tiempo_preparacion,
                destacado=destacado
            )
                 # Actualizar el producto en la base de datos
            producto.updateProducto()
            db.productos.update_one({"_id":ObjectId(existe["_id"])},
                                    {"$set":producto.getProducto()})

            # Producto actualizado exitosamente
            response["status"] = "success"
            response["message"] = "Producto actualizado correctamente."
            return jsonify(response), 201

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al actualizar el producto: {e}")
            response["message"] = f"Ocurrió un error al actualizar el producto: {e}"
            return jsonify(response), 500

    # Si el método no es POST, devolver error 405
    response["message"] = "Método no permitido."
    return jsonify(response), 405

           