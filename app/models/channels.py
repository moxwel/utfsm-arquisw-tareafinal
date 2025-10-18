from mongoengine import Document, StringField, FloatField, BooleanField, ListField
from ..schemas.channels import Channel
from datetime import datetime


class ChannelDocument(Document):
    meta = {"collection": "channels", "index_background": True}
    owner_id = StringField(required=True)
    name = StringField(required=True)
    users = ListField(StringField(), default=[])
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
        "users": document.users,
        "channel_type": document.channel_type,
        "is_active": document.is_active,
        "created_at": datetime.fromtimestamp(document.created_at) if document.created_at else None,
        "updated_at": datetime.fromtimestamp(document.updated_at) if document.updated_at else None,
        "deleted_at": datetime.fromtimestamp(document.deleted_at) if document.deleted_at else None,
    }
    return Channel.model_validate(data)
