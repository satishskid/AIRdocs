# GreyBrain Bank Deployment Guide

This guide provides comprehensive deployment strategies for the GreyBrain Bank AI Model Aggregation Platform.

## 🏗️ Architecture Overview

**GreyBrain Bank** consists of:
- **Backend**: FastAPI server with 88+ AI model integrations
- **Frontend**: Vanilla JavaScript SPA with admin dashboard
- **Database**: File-based JSON storage (easily upgradeable to PostgreSQL/MongoDB)
- **Assets**: Static files, logos, and generated content

## 🚀 Recommended Deployment Platforms

### 🥇 **Option 1: Railway (Recommended for Backend)**

**Why Railway?**
- ✅ Excellent FastAPI support
- ✅ Automatic HTTPS
- ✅ Easy environment variables
- ✅ Built-in monitoring
- ✅ Affordable pricing

**Deployment Steps:**
1. **Connect GitHub repository**
   ```bash
   # Railway will auto-detect FastAPI
   # No additional configuration needed
   ```

2. **Environment Variables**
   ```bash
   PORT=8001
   PYTHONPATH=/app
   API_HOST=0.0.0.0
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

3. **Railway Configuration** (`railway.toml`)
   ```toml
   [build]
   builder = "NIXPACKS"
   
   [deploy]
   startCommand = "cd backend && python app.py"
   healthcheckPath = "/"
   healthcheckTimeout = 300
   restartPolicyType = "ON_FAILURE"
   ```

### 🥈 **Option 2: Vercel (Recommended for Frontend)**

**Why Vercel?**
- ✅ Perfect for static sites
- ✅ Global CDN
- ✅ Automatic deployments
- ✅ Custom domains
- ✅ Free tier available

**Deployment Steps:**
1. **Create `vercel.json`**
   ```json
   {
     "builds": [
       {
         "src": "frontend/**",
         "use": "@vercel/static"
       }
     ],
     "routes": [
       {
         "src": "/(.*)",
         "dest": "/frontend/$1"
       }
     ]
   }
   ```

2. **Deploy**
   ```bash
   npm i -g vercel
   vercel --prod
   ```

### 🥉 **Option 3: DigitalOcean App Platform (Full Stack)**

**Why DigitalOcean?**
- ✅ Full-stack deployment
- ✅ Managed databases
- ✅ Scalable infrastructure
- ✅ Competitive pricing

**App Spec Configuration** (`.do/app.yaml`)
```yaml
name: greybrain-bank
services:
- name: backend
  source_dir: /backend
  github:
    repo: satishskid/greybrain-bank
    branch: main
  run_command: python app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: PORT
    value: "8001"
  - key: API_HOST
    value: "0.0.0.0"
  http_port: 8001
  
- name: frontend
  source_dir: /frontend
  github:
    repo: satishskid/greybrain-bank
    branch: main
  build_command: echo "No build needed"
  run_command: python -m http.server 8080
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8080
```

## 🐳 Docker Deployment

### **Backend Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ .
COPY models/ ./models/
COPY prompts/ ./prompts/

# Create necessary directories
RUN mkdir -p generated_content logs

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/ || exit 1

# Run the application
CMD ["python", "app.py"]
```

### **Frontend Dockerfile**
```dockerfile
FROM nginx:alpine

# Copy frontend files
COPY frontend/ /usr/share/nginx/html/

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### **Docker Compose**
```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    ports:
      - "8001:8001"
    environment:
      - API_HOST=0.0.0.0
      - PORT=8001
      - CORS_ORIGINS=http://localhost:3000
    volumes:
      - ./generated_content:/app/generated_content
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped
```

## ☁️ Cloud Platform Specific Guides

### **AWS Deployment**

#### **Option A: Elastic Beanstalk**
```bash
# Install EB CLI
pip install awsebcli

# Initialize and deploy
eb init greybrain-bank
eb create production
eb deploy
```

#### **Option B: ECS with Fargate**
```yaml
# task-definition.json
{
  "family": "greybrain-bank",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/greybrain-bank:latest",
      "portMappings": [
        {
          "containerPort": 8001,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/greybrain-bank",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### **Google Cloud Platform**

#### **Cloud Run Deployment**
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/greybrain-bank
gcloud run deploy --image gcr.io/PROJECT-ID/greybrain-bank --platform managed
```

#### **App Engine**
```yaml
# app.yaml
runtime: python39

env_variables:
  API_HOST: "0.0.0.0"
  PORT: "8080"

automatic_scaling:
  min_instances: 1
  max_instances: 10
  target_cpu_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 0.5
  disk_size_gb: 10
```

### **Azure Deployment**

#### **Container Instances**
```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name greybrain-bank \
  --image your-registry/greybrain-bank:latest \
  --dns-name-label greybrain-bank \
  --ports 8001
```

## 🔧 Environment Configuration

### **Production Environment Variables**
```bash
# API Configuration
API_HOST=0.0.0.0
PORT=8001
DEBUG=false
ENVIRONMENT=production

# CORS Configuration
CORS_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Security
ADMIN_API_KEY=your-secure-admin-key-here
SECRET_KEY=your-secret-key-for-sessions

# AI Model Configuration
MODEL_DISCOVERY_INTERVAL=300
HEALTH_CHECK_INTERVAL=60
MAX_CONCURRENT_REQUESTS=100

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/greybrain-bank.log

# Performance
WORKERS=4
TIMEOUT=300
KEEPALIVE=2

# Database (if using external DB)
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0

# File Storage
UPLOAD_PATH=/app/uploads
MAX_FILE_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=pdf,docx,txt,md

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
```

### **Development Environment**
```bash
# .env.development
API_HOST=localhost
PORT=8001
DEBUG=true
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
LOG_LEVEL=DEBUG
```

## 🔒 Security Configuration

### **SSL/TLS Setup**
```nginx
# nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://backend:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **API Security**
```python
# Security headers middleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["your-domain.com"])
app.add_middleware(HTTPSRedirectMiddleware)
```

## 📊 Monitoring & Logging

### **Health Checks**
```python
# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "models_count": len(ai_models),
        "uptime": get_uptime()
    }
```

### **Logging Configuration**
```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('logs/greybrain-bank.log', maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
```

### **Prometheus Metrics**
```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

## 🚀 CI/CD Pipeline

### **GitHub Actions**
```yaml
# .github/workflows/deploy.yml
name: Deploy GreyBrain Bank

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt
    - name: Run tests
      run: |
        cd backend
        python -m pytest tests/

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Deploy to Railway
      uses: railway-app/railway-action@v1
      with:
        api-token: ${{ secrets.RAILWAY_TOKEN }}
        service: greybrain-bank-backend
```

## 📈 Performance Optimization

### **Backend Optimization**
```python
# Async optimization
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Connection pooling
import aiohttp

# Caching
from functools import lru_cache
import redis

@lru_cache(maxsize=128)
def get_model_config(model_name: str):
    # Cache model configurations
    pass
```

### **Frontend Optimization**
```javascript
// Service Worker for caching
// sw.js
const CACHE_NAME = 'greybrain-bank-v1';
const urlsToCache = [
  '/',
  '/admin-dashboard.html',
  '/assets/logo.svg'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});
```

## 🔄 Backup & Recovery

### **Database Backup**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup JSON files
tar -czf "$BACKUP_DIR/models_$DATE.tar.gz" models/
tar -czf "$BACKUP_DIR/prompts_$DATE.tar.gz" prompts/

# Upload to cloud storage
aws s3 cp "$BACKUP_DIR/" s3://your-backup-bucket/ --recursive
```

### **Disaster Recovery**
```bash
#!/bin/bash
# restore.sh
BACKUP_FILE=$1

# Restore from backup
tar -xzf "$BACKUP_FILE" -C /app/

# Restart services
docker-compose restart
```

---

**🎉 Your GreyBrain Bank platform is now ready for production deployment!**

*For additional support, contact: support@greybrain.ai*
