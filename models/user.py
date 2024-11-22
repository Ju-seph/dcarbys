from datetime import datetime

class User:

    def __init__(self, cedula, nombre, usuario, clave, rol):
        self.cedula= cedula
        self.nombre= nombre
        self.usuario= usuario
        self.clave= clave
        self.rol= rol

    def obtener_user(self):
        return self.__dict__
    

    def crear_usuario(self):
        self.fecha_creacion = datetime.now()

    def update_usuario(self):
        self.fecha_modificacion = datetime.now()
    
