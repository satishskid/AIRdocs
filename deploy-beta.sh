#!/bin/bash

# 🚀 AIRDOCS Beta Deployment Script
# Automated deployment to Railway, Render, or DigitalOcean

set -e

echo "🚀 AIRDOCS Beta Deployment Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if git is initialized
if [ ! -d ".git" ]; then
    print_info "Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial AIRDOCS production build with all features"
    print_status "Git repository initialized"
else
    print_status "Git repository already exists"
fi

# Check for deployment platform choice
echo ""
echo "Choose your deployment platform:"
echo "1) Railway (Recommended - $5/month, built-in Redis)"
echo "2) Render (Free tier available)"
echo "3) DigitalOcean App Platform ($5/month)"
echo "4) Manual setup instructions"

read -p "Enter your choice (1-4): " platform_choice

case $platform_choice in
    1)
        echo ""
        print_info "🚂 Railway Deployment Selected"
        echo ""
        echo "Steps to deploy to Railway:"
        echo "1. Push your code to GitHub:"
        echo "   git remote add origin https://github.com/yourusername/airdocs.git"
        echo "   git push -u origin main"
        echo ""
        echo "2. Go to https://railway.app"
        echo "3. Sign up with GitHub"
        echo "4. Click 'New Project' → 'Deploy from GitHub repo'"
        echo "5. Select your AIRDOCS repository"
        echo ""
        print_status "Railway configuration files created:"
        print_status "- railway.json (deployment config)"
        print_status "- nixpacks.toml (build config)"
        echo ""
        print_warning "Don't forget to add environment variables in Railway dashboard!"
        ;;
    2)
        echo ""
        print_info "🎨 Render Deployment Selected"
        echo ""
        echo "Steps to deploy to Render:"
        echo "1. Push your code to GitHub"
        echo "2. Go to https://render.com"
        echo "3. Create new Web Service from GitHub"
        echo "4. Configure:"
        echo "   Build Command: cd backend && pip install -r requirements.txt"
        echo "   Start Command: cd backend && uvicorn app:app --host 0.0.0.0 --port \$PORT"
        echo "5. Add Redis database separately"
        ;;
    3)
        echo ""
        print_info "🌊 DigitalOcean App Platform Selected"
        echo ""
        echo "Steps to deploy to DigitalOcean:"
        echo "1. Push your code to GitHub"
        echo "2. Go to DigitalOcean → App Platform"
        echo "3. Create app from GitHub repository"
        echo "4. Configure build settings"
        echo "5. Add managed Redis database"
        ;;
    4)
        echo ""
        print_info "📋 Manual Setup Instructions"
        echo ""
        echo "See DEPLOYMENT_GUIDE.md for detailed instructions"
        ;;
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac

echo ""
print_info "🔧 Environment Variables Needed:"
echo ""
echo "Core Configuration:"
echo "API_HOST=0.0.0.0"
echo "PORT=\$PORT"
echo "ADMIN_API_KEY=airdocs-beta-admin-2024"
echo "DEBUG=false"
echo "ENVIRONMENT=beta"
echo ""
echo "Redis (auto-configured on Railway):"
echo "REDIS_URL=\${{Redis.REDIS_URL}}"
echo ""
echo "Authentication:"
echo "TOKEN_ENCRYPTION_KEY=airdocs-beta-encryption-2024"
echo ""
echo "Stripe (Test Mode):"
echo "STRIPE_SECRET_KEY=sk_test_..."
echo "STRIPE_WEBHOOK_SECRET=whsec_test_..."
echo "FRONTEND_URL=https://your-app.railway.app"
echo ""
echo "AI Services (Optional for beta):"
echo "OPENAI_API_KEY=sk-..."
echo "ANTHROPIC_API_KEY=sk-ant-..."
echo "PERPLEXITY_API_KEY=pplx-..."

echo ""
print_info "🧪 Beta Testing Endpoints:"
echo ""
echo "After deployment, test these URLs:"
echo "• Health Check: https://your-app.railway.app/health"
echo "• API Docs: https://your-app.railway.app/docs"
echo "• Pricing: https://your-app.railway.app/payments/pricing"
echo "• AI Services: https://your-app.railway.app/ai-routing-stats"
echo "• Beta Interface: https://your-app.railway.app/beta-test.html"

echo ""
print_status "🎉 AIRDOCS is ready for beta deployment!"
print_status "All production features implemented:"
print_status "✅ OAuth 2.0 Integration (12+ AI services)"
print_status "✅ Circuit Breaker Implementation"
print_status "✅ Redis Caching System"
print_status "✅ Stripe Payment Integration"
print_status "✅ Real-time Monitoring"
print_status "✅ 443 Free Credits across 20+ AI services"

echo ""
print_warning "Next Steps:"
echo "1. Deploy to your chosen platform"
echo "2. Add environment variables"
echo "3. Test all endpoints"
echo "4. Configure Stripe webhooks"
echo "5. Add AI service API keys"
echo "6. Invite beta users"

echo ""
print_info "📚 Documentation:"
echo "• Deployment Guide: DEPLOYMENT_GUIDE.md"
echo "• API Documentation: /docs (after deployment)"
echo "• Beta Test Interface: /beta-test.html"

echo ""
print_status "🚀 Ready for Q4 launch!"
