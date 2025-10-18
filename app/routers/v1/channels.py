from fastapi import APIRouter, HTTPException
from bson.errors import InvalidId
from mongoengine.errors import ValidationError
from ...db.querys_channels import (
    create_channel,
    get_channel_by_id,
    get_channels_by_server_id,
    update_channel,
    delete_channel,
)
from ...schemas.channels import ChannelCreate, ChannelUpdate, Channel, ChannelDelete
import logging
from ...events.conn import publish_message, publish_simple_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/channels", tags=["channels"])


@router.post("/", response_model=Channel, status_code=201)
async def add_channel(channel_data: ChannelCreate):
    """Crea un nuevo canal y lo guarda en MongoDB."""
    try:
        channel = create_channel(channel_data)
        if channel is None:
            raise HTTPException(status_code=500, detail="Error al crear el canal.")

        payload = {"channel_id": str(channel.id), "server_id": channel.server_id}
        
        try:
            await publish_message(payload, "channel.created", "channel_service_exchange")
        except Exception as e:
            logger.error(f"Error al publicar mensaje en RabbitMQ: {str(e)}")
            raise HTTPException(status_code=500, detail="Error al publicar mensaje en RabbitMQ.")

        return channel
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear el canal: {str(e)}")


@router.get("/id/{channel_id}", response_model=Channel)
async def read_channel(channel_id: str):
    """Obtiene un canal por su ID desde MongoDB."""
    try:
        channel = get_channel_by_id(channel_id)
        if channel is None:
            raise HTTPException(status_code=404, detail="Canal no encontrado.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"ID de canal inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.get("/server/{server_id}", response_model=list[Channel])
async def read_channels_by_server(server_id: str):
    """Obtiene todos los canales asociados a un servidor específico desde MongoDB."""
    try:
        channels = get_channels_by_server_id(server_id)
        return channels
    except (InvalidId, ValidationError):
        raise HTTPException(status_code=422, detail="ID de servidor inválido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.put("/id/{channel_id}", response_model=Channel)
async def modify_channel(channel_id: str, channel_update: ChannelUpdate):
    """Actualiza un canal existente en MongoDB."""
    try:
        channel = update_channel(channel_id, channel_update)
        if channel is None:
            raise HTTPException(status_code=404, detail="Canal no encontrado o sin datos para actualizar.")
        return channel
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"ID de canal inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar el canal: {str(e)}")


@router.delete("/id/{channel_id}", response_model=ChannelDelete)
async def remove_channel(channel_id: str):
    """Desactiva un canal en MongoDB (no lo elimina físicamente)."""
    try:
        success = delete_channel(channel_id)
        if not success:
            raise HTTPException(status_code=404, detail="Canal no encontrado.")
        return ChannelDelete(id=channel_id, status="desactivado")
    except (InvalidId, ValidationError) as e:
        raise HTTPException(status_code=422, detail=f"ID de canal inválido: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al desactivar el canal: {str(e)}")
