"""Routers internos del clúster (comunicación entre nodos basada en 3PC).

Endpoints consumidos exclusivamente por otros nodos para la orquestación del
consenso distribuido en tres fases, heartbeats, elecciones y sincronización.
"""
import asyncio

from fastapi import APIRouter, HTTPException

import app.core.config as cfg
from app.core.database import get_all, create, update, delete
from app.domain.schemas import ElectionMessage

router = APIRouter()

tx_buffer: dict[str, dict] = {}
_tx_lock = asyncio.Lock()


@router.get("/health")
async def health():
    role = "leader" if cfg.IS_LEADER else "follower"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive"}


# =======================================================================
#               ENDPOINTS DEL PROTOCOLO DE TRES FASES (3PC)
# =======================================================================

@router.post("/cluster/3pc/can_commit")
async def can_commit(payload: dict):
    tx_id = payload.get("tx_id")
    operation = payload.get("operation")
    if not tx_id or operation not in ["create", "update", "delete"]:
        raise HTTPException(status_code=400, detail="Estructura de transacción inválida")
    async with _tx_lock:
        tx_buffer[tx_id] = payload
    print(f"[3PC] [TX:{tx_id}] Fase CanCommit: VOTO POSITIVO para operación '{operation}'")
    return {"vote": "YES"}


@router.post("/cluster/3pc/pre_commit")
async def pre_commit(payload: dict):
    tx_id = payload.get("tx_id")
    async with _tx_lock:
        if tx_id not in tx_buffer:
            raise HTTPException(status_code=400, detail="Transacción desconocida en fase PreCommit")
    print(f"[3PC] [TX:{tx_id}] Fase PreCommit: Transacción preparada y respaldada en búfer")
    return {"status": "ACK"}


@router.post("/cluster/3pc/do_commit")
async def do_commit(payload: dict):
    tx_id = payload.get("tx_id")
    async with _tx_lock:
        if tx_id not in tx_buffer:
            raise HTTPException(status_code=400, detail="Transacción no encontrada para consolidación")
        tx_data = tx_buffer.pop(tx_id)

    operation = tx_data.get("operation")
    item_id = tx_data.get("item_id")
    data = tx_data.get("data")

    print(f"[3PC] [TX:{tx_id}] Fase DoCommit: Consolidando '{operation}' de forma definitiva")

    if operation == "create":
        result = create(data, item_id=item_id)
        return {"status": "committed", "item": result}
    elif operation == "update":
        result = update(item_id, data)
        if result:
            return {"status": "committed", "item": result}
        raise HTTPException(status_code=404, detail="Registro no encontrado en base de datos")
    elif operation == "delete":
        ok = delete(item_id)
        if ok:
            return {"status": "committed"}
        raise HTTPException(status_code=404, detail="Registro no encontrado en base de datos")


@router.post("/cluster/3pc/abort")
async def abort(payload: dict):
    tx_id = payload.get("tx_id")
    async with _tx_lock:
        if tx_id in tx_buffer:
            tx_buffer.pop(tx_id)
            print(f"[3PC] [TX:{tx_id}] Transacción abortada exitosamente. Búfer limpio.")
    return {"status": "aborted"}

# =======================================================================


@router.post("/election")
async def election(msg: ElectionMessage):
    """Recibe un mensaje de elección Bully."""
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
    """Retorna el listado completo de endpoints VoIP (sincronización total)."""
    items = get_all()
    return items
