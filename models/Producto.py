from datetime import datetime

class Producto:

    def __init__(self, nombre, precio):
        self.nombre= nombre
        self.precio= precio
        


    def getProducto(self):
        return self.__dict__
    

    def createProducto(self):
        self.createDateTime = datetime.now()

    def updateProducto(self):
        self.updateDateTime = datetime.now()