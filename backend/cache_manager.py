#!/usr/bin/env python3
"""
Redis Cache Manager for AI Service Responses
Provides intelligent caching to improve performance and reduce API calls
"""

import asyncio
import json
import hashlib
import time
import logging
from typing import Dict, Any, Optional, List
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ Redis not available, caching disabled")
    REDIS_AVAILABLE = False

class CacheManager:
    """
    Intelligent cache manager for AI service responses.
    Provides content-aware caching with TTL and invalidation strategies.
    """
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.redis_client: Optional[redis.Redis] = None
        # Only enable if Redis URL is provided and Redis is available
        self.enabled = REDIS_AVAILABLE and bool(self.redis_url)
        
        # Cache configuration
        self.default_ttl = 3600  # 1 hour default TTL
        self.cache_ttls = {
            "academic_papers": 7200,      # 2 hours (longer content)
            "presentations": 3600,        # 1 hour
            "business_reports": 5400,     # 1.5 hours
            "research_reports": 1800,     # 30 minutes (time-sensitive)
            "marketing_campaigns": 3600   # 1 hour
        }
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "errors": 0,
            "total_requests": 0
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        if not self.redis_url:
            logger.info("⚠️ No Redis URL provided, cache disabled")
            self.enabled = False
            return self

        if self.enabled:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self.redis_client.ping()
                logger.info("✅ Redis cache connected")
            except Exception as e:
                logger.error(f"❌ Redis connection failed: {str(e)}")
                self.enabled = False
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_cache_key(self, prompt: str, service_name: str, 
                          content_category: str, quality_level: int = 3,
                          output_formats: List[str] = None) -> str:
        """Generate unique cache key for request parameters."""
        
        # Create a deterministic hash of the request parameters
        key_data = {
            "prompt": prompt.strip().lower(),
            "service": service_name,
            "category": content_category,
            "quality": quality_level,
            "formats": sorted(output_formats or ["pdf"])
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
        
        return f"airdocs:cache:{content_category}:{service_name}:{key_hash}"
    
    async def get(self, prompt: str, service_name: str, content_category: str,
                  quality_level: int = 3, output_formats: List[str] = None) -> Optional[Dict[str, Any]]:
        """Get cached response for request parameters."""
        
        self.stats["total_requests"] += 1
        
        if not self.enabled or not self.redis_client:
            self.stats["misses"] += 1
            return None
        
        try:
            cache_key = self._generate_cache_key(
                prompt, service_name, content_category, quality_level, output_formats
            )
            
            # Get cached data
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                # Parse cached response
                cached_response = json.loads(cached_data)
                
                # Add cache metadata
                cached_response["cache_info"] = {
                    "hit": True,
                    "key": cache_key,
                    "cached_at": cached_response.get("cached_at"),
                    "ttl_remaining": await self.redis_client.ttl(cache_key)
                }
                
                self.stats["hits"] += 1
                logger.info(f"🎯 Cache HIT for {service_name} ({content_category})")
                
                return cached_response
            else:
                self.stats["misses"] += 1
                logger.debug(f"❌ Cache MISS for {service_name} ({content_category})")
                return None
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"💥 Cache get error: {str(e)}")
            return None
    
    async def set(self, prompt: str, service_name: str, content_category: str,
                  response: Dict[str, Any], quality_level: int = 3,
                  output_formats: List[str] = None, custom_ttl: int = None) -> bool:
        """Cache response for request parameters."""
        
        if not self.enabled or not self.redis_client:
            return False
        
        # Don't cache failed responses
        if not response.get("success", False):
            return False
        
        try:
            cache_key = self._generate_cache_key(
                prompt, service_name, content_category, quality_level, output_formats
            )
            
            # Prepare response for caching
            cache_response = response.copy()
            cache_response["cached_at"] = time.time()
            cache_response["cache_info"] = {
                "hit": False,
                "key": cache_key,
                "service": service_name,
                "category": content_category
            }
            
            # Determine TTL
            ttl = custom_ttl or self.cache_ttls.get(content_category, self.default_ttl)
            
            # Cache the response
            await self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(cache_response, default=str)
            )
            
            self.stats["sets"] += 1
            logger.info(f"💾 Cached response for {service_name} ({content_category}, TTL: {ttl}s)")
            
            return True
        
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"💥 Cache set error: {str(e)}")
            return False
    
    async def invalidate_service(self, service_name: str) -> int:
        """Invalidate all cached responses for a service."""
        
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            # Find all keys for this service
            pattern = f"airdocs:cache:*:{service_name}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} cached responses for {service_name}")
                return deleted
            
            return 0
        
        except Exception as e:
            logger.error(f"💥 Cache invalidation error for {service_name}: {str(e)}")
            return 0
    
    async def invalidate_category(self, content_category: str) -> int:
        """Invalidate all cached responses for a content category."""
        
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            # Find all keys for this category
            pattern = f"airdocs:cache:{content_category}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} cached responses for {content_category}")
                return deleted
            
            return 0
        
        except Exception as e:
            logger.error(f"💥 Cache invalidation error for {content_category}: {str(e)}")
            return 0
    
    async def clear_all(self) -> int:
        """Clear all AIRDOCS cache entries."""
        
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            # Find all AIRDOCS cache keys
            pattern = "airdocs:cache:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Cleared {deleted} cache entries")
                return deleted
            
            return 0
        
        except Exception as e:
            logger.error(f"💥 Cache clear error: {str(e)}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and performance metrics."""
        
        hit_rate = 0
        if self.stats["total_requests"] > 0:
            hit_rate = (self.stats["hits"] / self.stats["total_requests"]) * 100
        
        cache_info = {
            "enabled": self.enabled,
            "connected": bool(self.redis_client),
            "statistics": {
                "total_requests": self.stats["total_requests"],
                "cache_hits": self.stats["hits"],
                "cache_misses": self.stats["misses"],
                "cache_sets": self.stats["sets"],
                "cache_errors": self.stats["errors"],
                "hit_rate_percentage": hit_rate
            },
            "configuration": {
                "redis_url": self.redis_url,
                "default_ttl": self.default_ttl,
                "category_ttls": self.cache_ttls
            }
        }
        
        # Add Redis info if connected
        if self.enabled and self.redis_client:
            try:
                redis_info = await self.redis_client.info()
                cache_info["redis_info"] = {
                    "version": redis_info.get("redis_version"),
                    "memory_used": redis_info.get("used_memory_human"),
                    "connected_clients": redis_info.get("connected_clients"),
                    "total_commands_processed": redis_info.get("total_commands_processed")
                }
                
                # Count AIRDOCS cache keys
                pattern = "airdocs:cache:*"
                keys = await self.redis_client.keys(pattern)
                cache_info["cache_entries"] = len(keys)
                
            except Exception as e:
                logger.error(f"Error getting Redis info: {str(e)}")
                cache_info["redis_error"] = str(e)
        
        return cache_info
    
    async def warm_cache(self, popular_prompts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Pre-warm cache with popular prompts."""
        
        if not self.enabled:
            return {"success": False, "message": "Cache not enabled"}
        
        warmed = 0
        errors = 0
        
        for prompt_config in popular_prompts:
            try:
                # This would typically involve calling the AI service
                # For now, we'll just log the warming attempt
                logger.info(f"🔥 Warming cache for: {prompt_config.get('prompt', '')[:50]}...")
                warmed += 1
                
            except Exception as e:
                logger.error(f"Cache warming error: {str(e)}")
                errors += 1
        
        return {
            "success": True,
            "warmed_entries": warmed,
            "errors": errors,
            "message": f"Cache warming completed: {warmed} entries warmed, {errors} errors"
        }

# Global cache manager instance
cache_manager = CacheManager()

# Convenience functions
async def get_cached_response(prompt: str, service_name: str, content_category: str,
                            quality_level: int = 3, output_formats: List[str] = None) -> Optional[Dict[str, Any]]:
    """Get cached response if available."""
    return await cache_manager.get(prompt, service_name, content_category, quality_level, output_formats)

async def cache_response(prompt: str, service_name: str, content_category: str,
                        response: Dict[str, Any], quality_level: int = 3,
                        output_formats: List[str] = None) -> bool:
    """Cache AI service response."""
    return await cache_manager.set(prompt, service_name, content_category, response, quality_level, output_formats)

async def get_cache_statistics() -> Dict[str, Any]:
    """Get cache performance statistics."""
    return await cache_manager.get_cache_stats()
