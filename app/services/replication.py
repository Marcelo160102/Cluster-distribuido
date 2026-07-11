"""Motor de replicación del clúster.

El líder invoca replicate_to_followers() tras cada escritura local.
El quórum exige al menos 2 confirmaciones (ACK) de los 3 nodos totales,
contando al propio líder como ACK implícito (acks=1 inicial).
Si el quórum falla, se ejecuta rollback local y el líder se auto-degrada.
"""
import app.core.config as cfg
from app.core.database import delete
from app.services.node_client import send_replica


async def replicate_to_followers(operation: str, data: str | None = None, item_id: str | None = None) -> bool:
    """Replica una operación a todos los seguidores.

    Args:
        operation: "create", "update" o "delete"
        data: JSON stringificado del endpoint VoIP (solo create/update)
        item_id: UUID del registro (solo update/delete)

    Returns:
        True si se alcanzó quórum (ACK >= 2), False si falló.

    En caso de fallo:
        1. Elimina el registro local (rollback)
        2. Limpia el flag de liderazgo (auto-degradación)
        3. Retorna False para que la API responda 503
    """
    peers = [p for p in cfg.PEERS]
    payload = {"operation": operation, "data": data, "item_id": item_id}

    acks = 1
    for peer in peers:
        ok = await send_replica(peer, payload)
        if ok:
            acks += 1

    if acks >= 2:
        return True

    if item_id:
        delete(item_id)

    cfg.LEADER_ID = None
    cfg.IS_LEADER = False
    return False