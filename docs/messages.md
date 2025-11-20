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

### Eventos de Usuarios

El servicio se suscribe al exchange de usuarios para mantener la consistencia de datos (por ejemplo, si un usuario actualiza su perfil o es eliminado).

- **Exchange:** `user.events`
- **Cola:** `channel_service_users_queue`
- **Routing Key:** `user.#` (Escucha todos los eventos que comiencen con `user.`, como `user.created`, `user.updated`, etc.)

**Procesamiento:**
Actualmente, los mensajes son recibidos y logueados por el callback en [`app/events/callbacks/users.py`](../app/events/callbacks/users.py). La lógica específica de negocio está pendiente de implementación.

### Eventos de Moderación

El servicio se suscribe al exchange de moderación para procesar acciones de moderación sobre usuarios en canales.

- **Exchange:** `moderation_events` (configurado vía `MODERATION_RABBITMQ_EXCHANGE`)
- **Cola:** `channel_service_moderation_queue` (configurado vía `MODERATION_RABBITMQ_QUEUE`)
- **Routing Key:** `moderation.#` (Escucha todos los eventos que comiencen con `moderation.`)

**Procesamiento:**
Los mensajes son procesados por el callback en [`app/events/callbacks/moderation.py`](../app/events/callbacks/moderation.py).

Dependiendo del `event_type`, se realizan diferentes acciones:

#### `moderation.warning`

- **Descripción:** Marca a un usuario con estado de advertencia en un canal específico.
- **Payload minimo esperado:**
  ```json
  {
    "event_type": "moderation.warning",
    "data": {
      "user_id": "string",
      "channel_id": "string"
    }
  }
  ```
- **Acción:** Cambia el estado `status` del usuario en el canal a `warning`.

#### `moderation.user_banned`

- **Descripción:** Banea a un usuario de un canal específico.
- **Payload minimo esperado:**
  ```json
  {
    "event_type": "moderation.user_banned",
    "data": {
      "user_id": "string",
      "channel_id": "string"
    }
  }
  ```
- **Acción:** Cambia el estado `status` del usuario en el canal a `banned`.

#### `moderation.user_unbanned`

- **Descripción:** Desbanea a un usuario de un canal específico, restaurándolo a estado normal.
- **Payload minimo esperado:**
  ```json
  {
    "event_type": "moderation.user_unbanned",
    "data": {
      "user_id": "string",
      "channel_id": "string"
    }
  }
  ```
- **Acción:** Cambia el estado `status` del usuario en el canal a `normal`.
