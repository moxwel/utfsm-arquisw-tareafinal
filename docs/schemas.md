# Documentación de Esquemas de Datos

Esta es la documentación para los esquemas de datos utilizados en la API.

## `ChannelType` (Enum)

Enumeración para el tipo de canal.

- **Valores:**
  - `public`
  - `private`

## `ChannelMember`

Representa a un miembro de un canal.

- **Atributos:**
  - `id` (string): El ID del usuario.
  - `joined_at` (float): Timestamp de cuando el usuario se unió.

## `Channel`

El modelo de datos principal para un canal.

- **Atributos:**
  - `id` (string, opcional): El ID del canal (alias `_id` en MongoDB).
  - `name` (string): Nombre del canal.
  - `owner_id` (string): ID del propietario del canal.
  - `users` (list[`ChannelMember`]): Lista de miembros en el canal.
  - `is_active` (boolean): Indica si el canal está activo. Por defecto `True`.
  - `channel_type` (`ChannelType`): El tipo de canal. Por defecto `public`.
  - `created_at` (float): Timestamp de creación.
  - `updated_at` (float): Timestamp de la última actualización.
  - `deleted_at` (float, opcional): Timestamp de cuando fue desactivado.

## `ChannelCreate`

Esquema para crear un nuevo canal.

- **Atributos:**
  - `name` (string): Nombre del canal.
  - `owner_id` (string): ID del propietario.
  - `users` (list[string]): Lista de IDs de usuarios a añadir al canal.
  - `channel_type` (`ChannelType`): El tipo de canal. Por defecto `public`.

## `ChannelUpdate`

Esquema para actualizar un canal existente. Todos los campos son opcionales.

- **Atributos:**
  - `name` (string, opcional): Nuevo nombre del canal.
  - `owner_id` (string, opcional): Nuevo ID del propietario.
  - `channel_type` (`ChannelType`, opcional): Nuevo tipo de canal.

## `ChannelID`

Un esquema simple para devolver el ID de un canal.

- **Atributos:**
  - `id` (string): El ID del canal.

## `ChannelBasicInfo`

Esquema con información básica de un canal.

- **Atributos:**
  - `id` (string): ID del canal.
  - `name` (string): Nombre del canal.
  - `owner_id` (string): ID del propietario.
  - `channel_type` (`ChannelType`): Tipo de canal.
  - `created_at` (float): Timestamp de creación.

## `ChannelUserAction`

Esquema para acciones de usuario en un canal (añadir/eliminar).

- **Atributos:**
  - `channel_id` (string): ID del canal.
  - `user_id` (string): ID del usuario.

## `ErrorResponse`

Esquema para respuestas de error.

- **Atributos:**
  - `detail` (string): Mensaje de error detallado.
