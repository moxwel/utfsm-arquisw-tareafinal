from pydantic import BaseModel

class Item(BaseModel):
    id: str | None = None
    name: str
    price: float
    is_offer: bool | None = None
