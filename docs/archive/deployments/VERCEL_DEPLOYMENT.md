# 🚀 Vercel Deployment Guide

## Prerequisites
✅ Vercel CLI installed (`vercel` v48.5.0)
✅ GitHub repository: https://github.com/hankthevc/AGITracker
✅ vercel.json configuration created

## Quick Start (5 minutes)

### Step 1: Login to Vercel

```bash
cd /Users/HenryAppel/AI\ Doomsday\ Tracker
npx vercel login
```

This will:
1. Open your browser
2. Ask you to sign up/login (use your GitHub account for easiest setup)
3. Authenticate the CLI

### Step 2: Deploy

```bash
npx vercel
```

The CLI will ask you:

**"Set up and deploy?"** → Press **Enter** (Yes)

**"Which scope?"** → Select your account (press Enter)

**"Link to existing project?"** → Press **n** (No, create new)

**"What's your project's name?"** → Type: `agi-tracker` (or leave default)

**"In which directory is your code located?"** → Press **Enter** (`.` is correct)

**Vercel will detect:**
- ✓ Monorepo structure
- ✓ Next.js in `apps/web`
- ✓ Build settings from `vercel.json`

**"Want to override settings?"** → Press **n** (No)

### Step 3: Wait for Build

Vercel will:
1. ✓ Upload your code
2. ✓ Install dependencies (`npm install`)
3. ✓ Build Next.js (`npm run build --workspace=apps/web`)
4. ✓ Deploy to CDN

**Build time**: ~2-3 minutes

### Step 4: Get Your URL

After deployment, you'll see:

```
✅ Production: https://agi-tracker-abc123.vercel.app
```

**Copy this URL!** You'll need it.

## Important: Set Environment Variable

Your frontend needs to know where the backend API is:

### Option A: Using Vercel Dashboard (Recommended)

1. Go to https://vercel.com/dashboard
2. Click your project (`agi-tracker`)
3. Go to **Settings** → **Environment Variables**
4. Add:
   - **Key**: `NEXT_PUBLIC_API_BASE_URL`
   - **Value**: (leave empty for now, we'll add after deploying backend)
   - **Environment**: Production, Preview, Development (check all)
5. Click **Save**

### Option B: Using CLI

```bash
npx vercel env add NEXT_PUBLIC_API_BASE_URL production
# When prompted, enter: (leave empty for now)
```

## Test Your Deployment

Visit: `https://agi-tracker-abc123.vercel.app/events`

**Expected**:
- ✅ Page loads (even if data doesn't load yet)
- ✅ Dark mode toggle works
- ✅ Filters render correctly

**If data doesn't load**: That's fine! The backend isn't deployed yet.

## Automatic Deployments (Already Configured!)

Every time you push to GitHub:
```bash
git push origin main
```

Vercel automatically:
1. Detects the push
2. Runs a new build
3. Deploys to production
4. Updates your URL

**You never need to run `vercel` again!**

## Troubleshooting

### "Error: No framework detected"

**Solution**: Your `vercel.json` is configured correctly. Just press Enter through the prompts.

### "Build failed"

**Check**:
1. Does `npm run build --workspace=apps/web` work locally?
2. Are all dependencies in `apps/web/package.json`?

**Fix**: Run locally first:
```bash
cd apps/web
npm install
npm run build
```

### "Module not found" errors

**Solution**: Make sure you committed all changes:
```bash
git add -A
git commit -m "fix: Add missing dependencies"
git push origin main
```

Vercel will auto-rebuild.

## Next Steps After Deployment

### 1. Deploy Backend (Railway)
See: `RAILWAY_DEPLOYMENT.md` (to be created)

### 2. Connect Frontend to Backend
Once backend is deployed to Railway:
```bash
# Add backend URL to Vercel
npx vercel env add NEXT_PUBLIC_API_BASE_URL production
# Enter: https://agi-tracker-api.railway.app

# Redeploy to pick up new env var
npx vercel --prod
```

### 3. Custom Domain (Optional)
1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain (e.g., `agi-tracker.com`)
3. Follow DNS instructions (add CNAME record)

## Monitoring

**Vercel Dashboard** shows:
- Build logs
- Deployment status
- Analytics (page views, performance)
- Error tracking

Access at: https://vercel.com/dashboard

## Costs

**Free Tier includes**:
- 100GB bandwidth/month
- Unlimited deployments
- Automatic HTTPS
- Global CDN

**You'll only pay if you exceed** (unlikely for this project):
- Bandwidth > 100GB/month
- Build time > 6,000 minutes/month

**Expected cost**: $0/month

## Quick Reference

```bash
# View deployment logs
npx vercel logs

# Deploy to production (after changes)
npx vercel --prod

# View environment variables
npx vercel env ls

# Rollback to previous deployment
npx vercel rollback

# View project info
npx vercel inspect
```

## Summary

✅ **What you need to do**:
1. Run `npx vercel login`
2. Run `npx vercel`
3. Press Enter a few times
4. Copy your URL

✅ **What happens automatically**:
- Every `git push` triggers new deployment
- Build & deploy in ~2-3 minutes
- Global CDN distribution
- Automatic HTTPS

✅ **Total time**: 5 minutes

---

**Ready?** Open your terminal and run:
```bash
cd /Users/HenryAppel/AI\ Doomsday\ Tracker
npx vercel login
```

