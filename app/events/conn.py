import aio_pika
import os
import logging
import json
import asyncio

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RabbitMQClient:
    def __init__(self):
        self.connection: aio_pika.Connection | None = None
        self.channel: aio_pika.Channel | None = None

        self.main_exchange: aio_pika.Exchange | None = None
        self.main_queue: aio_pika.Queue | None = None

        self.dlx_exchange: aio_pika.Exchange | None = None
        self.dlq_queue: aio_pika.Queue | None = None

client = RabbitMQClient()

async def _setup_rabbitmq(channel: aio_pika.abc.AbstractChannel):
    """Funcion auxiliar para configurar los exchanges, colas y bindings."""
    logger.info("Configurando exchanges, colas y bindings...")

    # Configuración de Dead Letter Exchange (DLX) y Queue (DLQ)
    dlx_exchange_name = os.getenv("RABBITMQ_DLX", "dlx_exchange")
    dlq_queue_name = os.getenv("RABBITMQ_DLQ", "dlq_queue")

    client.dlx_exchange = await channel.declare_exchange(dlx_exchange_name, aio_pika.ExchangeType.FANOUT)
    client.dlq_queue = await channel.declare_queue(dlq_queue_name, durable=True)

    await client.dlq_queue.bind(client.dlx_exchange)

    # Configuración del Exchange y Cola principal
    main_exchange_name = os.getenv("RABBITMQ_MAIN_EXCHANGE", "main_exchange")
    main_queue_name = os.getenv("RABBITMQ_MAIN_QUEUE", "main_queue")

    client.main_exchange = await channel.declare_exchange(main_exchange_name, aio_pika.ExchangeType.TOPIC, durable=True)
    client.main_queue = await channel.declare_queue(
        main_queue_name,
        durable=True,
        arguments={
            "x-dead-letter-exchange": dlx_exchange_name,
            "x-dead-letter-routing-key": dlq_queue_name
        }
    )
    
    await client.main_queue.bind(client.main_exchange, routing_key="#")

    logger.info("Configuración de RabbitMQ completada.")

async def connect_to_rabbitmq():
    """Establece la conexión con RabbitMQ. Si falla, reintenta hasta N veces."""
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    max_retries = int(os.getenv("RABBITMQ_MAX_RETRIES", "20"))
    timeout_seconds = float(os.getenv("RABBITMQ_RETRY_DELAY", "3"))
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Conectando a RabbitMQ en: {rabbitmq_url}... (Intento {attempt + 1} de {max_retries})")
            client.connection = await aio_pika.connect(rabbitmq_url)
            client.channel = await client.connection.channel()

            await _setup_rabbitmq(client.channel)

            logger.info("Conexión a RabbitMQ establecida con exito.")
            return
        except (ConnectionError, asyncio.TimeoutError, aio_pika.exceptions.AMQPConnectionError) as e:
            if max_retries - (attempt + 1) > 0:
                logger.error(f"No se pudo conectar a RabbitMQ: {e}. Reintentando en {timeout_seconds} segundos...")
                await asyncio.sleep(timeout_seconds)
            else:
                logger.error(f"No se pudo conectar a RabbitMQ después de {max_retries} intentos. Rindiéndose.")
                raise e
        except Exception as e:
            logger.error(f"Ocurrió un error inesperado durante la conexión a RabbitMQ: {e}.")
            raise

async def close_rabbitmq_connection():
    """Cierra la conexión con RabbitMQ."""
    if client.channel:
        await client.channel.close()
    if client.connection:
        await client.connection.close()
    logger.info("Conexión a RabbitMQ cerrada.")
