"""Modelos Pydantic del dominio VoIP y mensajes del clúster.

VoipEndpoint define la estructura del campo data (JSON stringificado)
que se almacena en SQLite. El resto de modelos serializan las peticiones
y respuestas de la API interna entre nodos.
"""
from pydantic import BaseModel, field_validator


class VoipEndpoint(BaseModel):
    """Endpoint VoIP registrado en el clúster.

    El campo 'data' de la tabla items almacena este modelo como JSON stringificado.
    """
    extension: str       # Número de extensión (ej. "101", "2001")
    protocol: str        # Protocolo VoIP (SIP, WebRTC, PJSIP)
    ip_address: str      # Dirección IP del endpoint
    status: str          # Estado: online, offline, busy
    user_agent: str      # Software o dispositivo (ej. "Yealink T48S", "Jitsi Meet")

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        allowed = {"SIP", "WebRTC", "PJSIP"}
        if v not in allowed:
            raise ValueError(f"protocolo no válido: {v}. Permitidos: {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"online", "offline", "busy"}
        if v not in allowed:
            raise ValueError(f"estado no válido: {v}. Permitidos: {allowed}")
        return v


class ItemCreate(BaseModel):
    """Payload para crear un nuevo endpoint VoIP."""
    data: str

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: str) -> str:
        VoipEndpoint.model_validate_json(v)
        return v


class ItemUpdate(BaseModel):
    """Payload para actualizar un endpoint VoIP existente."""
    data: str

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: str) -> str:
        VoipEndpoint.model_validate_json(v)
        return v


class ItemResponse(BaseModel):
    """Respuesta estándar para operaciones CRUD."""
    id: str
    data: str
    created_at: str
    updated_at: str


class ReplicaRequest(BaseModel):
    """Mensaje de replicación enviado del líder a los seguidores."""
    operation: str              # "create" | "update" | "delete"
    item_id: str | None = None
    data: str | None = None


class ElectionMessage(BaseModel):
    """Mensaje de elección Bully."""
    from_node: str             # ID del nodo que inicia la elección
    candidate_id: str          # ID del nodo candidato a líder


class HealthStatus(BaseModel):
    """Estado de salud de un nodo."""
    node_id: str
    role: str                  # "leader" | "follower"
    status: str                # "alive"