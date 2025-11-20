from ..db import querys
from ..schemas.channels import Channel, ChannelMember
from ..schemas.payloads import ChannelUserPayload
from ..schemas.responses import ChannelBasicInfoResponse
from ..events.publish import publish_message_main
from ..events.clients import rabbit_clients
from datetime import datetime


async def add_user_to_channel(payload: ChannelUserPayload) -> Channel | None:
    """Agrega un usuario a un canal existente en MongoDB."""
    channel = querys.db_add_user_to_channel(payload.channel_id, payload.user_id)
    
    if channel:
        added_user = next((u for u in channel.users if u.id == payload.user_id), None)
        publish_payload = {"channel_id": channel.id, "user_id": payload.user_id, "added_at": added_user.joined_at if added_user else None}
        await publish_message_main(rabbit_clients["channel"], publish_payload, "channelService.v1.user.added")
    
    return channel


async def remove_user_from_channel(payload: ChannelUserPayload) -> Channel | None:
    """Elimina un usuario de un canal existente en MongoDB."""
    channel = querys.db_remove_user_from_channel(payload.channel_id, payload.user_id)
    
    if channel:
        publish_payload = {"channel_id": channel.id, "user_id": payload.user_id, "removed_at": datetime.now().timestamp()}
        await publish_message_main(rabbit_clients["channel"], publish_payload, "channelService.v1.user.removed")
    
    return channel


def get_channels_by_member(user_id: str) -> list[ChannelBasicInfoResponse]:
    """Obtiene todos los canales en los que un usuario es miembro desde MongoDB."""
    return querys.db_get_channels_by_member_id(user_id)


def get_channels_by_owner(owner_id: str) -> list[ChannelBasicInfoResponse]:
    """Obtiene todos los canales asociados a un propietario específico desde MongoDB."""
    return querys.db_get_channels_by_owner_id(owner_id)


def get_channel_member_ids(channel_id: str, page: int, page_size: int) -> list[ChannelMember] | None:
    """Obtiene los IDs de los miembros de un canal específico desde MongoDB."""
    offset = (page - 1) * page_size
    return querys.db_get_channel_member_ids(channel_id, skip=offset, limit=page_size)
