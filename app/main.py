"""Punto de entrada del nodo — FastAPI + Heartbeat Loop.

Cada nodo del clúster ejecuta:
1. Servidor FastAPI con routers de datos públicos y de clúster interno.
2. Tarea asíncrona en background (heartbeat_loop) que monitorea peers,
   detecta caídas del líder, dispara elecciones y sincroniza nodos recuperados.
"""
import asyncio

import app.core.config as cfg
from app.core.database import init_db, delete_all, insert_many
from app.services.leader_election import start_election
from app.services.node_client import health_check, cluster_sync
from app.api.routes_cluster import router as cluster_router
from app.api.routes_data import router as data_router
from fastapi import FastAPI

app = FastAPI(title="Nodo del Clúster Distribuido", version="1.0.0")
app.include_router(cluster_router)
app.include_router(data_router)

# Registro de intentos fallidos y estado de conectividad por peer
failed_attempts: dict[str, int] = {}
node_alive: dict[str, bool] = {}
my_url: str = ""


async def sync_from_leader():
    """Sincronización total por estado completo.

    Flujo:
    1. Vacía la tabla local (DELETE FROM items)
    2. Descarga TODO el listado del líder (GET /cluster/sync)
    3. Inserta en una transacción atómica (insert_many)
    """
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


async def discover_leader() -> str | None:
    """Consulta a todos los peers si alguno es líder.

    Retorna el ID del primer nodo que responda con role=leader,
    o None si no hay líder en el clúster.
    """
    for peer in cfg.PEERS:
        result = await health_check(peer)
        if result and result.get("role") == "leader":
            peer_id = peer.split("//")[1].split(":")[0]
            return peer_id
    return None


async def heartbeat_loop():
    """Loop principal de monitoreo (se ejecuta como tarea asíncrona de fondo).

    Por cada iteración:
    - Verifica salud del líder actual (si existe)
    - Si el líder murió, descubre uno existente o inicia elección Bully
    - Verifica salud de todos los peers, detecta recuperaciones y sincroniza
    """
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

        if cfg.LEADER_ID is not None and not leader_alive:
            existing_leader = await discover_leader()
            if existing_leader:
                cfg.LEADER_ID = existing_leader
                print(f"[DISCOVER] Líder existente encontrado: {existing_leader}")
                await sync_from_leader()
            else:
                elected = await start_election()
                if elected:
                    print(f"[ELECCIÓN] Nuevo líder elegido: {elected} (ID mayor en el clúster)")

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
                    if cfg.LEADER_ID:
                        await sync_from_leader()

        await asyncio.sleep(cfg.HEARTBEAT_INTERVAL)


@app.on_event("startup")
async def startup():
    """Inicialización del nodo al arrancar FastAPI.

    1. Inicializa base de datos SQLite
    2. Descubre si ya hay un líder en el clúster
    3. Si hay líder → se une como seguidor y sincroniza
    4. Si no hay líder → el de mayor ID se declara líder inicial
    5. Arranca el heartbeat_loop en background
    """
    global my_url
    my_url = f"http://{cfg.NODE_ID}:{cfg.NODE_PORT}"
    init_db()
    for peer in cfg.PEERS:
        node_alive[peer] = True

    existing_leader = await discover_leader()
    if existing_leader:
        cfg.LEADER_ID = existing_leader
        cfg.IS_LEADER = False
        print(f"[INIT] {cfg.NODE_ID} es SEGUIDOR, líder detectado: {cfg.LEADER_ID}")
        await sync_from_leader()
    else:
        all_urls = sorted(cfg.PEERS + [my_url])
        if my_url == all_urls[-1]:
            cfg.LEADER_ID = None
            cfg.IS_LEADER = True
            print(f"[INIT] {cfg.NODE_ID} es el LÍDER inicial (sin líder existente)")
        else:
            cfg.LEADER_ID = all_urls[-1].split("//")[1].split(":")[0]
            cfg.IS_LEADER = False
            print(f"[INIT] {cfg.NODE_ID} es SEGUIDOR (inicial), líder esperado: {cfg.LEADER_ID}")

    asyncio.create_task(heartbeat_loop())


@app.get("/")
async def root():
    """Endpoint raíz — información básica del nodo."""
    role = "leader" if cfg.IS_LEADER else "follower"
    return {"node_id": cfg.NODE_ID, "role": role, "status": "alive", "leader": cfg.LEADER_ID}