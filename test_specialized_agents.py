#!/usr/bin/env python3
"""
Comprehensive test of specialized AI agents vs generic models
Demonstrates the agent-first approach for maximum quality
"""

import time
from typing import Dict, Any, List

# Specialized AI Agents Configuration
SPECIALIZED_AGENTS = {
    "academic_papers": {
        "agents": [
            {"name": "paperpal", "credits": 10, "quality": 96, "specialty": "academic_writing"},
            {"name": "jenni_ai", "credits": 15, "quality": 94, "specialty": "research_papers"},
            {"name": "scispace", "credits": 12, "quality": 92, "specialty": "literature_review"},
            {"name": "consensus_ai", "credits": 8, "quality": 95, "specialty": "evidence_synthesis"},
            {"name": "elicit_ai", "credits": 6, "quality": 93, "specialty": "research_automation"},
            {"name": "semantic_scholar", "credits": 20, "quality": 90, "specialty": "citation_analysis"}
        ],
        "total_credits": 71,
        "avg_quality": 93.3
    },
    
    "presentations": {
        "agents": [
            {"name": "genspark", "credits": 50, "quality": 95, "specialty": "executive_presentations"},
            {"name": "manus", "credits": 30, "quality": 93, "specialty": "business_presentations"},
            {"name": "gamma_app", "credits": 40, "quality": 91, "specialty": "design_presentations"},
            {"name": "tome_app", "credits": 35, "quality": 89, "specialty": "storytelling_presentations"},
            {"name": "beautiful_ai", "credits": 25, "quality": 87, "specialty": "design_automation"}
        ],
        "total_credits": 180,
        "avg_quality": 91.0
    },
    
    "business_reports": {
        "agents": [
            {"name": "analyst_ai", "credits": 20, "quality": 94, "specialty": "business_analysis"},
            {"name": "pitchbook_ai", "credits": 15, "quality": 96, "specialty": "market_analysis"},
            {"name": "cb_insights", "credits": 12, "quality": 95, "specialty": "industry_intelligence"}
        ],
        "total_credits": 47,
        "avg_quality": 95.0
    },
    
    "research_reports": {
        "agents": [
            {"name": "perplexity_pro", "credits": 20, "quality": 94, "specialty": "research_synthesis"},
            {"name": "you_research", "credits": 15, "quality": 91, "specialty": "market_research"},
            {"name": "tavily_research", "credits": 25, "quality": 89, "specialty": "web_research"}
        ],
        "total_credits": 60,
        "avg_quality": 91.3
    },
    
    "marketing_campaigns": {
        "agents": [
            {"name": "jasper_ai", "credits": 30, "quality": 92, "specialty": "marketing_copy"},
            {"name": "copy_ai", "credits": 40, "quality": 89, "specialty": "conversion_copy"},
            {"name": "persado", "credits": 15, "quality": 95, "specialty": "emotional_marketing"}
        ],
        "total_credits": 85,
        "avg_quality": 92.0
    }
}

# Generic AI Models (Fallback)
GENERIC_MODELS = {
    "gpt-4o": {"quality": 85, "cost_per_request": 0.03},
    "claude-3-opus": {"quality": 87, "cost_per_request": 0.025},
    "gpt-4-turbo": {"quality": 83, "cost_per_request": 0.02}
}

class SpecializedAgentRouter:
    """Demonstrates agent-first routing strategy."""
    
    def __init__(self):
        self.agent_credits = {}
        self.usage_stats = {
            "specialized_requests": 0,
            "generic_requests": 0,
            "total_cost_savings": 0,
            "quality_improvements": []
        }
        
        # Initialize agent credits
        for category, config in SPECIALIZED_AGENTS.items():
            for agent in config["agents"]:
                self.agent_credits[agent["name"]] = {
                    "remaining": agent["credits"],
                    "used": 0,
                    "category": category,
                    "quality": agent["quality"],
                    "specialty": agent["specialty"]
                }
    
    def route_request(self, content_type: str, request_description: str) -> Dict[str, Any]:
        """Route request to best available agent."""
        
        print(f"\n🎯 Routing Request: {content_type}")
        print(f"   Description: {request_description[:60]}...")
        
        # Try specialized agents first
        if content_type in SPECIALIZED_AGENTS:
            agent_result = self._try_specialized_agents(content_type)
            if agent_result:
                self.usage_stats["specialized_requests"] += 1
                self.usage_stats["cost_savings"] += 0.025  # Estimated savings per request
                return agent_result
        
        # Fallback to generic models
        self.usage_stats["generic_requests"] += 1
        return self._use_generic_model(content_type)
    
    def _try_specialized_agents(self, content_type: str) -> Dict[str, Any]:
        """Try to find available specialized agent."""
        
        available_agents = []
        for agent in SPECIALIZED_AGENTS[content_type]["agents"]:
            agent_name = agent["name"]
            if self.agent_credits[agent_name]["remaining"] > 0:
                available_agents.append({
                    "name": agent_name,
                    "quality": agent["quality"],
                    "specialty": agent["specialty"],
                    "credits": self.agent_credits[agent_name]["remaining"]
                })
        
        if not available_agents:
            print(f"   ❌ No specialized agents available for {content_type}")
            return None
        
        # Select best available agent (highest quality)
        best_agent = max(available_agents, key=lambda x: x["quality"])
        
        # Consume credit
        self.agent_credits[best_agent["name"]]["remaining"] -= 1
        self.agent_credits[best_agent["name"]]["used"] += 1
        
        print(f"   ✅ Using specialized agent: {best_agent['name']}")
        print(f"      Quality Score: {best_agent['quality']}/100")
        print(f"      Specialty: {best_agent['specialty']}")
        print(f"      Credits Remaining: {best_agent['credits'] - 1}")
        
        return {
            "agent_type": "specialized",
            "agent_name": best_agent["name"],
            "quality_score": best_agent["quality"],
            "specialty": best_agent["specialty"],
            "cost": 0  # Free tier
        }
    
    def _use_generic_model(self, content_type: str) -> Dict[str, Any]:
        """Use generic AI model as fallback."""
        
        # Select best generic model
        best_model = max(GENERIC_MODELS.items(), key=lambda x: x[1]["quality"])
        model_name, model_info = best_model
        
        print(f"   🔄 Fallback to generic model: {model_name}")
        print(f"      Quality Score: {model_info['quality']}/100")
        print(f"      Cost: ${model_info['cost_per_request']:.3f}")
        
        return {
            "agent_type": "generic",
            "agent_name": model_name,
            "quality_score": model_info["quality"],
            "specialty": "general_purpose",
            "cost": model_info["cost_per_request"]
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        
        total_requests = self.usage_stats["specialized_requests"] + self.usage_stats["generic_requests"]
        specialized_percentage = (self.usage_stats["specialized_requests"] / max(total_requests, 1)) * 100
        
        # Calculate average quality
        total_quality = 0
        quality_count = 0
        
        for category, config in SPECIALIZED_AGENTS.items():
            for agent in config["agents"]:
                agent_name = agent["name"]
                used_credits = self.agent_credits[agent_name]["used"]
                if used_credits > 0:
                    total_quality += agent["quality"] * used_credits
                    quality_count += used_credits
        
        avg_specialized_quality = total_quality / max(quality_count, 1)
        avg_generic_quality = 85  # Average of generic models
        
        return {
            "routing_efficiency": {
                "total_requests": total_requests,
                "specialized_usage": self.usage_stats["specialized_requests"],
                "generic_usage": self.usage_stats["generic_requests"],
                "specialized_percentage": specialized_percentage
            },
            "quality_metrics": {
                "avg_specialized_quality": avg_specialized_quality,
                "avg_generic_quality": avg_generic_quality,
                "quality_improvement": avg_specialized_quality - avg_generic_quality
            },
            "cost_optimization": {
                "total_cost_savings": self.usage_stats["cost_savings"],
                "free_requests": self.usage_stats["specialized_requests"],
                "paid_requests": self.usage_stats["generic_requests"]
            },
            "agent_utilization": {
                agent_name: {
                    "used_credits": info["used"],
                    "remaining_credits": info["remaining"],
                    "category": info["category"],
                    "utilization_rate": (info["used"] / (info["used"] + info["remaining"])) * 100
                }
                for agent_name, info in self.agent_credits.items()
                if info["used"] > 0
            }
        }

def demonstrate_agent_first_approach():
    """Demonstrate the agent-first approach with realistic scenarios."""
    
    print("🤖 SPECIALIZED AI AGENTS - AGENT-FIRST DEMONSTRATION")
    print("=" * 60)
    
    router = SpecializedAgentRouter()
    
    # Show initial agent availability
    print("\n📊 INITIAL AGENT AVAILABILITY:")
    print("-" * 40)
    
    total_credits = 0
    for category, config in SPECIALIZED_AGENTS.items():
        category_credits = config["total_credits"]
        avg_quality = config["avg_quality"]
        agent_count = len(config["agents"])
        
        print(f"{category.upper()}:")
        print(f"  • {agent_count} specialized agents")
        print(f"  • {category_credits} total free credits")
        print(f"  • {avg_quality:.1f}% average quality")
        
        total_credits += category_credits
    
    print(f"\n🎯 TOTAL SYSTEM CAPACITY:")
    print(f"  • {total_credits} free credits across all agents")
    print(f"  • Estimated value: ${total_credits * 0.025:.2f}")
    print(f"  • 5 content categories with specialized agents")
    
    # Test realistic scenarios
    test_scenarios = [
        ("academic_papers", "Generate research paper on AI ethics in healthcare"),
        ("presentations", "Create Q4 investor pitch deck for SaaS startup"),
        ("business_reports", "Market analysis for electric vehicle adoption"),
        ("academic_papers", "Literature review on machine learning climate models"),
        ("presentations", "Executive presentation on digital transformation"),
        ("research_reports", "Competitive analysis of fintech landscape"),
        ("marketing_campaigns", "B2B SaaS product launch campaign"),
        ("academic_papers", "Systematic review of renewable energy technologies"),
        ("business_reports", "Industry analysis of AI automation trends"),
        ("presentations", "Board presentation on company strategy")
    ]
    
    print(f"\n🧪 TESTING AGENT-FIRST ROUTING:")
    print("-" * 40)
    
    for i, (content_type, description) in enumerate(test_scenarios, 1):
        print(f"\nTest {i}/10:")
        result = router.route_request(content_type, description)
    
    # Show final statistics
    print(f"\n📈 FINAL SYSTEM STATISTICS:")
    print("=" * 40)
    
    stats = router.get_system_stats()
    
    routing = stats["routing_efficiency"]
    quality = stats["quality_metrics"]
    cost = stats["cost_optimization"]
    
    print(f"\n🎯 Routing Efficiency:")
    print(f"  • Total Requests: {routing['total_requests']}")
    print(f"  • Specialized Agent Usage: {routing['specialized_usage']} ({routing['specialized_percentage']:.1f}%)")
    print(f"  • Generic Model Fallback: {routing['generic_usage']} ({100-routing['specialized_percentage']:.1f}%)")
    
    print(f"\n⭐ Quality Improvements:")
    print(f"  • Specialized Agent Quality: {quality['avg_specialized_quality']:.1f}%")
    print(f"  • Generic Model Quality: {quality['avg_generic_quality']:.1f}%")
    print(f"  • Quality Improvement: +{quality['quality_improvement']:.1f} points")
    
    print(f"\n💰 Cost Optimization:")
    print(f"  • Free Requests: {cost['free_requests']}")
    print(f"  • Paid Requests: {cost['paid_requests']}")
    print(f"  • Total Cost Savings: ${cost['total_cost_savings']:.2f}")
    
    print(f"\n🔋 Agent Utilization:")
    for agent_name, usage in stats["agent_utilization"].items():
        print(f"  • {agent_name}: {usage['used_credits']} credits used ({usage['utilization_rate']:.1f}%)")
    
    return stats

if __name__ == "__main__":
    demonstrate_agent_first_approach()
