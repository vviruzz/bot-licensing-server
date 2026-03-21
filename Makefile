.PHONY: backend-install admin-install backend-dev admin-dev up

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

admin-install:
	cd admin && npm install

backend-dev:
	cd backend && uvicorn app.main:app --reload

admin-dev:
	cd admin && npm run dev

up:
	docker compose up --build
