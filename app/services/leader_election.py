import app.core.config as cfg
from app.services.node_client import send_election, announce_leader


async def start_election() -> str | None:
    my_url = f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"
    all_urls = sorted(cfg.PEERS + [my_url])
    higher_peers = [p for p in all_urls if p > my_url]

    if not higher_peers:
        await become_leader()
        return cfg.NODE_ID

    msg = {"from_node": cfg.NODE_ID, "candidate_id": cfg.NODE_ID}
    ok_received = False

    for peer in higher_peers:
        result = await send_election(peer, msg)
        if result:
            ok_received = True

    if ok_received:
        return None

    await become_leader()
    return cfg.NODE_ID


async def become_leader() -> None:
    cfg.LEADER_ID = None
    cfg.IS_LEADER = True
    print(f"[ELECTION] {cfg.NODE_ID} se autodeclara LÍDER")
    for peer in cfg.PEERS:
        await announce_leader(peer, cfg.NODE_ID)