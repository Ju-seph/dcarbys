from datetime import datetime

class User:

    def __init__(self, idUser,nombreUsuario ,correo,password , rol,status):
        self.idUser= idUser
        self.nombreUsuario= nombreUsuario
        self.correo= correo
        self.password= password
        self.rol= rol
        self.status= status

    def getUser(self):
        return self.__dict__
    

    def createUser(self):
        self.createDateTime = datetime.now()

    def updateUser(self):
        self.updateDateTime = datetime.now()
    
