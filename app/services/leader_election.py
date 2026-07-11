"""Algoritmo de elección de líder (Bully Algorithm).

Reglas:
1. El nodo con mayor ID (lexicográfico: nodo3 > nodo2 > nodo1) tiene prioridad.
2. Al detectar un líder muerto, los nodos envían ELECTION a los de mayor ID.
3. Si nadie responde OK, el nodo se autodeclara líder y anuncia a todos.
4. Si alguien responde OK, ese nodo toma el control y el actual espera.
"""
import app.core.config as cfg
from app.services.node_client import send_election, announce_leader


async def start_election() -> str | None:
    """Inicia el proceso de elección Bully.

    Returns:
        str: ID del nodo que resultó elegido (None si otro tomó el control).
    """
    my_url = f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"
    all_urls = sorted(cfg.PEERS + [my_url])
    higher_peers = [p for p in all_urls if p > my_url]

    # Si soy el de mayor ID, me autodeclaro líder inmediatamente
    if not higher_peers:
        await become_leader()
        return cfg.NODE_ID

    # Envío ELECTION a los nodos con mayor ID
    msg = {"from_node": cfg.NODE_ID, "candidate_id": cfg.NODE_ID}
    ok_received = False

    for peer in higher_peers:
        result = await send_election(peer, msg)
        if result:
            ok_received = True

    # Si algún nodo mayor respondió OK, él tomará el control
    if ok_received:
        return None

    # Nadie respondió → soy el nuevo líder
    await become_leader()
    return cfg.NODE_ID


async def become_leader() -> None:
    """Autodeclara este nodo como líder y lo anuncia a todos los peers."""
    cfg.LEADER_ID = None
    cfg.IS_LEADER = True
    print(f"[ELECCIÓN] {cfg.NODE_ID} se autodeclara LÍDER")
    for peer in cfg.PEERS:
        await announce_leader(peer, cfg.NODE_ID)