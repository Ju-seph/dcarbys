from datetime import datetime
from bson import ObjectId

class Pedido:
    def __init__(self, numero_pedido, usuario_id, productos, nombre, celular, direccion, ciudad, referencia, total, estado="en transcurso"):
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
        self.estado = estado  # Estados: "en transcurso", "finalizado", "cancelado"
        self.cancelado_por = None  # Nuevo campo para almacenar quién canceló el pedido
        self.rol_cancelado= None
        self.tiempo_estimado = ""  # Nuevo campo para el tiempo estimado
        self.fecha_confirmacion = None
        self.createDateTime = None
        self.updateDateTime = None
    def getPedido(self):
        return self.__dict__

    def createPedido(self):
        self.createDateTime = datetime.now()
        self.fecha_confirmacion = self.createDateTime

    def updatePedido(self):
        self.updateDateTime = datetime.now()

    @classmethod
    def from_dict(cls, data):
        pedido = cls(
            numero_pedido=data['numero_pedido'],
            usuario_id=data['usuario_id'],
            productos=data['productos'],
            nombre=data['nombre'],
            celular=data['celular'],
            direccion=data['direccion'],
            ciudad=data['ciudad'],
            referencia=data['codigo_postal'],
            total=data['total'],
            estado=data.get('estado', 'confirmado')
        )
        if '_id' in data:
            pedido._id = data['_id']
        if 'createDateTime' in data:
            pedido.createDateTime = data['createDateTime']
        if 'updateDateTime' in data:
            pedido.updateDateTime = data['updateDateTime']
        if 'fecha_confirmacion' in data:
            pedido.fecha_confirmacion = data['fecha_confirmacion']
        return pedido

    @classmethod
    def from_pedido_temporal(cls, pedido_temporal):
        pedido = cls(
            numero_pedido=pedido_temporal['numero_pedido'],
            usuario_id=pedido_temporal['usuario_id'],
            productos=pedido_temporal['productos'],
            nombre=pedido_temporal['nombre'],
            celular=pedido_temporal['celular'],
            direccion=pedido_temporal['direccion'],
            ciudad=pedido_temporal['ciudad'],
            referencia=pedido_temporal['referencia'],
            total=pedido_temporal['total']
        )
        pedido.createPedido()
        return pedido

