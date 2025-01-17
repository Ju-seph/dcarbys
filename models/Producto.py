from datetime import datetime

class Producto:

    def __init__(self, nombreProducto, precio, cantidad, status, categoria=None, descripcion=None, 
                 imagen_url=None, tiempo_preparacion=None, destacado=False):
        self.nombreProducto = nombreProducto
        self.precio = precio
        self.cantidad = cantidad
        self.status = status
        self.categoria = categoria
        self.descripcion = descripcion
        self.imagen_url = imagen_url
        self.tiempo_preparacion = tiempo_preparacion
        self.destacado = destacado

    def getProducto(self):
        return self.__dict__

    def createProducto(self):
        self.createDateTime = datetime.now()

    def updateProducto(self):
        self.updateDateTime = datetime.now()
