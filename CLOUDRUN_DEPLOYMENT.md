# 🚀 AIRDOCS - Google Cloud Run Deployment Guide

## Why Google Cloud Run is Perfect for AIRDOCS

✅ **Generous Free Tier**: 2 million requests/month, 400,000 GB-seconds  
✅ **Serverless Auto-scaling**: Scales to zero when not used (saves money)  
✅ **Production-Ready**: Enterprise-grade infrastructure  
✅ **Global Performance**: Google's worldwide network  
✅ **Easy CI/CD**: Automatic deployments from GitHub  

## 🚀 Quick Deployment (5 Minutes)

### Prerequisites
1. **Google Cloud Account**: [cloud.google.com](https://cloud.google.com) (free $300 credit)
2. **Google Cloud SDK**: [Install gcloud CLI](https://cloud.google.com/sdk/docs/install)
3. **Docker**: [Install Docker](https://docs.docker.com/get-docker/) (optional)

### Step 1: Setup Google Cloud Project

```bash
# Login to Google Cloud
gcloud auth login

# Create new project (or use existing)
gcloud projects create airdocs-beta --name="AIRDOCS Beta"

# Set as default project
gcloud config set project airdocs-beta

# Enable billing (required for Cloud Run)
# Go to: https://console.cloud.google.com/billing
```

### Step 2: One-Command Deployment

```bash
# Clone your repository
git clone https://github.com/satishskid/AIRdocs.git
cd AIRdocs

# Run deployment script
./deploy-cloudrun.sh
```

**That's it!** AIRDOCS will be live in ~5 minutes.

---

## 🔧 Manual Deployment Steps

### Step 1: Enable APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### Step 2: Deploy to Cloud Run
```bash
gcloud run deploy airdocs \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10
```

### Step 3: Set Environment Variables
```bash
gcloud run services update airdocs \
    --region us-central1 \
    --set-env-vars="ENVIRONMENT=production,DEBUG=false,API_HOST=0.0.0.0,ADMIN_API_KEY=airdocs-cloudrun-admin-2024"
```

---

## 💾 Redis Setup (Recommended)

### Option 1: Google Cloud Memorystore (Managed Redis)
```bash
# Create Redis instance
gcloud redis instances create airdocs-redis \
    --size=1 \
    --region=us-central1 \
    --redis-version=redis_6_x

# Get Redis IP
REDIS_IP=$(gcloud redis instances describe airdocs-redis --region=us-central1 --format='value(host)')

# Update Cloud Run with Redis URL
gcloud run services update airdocs \
    --region us-central1 \
    --set-env-vars="REDIS_URL=redis://$REDIS_IP:6379"
```

### Option 2: External Redis (Free Options)
- **Redis Cloud**: Free 30MB tier
- **Upstash**: Serverless Redis with generous free tier
- **Railway Redis**: Free tier available

---

## 🔐 Environment Variables Configuration

### Core Variables (Required)
```bash
gcloud run services update airdocs \
    --region us-central1 \
    --set-env-vars="
API_HOST=0.0.0.0,
ENVIRONMENT=production,
DEBUG=false,
ADMIN_API_KEY=airdocs-cloudrun-admin-2024,
TOKEN_ENCRYPTION_KEY=airdocs-cloudrun-encryption-2024
"
```

### Payment Integration (Stripe)
```bash
gcloud run services update airdocs \
    --region us-central1 \
    --set-env-vars="
STRIPE_SECRET_KEY=sk_test_your_stripe_key,
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret,
FRONTEND_URL=https://your-service-url.run.app
"
```

### AI Service API Keys
```bash
gcloud run services update airdocs \
    --region us-central1 \
    --set-env-vars="
OPENAI_API_KEY=sk-your-openai-key,
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key,
PERPLEXITY_API_KEY=pplx-your-perplexity-key
"
```

---

## 🌐 Custom Domain Setup

### Step 1: Map Domain
```bash
gcloud run domain-mappings create \
    --service airdocs \
    --domain your-domain.com \
    --region us-central1
```

### Step 2: Configure DNS
Add the provided DNS records to your domain registrar.

---

## 📊 Monitoring & Scaling

### View Logs
```bash
gcloud run services logs read airdocs --region us-central1
```

### Scale Configuration
```bash
gcloud run services update airdocs \
    --region us-central1 \
    --min-instances 0 \
    --max-instances 100 \
    --cpu 2 \
    --memory 2Gi
```

### Traffic Allocation (Blue/Green Deployments)
```bash
gcloud run services update-traffic airdocs \
    --region us-central1 \
    --to-revisions LATEST=100
```

---

## 💰 Cost Optimization

### Free Tier Limits
- **Requests**: 2 million/month
- **CPU Time**: 400,000 GB-seconds/month
- **Memory**: Included in CPU time
- **Bandwidth**: 1GB/month

### Beyond Free Tier
- **Requests**: $0.40 per million
- **CPU**: $0.00002400 per GB-second
- **Memory**: $0.00000250 per GB-second

### Cost Optimization Tips
1. **Scale to Zero**: Automatic when no traffic
2. **Right-size Resources**: Start with 1 CPU, 1GB RAM
3. **Use Caching**: Redis reduces compute time
4. **Monitor Usage**: Cloud Console provides detailed metrics

---

## 🧪 Beta Testing URLs

After deployment, your AIRDOCS will be available at:
- **Service URL**: `https://airdocs-[hash].run.app`
- **API Documentation**: `/docs`
- **Beta Interface**: `/beta-test.html`
- **System Health**: `/health`
- **Pricing Plans**: `/payments/pricing`
- **AI Services**: `/ai-routing-stats`

---

## 🔄 CI/CD with GitHub Actions

### Automatic Deployments
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - uses: google-github-actions/setup-gcloud@v0
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}
    
    - name: Deploy to Cloud Run
      run: |
        gcloud run deploy airdocs \
          --source . \
          --platform managed \
          --region us-central1 \
          --allow-unauthenticated
```

---

## 🚨 Troubleshooting

### Common Issues

1. **Build Fails**
   ```bash
   # Check build logs
   gcloud builds log [BUILD_ID]
   ```

2. **Service Won't Start**
   ```bash
   # Check service logs
   gcloud run services logs read airdocs --region us-central1
   ```

3. **Environment Variables**
   ```bash
   # List current variables
   gcloud run services describe airdocs --region us-central1
   ```

4. **Memory Issues**
   ```bash
   # Increase memory
   gcloud run services update airdocs --memory 2Gi --region us-central1
   ```

---

## 🎯 Production Checklist

- [ ] **Service Deployed**: Cloud Run service running
- [ ] **Redis Connected**: Caching enabled
- [ ] **Environment Variables**: All secrets configured
- [ ] **Custom Domain**: Professional URL setup
- [ ] **Monitoring**: Logs and metrics configured
- [ ] **Scaling**: Auto-scaling configured
- [ ] **Security**: IAM and firewall rules
- [ ] **Backup**: Database backup strategy
- [ ] **CI/CD**: Automatic deployments

---

## 🎉 Success!

**AIRDOCS is now running on Google Cloud Run with:**

✅ **Enterprise Infrastructure**: Google's global network  
✅ **Auto-scaling**: Handles traffic spikes automatically  
✅ **Cost Optimization**: Pay only for what you use  
✅ **Production Ready**: All critical features enabled  
✅ **Global Performance**: Fast worldwide access  

**Your AI Document Factory is live and ready for beta testing! 🚀**
