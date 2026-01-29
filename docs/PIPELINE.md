# Automated Deployment Pipeline

## Overview

The entire deployment pipeline is **fully automated** using GitOps principles. No manual steps required!

## Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CODE PUSH (Developer)                                        │
│    git push origin main/develop                                 │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. INFRASTRUCTURE (Terraform Workflow)                          │
│    Trigger: Push to main/develop (if terraform/** changed)     │
│    ✅ terraform init                                            │
│    ✅ terraform plan                                            │
│    ✅ terraform apply (auto on push)                            │
│    Result: LKE clusters + ArgoCD installed                      │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. BUILD IMAGES (CI/CD Workflow)                               │
│    Trigger: Push to main/develop                               │
│    ✅ Run tests                                                 │
│    ✅ Build Docker images                                       │
│    ✅ Push to ghcr.io                                           │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. UPDATE MANIFESTS (GitOps Workflow)                          │
│    Trigger: After successful CI/CD build                       │
│    ✅ Update image tags in helm/vmshift/values-*.yaml          │
│    ✅ git commit & push to repo                                │
└────────────────────────┬────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ 5. DEPLOY (ArgoCD - Auto)                                      │
│    Trigger: Git change detected (polls every 3 min)            │
│    ✅ Sync Helm charts from Git                                │
│    ✅ Apply to Kubernetes                                      │
│    ✅ Health check & self-heal                                 │
│    Result: Application running!                                │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. Terraform Workflow (`.github/workflows/terraform.yaml`)

**Triggers:**
- Push to `main` → Auto-applies to production
- Push to `develop` → Auto-applies to staging
- Daily at 2 AM UTC → Drift detection
- Manual dispatch → Any environment

**Actions:**
```yaml
on push:
  - terraform init
  - terraform plan
  - terraform apply  # ✨ AUTOMATED (no approval needed)
```

**What it manages:**
- LKE clusters (dev, staging, production)
- ArgoCD installation (Helm chart)
- ArgoCD Applications (CRDs)
- Namespaces, secrets, RBAC

### 2. CI/CD Workflow (`.github/workflows/ci-cd.yaml`)

**Triggers:**
- Push to `main` → Production images
- Push to `develop` → Staging images

**Actions:**
```yaml
jobs:
  test:
    - Run pytest
    
  build:
    - Build API image
    - Build Celery image
    - Push to ghcr.io
    
  # deploy job DISABLED - ArgoCD handles this
```

### 3. GitOps Workflow (`.github/workflows/argocd-update.yaml`)

**Triggers:**
- After successful CI/CD build

**Actions:**
```yaml
jobs:
  update-manifests:
    - Get new image tag (commit SHA)
    - Update helm/vmshift/values-*.yaml
    - git commit & push
    # ArgoCD automatically detects and syncs
```

## Required Secrets (One-time Setup)

Add these secrets once in GitHub repository settings:

```bash
# GitHub: Settings → Secrets and variables → Actions

PAT_TOKEN=<github-personal-access-token>  # For GitOps push
LINODE_TOKEN=<linode-api-token>           # For Terraform
DB_PASSWORD_DEV=<dev-password>
DB_PASSWORD_STAGING=<staging-password>
DB_PASSWORD_PRODUCTION=<prod-password>
```

## How to Deploy

### Initial Setup (First Time Only)

```bash
# 1. Add secrets to GitHub (see above)

# 2. Push to trigger pipeline
git push origin main

# That's it! Pipeline handles everything:
# ✅ Creates infrastructure
# ✅ Installs ArgoCD
# ✅ Builds images
# ✅ Updates manifests
# ✅ Deploys application
```

### Daily Development Flow

```bash
# 1. Make code changes
vim app/main.py

# 2. Commit and push
git add .
git commit -m "feat: add new feature"
git push origin develop  # or main for production

# Pipeline automatically:
# ✅ Builds new image
# ✅ Updates manifest
# ✅ ArgoCD deploys to cluster
# 
# Wait 5-10 minutes, check: https://vmshift-staging.satyamay.tech
```

### Infrastructure Changes

```bash
# 1. Update Terraform config
vim terraform/main.tf

# 2. Commit and push
git add terraform/
git commit -m "infra: increase node count"
git push origin main

# Pipeline automatically:
# ✅ Plans changes
# ✅ Applies to cluster
# ✅ Updates infrastructure
```

## Monitoring

### Check Workflow Status

```bash
# Via CLI
gh run list --limit 5

# Via Web
https://github.com/ilearn-code/vmshift/actions
```

### Check ArgoCD Status

```bash
# Get ArgoCD URL
kubectl -n argocd get svc argocd-server -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
# Visit: http://<IP>

# Or via CLI
kubectl get applications -n argocd
kubectl describe application vmshift-production -n argocd
```

### Check Application

```bash
# Health endpoint
curl https://vmshift.satyamay.tech/health
curl https://vmshift-staging.satyamay.tech/health

# Or check pods
kubectl get pods -n vmshift-production
kubectl get pods -n vmshift-staging
```

## Rollback

### Application Rollback (Git-based)

```bash
# Find commit to rollback to
git log --oneline | head -10

# Revert to previous version
git revert <commit-sha>
git push

# ArgoCD automatically syncs the rollback (3 minutes)
```

### Infrastructure Rollback

```bash
# Revert Terraform changes
git revert <commit-sha>
git push

# Terraform workflow automatically applies rollback
```

## Pipeline Behavior

### On `main` branch push:
- ✅ Terraform applies to **production** (if terraform/ changed)
- ✅ CI/CD builds images with `main` tag
- ✅ GitOps updates `values-prod.yaml`
- ✅ ArgoCD syncs to **vmshift-production** namespace

### On `develop` branch push:
- ✅ Terraform applies to **staging** (if terraform/ changed)
- ✅ CI/CD builds images with `develop` tag
- ✅ GitOps updates `values-staging.yaml`
- ✅ ArgoCD syncs to **vmshift-staging** namespace

### On Pull Request:
- ✅ Terraform plan (preview changes)
- ✅ CI/CD runs tests
- ❌ No deployment

## Advantages

### 1. Zero Manual Steps
- No `terraform apply` commands
- No `kubectl apply` commands
- No `helm install` commands
- Just `git push`

### 2. Full Audit Trail
- Every change tracked in Git
- Pipeline logs for debugging
- ArgoCD sync history

### 3. Safe Deployments
- Terraform plans previewed in PR
- Can rollback with `git revert`
- ArgoCD health checks before marking success

### 4. Fast Feedback
- See pipeline status in GitHub
- Get notifications on failures
- Real-time ArgoCD UI

### 5. Multi-Environment Support
- Same pipeline for all environments
- Branch-based deployment (main → prod, develop → staging)
- Environment-specific configs

## Troubleshooting

### Pipeline Failing?

```bash
# Check workflow logs
gh run view <run-id>

# Common issues:
# - Missing secrets (PAT_TOKEN, LINODE_TOKEN)
# - Terraform state lock
# - Docker build errors
```

### ArgoCD Not Syncing?

```bash
# Check application status
kubectl describe application vmshift-production -n argocd

# Manual sync if needed
kubectl patch application vmshift-production -n argocd \
  --type merge -p '{"operation":{"sync":{}}}'

# Check if Git repo is accessible
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server
```

### Application Not Working?

```bash
# Check pods
kubectl get pods -n vmshift-production

# Check logs
kubectl logs -n vmshift-production -l app=vmshift-api

# Check ArgoCD events
kubectl get events -n argocd --sort-by='.lastTimestamp'
```

## Summary

**What's Automated:**
- ✅ Infrastructure provisioning (Terraform)
- ✅ ArgoCD installation (Terraform)
- ✅ Image building (GitHub Actions)
- ✅ Manifest updates (GitHub Actions)
- ✅ Application deployment (ArgoCD)
- ✅ Health checks (ArgoCD)
- ✅ Drift detection (Daily Terraform run)

**What You Do:**
- ✅ Write code
- ✅ Commit to Git
- ✅ Push to GitHub
- ✅ (Optional) Monitor in ArgoCD UI

**That's it!** The pipeline handles everything else automatically. 🚀
