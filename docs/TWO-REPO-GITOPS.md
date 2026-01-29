# Two-Repo GitOps Architecture

## Repository Structure

### 1. Infrastructure Repo (`iac-vmshift`)
**Purpose**: Manages Kubernetes clusters and ArgoCD installation

```
iac-vmshift/
├── .github/workflows/
│   └── terraform.yaml          # Manages infrastructure
├── main.tf                      # LKE cluster definitions
├── argocd.tf                   # ArgoCD installation & applications
├── kubernetes.tf               # Namespaces, cert-manager, ingress
├── terraform.tfvars.prod
├── terraform.tfvars.staging
└── terraform.tfvars.dev
```

**Workflows**:
- Push to `main` → Terraform applies to production cluster
- Push to `develop` → Terraform applies to staging cluster
- Creates & manages ArgoCD Applications that watch the **vmshift** repo

### 2. Application Repo (`vmshift`)
**Purpose**: Application code, Helm charts, and manifests

```
vmshift/
├── .github/workflows/
│   ├── ci-cd.yaml              # Builds Docker images
│   ├── argocd-update.yaml      # Updates Helm values (GitOps)
│   └── security.yaml           # Security scanning
├── app/                        # FastAPI application
├── helm/vmshift/
│   ├── Chart.yaml
│   ├── values-prod.yaml        # Production config
│   ├── values-staging.yaml     # Staging config
│   ├── values-dev.yaml         # Dev config
│   └── templates/              # Kubernetes manifests
└── Dockerfile
```

**Workflows**:
- Push to `main` → Build images → Update `values-prod.yaml` → ArgoCD deploys
- Push to `develop` → Build images → Update `values-staging.yaml` → ArgoCD deploys

## GitOps Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ INFRASTRUCTURE (iac-vmshift repo)                               │
└─────────────────────────────────────────────────────────────────┘
                         ↓
         Push to iac-vmshift (main/develop)
                         ↓
              Terraform Workflow Runs
                         ↓
         ┌───────────────────────────────┐
         │ Terraform Applies:            │
         │ - Creates LKE clusters        │
         │ - Installs ArgoCD             │
         │ - Creates ArgoCD Apps         │
         │   (points to vmshift repo)    │
         └───────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│ APPLICATION (vmshift repo)                                      │
└─────────────────────────────────────────────────────────────────┘
                         ↓
         Push to vmshift (main/develop)
                         ↓
              CI/CD Workflow Runs
                         ↓
         ┌───────────────────────────────┐
         │ 1. Build Docker images        │
         │ 2. Push to ghcr.io            │
         └───────────────────────────────┘
                         ↓
           GitOps Workflow Runs
                         ↓
         ┌───────────────────────────────┐
         │ 1. Get new image tag (SHA)    │
         │ 2. Update values-*.yaml       │
         │ 3. git commit & push          │
         └───────────────────────────────┘
                         ↓
         ArgoCD Watches vmshift Repo
                         ↓
         ┌───────────────────────────────┐
         │ ArgoCD Detects Change         │
         │ - Compares Git vs Cluster     │
         │ - Auto-syncs if different     │
         └───────────────────────────────┘
                         ↓
            Deployed to Kubernetes!
```

## How ArgoCD Connects the Repos

**In `iac-vmshift/argocd.tf`:**
```hcl
resource "kubernetes_manifest" "vmshift_application" {
  manifest = {
    spec = {
      source = {
        repoURL        = "https://github.com/ilearn-code/vmshift.git"  # ← Application repo
        targetRevision = "main"  # or "develop"
        path           = "helm/vmshift"
      }
    }
  }
}
```

ArgoCD (installed by Terraform from `iac-vmshift`) watches the `vmshift` repo for changes!

## Typical Development Workflow

### Infrastructure Changes
```bash
# Clone infrastructure repo
git clone https://github.com/ilearn-code/iac-vmshift.git
cd iac-vmshift

# Make changes
vim main.tf

# Push (Terraform auto-applies)
git add .
git commit -m "infra: increase node count"
git push origin main
```

### Application Changes
```bash
# Clone application repo
git clone https://github.com/ilearn-code/vmshift.git
cd vmshift

# Make changes
vim app/main.py

# Push (builds & deploys automatically)
git add .
git commit -m "feat: add new endpoint"
git push origin main

# Pipeline:
# 1. CI/CD builds image
# 2. GitOps updates values-prod.yaml
# 3. ArgoCD syncs to cluster
```

## Benefits of Two-Repo Structure

### ✅ Separation of Concerns
- Infrastructure team → `iac-vmshift`
- Application team → `vmshift`
- No accidental infrastructure changes

### ✅ Different Access Controls
- Platform engineers: Full access to `iac-vmshift`
- Developers: Full access to `vmshift`, read-only to infra

### ✅ Independent Lifecycles
- Infrastructure: Changes infrequently (clusters, networking)
- Application: Changes frequently (code, features)

### ✅ Clear Boundaries
- Terraform state in infrastructure repo
- Application code separate
- Easier auditing and compliance

## Current Setup

### iac-vmshift Repo
- Terraform workflows ✅
- 3 workspaces (dev, staging, production) ✅
- ArgoCD installation ✅
- All clusters imported into state ✅

### vmshift Repo
- CI/CD workflow ✅
- GitOps workflow ✅
- Helm charts ✅
- Application code ✅

## Testing the Setup

### 1. Test Infrastructure Changes
```bash
cd /path/to/iac-vmshift

# Make a change
echo "# Test" >> terraform.tfvars.prod

# Push
git add .
git commit -m "test: trigger infrastructure workflow"
git push origin main

# Check workflow
gh run list --repo ilearn-code/iac-vmshift
```

### 2. Test Application Deployment
```bash
cd /path/to/vmshift

# Make a change
echo "# Test $(date)" >> helm/vmshift/values-prod.yaml

# Push
git add .
git commit -m "test: trigger GitOps pipeline"
git push origin main

# Check workflows
gh run list --repo ilearn-code/vmshift
```

### 3. Verify ArgoCD
```bash
# Get ArgoCD URL
kubectl -n argocd get svc argocd-server

# Check applications
kubectl get applications -n argocd

# Should see:
# - vmshift-production (watches vmshift repo, main branch)
# - vmshift-staging (watches vmshift repo, develop branch)
```

## Secrets Required

### In `iac-vmshift` Repo
```bash
# Required for Terraform
LINODE_TOKEN=<linode-api-token>
```

### In `vmshift` Repo
```bash
# Required for GitOps workflow
PAT_TOKEN=<github-pat-with-repo-scope>

# Required for CI/CD (auto-provided)
GITHUB_TOKEN=<auto-provided-by-github>
```

## Monitoring

### Infrastructure
```bash
# Check Terraform runs
gh run list --repo ilearn-code/iac-vmshift --workflow="Terraform IaC"

# Check cluster status
kubectl get nodes
kubectl get pods --all-namespaces
```

### Application
```bash
# Check CI/CD runs
gh run list --repo ilearn-code/vmshift --workflow="CI/CD Pipeline"

# Check ArgoCD sync
kubectl get application vmshift-production -n argocd

# Check app pods
kubectl get pods -n vmshift-production
```

## Summary

**Two repos, one workflow:**

1. **`iac-vmshift`** manages infrastructure (Terraform)
   - Creates clusters
   - Installs ArgoCD
   - Configures what ArgoCD watches

2. **`vmshift`** manages application (Helm + GitOps)
   - Application code
   - Helm charts
   - ArgoCD watches this repo

3. **ArgoCD** connects them
   - Installed by iac-vmshift
   - Watches vmshift for changes
   - Auto-deploys to clusters

This is the **industry-standard** way to structure GitOps with Terraform! 🚀
