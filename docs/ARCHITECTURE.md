# System Architecture

## Overview

The DZ Customers Clustering system is a production-ready ML service built following MLOps best practices. It provides real-time customer segmentation using K-Prototypes clustering algorithm.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client Layer                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Web App │  │  Mobile  │  │   API    │  │  Backend │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTPS / API Key Auth
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        API Gateway Layer                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Ingress Controller (NGINX) + Rate Limiting + SSL/TLS  │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      Application Layer                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastAPI Application (Multiple Pods)                     │  │
│  │  ┌────────────────┐  ┌──────────────┐  ┌──────────────┐│  │
│  │  │  Middleware    │  │  Routers     │  │  Services    ││  │
│  │  │  - Logging     │  │  - Predict   │  │  - Predictor ││  │
│  │  │  - Metrics     │  │  - Health    │  │  - Cache     ││  │
│  │  │  - RateLimit   │  │  - Reload    │  │  - Drift     ││  │
│  │  │  - Auth        │  └──────────────┘  └──────────────┘│  │
│  │  └────────────────┘                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        Data Layer                                │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Model Store  │  │  Artifact Store│  │  Feature Store   │  │
│  │  (MLflow)     │  │  (S3/PVC)      │  │  (ClickHouse)    │  │
│  └───────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     Monitoring Layer                             │
│  ┌───────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Prometheus   │  │  Grafana       │  │  Alertmanager    │  │
│  │  (Metrics)    │  │  (Dashboard)   │  │  (Alerts)        │  │
│  └───────────────┘  └────────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. FastAPI Application

**Responsibilities:**
- Handle HTTP requests
- Validate input data
- Route requests to appropriate handlers
- Return responses

**Key Features:**
- Async request handling
- Auto-generated API documentation (OpenAPI/Swagger)
- Request/response validation with Pydantic
- Middleware chain for cross-cutting concerns

### 2. Middleware Stack

#### Logging Middleware
- Structured JSON logging
- Request ID tracking
- Performance timing
- Error tracking

#### Metrics Middleware
- Prometheus metrics collection
- Request counts, duration, status codes
- Model prediction metrics
- Data drift metrics

#### Rate Limiting Middleware
- Sliding window rate limiting
- Per-IP tracking
- Configurable limits (per minute, per hour)

#### Authentication Middleware
- API key validation
- Bearer token support
- Public endpoint bypass

### 3. Services Layer

#### Predictor Service
- Single and batch predictions
- Feature preprocessing
- Model inference
- Result caching
- Performance tracking

#### Model Loader
- Singleton pattern
- Async model loading
- Model hot-reloading
- Artifact management

#### Cache Service
- LRU cache with TTL
- Prediction result caching
- Performance optimization
- Memory-efficient

#### Drift Detector
- Statistical drift detection
- Feature distribution monitoring
- Alerts on significant drift
- Rolling window analysis

### 4. ML Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Data      │───▶│ Preprocessing│───▶│  Training   │
│ Extraction │    │              │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                                              ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│  Inference │◀───│  Validation  │◀───│  Artifact   │
│            │    │              │    │   Storage   │
└─────────────┘    └──────────────┘    └─────────────┘
```

## Deployment Architecture

### Kubernetes Deployment

```yaml
Components:
  - Deployment: 3+ replicas with rolling updates
  - Service: ClusterIP for internal communication
  - Ingress: External access with TLS
  - HPA: Auto-scaling based on CPU/memory
  - PVC: Persistent storage for model artifacts
  - ConfigMap: Configuration management
  - Secrets: Sensitive credentials
  - ServiceMonitor: Prometheus integration
```

### Scaling Strategy

**Horizontal Scaling:**
- HPA based on CPU (70%) and memory (80%)
- Min replicas: 3
- Max replicas: 10
- Scale-up: Fast (60s stabilization)
- Scale-down: Slow (300s stabilization)

**Vertical Scaling:**
- Resource requests: 250m CPU, 512Mi memory
- Resource limits: 1000m CPU, 2Gi memory

## Data Flow

### Prediction Request Flow

1. **Client** sends prediction request with customer features
2. **Ingress** terminates TLS and routes to service
3. **Auth Middleware** validates API key
4. **Rate Limit Middleware** checks request limits
5. **Logging Middleware** logs request details
6. **Metrics Middleware** records request metrics
7. **Router** validates request schema
8. **Predictor Service** checks cache
9. If cache miss:
   - Load model artifacts
   - Preprocess features
   - Run inference
   - Cache result
10. **Response** returned to client
11. **Drift Detector** analyzes features (async)

## Monitoring & Observability

### Metrics Collected

**HTTP Metrics:**
- `http_requests_total` - Total requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current in-flight requests

**ML Metrics:**
- `ml_predictions_total` - Predictions by cluster and type
- `ml_prediction_duration_seconds` - Prediction duration
- `ml_model_load_time_seconds` - Model loading time
- `ml_data_drift_score` - Drift score by feature

### Logging

**Structured JSON Format:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "logger": "uvicorn.access",
  "message": "Request completed",
  "request_id": "abc123",
  "method": "POST",
  "path": "/predict",
  "status_code": 200,
  "duration_ms": 45.2
}
```

### Alerting

**Critical Alerts:**
- API down for >5 minutes
- Error rate >5%
- Model load failures

**Warning Alerts:**
- High latency (p95 >1s)
- High memory/CPU usage (>80%)
- Data drift detected

## Security

### Authentication & Authorization
- API key-based authentication
- Bearer token support
- Secret rotation support

### Network Security
- TLS/SSL encryption
- HTTPS only
- Network policies (Kubernetes)

### Rate Limiting
- 60 requests/minute per IP
- 1000 requests/hour per IP
- Configurable limits

### Data Privacy
- No data persistence by default
- Audit logging
- GDPR compliance ready

## Disaster Recovery

### Backup Strategy
- Model artifacts: Versioned in MLflow
- Configuration: Git repository
- Secrets: External secret manager

### Recovery Procedures
1. Rolling back deployments
2. Model rollback via MLflow
3. Configuration rollback via Git
4. Database restoration (if applicable)

## Performance Optimization

### Caching
- In-memory LRU cache
- Configurable TTL
- Cache hit rate monitoring

### Model Optimization
- Model artifacts pre-loaded at startup
- Single model instance per pod
- Efficient numpy operations

### Resource Management
- Connection pooling
- Async I/O
- Garbage collection tuning

