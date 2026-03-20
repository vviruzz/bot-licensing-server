# Licensing + Admin MVP Specification

## 1. Purpose of the system

This document describes the **first contractual architecture step** for a future server-side licensing service and admin panel for the existing bot.

Goals of the MVP:

- license and track distributed copies of the bot;
- control which bot instances are allowed to run;
- allow manual operator actions from an admin panel;
- make unauthorized copying harder in a practical MVP way;
- support multiple bot products and strategy families on one server;
- stay compatible with the current bot architecture without changing current trading logic.

Important boundaries for this stage:

- this is **documentation only**;
- no server runtime is implemented here;
- no bot runtime integration is implemented here;
- `main.py` and the current trading logic must remain unchanged;
- the server and the bot should later be developed as **two dependent projects connected by one contract**.

---

## 2. Scope and MVP assumptions

The MVP is intentionally practical rather than “unbreakable”.

What the MVP should do:

- verify that a license is valid;
- identify a concrete bot installation and machine fingerprint;
- know whether a bot is online, stale, offline, paused, blocked, or stopping;
- receive regular heartbeats and state snapshots;
- allow an admin to issue simple remote commands;
- record audit history;
- detect suspicious usage patterns for manual review or policy enforcement;
- let one admin backend serve multiple bot products and strategy variants.

What the MVP does **not** try to do yet:

- fully prevent all reverse engineering or piracy;
- provide a complex distributed control plane;
- replace local bot safety logic;
- change order placement, reconciliation, or any trading session behavior.

---

## 3. Main entities

Below are the core entities for the contract between bot and server.

### 3.1 `license`

Represents the commercial or operational right to run one or more bot instances.

Suggested fields:

- `license_key`: unique external license identifier used by the bot.
- `license_id`: internal server UUID or numeric ID.
- `status`: `active | blocked | revoked | expired | suspicious`.
- `mode`: `off | monitor | enforce`.
- `product_code`: top-level commercial product code served by the platform.
- `bot_family`: bot family inside the product line.
- `strategy_code`: default or licensed strategy variant.
- `owner_label`: human-readable customer or owner name.
- `plan_name`: tariff or product plan.
- `max_instances`: allowed simultaneous bot instances.
- `max_fingerprints`: allowed distinct machine fingerprints.
- `allowed_protocol_min`: minimum supported protocol version.
- `allowed_protocol_max`: maximum supported protocol version.
- `allowed_bot_versions`: optional version mask or list.
- `allowed_products`: optional allowlist if one license can activate multiple products.
- `expires_at`: expiration timestamp if applicable.
- `blocked_reason`: optional human-readable reason.
- `suspicious_flag`: boolean quick marker for admin UI.
- `notes`: internal operator notes.
- `created_at`, `updated_at`: audit timestamps.

Meaning:

- `license_key` is the main contractual anchor.
- `status` defines whether the server will allow operation.
- `mode` controls whether the bot should only report data or must be authorized to trade.
- `product_code`, `bot_family`, and `strategy_code` make the contract multi-product from day one.

Example values:

- `product_code`: `grid`, `hedge`, `cover`
- `bot_family`: `grid`, `hedge`, `cover`
- `strategy_code`: `grid_v1`, `hedge_v1`

### 3.2 `bot_instance`

Represents one concrete installed/running copy of the bot.

Suggested fields:

- `bot_instance_id`: stable UUID generated once by the bot installation.
- `license_key`: bound license.
- `product_code`: product currently running on this installation.
- `bot_family`: family currently running on this installation.
- `strategy_code`: active strategy code configured for the runtime.
- `machine_fingerprint`: normalized machine identifier.
- `hostname`: OS hostname.
- `ip_address_last`: last public IP seen by server.
- `bot_version`: bot application version.
- `protocol_version`: protocol contract version.
- `platform`: OS family/version.
- `app_mode`: `off | monitor | enforce` from client config.
- `server_effective_mode`: mode returned by server.
- `status`: `online | offline | stale | paused | blocked | stopping | closing_positions`.
- `is_authorized`: whether current runtime is allowed.
- `authorized_until`: optional short-lived authorization expiry.
- `first_seen_at`, `last_seen_at`: visibility timestamps.
- `last_heartbeat_at`: last heartbeat timestamp.
- `last_state_sync_at`: last state snapshot timestamp.
- `last_error_code`: last contract-level error.
- `last_error_message`: short diagnostic message.

Meaning:

- one license can have multiple bot instances depending on policy;
- a bot instance is the operational object an admin controls;
- status is operational, while license status is commercial/policy-oriented;
- product/family/strategy fields prevent ambiguity when one backend serves different bot types.

### 3.3 `machine_fingerprint`

Represents a practical machine identity used for anti-copy monitoring.

Suggested fields:

- `machine_fingerprint`: normalized string or hash.
- `fingerprint_version`: algorithm version.
- `hardware_hint`: optional summarized machine traits.
- `os_hint`: optional summarized OS traits.
- `first_seen_ip`: first observed IP.
- `last_seen_ip`: latest observed IP.
- `first_seen_at`, `last_seen_at`: timestamps.
- `license_key_last`: last associated license.
- `risk_score`: simple numeric suspicion score.
- `allowlisted`: manual allow override.
- `denylisted`: manual deny override.

Meaning:

- this is not meant to be perfect hardware attestation;
- it is a practical signal for “same machine / new machine / suspicious machine”.

### 3.4 `operator` / `admin`

Represents a human who uses the admin panel.

Suggested fields:

- `admin_id`: internal ID.
- `email` or `login`: unique username.
- `display_name`: UI name.
- `role`: `owner | admin | support | viewer`.
- `status`: active/disabled.
- `password_hash` or external SSO reference.
- `mfa_enabled`: boolean.
- `last_login_at`: timestamp.
- `created_at`, `updated_at`: timestamps.

Meaning:

- roles must define who can view, block, pause, stop, or close positions.

### 3.5 `trading_session`

Represents one logical trading runtime session inside a bot.

Suggested fields:

- `session_id`: unique runtime session ID.
- `bot_instance_id`: owner instance.
- `license_key`: convenience linkage.
- `product_code`: product for this session.
- `bot_family`: family for this session.
- `strategy_code`: concrete strategy variant for this session.
- `account_label`: exchange account label.
- `subaccount_label`: optional subaccount identifier.
- `symbol`: traded market symbol.
- `started_at`: session start timestamp.
- `ended_at`: session end timestamp.
- `session_status`: `starting | active | paused | stopped | error`.
- `demo_mode`: boolean.
- `strategy_label`: optional human-readable strategy profile name.

Meaning:

- one bot instance may have one or multiple sessions over time;
- sessions are useful for audit, commands, and state history;
- session-level product/family/strategy fields allow one installation to run multiple supported profiles over time.

### 3.6 `heartbeat`

Represents a lightweight periodic signal that the bot is alive.

Suggested fields:

- `heartbeat_id`: internal ID.
- `bot_instance_id`: sender.
- `license_key`: license.
- `session_id`: optional current session.
- `product_code`: product dimension for routing and analytics.
- `bot_family`: family dimension for routing and analytics.
- `strategy_code`: strategy dimension for routing and analytics.
- `sent_at`: client timestamp.
- `received_at`: server timestamp.
- `status`: client-reported bot status.
- `latency_ms`: optional measured roundtrip or local metric.
- `public_ip`: server-observed IP or client-reported IP.
- `warnings`: optional compact warning list.

Meaning:

- heartbeats are small and frequent;
- they are used to determine online/stale/offline state and to deliver lightweight decisions.

### 3.7 `remote_command`

Represents a command created by the server/admin and delivered to a bot.

Suggested fields:

- `command_id`: unique ID.
- `target_license_key`: optional broad target.
- `target_bot_instance_id`: optional specific instance target.
- `target_session_id`: optional specific session target.
- `product_code`: required target product dimension.
- `bot_family`: optional stricter target family dimension.
- `strategy_code`: optional stricter target strategy dimension.
- `command_type`: command name.
- `risk_class`: `low-risk | medium-risk | high-risk`.
- `payload`: JSON object with parameters.
- `status`: `queued | delivered | acknowledged | running | completed | failed | expired | canceled`.
- `created_by_admin_id`: who issued it.
- `reason`: optional operator comment.
- `created_at`, `expires_at`: timestamps.
- `acknowledged_at`, `completed_at`: timestamps.
- `requires_license_recheck`: boolean.

Meaning:

- commands must be explicit, auditable, and idempotent where possible;
- product/family/strategy targeting prevents accidental cross-product command delivery.

### 3.8 `bot_state`

Represents the current snapshot of the bot from the server perspective.

Suggested fields:

- `bot_instance_id`
- `license_key`
- `session_id`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_status`
- `session_status`
- `connectivity_status`: `connected | grace | restricted | offline`
- `connectivity_mode`: `off | monitor | enforce`
- `grace_until`: optional timestamp for cached authorization grace.
- `can_open_new_orders`: boolean.
- `can_manage_existing_orders`: boolean.
- `close_only_mode`: boolean.
- `last_command_id`: latest relevant command.
- `last_command_status`: result summary.
- `current_symbols`: array of active symbols.
- `open_orders_count`: integer.
- `open_positions_count`: integer.
- `equity_snapshot`: optional numeric summary.
- `updated_at`: timestamp.

Meaning:

- `bot_state` is the server’s operational view of one running bot;
- connectivity fields make offline policy visible in admin UX and audit.

### 3.9 `symbol_state`

Represents per-symbol runtime state.

Suggested fields:

- `bot_instance_id`
- `session_id`
- `symbol`
- `symbol_status`: `idle | active | paused | close_only | error`.
- `side_mode`: `long | short | both | none`.
- `grid_enabled`: boolean.
- `open_orders_count`
- `position_size_long`
- `position_size_short`
- `unrealized_pnl`
- `last_exchange_sync_at`
- `last_update_at`

Meaning:

- lets the admin see not just “bot is online” but also “what is happening per symbol”.

### 3.10 `position_snapshot`

Represents a compact position record attached to a state update.

Suggested fields:

- `bot_instance_id`
- `session_id`
- `symbol`
- `position_idx`: for hedge/one-way compatibility.
- `side`: `long | short | flat`.
- `qty`
- `entry_price`
- `mark_price`
- `liq_price`: optional.
- `unrealized_pnl`
- `leverage`: optional.
- `margin_mode`: optional.
- `updated_at`

Meaning:

- this is not a full ledger;
- it is an operational snapshot for admin visibility and emergency actions.

---

## 4. Required identifiers

The following identifiers should be mandatory in the protocol.

### 4.1 `license_key`

- Primary external license identifier.
- Sent by the bot during register/check, heartbeat, and state sync.
- Stable across bot restarts.

### 4.2 `bot_instance_id`

- Stable installation/runtime identity generated once on the client side.
- Must persist across restarts of the same installed bot.
- Must not be regenerated on every launch.

### 4.3 `machine_fingerprint`

- Stable host identity derived from practical machine traits.
- Used for anti-copy monitoring.
- Algorithm must have a version field so it can evolve later.

### 4.4 `session_id`

- Runtime session identifier.
- New value for each distinct bot launch or trading session, depending on final implementation.
- Must be unique enough for audit and command correlation.

### 4.5 `account_label` / `subaccount_label`

- Human-readable account identifiers.
- Important for admin clarity when one license uses multiple exchange contexts.
- Should not expose secrets.

### 4.6 `symbol`

- Standard exchange symbol, for example `BTCUSDT`.
- Must use a normalized format shared by bot and server.

### 4.7 `protocol_version`

- Explicit version of the bot↔server contract.
- Required in every request.
- Lets the server reject or degrade unsupported clients in a controlled way.

### 4.8 `product_code`

- Required product discriminator for multi-product hosting.
- Must be present on `license`, `bot_instance`, `trading_session`, state sync payloads, admin filters, and all relevant API examples.
- Example values: `grid`, `hedge`, `cover`.

### 4.9 `bot_family`

- Required family discriminator when several related bots share one product line or backend.
- Must be present anywhere a command, state, or filter could otherwise target the wrong bot class.
- Example values: `grid`, `hedge`, `cover`.

### 4.10 `strategy_code`

- Required strategy discriminator for versioned strategies or presets.
- Must be present on `license`, `bot_instance`, `trading_session`, and state sync.
- Example values: `grid_v1`, `hedge_v1`.

---

## 5. Bot ↔ server MVP interaction flow

### 5.1 Startup: register/check license

On bot startup:

1. Bot loads local config.
2. Bot determines local licensing mode: `off`, `monitor`, or `enforce`.
3. If mode is `off`, the bot may skip server interaction entirely.
4. If mode is `monitor` or `enforce`, the bot calls registration/license-check.
5. Server validates `license_key`, `bot_instance_id`, `machine_fingerprint`, version compatibility, product/family/strategy compatibility, and basic risk rules.
6. Server returns:
   - current license status;
   - effective mode;
   - whether runtime is authorized;
   - heartbeat interval;
   - state sync interval;
   - polling interval for commands;
   - optional warning or policy flags.

MVP rule:

- `monitor`: startup should continue even if authorization is denied, but warnings should be shown/logged.
- `enforce`: live trading must not be allowed unless the server authorizes runtime.

### 5.2 Heartbeat every N seconds

- Bot sends a lightweight heartbeat every `N` seconds.
- Recommended MVP interval: **15–30 seconds**.
- Heartbeat should be much smaller than full state sync.
- Server updates `last_seen_at`, bot status, and IP observations.
- Server may include pending command metadata or short policy changes in response.

### 5.3 Periodic state sync

- Bot sends a fuller operational snapshot less frequently than heartbeat.
- Recommended MVP interval: **30–120 seconds**.
- State sync includes current status, symbol states, compact position snapshots, and product/family/strategy identifiers.
- State sync is also useful immediately after significant changes:
  - session start;
  - session stop;
  - pause/resume;
  - command completion;
  - critical error.

### 5.4 Command delivery model: polling first, push later

MVP recommendation:

- use **polling** first;
- do not require WebSocket or push in MVP.

Reason:

- simpler operationally;
- easier to audit and retry;
- enough for admin commands like pause/stop/close positions.

Recommended polling interval:

- **5–15 seconds** while online.

Future option:

- add push/WebSocket later without changing command semantics.

### 5.5 Server response model

Every server response should consistently include:

- `ok`: boolean.
- `request_id`: echoed or server-generated request ID.
- `server_time`: ISO timestamp.
- `protocol_version`: server protocol version.
- `license_status`: current license status if relevant.
- `bot_status`: effective bot status if relevant.
- `effective_mode`: `off | monitor | enforce` if relevant.
- `authorization`: object describing whether bot may continue and under what limits.
- `errors`: array of structured error objects.
- `warnings`: array of short warning objects/messages.

### 5.6 Offline and stale bot handling

Recommended server-side interpretation:

- `online`: heartbeat seen within expected interval.
- `stale`: no heartbeat for about **2 heartbeat windows**.
- `offline`: no heartbeat for about **4 heartbeat windows**.

Example with 15-second heartbeat:

- `online`: last heartbeat within 0–30s;
- `stale`: 31–60s;
- `offline`: 61s+.

Behavior:

- stale bots remain visible and may be marked yellow in UI;
- offline bots are marked unavailable for commands;
- if a previously online bot comes back, it should re-register or at least immediately re-heartbeat and re-check authorization;
- pending commands may expire if the bot remains offline too long.

### 5.7 Connectivity and offline policy

This section fixes the runtime policy when the licensing server is unreachable.

#### A. `mode = off`

- No server dependency is expected.
- No grace timer is needed.
- Bot may continue local operation because licensing integration is intentionally disabled.
- Admin panel should display such runtimes, if imported later, as unmanaged/off-contract rather than online.

#### B. `mode = monitor`

- Server is advisory, not mandatory.
- Recommended grace period: unlimited from a trading-permission perspective, but operational alerts should start immediately after stale/offline thresholds.
- During degraded connectivity, the bot may continue:
  - placing new orders;
  - managing existing orders;
  - closing positions;
  - pausing locally if local safety logic decides so.
- Recommended admin-side posture:
  - raise stale/offline alerts;
  - do not auto-block trading solely because the server is unreachable.

#### C. `mode = enforce`

- Server authorization is mandatory for live operation.
- Recommended grace period: **5–30 minutes** after the last successful authorization or policy refresh.
- `authorized_until` is the normative timer; the client should not invent a longer local grace period.

During the grace period, the recommended behavior is:

- `no new orders`: **recommended** once the bot enters degraded connectivity state.
- `manage existing orders`: **allowed** so the bot can safely manage already-open structures and reduce operational drift.
- `close only`: **allowed and recommended** if local safety logic or admin policy wants active exposure reduction.
- `pause`: **allowed** and recommended as the simplest visible state transition.

After the grace period expires in `enforce` mode, the recommended behavior is:

- **forbidden**: opening any new orders;
- **forbidden**: resuming normal trading from paused/restricted state;
- **allowed**: managing or canceling existing orders if that is necessary for safe wind-down;
- **allowed**: close-only actions that reduce or eliminate existing exposure;
- **recommended default posture**: move to `pause` + `close_only_mode = true`.

Recommended state model after grace expiry:

- `can_open_new_orders = false`
- `can_manage_existing_orders = true`
- `close_only_mode = true`
- `connectivity_status = restricted`

Recommended admin wording:

- “license server unreachable, grace active” during grace period;
- “license server unreachable, trading restricted after grace expiry” after grace period.

---

## 6. HTTP API MVP

JSON only. UTF-8. HTTPS required in production.

Common request headers:

- `Authorization: Bearer <bot_token_or_signed_token>`
- `Content-Type: application/json`
- `X-Request-Timestamp: <unix_or_iso_timestamp>`
- `X-Request-Id: <uuid>`
- optional request signature header in later hardening stage

Common response envelope:

```json
{
  "ok": true,
  "request_id": "req_123",
  "server_time": "2026-03-20T12:00:00Z",
  "protocol_version": "1.0",
  "errors": [],
  "warnings": []
}
```

### 6.1 `POST /api/v1/bot/register`

**Purpose**

Initial registration and startup authorization for a bot instance.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "machine_fingerprint": "fp_abc",
  "fingerprint_version": "1",
  "session_id": "sess_001",
  "protocol_version": "1.0",
  "bot_version": "0.1.0",
  "hostname": "trader-pc",
  "platform": "windows-11",
  "account_label": "main-demo",
  "subaccount_label": "",
  "mode": "monitor",
  "demo_mode": true,
  "symbols": ["BTCUSDT", "ETHUSDT"]
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `machine_fingerprint`
- `session_id`
- `protocol_version`
- `bot_version`
- `mode`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_123",
  "server_time": "2026-03-20T12:00:00Z",
  "protocol_version": "1.0",
  "license_status": "active",
  "bot_status": "online",
  "effective_mode": "monitor",
  "authorization": {
    "allowed": true,
    "reason_code": null,
    "message": "allowed",
    "authorized_until": "2026-03-20T12:30:00Z"
  },
  "timers": {
    "heartbeat_sec": 15,
    "state_sync_sec": 60,
    "command_poll_sec": 10
  },
  "flags": {
    "suspicious": false,
    "license_recheck_required": false
  },
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `license_not_found`
- `license_blocked`
- `license_expired`
- `protocol_unsupported`
- `product_not_allowed`
- `strategy_not_allowed`
- `fingerprint_denied`
- `too_many_instances`
- `too_many_fingerprints`
- `invalid_request`
- `auth_failed`

### 6.2 `POST /api/v1/bot/heartbeat`

**Purpose**

Keepalive signal and lightweight policy refresh.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "protocol_version": "1.0",
  "status": "online",
  "account_label": "main-demo",
  "subaccount_label": "",
  "symbol": "BTCUSDT",
  "sent_at": "2026-03-20T12:00:15Z"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `protocol_version`
- `status`
- `sent_at`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_124",
  "server_time": "2026-03-20T12:00:15Z",
  "protocol_version": "1.0",
  "license_status": "active",
  "bot_status": "online",
  "effective_mode": "monitor",
  "authorization": {
    "allowed": true,
    "reason_code": null,
    "message": "heartbeat accepted"
  },
  "pending_commands": 1,
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `bot_instance_unknown`
- `license_mismatch`
- `product_mismatch`
- `protocol_unsupported`
- `stale_timestamp`
- `auth_failed`

### 6.3 `POST /api/v1/bot/state`

**Purpose**

Periodic operational snapshot for admin visibility and audit.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "protocol_version": "1.0",
  "bot_state": {
    "product_code": "grid",
    "bot_family": "grid",
    "strategy_code": "grid_v1",
    "bot_status": "online",
    "session_status": "active",
    "connectivity_status": "connected",
    "connectivity_mode": "monitor",
    "can_open_new_orders": true,
    "can_manage_existing_orders": true,
    "close_only_mode": false,
    "current_symbols": ["BTCUSDT"]
  },
  "symbol_states": [
    {
      "symbol": "BTCUSDT",
      "symbol_status": "active",
      "side_mode": "both",
      "grid_enabled": true,
      "open_orders_count": 12,
      "position_size_long": 0.01,
      "position_size_short": 0.00,
      "unrealized_pnl": 4.25
    }
  ],
  "position_snapshots": [
    {
      "symbol": "BTCUSDT",
      "position_idx": 1,
      "side": "long",
      "qty": 0.01,
      "entry_price": 62000,
      "mark_price": 62100,
      "unrealized_pnl": 1.0
    }
  ],
  "sent_at": "2026-03-20T12:01:00Z"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `protocol_version`
- `bot_state`
- `sent_at`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_125",
  "server_time": "2026-03-20T12:01:00Z",
  "protocol_version": "1.0",
  "accepted": true,
  "license_status": "active",
  "bot_status": "online",
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `payload_too_large`
- `invalid_symbol_state`
- `invalid_position_snapshot`
- `product_mismatch`
- `protocol_unsupported`
- `auth_failed`

### 6.4 `GET /api/v1/bot/commands`

**Purpose**

Bot polls for pending commands.

**Query parameters**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `session_id` optional
- `protocol_version`
- `limit` optional

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `protocol_version`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_126",
  "server_time": "2026-03-20T12:01:05Z",
  "protocol_version": "1.0",
  "commands": [
    {
      "command_id": "cmd_001",
      "product_code": "grid",
      "bot_family": "grid",
      "strategy_code": "grid_v1",
      "command_type": "pause",
      "risk_class": "medium-risk",
      "payload": {},
      "created_at": "2026-03-20T12:01:02Z",
      "expires_at": "2026-03-20T12:06:02Z",
      "reason": "manual admin action",
      "requires_ack": true
    }
  ],
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `bot_instance_unknown`
- `license_mismatch`
- `product_mismatch`
- `protocol_unsupported`
- `auth_failed`

### 6.5 `POST /api/v1/bot/command-result`

**Purpose**

Bot acknowledges and reports command execution result.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "protocol_version": "1.0",
  "command_id": "cmd_001",
  "command_type": "pause",
  "result_status": "completed",
  "message": "new orders paused",
  "details": {
    "can_open_new_orders": false
  },
  "sent_at": "2026-03-20T12:01:08Z"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `protocol_version`
- `command_id`
- `command_type`
- `result_status`
- `sent_at`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_127",
  "server_time": "2026-03-20T12:01:08Z",
  "protocol_version": "1.0",
  "accepted": true,
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `command_not_found`
- `command_expired`
- `command_target_mismatch`
- `invalid_result_status`
- `auth_failed`

### 6.6 `POST /api/v1/license/check`

**Purpose**

Standalone license validation endpoint. Useful for startup or explicit recheck.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "machine_fingerprint": "fp_abc",
  "protocol_version": "1.0",
  "bot_version": "0.1.0",
  "mode": "enforce"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_instance_id`
- `machine_fingerprint`
- `protocol_version`
- `mode`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_128",
  "server_time": "2026-03-20T12:01:10Z",
  "protocol_version": "1.0",
  "license_status": "active",
  "effective_mode": "enforce",
  "authorization": {
    "allowed": true,
    "reason_code": null,
    "message": "license valid"
  },
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `license_not_found`
- `license_blocked`
- `license_expired`
- `product_not_allowed`
- `strategy_not_allowed`
- `fingerprint_denied`
- `protocol_unsupported`
- `auth_failed`

### 6.7 `POST /api/v1/admin/license/block`

**Purpose**

Admin blocks a license.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "reason": "suspected sharing",
  "block_mode": "blocked"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `reason`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_129",
  "server_time": "2026-03-20T12:02:00Z",
  "protocol_version": "1.0",
  "license_status": "blocked",
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `license_not_found`
- `forbidden`
- `invalid_transition`

### 6.8 `POST /api/v1/admin/bot/pause`

**Purpose**

Admin requests pause of new trading actions for a bot.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "reason": "manual pause from admin"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `bot_instance_id`
- `reason`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_130",
  "server_time": "2026-03-20T12:02:05Z",
  "protocol_version": "1.0",
  "queued_command_id": "cmd_002",
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `bot_not_found`
- `bot_offline`
- `forbidden`
- `duplicate_pending_command`

### 6.9 `POST /api/v1/admin/bot/resume`

**Purpose**

Admin requests resume after pause.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "reason": "resume approved"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `bot_instance_id`
- `reason`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_131",
  "server_time": "2026-03-20T12:02:10Z",
  "protocol_version": "1.0",
  "queued_command_id": "cmd_003",
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `bot_not_found`
- `invalid_state`
- `forbidden`

### 6.10 `POST /api/v1/admin/bot/stop`

**Purpose**

Admin requests graceful stop of trading activity.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "reason": "operator stop"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `bot_instance_id`
- `reason`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_132",
  "server_time": "2026-03-20T12:02:15Z",
  "protocol_version": "1.0",
  "queued_command_id": "cmd_004",
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `bot_not_found`
- `bot_offline`
- `forbidden`

### 6.11 `POST /api/v1/admin/bot/close-positions`

**Purpose**

Admin requests emergency or operator-driven position closure.

**Request JSON**

```json
{
  "license_key": "LIC-XXXXX",
  "product_code": "grid",
  "bot_family": "grid",
  "strategy_code": "grid_v1",
  "bot_instance_id": "botinst_123",
  "session_id": "sess_001",
  "reason": "risk intervention",
  "symbols": ["BTCUSDT"],
  "close_mode": "all"
}
```

**Required fields**

- `license_key`
- `product_code`
- `bot_family`
- `bot_instance_id`
- `reason`

**Response JSON**

```json
{
  "ok": true,
  "request_id": "req_133",
  "server_time": "2026-03-20T12:02:20Z",
  "protocol_version": "1.0",
  "queued_command_id": "cmd_005",
  "errors": [],
  "warnings": []
}
```

**Possible errors**

- `bot_not_found`
- `bot_offline`
- `forbidden`
- `invalid_symbols`

---

## 7. License and bot statuses

### 7.1 License statuses

- `active` — license is valid and normally allowed.
- `blocked` — manually or automatically blocked; bot should not be allowed in `enforce` mode.
- `revoked` — permanently invalidated.
- `expired` — term ended.
- `suspicious` — usable according to policy, but marked for review and possible limited handling.

Recommended interpretation:

- `monitor` mode may continue operating under `suspicious`, but should log warnings.
- `enforce` mode may either deny immediately or allow only by explicit operator policy.

### 7.2 Bot statuses

- `online` — heartbeat is fresh.
- `offline` — bot is not reachable within timeout policy.
- `stale` — heartbeat delay suggests degraded connectivity.
- `paused` — bot remains online but should not open new orders.
- `blocked` — server policy currently denies operation.
- `stopping` — graceful stop command in progress.
- `closing_positions` — close-all or close-selected positions in progress.

---

## 8. Server → bot command set

Commands should be explicit, auditable, and confirmed by `command-result`.

### 8.1 Command risk classes and admin policy

For MVP, remote commands should be grouped into explicit risk classes.

| Command | Risk class | Required admin role | Reason mandatory | Two-step UI confirmation recommended |
|---|---|---:|---:|---:|
| `noop` | low-risk | `support` or higher | no | no |
| `recheck_license` | low-risk | `support` or higher | no | no |
| `pause` | medium-risk | `admin` or `owner` | yes | yes |
| `resume` | medium-risk | `admin` or `owner` | yes | yes |
| `stop_new_orders` | medium-risk | `admin` or `owner` | yes | yes |
| `stop` | medium-risk | `admin` or `owner` | yes | yes |
| `cancel_all_orders` | high-risk | `owner` or specially privileged `admin` | yes | yes |
| `close_all_positions` | high-risk | `owner` or specially privileged `admin` | yes | yes |
| `shutdown` | high-risk | `owner` only by default | yes | yes |

Notes:

- `viewer` should never be allowed to issue commands.
- `support` is intended for observation and safe low-risk maintenance actions only.
- High-risk commands should produce especially prominent audit records and alert/event entries.

### 8.2 `noop`

**What it does**

- No operational change.
- Useful to test command path or refresh command acknowledgment logic.

**Confirmation**

- Bot responds with `completed` immediately.

**Safety**

- Can be used by support/admin roles.

### 8.3 `pause`

**What it does**

- Bot should stop opening new orders.
- Existing risk management and safe handling of already-open structures should continue.

**Confirmation**

- Bot reports `acknowledged` when accepted.
- Bot reports `completed` when pause state is active.
- State sync should show `can_open_new_orders = false`.

**Safety**

- Idempotent.
- Requires authorized admin role.
- Must not silently alter trading rules beyond “pause new actions”.

### 8.4 `resume`

**What it does**

- Bot may resume normal trading if license and local safety conditions allow.

**Confirmation**

- Bot reports `completed` when resume state becomes active.

**Safety**

- Only valid after prior paused/restricted state.
- In `enforce` mode, server must still confirm license is active.

### 8.5 `stop_new_orders`

**What it does**

- Stronger semantic alias for “do not place any new orders”.
- Can coexist with continued management of existing exposure.

**Confirmation**

- Bot reports `completed` and state shows no new-order permission.

**Safety**

- Prefer idempotent handling.
- Useful if pause semantics later split into finer modes.

### 8.6 `cancel_all_orders`

**What it does**

- Bot attempts to cancel all currently open exchange orders.

**Confirmation**

- Bot reports `running` then `completed` or `failed`.
- Result should include count of canceled, failed, and remaining orders.

**Safety**

- High-impact command.
- Must be restricted to higher privilege roles.
- Requires clear audit reason.

### 8.7 `close_all_positions`

**What it does**

- Bot attempts to close all current positions, ideally in a safe and explicit manner.

**Confirmation**

- Bot reports progress and final result.
- Final state sync should show zero open positions if successful.

**Safety**

- Highest-impact command.
- Must require strong authorization and audit trail.
- Command payload may later include symbol filters or close mode.

### 8.8 `shutdown`

**What it does**

- Bot stops trading activity and then shuts down the application process gracefully.

**Confirmation**

- Bot should send `acknowledged`, attempt graceful shutdown, optionally send final `completed` if possible.

**Safety**

- Use sparingly.
- Must not be issued accidentally by low-privilege users.

### 8.9 `recheck_license`

**What it does**

- Bot immediately re-runs license validation.

**Confirmation**

- Bot reports the recheck result and updated authorization state.

**Safety**

- Safe low-impact command.
- Useful after manual allow/deny decisions.

---

## 9. Anti-copy / anti-abuse MVP logic

The MVP should focus on detection and controlled enforcement, not impossible protection.

### 9.1 One license on multiple fingerprints

Detection:

- track distinct `machine_fingerprint` values per `license_key`;
- compare against `max_fingerprints` policy.

MVP action:

- if limit exceeded, mark license `suspicious`;
- optionally deny new registrations in `enforce` mode;
- show the event clearly in admin UI.

### 9.2 One license from multiple IPs

Detection:

- track recent distinct public IPs per license and per bot instance.

MVP action:

- flag rapid IP switching or concurrent IP activity;
- do not auto-block by default if IP movement may be legitimate;
- use as a risk signal rather than sole decision factor.

### 9.3 Too-frequent host changes

Detection:

- new `machine_fingerprint` appears repeatedly within short periods.

MVP action:

- increase `risk_score`;
- mark `suspicious`;
- optionally require manual allow in `enforce` mode.

### 9.4 Simultaneous operation of multiple copies

Detection:

- same `license_key` appears online at the same time from different `bot_instance_id` and/or different fingerprints.

MVP action:

- if license plan allows only one active instance, reject new runtime or mark both suspicious;
- if multiple instances are allowed, still show concurrency in UI.

### 9.5 Version or protocol mismatch

Detection:

- unsupported `protocol_version` or blocked `bot_version`.

MVP action:

- reject unsupported protocol;
- optionally warn but allow known older bot versions in `monitor` mode.

### 9.6 Manual allow / deny by owner

MVP recommendation:

- admin must be able to:
  - allow a new fingerprint;
  - deny a fingerprint;
  - mark an event as expected/approved;
  - block or unblock a license.

This is important because practical operations always produce edge cases.

### 9.7 Risk scoring approach

Simple additive score is enough for MVP.

Possible signals:

- +30 new fingerprint under same license
- +20 concurrent online bot on same single-instance license
- +15 rapid IP change
- +25 denied fingerprint attempted
- +20 unsupported or unexpected protocol/version

Example thresholds:

- `0–29`: normal
- `30–59`: watch
- `60+`: suspicious

---

## 10. Bot integration modes

### 10.1 `off`

Meaning:

- server integration is disabled;
- bot can operate without contacting the server.

Behavior:

- no register, heartbeat, state sync, or command polling required;
- intended for local development or transitional rollout.

### 10.2 `monitor`

Meaning:

- bot reports to the server, but the server does not hard-block runtime.

Behavior:

- register/check still happens;
- heartbeats and state sync still happen;
- warnings and suspicious signals are recorded;
- remote commands may still be accepted if enabled by product policy;
- if server is unavailable, bot may continue.

Use case:

- safe rollout phase before enforcing server dependency.

### 10.3 `enforce`

Meaning:

- server authorization is required for live operation.

Behavior:

- startup requires successful authorization;
- if server denies license, live trading must not start;
- if server becomes unreachable later, policy must define grace behavior.

Recommended MVP grace behavior:

- use `authorized_until` as the authoritative grace timer;
- recommended grace period is **5–30 minutes**;
- before grace expiry, prefer `pause` / `no new orders` while still allowing safe management of current exposure;
- after grace expiry, move to `close_only_mode = true` and keep `can_open_new_orders = false`.

Important note:

- exact runtime enforcement in the bot should be implemented later, but the contract should already support it.

---

## 11. Minimal server database schema

A simple relational schema is enough for MVP.

### 11.1 `licenses`

Key fields:

- `id`
- `license_key` (unique)
- `status`
- `mode`
- `product_code`
- `bot_family`
- `strategy_code`
- `owner_label`
- `plan_name`
- `max_instances`
- `max_fingerprints`
- `allowed_protocol_min`
- `allowed_protocol_max`
- `expires_at`
- `suspicious_flag`
- `blocked_reason`
- `notes`
- `created_at`
- `updated_at`

### 11.2 `bot_instances`

Key fields:

- `id`
- `bot_instance_id` (unique)
- `license_id` (FK)
- `product_code`
- `bot_family`
- `strategy_code`
- `machine_fingerprint`
- `fingerprint_version`
- `hostname`
- `ip_address_last`
- `bot_version`
- `protocol_version`
- `platform`
- `status`
- `is_authorized`
- `authorized_until`
- `first_seen_at`
- `last_seen_at`
- `last_state_sync_at`
- `last_error_code`
- `last_error_message`

### 11.3 `bot_heartbeats`

Key fields:

- `id`
- `bot_instance_id` (FK)
- `license_id` (FK)
- `session_id`
- `product_code`
- `bot_family`
- `strategy_code`
- `status`
- `sent_at`
- `received_at`
- `ip_address`
- `warnings_json`

### 11.4 `bot_states`

Key fields:

- `id`
- `bot_instance_id` (FK)
- `license_id` (FK)
- `session_id`
- `product_code`
- `bot_family`
- `strategy_code`
- `bot_status`
- `session_status`
- `connectivity_status`
- `grace_until`
- `current_symbols_json`
- `symbol_states_json`
- `position_snapshots_json`
- `open_orders_count`
- `open_positions_count`
- `equity_snapshot`
- `received_at`

MVP note:

- storing symbol and position details as JSON is acceptable initially.

### 11.5 `remote_commands`

Key fields:

- `id`
- `command_id` (unique)
- `license_id` (FK)
- `bot_instance_id` (FK, nullable)
- `session_id` (nullable)
- `product_code`
- `bot_family`
- `strategy_code`
- `command_type`
- `risk_class`
- `payload_json`
- `status`
- `reason`
- `created_by_admin_id`
- `created_at`
- `expires_at`
- `acknowledged_at`
- `completed_at`

### 11.6 `command_results`

Key fields:

- `id`
- `command_id` (FK)
- `bot_instance_id` (FK)
- `result_status`
- `message`
- `details_json`
- `sent_at`
- `received_at`

### 11.7 `audit_log`

Key fields:

- `id`
- `actor_type` (`admin | system | bot`)
- `actor_id`
- `action_type`
- `target_type`
- `target_id`
- `license_key`
- `bot_instance_id`
- `product_code`
- `bot_family`
- `strategy_code`
- `metadata_json`
- `created_at`

Purpose:

- central immutable-ish history of admin and system actions.

### 11.8 `admin_alerts`

Key fields:

- `id`
- `alert_type`
- `severity`
- `status` (`open | acknowledged | resolved`)
- `license_id` (FK, nullable)
- `bot_instance_id` (FK, nullable)
- `session_id` (nullable)
- `product_code`
- `bot_family`
- `strategy_code`
- `summary`
- `details_json`
- `first_seen_at`
- `last_seen_at`
- `resolved_at`

Purpose:

- drive the admin alert/event stream without mixing incident state into the pure audit log.

---

## 12. MVP admin panel

The first version of the admin UI should be intentionally simple and operational.

### 12.1 Required screens / widgets

#### A. License list

Must show:

- license key
- product code
- bot family
- strategy code
- owner/customer label
- status
- mode
- suspicious mark
- max instances
- active instances count
- last seen
- notes or short flags

#### B. Active bots list

Must show:

- bot instance ID
- license key
- product code
- bot family
- strategy code
- IP
- machine fingerprint
- bot version
- protocol version
- status
- effective mode
- symbols
- account/subaccount label
- last seen
- suspicious mark
- connectivity status (`connected | grace | restricted | offline`)

#### C. Bot details view

Must show:

- current bot state
- recent heartbeats
- current symbol states
- compact position snapshots
- recent commands and results
- recent audit events
- active alerts/incidents related to that bot, session, license, product, and strategy

### 12.2 Required actions

Admin must be able to issue:

- `pause`
- `resume`
- `stop`
- `close positions`
- `block/unblock license`
- `mark suspicious`
- `clear suspicious` or mark reviewed

### 12.3 Required filters

At minimum:

- by license
- by product code
- by bot family
- by strategy code
- by IP
- by status
- by suspicious flag
- by bot version
- by connectivity status

### 12.4 UI priorities

The MVP admin panel is an operational tool, not a BI dashboard.

Priority order:

1. quickly find which bots are online;
2. quickly identify suspicious duplicates;
3. quickly send a safe command;
4. quickly understand last seen and current status;
5. quickly distinguish which product/family/strategy a bot belongs to.

### 12.5 Admin alerts / incident stream

The admin panel should include a visible alert/event stream with filters by severity, status, product, family, strategy, license, and bot.

The stream should contain at least the following alert groups.

#### A. Suspicious incidents

Examples:

- same license used on a new fingerprint;
- same single-instance license active on multiple bots;
- denied fingerprint attempted registration;
- unusual product/family/strategy mismatch for a license.

UI should show:

- severity;
- alert type;
- product/family/strategy;
- license key;
- bot instance ID(s);
- machine fingerprint/IP summary;
- first seen / last seen;
- current status (`open | acknowledged | resolved`);
- operator notes and review actions.

#### B. Stale / offline alerts

Examples:

- heartbeat stale beyond threshold;
- bot offline beyond threshold;
- enforce-mode bot in grace period;
- enforce-mode bot restricted after grace expiry.

UI should show:

- last successful heartbeat;
- grace timer or restriction timer;
- current permissions (`no new orders`, `manage existing`, `close only`, `pause`);
- whether commands are still deliverable.

#### C. Duplicate license usage alerts

Examples:

- concurrent active instances above `max_instances`;
- concurrent fingerprints above `max_fingerprints`;
- same license active under multiple product or family combinations unexpectedly.

UI should show:

- affected license and policy limit;
- all active bot instances involved;
- product/family/strategy for each runtime;
- timestamps and IP/fingerprint summary;
- recommended operator actions.

#### D. Failed command alerts

Examples:

- command timed out without acknowledgment;
- command result reported `failed`;
- command target was offline or mismatched;
- repeated duplicate pending commands.

UI should show:

- command ID and command type;
- risk class;
- issuing admin;
- required reason;
- target license/bot/session/product/family/strategy;
- failure code/message;
- retry recommendation.

#### E. Protocol mismatch alerts

Examples:

- unsupported `protocol_version`;
- bot version outside allowed range;
- payload shape not matching product/family/strategy contract.

UI should show:

- reported protocol version and bot version;
- expected supported range;
- affected product/family/strategy;
- whether the runtime was denied, warned, or degraded to monitor-only handling.

---

## 13. Security baseline

The MVP should use practical minimum controls.

### 13.1 HTTPS

- All production traffic must use HTTPS.
- No plain HTTP outside local development.

### 13.2 Bearer token or signed token

- Bot requests should include a bearer token or signed access token.
- Admin requests must use separate admin authentication.
- Bot token scope should be limited to bot endpoints.

### 13.3 Rate limiting

- Rate limit bot endpoints per IP and per bot instance.
- Rate limit admin actions, especially command endpoints.
- Prevent heartbeat floods or brute-force license probing.

### 13.4 Audit log

- All admin actions must be written to `audit_log`.
- Sensitive command events must include actor, target, time, and reason.

### 13.5 Command authorization

- Not every admin role should be allowed to close positions or shutdown bots.
- High-impact commands require stricter permissions.

### 13.6 `protocol_version`

- Every request must include `protocol_version`.
- Server must validate supported versions explicitly.
- Version mismatch should be visible in logs and UI.

### 13.7 Request timestamp and replay protection

Minimum practical approach:

- every request carries timestamp plus request ID;
- server rejects requests outside acceptable skew window, for example ±120 seconds;
- server stores recent request IDs for short replay detection.

### 13.8 Optional future hardening

Later, without changing the overall contract, the system may add:

- request signing;
- short-lived per-bot tokens;
- device approval workflow;
- admin MFA and IP restrictions.

---

## 14. Error model and operational conventions

Recommended structured error object:

```json
{
  "code": "license_blocked",
  "message": "license is blocked",
  "retryable": false,
  "details": {}
}
```

Conventions:

- bot should treat unknown nonfatal fields as ignorable;
- server should prefer additive changes to preserve compatibility;
- command handling should be idempotent whenever possible;
- timestamps should use UTC ISO-8601;
- numeric values should be explicit and not overloaded as strings unless required by later language/runtime constraints.

---

## 15. Implementation guidance for future bot integration

This document does **not** require changes right now, but the future client integration should follow these rules:

- keep licensing code isolated from trading logic;
- do not mix server authorization with order placement internals;
- add a separate client module for register / heartbeat / state / commands;
- use explicit mode switches: `off`, `monitor`, `enforce`;
- ensure command execution maps to clearly defined bot actions;
- preserve existing trading safeguards and Bybit correctness checks.

This is important because licensing/admin concerns and trading concerns should remain separated.

---

## 16. Step-by-step rollout plan

### Stage 1 — Contract

Deliverables:

- finalize this specification;
- agree on entities, statuses, identifiers, API shapes, and product dimensions;
- freeze initial `protocol_version = 1.0`.

Outcome:

- server team and bot team can work in parallel against one contract.

### Stage 2 — Server MVP

Deliverables:

- implement basic HTTP API;
- store licenses, bot instances, heartbeats, states, commands, alerts, and audit log;
- support manual block/pause/resume/stop/close-positions command creation;
- basic suspicious detection and admin review.

Outcome:

- operational backend exists, even before hard enforcement.

### Stage 3 — Bot client

Deliverables:

- implement register/check on startup;
- implement heartbeat loop;
- implement periodic state sync;
- implement command polling and result reporting;
- support `off`, `monitor`, `enforce` modes.

Outcome:

- bot can talk to the server without altering core trading logic.

### Stage 4 — Admin UI

Deliverables:

- license list;
- active bots list;
- bot details page;
- filters;
- command buttons;
- suspicious markers;
- alert/event stream.

Outcome:

- owner/operator can monitor and manually manage bot fleet.

### Stage 5 — Anti-copy hardening

Deliverables:

- improved fingerprint policy;
- stricter replay protection and token strategy;
- manual device approval flow if needed;
- more refined risk scoring and alerting.

Outcome:

- stronger practical control without rewriting the contract.

---

## 17. Recommended MVP decisions summary

To keep the first implementation practical, the recommended choices are:

- HTTP + JSON only for MVP;
- polling for commands, not push;
- one explicit `protocol_version` in every request;
- stable `bot_instance_id` plus `machine_fingerprint`;
- explicit `product_code`, `bot_family`, and `strategy_code` dimensions everywhere ambiguity is possible;
- simple server-driven statuses;
- explicit connectivity grace policy for `off / monitor / enforce` modes;
- practical suspicious detection instead of “perfect protection”;
- clear command risk classes and role requirements;
- separate server project and bot project using the same contract.

This is the smallest architecture step that gives licensing visibility, remote control, multi-product routing, and a realistic path toward anti-copy enforcement without touching the current trading runtime yet.
