.PHONY: up down logs build migrate

up:
	docker compose up -d --build
	docker compose logs -f --tail=200

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

build:
	docker compose build

migrate:
	docker compose exec backend alembic upgrade head
