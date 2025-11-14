# API Documentation

## Base URL

```
Production: https://api.example.com
Development: http://localhost:8000
```

## Authentication

All endpoints (except public ones) require authentication via API key.

**Header Options:**

1. Bearer Token:
```bash
Authorization: Bearer YOUR_API_KEY
```

2. API Key Header:
```bash
X-API-Key: YOUR_API_KEY
```

## Endpoints

### Health Check

#### `GET /health`

Check API health and model status.

**Public:** Yes

**Response:**
```json
{
  "status": "ok",
  "model_loaded": true
}
```

**Status Codes:**
- `200`: Service is healthy
- `503`: Service unavailable

---

### Single Prediction

#### `POST /predict`

Predict cluster for a single customer.

**Authentication:** Required

**Request Body:**
```json
{
  "gender": "M",
  "age": 35.0,
  "bnpl_eligible": 1,
  "number_of_sessions": 10.0,
  "days_since_first_joined": 365.0,
  "number_of_failed_orders": 1.0,
  "number_of_successful_orders": 9.0
}
```

**Field Descriptions:**
| Field | Type | Required | Description | Constraints |
|-------|------|----------|-------------|-------------|
| gender | string | Yes | Customer gender | M, F, or Unknown |
| age | float | Yes | Customer age in years | >= 0 |
| bnpl_eligible | integer | Yes | BNPL eligibility | 0 or 1 |
| number_of_sessions | float | Yes | Total sessions | >= 0 |
| days_since_first_joined | float | Yes | Days since registration | >= 0 |
| number_of_failed_orders | float | Yes | Failed order count | >= 0 |
| number_of_successful_orders | float | Yes | Successful order count | >= 0 |

**Response:**
```json
{
  "cluster": 2,
  "scores": null,
  "meta": {
    "source": "predict_single"
  }
}
```

**Status Codes:**
- `200`: Successful prediction
- `422`: Invalid input data
- `503`: Model not loaded
- `500`: Internal server error

**Example:**
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "gender": "F",
    "age": 28.0,
    "bnpl_eligible": 0,
    "number_of_sessions": 5.0,
    "days_since_first_joined": 180.0,
    "number_of_failed_orders": 0.0,
    "number_of_successful_orders": 3.0
  }'
```

---

### Batch Prediction

#### `POST /batch_predict`

Predict clusters for multiple customers.

**Authentication:** Required

**Request Body:**
```json
{
  "customers": [
    {
      "gender": "M",
      "age": 35.0,
      "bnpl_eligible": 1,
      "number_of_sessions": 10.0,
      "days_since_first_joined": 365.0,
      "number_of_failed_orders": 1.0,
      "number_of_successful_orders": 9.0
    },
    {
      "gender": "F",
      "age": 28.0,
      "bnpl_eligible": 0,
      "number_of_sessions": 5.0,
      "days_since_first_joined": 180.0,
      "number_of_failed_orders": 0.0,
      "number_of_successful_orders": 3.0
    }
  ]
}
```

**Response:**
```json
[
  {
    "cluster": 2
  },
  {
    "cluster": 1
  }
]
```

**Status Codes:**
- `200`: Successful predictions
- `422`: Invalid input data
- `503`: Model not loaded
- `500`: Internal server error

**Example:**
```bash
curl -X POST "http://localhost:8000/batch_predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "customers": [
      {
        "gender": "M",
        "age": 35.0,
        "bnpl_eligible": 1,
        "number_of_sessions": 10.0,
        "days_since_first_joined": 365.0,
        "number_of_failed_orders": 1.0,
        "number_of_successful_orders": 9.0
      }
    ]
  }'
```

---

### Model Reload

#### `POST /reload_model`

Hot-reload the ML model without restarting the service.

**Authentication:** Required

**Request Body:** None

**Response:**
```json
{
  "detail": "model reloaded"
}
```

**Status Codes:**
- `200`: Model successfully reloaded
- `500`: Reload failed

**Example:**
```bash
curl -X POST "http://localhost:8000/reload_model" \
  -H "X-API-Key: YOUR_API_KEY"
```

---

### Metrics

#### `GET /metrics`

Prometheus metrics endpoint.

**Public:** Yes

**Response:** Prometheus text format

**Example:**
```bash
curl "http://localhost:8000/metrics"
```

**Metrics Exposed:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration
- `ml_predictions_total` - Total predictions
- `ml_prediction_duration_seconds` - Prediction duration
- `ml_model_load_time_seconds` - Model load time
- `ml_data_drift_score` - Data drift score

---

### Root

#### `GET /`

API information.

**Public:** Yes

**Response:**
```json
{
  "name": "DZ Customers Clustering API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs",
  "health": "/health",
  "metrics": "/metrics"
}
```

---

## Error Responses

### Standard Error Format

```json
{
  "detail": "Error message"
}
```

### Common Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing or invalid API key |
| 422 | Unprocessable Entity | Invalid input data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

---

## Rate Limiting

**Default Limits:**
- 60 requests per minute per IP
- 1000 requests per hour per IP

**Response Headers:**
- `X-RateLimit-Limit-Minute`: Requests allowed per minute
- `X-RateLimit-Remaining-Minute`: Requests remaining this minute
- `X-RateLimit-Limit-Hour`: Requests allowed per hour
- `X-RateLimit-Remaining-Hour`: Requests remaining this hour

**Rate Limit Exceeded:**
```json
{
  "detail": "Rate limit exceeded: 60 requests per minute"
}
```

**Response Headers:**
- `Retry-After: 60` - Seconds until retry

---

## Interactive Documentation

### Swagger UI

Visit `/docs` for interactive API documentation with:
- Endpoint descriptions
- Request/response schemas
- Try-it-out functionality
- Authentication support

### ReDoc

Visit `/redoc` for alternative documentation format with:
- Clean, responsive design
- Code examples
- Downloadable OpenAPI spec

---

## Client Examples

### Python

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your-api-key"

# Single prediction
response = requests.post(
    f"{API_URL}/predict",
    headers={"X-API-Key": API_KEY},
    json={
        "gender": "M",
        "age": 35.0,
        "bnpl_eligible": 1,
        "number_of_sessions": 10.0,
        "days_since_first_joined": 365.0,
        "number_of_failed_orders": 1.0,
        "number_of_successful_orders": 9.0,
    }
)

print(response.json())
```

### JavaScript

```javascript
const API_URL = 'http://localhost:8000';
const API_KEY = 'your-api-key';

// Single prediction
fetch(`${API_URL}/predict`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify({
    gender: 'M',
    age: 35.0,
    bnpl_eligible: 1,
    number_of_sessions: 10.0,
    days_since_first_joined: 365.0,
    number_of_failed_orders: 1.0,
    number_of_successful_orders: 9.0
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL

```bash
# Single prediction
curl -X POST "${API_URL}/predict" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ${API_KEY}" \
  -d '{
    "gender": "M",
    "age": 35.0,
    "bnpl_eligible": 1,
    "number_of_sessions": 10.0,
    "days_since_first_joined": 365.0,
    "number_of_failed_orders": 1.0,
    "number_of_successful_orders": 9.0
  }'
```

---

## Best Practices

1. **Use Batch Predictions** for multiple customers to reduce overhead
2. **Cache Results** on your end when appropriate
3. **Handle Rate Limits** with exponential backoff
4. **Monitor Your Usage** via the metrics endpoint
5. **Validate Input** before sending to reduce errors
6. **Use HTTPS** in production
7. **Rotate API Keys** regularly

