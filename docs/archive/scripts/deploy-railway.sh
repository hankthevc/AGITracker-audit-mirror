#!/bin/bash

# AGI Tracker - Railway Backend Deployment Helper
# This script helps you deploy the backend API to Railway

set -e

echo "🚂 AGI Tracker - Railway Backend Deployment"
echo "============================================"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
    echo "✅ Railway CLI installed"
    echo ""
fi

# Check Railway login
if ! railway whoami &> /dev/null; then
    echo "🔑 Please login to Railway..."
    railway login
    echo "✅ Logged in to Railway"
    echo ""
fi

# Navigate to etl directory
cd services/etl

echo "📋 Railway Deployment Checklist:"
echo ""
echo "You will need:"
echo "  1. ✅ Your Neon DATABASE_URL"
echo "  2. ✅ Your OpenAI API KEY"
echo "  3. ✅ A generated API_KEY for admin endpoints"
echo ""

read -p "Do you have all the above ready? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Please gather the following:"
    echo "  - DATABASE_URL: From your Neon dashboard"
    echo "  - OPENAI_API_KEY: From platform.openai.com"
    echo "  - API_KEY: Generate with: openssl rand -base64 32"
    echo ""
    echo "Then run this script again!"
    exit 1
fi

echo ""
echo "🚀 Starting Railway deployment..."
echo ""

# Initialize Railway project
echo "Step 1: Initialize Railway project"
railway init

echo ""
echo "Step 2: Add environment variables"
echo ""
echo "Now, add your environment variables in the Railway dashboard:"
echo "  1. Go to https://railway.app/dashboard"
echo "  2. Select your project"
echo "  3. Click 'Variables' tab"
echo "  4. Add these variables:"
echo ""
echo "     DATABASE_URL=<your-neon-url>"
echo "     OPENAI_API_KEY=<your-openai-key>"
echo "     API_KEY=<generated-random-key>"
echo "     ENVIRONMENT=production"
echo "     LOG_LEVEL=info"
echo ""

read -p "Press Enter when you've added the variables..."

echo ""
echo "Step 3: Deploy to Railway"
railway up

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "  1. Check deployment status: railway logs --follow"
echo "  2. Get your URL: railway domain"
echo "  3. Test health: curl https://your-url/health"
echo "  4. Update Vercel env: NEXT_PUBLIC_API_BASE_URL=https://your-url"
echo ""
echo "Full guide: See RAILWAY_DEPLOYMENT.md"

