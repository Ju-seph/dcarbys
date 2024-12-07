from datetime import datetime

class Cliente:

    def __init__(self, userId,lastName, username,direction):
        self.userId= userId
        self.lastName= lastName
        self.username= username
        self.direction= direction


    def getCliente(self):
        return self.__dict__
    

    def createCliente(self):
        self.createDateTime = datetime.now()

    def updateCliente(self):
        self.updateDateTime = datetime.now()
    