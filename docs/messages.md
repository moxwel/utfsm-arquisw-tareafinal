# Documentación de Mensajes del Broker

Esta documentación detalla los mensajes que el servicio emite y consume a través del broker de mensajería (RabbitMQ).

## Configuración General

El servicio maneja múltiples clientes de RabbitMQ definidos en [`app/events/clients.py`](../app/events/clients.py).

- **Exchange Principal (Emisión):** Configurado vía `RABBITMQ_MAIN_EXCHANGE` (default: `channel_service_exchange`).
- **Exchange de Usuarios (Consumo):** Configurado vía `USERS_RABBITMQ_EXCHANGE` (default: `users.events`).

---

## Mensajes Emitidos

Estos mensajes son publicados por el servicio de canales hacia el exchange principal cuando ocurren cambios en los recursos.

Todos los mensajes incluyen un campo llamado `type` en el payload que indica el tipo de evento (es decir, la routing key).

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

## Mensajes Consumidos

El servicio escucha eventos provenientes de otros dominios (actualmente el dominio de Usuarios).

### Eventos de Usuarios (`.#`)

El servicio se suscribe al exchange de usuarios para mantener la consistencia de datos (por ejemplo, si un usuario actualiza su perfil o es eliminado).

- **Exchange:** `user.events`
- **Cola:** `channel_service_users_queue`
- **Routing Key:** `user.#` (Escucha todos los eventos que comiencen con `user.`, como `user.created`, `user.updated`, etc.)

**Procesamiento:**
Actualmente, los mensajes son recibidos y logueados por el callback en [`app/events/callbacks/users.py`](../app/events/callbacks/users.py). La lógica específica de negocio está pendiente de implementación.
