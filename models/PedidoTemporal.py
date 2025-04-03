from datetime import datetime, timedelta
from bson import ObjectId
import pytz

class PedidoTemporal:
    def __init__(self, numero_pedido, usuario_id, productos, nombre, celular, direccion, ciudad, referencia, total, metodo_pago, estado="pendiente"):
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
        self.metodo_pago = metodo_pago  # Nuevo campo para el método de pago
        self.estado = estado
        self.estado_administrador = "pendiente"  # Estado del administrador (aceptado/rechazado)
        self.estado_cliente = "pendiente"  # Estado del cliente (confirmado/cancelado)
        self.createDateTime = None
        self.updateDateTime = None
        self.expireDateTime = None

    def getPedidoTemporal(self):
        return self.__dict__

    def createPedidoTemporal(self, custom_datetime=None):
        """
        Crea un pedido temporal con la fecha proporcionada o la fecha actual en UTC
        
        Args:
            custom_datetime (datetime, optional): Fecha personalizada para el pedido
        """
        # Si se proporciona una fecha personalizada, asegurarse de que tenga información de zona horaria
        if custom_datetime:
            # Si la fecha no tiene información de zona horaria, asumir que es UTC
            if custom_datetime.tzinfo is None:
                custom_datetime = pytz.UTC.localize(custom_datetime)
        else:
            # Si no se proporciona fecha, usar la hora actual en UTC
            custom_datetime = datetime.now(pytz.UTC)
        
        self.createDateTime = custom_datetime
        self.expireDateTime = self.createDateTime + timedelta(hours=2)

    def updatePedidoTemporal(self):
        # Usar UTC para la fecha de actualización
        self.updateDateTime = datetime.now(pytz.UTC)

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
            metodo_pago=data['metodo_pago'],  # Nuevo campo para el método de pago
            estado=data.get('estado', 'pendiente')
        )
        if '_id' in data:
            pedido._id = data['_id']
        if 'createDateTime' in data:
            # Asegurarse de que createDateTime tenga información de zona horaria
            create_time = data['createDateTime']
            if create_time and not hasattr(create_time, 'tzinfo'):
                create_time = pytz.UTC.localize(create_time)
            pedido.createDateTime = create_time
        if 'updateDateTime' in data:
            # Asegurarse de que updateDateTime tenga información de zona horaria
            update_time = data['updateDateTime']
            if update_time and not hasattr(update_time, 'tzinfo'):
                update_time = pytz.UTC.localize(update_time)
            pedido.updateDateTime = update_time
        if 'expireDateTime' in data:
            # Asegurarse de que expireDateTime tenga información de zona horaria
            expire_time = data['expireDateTime']
            if expire_time and not hasattr(expire_time, 'tzinfo'):
                expire_time = pytz.UTC.localize(expire_time)
            pedido.expireDateTime = expire_time
        return pedido