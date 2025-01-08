from pymongo import MongoClient

# Sustituye esta URI con tu configuración correcta.
DB_NAME="Dcarbys0"
DB_URI="mongodb+srv://Admin1:rPZkIbewdruBbunN@dcarbys0.qfnth.mongodb.net/?retryWrites=true&w=majority&appName=Dcarbys0"

try:
    client = MongoClient(DB_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    print("Conexión exitosa a MongoDB")
    print("Colecciones disponibles:", db.list_collection_names())
except Exception as e:
    print("Error de conexión:", e)
