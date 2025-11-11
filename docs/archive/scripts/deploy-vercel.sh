#!/bin/bash

# AGI Tracker - Vercel Deployment Script
# Run this after initial setup to deploy updates

set -e  # Exit on error

echo "🚀 AGI Tracker Deployment"
echo "=========================="
echo ""

# Check if we're in the right directory
if [ ! -f "vercel.json" ]; then
    echo "❌ Error: vercel.json not found. Are you in the project root?"
    exit 1
fi

# Check if build works locally
echo "📦 Building locally first..."
cd apps/web
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Local build successful"
else
    echo "❌ Local build failed. Fix errors before deploying."
    exit 1
fi

cd ../..

# Deploy to Vercel
echo ""
echo "🌍 Deploying to Vercel..."
npx vercel --prod

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Visit your Vercel dashboard to see the deployment"
echo "  2. Test your URL: https://agi-tracker-*.vercel.app"
echo "  3. Set NEXT_PUBLIC_API_BASE_URL env var once backend is deployed"

