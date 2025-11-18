import logging
from ...events.consumer import start_consumer_main
from ..callbacks.moderation import process_moderation_message

logger = logging.getLogger(__name__)


async def create_moderation_listeners(clients: dict):
    """Crea los listeners para las colas de moderación."""
    if "moderation" not in clients:
        logger.warning("Cliente 'moderation' no encontrado en la configuración de RabbitMQ")
        return
    
    try:
        consumer_tag = await start_consumer_main(
            client=clients["moderation"],
            callback=process_moderation_message,
            prefetch_count=1,
            manual_ack=False
        )
        logger.info(f"Listener de moderación iniciado con tag: {consumer_tag}")
    except Exception as e:
        logger.error(f"Error al iniciar listener de moderación: {e}")
        raise
