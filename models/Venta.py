from datetime import datetime

class Venta:

    def __init__(self,numeroVenta,userId, ProductoId,subTotal,total):
        self.numeroVenta=numeroVenta
        self.userId= userId
        self.ProductoId= ProductoId
        self.subTotal=subTotal
        self.total= total


    def getVenta(self):
        return self.__dict__
    

    def createVenta(self):
        self.createDateTime = datetime.now()

    def updateVenta(self):
        self.updateDateTime = datetime.now()