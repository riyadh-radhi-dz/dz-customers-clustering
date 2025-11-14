.PHONY: help install test lint format clean docker-build docker-run k8s-deploy

help:
	@echo "Available commands:"
	@echo "  make install        - Install dependencies"
	@echo "  make test           - Run tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make clean          - Clean temporary files"
	@echo "  make docker-build   - Build Docker image"
	@echo "  make docker-run     - Run Docker container"
	@echo "  make docker-compose - Start services with docker-compose"
	@echo "  make k8s-deploy     - Deploy to Kubernetes"
	@echo "  make pre-commit     - Install pre-commit hooks"

install:
	uv sync
	uv pip install pytest pytest-cov pytest-asyncio httpx
	uv pip install ruff black isort mypy pylint bandit safety

test:
	uv run pytest tests/ -v --cov=app --cov=src --cov-report=html --cov-report=term

test-unit:
	uv run pytest tests/unit/ -v

test-integration:
	uv run pytest tests/integration/ -v

lint:
	uv run ruff check .
	uv run mypy app/ src/ --ignore-missing-imports
	uv run bandit -r app/ src/

format:
	uv run black .
	uv run isort .
	uv run ruff check . --fix

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf htmlcov/ .coverage coverage.xml

docker-build:
	docker build -t dz-customers-clustering:latest .

docker-run:
	docker run --rm -p 8000:8000 --env-file .env dz-customers-clustering:latest

docker-compose:
	docker-compose up -d

docker-compose-down:
	docker-compose down -v

k8s-deploy:
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secret.yaml
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/service.yaml
	kubectl apply -f k8s/ingress.yaml
	kubectl apply -f k8s/hpa.yaml
	kubectl apply -f k8s/servicemonitor.yaml

k8s-delete:
	kubectl delete -f k8s/

pre-commit:
	uv pip install pre-commit
	pre-commit install
	pre-commit run --all-files

run-dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

train-model:
	uv run python main.py

train-with-mlflow:
	python3 scripts/train_with_mlflow.py

validate-and-promote:
	python3 scripts/validate_and_promote_model.py

generate-api-key:
	uv run python -c "from app.middleware.auth import generate_api_key; print(generate_api_key())"

