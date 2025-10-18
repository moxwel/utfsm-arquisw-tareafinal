from mongoengine.errors import DoesNotExist, ValidationError
from ..models.channels import ChannelDocument, _document_to_channel, _document_to_channel_response
from datetime import datetime
from ..schemas.channels import Channel, ChannelCreate, ChannelUpdate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_channel(channel_data: ChannelCreate) -> Channel | None:
    payload = channel_data.model_dump()
    if not payload:
        return None

    now = datetime.now().timestamp()
    if 'users' in payload and isinstance(payload['users'], list):
        payload['users'] = ",".join(payload['users'])
    document = ChannelDocument(**payload, created_at=now, updated_at=now)
    document.save()

    return _document_to_channel(document)

def get_channel_by_id(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel(document)

def get_channels_by_server_id(server_id: str) -> list[Channel]:
    if not server_id:
        return []
    return [_document_to_channel(doc) for doc in ChannelDocument.objects(server_id=server_id) if _document_to_channel(doc, str(doc.id))]

def update_channel(channel_id: str, update_data: ChannelUpdate) -> Channel | None:
    payload = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if not channel_id or not payload:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    for key, value in payload.items():
        setattr(document, key, value)
    document.updated_at = datetime.now().timestamp()
    document.save()
    return _document_to_channel(document)

def delete_channel(channel_id: str) -> bool:
    if not channel_id:
        return False
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return False
    document.is_active = False
    document.updated_at = datetime.now().timestamp()
    document.save()
    return True