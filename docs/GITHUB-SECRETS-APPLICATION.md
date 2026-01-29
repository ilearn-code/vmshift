# 🔐 Application Repo (vmshift) - GitHub Secrets Guide

**Repository**: https://github.com/ilearn-code/vmshift  
**Purpose**: Secrets needed for CI/CD, building, and deploying the application

---

## 📝 Required Secrets (6 Total)

### 1. Kubeconfig Files (3 secrets)
These give GitHub Actions access to deploy to each Kubernetes cluster.

#### `KUBECONFIG_PRODUCTION`
```bash
# Get the value:
cat kubeconfig-production.yaml | base64 -w 0
```
- **Name**: `KUBECONFIG_PRODUCTION`
- **Value**: Base64-encoded kubeconfig file for production cluster
- **Used by**: CI/CD workflow to deploy to production

#### `KUBECONFIG_STAGING`
```bash
# Get the value:
cat kubeconfig-staging.yaml | base64 -w 0
```
- **Name**: `KUBECONFIG_STAGING`
- **Value**: Base64-encoded kubeconfig file for staging cluster
- **Used by**: CI/CD workflow to deploy to staging

#### `KUBECONFIG_DEV`
```bash
# Get the value:
cat kubeconfig-dev.yaml | base64 -w 0
```
- **Name**: `KUBECONFIG_DEV`
- **Value**: Base64-encoded kubeconfig file for dev cluster
- **Used by**: CI/CD workflow to deploy to dev

---

### 2. Database Passwords (3 secrets)
Application database passwords for each environment.

#### `DB_PASSWORD_PRODUCTION`
- **Name**: `DB_PASSWORD_PRODUCTION`
- **Value**: PostgreSQL password for production database
- **Used by**: CI/CD to create Kubernetes secrets

#### `DB_PASSWORD_STAGING`
- **Name**: `DB_PASSWORD_STAGING`
- **Value**: PostgreSQL password for staging database
- **Used by**: CI/CD to create Kubernetes secrets

#### `DB_PASSWORD_DEV`
- **Name**: `DB_PASSWORD_DEV`
- **Value**: PostgreSQL password for dev database
- **Used by**: CI/CD to create Kubernetes secrets

---

## ✅ Automatic Secrets (No Action Needed)

These are automatically provided by GitHub:

### `GITHUB_TOKEN`
- **Provided by**: GitHub Actions (automatic)
- **Purpose**: Push Docker images to ghcr.io
- **Scope**: Read packages, write packages
- **No configuration needed** ✅

---

## 🚀 How to Add Secrets

### Step 1: Go to Application Repo Settings
```
https://github.com/ilearn-code/vmshift/settings/secrets/actions
```

### Step 2: Extract Kubeconfig Values

Run this script from the `terraform/` directory:

```bash
cd terraform

echo "=== KUBECONFIG_PRODUCTION ==="
cat kubeconfig-production.yaml | base64 -w 0
echo ""

echo "=== KUBECONFIG_STAGING ==="
cat kubeconfig-staging.yaml | base64 -w 0
echo ""

echo "=== KUBECONFIG_DEV ==="
cat kubeconfig-dev.yaml | base64 -w 0
echo ""
```

On Windows (PowerShell):
```powershell
cd terraform

Write-Host "=== KUBECONFIG_PRODUCTION ==="
[Convert]::ToBase64String([IO.File]::ReadAllBytes("kubeconfig-production.yaml"))

Write-Host "`n=== KUBECONFIG_STAGING ==="
[Convert]::ToBase64String([IO.File]::ReadAllBytes("kubeconfig-staging.yaml"))

Write-Host "`n=== KUBECONFIG_DEV ==="
[Convert]::ToBase64String([IO.File]::ReadAllBytes("kubeconfig-dev.yaml"))
```

### Step 3: Add Each Secret

Click "**New repository secret**" for each:

| Secret Name | Source | Notes |
|-------------|--------|-------|
| `KUBECONFIG_PRODUCTION` | Base64 from kubeconfig-production.yaml | Full cluster access |
| `KUBECONFIG_STAGING` | Base64 from kubeconfig-staging.yaml | Full cluster access |
| `KUBECONFIG_DEV` | Base64 from kubeconfig-dev.yaml | Full cluster access |
| `DB_PASSWORD_PRODUCTION` | Your production DB password | Strong password (20+ chars) |
| `DB_PASSWORD_STAGING` | Your staging DB password | Can be simpler |
| `DB_PASSWORD_DEV` | Your dev DB password | Can be simpler |

---

## 🔄 What Each Secret Does

### During CI/CD Workflow:

```yaml
1. Push to main branch
   ↓
2. Build Docker images (uses GITHUB_TOKEN automatically)
   ↓
3. Push to ghcr.io (uses GITHUB_TOKEN)
   ↓
4. Deploy to cluster:
   - Decode KUBECONFIG_* → Write to ~/.kube/config
   - Connect to Kubernetes cluster
   - Create image pull secret (uses GITHUB_TOKEN)
   - Create app secrets (uses DB_PASSWORD_*)
   - Deploy Helm chart
```

---

## 🔒 Security Best Practices

### ✅ Do:
- Use strong, unique passwords for each environment
- Rotate kubeconfig files periodically (every 90 days)
- Use different DB passwords per environment
- Review secrets access regularly

### ❌ Don't:
- Never commit kubeconfig files to Git
- Don't share production passwords with staging/dev
- Don't use simple passwords like "password123"
- Don't hardcode secrets in Helm values files

---

## 🧪 Test the Setup

After adding all secrets:

1. **Make a small code change**:
   ```bash
   echo "# Test" >> readme.md
   git add readme.md
   git commit -m "test: trigger CI/CD"
   ```

2. **Push to develop** (tests staging):
   ```bash
   git push origin develop
   ```

3. **Check GitHub Actions**:
   - Go to: https://github.com/ilearn-code/vmshift/actions
   - Watch the "CI/CD Pipeline" workflow run
   - Should build, push, and deploy automatically

4. **Verify deployment**:
   ```bash
   kubectl --kubeconfig=kubeconfig-staging.yaml get pods -n vmshift-staging
   # Should show pods running with new image
   ```

---

## 🆘 Troubleshooting

### Error: "kubeconfig decode failed"
→ Make sure you base64-encoded the ENTIRE kubeconfig file

### Error: "unable to connect to cluster"
→ Kubeconfig might be expired, regenerate from Linode

### Error: "permission denied"
→ GITHUB_TOKEN doesn't have packages permission (should be automatic)

### Error: "database connection failed"
→ Check DB_PASSWORD_* matches actual database password

---

## 📊 Summary Table

| Secret | Required? | Auto-Generated? | Used For |
|--------|-----------|-----------------|----------|
| `GITHUB_TOKEN` | ✅ | ✅ Yes | Push Docker images |
| `KUBECONFIG_PRODUCTION` | ✅ | ❌ Manual | Deploy to production |
| `KUBECONFIG_STAGING` | ✅ | ❌ Manual | Deploy to staging |
| `KUBECONFIG_DEV` | ✅ | ❌ Manual | Deploy to dev |
| `DB_PASSWORD_PRODUCTION` | ✅ | ❌ Manual | App database access |
| `DB_PASSWORD_STAGING` | ✅ | ❌ Manual | App database access |
| `DB_PASSWORD_DEV` | ✅ | ❌ Manual | App database access |

---

## 🔗 Related Documentation

- **Infrastructure Secrets**: See `terraform/GITHUB-SECRETS-SETUP.md`
- **Workflow Files**: `.github/workflows/ci-cd.yaml`
- **Helm Values**: `helm/vmshift/values-*.yaml`

---

✅ **After setup**: Push to any branch and watch automatic deployment!  
🚀 **Full GitOps**: Code → Build → Push → Deploy automatically!
