#!/bin/bash

# 🚀 AIRDOCS - Render.com FREE Deployment Script
# Complete free setup with Redis and PostgreSQL

set -e

echo "🚀 AIRDOCS FREE DEPLOYMENT TO RENDER.COM"
echo "========================================"
echo "✅ Web Service: FREE (750 hours/month)"
echo "✅ Redis: FREE (25MB)"
echo "✅ PostgreSQL: FREE (1GB)"
echo "✅ SSL: FREE (automatic)"
echo "✅ Custom Domain: FREE"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_info "🎯 RENDER DEPLOYMENT STEPS:"
echo ""

print_info "1. 📝 Create Render Account:"
echo "   • Go to: https://render.com"
echo "   • Sign up with GitHub (instant)"
echo "   • No credit card required"
echo ""

print_info "2. 🚀 Deploy Web Service:"
echo "   • Click 'New' → 'Web Service'"
echo "   • Connect GitHub repository: satishskid/AIRdocs"
echo "   • Configure:"
echo "     - Name: airdocs-backend"
echo "     - Environment: Python 3"
echo "     - Build Command: cd backend && pip install -r requirements.txt"
echo "     - Start Command: cd backend && uvicorn app:app --host 0.0.0.0 --port \$PORT"
echo "     - Plan: FREE"
echo ""

print_info "3. 💾 Add Redis Database:"
echo "   • Click 'New' → 'Redis'"
echo "   • Name: airdocs-redis"
echo "   • Plan: FREE (25MB)"
echo "   • Region: Oregon (same as web service)"
echo ""

print_info "4. 🔧 Environment Variables:"
echo "   In your web service settings, add:"
echo ""
echo "   ENVIRONMENT=production"
echo "   DEBUG=false"
echo "   API_HOST=0.0.0.0"
echo "   ADMIN_API_KEY=airdocs-render-admin-2024"
echo "   TOKEN_ENCRYPTION_KEY=airdocs-render-encryption-2024"
echo "   REDIS_URL=\${{airdocs-redis.REDIS_URL}}"
echo ""

print_info "5. 🎯 Optional Environment Variables:"
echo "   For full functionality, add:"
echo ""
echo "   # Stripe (Test Mode)"
echo "   STRIPE_SECRET_KEY=sk_test_..."
echo "   STRIPE_WEBHOOK_SECRET=whsec_test_..."
echo ""
echo "   # AI Services (Free Credits Available)"
echo "   OPENAI_API_KEY=sk-..."
echo "   ANTHROPIC_API_KEY=sk-ant-..."
echo "   PERPLEXITY_API_KEY=pplx-..."
echo ""

print_warning "📋 RENDER FREE TIER LIMITS:"
echo "• Web Service: 750 hours/month (25 hours/day)"
echo "• Redis: 25MB storage"
echo "• PostgreSQL: 1GB storage (if needed)"
echo "• Bandwidth: 100GB/month"
echo "• Build Minutes: Unlimited"
echo "• Custom Domains: Unlimited"
echo ""

print_info "🧪 AFTER DEPLOYMENT:"
echo "Your AIRDOCS will be available at:"
echo "• Main App: https://airdocs-backend.onrender.com"
echo "• API Docs: https://airdocs-backend.onrender.com/docs"
echo "• Beta Interface: https://airdocs-backend.onrender.com/beta-test.html"
echo "• System Health: https://airdocs-backend.onrender.com/health"
echo ""

print_warning "⚠️ IMPORTANT NOTES:"
echo "• Free tier spins down after 15 minutes of inactivity"
echo "• Cold start takes ~30 seconds (first request after sleep)"
echo "• Perfect for beta testing and demos"
echo "• Upgrade to paid plan (\$7/month) for always-on service"
echo ""

print_info "🔄 AUTOMATIC DEPLOYMENTS:"
echo "• Every push to main branch triggers automatic deployment"
echo "• No manual deployment needed"
echo "• View build logs in Render dashboard"
echo ""

print_info "📊 MONITORING:"
echo "• Render Dashboard: https://dashboard.render.com"
echo "• Logs: Real-time in dashboard"
echo "• Metrics: CPU, Memory, Response times"
echo "• Alerts: Email notifications for issues"
echo ""

print_status "🎉 RENDER SETUP COMPLETE!"
print_status "Follow the steps above to deploy AIRDOCS for FREE!"
print_status "All production features will be available!"

echo ""
print_info "💡 PRO TIPS:"
echo "• Use render.yaml for Infrastructure as Code"
echo "• Set up health checks for better reliability"
echo "• Monitor usage in dashboard"
echo "• Upgrade when you need always-on service"

echo ""
print_warning "🚀 READY TO DEPLOY?"
echo "1. Go to: https://render.com"
echo "2. Sign up with GitHub"
echo "3. Follow the steps above"
echo "4. Your AIRDOCS will be live in 5 minutes!"
