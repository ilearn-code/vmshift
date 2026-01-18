# 🎯 VMShift - Quick Reference Card

## 🌐 Live Application URLs

| Service | URL |
|---------|-----|
| **API** | https://vmshift.satyamay.tech |
| **API Docs** | https://vmshift.satyamay.tech/docs |
| **Health** | https://vmshift.satyamay.tech/health |
| **ArgoCD** | http://172.234.2.19 |
| **Grafana** | http://172.234.2.23 |

## 🔐 Credentials

```bash
# ArgoCD
Username: admin
Password: gWk3tIWiHITILwYq

# Grafana
Username: admin
Password: admin123

# Database (in-cluster)
Host: 10.128.204.136:5432
Database: vmshift
User: vmshift_user
Password: vmshift_password_2024
```

## 🚀 Quick Commands

### Check Application Status
```bash
# All pods
kubectl get pods -n vmshift

# Services and Ingress
kubectl get svc,ingress -n vmshift

# Logs (API)
kubectl logs -f deployment/vmshift-api -n vmshift

# Logs (Workers)
kubectl logs -f deployment/vmshift-celery-worker -n vmshift
```

### Test Application
```bash
# Health check
curl https://vmshift.satyamay.tech/health

# API root
curl https://vmshift.satyamay.tech/

# Create VM
curl -X POST https://vmshift.satyamay.tech/api/v1/vms/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-vm",
    "uuid": "vm-test-001",
    "os_type": "Ubuntu 22.04",
    "os_family": "linux",
    "cpu_count": 4,
    "memory_mb": 8192
  }'
```

### Deployment Commands
```bash
# Deploy/Update with Helm
helm upgrade --install vmshift ./helm/vmshift \
  --namespace vmshift \
  --set image.tag=latest

# Restart deployment
kubectl rollout restart deployment/vmshift-api -n vmshift

# Update image
kubectl set image deployment/vmshift-api \
  vmshift-api=ghcr.io/ilearn-code/vmshift-api:TAG -n vmshift
```

### CI/CD
```bash
# Trigger workflow
gh workflow run ci-cd.yaml

# Watch workflow
gh run list --workflow=ci-cd.yaml --limit 1
gh run watch <RUN_ID>

# View logs
gh run view <RUN_ID> --log
```

### Monitoring
```bash
# Port-forward ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Port-forward Grafana
kubectl port-forward svc/grafana -n monitoring 3000:80

# Port-forward API (local testing)
kubectl port-forward svc/vmshift-api-service -n vmshift 8000:80
```

### Troubleshooting
```bash
# Describe pod
kubectl describe pod <POD_NAME> -n vmshift

# Get events
kubectl get events -n vmshift --sort-by='.lastTimestamp'

# Check resource usage
kubectl top pods -n vmshift
kubectl top nodes

# Test database connection
kubectl exec -it deployment/vmshift-api -n vmshift -- \
  psql postgresql://vmshift_user:vmshift_password_2024@10.128.204.136:5432/vmshift -c "SELECT 1;"

# Delete and recreate pod
kubectl delete pod <POD_NAME> -n vmshift
```

## 📦 Container Images

```
# Current images
ghcr.io/ilearn-code/vmshift-api:3cca532
ghcr.io/ilearn-code/vmshift-celery:3cca532

# Pull locally
docker pull ghcr.io/ilearn-code/vmshift-api:3cca532
```

## 🏗️ Infrastructure

```
Cluster ID: 557602
Cluster Name: vmshift-lke-cluster
Region: us-east
Nodes: 3x g6-standard-2 (2 vCPU, 4GB RAM)
Kubernetes: v1.34.3
Ingress IP: 143.42.224.166
```

## 📊 Resource Summary

```
Namespace: vmshift
Pods: 8 total
├─ API: 2/2 Running
├─ Celery Workers: 2/2 Running
├─ Celery Beat: 1/1 Running
├─ PostgreSQL: 1/1 Running
└─ Redis: 1/1 Running

Storage: 20Gi (2x 10Gi PVCs)
```

## 🎓 Tech Stack at a Glance

```yaml
Language: Python 3.11
Framework: FastAPI
Task Queue: Celery + Redis
Database: PostgreSQL 16
Container: Docker
Orchestration: Kubernetes (LKE)
Package Manager: Helm
GitOps: ArgoCD
CI/CD: GitHub Actions
IaC: Terraform
Monitoring: Prometheus + Grafana
Ingress: NGINX
SSL: Let's Encrypt (cert-manager)
```

## 🔄 Common Workflows

### Update Application Code
```bash
# 1. Make changes locally
git add .
git commit -m "Your changes"
git push

# 2. CI/CD automatically:
#    - Builds images
#    - Pushes to GHCR
#    - Updates deployment
#    - ArgoCD syncs

# 3. Verify deployment
kubectl get pods -n vmshift
kubectl logs -f deployment/vmshift-api -n vmshift
```

### Scale Application
```bash
# Scale API pods
kubectl scale deployment/vmshift-api --replicas=4 -n vmshift

# Scale workers
kubectl scale deployment/vmshift-celery-worker --replicas=4 -n vmshift

# Check HPA status
kubectl get hpa -n vmshift
```

### Backup Database
```bash
# Exec into PostgreSQL pod
kubectl exec -it deployment/postgresql -n vmshift -- bash

# Create backup
pg_dump -U vmshift_user vmshift > /tmp/backup.sql

# Copy from pod
kubectl cp vmshift/postgresql-POD-NAME:/tmp/backup.sql ./backup.sql
```

### View Application Metrics
```bash
# Port-forward Grafana
kubectl port-forward svc/grafana -n monitoring 3000:80

# Open browser
open http://localhost:3000

# Login with admin/admin123
# Navigate to Dashboards → Kubernetes
```

## 🐛 Quick Fixes

### Pods Not Starting
```bash
# Check events
kubectl describe pod <POD_NAME> -n vmshift

# Check image pull
kubectl get pods -n vmshift | grep ImagePull

# Recreate image pull secret
kubectl delete secret ghcr-secret -n vmshift
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PAT \
  -n vmshift
```

### Database Connection Issues
```bash
# Check PostgreSQL pod
kubectl get pod -l app=postgresql -n vmshift

# Check connection from API
kubectl exec -it deployment/vmshift-api -n vmshift -- \
  curl http://10.128.204.136:5432

# Restart database
kubectl rollout restart deployment/postgresql -n vmshift
```

### SSL Certificate Issues
```bash
# Check certificate
kubectl get certificate -n vmshift

# Check cert-manager logs
kubectl logs -n cert-manager deployment/cert-manager

# Delete and recreate certificate
kubectl delete certificate vmshift-tls -n vmshift
kubectl rollout restart deployment/vmshift-api -n vmshift
```

## 📞 Support

- **Documentation**: [README.md](../README.md)
- **Deployment Guide**: [docs/DEPLOYMENT.md](./DEPLOYMENT.md)
- **Issues**: [GitHub Issues](https://github.com/ilearn-code/vmshift/issues)

---

**Last Updated**: January 18, 2026  
**Version**: 1.0.0  
**Status**: ✅ Production
