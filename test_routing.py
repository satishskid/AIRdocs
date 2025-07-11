#!/usr/bin/env python3
"""
Test script for the tiered AI routing system
"""

import time
from typing import Dict, Any, List, Optional

# Simplified routing configuration for testing
SPECIALIZED_AI_SERVICES = {
    "presentations": {
        "primary_tier": [
            {
                "name": "genspark",
                "free_credits": 50,
                "quality_score": 95,
                "specialization": "executive_presentations"
            },
            {
                "name": "manus",
                "free_credits": 30,
                "quality_score": 93,
                "specialization": "business_presentations"
            }
        ],
        "secondary_tier": ["gpt-4o", "claude-3-opus"]
    },
    "academic_papers": {
        "primary_tier": [
            {
                "name": "paperpal",
                "free_credits": 10,
                "quality_score": 96,
                "specialization": "academic_writing"
            },
            {
                "name": "jenni_ai",
                "free_credits": 15,
                "quality_score": 94,
                "specialization": "research_papers"
            }
        ],
        "secondary_tier": ["claude-3-opus", "gpt-4o"]
    }
}

# Credit tracking
SPECIALIZED_CREDITS = {}

def initialize_credit_tracking():
    """Initialize credit tracking for all specialized services."""
    global SPECIALIZED_CREDITS
    
    for category, services in SPECIALIZED_AI_SERVICES.items():
        for service in services["primary_tier"]:
            service_name = service["name"]
            SPECIALIZED_CREDITS[service_name] = {
                "used_credits": 0,
                "remaining_credits": service["free_credits"],
                "total_requests": 0,
                "successful_requests": 0,
                "category": category
            }

class AIModelRouter:
    """Simplified routing system for testing."""
    
    def __init__(self):
        self.routing_stats = {
            "primary_tier_usage": 0,
            "secondary_tier_usage": 0,
            "total_requests": 0
        }
    
    def get_best_model(self, content_category: str, quality_level: int = 3) -> Dict[str, Any]:
        """Select the best AI model for content generation."""
        
        self.routing_stats["total_requests"] += 1
        
        if content_category not in SPECIALIZED_AI_SERVICES:
            self.routing_stats["secondary_tier_usage"] += 1
            return self._get_secondary_tier_model(content_category)
        
        # Try primary tier first
        primary_model = self._try_primary_tier(content_category)
        if primary_model:
            self.routing_stats["primary_tier_usage"] += 1
            return primary_model
        
        # Fallback to secondary tier
        self.routing_stats["secondary_tier_usage"] += 1
        return self._get_secondary_tier_model(content_category)
    
    def _try_primary_tier(self, category: str) -> Optional[Dict[str, Any]]:
        """Try to find available specialized service with credits."""
        
        services = SPECIALIZED_AI_SERVICES[category]["primary_tier"]
        
        # Find services with available credits
        available_services = []
        for service in services:
            service_name = service["name"]
            credits_info = SPECIALIZED_CREDITS.get(service_name, {})
            
            if credits_info.get("remaining_credits", 0) > 0:
                available_services.append({
                    "service": service,
                    "credits": credits_info,
                    "priority_score": service["quality_score"]
                })
        
        if not available_services:
            return None
        
        # Select best available service
        best_service = max(available_services, key=lambda x: x["priority_score"])
        
        return {
            "tier": "primary",
            "service_name": best_service["service"]["name"],
            "quality_score": best_service["service"]["quality_score"],
            "specialization": best_service["service"]["specialization"],
            "remaining_credits": best_service["credits"]["remaining_credits"]
        }
    
    def _get_secondary_tier_model(self, category: str) -> Dict[str, Any]:
        """Get secondary tier (general AI) model."""
        
        return {
            "tier": "secondary",
            "service_name": "gpt-4o",
            "quality_score": 85,
            "specialization": "general_purpose",
            "remaining_credits": "unlimited"
        }
    
    def consume_credit(self, service_name: str, success: bool = True) -> bool:
        """Consume a credit for a specialized service."""
        
        if service_name not in SPECIALIZED_CREDITS:
            return False
        
        credits_info = SPECIALIZED_CREDITS[service_name]
        
        if credits_info["remaining_credits"] <= 0:
            return False
        
        # Consume credit
        credits_info["remaining_credits"] -= 1
        credits_info["used_credits"] += 1
        credits_info["total_requests"] += 1
        
        if success:
            credits_info["successful_requests"] += 1
        
        return True

def test_routing_system():
    """Test the AI routing system."""
    
    print("🧪 TESTING TIERED AI ROUTING SYSTEM")
    print("=" * 50)
    
    # Initialize system
    initialize_credit_tracking()
    router = AIModelRouter()
    
    print("\n📊 Initial Credit Status:")
    for service_name, info in SPECIALIZED_CREDITS.items():
        print(f"  {service_name}: {info['remaining_credits']} credits ({info['category']})")
    
    # Test scenarios
    test_scenarios = [
        ("presentations", "Create executive presentation for Q4 results"),
        ("academic_papers", "Generate research paper on AI ethics"),
        ("presentations", "Create investor pitch deck"),
        ("academic_papers", "Write literature review on machine learning"),
        ("business_reports", "Generate market analysis report"),  # No specialized service
    ]
    
    print("\n🎯 Testing Routing Decisions:")
    print("-" * 30)
    
    for i, (category, prompt) in enumerate(test_scenarios, 1):
        print(f"\nTest {i}: {category}")
        print(f"Prompt: {prompt[:50]}...")
        
        # Get routing decision
        model_info = router.get_best_model(category, quality_level=3)
        
        print(f"✅ Routed to: {model_info['tier']} tier")
        print(f"   Service: {model_info['service_name']}")
        print(f"   Quality Score: {model_info['quality_score']}")
        print(f"   Specialization: {model_info['specialization']}")
        
        # Consume credit if primary tier
        if model_info["tier"] == "primary":
            success = router.consume_credit(model_info["service_name"], True)
            remaining = SPECIALIZED_CREDITS[model_info["service_name"]]["remaining_credits"]
            print(f"   Credits Remaining: {remaining}")
    
    # Test credit exhaustion
    print("\n🔄 Testing Credit Exhaustion:")
    print("-" * 30)
    
    # Exhaust Genspark credits
    genspark_credits = SPECIALIZED_CREDITS["genspark"]["remaining_credits"]
    print(f"\nExhausting Genspark credits ({genspark_credits} remaining)...")
    
    for i in range(genspark_credits + 2):  # Try 2 extra requests
        model_info = router.get_best_model("presentations", quality_level=3)
        
        if model_info["tier"] == "primary":
            router.consume_credit(model_info["service_name"], True)
            remaining = SPECIALIZED_CREDITS[model_info["service_name"]]["remaining_credits"]
            print(f"  Request {i+1}: {model_info['service_name']} (Credits: {remaining})")
        else:
            print(f"  Request {i+1}: Fallback to {model_info['service_name']} (secondary tier)")
    
    # Final statistics
    print("\n📈 ROUTING STATISTICS:")
    print("=" * 30)
    
    stats = router.routing_stats
    total = stats["total_requests"]
    primary_pct = (stats["primary_tier_usage"] / total) * 100 if total > 0 else 0
    secondary_pct = (stats["secondary_tier_usage"] / total) * 100 if total > 0 else 0
    
    print(f"Total Requests: {total}")
    print(f"Primary Tier Usage: {stats['primary_tier_usage']} ({primary_pct:.1f}%)")
    print(f"Secondary Tier Usage: {stats['secondary_tier_usage']} ({secondary_pct:.1f}%)")
    
    print(f"\n💰 Cost Optimization:")
    free_requests = stats["primary_tier_usage"]
    paid_requests = stats["secondary_tier_usage"]
    estimated_savings = free_requests * 0.02  # Assume $0.02 per request saved
    
    print(f"Free Tier Requests: {free_requests}")
    print(f"Paid Tier Requests: {paid_requests}")
    print(f"Estimated Cost Savings: ${estimated_savings:.2f}")
    
    print(f"\n🎯 Final Credit Status:")
    for service_name, info in SPECIALIZED_CREDITS.items():
        used = info['used_credits']
        remaining = info['remaining_credits']
        total_credits = used + remaining
        usage_pct = (used / total_credits) * 100 if total_credits > 0 else 0
        
        print(f"  {service_name}: {used}/{total_credits} used ({usage_pct:.1f}%)")
    
    # Quality assessment
    print(f"\n⭐ Quality Assessment:")
    avg_quality = sum(
        SPECIALIZED_CREDITS[service]["category"] == "presentations" and 95 or 
        SPECIALIZED_CREDITS[service]["category"] == "academic_papers" and 95 or 85
        for service in SPECIALIZED_CREDITS.keys()
    ) / len(SPECIALIZED_CREDITS)
    
    print(f"Average Quality Score: {avg_quality:.1f}/100")
    print(f"Specialized Service Coverage: {len(SPECIALIZED_AI_SERVICES)} categories")
    
    return stats

if __name__ == "__main__":
    test_routing_system()
