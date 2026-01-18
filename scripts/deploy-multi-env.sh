#!/bin/bash
# Multi-Environment Setup Script for VMShift
# This script deploys all three environments (dev, staging, prod)

set -e

echo "🚀 VMShift Multi-Environment Setup"
echo "===================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found. Please install kubectl first.${NC}"
    exit 1
fi

if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm not found. Please install Helm first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

# Function to deploy environment
deploy_environment() {
    local ENV=$1
    local NAMESPACE="vmshift-$ENV"
    local VALUES_FILE="helm/vmshift/values-$ENV.yaml"
    
    echo -e "${YELLOW}📦 Deploying $ENV environment...${NC}"
    
    # Create namespace
    echo "  → Creating namespace: $NAMESPACE"
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Create GHCR secret
    echo "  → Creating image pull secret"
    read -p "  Enter GitHub username: " GITHUB_USER
    read -sp "  Enter GitHub PAT: " GITHUB_PAT
    echo ""
    
    kubectl delete secret ghcr-secret -n $NAMESPACE --ignore-not-found
    kubectl create secret docker-registry ghcr-secret \
        --docker-server=ghcr.io \
        --docker-username=$GITHUB_USER \
        --docker-password=$GITHUB_PAT \
        -n $NAMESPACE
    
    # Create database secrets
    echo "  → Creating database secrets"
    DB_NAME="vmshift_$ENV"
    DB_USER="vmshift_${ENV}_user"
    read -sp "  Enter database password for $ENV: " DB_PASSWORD
    echo ""
    
    kubectl delete secret vmshift-secrets -n $NAMESPACE --ignore-not-found
    kubectl create secret generic vmshift-secrets \
        --from-literal=database-url="postgresql://${DB_USER}:${DB_PASSWORD}@postgresql:5432/${DB_NAME}" \
        --from-literal=redis-url="redis://redis:6379/0" \
        --from-literal=celery-broker="redis://redis:6379/0" \
        --from-literal=celery-backend="redis://redis:6379/0" \
        -n $NAMESPACE
    
    # Deploy with Helm
    echo "  → Deploying with Helm"
    helm upgrade --install vmshift-$ENV ./helm/vmshift \
        --namespace $NAMESPACE \
        --values $VALUES_FILE \
        --set image.tag=latest \
        --wait \
        --timeout 10m
    
    echo -e "${GREEN}✓ $ENV environment deployed successfully${NC}"
    echo ""
}

# Deploy ArgoCD applications
deploy_argocd_apps() {
    echo -e "${YELLOW}🔄 Deploying ArgoCD applications...${NC}"
    
    if kubectl get namespace argocd &> /dev/null; then
        kubectl apply -f k8s/argocd/application-dev.yaml
        kubectl apply -f k8s/argocd/application-staging.yaml
        kubectl apply -f k8s/argocd/application-prod.yaml
        echo -e "${GREEN}✓ ArgoCD applications created${NC}"
    else
        echo -e "${YELLOW}⚠ ArgoCD namespace not found. Skipping ArgoCD setup.${NC}"
        echo "  Install ArgoCD first, then run: kubectl apply -f k8s/argocd/"
    fi
    echo ""
}

# Main menu
echo "Select deployment option:"
echo "1) Deploy all environments (dev, staging, prod)"
echo "2) Deploy development only"
echo "3) Deploy staging only"
echo "4) Deploy production only"
echo "5) Setup ArgoCD applications"
echo "6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        deploy_environment "dev"
        deploy_environment "staging"
        deploy_environment "prod"
        deploy_argocd_apps
        ;;
    2)
        deploy_environment "dev"
        ;;
    3)
        deploy_environment "staging"
        ;;
    4)
        deploy_environment "prod"
        ;;
    5)
        deploy_argocd_apps
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

# Summary
echo ""
echo "═══════════════════════════════════════════"
echo "🎉 Deployment Summary"
echo "═══════════════════════════════════════════"
echo ""

if kubectl get namespace vmshift-dev &> /dev/null; then
    echo -e "${GREEN}Development:${NC}"
    echo "  Namespace: vmshift-dev"
    echo "  URL: https://vmshift-dev.satyamay.tech"
    kubectl get pods -n vmshift-dev 2>/dev/null || echo "  (Not yet deployed)"
    echo ""
fi

if kubectl get namespace vmshift-staging &> /dev/null; then
    echo -e "${GREEN}Staging:${NC}"
    echo "  Namespace: vmshift-staging"
    echo "  URL: https://vmshift-staging.satyamay.tech"
    kubectl get pods -n vmshift-staging 2>/dev/null || echo "  (Not yet deployed)"
    echo ""
fi

if kubectl get namespace vmshift-production &> /dev/null; then
    echo -e "${GREEN}Production:${NC}"
    echo "  Namespace: vmshift-production"
    echo "  URL: https://vmshift.satyamay.tech"
    kubectl get pods -n vmshift-production 2>/dev/null || echo "  (Not yet deployed)"
    echo ""
fi

echo "═══════════════════════════════════════════"
echo ""
echo "📚 Useful commands:"
echo ""
echo "  # Check all environments"
echo "  kubectl get pods -A | grep vmshift"
echo ""
echo "  # View specific environment"
echo "  kubectl get all -n vmshift-dev"
echo "  kubectl get all -n vmshift-staging"
echo "  kubectl get all -n vmshift-production"
echo ""
echo "  # Follow logs"
echo "  kubectl logs -f deployment/vmshift-api -n vmshift-dev"
echo ""
echo "  # Access API"
echo "  curl https://vmshift-dev.satyamay.tech/health"
echo ""
echo "For more information, see: docs/MULTI-ENVIRONMENT.md"
echo ""
