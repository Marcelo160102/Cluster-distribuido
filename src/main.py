import asyncio

import src.config as cfg
from fastapi import FastAPI
from src.database import init_db, delete_all, insert_many, get_all
from src.leader_election import start_election
from src.node_client import health_check, cluster_sync
from src.routes_cluster import router as cluster_router
from src.routes_data import router as data_router

app = FastAPI(title="Nodo del Clúster Distribuido", version="1.0.0")
app.include_router(cluster_router)
app.include_router(data_router)

failed_attempts: dict[str, int] = {}
node_alive: dict[str, bool] = {}
my_url: str = ""


async def sync_from_leader():
    if not cfg.LEADER_ID:
        return
    leader_url = f"http://{cfg.LEADER_ID}:{cfg.NODE_PORT}"
    print(f"[SYNC] Solicitando sincronización total a {leader_url}")
    items = await cluster_sync(leader_url)
    if items is None:
        print(f"[SYNC] ERROR: no se pudo contactar al líder {leader_url}")
        return
    print(f"[SYNC] Recibidos {len(items)} registros del líder")
    delete_all()
    insert_many(items)
    print(f"[SYNC] Sincronización total completada: {len(items)} registros insertados")


async def heartbeat_loop():
    global my_url
    my_url = f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"
    while True:
        leader_alive = True
        if cfg.LEADER_ID:
            leader_url = f"http://{cfg.LEADER_ID}:{cfg.NODE_PORT}"
            result = await health_check(leader_url)
            if result is None:
                failed_attempts[leader_url] = failed_attempts.get(leader_url, 0) + 1
                if failed_attempts[leader_url] >= cfg.MAX_FAILED_ATTEMPTS:
                    print(f"[HEARTBEAT] LÍDER {cfg.LEADER_ID} declarado MUERTO")
                    leader_alive = False
                    node_alive[leader_url] = False
            else:
                failed_attempts[leader_url] = 0
                if not node_alive.get(leader_url, True):
                    print(f"[HEARTBEAT] LÍDER {cfg.LEADER_ID} RECUPERADO")
                    node_alive[leader_url] = True
                    await sync_from_leader()

        if not leader_alive:
            elected = await start_election()
            if elected:
                all_urls = sorted(cfg.PEERS + [my_url])
                print(f"[ELECTION] Nuevo líder elegido: {elected} (ID mayor en el clúster)")

        for peer in cfg.PEERS:
            if peer == my_url:
                continue
            result = await health_check(peer)
            if result is None:
                failed_attempts[peer] = failed_attempts.get(peer, 0) + 1
                if failed_attempts[peer] >= cfg.MAX_FAILED_ATTEMPTS:
                    if node_alive.get(peer, True):
                        print(f"[HEARTBEAT] {peer} declarado MUERTO tras {cfg.MAX_FAILED_ATTEMPTS} fallos")
                        node_alive[peer] = False
            else:
                was_dead = not node_alive.get(peer, True)
                failed_attempts[peer] = 0
                if was_dead:
                    print(f"[HEARTBEAT] {peer} RECUPERADO")
                    node_alive[peer] = True
                    await sync_from_leader()

        await asyncio.sleep(cfg.HEARTBEAT_INTERVAL)


@app.on_event("startup")
async def startup():
    global my_url
    my_url = f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"
    all_urls = sorted(cfg.PEERS + [my_url])
    if my_url == all_urls[-1]:
        cfg.LEADER_ID = None
        print(f"[INIT] {cfg.NODE_ID} es el LÍDER inicial (mayor ID)")
    else:
        cfg.LEADER_ID = all_urls[-1].split("//")[1].split(":")[0]
        print(f"[INIT] {cfg.NODE_ID} es SEGUIDOR, líder esperado: {cfg.LEADER_ID}")

    init_db()
    for peer in cfg.PEERS:
        node_alive[peer] = True
    asyncio.create_task(heartbeat_loop())


@app.get("/")
async def root():
    role = "follower" if cfg.LEADER_ID else "leader"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive", "leader": cfg.LEADER_ID}