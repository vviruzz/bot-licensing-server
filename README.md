# Bot Licensing Server

Minimal backend/bootstrap foundation for the licensing/admin MVP.

## Included in this stage

- FastAPI backend bootstrap
- PostgreSQL local development via Docker Compose
- SQLAlchemy 2.x session setup
- Alembic migration infrastructure with an initial empty migration plus auth baseline migration
- Health endpoints for liveness and readiness
- Separate admin JWT auth and bot bearer-token auth for MVP
- Bootstrap admin creation from environment variables after migrations are applied
- Demo seed tooling for a deterministic license, bot instance, and admin alert
- Repeatable smoke-test tooling that exercises the current backend flows end to end
- Admin frontend bootstrap placeholder under `admin/`
- Optional Adminer profile for local database inspection

## Local environment setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Review `.env` and adjust values if needed.

## Auth baseline environment variables

Set these values in `.env` for the auth baseline:

```bash
ADMIN_JWT_SECRET=change-me-admin-jwt-secret
ADMIN_JWT_EXPIRE_MINUTES=60
BOOTSTRAP_ADMIN_EMAIL=owner@example.com
BOOTSTRAP_ADMIN_PASSWORD=change-me-admin-password
BOOTSTRAP_ADMIN_ROLE=owner
BOOTSTRAP_ADMIN_NAME=Bootstrap Admin
BOT_API_TOKEN=change-me-bot-token
```

Notes:

- Admin auth and bot auth are intentionally separate.
- Admin users authenticate with `POST /api/v1/auth/login` and receive a JWT.
- Bot clients authenticate with a static bearer token from `BOT_API_TOKEN`.
- The bootstrap admin is created on backend startup only after the `admin_users` table exists.
- Demo seed data is intentionally MVP/demo oriented and is only created when the seed command is run.

## Run with Docker Compose

Start the main local stack:

```bash
docker compose up --build
```

Start the main stack plus the optional database inspection tool:

```bash
docker compose --profile db-tools up --build
```

The stack includes:

- backend: `http://localhost:8000`
- admin: `http://localhost:3000`
- PostgreSQL: `localhost:${POSTGRES_PORT:-5432}`
- optional Adminer: `http://localhost:8080`

## Run migrations

With the stack running, apply migrations from the backend container:

```bash
docker compose exec backend alembic -c /app/alembic.ini upgrade head
```

To inspect migration state:

```bash
docker compose exec backend alembic -c /app/alembic.ini current
```

## Seed deterministic demo data

After migrations are applied, load or refresh the MVP demo records:

```bash
docker compose exec backend python -m app.demo.seed_data
```

Equivalent shell wrapper:

```bash
docker compose exec backend ./app/scripts/seed_demo_data.sh
```

This seed step is idempotent and maintains deterministic demo values for:

- demo license key: `LIC-DEMO-SEED-001`
- demo bot instance: `bot-demo-seed-001`
- demo session id: `session-demo-seed-001`
- one demo admin alert tied to the seeded bot/license

High-level expected outcome:

- the license is active in `monitor` mode
- the demo bot is bound to that license and marked authorized
- the admin alerts endpoint has at least one deterministic demo alert to display

## Run repeatable smoke tests

Run the end-to-end smoke sequence against the current backend:

```bash
docker compose exec backend python -m app.demo.smoke_tests
```

Equivalent shell wrapper:

```bash
docker compose exec backend ./app/scripts/run_smoke_tests.sh
```

Optional overrides for remote/VDS validation:

```bash
docker compose exec \
  -e SMOKE_BASE_URL=http://localhost:8000 \
  -e BOOTSTRAP_ADMIN_EMAIL=owner@example.com \
  -e BOOTSTRAP_ADMIN_PASSWORD=change-me-admin-password \
  -e BOT_API_TOKEN=change-me-bot-token \
  backend python -m app.demo.smoke_tests
```

The smoke test validates these flows in order:

- health live
- health ready
- admin login
- license check
- bot register
- bot heartbeat
- bot state sync
- admin alerts read
- admin bot pause
- admin bot resume
- admin bot stop
- admin bot close-positions
- bot command poll
- bot command result submission

High-level expected outcome:

- the command exits with status `0`
- JSON output includes `"ok": true`
- all smoke steps are listed with `"status": "ok"`
- command IDs are returned for the four admin-issued bot commands

## Swagger / OpenAPI docs

Open Swagger UI at:

- `http://localhost:8000/docs`

Open ReDoc at:

- `http://localhost:8000/redoc`

## Verify backend health

Liveness check:

```bash
curl http://localhost:8000/health/live
```

Readiness check:

```bash
curl http://localhost:8000/health/ready
```

A healthy response from both endpoints is:

```json
{"status":"ok"}
```

## Admin login example

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "owner@example.com",
    "password": "change-me-admin-password"
  }'
```

Example response shape:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "email": "owner@example.com",
    "full_name": "Bootstrap Admin",
    "role": "owner",
    "is_active": true
  }
}
```

To inspect the current admin user:

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H 'Authorization: Bearer <jwt>'
```

## Bot bearer-token example

Bot-facing routes use a separate bearer token and do not accept the admin JWT.

```bash
curl -X POST http://localhost:8000/api/v1/license/check \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer change-me-bot-token' \
  -d '{
    "license_key": "LIC-XXXXX",
    "bot_instance_id": "botinst_123",
    "product_code": "grid",
    "bot_family": "grid",
    "strategy_code": "grid_v1",
    "protocol_version": "1.0"
  }'
```
