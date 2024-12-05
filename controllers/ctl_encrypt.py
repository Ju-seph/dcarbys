from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("ENCRYPTION_KEY")

if not key:
    raise ValueError("ENCRYPTION_KEY no está configurada en el archivo .env.")

cipher_suite = Fernet(key)

def encrypt(data):
  
    if not isinstance(data, str):
        raise TypeError("El dato a encriptar debe ser una cadena de texto.")
    return cipher_suite.encrypt(data.encode())

def decrypt(data):
   
    if not isinstance(data, bytes):
        raise TypeError("El dato a desencriptar debe ser en formato bytes.")
    return cipher_suite.decrypt(data).decode()
