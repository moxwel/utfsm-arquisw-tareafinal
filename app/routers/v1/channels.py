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
    db_get_basic_channel_info,
    db_get_all_channels_paginated
)
from ...schemas.channels import Channel
from ...schemas.payloads import ChannelCreatePayload, ChannelUpdatePayload
from ...schemas.responses import ChannelIDResponse, ChannelBasicInfoResponse
import logging
from ...events.publish import publish_message, publish_message_main, PublishError
from ...events.conn import rabbit_clients
from ...schemas.http_responses import ErrorResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROUTER_ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Recurso no encontrado."},
    422: {"model": ErrorResponse, "description": "Entidad no procesable – datos o ID inválidos."},
    500: {"model": ErrorResponse, "description": "Error interno del servidor."},
}

router = APIRouter(prefix="/v1/channels", tags=["channels"], responses=ROUTER_ERROR_RESPONSES)

@router.post("/", response_model=Channel, status_code=201)
async def add_channel(channel_data_payload: ChannelCreatePayload):
    """Crea un nuevo canal y lo guarda en MongoDB."""
    try:
        channel = db_create_channel(channel_data_payload)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el canal.")

        payload = {"channel_id": channel.id, "name": channel.name, "owner_id": channel.owner_id, "created_at": channel.created_at}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.created")

        return channel
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al crear el canal: {str(e)}")

@router.get("/", response_model=list[ChannelBasicInfoResponse])
async def list_channels(page: int = 1, page_size: int = 10):
    """Obtiene una lista paginada de información básica de todos los canales."""
    page_size_limit = 100
    
    try:
        if page_size > page_size_limit:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"El tamaño de página no puede exceder {page_size_limit}.")
        if page < 1 or page_size < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Los parámetros de paginación deben ser mayores a 0.")

        offset = (page - 1) * page_size
        channels = db_get_all_channels_paginated(skip=offset, limit=page_size)

        return channels
    except HTTPException as exc:
        raise exc
    except Exception as e:
        logger.exception("Error interno al listar canales")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{channel_id}", response_model=Channel)
async def read_channel(channel_id: str):
    """Obtiene un canal existente por su ID."""
    try:
        channel = db_get_channel_by_id(channel_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return channel
    except (InvalidId, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de canal inválido: {exc}") from exc
    except HTTPException as exc:
        raise exc
    except Exception as exc:
        logger.exception("Error interno al obtener canal")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor") from exc

@router.put("/{channel_id}", response_model=Channel)
async def modify_channel(channel_id: str, channel_update_payload: ChannelUpdatePayload):
    """Actualiza un canal existente en MongoDB."""
    try:
        channel = db_update_channel(channel_id, channel_update_payload)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o sin datos para actualizar.")

        updated_fields = channel_update_payload.model_dump(exclude_unset=True, exclude_none=True)
        payload = {"channel_id": channel.id, "updated_fields": updated_fields, "updated_at": channel.updated_at}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.updated")

        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al actualizar el canal: {str(e)}")


@router.delete(
    "/{channel_id}",
    response_model=ChannelIDResponse,
    responses={
        409: {"model": ErrorResponse, "description": "Conflict: el canal ya estaba desactivado al momento de la solicitud."}
    }
)
async def remove_channel(channel_id: str):
    """Desactiva un canal en MongoDB (no lo elimina físicamente)."""
    try:
        channel = db_get_channel_by_id(channel_id)
        
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        
        if not channel.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El canal ya está desactivado.")
        
        channel = db_deactivate_channel(channel_id)
        
        payload = {"channel_id": channel_id, "deleted_at": channel.deleted_at}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.deleted")
        
        return ChannelIDResponse(id=channel_id, status="desactivado")
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al desactivar el canal: {str(e)}")

@router.post(
    "/{channel_id}/reactivate",
    response_model=ChannelIDResponse,
    responses={
        409: {"model": ErrorResponse, "description": "Conflict: el canal ya se encuentra activo; no requiere reactivación."}
    }
)
async def reactivate_channel(channel_id: str):
    """Reactiva un canal desactivado en MongoDB."""
    try:
        channel = db_get_channel_by_id(channel_id)
        
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")

        if channel.is_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El canal ya está activo.")
        
        channel = db_reactivate_channel(channel_id)

        payload = {"channel_id": channel.id, "reactivated_at": channel.updated_at}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.reactivated")

        return ChannelIDResponse(id=channel.id)
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al reactivar el canal: {str(e)}")

@router.get("/{channel_id}/basic", response_model=ChannelBasicInfoResponse)
async def read_channel_basic_info(channel_id: str):
    """Obtiene información básica de un canal específico desde MongoDB."""
    try:
        channel = db_get_basic_channel_info(channel_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return channel
    except (InvalidId, ValidationError) as e:   
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")