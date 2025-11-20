import aio_pika
import json
import logging
import asyncio
from typing import Callable, Optional

logger = logging.getLogger(__name__)

class ConsumerError(Exception):
    """Excepción personalizada para errores de consumo en RabbitMQ."""
    pass

def _create_auto_ack_wrapper(process_func: Callable):
    """Función interna que crea un wrapper para manejar ACK/NACK automáticamente"""
    async def callback_wrapper(message: aio_pika.IncomingMessage):
        try:
            # Ejecutar la función de procesamiento
            if asyncio.iscoroutinefunction(process_func):
                await process_func(message)
            else:
                process_func(message)
            
            # Si todo salió bien, hacer ACK
            await message.ack()
            logger.debug(f"Mensaje ACK: {message.delivery_tag}")
            
        except Exception as e:
            # Si hubo error, hacer NACK (rechazar sin requeue)
            logger.error(f"Error procesando mensaje {message.delivery_tag}: {e}")
            await message.nack(requeue=False)
            logger.warning(f"Mensaje NACK (enviado a DLQ si está configurado): {message.delivery_tag}")
    
    return callback_wrapper

async def start_consumer_main(client, callback: Callable, prefetch_count: int = 1, manual_ack: bool = False):
    """Consume mensajes de la cola principal de RabbitMQ.
    
    Por defecto, maneja automáticamente el ACK/NACK de los mensajes:
    - Si el callback se ejecuta sin errores: ACK (confirma el mensaje)
    - Si el callback lanza una excepción: NACK sin requeue (envía a DLQ si está configurado)
    """
    if not client.channel:
        logger.error("No hay un canal de RabbitMQ disponible para consumir.")
        raise ConnectionError("La conexión a RabbitMQ no está establecida.")
    
    if not client.main_queue:
        logger.error("No hay una cola principal configurada para consumir.")
        raise ConsumerError("La cola principal no está configurada.")
    
    try:
        await client.channel.set_qos(prefetch_count=prefetch_count)
        
        # Si manual_ack=False, envolver el callback con manejo automático de ACK/NACK
        final_callback = callback if manual_ack else _create_auto_ack_wrapper(callback)
        
        consumer_tag = await client.main_queue.consume(final_callback, no_ack=False)
        client.active_consumers.append((consumer_tag, client.main_queue))
        
        logger.info(f"Consumidor iniciado en la cola principal '{client.main_queue.name}' (prefetch_count={prefetch_count}, manual_ack={manual_ack})")
        return consumer_tag
    except Exception as e:
        logger.error(f"Error al iniciar el consumidor en la cola principal: {e}")
        raise ConsumerError(f"Error al iniciar el consumidor: {e}")


async def start_consumer(client, callback: Callable, queue_name: str, prefetch_count: int = 1, manual_ack: bool = False):
    """Consume mensajes de una cola específica de RabbitMQ (la cola debe existir previamente).
    
    Por defecto, maneja automáticamente el ACK/NACK de los mensajes:
    - Si el callback se ejecuta sin errores: ACK (confirma el mensaje)
    - Si el callback lanza una excepción: NACK sin requeue (envía a DLQ si está configurado)"""
    if not client.channel:
        logger.error("No hay un canal de RabbitMQ disponible para consumir.")
        raise ConnectionError("La conexión a RabbitMQ no está establecida.")
    
    try:
        # Obtener la cola existente (no la declara, debe existir previamente)
        queue = await client.channel.get_queue(queue_name, ensure=False)
        
        # Configurar QoS
        await client.channel.set_qos(prefetch_count=prefetch_count)
        
        # Si manual_ack=False, envolver el callback con manejo automático de ACK/NACK
        final_callback = callback if manual_ack else _create_auto_ack_wrapper(callback)
        
        consumer_tag = await queue.consume(final_callback, no_ack=False)
        client.active_consumers.append((consumer_tag, queue))
        
        logger.info(f"Consumidor iniciado en la cola '{queue_name}' (prefetch_count={prefetch_count}, manual_ack={manual_ack})")
        return consumer_tag
    except aio_pika.exceptions.ChannelClosed as e:
        logger.error(f"La cola '{queue_name}' no existe: {e}")
        raise ConsumerError(f"La cola '{queue_name}' no existe.")
    except Exception as e:
        logger.error(f"Error al iniciar el consumidor en la cola '{queue_name}': {e}")
        raise ConsumerError(f"Error al iniciar el consumidor: {e}")

async def get_one_message_main(client, timeout: int = 5):
    """Obtiene UN solo mensaje de la cola principal bajo demanda."""
    if not client.main_queue:
        logger.error("No hay una cola principal configurada.")
        raise ConsumerError("La cola principal no está configurada.")
    
    try:
        message = await client.main_queue.get(timeout=timeout, no_ack=False)
        
        if message:
            body = message.body.decode()
            await message.ack()
            logger.info(f"Mensaje obtenido y confirmado: {body}")
            return {"success": True, "message": body, "error": None}
        else:
            return {"success": False, "message": None, "error": "No hay mensajes en la cola"}
            
    except Exception as e:
        logger.error(f"Error al obtener mensaje: {e}")
        return {"success": False, "message": None, "error": str(e)}

async def get_one_message(client, queue_name: str, timeout: int = 5):
    """Obtiene UN solo mensaje de una cola específica bajo demanda (la cola debe existir previamente)."""
    if not client.channel:
        logger.error("No hay un canal de RabbitMQ disponible.")
        raise ConnectionError("La conexión a RabbitMQ no está establecida.")
    
    try:
        # Obtener la cola existente (no la declara, debe existir previamente)
        queue = await client.channel.get_queue(queue_name, ensure=False)
    except aio_pika.exceptions.ChannelClosed:
        logger.error(f"La cola '{queue_name}' no existe.")
        raise ConsumerError(f"La cola '{queue_name}' no existe.")
    
    try:
        message = await queue.get(timeout=timeout, no_ack=False)
        
        if message:
            body = message.body.decode()
            await message.ack()
            logger.info(f"Mensaje obtenido y confirmado de la cola '{queue_name}': {body}")
            return {"success": True, "message": body, "error": None}
        else:
            return {"success": False, "message": None, "error": "No hay mensajes en la cola"}
            
    except Exception as e:
        logger.error(f"Error al obtener mensaje de la cola '{queue_name}': {e}")
        return {"success": False, "message": None, "error": str(e)}

async def stop_consumer(client, consumer_tag: str):
    """Detiene un consumidor específico usando su consumer_tag."""
    if not client.channel:
        logger.error("No hay un canal de RabbitMQ disponible.")
        raise ConnectionError("La conexión a RabbitMQ no está establecida.")
    
    try:
        await client.channel.basic_cancel(consumer_tag)
        logger.info(f"Consumidor detenido: {consumer_tag}")
    except Exception as e:
        logger.error(f"Error al detener el consumidor {consumer_tag}: {e}")
        raise ConsumerError(f"Error al detener el consumidor: {e}")
