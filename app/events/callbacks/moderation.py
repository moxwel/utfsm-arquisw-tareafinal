import aio_pika
import json
import logging

logger = logging.getLogger(__name__)


async def process_moderation_message(message: aio_pika.IncomingMessage):
    """Procesa mensajes de la cola de moderación."""
    try:
        body = message.body.decode()
        data = json.loads(body)
        
        logger.info(f"Mensaje recibido de moderation_queue: {data}")
        
        # TODO: Implementar lógica de procesamiento de moderación
        
    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error procesando mensaje de moderación: {e}")
        raise
