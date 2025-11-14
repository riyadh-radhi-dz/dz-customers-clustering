#!/bin/bash
echo "🧪 DZ Clustering MLOps Quick Test"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Testing API Health...${NC}"
curl -s http://localhost:8000/health | jq
echo ""

echo -e "${BLUE}2. Testing Single Prediction...${NC}"
curl -s -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "gender": "M",
    "age": 35.0,
    "bnpl_eligible": 1,
    "number_of_sessions": 10.0,
    "days_since_first_joined": 365.0,
    "number_of_failed_orders": 1.0,
    "number_of_successful_orders": 9.0
  }' | jq
echo ""

echo -e "${BLUE}3. Testing Cache Stats...${NC}"
curl -s http://localhost:8000/cache/stats | jq
echo ""

echo -e "${BLUE}4. Checking Prometheus Metrics...${NC}"
echo "Total requests:"
curl -s http://localhost:8000/metrics | grep -E "^http_requests_total" | head -3
echo ""
echo "Predictions:"
curl -s http://localhost:8000/metrics | grep -E "^ml_predictions_total" | head -3
echo ""

echo -e "${GREEN}✅ Quick test complete!${NC}"
echo ""
echo "📊 Access the services:"
echo "  - API Docs: http://localhost:8000/docs"
echo "  - MLflow: http://localhost:5001"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo ""
echo "📖 Full testing guide: cat TESTING_GUIDE.md"
