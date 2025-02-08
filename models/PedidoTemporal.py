from datetime import datetime, timedelta
from bson import ObjectId

class PedidoTemporal:
    def __init__(self, numero_pedido, usuario_id, productos, nombre, telefono, direccion, ciudad, codigo_postal, total, estado="pendiente"):
        self._id = ObjectId()
        self.numero_pedido = numero_pedido
        self.usuario_id = usuario_id
        self.productos = productos
        self.nombre = nombre
        self.telefono = telefono
        self.direccion = direccion
        self.ciudad = ciudad
        self.codigo_postal = codigo_postal
        self.total = total
        self.estado = estado
        self.createDateTime = None
        self.updateDateTime = None
        self.expireDateTime = None

    def getPedidoTemporal(self):
        return self.__dict__

    def createPedidoTemporal(self):
        self.createDateTime = datetime.now()
        self.expireDateTime = self.createDateTime + timedelta(minutes=15)

    def updatePedidoTemporal(self):
        self.updateDateTime = datetime.now()

    @classmethod
    def from_dict(cls, data):
        pedido = cls(
            numero_pedido=data['numero_pedido'],
            usuario_id=data['usuario_id'],
            productos=data['productos'],
            nombre=data['nombre'],
            telefono=data['telefono'],
            direccion=data['direccion'],
            ciudad=data['ciudad'],
            codigo_postal=data['codigo_postal'],
            total=data['total'],
            estado=data.get('estado', 'pendiente')
        )
        if '_id' in data:
            pedido._id = data['_id']
        if 'createDateTime' in data:
            pedido.createDateTime = data['createDateTime']
        if 'updateDateTime' in data:
            pedido.updateDateTime = data['updateDateTime']
        if 'expireDateTime' in data:
            pedido.expireDateTime = data['expireDateTime']
        return pedido

