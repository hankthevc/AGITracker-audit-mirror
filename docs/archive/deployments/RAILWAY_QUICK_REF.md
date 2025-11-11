# 🔑 Railway Deployment - Quick Reference

**Copy and paste these values when deploying**

---

## Environment Variables for Railway

### DATABASE_URL
```
your_neon_database_url_here
```

### OPENAI_API_KEY
```
your_openai_api_key_here
```

### API_KEY
**Generate fresh with:**
```bash
openssl rand -base64 32
```

Or use this pre-generated one (rotate after testing):
```
[The script will generate this for you]
```

### Optional Variables
```
ENVIRONMENT=production
LOG_LEVEL=info
CORS_ORIGINS=https://your-vercel-url.vercel.app
```

---

## Deployment Command

**Automated (easiest)**:
```bash
cd /Users/HenryAppel/AI\ Doomsday\ Tracker
./deploy-backend-auto.sh
```

This script will:
✅ Check Railway CLI installation
✅ Login to Railway
✅ Initialize project
✅ Generate API key
✅ Guide you through variable setup
✅ Deploy automatically
✅ Test the deployment
✅ Give you your URL

---

## After Deployment

### Get Your URL
```bash
railway domain
```

### Test Endpoints
```bash
# Save URL
export API_URL="https://your-railway-url.up.railway.app"

# Health check
curl $API_URL/health

# Get events
curl $API_URL/v1/events | jq

# Get review queue stats
curl $API_URL/v1/review-queue/stats | jq
```

### Connect to Vercel
```bash
npx vercel env add NEXT_PUBLIC_API_BASE_URL production
# Paste your Railway URL when prompted

npx vercel --prod
```

---

## Monitoring

### View Logs
```bash
railway logs --follow
```

### Open Dashboard
```bash
railway open
```

### Check Status
```bash
railway status
```

---

## Troubleshooting

### If deployment fails:
```bash
# Check logs
railway logs

# Verify env vars
railway variables

# Redeploy
railway up
```

### If health check fails:
```bash
# Wait 30 seconds for startup
sleep 30
curl https://your-url/health

# Check logs for errors
railway logs --tail 50
```

---

## Quick Commands

```bash
# CD to project
cd /Users/HenryAppel/AI\ Doomsday\ Tracker

# Deploy
./deploy-backend-auto.sh

# Or manual
cd services/etl
railway login
railway init
railway up

# Get URL
railway domain

# View logs
railway logs --follow

# Open dashboard
railway open
```

---

**Time to deploy**: 10-15 minutes  
**What you'll do**: Run script, paste 3 variables, wait  
**What happens**: Fully deployed backend API 🚀

