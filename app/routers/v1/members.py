from fastapi import APIRouter, HTTPException, status
from bson.errors import InvalidId
from mongoengine.errors import ValidationError
from ...db.querys import (
    db_create_channel,
    db_get_channel_by_id,
    db_get_channels_by_owner_id,
    db_update_channel,
    db_deactivate_channel,
    db_add_user_to_channel,
    db_remove_user_from_channel,
    db_get_channels_by_member_id,
    db_reactivate_channel
)
from ...schemas.channels import ChannelCreate, ChannelUpdate, Channel, ChannelID, ChannelUserAction, ChannelBasicInfo
import logging
from ...events.conn import publish_message, publish_message_main, PublishError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/members", tags=["members"])

@router.post("/", response_model=Channel)
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
    
@router.delete("/", response_model=Channel)
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

@router.get("/{user_id}", response_model=list[ChannelBasicInfo])
async def read_channels_by_member(user_id: str):
    """Obtiene todos los canales en los que un usuario es miembro desde MongoDB."""
    try:
        channels = db_get_channels_by_member_id(user_id)
        return channels
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de usuario inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

@router.get("/owner/{owner_id}", response_model=list[ChannelBasicInfo])
async def read_channels_by_owner(owner_id: str):
    """Obtiene todos los canales asociados a un propietario específico desde MongoDB."""
    try:
        channels = db_get_channels_by_owner_id(owner_id)
        return channels
    except (InvalidId, ValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ID de servidor inválido.")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")
