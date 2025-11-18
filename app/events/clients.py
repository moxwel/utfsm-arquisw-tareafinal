import aio_pika
import os
import logging
import json
import asyncio
from typing import Optional

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
    ),
    "users": RabbitMQClient(
        rabbitmq_url=os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/"), # !! Se asume que los clientes usan la misma URL !!
        
        exchange_name=os.getenv("USERS_RABBITMQ_EXCHANGE", "users.events"),
        exchange_type=aio_pika.ExchangeType.TOPIC,
        exchange_durable=True,

        queue_name=os.getenv("USERS_RABBITMQ_QUEUE", "channel_service_users_queue"),
        queue_durable=True,
        queue_routing_key=os.getenv("USERS_RABBITMQ_QUEUE_ROUTING_KEY", "users.#"),
        queue_arguments={
            "x-dead-letter-exchange": os.getenv("USERS_RABBITMQ_DLX", "channel_service_users_dlx"),
            "x-dead-letter-routing-key": os.getenv("USERS_RABBITMQ_DLQ", "channel_service_users_dlq"),
        },

        dlx_exchange_name=os.getenv("USERS_RABBITMQ_DLX", "channel_service_users_dlx"),
        dlx_exchange_type=aio_pika.ExchangeType.FANOUT,
        dlx_durable=True,

        dlq_queue_name=os.getenv("USERS_RABBITMQ_DLQ", "channel_service_users_dlq"),
        dlq_durable=True
    )
}