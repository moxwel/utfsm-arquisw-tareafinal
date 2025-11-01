from fastapi import APIRouter, HTTPException, status
from bson.errors import InvalidId
from mongoengine.errors import ValidationError
from ...db.querys import (
    db_add_thread_to_channel,
    db_remove_thread_from_channel,
    db_get_channel_by_id,
    db_get_channel_by_thread_id,
)
from ...schemas.channels import Channel
from ...schemas.payloads import ChannelThreadPayload
from ...schemas.http_responses import ErrorResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ROUTER_ERROR_RESPONSES = {
    404: {"model": ErrorResponse, "description": "Recurso no encontrado."},
    422: {"model": ErrorResponse, "description": "Entidad no procesable – datos o ID inválidos."},
    500: {"model": ErrorResponse, "description": "Error interno del servidor."},
}

router = APIRouter(prefix="/v1/threads", tags=["threads"], responses=ROUTER_ERROR_RESPONSES)

@router.post("/", response_model=Channel)
async def add_thread_to_channel(payload: ChannelThreadPayload):
    """Agrega un hilo a un canal."""
    try:
        channel = db_add_thread_to_channel(payload.channel_id, payload.thread_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o el hilo ya existe en un canal.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al agregar el hilo al canal: {str(e)}")

@router.delete("/", response_model=Channel)
async def remove_thread_from_channel(payload: ChannelThreadPayload):
    """Elimina un hilo de un canal."""
    try:
        channel = db_remove_thread_from_channel(payload.channel_id, payload.thread_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado o el hilo no existe en el canal.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al eliminar el hilo del canal: {str(e)}")

@router.get("/channel/{channel_id}", response_model=list[str])
async def get_threads_from_channel(channel_id: str):
    """Obtiene todos los hilos de un canal."""
    try:
        channel = db_get_channel_by_id(channel_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canal no encontrado.")
        return channel.threads
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de canal inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al obtener los hilos del canal: {str(e)}")

@router.get("/{thread_id}", response_model=Channel)
async def get_channel_by_thread(thread_id: str):
    """Obtiene el canal al que pertenece un hilo."""
    try:
        channel = db_get_channel_by_thread_id(thread_id)
        if channel is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hilo no encontrado en ningún canal.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"ID de hilo inválido: {str(e)}")
    except HTTPException as exc:
        raise exc
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error al obtener el canal por hilo: {str(e)}")
