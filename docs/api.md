# Documentación de la API

Esta es la documentación para la API de manejo de canales y miembros.

## Canales

### `POST /v1/channels/`

Crea un nuevo canal.

- **Body (JSON):**
  ```json
  {
    "name": "string",
    "description": "string",
    "owner_id": "string"
  }
  ```
- **Respuesta Exitosa (201):**
  ```json
  {
    "id": "string",
    "name": "string",
    "description": "string",
    "owner_id": "string",
    "created_at": "string (timestamp)",
    "updated_at": "string (timestamp)",
    "is_active": "boolean",
    "users": []
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
- **Body (JSON):**
  ```json
  {
    "name": "string",
    "description": "string"
  }
  ```
- **Respuesta Exitosa (200):**
  - Devuelve el objeto del canal actualizado.

### `DELETE /v1/channels/{channel_id}`

Desactiva un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200):**
  ```json
  {
    "id": "string"
  }
  ```

### `POST /v1/channels/{channel_id}/reactivate`

Reactiva un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200):**
  - Devuelve el objeto del canal reactivado.

### `GET /v1/channels/info/{channel_id}`

Obtiene información básica de un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200):**
  ```json
  {
    "id": "string",
    "name": "string",
    "description": "string"
  }
  ```

## Miembros

### `POST /v1/members/`

Agrega un usuario a un canal.

- **Query Params:**
  - `channel_id` (string): El ID del canal.
  - `user_id` (string): El ID del usuario.
- **Respuesta Exitosa (200):**
  - Devuelve el objeto del canal con el nuevo miembro.

### `DELETE /v1/members/`

Elimina un usuario de un canal.

- **Query Params:**
  - `channel_id` (string): El ID del canal.
  - `user_id` (string): El ID del usuario.
- **Respuesta Exitosa (200):**
  - Devuelve el objeto del canal sin el miembro eliminado.

### `GET /v1/members/{user_id}`

Obtiene todos los canales en los que un usuario es miembro.

- **Parámetros de Ruta:**
  - `user_id` (string): El ID del usuario.
- **Respuesta Exitosa (200):**
  - Devuelve una lista de información básica de los canales.

### `GET /v1/members/owner/{owner_id}`

Obtiene todos los canales de los que un usuario es propietario.

- **Parámetros de Ruta:**
  - `owner_id` (string): El ID del propietario.
- **Respuesta Exitosa (200):**
  - Devuelve una lista de información básica de los canales.

### `GET /v1/members/channel/{channel_id}`

Obtiene todos los miembros de un canal.

- **Parámetros de Ruta:**
  - `channel_id` (string): El ID del canal.
- **Respuesta Exitosa (200):**
  - Devuelve una lista de los miembros del canal.
  ```json
  [
    {
      "id": "string",
      "joined_at": "string (timestamp)"
    }
  ]
  ```
