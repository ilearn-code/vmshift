# Complete GitOps Setup Guide

## What You Need to Do

### Step 1: Create GitHub Personal Access Token (PAT)

The GitOps workflow needs permission to push manifest updates back to your repository.

1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Give it a name: `VMShift GitOps Token`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### Step 2: Add GitHub Secret

1. Go to your repository: `https://github.com/ilearn-code/vmshift`
2. Navigate to: `Settings → Secrets and variables → Actions`
3. Click "New repository secret"
4. Name: `PAT_TOKEN`
5. Value: Paste the token from Step 1
6. Click "Add secret"

### Step 3: Deploy Infrastructure with Terraform

```bash
cd terraform

# Production
terraform workspace select production || terraform workspace new production
terraform apply -var-file="terraform.tfvars.prod"

# Staging  
terraform workspace select staging || terraform workspace new staging
terraform apply -var-file="terraform.tfvars.staging"

# Dev
terraform workspace select dev || terraform workspace new dev
terraform apply -var-file="terraform.tfvars.dev"
```

**This will:**
- ✅ Create LKE clusters
- ✅ Install ArgoCD via Helm
- ✅ Create ArgoCD Application CRDs
- ✅ Configure namespaces
- ✅ Set up monitoring

### Step 4: Get ArgoCD Credentials

```bash
# Production cluster
export KUBECONFIG=./kubeconfig-production.yaml

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d && echo

# Get server IP
kubectl -n argocd get svc argocd-server \
  -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

**Login:**
- URL: `http://<ArgoCD-IP>`
- Username: `admin`
- Password: `<from above command>`

### Step 5: Verify ArgoCD Applications

```bash
# Check applications
kubectl get applications -n argocd

# Should see:
# NAME                STATUS   HEALTH   SYNC
# vmshift-production  Synced   Healthy  Auto
```

### Step 6: Test GitOps Flow

```bash
# Make a change to production
vi helm/vmshift/values-prod.yaml
# Change something like replica count

# Commit and push
git add helm/vmshift/values-prod.yaml
git commit -m "test: update production config"
git push origin main

# Watch ArgoCD sync
kubectl get application vmshift-production -n argocd -w
```

**Within 3 minutes:**
- ArgoCD detects Git change
- Syncs to cluster automatically
- Pods restart with new config

### Step 7: Trigger CI/CD Pipeline

```bash
# Push code to trigger full GitOps flow
git push origin main      # Production
git push origin develop   # Staging
```

**GitHub Actions will:**
1. Build Docker images
2. Push to ghcr.io
3. Update image tags in Helm values
4. Commit changes to Git
5. ArgoCD auto-syncs to cluster

## Architecture: Terraform + ArgoCD

### Why This Approach is Best

| Component | Managed By | Purpose |
|-----------|-----------|---------|
| **LKE Clusters** | Terraform | Infrastructure provisioning |
| **ArgoCD Installation** | Terraform (Helm) | GitOps controller setup |
| **Namespaces & RBAC** | Terraform | Security & isolation |
| **Application Deployments** | ArgoCD | Continuous delivery |
| **Image Builds** | GitHub Actions | CI pipeline |
| **Manifest Updates** | GitHub Actions → Git | GitOps trigger |

### Benefits

**Terraform for Infrastructure:**
- ✅ Version-controlled infrastructure
- ✅ Reproducible deployments
- ✅ State management
- ✅ Easy infrastructure updates

**ArgoCD for Applications:**
- ✅ Git as single source of truth
- ✅ Automatic sync from Git
- ✅ Declarative deployments
- ✅ Easy rollback (git revert)
- ✅ No cluster credentials in CI/CD

**GitHub Actions for CI:**
- ✅ Automated builds
- ✅ Image publishing
- ✅ Manifest updates

## File Structure

```
vmshift/
├── terraform/
│   ├── main.tf                 # Main config with providers
│   ├── argocd.tf              # ArgoCD installation & apps ✨ NEW
│   ├── lke-cluster.tf         # LKE cluster resources
│   ├── kubernetes.tf          # K8s namespaces & resources
│   ├── database.tf            # Managed database (optional)
│   ├── helm-values/
│   │   └── argocd-values.yaml # ArgoCD Helm values
│   ├── terraform.tfvars.prod  # Production variables
│   ├── terraform.tfvars.staging # Staging variables
│   └── terraform.tfvars.dev   # Dev variables
│
├── .github/workflows/
│   ├── ci-cd.yaml            # Build & push images
│   ├── argocd-update.yaml    # GitOps manifest updater ✨ UPDATED
│   └── terraform.yaml        # Terraform automation
│
├── helm/vmshift/
│   ├── Chart.yaml
│   ├── values-prod.yaml      # Production config
│   ├── values-staging.yaml   # Staging config
│   ├── values-dev.yaml       # Dev config
│   └── templates/
│       ├── api-deployment.yaml
│       ├── celery-deployment.yaml
│       └── ...
│
├── k8s/argocd/
│   ├── application-prod.yaml    # ArgoCD app for production
│   ├── application-staging.yaml # ArgoCD app for staging
│   └── application-dev.yaml     # ArgoCD app for dev
│
└── docs/
    └── GITOPS.md              # Full GitOps documentation ✨ NEW
```

## What Changed

### Before (Direct Helm Deployment)
```
GitHub Actions → Build Image → kubectl/helm deploy to cluster
```

**Problems:**
- ❌ Cluster credentials in CI/CD
- ❌ No declarative state
- ❌ Hard to track changes
- ❌ Manual rollback

### After (GitOps with ArgoCD)
```
GitHub Actions → Build Image → Update Git manifest
                                      ↓
                                 ArgoCD watches
                                      ↓
                              Auto-sync to cluster
```

**Benefits:**
- ✅ Git is source of truth
- ✅ Declarative deployments
- ✅ Automatic sync
- ✅ Easy rollback (git revert)
- ✅ Audit trail in Git
- ✅ No cluster access from CI/CD

## Quick Commands

### Terraform
```bash
# Deploy infrastructure
cd terraform
terraform workspace select production
terraform apply -var-file="terraform.tfvars.prod"

# Update ArgoCD config
terraform apply -target=helm_release.argocd

# Destroy environment
terraform destroy -var-file="terraform.tfvars.dev"
```

### ArgoCD
```bash
# Get applications
kubectl get applications -n argocd

# Describe application
kubectl describe application vmshift-production -n argocd

# Force sync
kubectl patch application vmshift-production -n argocd \
  --type merge -p '{"operation":{"sync":{}}}'

# Get ArgoCD password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

### Monitoring
```bash
# Watch application status
kubectl get application vmshift-production -n argocd -w

# Check application health
argocd app get vmshift-production

# View sync history
argocd app history vmshift-production

# Check pods
kubectl get pods -n vmshift-production
```

## Troubleshooting

### ArgoCD Not Syncing
```bash
# Check sync status
kubectl describe application vmshift-production -n argocd | grep -A 20 Status

# Check if Git repo is accessible
kubectl get secret -n argocd | grep repo

# Force refresh
kubectl patch application vmshift-production -n argocd \
  --type merge -p '{"operation":{"initiatedBy":{"username":"admin"},"info":[{"name":"Reason","value":"Force refresh"}]}}'
```

### PAT Token Issues
```bash
# Test GitHub API with token
curl -H "Authorization: token YOUR_PAT_TOKEN" \
  https://api.github.com/repos/ilearn-code/vmshift

# Should return repository info, not 403/401
```

### Terraform State Issues
```bash
# List workspaces
terraform workspace list

# Select correct workspace
terraform workspace select production

# Import existing resource
terraform import linode_lke_cluster.vmshift <cluster-id>
```

## Next Steps

1. ✅ Add PAT_TOKEN secret to GitHub
2. ✅ Run Terraform apply for all environments
3. ✅ Verify ArgoCD is running
4. ✅ Access ArgoCD UI
5. ✅ Push code change to test GitOps
6. ✅ Monitor deployments in ArgoCD UI

## Resources

- [docs/GITOPS.md](./docs/GITOPS.md) - Complete GitOps documentation
- [terraform/argocd.tf](./terraform/argocd.tf) - ArgoCD Terraform module
- [.github/workflows/argocd-update.yaml](../.github/workflows/argocd-update.yaml) - GitOps workflow

---

**Questions?** Open an issue or check the [ArgoCD docs](https://argo-cd.readthedocs.io/).
