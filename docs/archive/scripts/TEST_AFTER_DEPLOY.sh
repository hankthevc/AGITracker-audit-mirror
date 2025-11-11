#!/bin/bash
# Test script after Railway deployment completes

echo "🧪 Testing AGI Tracker API after deployment..."
echo ""

echo "1. Testing health endpoint:"
curl -s "https://agi-tracker-production.up.railway.app/health" | jq '.'
echo ""

echo "2. Testing events count:"
curl -s "https://agi-tracker-production.up.railway.app/v1/events" | jq '.total'
echo ""

echo "3. Testing sample event titles:"
curl -s "https://agi-tracker-production.up.railway.app/v1/events?limit=3" | jq '.items[].title'
echo ""

echo "4. Testing digests endpoint:"
curl -s "https://agi-tracker-production.up.railway.app/v1/digests" | jq '.'
echo ""

echo "5. Testing index:"
curl -s "https://agi-tracker-production.up.railway.app/v1/index" | jq '{overall, capabilities, agents, inputs, security}'
echo ""

echo "✅ If events count > 0, deployment successful!"
echo "❌ If events count = 0, DATABASE_URL still not updated"

