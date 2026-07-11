"""Cliente HTTP asíncrono para comunicación entre nodos.

Cada función encapsula una llamada REST a un endpoint interno del clúster.
Todas capturan httpx.TimeoutException y httpx.RequestError para robustez
ante fallos de red o nodos caídos.
"""
import httpx

import app.core.config as cfg


async def health_check(node_url: str) -> dict | None:
    """Consulta GET /health de un nodo peer. Retorna el JSON o None si falla."""
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.get(f"{node_url}/health")
            return resp.json() if resp.status_code == 200 else None
    except httpx.TimeoutException:
        return None
    except httpx.RequestError:
        return None


async def send_replica(node_url: str, payload: dict) -> bool:
    """Envía una operación de replicación a un seguidor vía POST /replicate."""
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.post(f"{node_url}/replicate", json=payload)
            return resp.status_code == 200
    except httpx.TimeoutException:
        return False
    except httpx.RequestError:
        return False


async def send_election(node_url: str, msg: dict) -> bool:
    """Envía un mensaje de elección Bully a un nodo peer."""
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.post(f"{node_url}/election", json=msg)
            return resp.status_code == 200
    except httpx.TimeoutException:
        return False
    except httpx.RequestError:
        return False


async def announce_leader(node_url: str, leader_id: str) -> bool:
    """Notifica a un nodo peer que un nuevo líder ha sido elegido.

    El nodo receptor actualiza su LEADER_ID con el ID recibido.
    """
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.post(
                f"{node_url}/leader-announce",
                json={"leader_id": leader_id},
            )
            return resp.status_code == 200
    except httpx.TimeoutException:
        return False
    except httpx.RequestError:
        return False


async def cluster_sync(node_url: str) -> list | None:
    """Solicita el estado completo del líder vía GET /cluster/sync.

    Usado por un nodo recuperado para descargar todos los registros
    y reemplazar su base de datos local.
    """
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT * 2) as client:
            resp = await client.get(f"{node_url}/cluster/sync")
            return resp.json() if resp.status_code == 200 else None
    except httpx.TimeoutException:
        return None
    except httpx.RequestError:
        return None