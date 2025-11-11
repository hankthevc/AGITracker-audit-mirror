#!/bin/bash
# Railway Deployment Verification Script
# Usage: ./verify_deployment.sh YOUR_API_URL YOUR_ADMIN_API_KEY

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <API_URL> <ADMIN_API_KEY>"
    echo "Example: $0 https://agi-tracker-production.up.railway.app sk-your-admin-key-here"
    exit 1
fi

API_URL=$1
ADMIN_API_KEY=$2

echo "🔍 Starting Railway Deployment Verification"
echo "==========================================="
echo ""

# Test 1: Health Endpoint
echo "Test 1: API Health Endpoint"
echo "-----------------------------------"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Health endpoint: PASS${NC}"
    echo "   Response: $BODY"
else
    echo -e "${RED}❌ Health endpoint: FAIL (HTTP $HTTP_CODE)${NC}"
    echo "   Response: $BODY"
fi
echo ""

# Test 2: Task Health Endpoint
echo "Test 2: Task Health Endpoint (Admin)"
echo "-----------------------------------"
TASK_HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "x-api-key: ${ADMIN_API_KEY}" \
    "${API_URL}/v1/admin/tasks/health")
HTTP_CODE=$(echo "$TASK_HEALTH_RESPONSE" | tail -n 1)
BODY=$(echo "$TASK_HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Task health endpoint: PASS${NC}"
    # Parse overall status
    OVERALL_STATUS=$(echo "$BODY" | grep -o '"overall_status":"[^"]*"' | cut -d'"' -f4)
    echo "   Overall Status: $OVERALL_STATUS"
    
    # Count task statuses
    PENDING=$(echo "$BODY" | grep -o '"pending":[0-9]*' | cut -d':' -f2)
    OK=$(echo "$BODY" | grep -o '"ok":[0-9]*' | cut -d':' -f2)
    ERROR=$(echo "$BODY" | grep -o '"error":[0-9]*' | cut -d':' -f2)
    
    echo "   Tasks - OK: $OK, Pending: $PENDING, Error: $ERROR"
elif [ "$HTTP_CODE" = "403" ]; then
    echo -e "${RED}❌ Task health endpoint: FAIL (Invalid API Key)${NC}"
    echo "   Check your ADMIN_API_KEY"
else
    echo -e "${RED}❌ Task health endpoint: FAIL (HTTP $HTTP_CODE)${NC}"
    echo "   Response: $BODY"
fi
echo ""

# Test 3: Events Endpoint
echo "Test 3: Events Endpoint"
echo "-----------------------------------"
EVENTS_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/v1/events?limit=1")
HTTP_CODE=$(echo "$EVENTS_RESPONSE" | tail -n 1)
BODY=$(echo "$EVENTS_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Events endpoint: PASS${NC}"
    EVENT_COUNT=$(echo "$BODY" | grep -o '"total":[0-9]*' | cut -d':' -f2)
    if [ -n "$EVENT_COUNT" ]; then
        echo "   Total events: $EVENT_COUNT"
    else
        echo "   Response appears valid (JSON array)"
    fi
else
    echo -e "${RED}❌ Events endpoint: FAIL (HTTP $HTTP_CODE)${NC}"
    echo "   Response: ${BODY:0:200}..."
fi
echo ""

# Test 4: Predictions/Surprises Endpoint
echo "Test 4: Predictions Surprises Endpoint"
echo "-----------------------------------"
SURPRISES_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/v1/predictions/surprises")
HTTP_CODE=$(echo "$SURPRISES_RESPONSE" | tail -n 1)
BODY=$(echo "$SURPRISES_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Surprises endpoint: PASS${NC}"
    COUNT=$(echo "$BODY" | grep -o '"count":[0-9]*' | cut -d':' -f2 | head -1)
    echo "   Surprise events found: ${COUNT:-0}"
else
    echo -e "${RED}❌ Surprises endpoint: FAIL (HTTP $HTTP_CODE)${NC}"
    echo "   Response: ${BODY:0:200}..."
fi
echo ""

# Test 5: Source Credibility Endpoint
echo "Test 5: Source Credibility Endpoint"
echo "-----------------------------------"
CREDIBILITY_RESPONSE=$(curl -s -w "\n%{http_code}" "${API_URL}/v1/admin/source-credibility")
HTTP_CODE=$(echo "$CREDIBILITY_RESPONSE" | tail -n 1)
BODY=$(echo "$CREDIBILITY_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Source credibility endpoint: PASS${NC}"
    TOTAL=$(echo "$BODY" | grep -o '"total_sources":[0-9]*' | cut -d':' -f2)
    echo "   Total sources tracked: ${TOTAL:-0}"
else
    echo -e "${RED}❌ Source credibility endpoint: FAIL (HTTP $HTTP_CODE)${NC}"
    echo "   Response: ${BODY:0:200}..."
fi
echo ""

# Summary
echo "==========================================="
echo "📊 Verification Summary"
echo "==========================================="
echo ""
echo "✅ = Test passed"
echo "❌ = Test failed (check logs above)"
echo ""
echo "Next Steps:"
echo "1. If any tests failed, check the Railway service logs"
echo "2. Verify environment variables are set correctly"
echo "3. Check VERIFICATION_CHECKLIST.md for detailed verification steps"
echo "4. Monitor Railway logs for scheduled task execution"
echo ""
echo "Railway CLI Commands:"
echo "  railway logs -s agi-tracker-api"
echo "  railway logs -s agi-tracker-celery-worker"
echo "  railway logs -s agi-tracker-celery-beat"
echo ""

