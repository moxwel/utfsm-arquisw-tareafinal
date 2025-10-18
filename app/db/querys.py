from ..schemas.item import ItemCreate, ItemRead
from mongoengine import Document, StringField, FloatField, BooleanField
from mongoengine.errors import DoesNotExist, ValidationError

collection = "items"


class ItemDocument(Document):
    meta = {"collection": collection}
    name = StringField(required=True)
    price = FloatField(required=True)
    is_offer = BooleanField(required=False, null=True)


def _document_to_item(document: ItemDocument) -> ItemRead | None:
    if not document:
        return None
    data = {
        "id": str(document.id),
        "name": document.name,
        "price": document.price,
        "is_offer": document.is_offer,
    }
    return ItemRead.model_validate(data)

def get_all_items() -> list[ItemRead]:
    return [_document_to_item(doc) for doc in ItemDocument.objects]

def create_item(item_data: ItemCreate) -> ItemRead:
    payload = item_data.model_dump(exclude={"id"})
    document = ItemDocument(**payload)
    document.save()
    return _document_to_item(document)

def get_item_by_id(item_id: str) -> ItemRead | None:
    if not item_id:
        return None
    try:
        document = ItemDocument.objects.get(id=item_id)
    except (DoesNotExist, ValidationError):
        return None
    return _document_to_item(document)
