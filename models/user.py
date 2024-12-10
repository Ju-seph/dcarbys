from datetime import datetime

class User:

    def __init__(self, ced, name ,password , rol,status):
        self.ced= ced
        self.name= name
        self.password= password
        self.rol= rol
        self.status= status

    def getUser(self):
        return self.__dict__
    

    def createUser(self):
        self.createDateTime = datetime.now()

    def updateUser(self):
        self.updateDateTime = datetime.now()
    
