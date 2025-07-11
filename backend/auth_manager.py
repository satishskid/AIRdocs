#!/usr/bin/env python3
"""
Authentication Manager for AI Services
Handles OAuth 2.0 flows, token management, and API authentication
"""

import asyncio
import aiohttp
import time
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import jwt
from cryptography.fernet import Fernet
import os

from oauth_config import OAUTH_CONFIGS, API_KEY_CONFIGS, AuthType, get_oauth_config, get_api_key_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TokenInfo:
    """Token information for authenticated service."""
    access_token: str
    refresh_token: Optional[str]
    expires_at: float
    token_type: str = "Bearer"
    scopes: List[str] = None
    service_name: str = ""

class AuthenticationManager:
    """
    Manages authentication and token lifecycle for all AI services.
    Handles OAuth 2.0 flows, token refresh, and secure storage.
    """
    
    def __init__(self, encryption_key: Optional[str] = None):
        self.tokens: Dict[str, TokenInfo] = {}
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Initialize encryption for secure token storage
        if encryption_key:
            self.cipher = Fernet(encryption_key.encode())
        else:
            # Generate a key for development (use proper key management in production)
            key = os.getenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
            self.cipher = Fernet(key.encode())
        
        # Token refresh background task
        self._refresh_task = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        # Start token refresh background task
        self._refresh_task = asyncio.create_task(self._token_refresh_loop())
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._refresh_task:
            self._refresh_task.cancel()
        if self.session:
            await self.session.close()
    
    def generate_auth_url(self, service_name: str, state: Optional[str] = None) -> Optional[str]:
        """Generate OAuth authorization URL for service."""
        
        config = get_oauth_config(service_name)
        if not config or config.auth_type != AuthType.OAUTH2:
            return None
        
        # Build authorization URL
        params = {
            "client_id": config.client_id,
            "response_type": "code",
            "redirect_uri": config.redirect_uri,
            "scope": " ".join(config.scopes),
            "state": state or f"{service_name}_{int(time.time())}"
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        auth_url = f"{config.auth_url}?{query_string}"
        
        logger.info(f"🔗 Generated auth URL for {service_name}")
        return auth_url
    
    async def exchange_code_for_token(self, service_name: str, code: str, state: Optional[str] = None) -> bool:
        """Exchange authorization code for access token."""
        
        config = get_oauth_config(service_name)
        if not config or config.auth_type != AuthType.OAUTH2:
            logger.error(f"❌ Invalid OAuth config for {service_name}")
            return False
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Prepare token exchange request
        data = {
            "grant_type": "authorization_code",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "code": code,
            "redirect_uri": config.redirect_uri
        }
        
        try:
            async with self.session.post(config.token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Create token info
                    expires_in = token_data.get("expires_in", 3600)
                    token_info = TokenInfo(
                        access_token=token_data["access_token"],
                        refresh_token=token_data.get("refresh_token"),
                        expires_at=time.time() + expires_in,
                        token_type=token_data.get("token_type", "Bearer"),
                        scopes=config.scopes,
                        service_name=service_name
                    )
                    
                    # Store encrypted token
                    self.tokens[service_name] = token_info
                    await self._save_token_to_storage(service_name, token_info)
                    
                    logger.info(f"✅ Successfully authenticated {service_name}")
                    return True
                
                else:
                    error_data = await response.text()
                    logger.error(f"❌ Token exchange failed for {service_name}: {error_data}")
                    return False
        
        except Exception as e:
            logger.error(f"💥 Token exchange error for {service_name}: {str(e)}")
            return False
    
    async def get_valid_token(self, service_name: str) -> Optional[str]:
        """Get valid access token for service, refreshing if necessary."""
        
        # Check if we have a stored token
        if service_name not in self.tokens:
            await self._load_token_from_storage(service_name)
        
        if service_name not in self.tokens:
            logger.warning(f"⚠️ No token found for {service_name}")
            return None
        
        token_info = self.tokens[service_name]
        
        # Check if token is expired
        if time.time() >= token_info.expires_at - 300:  # Refresh 5 minutes before expiry
            logger.info(f"🔄 Token expired for {service_name}, attempting refresh")
            
            if await self._refresh_token(service_name):
                token_info = self.tokens[service_name]
            else:
                logger.error(f"❌ Failed to refresh token for {service_name}")
                return None
        
        return token_info.access_token
    
    async def get_auth_headers(self, service_name: str) -> Dict[str, str]:
        """Get authentication headers for API requests."""
        
        config = get_oauth_config(service_name)
        if not config:
            return {}
        
        if config.auth_type == AuthType.OAUTH2:
            token = await self.get_valid_token(service_name)
            if token:
                return {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
        
        elif config.auth_type == AuthType.API_KEY:
            api_config = get_api_key_config(service_name)
            if api_config and api_config["api_key"]:
                header_value = api_config["header_format"].format(api_key=api_config["api_key"])
                return {
                    api_config["header_name"]: header_value,
                    "Content-Type": "application/json"
                }
        
        return {"Content-Type": "application/json"}
    
    async def _refresh_token(self, service_name: str) -> bool:
        """Refresh access token using refresh token."""
        
        if service_name not in self.tokens:
            return False
        
        token_info = self.tokens[service_name]
        if not token_info.refresh_token:
            logger.warning(f"⚠️ No refresh token for {service_name}")
            return False
        
        config = get_oauth_config(service_name)
        if not config:
            return False
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        # Prepare refresh request
        data = {
            "grant_type": "refresh_token",
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": token_info.refresh_token
        }
        
        try:
            async with self.session.post(config.token_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    
                    # Update token info
                    expires_in = token_data.get("expires_in", 3600)
                    token_info.access_token = token_data["access_token"]
                    token_info.expires_at = time.time() + expires_in
                    
                    # Update refresh token if provided
                    if "refresh_token" in token_data:
                        token_info.refresh_token = token_data["refresh_token"]
                    
                    # Save updated token
                    await self._save_token_to_storage(service_name, token_info)
                    
                    logger.info(f"✅ Successfully refreshed token for {service_name}")
                    return True
                
                else:
                    logger.error(f"❌ Token refresh failed for {service_name}")
                    return False
        
        except Exception as e:
            logger.error(f"💥 Token refresh error for {service_name}: {str(e)}")
            return False
    
    async def _save_token_to_storage(self, service_name: str, token_info: TokenInfo):
        """Save encrypted token to persistent storage."""
        
        try:
            # Convert to dict and encrypt
            token_dict = asdict(token_info)
            token_json = json.dumps(token_dict)
            encrypted_token = self.cipher.encrypt(token_json.encode())
            
            # Save to file (in production, use proper database)
            storage_dir = "tokens"
            os.makedirs(storage_dir, exist_ok=True)
            
            with open(f"{storage_dir}/{service_name}.token", "wb") as f:
                f.write(encrypted_token)
            
            logger.debug(f"💾 Saved token for {service_name}")
        
        except Exception as e:
            logger.error(f"💥 Failed to save token for {service_name}: {str(e)}")
    
    async def _load_token_from_storage(self, service_name: str):
        """Load encrypted token from persistent storage."""
        
        try:
            token_file = f"tokens/{service_name}.token"
            if not os.path.exists(token_file):
                return
            
            with open(token_file, "rb") as f:
                encrypted_token = f.read()
            
            # Decrypt and parse
            token_json = self.cipher.decrypt(encrypted_token).decode()
            token_dict = json.loads(token_json)
            
            # Create TokenInfo object
            token_info = TokenInfo(**token_dict)
            self.tokens[service_name] = token_info
            
            logger.debug(f"📂 Loaded token for {service_name}")
        
        except Exception as e:
            logger.error(f"💥 Failed to load token for {service_name}: {str(e)}")
    
    async def _token_refresh_loop(self):
        """Background task to refresh tokens before expiry."""
        
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                current_time = time.time()
                for service_name, token_info in self.tokens.items():
                    # Refresh tokens that expire in the next 10 minutes
                    if current_time >= token_info.expires_at - 600:
                        logger.info(f"🔄 Background refresh for {service_name}")
                        await self._refresh_token(service_name)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"💥 Token refresh loop error: {str(e)}")
    
    def get_authentication_status(self) -> Dict[str, Dict[str, Any]]:
        """Get authentication status for all services."""
        
        status = {}
        current_time = time.time()
        
        for service_name in OAUTH_CONFIGS.keys():
            if service_name in self.tokens:
                token_info = self.tokens[service_name]
                expires_in = max(0, token_info.expires_at - current_time)
                
                status[service_name] = {
                    "authenticated": True,
                    "expires_in_seconds": expires_in,
                    "expires_at": datetime.fromtimestamp(token_info.expires_at).isoformat(),
                    "scopes": token_info.scopes,
                    "has_refresh_token": bool(token_info.refresh_token)
                }
            else:
                config = get_oauth_config(service_name)
                if config and config.auth_type == AuthType.API_KEY:
                    api_config = get_api_key_config(service_name)
                    status[service_name] = {
                        "authenticated": bool(api_config and api_config["api_key"]),
                        "auth_type": "api_key",
                        "expires_in_seconds": None,
                        "expires_at": None
                    }
                else:
                    status[service_name] = {
                        "authenticated": False,
                        "auth_type": "oauth2",
                        "expires_in_seconds": None,
                        "expires_at": None
                    }
        
        return status
    
    async def revoke_token(self, service_name: str) -> bool:
        """Revoke authentication for service."""
        
        try:
            # Remove from memory
            if service_name in self.tokens:
                del self.tokens[service_name]
            
            # Remove from storage
            token_file = f"tokens/{service_name}.token"
            if os.path.exists(token_file):
                os.remove(token_file)
            
            logger.info(f"🗑️ Revoked authentication for {service_name}")
            return True
        
        except Exception as e:
            logger.error(f"💥 Failed to revoke token for {service_name}: {str(e)}")
            return False

# Global authentication manager instance
auth_manager = AuthenticationManager()

# Convenience functions
async def get_auth_headers(service_name: str) -> Dict[str, str]:
    """Get authentication headers for service."""
    return await auth_manager.get_auth_headers(service_name)

async def is_service_authenticated(service_name: str) -> bool:
    """Check if service is authenticated."""
    token = await auth_manager.get_valid_token(service_name)
    return token is not None

def generate_auth_url(service_name: str) -> Optional[str]:
    """Generate OAuth authorization URL for service."""
    return auth_manager.generate_auth_url(service_name)
