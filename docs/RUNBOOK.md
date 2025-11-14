# Operations Runbook

## Table of Contents
1. [Deployment](#deployment)
2. [Monitoring](#monitoring)
3. [Troubleshooting](#troubleshooting)
4. [Incident Response](#incident-response)
5. [Maintenance](#maintenance)

---

## Deployment

### Local Development

```bash
# 1. Clone repository
git clone <repository-url>
cd dz-customers-clustering

# 2. Create virtual environment
uv venv
source .venv/bin/activate

# 3. Install dependencies
uv sync

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Run the application
make run-dev
```

### Docker Deployment

```bash
# Build image
make docker-build

# Run container
make docker-run

# Or use docker-compose for full stack
make docker-compose
```

### Kubernetes Deployment

```bash
# 1. Create namespace
kubectl create namespace dz-clustering

# 2. Create secrets
kubectl create secret generic dz-clustering-secrets \
  --from-literal=API_KEYS='["key1","key2"]' \
  --from-literal=CLICKHOUSE_PASSWORD='password' \
  -n dz-clustering

# 3. Deploy all resources
make k8s-deploy

# 4. Verify deployment
kubectl get pods -n dz-clustering
kubectl get svc -n dz-clustering
kubectl logs -f deployment/dz-clustering-api -n dz-clustering
```

---

## Monitoring

### Health Checks

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {"status":"ok","model_loaded":true}
```

### Metrics

```bash
# View Prometheus metrics
curl http://localhost:8000/metrics

# Key metrics to monitor:
# - http_requests_total
# - http_request_duration_seconds
# - ml_predictions_total
# - ml_model_load_time_seconds
# - ml_data_drift_score
```

### Dashboards

**Grafana Dashboard:**
- URL: http://localhost:3000 (docker-compose)
- Default credentials: admin/admin
- Import dashboard from `monitoring/grafana/dashboards/`

**Prometheus:**
- URL: http://localhost:9090 (docker-compose)
- Query examples:
  ```promql
  # Request rate
  rate(http_requests_total[5m])
  
  # Error rate
  rate(http_requests_total{status_code=~"5.."}[5m])
  
  # P95 latency
  histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
  ```

---

## Troubleshooting

### API Not Responding

**Symptoms:**
- API returns 503 errors
- No response from endpoints

**Investigation:**
```bash
# Check pod status
kubectl get pods -n dz-clustering

# Check pod logs
kubectl logs deployment/dz-clustering-api -n dz-clustering

# Check events
kubectl get events -n dz-clustering
```

**Common Causes:**
1. Model artifacts not loaded
   - Solution: Check PVC mount, verify artifacts exist
2. Out of memory
   - Solution: Increase memory limits in deployment
3. Database connection failure
   - Solution: Verify ClickHouse credentials

---

### High Latency

**Symptoms:**
- Slow response times (>1s)
- Increased P95 latency

**Investigation:**
```bash
# Check resource usage
kubectl top pods -n dz-clustering

# View metrics
curl http://localhost:8000/metrics | grep duration
```

**Solutions:**
1. Scale up replicas:
   ```bash
   kubectl scale deployment dz-clustering-api --replicas=5 -n dz-clustering
   ```

2. Check cache hit rate:
   - Low cache hits indicate need for larger cache or longer TTL

3. Profile predictions:
   - Review model complexity
   - Consider model optimization

---

### High Error Rate

**Symptoms:**
- Many 500 errors
- Increased error metrics

**Investigation:**
```bash
# Check logs for errors
kubectl logs deployment/dz-clustering-api -n dz-clustering | grep ERROR

# Check error metrics
curl http://localhost:8000/metrics | grep 'status_code="5'
```

**Solutions:**
1. Model loading issues:
   ```bash
   # Reload model
   curl -X POST http://localhost:8000/reload_model \
     -H "X-API-Key: YOUR_KEY"
   ```

2. Input validation errors:
   - Review recent requests
   - Update validation rules if needed

3. Dependency failures:
   - Check ClickHouse connectivity
   - Verify external service health

---

### Rate Limiting Issues

**Symptoms:**
- Many 429 errors
- Clients reporting rate limit errors

**Investigation:**
```bash
# Check rate limit metrics
curl http://localhost:8000/metrics | grep rate_limit
```

**Solutions:**
1. Increase limits (temporary):
   ```bash
   # Update ConfigMap
   kubectl edit configmap dz-clustering-config -n dz-clustering
   # Set RATE_LIMIT_PER_MINUTE=100
   # Set RATE_LIMIT_PER_HOUR=5000
   
   # Restart pods
   kubectl rollout restart deployment/dz-clustering-api -n dz-clustering
   ```

2. Implement client-side throttling
3. Use batch predictions to reduce requests

---

### Data Drift Detected

**Symptoms:**
- Alert: "Data drift detected"
- High drift scores in metrics

**Investigation:**
```bash
# Check drift metrics
curl http://localhost:8000/metrics | grep drift

# Review recent predictions
kubectl logs deployment/dz-clustering-api -n dz-clustering | grep drift
```

**Actions:**
1. Review feature distributions
2. Analyze incoming data patterns
3. Consider model retraining:
   ```bash
   # Trigger model training workflow
   gh workflow run model-training.yml
   ```

---

## Incident Response

### Severity Levels

| Level | Description | Response Time |
|-------|-------------|---------------|
| P0 | Complete outage | Immediate |
| P1 | Degraded service | 15 minutes |
| P2 | Minor issues | 1 hour |
| P3 | Cosmetic issues | Next business day |

### P0: Complete Outage

**Response Steps:**
1. Acknowledge incident
2. Check status:
   ```bash
   kubectl get pods -n dz-clustering
   kubectl get svc -n dz-clustering
   ```
3. Review logs:
   ```bash
   kubectl logs -f deployment/dz-clustering-api -n dz-clustering --tail=100
   ```
4. If pods are down, check events:
   ```bash
   kubectl describe pod <pod-name> -n dz-clustering
   ```
5. Quick fixes:
   - Restart pods: `kubectl rollout restart deployment/dz-clustering-api -n dz-clustering`
   - Scale up: `kubectl scale deployment dz-clustering-api --replicas=5 -n dz-clustering`
6. If unresolved, rollback:
   ```bash
   kubectl rollout undo deployment/dz-clustering-api -n dz-clustering
   ```
7. Communicate status to stakeholders
8. Post-incident review after resolution

---

## Maintenance

### Model Updates

#### Training New Model

```bash
# 1. Run training pipeline
make train-model

# 2. Validate artifacts
ls -lh artifacts/
# Should see: kmeans_cta_model.pkl, scaler.pkl, preprocess_config.json

# 3. Test locally
make run-dev
curl -X POST http://localhost:8000/predict ...
```

#### Deploying New Model

**Option 1: Update PVC (Recommended)**
```bash
# 1. Copy artifacts to PVC
kubectl cp artifacts/ <pod-name>:/app/artifacts/ -n dz-clustering

# 2. Reload model
curl -X POST http://localhost:8000/reload_model \
  -H "X-API-Key: YOUR_KEY"
```

**Option 2: New Deployment**
```bash
# 1. Build new image with artifacts
docker build -t dz-customers-clustering:v2 .

# 2. Update deployment
kubectl set image deployment/dz-clustering-api \
  api=dz-customers-clustering:v2 \
  -n dz-clustering

# 3. Monitor rollout
kubectl rollout status deployment/dz-clustering-api -n dz-clustering
```

### Database Maintenance

```bash
# Backup ClickHouse data (if needed)
clickhouse-client --query "SELECT * FROM ... FORMAT CSV" > backup.csv

# Test connection
clickhouse-client --host=$CLICKHOUSE_HOST --query "SELECT 1"
```

### Secret Rotation

```bash
# 1. Generate new API key
make generate-api-key

# 2. Update secret
kubectl create secret generic dz-clustering-secrets \
  --from-literal=API_KEYS='["new-key"]' \
  --dry-run=client -o yaml | kubectl apply -f - -n dz-clustering

# 3. Restart pods
kubectl rollout restart deployment/dz-clustering-api -n dz-clustering
```

### Log Management

```bash
# View recent logs
kubectl logs deployment/dz-clustering-api -n dz-clustering --tail=100

# Follow logs
kubectl logs -f deployment/dz-clustering-api -n dz-clustering

# Export logs to file
kubectl logs deployment/dz-clustering-api -n dz-clustering > app.log

# If using ELK/Loki, query there
```

### Scaling

**Manual Scaling:**
```bash
# Scale up
kubectl scale deployment dz-clustering-api --replicas=5 -n dz-clustering

# Scale down
kubectl scale deployment dz-clustering-api --replicas=2 -n dz-clustering
```

**Auto-Scaling:**
```bash
# Check HPA status
kubectl get hpa -n dz-clustering

# Update HPA
kubectl edit hpa dz-clustering-hpa -n dz-clustering
```

### Backup & Recovery

**Backup:**
```bash
# 1. Backup Kubernetes configs
kubectl get all -n dz-clustering -o yaml > backup-k8s.yaml

# 2. Backup artifacts
kubectl cp <pod-name>:/app/artifacts ./artifacts-backup/ -n dz-clustering

# 3. Export secrets (encrypted)
kubectl get secret dz-clustering-secrets -n dz-clustering -o yaml > secrets-backup.yaml
```

**Recovery:**
```bash
# 1. Restore configs
kubectl apply -f backup-k8s.yaml

# 2. Restore artifacts
kubectl cp ./artifacts-backup/ <pod-name>:/app/artifacts/ -n dz-clustering

# 3. Reload model
curl -X POST http://localhost:8000/reload_model -H "X-API-Key: YOUR_KEY"
```

---

## Monitoring Checklist

### Daily
- [ ] Check error rates
- [ ] Review latency metrics
- [ ] Verify all pods are running
- [ ] Check disk space on PVC

### Weekly
- [ ] Review prediction accuracy
- [ ] Check data drift metrics
- [ ] Analyze traffic patterns
- [ ] Review resource utilization

### Monthly
- [ ] Update dependencies
- [ ] Rotate secrets
- [ ] Review and update alerts
- [ ] Performance tuning
- [ ] Model retraining evaluation

---

## Contact Information

**On-Call:**
- Primary: [Your Team]
- Secondary: [Backup Team]

**Escalation:**
- L1: DevOps Team
- L2: ML Engineering Team
- L3: Platform Team

**Communication Channels:**
- Slack: #dz-clustering-alerts
- Email: ml-ops@example.com
- PagerDuty: [Your PagerDuty Service]

