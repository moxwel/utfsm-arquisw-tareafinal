import logging
from ...events.consumer import start_consumer
from ..callbacks.users import process_user_message

logger = logging.getLogger(__name__)


async def create_user_listeners(clients: dict):
    """Crea los listeners para las colas de usuarios.
    
    Args:
        clients: Diccionario con los clientes de RabbitMQ configurados.
                 Ejemplo: {"users": RabbitMQClient, "channels": RabbitMQClient}
    """
    # TODO: Descomentar cuando el cliente 'users' esté disponible en conn.py
    # if "users" not in clients:
    #     logger.warning("Cliente 'users' no encontrado en la configuración de RabbitMQ")
    #     return
    
    # try:
    #     consumer_tag = await start_consumer(
    #         client=clients["users"],
    #         callback=process_user_message,
    #         queue_name="users_queue",
    #         prefetch_count=1,
    #         manual_ack=False
    #     )
    #     logger.info(f"Listener de usuarios iniciado con tag: {consumer_tag}")
    # except Exception as e:
    #     logger.error(f"Error al iniciar listener de usuarios: {e}")
    #     raise
    
    logger.info("Listeners de usuarios deshabilitados (descomentar en listener.py)")
