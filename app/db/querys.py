from mongoengine.errors import DoesNotExist, ValidationError
from mongoengine.queryset.visitor import Q
from ..models.channels import ChannelDocument, _document_to_channel, _document_to_channel_basic_info, ChannelMemberDocument
from datetime import datetime
from ..schemas.channels import Channel, ChannelMember
from ..schemas.payloads import ChannelUserPayload, ChannelUpdatePayload, ChannelCreatePayload
from ..schemas.responses import ChannelBasicInfoResponse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def db_create_channel(channel_data: ChannelCreatePayload) -> Channel | None:
    payload = channel_data.model_dump()
    if not payload:
        return None
    
    now = datetime.now().timestamp()
    
    user_ids = payload.pop("users", [])
    if payload["owner_id"] not in user_ids:
        user_ids.append(payload["owner_id"])
    
    users_with_timestamp = [ChannelMemberDocument(id=uid, joined_at=now) for uid in user_ids]

    document = ChannelDocument(**payload, users=users_with_timestamp, created_at=now, updated_at=now)
    document.save()
    return _document_to_channel(document)

def db_get_channel_by_id(channel_id: str) -> Channel | None:
    if not channel_id:
        return None
    try:
        query = Q(id=channel_id)
        document = ChannelDocument.objects.get(query)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel(document)

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
        new_member = ChannelMemberDocument(id=user_id, joined_at=datetime.now().timestamp())
        
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

def db_get_channels_by_member_id(user_id: str) -> list[ChannelBasicInfoResponse]:
    if not user_id:
        return []
    query = Q(users__id=user_id) & Q(is_active=True)
    documents = ChannelDocument.objects(query)
    return [_document_to_channel_basic_info(doc) for doc in documents]

def db_get_basic_channel_info(channel_id: str) -> ChannelBasicInfoResponse | None:
    if not channel_id:
        return None
    try:
        query = Q(id=channel_id)
        document = ChannelDocument.objects.get(query)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel_basic_info(document)

def db_get_channel_member_ids(channel_id: str) -> list[ChannelMember] | None:
    if not channel_id:
        return None
    try:
        query = Q(id=channel_id)
        document = ChannelDocument.objects.only("users").get(query)
    except (DoesNotExist, ValidationError):
        return None
    
    return [ChannelMember(id=u.id, joined_at=u.joined_at) for u in document.users]

def db_add_thread_to_channel(channel_id: str, thread_id: str) -> Channel | None:
    if not channel_id or not thread_id:
        return None
    try:
        if db_get_channel_by_thread_id(thread_id):
            # El hilo ya está asociado a un canal
            return None
        
        query = Q(id=channel_id) & Q(threads__ne=thread_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            add_to_set__threads=thread_id,
            set__updated_at=datetime.now().timestamp()
        )
        if not document:
            # El canal no existe o el hilo ya está en el canal
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)

def db_remove_thread_from_channel(channel_id: str, thread_id: str) -> Channel | None:
    if not channel_id or not thread_id:
        return None
    try:
        if not db_get_channel_by_thread_id(thread_id):
            # El hilo no está asociado a ningún canal
            return None
        
        query = Q(id=channel_id) & Q(threads=thread_id)
        document = ChannelDocument.objects(query).modify(
            new=True,
            pull__threads=thread_id,
            set__updated_at=datetime.now().timestamp()
        )
        if not document:
            # El canal no existe o el hilo no estaba en el canal
            return None
    except ValidationError:
        return None
    return _document_to_channel(document)

def db_get_channel_by_thread_id(thread_id: str) -> Channel | None:
    if not thread_id:
        return None
    try:
        query = Q(threads=thread_id)
        document = ChannelDocument.objects.get(query)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_channel(document)