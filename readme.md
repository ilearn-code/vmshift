# VMShift Demo - VM Migration Platform

A demonstration application showcasing VM-to-Container migration workflows using **FastAPI**, **Celery**, **PostgreSQL**, **Docker**, and **Kubernetes** deployed on **Akamai Cloud** (Linode Kubernetes Engine).

## 🎯 Features

- **VM Discovery** - Discover and catalog virtual machines from vSphere/VMware
- **Migration Workflows** - Orchestrate VM containerization with progress tracking
- **Artifact Generation** - Auto-generate Dockerfiles, Kubernetes manifests, and Docker Compose files
- **Background Processing** - Async task queue with Celery for reliable job execution
- **REST API** - FastAPI with auto-generated OpenAPI documentation
- **GitOps with ArgoCD** - Declarative, Git-based continuous deployment
- **Production Ready** - Health checks, logging, monitoring, and CI/CD

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Akamai Cloud (LKE)                             │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                                                        │
│  │   ArgoCD    │◀── Git Repository (GitHub)                             │
│  │   (GitOps)  │    - Watches for changes                               │
│  └──────┬──────┘    - Auto-syncs deployments                            │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐          │
│  │   Ingress   │───▶│  FastAPI    │───▶│   Celery Workers    │          │
│  │   (nginx)   │    │    API      │    │   (Background Jobs) │          │
│  └─────────────┘    └──────┬──────┘    └──────────┬──────────┘          │
│                            │                       │                    │
│                            ▼                       ▼                    │
│                    ┌───────────────┐       ┌─────────────┐              │
│                    │  PostgreSQL   │       │    Redis    │              │
│                    │  (Managed DB) │       │   (Broker)  │              │
│                    └───────────────┘       └─────────────┘              │
└─────────────────────────────────────────────────────────────────────────┘

GitOps Flow:
  Developer → Push Code → GitHub Actions (CI) → Build Image → Push to GHCR
                                    ↓
                          Update K8s manifests
                                    ↓
                          ArgoCD detects changes → Auto-deploy to LKE
```

## 📋 Prerequisites

- **Akamai Cloud Account** with $100 free trial
- **Docker** and **Docker Compose** installed locally
- **kubectl** configured for Kubernetes
- **Terraform** v1.0+ (for IaC provisioning)
- **Helm** v3+ (for package management)
- **GitHub Account** for CI/CD with GitHub Actions
- **Python 3.11+** for local development

## 🚀 Quick Start - Local Development

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/vmshift-demo.git
cd vmshift-demo

# Copy environment file
cp .env.example .env

# Start all services with Docker Compose
docker-compose up -d
```

### 2. Access the Application

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Celery Flower (Task Monitor)**: http://localhost:5555

### 3. Test the API

```bash
# Check health
curl http://localhost:8000/health

# Create a VM (simulated discovery)
curl -X POST http://localhost:8000/api/v1/vms/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "uuid": "vm-001-test",
    "os_type": "Windows Server 2019",
    "os_family": "windows",
    "cpu_count": 4,
    "memory_mb": 8192
  }'

# Create a migration
curl -X POST http://localhost:8000/api/v1/migrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Migrate Web Server",
    "vm_id": 1,
    "target_platform": "kubernetes",
    "container_port": 80
  }'

# Generate artifacts
curl -X POST http://localhost:8000/api/v1/migrations/1/generate-artifacts

# Start migration
curl -X POST http://localhost:8000/api/v1/migrations/1/start
```

## ☁️ Deploy to Akamai Cloud (LKE) - Complete Guide

This guide shows you how to deploy the complete application stack to Akamai Cloud using Infrastructure as Code (Terraform), GitOps (ArgoCD), and Helm charts.

### 📸 Deployment Overview

![Architecture Diagram](./docs/screenshots/architecture.png)
*Complete deployment architecture on Akamai Cloud*

---

## 🛠️ Step-by-Step Deployment

### Step 1: Prerequisites Setup

#### 1.1 Create Akamai Cloud Account
1. Sign up at [https://cloud.linode.com](https://cloud.linode.com)
2. Activate your **$100 free credit**
3. Navigate to **Profile** → **API Tokens**
4. Create a new token with **Read/Write** access

![Akamai API Token](./docs/screenshots/01-akamai-api-token.png)
*Creating API token in Akamai Cloud Console*

#### 1.2 Fork the Repository
```bash
# Fork this repo to your GitHub account
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/vmshift.git
cd vmshift
```

#### 1.3 Install Required Tools
```bash
# Install Terraform
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform

# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# Install Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Install GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Authenticate with GitHub
gh auth login
```

---

### Step 2: Infrastructure Provisioning with Terraform

#### 2.1 Configure Terraform Variables
```bash
cd terraform

# Create variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
nano terraform.tfvars
```

**terraform.tfvars content:**
```hcl
linode_token = "YOUR_LINODE_API_TOKEN"
cluster_name = "vmshift-cluster"
region       = "us-east"  # or your preferred region
node_count   = 3
node_type    = "g6-standard-2"  # 2 vCPUs, 4GB RAM
```

![Terraform Configuration](./docs/screenshots/02-terraform-config.png)
*Terraform variables configuration*

#### 2.2 Deploy Infrastructure
```bash
# Initialize Terraform
terraform init

# Review the plan
terraform plan

# Apply configuration (creates all resources)
terraform apply
```

**What gets created:**
- ✅ **LKE Cluster** - 3-node Kubernetes cluster (v1.34.3)
- ✅ **PostgreSQL Database** - Managed PostgreSQL 16 instance (deployed in-cluster for reliability)
- ✅ **ArgoCD** - GitOps continuous deployment
- ✅ **NGINX Ingress Controller** - Load balancer with SSL
- ✅ **Cert-Manager** - Automatic SSL certificate management
- ✅ **Prometheus & Grafana** - Monitoring and observability
- ✅ **Redis** - Message broker for Celery

![Terraform Apply](./docs/screenshots/03-terraform-apply.png)
*Terraform applying infrastructure changes*

#### 2.3 Save Outputs
```bash
# Save important outputs
terraform output -raw kubeconfig > ~/.kube/config
terraform output -raw argocd_password > argocd-password.txt
terraform output -raw grafana_password > grafana-password.txt

# Test cluster access
kubectl cluster-info
kubectl get nodes
```

![Cluster Info](./docs/screenshots/04-cluster-info.png)
*Kubernetes cluster running on Akamai Cloud*

---

### Step 3: Configure GitHub Secrets for CI/CD

#### 3.1 Get KUBECONFIG
```bash
# Get base64 encoded kubeconfig
cat ~/.kube/config | base64 -w 0
```

#### 3.2 Get ArgoCD Auth Token
```bash
# Port-forward to ArgoCD
kubectl port-forward svc/argocd-server -n argocd 8080:443 &

# Login to ArgoCD
argocd login localhost:8080 --username admin --password $(cat argocd-password.txt) --insecure

# Generate auth token
argocd account generate-token --account admin
```

#### 3.3 Generate GitHub Container Registry Token
1. Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click **Generate new token (classic)**
3. Select scopes: `write:packages`, `read:packages`, `delete:packages`
4. Copy the token

![GitHub PAT](./docs/screenshots/05-github-pat.png)
*Creating GitHub Personal Access Token*

#### 3.4 Add Secrets to GitHub Repository
1. Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**
2. Add three secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `KUBECONFIG` | Base64 kubeconfig from step 3.1 | Kubernetes access |
| `ARGOCD_AUTH_TOKEN` | Token from step 3.2 | ArgoCD CLI access |
| `GHCR_PAT` | Token from step 3.3 | GitHub Container Registry |

![GitHub Secrets](./docs/screenshots/06-github-secrets.png)
*GitHub Actions secrets configuration*

---

### Step 4: Deploy Application with Helm

#### 4.1 Configure Helm Values
```bash
# Edit Helm values
nano helm/vmshift/values.yaml
```

**Key configurations to update:**
```yaml
image:
  registry: ghcr.io
  repository: YOUR_GITHUB_USERNAME/vmshift
  tag: latest
  pullPolicy: Always

ingress:
  enabled: true
  hosts:
    - host: vmshift.yourdomain.com  # Update with your domain
      paths:
        - path: /
          pathType: Prefix

postgresql:
  enabled: true  # Use in-cluster PostgreSQL
  persistence:
    size: 10Gi
```

![Helm Values](./docs/screenshots/07-helm-values.png)
*Helm chart configuration*

#### 4.2 Make GitHub Packages Public
1. Go to your GitHub profile → **Packages**
2. Click on `vmshift-api` package
3. Go to **Package settings**
4. Scroll to **Danger Zone** → Click **Change visibility**
5. Select **Public** and confirm
6. Repeat for `vmshift-celery` package

![GitHub Packages](./docs/screenshots/08-github-packages.png)
*Making GitHub Container Registry packages public*

#### 4.3 Fix Existing Resources for Helm
```bash
# Add Helm labels/annotations to existing PVC
kubectl annotate pvc postgresql-pvc -n vmshift \
  meta.helm.sh/release-name=vmshift \
  meta.helm.sh/release-namespace=vmshift --overwrite

kubectl label pvc postgresql-pvc -n vmshift \
  app.kubernetes.io/managed-by=Helm --overwrite
```

#### 4.4 Deploy with Helm
```bash
# Create namespace
kubectl create namespace vmshift

# Create image pull secret for GHCR
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_PAT \
  -n vmshift

# Install/upgrade with Helm
helm upgrade --install vmshift ./helm/vmshift \
  --namespace vmshift \
  --set image.tag=latest \
  --debug
```

![Helm Install](./docs/screenshots/09-helm-install.png)
*Deploying application with Helm*

---

### Step 5: Trigger CI/CD Pipeline

#### 5.1 Push Code Changes
```bash
# Make any change to trigger CI/CD
git add .
git commit -m "Deploy to Akamai Cloud"
git push origin main
```

#### 5.2 Monitor GitHub Actions
1. Go to your GitHub repository → **Actions** tab
2. Watch the **CI/CD Pipeline** workflow
3. It will:
   - Build Docker images for API and Celery
   - Push images to GitHub Container Registry
   - Update Helm deployment
   - Sync with ArgoCD

![GitHub Actions](./docs/screenshots/10-github-actions.png)
*CI/CD pipeline running in GitHub Actions*

#### 5.3 Verify Workflow Success
```bash
# Check workflow status from CLI
gh run list --workflow=ci-cd.yaml --limit 5

# Watch specific run
gh run watch <RUN_ID>
```

---

### Step 6: Verify Deployment

#### 6.1 Check Pod Status
```bash
# Check all pods in vmshift namespace
kubectl get pods -n vmshift

# Expected output:
# NAME                                     READY   STATUS    RESTARTS   AGE
# postgresql-xxxxxxxxxx-xxxxx              1/1     Running   0          5m
# redis-xxxxxxxxxx-xxxxx                   1/1     Running   0          5m
# vmshift-api-xxxxxxxxxx-xxxxx             1/1     Running   0          3m
# vmshift-api-xxxxxxxxxx-xxxxx             1/1     Running   0          3m
# vmshift-celery-worker-xxxxxx-xxxxx       1/1     Running   0          3m
# vmshift-celery-worker-xxxxxx-xxxxx       1/1     Running   0          3m
# vmshift-celery-beat-xxxxxxxxx-xxxxx      1/1     Running   0          3m
```

![Pod Status](./docs/screenshots/11-pod-status.png)
*All application pods running successfully*

#### 6.2 Check Services and Ingress
```bash
# Get services
kubectl get svc -n vmshift

# Get ingress
kubectl get ingress -n vmshift

# Note the EXTERNAL-IP (e.g., 143.42.224.166)
```

![Services](./docs/screenshots/12-services-ingress.png)
*Kubernetes services and ingress configuration*

#### 6.3 Test Application Health
```bash
# Get ingress IP
INGRESS_IP=$(kubectl get ingress vmshift-ingress -n vmshift -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl -k https://$INGRESS_IP/health -H "Host: vmshift.yourdomain.com"

# Expected response:
# {"status":"healthy","database":"connected","redis":"connected"}
```

---

### Step 7: Access Monitoring & GitOps Dashboards

#### 7.1 Access ArgoCD
```bash
# Get ArgoCD external IP
ARGOCD_IP=$(kubectl get svc argocd-server -n argocd -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "ArgoCD URL: http://$ARGOCD_IP"
echo "Username: admin"
echo "Password: $(cat argocd-password.txt)"

# Or use port-forward
kubectl port-forward svc/argocd-server -n argocd 8080:443
# Access at: http://localhost:8080
```

![ArgoCD Dashboard](./docs/screenshots/13-argocd-dashboard.png)
*ArgoCD GitOps dashboard showing application sync status*

#### 7.2 Access Grafana Monitoring
```bash
# Get Grafana external IP
GRAFANA_IP=$(kubectl get svc grafana -n monitoring -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

echo "Grafana URL: http://$GRAFANA_IP"
echo "Username: admin"
echo "Password: $(cat grafana-password.txt)"
```

![Grafana Dashboard](./docs/screenshots/14-grafana-metrics.png)
*Grafana showing application metrics and resource usage*

#### 7.3 View Application Logs
```bash
# API logs
kubectl logs -f deployment/vmshift-api -n vmshift

# Celery worker logs
kubectl logs -f deployment/vmshift-celery-worker -n vmshift

# Follow all logs
kubectl logs -f -l app=vmshift -n vmshift --all-containers=true
```

---

### Step 8: Configure Domain (Optional)

#### 8.1 Add DNS Record
1. Get ingress IP: `kubectl get ingress -n vmshift`
2. In your DNS provider (Cloudflare, GoDaddy, etc.):
   - Add **A Record**: `vmshift` → `143.42.224.166` (your ingress IP)
   - Or add **CNAME**: `vmshift` → `<ingress-hostname>`

![DNS Configuration](./docs/screenshots/15-dns-config.png)
*DNS A record pointing to Kubernetes ingress*

#### 8.2 Wait for SSL Certificate
```bash
# Check certificate status
kubectl get certificate -n vmshift

# Wait for "Ready" status
kubectl wait --for=condition=ready certificate/vmshift-tls -n vmshift --timeout=300s
```

#### 8.3 Access via Domain
```bash
# Test HTTPS access
curl https://vmshift.yourdomain.com/health

# Open in browser
open https://vmshift.yourdomain.com/docs
```

![Application Live](./docs/screenshots/16-app-running.png)
*Application running live with SSL certificate*

---

### Step 9: Test the Application

#### 9.1 Access API Documentation
Open `https://vmshift.yourdomain.com/docs` in your browser

![API Docs](./docs/screenshots/17-api-docs.png)
*Interactive API documentation with Swagger UI*

#### 9.2 Create a Test VM
```bash
curl -X POST https://vmshift.yourdomain.com/api/v1/vms/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "web-server-01",
    "uuid": "vm-001-prod",
    "os_type": "Ubuntu 22.04",
    "os_family": "linux",
    "cpu_count": 4,
    "memory_mb": 8192,
    "disk_gb": 100
  }'
```

![Create VM](./docs/screenshots/18-create-vm.png)
*Creating a VM entry via API*

#### 9.3 Create Migration Workflow
```bash
curl -X POST https://vmshift.yourdomain.com/api/v1/migrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Migrate Ubuntu Web Server",
    "vm_id": 1,
    "target_platform": "kubernetes",
    "container_port": 80,
    "environment": "production"
  }'
```

#### 9.4 Generate Container Artifacts
```bash
# Generate Dockerfile, K8s manifests
curl -X POST https://vmshift.yourdomain.com/api/v1/migrations/1/generate-artifacts

# Check Celery task execution in logs
kubectl logs -f deployment/vmshift-celery-worker -n vmshift
```

![Migration Progress](./docs/screenshots/19-migration-workflow.png)
*Migration workflow in progress*

---

## 📊 Monitoring & Observability

### View Application Metrics

**Prometheus Queries:**
```promql
# API request rate
rate(http_requests_total[5m])

# Pod CPU usage
container_cpu_usage_seconds_total{namespace="vmshift"}

# Pod memory usage
container_memory_usage_bytes{namespace="vmshift"}
```

**Grafana Dashboards:**
- **Kubernetes Cluster** - Node metrics, resource usage
- **Application Performance** - API latency, error rates
- **Celery Workers** - Task queue depth, worker health

![Prometheus Metrics](./docs/screenshots/20-prometheus-queries.png)
*Prometheus metrics for application monitoring*

---

## 🔧 Troubleshooting

### Common Issues

#### Issue 1: Pods Stuck in ImagePullBackOff
```bash
# Check image pull secrets
kubectl get secrets -n vmshift

# Recreate GHCR secret
kubectl delete secret ghcr-secret -n vmshift
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_PAT \
  -n vmshift

# Restart deployment
kubectl rollout restart deployment/vmshift-api -n vmshift
```

#### Issue 2: Worker Timeout During Startup
```bash
# Check API logs
kubectl logs deployment/vmshift-api -n vmshift --tail=50

# Increase resource limits in values.yaml
api:
  resources:
    limits:
      memory: "2Gi"
      cpu: "2000m"

# Redeploy
helm upgrade vmshift ./helm/vmshift -n vmshift
```

#### Issue 3: Database Connection Failed
```bash
# Check PostgreSQL pod
kubectl get pods -n vmshift | grep postgresql

# Check database logs
kubectl logs deployment/postgresql -n vmshift

# Test connection from API pod
kubectl exec -it deployment/vmshift-api -n vmshift -- \
  psql postgresql://vmshift_user:password@postgresql:5432/vmshift -c "SELECT 1;"
```

#### Issue 4: Helm Install Fails - PVC Ownership
```bash
# Add Helm labels to existing PVC
kubectl annotate pvc postgresql-pvc -n vmshift \
  meta.helm.sh/release-name=vmshift \
  meta.helm.sh/release-namespace=vmshift --overwrite

kubectl label pvc postgresql-pvc -n vmshift \
  app.kubernetes.io/managed-by=Helm --overwrite
```

---

## 🎯 Project Showcase Checklist

Use this checklist when documenting your project:

- [ ] Screenshot: Akamai Cloud Console showing cluster
- [ ] Screenshot: Terraform apply output
- [ ] Screenshot: GitHub Actions workflow success
- [ ] Screenshot: ArgoCD showing synced applications
- [ ] Screenshot: kubectl get pods showing all running
- [ ] Screenshot: Grafana dashboard with metrics
- [ ] Screenshot: API documentation (Swagger UI)
- [ ] Screenshot: Successful API request/response
- [ ] Screenshot: Celery worker processing tasks
- [ ] Screenshot: Application accessible via domain with SSL
- [ ] Diagram: Architecture overview
- [ ] Diagram: CI/CD pipeline flow
- [ ] Video: Quick demo of API functionality (optional)

---

## 💰 Cost Optimization

**Monthly Cost Estimate (Akamai Cloud):**
- LKE Cluster (3x g6-standard-2): ~$36/month
- Block Storage (20Gi): ~$2/month
- Bandwidth: Included (free)
- **Total: ~$38/month** (covered by $100 free credit for 2+ months)

**Free Tier Components:**
- GitHub Actions: 2,000 minutes/month (free)
- GitHub Container Registry: 500MB storage (free)
- Let's Encrypt SSL: Free

---

## 🎓 What You'll Learn

By deploying this project, you'll gain hands-on experience with:

✅ **Infrastructure as Code (IaC)** - Terraform for cloud provisioning  
✅ **Container Orchestration** - Kubernetes deployment and management  
✅ **GitOps** - ArgoCD for declarative continuous deployment  
✅ **CI/CD Pipelines** - GitHub Actions for automation  
✅ **Package Management** - Helm charts for Kubernetes  
✅ **Microservices** - FastAPI + Celery worker architecture  
✅ **Observability** - Prometheus & Grafana monitoring  
✅ **Cloud Platforms** - Akamai Cloud (Linode) LKE  
✅ **Security** - SSL certificates, secrets management  
✅ **Database Management** - PostgreSQL in Kubernetes

# 4. Access your cluster
export KUBECONFIG=$(pwd)/kubeconfig.yaml
kubectl get nodes

# 5. Get ArgoCD password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d
```

**See [terraform/README.md](terraform/README.md) for detailed documentation.**

---

### Option 2: Manual Setup

#### Step 1: Create Akamai Cloud Resources

1. **Log in to Akamai Cloud Console**: https://cloud.linode.com

2. **Create a Kubernetes Cluster (LKE)**:
   - Click "Kubernetes" → "Create Cluster"
   - Name: `vmshift-cluster`
   - Region: Choose nearest region
   - Kubernetes Version: Latest (1.28+)
   - Node Pool: 3x Shared CPU (Linode 4GB) - $36/month
   - Click "Create Cluster"

3. **Create PostgreSQL Database**:
   - Click "Databases" → "Create Database"
   - Engine: PostgreSQL 15
   - Plan: Shared CPU (1GB) - $15/month
   - Label: `vmshift-db`
   - Save the connection details

4. **Download kubeconfig**:
   - In your cluster, click "Download kubeconfig"
   - Save to `~/.kube/config` or set `KUBECONFIG` env var

### Step 2: Configure Secrets

```bash
# Test cluster connection
kubectl get nodes

# Create namespace
kubectl create namespace vmshift

# Create secrets with your Akamai PostgreSQL details
kubectl create secret generic vmshift-secrets \
  --from-literal=database-url='postgresql://linpostgres:YOUR_PASSWORD@YOUR_DB_HOST:5432/defaultdb?sslmode=require' \
  --from-literal=redis-url='redis://redis:6379/0' \
  --from-literal=celery-broker-url='redis://redis:6379/0' \
  --from-literal=celery-result-backend='redis://redis:6379/1' \
  -n vmshift
```

### Step 3: Setup GitHub Actions

1. **Fork/Clone this repository** to your GitHub account

2. **Add GitHub Secrets** (Settings → Secrets → Actions):
   
   | Secret Name | Value |
   |-------------|-------|
   | `KUBECONFIG` | Base64 encoded kubeconfig: `cat ~/.kube/config \| base64` |
   
3. **Update image references** in k8s manifests:
   - Replace `YOUR_GITHUB_USERNAME` with your GitHub username
   - Replace `YOUR_DOMAIN.com` with your domain (or use NodePort for testing)

### Step 4: Deploy

**Option A: Deploy with ArgoCD (Recommended - GitOps)**

```bash
# 1. Install ArgoCD on your cluster
kubectl create namespace argocd
---

### Option 3: Helm Charts

**Deploy using Helm package manager:**

```bash
# 1. Add custom values
cd helm/vmshift

# 2. Edit values.yaml with your settings
nano values.yaml

# 3. Install chart
helm install vmshift . \
  --namespace vmshift \
  --create-namespace \
  --set image.repository=ghcr.io/YOUR_USERNAME/vmshift-api \
  --set image.tag=latest

# 4. Verify deployment
helm status vmshift -n vmshift
kubectl get pods -n vmshift

# 5. Upgrade
helm upgrade vmshift . -n vmshift

# 6. Uninstall
helm uninstall vmshift -n vmshift
```

---

kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Apply custom ArgoCD configuration
kubectl apply -f k8s/argocd/install-argocd.yaml

# 3. Get ArgoCD admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# 4. Access ArgoCD UI (port-forward)
kubectl port-forward svc/argocd-server -n argocd 8080:443

# 5. Open https://localhost:8080 and login with admin/<password>

# 6. Register your application with ArgoCD
kubectl apply -f k8s/argocd/application.yaml

# ArgoCD will now:
# - Watch your GitHub repo for changes
# - Auto-sync deployments when you push
# - Self-heal if someone manually changes cluster state
```

**Option B: Deploy with kubectl (Manual)**

```bash
kubectl apply -f k8s/namespace-secrets.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/api-deployment.yaml
kubectl apply -f k8s/celery-deployment.yaml
kubectl apply -f k8s/hpa.yaml
```�️ Redis Configuration

The project includes **3 Redis deployment options**:

### 1. Simple Redis (Development)
```bash
kubectl apply -f k8s/redis-deployment.yaml
```
- Single instance
- No persistence
- Good for: Local development, testing

### 2. Redis StatefulSet (Production)
```bash
kubectl apply -f k8s/redis-statefulset.yaml
```
- ✅ **Persistent storage** (AOF + RDB)
- ✅ **Resource limits**
- ✅ **Health checks**
- ✅ **Prometheus metrics**
- Good for: Production single-node

### 3. Redis Sentinel (High Availability)
```bash
kubectl apply -f k8s/redis-ha.yaml
```
- ✅ **Master-Slave replication**
- ✅ **Automatic failover**
- ✅ **3 sentinel nodes**
- ✅ **Data redundancy**
- Good for: Mission-critical        # Simple Redis
│   ├── redis-statefulset.yaml     # Production Redis with persistence
│   ├── redis-ha.yaml              # Redis HA with Sentinel
│   ├── hpa.yaml
│   ├── argocd/              # ArgoCD GitOps configuration
│   │   ├── application.yaml     # ArgoCD Application CRD
│   │   ├── applicationset.yaml  # Multi-environment setup
│   │   └── install-argocd.yaml  # ArgoCD installation
│   ├── base/                # Kustomize base
│   │   └── kustomization.yaml
│   └── overlays/            # Environment-specific configs
│       ├── development/
│       │   └── kustomization.yaml
│       └── production/
│           └── kustomization.yaml
├── terraform/               # Infrastructure as Code
│   ├── main.tf                 # Provider and variables
│   ├── lke-cluster.tf          # LKE cluster definition
│   ├── database.tf             # PostgreSQL database
│   ├── kubernetes.tf           # K8s resources
│   ├── terraform.tfvars.example
│   ├── helm-values/
│   │   ├── argocd-values.yaml
│   │   └── prometheus-values.yaml
│   └── README.md
├── helm/                    # Helm Charts
│   └── vmshift/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
```bash
# Development environment
kubectl apply -k k8s/overlays/development

# Production environment
kubectl apply -k k8s/overlays/production
```

**Option D: Push to main branch to trigger GitHub Actions**

```bash
git add .
git commit -m "Initial deployment"
git push origin main
```

### Step 5: Access Your Application

```bash
# Get the external IP (if using LoadBalancer)
kubectl get svc -n vmshift

# Or use port-forward for testing
kubectl port-forward svc/vmshift-api-service 8000:80 -n vmshift

# Access API docs
open http://localhost:8000/docs
```

## 📁 Project Structure

```
vmshift-demo/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # SQLAlchemy setup
│   ├── celery_app.py        # Celery configuration
│   ├── models/              # SQLAlchemy models
│   │   ├── vm.py
│   │   └── migration.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── vm.py
│   │   └── migration.py
│   ├── routers/             # API routes
│   │   ├── health.py
│   │   ├── vms.py
│   │   ├── migrations.py
│   │   └── tasks.py
│   ├── tasks/               # Celery tasks
│   │   ├── vm_tasks.py
│   │   └── migration_tasks.py
│   └── services/            # Business logic
│       └── artifact_generator.py
├── k8s/                     # Kubernetes manifests
│   ├── namespace-secrets.yaml
│   ├── api-deployment.yaml
│   ├── celery-deployment.yaml
│   ├── redis-deployment.yaml
│   ├── hpa.yaml
│   ├── argocd/              # ArgoCD GitOps configuration
│   │   ├── application.yaml     # ArgoCD Application CRD
│   │   ├── applicationset.yaml  # Multi-environment setup
│   │   └── install-argocd.yaml  # ArgoCD installation
│   ├── base/                # Kustomize base
│   │   └── kustomization.yaml
│   └── overlays/            # Environment-specific configs
│       ├── development/
│       │   └── kustomization.yaml
│       └── production/
│           └── kustomization.yaml
├── .github/
│   └── workflows/
│       ├── ci-cd.yaml           # Main CI/CD pipeline
│       ├── security.yaml        # Security scanning
│       └── argocd-update.yaml   # GitOps image updates
├── Dockerfile               # API container
├── Dockerfile.celery        # Celery worker container
├── docker-compose.yml       # Local development
├── requirements.txt         # Python dependencies
└── README.md
```

## 🔄 ArgoCD GitOps Workflow

ArgoCD provides declarative, GitOps continuous delivery:

### How It Works

1. **Developer pushes code** → GitHub
2. **GitHub Actions builds** → Docker images pushed to GHCR
3. **Workflow updates** → K8s manifests with new image tags
4. **ArgoCD detects changes** → Auto-syncs to cluster
5. **Self-healing** → Reverts manual cluster changes

### ArgoCD Features Used

| Feature | Description |
|---------|-------------|
| **Auto-Sync** | Automatically deploys when Git changes |
| **Self-Heal** | Reverts manual cluster changes |
| **ApplicationSet** | Multi-environment deployments |
| **Kustomize** | Environment-specific configurations |
| **Health Checks** | Monitors deployment health |
| **Rollback** | One-click rollback to previous version |

### ArgoCD UI Access

```bash
# Port-forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Get admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# Open https://localhost:8080
### Backend & Application
- ✅ **Python** - FastAPI, SQLAlchemy, Pydantic, Celery
- ✅ **PostgreSQL** - Database design, connection pooling, managed databases
- ✅ **Redis** - Message broker, caching, persistence, HA with Sentinel

### Containerization & Orchestration
- ✅ **Docker** - Multi-stage builds, Docker Compose, optimization
- ✅ **Kubernetes** - Deployments, StatefulSets, Services, HPA, ConfigMaps, Secrets, PVCs
- ✅ **Helm** - Chart creation, templating, package management

### Infrastructure & DevOps
- ✅ **Terraform** - Infrastructure as Code, Linode provider, state management
- ✅ **GitOps/ArgoCD** - Declarative deployments, auto-sync, self-healing
- ✅ **Kustomize** - Base + overlays, environment-specific configurations
- ✅ **CI/CD** - GitHub Actions, automated testing, container scanning, image updates

### Cloud & Networking
- ✅ **Akamai/Linode** - LKE (Kubernetes), managed databases, block storage
- ✅ **Ingress/Load Balancing** - NGINX Ingress Controller
- ✅ **TLS/SSL** - Cert-Manager, Let's Encrypt integration

### Monitoring & Observability
- ✅ **Prometheus & Grafana** - Metrics collection, visualization
- ✅ **Health Checks** - Liveness/readiness probes
- ✅ **Logging** - Structured logging, centralized logs

### Architecture & Design
- ✅ **VM Migration** - Discovery, classification, containerization workflows
- ✅ **Microservices** - API-driven architecture, async task processing
- ✅ **High Availability** - Replication, failover, auto-scaling...` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `DEBUG` | Enable debug mode | `false` |

## 📊 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/vms/` | List all VMs |
| POST | `/api/v1/vms/` | Create/register a VM |
| POST | `/api/v1/vms/discover` | Start VM discovery task |
| GET | `/api/v1/migrations/` | List all migrations |
| POST | `/api/v1/migrations/` | Create a migration |
| POST | `/api/v1/migrations/{id}/start` | Start migration |
| GET | `/api/v1/migrations/{id}/artifacts` | Get generated artifacts |
| GET | `/api/v1/tasks/{id}` | Get task status |

## 💰 Cost Estimate (Akamai Cloud)

| Resource | Specification | Monthly Cost |
|----------|--------------|--------------|
| LKE Cluster | 3x Linode 4GB | ~$36 |
| PostgreSQL | Shared 1GB | ~$15 |
| Block Storage | 10GB | ~$1 |
| **Total** | | **~$52/month** |

*$100 free trial covers ~2 months of usage*

## 🧪 Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest tests/ -v --cov=app

# Run with coverage report
pytest tests/ --cov=app --cov-report=html
```

## 📝 Skills Demonstrated

This project demonstrates proficiency in:

- ✅ **Python** - FastAPI, SQLAlchemy, Pydantic, Celery
- ✅ **Docker** - Multi-stage builds, Docker Compose
- ✅ **Kubernetes** - Deployments, Services, HPA, ConfigMaps, Secrets
- ✅ **GitOps/ArgoCD** - Declarative deployments, auto-sync, self-healing
- ✅ **CI/CD** - GitHub Actions, automated testing, container scanning
- ✅ **Kustomize** - Environment-specific Kubernetes configurations
- ✅ **PostgreSQL** - Database design, connection pooling
- ✅ **Redis** - Message broker, result backend
- ✅ **Cloud Platforms** - Akamai/Linode (LKE)
- ✅ **Infrastructure** - VM migration concepts, containerization

## 📄 License

MIT License - feel free to use this as a portfolio project!

---

## 📋 Original Job Requirements Reference

<details>
<summary>Click to expand job requirements this project addresses</summary>

**Key Responsibilities:**

● Design, implement, and maintain core Python services for the backend (APIs, orchestration, automation workflows)
● Build and evolve migration workflows for Windows VMs, including discovery, classification, and containerization logic
● Integrate with VMware environments (vSphere, ESXi, or similar) to collect VM metadata, parse configurations, and generate container artifacts (e.g., Dockerfiles, manifests)
● Develop and optimize containerized environments using Docker / Docker Compose for local development and production-like testing
● Implement and extend deployment functionality targeting container platforms such as OpenShift, Amazon EKS, and Azure AKS, including Windows node scenarios
● Design and optimize queue-based processes and background jobs (Celery or similar) for reliability, observability, and scale
● Ensure consistency and observability across distributed components (logging, metrics, tracing, error handling)
● Contribute to and occasionally extend the React-based UI that interacts with the VMShift backend and repository model
● Collaborate with infrastructure, DevOps, and platform engineers to evolve the overall architecture and harden the product for enterprise use

**Required Skills & Experience:**

● 3+ years of experience in a System Administration, Infrastructure, or Platform Engineering role (priority over pure app-dev backgrounds)
● Strong hands-on experience with Windows Server environments (e.g., IIS, Windows Services, AD-integrated environments, PowerShell automation)
● Practical experience with VMware (vSphere, ESXi, or similar virtualization platforms)
● Strong programming experience in Python (APIs, automation scripts, or services)
● Solid understanding of networking and virtualization fundamentals (e.g., subnets, firewalls/security groups, load balancing, DNS)
● Hands-on experience with Docker and Kubernetes (or OpenShift/EKS/AKS) in production-grade or pre-production environments
● Experience developing and maintaining Celery (or similar) task queues and background worker systems.
● Proficiency with MySQL or a similar relational database (schema design, queries, basic performance tuning)
● Experience with React or another modern frontend framework, and integrating frontend components with REST APIs
● Familiarity with CI/CD pipelines, Git-based workflows, and automation around build/test/deploy

**Preferred Qualifications:**

● Experience building migration, modernization, or infrastructure automation tools (e.g., VM-to-container, lift-and-shift, replatforming)
● Knowledge of Windows containers (Windows base images, process vs. Hyper-V isolation) and containerization of Windows workloads (e.g., IIS, .NET Framework, Windows Services)
● Experience implementing deployment logic or abstractions across multiple clusters or environments (multi-region / multi-account / multi-subscription)
● Exposure to cloud environments (AWS, Azure) including compute services and container registries (e.g., ECR, ACR)
● AWS or cloud certifications are a plus (e.g., AWS Solutions Architect, AWS Developer, Azure Administrator)

</details>