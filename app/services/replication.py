import app.core.config as cfg
from app.core.database import delete
from app.services.node_client import send_replica


async def replicate_to_followers(operation: str, data: str | None = None, item_id: str | None = None) -> bool:
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