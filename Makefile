.PHONY: lint test fmt up down psql reset-db
lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest -q

fmt:
	uv run ruff check . --fix
	uv run ruff format .

up:
	docker compose up -d --wait

down:
	docker compose down

psql:
	docker compose exec db sh -c 'psql -U "$${POSTGRES_USER}" -d "$${POSTGRES_DB}"'

reset-db:
	@read -p "This deletes ALL local DB data. Type 'yes' to continue: " ans && [ "$$ans" = "yes" ]
	docker compose down -v
	docker compose up -d --wait
