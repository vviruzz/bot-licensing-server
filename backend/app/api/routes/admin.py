from __future__ import annotations

from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_admin_user
from app.models.admin_user import AdminUser
from app.schemas.admin_api import (
    AdminCommandRequest,
    AdminCommandResponse,
    AdminLicenseBlockRequest,
    AlertListResponse,
    AlertSummary,
    BotDetail,
    BotDetailResponse,
    BotListResponse,
    BotSummary,
    LicenseListResponse,
    LicenseSummary,
    build_command_payload,
)
from app.schemas.common import BotStatusEnum, CommandTypeEnum, LicenseStatusEnum, ModeEnum

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/license/block", response_model=AdminCommandResponse)
def block_license(
    payload: AdminLicenseBlockRequest,
    _: AdminUser = Depends(get_current_admin_user),
) -> AdminCommandResponse:
    # TODO: change license status in the database and create a durable audit log record.
    command_request = AdminCommandRequest(
        license_key=payload.license_key,
        product_code=payload.product_code,
        bot_family=payload.bot_family,
        strategy_code=payload.strategy_code,
        protocol_version=payload.protocol_version,
        reason=payload.reason,
    )
    return AdminCommandResponse(
        protocol_version=payload.protocol_version,
        command=build_command_payload(command_request, CommandTypeEnum.block_license),
        target_bot_status=BotStatusEnum.blocked,
    )


@router.post("/bot/pause", response_model=AdminCommandResponse)
def pause_bot(payload: AdminCommandRequest, _: AdminUser = Depends(get_current_admin_user)) -> AdminCommandResponse:
    # TODO: enqueue pause commands in remote_commands once service logic is added.
    return AdminCommandResponse(
        protocol_version=payload.protocol_version,
        command=build_command_payload(payload, CommandTypeEnum.pause),
        target_bot_status=BotStatusEnum.paused,
    )


@router.post("/bot/resume", response_model=AdminCommandResponse)
def resume_bot(payload: AdminCommandRequest, _: AdminUser = Depends(get_current_admin_user)) -> AdminCommandResponse:
    # TODO: enqueue resume commands in remote_commands once service logic is added.
    return AdminCommandResponse(
        protocol_version=payload.protocol_version,
        command=build_command_payload(payload, CommandTypeEnum.resume),
        target_bot_status=BotStatusEnum.online,
    )


@router.post("/bot/stop", response_model=AdminCommandResponse)
def stop_bot(payload: AdminCommandRequest, _: AdminUser = Depends(get_current_admin_user)) -> AdminCommandResponse:
    # TODO: enqueue stop commands in remote_commands once service logic is added.
    return AdminCommandResponse(
        protocol_version=payload.protocol_version,
        command=build_command_payload(payload, CommandTypeEnum.stop),
        target_bot_status=BotStatusEnum.stopping,
    )


@router.post("/bot/close-positions", response_model=AdminCommandResponse)
def close_positions(payload: AdminCommandRequest, _: AdminUser = Depends(get_current_admin_user)) -> AdminCommandResponse:
    # TODO: enqueue close_positions commands in remote_commands once service logic is added.
    return AdminCommandResponse(
        protocol_version=payload.protocol_version,
        command=build_command_payload(payload, CommandTypeEnum.close_positions),
        target_bot_status=BotStatusEnum.closing_positions,
    )


@router.get("/licenses", response_model=LicenseListResponse)
def list_licenses(
    protocol_version: str = "1.0",
    _: AdminUser = Depends(get_current_admin_user),
) -> LicenseListResponse:
    # TODO: query licenses with filtering and pagination once read-side services are implemented.
    return LicenseListResponse(
        protocol_version=protocol_version,
        items=[
            LicenseSummary(
                license_key="LIC-STUB-001",
                status=LicenseStatusEnum.active,
                mode=ModeEnum.monitor,
                product_code="grid",
                bot_family="grid",
                strategy_code="grid_v1",
                owner_label="Stub Customer",
                plan_name="mvp-pro",
            )
        ],
    )


@router.get("/bots", response_model=BotListResponse)
def list_bots(protocol_version: str = "1.0", _: AdminUser = Depends(get_current_admin_user)) -> BotListResponse:
    # TODO: query bot_instances with filtering and paging once read-side services are implemented.
    return BotListResponse(
        protocol_version=protocol_version,
        items=[
            BotSummary(
                bot_instance_id="botinst_stub_001",
                license_key="LIC-STUB-001",
                product_code="grid",
                bot_family="grid",
                strategy_code="grid_v1",
                machine_fingerprint="fp_stub_001",
                protocol_version=protocol_version,
                status=BotStatusEnum.online,
            )
        ],
    )


@router.get("/bots/{bot_instance_id}", response_model=BotDetailResponse)
def get_bot(
    bot_instance_id: str,
    protocol_version: str = "1.0",
    _: AdminUser = Depends(get_current_admin_user),
) -> BotDetailResponse:
    # TODO: hydrate bot detail from bot_instances/state/command tables once read-side services exist.
    return BotDetailResponse(
        protocol_version=protocol_version,
        item=BotDetail(
            bot_instance_id=bot_instance_id,
            license_key="LIC-STUB-001",
            product_code="grid",
            bot_family="grid",
            strategy_code="grid_v1",
            machine_fingerprint="fp_stub_001",
            protocol_version=protocol_version,
            status=BotStatusEnum.online,
            hostname="stub-host",
            platform="linux",
            bot_version="0.1.0",
            session_id="sess_stub_001",
        ),
    )


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(protocol_version: str = "1.0", _: AdminUser = Depends(get_current_admin_user)) -> AlertListResponse:
    # TODO: query admin alerts with filters once alert generation and persistence are implemented.
    return AlertListResponse(
        protocol_version=protocol_version,
        items=[
            AlertSummary(
                alert_type="protocol_mismatch",
                severity="medium",
                status="open",
                license_key="LIC-STUB-001",
                bot_instance_id="botinst_stub_001",
                product_code="grid",
                bot_family="grid",
                strategy_code="grid_v1",
                summary="stub alert placeholder",
            )
        ],
    )
