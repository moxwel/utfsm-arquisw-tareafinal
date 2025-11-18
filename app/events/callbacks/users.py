import aio_pika
import json
import logging

logger = logging.getLogger(__name__)


async def process_user_message(message: aio_pika.IncomingMessage):
    """Procesa mensajes de la cola de usuarios."""
    try:
        body = message.body.decode()
        data = json.loads(body)
        
        logger.info(f"Mensaje recibido de users_queue: {data}")
        
        # TODO: Implementar lógica de procesamiento de usuarios
        # Ejemplo: crear usuario, actualizar usuario, etc.
        
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error procesando mensaje de usuario: {e}")
        raise
