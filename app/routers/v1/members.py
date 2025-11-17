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
    db_reactivate_channel,
    db_get_channel_member_ids,
)
from ...schemas.channels import Channel, ChannelMember
from ...schemas.payloads import ChannelCreatePayload, ChannelUpdatePayload, ChannelUserPayload
from ...schemas.responses import ChannelIDResponse, ChannelBasicInfoResponse
import logging
from ...events.publish import publish_message, publish_message_main, PublishError
from ...events.conn import rabbit_clients
from ...schemas.http_responses import ErrorResponse
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROUTER_ERROR_RESPONSES = {
    422: {"model": ErrorResponse, "description": "Entidad no procesable – datos o ID inválidos."},
    500: {"model": ErrorResponse, "description": "Error interno del servidor."},
}

router = APIRouter(prefix="/v1/members", tags=["members"], responses=ROUTER_ERROR_RESPONSES)

@router.post(
    "/",
    response_model=Channel,
    responses={
        404: {"model": ErrorResponse, "description": "Recurso no encontrado."}
    }
)
async def add_user_to_channel(payload: ChannelUserPayload):
    """Agrega un usuario a un canal existente en MongoDB."""
    try:
        channel = db_add_user_to_channel(payload.channel_id, payload.user_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o usuario ya en el canal.")
        added_user = next((u for u in channel.users if u.id == payload.user_id), None)
        payload = {"channel_id": channel.id, "user_id": payload.user_id, "added_at": added_user.joined_at if added_user else None}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.user.added")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al agregar usuario al canal: {str(e)}")
    
@router.delete(
    "/",
    response_model=Channel,
    responses={
        404: {"model": ErrorResponse, "description": "Recurso no encontrado."}
    }
)
async def remove_user_from_channel(payload: ChannelUserPayload):
    """Elimina un usuario de un canal existente en MongoDB."""
    try:
        channel = db_remove_user_from_channel(payload.channel_id, payload.user_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado, el usuario no está en el canal o es el propietario.")
        payload = {"channel_id": channel.id, "user_id": payload.user_id, "removed_at": datetime.now().timestamp()}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.user.removed")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al eliminar usuario del canal: {str(e)}")

@router.get("/{user_id}", response_model=list[ChannelBasicInfoResponse])
async def read_channels_by_member(user_id: str):
    """Obtiene todos los canales en los que un usuario es miembro desde MongoDB."""
    try:
        channels = db_get_channels_by_member_id(user_id)
        return channels
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de usuario inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

@router.get("/owner/{owner_id}", response_model=list[ChannelBasicInfoResponse])
async def read_channels_by_owner(owner_id: str):
    """Obtiene todos los canales asociados a un propietario específico desde MongoDB."""
    try:
        channels = db_get_channels_by_owner_id(owner_id)
        return channels
    except (InvalidId, ValidationError):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="ID de servidor inválido.")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

@router.get(
    "/channel/{channel_id}",
    response_model=list[ChannelMember],
    responses={
        404: {"model": ErrorResponse, "description": "Recurso no encontrado."}
    }
)
async def read_channel_member_ids(channel_id: str, page: int = 1, page_size: int = 100):
    """Obtiene los IDs de los miembros de un canal específico desde MongoDB."""
    page_size_limit = 100
    try:
        if page_size > page_size_limit:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"El tamaño de página no puede exceder {page_size_limit}.")
        if page < 1 or page_size < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Los parámetros de paginación deben ser mayores a 0.")
        
        offset = (page - 1) * page_size
        member_ids = db_get_channel_member_ids(channel_id, skip=offset, limit=page_size)
        if member_ids is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return member_ids
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")