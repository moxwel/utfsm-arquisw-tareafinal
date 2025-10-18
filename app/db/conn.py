import os
from mongoengine import connect, disconnect, connection
from logging import getLogger, INFO

# Configuración básica de logging
logger = getLogger(__name__)

class DBManager:
    """
    Clase para gestionar la conexión a la base de datos MongoDB.
    """
    client = None
    database = None
    alias: str = "default"

db_manager = DBManager()

# ====================================

def connect_to_mongo():
    """
    Establece la conexión con la base de datos MongoDB.
    """
    mongo_url = os.getenv("MONGO_URL", "mongodb://mongo:27017")
    logger.info(f"Conectando a MongoDB en: {mongo_url} ...")
    
    mongo_db_name = os.getenv("MONGO_DB_NAME", "channel_db")
    connect(db=mongo_db_name, host=mongo_url, alias=db_manager.alias)
    db_manager.client = connection.get_connection(alias=db_manager.alias)
    db_manager.database = connection.get_db(alias=db_manager.alias)
    logger.info("Conexión a MongoDB establecida con éxito.")

def close_mongo_connection():
    """
    Cierra la conexión con la base de datos MongoDB.
    """
    logger.info("Cerrando la conexión a MongoDB...")
    if db_manager.client:
        disconnect(alias=db_manager.alias)
        db_manager.client = None
        db_manager.database = None
        logger.info("Conexión a MongoDB cerrada.")

def get_database():
    """
    Obtiene la instancia de la base de datos MongoDB.
    """
    if db_manager.client is None:
        raise Exception("La conexión a la base de datos no está establecida. Llama a connect_to_mongo() primero.")
    return connection.get_db(alias=db_manager.alias)
