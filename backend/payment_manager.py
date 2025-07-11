#!/usr/bin/env python3
"""
Payment Manager for AIRDOCS
Stripe integration for subscription management and billing
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import stripe
    STRIPE_AVAILABLE = True
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
except ImportError:
    logger.warning("⚠️ Stripe not available, payment features disabled")
    STRIPE_AVAILABLE = False

class SubscriptionTier(Enum):
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"

@dataclass
class PricingPlan:
    """Pricing plan configuration."""
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    credits_per_month: int
    features: List[str]
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str

# AIRDOCS Pricing Plans
PRICING_PLANS = {
    SubscriptionTier.FREE: PricingPlan(
        tier=SubscriptionTier.FREE,
        name="Free",
        price_monthly=0.0,
        price_yearly=0.0,
        credits_per_month=50,
        features=[
            "50 AI generations per month",
            "Basic document formats (PDF, DOCX)",
            "Standard quality AI models",
            "Email support"
        ],
        stripe_price_id_monthly="",
        stripe_price_id_yearly=""
    ),
    
    SubscriptionTier.PRO: PricingPlan(
        tier=SubscriptionTier.PRO,
        name="Pro",
        price_monthly=29.99,
        price_yearly=299.99,  # 2 months free
        credits_per_month=500,
        features=[
            "500 AI generations per month",
            "All document formats (PDF, DOCX, PPTX, HTML)",
            "Premium AI models (Genspark, PaperPal, etc.)",
            "Priority support",
            "Advanced templates",
            "Collaboration features"
        ],
        stripe_price_id_monthly="price_pro_monthly",
        stripe_price_id_yearly="price_pro_yearly"
    ),
    
    SubscriptionTier.ENTERPRISE: PricingPlan(
        tier=SubscriptionTier.ENTERPRISE,
        name="Enterprise",
        price_monthly=99.99,
        price_yearly=999.99,  # 2 months free
        credits_per_month=2000,
        features=[
            "2000 AI generations per month",
            "All premium features",
            "Custom AI model training",
            "API access",
            "Dedicated support",
            "Custom integrations",
            "Team management",
            "Advanced analytics"
        ],
        stripe_price_id_monthly="price_enterprise_monthly",
        stripe_price_id_yearly="price_enterprise_yearly"
    )
}

class PaymentManager:
    """
    Manages payments, subscriptions, and billing for AIRDOCS.
    Integrates with Stripe for payment processing.
    """
    
    def __init__(self):
        self.enabled = STRIPE_AVAILABLE
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        
    async def create_checkout_session(self, user_id: str, tier: SubscriptionTier, 
                                    billing_cycle: str = "monthly") -> Dict[str, Any]:
        """Create Stripe checkout session for subscription."""
        
        if not self.enabled:
            return {"success": False, "error": "Payment system not available"}
        
        try:
            plan = PRICING_PLANS[tier]
            
            if tier == SubscriptionTier.FREE:
                return {"success": False, "error": "Free tier doesn't require payment"}
            
            # Select price ID based on billing cycle
            price_id = (plan.stripe_price_id_yearly if billing_cycle == "yearly" 
                       else plan.stripe_price_id_monthly)
            
            # Create checkout session
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/pricing",
                client_reference_id=user_id,
                metadata={
                    'user_id': user_id,
                    'tier': tier.value,
                    'billing_cycle': billing_cycle
                }
            )
            
            logger.info(f"✅ Created checkout session for user {user_id}, tier {tier.value}")
            
            return {
                "success": True,
                "checkout_url": session.url,
                "session_id": session.id,
                "tier": tier.value,
                "billing_cycle": billing_cycle,
                "amount": plan.price_yearly if billing_cycle == "yearly" else plan.price_monthly
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to create checkout session: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def create_customer_portal_session(self, customer_id: str) -> Dict[str, Any]:
        """Create Stripe customer portal session for subscription management."""
        
        if not self.enabled:
            return {"success": False, "error": "Payment system not available"}
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard"
            )
            
            return {
                "success": True,
                "portal_url": session.url
            }
        
        except Exception as e:
            logger.error(f"❌ Failed to create portal session: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_subscription_status(self, customer_id: str) -> Dict[str, Any]:
        """Get current subscription status for customer."""
        
        if not self.enabled:
            return {
                "success": False,
                "error": "Payment system not available",
                "tier": SubscriptionTier.FREE.value
            }
        
        try:
            # Get customer's subscriptions
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='active',
                limit=1
            )
            
            if subscriptions.data:
                subscription = subscriptions.data[0]
                
                # Determine tier based on price ID
                price_id = subscription['items']['data'][0]['price']['id']
                tier = self._get_tier_from_price_id(price_id)
                
                return {
                    "success": True,
                    "active": True,
                    "tier": tier.value,
                    "subscription_id": subscription.id,
                    "current_period_start": subscription.current_period_start,
                    "current_period_end": subscription.current_period_end,
                    "status": subscription.status,
                    "credits_per_month": PRICING_PLANS[tier].credits_per_month
                }
            else:
                return {
                    "success": True,
                    "active": False,
                    "tier": SubscriptionTier.FREE.value,
                    "credits_per_month": PRICING_PLANS[SubscriptionTier.FREE].credits_per_month
                }
        
        except Exception as e:
            logger.error(f"❌ Failed to get subscription status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _get_tier_from_price_id(self, price_id: str) -> SubscriptionTier:
        """Determine subscription tier from Stripe price ID."""
        
        for tier, plan in PRICING_PLANS.items():
            if price_id in [plan.stripe_price_id_monthly, plan.stripe_price_id_yearly]:
                return tier
        
        return SubscriptionTier.FREE
    
    async def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """Handle Stripe webhook events."""
        
        if not self.enabled:
            return {"success": False, "error": "Payment system not available"}
        
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            event_type = event['type']
            logger.info(f"📨 Received Stripe webhook: {event_type}")
            
            if event_type == 'checkout.session.completed':
                return await self._handle_checkout_completed(event['data']['object'])
            
            elif event_type == 'customer.subscription.updated':
                return await self._handle_subscription_updated(event['data']['object'])
            
            elif event_type == 'customer.subscription.deleted':
                return await self._handle_subscription_cancelled(event['data']['object'])
            
            elif event_type == 'invoice.payment_succeeded':
                return await self._handle_payment_succeeded(event['data']['object'])
            
            elif event_type == 'invoice.payment_failed':
                return await self._handle_payment_failed(event['data']['object'])
            
            else:
                logger.info(f"ℹ️ Unhandled webhook event: {event_type}")
                return {"success": True, "message": f"Unhandled event: {event_type}"}
        
        except Exception as e:
            logger.error(f"❌ Webhook handling failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout completion."""
        
        user_id = session.get('client_reference_id')
        customer_id = session.get('customer')
        
        logger.info(f"✅ Checkout completed for user {user_id}, customer {customer_id}")
        
        # Here you would update your database with the new subscription
        # For now, we'll just log the event
        
        return {
            "success": True,
            "event": "checkout_completed",
            "user_id": user_id,
            "customer_id": customer_id
        }
    
    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates."""
        
        customer_id = subscription.get('customer')
        status = subscription.get('status')
        
        logger.info(f"🔄 Subscription updated for customer {customer_id}, status: {status}")
        
        return {
            "success": True,
            "event": "subscription_updated",
            "customer_id": customer_id,
            "status": status
        }
    
    async def _handle_subscription_cancelled(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        
        customer_id = subscription.get('customer')
        
        logger.info(f"❌ Subscription cancelled for customer {customer_id}")
        
        return {
            "success": True,
            "event": "subscription_cancelled",
            "customer_id": customer_id
        }
    
    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment."""
        
        customer_id = invoice.get('customer')
        amount = invoice.get('amount_paid', 0) / 100  # Convert from cents
        
        logger.info(f"💰 Payment succeeded for customer {customer_id}, amount: ${amount}")
        
        return {
            "success": True,
            "event": "payment_succeeded",
            "customer_id": customer_id,
            "amount": amount
        }
    
    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment."""
        
        customer_id = invoice.get('customer')
        
        logger.error(f"💳 Payment failed for customer {customer_id}")
        
        return {
            "success": True,
            "event": "payment_failed",
            "customer_id": customer_id
        }
    
    def get_pricing_plans(self) -> Dict[str, Any]:
        """Get all available pricing plans."""
        
        plans = {}
        for tier, plan in PRICING_PLANS.items():
            plans[tier.value] = {
                "name": plan.name,
                "price_monthly": plan.price_monthly,
                "price_yearly": plan.price_yearly,
                "credits_per_month": plan.credits_per_month,
                "features": plan.features,
                "savings_yearly": (plan.price_monthly * 12) - plan.price_yearly
            }
        
        return {
            "success": True,
            "plans": plans,
            "currency": "USD"
        }

# Global payment manager instance
payment_manager = PaymentManager()

# Convenience functions
async def create_checkout_session(user_id: str, tier: str, billing_cycle: str = "monthly") -> Dict[str, Any]:
    """Create checkout session for subscription."""
    tier_enum = SubscriptionTier(tier)
    return await payment_manager.create_checkout_session(user_id, tier_enum, billing_cycle)

async def get_subscription_status(customer_id: str) -> Dict[str, Any]:
    """Get subscription status for customer."""
    return await payment_manager.get_subscription_status(customer_id)

def get_pricing_plans() -> Dict[str, Any]:
    """Get all pricing plans."""
    return payment_manager.get_pricing_plans()
