from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.dependencies.auth import require_admin_auth
from app.schemas.admin import (
    AdminBotCommandRequest,
    AdminCommandResponse,
    AdminLicenseCommandRequest,
    AlertListItem,
    AlertListResponse,
    BotDetailResponse,
    BotListItem,
    BotListResponse,
    LicenseListItem,
    LicenseListResponse,
)
from app.schemas.common import BotStatusEnum, CommandTypeEnum, LicenseStatusEnum, ModeEnum

router = APIRouter(prefix="/api/v1/admin", tags=["admin"], dependencies=[Depends(require_admin_auth)])


def _command_response(command_type: CommandTypeEnum, message: str) -> AdminCommandResponse:
    return AdminCommandResponse(
        message=message,
        command_id=f"cmd_{uuid4().hex}",
        command_type=command_type,
    )


@router.post("/license/block", response_model=AdminCommandResponse)
def block_license(payload: AdminLicenseCommandRequest) -> AdminCommandResponse:
    # TODO: write license status change + audit log entry and queue follow-up bot actions if needed.
    return _command_response(CommandTypeEnum.BLOCK_LICENSE, f"license block queued for {payload.license_key}")


@router.post("/bot/pause", response_model=AdminCommandResponse)
def pause_bot(payload: AdminBotCommandRequest) -> AdminCommandResponse:
    # TODO: persist queued pause command targeted to bot/session scope.
    return _command_response(CommandTypeEnum.PAUSE, f"pause command queued for {payload.bot_instance_id}")


@router.post("/bot/resume", response_model=AdminCommandResponse)
def resume_bot(payload: AdminBotCommandRequest) -> AdminCommandResponse:
    # TODO: persist queued resume command targeted to bot/session scope.
    return _command_response(CommandTypeEnum.RESUME, f"resume command queued for {payload.bot_instance_id}")


@router.post("/bot/stop", response_model=AdminCommandResponse)
def stop_bot(payload: AdminBotCommandRequest) -> AdminCommandResponse:
    # TODO: persist queued stop command targeted to bot/session scope.
    return _command_response(CommandTypeEnum.STOP, f"stop command queued for {payload.bot_instance_id}")


@router.post("/bot/close-positions", response_model=AdminCommandResponse)
def close_positions(payload: AdminBotCommandRequest) -> AdminCommandResponse:
    # TODO: persist queued close_positions command targeted to bot/session scope.
    return _command_response(CommandTypeEnum.CLOSE_POSITIONS, f"close-positions command queued for {payload.bot_instance_id}")


@router.get("/licenses", response_model=LicenseListResponse)
def list_licenses() -> LicenseListResponse:
    # TODO: replace placeholder items with paginated database-backed license queries.
    return LicenseListResponse(items=[])


@router.get("/bots", response_model=BotListResponse)
def list_bots() -> BotListResponse:
    # TODO: replace placeholder items with database-backed bot instance queries.
    return BotListResponse(items=[])


@router.get("/bots/{bot_instance_id}", response_model=BotDetailResponse)
def get_bot(bot_instance_id: str) -> BotDetailResponse:
    # TODO: load bot detail, last state snapshot, and recent commands from persistence.
    return BotDetailResponse(
        item=BotListItem(
            bot_instance_id=bot_instance_id,
            license_key="LIC-STUB",
            product_code="grid",
            bot_family="grid",
            strategy_code="grid_v1",
            machine_fingerprint="fp_stub",
            protocol_version="1.0",
            bot_status=BotStatusEnum.STALE,
            effective_mode=ModeEnum.MONITOR,
            session_id="sess_stub",
            last_seen_at=datetime.now(timezone.utc),
        )
    )


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts() -> AlertListResponse:
    # TODO: replace placeholder items with paginated database-backed alert queries.
    return AlertListResponse(
        items=[
            AlertListItem(
                alert_id="alert_stub_protocol",
                alert_type="protocol_mismatch",
                severity="medium",
                status="open",
                license_key="LIC-STUB",
                product_code="grid",
                bot_family="grid",
                strategy_code="grid_v1",
                summary="TODO placeholder alert until alert storage is implemented",
                first_seen_at=datetime.now(timezone.utc),
            )
        ]
    )
