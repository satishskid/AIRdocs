#!/usr/bin/env python3
"""
AIRDOCS API vs Embedded Services Comparison Test
Validates that API services provide real AI integration while embedded services route correctly
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class APIvsEmbeddedTester:
    """Test API services vs Embedded services to validate dual-architecture implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        
        # API services that should have real integrations
        self.api_services = {
            "perplexity_pro": {
                "category": "research_reports",
                "expected_indicators": ["real_api: true", "model_used", "llama-3.1-sonar"],
                "quality_score": 94
            },
            "jasper_ai": {
                "category": "marketing_campaigns", 
                "expected_indicators": ["real_api: true", "template_used", "marketing_campaign"],
                "quality_score": 92
            },
            "semantic_scholar": {
                "category": "academic_papers",
                "expected_indicators": ["papers", "citations", "authors"],
                "quality_score": 90
            }
        }
        
        # Embedded services that should route to embedded interface
        self.embedded_services = {
            "genspark": {
                "category": "presentations",
                "embed_url": "https://www.genspark.ai/",
                "quality_score": 95
            },
            "paperpal": {
                "category": "academic_papers",
                "embed_url": "https://paperpal.com/",
                "quality_score": 96
            },
            "manus": {
                "category": "presentations",
                "embed_url": "https://www.manus.chat/",
                "quality_score": 93
            }
        }
        
        # Test prompts
        self.test_prompts = {
            "research_reports": "Analyze the latest trends in renewable energy adoption across European markets in 2024",
            "marketing_campaigns": "Create a comprehensive B2B marketing campaign for an AI-powered project management tool",
            "academic_papers": "Search for recent academic papers on machine learning applications in climate science",
            "presentations": "Create a business presentation on the future of artificial intelligence in healthcare"
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_api_service(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test an API service to verify real integration."""
        logger.info(f"🔗 Testing API service: {service_name}")
        
        category = service_config["category"]
        prompt = self.test_prompts[category]
        expected_indicators = service_config["expected_indicators"]
        
        start_time = time.time()
        
        try:
            payload = {
                "prompt": prompt,
                "content_category": category,
                "service_preference": service_name,
                "quality_level": 3
            }
            
            async with self.session.post(
                f"{self.base_url}/api/generate-content",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    content = data.get("content", "")
                    
                    # Check for real API indicators
                    real_api_indicators_found = []
                    for indicator in expected_indicators:
                        if indicator.lower() in content.lower():
                            real_api_indicators_found.append(indicator)
                    
                    # Check for mock/template indicators
                    mock_indicators = [
                        "enhanced mock content",
                        "template content", 
                        "note: this is enhanced mock content",
                        "mock",
                        "template"
                    ]
                    
                    mock_indicators_found = []
                    for indicator in mock_indicators:
                        if indicator.lower() in content.lower():
                            mock_indicators_found.append(indicator)
                    
                    is_real_api = len(real_api_indicators_found) > 0 and len(mock_indicators_found) == 0
                    
                    return {
                        "service_name": service_name,
                        "category": category,
                        "success": True,
                        "is_real_api": is_real_api,
                        "real_api_indicators_found": real_api_indicators_found,
                        "mock_indicators_found": mock_indicators_found,
                        "content_length": len(content),
                        "word_count": len(content.split()),
                        "response_time": response_time,
                        "quality_score": data.get("quality_score", 0),
                        "content_preview": content[:500] + "..." if len(content) > 500 else content
                    }
                else:
                    return {
                        "service_name": service_name,
                        "category": category,
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "response_time": response_time
                    }
                    
        except Exception as e:
            return {
                "service_name": service_name,
                "category": category,
                "success": False,
                "error": str(e),
                "response_time": time.time() - start_time
            }

    async def test_embedded_service_routing(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test embedded service routing to verify it routes to embedded interface."""
        logger.info(f"🌐 Testing embedded service routing: {service_name}")
        
        category = service_config["category"]
        
        try:
            # Test service routing endpoint
            payload = {
                "content_category": category,
                "prompt": self.test_prompts[category],
                "quality_level": 3
            }
            
            async with self.session.post(
                f"{self.base_url}/api/service/route",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    routing_decision = data.get("routing_decision", {})
                    
                    return {
                        "service_name": service_name,
                        "category": category,
                        "success": True,
                        "routes_to_embedded": routing_decision.get("service_type") == "embedded",
                        "selected_service": routing_decision.get("service_name"),
                        "quality_score": routing_decision.get("quality_score", 0),
                        "oauth_required": routing_decision.get("oauth_required", False),
                        "embed_url": routing_decision.get("embed_url", ""),
                        "routing_decision": routing_decision
                    }
                else:
                    return {
                        "service_name": service_name,
                        "category": category,
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "service_name": service_name,
                "category": category,
                "success": False,
                "error": str(e)
            }

    async def test_service_configuration_endpoint(self) -> Dict[str, Any]:
        """Test the service configuration endpoint."""
        logger.info("⚙️ Testing service configuration endpoint")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/services/configuration",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    services = data.get("services", {})
                    
                    api_services_count = len([s for s in services.values() if s.get("api_available")])
                    embedded_services_count = len([s for s in services.values() if not s.get("api_available")])
                    
                    return {
                        "success": True,
                        "total_services": len(services),
                        "api_services_count": api_services_count,
                        "embedded_services_count": embedded_services_count,
                        "categories": data.get("categories", []),
                        "services_by_category": {
                            category: len([s for s in services.values() if s.get("category") == category])
                            for category in data.get("categories", [])
                        }
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def run_comprehensive_comparison(self) -> Dict[str, Any]:
        """Run comprehensive API vs Embedded comparison tests."""
        logger.info("🧪 Starting API vs Embedded Services Comparison Test")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "api_service_tests": [],
            "embedded_service_tests": [],
            "service_configuration_test": {},
            "summary": {}
        }
        
        # Test service configuration endpoint
        config_result = await self.test_service_configuration_endpoint()
        results["service_configuration_test"] = config_result
        
        # Test API services
        logger.info("\n🔗 Testing API Services (Real Integration Expected)")
        for service_name, service_config in self.api_services.items():
            result = await self.test_api_service(service_name, service_config)
            results["api_service_tests"].append(result)
            
            status = "✅ REAL API" if result.get("is_real_api") else "❌ MOCK/TEMPLATE"
            logger.info(f"  {service_name}: {status}")
        
        # Test embedded services routing
        logger.info("\n🌐 Testing Embedded Services (Routing Expected)")
        for service_name, service_config in self.embedded_services.items():
            result = await self.test_embedded_service_routing(service_name, service_config)
            results["embedded_service_tests"].append(result)
            
            status = "✅ ROUTES TO EMBEDDED" if result.get("routes_to_embedded") else "❌ INCORRECT ROUTING"
            logger.info(f"  {service_name}: {status}")
        
        # Generate summary
        api_real_count = len([r for r in results["api_service_tests"] if r.get("is_real_api")])
        embedded_routing_count = len([r for r in results["embedded_service_tests"] if r.get("routes_to_embedded")])
        
        results["summary"] = {
            "api_services_tested": len(self.api_services),
            "api_services_real": api_real_count,
            "api_real_percentage": (api_real_count / len(self.api_services) * 100) if self.api_services else 0,
            "embedded_services_tested": len(self.embedded_services),
            "embedded_services_routing_correctly": embedded_routing_count,
            "embedded_routing_percentage": (embedded_routing_count / len(self.embedded_services) * 100) if self.embedded_services else 0,
            "dual_architecture_working": api_real_count > 0 and embedded_routing_count > 0
        }
        
        return results

    def generate_comparison_report(self, results: Dict[str, Any]) -> str:
        """Generate HTML comparison report."""
        
        summary = results["summary"]
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIRDOCS API vs Embedded Services Test Report</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 2rem; background: #f8fafc; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 3rem; }}
        .title {{ font-size: 2.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem; }}
        .subtitle {{ font-size: 1.2rem; color: #64748b; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 3rem; }}
        .summary-card {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; }}
        .summary-value {{ font-size: 2rem; font-weight: 700; color: #667eea; }}
        .summary-label {{ font-size: 0.9rem; color: #6b7280; margin-top: 0.5rem; }}
        .test-section {{ background: white; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .section-title {{ font-size: 1.5rem; font-weight: 600; color: #1e293b; margin-bottom: 1.5rem; }}
        .test-result {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }}
        .test-result.success {{ border-left: 4px solid #10b981; }}
        .test-result.failure {{ border-left: 4px solid #ef4444; }}
        .test-name {{ font-weight: 600; color: #374151; }}
        .test-details {{ font-size: 0.9rem; color: #6b7280; margin-top: 0.5rem; }}
        .status-badge {{ padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 500; }}
        .status-success {{ background: #dcfce7; color: #166534; }}
        .status-failure {{ background: #fee2e2; color: #991b1b; }}
        .content-preview {{ background: #f8fafc; padding: 1rem; border-radius: 8px; font-size: 0.9rem; margin-top: 1rem; max-height: 200px; overflow-y: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🔗 API vs 🌐 Embedded Services Test</div>
            <div class="subtitle">Validation of AIRDOCS Dual-Architecture Implementation</div>
            <div class="subtitle">Generated: {results["timestamp"]}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value">{summary["api_real_percentage"]:.0f}%</div>
                <div class="summary-label">API Services with Real Integration</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary["embedded_routing_percentage"]:.0f}%</div>
                <div class="summary-label">Embedded Services Routing Correctly</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{'✅' if summary["dual_architecture_working"] else '❌'}</div>
                <div class="summary-label">Dual Architecture Status</div>
            </div>
        </div>
        
        <div class="test-section">
            <div class="section-title">🔗 API Services Test Results</div>
"""
        
        for test in results["api_service_tests"]:
            status_class = "success" if test.get("is_real_api") else "failure"
            status_text = "Real API Integration" if test.get("is_real_api") else "Mock/Template Content"
            badge_class = "status-success" if test.get("is_real_api") else "status-failure"
            
            html_content += f"""
            <div class="test-result {status_class}">
                <div class="test-name">{test["service_name"].replace('_', ' ').title()}</div>
                <div class="test-details">
                    <span class="status-badge {badge_class}">{status_text}</span>
                    Category: {test["category"]} | 
                    Words: {test.get("word_count", 0)} | 
                    Time: {test.get("response_time", 0):.2f}s
                </div>
                {f'<div class="content-preview">{test.get("content_preview", "")}</div>' if test.get("content_preview") else ''}
            </div>
"""
        
        html_content += """
        </div>
        
        <div class="test-section">
            <div class="section-title">🌐 Embedded Services Test Results</div>
"""
        
        for test in results["embedded_service_tests"]:
            status_class = "success" if test.get("routes_to_embedded") else "failure"
            status_text = "Routes to Embedded" if test.get("routes_to_embedded") else "Incorrect Routing"
            badge_class = "status-success" if test.get("routes_to_embedded") else "status-failure"
            
            html_content += f"""
            <div class="test-result {status_class}">
                <div class="test-name">{test["service_name"].replace('_', ' ').title()}</div>
                <div class="test-details">
                    <span class="status-badge {badge_class}">{status_text}</span>
                    Category: {test["category"]} | 
                    Selected: {test.get("selected_service", "N/A")} |
                    OAuth: {'Required' if test.get("oauth_required") else 'Not Required'}
                </div>
            </div>
"""
        
        html_content += """
        </div>
    </div>
</body>
</html>
"""
        
        return html_content

async def main():
    """Run the API vs Embedded comparison test."""
    
    async with APIvsEmbeddedTester() as tester:
        # Run comprehensive comparison
        results = await tester.run_comprehensive_comparison()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"api_vs_embedded_test_{timestamp}.json"
        report_file = f"api_vs_embedded_report_{timestamp}.html"
        
        # Save JSON results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate and save HTML report
        html_report = tester.generate_comparison_report(results)
        with open(report_file, 'w') as f:
            f.write(html_report)
        
        # Print summary
        summary = results["summary"]
        
        print(f"\n🔗 API vs 🌐 Embedded Services Test Results")
        print(f"=" * 50)
        print(f"API Services Real Integration: {summary['api_services_real']}/{summary['api_services_tested']} ({summary['api_real_percentage']:.1f}%)")
        print(f"Embedded Services Routing: {summary['embedded_services_routing_correctly']}/{summary['embedded_services_tested']} ({summary['embedded_routing_percentage']:.1f}%)")
        print(f"Dual Architecture Working: {'✅ YES' if summary['dual_architecture_working'] else '❌ NO'}")
        
        print(f"\n📄 Detailed report: {report_file}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
