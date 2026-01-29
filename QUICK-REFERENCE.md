# 🚀 Quick Reference - Multi-Cluster GitOps

## ArgoCD Access
```
URL:      http://172.234.2.39
Username: admin
Password: T3ECWVag1iT0mz7q
```

## Application URLs

### Production ✅
```
URL:    http://vmshift.satyamay.tech
IP:     172.234.3.83
Health: http://vmshift.satyamay.tech/health
```

### Staging 🔧
```
LoadBalancer IP: 172.234.3.86
DNS to configure: vmshift-staging.satyamay.tech → 172.234.3.86
```

### Dev 🔧
```
LoadBalancer IP: 172.234.3.87
DNS to configure: vmshift-dev.satyamay.tech → 172.234.3.87
```

## ArgoCD Applications Status

| Application | Branch | Cluster | Status | Health |
|-------------|--------|---------|--------|--------|
| vmshift-prod | main | Production | ✅ Synced | ⏳ Progressing |
| vmshift-staging | develop | Staging | ✅ Synced | ⏳ Progressing |
| vmshift-dev | develop | Dev | ✅ Synced | ⏳ Progressing |

## Quick Commands

### View All Applications
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml
kubectl get applications -n argocd
```

### Check Production
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml
kubectl get pods -n vmshift-production
```

### Check Staging
```bash
export KUBECONFIG=terraform/kubeconfig-staging.yaml
kubectl get pods -n vmshift-staging
```

### Check Dev
```bash
export KUBECONFIG=terraform/kubeconfig-dev.yaml
kubectl get pods -n vmshift-dev
```

### Manual Sync (if needed)
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml

# Sync production
kubectl patch application vmshift-prod -n argocd --type merge -p '{"operation":{"sync":{}}}'

# Sync staging
kubectl patch application vmshift-staging -n argocd --type merge -p '{"operation":{"sync":{}}}'

# Sync dev
kubectl patch application vmshift-dev -n argocd --type merge -p '{"operation":{"sync":{}}}'
```

## GitOps Workflow

### Deploy to Production
```bash
git checkout main
# Make changes
git commit -am "Your change"
git push origin main
# GitHub Actions → builds images → updates values-production.yaml → ArgoCD syncs
```

### Deploy to Staging & Dev
```bash
git checkout develop
# Make changes
git commit -am "Your change"
git push origin develop
# GitHub Actions → builds images → updates values-staging.yaml & values-dev.yaml → ArgoCD syncs
```

## Files Structure

```
terraform/
├── argocd-apps/
│   ├── staging-app.yaml
│   └── dev-app.yaml
├── cluster-secrets/
│   ├── staging-cluster.yaml
│   └── dev-cluster.yaml
├── kubeconfig-production.yaml
├── kubeconfig-staging.yaml
└── kubeconfig-dev.yaml

docs/
├── SETUP-COMPLETE.md
├── MULTI-CLUSTER-ARGOCD.md
├── GITOPS.md
├── TWO-REPO-GITOPS.md
└── PIPELINE.md
```

## Cluster Details

### Production Cluster (lke561964)
- **ArgoCD**: http://172.234.2.39
- **Application**: http://vmshift.satyamay.tech (172.234.3.83)
- **Manages**: All three environments via ArgoCD

### Staging Cluster (lke562015)
- **API**: https://bb71cee1-2781-46d6-b409-8e633a601840.us-east-2-gw.linodelke.net:443
- **LoadBalancer**: 172.234.3.86
- **Managed by**: Production ArgoCD

### Dev Cluster (lke562023)
- **API**: https://9a0e3d87-c7ba-472c-88e6-949fac190c5d.us-east-1-gw.linodelke.net:443
- **LoadBalancer**: 172.234.3.87
- **Managed by**: Production ArgoCD

## Troubleshooting

### ArgoCD Logs
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller --tail=50
```

### Check Sync Status
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml
kubectl describe application vmshift-staging -n argocd
```

### Verify Cluster Connectivity
```bash
export KUBECONFIG=terraform/kubeconfig-production.yaml
kubectl get secrets -n argocd | grep cluster
```

## Next Actions

1. **Configure Staging DNS**:
   ```
   vmshift-staging.satyamay.tech → 172.234.3.86
   ```

2. **Configure Dev DNS**:
   ```
   vmshift-dev.satyamay.tech → 172.234.3.87
   ```

3. **Test GitOps Flow**:
   ```bash
   git checkout develop
   echo "# Test" >> README.md
   git commit -am "Test GitOps"
   git push
   # Watch ArgoCD UI: http://172.234.2.39
   ```

4. **Enable HTTPS**:
   - cert-manager is already installed
   - Will auto-issue certificates for all domains

## Success! ✅

- ✅ Single ArgoCD managing 3 clusters
- ✅ GitOps workflow for all environments
- ✅ Automated deployments via GitHub Actions
- ✅ Production accessible at vmshift.satyamay.tech
- ✅ Staging & Dev ready (DNS pending)

**You now have a complete multi-cluster GitOps setup!** 🎉
