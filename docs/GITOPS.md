# GitOps Implementation with ArgoCD + Terraform

## Architecture Overview

This project implements **full GitOps practices** using:
- **Terraform** for infrastructure management (IaC)
- **ArgoCD** for application delivery (GitOps)
- **GitHub Actions** for CI/CD pipeline

## How It Works

### 1. Infrastructure Layer (Terraform)
```
Terraform manages:
├── LKE Clusters (dev, staging, production)
├── ArgoCD Installation (Helm chart)
├── ArgoCD Applications (CRDs)
├── Namespaces & RBAC
└── Monitoring Stack
```

### 2. Application Layer (ArgoCD)
```
ArgoCD watches Git repo and syncs:
├── Helm Charts (helm/vmshift/)
├── Image Tags (updated by GitHub Actions)
├── Configuration (values-*.yaml)
└── Kubernetes Resources
```

### 3. CI/CD Pipeline (GitHub Actions)
```
GitHub Actions workflow:
1. Test & Build → Docker images
2. Push → GitHub Container Registry  
3. Update → Git manifest (image tags)
4. ArgoCD → Automatically syncs changes
```

## Deployment Flow

### GitOps Flow (Recommended)
```
Code Push → GitHub Actions → Build Images → Update Git Manifests
                                                      ↓
                                                  ArgoCD watches
                                                      ↓
                                              Sync to Kubernetes
```

**Benefits:**
- ✅ Git as single source of truth
- ✅ Declarative infrastructure
- ✅ Automatic rollback on failures
- ✅ Audit trail in Git history
- ✅ Easy rollback (git revert)
- ✅ No kubectl/helm access needed for deployments

### Traditional CI/CD Flow (Old approach)
```
Code Push → GitHub Actions → Build Images → kubectl/helm deploy
```

**Drawbacks:**
- ❌ No declarative state
- ❌ Cluster credentials in CI/CD
- ❌ Harder to track changes
- ❌ Manual rollback process

## Setup Instructions

### Prerequisites
1. GitHub Personal Access Token (PAT) with `repo` scope
2. Linode API Token
3. Repository secrets configured

### Step 1: Configure GitHub Secrets

Add these secrets to your repository (`Settings → Secrets and variables → Actions`):

```bash
# Linode
LINODE_TOKEN=<your-linode-token>

# GitHub PAT (for pushing manifest updates)
PAT_TOKEN=<your-github-pat>  # Must have 'repo' scope

# Database passwords per environment
DB_PASSWORD_DEV=<dev-db-password>
DB_PASSWORD_STAGING=<staging-db-password>
DB_PASSWORD_PRODUCTION=<production-db-password>
```

**⚠️ Important:** `PAT_TOKEN` is required for GitOps workflow to push manifest updates back to Git.

### Step 2: Deploy Infrastructure with Terraform

```bash
# Navigate to terraform directory
cd terraform

# Initialize Terraform
terraform init

# Deploy production infrastructure
terraform workspace select production || terraform workspace new production
terraform apply -var-file="terraform.tfvars.prod"

# Deploy staging infrastructure  
terraform workspace select staging || terraform workspace new staging
terraform apply -var-file="terraform.tfvars.staging"

# Deploy dev infrastructure
terraform workspace select dev || terraform workspace new dev  
terraform apply -var-file="terraform.tfvars.dev"
```

This will:
- Create LKE clusters
- Install ArgoCD via Helm
- Configure ArgoCD Applications
- Set up namespaces and RBAC

### Step 3: Access ArgoCD UI

```bash
# Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo

# Get ArgoCD server URL
kubectl -n argocd get svc argocd-server \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

# Login
# Username: admin
# Password: <from above command>
```

Or port-forward for local access:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Access: https://localhost:8080
```

### Step 4: Trigger Deployment

Push code to trigger the GitOps flow:

```bash
# Deploy to production
git push origin main

# Deploy to staging
git push origin develop
```

**What happens:**
1. GitHub Actions builds images
2. Pushes to ghcr.io
3. Updates image tags in `helm/vmshift/values-*.yaml`
4. Commits and pushes to Git
5. ArgoCD detects change
6. ArgoCD syncs to cluster

### Step 5: Monitor Deployment

```bash
# Watch ArgoCD applications
kubectl get applications -n argocd

# Check application status
kubectl get application vmshift-production -n argocd -o yaml

# View application pods
kubectl get pods -n vmshift-production
```

Or use ArgoCD UI for visual monitoring.

## ArgoCD Application Configuration

### Production
- **Source:** `main` branch
- **Path:** `helm/vmshift`
- **Values:** `values-prod.yaml`
- **Sync:** Auto-sync enabled, prune disabled (manual)
- **Namespace:** `vmshift-production`

### Staging
- **Source:** `develop` branch
- **Path:** `helm/vmshift`
- **Values:** `values-staging.yaml`
- **Sync:** Auto-sync and auto-prune enabled
- **Namespace:** `vmshift-staging`

### Development
- **Source:** `develop` branch
- **Path:** `helm/vmshift`
- **Values:** `values-dev.yaml`
- **Sync:** Auto-sync and auto-prune enabled
- **Namespace:** `vmshift-dev`

## Workflows

### 1. CI/CD Pipeline (`.github/workflows/ci-cd.yaml`)
- **Trigger:** Push to `main` or `develop`
- **Actions:**
  - Run tests
  - Build Docker images
  - Push to ghcr.io
  - ~~Deploy with Helm~~ (Disabled for GitOps)
  - Trigger GitOps manifest update

### 2. GitOps Manifest Update (`.github/workflows/argocd-update.yaml`)
- **Trigger:** After successful CI/CD build
- **Actions:**
  - Update image tags in Helm values
  - Commit changes to Git
  - ArgoCD auto-syncs

### 3. Terraform (`.github/workflows/terraform.yaml`)
- **Trigger:** Manual or PR to `terraform/` folder
- **Actions:**
  - Plan infrastructure changes
  - Apply on approval

## Managing Applications

### Manual Sync
```bash
# Sync specific application
argocd app sync vmshift-production

# Or via kubectl
kubectl patch application vmshift-production \
  -n argocd \
  --type merge \
  -p '{"operation":{"initiatedBy":{"username":"admin"},"sync":{}}}'
```

### Rollback
```bash
# Via Git
git revert <commit-sha>
git push

# ArgoCD will automatically sync the rollback

# Or via ArgoCD CLI
argocd app rollback vmshift-production <history-id>
```

### Update Configuration
```bash
# Edit Helm values
vi helm/vmshift/values-prod.yaml

# Commit and push
git add helm/vmshift/values-prod.yaml
git commit -m "chore: update production config"
git push

# ArgoCD automatically applies changes
```

## Troubleshooting

### ArgoCD Application Out of Sync
```bash
# Check diff
argocd app diff vmshift-production

# Force sync
argocd app sync vmshift-production --force

# Refresh
argocd app get vmshift-production --refresh
```

### Image Not Updating
```bash
# Check if manifest was updated
git log --oneline | head -5

# Check ArgoCD sync status
kubectl describe application vmshift-production -n argocd

# Manual image update
# Edit: helm/vmshift/values-prod.yaml
# Change: image.tag: "new-tag"
# Commit and push
```

### ArgoCD Not Syncing Automatically
```bash
# Check sync policy
kubectl get application vmshift-production -n argocd -o yaml | grep -A 10 syncPolicy

# Enable auto-sync if disabled
argocd app set vmshift-production --sync-policy automated
```

## Best Practices

### 1. Use Specific Image Tags in Production
```yaml
# ❌ Bad (in values-prod.yaml)
image:
  tag: latest

# ✅ Good (let GitOps workflow update this)
image:
  tag: "a1b2c3d"  # Specific commit SHA
```

### 2. Enable Pruning Carefully
- **Dev/Staging:** Auto-prune enabled (safe to delete resources)
- **Production:** Manual prune (safer for critical workloads)

### 3. Use Sync Waves for Dependencies
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"  # Database first
    argocd.argoproj.io/sync-wave: "1"  # Application second
```

### 4. Monitor Application Health
```bash
# Set up alerts for unhealthy apps
kubectl get applications -n argocd -w
```

### 5. Backup ArgoCD Configuration
```bash
# Export applications
kubectl get applications -n argocd -o yaml > argocd-apps-backup.yaml

# Export secrets
kubectl get secrets -n argocd -o yaml > argocd-secrets-backup.yaml
```

## Migration from Helm to GitOps

If migrating from direct Helm deployments:

1. **Disable direct Helm deploys** in CI/CD workflow
2. **Enable GitOps workflow** to update manifests
3. **Import existing Helm releases** into ArgoCD:
   ```bash
   argocd app create vmshift-production \
     --repo https://github.com/ilearn-code/vmshift.git \
     --path helm/vmshift \
     --dest-server https://kubernetes.default.svc \
     --dest-namespace vmshift-production \
     --helm-set-file values=values-prod.yaml \
     --sync-policy automated
   ```
4. **Verify ArgoCD takes ownership** of resources
5. **Remove kubectl/helm from CI/CD**

## Resources

- [ArgoCD Documentation](https://argo-cd.readthedocs.io/)
- [GitOps Principles](https://opengitops.dev/)
- [Terraform Helm Provider](https://registry.terraform.io/providers/hashicorp/helm/latest/docs)
- [GitHub Actions Workflows](https://docs.github.com/en/actions)

## Summary

**GitOps Architecture:**
```
Git (Source of Truth)
  ↓
ArgoCD (Sync Engine)
  ↓
Kubernetes (Deployment Target)
```

**Benefits:**
- Declarative infrastructure
- Git-based audit trail
- Automatic sync and rollback
- Reduced manual interventions
- Enhanced security (no cluster credentials in CI/CD)

---

**Questions?** Check [ArgoCD Troubleshooting](https://argo-cd.readthedocs.io/en/stable/operator-manual/troubleshooting/) or open an issue.
