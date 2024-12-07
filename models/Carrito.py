from datetime import datetime

class Carrito:

    def __init__(self, clienteId, producto,total):
        self.clienteId= clienteId
        self.producto= producto
        self.total= total


    def getCarrito(self):
        return self.__dict__
    

    def createCarrito(self):
        self.createDateTime = datetime.now()

    def updateCarrito(self):
        self.updateDateTime = datetime.now()