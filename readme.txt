README
=================================================================
Maximiliano Sepúlveda
Felipe Mellado
Cristopher Fuentes Llantén  - ROL: 201973598-5

=================================================================
Este proyecto es un servicio (API) en FastAPI para gestión de canales y miembros,
con persistencia en MongoDB y mensajería de eventos vía RabbitMQ.
=================================================================

    INSTRUCCIONES DE USO

Paso 0: Verificar/ajustar variables de entorno (.env)

    Archivo .env (valores por defecto):
        MONGO_URL=mongodb://mongo:27017
        MONGO_DB_NAME=channel_service_db

        RABBITMQ_URL=amqp://guest:guest@rabbitmq/
        RABBITMQ_MAIN_EXCHANGE=channel_service_exchange
        RABBITMQ_MAIN_QUEUE=channel_service_queue
        RABBITMQ_DLX=dlx_exchange
        RABBITMQ_DLQ=dlq_queue

        RABBITMQ_MAX_RETRIES=20
        RABBITMQ_RETRY_DELAY=3

    Solo modifique si necesita otras credenciales/hosts.

Paso 1: Construir y levantar los servicios con Docker

    $ docker compose up --build

    Esto levanta:
      - api (FastAPI) en http://localhost:8000
      - mongo en el puerto 27017
      - rabbitmq en los puertos 5672 (AMQP) y 15672 (UI)

    Para detener y borrar volúmenes:
      $ docker compose down -v

Paso 2: Verificar que todo esté corriendo

    API (Swagger UI):
      http://localhost:8000/docs
    
    RabbitMQ Management UI (usuario/clave: guest/guest):
      http://localhost:15672

    La API no intentará conectarse a RabbitMQ hasta que esté saludable (healthcheck).

Paso 3: Probar flujo básico

    - Crear, listar y eliminar canales desde la API (ver /docs).
    - Al crear/eliminar, el servicio publica eventos en RabbitMQ (por ejemplo, channel.created / channel.deleted).
    - Revise la cola/intercambio configurados en RabbitMQ para validar los mensajes.

FIN


================================================================
REQUERIMIENTOS
================================================================
- Docker 24+ y Docker Compose (plugin) 2.20+
- Python 3.11+ (solo si ejecuta sin Docker)

Notas:

1) La orquestación usa healthcheck en RabbitMQ para evitar errores de conexión temprana.
2) Si cambia nombres de colas/exchanges, actualice el .env y reinicie los contenedores.
3) Credenciales por defecto de RabbitMQ: guest/guest (solo en localhost).
4) Si modifica los esquemas o eventos de la API, recuerde alinear los consumidores de mensajes.

