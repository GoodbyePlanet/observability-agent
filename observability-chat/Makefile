.PHONY: run install

install:
	uv sync

run:
	uv run uvicorn backend.main:app --host 0.0.0.0 --port 8084 --reload
