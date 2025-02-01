from datetime import datetime

class Carrito:

    def __init__(self,VentaId,userId, productoId,direccionDestino,total):
        self.VentaId=VentaId
        self.userId= userId
        self.productoId= productoId
        self.total= total


    def getCarrito(self):
        return self.__dict__
    

    def createCarrito(self):
        self.createDateTime = datetime.now()

    def updateCarrito(self):
        self.updateDateTime = datetime.now()