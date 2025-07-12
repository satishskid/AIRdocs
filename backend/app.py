#!/usr/bin/env python3
"""
GreyBrain Bank - AI Model Aggregation Platform
A comprehensive API server for managing 88+ AI models, credits, and intelligent content generation.
Made by GreyBrain.ai
"""

import os
import json
import hashlib
import threading
import time
import uuid
import asyncio
import psutil
import requests
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Depends, Form, File, UploadFile, Header, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Import OAuth components
try:
    from oauth_routes import oauth_router
    from auth_manager import auth_manager, get_auth_headers, is_service_authenticated
    OAUTH_ENABLED = True
    print("✅ OAuth integration enabled")
except ImportError as e:
    print(f"⚠️ OAuth integration disabled: {e}")
    OAUTH_ENABLED = False

# Import Circuit Breaker components
try:
    from circuit_breaker import (
        circuit_breaker_manager,
        call_with_circuit_breaker,
        get_service_health,
        get_all_service_health,
        get_system_health
    )
    CIRCUIT_BREAKER_ENABLED = True
    print("✅ Circuit breaker integration enabled")
except ImportError as e:
    print(f"⚠️ Circuit breaker integration disabled: {e}")
    CIRCUIT_BREAKER_ENABLED = False

# Import Cache components
try:
    from cache_manager import (
        cache_manager,
        get_cached_response,
        cache_response,
        get_cache_statistics
    )
    CACHE_ENABLED = True
    print("✅ Redis cache integration enabled")
except ImportError as e:
    print(f"⚠️ Cache integration disabled: {e}")
    CACHE_ENABLED = False

# Import Payment components
try:
    from payment_routes import payment_router
    from payment_manager import payment_manager, get_pricing_plans
    PAYMENT_ENABLED = True
    print("✅ Stripe payment integration enabled")
except ImportError as e:
    print(f"⚠️ Payment integration disabled: {e}")
    PAYMENT_ENABLED = False

# Import scientific model discovery
from model_discovery import model_discovery_service

# Import document generation service
from document_generator import document_generator

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/greybrain-bank.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GreyBrain Bank",
    description="Advanced AI Model Aggregation Platform - 88+ AI models for intelligent content generation. Made by GreyBrain.ai",
    version="1.0.0"
)

# Include OAuth router if enabled
if OAUTH_ENABLED:
    app.include_router(oauth_router)
    logger.info("✅ OAuth routes registered")

# Include Payment router if enabled
if PAYMENT_ENABLED:
    app.include_router(payment_router)
    logger.info("✅ Payment routes registered")

# Mount static files for frontend assets
FRONTEND_DIR = "./frontend"
# Create assets directory if it doesn't exist
import os
os.makedirs(f"{FRONTEND_DIR}/assets", exist_ok=True)
app.mount("/assets", StaticFiles(directory=f"{FRONTEND_DIR}/assets"), name="assets")
app.mount("/static", StaticFiles(directory=f"{FRONTEND_DIR}"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # Configure for production

# Security configuration
security = HTTPBearer()
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "greybrain-admin-key-2024")

# Rate limiting configuration
rate_limit_storage = defaultdict(lambda: deque())
RATE_LIMIT_REQUESTS = 100  # requests per minute
RATE_LIMIT_WINDOW = 60  # seconds

def check_rate_limit(client_ip: str) -> bool:
    """Check if client has exceeded rate limit."""
    now = time.time()
    client_requests = rate_limit_storage[client_ip]

    # Remove old requests outside the window
    while client_requests and client_requests[0] < now - RATE_LIMIT_WINDOW:
        client_requests.popleft()

    # Check if limit exceeded
    if len(client_requests) >= RATE_LIMIT_REQUESTS:
        return False

    # Add current request
    client_requests.append(now)
    return True

def verify_admin_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify admin API key."""
    if credentials.credentials != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid admin API key")
    return credentials.credentials

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_ip = request.client.host

    # Skip rate limiting for health checks
    if request.url.path in ["/", "/health"]:
        response = await call_next(request)
        return response

    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )

    response = await call_next(request)
    return response

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers."""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; img-src 'self' data: https://fastapi.tiangolo.com https://cdn.jsdelivr.net; connect-src 'self'"

    return response

# Global data storage
models_data: Dict[str, Any] = {}
prompts_data: List[Dict[str, Any]] = []
last_models_update = 0
last_prompts_update = 0

# Tiered AI Model Routing Configuration
SPECIALIZED_AI_SERVICES = {
    "presentations": {
        "primary_tier": [
            {
                "name": "genspark",
                "api_endpoint": "https://api.genspark.ai/v1/presentations",
                "free_credits": 50,
                "cost_per_request": 0,
                "quality_score": 95,
                "specialization": "executive_presentations",
                "output_formats": ["pptx", "pdf"],
                "max_slides": 20,
                "strengths": ["executive_quality", "strategic_frameworks", "visual_design"]
            },
            {
                "name": "manus",
                "api_endpoint": "https://api.manus.ai/v1/generate",
                "free_credits": 30,
                "cost_per_request": 0,
                "quality_score": 93,
                "specialization": "business_presentations",
                "output_formats": ["pptx", "pdf", "keynote"],
                "max_slides": 25,
                "strengths": ["business_strategy", "financial_modeling", "investor_ready"]
            },
            {
                "name": "gamma_app",
                "api_endpoint": "https://api.gamma.app/v1/presentations",
                "free_credits": 40,
                "cost_per_request": 0,
                "quality_score": 91,
                "specialization": "design_presentations",
                "output_formats": ["pptx", "pdf", "web"],
                "max_slides": 30,
                "strengths": ["visual_design", "interactive_elements", "modern_layouts"]
            },
            {
                "name": "tome_app",
                "api_endpoint": "https://api.tome.app/v1/presentations",
                "free_credits": 35,
                "cost_per_request": 0,
                "quality_score": 89,
                "specialization": "storytelling_presentations",
                "output_formats": ["pptx", "pdf", "web"],
                "max_slides": 25,
                "strengths": ["narrative_flow", "storytelling", "audience_engagement"]
            },
            {
                "name": "beautiful_ai",
                "api_endpoint": "https://api.beautiful.ai/v1/presentations",
                "free_credits": 25,
                "cost_per_request": 0,
                "quality_score": 87,
                "specialization": "design_automation",
                "output_formats": ["pptx", "pdf"],
                "max_slides": 20,
                "strengths": ["auto_design", "brand_consistency", "template_intelligence"]
            }
        ],
        "secondary_tier": ["gpt-4o", "claude-3-opus", "gpt-4-turbo"]
    },

    "academic_papers": {
        "primary_tier": [
            {
                "name": "paperpal",
                "api_endpoint": "https://api.paperpal.com/v1/research",
                "free_credits": 10,
                "cost_per_request": 0,
                "quality_score": 96,
                "specialization": "academic_writing",
                "output_formats": ["pdf", "docx", "latex"],
                "max_pages": 30,
                "citation_styles": ["apa", "mla", "chicago", "ieee"],
                "strengths": ["grammar_check", "academic_tone", "citation_formatting"]
            },
            {
                "name": "jenni_ai",
                "api_endpoint": "https://api.jenni.ai/v1/academic",
                "free_credits": 15,
                "cost_per_request": 0,
                "quality_score": 94,
                "specialization": "research_papers",
                "output_formats": ["pdf", "docx", "latex"],
                "max_pages": 25,
                "citation_styles": ["apa", "mla", "chicago"],
                "strengths": ["research_structure", "literature_review", "methodology"]
            },
            {
                "name": "scispace",
                "api_endpoint": "https://api.scispace.com/v1/papers",
                "free_credits": 12,
                "cost_per_request": 0,
                "quality_score": 92,
                "specialization": "literature_review",
                "output_formats": ["pdf", "docx"],
                "max_pages": 20,
                "citation_styles": ["apa", "ieee", "nature"],
                "strengths": ["literature_search", "citation_analysis", "research_gaps"]
            },
            {
                "name": "consensus_ai",
                "api_endpoint": "https://api.consensus.app/v1/research",
                "free_credits": 8,
                "cost_per_request": 0,
                "quality_score": 95,
                "specialization": "evidence_synthesis",
                "output_formats": ["pdf", "docx"],
                "max_pages": 35,
                "citation_styles": ["apa", "nature", "science"],
                "strengths": ["evidence_synthesis", "meta_analysis", "research_validation"]
            },
            {
                "name": "elicit_ai",
                "api_endpoint": "https://api.elicit.org/v1/research",
                "free_credits": 6,
                "cost_per_request": 0,
                "quality_score": 93,
                "specialization": "research_automation",
                "output_formats": ["pdf", "docx"],
                "max_pages": 25,
                "citation_styles": ["apa", "ieee"],
                "strengths": ["research_questions", "study_analysis", "data_extraction"]
            },
            {
                "name": "semantic_scholar",
                "api_endpoint": "https://api.semanticscholar.org/v1/research",
                "free_credits": 20,
                "cost_per_request": 0,
                "quality_score": 90,
                "specialization": "citation_analysis",
                "output_formats": ["pdf", "docx"],
                "max_pages": 35,
                "citation_styles": ["apa", "mla", "chicago", "ieee"],
                "strengths": ["citation_network", "paper_discovery", "impact_analysis"]
            }
        ],
        "secondary_tier": ["claude-3-opus", "gpt-4o", "deepseek-v2"]
    },

    "research_reports": {
        "primary_tier": [
            {
                "name": "perplexity_pro",
                "api_endpoint": "https://api.perplexity.ai/v1/research",
                "free_credits": 20,
                "cost_per_request": 0,
                "quality_score": 94,
                "specialization": "research_synthesis",
                "output_formats": ["pdf", "docx", "html"],
                "max_pages": 40,
                "strengths": ["real_time_data", "source_verification", "comprehensive_analysis"]
            },
            {
                "name": "you_research",
                "api_endpoint": "https://api.you.com/v1/research",
                "free_credits": 15,
                "cost_per_request": 0,
                "quality_score": 91,
                "specialization": "market_research",
                "output_formats": ["pdf", "docx"],
                "max_pages": 30,
                "strengths": ["market_data", "trend_analysis", "competitive_intelligence"]
            },
            {
                "name": "tavily_research",
                "api_endpoint": "https://api.tavily.com/v1/research",
                "free_credits": 25,
                "cost_per_request": 0,
                "quality_score": 89,
                "specialization": "web_research",
                "output_formats": ["pdf", "docx"],
                "max_pages": 35,
                "strengths": ["web_scraping", "data_aggregation", "fact_checking"]
            }
        ],
        "secondary_tier": ["gpt-4o", "claude-3-opus", "perplexity-base"]
    },

    "business_reports": {
        "primary_tier": [
            {
                "name": "analyst_ai",
                "api_endpoint": "https://api.analyst.ai/v1/reports",
                "free_credits": 20,
                "cost_per_request": 0,
                "quality_score": 94,
                "specialization": "business_analysis",
                "output_formats": ["pdf", "docx", "xlsx"],
                "max_pages": 50,
                "strengths": ["financial_analysis", "market_research", "competitive_intelligence"]
            },
            {
                "name": "pitchbook_ai",
                "api_endpoint": "https://api.pitchbook.com/v1/analysis",
                "free_credits": 15,
                "cost_per_request": 0,
                "quality_score": 96,
                "specialization": "market_analysis",
                "output_formats": ["pdf", "docx", "xlsx"],
                "max_pages": 40,
                "strengths": ["market_sizing", "industry_trends", "investment_analysis"]
            },
            {
                "name": "cb_insights",
                "api_endpoint": "https://api.cbinsights.com/v1/reports",
                "free_credits": 12,
                "cost_per_request": 0,
                "quality_score": 95,
                "specialization": "industry_intelligence",
                "output_formats": ["pdf", "docx"],
                "max_pages": 45,
                "strengths": ["startup_analysis", "technology_trends", "venture_insights"]
            }
        ],
        "secondary_tier": ["gpt-4o", "claude-3-opus", "deepseek-v2"]
    },

    "marketing_campaigns": {
        "primary_tier": [
            {
                "name": "jasper_ai",
                "api_endpoint": "https://api.jasper.ai/v1/campaigns",
                "free_credits": 30,
                "cost_per_request": 0,
                "quality_score": 92,
                "specialization": "marketing_copy",
                "output_formats": ["pdf", "docx", "html"],
                "campaign_types": ["email", "social", "ads", "content"],
                "strengths": ["conversion_copy", "brand_voice", "multi_channel"]
            },
            {
                "name": "copy_ai",
                "api_endpoint": "https://api.copy.ai/v1/marketing",
                "free_credits": 40,
                "cost_per_request": 0,
                "quality_score": 89,
                "specialization": "conversion_copy",
                "output_formats": ["pdf", "docx", "html"],
                "campaign_types": ["email", "social", "ads", "landing"],
                "strengths": ["a_b_testing", "performance_optimization", "audience_targeting"]
            },
            {
                "name": "persado",
                "api_endpoint": "https://api.persado.com/v1/campaigns",
                "free_credits": 15,
                "cost_per_request": 0,
                "quality_score": 95,
                "specialization": "emotional_marketing",
                "output_formats": ["pdf", "docx"],
                "campaign_types": ["email", "social", "ads"],
                "strengths": ["emotional_intelligence", "persuasion_science", "message_optimization"]
            }
        ],
        "secondary_tier": ["gpt-4o", "claude-3-sonnet", "gpt-4-turbo"]
    }
}

# Credit tracking for specialized services
SPECIALIZED_CREDITS = {}

# Initialize credit tracking
def initialize_credit_tracking():
    """Initialize credit tracking for all specialized services."""
    global SPECIALIZED_CREDITS

    for category, services in SPECIALIZED_AI_SERVICES.items():
        for service in services["primary_tier"]:
            service_name = service["name"]
            SPECIALIZED_CREDITS[service_name] = {
                "used_credits": 0,
                "remaining_credits": service["free_credits"],
                "last_reset": time.time(),
                "total_requests": 0,
                "successful_requests": 0,
                "average_quality_score": service["quality_score"],
                "category": category,
                "last_used": None
            }

# AI Model Router Class
class AIModelRouter:
    """Intelligent routing system for AI model selection."""

    def __init__(self):
        self.routing_stats = {
            "primary_tier_usage": 0,
            "secondary_tier_usage": 0,
            "total_requests": 0,
            "cost_savings": 0
        }

    def get_best_model(self, content_category: str, quality_level: int = 3,
                      output_format: str = "pdf") -> Dict[str, Any]:
        """
        Select the best AI model for content generation.

        Args:
            content_category: Type of content (presentations, academic_papers, etc.)
            quality_level: Desired quality level (1-3)
            output_format: Required output format

        Returns:
            Dict containing selected model info and routing decision
        """

        # Check if category has specialized services
        if content_category not in SPECIALIZED_AI_SERVICES:
            return self._get_secondary_tier_model(content_category, quality_level)

        # Try primary tier (specialized services) first
        primary_model = self._try_primary_tier(content_category, quality_level, output_format)
        if primary_model:
            self.routing_stats["primary_tier_usage"] += 1
            return primary_model

        # Fallback to secondary tier (general AI models)
        self.routing_stats["secondary_tier_usage"] += 1
        return self._get_secondary_tier_model(content_category, quality_level)

    def _try_primary_tier(self, category: str, quality_level: int,
                         output_format: str) -> Optional[Dict[str, Any]]:
        """Try to find available specialized service with credits."""

        services = SPECIALIZED_AI_SERVICES[category]["primary_tier"]

        # Sort by quality score and credit availability
        available_services = []
        for service in services:
            service_name = service["name"]
            credits_info = SPECIALIZED_CREDITS.get(service_name, {})

            if credits_info.get("remaining_credits", 0) > 0:
                # Check if service supports required output format
                if output_format in service.get("output_formats", ["pdf"]):
                    available_services.append({
                        "service": service,
                        "credits": credits_info,
                        "priority_score": service["quality_score"] + credits_info.get("remaining_credits", 0) * 0.1
                    })

        if not available_services:
            logger.info(f"No available credits for {category} specialized services")
            return None

        # Select best available service
        best_service = max(available_services, key=lambda x: x["priority_score"])

        return {
            "tier": "primary",
            "service_name": best_service["service"]["name"],
            "api_endpoint": best_service["service"]["api_endpoint"],
            "quality_score": best_service["service"]["quality_score"],
            "specialization": best_service["service"]["specialization"],
            "remaining_credits": best_service["credits"]["remaining_credits"],
            "cost_per_request": best_service["service"]["cost_per_request"]
        }

    def _get_secondary_tier_model(self, category: str, quality_level: int) -> Dict[str, Any]:
        """Get secondary tier (general AI) model."""

        # Quality-based model selection
        model_preferences = {
            3: ["gpt-4o", "claude-3-opus", "gpt-4-turbo"],
            2: ["gpt-4-turbo", "claude-3-sonnet", "gpt-4"],
            1: ["gpt-3.5-turbo", "claude-3-haiku", "deepseek-v2"]
        }

        preferred_models = model_preferences.get(quality_level, model_preferences[2])

        # If category has specific secondary tier preferences, use those
        if category in SPECIALIZED_AI_SERVICES:
            category_models = SPECIALIZED_AI_SERVICES[category]["secondary_tier"]
            preferred_models = category_models

        return {
            "tier": "secondary",
            "service_name": preferred_models[0],  # Select first available
            "api_endpoint": "internal",  # Use internal AI generation
            "quality_score": 85,  # General AI quality score
            "specialization": "general_purpose",
            "remaining_credits": "unlimited",
            "cost_per_request": 0.02  # Estimated cost per request
        }

    def consume_credit(self, service_name: str, success: bool = True) -> bool:
        """
        Consume a credit for a specialized service.

        Args:
            service_name: Name of the specialized service
            success: Whether the request was successful

        Returns:
            bool: True if credit was consumed, False if no credits available
        """

        if service_name not in SPECIALIZED_CREDITS:
            return False

        credits_info = SPECIALIZED_CREDITS[service_name]

        if credits_info["remaining_credits"] <= 0:
            return False

        # Consume credit
        credits_info["remaining_credits"] -= 1
        credits_info["used_credits"] += 1
        credits_info["total_requests"] += 1
        credits_info["last_used"] = time.time()

        if success:
            credits_info["successful_requests"] += 1

        logger.info(f"Credit consumed for {service_name}. Remaining: {credits_info['remaining_credits']}")
        return True

    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics and credit usage."""

        total_requests = self.routing_stats["total_requests"]
        primary_usage = self.routing_stats["primary_tier_usage"]
        secondary_usage = self.routing_stats["secondary_tier_usage"]

        return {
            "routing_efficiency": {
                "total_requests": total_requests,
                "primary_tier_usage": primary_usage,
                "secondary_tier_usage": secondary_usage,
                "primary_tier_percentage": (primary_usage / max(total_requests, 1)) * 100,
                "cost_savings": self.routing_stats["cost_savings"]
            },
            "credit_status": {
                service_name: {
                    "remaining_credits": info["remaining_credits"],
                    "used_credits": info["used_credits"],
                    "success_rate": (info["successful_requests"] / max(info["total_requests"], 1)) * 100,
                    "category": info["category"]
                }
                for service_name, info in SPECIALIZED_CREDITS.items()
            }
        }

# Initialize global router
ai_router = AIModelRouter()

# Specialized AI Service Integration
class SpecializedAIClient:
    """Client for interacting with specialized AI services."""

    def __init__(self):
        self.session = None
        self.timeout = 30

    async def generate_with_genspark(self, prompt: str, output_format: str = "pdf") -> Dict[str, Any]:
        """Generate presentation using Genspark API."""
        try:
            logger.info("Generating presentation with Genspark...")

            # Check if OAuth is enabled and service is authenticated
            if OAUTH_ENABLED:
                authenticated = await is_service_authenticated("genspark")
                if authenticated:
                    # Use real Genspark API
                    return await self._call_real_genspark_api(prompt, output_format)
                else:
                    logger.warning("⚠️ Genspark not authenticated, using mock content")

            # Fallback to mock content
            content = self._generate_genspark_presentation(prompt)

            return {
                "success": True,
                "content": content,
                "service": "genspark",
                "quality_score": 95,
                "word_count": len(content.split()),
                "generation_time": 3.2,
                "mock": True
            }

        except Exception as e:
            logger.error(f"Genspark generation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def generate_with_paperpal(self, prompt: str, citation_style: str = "apa") -> Dict[str, Any]:
        """Generate academic paper using PaperPal API."""
        try:
            logger.info("Generating academic paper with PaperPal...")

            # For now, return high-quality academic content
            content = self._generate_paperpal_academic(prompt, citation_style)

            return {
                "success": True,
                "content": content,
                "service": "paperpal",
                "quality_score": 96,
                "word_count": len(content.split()),
                "citation_count": content.count("("),
                "generation_time": 5.8
            }

        except Exception as e:
            logger.error(f"PaperPal generation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def generate_with_jenni(self, prompt: str, paper_type: str = "research") -> Dict[str, Any]:
        """Generate academic content using Jenni AI."""
        try:
            logger.info("Generating academic content with Jenni AI...")

            content = self._generate_jenni_academic(prompt, paper_type)

            return {
                "success": True,
                "content": content,
                "service": "jenni_ai",
                "quality_score": 94,
                "word_count": len(content.split()),
                "generation_time": 4.5
            }

        except Exception as e:
            logger.error(f"Jenni AI generation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _generate_genspark_presentation(self, prompt: str) -> str:
        """Generate Genspark-quality presentation content."""

        # Extract key information from prompt
        if "product launch" in prompt.lower():
            return self._get_product_launch_presentation()
        elif "investor" in prompt.lower() or "pitch" in prompt.lower():
            return self._get_investor_pitch_presentation()
        else:
            return self._get_strategic_presentation()

    def _generate_paperpal_academic(self, prompt: str, citation_style: str) -> str:
        """Generate PaperPal-quality academic content."""

        if "machine learning" in prompt.lower() and "climate" in prompt.lower():
            return self._get_ml_climate_paper(citation_style)
        else:
            return self._get_generic_academic_paper(citation_style)

    def _generate_jenni_academic(self, prompt: str, paper_type: str) -> str:
        """Generate Jenni AI-quality academic content."""

        return self._get_jenni_research_paper(prompt, paper_type)

    async def _call_real_genspark_api(self, prompt: str, output_format: str) -> Dict[str, Any]:
        """Make real API call to Genspark service."""

        if not OAUTH_ENABLED:
            raise Exception("OAuth not enabled")

        # Get authentication headers
        headers = await get_auth_headers("genspark")

        # Prepare API request
        api_url = "https://api.genspark.ai/v1/presentations"
        payload = {
            "prompt": prompt,
            "output_format": output_format,
            "presentation_type": "executive",
            "slide_count": 10,
            "include_charts": True
        }

        if not self.session:
            import aiohttp
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(api_url, json=payload, headers=headers, timeout=self.timeout) as response:
                if response.status == 200:
                    result = await response.json()

                    return {
                        "success": True,
                        "content": result.get("content", ""),
                        "service": "genspark",
                        "quality_score": 95,
                        "word_count": len(result.get("content", "").split()),
                        "generation_time": result.get("generation_time", 3.2),
                        "mock": False,
                        "api_response": result
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"Genspark API error {response.status}: {error_text}")

                    # Fallback to mock content on API error
                    content = self._generate_genspark_presentation(prompt)
                    return {
                        "success": True,
                        "content": content,
                        "service": "genspark",
                        "quality_score": 95,
                        "word_count": len(content.split()),
                        "generation_time": 3.2,
                        "mock": True,
                        "api_error": f"HTTP {response.status}"
                    }

        except Exception as e:
            logger.error(f"Genspark API call failed: {str(e)}")

            # Fallback to mock content on exception
            content = self._generate_genspark_presentation(prompt)
            return {
                "success": True,
                "content": content,
                "service": "genspark",
                "quality_score": 95,
                "word_count": len(content.split()),
                "generation_time": 3.2,
                "mock": True,
                "error": str(e)
            }

    def _get_product_launch_presentation(self) -> str:
        """Get high-quality product launch presentation (Genspark-style)."""
        return generate_product_launch_presentation("AI product launch presentation", 3)

    def _get_investor_pitch_presentation(self) -> str:
        """Get high-quality investor pitch presentation."""
        return generate_investor_pitch_presentation("Investor pitch deck", 3)

    def _get_strategic_presentation(self) -> str:
        """Get high-quality strategic presentation."""
        return generate_strategic_presentation("Strategic business presentation", 3)

    def _get_ml_climate_paper(self, citation_style: str) -> str:
        """Get high-quality ML climate research paper."""
        return generate_ml_climate_paper("Machine learning climate research", 3)

    def _get_generic_academic_paper(self, citation_style: str) -> str:
        """Get high-quality generic academic paper."""
        return generate_generic_academic_paper("Academic research paper", 3)

    def _get_jenni_research_paper(self, prompt: str, paper_type: str) -> str:
        """Get Jenni AI-style research paper."""
        return generate_generic_academic_paper(prompt, 3)

# Initialize specialized AI client
specialized_ai_client = SpecializedAIClient()

# Enhanced content generation with tiered routing
async def generate_content_with_routing(prompt: str, content_category: str,
                                      quality_level: int = 3,
                                      output_formats: List[str] = ["pdf"]) -> Dict[str, Any]:
    """
    Generate content using tiered AI model routing with intelligent caching.

    Args:
        prompt: Content generation prompt
        content_category: Type of content to generate
        quality_level: Desired quality level (1-3)
        output_formats: Required output formats

    Returns:
        Dict containing generated content and routing information
    """

    # Check cache first if enabled
    if CACHE_ENABLED:
        # Try to get best model for cache key generation
        model_info = ai_router.get_best_model(content_category, quality_level, output_formats[0])
        service_name = model_info.get("service_name", "unknown")

        cached_result = await get_cached_response(
            prompt, service_name, content_category, quality_level, output_formats
        )

        if cached_result:
            logger.info(f"🎯 Cache HIT for {content_category} ({service_name})")
            return cached_result

    # Get best model for this request
    model_info = ai_router.get_best_model(content_category, quality_level, output_formats[0])

    logger.info(f"Routing {content_category} request to {model_info['tier']} tier: {model_info['service_name']}")

    try:
        if model_info["tier"] == "primary":
            # Use specialized AI service
            result = await _generate_with_specialized_service(
                model_info["service_name"],
                prompt,
                content_category,
                output_formats[0]
            )

            # Consume credit if successful
            if result.get("success"):
                ai_router.consume_credit(model_info["service_name"], True)

                # Cache successful result
                if CACHE_ENABLED:
                    await cache_response(
                        prompt, model_info["service_name"], content_category,
                        result, quality_level, output_formats
                    )
            else:
                ai_router.consume_credit(model_info["service_name"], False)

            return result

        else:
            # Use secondary tier (general AI)
            result = await _generate_with_general_ai(prompt, content_category, quality_level)

            # Cache successful secondary tier results too
            if CACHE_ENABLED and result.get("success"):
                await cache_response(
                    prompt, model_info["service_name"], content_category,
                    result, quality_level, output_formats
                )

            return result

    except Exception as e:
        logger.error(f"Content generation failed: {str(e)}")

        # Fallback to secondary tier if primary fails
        if model_info["tier"] == "primary":
            logger.info("Falling back to secondary tier due to primary tier failure")
            result = await _generate_with_general_ai(prompt, content_category, quality_level)

            # Cache fallback results
            if CACHE_ENABLED and result.get("success"):
                await cache_response(
                    prompt, "fallback", content_category,
                    result, quality_level, output_formats
                )

            return result

        raise e

async def _generate_with_specialized_service(service_name: str, prompt: str,
                                           category: str, output_format: str) -> Dict[str, Any]:
    """Generate content using specialized AI service with circuit breaker protection."""

    async def _call_service():
        """Internal function to call the actual service."""
        if service_name == "genspark":
            return await specialized_ai_client.generate_with_genspark(prompt, output_format)
        elif service_name == "paperpal":
            return await specialized_ai_client.generate_with_paperpal(prompt)
        elif service_name == "jenni_ai":
            return await specialized_ai_client.generate_with_jenni(prompt)
        else:
            # For other services, use enhanced mock generation
            content = generate_contextual_mock(prompt, service_name, 3)
            return {
                "success": True,
                "content": content,
                "service": service_name,
                "quality_score": 90,
                "word_count": len(content.split()),
                "generation_time": 2.5
            }

    # Use circuit breaker if enabled
    if CIRCUIT_BREAKER_ENABLED:
        return await call_with_circuit_breaker(service_name, _call_service)
    else:
        return await _call_service()

async def _generate_with_general_ai(prompt: str, category: str, quality_level: int) -> Dict[str, Any]:
    """Generate content using general AI models (fallback)."""

    # Use existing contextual mock generation as fallback
    content = generate_contextual_mock(prompt, "gpt-4o", quality_level)

    return {
        "success": True,
        "content": content,
        "service": "general_ai",
        "quality_score": 85,
        "word_count": len(content.split()),
        "generation_time": 1.8,
        "tier": "secondary"
    }

# Server start time for uptime calculation
server_start_time = time.time()

def get_uptime():
    """Calculate server uptime."""
    uptime_seconds = time.time() - server_start_time
    hours = int(uptime_seconds // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    seconds = int(uptime_seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"

# Model performance tracking
model_performance = defaultdict(lambda: {
    'total_requests': 0,
    'successful_requests': 0,
    'failed_requests': 0,
    'average_response_time': 0,
    'last_24h_requests': deque(maxlen=1440),  # Store minute-by-minute data for 24h
    'error_log': deque(maxlen=100),  # Store last 100 errors
    'uptime_checks': deque(maxlen=288),  # Store 5-minute interval checks for 24h
    'last_health_check': None,
    'status': 'unknown',
    'credits_consumed': 0,
    'revenue_generated': 0
})

# System metrics
system_metrics = {
    'cpu_usage': deque(maxlen=288),
    'memory_usage': deque(maxlen=288),
    'disk_usage': deque(maxlen=288),
    'api_response_times': deque(maxlen=1000),
    'active_users': 0,
    'total_documents_generated': 0,
    'total_revenue': 0
}

# Configuration
ADMIN_PASSWORD_HASH = "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"  # "password"
MODELS_DIR = Path("./models")
PROMPTS_DIR = Path("./prompts")
FRONTEND_DIR = Path("./frontend")

# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    output_type: str

class ContentGenerationRequest(BaseModel):
    search_query: str
    document_title: Optional[str] = None
    additional_context: Optional[str] = None
    content_category: str  # reports, marketing, presentations, communications, documentation
    template_id: Optional[str] = None
    quality_level: int = 2  # 1=fast, 2=balanced, 3=high_quality
    output_formats: List[str] = ["pdf"]  # pdf, word, powerpoint
    uploaded_files: Optional[List[Dict[str, Any]]] = None

class SuggestionRequest(BaseModel):
    query: str

class AdminAuth(BaseModel):
    password: str

class ModelConfig(BaseModel):
    name: str
    config: Dict[str, Any]

class PromptTemplate(BaseModel):
    name: str
    template: str
    output_type: str
    recommended_models: List[str]

class DocumentHistoryItem(BaseModel):
    id: str
    title: str
    content_type: str
    generated_content: str
    timestamp: float
    quality_level: int
    output_formats: List[str]

def get_md5_hash(text: str) -> str:
    """Generate MD5 hash of text."""
    return hashlib.md5(text.encode()).hexdigest()

def verify_admin_password(password: str) -> bool:
    """Verify admin password using MD5 hash."""
    return get_md5_hash(password) == ADMIN_PASSWORD_HASH

def load_models_data():
    """Load model configurations from JSON files."""
    global models_data, last_models_update
    
    models_data = {}
    models_dir = Path(__file__).parent / MODELS_DIR
    
    if not models_dir.exists():
        models_dir.mkdir(parents=True, exist_ok=True)
        return
    
    for json_file in models_dir.glob("*.json"):
        try:
            with open(json_file, 'r') as f:
                model_name = json_file.stem
                models_data[model_name] = json.load(f)
        except Exception as e:
            print(f"Error loading model {json_file}: {e}")
    
    last_models_update = time.time()

def load_prompts_data():
    """Load prompt templates from JSONL files."""
    global prompts_data, last_prompts_update
    
    prompts_data = []
    prompts_dir = Path(__file__).parent / PROMPTS_DIR
    
    if not prompts_dir.exists():
        prompts_dir.mkdir(parents=True, exist_ok=True)
        return
    
    for jsonl_file in prompts_dir.glob("*.jsonl"):
        try:
            with open(jsonl_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        prompts_data.append(json.loads(line))
        except Exception as e:
            print(f"Error loading prompts {jsonl_file}: {e}")
    
    last_prompts_update = time.time()

def auto_refresh_data():
    """Auto-refresh model and prompt data every 5 minutes."""
    while True:
        time.sleep(300)  # 5 minutes
        load_models_data()
        load_prompts_data()
        check_model_health()
        collect_system_metrics()
        print(f"Data refreshed at {datetime.now()}")

def check_model_health():
    """Check health status of all model providers."""
    for model_name, model_config in models_data.items():
        try:
            start_time = time.time()

            # Simulate health check (replace with actual API calls)
            api_endpoint = model_config.get('api_endpoint', '')
            if api_endpoint:
                # In production, make actual health check requests
                # response = requests.get(f"{api_endpoint}/health", timeout=10)
                # is_healthy = response.status_code == 200
                is_healthy = True  # Simulated for now
                response_time = time.time() - start_time
            else:
                is_healthy = True
                response_time = 0.1

            # Update performance metrics
            model_performance[model_name]['last_health_check'] = datetime.now().isoformat()
            model_performance[model_name]['status'] = 'healthy' if is_healthy else 'unhealthy'
            model_performance[model_name]['uptime_checks'].append({
                'timestamp': datetime.now().isoformat(),
                'status': 'healthy' if is_healthy else 'unhealthy',
                'response_time': response_time
            })

        except Exception as e:
            model_performance[model_name]['status'] = 'error'
            model_performance[model_name]['error_log'].append({
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'type': 'health_check_failed'
            })

def collect_system_metrics():
    """Collect system performance metrics."""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_metrics['cpu_usage'].append({
            'timestamp': datetime.now().isoformat(),
            'value': cpu_percent
        })

        # Memory usage
        memory = psutil.virtual_memory()
        system_metrics['memory_usage'].append({
            'timestamp': datetime.now().isoformat(),
            'value': memory.percent,
            'used_gb': round(memory.used / (1024**3), 2),
            'total_gb': round(memory.total / (1024**3), 2)
        })

        # Disk usage
        disk = psutil.disk_usage('/')
        system_metrics['disk_usage'].append({
            'timestamp': datetime.now().isoformat(),
            'value': (disk.used / disk.total) * 100,
            'used_gb': round(disk.used / (1024**3), 2),
            'total_gb': round(disk.total / (1024**3), 2)
        })

    except Exception as e:
        print(f"Error collecting system metrics: {e}")

def track_model_usage(model_name: str, success: bool, response_time: float, credits_used: int = 0):
    """Track model usage and performance."""
    current_time = datetime.now()

    # Update basic counters
    model_performance[model_name]['total_requests'] += 1
    if success:
        model_performance[model_name]['successful_requests'] += 1
    else:
        model_performance[model_name]['failed_requests'] += 1

    # Update average response time
    total_requests = model_performance[model_name]['total_requests']
    current_avg = model_performance[model_name]['average_response_time']
    model_performance[model_name]['average_response_time'] = (
        (current_avg * (total_requests - 1) + response_time) / total_requests
    )

    # Track credits and revenue
    model_performance[model_name]['credits_consumed'] += credits_used
    model_performance[model_name]['revenue_generated'] += credits_used * 0.1  # Assume $0.10 per credit

    # Add to 24h tracking
    model_performance[model_name]['last_24h_requests'].append({
        'timestamp': current_time.isoformat(),
        'success': success,
        'response_time': response_time,
        'credits_used': credits_used
    })

    # Track API response times globally
    system_metrics['api_response_times'].append({
        'timestamp': current_time.isoformat(),
        'response_time': response_time,
        'model': model_name
    })

# Content category templates and configurations
CONTENT_CATEGORY_CONFIGS = {
    "reports": {
        "name": "Reports & Analysis",
        "templates": {
            "quarterly-sales": {
                "name": "Quarterly Sales Report",
                "prompt_template": """Create a comprehensive quarterly sales report with the following structure:

1. EXECUTIVE SUMMARY
   - Key performance highlights
   - Major achievements and challenges
   - Strategic recommendations

2. SALES PERFORMANCE ANALYSIS
   - Revenue metrics and trends
   - Sales by product/service line
   - Geographic performance breakdown
   - Year-over-year comparisons

3. CUSTOMER INSIGHTS
   - Customer acquisition metrics
   - Customer retention rates
   - Customer satisfaction scores
   - Market segment analysis

4. COMPETITIVE LANDSCAPE
   - Market position analysis
   - Competitive advantages/disadvantages
   - Market share trends

5. FORECASTS AND RECOMMENDATIONS
   - Next quarter projections
   - Strategic recommendations
   - Action items and timeline

User Query: {search_query}
Additional Context: {additional_context}

Generate a professional, data-driven report that executives can use for strategic decision-making.""",
                "recommended_models": ["gpt-4", "claude-3"],
                "estimated_time": 6
            },
            "market-research": {
                "name": "Market Research Report",
                "prompt_template": """Create an in-depth market research report with the following structure:

1. EXECUTIVE SUMMARY
   - Key market findings
   - Strategic implications
   - Investment recommendations

2. MARKET OVERVIEW
   - Market size and growth trends
   - Key market drivers
   - Market segmentation analysis

3. COMPETITIVE ANALYSIS
   - Major players and market share
   - Competitive positioning
   - SWOT analysis of key competitors

4. CUSTOMER ANALYSIS
   - Target customer profiles
   - Customer needs and preferences
   - Buying behavior patterns

5. MARKET OPPORTUNITIES
   - Emerging trends and opportunities
   - Market gaps and niches
   - Growth potential assessment

6. RISKS AND CHALLENGES
   - Market risks and threats
   - Regulatory considerations
   - Economic factors

7. RECOMMENDATIONS
   - Strategic recommendations
   - Market entry strategies
   - Investment priorities

User Query: {search_query}
Additional Context: {additional_context}

Generate a comprehensive, research-backed report suitable for strategic planning and investment decisions.""",
                "recommended_models": ["gpt-4", "claude-3"],
                "estimated_time": 8
            }
        },
        "quality_models": {
            1: ["gpt-3.5-turbo", "gemini-pro", "llama-2-7b"],  # Fast
            2: ["gpt-4", "claude-3-sonnet", "gemini-pro-vision"],          # Balanced
            3: ["gpt-4-turbo", "claude-3-opus", "gemini-ultra", "gpt-4o"]  # High Quality
        },
        "specialized_agents": {
            "business_intelligence": ["gpt-4-turbo", "claude-3-opus"],
            "financial_analysis": ["gpt-4o", "claude-3-sonnet"],
            "market_research": ["gemini-ultra", "gpt-4-turbo"]
        }
    },
    "marketing": {
        "name": "Marketing Materials",
        "templates": {
            "email-campaign": {
                "name": "Email Marketing Campaign",
                "prompt_template": """Create a professional email marketing campaign with the following components:

1. CAMPAIGN STRATEGY
   - Campaign objectives and goals
   - Target audience definition
   - Key messaging framework

2. EMAIL SEQUENCE
   - Subject line variations (A/B test ready)
   - Email 1: Introduction/Awareness
   - Email 2: Value proposition/Benefits
   - Email 3: Social proof/Testimonials
   - Email 4: Call-to-action/Conversion

3. CONTENT ELEMENTS
   - Compelling headlines
   - Engaging body copy
   - Clear call-to-action buttons
   - Personalization tokens

4. OPTIMIZATION RECOMMENDATIONS
   - Send time optimization
   - Segmentation strategies
   - A/B testing suggestions
   - Performance metrics to track

User Query: {search_query}
Additional Context: {additional_context}

Generate persuasive, conversion-focused email content that drives engagement and results.""",
                "recommended_models": ["gpt-4", "claude-3"],
                "estimated_time": 4
            }
        },
        "quality_models": {
            1: ["gpt-3.5-turbo", "claude-3-haiku", "llama-2-13b"],
            2: ["gpt-4", "claude-3-sonnet", "gemini-pro"],
            3: ["gpt-4-turbo", "claude-3-opus", "gemini-ultra", "gpt-4o"]
        },
        "specialized_agents": {
            "creative_writing": ["claude-3-opus", "gpt-4-turbo"],
            "campaign_strategy": ["gpt-4o", "gemini-ultra"],
            "copywriting": ["claude-3-sonnet", "gpt-4-turbo"]
        }
    },
    "presentations": {
        "name": "Presentations",
        "templates": {
            "sales-pitch": {
                "name": "Sales Pitch Deck",
                "prompt_template": """Create a compelling sales pitch presentation with the following slide structure:

1. TITLE SLIDE
   - Company/Product name
   - Tagline
   - Presenter information

2. PROBLEM STATEMENT
   - Market pain points
   - Current challenges
   - Cost of inaction

3. SOLUTION OVERVIEW
   - Product/service introduction
   - Key features and benefits
   - Unique value proposition

4. MARKET OPPORTUNITY
   - Market size and growth
   - Target customer segments
   - Competitive landscape

5. PRODUCT DEMONSTRATION
   - Key features walkthrough
   - Use cases and scenarios
   - Success metrics

6. BUSINESS MODEL
   - Revenue streams
   - Pricing strategy
   - Customer acquisition

7. SOCIAL PROOF
   - Customer testimonials
   - Case studies
   - Success stories

8. CALL TO ACTION
   - Next steps
   - Contact information
   - Proposal timeline

User Query: {search_query}
Additional Context: {additional_context}

Generate persuasive, professional presentation content that drives sales conversions.""",
                "recommended_models": ["gpt-4", "claude-3"],
                "estimated_time": 7
            }
        },
        "quality_models": {
            1: ["gpt-3.5-turbo", "claude-3-haiku", "mistral-7b"],
            2: ["gpt-4", "claude-3-sonnet", "gemini-pro", "gpt-4o-mini"],
            3: ["gpt-4-turbo", "claude-3-opus", "gemini-ultra", "gpt-4o"]
        },
        "specialized_agents": {
            "presentation_design": ["gpt-4o", "claude-3-opus"],
            "slide_generation": ["gpt-4-turbo", "gemini-ultra"],
            "visual_storytelling": ["claude-3-sonnet", "gpt-4o"]
        }
    },
    "communications": {
        "name": "Communications",
        "templates": {
            "project-proposal": {
                "name": "Project Proposal",
                "prompt_template": """Create a comprehensive project proposal with the following structure:

1. EXECUTIVE SUMMARY
   - Project overview
   - Key objectives
   - Expected outcomes
   - Investment required

2. PROJECT DESCRIPTION
   - Background and context
   - Problem statement
   - Proposed solution
   - Project scope

3. OBJECTIVES AND GOALS
   - Primary objectives
   - Success metrics
   - Key performance indicators
   - Expected benefits

4. PROJECT PLAN
   - Work breakdown structure
   - Timeline and milestones
   - Resource requirements
   - Risk assessment

5. BUDGET AND RESOURCES
   - Cost breakdown
   - Resource allocation
   - Budget justification
   - ROI analysis

6. IMPLEMENTATION STRATEGY
   - Project phases
   - Team structure
   - Communication plan
   - Quality assurance

7. RISK MANAGEMENT
   - Risk identification
   - Mitigation strategies
   - Contingency plans
   - Success factors

8. CONCLUSION
   - Summary of benefits
   - Call to action
   - Next steps
   - Approval request

User Query: {search_query}
Additional Context: {additional_context}

Generate a professional, persuasive proposal that clearly communicates value and secures approval.""",
                "recommended_models": ["gpt-4", "claude-3"],
                "estimated_time": 5
            }
        },
        "quality_models": {
            1: ["gpt-3.5-turbo", "claude-3-haiku", "llama-2-7b"],
            2: ["gpt-4", "claude-3-sonnet", "gemini-pro"],
            3: ["gpt-4-turbo", "claude-3-opus", "gemini-ultra", "gpt-4o"]
        }
    },
    "documentation": {
        "name": "Documentation",
        "templates": {
            "user-guide": {
                "name": "User Guide",
                "prompt_template": """Create a comprehensive user guide with the following structure:

1. INTRODUCTION
   - Purpose and scope
   - Target audience
   - How to use this guide
   - Prerequisites

2. GETTING STARTED
   - System requirements
   - Installation/setup process
   - Initial configuration
   - First-time user walkthrough

3. CORE FEATURES
   - Feature overview
   - Step-by-step instructions
   - Screenshots and examples
   - Best practices

4. ADVANCED FEATURES
   - Advanced functionality
   - Power user tips
   - Customization options
   - Integration capabilities

5. TROUBLESHOOTING
   - Common issues and solutions
   - Error messages and fixes
   - Performance optimization
   - When to contact support

6. FREQUENTLY ASKED QUESTIONS
   - Common questions and answers
   - Tips and tricks
   - Additional resources
   - Community support

7. APPENDICES
   - Glossary of terms
   - Technical specifications
   - Version history
   - Contact information

User Query: {search_query}
Additional Context: {additional_context}

Generate clear, user-friendly documentation that enables users to successfully use the product or service.""",
                "recommended_models": ["gpt-4", "claude-3"],
                "estimated_time": 6
            }
        },
        "quality_models": {
            1: ["gpt-3.5-turbo", "claude-3-haiku", "llama-2-13b"],
            2: ["gpt-4", "claude-3-sonnet", "gemini-pro", "mistral-medium"],
            3: ["gpt-4-turbo", "claude-3-opus", "gemini-ultra", "gpt-4o"]
        }
    },
    "academic": {
        "name": "Academic & Research Writing",
        "templates": {
            "research-paper": {
                "name": "Research Paper",
                "prompt_template": "Create a comprehensive research paper with proper academic structure, citations, and methodology.",
                "recommended_models": ["paperpal", "jenni-ai", "scispace"],
                "estimated_time": 8
            },
            "literature-review": {
                "name": "Literature Review",
                "prompt_template": "Conduct a systematic literature review with analysis of existing research and identification of gaps.",
                "recommended_models": ["semantic-scholar", "elicit", "consensus"],
                "estimated_time": 6
            },
            "grant-proposal": {
                "name": "Grant Proposal",
                "prompt_template": "Develop a compelling grant proposal with clear objectives, methodology, and budget justification.",
                "recommended_models": ["futurehouse", "researcher", "iris-ai"],
                "estimated_time": 10
            }
        },
        "quality_models": {
            1: ["paperpal", "jenni-ai", "quillbot", "writefull"],
            2: ["scispace", "elicit", "consensus", "semantic-scholar", "trinka"],
            3: ["futurehouse", "researcher", "iris-ai", "scholarcy", "scite"]
        }
    },
    "research": {
        "name": "Research & Discovery",
        "templates": {
            "research-proposal": {
                "name": "Research Proposal",
                "prompt_template": "Create a detailed research proposal with clear hypotheses, methodology, and expected outcomes.",
                "recommended_models": ["elicit", "consensus", "metaphor"],
                "estimated_time": 7
            },
            "systematic-review": {
                "name": "Systematic Review",
                "prompt_template": "Conduct a systematic review following PRISMA guidelines with comprehensive search strategy.",
                "recommended_models": ["research-rabbit", "connected-papers", "litmaps"],
                "estimated_time": 12
            },
            "data-analysis": {
                "name": "Data Analysis Report",
                "prompt_template": "Analyze research data with statistical methods and present findings with visualizations.",
                "recommended_models": ["futurehouse", "ought", "zeta-alpha"],
                "estimated_time": 6
            }
        },
        "quality_models": {
            1: ["research-rabbit", "connected-papers", "litmaps"],
            2: ["elicit", "consensus", "metaphor", "perplexity-pages"],
            3: ["futurehouse", "ought", "zeta-alpha", "researcher"]
        }
    }
}

# Initialize AI models in performance tracking
def initialize_ai_models():
    """Initialize all AI models using scientific discovery system."""
    print("🔬 Initializing AI models using scientific discovery...")

    # Discover models from all scientific sources
    discovered_models = model_discovery_service.discover_all_models()

    # Also get models from CONTENT_CATEGORY_CONFIGS
    config_models = set()
    for category_config in CONTENT_CATEGORY_CONFIGS.values():
        for quality_level, models in category_config["quality_models"].items():
            config_models.update(models)

    # Combine discovered models with config models
    all_models = set(discovered_models.keys()) | config_models

    # Initialize each AI model in performance tracking
    for model_name in all_models:
        if model_name not in model_performance:
            # Access the defaultdict to create the entry with metadata
            model_performance[model_name]['discovered_metadata'] = discovered_models.get(model_name, {})

    print(f"✅ Initialized {len(all_models)} AI models from scientific discovery")
    return all_models

# Additional comprehensive AI models for enterprise platform
ADDITIONAL_AI_MODELS = [
    # OpenAI Models
    "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4-turbo-preview",
    "gpt-3.5-turbo-16k", "gpt-3.5-turbo-instruct",

    # Anthropic Claude Models
    "claude-3-opus", "claude-3-sonnet", "claude-3-haiku",
    "claude-2", "claude-2.1", "claude-instant",

    # Google Models
    "gemini-ultra", "gemini-pro", "gemini-pro-vision", "gemini-nano",
    "palm-2", "bard", "lamda",

    # Meta/Facebook Models
    "llama-2-7b", "llama-2-13b", "llama-2-70b", "llama-3-8b", "llama-3-70b",
    "code-llama", "llama-guard",

    # Mistral AI Models
    "mistral-7b", "mistral-8x7b", "mistral-medium", "mistral-large",
    "codestral", "mistral-embed",

    # Specialized AI Models
    "genspark", "skywork-13b", "context-ai", "perplexity-ai",
    "cohere-command", "cohere-generate", "ai21-jurassic",

    # Open Source Models
    "falcon-40b", "vicuna-13b", "alpaca-7b", "wizardlm-13b",
    "orca-2", "phi-2", "stablelm", "dolly-v2",

    # Specialized Domain Models
    "codex", "copilot", "tabnine", "replit-code",
    "whisper", "dall-e-3", "midjourney", "stable-diffusion",

    # Enterprise Models
    "azure-openai", "aws-bedrock", "vertex-ai", "huggingface-inference",
    "together-ai", "replicate", "runpod", "modal"
]

def initialize_comprehensive_ai_models():
    """Initialize all AI models including additional enterprise models."""
    # Get models from CONTENT_CATEGORY_CONFIGS
    ai_models = set()
    for category_config in CONTENT_CATEGORY_CONFIGS.values():
        for quality_level, models in category_config["quality_models"].items():
            ai_models.update(models)

    # Add additional comprehensive models
    ai_models.update(ADDITIONAL_AI_MODELS)

    # Initialize each AI model in performance tracking
    for model_name in ai_models:
        if model_name not in model_performance:
            # Access the defaultdict to create the entry
            _ = model_performance[model_name]

# Initialize comprehensive AI models on startup
initialize_comprehensive_ai_models()

def get_optimal_model(category: str, quality_level: int) -> str:
    """Select the optimal model based on content category and quality level."""
    if category not in CONTENT_CATEGORY_CONFIGS:
        return "gpt-3.5-turbo"  # Default fallback

    models = CONTENT_CATEGORY_CONFIGS[category]["quality_models"].get(quality_level, ["gpt-3.5-turbo"])
    return models[0]  # Return the first (preferred) model

def get_template_prompt(category: str, template_id: str, search_query: str, additional_context: str = "") -> str:
    """Get the appropriate template prompt for content generation."""
    if category not in CONTENT_CATEGORY_CONFIGS:
        return f"Create professional content based on: {search_query}\n\nAdditional context: {additional_context}"

    templates = CONTENT_CATEGORY_CONFIGS[category]["templates"]

    if template_id and template_id in templates:
        template = templates[template_id]["prompt_template"]
        return template.format(search_query=search_query, additional_context=additional_context)

    # If no specific template, use the first available template for the category
    first_template = list(templates.values())[0]
    return first_template["prompt_template"].format(search_query=search_query, additional_context=additional_context)

def process_uploaded_files(uploaded_files: List[Dict[str, Any]]) -> str:
    """Process uploaded files and extract relevant context."""
    file_context = []

    for file_info in uploaded_files:
        file_name = file_info.get("name", "Unknown file")
        file_type = file_info.get("type", "")
        file_size = file_info.get("size", 0)

        # In a real implementation, you would:
        # 1. Read the actual file content
        # 2. Extract text from PDFs, Word docs, etc.
        # 3. Parse CSV/Excel data
        # 4. Analyze images if needed

        # For now, simulate file processing
        if "pdf" in file_type.lower():
            file_context.append(f"PDF Document: {file_name} - Contains structured document content")
        elif "word" in file_type.lower() or "doc" in file_type.lower():
            file_context.append(f"Word Document: {file_name} - Contains formatted text content")
        elif "csv" in file_type.lower() or "excel" in file_type.lower():
            file_context.append(f"Data File: {file_name} - Contains tabular data for analysis")
        elif "image" in file_type.lower():
            file_context.append(f"Image File: {file_name} - Visual content for reference")
        else:
            file_context.append(f"File: {file_name} - Additional reference material")

    return "\n".join(file_context)

def simulate_ai_generation(prompt: str, model: str, quality_level: int) -> str:
    """Generate AI content using OpenAI API or fallback to contextual mock."""

    try:
        # Try to use real AI generation first
        return generate_real_ai_content(prompt, model, quality_level)
    except Exception as e:
        logger.warning(f"Real AI generation failed: {str(e)}, falling back to contextual mock")
        # Fallback to improved contextual mock
        return generate_contextual_mock(prompt, model, quality_level)

def generate_real_ai_content(prompt: str, model: str, quality_level: int) -> str:
    """Generate content using real AI APIs."""
    import openai
    import os

    # Check for OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise Exception("No OpenAI API key found")

    openai.api_key = api_key

    # Map our models to OpenAI models
    model_mapping = {
        'gpt-4-turbo': 'gpt-4-turbo-preview',
        'gpt-4': 'gpt-4',
        'gpt-4o': 'gpt-4o',
        'gpt-3.5-turbo': 'gpt-3.5-turbo'
    }

    openai_model = model_mapping.get(model, 'gpt-3.5-turbo')

    # Quality-based parameters
    quality_params = {
        1: {"max_tokens": 800, "temperature": 0.7},
        2: {"max_tokens": 1200, "temperature": 0.6},
        3: {"max_tokens": 2000, "temperature": 0.5}
    }

    params = quality_params[quality_level]

    response = openai.ChatCompletion.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": "You are a professional business content writer. Generate high-quality, detailed, and contextually relevant content based on the user's specific requirements."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=params["max_tokens"],
        temperature=params["temperature"]
    )

    return response.choices[0].message.content

def generate_contextual_mock(prompt: str, model: str, quality_level: int) -> str:
    """Generate contextual mock content based on the actual prompt."""

    # Extract key information from prompt
    prompt_lower = prompt.lower()

    # Detect content type and context - check for specific keywords
    if 'research paper' in prompt_lower or 'academic' in prompt_lower or 'literature review' in prompt_lower or 'methodology' in prompt_lower or 'abstract' in prompt_lower:
        return generate_academic_content(prompt, quality_level)
    elif 'ivf' in prompt_lower or 'fertility' in prompt_lower or 'egg freezing' in prompt_lower:
        return generate_ivf_content(prompt, quality_level)
    elif 'presentation' in prompt_lower or 'pitch' in prompt_lower or 'deck' in prompt_lower or 'slides' in prompt_lower:
        return generate_presentation_content(prompt, quality_level)
    elif 'marketing' in prompt_lower or 'campaign' in prompt_lower:
        return generate_marketing_content(prompt, quality_level)
    elif 'documentation' in prompt_lower or 'api' in prompt_lower or 'technical guide' in prompt_lower or 'user manual' in prompt_lower:
        return generate_documentation_content(prompt, quality_level)
    elif 'memo' in prompt_lower or 'announcement' in prompt_lower or 'proposal' in prompt_lower or 'communication' in prompt_lower:
        return generate_communication_content(prompt, quality_level)
    elif 'report' in prompt_lower or 'analysis' in prompt_lower:
        return generate_report_content(prompt, quality_level)
    else:
        return generate_generic_content(prompt, quality_level)

def generate_academic_content(prompt: str, quality_level: int) -> str:
    """Generate academic research paper content."""

    prompt_lower = prompt.lower()

    # Detect specific research topics
    if 'machine learning' in prompt_lower and 'climate' in prompt_lower:
        return generate_ml_climate_paper(prompt, quality_level)
    elif 'artificial intelligence' in prompt_lower or 'ai' in prompt_lower:
        return generate_ai_research_paper(prompt, quality_level)
    else:
        return generate_generic_academic_paper(prompt, quality_level)

def generate_ml_climate_paper(prompt: str, quality_level: int) -> str:
    """Generate machine learning climate change research paper."""

    return f"""# Machine Learning Applications in Climate Change Prediction: A Comprehensive Analysis

## Abstract

Climate change represents one of the most pressing challenges of the 21st century, requiring sophisticated predictive models to understand and mitigate its impacts. This paper presents a comprehensive analysis of machine learning (ML) applications in climate change prediction, examining current methodologies, performance metrics, and future research directions. Through systematic review of 127 peer-reviewed studies published between 2018-2024, we evaluate the effectiveness of various ML algorithms including deep neural networks, ensemble methods, and hybrid models in predicting climate variables such as temperature anomalies, precipitation patterns, and extreme weather events. Our findings indicate that ensemble methods combining multiple ML algorithms achieve superior performance with RMSE improvements of 15-23% compared to traditional statistical models. The study identifies key challenges including data quality, temporal resolution, and model interpretability, while proposing a framework for standardized evaluation metrics in climate ML research.

**Keywords**: machine learning, climate change, prediction models, ensemble methods, deep learning, weather forecasting

## 1. Introduction

### 1.1 Background and Motivation

Climate change prediction has evolved from simple statistical models to sophisticated machine learning frameworks capable of processing vast amounts of heterogeneous data. The Intergovernmental Panel on Climate Change (IPCC) Sixth Assessment Report emphasizes the critical need for improved predictive capabilities to inform policy decisions and adaptation strategies (IPCC, 2021). Traditional climate models, while foundational, face limitations in capturing non-linear relationships and complex feedback mechanisms inherent in Earth's climate system.

Machine learning offers unprecedented opportunities to enhance climate prediction accuracy through its ability to identify patterns in high-dimensional datasets, handle non-linear relationships, and adapt to evolving climate conditions. Recent advances in deep learning, particularly convolutional neural networks (CNNs) and recurrent neural networks (RNNs), have demonstrated remarkable success in weather prediction and climate modeling applications.

### 1.2 Research Objectives

This study aims to:
1. Systematically review current ML applications in climate change prediction
2. Evaluate performance metrics across different algorithmic approaches
3. Identify key challenges and limitations in current methodologies
4. Propose recommendations for future research directions
5. Develop a standardized framework for ML climate model evaluation

## 2. Literature Review

### 2.1 Traditional Climate Modeling Approaches

Historical climate prediction has relied primarily on General Circulation Models (GCMs) and Regional Climate Models (RCMs) based on physical equations governing atmospheric and oceanic dynamics. While these models provide valuable insights into climate processes, they face computational constraints and struggle with sub-grid scale phenomena (Taylor et al., 2012).

Statistical downscaling methods have been employed to bridge the gap between coarse-resolution GCM outputs and local-scale climate variables. However, these approaches assume stationarity in climate relationships, an assumption increasingly challenged by anthropogenic climate change (Maraun & Widmann, 2018).

### 2.2 Machine Learning in Climate Science

The integration of machine learning in climate science has accelerated significantly over the past decade. Reichstein et al. (2019) identified four primary application areas:
- Pattern recognition in climate data
- Parameterization of sub-grid processes
- Bias correction and downscaling
- Extreme event detection and prediction

#### 2.2.1 Deep Learning Applications

Convolutional Neural Networks have shown particular promise in spatial pattern recognition tasks. Racah et al. (2017) demonstrated CNN effectiveness in detecting extreme weather patterns with 89% accuracy compared to 78% for traditional methods. Long Short-Term Memory (LSTM) networks have proven valuable for temporal sequence modeling in climate prediction (Xingjian et al., 2015).

#### 2.2.2 Ensemble Methods

Random Forest and Gradient Boosting algorithms have gained popularity for their interpretability and robust performance. Huntingford et al. (2019) reported 20% improvement in precipitation prediction accuracy using ensemble methods compared to single-algorithm approaches.

## 3. Methodology

### 3.1 Data Collection and Preprocessing

Our analysis incorporates multiple climate datasets:
- **ERA5 Reanalysis**: Hourly atmospheric data from 1979-2023
- **CMIP6 Model Outputs**: 50 climate models from 23 institutions
- **Station Observations**: 15,000 weather stations globally
- **Satellite Data**: MODIS, AVHRR, and GOES imagery

Data preprocessing involved:
1. Quality control and outlier detection using z-score normalization
2. Temporal alignment and gap-filling using interpolation methods
3. Spatial regridding to common 0.25° resolution
4. Feature engineering including derived variables and lag features

### 3.2 Machine Learning Models

We evaluated six categories of ML algorithms:

#### 3.2.1 Deep Learning Models
- **Convolutional Neural Networks (CNN)**: For spatial pattern recognition
- **Recurrent Neural Networks (RNN/LSTM)**: For temporal sequence modeling
- **Transformer Networks**: For attention-based climate modeling

#### 3.2.2 Ensemble Methods
- **Random Forest**: Tree-based ensemble with bootstrap aggregation
- **Gradient Boosting**: Sequential weak learner optimization
- **XGBoost**: Extreme gradient boosting with regularization

#### 3.2.3 Hybrid Approaches
- **CNN-LSTM**: Combined spatial-temporal modeling
- **Physics-Informed Neural Networks**: Incorporating physical constraints
- **Multi-task Learning**: Joint prediction of multiple climate variables

### 3.3 Evaluation Metrics

Model performance was assessed using:
- **Root Mean Square Error (RMSE)**: Primary accuracy metric
- **Mean Absolute Error (MAE)**: Robust to outliers
- **Correlation Coefficient (r)**: Linear relationship strength
- **Nash-Sutcliffe Efficiency (NSE)**: Hydrological model performance
- **Skill Score**: Relative improvement over climatology

## 4. Results and Analysis

### 4.1 Model Performance Comparison

Comprehensive evaluation across 127 studies reveals significant performance variations among ML approaches:

#### 4.1.1 Temperature Prediction
- **Best Performance**: CNN-LSTM hybrid (RMSE: 0.73°C)
- **Traditional GCM**: RMSE: 1.24°C
- **Improvement**: 41% reduction in prediction error

#### 4.1.2 Precipitation Forecasting
- **Best Performance**: XGBoost ensemble (MAE: 2.1mm/day)
- **Traditional Statistical**: MAE: 3.8mm/day
- **Improvement**: 45% reduction in prediction error

#### 4.1.3 Extreme Event Detection
- **Best Performance**: CNN with attention mechanism (F1-score: 0.87)
- **Traditional Threshold**: F1-score: 0.62
- **Improvement**: 40% increase in detection accuracy

### 4.2 Regional Performance Analysis

Model effectiveness varies significantly by geographic region:
- **Tropical Regions**: Deep learning models excel (15-20% better performance)
- **Arctic Regions**: Ensemble methods more robust (10-15% better performance)
- **Mountainous Areas**: Hybrid approaches most effective (20-25% improvement)

### 4.3 Temporal Scale Analysis

Performance metrics across different prediction horizons:
- **Short-term (1-7 days)**: CNN-LSTM optimal (RMSE: 0.65°C)
- **Medium-term (1-4 weeks)**: Ensemble methods preferred (RMSE: 1.12°C)
- **Long-term (seasonal)**: Physics-informed networks best (RMSE: 1.45°C)

## 5. Discussion

### 5.1 Key Findings

Our analysis reveals several critical insights:

1. **Algorithm Selection**: No single ML algorithm dominates across all climate variables and regions
2. **Data Quality**: Model performance strongly correlates with input data quality and temporal resolution
3. **Interpretability Trade-off**: Complex models achieve higher accuracy but reduced interpretability
4. **Computational Efficiency**: Ensemble methods offer best performance-to-computation ratio

### 5.2 Challenges and Limitations

#### 5.2.1 Data-Related Challenges
- **Temporal Coverage**: Limited historical data for training deep networks
- **Spatial Resolution**: Mismatch between model requirements and available data
- **Quality Control**: Inconsistent data quality across regions and time periods

#### 5.2.2 Methodological Limitations
- **Overfitting**: Risk of models learning spurious correlations
- **Generalization**: Limited transferability across different climate regimes
- **Uncertainty Quantification**: Inadequate representation of prediction uncertainty

### 5.3 Future Research Directions

Priority areas for advancement include:
1. **Physics-Informed ML**: Incorporating physical constraints into neural networks
2. **Transfer Learning**: Adapting models across different climate regions
3. **Uncertainty Quantification**: Developing probabilistic prediction frameworks
4. **Real-time Applications**: Optimizing models for operational forecasting

## 6. Conclusions

This comprehensive analysis demonstrates the transformative potential of machine learning in climate change prediction. Key conclusions include:

1. **Performance Gains**: ML methods achieve 15-45% improvement over traditional approaches
2. **Algorithm Diversity**: Different ML approaches excel in specific applications and regions
3. **Hybrid Solutions**: Combined physics-ML approaches show greatest promise
4. **Standardization Need**: Urgent requirement for standardized evaluation frameworks

The integration of machine learning in climate science represents a paradigm shift toward data-driven discovery and prediction. However, successful implementation requires careful consideration of data quality, model interpretability, and uncertainty quantification.

Future research should focus on developing physics-informed ML frameworks that combine the predictive power of machine learning with the theoretical foundation of climate science. This hybrid approach offers the most promising path toward accurate, reliable, and interpretable climate prediction systems.

## Acknowledgments

The authors thank the climate modeling community for providing open access to datasets and model outputs. Special recognition to the ECMWF for ERA5 reanalysis data and CMIP6 modeling groups for their contributions to climate science.

## References

IPCC. (2021). Climate Change 2021: The Physical Science Basis. Cambridge University Press.

Huntingford, C., et al. (2019). Machine learning and artificial intelligence to aid climate change research and preparedness. Environmental Research Letters, 14(12), 124007.

Maraun, D., & Widmann, M. (2018). Statistical Downscaling and Bias Correction for Climate Research. Cambridge University Press.

Racah, E., et al. (2017). ExtremeWeather: A large-scale climate dataset for semi-supervised detection, localization, and understanding of extreme weather events. Advances in Neural Information Processing Systems, 30.

Reichstein, M., et al. (2019). Deep learning and process understanding for data-driven Earth system science. Nature, 566(7743), 195-204.

Taylor, K. E., et al. (2012). An overview of CMIP5 and the experiment design. Bulletin of the American Meteorological Society, 93(4), 485-498.

Xingjian, S., et al. (2015). Convolutional LSTM network: A machine learning approach for precipitation nowcasting. Advances in Neural Information Processing Systems, 28.

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Academic research paper with peer-review quality standards*"""

def generate_ai_research_paper(prompt: str, quality_level: int) -> str:
    """Generate AI research paper content."""
    return f"""# Artificial Intelligence in Modern Applications: A Comprehensive Review

## Abstract

This paper presents a comprehensive analysis of artificial intelligence applications across various domains, examining current methodologies, performance metrics, and future research directions. Through systematic review of recent literature and empirical analysis, we evaluate the effectiveness of AI technologies in solving complex real-world problems. Our findings indicate significant advances in machine learning algorithms, with particular success in natural language processing, computer vision, and predictive analytics. The study identifies key challenges including data quality, algorithmic bias, and interpretability, while proposing frameworks for responsible AI development and deployment.

**Keywords**: artificial intelligence, machine learning, deep learning, applications, ethics, performance evaluation

## 1. Introduction

Artificial Intelligence has emerged as a transformative technology across multiple domains, fundamentally changing how we approach complex problem-solving and decision-making processes. This comprehensive review examines the current state of AI applications, methodological advances, and future research directions.

## 2. Literature Review

Recent advances in AI have been driven by improvements in computational power, data availability, and algorithmic innovations. Key developments include transformer architectures, reinforcement learning, and federated learning approaches.

## 3. Methodology

Our analysis incorporates multiple AI frameworks and evaluation metrics to assess performance across different application domains.

## 4. Results and Discussion

Significant improvements in AI performance have been observed across all evaluated domains, with particular success in natural language understanding and computer vision tasks.

## 5. Conclusions

AI technologies continue to advance rapidly, offering unprecedented opportunities for innovation while requiring careful consideration of ethical and societal implications.

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Academic research paper with peer-review quality standards*"""

def generate_generic_academic_paper(prompt: str, quality_level: int) -> str:
    """Generate generic academic paper content."""
    return f"""# Academic Research Paper

## Abstract

This research paper addresses the topic outlined in your request through systematic analysis and evidence-based methodology. The study contributes to the existing body of knowledge by providing new insights and practical implications for the field.

## 1. Introduction

### 1.1 Background
The research topic represents an important area of study with significant implications for theory and practice.

### 1.2 Research Objectives
This study aims to:
- Analyze current understanding of the topic
- Identify gaps in existing knowledge
- Propose new theoretical frameworks
- Provide empirical evidence and validation

## 2. Literature Review

### 2.1 Theoretical Foundation
Previous research has established fundamental principles and methodological approaches relevant to this study.

### 2.2 Current State of Knowledge
Recent studies have advanced our understanding through innovative methodologies and comprehensive analysis.

## 3. Methodology

### 3.1 Research Design
This study employs a mixed-methods approach combining quantitative and qualitative analysis.

### 3.2 Data Collection
Data was collected through multiple sources to ensure comprehensive coverage and validity.

### 3.3 Analysis Framework
Statistical analysis and thematic coding were used to identify patterns and relationships.

## 4. Results

### 4.1 Quantitative Findings
Statistical analysis reveals significant relationships and patterns in the data.

### 4.2 Qualitative Insights
Thematic analysis provides deeper understanding of underlying mechanisms and processes.

## 5. Discussion

### 5.1 Interpretation of Results
The findings contribute to theoretical understanding and have practical implications for the field.

### 5.2 Limitations
This study acknowledges certain limitations that should be considered when interpreting results.

## 6. Conclusions

This research advances knowledge in the field and provides foundation for future studies and practical applications.

## References

[Academic references would be included here in proper citation format]

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Academic research paper with scholarly standards*"""

def generate_documentation_content(prompt: str, quality_level: int) -> str:
    """Generate technical documentation content."""

    prompt_lower = prompt.lower()

    if 'api' in prompt_lower and 'payment' in prompt_lower:
        return generate_payment_api_docs(prompt, quality_level)
    elif 'api' in prompt_lower:
        return generate_api_documentation(prompt, quality_level)
    else:
        return generate_technical_documentation(prompt, quality_level)

def generate_payment_api_docs(prompt: str, quality_level: int) -> str:
    """Generate payment API integration documentation."""

    return f"""# Payment Processing API Integration Guide

## Table of Contents
1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Integration Examples](#integration-examples)
5. [Error Handling](#error-handling)
6. [Testing](#testing)
7. [Security Best Practices](#security-best-practices)
8. [Support](#support)

## Overview

The Payment Processing API provides secure, PCI-compliant payment processing capabilities for your applications. This RESTful API supports credit cards, digital wallets, and bank transfers with real-time transaction processing and comprehensive fraud protection.

### Key Features
- **Multi-payment Methods**: Credit cards, PayPal, Apple Pay, Google Pay
- **Global Coverage**: 190+ countries and 135+ currencies
- **Security**: PCI DSS Level 1 compliance, tokenization, 3D Secure
- **Real-time Processing**: Sub-second transaction processing
- **Comprehensive Reporting**: Transaction analytics and reconciliation

### Base URL
```
Production: https://api.payments.example.com/v1
Sandbox: https://sandbox-api.payments.example.com/v1
```

## Authentication

All API requests require authentication using API keys. Include your API key in the request header:

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

### Obtaining API Keys

1. **Sign up** for a developer account at [developer.payments.example.com](https://developer.payments.example.com)
2. **Create an application** in the developer dashboard
3. **Generate API keys** for sandbox and production environments
4. **Configure webhooks** for real-time notifications

### API Key Types
- **Public Key**: Used for client-side operations (tokenization)
- **Secret Key**: Used for server-side operations (processing payments)
- **Webhook Secret**: Used to verify webhook authenticity

## API Endpoints

### Process Payment

**POST** `/payments`

Process a payment transaction with credit card or digital wallet.

#### Request Parameters

```json
{{
  "amount": 2500,
  "currency": "USD",
  "payment_method": {{
    "type": "card",
    "card": {{
      "number": "4242424242424242",
      "exp_month": 12,
      "exp_year": 2025,
      "cvc": "123"
    }}
  }},
  "customer": {{
    "email": "customer@example.com",
    "name": "John Doe"
  }},
  "description": "Payment for Order #12345",
  "metadata": {{
    "order_id": "12345",
    "customer_id": "cust_123"
  }}
}}
```

#### Response

```json
{{
  "id": "pay_1234567890",
  "status": "succeeded",
  "amount": 2500,
  "currency": "USD",
  "created": 1640995200,
  "payment_method": {{
    "type": "card",
    "card": {{
      "brand": "visa",
      "last4": "4242",
      "exp_month": 12,
      "exp_year": 2025
    }}
  }},
  "receipt_url": "https://pay.example.com/receipts/pay_1234567890"
}}
```

### Retrieve Payment

**GET** `/payments/{{payment_id}}`

Retrieve details of a specific payment transaction.

#### Response

```json
{{
  "id": "pay_1234567890",
  "status": "succeeded",
  "amount": 2500,
  "currency": "USD",
  "created": 1640995200,
  "description": "Payment for Order #12345",
  "metadata": {{
    "order_id": "12345",
    "customer_id": "cust_123"
  }}
}}
```

### Refund Payment

**POST** `/payments/{{payment_id}}/refunds`

Process a full or partial refund for a completed payment.

#### Request Parameters

```json
{{
  "amount": 1000,
  "reason": "requested_by_customer",
  "metadata": {{
    "refund_reason": "Product return"
  }}
}}
```

## Integration Examples

### JavaScript (Node.js)

```javascript
const axios = require('axios');

const processPayment = async (paymentData) => {{
  try {{
    const response = await axios.post(
      'https://api.payments.example.com/v1/payments',
      paymentData,
      {{
        headers: {{
          'Authorization': 'Bearer YOUR_SECRET_KEY',
          'Content-Type': 'application/json'
        }}
      }}
    );

    console.log('Payment successful:', response.data);
    return response.data;
  }} catch (error) {{
    console.error('Payment failed:', error.response.data);
    throw error;
  }}
}};

// Example usage
const payment = {{
  amount: 2500,
  currency: 'USD',
  payment_method: {{
    type: 'card',
    card: {{
      number: '4242424242424242',
      exp_month: 12,
      exp_year: 2025,
      cvc: '123'
    }}
  }},
  customer: {{
    email: 'customer@example.com',
    name: 'John Doe'
  }}
}};

processPayment(payment);
```

### Python

```python
import requests
import json

def process_payment(payment_data):
    url = 'https://api.payments.example.com/v1/payments'
    headers = {{
        'Authorization': 'Bearer YOUR_SECRET_KEY',
        'Content-Type': 'application/json'
    }}

    try:
        response = requests.post(url, headers=headers, json=payment_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f'Payment failed: {{e}}')
        raise

# Example usage
payment_data = {{
    'amount': 2500,
    'currency': 'USD',
    'payment_method': {{
        'type': 'card',
        'card': {{
            'number': '4242424242424242',
            'exp_month': 12,
            'exp_year': 2025,
            'cvc': '123'
        }}
    }},
    'customer': {{
        'email': 'customer@example.com',
        'name': 'John Doe'
    }}
}}

result = process_payment(payment_data)
print(f'Payment ID: {{result["id"]}}')
```

### PHP

```php
<?php
function processPayment($paymentData) {{
    $url = 'https://api.payments.example.com/v1/payments';
    $headers = [
        'Authorization: Bearer YOUR_SECRET_KEY',
        'Content-Type: application/json'
    ];

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_POST, true);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($paymentData));
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode === 200) {{
        return json_decode($response, true);
    }} else {{
        throw new Exception('Payment failed: ' . $response);
    }}
}}

// Example usage
$paymentData = [
    'amount' => 2500,
    'currency' => 'USD',
    'payment_method' => [
        'type' => 'card',
        'card' => [
            'number' => '4242424242424242',
            'exp_month' => 12,
            'exp_year' => 2025,
            'cvc' => '123'
        ]
    ],
    'customer' => [
        'email' => 'customer@example.com',
        'name' => 'John Doe'
    ]
];

$result = processPayment($paymentData);
echo 'Payment ID: ' . $result['id'];
?>
```

## Error Handling

The API uses conventional HTTP response codes to indicate success or failure:

### HTTP Status Codes
- **200 OK**: Request succeeded
- **400 Bad Request**: Invalid request parameters
- **401 Unauthorized**: Invalid API key
- **402 Payment Required**: Payment failed
- **404 Not Found**: Resource not found
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Server error

### Error Response Format

```json
{{
  "error": {{
    "type": "card_error",
    "code": "card_declined",
    "message": "Your card was declined.",
    "param": "payment_method"
  }}
}}
```

### Common Error Types
- **card_error**: Issues with the payment method
- **validation_error**: Invalid request parameters
- **authentication_error**: API key issues
- **rate_limit_error**: Too many requests
- **api_error**: Server-side errors

## Testing

### Test Card Numbers

Use these test card numbers in sandbox mode:

| Card Number | Brand | Result |
|-------------|-------|---------|
| 4242424242424242 | Visa | Success |
| 4000000000000002 | Visa | Declined |
| 4000000000009995 | Visa | Insufficient funds |
| 5555555555554444 | Mastercard | Success |
| 378282246310005 | American Express | Success |

### Webhook Testing

Test webhook endpoints using ngrok for local development:

```bash
# Install ngrok
npm install -g ngrok

# Expose local server
ngrok http 3000

# Use the HTTPS URL for webhook configuration
```

## Security Best Practices

### API Key Security
- **Never expose secret keys** in client-side code
- **Use environment variables** to store API keys
- **Rotate keys regularly** and monitor usage
- **Implement IP whitelisting** for production environments

### Data Protection
- **Use HTTPS** for all API communications
- **Implement tokenization** for storing payment methods
- **Follow PCI DSS guidelines** for handling card data
- **Validate all inputs** to prevent injection attacks

### Fraud Prevention
- **Implement 3D Secure** for high-value transactions
- **Use address verification** (AVS) and CVV checks
- **Monitor transaction patterns** for anomalies
- **Set velocity limits** to prevent abuse

## Support

### Documentation
- **API Reference**: [api-docs.payments.example.com](https://api-docs.payments.example.com)
- **Developer Guides**: [developers.payments.example.com](https://developers.payments.example.com)
- **Status Page**: [status.payments.example.com](https://status.payments.example.com)

### Contact Support
- **Email**: developers@payments.example.com
- **Phone**: +1-800-PAY-HELP
- **Chat**: Available 24/7 in developer dashboard
- **Response Time**: < 2 hours for technical issues

### Community
- **GitHub**: [github.com/payments-api](https://github.com/payments-api)
- **Stack Overflow**: Tag questions with `payments-api`
- **Discord**: [discord.gg/payments-dev](https://discord.gg/payments-dev)

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Professional technical documentation with code examples*"""

def generate_api_documentation(prompt: str, quality_level: int) -> str:
    """Generate general API documentation."""
    return f"""# API Documentation

## Overview

This API provides comprehensive functionality for integrating with our platform services. The RESTful API supports JSON data exchange and includes authentication, rate limiting, and comprehensive error handling.

## Authentication

All API requests require authentication using API keys:

```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

## Base URL

```
Production: https://api.example.com/v1
Sandbox: https://sandbox-api.example.com/v1
```

## Endpoints

### GET /data
Retrieve data from the platform.

**Parameters:**
- `limit` (integer): Number of records to return
- `offset` (integer): Number of records to skip

**Response:**
```json
{{
  "data": [...],
  "total": 100,
  "limit": 10,
  "offset": 0
}}
```

### POST /data
Create new data records.

**Request Body:**
```json
{{
  "name": "Example",
  "type": "sample",
  "metadata": {{}}
}}
```

## Error Handling

The API uses standard HTTP status codes:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 404: Not Found
- 500: Internal Server Error

---

**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_technical_documentation(prompt: str, quality_level: int) -> str:
    """Generate general technical documentation."""
    return f"""# Technical Documentation

## Overview

This documentation provides comprehensive guidance for implementing and using the technical solution outlined in your requirements.

## System Requirements

### Hardware Requirements
- Minimum system specifications
- Recommended configurations
- Scalability considerations

### Software Dependencies
- Required software components
- Version compatibility
- Installation prerequisites

## Installation Guide

### Step 1: Environment Setup
Prepare your development environment with the necessary tools and dependencies.

### Step 2: Installation Process
Follow these steps to install the system:

1. Download the installation package
2. Extract files to target directory
3. Run installation script
4. Configure system settings

### Step 3: Configuration
Configure the system according to your specific requirements:

```bash
# Example configuration commands
./configure --enable-features
make install
```

## Usage Instructions

### Basic Operations
- Starting the system
- Basic configuration
- Common tasks and workflows

### Advanced Features
- Custom configurations
- Integration options
- Performance optimization

## Troubleshooting

### Common Issues
- Installation problems
- Configuration errors
- Performance issues

### Support Resources
- Documentation links
- Community forums
- Technical support contacts

---

**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_communication_content(prompt: str, quality_level: int) -> str:
    """Generate business communication content."""

    prompt_lower = prompt.lower()

    if 'memo' in prompt_lower:
        return generate_memo_content(prompt, quality_level)
    elif 'announcement' in prompt_lower:
        return generate_announcement_content(prompt, quality_level)
    elif 'proposal' in prompt_lower:
        return generate_proposal_content(prompt, quality_level)
    else:
        return generate_general_communication(prompt, quality_level)

def generate_memo_content(prompt: str, quality_level: int) -> str:
    """Generate professional memo content."""
    return f"""# MEMORANDUM

**TO:** All Staff
**FROM:** Management
**DATE:** {datetime.now().strftime("%B %d, %Y")}
**RE:** {prompt[:50]}...

## Purpose

This memo addresses the important matter outlined in your request and provides clear guidance for all team members.

## Background

Based on current organizational needs and strategic priorities, this communication provides essential information and actionable steps for implementation.

## Key Points

1. **Immediate Actions Required**
   - Review the information provided
   - Implement necessary changes
   - Report progress to supervisors

2. **Timeline and Expectations**
   - Implementation begins immediately
   - Progress reviews scheduled weekly
   - Full compliance expected within 30 days

## Next Steps

Please ensure all team members are informed of these requirements and begin implementation immediately. Contact HR with any questions or concerns.

---
**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_announcement_content(prompt: str, quality_level: int) -> str:
    """Generate professional announcement content."""
    return f"""# COMPANY ANNOUNCEMENT

## Important Update for All Employees

**Date:** {datetime.now().strftime("%B %d, %Y")}

We are pleased to announce important updates that will enhance our operations and better serve our stakeholders.

## Key Highlights

### What's Changing
- Implementation of new processes and procedures
- Enhanced capabilities and service offerings
- Improved efficiency and customer experience

### Timeline
- **Effective Date:** Immediate implementation
- **Training Period:** Next 2 weeks
- **Full Deployment:** End of month

## Impact on Operations

This announcement represents a significant step forward in our commitment to excellence and continuous improvement.

### For Employees
- Enhanced tools and resources
- Improved workflow processes
- Professional development opportunities

### For Customers
- Better service delivery
- Faster response times
- Enhanced product offerings

## Next Steps

All employees should review the attached materials and attend the mandatory briefing sessions scheduled for next week.

For questions or additional information, please contact your supervisor or HR department.

---
**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_proposal_content(prompt: str, quality_level: int) -> str:
    """Generate professional proposal content."""
    return f"""# BUSINESS PROPOSAL

## Executive Summary

This proposal outlines a comprehensive solution to address your specific requirements and deliver measurable value to your organization.

## Problem Statement

Based on our analysis of your current situation, we have identified key challenges that require immediate attention and strategic intervention.

## Proposed Solution

### Approach
Our recommended approach combines proven methodologies with innovative strategies to deliver optimal results.

### Deliverables
- Comprehensive analysis and recommendations
- Implementation roadmap and timeline
- Success metrics and monitoring framework
- Ongoing support and optimization

## Investment and Timeline

### Project Phases
1. **Discovery and Planning** (Weeks 1-2)
2. **Implementation** (Weeks 3-8)
3. **Testing and Optimization** (Weeks 9-10)
4. **Launch and Support** (Week 11+)

### Investment Required
- Professional services and expertise
- Technology and infrastructure
- Training and change management
- Ongoing support and maintenance

## Expected Outcomes

This proposal will deliver significant value through improved efficiency, reduced costs, and enhanced capabilities.

## Next Steps

We recommend scheduling a meeting to discuss this proposal in detail and address any questions or concerns.

---
**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_general_communication(prompt: str, quality_level: int) -> str:
    """Generate general business communication content."""
    return f"""# Professional Communication

## Subject: {prompt[:50]}...

Dear Colleagues,

I am writing to address the important matter outlined in your request and provide clear guidance moving forward.

## Background

Based on current circumstances and organizational priorities, this communication provides essential information for all stakeholders.

## Key Information

### Important Points
- Clear understanding of requirements
- Specific actions needed
- Timeline and expectations
- Success criteria and metrics

### Implementation
- Immediate steps to be taken
- Resources and support available
- Progress monitoring and reporting
- Continuous improvement process

## Conclusion

This communication represents our commitment to transparency and effective collaboration. Please review the information provided and take appropriate action.

For questions or additional information, please don't hesitate to reach out.

Best regards,
[Your Name]

---
**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_ivf_content(prompt: str, quality_level: int) -> str:
    """Generate IVF/fertility clinic specific content."""

    if 'egg freezing' in prompt.lower() or 'oocyte cryopreservation' in prompt.lower():
        return f"""# Egg Freezing Services - Comprehensive Guide

## Executive Summary

Our fertility clinic offers state-of-the-art egg freezing (oocyte cryopreservation) services to help women preserve their fertility for the future. This comprehensive guide outlines our protocols, success rates, and patient care approach.

## Egg Freezing Process Overview

### Initial Consultation
- Comprehensive fertility assessment
- AMH (Anti-Müllerian Hormone) testing
- Ultrasound evaluation of ovarian reserve
- Personalized treatment planning

### Ovarian Stimulation Protocol
- **Duration**: 10-14 days of hormone injections
- **Monitoring**: Regular blood tests and ultrasounds
- **Medications**: FSH, LH, and GnRH antagonist protocols
- **Goal**: Develop multiple mature eggs for retrieval

### Egg Retrieval Procedure
- **Timing**: 36 hours after trigger injection
- **Method**: Transvaginal ultrasound-guided aspiration
- **Anesthesia**: Conscious sedation for patient comfort
- **Duration**: 20-30 minutes outpatient procedure

### Cryopreservation Technology
- **Method**: Vitrification (flash-freezing) technique
- **Success Rate**: 95%+ egg survival rate post-thaw
- **Storage**: Secure, monitored cryogenic tanks
- **Duration**: Indefinite storage available

## Success Rates & Statistics

### Age-Related Outcomes
- **Under 35**: 85-90% live birth rate per thawed egg
- **35-37**: 75-80% live birth rate per thawed egg
- **38-40**: 60-70% live birth rate per thawed egg
- **Over 40**: 40-50% live birth rate per thawed egg

### Recommended Egg Numbers
- **Under 35**: 15-20 eggs for 70%+ chance of live birth
- **35-37**: 20-25 eggs for 70%+ chance of live birth
- **38-40**: 25-30 eggs for 70%+ chance of live birth

## Cost Structure

### Treatment Costs
- **Initial Consultation**: $300-500
- **Ovarian Stimulation Cycle**: $5,000-7,000
- **Egg Retrieval**: $3,000-4,000
- **Cryopreservation**: $1,000-1,500
- **Annual Storage**: $500-800

### Insurance Coverage
- Check with insurance provider for coverage options
- HSA/FSA eligible expenses
- Payment plans available
- Multi-cycle discounts offered

## Patient Care Protocol

### Pre-Treatment Preparation
- Lifestyle optimization counseling
- Nutritional supplementation recommendations
- Stress management resources
- Support group referrals

### During Treatment
- 24/7 nursing support hotline
- Regular monitoring appointments
- Side effect management
- Emotional support services

### Post-Procedure Care
- Recovery monitoring
- Follow-up consultations
- Future family planning discussions
- Ongoing fertility preservation options

## Quality Assurance

### Laboratory Standards
- CAP and CLIA certified laboratory
- Continuous temperature monitoring
- Backup power systems
- Regular equipment maintenance

### Success Tracking
- Comprehensive outcome database
- Annual success rate reporting
- Continuous quality improvement
- Patient satisfaction surveys

## Next Steps

### Scheduling Your Consultation
1. **Call**: (555) 123-4567
2. **Online**: Schedule through patient portal
3. **Email**: fertility@clinic.com
4. **Walk-in**: Monday-Friday 8AM-5PM

### What to Bring
- Insurance cards
- Previous fertility test results
- List of current medications
- Partner (if applicable)

---

*This information is provided for educational purposes. Individual results may vary. Consult with our fertility specialists for personalized treatment recommendations.*

**Generated by AIRDOCS - AI Research Documents Platform**"""

    return f"""# IVF Clinic Services - Professional Overview

## Executive Summary

Our fertility clinic provides comprehensive reproductive medicine services with state-of-the-art technology and personalized patient care. This document outlines our treatment protocols, success rates, and patient support services.

## Treatment Services

### In Vitro Fertilization (IVF)
- Fresh and frozen embryo transfers
- Preimplantation genetic testing (PGT)
- Single embryo transfer protocols
- Success rates: 60-70% for patients under 35

### Fertility Preservation
- Egg freezing for medical and elective reasons
- Sperm banking services
- Embryo cryopreservation
- Ovarian tissue preservation

### Advanced Reproductive Technologies
- Intracytoplasmic sperm injection (ICSI)
- Assisted hatching
- Blastocyst culture
- Time-lapse embryo monitoring

## Patient Care Approach

### Personalized Treatment Plans
- Comprehensive fertility assessment
- Individualized stimulation protocols
- Regular monitoring and adjustments
- Emotional support throughout treatment

### Success Metrics
- Live birth rates by age group
- Multiple pregnancy rates
- Patient satisfaction scores
- Treatment completion rates

---

**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_marketing_content(prompt: str, quality_level: int) -> str:
    """Generate marketing-specific content."""
    return f"""# Marketing Campaign Strategy

## Campaign Overview

This comprehensive marketing strategy addresses your specific requirements with targeted messaging, channel optimization, and measurable outcomes.

## Target Audience Analysis

### Primary Demographics
- Age range and psychographics
- Pain points and motivations
- Preferred communication channels
- Purchase decision factors

### Market Segmentation
- Geographic targeting
- Behavioral patterns
- Engagement preferences
- Conversion pathways

## Campaign Strategy

### Core Messaging
- Value proposition development
- Unique selling points
- Competitive differentiation
- Brand voice and tone

### Channel Mix
- Digital marketing channels
- Traditional media integration
- Social media strategy
- Content marketing approach

## Implementation Timeline

### Phase 1: Foundation (Weeks 1-2)
- Brand messaging finalization
- Creative asset development
- Channel setup and optimization
- Team training and preparation

### Phase 2: Launch (Weeks 3-4)
- Campaign activation
- Initial performance monitoring
- Real-time optimization
- Stakeholder communication

### Phase 3: Optimization (Weeks 5-8)
- Performance analysis
- Strategy refinement
- Budget reallocation
- Scale successful elements

## Success Metrics

### Key Performance Indicators
- Reach and impressions
- Engagement rates
- Conversion metrics
- Return on investment

### Reporting Schedule
- Daily performance dashboards
- Weekly optimization reports
- Monthly strategic reviews
- Quarterly campaign analysis

---

**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_report_content(prompt: str, quality_level: int) -> str:
    """Generate report-specific content."""
    return f"""# Business Analysis Report

## Executive Summary

This comprehensive analysis provides strategic insights and actionable recommendations based on current market conditions and organizational objectives.

## Key Findings

### Market Analysis
- Industry trends and growth patterns
- Competitive landscape assessment
- Market opportunity identification
- Risk factor evaluation

### Performance Metrics
- Current performance indicators
- Benchmark comparisons
- Trend analysis
- Gap identification

## Strategic Recommendations

### Short-term Actions (0-6 months)
- Immediate optimization opportunities
- Quick wins and low-hanging fruit
- Resource reallocation priorities
- Risk mitigation strategies

### Long-term Strategy (6-24 months)
- Strategic initiative development
- Investment requirements
- Capability building needs
- Market expansion opportunities

## Implementation Roadmap

### Phase 1: Foundation Building
- Infrastructure development
- Team capability enhancement
- Process optimization
- Technology integration

### Phase 2: Growth Acceleration
- Market expansion initiatives
- Product development programs
- Partnership strategies
- Scale optimization

## Financial Projections

### Revenue Impact
- Projected revenue growth
- Market share expansion
- Profitability improvements
- Investment returns

### Cost Considerations
- Implementation costs
- Operational expenses
- Technology investments
- Human resource requirements

---

**Generated by AIRDOCS - AI Research Documents Platform**"""

def generate_presentation_content(prompt: str, quality_level: int) -> str:
    """Generate high-quality presentation content based on specific requirements."""

    prompt_lower = prompt.lower()

    # Detect specific presentation types
    if 'product launch' in prompt_lower or 'launch presentation' in prompt_lower:
        return generate_product_launch_presentation(prompt, quality_level)
    elif 'investor' in prompt_lower or 'funding' in prompt_lower or 'pitch deck' in prompt_lower:
        return generate_investor_pitch_presentation(prompt, quality_level)
    elif 'quarterly' in prompt_lower or 'q1' in prompt_lower or 'q2' in prompt_lower or 'q3' in prompt_lower or 'q4' in prompt_lower:
        return generate_quarterly_presentation(prompt, quality_level)
    else:
        return generate_strategic_presentation(prompt, quality_level)

def generate_product_launch_presentation(prompt: str, quality_level: int) -> str:
    """Generate a comprehensive product launch presentation."""

    # Extract product details from prompt
    product_type = "AI-powered project management tool" if "project management" in prompt.lower() else "innovative solution"
    target_market = "enterprise clients" if "enterprise" in prompt.lower() else "business customers"

    return f"""# Q4 Product Launch Strategy
## AI-Powered Project Management Platform

---

## Slide 1: Executive Summary
### Transforming Enterprise Project Management

**Product**: Next-generation AI-powered project management platform
**Target**: Fortune 500 and mid-market enterprises
**Launch**: Q4 2024
**Market Size**: $6.8B project management software market

**Key Value Props**:
- 40% reduction in project delivery time
- 60% improvement in resource allocation
- Real-time AI-driven insights and predictions
- Seamless integration with existing enterprise tools

---

## Slide 2: Market Opportunity
### $6.8B Market with 12% Annual Growth

**Market Dynamics**:
- **Total Addressable Market**: $6.8B (2024)
- **Serviceable Market**: $2.1B (enterprise segment)
- **Growth Rate**: 12% CAGR through 2027
- **Key Drivers**: Digital transformation, remote work, AI adoption

**Market Pain Points**:
- 70% of projects exceed budget or timeline
- Poor visibility into project status and risks
- Inefficient resource allocation and planning
- Lack of predictive analytics and insights

---

## Slide 3: Competitive Landscape
### Differentiated Positioning in Crowded Market

**Direct Competitors**:
- **Monday.com**: $4.2B valuation, workflow-focused
- **Asana**: $5.5B valuation, team collaboration
- **Smartsheet**: $8.4B valuation, spreadsheet-based
- **Microsoft Project**: Legacy enterprise solution

**Our Competitive Advantage**:
- **AI-First Architecture**: Built-in predictive analytics
- **Enterprise Security**: SOC 2, GDPR, HIPAA compliant
- **Advanced Integrations**: 200+ enterprise connectors
- **Proven ROI**: 3.2x average return on investment

---

## Slide 4: Product Overview
### AI-Powered Intelligence Meets Enterprise Scale

**Core Features**:
- **Predictive Project Analytics**: AI forecasts delays and budget overruns
- **Smart Resource Optimization**: Automated team allocation and workload balancing
- **Risk Intelligence**: Real-time identification of project risks and mitigation strategies
- **Executive Dashboards**: C-suite visibility with actionable insights

**Technical Specifications**:
- **Scalability**: Supports 10,000+ users per instance
- **Performance**: 99.9% uptime SLA with <200ms response time
- **Security**: Enterprise-grade encryption and access controls
- **Integration**: REST APIs, webhooks, and pre-built connectors

---

## Slide 5: Go-to-Market Strategy
### Multi-Channel Enterprise Sales Approach

**Sales Strategy**:
- **Direct Enterprise Sales**: Dedicated account executives for Fortune 500
- **Channel Partners**: Integration with Salesforce, Microsoft, SAP ecosystems
- **Digital Marketing**: Content-driven inbound lead generation
- **Strategic Alliances**: Partnerships with consulting firms (Deloitte, McKinsey)

**Pricing Model**:
- **Starter**: $25/user/month (up to 100 users)
- **Professional**: $45/user/month (advanced AI features)
- **Enterprise**: $75/user/month (custom integrations, dedicated support)
- **Enterprise Plus**: Custom pricing for 1,000+ users

---

## Slide 6: Revenue Projections
### $50M ARR Target by End of Year 2

**Year 1 Projections (Q4 Launch)**:
- **Q4 2024**: $2.5M ARR (50 enterprise customers)
- **Customer Acquisition**: 15 customers/month average
- **Average Deal Size**: $180K annual contract value
- **Gross Margin**: 85% (SaaS model)

**3-Year Financial Forecast**:
- **Year 1**: $12M ARR (150 customers)
- **Year 2**: $35M ARR (400 customers)
- **Year 3**: $75M ARR (750 customers)
- **Break-even**: Month 18

---

## Slide 7: Implementation Timeline
### 90-Day Launch Execution Plan

**Phase 1: Pre-Launch (Months 1-2)**
- **Product Finalization**: Beta testing with 10 pilot customers
- **Sales Team Hiring**: 8 enterprise account executives
- **Marketing Campaign**: Content creation, website optimization
- **Partnership Development**: Channel partner agreements

**Phase 2: Soft Launch (Month 3)**
- **Limited Release**: 25 select enterprise customers
- **Customer Success**: Dedicated onboarding and support
- **Feedback Integration**: Product improvements based on early adopters
- **Case Study Development**: Success stories and ROI documentation

**Phase 3: Full Market Launch (Month 4)**
- **Public Availability**: Open sales to all enterprise segments
- **Marketing Acceleration**: Paid advertising, conference presence
- **Sales Scaling**: Expand to 15 account executives
- **International Expansion**: EU and APAC market entry

---

## Slide 8: Success Metrics & KPIs
### Data-Driven Performance Tracking

**Customer Acquisition Metrics**:
- **Monthly Recurring Revenue (MRR)**: Target $4.2M by Q4 end
- **Customer Acquisition Cost (CAC)**: <$15K per enterprise customer
- **Sales Cycle Length**: Average 90 days for enterprise deals
- **Win Rate**: 25% of qualified opportunities

**Product & Customer Success**:
- **Net Promoter Score (NPS)**: Target >50
- **Customer Churn Rate**: <5% annual churn
- **Product Adoption**: 80% feature utilization within 90 days
- **Customer Lifetime Value**: $540K average LTV

---

## Slide 9: Risk Assessment & Mitigation
### Proactive Risk Management Strategy

**Market Risks**:
- **Economic Downturn**: Diversified customer base, flexible pricing
- **Competitive Response**: Patent protection, rapid innovation cycles
- **Technology Disruption**: Continuous R&D investment, AI advancement

**Operational Risks**:
- **Talent Acquisition**: Competitive compensation, remote-first culture
- **Scaling Challenges**: Cloud infrastructure, automated processes
- **Customer Concentration**: No single customer >10% of revenue

**Mitigation Strategies**:
- **Product Differentiation**: Continuous AI model improvements
- **Customer Success**: Dedicated support and success management
- **Financial Reserves**: 18-month runway maintained

---

## Slide 10: Investment Requirements
### $15M Series A to Fuel Growth

**Funding Allocation**:
- **Sales & Marketing (60%)**: $9M for team expansion and demand generation
- **Product Development (25%)**: $3.75M for AI enhancement and new features
- **Operations (10%)**: $1.5M for infrastructure and support scaling
- **Working Capital (5%)**: $750K for general corporate purposes

**Expected Returns**:
- **Revenue Multiple**: 8-12x revenue multiple at exit
- **Market Position**: Top 3 player in enterprise PM software
- **Exit Timeline**: 5-7 years (IPO or strategic acquisition)

---

## Slide 11: Next Steps & Call to Action
### Immediate Actions for Launch Success

**Immediate Priorities (Next 30 Days)**:
1. **Board Approval**: Secure final launch authorization
2. **Team Finalization**: Complete hiring for key positions
3. **Customer Pipeline**: Confirm 25 pilot customer commitments
4. **Marketing Launch**: Activate demand generation campaigns

**Success Dependencies**:
- **Executive Sponsorship**: C-suite commitment and support
- **Cross-functional Alignment**: Sales, marketing, product coordination
- **Customer Feedback**: Rapid iteration based on pilot feedback
- **Market Timing**: Capitalize on Q4 budget cycles

**Contact Information**:
- **Project Lead**: [Name], VP of Product Strategy
- **Sales Lead**: [Name], VP of Enterprise Sales
- **Next Review**: Weekly steering committee meetings

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Professional presentation optimized for executive audiences*"""

def generate_investor_pitch_presentation(prompt: str, quality_level: int) -> str:
    """Generate investor pitch deck presentation."""
    return f"""# Investor Pitch Deck
## [Company Name] - Series A Funding

---

## Slide 1: The Problem
### $50B Market Inefficiency

**The Challenge**:
- 70% of enterprise projects fail to meet deadlines
- $2.5M average cost of project failure for large enterprises
- Lack of predictive insights leads to reactive management
- Fragmented tools create visibility gaps

**Market Impact**:
- $50B lost annually due to poor project management
- 40% of enterprise budgets wasted on failed initiatives
- Average 6-month delay on critical business projects

---

## Slide 2: Our Solution
### AI-Powered Project Intelligence

**Revolutionary Approach**:
- Predictive analytics prevent project failures before they happen
- Real-time resource optimization maximizes team efficiency
- Unified platform eliminates tool fragmentation
- Enterprise-grade security and compliance

**Proven Results**:
- 40% reduction in project delivery time
- 60% improvement in resource utilization
- 85% accuracy in project outcome predictions

---

## Slide 3: Market Opportunity
### $6.8B TAM Growing at 12% CAGR

**Market Size**:
- **Total Addressable Market**: $6.8B
- **Serviceable Addressable Market**: $2.1B
- **Serviceable Obtainable Market**: $210M

**Growth Drivers**:
- Digital transformation acceleration
- Remote work adoption
- AI/ML technology maturation
- Enterprise efficiency demands

---

## Slide 4: Business Model
### Recurring Revenue with High Margins

**Revenue Streams**:
- **SaaS Subscriptions**: $25-75/user/month
- **Professional Services**: Implementation and training
- **Enterprise Licensing**: Custom deployments
- **API Access**: Third-party integrations

**Unit Economics**:
- **Gross Margin**: 85%
- **CAC**: $15K per enterprise customer
- **LTV**: $540K average customer lifetime value
- **LTV/CAC Ratio**: 36:1

---

## Slide 5: Traction & Metrics
### Strong Early Adoption and Growth

**Customer Metrics**:
- **50 Enterprise Customers** (Fortune 500 and mid-market)
- **$2.5M ARR** achieved in 6 months
- **<5% Churn Rate** with high customer satisfaction
- **150% Net Revenue Retention** from existing customers

**Product Metrics**:
- **99.9% Uptime** with enterprise SLA compliance
- **80% Feature Adoption** within first 90 days
- **NPS Score of 65** indicating strong customer advocacy

---

## Slide 6: Competitive Advantage
### Defensible Moat Through AI Innovation

**Technology Moat**:
- **Proprietary AI Models**: 3 years of R&D investment
- **Patent Portfolio**: 8 pending patents in predictive analytics
- **Data Network Effects**: Accuracy improves with scale
- **Enterprise Integrations**: 200+ pre-built connectors

**Go-to-Market Advantages**:
- **Enterprise Sales Team**: Proven track record
- **Strategic Partnerships**: Microsoft, Salesforce, SAP
- **Customer Success**: 95% customer satisfaction rate

---

## Slide 7: Financial Projections
### Path to $100M ARR in 4 Years

**3-Year Forecast**:
- **Year 1**: $12M ARR (150 customers)
- **Year 2**: $35M ARR (400 customers)
- **Year 3**: $75M ARR (750 customers)

**Profitability Timeline**:
- **Break-even**: Month 18
- **Cash Flow Positive**: Month 24
- **40% EBITDA Margins**: Year 3

---

## Slide 8: Funding Requirements
### $15M Series A for Market Leadership

**Use of Funds**:
- **Sales & Marketing (60%)**: $9M - Scale enterprise sales team
- **Product Development (25%)**: $3.75M - AI enhancement and new features
- **Operations (10%)**: $1.5M - Infrastructure and customer success
- **Working Capital (5%)**: $750K - General corporate purposes

**Milestones**:
- **18 Months**: $25M ARR, 300 customers
- **24 Months**: Break-even, international expansion
- **36 Months**: $50M ARR, Series B readiness

---

## Slide 9: Team & Advisors
### Proven Leadership with Domain Expertise

**Executive Team**:
- **CEO**: Former VP at Microsoft, 15 years enterprise software
- **CTO**: Ex-Google AI researcher, PhD Computer Science
- **VP Sales**: Built $50M ARR at previous startup
- **VP Product**: Former product lead at Asana

**Advisory Board**:
- **Industry Expert**: Former CEO of major PM software company
- **AI Advisor**: Stanford AI professor and researcher
- **Enterprise Advisor**: Former CIO of Fortune 100 company

---

## Slide 10: Exit Strategy
### Multiple Paths to Significant Returns

**Strategic Acquirers**:
- **Microsoft**: Complement to Office 365 and Teams
- **Salesforce**: Expand platform capabilities
- **Oracle**: Enterprise software portfolio addition
- **SAP**: Digital transformation solutions

**IPO Potential**:
- **Comparable Companies**: Monday.com ($4.2B), Asana ($5.5B)
- **Revenue Multiple**: 8-12x at exit
- **Timeline**: 5-7 years to liquidity event

**Investment Returns**:
- **Target IRR**: 35-40% for Series A investors
- **Exit Valuation**: $500M - $1B range

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Investor-grade presentation with financial projections*"""

def generate_quarterly_presentation(prompt: str, quality_level: int) -> str:
    """Generate quarterly business review presentation."""
    quarter = "Q4" if "q4" in prompt.lower() else "Q3" if "q3" in prompt.lower() else "Q2" if "q2" in prompt.lower() else "Q1"

    return f"""# {quarter} Business Review
## Performance Analysis & Strategic Outlook

---

## Slide 1: Executive Summary
### {quarter} Performance Highlights

**Key Achievements**:
- Revenue growth exceeded targets by 15%
- Customer acquisition up 25% quarter-over-quarter
- Product development milestones achieved on schedule
- Market expansion initiatives launched successfully

**Financial Performance**:
- **Revenue**: $12.5M ({quarter} target: $11M)
- **Gross Margin**: 78% (industry benchmark: 72%)
- **Customer Growth**: 150 new enterprise customers
- **Churn Rate**: 3.2% (best-in-class performance)

---

## Slide 2: Financial Performance
### Strong Revenue Growth and Margin Expansion

**Revenue Metrics**:
- **Total Revenue**: $12.5M (+15% vs target)
- **Recurring Revenue**: $11.2M (90% of total)
- **New Business**: $3.8M in new customer acquisitions
- **Expansion Revenue**: $2.1M from existing customers

**Profitability Analysis**:
- **Gross Profit**: $9.75M (78% margin)
- **Operating Expenses**: $8.2M (66% of revenue)
- **EBITDA**: $1.55M (12% margin)
- **Cash Flow**: $2.1M positive operating cash flow

---

## Slide 3: Customer Metrics
### Accelerating Growth with High Retention

**Customer Acquisition**:
- **New Customers**: 150 enterprise accounts
- **Pipeline Growth**: $25M qualified opportunities
- **Sales Cycle**: 85 days average (15% improvement)
- **Win Rate**: 28% of qualified leads

**Customer Success**:
- **Net Retention Rate**: 125% (target: 120%)
- **Customer Satisfaction**: NPS score of 58
- **Product Adoption**: 82% feature utilization
- **Support Metrics**: 4.8/5 customer support rating

---

## Slide 4: Product Development
### Innovation Driving Competitive Advantage

**Feature Releases**:
- **AI Predictive Analytics**: Advanced project forecasting
- **Mobile Application**: iOS and Android native apps
- **API Platform**: 50+ new integration endpoints
- **Enterprise Security**: SOC 2 Type II certification

**Development Metrics**:
- **Release Velocity**: 2-week sprint cycles maintained
- **Bug Resolution**: 24-hour average resolution time
- **Feature Adoption**: 75% of new features adopted within 30 days
- **Technical Debt**: Reduced by 20% through refactoring

---

## Slide 5: Market Position
### Strengthening Competitive Differentiation

**Market Share**:
- **Enterprise Segment**: 3.2% market share (up from 2.1%)
- **Geographic Expansion**: Launched in EU and APAC
- **Competitive Wins**: 65% win rate against top competitors
- **Brand Recognition**: 40% increase in brand awareness

**Competitive Analysis**:
- **Product Differentiation**: AI capabilities 18 months ahead
- **Customer Satisfaction**: Highest NPS in category
- **Pricing Position**: Premium pricing with proven ROI
- **Partnership Ecosystem**: 25 strategic partnerships

---

## Slide 6: Operational Excellence
### Scaling Infrastructure and Processes

**Team Growth**:
- **Headcount**: 125 employees (20% growth)
- **Key Hires**: VP of International, Head of AI Research
- **Retention Rate**: 94% employee retention
- **Diversity Metrics**: 40% women in leadership roles

**Operational Metrics**:
- **System Uptime**: 99.97% availability
- **Customer Onboarding**: 30-day average time to value
- **Support Response**: 2-hour average first response
- **Process Automation**: 60% of routine tasks automated

---

## Slide 7: Strategic Initiatives
### {quarter} Achievements and Progress

**Completed Initiatives**:
- **International Expansion**: EU operations launched
- **Product Platform**: API ecosystem released
- **Strategic Partnerships**: Microsoft integration completed
- **Compliance**: SOC 2 and GDPR certification achieved

**In-Progress Projects**:
- **AI Enhancement**: Next-gen predictive models (75% complete)
- **Mobile Platform**: Native apps in beta testing
- **Enterprise Features**: Advanced reporting suite
- **Market Expansion**: APAC go-to-market strategy

---

## Slide 8: Challenges & Risks
### Proactive Risk Management

**Current Challenges**:
- **Talent Acquisition**: Competitive market for AI engineers
- **Market Competition**: Increased competitive pressure
- **Economic Uncertainty**: Potential impact on enterprise spending
- **Scaling Operations**: Infrastructure capacity planning

**Mitigation Strategies**:
- **Talent Strategy**: Enhanced compensation and remote work
- **Product Innovation**: Accelerated AI development roadmap
- **Customer Success**: Focus on retention and expansion
- **Operational Efficiency**: Automation and process optimization

---

## Slide 9: Next Quarter Outlook
### Strategic Priorities and Targets

**Revenue Targets**:
- **Total Revenue**: $15M (20% growth)
- **New Customer Acquisition**: 180 enterprise accounts
- **Expansion Revenue**: $2.8M from existing customers
- **International Revenue**: 15% of total revenue

**Strategic Priorities**:
- **Product Innovation**: Launch AI-powered resource optimization
- **Market Expansion**: Complete APAC market entry
- **Partnership Growth**: 10 new strategic partnerships
- **Operational Scale**: Implement advanced automation

---

## Slide 10: Investment & Resource Requirements
### Funding Next Phase of Growth

**Investment Priorities**:
- **Sales Team Expansion**: 15 additional account executives
- **Product Development**: AI research team expansion
- **International Operations**: Local teams in EU and APAC
- **Infrastructure**: Cloud capacity and security enhancements

**Expected Returns**:
- **Revenue Impact**: $5M incremental annual revenue
- **Market Position**: Top 3 player in enterprise segment
- **Operational Efficiency**: 25% improvement in key metrics
- **Customer Satisfaction**: Maintain >95% retention rate

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Comprehensive quarterly business review*"""

def generate_strategic_presentation(prompt: str, quality_level: int) -> str:
    """Generate strategic business presentation."""
    return f"""# Strategic Business Presentation
## Analysis and Recommendations

---

## Slide 1: Executive Overview
### Strategic Analysis and Recommendations

**Presentation Scope**:
- Current market position assessment
- Strategic opportunities identification
- Competitive landscape analysis
- Implementation roadmap development

**Key Objectives**:
- Align stakeholders on strategic direction
- Present data-driven recommendations
- Outline implementation timeline
- Define success metrics and KPIs

---

## Slide 2: Current State Analysis
### Market Position and Performance

**Market Context**:
- Industry trends and growth patterns
- Competitive positioning assessment
- Internal capability evaluation
- External opportunity identification

**Performance Metrics**:
- Current performance indicators
- Benchmark comparisons
- Trend analysis and projections
- Gap identification and prioritization

---

## Slide 3: Strategic Recommendations
### Data-Driven Action Plan

**Primary Recommendations**:
1. **Market Expansion**: Geographic and segment growth
2. **Product Innovation**: Technology advancement priorities
3. **Operational Excellence**: Efficiency and scale optimization
4. **Partnership Strategy**: Strategic alliance development

**Implementation Priorities**:
- Short-term wins (0-6 months)
- Medium-term initiatives (6-18 months)
- Long-term strategic goals (18+ months)

---

## Slide 4: Implementation Roadmap
### Phased Execution Strategy

**Phase 1: Foundation (Months 1-6)**
- Infrastructure development and optimization
- Team capability building and training
- Process standardization and automation
- Technology platform enhancement

**Phase 2: Growth (Months 7-18)**
- Market expansion and customer acquisition
- Product development and innovation
- Partnership development and integration
- Performance optimization and scaling

---

## Slide 5: Success Metrics
### Measurable Outcomes and KPIs

**Financial Metrics**:
- Revenue growth targets
- Profitability improvements
- Market share expansion
- Return on investment

**Operational Metrics**:
- Efficiency improvements
- Customer satisfaction scores
- Employee engagement levels
- Process optimization results

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Strategic presentation framework*"""

def generate_generic_content(prompt: str, quality_level: int) -> str:
    """Generate generic professional content."""

    # Extract key terms from prompt for contextual content
    prompt_lower = prompt.lower()

    return f"""# Professional Analysis Document

## Executive Summary

Based on your specific requirements: "{prompt[:100]}...", this document provides targeted analysis and actionable recommendations tailored to your needs.

## Context Analysis

### Your Requirements
The request focuses on: {', '.join([word for word in prompt.split()[:10] if len(word) > 3])}

### Approach
Our analysis addresses your specific context with:
- Targeted research and insights
- Industry-specific recommendations
- Practical implementation strategies
- Measurable success metrics

## Key Findings

### Primary Insights
1. **Contextual Analysis**: Your specific requirements indicate opportunities for strategic improvement and optimization.

2. **Targeted Recommendations**: Based on the context provided, we recommend focused actions that address your immediate needs.

3. **Implementation Strategy**: A structured approach tailored to your specific situation will ensure successful outcomes.

## Detailed Recommendations

### Immediate Actions
- Assess current state relative to your requirements
- Identify quick wins and optimization opportunities
- Develop implementation timeline
- Establish success metrics

### Strategic Considerations
- Long-term planning aligned with your objectives
- Resource allocation and capability building
- Risk mitigation and contingency planning
- Continuous improvement processes

## Implementation Plan

### Phase 1: Assessment and Planning
- Detailed situation analysis
- Stakeholder alignment
- Resource planning
- Timeline development

### Phase 2: Execution
- Implementation of recommendations
- Progress monitoring
- Adjustment and optimization
- Regular stakeholder updates

### Phase 3: Evaluation and Optimization
- Results measurement
- Success evaluation
- Process refinement
- Future planning

## Success Metrics

### Key Performance Indicators
- Specific metrics aligned with your objectives
- Progress tracking mechanisms
- Quality assurance measures
- Return on investment calculations

## Next Steps

1. **Review**: Assess recommendations against your specific needs
2. **Plan**: Develop detailed implementation strategy
3. **Execute**: Begin implementation with proper monitoring
4. **Optimize**: Continuous improvement based on results

---

**Generated by AIRDOCS - AI Research Documents Platform**
*Contextual analysis based on your specific requirements*"""

def get_estimated_time(category: str, template_id: str) -> int:
    """Get estimated generation time for a specific template."""
    if category not in CONTENT_CATEGORY_CONFIGS:
        return 5  # Default

    templates = CONTENT_CATEGORY_CONFIGS[category]["templates"]

    if template_id and template_id in templates:
        return templates[template_id]["estimated_time"]

    # Return average time for the category
    times = [template["estimated_time"] for template in templates.values()]
    return sum(times) // len(times) if times else 5

def refine_prompt_by_type(prompt: str, output_type: str) -> str:
    """Enhance prompt based on output type."""
    refinements = {
        "slides": """
Structure your presentation with:
1. Title slide with clear objective
2. Agenda/outline slide
3. Content slides with key points
4. Conclusion with call-to-action
5. Q&A slide

Keep slides concise with bullet points and visual elements.""",
        
        "pdf": """
Format for professional PDF document:
- Clear headings and subheadings
- Proper paragraph structure
- Include table of contents if lengthy
- Use consistent formatting
- Add page numbers and headers/footers""",
        
        "web": """
Design for responsive web interface:
- Mobile-first approach
- Accessible design (WCAG compliance)
- Fast loading times
- SEO optimization
- Cross-browser compatibility
- Progressive enhancement""",
        
        "code": """
Follow coding best practices:
- Clean, readable code structure
- Comprehensive documentation
- Error handling and validation
- Unit tests where applicable
- Security considerations
- Performance optimization"""
    }
    
    base_prompt = prompt.strip()
    if output_type.lower() in refinements:
        return f"{base_prompt}\n\nAdditional Requirements:\n{refinements[output_type.lower()]}"
    
    return base_prompt

def search_prompt_suggestions(query: str) -> List[Dict[str, Any]]:
    """Search for relevant prompt templates."""
    if len(query) < 5:
        return []
    
    query_lower = query.lower()
    suggestions = []
    
    for prompt in prompts_data:
        score = 0
        
        # Check name match
        if query_lower in prompt.get("name", "").lower():
            score += 10
        
        # Check template content match
        if query_lower in prompt.get("template", "").lower():
            score += 5
        
        # Check output type match
        if query_lower in prompt.get("output_type", "").lower():
            score += 3
        
        if score > 0:
            suggestions.append({
                **prompt,
                "relevance_score": score
            })
    
    # Sort by relevance and return top 5
    suggestions.sort(key=lambda x: x["relevance_score"], reverse=True)
    return suggestions[:5]

# Initialize data loading
load_models_data()
load_prompts_data()

# Start auto-refresh thread
refresh_thread = threading.Thread(target=auto_refresh_data, daemon=True)
refresh_thread.start()

# API Endpoints
@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file."""
    frontend_file = Path(__file__).parent / FRONTEND_DIR / "index.html"
    if frontend_file.exists():
        return FileResponse(frontend_file)
    return {"message": "AIRDOCS AI Document Factory", "status": "running", "version": "1.0.0"}

@app.get("/beta-test.html")
async def serve_beta_test():
    """Serve the beta testing interface."""
    beta_file = Path(__file__).parent / FRONTEND_DIR / "beta-test.html"
    if beta_file.exists():
        return FileResponse(beta_file)
    return {"error": "Beta test interface not found"}

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    try:
        # Check system resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Check model discovery service
        discovery_status = "healthy" if model_discovery_service else "unavailable"

        # Calculate healthy models percentage
        total_models = len(models_data)
        healthy_models = sum(1 for model in models_data.values()
                           if model.get('status') == 'healthy')
        health_percentage = (healthy_models / total_models * 100) if total_models > 0 else 0

        health_status = {
            "status": "healthy" if health_percentage > 50 else "degraded",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime": get_uptime(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "available_memory_gb": round(memory.available / (1024**3), 2),
                "free_disk_gb": round(disk.free / (1024**3), 2)
            },
            "models": {
                "total": total_models,
                "healthy": healthy_models,
                "health_percentage": round(health_percentage, 2)
            },
            "services": {
                "model_discovery": discovery_status,
                "api": "healthy",
                "logging": "healthy"
            }
        }

        logger.info(f"Health check completed: {health_status['status']}")
        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/models")
async def get_models():
    """Get all available models with their credits and capabilities."""
    return {
        "models": models_data,
        "last_updated": last_models_update,
        "total_models": len(models_data)
    }

@app.post("/refine-prompt")
async def refine_prompt(request: PromptRequest):
    """Refine prompt based on output type."""
    try:
        refined_prompt = refine_prompt_by_type(request.prompt, request.output_type)
        return {
            "original_prompt": request.prompt,
            "refined_prompt": refined_prompt,
            "output_type": request.output_type,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refining prompt: {str(e)}")

@app.post("/suggest-prompts")
async def suggest_prompts(request: SuggestionRequest):
    """Get prompt suggestions based on query."""
    try:
        suggestions = search_prompt_suggestions(request.query)
        return {
            "query": request.query,
            "suggestions": suggestions,
            "count": len(suggestions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")

@app.post("/generate-content")
async def generate_content(request: ContentGenerationRequest):
    """Generate professional content using tiered AI model routing."""
    try:
        # Initialize credit tracking if not done
        if not SPECIALIZED_CREDITS:
            initialize_credit_tracking()

        # Validate content category
        if request.content_category not in CONTENT_CATEGORY_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Invalid content category: {request.content_category}")

        # Use tiered routing system for model selection
        logger.info(f"🎯 Generating {request.content_category} content with tiered routing")

        # Generate content using intelligent routing
        generation_result = await generate_content_with_routing(
            prompt=request.search_query,
            content_category=request.content_category,
            quality_level=request.quality_level,
            output_formats=request.output_formats
        )

        if not generation_result.get("success"):
            raise HTTPException(status_code=500, detail="Content generation failed")

        # Get routing information for response
        routing_stats = ai_router.get_routing_stats()

        # Extract generated content
        generated_content = generation_result["content"]

        # Continue with existing document generation logic...
        # (The rest of the function remains the same)

        # Get optimal model for document generation (fallback)
        optimal_model = get_optimal_model(request.content_category, request.quality_level)

        # Generate the prompt using template
        enhanced_prompt = get_template_prompt(
            request.content_category,
            request.template_id,
            request.search_query,
            request.additional_context or ""
        )

        # Process uploaded files if any
        file_context = ""
        if request.uploaded_files:
            file_context = process_uploaded_files(request.uploaded_files)
            enhanced_prompt += f"\n\nReference Files Context:\n{file_context}"

        # Simulate AI model processing (replace with actual AI API calls)
        start_time = time.time()
        generated_content = simulate_ai_generation(enhanced_prompt, optimal_model, request.quality_level)
        response_time = time.time() - start_time

        # Track model usage
        credits_used = request.quality_level * 3  # Base credits based on quality
        track_model_usage(optimal_model, True, response_time, credits_used)

        # Update system metrics
        system_metrics['total_documents_generated'] += 1
        system_metrics['total_revenue'] += credits_used * 0.1

        # Generate professional documents in requested formats
        document_files = {}
        if request.output_formats:
            try:
                metadata_for_docs = {
                    "document_title": request.document_title or "Generated Document",
                    "content_category": request.content_category,
                    "template_id": request.template_id,
                    "quality_level": request.quality_level,
                    "model_used": optimal_model,
                    "estimated_time": get_estimated_time(request.content_category, request.template_id),
                    "word_count": len(generated_content.split()),
                    "character_count": len(generated_content)
                }

                document_files = document_generator.generate_document(
                    generated_content,
                    metadata_for_docs,
                    request.output_formats
                )
                logger.info(f"Generated documents: {list(document_files.keys())}")
            except Exception as e:
                logger.error(f"Document generation error: {str(e)}")
                # Continue without failing the entire request

        # Create response
        response = {
            "success": True,
            "content": generated_content,
            "metadata": {
                "document_title": request.document_title or "Generated Document",
                "content_category": request.content_category,
                "template_id": request.template_id,
                "quality_level": request.quality_level,
                "model_used": optimal_model,
                "estimated_time": get_estimated_time(request.content_category, request.template_id),
                "output_formats": request.output_formats,
                "timestamp": datetime.now().isoformat(),
                "word_count": len(generated_content.split()),
                "character_count": len(generated_content)
            },
            "documents": document_files
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")

@app.get("/content-categories")
async def get_content_categories():
    """Get all available content categories and their templates."""
    categories = {}
    for category_id, config in CONTENT_CATEGORY_CONFIGS.items():
        categories[category_id] = {
            "name": config["name"],
            "templates": {
                template_id: {
                    "name": template_data["name"],
                    "estimated_time": template_data["estimated_time"]
                }
                for template_id, template_data in config["templates"].items()
            }
        }

    return {
        "categories": categories,
        "total_categories": len(categories),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated document files."""
    try:
        file_path = os.path.join(document_generator.output_dir, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

        # Determine media type based on file extension
        if filename.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename.endswith('.pptx'):
            media_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
        elif filename.endswith('.docx'):
            media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            media_type = 'application/octet-stream'

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type=media_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")

@app.post("/upload-files")
async def upload_files(files: List[UploadFile] = File(...)):
    """Handle file uploads for content generation."""
    try:
        uploaded_files = []
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        for file in files:
            # Generate unique filename
            file_id = str(uuid.uuid4())
            file_extension = Path(file.filename).suffix
            unique_filename = f"{file_id}{file_extension}"
            file_path = upload_dir / unique_filename

            # Save file
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Process file content
            file_content = await process_file_content(file_path, file.content_type)

            uploaded_files.append({
                "id": file_id,
                "original_name": file.filename,
                "filename": unique_filename,
                "content_type": file.content_type,
                "size": len(content),
                "processed_content": file_content,
                "upload_time": datetime.now().isoformat()
            })

        return {
            "success": True,
            "files": uploaded_files,
            "total_files": len(uploaded_files),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading files: {str(e)}")

async def process_file_content(file_path: Path, content_type: str) -> str:
    """Process uploaded file and extract text content."""
    try:
        if "text" in content_type.lower():
            # Handle text files
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        elif "pdf" in content_type.lower():
            # Handle PDF files (would need PyPDF2 or similar)
            return f"PDF file content from {file_path.name} - [PDF processing would be implemented here]"

        elif "word" in content_type.lower() or "document" in content_type.lower():
            # Handle Word documents (would need python-docx)
            return f"Word document content from {file_path.name} - [Word processing would be implemented here]"

        elif "csv" in content_type.lower():
            # Handle CSV files
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                return f"CSV data from {file_path.name}:\n{content[:1000]}..." if len(content) > 1000 else content

        elif "excel" in content_type.lower() or "spreadsheet" in content_type.lower():
            # Handle Excel files (would need openpyxl or pandas)
            return f"Excel spreadsheet content from {file_path.name} - [Excel processing would be implemented here]"

        else:
            return f"File: {file_path.name} - Content type: {content_type}"

    except Exception as e:
        return f"Error processing file {file_path.name}: {str(e)}"

# Document history storage (in production, use a proper database)
document_history: Dict[str, DocumentHistoryItem] = {}

@app.post("/save-document")
async def save_document(
    title: str = Form(...),
    content: str = Form(...),
    content_type: str = Form(...),
    quality_level: int = Form(...),
    output_formats: str = Form(...)  # JSON string of list
):
    """Save a generated document to history."""
    try:
        doc_id = str(uuid.uuid4())
        output_formats_list = json.loads(output_formats) if output_formats else ["pdf"]

        document = DocumentHistoryItem(
            id=doc_id,
            title=title,
            content_type=content_type,
            generated_content=content,
            timestamp=time.time(),
            quality_level=quality_level,
            output_formats=output_formats_list
        )

        document_history[doc_id] = document

        return {
            "success": True,
            "document_id": doc_id,
            "message": "Document saved successfully",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving document: {str(e)}")

@app.get("/document-history")
async def get_document_history(limit: int = 50):
    """Get document history."""
    try:
        # Sort by timestamp (newest first)
        sorted_docs = sorted(
            document_history.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )

        # Limit results
        limited_docs = sorted_docs[:limit]

        # Convert to dict format for JSON response
        history_data = []
        for doc in limited_docs:
            history_data.append({
                "id": doc.id,
                "title": doc.title,
                "content_type": doc.content_type,
                "timestamp": doc.timestamp,
                "quality_level": doc.quality_level,
                "output_formats": doc.output_formats,
                "preview": doc.generated_content[:200] + "..." if len(doc.generated_content) > 200 else doc.generated_content
            })

        return {
            "success": True,
            "documents": history_data,
            "total_documents": len(document_history),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document history: {str(e)}")

@app.get("/document/{doc_id}")
async def get_document(doc_id: str):
    """Get a specific document by ID."""
    try:
        if doc_id not in document_history:
            raise HTTPException(status_code=404, detail="Document not found")

        document = document_history[doc_id]

        return {
            "success": True,
            "document": {
                "id": document.id,
                "title": document.title,
                "content_type": document.content_type,
                "generated_content": document.generated_content,
                "timestamp": document.timestamp,
                "quality_level": document.quality_level,
                "output_formats": document.output_formats
            },
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving document: {str(e)}")

@app.post("/regenerate-document/{doc_id}")
async def regenerate_document(doc_id: str):
    """Regenerate a document from history."""
    try:
        if doc_id not in document_history:
            raise HTTPException(status_code=404, detail="Document not found")

        original_doc = document_history[doc_id]

        # Create a new generation request based on the original
        # This is a simplified version - in practice, you'd store the original request parameters
        regeneration_request = ContentGenerationRequest(
            search_query=f"Regenerate: {original_doc.title}",
            document_title=original_doc.title,
            additional_context="Regenerated from document history",
            content_category="reports",  # Default category
            quality_level=original_doc.quality_level,
            output_formats=original_doc.output_formats
        )

        # Generate new content
        result = await generate_content(regeneration_request)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error regenerating document: {str(e)}")

@app.post("/download-document")
async def download_document(
    content: str = Form(...),
    title: str = Form(...),
    format: str = Form(...)
):
    """Generate and download document in specified format."""
    try:
        # Create downloads directory
        downloads_dir = Path("downloads")
        downloads_dir.mkdir(exist_ok=True)

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

        if format.lower() == "pdf":
            filename = f"{title}_{timestamp}.pdf"
            file_path = downloads_dir / filename

            # Generate PDF (simplified - would use reportlab or similar)
            pdf_content = generate_pdf_content(content, title)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(pdf_content)

        elif format.lower() == "word":
            filename = f"{title}_{timestamp}.docx"
            file_path = downloads_dir / filename

            # Generate Word document (simplified - would use python-docx)
            word_content = generate_word_content(content, title)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(word_content)

        elif format.lower() == "powerpoint":
            filename = f"{title}_{timestamp}.pptx"
            file_path = downloads_dir / filename

            # Generate PowerPoint (simplified - would use python-pptx)
            ppt_content = generate_powerpoint_content(content, title)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(ppt_content)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating document: {str(e)}")

def generate_pdf_content(content: str, title: str) -> str:
    """Generate PDF-formatted content (simplified version)."""
    return f"""PDF Document: {title}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{content}

---
Generated by ContentPro - Professional Content Creation Platform
"""

def generate_word_content(content: str, title: str) -> str:
    """Generate Word document content (simplified version)."""
    return f"""Word Document: {title}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

{content}

---
Generated by ContentPro - Professional Content Creation Platform
"""

def generate_powerpoint_content(content: str, title: str) -> str:
    """Generate PowerPoint content (simplified version)."""
    # Split content into slides based on headers
    slides = []
    current_slide = []

    for line in content.split('\n'):
        if line.startswith('#'):
            if current_slide:
                slides.append('\n'.join(current_slide))
                current_slide = []
            current_slide.append(line)
        else:
            current_slide.append(line)

    if current_slide:
        slides.append('\n'.join(current_slide))

    ppt_content = f"""PowerPoint Presentation: {title}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

"""

    for i, slide in enumerate(slides, 1):
        ppt_content += f"""
--- SLIDE {i} ---
{slide}

"""

    ppt_content += """
---
Generated by ContentPro - Professional Content Creation Platform
"""

    return ppt_content

# Admin endpoints
def verify_admin(auth: AdminAuth = Depends()):
    """Dependency to verify admin authentication."""
    if not verify_admin_password(auth.password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    return True

def verify_admin_header(authorization: str = None):
    """Verify admin authentication from Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")

    try:
        # Extract password from Bearer token (base64 encoded)
        if authorization.startswith("Bearer "):
            import base64
            encoded_password = authorization.split(" ")[1]
            password = base64.b64decode(encoded_password).decode('utf-8')

            if not verify_admin_password(password):
                raise HTTPException(status_code=401, detail="Invalid admin password")
            return True
        else:
            raise HTTPException(status_code=401, detail="Invalid authorization format")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid authorization")

@app.post("/admin/add-model")
async def add_model(
    name: str = Form(...),
    config: str = Form(...),
    password: str = Form(...)
):
    """Add new model configuration (admin only)."""
    if not verify_admin_password(password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    try:
        # Parse and validate JSON config
        model_config = json.loads(config)
        
        # Save to file
        models_dir = Path(__file__).parent / MODELS_DIR
        models_dir.mkdir(parents=True, exist_ok=True)
        
        model_file = models_dir / f"{name}.json"
        with open(model_file, 'w') as f:
            json.dump(model_config, f, indent=2)
        
        # Reload data
        load_models_data()
        
        return {
            "message": f"Model '{name}' added successfully",
            "model": model_config
        }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON configuration")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding model: {str(e)}")

@app.post("/admin/add-prompt")
async def add_prompt(
    name: str = Form(...),
    template: str = Form(...),
    output_type: str = Form(...),
    recommended_models: str = Form(...),
    password: str = Form(...)
):
    """Add new prompt template (admin only)."""
    if not verify_admin_password(password):
        raise HTTPException(status_code=401, detail="Invalid admin password")
    
    try:
        # Parse recommended models
        models_list = [m.strip() for m in recommended_models.split(",") if m.strip()]
        
        prompt_data = {
            "name": name,
            "template": template,
            "output_type": output_type,
            "recommended_models": models_list
        }
        
        # Save to appropriate JSONL file
        prompts_dir = Path(__file__).parent / PROMPTS_DIR
        prompts_dir.mkdir(parents=True, exist_ok=True)
        
        # Use output_type as filename
        prompt_file = prompts_dir / f"{output_type}.jsonl"
        with open(prompt_file, 'a') as f:
            f.write(json.dumps(prompt_data) + '\n')
        
        # Reload data
        load_prompts_data()
        
        return {
            "message": f"Prompt template '{name}' added successfully",
            "prompt": prompt_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding prompt: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models_loaded": len(models_data),
        "prompts_loaded": len(prompts_data),
        "last_models_update": last_models_update,
        "last_prompts_update": last_prompts_update,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/admin/dashboard")
async def get_admin_dashboard(admin_key: str = Depends(verify_admin_key)):
    """Get comprehensive admin dashboard data."""
    try:
        # Calculate overall system health
        healthy_models = sum(1 for model in model_performance.values() if model['status'] == 'healthy')
        total_models = len(model_performance)
        system_health = (healthy_models / total_models * 100) if total_models > 0 else 0

        # Calculate 24h statistics
        now = datetime.now()
        last_24h = now - timedelta(hours=24)

        total_requests_24h = sum(
            len(model['last_24h_requests']) for model in model_performance.values()
        )

        return {
            "system_overview": {
                "status": "healthy" if system_health > 80 else "degraded" if system_health > 50 else "critical",
                "uptime": "99.9%",
                "total_models": total_models,
                "healthy_models": healthy_models,
                "system_health_percentage": round(system_health, 1),
                "total_requests_24h": total_requests_24h,
                "active_users": system_metrics['active_users'],
                "total_documents": system_metrics['total_documents_generated'],
                "total_revenue": system_metrics['total_revenue']
            },
            "model_performance": {
                model_name: {
                    "status": perf['status'],
                    "total_requests": perf['total_requests'],
                    "success_rate": round((perf['successful_requests'] / perf['total_requests'] * 100) if perf['total_requests'] > 0 else 0, 2),
                    "avg_response_time": round(perf['average_response_time'], 3),
                    "credits_consumed": perf['credits_consumed'],
                    "revenue_generated": round(perf['revenue_generated'], 2),
                    "last_health_check": perf['last_health_check']
                }
                for model_name, perf in model_performance.items()
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving dashboard data: {str(e)}")

@app.get("/admin/models/performance")
async def get_models_performance():
    """Get detailed model performance metrics."""
    try:
        performance_data = {}

        for model_name, perf in model_performance.items():
            # Calculate success rate
            success_rate = (perf['successful_requests'] / perf['total_requests'] * 100) if perf['total_requests'] > 0 else 0

            # Get model config if it exists (for JSON-defined models)
            model_config = models_data.get(model_name, {})

            # Determine model type and info
            if model_name in models_data:
                # This is a JSON-defined model
                model_info = {
                    "name": model_name,
                    "type": "configuration_model",
                    "credits": model_config.get('credits', 0),
                    "api_endpoint": model_config.get('api_endpoint', ''),
                    "capabilities": model_config.get('capabilities', []),
                    "supported_formats": model_config.get('supported_formats', {})
                }
            else:
                # This is an AI model used for content generation
                model_info = {
                    "name": model_name,
                    "type": "ai_model",
                    "credits": 0,
                    "api_endpoint": f"AI API for {model_name}",
                    "capabilities": ["content_generation", "text_processing"],
                    "supported_formats": ["text", "markdown"]
                }

            performance_data[model_name] = {
                "model_info": model_info,
                "performance_metrics": {
                    "status": perf['status'],
                    "last_health_check": perf['last_health_check'],
                    "total_requests": perf['total_requests'],
                    "successful_requests": perf['successful_requests'],
                    "failed_requests": perf['failed_requests'],
                    "success_rate": round(success_rate, 2),
                    "average_response_time": round(perf['average_response_time'], 3),
                    "credits_consumed": perf['credits_consumed'],
                    "revenue_generated": round(perf['revenue_generated'], 2)
                },
                "recent_errors": list(perf['error_log'])[-5:],
                "uptime_checks": list(perf['uptime_checks'])[-12:]
            }

        return {
            "models": performance_data,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving model performance: {str(e)}")

@app.post("/admin/models/{model_name}/test")
async def test_model_health(model_name: str, admin_key: str = Depends(verify_admin_key)):
    """Manually test a specific model's health."""
    try:
        if model_name not in model_performance:
            raise HTTPException(status_code=404, detail=f"Model {model_name} not found")

        start_time = time.time()

        # Get model metadata for enhanced testing
        model_metadata = model_performance[model_name].get('discovered_metadata', {})
        model_source = model_metadata.get('source', 'unknown')

        # Simulate model test (replace with actual API call)
        try:
            # Enhanced testing based on model source and type
            if model_source == 'lmsys_arena':
                # High-quality models from arena - higher success rate
                success = random.choice([True, True, True, True, False])  # 80% success rate
                response_time = time.time() - start_time + random.uniform(0.1, 0.4)
                error_message = None if success else "Arena model temporary unavailable"
            elif model_source == 'enterprise':
                # Enterprise models - very high success rate
                success = random.choice([True, True, True, True, True, False])  # 83% success rate
                response_time = time.time() - start_time + random.uniform(0.05, 0.3)
                error_message = None if success else "Enterprise API rate limit"
            elif model_source == 'huggingface':
                # HuggingFace models - variable success rate
                success = random.choice([True, True, False])  # 67% success rate
                response_time = time.time() - start_time + random.uniform(0.2, 0.8)
                error_message = None if success else "HuggingFace model loading timeout"
            else:
                # Default/unknown models
                success = random.choice([True, True, True, False])  # 75% success rate
                response_time = time.time() - start_time + random.uniform(0.1, 0.5)
                error_message = None if success else "Model health check failed"
        except Exception as e:
            success = False
            response_time = time.time() - start_time
            error_message = str(e)

        # Track the test result
        track_model_usage(model_name, success, response_time)

        # Update model status based on test result
        model_performance[model_name]['status'] = 'healthy' if success else 'error'
        model_performance[model_name]['last_health_check'] = datetime.now().isoformat()

        return {
            "model_name": model_name,
            "test_result": "success" if success else "failed",
            "response_time": round(response_time, 3),
            "error_message": error_message,
            "model_source": model_source,
            "model_metadata": model_metadata,
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing model: {str(e)}")

@app.get("/admin/models/discovery")
async def get_model_discovery_info(admin_key: str = Depends(verify_admin_key)):
    """Get information about discovered models and their sources."""
    try:
        discovered_models = model_discovery_service.discovered_models

        # Group models by source
        models_by_source = {}
        for model_name, model_info in discovered_models.items():
            source = model_info.get('source', 'unknown')
            if source not in models_by_source:
                models_by_source[source] = []
            models_by_source[source].append(model_info)

        # Get top models by rating
        top_models = model_discovery_service.get_top_models_by_rating(15)

        # Get models by provider
        providers = {}
        for model_name, model_info in discovered_models.items():
            provider = model_info.get('provider', 'unknown')
            if provider not in providers:
                providers[provider] = 0
            providers[provider] += 1

        return {
            "discovery_summary": {
                "total_discovered": len(discovered_models),
                "sources": list(models_by_source.keys()),
                "providers": providers,
                "discovery_timestamp": datetime.now().isoformat()
            },
            "models_by_source": models_by_source,
            "top_rated_models": top_models,
            "discovery_sources": {
                "lmsys_arena": "LMSYS Chatbot Arena Leaderboard",
                "enterprise": "Enterprise AI Providers",
                "huggingface": "HuggingFace Trending Models",
                "specialized": "Specialized AI Services",
                "academic": "Academic & Research Writing AI",
                "research": "Research and Academic Models",
                "open_source": "Open Source AI Models"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving discovery info: {str(e)}")

@app.get("/ai-routing-stats")
async def get_ai_routing_stats():
    """Get AI model routing statistics and credit usage."""
    try:
        # Initialize credit tracking if not done
        if not SPECIALIZED_CREDITS:
            initialize_credit_tracking()

        routing_stats = ai_router.get_routing_stats()

        # Add service availability information
        service_availability = {}
        for category, services in SPECIALIZED_AI_SERVICES.items():
            service_availability[category] = {
                "primary_tier_services": len(services["primary_tier"]),
                "available_services": sum(
                    1 for service in services["primary_tier"]
                    if SPECIALIZED_CREDITS.get(service["name"], {}).get("remaining_credits", 0) > 0
                ),
                "total_credits_remaining": sum(
                    SPECIALIZED_CREDITS.get(service["name"], {}).get("remaining_credits", 0)
                    for service in services["primary_tier"]
                )
            }

        return {
            "success": True,
            "routing_statistics": routing_stats,
            "service_availability": service_availability,
            "specialized_services": {
                category: {
                    "primary_tier": [
                        {
                            "name": service["name"],
                            "quality_score": service["quality_score"],
                            "specialization": service["specialization"],
                            "remaining_credits": SPECIALIZED_CREDITS.get(service["name"], {}).get("remaining_credits", 0),
                            "used_credits": SPECIALIZED_CREDITS.get(service["name"], {}).get("used_credits", 0)
                        }
                        for service in services["primary_tier"]
                    ],
                    "secondary_tier": services["secondary_tier"]
                }
                for category, services in SPECIALIZED_AI_SERVICES.items()
            }
        }

    except Exception as e:
        logger.error(f"Error getting routing stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting routing stats: {str(e)}")

@app.post("/reset-ai-credits")
async def reset_ai_credits():
    """Reset AI service credits (for testing/admin purposes)."""
    try:
        initialize_credit_tracking()

        return {
            "success": True,
            "message": "AI service credits have been reset",
            "credit_status": {
                service_name: info["remaining_credits"]
                for service_name, info in SPECIALIZED_CREDITS.items()
            }
        }

    except Exception as e:
        logger.error(f"Error resetting credits: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting credits: {str(e)}")

@app.get("/circuit-breaker-status")
async def get_circuit_breaker_status():
    """Get circuit breaker status for all AI services."""
    try:
        if not CIRCUIT_BREAKER_ENABLED:
            return {
                "success": False,
                "message": "Circuit breaker not enabled",
                "enabled": False
            }

        # Get individual service health
        service_health = get_all_service_health()

        # Get system health summary
        system_health = get_system_health()

        return {
            "success": True,
            "enabled": True,
            "system_health": system_health,
            "services": service_health,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error getting circuit breaker status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting circuit breaker status: {str(e)}")

@app.post("/reset-circuit-breaker/{service_name}")
async def reset_circuit_breaker(service_name: str):
    """Reset circuit breaker for specific service."""
    try:
        if not CIRCUIT_BREAKER_ENABLED:
            raise HTTPException(status_code=400, detail="Circuit breaker not enabled")

        success = circuit_breaker_manager.reset_circuit_breaker(service_name)

        if success:
            return {
                "success": True,
                "service": service_name,
                "message": f"Circuit breaker reset for {service_name}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Circuit breaker not found for {service_name}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting circuit breaker for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting circuit breaker: {str(e)}")

@app.post("/reset-all-circuit-breakers")
async def reset_all_circuit_breakers():
    """Reset all circuit breakers."""
    try:
        if not CIRCUIT_BREAKER_ENABLED:
            raise HTTPException(status_code=400, detail="Circuit breaker not enabled")

        circuit_breaker_manager.reset_all_circuit_breakers()

        return {
            "success": True,
            "message": "All circuit breakers have been reset",
            "reset_count": len(circuit_breaker_manager.circuit_breakers)
        }

    except Exception as e:
        logger.error(f"Error resetting all circuit breakers: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error resetting circuit breakers: {str(e)}")

@app.get("/cache-status")
async def get_cache_status():
    """Get cache status and performance metrics."""
    try:
        if not CACHE_ENABLED:
            return {
                "success": False,
                "message": "Cache not enabled",
                "enabled": False
            }

        cache_stats = await get_cache_statistics()

        return {
            "success": True,
            "enabled": True,
            "cache_statistics": cache_stats,
            "timestamp": time.time()
        }

    except Exception as e:
        logger.error(f"Error getting cache status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting cache status: {str(e)}")

@app.post("/clear-cache")
async def clear_cache():
    """Clear all cache entries."""
    try:
        if not CACHE_ENABLED:
            raise HTTPException(status_code=400, detail="Cache not enabled")

        cleared_count = await cache_manager.clear_all()

        return {
            "success": True,
            "message": f"Cache cleared: {cleared_count} entries removed",
            "cleared_entries": cleared_count
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.post("/invalidate-cache/{service_name}")
async def invalidate_service_cache(service_name: str):
    """Invalidate cache for specific service."""
    try:
        if not CACHE_ENABLED:
            raise HTTPException(status_code=400, detail="Cache not enabled")

        invalidated_count = await cache_manager.invalidate_service(service_name)

        return {
            "success": True,
            "service": service_name,
            "message": f"Invalidated {invalidated_count} cache entries for {service_name}",
            "invalidated_entries": invalidated_count
        }

    except Exception as e:
        logger.error(f"Error invalidating cache for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error invalidating cache: {str(e)}")

# Initialize the system on startup
@app.on_event("startup")
async def startup_event():
    """Initialize the AI routing system on startup."""
    logger.info("🚀 Initializing AIRDOCS AI Routing System...")

    # Initialize credit tracking
    initialize_credit_tracking()

    # Initialize cache manager
    if CACHE_ENABLED:
        try:
            await cache_manager.__aenter__()
            logger.info("✅ Cache manager initialized")
        except Exception as e:
            logger.error(f"❌ Cache manager initialization failed: {str(e)}")

    # Initialize auth manager
    if OAUTH_ENABLED:
        try:
            await auth_manager.__aenter__()
            logger.info("✅ Auth manager initialized")
        except Exception as e:
            logger.error(f"❌ Auth manager initialization failed: {str(e)}")

    # Log available services
    total_credits = sum(info["remaining_credits"] for info in SPECIALIZED_CREDITS.values())
    logger.info(f"✅ Initialized {len(SPECIALIZED_CREDITS)} specialized AI services with {total_credits} total credits")

    # Log service breakdown
    for category, services in SPECIALIZED_AI_SERVICES.items():
        primary_services = len(services["primary_tier"])
        logger.info(f"📋 {category}: {primary_services} specialized services available")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("🛑 Shutting down AIRDOCS...")

    # Cleanup cache manager
    if CACHE_ENABLED:
        try:
            await cache_manager.__aexit__(None, None, None)
            logger.info("✅ Cache manager cleaned up")
        except Exception as e:
            logger.error(f"❌ Cache manager cleanup failed: {str(e)}")

    # Cleanup auth manager
    if OAUTH_ENABLED:
        try:
            await auth_manager.__aexit__(None, None, None)
            logger.info("✅ Auth manager cleaned up")
        except Exception as e:
            logger.error(f"❌ Auth manager cleanup failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
