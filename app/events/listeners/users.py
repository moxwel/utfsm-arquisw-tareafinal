import logging
from ...events.consumer import start_consumer_main
from ..callbacks.users import process_user_message

logger = logging.getLogger(__name__)


async def create_user_listeners(clients: dict):
    """Crea los listeners para las colas de usuarios."""
    if "users" not in clients:
        logger.warning("Cliente 'users' no encontrado en la configuración de RabbitMQ")
        return
    
    try:
        consumer_tag = await start_consumer_main(
            client=clients["users"],
            callback=process_user_message,
            prefetch_count=1,
            manual_ack=False
        )
        logger.info(f"Listener de usuarios iniciado con tag: {consumer_tag}")
    except Exception as e:
        logger.error(f"Error al iniciar listener de usuarios: {e}")
        raise
