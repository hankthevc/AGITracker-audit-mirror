#!/bin/bash
# Quick deployment script for AGI Tracker
# Runs all necessary seed tasks and validations

set -e  # Exit on error

echo "🚀 AGI Tracker - Quick Start Deployment"
echo "========================================"
echo ""

# Check environment
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL not set"
    echo "   Set with: export DATABASE_URL='your_neon_database_url'"
    exit 1
fi

if [ -z "$REDIS_URL" ]; then
    echo "⚠️  WARNING: REDIS_URL not set (Celery tasks will not work)"
fi

if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  WARNING: OPENAI_API_KEY not set (Will use mock LLM analysis)"
fi

echo "✅ Environment variables OK"
echo ""

# Navigate to ETL directory
cd services/etl || exit 1

echo "📦 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

echo "🗄️  Running database migrations..."
cd ../../infra/migrations || exit 1
alembic upgrade head
cd ../../services/etl || exit 1
echo "✅ Migrations complete"
echo ""

echo "🌱 Seeding database..."

# Seed expert predictions
echo "  📊 Loading expert predictions..."
python -c "
from app.tasks.predictions.seed_expert_predictions import seed_all_predictions
seed_all_predictions()
"
echo "✅ Expert predictions loaded"
echo ""

# Optional: Run golden set test
read -p "🧪 Run mapper golden set test? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  🧪 Running golden set test..."
    pytest tests/test_mapper_accuracy.py -v
fi

echo ""
echo "✅ Seed tasks complete!"
echo ""

# Verify health
echo "🏥 Checking API health..."
cd ../../ || exit 1

# Start API in background for health check
if command -v uvicorn &> /dev/null; then
    echo "  Starting API server..."
    cd services/etl || exit 1
    uvicorn app.main:app --host 0.0.0.0 --port 8000 &
    API_PID=$!
    sleep 3
    
    # Health check
    if curl -s http://localhost:8000/health | grep -q "ok"; then
        echo "✅ API health check passed"
    else
        echo "⚠️  API health check failed"
    fi
    
    # Stop API
    kill $API_PID 2>/dev/null || true
    cd ../../ || exit 1
else
    echo "⚠️  uvicorn not found, skipping health check"
fi

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Deploy to Railway:"
echo "     railway up"
echo ""
echo "  2. Start Celery worker:"
echo "     celery -A app.celery_app worker --loglevel=info"
echo ""
echo "  3. Start Celery beat (scheduler):"
echo "     celery -A app.celery_app beat --loglevel=info"
echo ""
echo "  4. Deploy frontend to Vercel:"
echo "     cd apps/web && vercel --prod"
echo ""
echo "  5. View events:"
echo "     https://your-frontend.vercel.app/events"
echo ""
echo "📚 See IMPLEMENTATION_COMPLETE_NEXT_STEPS.md for full details"

