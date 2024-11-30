from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

# Obtener la clave de encriptación del archivo .env
key = os.getenv("ENCRYPTION_KEY")

# Verificar si la clave está configurada
if not key:
    raise ValueError("ENCRYPTION_KEY no está configurada en el archivo .env.")

# Crear el objeto Fernet
cipher_suite = Fernet(key)

def encrypt(data):
    """
    Encripta una cadena de texto.
    :param data: Cadena de texto a encriptar
    :return: Cadena encriptada en formato bytes
    """
    if not isinstance(data, str):
        raise TypeError("El dato a encriptar debe ser una cadena de texto.")
    return cipher_suite.encrypt(data.encode())

def decrypt(data):
    """
    Desencripta una cadena de texto encriptada.
    :param data: Cadena encriptada en formato bytes
    :return: Cadena de texto desencriptada
    """
    if not isinstance(data, bytes):
        raise TypeError("El dato a desencriptar debe ser en formato bytes.")
    return cipher_suite.decrypt(data).decode()
