from fastapi import APIRouter, HTTPException
from bson.errors import InvalidId
from ..db.querys import get_all_items, create_item, get_item_by_id
from ..models.item import Item

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=list[Item])
def read_items():
    """Obtiene todos los items almacenados en MongoDB."""
    try:
        return get_all_items()
    except Exception:
        raise HTTPException(status_code=500, detail="error al obtener items")

@router.post("/", response_model=Item, status_code=201)
def add_item(item: Item):
    """Crea un nuevo item y lo guarda en MongoDB."""
    try:
        return create_item(item)
    except InvalidId:
        raise HTTPException(status_code=422, detail="improcesable")
    except Exception:
        raise HTTPException(status_code=500, detail="error al crear item")

@router.get("/id")
def read_item_no_id():
    """Manejo de error para cuando no se proporciona un ID."""
    raise HTTPException(status_code=400, detail="se requiere id")

@router.get("/id/{item_id}", response_model=Item | None)
def read_item(item_id: str):
    """Obtiene un item por su ID desde MongoDB."""
    print(f"Obteniendo item con ID: {item_id}")
    try:
        item = get_item_by_id(item_id)
    except InvalidId:
        raise HTTPException(status_code=422, detail="improcesable")
    except Exception:
        raise HTTPException(status_code=500, detail="error interno")
    if item is None:
        raise HTTPException(status_code=404, detail="item no encontrado")
    return item