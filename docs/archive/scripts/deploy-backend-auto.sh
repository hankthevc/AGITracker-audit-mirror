#!/bin/bash

# AGI Tracker - Automated Railway Deployment
# This script automates as much as possible

set -e

echo "🚂 AGI Tracker Backend - Automated Railway Deployment"
echo "======================================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Railway CLI
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found${NC}"
    echo "Installing via Homebrew..."
    brew install railway
    echo -e "${GREEN}✅ Railway CLI installed${NC}"
fi

echo -e "${BLUE}Railway CLI version:${NC}"
railway --version
echo ""

# Step 1: Login
echo -e "${YELLOW}Step 1: Login to Railway${NC}"
echo "This will open your browser for authentication..."
echo ""
read -p "Press Enter to open browser and login..."

if railway login; then
    echo -e "${GREEN}✅ Successfully logged in${NC}"
else
    echo -e "${RED}❌ Login failed. Please try again.${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Navigate to backend directory${NC}"
cd services/etl
echo -e "${GREEN}✅ In $(pwd)${NC}"
echo ""

# Step 3: Initialize project
echo -e "${YELLOW}Step 3: Initialize Railway project${NC}"
echo "Creating new Railway project..."
echo ""

railway init --name "agi-tracker-api"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Project initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Project may already exist. Continuing...${NC}"
fi

echo ""
echo -e "${YELLOW}Step 4: Environment Variables${NC}"
echo ""
echo "Now we need to set up environment variables."
echo "You'll need:"
echo "  1. DATABASE_URL (Neon)"
echo "  2. OPENAI_API_KEY"
echo "  3. API_KEY (admin endpoints)"
echo ""

# Generate API key
echo -e "${BLUE}Generating API_KEY...${NC}"
GENERATED_API_KEY=$(openssl rand -base64 32)
echo -e "${GREEN}Generated API_KEY: ${GENERATED_API_KEY}${NC}"
echo -e "${YELLOW}⚠️  SAVE THIS KEY SECURELY!${NC}"
echo ""
echo "$GENERATED_API_KEY" > .api_key_generated.txt
echo "API key also saved to: services/etl/.api_key_generated.txt"
echo ""

read -p "Press Enter to add environment variables in Railway dashboard..."

echo ""
echo "Opening Railway dashboard..."
railway open

echo ""
echo -e "${BLUE}In the Railway dashboard:${NC}"
echo "  1. Click 'Variables' tab"
echo "  2. Add these variables:"
echo ""
echo -e "${GREEN}Required variables:${NC}"
echo "  DATABASE_URL = (paste your Neon connection string)"
echo "  OPENAI_API_KEY = (paste your OpenAI key)"  
echo "  API_KEY = $GENERATED_API_KEY"
echo ""
echo -e "${GREEN}Optional but recommended:${NC}"
echo "  ENVIRONMENT = production"
echo "  LOG_LEVEL = info"
echo ""

read -p "Press Enter once you've added all variables..."

# Step 5: Deploy
echo ""
echo -e "${YELLOW}Step 5: Deploy to Railway${NC}"
echo "Uploading code and building..."
echo ""

railway up

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Deployment successful!${NC}"
else
    echo ""
    echo -e "${RED}❌ Deployment failed. Check errors above.${NC}"
    exit 1
fi

# Step 6: Get domain
echo ""
echo -e "${YELLOW}Step 6: Get your public URL${NC}"
echo ""

DOMAIN=$(railway domain 2>&1 | grep -o 'https://[^[:space:]]*' | head -1)

if [ -z "$DOMAIN" ]; then
    echo "Getting domain..."
    echo "Run this command to see your URL:"
    echo "  railway domain"
else
    echo -e "${GREEN}Your backend API is live at:${NC}"
    echo -e "${BLUE}${DOMAIN}${NC}"
    echo ""
    
    # Test the deployment
    echo -e "${YELLOW}Step 7: Testing deployment${NC}"
    echo ""
    
    sleep 5  # Give it a moment to start
    
    echo "Testing health endpoint..."
    if curl -f -s "${DOMAIN}/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check passed!${NC}"
        curl -s "${DOMAIN}/health" | jq '.' || curl -s "${DOMAIN}/health"
    else
        echo -e "${YELLOW}⚠️  Health check pending (service may still be starting)${NC}"
        echo "Try manually: curl ${DOMAIN}/health"
    fi
fi

echo ""
echo "=================================================="
echo -e "${GREEN}✅ DEPLOYMENT COMPLETE!${NC}"
echo "=================================================="
echo ""
echo -e "${BLUE}Your API URL:${NC}"
railway domain || echo "Run 'railway domain' to get your URL"
echo ""
echo -e "${BLUE}API Key (admin endpoints):${NC}"
echo "$GENERATED_API_KEY"
echo "(Also saved in services/etl/.api_key_generated.txt)"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Test your API:"
echo "     export API_URL=\$(railway domain)"
echo "     curl \$API_URL/health"
echo "     curl \$API_URL/v1/events | jq"
echo ""
echo "  2. Connect frontend (Vercel):"
echo "     npx vercel env add NEXT_PUBLIC_API_BASE_URL production"
echo "     (Enter your Railway URL above)"
echo "     npx vercel --prod"
echo ""
echo "  3. View logs:"
echo "     railway logs --follow"
echo ""
echo "  4. Open dashboard:"
echo "     railway open"
echo ""
echo -e "${GREEN}Backend deployment successful! 🎉${NC}"

