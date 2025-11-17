import aio_pika
import json
import logging

logger = logging.getLogger(__name__)

class PublishError(Exception):
    """Excepción personalizada para errores de publicación en RabbitMQ."""
    pass

async def publish_message_main(client, message_body: dict, routing_key: str):
    """Publica un mensaje simple en el exchange principal de RabbitMQ."""
    if not client.channel:
        logger.error("No hay un canal de RabbitMQ disponible para publicar.")
        raise ConnectionError("La conexión a RabbitMQ no está establecida.")

    message_payload = aio_pika.Message(
        body=json.dumps(message_body).encode('utf-8'),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    
    try:
        _ = await client.channel.get_exchange(client.main_exchange.name, ensure=True)
    except aio_pika.exceptions.ExchangeNotFoundEntity:
        logger.error(f"El exchange '{client.main_exchange.name}' no existe.")
        raise PublishError(f"El exchange '{client.main_exchange.name}' no existe.")

    await client.main_exchange.publish(message_payload, routing_key=routing_key)
    logger.info(f"Mensaje publicado en exchange '{client.main_exchange.name}' con routing key '{routing_key}'")


async def publish_message(client, message_body: dict, routing_key: str, exchange_name: str):
    """Publica un mensaje en un exchange de RabbitMQ."""
    if not client.channel:
        logger.error("No hay un canal de RabbitMQ disponible para publicar.")
        raise ConnectionError("La conexión a RabbitMQ no está establecida.")

    message_payload = aio_pika.Message(
        body=json.dumps(message_body).encode('utf-8'),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )
    
    try:
        target_exchange = await client.channel.get_exchange(exchange_name, ensure=True)
    except aio_pika.exceptions.ChannelClosed:
        logger.error(f"El exchange '{exchange_name}' no existe.")
        raise PublishError(f"El exchange '{exchange_name}' no existe.")
    
    await target_exchange.publish(message_payload, routing_key=routing_key)
    logger.info(f"Mensaje publicado en exchange '{exchange_name}' con routing key '{routing_key}'")
