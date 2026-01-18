# 🌍 Multi-Environment Deployment Guide

This guide explains how to manage and deploy VMShift across multiple environments: **Development**, **Staging**, and **Production**.

## 📋 Environment Overview

| Environment | Branch | Namespace | Domain | Purpose |
|------------|--------|-----------|---------|---------|
| **Development** | `develop` / `feature/*` | `vmshift-dev` | vmshift-dev.satyamay.tech | Feature development and testing |
| **Staging** | `develop` | `vmshift-staging` | vmshift-staging.satyamay.tech | Pre-production testing |
| **Production** | `main` | `vmshift-production` | vmshift.satyamay.tech | Live production environment |

---

## 🏗️ Architecture Per Environment

### Development Environment
```
Minimal resources for rapid development:
├─ API Pods: 1 replica (256Mi RAM, 250m CPU)
├─ Celery Workers: 1 replica
├─ PostgreSQL: vmshift_dev (5Gi storage)
├─ Redis: 2Gi storage
├─ Autoscaling: Disabled
└─ SSL: Let's Encrypt Staging
```

### Staging Environment
```
Production-like for testing:
├─ API Pods: 2 replicas (1Gi RAM, 1 CPU)
├─ Celery Workers: 2 replicas
├─ PostgreSQL: vmshift_staging (10Gi storage)
├─ Redis: 5Gi storage
├─ Autoscaling: 2-4 API, 2-6 Workers
└─ SSL: Let's Encrypt Staging
```

### Production Environment
```
Full production resources:
├─ API Pods: 3 replicas (2Gi RAM, 2 CPU)
├─ Celery Workers: 3 replicas
├─ PostgreSQL: vmshift_prod (20Gi storage)
├─ Redis: 10Gi storage
├─ Autoscaling: 3-10 API, 3-8 Workers
├─ SSL: Let's Encrypt Production
└─ PodDisruptionBudget: Enabled
```

---

## 🚀 Deployment Workflows

### Automatic Deployment

The CI/CD pipeline automatically determines which environment to deploy based on the branch:

```bash
# Deploy to Development
git checkout develop
git push origin develop  # Auto-deploys to vmshift-dev

# Deploy to Staging
git checkout develop
git push origin develop  # Auto-deploys to vmshift-staging

# Deploy to Production
git checkout main
git merge develop
git push origin main  # Auto-deploys to vmshift-production
```

### Manual Deployment

Trigger manual deployment to any environment:

```bash
# Via GitHub CLI
gh workflow run ci-cd.yaml -f environment=dev
gh workflow run ci-cd.yaml -f environment=staging
gh workflow run ci-cd.yaml -f environment=production

# Via GitHub UI
# Go to Actions → CI/CD Pipeline → Run workflow
# Select environment from dropdown
```

### Local Helm Deployment

Deploy to specific environment using Helm:

```bash
# Development
helm upgrade --install vmshift-dev ./helm/vmshift \
  --namespace vmshift-dev \
  --values ./helm/vmshift/values-dev.yaml \
  --create-namespace

# Staging
helm upgrade --install vmshift-staging ./helm/vmshift \
  --namespace vmshift-staging \
  --values ./helm/vmshift/values-staging.yaml \
  --create-namespace

# Production
helm upgrade --install vmshift-prod ./helm/vmshift \
  --namespace vmshift-production \
  --values ./helm/vmshift/values-prod.yaml \
  --create-namespace
```

---

## 🗄️ Database Configuration

### Separate PostgreSQL Databases

Each environment has its own isolated PostgreSQL database:

```yaml
Development:
  Database: vmshift_dev
  User: vmshift_dev_user
  Storage: 5Gi

Staging:
  Database: vmshift_staging
  User: vmshift_staging_user
  Storage: 10Gi

Production:
  Database: vmshift_prod
  User: vmshift_prod_user
  Storage: 20Gi
```

### Database Secrets

Create secrets for each environment:

```bash
# Development
kubectl create secret generic vmshift-secrets \
  --from-literal=database-url="postgresql://vmshift_dev_user:password@postgresql:5432/vmshift_dev" \
  --from-literal=redis-url="redis://redis:6379/0" \
  -n vmshift-dev

# Staging
kubectl create secret generic vmshift-secrets \
  --from-literal=database-url="postgresql://vmshift_staging_user:password@postgresql:5432/vmshift_staging" \
  --from-literal=redis-url="redis://redis:6379/0" \
  -n vmshift-staging

# Production
kubectl create secret generic vmshift-secrets \
  --from-literal=database-url="postgresql://vmshift_prod_user:password@postgresql:5432/vmshift_prod" \
  --from-literal=redis-url="redis://redis:6379/0" \
  -n vmshift-production
```

### Database Migration Strategy

```bash
# 1. Test migrations in development
kubectl exec -it deployment/vmshift-api -n vmshift-dev -- \
  python -m alembic upgrade head

# 2. Verify in staging
kubectl exec -it deployment/vmshift-api -n vmshift-staging -- \
  python -m alembic upgrade head

# 3. Apply to production
kubectl exec -it deployment/vmshift-api -n vmshift-production -- \
  python -m alembic upgrade head
```

---

## 🔐 Environment Secrets

### GitHub Repository Secrets

Add these secrets to your GitHub repository (Settings → Secrets → Actions):

| Secret Name | Description | Required For |
|-------------|-------------|--------------|
| `KUBECONFIG` | Base64 encoded kubeconfig | All environments |
| `GHCR_PAT` | GitHub Container Registry token | All environments |
| `DB_PASSWORD_DEV` | Development database password | Development |
| `DB_PASSWORD_STAGING` | Staging database password | Staging |
| `DB_PASSWORD_PRODUCTION` | Production database password | Production |
| `ARGOCD_AUTH_TOKEN` | ArgoCD admin token | Optional |

### Adding Secrets

```bash
# Generate secure passwords
DEV_PASSWORD=$(openssl rand -base64 32)
STAGING_PASSWORD=$(openssl rand -base64 32)
PROD_PASSWORD=$(openssl rand -base64 32)

# Add via GitHub CLI
gh secret set DB_PASSWORD_DEV --body "$DEV_PASSWORD"
gh secret set DB_PASSWORD_STAGING --body "$STAGING_PASSWORD"
gh secret set DB_PASSWORD_PRODUCTION --body "$PROD_PASSWORD"
```

---

## 🌐 Domain Configuration

### DNS Setup

Configure DNS records for each environment:

```
# A Records (or CNAME to ingress IP)
vmshift-dev.satyamay.tech      →  143.42.224.166
vmshift-staging.satyamay.tech  →  143.42.224.166
vmshift.satyamay.tech          →  143.42.224.166
```

### SSL Certificates

Certificates are automatically provisioned by cert-manager:

- **Development**: Let's Encrypt Staging (for testing)
- **Staging**: Let's Encrypt Staging (for testing)
- **Production**: Let's Encrypt Production (trusted certificates)

---

## 📊 Monitoring Per Environment

### Access Metrics

```bash
# Development pods
kubectl get pods -n vmshift-dev

# Staging pods
kubectl get pods -n vmshift-staging

# Production pods
kubectl get pods -n vmshift-production

# All environments
kubectl get pods -A | grep vmshift
```

### Resource Usage

```bash
# Development
kubectl top pods -n vmshift-dev

# Staging
kubectl top pods -n vmshift-staging

# Production
kubectl top pods -n vmshift-production
```

### Logs

```bash
# Follow logs for specific environment
kubectl logs -f deployment/vmshift-api -n vmshift-dev
kubectl logs -f deployment/vmshift-api -n vmshift-staging
kubectl logs -f deployment/vmshift-api -n vmshift-production
```

---

## 🔄 Promotion Workflow

### Feature Development → Staging → Production

```bash
# 1. Develop feature in feature branch
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# Auto-deploys to vmshift-dev

# 2. Create PR to develop
gh pr create --base develop --title "New Feature"
# Review, approve, merge

# Auto-deploys to vmshift-staging

# 3. Test in staging, then promote to production
git checkout main
git merge develop
git tag v1.2.3
git push origin main --tags

# Auto-deploys to vmshift-production
```

### Rollback Strategy

```bash
# Development - rollback is easy
helm rollback vmshift-dev -n vmshift-dev

# Staging - test rollback before production
helm rollback vmshift-staging -n vmshift-staging

# Production - careful rollback
helm rollback vmshift-prod -n vmshift-production
helm history vmshift-prod -n vmshift-production
```

---

## 🎯 Environment-Specific Features

### Development
- ✅ Debug mode enabled
- ✅ Verbose logging (DEBUG level)
- ✅ Fast deployment (no wait times)
- ✅ Staging SSL certificates
- ✅ Minimal resources

### Staging
- ✅ Production-like setup
- ✅ Autoscaling enabled
- ✅ Integration testing
- ✅ Performance testing
- ✅ INFO level logging

### Production
- ✅ High availability (3+ replicas)
- ✅ Autoscaling (up to 10 pods)
- ✅ PodDisruptionBudget
- ✅ Production SSL
- ✅ WARNING level logging
- ✅ Rate limiting enabled

---

## 🧪 Testing Across Environments

### Development Testing
```bash
# Test API in dev
curl https://vmshift-dev.satyamay.tech/health

# Create test VM
curl -X POST https://vmshift-dev.satyamay.tech/api/v1/vms/ \
  -H "Content-Type: application/json" \
  -d '{"name": "test-vm-dev", "uuid": "vm-dev-001"}'
```

### Staging Testing
```bash
# Run integration tests against staging
pytest tests/integration --env=staging

# Load testing
locust -f tests/load_test.py --host=https://vmshift-staging.satyamay.tech
```

### Production Smoke Tests
```bash
# Health check
curl https://vmshift.satyamay.tech/health

# Read-only tests only in production
curl https://vmshift.satyamay.tech/api/v1/vms/
```

---

## 🔧 Troubleshooting

### Check Environment Status

```bash
# See all environments
kubectl get namespaces | grep vmshift

# Check specific environment
kubectl get all -n vmshift-dev
kubectl get all -n vmshift-staging
kubectl get all -n vmshift-production
```

### Common Issues

#### Pods Not Starting
```bash
# Check events
kubectl get events -n vmshift-dev --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n vmshift-dev
```

#### Database Connection Issues
```bash
# Test database connectivity
kubectl exec -it deployment/vmshift-api -n vmshift-dev -- \
  psql postgresql://vmshift_dev_user:password@postgresql:5432/vmshift_dev -c "SELECT 1;"
```

#### SSL Certificate Issues
```bash
# Check certificates
kubectl get certificate -n vmshift-dev
kubectl describe certificate vmshift-dev-tls -n vmshift-dev
```

---

## 💰 Cost Management

### Resource Usage by Environment

| Environment | Pods | Storage | Estimated Cost/Month |
|------------|------|---------|---------------------|
| Development | 4 | 7Gi | ~$5 |
| Staging | 7 | 15Gi | ~$15 |
| Production | 10 | 30Gi | ~$38 |
| **Total** | **21** | **52Gi** | **~$58** |

### Cost Optimization Tips

1. **Scale down dev at night**:
   ```bash
   kubectl scale deployment/vmshift-api --replicas=0 -n vmshift-dev
   ```

2. **Use spot instances** for dev/staging nodes

3. **Share Redis** across dev/staging (optional)

4. **Clean up old resources**:
   ```bash
   # Delete old deployments
   kubectl delete deployment <old-deployment> -n vmshift-dev
   ```

---

## 📚 Quick Reference

### Environment URLs
```
Development:  https://vmshift-dev.satyamay.tech
Staging:      https://vmshift-staging.satyamay.tech
Production:   https://vmshift.satyamay.tech
```

### Namespaces
```
Development:  vmshift-dev
Staging:      vmshift-staging
Production:   vmshift-production
```

### ArgoCD Applications
```
kubectl get applications -n argocd
```

### Helm Releases
```
helm list -A | grep vmshift
```

---

**Last Updated**: January 18, 2026  
**Environments**: Dev, Staging, Production  
**Status**: ✅ Ready for multi-environment deployment
