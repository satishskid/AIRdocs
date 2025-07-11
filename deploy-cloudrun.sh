#!/bin/bash

# 🚀 AIRDOCS - Google Cloud Run Deployment Script
# Automated deployment to Google Cloud Run with Redis

set -e

echo "🚀 AIRDOCS Google Cloud Run Deployment"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "Google Cloud SDK not installed. Please install it first:"
    echo "https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Get project ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    print_warning "No default project set. Please set your project:"
    read -p "Enter your Google Cloud Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

print_info "Using Google Cloud Project: $PROJECT_ID"

# Enable required APIs
print_info "Enabling required Google Cloud APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable redis.googleapis.com
print_status "APIs enabled"

# Set default region
REGION="us-central1"
gcloud config set run/region $REGION
print_info "Using region: $REGION"

# Build and deploy
print_info "Building and deploying AIRDOCS to Cloud Run..."

# Option 1: Direct deployment (recommended for first time)
print_info "Deploying directly to Cloud Run..."

gcloud run deploy airdocs \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8000 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production,DEBUG=false,API_HOST=0.0.0.0,ADMIN_API_KEY=airdocs-cloudrun-admin-2024,TOKEN_ENCRYPTION_KEY=airdocs-cloudrun-encryption-2024"

# Get the service URL
SERVICE_URL=$(gcloud run services describe airdocs --region=$REGION --format='value(status.url)')

print_status "AIRDOCS deployed successfully!"
print_status "Service URL: $SERVICE_URL"

echo ""
print_info "🧪 Beta Testing URLs:"
echo "• API Documentation: $SERVICE_URL/docs"
echo "• Beta Interface: $SERVICE_URL/beta-test.html"
echo "• System Health: $SERVICE_URL/health"
echo "• Pricing Plans: $SERVICE_URL/payments/pricing"
echo "• AI Services: $SERVICE_URL/ai-routing-stats"

echo ""
print_warning "Next Steps:"
echo "1. Set up Redis (see instructions below)"
echo "2. Configure environment variables"
echo "3. Add Stripe API keys for payments"
echo "4. Test all endpoints"

echo ""
print_info "🔧 Redis Setup (Optional but Recommended):"
echo "gcloud redis instances create airdocs-redis \\"
echo "    --size=1 \\"
echo "    --region=$REGION \\"
echo "    --redis-version=redis_6_x"

echo ""
print_info "📝 Environment Variables to Add:"
echo "gcloud run services update airdocs \\"
echo "    --region=$REGION \\"
echo "    --set-env-vars=\"REDIS_URL=redis://your-redis-ip:6379,STRIPE_SECRET_KEY=sk_test_...,FRONTEND_URL=$SERVICE_URL\""

echo ""
print_status "🎉 AIRDOCS is now live on Google Cloud Run!"
print_status "All production features are ready for beta testing!"
