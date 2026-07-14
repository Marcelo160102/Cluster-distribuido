"""Cliente de red para la comunicación entre nodos del clúster.

Contiene las llamadas HTTP asíncronas para gestionar las fases de consenso,
validar la salud de los peers y participar en las elecciones del clúster.
"""
import httpx
import asyncio

# Tiempo de espera optimizado para evitar bloqueos del event loop durante el consenso
TIMEOUT_CONFIG = httpx.Timeout(5.0, connect=2.0)

async def send_3pc_phase(peer_url: str, phase: str, payload: dict) -> bool:
    """Envía de forma asíncrona una fase del protocolo 3PC a un nodo seguidor.

    Args:
        peer_url: URL base del nodo destino (ej. "http://nodo2:8000")
        phase: Nombre de la fase ("can_commit", "pre_commit", "do_commit", "abort")
        payload: Datos de la transacción o identificador de la misma (tx_id)

    Returns:
        True si el nodo responde con éxito y aprueba la fase, False si falla o da timeout.
    """
    url = f"{peer_url}/cluster/3pc/{phase}"
    
    async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
        try:
            response = await client.post(url, json=payload)
            
            if response.status_code != 200:
                print(f"[CLIENT-3PC] Nodo {peer_url} rechazó la fase {phase}. Código: {response.status_code}")
                return False
                
            data = response.json()
            
            # Validaciones de confirmación según la fase específica
            if phase == "can_commit" and data.get("vote") == "YES":
                return True
            elif phase == "pre_commit" and data.get("status") == "ACK":
                return True
            elif phase == "do_commit" and data.get("status") == "committed":
                return True
            elif phase == "abort" and data.get("status") == "aborted":
                return True
                
            return False
            
        except (httpx.RequestError, httpx.TimeoutException) as e:
            print(f"[CLIENT-3PC] Error de red al conectar con {peer_url} en fase {phase}: {str(e)}")
            return False


# =======================================================================
#  Funciones de salud, sincronización y elección (Bully Algorithm)
# =======================================================================

async def health_check(node_url: str) -> dict | None:
    """Consulta GET /health de un peer.
    
    Returns:
        dict con node_id, role, status si OK; None si falla.
    """
    url = f"{node_url}/health"
    async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except (httpx.RequestError, httpx.TimeoutException):
            pass
    return None


async def cluster_sync(leader_url: str) -> list | None:
    """Descarga la lista completa de registros desde GET /cluster/sync.
    
    Returns:
        list[dict] con los registros; None si falla.
    """
    url = f"{leader_url}/cluster/sync"
    async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
        except (httpx.RequestError, httpx.TimeoutException):
            pass
    return None


async def send_election(node_url: str, msg: dict) -> bool:
    """Envía un mensaje ELECTION a un peer (POST /election).
    
    Returns:
        True si el peer respondió OK, False en otro caso.
    """
    url = f"{node_url}/election"
    async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
        try:
            resp = await client.post(url, json=msg)
            data = resp.json()
            return data.get("response") == "OK"
        except (httpx.RequestError, httpx.TimeoutException):
            return False


async def announce_leader(node_url: str, leader_id: str) -> None:
    """Anuncia un nuevo líder (POST /leader-announce).
    
    Es fire-and-forget; no se espera confirmación.
    """
    url = f"{node_url}/leader-announce"
    async with httpx.AsyncClient(timeout=TIMEOUT_CONFIG) as client:
        try:
            await client.post(url, json={"leader_id": leader_id})
        except (httpx.RequestError, httpx.TimeoutException):
            pass
