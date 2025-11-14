#!/bin/bash
# Quick test script for Champion/Challenger system

echo "🏆 Champion/Challenger System Test"
echo "===================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from template..."
    cp .env.example .env 2>/dev/null || echo "Please create .env file with ClickHouse credentials"
    echo ""
fi

# Check if MLflow is installed
if ! python3 -c "import mlflow" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  MLflow not installed${NC}"
    echo "Installing MLflow..."
    pip install mlflow scikit-learn
    echo ""
fi

# Check current champion
echo -e "${BLUE}📦 Checking current champion model...${NC}"
if [ -d "artifacts/champion" ] && [ -f "artifacts/champion/kmeans_cta_model.pkl" ]; then
    echo -e "${GREEN}✅ Champion model exists${NC}"
    echo "   Location: artifacts/champion/"
    ls -lh artifacts/champion/*.pkl 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
    echo ""
    
    # Show when it was created
    CHAMP_DATE=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" artifacts/champion/kmeans_cta_model.pkl 2>/dev/null || stat -c "%y" artifacts/champion/kmeans_cta_model.pkl 2>/dev/null | cut -d'.' -f1)
    echo "   Last updated: $CHAMP_DATE"
else
    echo -e "${YELLOW}⚠️  No champion model found${NC}"
    echo "   This will be your first run - it will become the champion"
fi

echo ""
echo -e "${BLUE}🔄 Would you like to run validation now?${NC}"
echo "This will:"
echo "  1. Train a new model (Challenger)"
echo "  2. Compare with current Champion (if exists)"
echo "  3. Promote if Challenger is >2% better"
echo ""
read -p "Run validation? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo -e "${BLUE}🚀 Running validation and promotion pipeline...${NC}"
    echo "===================================="
    echo ""
    
    # Run the validation script
    python3 validate_and_promote_model.py
    
    EXIT_CODE=$?
    
    echo ""
    echo "===================================="
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Validation completed successfully!${NC}"
        echo ""
        
        # Show results
        if [ -f "artifacts/promotion_report.json" ]; then
            echo -e "${BLUE}📊 Results:${NC}"
            
            # Extract key info using python
            python3 << 'PYTHON_SCRIPT'
import json
try:
    with open('artifacts/promotion_report.json') as f:
        report = json.load(f)
    
    decision = report.get('decision', 'Unknown')
    reason = report.get('reason', 'No reason provided')
    
    if decision == "PROMOTE":
        print("   🎉 Decision: PROMOTED to production")
    elif decision == "KEEP_CHAMPION":
        print("   🛡️  Decision: Champion RETAINED")
    elif decision == "FIRST_DEPLOYMENT":
        print("   🏆 Decision: First deployment")
    
    print(f"   Reason: {reason}")
    
    if 'challenger' in report and 'composite_score' in report['challenger']:
        challenger_score = report['challenger']['composite_score']
        print(f"\n   Challenger Score: {challenger_score:.4f}")
    
    if 'champion' in report and 'composite_score' in report['champion']:
        champion_score = report['champion']['composite_score']
        print(f"   Champion Score: {champion_score:.4f}")
        
        if 'improvements' in report and 'composite_score' in report['improvements']:
            improvement = report['improvements']['composite_score']
            print(f"   Improvement: {improvement:+.2f}%")

except Exception as e:
    print(f"   Could not parse report: {e}")
PYTHON_SCRIPT
            
            echo ""
        fi
        
        echo -e "${BLUE}📁 Check files:${NC}"
        echo "   Champion: artifacts/champion/"
        echo "   Challenger: artifacts/challenger/"
        echo "   Report: artifacts/promotion_report.json"
        echo ""
        
        echo -e "${BLUE}📊 View in MLflow:${NC}"
        echo "   http://localhost:5001"
        echo ""
        
        echo -e "${BLUE}🔄 Reload model in API:${NC}"
        echo "   curl -X POST http://localhost:8000/reload_model"
        echo ""
    else
        echo -e "${YELLOW}❌ Validation failed with exit code $EXIT_CODE${NC}"
        echo "Check the logs above for errors"
        echo ""
    fi
else
    echo ""
    echo "Validation skipped."
    echo ""
    echo "To run manually:"
    echo "  make validate-and-promote"
    echo "  or"
    echo "  python3 validate_and_promote_model.py"
    echo ""
fi

echo -e "${BLUE}📚 Documentation:${NC}"
echo "  Quick Start: AUTO_MODEL_UPDATE_SUMMARY.md"
echo "  Full Guide:  MODEL_VALIDATION_GUIDE.md"
echo ""
echo "✅ Done!"

