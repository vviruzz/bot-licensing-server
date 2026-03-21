from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import (
    ApiResponseEnvelope,
    BotStatusEnum,
    CommandPayload,
    CommandTypeEnum,
    LicenseStatusEnum,
    ModeEnum,
)


class CommandTarget(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    bot_instance_id: str | None = None
    session_id: str | None = None
    protocol_version: str = "1.0"


class AdminCommandRequest(CommandTarget):
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class AdminCommandResponse(ApiResponseEnvelope):
    command: CommandPayload
    target_bot_status: BotStatusEnum | None = None


class AdminLicenseBlockRequest(BaseModel):
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    protocol_version: str
    reason: str


class LicenseSummary(BaseModel):
    license_key: str
    status: LicenseStatusEnum
    mode: ModeEnum
    product_code: str
    bot_family: str
    strategy_code: str
    owner_label: str | None = None
    plan_name: str | None = None
    suspicious_flag: bool = False
    expires_at: datetime | None = None


class BotSummary(BaseModel):
    bot_instance_id: str
    license_key: str
    product_code: str
    bot_family: str
    strategy_code: str
    machine_fingerprint: str | None = None
    protocol_version: str
    status: BotStatusEnum
    authorized_until: datetime | None = None
    last_seen_at: datetime | None = None


class BotDetail(BotSummary):
    hostname: str | None = None
    platform: str | None = None
    bot_version: str | None = None
    session_id: str | None = None
    effective_mode: ModeEnum = ModeEnum.monitor
    warnings: list[str] = Field(default_factory=list)


class AlertSummary(BaseModel):
    alert_type: str
    severity: str
    status: str
    license_key: str | None = None
    bot_instance_id: str | None = None
    session_id: str | None = None
    product_code: str | None = None
    bot_family: str | None = None
    strategy_code: str | None = None
    summary: str
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None


class LicenseListResponse(ApiResponseEnvelope):
    items: list[LicenseSummary] = Field(default_factory=list)


class BotListResponse(ApiResponseEnvelope):
    items: list[BotSummary] = Field(default_factory=list)


class BotDetailResponse(ApiResponseEnvelope):
    item: BotDetail


class AlertListResponse(ApiResponseEnvelope):
    items: list[AlertSummary] = Field(default_factory=list)


def build_command_payload(request: AdminCommandRequest, command_type: CommandTypeEnum) -> CommandPayload:
    return CommandPayload(
        command_id=f"cmd_stub_{command_type.value}_{request.bot_instance_id or request.license_key}",
        product_code=request.product_code,
        bot_family=request.bot_family,
        strategy_code=request.strategy_code,
        command_type=command_type,
        payload=request.payload,
        reason=request.reason,
    )
