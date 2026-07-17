"""Motor de replicación del clúster basado en Consenso 3PC.

El líder coordina de manera no bloqueante las fases CanCommit, PreCommit y DoCommit
antes de consolidar cualquier cambio en las bases de datos locales o de los seguidores.
"""
import asyncio
import uuid
import app.core.config as cfg
from app.services.node_client import send_3pc_phase

QUORUM = 2  # votos mínimos (líder + al menos 1 seguidor)


async def _run_3pc_phase(peers: list[str], phase: str, payload: dict) -> int:
    """Envía fase 3PC a todos los peers y retorna cuántos respondieron OK (incluye al líder)."""
    tasks = [send_3pc_phase(peer, phase=phase, payload=payload) for peer in peers]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return 1 + sum(1 for res in results if res is True)


async def replicate_to_followers(operation: str, data: str | None = None, item_id: str | None = None) -> bool:
    """Coordina la replicación distribuida mediante el protocolo 3PC."""
    peers = [p for p in cfg.PEERS]

    tx_id = str(uuid.uuid4())
    payload = {
        "tx_id": tx_id,
        "operation": operation,
        "data": data,
        "item_id": item_id
    }

    # FASE 1: CAN-COMMIT
    votes_yes = await _run_3pc_phase(peers, "can_commit", payload)
    if votes_yes < QUORUM:
        print(f"[3PC] [TX:{tx_id}] Abortando: No se alcanzó el quórum en CanCommit.")
        await abort_transaction(peers, tx_id)
        return False

    # FASE 2: PRE-COMMIT
    acks = await _run_3pc_phase(peers, "pre_commit", {"tx_id": tx_id})
    if acks < QUORUM:
        print(f"[3PC] [TX:{tx_id}] Abortando: Fallo en fase de preparación PreCommit.")
        await abort_transaction(peers, tx_id)
        return False

    # FASE 3: DO-COMMIT
    results = await asyncio.gather(
        *[send_3pc_phase(peer, phase="do_commit", payload={"tx_id": tx_id}) for peer in peers],
        return_exceptions=True,
    )
    for peer, res in zip(peers, results):
        if res is not True:
            print(f"[3PC] [TX:{tx_id}] DoCommit FALLÓ en {peer}")

    return True


async def abort_transaction(peers: list[str], tx_id: str):
    """Notifica de manera asíncrona la cancelación a todos los nodos."""
    tasks = [send_3pc_phase(peer, phase="abort", payload={"tx_id": tx_id}) for peer in peers]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Auto-degradación preventiva si el líder pierde su capacidad de coordinación
    cfg.LEADER_ID = None
    cfg.IS_LEADER = False
