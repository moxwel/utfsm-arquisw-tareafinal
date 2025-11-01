from fastapi import FastAPI
from .routers.v1 import channels, members, threads
from .db.conn import connect_to_mongo, close_mongo_connection
from .events.conn import connect_to_rabbitmq, close_rabbitmq_connection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    connect_to_mongo()
    await connect_to_rabbitmq()

@app.on_event("shutdown")
async def shutdown_event():
    close_mongo_connection()
    await close_rabbitmq_connection()

app.include_router(channels.router)
app.include_router(members.router)
app.include_router(threads.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
