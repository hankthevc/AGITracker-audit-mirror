# GitHub Audit Mirror Setup Checklist

**Status**: ⚠️ NOT YET CONFIGURED  
**Action Required**: Follow steps 1-5 below

---

## Prerequisites

- ✅ Hardened workflow committed: `.github/workflows/publish-audit-snapshot.yml`
- ⏳ Public mirror repo: NOT CREATED YET
- ⏳ Access token: NOT CREATED YET
- ⏳ Secret configured: NOT SET YET

---

## Step-by-Step Setup (10 minutes)

### Step 1: Create Public Mirror Repository

1. **Go to**: https://github.com/new
2. **Repository name**: `AGITracker-audit-mirror`
3. **Description**: `Public audit snapshot of AGI Tracker for security verification`
4. **Visibility**: ✅ **Public** (CRITICAL - must be public)
5. **Initialize**:
   - ❌ Do NOT add README
   - ❌ Do NOT add .gitignore
   - ❌ Do NOT add license
   - (Workflow will create all files)
6. Click **"Create repository"**
7. **Note the repository URL**: `https://github.com/hankthevc/AGITracker-audit-mirror`

✅ **Verification**: Repository exists and is **public**

---

### Step 2: Generate Fine-Grained Personal Access Token

1. **Go to**: https://github.com/settings/tokens?type=beta
2. Click **"Generate new token"** (fine-grained)
3. **Token name**: `AGI Tracker Audit Mirror Bot`
4. **Expiration**: 90 days (recommended)
5. **Resource owner**: `hankthevc` (your username)
6. **Repository access**: ✅ **Only select repositories**
   - Click "Select repositories"
   - Choose **only**: `AGITracker-audit-mirror`
7. **Permissions** → **Repository permissions**:
   - **Contents**: ✅ **Read and write** (required for push)
   - **Metadata**: Read-only (auto-selected)
   - All others: No access
8. Click **"Generate token"**
9. **COPY THE TOKEN** immediately (you won't see it again)
   - Should look like: `github_pat_11AXXXXX...` (82 characters)

✅ **Verification**: Token copied to clipboard

---

### Step 3: Add Secret to Private Repository

1. **Go to**: https://github.com/hankthevc/AGITracker/settings/secrets/actions
2. Click **"New repository secret"**
3. **Name** (EXACT): `GH_MIRROR_TOKEN`
4. **Secret**: Paste the token from Step 2
5. Click **"Add secret"**

✅ **Verification**: Secret `GH_MIRROR_TOKEN` appears in list

---

### Step 4: Trigger Workflow Manually

1. **Go to**: https://github.com/hankthevc/AGITracker/actions/workflows/publish-audit-snapshot.yml
2. Click **"Run workflow"** dropdown button
3. Branch: `main`
4. Click green **"Run workflow"** button
5. Wait 30-60 seconds for workflow to complete
6. **Check for green checkmark** ✅

If workflow fails:
- Click the failed run
- Expand "Push to public mirror" step
- Check error message
- Common issues:
  - Token missing → Verify Step 3
  - Permission denied → Regenerate token with correct permissions
  - 404 not found → Verify mirror repo exists and is public

✅ **Verification**: Workflow completes with green checkmark

---

### Step 5: Verify Mirror Works

Run these commands from your terminal:

```bash
# 1. Check mirror README exists
curl -I https://raw.githubusercontent.com/hankthevc/AGITracker-audit-mirror/main/README.md

# Expected: HTTP/2 200

# 2. List root directory
curl -s https://api.github.com/repos/hankthevc/AGITracker-audit-mirror/contents/ | jq '.[].name'

# Expected: List of directories (apps, services, infra, docs, etc.)

# 3. Check latest commit
curl -s https://api.github.com/repos/hankthevc/AGITracker-audit-mirror/commits | jq '.[0] | {sha:.sha[0:7], msg:.commit.message, date:.commit.author.date}'

# Expected: Recent commit with message like "Audit snapshot: <sha>"

# 4. Verify MANIFEST.txt exists
curl -s https://raw.githubusercontent.com/hankthevc/AGITracker-audit-mirror/main/MANIFEST.txt | wc -l

# Expected: ~500-1000 lines (list of all files)
```

✅ **Verification**: All 4 commands return expected results

---

## What Gets Published

### ✅ Included (Public Audit Scope)
- **Migrations**: All database migration files
- **Frontend**:
  - Security code (SafeLink, CSP config)
  - Legal pages (privacy, terms)
  - Test suites
- **Backend**:
  - Seed loader + validator
  - Auth/audit utilities
  - Admin router (for audit logging verification)
  - Tests (seed validation, audit logging)
- **CI/CD**: All workflow files
- **Documentation**: Engineering docs, security docs, state reports

### ❌ Excluded (Security)
- `.env` files (secrets)
- `node_modules/` (dependencies)
- `.next/` (build artifacts)
- `__pycache__/` (compiled Python)
- `.cursor/` (IDE config)
- Any files with API keys or tokens

---

## Usage for GPT-5 Pro Audits

Once setup is complete, give GPT-5 this message:

```
Please audit the AGI Tracker codebase:
https://github.com/hankthevc/AGITracker-audit-mirror

This is an auto-updated public snapshot (syncs on every push to main).

Verify:
1. Migration integrity (single head at 030_openai_prep_conf)
2. SafeLink enforcement (zero raw <a> tags)
3. CSP production strictness (no unsafe directives)
4. Seed validation (ON CONFLICT + validator)
5. Audit logging (all admin routes call log_admin_action)

See docs/ops/FINAL_STATE_REPORT.md for verification commands.
```

---

## Troubleshooting

### "Repository not found" (404)
- **Cause**: Mirror repo doesn't exist or isn't public
- **Fix**: Complete Step 1, ensure **Public** visibility

### "Permission denied" / "403 Forbidden"
- **Cause**: Token missing or wrong permissions
- **Fix**: 
  - Verify `GH_MIRROR_TOKEN` secret exists (Step 3)
  - Regenerate token with **Contents: Read and write** (Step 2)
  - Ensure token is for `AGITracker-audit-mirror` only

### "Workflow doesn't run"
- **Cause**: Missing `workflow_dispatch` or paths-ignore too broad
- **Fix**: Hardened workflow already includes `workflow_dispatch`
- Try manual trigger (Step 4)

### "Mirror is empty"
- **Cause**: Workflow hasn't run yet
- **Fix**: Trigger manually (Step 4) or push new commit to main

### "GPT-5 still can't access"
- **Cause**: Mirror might not be public or DNS propagation
- **Fix**: 
  - Check mirror repo settings: Visibility must be **Public**
  - Wait 1-2 minutes for GitHub to index
  - Try incognito browser: https://github.com/hankthevc/AGITracker-audit-mirror

---

## Current Status

**Mirror Repo**: ❌ Not created yet  
**Token**: ❌ Not generated yet  
**Secret**: ❌ Not configured yet  
**Workflow**: ✅ Committed and ready  

**Next Action**: Follow Steps 1-3 above to complete setup.

---

## Expected Timeline

- **Step 1**: 2 minutes (create mirror repo)
- **Step 2**: 3 minutes (generate token)
- **Step 3**: 1 minute (add secret)
- **Step 4**: 1 minute (trigger workflow)
- **Step 5**: 2 minutes (verify)

**Total**: ~10 minutes

---

## Benefits After Setup

1. ✅ **No more ZIP uploads** - GPT-5 reads code directly
2. ✅ **Auto-updated** - Every push to main updates mirror
3. ✅ **Real-time verification** - GPT-5 sees latest code
4. ✅ **Transparent** - Public snapshot builds trust
5. ✅ **Secure** - No secrets exposed (sanitized snapshot)

---

**Once setup is complete, GPT-5 Pro can audit your code in real-time at:**  
**https://github.com/hankthevc/AGITracker-audit-mirror**

