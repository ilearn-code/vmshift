# DevOps Improvements Needed

Current Status: Both Application and IAC repos have multi-environment support (dev, staging, production)

## 🔴 Critical (Implement ASAP)

### 1. Environment Protection & Approvals ⚠️
**Status**: Missing  
**Impact**: Production can be deployed without review

**Actions**:
```bash
# Run this script to create environments
./setup-environments.sh

# Then manually configure at:
# https://github.com/ilearn-code/vmshift/settings/environments
# https://github.com/ilearn-code/iac-vmshift/settings/environments
```

**Configuration**:
- **Production**:
  - ✅ Required reviewers: 2+ team members
  - ✅ Wait timer: 5 minutes
  - ✅ Deployment branches: `main` only
  - ✅ Prevent self-review

- **Staging**: 
  - ✅ Required reviewers: 1 team member
  - ✅ Deployment branches: `develop` only

- **Dev**:
  - ❌ No restrictions (auto-deploy)

### 2. Remote Terraform State Backend ⚠️
**Status**: Using local state (committed to git - SECURITY RISK)  
**Impact**: State conflicts, no locking, secrets exposed

**Option A: Terraform Cloud (Recommended)**
```hcl
# Add to terraform/main.tf
terraform {
  cloud {
    organization = "your-org"
    workspaces {
      tags = ["vmshift"]
    }
  }
}
```

**Option B: S3 + DynamoDB**
```hcl
# Add to terraform/main.tf
terraform {
  backend "s3" {
    bucket         = "vmshift-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

**Setup Steps**:
1. Create S3 bucket with versioning enabled
2. Create DynamoDB table for locking
3. Migrate existing state: `terraform init -migrate-state`
4. Remove state files from git: `git rm -r terraform.tfstate.d/`

### 3. Automated Testing in CI/CD ⚠️
**Status**: No tests running  
**Impact**: Bugs reach production

**Add to Application CI/CD**:
```yaml
# .github/workflows/ci-cd.yaml
test:
  name: Run Tests
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    - name: Run unit tests
      run: pytest tests/ --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v4
```

**Create test structure**:
```
tests/
├── __init__.py
├── test_api.py
├── test_tasks.py
└── test_integration.py
```

### 4. Health Check & Smoke Tests ⚠️
**Status**: Deployment succeeds even if app is broken  
**Impact**: Failed deployments marked as successful

**Add post-deployment verification**:
```yaml
# Add to both CI/CD workflows after deploy
- name: Health Check
  run: |
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
      if curl -f https://vmshift-${ENV}.satyamay.tech/health; then
        echo "✅ Health check passed"
        exit 0
      fi
      echo "⏳ Waiting for app... ($ATTEMPT/$MAX_ATTEMPTS)"
      sleep 10
      ATTEMPT=$((ATTEMPT + 1))
    done
    
    echo "❌ Health check failed"
    exit 1

- name: Smoke Tests
  run: |
    # Test critical endpoints
    curl -f https://vmshift-${ENV}.satyamay.tech/api/v1/status
    curl -f https://vmshift-${ENV}.satyamay.tech/docs
```

### 5. Secret Rotation Policy ⚠️
**Status**: Secrets never rotated (API tokens, DB passwords visible in attachment)  
**Impact**: Compromised credentials stay valid forever

**Actions**:
1. **Rotate Linode API Token** (exposed in terraform.tfvars):
   ```bash
   # Generate new token at: https://cloud.linode.com/profile/tokens
   # Update in GitHub secrets
   gh secret set LINODE_TOKEN --repo ilearn-code/iac-vmshift
   gh secret set LINODE_TOKEN --repo ilearn-code/vmshift
   ```

2. **Rotate Database Passwords**:
   ```bash
   # Generate strong passwords
   NEW_PASS=$(openssl rand -base64 32)
   
   # Update in each environment
   kubectl set env deployment/postgresql -n vmshift-production \
     POSTGRES_PASSWORD=$NEW_PASS
   
   # Update secrets
   gh secret set DB_PASSWORD_PRODUCTION --body "$NEW_PASS"
   ```

3. **Rotate Kubeconfig Tokens** (every 90 days):
   ```bash
   cd terraform
   terraform output -raw kubeconfig_production > kubeconfig-production.yaml
   gh secret set KUBECONFIG_PRODUCTION < kubeconfig-production.yaml
   ```

4. **Set up rotation schedule**:
   - API Tokens: Every 90 days
   - DB Passwords: Every 180 days
   - Kubeconfig: Every 90 days
   - Set calendar reminders

## 🟡 High Priority (Within 2 Weeks)

### 6. Centralized Logging
**Status**: No log aggregation  
**Impact**: Can't debug issues across environments

**Options**:

**A. Loki + Promtail (Lightweight)**
```bash
# Add to terraform/kubernetes.tf
resource "helm_release" "loki" {
  name       = "loki"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "loki-stack"
  namespace  = "monitoring"
  
  set {
    name  = "promtail.enabled"
    value = "true"
  }
}
```

**B. ELK Stack (Full-featured)**
- Deploy Elasticsearch, Logstash, Kibana
- Use Filebeat for log shipping

**C. Cloud Service**
- Datadog
- New Relic
- Papertrail

### 7. Monitoring & Alerting
**Status**: Prometheus/Grafana only in prod, no alerts configured  
**Impact**: Don't know when things break

**Setup Alerts**:
```yaml
# Create alerts.yaml in terraform/helm-values/
groups:
  - name: application_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          
      - alert: PodCrashLooping
        expr: rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pod is crash looping"
          
      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
```

**Configure AlertManager**:
```yaml
# alertmanager-config.yaml
route:
  receiver: 'slack'
  group_by: ['alertname', 'cluster', 'service']
  
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'YOUR_SLACK_WEBHOOK'
        channel: '#alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
```

### 8. Database Backups
**Status**: No automated backups  
**Impact**: Data loss if database fails

**Setup Automated Backups**:
```yaml
# Add to kubernetes manifests
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: vmshift-production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: postgres:16
            command:
            - /bin/sh
            - -c
            - |
              pg_dump -h postgresql -U postgres vmshift_prod | \
              gzip > /backups/backup-$(date +%Y%m%d-%H%M%S).sql.gz
              # Upload to S3 or object storage
              aws s3 cp /backups/*.sql.gz s3://vmshift-backups/
          restartPolicy: OnFailure
```

### 9. Security Scanning
**Status**: No vulnerability scanning  
**Impact**: Deploying vulnerable dependencies

**Add to CI/CD**:
```yaml
# Add to .github/workflows/ci-cd.yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
    
    - name: Upload to GitHub Security
      uses: github/codeql-action/upload-sarif@v3
      with:
        sarif_file: 'trivy-results.sarif'
    
    - name: Scan Docker images
      run: |
        docker pull ghcr.io/ilearn-code/vmshift-api:latest
        trivy image ghcr.io/ilearn-code/vmshift-api:latest
```

### 10. Rollback Strategy
**Status**: No automated rollback  
**Impact**: Manual intervention needed for bad deploys

**Add to Application CI/CD**:
```yaml
rollback:
  name: Rollback on Failure
  runs-on: ubuntu-latest
  needs: [deploy]
  if: failure()
  steps:
    - name: Rollback Helm Release
      run: |
        helm rollback vmshift -n vmshift-${ENV}
        
    - name: Notify Team
      uses: 8398a7/action-slack@v3
      with:
        status: failure
        text: 'Deployment failed, rolled back to previous version'
```

## 🟢 Medium Priority (Within 1 Month)

### 11. GitOps with ArgoCD
**Status**: ArgoCD installed but not used  
**Impact**: Missing declarative deployment benefits

**Setup ArgoCD Applications**:
```yaml
# Create argocd-apps/vmshift-production.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: vmshift-production
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/ilearn-code/vmshift
    targetRevision: main
    path: helm/vmshift
    helm:
      valueFiles:
        - values-prod.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: vmshift-production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

### 12. Infrastructure as Code for Everything
**Status**: Some manual kubectl commands still used  
**Impact**: Configuration drift

**Helmify Everything**:
- Move all kubectl patches to Helm values
- Document all manual changes
- Enforce "no manual changes" policy

### 13. Cost Monitoring
**Status**: No cost tracking  
**Impact**: Unexpected bills

**Setup Cost Monitoring**:
```yaml
# Add to terraform/kubernetes.tf
resource "kubernetes_namespace" "kubecost" {
  metadata {
    name = "kubecost"
  }
}

resource "helm_release" "kubecost" {
  name       = "kubecost"
  repository = "https://kubecost.github.io/cost-analyzer/"
  chart      = "cost-analyzer"
  namespace  = "kubecost"
}
```

**Linode Cost Alerts**:
- Set up billing alerts in Linode Cloud Manager
- Export cost data to spreadsheet monthly
- Tag resources for cost allocation

### 14. Kubernetes RBAC
**Status**: Using cluster-admin everywhere  
**Impact**: Security risk

**Create Service Accounts**:
```yaml
# rbac/ci-cd-service-account.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ci-cd-deployer
  namespace: vmshift-production
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: vmshift-production
rules:
- apiGroups: ["apps", ""]
  resources: ["deployments", "pods", "services"]
  verbs: ["get", "list", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-cd-deployer
  namespace: vmshift-production
subjects:
- kind: ServiceAccount
  name: ci-cd-deployer
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

### 15. Disaster Recovery Plan
**Status**: No DR documentation  
**Impact**: Slow recovery from major incidents

**Create DR Runbook**:
```markdown
# Disaster Recovery Runbook

## Scenario 1: Cluster Failure
1. Create new cluster: `cd terraform && terraform apply`
2. Restore from backup: `kubectl apply -f backups/`
3. Update DNS: Point to new cluster IP
4. Verify: Run smoke tests

## Scenario 2: Database Corruption
1. Stop application: `kubectl scale deployment vmshift-api --replicas=0`
2. Restore from backup: `pg_restore -d vmshift_prod backup.sql`
3. Verify data integrity
4. Restart application

## Scenario 3: Region Outage
1. Deploy to backup region (us-west)
2. Update DNS to failover
3. Monitor for region recovery
```

## 🔵 Nice to Have (Within 3 Months)

### 16. Service Mesh (Istio/Linkerd)
- Better observability
- Traffic management
- mTLS between services

### 17. Canary Deployments
- Deploy to subset of users first
- Automatic rollback on errors
- A/B testing capabilities

### 18. Performance Testing
- Load testing with k6
- Stress testing
- Performance regression detection

### 19. Multi-Region Deployment
- Deploy to multiple Linode regions
- Global load balancing
- Geo-routing

### 20. Developer Experience
- Local development with Tilt/Skaffold
- Pull request preview environments
- Self-service deployments

## Summary Priority Matrix

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| 🔴 Critical | Environment Protection | Low | High |
| 🔴 Critical | Remote Terraform State | Medium | High |
| 🔴 Critical | Automated Testing | Medium | High |
| 🔴 Critical | Health Checks | Low | High |
| 🔴 Critical | Secret Rotation | Low | Critical |
| 🟡 High | Centralized Logging | Medium | High |
| 🟡 High | Monitoring/Alerting | Medium | High |
| 🟡 High | Database Backups | Low | Critical |
| 🟡 High | Security Scanning | Low | Medium |
| 🟡 High | Rollback Strategy | Low | High |
| 🟢 Medium | GitOps with ArgoCD | High | Medium |
| 🟢 Medium | Full IaC | Medium | Medium |
| 🟢 Medium | Cost Monitoring | Low | Low |
| 🟢 Medium | RBAC | Medium | Medium |
| 🟢 Medium | DR Plan | Low | High |
| 🔵 Low | Service Mesh | High | Low |
| 🔵 Low | Canary Deployments | High | Low |
| 🔵 Low | Performance Testing | Medium | Low |
| 🔵 Low | Multi-Region | Very High | Medium |
| 🔵 Low | Dev Experience | Medium | Low |

## Next Steps

### Week 1:
1. ✅ Run `./setup-environments.sh` and configure GitHub environment protection
2. ✅ Rotate all exposed secrets (Linode token, DB passwords)
3. ✅ Set up remote Terraform state backend

### Week 2:
4. ✅ Add automated tests to CI/CD
5. ✅ Implement health checks and smoke tests
6. ✅ Set up database backups

### Week 3-4:
7. ✅ Deploy centralized logging (Loki)
8. ✅ Configure Prometheus alerts
9. ✅ Add security scanning

### Month 2:
10. ✅ Implement GitOps with ArgoCD
11. ✅ Set up cost monitoring
12. ✅ Create RBAC policies
13. ✅ Document DR procedures

---

**Generated**: January 28, 2026  
**Status**: Multi-environment CI/CD operational, DevOps maturity improvements needed  
**Repositories**: 
- Application: https://github.com/ilearn-code/vmshift
- Infrastructure: https://github.com/ilearn-code/iac-vmshift
