# bot-licensing-server

## Purpose

`bot-licensing-server` is the initial server-side MVP skeleton for a future licensing and admin service for trading bots. The repository is intentionally contract-first and derived from the documents in `contracts/`, which remain the source of truth for the MVP API and data model.

## Boundaries

- This repository is fully separate from any trading bot repository.
- No existing trading bot is integrated here yet.
- No Bybit logic or trading runtime logic is included.
- This MVP skeleton focuses on explicit product dimensions: `product_code`, `bot_family`, and `strategy_code`.
- Business logic is intentionally left minimal so the codebase stays runnable and easy to evolve.

## Planned modules

- `contracts/`: source-of-truth contract documents plus the initial OpenAPI skeleton.
- `backend/`: FastAPI-style server skeleton for bot-facing and admin-facing APIs.
- `admin/`: minimal React + TypeScript + Vite admin shell.
- Future work: persistence models, auth, audit history, command delivery, policy enforcement, and UI workflows.

## Local startup overview

### Backend

1. Create a virtual environment.
2. Install `backend/requirements.txt`.
3. Run the FastAPI app with Uvicorn.

### Admin

1. Install `admin/package.json` dependencies.
2. Start the Vite development server.

### Docker Compose

Use `docker compose up --build` to run the backend and admin skeleton together for local development.

## Contract-first note

The files under `contracts/` are the source of truth for this repository. The added OpenAPI file is only an initial machine-readable skeleton derived from those contracts and should evolve with the contract documents rather than replace them.

## Exact local commands

```bash
cp .env.example .env
cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload
cd admin && npm install && npm run dev
# or from the repository root
make up
```
