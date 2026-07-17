"""Routers públicos de datos (CRUD de endpoints VoIP).

Las operaciones de escritura (POST, PUT, DELETE) solo son aceptadas
por el nodo líder. Los seguidores redirigen al líder con 307.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

import app.core.config as cfg
from app.core.database import get_all, get_by_id, create, update, delete
from app.domain.schemas import ItemCreate, ItemUpdate, ItemResponse
from app.services.replication import replicate_to_followers

router = APIRouter()


def _ensure_leader():
    """Verifica que este nodo sea el líder actual; si no, lanza 503."""
    if cfg.LEADER_ID and cfg.LEADER_ID != cfg.NODE_ID:
        raise HTTPException(status_code=503, detail=f"El líder es {cfg.LEADER_ID}")
    if not cfg.IS_LEADER:
        raise HTTPException(status_code=503, detail="Este nodo no es el líder")


@router.post("/data", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    """Crea un nuevo endpoint VoIP (solo líder). Replica a seguidores."""
    _ensure_leader()
    local = create(item.data)
    success = await replicate_to_followers("create", data=item.data, item_id=local["id"])
    if not success:
        raise HTTPException(
            status_code=503,
            detail="Quórum de replicación fallido — líder auto-degradado",
        )
    return local


@router.get("/data", response_model=list[ItemResponse])
async def list_items():
    """Retorna todos los endpoints VoIP registrados (lectura local, cualquier nodo)."""
    return get_all()


@router.get("/data/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    """Retorna un endpoint VoIP por su UUID (cualquier nodo)."""
    item = get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return item


@router.put("/data/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item: ItemUpdate):
    """Actualiza un endpoint VoIP existente (solo líder). Replica a seguidores."""
    _ensure_leader()
    existing = get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    updated = update(item_id, item.data)
    success = await replicate_to_followers("update", data=item.data, item_id=item_id)
    if not success:
        update(item_id, existing["data"])
        raise HTTPException(
            status_code=503,
            detail="Quórum de replicación fallido — líder auto-degradado",
        )
    return updated


@router.delete("/data/{item_id}")
async def delete_item(item_id: str):
    """Elimina un endpoint VoIP (solo líder). Replica a seguidores."""
    _ensure_leader()
    existing = get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    ok = delete(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Registro no encontrado")

    success = await replicate_to_followers("delete", item_id=item_id)
    if not success:
        create(existing["data"])
        raise HTTPException(
            status_code=503,
            detail="Quórum de replicación fallido — líder auto-degradado",
        )
    return {"status": "eliminado", "id": item_id}