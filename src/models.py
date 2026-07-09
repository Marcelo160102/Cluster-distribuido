import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


class VoipEndpoint(BaseModel):
    extension: str
    protocol: str
    ip_address: str
    status: str
    user_agent: str

    @field_validator("protocol")
    @classmethod
    def validate_protocol(cls, v: str) -> str:
        allowed = {"SIP", "WebRTC", "PJSIP"}
        if v not in allowed:
            raise ValueError(f"protocol must be one of {allowed}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"online", "offline", "busy"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class ItemCreate(BaseModel):
    data: str

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: str) -> str:
        VoipEndpoint.model_validate_json(v)
        return v


class ItemUpdate(BaseModel):
    data: str

    @field_validator("data")
    @classmethod
    def validate_data(cls, v: str) -> str:
        VoipEndpoint.model_validate_json(v)
        return v


class ItemResponse(BaseModel):
    id: str
    data: str
    created_at: str
    updated_at: str


class ReplicaRequest(BaseModel):
    operation: str
    item_id: str | None = None
    data: str | None = None


class ElectionMessage(BaseModel):
    from_node: str
    candidate_id: str


class HealthStatus(BaseModel):
    node_id: str
    role: str
    status: str