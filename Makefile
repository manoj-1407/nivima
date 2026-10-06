.PHONY: install dev-install download-models setup-mfa migrate \
        run-api run-worker run-flower docker-up docker-down \
        test test-unit test-integration lint format smoke-test

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt
	pre-commit install

download-models:
	bash scripts/download_models.sh

setup-mfa:
	bash scripts/setup_mfa.sh

migrate:
	alembic upgrade head

run-api:
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	celery -A src.worker.celery_app worker --loglevel=info --concurrency=2 -Q default

run-flower:
	celery -A src.worker.celery_app flower --port=5555

docker-up:
	docker-compose -f infra/docker/docker-compose.yml up -d

docker-down:
	docker-compose -f infra/docker/docker-compose.yml down -v

test:
	pytest tests/ -v --cov=src --cov-report=term-missing -x

test-unit:
	pytest tests/unit/ -v -x

test-integration:
	pytest tests/integration/ -v -x

lint:
	ruff check src/ tests/
	mypy src/

format:
	ruff format src/ tests/
	ruff check --fix src/ tests/

smoke-test:
	bash scripts/smoke_test.sh

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	find . -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
