import aio_pika
import os
import logging
import json
import asyncio
from typing import Optional

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración global de reintentos
MAX_RETRIES = int(os.getenv("RABBITMQ_MAX_RETRIES", "20"))
RETRY_DELAY = float(os.getenv("RABBITMQ_RETRY_DELAY", "3"))

class RabbitMQClient:
    def __init__(
        self,
        rabbitmq_url: str,
        
        exchange_name: str,
        exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.TOPIC,
        exchange_durable: bool = True,
        
        queue_name: str = "",
        queue_durable: bool = True,
        queue_routing_key: str = "#",
        queue_arguments: Optional[dict] = None,
        
        dlx_exchange_name: Optional[str] = None,
        dlx_exchange_type: aio_pika.ExchangeType = aio_pika.ExchangeType.FANOUT,
        dlx_durable: bool = True,
        
        dlq_queue_name: Optional[str] = None,
        dlq_durable: bool = True
    ):
        self.rabbitmq_url = rabbitmq_url
        
        # Configuración de exchange y queue principal
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.exchange_durable = exchange_durable
        
        self.queue_name = queue_name
        self.queue_durable = queue_durable
        self.queue_routing_key = queue_routing_key
        self.queue_arguments = queue_arguments or {}
        
        # Configuración de DLX y DLQ (opcional)
        self.dlx_exchange_name = dlx_exchange_name
        self.dlx_exchange_type = dlx_exchange_type
        self.dlx_durable = dlx_durable
        
        self.dlq_queue_name = dlq_queue_name
        self.dlq_durable = dlq_durable
        
        # Objetos de conexión
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        
        # Objetos declarados
        self.main_exchange: Optional[aio_pika.Exchange] = None
        self.main_queue: Optional[aio_pika.Queue] = None
        self.dlx_exchange: Optional[aio_pika.Exchange] = None
        self.dlq_queue: Optional[aio_pika.Queue] = None

# Diccionario de clientes RabbitMQ
# TODO: Si hay que agregar más clientes, hacerlo aquí!!!
rabbit_clients = {
    "channel": RabbitMQClient(
        rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/"),
        
        exchange_name=os.getenv("RABBITMQ_MAIN_EXCHANGE", "main_exchange"),
        exchange_type=aio_pika.ExchangeType.TOPIC,
        exchange_durable=True,
        
        queue_name=os.getenv("RABBITMQ_MAIN_QUEUE", "main_queue"),
        queue_durable=True,
        queue_routing_key="#",
        queue_arguments={
            "x-dead-letter-exchange": os.getenv("RABBITMQ_DLX", "dlx_exchange"),
            "x-dead-letter-routing-key": os.getenv("RABBITMQ_DLQ", "dlq_queue"),
        },
        
        dlx_exchange_name=os.getenv("RABBITMQ_DLX", "dlx_exchange"),
        dlx_exchange_type=aio_pika.ExchangeType.FANOUT,
        dlx_durable=True,
        
        dlq_queue_name=os.getenv("RABBITMQ_DLQ", "dlq_queue"),
        dlq_durable=True
    )
}

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
