from flask import render_template, session, redirect, url_for, abort, jsonify, json, flash
from werkzeug.utils import secure_filename
import time 
from database.mongodb import Mongodb
from bson.objectid import ObjectId
from models.Producto import Producto
from bson.errors import InvalidId
import os


# Assuming you have these imports at the top of your file
from database.mongodb import Mongodb
from models.Producto import Producto

# Database connection
db = Mongodb().db()

# Configuration for file uploads
UPLOAD_FOLDER = 'public/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def ver_productos(request):
    if request.method == 'POST':
        try:
            productos = db.productos.find()
            lista_productos = list(productos)

            for producto in lista_productos:
                producto["_id"] = str(producto["_id"])  # Convierte ObjectId en cadena
                producto["id"] = producto["_id"]        # Agrega un alias "id"

            datos = {"data": lista_productos}  # Estructura esperada por DataTables
            return jsonify(datos), 200  # Usa jsonify directamente para JSON válido

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

            # Validación de cantidad negativa
            if cantidad < 0:
                response["message"] = "La cantidad del producto no puede ser negativa."
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
    response = {"status": "error", "message": "", "data": None}

    if request.method == 'POST':
        try:
            # Get product ID
            producto_id = request.form.get("u_id")
            if not producto_id:
                response["message"] = "ID del producto es requerido."
                return jsonify(response), 400

            # Find the product in the database
            producto = db.productos.find_one({"_id": ObjectId(producto_id)})
            if not producto:
                response["message"] = "Producto no encontrado."
                return jsonify(response), 404

            # Get form data
            nombreProducto = request.form.get("u_nombreProducto")
            precio = request.form.get("u_precio")
            cantidad = request.form.get("u_cantidad")
            categoria = request.form.get("u_categoria")
            descripcion = request.form.get("u_descripcion")
            tiempo_preparacion = request.form.get("u_tiempo_preparacion")
            destacado = request.form.get("u_destacado") == 'true'

            if not all([nombreProducto, precio, cantidad, categoria, tiempo_preparacion]):
                response["message"] = "Todos los campos son obligatorios."
                return jsonify(response), 400

            try:
                precio = float(precio)
                cantidad = int(cantidad)
                tiempo_preparacion = int(tiempo_preparacion)
            except ValueError:
                response["message"] = "Formato inválido para precio, cantidad o tiempo de preparación."
                return jsonify(response), 400

            # Validación de cantidad negativa
            if cantidad < 0:
                response["message"] = "La cantidad del producto no puede ser negativa."
                return jsonify(response), 400

            # Handle image upload
            image_file = request.files.get("u_imagen_producto")
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{int(time.time())}{ext}"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(save_path)
                imagen_path = f"/img/{filename}"
            else:
                imagen_path = producto.get('imagen_path')  # Keep existing image if no new one is uploaded

            # Update product
            updated_product = Producto(
                nombreProducto=nombreProducto,
                precio=precio,
                cantidad=cantidad,
                status=producto.get('status', 'activo'),
                categoria=categoria,
                descripcion=descripcion,
                imagen_path=imagen_path,
                tiempo_preparacion=tiempo_preparacion,
                destacado=destacado
            )
            updated_product.updateProducto()  # Set update timestamp

            # Update in database
            result = db.productos.update_one(
                {"_id": ObjectId(producto_id)},
                {"$set": updated_product.getProducto()}
            )

            if result.modified_count > 0:
                response["status"] = "success"
                response["message"] = "Producto actualizado correctamente."
                return jsonify(response), 200
            else:
                response["message"] = "No se realizaron cambios en el producto."
                return jsonify(response), 200

        except Exception as e:
            print(f"Error al editar el producto: {e}")
            response["message"] = f"Ocurrió un error al editar el producto: {str(e)}"
            return jsonify(response), 500

    response["message"] = "Método no permitido."
    return jsonify(response), 405

def del_product(request):
    response = {"status": "error", "message": "", "data": None}

    if request.method == 'POST':
        try:
            # Get product ID
            producto_id = request.form.get("u_id")
            if not producto_id:
                response["message"] = "ID del producto es requerido."
                return jsonify(response), 400

            # Find the product in the database
            producto = db.productos.find_one({"_id": ObjectId(producto_id)})
            if not producto:
                response["message"] = "Producto no encontrado."
                return jsonify(response), 404

            # Delete the product's image if it exists
            if producto.get('imagen_path'):
                image_path = os.path.join('public', producto['imagen_path'].lstrip('/'))
                if os.path.exists(image_path):
                    os.remove(image_path)

            # Delete the product from the database
            result = db.productos.delete_one({"_id": ObjectId(producto_id)})

            if result.deleted_count > 0:
                response["status"] = "success"
                response["message"] = f"Producto '{producto['nombreProducto']}' eliminado correctamente."
                return jsonify(response), 200
            else:
                response["message"] = "No se pudo eliminar el producto."
                return jsonify(response), 500

        except Exception as e:
            print(f"Error al eliminar el producto: {e}")
            response["message"] = f"Ocurrió un error al eliminar el producto: {str(e)}"
            return jsonify(response), 500

    response["message"] = "Método no permitido."
    return jsonify(response), 405

