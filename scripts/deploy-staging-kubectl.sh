#!/bin/bash
# Deploy VMShift to production environment using kubectl
# This script manually renders Helm-like templates

NAMESPACE="vmshift-staging"
KUBECONFIG_PATH="../terraform/kubeconfig-production.yaml"

export KUBECONFIG="$KUBECONFIG_PATH"

echo "Deploying VMShift to $NAMESPACE..."

# Create ConfigMap for PostgreSQL init
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init-script
data:
  init.sql: |
    CREATE DATABASE vmshift;
    GRANT ALL PRIVILEGES ON DATABASE vmshift TO postgres;
EOF

# Deploy PostgreSQL
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgresql-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgresql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgresql
  template:
    metadata:
      labels:
        app: postgresql
    spec:
      containers:
      - name: postgresql
        image: postgres:16-alpine
        ports:
        - containerPort: 5432
        env:
        - name: POSTGRES_DB
          value: "vmshift"
        - name: POSTGRES_USER
          value: "postgres"
        - name: POSTGRES_PASSWORD
          value: "postgres123"
        - name: PGDATA
          value: "/var/lib/postgresql/data/pgdata"
        volumeMounts:
        - name: postgresql-storage
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgresql-storage
        persistentVolumeClaim:
          claimName: postgresql-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: postgresql
spec:
  selector:
    app: postgresql
  ports:
    - port: 5432
      targetPort: 5432
EOF

# Deploy Redis
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
spec:
  selector:
    app: redis
  ports:
    - port: 6379
      targetPort: 6379
EOF

echo "Waiting for PostgreSQL and Redis to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/postgresql -n $NAMESPACE
kubectl wait --for=condition=available --timeout=300s deployment/redis -n $NAMESPACE

# Create application secret
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: vmshift-secrets
type: Opaque
stringData:
  DATABASE_URL: "postgresql://postgres:postgres123@postgresql:5432/vmshift"
  REDIS_URL: "redis://redis:6379/0"
  CELERY_BROKER_URL: "redis://redis:6379/0"
  CELERY_RESULT_BACKEND: "redis://redis:6379/1"
  SECRET_KEY: "your-secret-key-change-in-production"
  LINODE_API_TOKEN: "your-linode-token-here"
  SENTRY_DSN: ""
EOF

# Deploy API
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vmshift-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vmshift-api
  template:
    metadata:
      labels:
        app: vmshift-api
    spec:
      containers:
      - name: api
        image: YOUR_DOCKER_IMAGE:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: vmshift-secrets
              key: DATABASE_URL
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: vmshift-secrets
              key: REDIS_URL
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: vmshift-secrets
              key: SECRET_KEY
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: vmshift-api
spec:
  selector:
    app: vmshift-api
  ports:
    - port: 80
      targetPort: 8000
  type: LoadBalancer
EOF

# Deploy Celery Workers
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vmshift-celery-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: vmshift-celery-worker
  template:
    metadata:
      labels:
        app: vmshift-celery-worker
    spec:
      containers:
      - name: celery-worker
        image: YOUR_DOCKER_IMAGE:latest
        command: ["celery"]
        args: ["-A", "app.celery_worker", "worker", "--loglevel=info", "--concurrency=4"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: vmshift-secrets
              key: DATABASE_URL
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: vmshift-secrets
              key: CELERY_BROKER_URL
        - name: CELERY_RESULT_BACKEND
          valueFrom:
            secretKeyRef:
              name: vmshift-secrets
              key: CELERY_RESULT_BACKEND
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
EOF

# Create Ingress
kubectl apply -n $NAMESPACE -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: vmshift-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  ingressClassName: nginx
  rules:
  - host: vmshift.satyamay.tech
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: vmshift-api
            port:
              number: 80
  tls:
  - hosts:
    - vmshift.satyamay.tech
    secretName: vmshift-tls
EOF

echo "Deployment complete!"
echo "Waiting for API to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/vmshift-api -n $NAMESPACE

echo "Getting service status..."
kubectl get pods -n $NAMESPACE
kubectl get svc -n $NAMESPACE

echo ""
echo "Access your application at:"
kubectl get svc vmshift-api -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
