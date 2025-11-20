from fastapi import FastAPI
from contextlib import asynccontextmanager
from .routers.v1 import channels, members
from .db.conn import connect_to_mongo, close_mongo_connection
from .events.conn import connect_to_rabbitmq_all, close_rabbitmq_connection_all
from .events.clients import rabbit_clients
from .events.listeners.users import create_user_listeners
from .events.listeners.moderation import create_moderation_listeners
import logging
import socket
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Equivalente a on.event("startup")
    logging.info("Iniciando la aplicación y conectando a servicios externos...")
    connect_to_mongo()
    await connect_to_rabbitmq_all()
    await create_user_listeners(rabbit_clients)
    await create_moderation_listeners(rabbit_clients)
    yield
    # Equivalente a on.event("shutdown")
    logging.info("Cerrando conexiones a servicios externos...")
    close_mongo_connection()
    await close_rabbitmq_connection_all()
    logging.info("Aplicación detenida.")

descripcion_texto = f"""API para la gestión de canales.\n
Repositorio: https://github.com/moxwel/utfsm-arquisw-tareafinal/\n
Fecha de compilación: {os.getenv("BUILD_DATE", "unknown")}\n
Hostname: {socket.gethostname()}
"""

app = FastAPI(
    title="Servicio de Canales",
    version="1.0.0",
    lifespan=lifespan,
    description=descripcion_texto
)

app.include_router(channels.router)
app.include_router(members.router)

@app.get("/")
async def root():
    hostname = socket.gethostname()
    build_date = os.getenv("BUILD_DATE", "unknown")
    return {"message": "Hello World", "hostname": hostname, "build_date": build_date}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
