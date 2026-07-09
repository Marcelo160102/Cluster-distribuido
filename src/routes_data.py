from fastapi import APIRouter, HTTPException

import src.config as cfg
from src.database import get_all, get_by_id, create, update, delete
from src.models import ItemCreate, ItemUpdate, ItemResponse
from src.replication import replicate_to_followers

router = APIRouter()


@router.post("/data", response_model=ItemResponse)
async def create_item(item: ItemCreate):
    if cfg.LEADER_ID and cfg.LEADER_ID != cfg.NODE_ID:
        raise HTTPException(status_code=503, detail=f"Leader is {cfg.LEADER_ID}")

    if not cfg.LEADER_ID and cfg.NODE_ID != sorted(cfg.PEERS + [cfg.NODE_ID])[-1]:
        raise HTTPException(status_code=503, detail="This node is not the leader")

    local = create(item.data)
    success = await replicate_to_followers("create", data=item.data, item_id=local["id"])
    if not success:
        raise HTTPException(
            status_code=503,
            detail="Replication quorum failed — leader auto-degraded",
        )
    return local


@router.get("/data", response_model=list[ItemResponse])
async def list_items():
    return get_all()


@router.get("/data/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    item = get_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/data/{item_id}", response_model=ItemResponse)
async def update_item(item_id: str, item: ItemUpdate):
    if cfg.LEADER_ID and cfg.LEADER_ID != cfg.NODE_ID:
        raise HTTPException(status_code=503, detail=f"Leader is {cfg.LEADER_ID}")

    if not cfg.LEADER_ID and cfg.NODE_ID != sorted(cfg.PEERS + [cfg.NODE_ID])[-1]:
        raise HTTPException(status_code=503, detail="This node is not the leader")

    existing = get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    updated = update(item_id, item.data)
    success = await replicate_to_followers("update", data=item.data, item_id=item_id)
    if not success:
        update(item_id, existing["data"])
        raise HTTPException(
            status_code=503,
            detail="Replication quorum failed — leader auto-degraded",
        )
    return updated


@router.delete("/data/{item_id}")
async def delete_item(item_id: str):
    if cfg.LEADER_ID and cfg.LEADER_ID != cfg.NODE_ID:
        raise HTTPException(status_code=503, detail=f"Leader is {cfg.LEADER_ID}")

    if not cfg.LEADER_ID and cfg.NODE_ID != sorted(cfg.PEERS + [cfg.NODE_ID])[-1]:
        raise HTTPException(status_code=503, detail="This node is not the leader")

    existing = get_by_id(item_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")

    ok = delete(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")

    success = await replicate_to_followers("delete", item_id=item_id)
    if not success:
        create(existing["data"])
        raise HTTPException(
            status_code=503,
            detail="Replication quorum failed — leader auto-degraded",
        )
    return {"status": "deleted", "id": item_id}