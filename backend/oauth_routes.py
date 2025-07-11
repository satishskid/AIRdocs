#!/usr/bin/env python3
"""
OAuth 2.0 Routes for AI Service Authentication
FastAPI endpoints for handling OAuth flows and authentication
"""

from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Dict, Any, Optional
import logging
import asyncio

from auth_manager import auth_manager, generate_auth_url
from oauth_config import OAUTH_CONFIGS, get_oauth_config, get_all_configured_services

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create OAuth router
oauth_router = APIRouter(prefix="/auth", tags=["authentication"])

@oauth_router.get("/status")
async def get_authentication_status():
    """Get authentication status for all AI services."""
    
    try:
        # Get authentication status from auth manager
        auth_status = auth_manager.get_authentication_status()
        
        # Get configuration status
        config_status = get_all_configured_services()
        
        # Combine status information
        combined_status = {}
        for service_name in OAUTH_CONFIGS.keys():
            combined_status[service_name] = {
                "configured": config_status.get(service_name, False),
                "authenticated": auth_status.get(service_name, {}).get("authenticated", False),
                "auth_type": auth_status.get(service_name, {}).get("auth_type", "oauth2"),
                "expires_at": auth_status.get(service_name, {}).get("expires_at"),
                "scopes": auth_status.get(service_name, {}).get("scopes", [])
            }
        
        # Calculate summary statistics
        total_services = len(combined_status)
        configured_services = sum(1 for status in combined_status.values() if status["configured"])
        authenticated_services = sum(1 for status in combined_status.values() if status["authenticated"])
        
        return {
            "success": True,
            "summary": {
                "total_services": total_services,
                "configured_services": configured_services,
                "authenticated_services": authenticated_services,
                "configuration_percentage": (configured_services / total_services) * 100,
                "authentication_percentage": (authenticated_services / total_services) * 100
            },
            "services": combined_status,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    except Exception as e:
        logger.error(f"Error getting authentication status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting authentication status: {str(e)}")

@oauth_router.get("/login/{service_name}")
async def initiate_oauth_login(service_name: str):
    """Initiate OAuth login flow for AI service."""
    
    try:
        # Validate service name
        if service_name not in OAUTH_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
        
        # Check if service is configured
        config = get_oauth_config(service_name)
        if not config:
            raise HTTPException(status_code=400, detail=f"Service {service_name} not configured")
        
        # Generate authorization URL
        auth_url = generate_auth_url(service_name)
        if not auth_url:
            raise HTTPException(status_code=400, detail=f"Cannot generate auth URL for {service_name}")
        
        logger.info(f"🔗 Initiating OAuth login for {service_name}")
        
        return {
            "success": True,
            "service": service_name,
            "auth_url": auth_url,
            "message": f"Redirect user to auth_url to complete OAuth flow for {service_name}"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initiating OAuth login for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initiating OAuth login: {str(e)}")

@oauth_router.get("/callback/{service_name}")
async def oauth_callback(
    service_name: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: Optional[str] = Query(None, description="State parameter for CSRF protection"),
    error: Optional[str] = Query(None, description="Error from OAuth provider")
):
    """Handle OAuth callback from AI service."""
    
    try:
        # Check for OAuth errors
        if error:
            logger.error(f"OAuth error for {service_name}: {error}")
            raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
        
        # Validate service name
        if service_name not in OAUTH_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
        
        # Exchange code for token
        success = await auth_manager.exchange_code_for_token(service_name, code, state)
        
        if success:
            logger.info(f"✅ Successfully authenticated {service_name}")
            
            # Return success response (in production, redirect to frontend)
            return {
                "success": True,
                "service": service_name,
                "message": f"Successfully authenticated with {service_name}",
                "redirect_url": f"/?auth_success={service_name}"
            }
        else:
            logger.error(f"❌ Failed to authenticate {service_name}")
            raise HTTPException(status_code=400, detail=f"Failed to authenticate with {service_name}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in OAuth callback for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"OAuth callback error: {str(e)}")

@oauth_router.post("/logout/{service_name}")
async def logout_service(service_name: str):
    """Logout from AI service (revoke authentication)."""
    
    try:
        # Validate service name
        if service_name not in OAUTH_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
        
        # Revoke authentication
        success = await auth_manager.revoke_token(service_name)
        
        if success:
            logger.info(f"🗑️ Successfully logged out from {service_name}")
            return {
                "success": True,
                "service": service_name,
                "message": f"Successfully logged out from {service_name}"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to logout from {service_name}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error logging out from {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Logout error: {str(e)}")

@oauth_router.get("/test/{service_name}")
async def test_service_authentication(service_name: str):
    """Test authentication with AI service."""
    
    try:
        # Validate service name
        if service_name not in OAUTH_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
        
        # Get authentication headers
        headers = await auth_manager.get_auth_headers(service_name)
        
        if not headers or "Authorization" not in headers:
            return {
                "success": False,
                "service": service_name,
                "authenticated": False,
                "message": f"No valid authentication for {service_name}"
            }
        
        # Test API call (simplified - just check if we have valid headers)
        config = get_oauth_config(service_name)
        
        return {
            "success": True,
            "service": service_name,
            "authenticated": True,
            "auth_type": config.auth_type.value if config else "unknown",
            "api_base_url": config.api_base_url if config else "unknown",
            "message": f"Authentication test successful for {service_name}"
        }
    
    except Exception as e:
        logger.error(f"Error testing authentication for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication test error: {str(e)}")

@oauth_router.get("/services")
async def get_available_services():
    """Get list of available AI services and their configuration status."""
    
    try:
        config_status = get_all_configured_services()
        auth_status = auth_manager.get_authentication_status()
        
        services = []
        for service_name, config in OAUTH_CONFIGS.items():
            service_info = {
                "name": service_name,
                "display_name": service_name.replace("_", " ").title(),
                "auth_type": config.auth_type.value,
                "scopes": config.scopes,
                "configured": config_status.get(service_name, False),
                "authenticated": auth_status.get(service_name, {}).get("authenticated", False),
                "api_base_url": config.api_base_url
            }
            
            # Add category information
            if service_name in ["paperpal", "jenni_ai", "scispace", "consensus_ai", "elicit_ai", "semantic_scholar"]:
                service_info["category"] = "academic_papers"
            elif service_name in ["genspark", "manus", "gamma_app", "tome_app", "beautiful_ai"]:
                service_info["category"] = "presentations"
            elif service_name in ["pitchbook_ai", "cb_insights", "analyst_ai"]:
                service_info["category"] = "business_reports"
            elif service_name in ["perplexity_pro", "you_research", "tavily_research"]:
                service_info["category"] = "research_reports"
            elif service_name in ["jasper_ai", "copy_ai", "persado"]:
                service_info["category"] = "marketing_campaigns"
            else:
                service_info["category"] = "generic"
            
            services.append(service_info)
        
        # Group by category
        categories = {}
        for service in services:
            category = service["category"]
            if category not in categories:
                categories[category] = []
            categories[category].append(service)
        
        return {
            "success": True,
            "total_services": len(services),
            "services": services,
            "categories": categories
        }
    
    except Exception as e:
        logger.error(f"Error getting available services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting services: {str(e)}")

@oauth_router.post("/bulk-login")
async def initiate_bulk_login():
    """Initiate OAuth login for all configured services."""
    
    try:
        config_status = get_all_configured_services()
        auth_urls = {}
        
        for service_name, configured in config_status.items():
            if configured:
                config = get_oauth_config(service_name)
                if config and config.auth_type.value == "oauth2":
                    auth_url = generate_auth_url(service_name)
                    if auth_url:
                        auth_urls[service_name] = auth_url
        
        return {
            "success": True,
            "message": f"Generated auth URLs for {len(auth_urls)} services",
            "auth_urls": auth_urls,
            "instructions": "User needs to visit each auth_url to complete OAuth flow"
        }
    
    except Exception as e:
        logger.error(f"Error initiating bulk login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk login error: {str(e)}")

@oauth_router.get("/health")
async def auth_health_check():
    """Health check for authentication system."""
    
    try:
        # Check auth manager status
        auth_status = auth_manager.get_authentication_status()
        
        # Count authenticated services
        authenticated_count = sum(
            1 for status in auth_status.values() 
            if status.get("authenticated", False)
        )
        
        # Check for services expiring soon
        expiring_soon = []
        for service_name, status in auth_status.items():
            if status.get("expires_in_seconds"):
                if status["expires_in_seconds"] < 3600:  # Less than 1 hour
                    expiring_soon.append(service_name)
        
        return {
            "success": True,
            "status": "healthy",
            "authenticated_services": authenticated_count,
            "total_services": len(OAUTH_CONFIGS),
            "expiring_soon": expiring_soon,
            "timestamp": asyncio.get_event_loop().time()
        }
    
    except Exception as e:
        logger.error(f"Auth health check error: {str(e)}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": asyncio.get_event_loop().time()
        }
