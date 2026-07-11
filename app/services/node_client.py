import httpx

import app.core.config as cfg


async def health_check(node_url: str) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.get(f"{node_url}/health")
            return resp.json() if resp.status_code == 200 else None
    except httpx.TimeoutException:
        return None
    except httpx.RequestError:
        return None


async def send_replica(node_url: str, payload: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.post(f"{node_url}/replicate", json=payload)
            return resp.status_code == 200
    except httpx.TimeoutException:
        return False
    except httpx.RequestError:
        return False


async def send_election(node_url: str, msg: dict) -> bool:
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT) as client:
            resp = await client.post(f"{node_url}/election", json=msg)
            return resp.status_code == 200
    except httpx.TimeoutException:
        return False
    except httpx.RequestError:
        return False


async def announce_leader(node_url: str, leader_id: str) -> bool:
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
    try:
        async with httpx.AsyncClient(timeout=cfg.HTTP_TIMEOUT * 2) as client:
            resp = await client.get(f"{node_url}/cluster/sync")
            return resp.json() if resp.status_code == 200 else None
    except httpx.TimeoutException:
        return None
    except httpx.RequestError:
        return None