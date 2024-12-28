import pymongo
from dotenv import load_dotenv
import os

load_dotenv()


class Mongodb:
    db_name = os.getenv("DB_NAME")
    db_URI = os.getenv("DB_URI")

    def __init__(self):
        try:
            # Intenta conectar a MongoDB usando la URI de conexión
            self.client = pymongo.MongoClient(self.db_URI, serverSelectionTimeoutMS=5000)
            # Intenta acceder a la base de datos
            self.mbd = self.client[self.db_name]
            # Verificar si la conexión fue exitosa
            self.client.admin.command('ping')  # Comando para comprobar si MongoDB está activo
            print("Conexión exitosa a MongoDB.")
        except pymongo.errors.ConnectionError as e:
            print(f"Error de conexión a MongoDB: {e}")
        except Exception as e:
            print(f"Ocurrió un error: {e}")

    def db(self):
        return self.mbd

    
