"""Routers internos del clúster (comunicación entre nodos).

Estos endpoints NO son públicos. Son consumidos exclusivamente por
otros nodos del clúster para healthchecks, replicación, elección
y sincronización de datos.
"""
from fastapi import APIRouter

import app.core.config as cfg
from app.core.database import get_all
from app.domain.schemas import ElectionMessage

router = APIRouter()


@router.get("/health")
async def health():
    """Responde con el estado actual del nodo (usado por heartbeats de peers)."""
    role = "leader" if cfg.IS_LEADER else "follower"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive"}


@router.post("/replicate")
async def replicate(payload: dict):
    """Recibe una operación de replicación desde el líder y la persiste localmente."""
    from app.core.database import create, update, delete

    operation = payload.get("operation")
    if operation == "create":
        result = create(payload["data"])
        return {"status": "ok", "item": result}
    elif operation == "update":
        result = update(payload["item_id"], payload["data"])
        if result:
            return {"status": "ok", "item": result}
        return {"status": "error", "message": "registro no encontrado"}, 404
    elif operation == "delete":
        ok = delete(payload["item_id"])
        if ok:
            return {"status": "ok"}
        return {"status": "error", "message": "registro no encontrado"}, 404
    return {"status": "error", "message": "operación desconocida"}, 400


@router.post("/election")
async def election(msg: ElectionMessage):
    """Recibe un mensaje de elección Bully.

    Responde OK si el nodo local tiene mayor ID que el candidato,
    indicando que él tomará el control de la elección.
    """
    if cfg.NODE_ID > msg.candidate_id:
        return {"response": "OK", "from": cfg.NODE_ID}
    return {"response": "IGNORE"}


@router.post("/leader-announce")
async def leader_announce(payload: dict):
    """Recibe el anuncio de un nuevo líder y actualiza LEADER_ID local."""
    cfg.LEADER_ID = payload.get("leader_id")
    return {"status": "ack", "leader": cfg.LEADER_ID}


@router.get("/cluster/sync")
async def cluster_sync():
    """Retorna el listado completo de endpoints VoIP (sincronización total).

    Usado por nodos recuperados para descargar todo el estado del líder
    en una sola llamada.
    """
    items = get_all()
    return items