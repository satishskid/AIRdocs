# 🚀 AIRDOCS Beta Deployment Guide

## Quick Deploy to Railway (Recommended)

### Step 1: Prepare Repository
```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial AIRDOCS production build"

# Push to GitHub
git remote add origin https://github.com/yourusername/airdocs.git
git push -u origin main
```

### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your AIRDOCS repository
5. Railway will automatically detect and deploy

### Step 3: Add Environment Variables
In Railway dashboard, go to Variables tab and add:

```env
# Core Configuration
API_HOST=0.0.0.0
PORT=$PORT
CORS_ORIGINS=https://your-frontend-domain.com
ADMIN_API_KEY=your-secure-admin-key-2024
DEBUG=false
ENVIRONMENT=production

# Redis (Railway provides this automatically)
REDIS_URL=${{Redis.REDIS_URL}}

# Authentication
TOKEN_ENCRYPTION_KEY=your-secure-encryption-key-2024

# Stripe Payment (Get from Stripe Dashboard)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
FRONTEND_URL=https://your-frontend-domain.com

# AI Service API Keys (Add as you get them)
OPENAI_API_KEY=sk-your-openai-key
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key
PERPLEXITY_API_KEY=pplx-your-perplexity-key

# OAuth Credentials (Add as you configure each service)
PAPERPAL_CLIENT_ID=your-paperpal-client-id
PAPERPAL_CLIENT_SECRET=your-paperpal-client-secret
GENSPARK_CLIENT_ID=your-genspark-client-id
GENSPARK_CLIENT_SECRET=your-genspark-client-secret
```

### Step 4: Add Redis Database
1. In Railway dashboard, click "New" → "Database" → "Redis"
2. Railway will automatically connect it to your app
3. The `REDIS_URL` environment variable will be set automatically

### Step 5: Configure Custom Domain (Optional)
1. Go to Settings → Domains
2. Add your custom domain
3. Update CORS_ORIGINS and FRONTEND_URL accordingly

---

## Alternative: Deploy to Render

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: Create Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3.9

### Step 3: Add Redis
1. Create new Redis instance in Render
2. Copy the Redis URL to your environment variables

---

## Alternative: Deploy to DigitalOcean

### Step 1: Create App Platform App
1. Go to DigitalOcean → App Platform
2. Create app from GitHub repository

### Step 2: Configure Build
```yaml
name: airdocs-backend
services:
- name: api
  source_dir: /backend
  github:
    repo: yourusername/airdocs
    branch: main
  run_command: uvicorn app:app --host 0.0.0.0 --port $PORT
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  routes:
  - path: /
databases:
- name: redis
  engine: REDIS
  version: "6"
```

---

## 🧪 Beta Testing Setup

### Essential Environment Variables for Beta
```env
# Minimum required for beta testing
API_HOST=0.0.0.0
PORT=$PORT
ADMIN_API_KEY=airdocs-beta-admin-2024
DEBUG=false
ENVIRONMENT=beta
REDIS_URL=${{Redis.REDIS_URL}}
TOKEN_ENCRYPTION_KEY=airdocs-beta-encryption-2024

# Add these for payment testing
STRIPE_SECRET_KEY=sk_test_... # Use test keys for beta
STRIPE_WEBHOOK_SECRET=whsec_test_...
FRONTEND_URL=https://your-app.railway.app
```

### Beta Testing Checklist
- [ ] Deploy backend to Railway/Render
- [ ] Add Redis database
- [ ] Configure environment variables
- [ ] Test health endpoint: `https://your-app.railway.app/health`
- [ ] Test API docs: `https://your-app.railway.app/docs`
- [ ] Test payment endpoints: `https://your-app.railway.app/payments/pricing`
- [ ] Test AI routing: `https://your-app.railway.app/ai-routing-stats`
- [ ] Configure Stripe webhooks (point to your deployed URL)

### Getting API Keys for Beta Testing

#### Free/Easy to Get:
1. **OpenAI**: $5 free credit → [platform.openai.com](https://platform.openai.com)
2. **Anthropic**: $5 free credit → [console.anthropic.com](https://console.anthropic.com)
3. **Perplexity**: Free tier available → [perplexity.ai](https://perplexity.ai)

#### For Full Testing:
1. **Stripe**: Test mode is free → [dashboard.stripe.com](https://dashboard.stripe.com)
2. **Specialized AI Services**: Contact for beta access
   - Genspark, PaperPal, Jenni, SciSpace, etc.

---

## 🎯 Recommended Beta Flow

### Phase 1: Core Deployment (Day 1)
1. Deploy to Railway with basic config
2. Add Redis
3. Test health and API endpoints
4. Verify all production features work

### Phase 2: Payment Integration (Day 2-3)
1. Set up Stripe test account
2. Configure payment endpoints
3. Test subscription flows
4. Set up webhook endpoints

### Phase 3: AI Service Integration (Week 1)
1. Add OpenAI/Anthropic API keys
2. Test content generation
3. Add specialized service APIs as available
4. Test routing and failover

### Phase 4: Beta User Testing (Week 2+)
1. Invite beta users
2. Monitor usage and performance
3. Collect feedback
4. Iterate based on user needs

---

## 🔧 Troubleshooting

### Common Issues:
1. **Build Fails**: Check Python version (use 3.9+)
2. **Redis Connection**: Ensure Redis URL is set correctly
3. **CORS Errors**: Update CORS_ORIGINS with your frontend domain
4. **Payment Webhooks**: Use ngrok for local testing, deployed URL for production

### Health Check URLs:
- **System Health**: `/health`
- **Payment Health**: `/payments/health`
- **Cache Status**: `/cache-status`
- **Circuit Breakers**: `/circuit-breaker-status`
- **AI Routing**: `/ai-routing-stats`

---

## 💡 Pro Tips for Beta Testing

1. **Use Railway**: Fastest deployment, built-in Redis, $5/month
2. **Start with Stripe Test Mode**: No real charges during beta
3. **Monitor Health Endpoints**: Set up uptime monitoring
4. **Use API Documentation**: Share `/docs` with beta testers
5. **Collect Analytics**: Monitor usage patterns and performance
6. **Gradual Rollout**: Start with 10-20 beta users, scale up

---

## 🎉 You're Ready to Deploy!

Your AIRDOCS platform is production-ready with all critical features:
- ✅ OAuth 2.0 Integration
- ✅ Circuit Breaker Implementation  
- ✅ Redis Caching
- ✅ Stripe Payment System
- ✅ Real-time Monitoring

**Choose Railway for the fastest beta deployment experience!**
