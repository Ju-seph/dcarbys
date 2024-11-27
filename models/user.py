from datetime import datetime

class User:

    def __init__(self, ced, name,lastName, username,password , rol, direction,status):
        self.ced= ced
        self.name= name
        self.lastName= lastName
        self.username= username
        self.password= password
        self.rol= rol
        self.direction= direction
        self.status= status

    def getUser(self):
        return self.__dict__
    

    def createUser(self):
        self.createDateTime = datetime.now()

    def updateUser(self):
        self.updateDateTime = datetime.now()
    
