from fastapi import APIRouter

import src.config as cfg
from src.database import get_all
from src.models import ElectionMessage

router = APIRouter()


@router.get("/health")
async def health():
    role = "follower" if cfg.LEADER_ID else "leader"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive"}


@router.post("/replicate")
async def replicate(payload: dict):
    from src.database import create, update, delete

    operation = payload.get("operation")
    if operation == "create":
        result = create(payload["data"])
        return {"status": "ok", "item": result}
    elif operation == "update":
        result = update(payload["item_id"], payload["data"])
        if result:
            return {"status": "ok", "item": result}
        return {"status": "error", "message": "item not found"}, 404
    elif operation == "delete":
        ok = delete(payload["item_id"])
        if ok:
            return {"status": "ok"}
        return {"status": "error", "message": "item not found"}, 404
    return {"status": "error", "message": "unknown operation"}, 400


@router.post("/election")
async def election(msg: ElectionMessage):
    if cfg.NODE_ID > msg.candidate_id:
        return {"response": "OK", "from": cfg.NODE_ID}
    return {"response": "IGNORE"}


@router.post("/leader-announce")
async def leader_announce(payload: dict):
    cfg.LEADER_ID = payload.get("leader_id")
    return {"status": "ack", "leader": cfg.LEADER_ID}


@router.get("/cluster/sync")
async def cluster_sync():
    items = get_all()
    return items