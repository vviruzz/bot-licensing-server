from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import require_bot_token
from app.schemas.bot_api import (
    BotCommandsResponse,
    BotHeartbeatRequest,
    BotHeartbeatResponse,
    BotRegisterRequest,
    BotRegisterResponse,
    BotStateRequest,
    BotStateResponse,
    CommandResultRequest,
    CommandResultResponse,
)
from app.schemas.common import AuthorizationDecision, BotStatusEnum, CommandPayload, CommandTypeEnum, CommandStatusEnum, LicenseStatusEnum, ModeEnum

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/register", response_model=BotRegisterResponse)
def register_bot(payload: BotRegisterRequest, _: str = Depends(require_bot_token)) -> BotRegisterResponse:
    # TODO: persist or upsert bot instance registration after service layer is introduced.
    return BotRegisterResponse(
        protocol_version=payload.protocol_version,
        license_status=LicenseStatusEnum.active,
        bot_status=BotStatusEnum.online,
        effective_mode=ModeEnum.monitor,
        authorization=AuthorizationDecision(allowed=True, message="stub registration accepted"),
    )


@router.post("/heartbeat", response_model=BotHeartbeatResponse)
def create_heartbeat(payload: BotHeartbeatRequest, _: str = Depends(require_bot_token)) -> BotHeartbeatResponse:
    # TODO: persist heartbeat rows and update last_seen_at when bot services are implemented.
    return BotHeartbeatResponse(
        protocol_version=payload.protocol_version,
        license_status=LicenseStatusEnum.active,
        bot_status=payload.status,
        effective_mode=ModeEnum.monitor,
        authorization=AuthorizationDecision(allowed=True, message="stub heartbeat accepted"),
    )


@router.post("/state", response_model=BotStateResponse)
def sync_state(payload: BotStateRequest, _: str = Depends(require_bot_token)) -> BotStateResponse:
    # TODO: persist state snapshots and derive server-side bot status in the future service layer.
    return BotStateResponse(
        protocol_version=payload.protocol_version,
        bot_status=payload.bot_state.bot_status,
        effective_mode=ModeEnum.monitor,
    )


@router.get("/commands", response_model=BotCommandsResponse)
def list_commands(
    license_key: str,
    product_code: str,
    bot_family: str,
    strategy_code: str,
    bot_instance_id: str,
    protocol_version: str,
    session_id: str | None = None,
    _: str = Depends(require_bot_token),
) -> BotCommandsResponse:
    # TODO: load queued remote commands for the license/bot target from the database.
    command = CommandPayload(
        command_id=f"cmd_stub_pause_{bot_instance_id}",
        product_code=product_code,
        bot_family=bot_family,
        strategy_code=strategy_code,
        command_type=CommandTypeEnum.pause,
        status=CommandStatusEnum.queued,
        reason=f"stub command placeholder for {license_key}",
    )
    return BotCommandsResponse(
        protocol_version=protocol_version,
        bot_status=BotStatusEnum.online,
        commands=[command],
        warnings=[],
    )


@router.post("/command-result", response_model=CommandResultResponse)
def submit_command_result(
    payload: CommandResultRequest,
    _: str = Depends(require_bot_token),
) -> CommandResultResponse:
    # TODO: persist command execution results and update remote command status transitions.
    return CommandResultResponse(
        protocol_version=payload.protocol_version,
        command_id=payload.command_id,
        command_status=payload.result_status,
    )
