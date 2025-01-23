from datetime import datetime

class Producto:

    def __init__(self, nombreProducto, precio, cantidad, status, categoria=None, descripcion=None, 
                 imagen_path=None, tiempo_preparacion=None, destacado=False):
        self.nombreProducto = nombreProducto
        self.precio = round(float(precio), 2)  # Asegurar precio en formato decimal y con 2 decimales
        self.cantidad = int(cantidad)  # Asegurar que la cantidad sea un entero
        self.status = status
        self.categoria = categoria
        self.descripcion = descripcion
        self.imagen_path = imagen_path  # Cambiado el nombre del atributo
        self.tiempo_preparacion = tiempo_preparacion
        self.destacado = destacado
        self.createDateTime = None  # Se inicializa vacío
        self.updateDateTime = None  # Se inicializa vacío

    def getProducto(self):
        """
        Retorna un diccionario del producto para ser guardado en la base de datos.
        """
        return self.__dict__

    def createProducto(self):
        """
        Establece la fecha de creación del producto.
        """
        self.createDateTime = datetime.now()

    def updateProducto(self):
        """
        Establece la fecha de última actualización del producto.
        """
        self.updateDateTime = datetime.now()

    def setImagePath(self, image_filename):
        """
        Establece la ruta del archivo de imagen del producto.
        """
        self.imagen_path = f"/img/{image_filename}"  # Actualiza el atributo con la ruta relativa
