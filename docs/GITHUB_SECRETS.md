# GitHub Secrets Configuration

This document lists all the secrets required for the CI/CD pipelines to function properly.

## Required Secrets

### Deployment Secrets

#### Vercel (Frontend Deployment)

Configure these secrets in GitHub repository settings → Secrets and variables → Actions:

- **`VERCEL_TOKEN`**
  - **Description**: Vercel authentication token for CLI deployments
  - **How to get**: 
    1. Go to https://vercel.com/account/tokens
    2. Click "Create Token"
    3. Give it a name (e.g., "GitHub Actions - AGI Tracker")
    4. Copy the token (you won't see it again)
  - **Used in**: `.github/workflows/deploy.yml`

- **`VERCEL_ORG_ID`**
  - **Description**: Your Vercel organization/team ID
  - **How to get**:
    1. Run `vercel link` in your local `apps/web` directory
    2. The ID will be saved in `.vercel/project.json` as `orgId`
    3. Or find it in Vercel dashboard → Settings → General
  - **Used in**: `.github/workflows/deploy.yml`

- **`VERCEL_PROJECT_ID`**
  - **Description**: Your Vercel project ID
  - **How to get**:
    1. Run `vercel link` in your local `apps/web` directory
    2. The ID will be saved in `.vercel/project.json` as `projectId`
    3. Or find it in Vercel dashboard → Project Settings → General
  - **Used in**: `.github/workflows/deploy.yml`

#### Railway (Backend Deployment)

- **`RAILWAY_TOKEN`**
  - **Description**: Railway CLI authentication token
  - **How to get**:
    1. Go to https://railway.app/account/tokens
    2. Click "Create Token"
    3. Give it a name (e.g., "GitHub Actions")
    4. Copy the token
  - **Used in**: `.github/workflows/deploy.yml`

- **`RAILWAY_PROJECT_ID`**
  - **Description**: Your Railway project ID
  - **How to get**:
    1. Go to your Railway project dashboard
    2. Click Settings → General
    3. Copy the Project ID
    4. Or run `railway status --json | jq -r '.projectId'`
  - **Used in**: `.github/workflows/deploy.yml`

### Optional Secrets (for enhanced workflows)

#### Code Quality

- **`CODECOV_TOKEN`** (Optional)
  - **Description**: Token for uploading code coverage reports to Codecov
  - **How to get**: https://codecov.io/ → Add repository
  - **Used in**: `.github/workflows/ci.yml` (if coverage reporting is enabled)

#### Monitoring

- **`SENTRY_AUTH_TOKEN`** (Optional)
  - **Description**: Token for Sentry release tracking
  - **How to get**: Sentry → Settings → Auth Tokens
  - **Used in**: Deployment workflows for release tracking

## Setting GitHub Secrets

### Via GitHub Web UI

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Enter the secret name (e.g., `RAILWAY_TOKEN`)
5. Paste the secret value
6. Click **Add secret**

### Via GitHub CLI

```bash
# Install GitHub CLI if needed
brew install gh

# Authenticate
gh auth login

# Add secrets
gh secret set VERCEL_TOKEN
gh secret set VERCEL_ORG_ID
gh secret set VERCEL_PROJECT_ID
gh secret set RAILWAY_TOKEN
gh secret set RAILWAY_PROJECT_ID
```

## Verification

After adding secrets, you can verify they're set correctly:

```bash
# List all secrets (values are hidden)
gh secret list

# Test by triggering a workflow
gh workflow run deploy.yml
```

## Security Best Practices

1. **Never commit secrets to the repository**
   - Check `.gitignore` includes `.env`, `.vercel/`, and similar files
   - Use environment variables for all sensitive data

2. **Rotate secrets regularly**
   - Set a reminder to rotate tokens every 90 days
   - Immediately rotate if you suspect a token has been compromised

3. **Use least-privilege access**
   - Create service-specific tokens with minimal required permissions
   - Don't use personal access tokens for CI/CD

4. **Monitor secret usage**
   - Check GitHub Actions logs for unauthorized access attempts
   - Review audit logs in Vercel and Railway dashboards

5. **Use environment-specific secrets**
   - Use GitHub Environments for production/staging separation
   - Configure environment protection rules

## Troubleshooting

### "Authentication failed" errors

- Verify the secret value is correct (no extra spaces)
- Check token hasn't expired
- Ensure token has required permissions
- Try regenerating the token

### Deployment fails with "Project not found"

- Verify `VERCEL_PROJECT_ID` and `RAILWAY_PROJECT_ID` are correct
- Ensure the tokens have access to the specified projects
- Check organization/team membership

### Workflow doesn't have access to secrets

- Secrets are only available to workflows triggered by:
  - Push events
  - Pull requests from the same repository
  - Workflow dispatch (manual trigger)
- PRs from forks don't have access to secrets (security feature)

## Required Secrets Checklist

Before deploying, ensure all required secrets are set:

- [ ] `VERCEL_TOKEN`
- [ ] `VERCEL_ORG_ID`
- [ ] `VERCEL_PROJECT_ID`
- [ ] `RAILWAY_TOKEN`
- [ ] `RAILWAY_PROJECT_ID`

## Related Documentation

- [GitHub Actions Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vercel CLI Documentation](https://vercel.com/docs/cli)
- [Railway CLI Documentation](https://docs.railway.app/develop/cli)

