import os


NODE_ID: str = os.environ.get("NODE_ID", "nodo1")
NODE_PORT: int = int(os.environ.get("NODE_PORT", "8000"))
PEERS: list[str] = os.environ.get("PEERS", "http://nodo2:8000,http://nodo3:8000").split(",")
LEADER_ID: str | None = os.environ.get("LEADER_ID")

HEARTBEAT_INTERVAL: float = 3.0
HTTP_TIMEOUT: float = 1.5
MAX_FAILED_ATTEMPTS: int = 3