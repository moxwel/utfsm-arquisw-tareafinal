import aio_pika
import json
import logging
from ...db import querys

logger = logging.getLogger(__name__)

def _process_warning(data: dict):
    user_id = data.get("user_id")
    channel_id = data.get("channel_id")
    
    if not user_id or not channel_id:
        logger.error("Faltan 'user_id' o 'channel_id' en los datos del evento de advertencia.")
        return
    
    channel = querys.db_change_status(channel_id, user_id, "warning")
    
    if channel is None:
        logger.warning(f"No se encontró el canal '{channel_id}' o el usuario '{user_id}' no es miembro.")
    else:
        logger.info(f"Usuario '{user_id}' en canal '{channel_id}' marcado con 'warning'.")

def _process_ban(data: dict):
    user_id = data.get("user_id")
    channel_id = data.get("channel_id")
    
    if not user_id or not channel_id:
        logger.error("Faltan 'user_id' o 'channel_id' en los datos del evento de usuario baneado.")
        return
    
    channel = querys.db_change_status(channel_id, user_id, "banned")
    
    if channel is None:
        logger.warning(f"No se encontró el canal '{channel_id}' o el usuario '{user_id}' no es miembro.")
    else:
        logger.info(f"Usuario '{user_id}' en canal '{channel_id}' marcado con 'banned'.")

def _process_unban(data: dict):
    user_id = data.get("user_id")
    channel_id = data.get("channel_id")
    
    if not user_id or not channel_id:
        logger.error("Faltan 'user_id' o 'channel_id' en los datos del evento de usuario desbaneado.")
        return
    
    channel = querys.db_change_status(channel_id, user_id, "normal")
    
    if channel is None:
        logger.warning(f"No se encontró el canal '{channel_id}' o el usuario '{user_id}' no es miembro.")
    else:
        logger.info(f"Usuario '{user_id}' en canal '{channel_id}' marcado con 'normal'.")

async def process_moderation_message(message: aio_pika.IncomingMessage):
    """Procesa mensajes de la cola de moderación."""
    try:
        body = message.body.decode()
        data = json.loads(body)
        
        logger.info(f"Mensaje recibido de moderation_queue: {data}")
        
        event_type = data.get("event_type")
        message_data = data.get("data", {})
        
        if event_type == "moderation.warning":
            _process_warning(message_data)
        elif event_type == "moderation.user_banned":
            _process_ban(message_data)
        elif event_type == "moderation.user_unbanned":
            _process_unban(message_data)
        else:
            logger.error(f"Tipo de evento desconocido: {event_type}")

    except json.JSONDecodeError as e:
        logger.error(f"Error al decodificar JSON: {e}")
        raise
    except Exception as e:
        logger.error(f"Error procesando mensaje de moderación: {e}")
        raise
