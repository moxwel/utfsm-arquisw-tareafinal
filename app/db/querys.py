from .conn import get_database
from ..models.item import Item
from bson import ObjectId

collection = "items"

def _document_to_item(document: dict) -> Item:
    if not document:
        return None
    data = {
        "id": str(document.get("_id")),
        "name": document.get("name"),
        "price": document.get("price"),
        "is_offer": document.get("is_offer"),
    }
    return Item(**data)

# ===================================

def get_all_items() -> list[Item]:
    db = get_database()
    items_cursor = db[collection].find()
    return [_document_to_item(doc) for doc in items_cursor]

def create_item(item_data: Item) -> Item:
    db = get_database()
    payload = item_data.model_dump(exclude_none=True, exclude={"id"})
    result = db[collection].insert_one(payload)
    new_item_doc = db[collection].find_one({"_id": result.inserted_id})
    return _document_to_item(new_item_doc)

def get_item_by_id(item_id: str) -> Item | None:
    db = get_database()
    document = db[collection].find_one({"_id": ObjectId(item_id)})
    return _document_to_item(document)
