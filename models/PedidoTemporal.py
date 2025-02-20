from datetime import datetime, timedelta
from bson import ObjectId

class PedidoTemporal:
    def __init__(self, numero_pedido, usuario_id, productos, nombre, celular, direccion, ciudad, referencia, total, estado="pendiente"):
        self._id = ObjectId()
        self.numero_pedido = numero_pedido
        self.usuario_id = usuario_id
        self.productos = productos
        self.nombre = nombre
        self.celular = celular
        self.direccion = direccion
        self.ciudad = ciudad
        self.referencia = referencia
        self.total = total
        self.estado = estado
        self.estado_administrador = "pendiente"  # Estado del administrador (aceptado/rechazado)
        self.estado_cliente = "pendiente"  # Estado del cliente (confirmado/cancelado)
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
            celular=data['celular'],
            ciudad=data['ciudad'],
            direccion=data['direccion'],
            referencia=data['referencia'],
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

