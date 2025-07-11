#!/bin/bash

# 🚀 AIRDOCS - Fly.io FREE Deployment Script
# No cold starts, always-on free tier

set -e

echo "🚀 AIRDOCS FREE DEPLOYMENT TO FLY.IO"
echo "==================================="
echo "✅ 3 shared VMs: FREE (always on)"
echo "✅ 3GB storage: FREE"
echo "✅ 160GB bandwidth: FREE"
echo "✅ No cold starts: Always responsive"
echo "✅ Global deployment: Fast worldwide"
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

# Check if flyctl is installed
if ! command -v flyctl &> /dev/null; then
    print_warning "Fly CLI not installed. Installing..."
    
    # Install flyctl
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # Mac
        brew install flyctl
    else
        # Linux/Windows
        curl -L https://fly.io/install.sh | sh
    fi
    
    print_status "Fly CLI installed"
fi

print_info "🎯 FLY.IO DEPLOYMENT STEPS:"
echo ""

print_info "1. 📝 Create Fly.io Account:"
echo "   • Go to: https://fly.io"
echo "   • Sign up (no credit card required for free tier)"
echo "   • Verify email"
echo ""

print_info "2. 🔐 Login to Fly:"
flyctl auth login

print_info "3. 🚀 Deploy AIRDOCS:"
echo "   Deploying to Fly.io..."

# Launch the app
flyctl launch --no-deploy --name airdocs-beta --region iad

print_info "4. 🔧 Set Environment Variables:"
flyctl secrets set \
  ENVIRONMENT=production \
  DEBUG=false \
  API_HOST=0.0.0.0 \
  ADMIN_API_KEY=airdocs-fly-admin-2024 \
  TOKEN_ENCRYPTION_KEY=airdocs-fly-encryption-2024

print_info "5. 🚀 Deploy Application:"
flyctl deploy

# Get the app URL
APP_URL=$(flyctl info --json | jq -r '.Hostname')
if [ "$APP_URL" != "null" ]; then
    APP_URL="https://$APP_URL"
else
    APP_URL="https://airdocs-beta.fly.dev"
fi

print_status "🎉 AIRDOCS deployed successfully!"
print_status "App URL: $APP_URL"

echo ""
print_info "🧪 Your AIRDOCS URLs:"
echo "• 📚 API Documentation: $APP_URL/docs"
echo "• 🎯 Beta Interface: $APP_URL/beta-test.html"
echo "• 🏥 System Health: $APP_URL/health"
echo "• 💳 Pricing Plans: $APP_URL/payments/pricing"
echo "• 🤖 AI Services: $APP_URL/ai-routing-stats"

echo ""
print_warning "🔧 NEXT STEPS FOR FULL FUNCTIONALITY:"
echo ""
echo "1. 💾 Add Redis (Upstash recommended):"
echo "   • Go to: https://upstash.com"
echo "   • Create free Redis database"
echo "   • Add to Fly secrets:"
echo "   flyctl secrets set REDIS_URL=redis://your-upstash-url"
echo ""
echo "2. 💳 Add Stripe for Payments:"
echo "   flyctl secrets set \\"
echo "     STRIPE_SECRET_KEY=sk_test_... \\"
echo "     STRIPE_WEBHOOK_SECRET=whsec_test_... \\"
echo "     FRONTEND_URL=$APP_URL"
echo ""
echo "3. 🤖 Add AI Service API Keys:"
echo "   flyctl secrets set \\"
echo "     OPENAI_API_KEY=sk-... \\"
echo "     ANTHROPIC_API_KEY=sk-ant-..."

echo ""
print_warning "📋 FLY.IO FREE TIER BENEFITS:"
echo "• 3 shared-cpu-1x VMs (always on)"
echo "• 3GB persistent storage"
echo "• 160GB bandwidth/month"
echo "• No cold starts (always responsive)"
echo "• Global deployment (fast worldwide)"
echo "• Custom domains included"
echo ""

print_info "📊 MONITORING:"
echo "• Logs: flyctl logs"
echo "• Status: flyctl status"
echo "• Metrics: flyctl metrics"
echo "• Dashboard: https://fly.io/dashboard"
echo ""

print_info "🔄 UPDATES:"
echo "• Deploy changes: flyctl deploy"
echo "• Scale: flyctl scale count 2"
echo "• Restart: flyctl restart"
echo ""

print_status "🎉 FLY.IO DEPLOYMENT COMPLETE!"
print_status "AIRDOCS is now live with NO COLD STARTS!"
print_status "Perfect for production-like beta testing!"

echo ""
print_info "💡 PRO TIPS:"
echo "• Fly.io has the most generous free tier"
echo "• No cold starts = better user experience"
echo "• Global deployment = fast worldwide access"
echo "• Easy scaling when you grow"

echo ""
print_warning "🚀 AIRDOCS IS LIVE!"
echo "Visit: $APP_URL"
echo "Start inviting beta users immediately!"
