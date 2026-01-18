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

## ☁️ Deploy to Akamai Cloud (LKE)

### Deployment Options

Choose your preferred deployment method:
- **Option 1**: [Terraform (IaC)](#option-1-terraform-iac-recommended) - Fully automated infrastructure provisioning
- **Option 2**: [Manual Setup](#option-2-manual-setup) - Step-by-step using Linode Console
- **Option 3**: [Helm Charts](#option-3-helm-charts) - Kubernetes package manager

---

### Option 1: Terraform (IaC) - Recommended

**Provisions everything in one command!**

```bash
# 1. Get Linode API token from https://cloud.linode.com/profile/tokens
cd terraform

# 2. Configure variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Add your LINODE_TOKEN

# 3. Deploy everything!
terraform init
terraform plan
terraform apply  # Type 'yes'

# ✅ This creates:
#   - LKE Cluster (3 nodes)
#   - PostgreSQL Database (managed)
#   - ArgoCD (GitOps)
#   - Cert-Manager (SSL)
#   - NGINX Ingress
#   - Prometheus & Grafana (monitoring)
#   - All Kubernetes resources

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