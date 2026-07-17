"""Routers públicos de datos (CRUD de endpoints VoIP).

Las operaciones de escritura (POST, PUT, DELETE) solo son aceptadas
por el nodo líder. Los seguidores redirigen al líder con 307.
"""
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

import app.core.config as cfg
from app.core.database import get_all, get_by_id, create, update, delete
from app.domain.schemas import ItemCreate, ItemResponse
from app.services.replication import replicate_to_followers

router = APIRouter()


def _ensure_leader():
    if cfg.LEADER_ID and cfg.LEADER_ID != cfg.NODE_ID:
        raise HTTPException(status_code=503, detail=f"El líder es {cfg.LEADER_ID}")
    if not cfg.IS_LEADER:
        raise HTTPException(status_code=503, detail="Este nodo no es el líder")


async def _replicate_or_raise(operation: str, *, item_id: str | None = None, data: str | None = None) -> None:
    if not await replicate_to_followers(operation, data=data, item_id=item_id):
        raise HTTPException(
            status_code=503,
            detail="Quórum de replicación fallido — líder auto-degradado",
        )


@router.post("/data", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    _ensure_leader()
    item_id = str(uuid.uuid4())
    await _replicate_or_raise("create", data=item.data, item_id=item_id)
    return create(item.data, item_id=item_id)


@router.get("/data", response_model=list[ItemResponse])
async def list_items():
    return get_all()


@router.get("/data/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    item = get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    return item


@router.put("/data/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item: ItemCreate):
    _ensure_leader()
    if not get_by_id(item_id):
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    await _replicate_or_raise("update", data=item.data, item_id=item_id)
    return update(item_id, item.data)


@router.delete("/data/{item_id}")
async def delete_item(item_id: str):
    _ensure_leader()
    if not get_by_id(item_id):
        raise HTTPException(status_code=404, detail="Registro no encontrado")
    await _replicate_or_raise("delete", item_id=item_id)
    delete(item_id)
    return {"status": "eliminado", "id": item_id}