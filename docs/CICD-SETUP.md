# CI/CD Setup Documentation

## ✅ Application CI/CD Pipeline Configured

### **Overview**
Multi-environment CI/CD pipeline automatically deploys VMShift application to dev, staging, and production environments based on git branches.

### **Deployment Triggers**

| Branch | Environment | Automatic Deployment |
|--------|-------------|---------------------|
| `feature/*` | Dev | ✅ Yes |
| `develop` | Staging | ✅ Yes |
| `main` | Production | ✅ Yes |

### **Manual Deployment**
You can also trigger deployments manually:
```bash
gh workflow run "CI/CD Pipeline" -f environment=dev
gh workflow run "CI/CD Pipeline" -f environment=staging
gh workflow run "CI/CD Pipeline" -f environment=production
```

## 🔐 GitHub Secrets Configured

All required secrets have been set up in GitHub Actions:

### **Infrastructure Secrets:**
- `LINODE_TOKEN` - Akamai/Linode API token for infrastructure management
- `KUBECONFIG_DEV` - Kubernetes configuration for dev cluster
- `KUBECONFIG_STAGING` - Kubernetes configuration for staging cluster
- `KUBECONFIG_PRODUCTION` - Kubernetes configuration for production cluster

### **Database Secrets:**
- `DB_PASSWORD_DEV` - PostgreSQL password for dev environment
- `DB_PASSWORD_STAGING` - PostgreSQL password for staging environment
- `DB_PASSWORD_PRODUCTION` - PostgreSQL password for production environment

### **Container Registry:**
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions for GHCR access

## 🚀 Deployment Flow

### **1. Code Push**
```bash
git push origin main           # → Deploys to production
git push origin develop        # → Deploys to staging
git push origin feature/xyz    # → Deploys to dev
```

### **2. Automated Steps**
1. **Test** - Run linting and unit tests
2. **Build** - Build Docker images for API and Celery worker
3. **Push** - Push images to GitHub Container Registry (ghcr.io)
4. **Deploy** - Deploy to appropriate Kubernetes cluster using Helm
5. **Verify** - Check pod health and service availability

### **3. Deployment Details**

Each deployment:
- Creates/updates namespace (vmshift-dev, vmshift-staging, vmshift-production)
- Creates image pull secret for GitHub Container Registry
- Creates database connection secrets
- Deploys using environment-specific Helm values
- Waits for pods to be ready
- Reports LoadBalancer IP and URL

## 🌐 Environment URLs

After successful deployment:
- **Dev**: http://172.234.3.87 or https://vmshift-dev.satyamay.tech
- **Staging**: http://172.234.3.86 or https://vmshift-staging.satyamay.tech
- **Production**: http://172.234.3.83 or https://vmshift.satyamay.tech

## 📊 Monitoring Deployments

### **View Workflow Runs:**
```bash
gh run list --limit 10
```

### **Watch Active Run:**
```bash
gh run watch
```

### **View Run Logs:**
```bash
gh run view <run-id> --log
```

### **Check Deployment Status:**
```bash
# Dev
export KUBECONFIG=terraform/kubeconfig-dev.yaml
kubectl get pods -n vmshift-dev

# Staging
export KUBECONFIG=terraform/kubeconfig-staging.yaml
kubectl get pods -n vmshift-staging

# Production
export KUBECONFIG=terraform/kubeconfig-production.yaml
kubectl get pods -n vmshift-production
```

## 🔄 Rollback Strategy

If a deployment fails or has issues:

### **Option 1: Revert Git Commit**
```bash
git revert HEAD
git push origin main  # Automatically redeploys previous version
```

### **Option 2: Manual Helm Rollback**
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml
helm rollback vmshift -n vmshift-production
```

### **Option 3: Redeploy Specific Version**
```bash
# Trigger workflow with specific commit
gh workflow run "CI/CD Pipeline" --ref <commit-sha>
```

## 🐛 Troubleshooting

### **Pipeline Fails at Build Step:**
- Check if Docker images build locally
- Verify Dockerfile syntax
- Check GitHub Container Registry permissions

### **Pipeline Fails at Deploy Step:**
- Verify kubeconfig secrets are correct
- Check cluster connectivity
- Verify namespace exists
- Check Helm chart syntax

### **Pods CrashLoopBackOff:**
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>

# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check resource limits
kubectl top pods -n <namespace>
```

### **Database Connection Issues:**
- Verify database secrets are created
- Check PostgreSQL pod is running
- Test connection from API pod:
```bash
kubectl exec -it <api-pod> -n <namespace> -- env | grep DATABASE_URL
```

## 📝 Next Steps

1. **Set up Terraform CI/CD** - Automate infrastructure changes
2. **Add integration tests** - Test deployments after successful deployment
3. **Set up monitoring alerts** - Get notified of deployment failures
4. **Configure staging approval** - Require manual approval before production
5. **Add deployment notifications** - Slack/Discord notifications

## 🔗 Related Documentation

- [Multi-Environment Setup](MULTI-ENVIRONMENT.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Terraform Documentation](../terraform/TERRAFORM-MULTI-ENV.md)
- [Quick Reference](QUICK-REFERENCE.md)
