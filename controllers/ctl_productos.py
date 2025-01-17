from flask import render_template, session, redirect, url_for, abort,jsonify,json, flash
from database.mongodb import Mongodb
import controllers.ctl_encrypt as ctl_encrypt
from controllers.ctl_encrypt import encrypt, decrypt
from bson.objectid import ObjectId
from models.Producto import Producto

import re

db = Mongodb().db()

def save_product(request):
    # Inicializar el diccionario de respuesta
    response = {"status": "error", "message": "", "data": None}

    # Verificar si el método de la solicitud es POST
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get("u_nombreProducto")
            precio = request.form.get("u_precio")
            cantidad = request.form.get("u_cantidad")
            status = request.form.get("u_status")
            categoria = request.form.get("u_categoria")
            descripcion = request.form.get("u_descripcion")
            imagen_url = request.form.get("u_imagen_url")
            tiempo_preparacion = request.form.get("u_tiempo_preparacion")
            destacado = request.form.get("u_destacado") == 'true'

            # Validar campos obligatorios
            if not nombre or not precio or not cantidad or not status:
                response["message"] = "Todos los campos obligatorios deben ser completados."
                return jsonify(response), 400

            # Validar que el precio y cantidad sean números
            try:
                precio = float(precio)
                cantidad = int(cantidad)
            except ValueError:
                response["message"] = "El precio debe ser un número decimal y la cantidad un número entero."
                return jsonify(response), 400

            # Crear objeto Producto
            producto = Producto(
                nombre=nombre,
                precio=precio,
                cantidad=cantidad,
                status="activo",
                categoria=categoria,
                descripcion=descripcion,
                imagen_url=imagen_url,
                tiempo_preparacion=tiempo_preparacion,
                destacado=destacado
            )
            producto_data = producto.getProducto()

            # Guardar el producto en la base de datos
            db.productos.insert_one(producto_data)

            # Producto creado exitosamente
            response["status"] = "success"
            response["message"] = "Producto creado correctamente."
            response["data"] = producto_data  # Retornar los datos del producto creado
            return jsonify(response), 201

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al guardar el producto: {e}")
            response["message"] = f"Ocurrió un error al guardar el producto: {e}"
            return jsonify(response), 500

    # Si el método no es POST, devolver error 405
    response["message"] = "Método no permitido."
    return jsonify(response), 405


