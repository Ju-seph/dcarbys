from datetime import datetime

class User:

    def __init__(self,nombreUsuario ,correo,clave , rol,status):
        self.nombreUsuario= nombreUsuario
        self.correo= correo
        self.clave= clave
        self.rol= rol
        self.status= status

    def getUser(self):
        return self.__dict__
    

    def createUser(self):
        self.createDateTime = datetime.now()

    def updateUser(self):
        self.updateDateTime = datetime.now()
    
