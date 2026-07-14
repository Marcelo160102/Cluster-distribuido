"""Motor de replicación del clúster basado en Consenso 3PC.

El líder coordina de manera no bloqueante las fases CanCommit, PreCommit y DoCommit
antes de consolidar cualquier cambio en las bases de datos locales o de los seguidores.
"""
import asyncio
import uuid
import app.core.config as cfg
from app.services.node_client import send_3pc_phase  # Deberás mapear esta función en tu cliente HTTP

async def replicate_to_followers(operation: str, data: str | None = None, item_id: str | None = None) -> bool:
    """Coordina la replicación distribuida mediante el protocolo 3PC.

    Args:
        operation: "create", "update" o "delete"
        data: JSON stringificado del endpoint VoIP
        item_id: UUID del registro

    Returns:
        True si la transacción se consolida con éxito en el clúster, False si se aborta.
    """
    peers = [p for p in cfg.PEERS]
    
    # 0. Generar identificador único global para la transacción distribuida
    tx_id = str(uuid.uuid4())
    payload = {
        "tx_id": tx_id,
        "operation": operation,
        "data": data,
        "item_id": item_id
    }

    # ==========================================
    # FASE 1: CAN-COMMIT (Voto Unánime / Quórum)
    # ==========================================
    # El coordinador pregunta a los participantes si pueden procesar la transacción
    tasks_can_commit = [send_3pc_phase(peer, phase="can_commit", payload=payload) for peer in peers]
    results_can_commit = await asyncio.gather(*tasks_can_commit, return_exceptions=True)
    
    # Contamos votos afirmativos (Líder cuenta como un voto implícito 'Sí')
    votes_yes = 1 + sum(1 for res in results_can_commit if res is True)
    
    # Validamos requerimiento según el diseño del clúster (Quórum o Unanimidad)
    # 3PC teórico pide unanimidad, pero puedes usar quórum (>= 2) para tolerar caídas de nodos esclavos
    if votes_yes < 2:
        print(f"[3PC] [TX:{tx_id}] Abortando: No se alcanzó el quórum en CanCommit.")
        await abort_transaction(peers, tx_id)
        return False

    # ==========================================
    # FASE 2: PRE-COMMIT (Buffer de Seguridad)
    # ==========================================
    # Los participantes preparan los recursos y escriben en su log temporal aislado
    tasks_pre_commit = [send_3pc_phase(peer, phase="pre_commit", payload={"tx_id": tx_id}) for peer in peers]
    results_pre_commit = await asyncio.gather(*tasks_pre_commit, return_exceptions=True)
    
    acks_pre_commit = 1 + sum(1 for res in results_pre_commit if res is True)
    
    if acks_pre_commit < 2:
        print(f"[3PC] [TX:{tx_id}] Abortando: Fallo en fase de preparación PreCommit.")
        await abort_transaction(peers, tx_id)
        return False

    # ==========================================
    # FASE 3: DO-COMMIT (Ejecución final)
    # ==========================================
    # Llegados aquí, el éxito está garantizado. El líder envía la orden de confirmación final
    tasks_do_commit = [send_3pc_phase(peer, phase="do_commit", payload={"tx_id": tx_id}) for peer in peers]
    
    # Lanzamos las confirmaciones a los seguidores de fondo (No bloqueante)
    await asyncio.gather(*tasks_do_commit, return_exceptions=True)
    
    # Retorna True para indicarle a 'routes_data.py' que la transacción fue exitosa
    # y proceda de inmediato con la escritura local final.
    return True


async def abort_transaction(peers: list[str], tx_id: str):
    """Notifica de manera asíncrona la cancelación a todos los nodos."""
    tasks = [send_3pc_phase(peer, phase="abort", payload={"tx_id": tx_id}) for peer in peers]
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Auto-degradación preventiva si el líder pierde su capacidad de coordinación
    cfg.LEADER_ID = None
    cfg.IS_LEADER = False
