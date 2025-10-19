from mongoengine.errors import DoesNotExist, ValidationError
from ..models.channels import ChannelDocument, _document_to_channel, _document_to_channel_basic_info
from datetime import datetime
from ..schemas.channels import Channel, ChannelCreate, ChannelUpdate, ChannelBasicInfo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def db_create_channel(channel_data: ChannelCreate) -> Channel | None:
    payload = channel_data.model_dump()
    if not payload:
        return None
    if payload["owner_id"] not in payload["users"]:
        payload["users"].append(payload["owner_id"])
    now = datetime.now().timestamp()
    document = ChannelDocument(**payload, created_at=now, updated_at=now)
    document.save()
    return _document_to_channel(document)

def db_get_channel_by_id(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel(document)

def db_get_channels_by_owner_id(owner_id: str) -> list[ChannelBasicInfo]:
    if not owner_id:
        return []
    documents = ChannelDocument.objects(owner_id=owner_id)
    return [_document_to_channel_basic_info(doc) for doc in documents]

def db_update_channel(channel_id: str, update_data: ChannelUpdate) -> Channel | None:
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

def db_deactivate_channel(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    document.is_active = False
    now = datetime.now().timestamp()
    document.deleted_at = now
    document.save()
    return _document_to_channel(document)

def db_reactivate_channel(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    now = datetime.now().timestamp()
    document.is_active = True
    document.updated_at = now
    document.save()
    return _document_to_channel(document)

def db_add_user_to_channel(channel_id: str, user_id: str) -> Channel | None:
    if not channel_id or not user_id:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    users = document.users if document.users else []
    if user_id not in users:
        users.append(user_id)
        document.users = users
        document.updated_at = datetime.now().timestamp()
        document.save()
    else:
        return None
    return _document_to_channel(document)

def db_remove_user_from_channel(channel_id: str, user_id: str) -> Channel | None:
    if not channel_id or not user_id:
        return None
    try:
        document = ChannelDocument.objects.get(id=channel_id)
    except (DoesNotExist, ValidationError):
        return None
    users = document.users if document.users else []
    if user_id in users and user_id != document.owner_id:
        users.remove(user_id)
        document.users = users
        document.updated_at = datetime.now().timestamp()
        document.save()
    else:
        return None
    return _document_to_channel(document)

def db_get_channels_by_member_id(user_id: str) -> list[ChannelBasicInfo]:
    if not user_id:
        return []
    documents = ChannelDocument.objects(users=user_id, is_active=True)
    return [_document_to_channel_basic_info(doc) for doc in documents]
