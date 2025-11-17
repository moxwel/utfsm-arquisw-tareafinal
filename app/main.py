from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers.v1 import channels, members
from .db.conn import connect_to_mongo, close_mongo_connection
from .events.conn import connect_to_rabbitmq_all, close_rabbitmq_connection_all
import logging
import socket

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Equivalente a on.event("startup")
    logging.info("Iniciando la aplicación y conectando a servicios externos...")
    connect_to_mongo()
    await connect_to_rabbitmq_all()
    yield
    # Equivalente a on.event("shutdown")
    logging.info("Cerrando conexiones a servicios externos...")
    close_mongo_connection()
    await close_rabbitmq_connection_all()

app = FastAPI(title="Servicio de Canales", version="1.0.0", lifespan=lifespan)

app.include_router(channels.router)
app.include_router(members.router)

@app.get("/")
async def root():
    hostname = socket.gethostname()
    return {"message": "Hello World", "hostname": hostname}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
