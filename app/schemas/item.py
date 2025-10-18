#crear itemcreate e itemread
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
class ItemCreate(BaseModel):
    name: str = Field(..., title="Nombre del ítem", max_length=100)
    price: float = Field(..., gt=0, title="Precio del ítem")
    is_offer: Optional[bool] = Field(None, title="Indica si el ítem está en oferta")
class ItemRead(BaseModel):
    id: str = Field(..., title="ID del ítem")
    name: str = Field(..., title="Nombre del ítem", max_length=100)
    price: float = Field(..., gt=0, title="Precio del ítem")
    is_offer: Optional[bool] = Field(None, title="Indica si el ítem está en oferta")
    created_at: Optional[datetime] = Field(None, title="Fecha de creación del ítem")
    updated_at: Optional[datetime] = Field(None, title="Fecha de última actualización del ítem")
    deleted_at: Optional[datetime] = Field(None, title="Fecha de eliminación del ítem")

