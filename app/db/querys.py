from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine.queryset.visitor import Q
from ..models.channels import ChannelDocument, _document_to_channel, _document_to_channel_basic_info, ChannelMemberDocument
from datetime import datetime
from ..schemas.channels import Channel, ChannelMember
from ..schemas.payloads import ChannelUserPayload, ChannelUpdatePayload, ChannelCreatePayload
from ..schemas.responses import ChannelBasicInfoResponse
import logging
from bson import ObjectId

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def db_create_channel(channel_data: ChannelCreatePayload) -> Channel | None:
    payload = channel_data.model_dump()
    if not payload:
        return None
    
    now = datetime.now().timestamp()
    
    user_list = [{"id": payload["owner_id"], "joined_at": now, "status": "normal"}]
    
    document = ChannelDocument(**payload, users=user_list, created_at=now, updated_at=now)
    document.save()
    return _document_to_channel(document)

def db_get_all_channels_paginated(skip: int = 0, limit: int = 100) -> list[ChannelBasicInfoResponse]:
    try:
        pipeline = [
            {
                "$project": {
                    "id": {"$toString": "$_id"},
                    "name": "$name",
                    "owner_id": "$owner_id",
                    "channel_type": "$channel_type",
                    "created_at": "$created_at",
                    "user_count": {"$size": "$users"}
                }
            },
            {"$skip": skip},
            {"$limit": limit}
        ]
        aggregated_results = ChannelDocument.objects.aggregate(pipeline)
        return [ChannelBasicInfoResponse.model_validate(doc) for doc in aggregated_results]
    except Exception as e:
        logger.exception("Error al obtener canales paginados")
        return []

def db_get_channel_by_id(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        query = Q(id=channel_id)
        document = ChannelDocument.objects.get(query)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel(document)

# !! INEFICIENTE, USAR AGREGACIÓN
def db_get_channels_by_owner_id(user_id: str) -> list[ChannelBasicInfoResponse]:
    if not user_id:
        return []
    query = Q(owner_id=user_id)
    documents = ChannelDocument.objects(query)
    return [_document_to_channel_basic_info(doc) for doc in documents]

def db_update_channel(channel_id: str, update_data: ChannelUpdatePayload) -> Channel | None:
    payload = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if not channel_id or not payload:
        return None

    try:
        now = datetime.now().timestamp()
        update_fields = {f"set__{key}": value for key, value in payload.items()}
        update_fields["set__updated_at"] = now
        query = Q(id=channel_id)
        document = ChannelDocument.objects(query).modify(
            new=True, 
            **update_fields
        )
        if not document:
            return None
    except ValidationError:
        return None

    return _document_to_channel(document)

def db_deactivate_channel(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        now = datetime.now().timestamp()
        query = Q(id=channel_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            set__is_active=False,
            set__deleted_at=now
        )
        if not document:
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)

def db_reactivate_channel(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        now = datetime.now().timestamp()
        query = Q(id=channel_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            set__is_active=True,
            set__updated_at=now
        )
        if not document:
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)

def db_add_user_to_channel(channel_id: str, user_id: str) -> Channel | None:
    if not channel_id or not user_id:
        return None
    try:
        new_member = ChannelMemberDocument(id=user_id, joined_at=datetime.now().timestamp(), status="normal")
        
        query = Q(id=channel_id) & Q(users__id__ne=user_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            add_to_set__users=new_member
        )
        if not document:
            # El canal no existe o el usuario ya es miembro
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)

def db_remove_user_from_channel(channel_id: str, user_id: str) -> Channel | None:
    if not channel_id or not user_id:
        return None
    try:
        query = Q(id=channel_id) & Q(owner_id__ne=user_id) & Q(users__id=user_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            pull__users__id=user_id
        )
        if not document:
            # El canal no existe, el usuario no es miembro o es el propietario
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)

# !! INEFICIENTE, USAR AGREGACIÓN
def db_get_channels_by_member_id(user_id: str) -> list[ChannelBasicInfoResponse]:
    if not user_id:
        return []
    query = Q(users__id=user_id) & Q(is_active=True)
    documents = ChannelDocument.objects(query)
    return [_document_to_channel_basic_info(doc) for doc in documents]

# !! INEFICIENTE, USAR AGREGACIÓN
def db_get_basic_channel_info(channel_id: str) -> ChannelBasicInfoResponse | None:
    if not channel_id:
        return None
    try:
        query = Q(id=channel_id)
        document = ChannelDocument.objects.get(query)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel_basic_info(document)

def db_get_channel_member_ids(channel_id: str, skip: int = 0, limit: int = 100) -> list[ChannelMember] | None:
    if not channel_id:
        return None
    try:
        if not ChannelDocument.objects(id=channel_id).first():
            return None

        pipeline = [
            {"$match": {"_id": ObjectId(channel_id)}},
            {"$unwind": "$users"},
            {"$replaceRoot": {"newRoot": "$users"}},
            {"$skip": skip},
            {"$limit": limit}
        ]
        aggregated_results = ChannelDocument.objects.aggregate(pipeline)
        return [ChannelMember.model_validate(doc) for doc in aggregated_results]
    except (DoesNotExist, ValidationError):
        return None
    except Exception as e:
        logger.exception(f"Error al obtener miembros del canal {channel_id}")
        return None

def db_change_status(channel_id: str, user_id: str, new_status: str) -> Channel | None:
    """Cambia el status de un usuario en un canal específico.
    
    Args:
        channel_id: ID del canal
        user_id: ID del usuario
        new_status: Nuevo status ("normal", "warning", o "banned")
    
    Returns:
        Channel actualizado o None si no se pudo actualizar
    """
    if not channel_id or not user_id or not new_status:
        return None
    
    valid_statuses = ["normal", "warning", "banned"]
    if new_status not in valid_statuses:
        return None
    
    try:
        query = Q(id=channel_id) & Q(users__id=user_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            set__users__S__status=new_status
        )
        if not document:
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)