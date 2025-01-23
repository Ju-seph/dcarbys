from flask import render_template, session, redirect, url_for, abort, jsonify, json, flash
from werkzeug.utils import secure_filename
import time 
from database.mongodb import Mongodb
from bson.objectid import ObjectId
from models.Producto import Producto
import os

# Configuración de la carpeta de subida
UPLOAD_FOLDER = 'public/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Base de datos
db = Mongodb().db()

# Verificar si la extensión es válida
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ver_productos(request):
    if request.method == 'POST':
        try:
            productos = db.productos.find()
            lista_productos = list(productos)

            for producto in lista_productos:
                producto["_id"] = str(producto["_id"])

            datos = {"data": lista_productos}
            return json.dumps(datos, default=str), 200

        except Exception as e:
            print(f"Error al obtener los productos: {e}")
            return jsonify({"message": f"Error al obtener los productos: {e}"}), 500

    return jsonify({"message": "Petición Incorrecta"}), 405


def save_product(request):
    response = {"status": "error", "message": "", "data": None}

    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombreProducto = request.form.get("u_nombreProducto")
            precio = request.form.get("u_precio")
            cantidad = request.form.get("u_cantidad")
            status = request.form.get("u_status")
            categoria = request.form.get("u_categoria")
            descripcion = request.form.get("u_descripcion")
            tiempo_preparacion = request.form.get("u_tiempo_preparacion")
            destacado = request.form.get("u_destacado") == 'true'

            if not (nombreProducto and precio and cantidad):
                response["message"] = "Nombre, precio y cantidad son obligatorios."
                return jsonify(response), 400

            try:
                precio = float(precio)
                cantidad = int(cantidad)
            except ValueError:
                response["message"] = "El precio debe ser un número decimal y la cantidad un entero."
                return jsonify(response), 400

            # Manejar la carga de imagen
            image_file = request.files.get("u_imagen_producto")
            if not image_file or not allowed_file(image_file.filename):
                response["message"] = "Debe cargar una imagen válida (png, jpg, jpeg, gif)."
                return jsonify(response), 400

            filename = secure_filename(image_file.filename)
            save_path = os.path.join(UPLOAD_FOLDER, filename)

            # Evitar sobrescritura
            if os.path.exists(save_path):
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{int(time.time())}{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)

            image_file.save(save_path)  # Guardar la imagen en el servidor
            imagen_path = f"/img/{filename}"  # Ruta relativa

            # Crear y guardar el producto
            producto = Producto(
                nombreProducto=nombreProducto,
                precio=precio,
                cantidad=cantidad,
                status="activo" if not status else status,
                categoria=categoria,
                descripcion=descripcion,
                imagen_path=imagen_path,
                tiempo_preparacion=tiempo_preparacion,
                destacado=destacado,
            )
            producto.createProducto()
            db.productos.insert_one(producto.getProducto())

            response["status"] = "success"
            response["message"] = "Producto creado correctamente."
            return jsonify(response), 201

        except Exception as e:
            print(f"Error al guardar el producto: {e}")
            response["message"] = f"Ocurrió un error al guardar el producto: {e}"
            return jsonify(response), 500

    response["message"] = "Método no permitido."
    return jsonify(response), 405



def edit_product(request):
    # Inicializar el diccionario de respuesta
    response = {"status": "error", "message": "", "data": None}

    # Verificar si el método de la solicitud es POST
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            producto_id = request.form.get("u_id")  # ID del producto a editar
            nombreProducto = request.form.get("u_nombreProducto")
            precio = request.form.get("u_precio")
            cantidad = request.form.get("u_cantidad")
            status = request.form.get("u_status")
            categoria = request.form.get("u_categoria")
            descripcion = request.form.get("u_descripcion")
            tiempo_preparacion = request.form.get("u_tiempo_preparacion")
            destacado = request.form.get("u_destacado") == 'true'

            # Validar campos obligatorios
            if not (producto_id and nombreProducto and precio and cantidad):
                response["message"] = "ID del producto, nombre, precio y cantidad son obligatorios."
                return jsonify(response), 400

            # Validar que el precio sea decimal y la cantidad un entero
            try:
                precio = float(precio)
                cantidad = int(cantidad)
            except ValueError:
                response["message"] = "El precio debe ser un número decimal y la cantidad un número entero."
                return jsonify(response), 400

            # Buscar el producto en la base de datos
            producto_existente = db.productos.find_one({"_id": ObjectId(producto_id)})
            if not producto_existente:
                response["message"] = "El producto no existe."
                return jsonify(response), 404

            # Manejar la carga de una nueva imagen
            imagen_file = request.files.get("u_imagen_producto")
            imagen_path = producto_existente.get("imagen_path")  # Mantener la imagen actual si no se sube una nueva

            if imagen_file and allowed_file(imagen_file.filename):
                # Generar un nombre de archivo seguro
                filename = secure_filename(imagen_file.filename)
                save_path = os.path.join(UPLOAD_FOLDER, filename)

                # Evitar sobrescritura
                if os.path.exists(save_path):
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{int(time.time())}{ext}"
                    save_path = os.path.join(UPLOAD_FOLDER, filename)

                # Guardar la nueva imagen en el servidor
                imagen_file.save(save_path)
                imagen_path = f"/img/{filename}"  # Actualizar la ruta relativa

                # Eliminar la imagen anterior si existe
                if "imagen_path" in producto_existente and os.path.exists(os.path.join(UPLOAD_FOLDER, producto_existente["imagen_path"].split('/')[-1])):
                    os.remove(os.path.join(UPLOAD_FOLDER, producto_existente["imagen_path"].split('/')[-1]))

            # Crear objeto Producto con los datos actualizados
            producto = Producto(
                nombreProducto=nombreProducto,
                precio=precio,
                cantidad=cantidad,
                status="activo" if not status else status,
                categoria=categoria,
                descripcion=descripcion,
                imagen_path=imagen_path,
                tiempo_preparacion=tiempo_preparacion,
                destacado=destacado
            )

            # Actualizar el producto en la base de datos
            db.productos.update_one(
                {"_id": ObjectId(producto_id)},
                {"$set": producto.getProducto()}
            )

            # Producto actualizado exitosamente
            response["status"] = "success"
            response["message"] = "Producto actualizado correctamente."
            return jsonify(response), 200

        except Exception as e:
            # Manejar errores y enviar mensaje de error
            print(f"Error al actualizar el producto: {e}")
            response["message"] = f"Ocurrió un error al actualizar el producto: {e}"
            return jsonify(response), 500

    # Si el método no es POST, devolver error 405
    response["message"] = "Método no permitido."
    return jsonify(response), 405
