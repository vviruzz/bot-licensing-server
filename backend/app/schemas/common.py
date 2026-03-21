from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ModeEnum(StrEnum):
    OFF = "off"
    MONITOR = "monitor"
    ENFORCE = "enforce"


class LicenseStatusEnum(StrEnum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPICIOUS = "suspicious"


class BotStatusEnum(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    STALE = "stale"
    PAUSED = "paused"
    BLOCKED = "blocked"
    STOPPING = "stopping"
    CLOSING_POSITIONS = "closing_positions"


class CommandTypeEnum(StrEnum):
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    CLOSE_POSITIONS = "close_positions"
    BLOCK_LICENSE = "block_license"


class CommandStatusEnum(StrEnum):
    QUEUED = "queued"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELED = "canceled"


class ErrorItem(BaseModel):
    code: str
    message: str
    field: str | None = None


class WarningItem(BaseModel):
    code: str
    message: str


class AuthorizationInfo(BaseModel):
    allowed: bool
    reason_code: str | None = None
    message: str
    authorized_until: datetime | None = None


class ResponseEnvelope(BaseModel):
    ok: bool = True
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex}")
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    protocol_version: str = "1.0"
    errors: list[ErrorItem] = Field(default_factory=list)
    warnings: list[WarningItem] = Field(default_factory=list)

    model_config = ConfigDict(use_enum_values=True)


class IdentifiedRequest(BaseModel):
    license_key: str = Field(min_length=3, max_length=128)
    product_code: str = Field(min_length=1, max_length=64)
    bot_family: str = Field(min_length=1, max_length=64)
    strategy_code: str = Field(min_length=1, max_length=64)
    bot_instance_id: str = Field(min_length=3, max_length=128)
    protocol_version: str = Field(min_length=1, max_length=32)


class SessionScopedRequest(IdentifiedRequest):
    session_id: str = Field(min_length=1, max_length=128)


class MachineBoundRequest(IdentifiedRequest):
    machine_fingerprint: str = Field(min_length=3, max_length=256)


class BasicAckResponse(ResponseEnvelope):
    message: str
    data: dict[str, Any] | None = None
