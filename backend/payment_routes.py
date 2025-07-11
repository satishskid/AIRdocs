#!/usr/bin/env python3
"""
Payment Routes for AIRDOCS
FastAPI endpoints for Stripe payment integration
"""

from fastapi import APIRouter, HTTPException, Request, Header
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging

from payment_manager import (
    payment_manager, 
    create_checkout_session, 
    get_subscription_status,
    get_pricing_plans,
    SubscriptionTier
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create payment router
payment_router = APIRouter(prefix="/payments", tags=["payments"])

@payment_router.get("/pricing")
async def get_pricing():
    """Get all available pricing plans."""
    
    try:
        return get_pricing_plans()
    
    except Exception as e:
        logger.error(f"Error getting pricing plans: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting pricing plans: {str(e)}")

@payment_router.post("/create-checkout-session")
async def create_checkout(request: Dict[str, Any]):
    """Create Stripe checkout session for subscription."""
    
    try:
        user_id = request.get("user_id")
        tier = request.get("tier", "pro")
        billing_cycle = request.get("billing_cycle", "monthly")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        # Validate tier
        try:
            tier_enum = SubscriptionTier(tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {tier}")
        
        # Validate billing cycle
        if billing_cycle not in ["monthly", "yearly"]:
            raise HTTPException(status_code=400, detail="billing_cycle must be 'monthly' or 'yearly'")
        
        result = await create_checkout_session(user_id, tier, billing_cycle)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")

@payment_router.post("/create-portal-session")
async def create_portal(request: Dict[str, Any]):
    """Create Stripe customer portal session."""
    
    try:
        customer_id = request.get("customer_id")
        
        if not customer_id:
            raise HTTPException(status_code=400, detail="customer_id is required")
        
        result = await payment_manager.create_customer_portal_session(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating portal session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating portal session: {str(e)}")

@payment_router.get("/subscription-status/{customer_id}")
async def get_subscription(customer_id: str):
    """Get subscription status for customer."""
    
    try:
        result = await get_subscription_status(customer_id)
        
        if result["success"]:
            return result
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting subscription status: {str(e)}")

@payment_router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    """Handle Stripe webhook events."""
    
    try:
        # Get raw body
        body = await request.body()
        
        if not stripe_signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Handle webhook
        result = await payment_manager.handle_webhook(body, stripe_signature)
        
        if result["success"]:
            return {"received": True, "event": result.get("event", "unknown")}
        else:
            logger.error(f"Webhook handling failed: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")

@payment_router.get("/health")
async def payment_health():
    """Health check for payment system."""
    
    try:
        return {
            "success": True,
            "status": "healthy" if payment_manager.enabled else "disabled",
            "stripe_available": payment_manager.enabled,
            "webhook_configured": bool(payment_manager.webhook_secret),
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    except Exception as e:
        logger.error(f"Payment health check error: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

@payment_router.get("/usage/{user_id}")
async def get_usage_stats(user_id: str):
    """Get usage statistics for user."""
    
    try:
        # This would typically query your database for user usage
        # For now, return mock data
        
        return {
            "success": True,
            "user_id": user_id,
            "current_period": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-31",
                "credits_used": 45,
                "credits_limit": 500,
                "credits_remaining": 455,
                "usage_percentage": 9.0
            },
            "tier": "pro",
            "next_billing_date": "2024-02-01",
            "usage_history": [
                {"date": "2024-01-01", "credits_used": 5},
                {"date": "2024-01-02", "credits_used": 8},
                {"date": "2024-01-03", "credits_used": 12},
                {"date": "2024-01-04", "credits_used": 20}
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting usage stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting usage stats: {str(e)}")

@payment_router.post("/upgrade-plan")
async def upgrade_plan(request: Dict[str, Any]):
    """Upgrade user's subscription plan."""
    
    try:
        user_id = request.get("user_id")
        new_tier = request.get("new_tier")
        billing_cycle = request.get("billing_cycle", "monthly")
        
        if not user_id or not new_tier:
            raise HTTPException(status_code=400, detail="user_id and new_tier are required")
        
        # Validate new tier
        try:
            tier_enum = SubscriptionTier(new_tier)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid tier: {new_tier}")
        
        # For upgrade, we create a new checkout session
        # In a real implementation, you might use Stripe's subscription modification APIs
        result = await create_checkout_session(user_id, new_tier, billing_cycle)
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Upgrade initiated to {new_tier}",
                "checkout_url": result["checkout_url"],
                "new_tier": new_tier
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error upgrading plan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error upgrading plan: {str(e)}")

@payment_router.get("/invoice-history/{customer_id}")
async def get_invoice_history(customer_id: str):
    """Get invoice history for customer."""
    
    try:
        if not payment_manager.enabled:
            return {
                "success": False,
                "error": "Payment system not available",
                "invoices": []
            }
        
        # This would typically fetch from Stripe
        # For now, return mock data
        
        return {
            "success": True,
            "customer_id": customer_id,
            "invoices": [
                {
                    "id": "in_1234567890",
                    "date": "2024-01-01",
                    "amount": 29.99,
                    "status": "paid",
                    "description": "AIRDOCS Pro - Monthly",
                    "download_url": "https://invoice.stripe.com/..."
                },
                {
                    "id": "in_0987654321",
                    "date": "2023-12-01",
                    "amount": 29.99,
                    "status": "paid",
                    "description": "AIRDOCS Pro - Monthly",
                    "download_url": "https://invoice.stripe.com/..."
                }
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting invoice history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting invoice history: {str(e)}")

@payment_router.post("/cancel-subscription")
async def cancel_subscription(request: Dict[str, Any]):
    """Cancel user's subscription."""
    
    try:
        customer_id = request.get("customer_id")
        immediate = request.get("immediate", False)
        
        if not customer_id:
            raise HTTPException(status_code=400, detail="customer_id is required")
        
        if not payment_manager.enabled:
            return {
                "success": False,
                "error": "Payment system not available"
            }
        
        # This would typically cancel the subscription in Stripe
        # For now, return mock response
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "customer_id": customer_id,
            "cancellation_type": "immediate" if immediate else "at_period_end",
            "effective_date": "2024-01-31" if not immediate else "2024-01-15"
        }
    
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cancelling subscription: {str(e)}")
