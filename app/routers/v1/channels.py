from fastapi import APIRouter, HTTPException, status
from bson.errors import InvalidId
from mongoengine.errors import ValidationError
from ...db.querys import (
    create_channel,
    get_channel_by_id,
    get_channels_by_owner_id,
    update_channel,
    delete_channel,
    db_add_user_to_channel,
    db_remove_user_from_channel,
    get_channels_by_member_id,
    db_reactivate_channel
)
from ...schemas.channels import ChannelCreate, ChannelUpdate, Channel, ChannelID, AddDeleteUserChannel
import logging
from ...events.conn import publish_message, publish_message_main, PublishError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/channels", tags=["channels"])

@router.post("/", response_model=Channel, status_code=201)
async def add_channel(channel_data: ChannelCreate):
    """Crea un nuevo canal y lo guarda en MongoDB."""
    try:
        channel = create_channel(channel_data)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el canal.")

        payload = {"channel_id": channel.id, "name": channel.name, "owner_id": channel.owner_id, "created_at": channel.created_at}
        await publish_message_main(payload, "channel.created")

        return channel
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el canal: {str(e)}")


@router.get("/id/{channel_id}", response_model=Channel)
async def read_channel(channel_id: str):
    try:
        channel = get_channel_by_id(channel_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return channel
    except (InvalidId, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {exc}") from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        logger.exception("Error interno al obtener canal")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor") from exc

@router.get("/owner/{owner_id}", response_model=list[Channel])
async def read_channels_by_owner(owner_id: str):
    """Obtiene todos los canales asociados a un propietario específico desde MongoDB."""
    try:
        channels = get_channels_by_owner_id(owner_id)
        return channels
    except (InvalidId, ValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID de servidor inválido.")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")


@router.put("/id/{channel_id}", response_model=Channel)
async def modify_channel(channel_id: str, channel_update: ChannelUpdate):
    """Actualiza un canal existente en MongoDB."""
    try:
        channel = update_channel(channel_id, channel_update)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o sin datos para actualizar.")

        updated_fields = channel_update.model_dump(exclude_unset=True, exclude_none=True)
        payload = {"channel_id": channel.id, "updated_fields": updated_fields, "updated_at": channel.updated_at}
        await publish_message_main(payload, "channel.updated")

        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar el canal: {str(e)}")


@router.delete("/id/{channel_id}", response_model=ChannelID)
async def remove_channel(channel_id: str):
    """Desactiva un canal en MongoDB (no lo elimina físicamente)."""
    try:
        channel = get_channel_by_id(channel_id)
        
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        
        if not channel.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El canal ya está desactivado.")
        
        channel = delete_channel(channel_id)
        
        payload = {"channel_id": channel_id, "deleted_at": channel.deleted_at}
        await publish_message_main(payload, "channel.deleted")
        
        return ChannelID(id=channel_id, status="desactivado")
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al desactivar el canal: {str(e)}")

@router.post("/reactivate/{channel_id}", response_model=ChannelID)
async def reactivate_channel(channel_id: str):
    """Reactiva un canal desactivado en MongoDB."""
    try:
        channel = get_channel_by_id(channel_id)
        
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")

        if channel.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El canal ya está activo.")
        
        channel = db_reactivate_channel(channel_id)

        payload = {"channel_id": channel.id, "reactivated_at": channel.updated_at}
        await publish_message_main(payload, "channel.reactivated")

        return ChannelID(id=channel.id)
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al reactivar el canal: {str(e)}")

@router.post("/add_user", response_model=Channel)
async def add_user_to_channel(channel_id: str, user_id: str):
    """Agrega un usuario a un canal existente en MongoDB."""
    try:
        channel = db_add_user_to_channel(channel_id, user_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o usuario ya en el canal.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al agregar usuario al canal: {str(e)}")
    
@router.post("/remove_user", response_model=Channel)
async def remove_user_from_channel(channel_id: str, user_id: str):
    """Elimina un usuario de un canal existente en MongoDB."""
    try:
        channel = db_remove_user_from_channel(channel_id, user_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o usuario no está en el canal.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al eliminar usuario del canal: {str(e)}")

@router.get("/member/user/{user_id}", response_model=list[Channel])
async def read_channels_by_member(user_id: str):
    """Obtiene todos los canales en los que un usuario es miembro desde MongoDB."""
    try:
        channels = get_channels_by_member_id(user_id)
        return channels
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de usuario inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")
