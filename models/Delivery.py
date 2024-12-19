from datetime import datetime

class Carrito:

    def __init__(self, idProducto, clienteId,direccionDestino,total):
        self.clienteId= clienteId
        self.idProducto= idProducto
        self.direccionDestino= direccionDestino
        self.total= total


    def getCarrito(self):
        return self.__dict__
    

    def createCarrito(self):
        self.createDateTime = datetime.now()

    def updateCarrito(self):
        self.updateDateTime = datetime.now()