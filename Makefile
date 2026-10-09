.PHONY: lint test fmt
lint:
	uv run ruff check .
	uv run ruff format --check .

test:
	uv run pytest -q

fmt:
	uv run ruff check . --fix
	uv run ruff format .
