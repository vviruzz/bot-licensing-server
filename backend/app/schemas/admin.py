from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import (
    BasicAckResponse,
    BotStatusEnum,
    CommandStatusEnum,
    CommandTypeEnum,
    LicenseStatusEnum,
    ModeEnum,
    ResponseEnvelope,
)


class AdminLoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)


class AdminLoginResponse(ResponseEnvelope):
    access_token: str
    token_type: str = "bearer"
    admin: dict[str, str]


class AdminMeResponse(ResponseEnvelope):
    admin: dict[str, str]


class AdminLicenseCommandRequest(BaseModel):
    license_key: str = Field(min_length=3, max_length=128)
    product_code: str = Field(min_length=1, max_length=64)
    bot_family: str = Field(min_length=1, max_length=64)
    strategy_code: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=512)


class AdminBotCommandRequest(BaseModel):
    bot_instance_id: str = Field(min_length=3, max_length=128)
    session_id: str | None = Field(default=None, max_length=128)
    product_code: str = Field(min_length=1, max_length=64)
    bot_family: str = Field(min_length=1, max_length=64)
    strategy_code: str = Field(min_length=1, max_length=64)
    reason: str = Field(min_length=1, max_length=512)


class AdminCommandResponse(BasicAckResponse):
    command_id: str
    command_type: CommandTypeEnum
    command_status: CommandStatusEnum = CommandStatusEnum.QUEUED


class LicenseListItem(BaseModel):
    license_key: str
    status: LicenseStatusEnum
    mode: ModeEnum
    product_code: str
    bot_family: str
    strategy_code: str
    owner_label: str | None = None
    plan_name: str | None = None
    expires_at: datetime | None = None
    suspicious_flag: bool = False


class BotListItem(BaseModel):
    bot_instance_id: str
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    machine_fingerprint: str
    protocol_version: str
    bot_status: BotStatusEnum
    effective_mode: ModeEnum
    session_id: str | None = None
    last_seen_at: datetime | None = None


class AlertListItem(BaseModel):
    alert_id: str
    alert_type: str
    severity: str
    status: str
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    summary: str
    first_seen_at: datetime


class LicenseListResponse(ResponseEnvelope):
    items: list[LicenseListItem] = Field(default_factory=list)


class BotListResponse(ResponseEnvelope):
    items: list[BotListItem] = Field(default_factory=list)


class BotDetailResponse(ResponseEnvelope):
    item: BotListItem


class AlertListResponse(ResponseEnvelope):
    items: list[AlertListItem] = Field(default_factory=list)
