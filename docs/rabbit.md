# Arquitectura de Eventos (RabbitMQ)

Este documento describe cómo funciona la capa de eventos del servicio, ubicada en el directorio [`app/events/`](../app/events/). El sistema utiliza `aio-pika` para la comunicación asíncrona con RabbitMQ.

## Estructura del Módulo

- **`clients.py`**: Definición de configuraciones para los distintos clientes/conexiones.
- **`conn.py`**: Gestión del ciclo de vida de las conexiones (conectar, reintentar, desconectar).
- **`publish.py`**: Funciones para enviar mensajes.
- **`consumer.py`**: Lógica genérica para consumir mensajes y manejar ACKs.
- **`listeners/`**: Inicializadores de consumidores específicos.
- **`callbacks/`**: Funciones que procesan la lógica de negocio de los mensajes recibidos.

## 1. Clientes (`clients.py`)

En [`app/events/clients.py`](../app/events/clients.py) se define la clase `RabbitMQClient` y el diccionario `rabbit_clients`.

Cada entrada en `rabbit_clients` representa una configuración lógica de conexión que incluye:
- URL de conexión.
- Exchange principal y su tipo.
- Cola principal y routing keys.
- Configuración de Dead Letter Exchange (DLX) y Queue (DLQ) para manejo de errores.

Actualmente existen dos clientes configurados:
1. **`channel`**: Usado principalmente para **publicar** eventos del dominio de canales.
2. **`users`**: Usado para **consumir** eventos del dominio de usuarios.

## 2. Conexión (`conn.py`)

El archivo [`app/events/conn.py`](../app/events/conn.py) maneja la conexión física.

- **`connect_to_rabbitmq_all()`**: Itera sobre todos los clientes definidos y establece la conexión.
- **`_setup_rabbitmq(client)`**: Una vez conectado, declara automáticamente:
  - El Exchange principal.
  - La Cola principal (si aplica).
  - El Binding entre Exchange y Cola.
  - La infraestructura de DLX/DLQ si está configurada.
- **Reintentos**: Si la conexión falla al inicio, el sistema reintenta `RABBITMQ_MAX_RETRIES` veces con un delay de `RABBITMQ_RETRY_DELAY`.

## 3. Publicación (`publish.py`)

Para enviar mensajes se utiliza [`app/events/publish.py`](../app/events/publish.py).

- **`publish_message_main(client, body, routing_key)`**: Publica un mensaje en el exchange configurado como principal en el cliente.
- **`publish_message(...)`**: Permite especificar un exchange arbitrario.

Los mensajes se envían como persistentes (`delivery_mode=PERSISTENT`) y serializados en JSON.

## 4. Consumidores (`consumer.py`)

La lógica de consumo en [`app/events/consumer.py`](../app/events/consumer.py) abstrae el manejo manual de los mensajes.

- **`start_consumer_main`**: Inicia la escucha en la cola principal del cliente.
- **Auto-ACK Wrapper**: Por defecto, envuelve la función de callback.
  - Si el callback se ejecuta **sin errores**, envía `ACK`.
  - Si el callback **lanza una excepción**, envía `NACK` con `requeue=False` (enviando el mensaje a la DLQ).

## 5. Listeners y Callbacks

Para organizar el código, se separa la inicialización del consumidor de la lógica de negocio.

1. **Listeners (`app/events/listeners/`)**:
   - Ejemplo: [`create_user_listeners`](../app/events/listeners/users.py).
   - Se llama al inicio de la aplicación (`main.py`).
   - Obtiene el cliente `users` y llama a `start_consumer_main` pasando la función de callback.

2. **Callbacks (`app/events/callbacks/`)**:
   - Ejemplo: [`process_user_message`](../app/events/callbacks/users.py).
   - Contiene la lógica pura de qué hacer con el mensaje (actualizar BD, logs, etc.).
   - Recibe un objeto `aio_pika.IncomingMessage`.

## Flujo de Inicio

El ciclo de vida se gestiona en [`app/main.py`](../app/main.py):

1. Al iniciar la app (`lifespan` startup):
   - Se llama a `connect_to_rabbitmq_all()` para establecer conexiones y declarar topología.
   - Se llama a `create_user_listeners(rabbit_clients)` para empezar a escuchar eventos de usuarios.

2. Al detener la app (`lifespan` shutdown):
   - Se llama a `disconnect_from_rabbitmq_all()` para cerrar canales y conexiones limpiamente.
