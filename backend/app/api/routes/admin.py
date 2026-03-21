from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.dependencies.auth import get_current_admin_user
from app.models.admin_user import AdminUser
from app.schemas.admin import AdminAlertItem, AdminBotDetail, AdminBotItem, AdminCommandRequest, AdminCommandResponse, AdminLicenseItem, BlockLicenseRequest
from app.services import block_license, create_admin_bot_command, get_admin_bot_detail, list_admin_alerts, list_admin_bots, list_admin_licenses

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/licenses", response_model=list[AdminLicenseItem])
def read_licenses(_: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> list[AdminLicenseItem]:
    return [AdminLicenseItem.model_validate(item) for item in list_admin_licenses(db_session)]

@router.get("/bots", response_model=list[AdminBotItem])
def read_bots(_: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> list[AdminBotItem]:
    return [AdminBotItem.model_validate(item) for item in list_admin_bots(db_session)]

@router.get("/bots/{bot_instance_id}", response_model=AdminBotDetail)
def read_bot(bot_instance_id: str, _: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> AdminBotDetail:
    return AdminBotDetail.model_validate(get_admin_bot_detail(db_session, bot_instance_id))

@router.get("/alerts", response_model=list[AdminAlertItem])
def read_alerts(_: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> list[AdminAlertItem]:
    return [AdminAlertItem.model_validate(item) for item in list_admin_alerts(db_session)]

@router.post("/license/block", response_model=AdminCommandResponse)
def admin_block_license(payload: BlockLicenseRequest, admin_user: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> AdminCommandResponse:
    result = block_license(db_session, payload, admin_user)
    return AdminCommandResponse.model_validate({"ok": result["ok"], "status": result["status"]})

@router.post("/bot/pause", response_model=AdminCommandResponse)
def pause_bot(payload: AdminCommandRequest, admin_user: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> AdminCommandResponse:
    return AdminCommandResponse.model_validate(create_admin_bot_command(db_session, bot_instance_id=payload.bot_instance_id, command_type="pause", reason=payload.reason, admin_user=admin_user))

@router.post("/bot/resume", response_model=AdminCommandResponse)
def resume_bot(payload: AdminCommandRequest, admin_user: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> AdminCommandResponse:
    return AdminCommandResponse.model_validate(create_admin_bot_command(db_session, bot_instance_id=payload.bot_instance_id, command_type="resume", reason=payload.reason, admin_user=admin_user))

@router.post("/bot/stop", response_model=AdminCommandResponse)
def stop_bot(payload: AdminCommandRequest, admin_user: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> AdminCommandResponse:
    return AdminCommandResponse.model_validate(create_admin_bot_command(db_session, bot_instance_id=payload.bot_instance_id, command_type="stop", reason=payload.reason, admin_user=admin_user))

@router.post("/bot/close-positions", response_model=AdminCommandResponse)
def close_positions(payload: AdminCommandRequest, admin_user: AdminUser = Depends(get_current_admin_user), db_session: Session = Depends(get_db_session)) -> AdminCommandResponse:
    return AdminCommandResponse.model_validate(create_admin_bot_command(db_session, bot_instance_id=payload.bot_instance_id, command_type="close_positions", reason=payload.reason, admin_user=admin_user))
