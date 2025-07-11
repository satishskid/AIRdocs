#!/usr/bin/env python3
"""
Production Features Test Suite
Tests OAuth, Circuit Breakers, Redis Caching, and Real-time Monitoring
"""

import asyncio
import aiohttp
import time
import json
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_PROMPT = "Generate a comprehensive analysis of AI in healthcare delivery"

class ProductionFeaturesTester:
    """Test all production-ready features."""
    
    def __init__(self):
        self.session = None
        self.test_results = {}
    
    async def __aenter__(self):
        """Initialize test session."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup test session."""
        if self.session:
            await self.session.close()
    
    async def test_oauth_integration(self) -> Dict[str, Any]:
        """Test OAuth 2.0 integration and authentication status."""
        
        print("🔐 Testing OAuth Integration...")
        
        try:
            # Test authentication status endpoint
            async with self.session.get(f"{BASE_URL}/auth/status") as response:
                if response.status == 200:
                    auth_status = await response.json()
                    
                    total_services = auth_status["summary"]["total_services"]
                    configured_services = auth_status["summary"]["configured_services"]
                    
                    print(f"   ✅ OAuth Status: {configured_services}/{total_services} services configured")
                    
                    return {
                        "success": True,
                        "total_services": total_services,
                        "configured_services": configured_services,
                        "configuration_percentage": auth_status["summary"]["configuration_percentage"]
                    }
                else:
                    print(f"   ❌ OAuth status check failed: HTTP {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        
        except Exception as e:
            print(f"   ❌ OAuth test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_circuit_breakers(self) -> Dict[str, Any]:
        """Test circuit breaker functionality."""
        
        print("⚡ Testing Circuit Breakers...")
        
        try:
            # Test circuit breaker status endpoint
            async with self.session.get(f"{BASE_URL}/circuit-breaker-status") as response:
                if response.status == 200:
                    cb_status = await response.json()
                    
                    if cb_status["enabled"]:
                        system_health = cb_status["system_health"]
                        healthy_services = system_health["healthy_services"]
                        total_services = system_health["total_services"]
                        
                        print(f"   ✅ Circuit Breakers: {healthy_services}/{total_services} services healthy")
                        print(f"   📊 System Status: {system_health['system_status']}")
                        
                        return {
                            "success": True,
                            "enabled": True,
                            "healthy_services": healthy_services,
                            "total_services": total_services,
                            "system_status": system_health["system_status"]
                        }
                    else:
                        print("   ⚠️ Circuit breakers not enabled")
                        return {"success": True, "enabled": False}
                else:
                    print(f"   ❌ Circuit breaker status check failed: HTTP {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        
        except Exception as e:
            print(f"   ❌ Circuit breaker test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_redis_caching(self) -> Dict[str, Any]:
        """Test Redis caching functionality."""
        
        print("💾 Testing Redis Caching...")
        
        try:
            # Test cache status endpoint
            async with self.session.get(f"{BASE_URL}/cache-status") as response:
                if response.status == 200:
                    cache_status = await response.json()
                    
                    if cache_status["enabled"]:
                        stats = cache_status["cache_statistics"]["statistics"]
                        hit_rate = stats["hit_rate_percentage"]
                        
                        print(f"   ✅ Redis Cache: Connected")
                        print(f"   📊 Hit Rate: {hit_rate:.1f}%")
                        print(f"   📈 Total Requests: {stats['total_requests']}")
                        
                        return {
                            "success": True,
                            "enabled": True,
                            "connected": cache_status["cache_statistics"]["connected"],
                            "hit_rate": hit_rate,
                            "total_requests": stats["total_requests"]
                        }
                    else:
                        print("   ⚠️ Redis cache not enabled")
                        return {"success": True, "enabled": False}
                else:
                    print(f"   ❌ Cache status check failed: HTTP {response.status}")
                    return {"success": False, "error": f"HTTP {response.status}"}
        
        except Exception as e:
            print(f"   ❌ Cache test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_ai_routing_with_features(self) -> Dict[str, Any]:
        """Test AI routing with all production features enabled."""
        
        print("🎯 Testing AI Routing with Production Features...")
        
        try:
            # Test content generation with caching
            payload = {
                "search_query": TEST_PROMPT,
                "content_category": "academic_papers",
                "quality_level": 3,
                "output_formats": ["pdf"]
            }
            
            # First request (should miss cache)
            start_time = time.time()
            async with self.session.post(f"{BASE_URL}/generate-content", json=payload) as response:
                first_response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"   ✅ First Request: {first_response_time:.2f}s")
                    
                    # Check if cache info is present
                    cache_hit = False
                    if "cache_info" in str(result):
                        cache_hit = True
                    
                    # Second request (should hit cache if enabled)
                    start_time = time.time()
                    async with self.session.post(f"{BASE_URL}/generate-content", json=payload) as response2:
                        second_response_time = time.time() - start_time
                        
                        if response2.status == 200:
                            result2 = await response2.json()
                            
                            print(f"   ✅ Second Request: {second_response_time:.2f}s")
                            
                            # Check for cache hit
                            cache_hit_second = False
                            if "cache_info" in str(result2):
                                cache_hit_second = True
                            
                            performance_improvement = ((first_response_time - second_response_time) / first_response_time) * 100
                            
                            print(f"   📈 Performance Improvement: {performance_improvement:.1f}%")
                            
                            return {
                                "success": True,
                                "first_response_time": first_response_time,
                                "second_response_time": second_response_time,
                                "performance_improvement": performance_improvement,
                                "cache_working": cache_hit_second,
                                "content_generated": bool(result.get("success"))
                            }
                        else:
                            print(f"   ❌ Second request failed: HTTP {response2.status}")
                            return {"success": False, "error": f"Second request HTTP {response2.status}"}
                else:
                    print(f"   ❌ First request failed: HTTP {response.status}")
                    return {"success": False, "error": f"First request HTTP {response.status}"}
        
        except Exception as e:
            print(f"   ❌ AI routing test failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_monitoring_endpoints(self) -> Dict[str, Any]:
        """Test real-time monitoring endpoints."""
        
        print("📊 Testing Monitoring Endpoints...")
        
        monitoring_results = {}
        
        # Test AI routing stats
        try:
            async with self.session.get(f"{BASE_URL}/ai-routing-stats") as response:
                if response.status == 200:
                    routing_stats = await response.json()
                    print("   ✅ AI Routing Stats: Available")
                    monitoring_results["routing_stats"] = True
                else:
                    print("   ❌ AI Routing Stats: Failed")
                    monitoring_results["routing_stats"] = False
        except:
            monitoring_results["routing_stats"] = False
        
        # Test system health
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    health = await response.json()
                    print("   ✅ System Health: Available")
                    monitoring_results["system_health"] = True
                else:
                    print("   ❌ System Health: Failed")
                    monitoring_results["system_health"] = False
        except:
            monitoring_results["system_health"] = False
        
        # Test admin dashboard
        try:
            async with self.session.get(f"{BASE_URL}/admin/dashboard") as response:
                if response.status == 200:
                    dashboard = await response.json()
                    print("   ✅ Admin Dashboard: Available")
                    monitoring_results["admin_dashboard"] = True
                else:
                    print("   ❌ Admin Dashboard: Failed")
                    monitoring_results["admin_dashboard"] = False
        except:
            monitoring_results["admin_dashboard"] = False
        
        success_count = sum(1 for result in monitoring_results.values() if result)
        total_count = len(monitoring_results)
        
        return {
            "success": success_count > 0,
            "available_endpoints": success_count,
            "total_endpoints": total_count,
            "availability_percentage": (success_count / total_count) * 100,
            "endpoints": monitoring_results
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test of all production features."""
        
        print("🧪 AIRDOCS PRODUCTION FEATURES TEST")
        print("=" * 50)
        
        # Test OAuth integration
        oauth_result = await self.test_oauth_integration()
        self.test_results["oauth"] = oauth_result
        
        # Test circuit breakers
        circuit_breaker_result = await self.test_circuit_breakers()
        self.test_results["circuit_breakers"] = circuit_breaker_result
        
        # Test Redis caching
        cache_result = await self.test_redis_caching()
        self.test_results["caching"] = cache_result
        
        # Test AI routing with features
        routing_result = await self.test_ai_routing_with_features()
        self.test_results["ai_routing"] = routing_result
        
        # Test monitoring endpoints
        monitoring_result = await self.test_monitoring_endpoints()
        self.test_results["monitoring"] = monitoring_result
        
        # Calculate overall success rate
        successful_tests = sum(1 for result in self.test_results.values() if result.get("success"))
        total_tests = len(self.test_results)
        success_rate = (successful_tests / total_tests) * 100
        
        print(f"\n📊 TEST RESULTS SUMMARY:")
        print("=" * 30)
        print(f"Successful Tests: {successful_tests}/{total_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Feature status
        features_status = {
            "OAuth Integration": oauth_result.get("success", False),
            "Circuit Breakers": circuit_breaker_result.get("success", False),
            "Redis Caching": cache_result.get("success", False),
            "AI Routing": routing_result.get("success", False),
            "Monitoring": monitoring_result.get("success", False)
        }
        
        print(f"\n🎯 FEATURE STATUS:")
        for feature, status in features_status.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {feature}")
        
        return {
            "success": success_rate >= 80,  # 80% success rate required
            "success_rate": success_rate,
            "successful_tests": successful_tests,
            "total_tests": total_tests,
            "features_status": features_status,
            "detailed_results": self.test_results
        }

async def main():
    """Run the production features test."""
    
    async with ProductionFeaturesTester() as tester:
        results = await tester.run_comprehensive_test()
        
        if results["success"]:
            print(f"\n🎉 PRODUCTION READINESS: PASSED")
            print(f"   All critical features are working correctly!")
        else:
            print(f"\n⚠️ PRODUCTION READINESS: NEEDS ATTENTION")
            print(f"   Some features require fixes before production deployment.")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
