from ..db.querys import (
    db_create_channel,
    db_get_channel_by_id,
    db_update_channel,
    db_deactivate_channel,
    db_reactivate_channel,
    db_get_basic_channel_info,
    db_get_all_channels_paginated
)
from ..schemas.channels import Channel
from ..schemas.payloads import ChannelCreatePayload, ChannelUpdatePayload
from ..schemas.responses import ChannelIDResponse, ChannelBasicInfoResponse
from ..events.publish import publish_message_main
from ..events.clients import rabbit_clients


async def create_channel(channel_data_payload: ChannelCreatePayload) -> Channel:
    """Crea un nuevo canal y lo guarda en MongoDB."""
    channel = db_create_channel(channel_data_payload)
    
    payload = {"channel_id": channel.id, "name": channel.name, "owner_id": channel.owner_id, "created_at": channel.created_at}
    await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.created")
    
    return channel


def list_channels(page: int, page_size: int) -> list[ChannelBasicInfoResponse]:
    """Obtiene una lista paginada de información básica de todos los canales."""
    offset = (page - 1) * page_size
    channels = db_get_all_channels_paginated(skip=offset, limit=page_size)
    return channels


def get_channel(channel_id: str) -> Channel | None:
    """Obtiene un canal existente por su ID."""
    return db_get_channel_by_id(channel_id)


async def update_channel(channel_id: str, channel_update_payload: ChannelUpdatePayload) -> Channel | None:
    """Actualiza un canal existente en MongoDB."""
    channel = db_update_channel(channel_id, channel_update_payload)
    
    if channel:
        updated_fields = channel_update_payload.model_dump(exclude_unset=True, exclude_none=True)
        payload = {"channel_id": channel.id, "updated_fields": updated_fields, "updated_at": channel.updated_at}
        await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.updated")
    
    return channel


async def delete_channel(channel_id: str) -> tuple[Channel | None, Channel | None]:
    """Desactiva un canal en MongoDB (no lo elimina físicamente).
    
    Returns:
        tuple: (channel_before_delete, channel_after_delete)
    """
    channel_before = db_get_channel_by_id(channel_id)
    
    if not channel_before:
        return None, None
    
    if not channel_before.is_active:
        return channel_before, None
    
    channel_after = db_deactivate_channel(channel_id)
    
    payload = {"channel_id": channel_id, "deleted_at": channel_after.deleted_at}
    await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.deleted")
    
    return channel_before, channel_after


async def reactivate_channel(channel_id: str) -> tuple[Channel | None, bool]:
    """Reactiva un canal desactivado en MongoDB.
    
    Returns:
        tuple: (channel, was_already_active)
    """
    channel = db_get_channel_by_id(channel_id)
    
    if not channel:
        return None, False
    
    if channel.is_active:
        return channel, True
    
    channel = db_reactivate_channel(channel_id)
    
    payload = {"channel_id": channel.id, "reactivated_at": channel.updated_at}
    await publish_message_main(rabbit_clients["channel"], payload, "channelService.v1.channel.reactivated")
    
    return channel, False


def get_channel_basic_info(channel_id: str) -> ChannelBasicInfoResponse | None:
    """Obtiene información básica de un canal específico desde MongoDB."""
    return db_get_basic_channel_info(channel_id)
