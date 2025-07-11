#!/usr/bin/env python3
"""
OAuth 2.0 Configuration for AI Services
Real authentication integration with specialized AI platforms
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class AuthType(Enum):
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    BEARER_TOKEN = "bearer_token"

@dataclass
class OAuthConfig:
    """OAuth configuration for AI service."""
    service_name: str
    auth_type: AuthType
    client_id: str
    client_secret: str
    auth_url: str
    token_url: str
    scopes: list
    redirect_uri: str
    api_base_url: str

# OAuth 2.0 Configurations for Specialized AI Services
OAUTH_CONFIGS = {
    # Academic Paper Specialists
    "paperpal": OAuthConfig(
        service_name="paperpal",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("PAPERPAL_CLIENT_ID", "airdocs_paperpal_client"),
        client_secret=os.getenv("PAPERPAL_CLIENT_SECRET", ""),
        auth_url="https://api.paperpal.com/oauth/authorize",
        token_url="https://api.paperpal.com/oauth/token",
        scopes=["research", "academic_writing", "citations", "grammar_check"],
        redirect_uri=os.getenv("PAPERPAL_REDIRECT_URI", "http://localhost:8001/auth/paperpal/callback"),
        api_base_url="https://api.paperpal.com/v1"
    ),
    
    "jenni_ai": OAuthConfig(
        service_name="jenni_ai",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("JENNI_CLIENT_ID", "airdocs_jenni_client"),
        client_secret=os.getenv("JENNI_CLIENT_SECRET", ""),
        auth_url="https://api.jenni.ai/oauth/authorize",
        token_url="https://api.jenni.ai/oauth/token",
        scopes=["research_papers", "methodology", "literature_review", "citations"],
        redirect_uri=os.getenv("JENNI_REDIRECT_URI", "http://localhost:8001/auth/jenni/callback"),
        api_base_url="https://api.jenni.ai/v1"
    ),
    
    "scispace": OAuthConfig(
        service_name="scispace",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("SCISPACE_CLIENT_ID", "airdocs_scispace_client"),
        client_secret=os.getenv("SCISPACE_CLIENT_SECRET", ""),
        auth_url="https://api.scispace.com/oauth/authorize",
        token_url="https://api.scispace.com/oauth/token",
        scopes=["literature_search", "citation_analysis", "research_gaps"],
        redirect_uri=os.getenv("SCISPACE_REDIRECT_URI", "http://localhost:8001/auth/scispace/callback"),
        api_base_url="https://api.scispace.com/v1"
    ),
    
    # Presentation Specialists
    "genspark": OAuthConfig(
        service_name="genspark",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("GENSPARK_CLIENT_ID", "airdocs_genspark_client"),
        client_secret=os.getenv("GENSPARK_CLIENT_SECRET", ""),
        auth_url="https://api.genspark.ai/oauth/authorize",
        token_url="https://api.genspark.ai/oauth/token",
        scopes=["presentations", "executive_content", "strategic_frameworks", "visual_design"],
        redirect_uri=os.getenv("GENSPARK_REDIRECT_URI", "http://localhost:8001/auth/genspark/callback"),
        api_base_url="https://api.genspark.ai/v1"
    ),
    
    "manus": OAuthConfig(
        service_name="manus",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("MANUS_CLIENT_ID", "airdocs_manus_client"),
        client_secret=os.getenv("MANUS_CLIENT_SECRET", ""),
        auth_url="https://api.manus.ai/oauth/authorize",
        token_url="https://api.manus.ai/oauth/token",
        scopes=["business_presentations", "financial_modeling", "investor_decks"],
        redirect_uri=os.getenv("MANUS_REDIRECT_URI", "http://localhost:8001/auth/manus/callback"),
        api_base_url="https://api.manus.ai/v1"
    ),
    
    "gamma_app": OAuthConfig(
        service_name="gamma_app",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("GAMMA_CLIENT_ID", "airdocs_gamma_client"),
        client_secret=os.getenv("GAMMA_CLIENT_SECRET", ""),
        auth_url="https://api.gamma.app/oauth/authorize",
        token_url="https://api.gamma.app/oauth/token",
        scopes=["design_presentations", "visual_design", "interactive_content"],
        redirect_uri=os.getenv("GAMMA_REDIRECT_URI", "http://localhost:8001/auth/gamma/callback"),
        api_base_url="https://api.gamma.app/v1"
    ),
    
    # Business Report Specialists
    "pitchbook_ai": OAuthConfig(
        service_name="pitchbook_ai",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("PITCHBOOK_CLIENT_ID", "airdocs_pitchbook_client"),
        client_secret=os.getenv("PITCHBOOK_CLIENT_SECRET", ""),
        auth_url="https://api.pitchbook.com/oauth/authorize",
        token_url="https://api.pitchbook.com/oauth/token",
        scopes=["market_analysis", "investment_data", "company_research"],
        redirect_uri=os.getenv("PITCHBOOK_REDIRECT_URI", "http://localhost:8001/auth/pitchbook/callback"),
        api_base_url="https://api.pitchbook.com/v1"
    ),
    
    "cb_insights": OAuthConfig(
        service_name="cb_insights",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("CB_INSIGHTS_CLIENT_ID", "airdocs_cbinsights_client"),
        client_secret=os.getenv("CB_INSIGHTS_CLIENT_SECRET", ""),
        auth_url="https://api.cbinsights.com/oauth/authorize",
        token_url="https://api.cbinsights.com/oauth/token",
        scopes=["industry_intelligence", "startup_analysis", "technology_trends"],
        redirect_uri=os.getenv("CB_INSIGHTS_REDIRECT_URI", "http://localhost:8001/auth/cbinsights/callback"),
        api_base_url="https://api.cbinsights.com/v1"
    ),
    
    # Research Specialists
    "perplexity_pro": OAuthConfig(
        service_name="perplexity_pro",
        auth_type=AuthType.API_KEY,
        client_id="",
        client_secret="",
        auth_url="",
        token_url="",
        scopes=["research_synthesis", "real_time_data", "web_search"],
        redirect_uri="",
        api_base_url="https://api.perplexity.ai/v1"
    ),
    
    # Marketing Specialists
    "jasper_ai": OAuthConfig(
        service_name="jasper_ai",
        auth_type=AuthType.OAUTH2,
        client_id=os.getenv("JASPER_CLIENT_ID", "airdocs_jasper_client"),
        client_secret=os.getenv("JASPER_CLIENT_SECRET", ""),
        auth_url="https://api.jasper.ai/oauth/authorize",
        token_url="https://api.jasper.ai/oauth/token",
        scopes=["marketing_copy", "brand_voice", "conversion_optimization"],
        redirect_uri=os.getenv("JASPER_REDIRECT_URI", "http://localhost:8001/auth/jasper/callback"),
        api_base_url="https://api.jasper.ai/v1"
    ),
    
    # Generic AI Models
    "openai": OAuthConfig(
        service_name="openai",
        auth_type=AuthType.API_KEY,
        client_id="",
        client_secret="",
        auth_url="",
        token_url="",
        scopes=["gpt-4o", "gpt-4-turbo", "text-generation"],
        redirect_uri="",
        api_base_url="https://api.openai.com/v1"
    ),
    
    "anthropic": OAuthConfig(
        service_name="anthropic",
        auth_type=AuthType.API_KEY,
        client_id="",
        client_secret="",
        auth_url="",
        token_url="",
        scopes=["claude-3-opus", "claude-3-sonnet", "text-generation"],
        redirect_uri="",
        api_base_url="https://api.anthropic.com/v1"
    )
}

# API Key Configurations (for services that don't use OAuth)
API_KEY_CONFIGS = {
    "perplexity_pro": {
        "api_key": os.getenv("PERPLEXITY_API_KEY", ""),
        "header_name": "Authorization",
        "header_format": "Bearer {api_key}"
    },
    "openai": {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "header_name": "Authorization", 
        "header_format": "Bearer {api_key}"
    },
    "anthropic": {
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "header_name": "x-api-key",
        "header_format": "{api_key}"
    }
}

# Production vs Development Configuration
def get_oauth_config(service_name: str, environment: str = "development") -> Optional[OAuthConfig]:
    """Get OAuth configuration for service based on environment."""
    
    config = OAUTH_CONFIGS.get(service_name)
    if not config:
        return None
    
    # Adjust URLs for production environment
    if environment == "production":
        # Update redirect URIs for production domain
        production_domain = os.getenv("PRODUCTION_DOMAIN", "https://airdocs.ai")
        config.redirect_uri = config.redirect_uri.replace("http://localhost:8001", production_domain)
    
    return config

def get_api_key_config(service_name: str) -> Optional[Dict[str, str]]:
    """Get API key configuration for service."""
    return API_KEY_CONFIGS.get(service_name)

def validate_oauth_config(service_name: str) -> bool:
    """Validate that OAuth configuration is complete for service."""
    
    config = OAUTH_CONFIGS.get(service_name)
    if not config:
        return False
    
    if config.auth_type == AuthType.OAUTH2:
        required_fields = [config.client_id, config.client_secret, config.auth_url, config.token_url]
        return all(field for field in required_fields)
    
    elif config.auth_type == AuthType.API_KEY:
        api_config = API_KEY_CONFIGS.get(service_name)
        return api_config and api_config.get("api_key")
    
    return False

def get_all_configured_services() -> Dict[str, bool]:
    """Get status of all service configurations."""
    
    status = {}
    for service_name in OAUTH_CONFIGS.keys():
        status[service_name] = validate_oauth_config(service_name)
    
    return status

# Environment Variables Template
ENV_TEMPLATE = """
# OAuth 2.0 Configuration for AI Services
# Copy these to your .env file and fill in the actual values

# Academic Paper Specialists
PAPERPAL_CLIENT_ID=your_paperpal_client_id
PAPERPAL_CLIENT_SECRET=your_paperpal_client_secret
JENNI_CLIENT_ID=your_jenni_client_id
JENNI_CLIENT_SECRET=your_jenni_client_secret
SCISPACE_CLIENT_ID=your_scispace_client_id
SCISPACE_CLIENT_SECRET=your_scispace_client_secret

# Presentation Specialists
GENSPARK_CLIENT_ID=your_genspark_client_id
GENSPARK_CLIENT_SECRET=your_genspark_client_secret
MANUS_CLIENT_ID=your_manus_client_id
MANUS_CLIENT_SECRET=your_manus_client_secret
GAMMA_CLIENT_ID=your_gamma_client_id
GAMMA_CLIENT_SECRET=your_gamma_client_secret

# Business Report Specialists
PITCHBOOK_CLIENT_ID=your_pitchbook_client_id
PITCHBOOK_CLIENT_SECRET=your_pitchbook_client_secret
CB_INSIGHTS_CLIENT_ID=your_cbinsights_client_id
CB_INSIGHTS_CLIENT_SECRET=your_cbinsights_client_secret

# Marketing Specialists
JASPER_CLIENT_ID=your_jasper_client_id
JASPER_CLIENT_SECRET=your_jasper_client_secret

# API Key Services
PERPLEXITY_API_KEY=your_perplexity_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Production Configuration
PRODUCTION_DOMAIN=https://airdocs.ai
"""

if __name__ == "__main__":
    # Print configuration status
    print("🔐 OAuth Configuration Status:")
    print("=" * 40)
    
    status = get_all_configured_services()
    for service, configured in status.items():
        status_icon = "✅" if configured else "❌"
        print(f"{status_icon} {service}: {'Configured' if configured else 'Missing credentials'}")
    
    print(f"\n📋 Environment Variables Template:")
    print(ENV_TEMPLATE)
