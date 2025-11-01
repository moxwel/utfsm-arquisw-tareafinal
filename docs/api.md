# Documentación de la API

Esta es la documentación para la API de manejo de canales y miembros.

## Canales

### `POST /v1/channels/`

Crea un nuevo canal.

- **Body (`ChannelCreatePayload`):**
  ```json
  {
    "name": "string",
    "owner_id": "string",
    "users": ["string"],
    "channel_type": "public"
  }
  ```
- **Respuesta Exitosa (201, `Channel`):**
  ```json
  {
    "id": "string",
    "name": "string",
    "owner_id": "string",
    "users": [
      {
        "id": "string",
        "joined_at": "float"
      }
    ],
    "threads": [],
    "is_active": true,
    "channel_type": "public",
    "created_at": "float",
    "updated_at": "float",
    "deleted_at": null
  }
  ```

### `GET /v1/channels/{channel_id}`

Obtiene un canal por su ID.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200):**
  - Devuelve el objeto completo del canal.

### `PUT /v1/channels/{channel_id}`

Actualiza un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Body (`ChannelUpdatePayload`):**
  ```json
  {
    "name": "string",
    "owner_id": "string",
    "channel_type": "private"
  }
  ```
- **Respuesta Exitosa (200, `Channel`):**
  - Devuelve el objeto del canal actualizado.

### `DELETE /v1/channels/{channel_id}`

Desactiva un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200, `ChannelIDResponse`):**
  ```json
  {
    "id": "string",
    "status": "desactivado"
  }
  ```

### `POST /v1/channels/{channel_id}/reactivate`

Reactiva un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200, `ChannelIDResponse`):**
  - Devuelve el ID del canal reactivado.

### `GET /v1/channels/{channel_id}/basic`

Obtiene información básica de un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200, `ChannelBasicInfoResponse`):**
  ```json
  {
    "id": "string",
    "name": "string",
    "owner_id": "string",
    "channel_type": "public",
    "created_at": "float"
  }
  ```

## Miembros

### `POST /v1/members/`

Agrega un usuario a un canal.

- **Body (`ChannelUserPayload`):**
  ```json
  {
    "channel_id": "string",
    "user_id": "string"
  }
  ```
- **Respuesta Exitosa (200, `Channel`):**
  - Devuelve el objeto del canal con el nuevo miembro.

### `DELETE /v1/members/`

Elimina un usuario de un canal.

- **Body (`ChannelUserPayload`):**
  ```json
  {
    "channel_id": "string",
    "user_id": "string"
  }
  ```
- **Respuesta Exitosa (200, `Channel`):**
  - Devuelve el objeto del canal sin el miembro eliminado.

### `GET /v1/members/{user_id}`

Obtiene todos los canales en los que un usuario es miembro.

- **Parámetros de Ruta:**
  - `user_id` (string): El ID del usuario.
- **Respuesta Exitosa (200, `list[ChannelBasicInfoResponse]`):**
  - Devuelve una lista de información básica de los canales.

### `GET /v1/members/owner/{owner_id}`

Obtiene todos los canales de los que un usuario es propietario.

- **Parámetros de Ruta:**
  - `owner_id` (string): El ID del propietario.
- **Respuesta Exitosa (200, `list[ChannelBasicInfoResponse]`):**
  - Devuelve una lista de información básica de los canales.

### `GET /v1/members/channel/{channel_id}`

Obtiene todos los miembros de un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200, `list[ChannelMember]`):**
  - Devuelve una lista de los miembros del canal.
  ```json
  [
    {
      "id": "string",
      "joined_at": "float"
    }
  ]
  ```

## Hilos

### `POST /v1/threads/`

Agrega un hilo a un canal.

- **Body (`ChannelThreadPayload`):**
  ```json
  {
    "channel_id": "string",
    "thread_id": "string"
  }
  ```
- **Respuesta Exitosa (200, `Channel`):**
  - Devuelve el objeto del canal actualizado con el nuevo hilo.

### `DELETE /v1/threads/`

Elimina un hilo de un canal.

- **Body (`ChannelThreadPayload`):**
  ```json
  {
    "channel_id": "string",
    "thread_id": "string"
  }
  ```
- **Respuesta Exitosa (200, `Channel`):**
  - Devuelve el objeto del canal actualizado sin el hilo.

### `GET /v1/threads/channel/{channel_id}`

Obtiene todos los hilos de un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200, `list[string]`):**
  - Devuelve una lista de IDs de los hilos del canal.

### `GET /v1/threads/{thread_id}`

Obtiene el canal al que pertenece un hilo.

- **Parámetros de Ruta:**
  - `thread_id` (string): El ID del hilo.
- **Respuesta Exitosa (200, `Channel`):**
  - Devuelve el objeto del canal que contiene el hilo.
