from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.request_context import get_request_id
from app.models.domain import AuditLog


def write_audit_log(
    db: Session,
    *,
    actor_type: str,
    actor_id: str | None,
    action_type: str,
    target_type: str,
    target_id: str | None,
    license_key: str | None = None,
    bot_instance_id: str | None = None,
    product_code: str | None = None,
    bot_family: str | None = None,
    strategy_code: str | None = None,
    metadata: dict[str, Any] | list[Any] | None = None,
) -> None:
    payload_metadata: dict[str, Any] | list[Any] | None
    if isinstance(metadata, dict):
        payload_metadata = {"request_id": get_request_id(), **metadata}
    elif metadata is None:
        payload_metadata = {"request_id": get_request_id()}
    else:
        payload_metadata = metadata
    db.add(
        AuditLog(
            actor_type=actor_type,
            actor_id=actor_id,
            action_type=action_type,
            target_type=target_type,
            target_id=target_id,
            license_key=license_key,
            bot_instance_id=bot_instance_id,
            product_code=product_code,
            bot_family=bot_family,
            strategy_code=strategy_code,
            metadata_json=payload_metadata,
        )
    )
