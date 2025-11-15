from mongoengine import Document, StringField, FloatField, BooleanField, ListField, EmbeddedDocument, EmbeddedDocumentField
from ..schemas.channels import Channel
from ..schemas.responses import ChannelBasicInfoResponse
from datetime import datetime


class ChannelMemberDocument(EmbeddedDocument):
    id = StringField(required=True)
    joined_at = FloatField(required=True)

class ChannelDocument(Document):
    meta = {"collection": "channels", "index_background": True}
    owner_id = StringField(required=True)
    name = StringField(required=True)
    users = ListField(EmbeddedDocumentField(ChannelMemberDocument), default=[])
    channel_type = StringField(required=True, choices=["public", "private"], default="public")
    is_active = BooleanField(required=True, default=True)
    created_at = FloatField(required=True)
    updated_at = FloatField(required=True)
    deleted_at = FloatField()

def _document_to_channel(document: ChannelDocument) -> Channel | None:
    if not document:
        return None
    data = {
        "_id": str(document.pk),
        "owner_id": document.owner_id,
        "name": document.name,
        "users": [{"id": u.id, "joined_at": u.joined_at} for u in document.users],
        "channel_type": document.channel_type,
        "is_active": document.is_active,
        "created_at": document.created_at,
        "updated_at": document.updated_at,
        "deleted_at": document.deleted_at,
    }
    return Channel.model_validate(data)

def _document_to_channel_basic_info(document: ChannelDocument) -> ChannelBasicInfoResponse | None:
    if not document:
        return None
    data = {
        "id": str(document.pk),
        "name": document.name,
        "owner_id": document.owner_id,
        "channel_type": document.channel_type,
        "created_at": document.created_at,
    }
    return ChannelBasicInfoResponse.model_validate(data)
