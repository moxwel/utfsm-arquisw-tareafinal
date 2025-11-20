import aio_pika
import os
import logging
import json
import asyncio
from typing import Optional
from .clients import RabbitMQClient, rabbit_clients

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración global de reintentos
MAX_RETRIES = int(os.getenv("RABBITMQ_MAX_RETRIES", "20"))
RETRY_DELAY = float(os.getenv("RABBITMQ_RETRY_DELAY", "3"))

async def _setup_rabbitmq(client: RabbitMQClient):
    """Funcion auxiliar para configurar los exchanges, colas y bindings."""
    logger.info(f"Configurando exchanges, colas y bindings para cliente con exchange '{client.exchange_name}'...")
    
    # Configurar DLX y DLQ si están definidos
    if client.dlx_exchange_name and client.dlq_queue_name:
        logger.info(f"Declarando DLX '{client.dlx_exchange_name}'...")
        
        client.dlx_exchange = await client.channel.declare_exchange(
            name=client.dlx_exchange_name,
            type=client.dlx_exchange_type,
            durable=client.dlx_durable
        )

        logger.info(f"Declarando DLQ '{client.dlq_queue_name}' con routing key '{client.dlq_queue_name}'...")

        client.dlq_queue = await client.channel.declare_queue(
            name=client.dlq_queue_name,
            durable=client.dlq_durable
        )
        
        await client.dlq_queue.bind(client.dlx_exchange, routing_key=client.dlq_queue_name)
    
    # Configurar exchange y cola principal
    logger.info(f"Declarando exchange '{client.exchange_name}'...")
    
    client.main_exchange = await client.channel.declare_exchange(
        name=client.exchange_name,
        type=client.exchange_type,
        durable=client.exchange_durable
    )
    
    logger.info(f"Declarando cola '{client.queue_name}' con routing key '{client.queue_routing_key}'...")
    
    client.main_queue = await client.channel.declare_queue(
        name=client.queue_name,
        durable=client.queue_durable,
        arguments=client.queue_arguments if client.queue_arguments else None
    )
    
    await client.main_queue.bind(client.main_exchange, routing_key=client.queue_routing_key)
    
    logger.info("Configuración de RabbitMQ completada.")

async def connect_to_rabbitmq(client: RabbitMQClient):
    """Establece la conexión con RabbitMQ para un cliente específico. Si falla, reintenta hasta N veces."""
    for attempt in range(MAX_RETRIES):
        try:
            logger.info(f"Conectando a RabbitMQ en: {client.rabbitmq_url}... (Intento {attempt + 1} de {MAX_RETRIES})")
            client.connection = await aio_pika.connect(client.rabbitmq_url)
            client.channel = await client.connection.channel()

            await _setup_rabbitmq(client)

            logger.info(f"Conexión a RabbitMQ en {client.rabbitmq_url} establecida con éxito para exchange '{client.exchange_name}'.")
            return
        except (ConnectionError, asyncio.TimeoutError, aio_pika.exceptions.AMQPConnectionError) as e:
            if MAX_RETRIES - (attempt + 1) > 0:
                logger.error(f"No se pudo conectar a RabbitMQ: {e}. Reintentando en {RETRY_DELAY} segundos...")
                await asyncio.sleep(RETRY_DELAY)
            else:
                logger.error(f"No se pudo conectar a RabbitMQ después de {MAX_RETRIES} intentos. Rindiéndose.")
                raise e
        except Exception as e:
            logger.error(f"Ocurrió un error inesperado durante la conexión a RabbitMQ: {e}.")
            raise

async def connect_to_rabbitmq_all():
    """Establece la conexión con RabbitMQ para todos los clientes en rabbit_clients."""
    logger.info(f"Conectando a todos los clientes RabbitMQ ({len(rabbit_clients)} cliente(s))...")
    for client_name, client in rabbit_clients.items():
        logger.info(f"Conectando cliente '{client_name}'...")
        await connect_to_rabbitmq(client)
    logger.info("Todos los clientes RabbitMQ conectados exitosamente.")

async def close_rabbitmq_connection(client: RabbitMQClient):
    """Cierra la conexión con RabbitMQ para un cliente específico."""
    if client.channel:
        for tag, queue in client.active_consumers:
            try:
                await queue.cancel(consumer_tag=tag)
                logger.info(f"Consumidor con tag '{tag}' en cola '{queue.name}' cancelado.")
            except Exception as e:
                logger.error(f"Error al cancelar consumidor con tag '{tag}' en cola '{queue.name}': {e}")
        
        client.active_consumers.clear()

        await client.channel.close()
    if client.connection:
        await client.connection.close()
    logger.info(f"Conexión a RabbitMQ cerrada para exchange '{client.exchange_name}'.")

async def close_rabbitmq_connection_all():
    """Cierra la conexión con RabbitMQ para todos los clientes."""
    logger.info(f"Cerrando conexiones de todos los clientes RabbitMQ ({len(rabbit_clients)} cliente(s))...")
    for client_name, client in rabbit_clients.items():
        logger.info(f"Cerrando cliente '{client_name}'...")
        await close_rabbitmq_connection(client)
    logger.info("Todas las conexiones RabbitMQ cerradas.")
