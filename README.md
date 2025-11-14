# DZ Customers Clustering - Production ML API

<div align="center">

![Python Version](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)
![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen.svg)

Production-ready ML API for real-time customer clustering using K-Prototypes algorithm with full MLOps capabilities.

[Features](#-features) •
[Quick Start](#-quick-start) •
[Documentation](#-documentation) •
[Architecture](#-architecture) •
[Deployment](#-deployment)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Documentation](#-documentation)
- [Architecture](#-architecture)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Monitoring](#-monitoring)
- [Contributing](#-contributing)

## 🎯 Overview

This is a **production-ready ML service** that provides real-time customer segmentation using the K-Prototypes clustering algorithm. Built with FastAPI and following MLOps best practices used by big tech companies.

### What Makes This Production-Ready?

✅ **Comprehensive Testing** - Unit, integration, and E2E tests with 90%+ coverage  
✅ **CI/CD Pipelines** - Automated testing, building, and deployment via GitHub Actions  
✅ **Monitoring & Observability** - Prometheus metrics, structured logging, Grafana dashboards  
✅ **Security** - API key authentication, rate limiting, CORS, secret management  
✅ **Scalability** - Kubernetes-ready with HPA, load balancing, and caching  
✅ **Model Versioning** - MLflow integration for experiment tracking and model registry  
✅ **Data Quality** - Input validation, drift detection, and quality checks  
✅ **Performance** - Caching, async operations, optimized model inference  
✅ **Documentation** - Comprehensive API docs, runbooks, and architecture diagrams  

## ✨ Features

### Core ML Features
- **Real-time Predictions** - Sub-100ms p95 latency
- **Batch Processing** - Efficient batch inference for multiple customers
- **Hot Model Reloading** - Update models without downtime
- **Data Drift Detection** - Statistical monitoring of feature distributions

### MLOps Features
- **Experiment Tracking** - MLflow integration
- **Model Registry** - Versioned model artifacts
- **Automated Training** - Daily scheduled model retraining
- **Champion/Challenger** - Automatic model validation and promotion
- **Smart Updates** - Only promotes models with >2% improvement
- **A/B Testing Ready** - Infrastructure for model comparison

### Production Features
- **API Authentication** - Secure API key-based auth
- **Rate Limiting** - Protect against abuse (60 req/min, 1000 req/hour)
- **Caching** - LRU cache with TTL for improved performance
- **Structured Logging** - JSON logs for easy parsing
- **Prometheus Metrics** - 20+ metrics tracked
- **Health Checks** - Liveness and readiness probes
- **Auto-scaling** - HPA based on CPU/memory

### Developer Experience
- **Interactive API Docs** - Swagger UI and ReDoc
- **Pre-commit Hooks** - Automated code quality checks
- **Type Safety** - Full type hints and validation
- **Docker Support** - Multi-stage builds and docker-compose
- **Makefile Commands** - Simple command interface

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- Docker & Docker Compose
- `uv` package manager (recommended) or `pip`

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/digitalzone/dz-customers-clustering.git
cd dz-customers-clustering

# 2. Install dependencies
uv sync
# or: pip install -r requirements.txt

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Run the application
make run-dev
# or: uvicorn app.main:app --reload

# 5. Access the API
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# Health: http://localhost:8000/health
```

### Using Docker

```bash
# Build and run
make docker-build
make docker-run

# Or using docker-compose (includes MLflow, Prometheus, Grafana)
make docker-compose

# Services will be available at:
# - API: http://localhost:8000
# - MLflow: http://localhost:5000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
```

### Making Your First Prediction

```bash
# Generate API key
make generate-api-key

# Make a prediction
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "gender": "M",
    "age": 35.0,
    "bnpl_eligible": 1,
    "number_of_sessions": 10.0,
    "days_since_first_joined": 365.0,
    "number_of_failed_orders": 1.0,
    "number_of_successful_orders": 9.0
  }'

# Response:
# {
#   "cluster": 2,
#   "meta": {"source": "predict_single"}
# }
```

## 📚 Documentation

### Core Documentation
- **[API Documentation](docs/API.md)** - Complete API reference with examples
- **[Architecture](docs/ARCHITECTURE.md)** - System design and components
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment instructions
- **[Operations Runbook](docs/RUNBOOK.md)** - Troubleshooting and maintenance

### MLOps Documentation
- **[Automated Training Guide](AUTOMATED_TRAINING_GUIDE.md)** - 🎯 **START HERE** - Complete guide for training with new users
- **[Model Validation Guide](MODEL_VALIDATION_GUIDE.md)** - Champion/Challenger pattern details
- **[Auto Update Summary](AUTO_MODEL_UPDATE_SUMMARY.md)** - Quick reference for model updates
- **[MLflow Training Guide](MLFLOW_TRAINING_GUIDE.md)** - MLflow integration and tracking
- **[Quick Start MLflow](QUICK_START_MLFLOW.md)** - Get started with MLflow quickly
- **[ML Handover](HANDOVER.md)** - Model training and artifacts overview

### Interactive Documentation

Once the API is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🏗 Architecture

### MLOps Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│                   🚀 DZ CUSTOMER CLUSTERING - MLOps ARCHITECTURE                   │
└────────────────────────────────────────────────────────────────────────────────────┘


    ┌─────────────────────┐         ┌─────────────────────┐         ┌─────────────────────┐
    │                     │         │                     │         │                     │
    │    📊 TRAINING      │────────▶│   📈 MONITORING     │────────▶│   🚀 DEPLOYMENT     │
    │                     │         │                     │         │                     │
    └─────────────────────┘         └─────────────────────┘         └─────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                    TRAINING                                          │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│    🗄️                  📊                  🐍                  📦                   │
│  ClickHouse  ───────▶  CSV Data  ───────▶  Python  ───────▶  MLflow                │
│  Database           Training Data      K-Prototypes      Experiment                │
│                                           Model            Tracking                 │
│                                             │                                        │
│                                             ▼                                        │
│                    ┌────────────────────────────────────────┐                       │
│                    │  🏆 Champion/Challenger Pattern        │                       │
│                    │                                        │                       │
│                    │  Challenger ──▶ Validate ──▶ Promote? │                       │
│                    │                    │                   │                       │
│                    │                    ├─ Yes ──▶ Champion │                       │
│                    │                    └─ No  ──▶ Reject   │                       │
│                    └────────────────────────────────────────┘                       │
│                                             │                                        │
│                                             ▼                                        │
│                                      💾 Artifact Storage                            │
│                                    (Model Files + Metadata)                         │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                   MONITORING                                         │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│    📊 Production Data       🔍 Model Monitoring       📈 Metrics & Dashboards       │
│         │                           │                          │                    │
│         ▼                           ▼                          ▼                    │
│    ┌─────────┐              ┌─────────────┐           ┌──────────────┐            │
│    │ FastAPI │─────────────▶│   MLflow    │◀──────────│  Prometheus  │            │
│    │   API   │              │  Tracking   │           │  + Grafana   │            │
│    └─────────┘              └─────────────┘           └──────────────┘            │
│                                                                                      │
│    • Data Drift Detection    • Performance Metrics    • Real-time Alerts           │
│    • Feature Quality         • Prediction Logs        • Custom Dashboards          │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                   DEPLOYMENT                                         │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                            🐳 Docker Container                                       │
│                     ┌──────────────────────────────────┐                            │
│                     │    ⚡ FastAPI Service            │                            │
│                     │   (Model API Endpoint)           │                            │
│                     │                                  │                            │
│                     │  • Authentication                │                            │
│                     │  • Rate Limiting                 │                            │
│                     │  • Caching                       │                            │
│                     │  • Load Champion Model           │                            │
│                     └──────────────────────────────────┘                            │
│                                   │                                                  │
│          ┌────────────────────────┼────────────────────────┐                        │
│          │                        │                        │                        │
│          ▼                        ▼                        ▼                        │
│                                                                                      │
│  🐳 Docker Compose      ☸️  Kubernetes        🔄 GitHub Actions                     │
│  (Development)          (Production)          (CI/CD Pipeline)                      │
│                                                                                      │
│  • Local testing        • Auto-scaling        • Automated training                  │
│  • All services         • High availability   • Validation & promotion              │
│  • Quick iteration      • Load balancing      • Automated deployment                │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────────────────────────────────────────────────────────────────┐
│                              🔄 AUTOMATED WORKFLOW                                   │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│   ⏰ Daily (2 AM UTC)                                                                │
│        │                                                                             │
│        ▼                                                                             │
│   Extract Data ──▶ Train Model ──▶ Validate ──▶ Promote? ──▶ Deploy               │
│   (ClickHouse)   (K-Prototypes)  (Compare)    (If Better)   (Reload API)           │
│                                                                                      │
│        │              │              │            │            │                     │
│        └──────────────┴──────────────┴────────────┴────────────┘                    │
│                                   │                                                  │
│                                   ▼                                                  │
│                         📊 MLflow Logging                                            │
│                  (All metrics, params, artifacts)                                   │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘


                        ┌────────────────────────────────┐
                        │     🔧 TECH STACK              │
                        ├────────────────────────────────┤
                        │  Data: ClickHouse              │
                        │  ML: K-Prototypes, scikit-learn│
                        │  API: FastAPI                  │
                        │  Tracking: MLflow              │
                        │  Metrics: Prometheus + Grafana │
                        │  Deploy: Docker + Kubernetes   │
                        │  CI/CD: GitHub Actions         │
                        └────────────────────────────────┘
```

### Detailed System Architecture

```
┌──────────────────────────────────────────────────────┐
│                    Client Layer                       │
│         (Web/Mobile/Backend Applications)            │
└────────────────────┬─────────────────────────────────┘
                     │
                     │ HTTPS + API Key
                     ▼
┌──────────────────────────────────────────────────────┐
│              API Gateway (Ingress/NGINX)             │
│         Rate Limiting + SSL/TLS + Load Balancing     │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│         FastAPI Application (Multiple Pods)          │
│  ┌────────────────┬─────────────┬──────────────────┐│
│  │  Middleware    │   Routers   │    Services      ││
│  │  - Logging     │   - Predict │    - Predictor   ││
│  │  - Metrics     │   - Health  │    - Cache       ││
│  │  - Auth        │   - Reload  │    - Drift       ││
│  │  - RateLimit   │             │    - MLflow      ││
│  └────────────────┴─────────────┴──────────────────┘│
└────────────────────┬─────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    ┌────────┐  ┌─────────┐  ┌──────────┐
    │ Models │  │ MLflow  │  │ ClickHouse│
    │  (PVC) │  │Registry │  │   (DB)   │
    └────────┘  └─────────┘  └──────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│              Monitoring & Alerting                   │
│  Prometheus → Grafana → Alertmanager → PagerDuty   │
└──────────────────────────────────────────────────────┘
```

### Key Components

- **FastAPI Application** - Async web framework with automatic validation
- **Model Loader** - Singleton pattern for efficient model management
- **Predictor Service** - Optimized inference with caching
- **Drift Detector** - Statistical monitoring of data drift
- **MLflow Tracker** - Experiment and model versioning
- **Middleware Stack** - Logging, metrics, auth, rate limiting
- **Kubernetes** - Container orchestration with auto-scaling

## 💻 Development

### Project Structure

```
dz-customers-clustering/
├── app/                      # FastAPI application
│   ├── main.py              # Application entry point
│   ├── config.py            # Configuration management
│   ├── schemas.py           # Pydantic models
│   ├── middleware/          # Custom middleware
│   │   ├── auth.py         # Authentication
│   │   ├── logging.py      # Structured logging
│   │   ├── metrics.py      # Prometheus metrics
│   │   └── rate_limit.py   # Rate limiting
│   ├── routers/            # API endpoints
│   │   └── utils_router.py
│   ├── services/           # Business logic
│   │   ├── predictor.py   # Prediction service
│   │   ├── model_loader.py # Model management
│   │   ├── cache.py       # Caching layer
│   │   ├── drift_detector.py
│   │   └── mlflow_tracker.py
│   └── validators/         # Data validation
│       └── data_quality.py
├── src/                    # ML pipeline code
│   └── dz_customers_clustering/
│       ├── pipeline.py    # Training pipeline
│       ├── inference.py   # Inference logic
│       ├── artifacts.py   # Artifact management
│       └── settings.py    # Configuration
├── scripts/               # Training & testing scripts
│   ├── train_with_mlflow.py         # MLflow training
│   ├── validate_and_promote_model.py # Champion/Challenger
│   └── test_*.py/sh       # Testing utilities
├── tests/                  # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
├── k8s/                    # Kubernetes manifests
├── .github/workflows/     # CI/CD pipelines
├── docs/                   # Documentation
├── monitoring/            # Monitoring configs
├── artifacts/             # Model artifacts
│   ├── champion/          # Production model (Champion)
│   ├── challenger/        # Latest trained (Challenger)
│   └── backup/           # Historical backups
└── outputs/               # Training outputs
```

### Development Workflow

```bash
# Install pre-commit hooks
make pre-commit

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Run all checks
make pre-commit

# Start development server
make run-dev
```

## 🧪 Testing

### Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# Integration tests only
make test-integration

# Generate coverage report
pytest --cov=app --cov=src --cov-report=html
```

### Test Coverage

- **Unit Tests**: 90%+ coverage
- **Integration Tests**: All API endpoints
- **Mocking**: External dependencies mocked
- **Fixtures**: Reusable test data and mocks

### CI/CD Testing

Tests run automatically on:
- Every push to `main`, `develop`, `mlops` branches
- Every pull request
- Before deployment

## 🚢 Deployment

### Kubernetes (Production)

```bash
# 1. Create namespace and secrets
kubectl create namespace dz-clustering
kubectl create secret generic dz-clustering-secrets \
  --from-literal=API_KEYS='["key1"]' \
  -n dz-clustering

# 2. Deploy application
make k8s-deploy

# 3. Verify deployment
kubectl get pods -n dz-clustering
kubectl logs -f deployment/dz-clustering-api -n dz-clustering
```

### Docker Swarm

```bash
docker stack deploy -c docker-compose.prod.yml dz-clustering
```

### VM / Bare Metal

```bash
# Install as systemd service
sudo systemctl enable dz-clustering
sudo systemctl start dz-clustering
```

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed instructions.

## 📊 Monitoring

### Metrics

Access Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8000/metrics
```

**Key Metrics:**
- `http_requests_total` - Request count by endpoint and status
- `http_request_duration_seconds` - Request latency histogram
- `ml_predictions_total` - Predictions by cluster
- `ml_prediction_duration_seconds` - Inference latency
- `ml_data_drift_score` - Data drift detection
- `ml_model_load_time_seconds` - Model loading time

### Dashboards

**Grafana** (http://localhost:3000):
- API Performance Dashboard
- ML Model Monitoring
- System Resources
- Custom Alerts

**Prometheus** (http://localhost:9090):
- Query metrics
- View alerts
- Service discovery

### Alerts

Configured in `monitoring/alerts.yml`:
- API down (P0)
- High error rate (P0)
- High latency (P1)
- Data drift detected (P1)
- Resource usage (P2)

## 🛠 Available Commands

```bash
# Development
make install          # Install dependencies
make run-dev          # Run development server
make run-prod         # Run production server

# Testing
make test            # Run all tests
make test-unit       # Run unit tests
make test-integration # Run integration tests
make lint            # Run linters
make format          # Format code

# Docker
make docker-build    # Build Docker image
make docker-run      # Run Docker container
make docker-compose  # Start all services

# Kubernetes
make k8s-deploy      # Deploy to Kubernetes
make k8s-delete      # Delete from Kubernetes

# ML
make train-model     # Train new model
make generate-api-key # Generate API key

# Quality
make pre-commit      # Run pre-commit hooks
make clean           # Clean temporary files
```

## 📝 Environment Variables

Key environment variables (see `.env.example`):

```env
# API Configuration
DEBUG=false
LOG_LEVEL=INFO
AUTH_ENABLED=true
API_KEYS=["your-api-key"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_EXPERIMENT_NAME=dz-customers-clustering

# ClickHouse (for training)
CLICKHOUSE_HOST=your-host
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
```

## 🔧 Troubleshooting

### Common Issues

**API not responding:**
```bash
# Check logs
kubectl logs deployment/dz-clustering-api -n dz-clustering

# Check health
curl http://localhost:8000/health
```

**Model not loading:**
```bash
# Verify artifacts exist
kubectl exec -it <pod> -n dz-clustering -- ls -la /app/artifacts

# Reload model
curl -X POST http://localhost:8000/reload_model -H "X-API-Key: YOUR_KEY"
```

**High latency:**
```bash
# Check cache stats
curl http://localhost:8000/cache/stats

# Scale up
kubectl scale deployment dz-clustering-api --replicas=5 -n dz-clustering
```

See [Operations Runbook](docs/RUNBOOK.md) for detailed troubleshooting.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add tests for new features
- Update documentation
- Run pre-commit hooks
- Keep coverage above 80%

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Scikit-learn for ML algorithms
- Prometheus for monitoring
- MLflow for experiment tracking
- The open-source community

---

<div align="center">
Made with ❤️ by the DigitalZone Team
</div>
