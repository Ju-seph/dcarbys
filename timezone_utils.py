# Archivo para manejar las zonas horarias
from datetime import datetime, timedelta

def get_ecuador_time():
    """
    Obtiene la hora actual en Ecuador (UTC-5)
    
    Returns:
        datetime: La hora actual en Ecuador
    """
    utc_time = datetime.utcnow()
    ecuador_time = utc_time - timedelta(hours=5)
    return ecuador_time

def format_ecuador_time(utc_datetime):
    """
    Convierte una fecha UTC a hora de Ecuador y la formatea
    
    Args:
        utc_datetime (datetime): Fecha en UTC
        
    Returns:
        str: Fecha formateada en hora de Ecuador
    """
    if not utc_datetime:
        return "No disponible"
    
    ecuador_time = utc_datetime - timedelta(hours=5)
    return ecuador_time.strftime('%d/%m/%Y %H:%M')

