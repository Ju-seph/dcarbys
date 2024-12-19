from datetime import datetime

class Producto:

    def __init__(self,idProducto,nombre, precio,subTotal,iva,descuento,status):
        self.idProducto=idProducto
        self.nombre= nombre
        self.precio= precio
        self.subTotal= subTotal
        self.iva= iva
        self.descuento= descuento
        self.status= status


    def getProducto(self):
        return self.__dict__
    

    def createProducto(self):
        self.createDateTime = datetime.now()

    def updateProducto(self):
        self.updateDateTime = datetime.now()