# Documentación de Mensajes del Broker

Esta es la documentación para los mensajes que se emiten a través del broker de mensajería (RabbitMQ). Actualmente, este servicio solo emite mensajes y no consume eventos de otros servicios.

## Generalidades

Todos los mensajes se publican en el exchange principal (configurado a través de la variable de entorno `RABBITMQ_MAIN_EXCHANGE`, por defecto `main_exchange`). Los mensajes utilizan un `routing_key` que sigue el formato `servicio.version.recurso.evento`.

## Mensajes Emitidos

A continuación se detallan los mensajes que este servicio emite.

### `channelService.v1.channel.created`

- **Descripción:** Se emite cuando se crea un nuevo canal.
- **Payload:**
  ```json
  {
    "channel_id": "string",
    "name": "string",
    "owner_id": "string",
    "created_at": "float"
  }
  ```

### `channelService.v1.channel.updated`

- **Descripción:** Se emite cuando se actualizan los datos de un canal (nombre, propietario, etc.).
- **Payload:**
  ```json
  {
    "channel_id": "string",
    "updated_fields": {
      "name": "string",
      "owner_id": "string",
      "channel_type": "string"
    },
    "updated_at": "float"
  }
  ```
  *Nota: `updated_fields` contiene solo los campos que fueron modificados.*

### `channelService.v1.channel.deleted`

- **Descripción:** Se emite cuando un canal es desactivado (soft delete).
- **Payload:**
  ```json
  {
    "channel_id": "string",
    "deleted_at": "float"
  }
  ```

### `channelService.v1.channel.reactivated`

- **Descripción:** Se emite cuando un canal previamente desactivado es reactivado.
- **Payload:**
  ```json
  {
    "channel_id": "string",
    "reactivated_at": "float"
  }
  ```

### `channelService.v1.user.added`

- **Descripción:** Se emite cuando un usuario es agregado a un canal.
- **Payload:**
  ```json
  {
    "channel_id": "string",
    "user_id": "string",
    "added_at": "float"
  }
  ```

### `channelService.v1.user.removed`

- **Descripción:** Se emite cuando un usuario es eliminado de un canal.
- **Payload:**
  ```json
  {
    "channel_id": "string",
    "user_id": "string",
    "removed_at": "float"
  }
  ```
