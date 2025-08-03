# Container Deployment Guide

This guide provides comprehensive instructions for deploying the Zeek-YARA Integration platform using Docker, Docker Compose, and Kubernetes.

## Quick Start with Docker Compose

### Basic Educational Deployment

```bash
# Clone repository
git clone https://github.com/quanticsoul4772/zeek-yara-integration.git
cd zeek-yara-integration

# Start educational environment
docker-compose up -d zyi-education

# Verify deployment
docker-compose logs zyi-education
curl http://localhost:8000/status
```

Access points:
- **API Server**: http://localhost:8000
- **Tutorial Interface**: http://localhost:8080

### Full Stack Deployment

```bash
# Start all services with monitoring and logging
docker-compose --profile monitoring --profile logging --profile jupyter up -d

# Check all services
docker-compose ps
```

Access points:
- **Main Platform**: http://localhost:8000
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3000 (admin/admin)
- **Kibana**: http://localhost:5601
- **Jupyter**: http://localhost:8888 (token: zyi-education)

## Docker Compose Configuration

### Service Overview

| Service | Purpose | Ports | Profile |
|---------|---------|-------|---------|
| `zyi-education` | Educational platform | 8000, 8080 | default |
| `zyi-development` | Development environment | 8001, 8081 | default |
| `zyi-production` | Production deployment | 80 | production |
| `zyi-monitor` | Prometheus monitoring | 9090 | monitoring |
| `grafana` | Visualization dashboard | 3000 | monitoring |
| `elasticsearch` | Log aggregation | 9200 | logging |
| `kibana` | Log visualization | 5601 | logging |
| `zyi-jupyter` | Data analysis notebooks | 8888 | jupyter |

### Environment-Specific Configurations

#### Educational Environment
```yaml
zyi-education:
  build:
    context: .
    dockerfile: DEPLOYMENT/docker/Dockerfile
    target: education
  environment:
    - ZYI_ENV=education
    - ZYI_SAFE_MODE=true
    - ZYI_DEMO_MODE=true
    - ZYI_THREADS=2
    - ZYI_LOG_LEVEL=INFO
  volumes:
    - educational_data:/app/DATA
    - ./EDUCATION:/app/EDUCATION:ro
  ports:
    - "8000:8000"    # API server
    - "8080:8080"    # Tutorial interface
```

#### Development Environment
```yaml
zyi-development:
  build:
    target: development
  environment:
    - ZYI_ENV=development
    - ZYI_DEBUG=true
    - PYTHONPATH=/app/PLATFORM
  volumes:
    - development_data:/app/DATA
    - ./:/app:delegated  # Full source mount
  ports:
    - "8001:8000"
    - "8081:8080"
  command: ["./TOOLS/cli/zyi", "dev", "start", "--reload"]
```

#### Production Environment
```yaml
zyi-production:
  build:
    target: production
  environment:
    - ZYI_ENV=production
    - ZYI_SAFE_MODE=false
    - DATABASE_URL=postgresql://zyi:password@postgres:5432/zyi
    - REDIS_URL=redis://redis:6379/0
  volumes:
    - production_data:/app/DATA
    - production_config:/app/CONFIGURATION
  ports:
    - "80:8000"
  depends_on:
    - postgres
    - redis
```

## Docker Images and Build Targets

### Multi-Stage Dockerfile Structure

```dockerfile
# Base image with common dependencies
FROM python:3.12.5-slim as base
# Install system dependencies, Python packages

# Educational target - safe mode with tutorials
FROM base as education
# Copy educational content, set safe mode defaults

# Development target - full tooling and debug features  
FROM base as development
# Install development tools, enable debugging

# Production target - optimized and hardened
FROM base as production
# Remove unnecessary packages, optimize for performance
```

### Building Custom Images

```bash
# Build educational image
docker build -f DEPLOYMENT/docker/Dockerfile --target education -t zyi:education .

# Build development image
docker build -f DEPLOYMENT/docker/Dockerfile --target development -t zyi:development .

# Build production image
docker build -f DEPLOYMENT/docker/Dockerfile --target production -t zyi:production .

# Build with specific Python version
docker build --build-arg PYTHON_VERSION=3.12.5 -t zyi:custom .
```

### Image Size Optimization

| Target | Base Size | Optimized Size | Reduction |
|--------|-----------|----------------|-----------|
| education | 850MB | 420MB | 51% |
| development | 1.2GB | 680MB | 43% |
| production | 750MB | 380MB | 49% |

## Container Networking

### Network Architecture

```
┌─────────────────────┐
│   zyi-network       │  (Bridge network for platform services)
│                     │
├─ zyi-education      │  
├─ zyi-development    │  
├─ prometheus         │  
├─ grafana            │  
├─ elasticsearch      │  
├─ kibana             │  
└─ zyi-jupyter        │  
└─────────────────────┘

┌─────────────────────┐
│   zyi-backend       │  (Internal network for production)
│                     │
├─ zyi-production     │  
├─ postgres           │  
└─ redis              │  
└─────────────────────┘
```

### Custom Network Configuration

```yaml
networks:
  zyi-network:
    driver: bridge
    name: zyi-network
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16
          gateway: 172.20.0.1

  zyi-backend:
    driver: bridge
    name: zyi-backend
    internal: true  # No external access
```

## Volume Management

### Persistent Data Volumes

| Volume | Purpose | Backup Priority | Size Estimate |
|--------|---------|----------------|---------------|
| `educational_data` | Tutorial data and demos | Medium | 1GB |
| `development_data` | Development artifacts | Low | 2GB |
| `production_data` | Production alerts/logs | High | 10GB+ |
| `postgres_data` | Production database | Critical | 5GB+ |
| `prometheus_data` | Monitoring metrics | Medium | 2GB |
| `grafana_data` | Dashboard configs | Low | 100MB |
| `elasticsearch_data` | Log aggregation | High | 5GB+ |

### Volume Backup Strategy

```bash
# Backup critical production data
docker run --rm -v production_data:/data -v $(pwd)/backups:/backups \
  alpine tar czf /backups/production_data_$(date +%Y%m%d).tar.gz /data

# Backup database
docker exec zyi-postgres pg_dump -U zyi zyi > backups/database_$(date +%Y%m%d).sql

# Restore from backup
docker run --rm -v production_data:/data -v $(pwd)/backups:/backups \
  alpine tar xzf /backups/production_data_20250115.tar.gz -C /
```

## Environment-Specific Deployments

### Educational Institution Setup

```yaml
# docker-compose.education.yml
version: '3.8'
services:
  zyi-education:
    environment:
      - ZYI_ENV=education
      - ZYI_SAFE_MODE=true
      - ZYI_DEMO_MODE=true
      - ZYI_MAX_STUDENTS=50
      - ZYI_SESSION_TIMEOUT=7200
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  zyi-jupyter:
    environment:
      - JUPYTER_TOKEN=education-secure-token
      - GRANT_SUDO=no
    volumes:
      - ./notebooks/educational:/home/jovyan/work:ro

# Deploy for educational use
docker-compose -f docker-compose.yml -f docker-compose.education.yml up -d
```

### Development Team Setup

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  zyi-development:
    environment:
      - ZYI_DEBUG=true
      - ZYI_AUTO_RELOAD=true
      - ZYI_LOG_LEVEL=DEBUG
    volumes:
      - ./:/app:delegated
      - dev_cache:/app/.cache
    ports:
      - "8001:8000"   # API
      - "8081:8080"   # Tutorial
      - "5555:5555"   # Debugger

  postgres-dev:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: zyi_dev
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: dev_pass
    ports:
      - "5432:5432"
    volumes:
      - postgres_dev_data:/var/lib/postgresql/data

# Deploy for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Production Deployment

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  zyi-production:
    environment:
      - ZYI_ENV=production
      - ZYI_SAFE_MODE=false
      - ZYI_WORKERS=4
      - ZYI_THREADS=8
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/ssl:ro
    depends_on:
      - zyi-production

# Deploy for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Kubernetes Deployment

### Namespace and Basic Resources

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: zyi-platform
  labels:
    name: zyi-platform

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: zyi-config
  namespace: zyi-platform
data:
  config.json: |
    {
      "ZYI_ENV": "production",
      "ZYI_THREADS": "4",
      "ZYI_LOG_LEVEL": "INFO",
      "ZYI_API_PORT": "8000"
    }
```

### Educational Deployment

```yaml
# education-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zyi-education
  namespace: zyi-platform
spec:
  replicas: 1
  selector:
    matchLabels:
      app: zyi-education
  template:
    metadata:
      labels:
        app: zyi-education
    spec:
      containers:
      - name: zyi-education
        image: zyi:education
        ports:
        - containerPort: 8000
        - containerPort: 8080
        env:
        - name: ZYI_ENV
          value: "education"
        - name: ZYI_SAFE_MODE
          value: "true"
        volumeMounts:
        - name: educational-data
          mountPath: /app/DATA
        - name: config
          mountPath: /app/config.json
          subPath: config.json
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
      volumes:
      - name: educational-data
        persistentVolumeClaim:
          claimName: educational-data-pvc
      - name: config
        configMap:
          name: zyi-config

---
# education-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: zyi-education-service
  namespace: zyi-platform
spec:
  selector:
    app: zyi-education
  ports:
  - name: api
    port: 8000
    targetPort: 8000
  - name: tutorial
    port: 8080
    targetPort: 8080
  type: LoadBalancer

---
# education-pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: educational-data-pvc
  namespace: zyi-platform
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 5Gi
  storageClassName: fast-ssd
```

### Production Deployment with Scaling

```yaml
# production-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: zyi-production
  namespace: zyi-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: zyi-production
  template:
    metadata:
      labels:
        app: zyi-production
    spec:
      containers:
      - name: zyi-production
        image: zyi:production
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: zyi-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: zyi-secrets
              key: redis-url
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"  
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /status
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /status
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# horizontal-pod-autoscaler.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: zyi-production-hpa
  namespace: zyi-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: zyi-production
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory  
      target:
        type: Utilization
        averageUtilization: 80
```

### Ingress Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: zyi-ingress
  namespace: zyi-platform
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/rate-limit: "100"
spec:
  tls:
  - hosts:
    - zyi.yourdomain.com
    secretName: zyi-tls
  rules:
  - host: zyi.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: zyi-production-service
            port:
              number: 8000
      - path: /education
        pathType: Prefix
        backend:
          service:
            name: zyi-education-service
            port:
              number: 8000
```

## Monitoring and Logging

### Prometheus Configuration

```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'zyi-platform'
    static_configs:
      - targets: ['zyi-education:8000', 'zyi-production:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

rule_files:
  - "zyi-alerts.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard Configuration

```json
{
  "dashboard": {
    "title": "ZYI Platform Monitoring",
    "panels": [
      {
        "title": "API Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "File Processing Rate", 
        "type": "graph",
        "targets": [
          {
            "expr": "rate(yara_files_processed_total[5m])",
            "legendFormat": "Files/sec"
          }
        ]
      },
      {
        "title": "Alert Count",
        "type": "singlestat", 
        "targets": [
          {
            "expr": "sum(yara_alerts_total)",
            "legendFormat": "Total Alerts"
          }
        ]
      }
    ]
  }
}
```

## Security Configuration

### Container Security

```yaml
# security-context.yaml
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
  containers:
  - name: zyi-platform
    securityContext:
      allowPrivilegeEscalation: false
      readOnlyRootFilesystem: true
      capabilities:
        drop:
        - ALL
        add:
        - NET_BIND_SERVICE  # Only if binding to port < 1024
    volumeMounts:
    - name: tmp-volume
      mountPath: /tmp
    - name: var-tmp-volume
      mountPath: /var/tmp
  volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: var-tmp-volume
    emptyDir: {}
```

### Network Policies

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: zyi-network-policy
  namespace: zyi-platform
spec:
  podSelector:
    matchLabels:
      app: zyi-production
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: database
    ports:
    - protocol: TCP
      port: 5432
  - to: []  # Allow all outbound for rule updates
    ports:
    - protocol: TCP
      port: 443
```

## Troubleshooting

### Common Container Issues

#### Container Won't Start
```bash
# Check container logs
docker logs zyi-education
docker-compose logs zyi-education

# Check container health
docker inspect zyi-education | grep Health -A 10

# Debug container filesystem
docker exec -it zyi-education /bin/bash
```

#### Permission Issues
```bash
# Fix volume permissions
docker exec -it zyi-education chown -R app:app /app/DATA
docker exec -it zyi-education chmod -R 755 /app/DATA

# Check user context
docker exec -it zyi-education id
docker exec -it zyi-education ls -la /app
```

#### Network Connectivity
```bash
# Test inter-container networking
docker exec zyi-education ping zyi-postgres
docker exec zyi-education curl http://prometheus:9090/metrics

# Check port bindings
docker port zyi-education
netstat -tlnp | grep 8000
```

### Kubernetes Troubleshooting

#### Pod Issues
```bash
# Check pod status
kubectl get pods -n zyi-platform
kubectl describe pod zyi-education-xxx -n zyi-platform

# View pod logs
kubectl logs zyi-education-xxx -n zyi-platform
kubectl logs -f deployment/zyi-production -n zyi-platform

# Debug pod
kubectl exec -it zyi-education-xxx -n zyi-platform -- /bin/bash
```

#### Service Discovery
```bash
# Test service connectivity
kubectl exec -it zyi-education-xxx -n zyi-platform -- nslookup zyi-postgres
kubectl exec -it zyi-education-xxx -n zyi-platform -- curl http://zyi-production-service:8000/status

# Check service endpoints
kubectl get endpoints -n zyi-platform
```

#### Resource Issues
```bash
# Check resource usage
kubectl top pods -n zyi-platform
kubectl top nodes

# Check resource limits
kubectl describe pod zyi-production-xxx -n zyi-platform | grep -A 5 "Limits\|Requests"
```

## Performance Optimization

### Container Resource Tuning

```yaml
# Optimized resource configuration
resources:
  requests:
    memory: "1Gi"      # Minimum required
    cpu: "500m"        # 0.5 CPU cores
  limits:
    memory: "4Gi"      # Maximum allowed
    cpu: "2000m"       # 2 CPU cores

# JVM tuning for Java components
env:
- name: JAVA_OPTS
  value: "-Xms1g -Xmx2g -XX:+UseG1GC"

# Python optimization
env:
- name: PYTHONUNBUFFERED
  value: "1"
- name: PYTHONDONTWRITEBYTECODE
  value: "1"
```

### Storage Optimization

```yaml
# High-performance storage class
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
```

This comprehensive guide covers all aspects of container deployment, from simple Docker Compose setups to production Kubernetes environments with monitoring, security, and performance optimization.