# Screenshots Guide

This directory contains screenshots for the VMShift deployment documentation.

## 📸 Required Screenshots

### 1. Prerequisites & Setup
- **01-akamai-api-token.png** - Akamai Cloud Console showing API token creation
- **02-terraform-config.png** - Terraform configuration file with variables

### 2. Infrastructure Deployment
- **03-terraform-apply.png** - Terminal showing `terraform apply` output
- **04-cluster-info.png** - `kubectl cluster-info` and `kubectl get nodes` output

### 3. GitHub Configuration
- **05-github-pat.png** - GitHub Personal Access Token creation page
- **06-github-secrets.png** - GitHub repository secrets page with KUBECONFIG, ARGOCD_AUTH_TOKEN, GHCR_PAT
- **08-github-packages.png** - GitHub Container Registry packages (vmshift-api, vmshift-celery)

### 4. Helm Deployment
- **07-helm-values.png** - Helm values.yaml configuration
- **09-helm-install.png** - Terminal showing `helm upgrade --install` command output

### 5. CI/CD Pipeline
- **10-github-actions.png** - GitHub Actions workflow running successfully
- **11-pod-status.png** - `kubectl get pods -n vmshift` showing all pods running
- **12-services-ingress.png** - `kubectl get svc,ingress -n vmshift` output

### 6. Monitoring & Management
- **13-argocd-dashboard.png** - ArgoCD UI showing synced applications
- **14-grafana-metrics.png** - Grafana dashboard with Kubernetes/application metrics
- **15-dns-config.png** - DNS provider showing A record configuration
- **20-prometheus-queries.png** - Prometheus UI with sample queries

### 7. Application Testing
- **16-app-running.png** - Browser showing application homepage with SSL
- **17-api-docs.png** - FastAPI Swagger UI documentation page
- **18-create-vm.png** - API request creating a VM in Swagger UI
- **19-migration-workflow.png** - API showing migration workflow status

### 8. Architecture Diagrams
- **architecture.png** - Complete system architecture diagram (can be created with draw.io, lucidchart, or excalidraw)

---

## 🎨 Screenshot Guidelines

### How to Take Good Screenshots

1. **High Resolution**: Use at least 1920x1080 resolution
2. **Clean Interface**: Close unnecessary tabs/windows
3. **Highlight Important Parts**: Use arrows or boxes to highlight key areas
4. **Remove Sensitive Data**: Blur/redact any passwords, tokens, or personal information
5. **Consistent Theme**: Use the same terminal/browser theme across screenshots
6. **Include Context**: Show enough of the UI to understand what you're doing

### Recommended Tools

- **Windows**: Snipping Tool, Greenshot, ShareX
- **Mac**: Cmd+Shift+4, CleanShot X
- **Linux**: Flameshot, GNOME Screenshot, Spectacle
- **Browser**: Firefox Screenshot, Chrome DevTools
- **Annotation**: Snagit, Skitch, Ksnip

### Example Commands to Capture

```bash
# Terminal screenshots with clean output
kubectl get pods -n vmshift
kubectl get svc,ingress -n vmshift
kubectl describe pod <pod-name> -n vmshift
helm list -n vmshift
terraform output

# Make terminal readable
export PS1='\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
clear  # Clear before taking screenshot
```

---

## 📝 Screenshot Checklist

Use this checklist when preparing your project showcase:

### Infrastructure
- [ ] Akamai Cloud Console - Cluster overview
- [ ] Akamai Cloud Console - API token page
- [ ] Terraform init/plan/apply output
- [ ] Kubernetes cluster info and nodes

### GitHub Setup
- [ ] Personal Access Token creation
- [ ] Repository secrets configuration
- [ ] GitHub Actions workflow running
- [ ] GitHub Actions workflow success
- [ ] GHCR packages (public)

### Deployment
- [ ] Helm values configuration
- [ ] Helm install output
- [ ] All pods running (2/2, 1/1 ready)
- [ ] Services and Ingress with external IPs

### GitOps & Monitoring
- [ ] ArgoCD login page
- [ ] ArgoCD applications synced
- [ ] Grafana dashboard with metrics
- [ ] Prometheus queries

### Application
- [ ] Application homepage with SSL
- [ ] Swagger UI documentation
- [ ] API request/response example
- [ ] Celery worker logs processing tasks

### DNS & SSL
- [ ] DNS A record configuration
- [ ] SSL certificate valid (browser padlock)
- [ ] cert-manager certificate ready

---

## 🎬 Creating Architecture Diagram

### Using Draw.io (Recommended)

1. Go to [diagrams.net](https://app.diagrams.net/)
2. Choose "Blank Diagram"
3. Use these icons:
   - **Kubernetes**: Pod, Deployment, Service, Ingress
   - **Cloud**: Akamai/Linode logo
   - **Databases**: PostgreSQL, Redis cylinders
   - **Tools**: GitHub, ArgoCD, Prometheus, Grafana logos
   - **Arrows**: Show data flow and relationships

4. Save as PNG: **File → Export as → PNG**

### Recommended Layout

```
[GitHub] → [GitHub Actions] → [GHCR]
                ↓
           [ArgoCD] ← [Git Repository]
                ↓
        [Kubernetes Cluster]
           ├─ [NGINX Ingress] → [LoadBalancer]
           ├─ [FastAPI Pods]
           ├─ [Celery Workers]
           ├─ [PostgreSQL]
           └─ [Redis]
                ↓
        [Prometheus/Grafana]
```

### Color Scheme
- **Blue**: Kubernetes resources
- **Green**: Healthy/running components
- **Purple**: External services (GitHub, Akamai)
- **Orange**: Monitoring/observability
- **Gray**: Databases/storage

---

## 💡 Tips for Portfolio/Resume

When showcasing this project:

1. **README First**: Well-documented README is as important as the code
2. **Live Demo**: Include links to live application (if still running)
3. **Video Walkthrough**: 2-3 minute Loom/YouTube video demonstrating features
4. **Blog Post**: Write about challenges faced and how you solved them
5. **LinkedIn Post**: Share your deployment journey with screenshots
6. **GitHub Stars**: Keep README updated to attract stars/forks

### Example Portfolio Description

> **VMShift - Cloud-Native VM Migration Platform**
> 
> Architected and deployed a production-grade microservices application on Akamai Cloud using Kubernetes, demonstrating expertise in:
> - Infrastructure as Code (Terraform)
> - GitOps with ArgoCD
> - CI/CD pipelines (GitHub Actions)
> - Container orchestration (Kubernetes, Helm)
> - Observability (Prometheus, Grafana)
> - Cloud platforms (Akamai/Linode LKE)
> 
> **Tech Stack**: Python, FastAPI, Celery, PostgreSQL, Redis, Docker, Kubernetes, Terraform, ArgoCD, Helm
> 
> 🔗 [Live Demo](https://vmshift.yourdomain.com) | [GitHub](https://github.com/username/vmshift) | [Blog Post](https://yourblog.com/vmshift)

---

## 📤 Next Steps

1. Take all required screenshots during deployment
2. Store them in this directory with the exact filenames listed above
3. Optionally compress images: `mogrify -resize 1920x1080 -quality 85 *.png`
4. Commit screenshots: `git add docs/screenshots/ && git commit -m "Add deployment screenshots"`
5. Push to GitHub: `git push origin main`
6. Share your project on LinkedIn, Twitter, or Dev.to!
