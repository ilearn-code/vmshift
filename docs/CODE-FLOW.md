# Complete Code Flow - Infrastructure as Code + GitOps

## Overview

Your setup now has **two repositories** working together:
1. **vmshift** (application code) - Triggers deployments
2. **iac-vmshift** (infrastructure) - Manages clusters and ArgoCD

## Code Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          DEVELOPER WORKFLOW                             │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  Developer       │         │  Developer       │
│  pushes to       │         │  updates         │
│  vmshift repo    │         │  iac-vmshift     │
│  (app code)      │         │  (infrastructure)│
└────────┬─────────┘         └────────┬─────────┘
         │                            │
         ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           GITHUB ACTIONS                                │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐   ┌──────────────────────────┐
│  vmshift/.github/       │   │  iac-vmshift/.github/    │
│  workflows/             │   │  workflows/              │
│                         │   │                          │
│  1. ci-cd.yaml          │   │  1. terraform.yaml       │
│     - Build images      │   │     - terraform plan     │
│     - Push to ghcr.io   │   │     - terraform apply    │
│                         │   │     - Update clusters    │
│  2. argocd-update.yaml  │   │                          │
│     - Update values.yaml│   │                          │
│     - Commit & push     │   │                          │
└────────┬────────────────┘   └────────┬─────────────────┘
         │                             │
         ▼                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    GIT REPOSITORIES (SOURCE OF TRUTH)                   │
└─────────────────────────────────────────────────────────────────────────┘

┌────────────────────────┐   ┌───────────────────────────┐
│  vmshift repo          │   │  iac-vmshift repo         │
│  - Helm charts updated │   │  - Terraform state        │
│  - values-*.yaml       │   │  - ArgoCD config          │
└────────┬───────────────┘   └────────┬──────────────────┘
         │                            │
         │                            │ Terraform applies to
         │                            ▼
         │                   ┌──────────────────┐
         │                   │  Production      │
         │                   │  Cluster         │
         │                   │                  │
         │                   │  - ArgoCD        │
         │                   │  - Secrets       │
         │                   │  - Applications  │
         │                   └────────┬─────────┘
         │                            │
         │ ArgoCD watches             │ Manages all clusters
         ▼                            ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     ARGOCD (CONTINUOUS DEPLOYMENT)                      │
└─────────────────────────────────────────────────────────────────────────┘

         ┌────────────────────────────┐
         │  ArgoCD (Production)       │
         │  Watches vmshift repo      │
         │  for changes               │
         └──────┬──────┬──────┬───────┘
                │      │      │
        ┌───────┘      │      └───────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Production   │ │ Staging      │ │ Dev          │
│ Cluster      │ │ Cluster      │ │ Cluster      │
│              │ │              │ │              │
│ vmshift-prod │ │ vmshift-     │ │ vmshift-dev  │
│ (main)       │ │ staging      │ │ (develop)    │
│              │ │ (develop)    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Detailed Flow for Application Code

### Scenario 1: Deploy to Production

```bash
# 1. Developer makes changes
git checkout main
vim src/api/handlers.py
git commit -am "feat: add new endpoint"
git push origin main
```

**What happens automatically:**

1. **GitHub Actions: CI/CD** (`.github/workflows/ci-cd.yaml`)
   ```
   ✓ Checkout code
   ✓ Build Docker images:
     - vmshift-api:main-<commit-sha>
     - vmshift-celery:main-<commit-sha>
   ✓ Push to ghcr.io/ilearn-code/
   ```

2. **GitHub Actions: ArgoCD Update** (`.github/workflows/argocd-update.yaml`)
   ```
   ✓ Detects main branch
   ✓ Updates helm/vmshift/values-production.yaml:
     image:
       tag: main-<commit-sha>
   ✓ Commits and pushes to main
   ```

3. **ArgoCD Detects Change**
   ```
   ✓ Polls vmshift repo (every 3 minutes)
   ✓ Detects values-production.yaml changed
   ✓ Syncs vmshift-production application
   ✓ Deploys to production cluster
   ```

4. **Production Updated!**
   ```
   ✓ http://vmshift.satyamay.tech shows new code
   ✓ Deployment takes ~2-5 minutes total
   ```

### Scenario 2: Deploy to Staging & Dev

```bash
# 1. Developer makes changes
git checkout develop
vim src/api/handlers.py
git commit -am "feat: test new feature"
git push origin develop
```

**What happens automatically:**

1. **GitHub Actions: CI/CD** (`.github/workflows/ci-cd.yaml`)
   ```
   ✓ Build Docker images:
     - vmshift-api:develop-<commit-sha>
     - vmshift-celery:develop-<commit-sha>
   ✓ Push to ghcr.io
   ```

2. **GitHub Actions: ArgoCD Update** (`.github/workflows/argocd-update.yaml`)
   ```
   ✓ Detects develop branch
   ✓ Updates TWO files:
     - helm/vmshift/values-staging.yaml
     - helm/vmshift/values-dev.yaml
   ✓ Commits and pushes to develop
   ```

3. **ArgoCD Syncs BOTH Applications**
   ```
   ✓ vmshift-staging: Syncs to staging cluster
   ✓ vmshift-dev: Syncs to dev cluster
   ✓ Both environments updated simultaneously
   ```

4. **Staging & Dev Updated!**
   ```
   ✓ http://172.234.3.86 (staging)
   ✓ http://172.234.3.87 (dev)
   ✓ Both show new code
   ```

## Detailed Flow for Infrastructure Changes

### Scenario 3: Update Infrastructure

```bash
# 1. Developer updates Terraform
cd iac-vmshift
git checkout main
vim terraform/argocd.tf  # Change ArgoCD config
git commit -am "feat: update ArgoCD sync interval"
git push origin main
```

**What happens automatically:**

1. **GitHub Actions: Terraform** (`.github/workflows/terraform.yaml`)
   ```
   ✓ Checkout code
   ✓ terraform init
   ✓ terraform plan (review changes)
   ✓ terraform apply (auto-approve on main)
   ✓ Updates production cluster resources
   ```

2. **Terraform Updates Resources**
   ```
   ✓ Modifies ArgoCD Helm release
   ✓ Updates cluster secrets if changed
   ✓ Updates ArgoCD application manifests
   ✓ All changes tracked in Terraform state
   ```

3. **Infrastructure Updated!**
   ```
   ✓ Changes applied to production cluster
   ✓ ArgoCD continues managing deployments
   ```

## Branch Strategy

```
main branch (vmshift)
├── Deploys to: Production cluster
├── Image tag: main-<sha>
├── Values: values-production.yaml
└── ArgoCD app: vmshift-production

develop branch (vmshift)
├── Deploys to: Staging + Dev clusters
├── Image tag: develop-<sha>
├── Values: values-staging.yaml + values-dev.yaml
└── ArgoCD apps: vmshift-staging + vmshift-dev

main branch (iac-vmshift)
├── Manages: All three clusters
├── Terraform workspace: production
└── Creates: ArgoCD + all resources
```

## Complete Workflow Example

### Adding a New Feature

```bash
# Day 1: Development
git checkout develop
git pull origin develop

# Make changes
vim src/api/new_feature.py
git add .
git commit -m "feat: add new feature"
git push origin develop

# ✓ Auto-deployed to staging & dev
# ✓ Test at: http://172.234.3.86 (staging)
# ✓ Test at: http://172.234.3.87 (dev)

# Day 2: Testing passed, release to production
git checkout main
git merge develop
git push origin main

# ✓ Auto-deployed to production
# ✓ Live at: http://vmshift.satyamay.tech
```

### Updating Infrastructure

```bash
# Need to change cluster size or ArgoCD config
cd iac-vmshift
git checkout main

# Update Terraform
vim terraform/lke-cluster.tf
# Change node_count or resources

git add .
git commit -m "feat: scale up production nodes"
git push origin main

# ✓ Terraform auto-applies changes
# ✓ Cluster scaled without touching app code
```

## Key Principles

### Separation of Concerns

| Repo | Purpose | Triggers |
|------|---------|----------|
| **vmshift** | Application code | Developer pushes → CI/CD builds → ArgoCD deploys |
| **iac-vmshift** | Infrastructure | Developer pushes → Terraform applies → Clusters updated |

### Single Source of Truth

```
Application State:
  Git (vmshift) → Helm values → ArgoCD → Kubernetes

Infrastructure State:
  Git (iac-vmshift) → Terraform → Kubernetes resources
```

### Automation Levels

```
1. Code Push (Manual)
   └─> 2. CI/CD Build (Automatic)
       └─> 3. Update Manifests (Automatic)
           └─> 4. ArgoCD Sync (Automatic)
               └─> 5. Deployment (Automatic)
```

## Monitoring the Flow

### Check CI/CD Status
```bash
# View GitHub Actions
https://github.com/ilearn-code/vmshift/actions
https://github.com/ilearn-code/iac-vmshift/actions
```

### Check ArgoCD Status
```bash
# Via UI
http://172.234.2.39
# Login: admin / T3ECWVag1iT0mz7q

# Via CLI
kubectl get applications -n argocd
# Shows sync status of all apps
```

### Check Application Status
```bash
# Production
curl http://vmshift.satyamay.tech/health

# Staging
curl http://172.234.3.86/health

# Dev
curl http://172.234.3.87/health
```

## What Happens Behind the Scenes

### Every 3 Minutes:
```
ArgoCD polls vmshift repo
  ├─> Checks values-production.yaml (main branch)
  ├─> Checks values-staging.yaml (develop branch)
  └─> Checks values-dev.yaml (develop branch)
  
If changed:
  ├─> Compares desired state (Git) vs actual state (Kubernetes)
  ├─> Generates diff
  ├─> Applies changes
  └─> Updates application status
```

### On Every Push to vmshift:
```
GitHub Actions triggered
  ├─> ci-cd.yaml: Builds images (~2-3 minutes)
  └─> argocd-update.yaml: Updates values (~30 seconds)
      └─> ArgoCD detects change (~1-3 minutes)
          └─> Syncs to cluster (~1-2 minutes)

Total time: 4-8 minutes from push to deployment
```

### On Every Push to iac-vmshift:
```
GitHub Actions triggered
  └─> terraform.yaml: Applies infrastructure changes (~5-10 minutes)
      └─> ArgoCD continues normal operations
```

## Rollback Process

### Application Rollback
```bash
# Option 1: Revert git commit
git revert <commit-sha>
git push origin main
# ArgoCD auto-deploys previous version

# Option 2: ArgoCD UI rollback
# Go to: http://172.234.2.39
# Select application → History → Rollback to previous revision

# Option 3: kubectl rollback
kubectl rollout undo deployment/vmshift-api -n vmshift-production
```

### Infrastructure Rollback
```bash
cd iac-vmshift
git revert <commit-sha>
git push origin main
# Terraform auto-applies previous state
```

## Advantages of This Flow

✅ **Fully Automated**: Push code → Automatically deployed  
✅ **Auditable**: Every change tracked in Git  
✅ **Rollback Easy**: Revert Git commit = rollback deployment  
✅ **Multi-Environment**: One push → staging + dev updated  
✅ **Consistent**: Same process for all environments  
✅ **Safe**: Terraform plan before apply, ArgoCD sync with health checks  
✅ **Scalable**: Add new environments by editing Terraform  

## Troubleshooting

### Deployment Stuck?
```bash
# Check ArgoCD
kubectl get applications -n argocd -o wide

# Check logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

### CI/CD Failed?
```bash
# Check GitHub Actions
https://github.com/ilearn-code/vmshift/actions

# Check workflow logs
# Click on failed workflow → View logs
```

### Terraform Failed?
```bash
# Check GitHub Actions
https://github.com/ilearn-code/iac-vmshift/actions

# Manual fix
cd iac-vmshift/terraform
terraform workspace select production
terraform plan
terraform apply
```

## Summary

Your code flow is now:

1. **Developer pushes** → Triggers everything automatically
2. **GitHub Actions** → Builds images and updates manifests
3. **ArgoCD** → Deploys to appropriate clusters based on branch
4. **Terraform** → Manages infrastructure when iac-vmshift changes

**Zero manual kubectl commands needed!** Everything is GitOps! 🚀
