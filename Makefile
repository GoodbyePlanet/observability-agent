.PHONY: up down restart status logs

# ── Start all containers in detached mode, building images as needed ──
up:
	docker compose up -d --build

# ── Stop all containers ──
down:
	docker compose down

# ── Restart all containers ──
restart: down up

# ── Tail logs from all containers ──
logs:
	docker compose logs -f --tail=50
