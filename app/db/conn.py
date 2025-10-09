import os
from pymongo import MongoClient
from logging import getLogger, INFO

# Configuración básica de logging
logger = getLogger(__name__)

class DBManager:
    """
    Clase para gestionar la conexión a la base de datos MongoDB.
    """
    client: MongoClient = None
    database = None

db_manager = DBManager()

# ====================================

def connect_to_mongo():
    """
    Establece la conexión con la base de datos MongoDB.
    """
    mongo_url = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    logger.info(f"Conectando a MongoDB en: {mongo_url} ...")
    db_manager.client = MongoClient(mongo_url)
    
    mongo_db_name = os.getenv("MONGO_DB_NAME", "fastapi_db")
    db_manager.database = db_manager.client.get_database(mongo_db_name)
    
    logger.info("Conexión a MongoDB establecida con éxito.")

def close_mongo_connection():
    """
    Cierra la conexión con la base de datos MongoDB.
    """
    logger.info("Cerrando la conexión a MongoDB...")
    if db_manager.client:
        db_manager.client.close()
        logger.info("Conexión a MongoDB cerrada.")

def get_database():
    """
    Obtiene la instancia de la base de datos MongoDB.
    """
    if db_manager.database is None:
        raise Exception("La conexión a la base de datos no está establecida. Llama a connect_to_mongo() primero.")
    return db_manager.database
