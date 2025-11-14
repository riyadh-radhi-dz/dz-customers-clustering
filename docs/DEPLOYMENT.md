# Deployment Guide

## Prerequisites

- Python 3.13+
- Docker 24+
- Kubernetes 1.28+ (for production)
- kubectl configured
- uv package manager

## Environment Setup

### 1. Configuration

Create `.env` file from template:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# API Configuration
DEBUG=false
LOG_LEVEL=INFO
AUTH_ENABLED=true
API_KEYS=["your-generated-api-key"]

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# MLflow
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_EXPERIMENT_NAME=dz-customers-clustering

# ClickHouse (for training)
CLICKHOUSE_HOST=your-host
CLICKHOUSE_PORT=8443
CLICKHOUSE_USERNAME=your-username
CLICKHOUSE_PASSWORD=your-password
CLICKHOUSE_DATABASE=your-database
```

### 2. Generate API Keys

```bash
make generate-api-key
```

## Local Development

### Using UV

```bash
# Install dependencies
uv sync

# Run tests
make test

# Run linting
make lint

# Start development server
make run-dev
```

### Using Docker

```bash
# Build image
make docker-build

# Run container
make docker-run

# Access API
curl http://localhost:8000/health
```

### Using Docker Compose

```bash
# Start all services (API + MLflow + Prometheus + Grafana + Redis)
make docker-compose

# Services available at:
# - API: http://localhost:8000
# - MLflow: http://localhost:5000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000

# Stop services
make docker-compose-down
```

## Production Deployment

### Option 1: Kubernetes

#### Step 1: Prepare Kubernetes Cluster

```bash
# Create namespace
kubectl create namespace dz-clustering

# Verify cluster access
kubectl cluster-info
```

#### Step 2: Create Secrets

```bash
# Generate API keys
API_KEY=$(python -c "from app.middleware.auth import generate_api_key; print(generate_api_key())")

# Create secret
kubectl create secret generic dz-clustering-secrets \
  --from-literal=API_KEYS="[\"$API_KEY\"]" \
  --from-literal=CLICKHOUSE_HOST="your-host" \
  --from-literal=CLICKHOUSE_PORT="8443" \
  --from-literal=CLICKHOUSE_USERNAME="your-username" \
  --from-literal=CLICKHOUSE_PASSWORD="your-password" \
  --from-literal=CLICKHOUSE_DATABASE="your-database" \
  --from-literal=MLFLOW_TRACKING_URI="http://mlflow:5000" \
  --namespace dz-clustering
```

#### Step 3: Update ConfigMap

Edit `k8s/configmap.yaml` with your configuration.

#### Step 4: Prepare Model Artifacts

```bash
# Option A: Train new model
make train-model

# Option B: Copy existing artifacts
# Ensure artifacts/ directory contains:
# - kmeans_cta_model.pkl
# - scaler.pkl
# - preprocess_config.json
```

#### Step 5: Create PVC and Upload Artifacts

```bash
# Create PVC
kubectl apply -f k8s/pvc.yaml -n dz-clustering

# Create a temporary pod to upload artifacts
kubectl run tmp-uploader --image=busybox --restart=Never \
  --overrides='
{
  "spec": {
    "volumes": [{
      "name": "model-storage",
      "persistentVolumeClaim": {"claimName": "dz-clustering-models"}
    }],
    "containers": [{
      "name": "uploader",
      "image": "busybox",
      "command": ["sleep", "3600"],
      "volumeMounts": [{
        "name": "model-storage",
        "mountPath": "/artifacts"
      }]
    }]
  }
}' -n dz-clustering

# Copy artifacts
kubectl cp artifacts/ tmp-uploader:/artifacts/ -n dz-clustering

# Clean up
kubectl delete pod tmp-uploader -n dz-clustering
```

#### Step 6: Deploy Application

```bash
# Deploy all resources
make k8s-deploy

# Or deploy manually
kubectl apply -f k8s/configmap.yaml -n dz-clustering
kubectl apply -f k8s/deployment.yaml -n dz-clustering
kubectl apply -f k8s/service.yaml -n dz-clustering
kubectl apply -f k8s/ingress.yaml -n dz-clustering
kubectl apply -f k8s/hpa.yaml -n dz-clustering
kubectl apply -f k8s/servicemonitor.yaml -n dz-clustering
```

#### Step 7: Verify Deployment

```bash
# Check pod status
kubectl get pods -n dz-clustering

# Check logs
kubectl logs -f deployment/dz-clustering-api -n dz-clustering

# Check service
kubectl get svc -n dz-clustering

# Test API
kubectl port-forward svc/dz-clustering-api 8000:80 -n dz-clustering
curl http://localhost:8000/health
```

#### Step 8: Configure Ingress (Optional)

Update `k8s/ingress.yaml` with your domain:

```yaml
spec:
  tls:
  - hosts:
    - api.yourdomain.com
    secretName: dz-clustering-tls
  rules:
  - host: api.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dz-clustering-api
            port:
              number: 80
```

Apply:
```bash
kubectl apply -f k8s/ingress.yaml -n dz-clustering
```

### Option 2: Docker Swarm

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: dz-customers-clustering:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
    secrets:
      - api_keys
      - clickhouse_password
    networks:
      - dz-network

secrets:
  api_keys:
    external: true
  clickhouse_password:
    external: true

networks:
  dz-network:
    driver: overlay
```

Deploy:
```bash
docker stack deploy -c docker-compose.prod.yml dz-clustering
```

### Option 3: VM/Bare Metal

```bash
# 1. Install system dependencies
sudo apt-get update
sudo apt-get install -y python3.13 python3-pip

# 2. Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Clone repository
git clone <repo-url>
cd dz-customers-clustering

# 4. Install dependencies
uv sync

# 5. Set up systemd service
sudo nano /etc/systemd/system/dz-clustering.service

[Unit]
Description=DZ Customers Clustering API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/dz-customers-clustering
Environment="PATH=/opt/dz-customers-clustering/.venv/bin"
ExecStart=/opt/dz-customers-clustering/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=on-failure

[Install]
WantedBy=multi-user.target

# 6. Enable and start service
sudo systemctl enable dz-clustering
sudo systemctl start dz-clustering
sudo systemctl status dz-clustering
```

## CI/CD Setup

### GitHub Actions

The repository includes CI/CD workflows:

- `.github/workflows/ci.yml` - Continuous Integration
- `.github/workflows/cd.yml` - Continuous Deployment
- `.github/workflows/model-training.yml` - Model Training Pipeline

#### Required Secrets

Add these to GitHub repository secrets:

```
CLICKHOUSE_HOST
CLICKHOUSE_PORT
CLICKHOUSE_USERNAME
CLICKHOUSE_PASSWORD
CLICKHOUSE_DATABASE
KUBE_CONFIG (base64 encoded kubeconfig)
```

#### Trigger Deployment

```bash
# Push to main branch triggers deployment to staging
git push origin main

# Create tag for production deployment
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Monitoring Setup

### Prometheus

```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack -n monitoring

# Apply ServiceMonitor
kubectl apply -f k8s/servicemonitor.yaml -n dz-clustering
```

### Grafana

```bash
# Access Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Import dashboard
# Use dashboards from monitoring/grafana/dashboards/
```

## Troubleshooting

### Pods Not Starting

```bash
# Check events
kubectl describe pod <pod-name> -n dz-clustering

# Common issues:
# 1. Image pull errors - verify image exists
# 2. Resource limits - check available resources
# 3. PVC mount errors - verify PVC exists and has artifacts
```

### Model Not Loading

```bash
# Check artifacts in PVC
kubectl exec -it <pod-name> -n dz-clustering -- ls -la /app/artifacts

# Should see:
# - kmeans_cta_model.pkl
# - scaler.pkl
# - preprocess_config.json

# If missing, re-upload artifacts
```

### High Memory Usage

```bash
# Check resource usage
kubectl top pods -n dz-clustering

# Increase limits in deployment.yaml:
resources:
  limits:
    memory: "4Gi"  # Increase from 2Gi
```

## Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/dz-clustering-api -n dz-clustering

# Rollback to specific revision
kubectl rollout history deployment/dz-clustering-api -n dz-clustering
kubectl rollout undo deployment/dz-clustering-api --to-revision=2 -n dz-clustering
```

## Health Checks

```bash
# API health
curl https://api.yourdomain.com/health

# Metrics
curl https://api.yourdomain.com/metrics

# Test prediction
curl -X POST https://api.yourdomain.com/predict \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_KEY" \
  -d '{...}'
```

## Performance Tuning

### Application Level

```env
# .env
MAX_WORKERS=8  # Increase for more concurrent requests
RATE_LIMIT_PER_MINUTE=120  # Adjust based on load
```

### Kubernetes Level

```yaml
# deployment.yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Caching

```python
# Adjust cache settings in app/services/cache.py
PredictionCache(max_size=20000, ttl_seconds=7200)
```

