from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib import error, parse, request

from app.demo.constants import (
    DEMO_BOT_FAMILY,
    DEMO_BOT_INSTANCE_ID,
    DEMO_HOSTNAME,
    DEMO_LICENSE_KEY,
    DEMO_MACHINE_FINGERPRINT,
    DEMO_PLATFORM,
    DEMO_PRODUCT_CODE,
    DEMO_PROTOCOL_VERSION,
    DEMO_SESSION_ID,
    DEMO_STRATEGY_CODE,
)


@dataclass(slots=True)
class SmokeContext:
    base_url: str
    admin_email: str
    admin_password: str
    bot_token: str
    admin_token: str | None = None
    command_ids: list[str] | None = None


def _http_json(method: str, url: str, *, payload: Any | None = None, headers: dict[str, str] | None = None) -> Any:
    request_headers = {"Accept": "application/json", **(headers or {})}
    data: bytes | None = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = request.Request(url, method=method, data=data, headers=request_headers)
    try:
        with request.urlopen(req, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else None
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        raise RuntimeError(f"{method} {url} -> HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def _expect(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _bot_headers(ctx: SmokeContext) -> dict[str, str]:
    return {"Authorization": f"Bearer {ctx.bot_token}"}


def _admin_headers(ctx: SmokeContext) -> dict[str, str]:
    _expect(bool(ctx.admin_token), "missing admin JWT from login step")
    return {"Authorization": f"Bearer {ctx.admin_token}"}


def run_smoke_tests(ctx: SmokeContext) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []

    live = _http_json("GET", f"{ctx.base_url}/health/live")
    _expect(live == {"status": "ok"}, "live health check did not return ok")
    steps.append({"step": "health_live", "status": "ok"})

    ready = _http_json("GET", f"{ctx.base_url}/health/ready")
    _expect(ready == {"status": "ok"}, "ready health check did not return ok")
    steps.append({"step": "health_ready", "status": "ok"})

    login = _http_json(
        "POST",
        f"{ctx.base_url}/api/v1/auth/login",
        payload={"email": ctx.admin_email, "password": ctx.admin_password},
    )
    ctx.admin_token = login["access_token"]
    _expect(login["user"]["email"] == ctx.admin_email, "admin login returned unexpected user")
    steps.append({"step": "admin_login", "status": "ok"})

    license_check = _http_json(
        "POST",
        f"{ctx.base_url}/api/v1/license/check",
        headers=_bot_headers(ctx),
        payload={
            "license_key": DEMO_LICENSE_KEY,
            "bot_instance_id": DEMO_BOT_INSTANCE_ID,
            "product_code": DEMO_PRODUCT_CODE,
            "bot_family": DEMO_BOT_FAMILY,
            "strategy_code": DEMO_STRATEGY_CODE,
            "protocol_version": DEMO_PROTOCOL_VERSION,
            "request_timestamp": _timestamp(),
        },
    )
    _expect(license_check["authorization"]["allowed"] is True, "license/check did not authorize demo license")
    steps.append({"step": "license_check", "status": "ok"})

    register = _http_json(
        "POST",
        f"{ctx.base_url}/api/v1/bot/register",
        headers=_bot_headers(ctx),
        payload={
            "license_key": DEMO_LICENSE_KEY,
            "product_code": DEMO_PRODUCT_CODE,
            "bot_family": DEMO_BOT_FAMILY,
            "strategy_code": DEMO_STRATEGY_CODE,
            "bot_instance_id": DEMO_BOT_INSTANCE_ID,
            "machine_fingerprint": DEMO_MACHINE_FINGERPRINT,
            "fingerprint_version": "1",
            "session_id": DEMO_SESSION_ID,
            "protocol_version": DEMO_PROTOCOL_VERSION,
            "request_timestamp": _timestamp(),
            "bot_version": "1.0.0-smoke",
            "hostname": DEMO_HOSTNAME,
            "platform": DEMO_PLATFORM,
        },
    )
    _expect(register["authorization"]["allowed"] is True, "bot/register did not authorize demo bot")
    steps.append({"step": "bot_register", "status": "ok"})

    heartbeat = _http_json(
        "POST",
        f"{ctx.base_url}/api/v1/bot/heartbeat",
        headers=_bot_headers(ctx),
        payload={
            "license_key": DEMO_LICENSE_KEY,
            "product_code": DEMO_PRODUCT_CODE,
            "bot_family": DEMO_BOT_FAMILY,
            "strategy_code": DEMO_STRATEGY_CODE,
            "bot_instance_id": DEMO_BOT_INSTANCE_ID,
            "session_id": DEMO_SESSION_ID,
            "protocol_version": DEMO_PROTOCOL_VERSION,
            "status": "online",
            "sent_at": _timestamp(),
            "warnings": ["smoke-test-heartbeat"],
        },
    )
    _expect(heartbeat["connectivity_status"] in {"online", "stale"}, "bot/heartbeat connectivity status was unexpected")
    steps.append({"step": "bot_heartbeat", "status": "ok"})

    state = _http_json(
        "POST",
        f"{ctx.base_url}/api/v1/bot/state",
        headers=_bot_headers(ctx),
        payload={
            "license_key": DEMO_LICENSE_KEY,
            "product_code": DEMO_PRODUCT_CODE,
            "bot_family": DEMO_BOT_FAMILY,
            "strategy_code": DEMO_STRATEGY_CODE,
            "bot_instance_id": DEMO_BOT_INSTANCE_ID,
            "session_id": DEMO_SESSION_ID,
            "protocol_version": DEMO_PROTOCOL_VERSION,
            "sent_at": _timestamp(),
            "bot_state": {
                "bot_status": "online",
                "session_status": "running",
                "connectivity_status": "online",
                "current_symbols": ["BTCUSDT"],
                "open_orders_count": 0,
                "open_positions_count": 0,
                "equity_snapshot": "10000.0000",
            },
            "symbol_states": [{"symbol": "BTCUSDT", "status": "watching"}],
            "position_snapshots": [{"symbol": "BTCUSDT", "side": "flat", "qty": 0}],
        },
    )
    _expect(state["bot_instance_id"] == DEMO_BOT_INSTANCE_ID, "bot/state did not return the demo bot instance id")
    steps.append({"step": "bot_state", "status": "ok"})

    alerts = _http_json("GET", f"{ctx.base_url}/api/v1/admin/alerts", headers=_admin_headers(ctx))
    _expect(any(alert.get("bot_instance_id") == DEMO_BOT_INSTANCE_ID for alert in alerts), "admin alerts did not include the demo bot")
    steps.append({"step": "admin_alerts", "status": "ok"})

    command_types = ["pause", "resume", "stop", "close-positions"]
    command_ids: list[str] = []
    for command_type in command_types:
        response = _http_json(
            "POST",
            f"{ctx.base_url}/api/v1/admin/bot/{command_type}",
            headers=_admin_headers(ctx),
            payload={"bot_instance_id": DEMO_BOT_INSTANCE_ID, "reason": f"smoke-test-{command_type}"},
        )
        _expect(response["status"] == "queued", f"admin {command_type} command was not queued")
        command_ids.append(response["command_id"])
    ctx.command_ids = command_ids
    steps.append({"step": "admin_bot_commands", "status": "ok"})

    query = parse.urlencode(
        {
            "license_key": DEMO_LICENSE_KEY,
            "product_code": DEMO_PRODUCT_CODE,
            "bot_family": DEMO_BOT_FAMILY,
            "strategy_code": DEMO_STRATEGY_CODE,
            "bot_instance_id": DEMO_BOT_INSTANCE_ID,
            "session_id": DEMO_SESSION_ID,
            "protocol_version": DEMO_PROTOCOL_VERSION,
            "request_timestamp": _timestamp(),
        }
    )
    commands = _http_json("GET", f"{ctx.base_url}/api/v1/bot/commands?{query}", headers=_bot_headers(ctx))
    command_map = {item["command_type"]: item for item in commands["commands"]}
    _expect(all(name in command_map for name in ["pause", "resume", "stop", "close_positions"]), "bot command poll did not return all expected commands")
    steps.append({"step": "bot_command_poll", "status": "ok"})

    for command in commands["commands"]:
        result = _http_json(
            "POST",
            f"{ctx.base_url}/api/v1/bot/command-result",
            headers=_bot_headers(ctx),
            payload={
                "license_key": DEMO_LICENSE_KEY,
                "product_code": DEMO_PRODUCT_CODE,
                "bot_family": DEMO_BOT_FAMILY,
                "strategy_code": DEMO_STRATEGY_CODE,
                "bot_instance_id": DEMO_BOT_INSTANCE_ID,
                "session_id": DEMO_SESSION_ID,
                "protocol_version": DEMO_PROTOCOL_VERSION,
                "command_id": command["command_id"],
                "command_type": command["command_type"],
                "result_status": "completed",
                "message": f"smoke completed {command['command_type']}",
                "details": {"source": "smoke-test"},
                "sent_at": _timestamp(),
            },
        )
        _expect(result["status"] == "completed", f"command result for {command['command_type']} was not marked completed")
    steps.append({"step": "bot_command_results", "status": "ok"})

    post_result_commands = _http_json("GET", f"{ctx.base_url}/api/v1/bot/commands?{query}", headers=_bot_headers(ctx))
    repeated_command_ids = {
        item["command_id"]
        for item in post_result_commands["commands"]
        if item["command_id"] in set(command_ids)
    }
    _expect(not repeated_command_ids, f"bot command poll re-delivered completed commands: {sorted(repeated_command_ids)}")
    steps.append({"step": "bot_command_poll_after_results", "status": "ok"})

    return steps


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MVP smoke tests against the current licensing backend.")
    parser.add_argument("--base-url", default=os.getenv("SMOKE_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--admin-email", default=os.getenv("BOOTSTRAP_ADMIN_EMAIL", "owner@example.com"))
    parser.add_argument("--admin-password", default=os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "change-me-admin-password"))
    parser.add_argument("--bot-token", default=os.getenv("BOT_API_TOKEN", "change-me-bot-token"))
    args = parser.parse_args()

    ctx = SmokeContext(
        base_url=args.base_url.rstrip("/"),
        admin_email=args.admin_email.strip().lower(),
        admin_password=args.admin_password,
        bot_token=args.bot_token,
    )
    try:
        results = run_smoke_tests(ctx)
    except Exception as exc:  # pragma: no cover - CLI reporting path
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2), file=sys.stderr)
        raise SystemExit(1) from exc

    print(
        json.dumps(
            {
                "ok": True,
                "base_url": ctx.base_url,
                "license_key": DEMO_LICENSE_KEY,
                "bot_instance_id": DEMO_BOT_INSTANCE_ID,
                "command_ids": ctx.command_ids or [],
                "steps": results,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
