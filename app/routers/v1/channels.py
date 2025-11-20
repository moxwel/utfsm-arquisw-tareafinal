from fastapi import APIRouter, HTTPException, status
from bson.errors import InvalidId
from mongoengine.errors import ValidationError
import logging
from ...schemas.channels import Channel
from ...schemas.payloads import ChannelCreatePayload, ChannelUpdatePayload
from ...schemas.responses import ChannelIDResponse, ChannelBasicInfoResponse
from ...schemas.http_responses import ErrorResponse
from ...events.publish import PublishError
from ...controllers import channels

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
        channel = await channels.create_channel(channel_data_payload)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al crear el canal.")
        return channel
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
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"El tamaño de página no puede exceder {page_size_limit}.")
        if page < 1 or page_size < 1:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Los parámetros de paginación deben ser mayores a 0.")
        
        return channels.list_channels(page, page_size)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error interno al listar canales")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")

@router.get("/{channel_id}", response_model=Channel)
async def read_channel(channel_id: str):
    """Obtiene un canal existente por su ID."""
    try:
        channel = channels.get_channel(channel_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return channel
    except (InvalidId, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {exc}") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error interno al obtener canal")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor") from exc

@router.put("/{channel_id}", response_model=Channel)
async def modify_channel(channel_id: str, channel_update_payload: ChannelUpdatePayload):
    """Actualiza un canal existente en MongoDB."""
    try:
        channel = await channels.update_channel(channel_id, channel_update_payload)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o sin datos para actualizar.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException:
        raise
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
        channel_before, channel_after = await channels.delete_channel(channel_id)
        
        if channel_before is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        
        if channel_after is None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El canal ya está desactivado.")
        
        return ChannelIDResponse(id=channel_id, status="desactivado")
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException:
        raise
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
        channel, was_already_active = await channels.reactivate_channel(channel_id)
        
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        
        if was_already_active:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El canal ya está activo.")
        
        return ChannelIDResponse(id=channel.id)
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException:
        raise
    except PublishError as e:
        logger.error(f"Error de publicación en RabbitMQ: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error de publicación en RabbitMQ.")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al reactivar el canal: {str(e)}")

@router.get("/{channel_id}/basic", response_model=ChannelBasicInfoResponse)
async def read_channel_basic_info(channel_id: str):
    """Obtiene información básica de un canal específico desde MongoDB."""
    try:
        channel = channels.get_channel_basic_info(channel_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return channel
    except (InvalidId, ValidationError) as e:   
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error interno del servidor: {str(e)}")