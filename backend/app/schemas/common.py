from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ModeEnum(str, Enum):
    off = "off"
    monitor = "monitor"
    enforce = "enforce"


class LicenseStatusEnum(str, Enum):
    active = "active"
    blocked = "blocked"
    revoked = "revoked"
    expired = "expired"
    suspicious = "suspicious"


class BotStatusEnum(str, Enum):
    online = "online"
    offline = "offline"
    stale = "stale"
    paused = "paused"
    blocked = "blocked"
    stopping = "stopping"
    closing_positions = "closing_positions"


class CommandTypeEnum(str, Enum):
    pause = "pause"
    resume = "resume"
    stop = "stop"
    close_positions = "close_positions"
    block_license = "block_license"


class CommandStatusEnum(str, Enum):
    queued = "queued"
    delivered = "delivered"
    acknowledged = "acknowledged"
    running = "running"
    completed = "completed"
    failed = "failed"
    expired = "expired"
    canceled = "canceled"


class ApiMessage(BaseModel):
    code: str
    message: str
    field: str | None = None


class ApiResponseEnvelope(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    ok: bool = True
    request_id: str = Field(default_factory=lambda: f"req_{uuid4().hex}")
    server_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    protocol_version: str
    errors: list[ApiMessage] = Field(default_factory=list)
    warnings: list[ApiMessage] = Field(default_factory=list)


class AuthorizationDecision(BaseModel):
    allowed: bool
    reason_code: str | None = None
    message: str
    authorized_until: datetime | None = None


class PollingTimers(BaseModel):
    heartbeat_sec: int = 15
    state_sync_sec: int = 60
    command_poll_sec: int = 10


class DecisionFlags(BaseModel):
    suspicious: bool = False
    license_recheck_required: bool = False


class CommandPayload(BaseModel):
    command_id: str
    product_code: str
    bot_family: str
    strategy_code: str
    command_type: CommandTypeEnum
    risk_class: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    status: CommandStatusEnum = CommandStatusEnum.queued
    created_at: datetime | None = None
    expires_at: datetime | None = None
    reason: str | None = None
    requires_ack: bool = True
