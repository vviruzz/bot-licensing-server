# Bot Licensing Server

Minimal backend/bootstrap foundation for the licensing/admin MVP.

## Included in this stage

- FastAPI backend bootstrap
- PostgreSQL local development via Docker Compose
- SQLAlchemy 2.x session setup
- Alembic migration infrastructure with an initial empty migration
- Health endpoints for liveness and readiness
- Admin frontend bootstrap placeholder under `admin/`
- Optional Adminer profile for local database inspection

## Local environment setup

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Review `.env` and adjust values if needed.

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
