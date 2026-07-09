import asyncio

import src.config as cfg
from fastapi import FastAPI
from src.database import init_db
from src.node_client import health_check
from src.routes_cluster import router as cluster_router
from src.routes_data import router as data_router

app = FastAPI(title="Nodo del Clúster Distribuido", version="1.0.0")
app.include_router(cluster_router)
app.include_router(data_router)

failed_attempts: dict[str, int] = {}
node_alive: dict[str, bool] = {}


async def heartbeat_loop():
    while True:
        for peer in cfg.PEERS:
            result = await health_check(peer)
            if result is None:
                failed_attempts[peer] = failed_attempts.get(peer, 0) + 1
                if failed_attempts[peer] >= cfg.MAX_FAILED_ATTEMPTS:
                    if node_alive.get(peer, True):
                        print(f"[HEARTBEAT] {peer} declarado MUERTO tras {cfg.MAX_FAILED_ATTEMPTS} fallos")
                        node_alive[peer] = False
            else:
                failed_attempts[peer] = 0
                if not node_alive.get(peer, True):
                    print(f"[HEARTBEAT] {peer} RECUPERADO")
                    node_alive[peer] = True
        await asyncio.sleep(cfg.HEARTBEAT_INTERVAL)


@app.on_event("startup")
async def startup():
    all_ids = sorted(cfg.PEERS + [f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"])
    my_url = f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"
    if my_url == all_ids[-1]:
        cfg.LEADER_ID = None
        print(f"[INIT] {cfg.NODE_ID} es el LÍDER inicial (mayor ID)")
    else:
        cfg.LEADER_ID = all_ids[-1].split("//")[1].split(":")[0]
        print(f"[INIT] {cfg.NODE_ID} es SEGUIDOR, líder esperado: {cfg.LEADER_ID}")

    init_db()
    for peer in cfg.PEERS:
        node_alive[peer] = True
    asyncio.create_task(heartbeat_loop())


@app.get("/")
async def root():
    role = "follower" if cfg.LEADER_ID else "leader"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive", "leader": cfg.LEADER_ID}