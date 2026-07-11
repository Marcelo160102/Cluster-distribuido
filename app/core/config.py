"""Configuración central del nodo.

Todas las variables de entorno, constantes de red y flags de estado
se definen aquí como variables de módulo para acceso global.
"""
import os


# Identidad del nodo en el clúster
NODE_ID: str = os.environ.get("NODE_ID", "nodo1")
NODE_PORT: int = int(os.environ.get("NODE_PORT", "8000"))

# Lista de URLs de los otros nodos (sin incluirse a sí mismo)
PEERS: list[str] = os.environ.get("PEERS", "http://nodo2:8000,http://nodo3:8000").split(",")

# ID del líder actual; None significa "yo soy el líder" o "no hay líder"
LEADER_ID: str | None = os.environ.get("LEADER_ID")

# --- Parámetros de red y tolerancia a fallos ---
HEARTBEAT_INTERVAL: float = 3.0         # segundos entre pings de salud
HTTP_TIMEOUT: float = 1.5               # timeout máximo por petición HTTP entre nodos
MAX_FAILED_ATTEMPTS: int = 3            # intentos fallidos antes de declarar muerto a un nodo

# Flag explícito de liderazgo (se setea en become_leader / se limpia en degradación)
IS_LEADER: bool = False