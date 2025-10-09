from fastapi import FastAPI
from .routers import items
from .db.conn import connect_to_mongo, close_mongo_connection
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = FastAPI()

@app.on_event("startup")
def startup_event():
    connect_to_mongo()

@app.on_event("shutdown")
def shutdown_event():
    close_mongo_connection()

app.include_router(items.router)

@app.get("/")
async def root():
    return {"message": "Hello World"}
