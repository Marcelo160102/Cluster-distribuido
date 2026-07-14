"""Routers internos del clúster (comunicación entre nodos basada en 3PC).

Endpoints consumidos exclusivamente por otros nodos para la orquestación del
consenso distribuido en tres fases, heartbeats, elecciones y sincronización.
"""
from fastapi import APIRouter, HTTPException

import app.core.config as cfg
from app.core.database import get_all
from app.domain.schemas import ElectionMessage

router = APIRouter()

# Búfer en memoria para guardar de manera aislada los datos en fase de preparación (PreCommit)
tx_buffer: dict[str, dict] = {}


@router.get("/health")
async def health():
    """Responde con el estado actual del nodo (usado por heartbeats de peers)."""
    role = "leader" if cfg.IS_LEADER else "follower"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive"}


# =======================================================================
#               ENDPOINTS DEL PROTOCOLO DE TRES FASES (3PC)
# =======================================================================

@router.post("/cluster/3pc/can_commit")
async def can_commit(payload: dict):
    """Fase 1 (3PC): Verifica disponibilidad de recursos y valida la carga útil.

    No altera la tabla activa. Si pasa las validaciones, responde afirmativamente.
    """
    tx_id = payload.get("tx_id")
    operation = payload.get("operation")
    
    if not tx_id or operation not in ["create", "update", "delete"]:
        raise HTTPException(status_code=400, detail="Estructura de transacción inválida")
    
    # Aquí irían verificaciones de recursos o bloqueos preventivos (ej. validar si existe el UUID)
    # Si todo está en orden, guardamos en el búfer inicial y votamos 'Sí' (HTTP 200)
    tx_buffer[tx_id] = payload
    print(f"[3PC] [TX:{tx_id}] Fase CanCommit: VOTO POSITIVO para operación '{operation}'")
    return {"vote": "YES"}


@router.post("/cluster/3pc/pre_commit")
async def pre_commit(payload: dict):
    """Fase 2 (3PC): Guarda la información en el log temporal o búfer seguro.

    Elimina la incertidumbre bloqueante. El nodo se compromete a que puede confirmar.
    """
    tx_id = payload.get("tx_id")
    if tx_id not in tx_buffer:
        raise HTTPException(status_code=400, detail="Transacción desconocida en fase PreCommit")
    
    print(f"[3PC] [TX:{tx_id}] Fase PreCommit: Transacción preparada y respaldada en búfer")
    return {"status": "ACK"}


@router.post("/cluster/3pc/do_commit")
async def do_commit(payload: dict):
    """Fase 3 (3PC): Ejecuta la confirmación final transfiriendo los datos a la base de datos."""
    from app.core.database import create, update, delete

    tx_id = payload.get("tx_id")
    if tx_id not in tx_buffer:
        raise HTTPException(status_code=400, detail="Transacción no encontrada para consolidación")
    
    tx_data = tx_buffer.pop(tx_id)  # Extraemos y limpiamos el búfer
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
    """Cancela la transacción distribuida y libera los recursos del búfer."""
    tx_id = payload.get("tx_id")
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
