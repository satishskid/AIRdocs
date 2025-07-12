#!/usr/bin/env python3
"""
AIRDOCS Implementation Validation Test
Quick validation of dual-architecture implementation with current endpoints
"""

import asyncio
import aiohttp
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImplementationValidator:
    """Validate the current AIRDOCS dual-architecture implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_service_configuration(self) -> dict:
        """Test the service configuration endpoint."""
        logger.info("🔧 Testing service configuration endpoint...")
        
        try:
            async with self.session.get(f"{self.base_url}/api/services/configuration") as response:
                if response.status == 200:
                    data = await response.json()
                    services = data.get("services", {})
                    
                    # Analyze service configuration
                    total_services = len(services)
                    api_services = [s for s in services.values() if s.get("api_available")]
                    embedded_services = [s for s in services.values() if not s.get("api_available")]
                    
                    categories = {}
                    for service in services.values():
                        category = service.get("category", "unknown")
                        if category not in categories:
                            categories[category] = []
                        categories[category].append(service)
                    
                    return {
                        "success": True,
                        "total_services": total_services,
                        "api_services_count": len(api_services),
                        "embedded_services_count": len(embedded_services),
                        "categories": list(categories.keys()),
                        "services_by_category": {cat: len(services) for cat, services in categories.items()},
                        "quality_scores": [s.get("quality_score", 0) for s in services.values()],
                        "sample_services": list(services.keys())[:5]
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_embedded_interfaces(self) -> dict:
        """Test embedded service interfaces."""
        logger.info("🌐 Testing embedded service interfaces...")
        
        interfaces_to_test = [
            ("/services", "Embedded Services Hub"),
            ("/selector", "Service Selector"),
            ("/", "Main Interface")
        ]
        
        results = {}
        
        for endpoint, name in interfaces_to_test:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        content = await response.text()
                        results[endpoint] = {
                            "success": True,
                            "name": name,
                            "content_length": len(content),
                            "has_oauth": "oauth" in content.lower(),
                            "has_iframe": "iframe" in content.lower(),
                            "has_service_selection": "service" in content.lower()
                        }
                    else:
                        results[endpoint] = {
                            "success": False,
                            "name": name,
                            "error": f"HTTP {response.status}"
                        }
            except Exception as e:
                results[endpoint] = {
                    "success": False,
                    "name": name,
                    "error": str(e)
                }
        
        return results

    async def test_oauth_flow(self) -> dict:
        """Test OAuth authentication flow."""
        logger.info("🔐 Testing OAuth authentication flow...")
        
        try:
            # Test OAuth initiation
            async with self.session.post(f"{self.base_url}/api/auth/google/initiate") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "has_auth_url": "auth_url" in data,
                        "has_state": "state" in data,
                        "auth_url_valid": data.get("auth_url", "").startswith("https://accounts.google.com")
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_api_search_papers(self) -> dict:
        """Test the academic paper search API."""
        logger.info("📚 Testing academic paper search API...")
        
        try:
            payload = {
                "query": "machine learning climate change",
                "limit": 5
            }
            
            async with self.session.post(
                f"{self.base_url}/api/search-papers",
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    papers = data.get("papers", [])
                    
                    return {
                        "success": True,
                        "papers_found": len(papers),
                        "has_real_data": len(papers) > 0 and any(paper.get("title") for paper in papers),
                        "sample_paper": papers[0] if papers else None
                    }
                else:
                    return {"success": False, "error": f"HTTP {response.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def test_service_routing(self) -> dict:
        """Test intelligent service routing."""
        logger.info("🎯 Testing intelligent service routing...")
        
        test_cases = [
            {"content_category": "presentations", "prompt": "Create a business presentation"},
            {"content_category": "academic_papers", "prompt": "Write a research paper"},
            {"content_category": "research_reports", "prompt": "Analyze market trends"}
        ]
        
        results = {}
        
        for test_case in test_cases:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/service/route",
                    json=test_case
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        routing_decision = data.get("routing_decision", {})
                        
                        results[test_case["content_category"]] = {
                            "success": True,
                            "selected_service": routing_decision.get("service_name"),
                            "service_type": routing_decision.get("service_type"),
                            "quality_score": routing_decision.get("quality_score"),
                            "oauth_required": routing_decision.get("oauth_required")
                        }
                    else:
                        results[test_case["content_category"]] = {
                            "success": False,
                            "error": f"HTTP {response.status}"
                        }
            except Exception as e:
                results[test_case["content_category"]] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results

    async def run_validation(self) -> dict:
        """Run comprehensive validation of the dual-architecture implementation."""
        logger.info("🧪 Starting AIRDOCS Implementation Validation...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "validation_results": {}
        }
        
        # Test 1: Service Configuration
        config_result = await self.test_service_configuration()
        results["validation_results"]["service_configuration"] = config_result
        
        # Test 2: Embedded Interfaces
        interface_result = await self.test_embedded_interfaces()
        results["validation_results"]["embedded_interfaces"] = interface_result
        
        # Test 3: OAuth Flow
        oauth_result = await self.test_oauth_flow()
        results["validation_results"]["oauth_flow"] = oauth_result
        
        # Test 4: API Search Papers
        search_result = await self.test_api_search_papers()
        results["validation_results"]["api_search_papers"] = search_result
        
        # Test 5: Service Routing
        routing_result = await self.test_service_routing()
        results["validation_results"]["service_routing"] = routing_result
        
        # Generate summary
        results["summary"] = self._generate_summary(results["validation_results"])
        
        return results

    def _generate_summary(self, validation_results: dict) -> dict:
        """Generate a summary of validation results."""
        
        total_tests = 0
        passed_tests = 0
        
        # Count service configuration tests
        if validation_results.get("service_configuration", {}).get("success"):
            passed_tests += 1
        total_tests += 1
        
        # Count interface tests
        interface_results = validation_results.get("embedded_interfaces", {})
        for endpoint_result in interface_results.values():
            if isinstance(endpoint_result, dict) and endpoint_result.get("success"):
                passed_tests += 1
            total_tests += 1
        
        # Count OAuth test
        if validation_results.get("oauth_flow", {}).get("success"):
            passed_tests += 1
        total_tests += 1
        
        # Count API search test
        if validation_results.get("api_search_papers", {}).get("success"):
            passed_tests += 1
        total_tests += 1
        
        # Count routing tests
        routing_results = validation_results.get("service_routing", {})
        for category_result in routing_results.values():
            if isinstance(category_result, dict) and category_result.get("success"):
                passed_tests += 1
            total_tests += 1
        
        # Get service configuration details
        config = validation_results.get("service_configuration", {})
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "dual_architecture_implemented": passed_tests >= total_tests * 0.7,  # 70% success threshold
            "total_services_configured": config.get("total_services", 0),
            "api_services_available": config.get("api_services_count", 0),
            "embedded_services_available": config.get("embedded_services_count", 0),
            "categories_supported": len(config.get("categories", [])),
            "key_features_working": {
                "service_configuration": validation_results.get("service_configuration", {}).get("success", False),
                "embedded_interfaces": any(r.get("success", False) for r in validation_results.get("embedded_interfaces", {}).values()),
                "oauth_authentication": validation_results.get("oauth_flow", {}).get("success", False),
                "api_integration": validation_results.get("api_search_papers", {}).get("success", False),
                "intelligent_routing": any(r.get("success", False) for r in validation_results.get("service_routing", {}).values())
            }
        }

    def generate_validation_report(self, results: dict) -> str:
        """Generate HTML validation report."""
        
        summary = results["summary"]
        validation_results = results["validation_results"]
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIRDOCS Implementation Validation Report</title>
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
        .status-badge {{ padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 500; }}
        .status-success {{ background: #dcfce7; color: #166534; }}
        .status-failure {{ background: #fee2e2; color: #991b1b; }}
        .feature-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; }}
        .feature-item {{ display: flex; align-items: center; gap: 0.5rem; padding: 0.5rem; }}
        .feature-icon {{ font-size: 1.2rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🧪 AIRDOCS Implementation Validation</div>
            <div class="subtitle">Dual-Architecture Implementation Status Report</div>
            <div class="subtitle">Generated: {results["timestamp"]}</div>
        </div>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value">{summary["success_rate"]:.1f}%</div>
                <div class="summary-label">Tests Passed</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary["total_services_configured"]}</div>
                <div class="summary-label">Services Configured</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{summary["categories_supported"]}</div>
                <div class="summary-label">Categories Supported</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{'✅' if summary["dual_architecture_implemented"] else '❌'}</div>
                <div class="summary-label">Dual Architecture</div>
            </div>
        </div>
        
        <div class="test-section">
            <div class="section-title">🔧 Service Configuration</div>
            <div class="test-result {'success' if validation_results.get('service_configuration', {}).get('success') else 'failure'}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>Service Configuration Endpoint</span>
                    <span class="status-badge {'status-success' if validation_results.get('service_configuration', {}).get('success') else 'status-failure'}">
                        {'✅ Working' if validation_results.get('service_configuration', {}).get('success') else '❌ Failed'}
                    </span>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #6b7280;">
                    API Services: {summary["api_services_available"]} | 
                    Embedded Services: {summary["embedded_services_available"]} |
                    Categories: {summary["categories_supported"]}
                </div>
            </div>
        </div>
        
        <div class="test-section">
            <div class="section-title">🌐 Embedded Interfaces</div>
"""
        
        # Add interface test results
        interface_results = validation_results.get("embedded_interfaces", {})
        for endpoint, result in interface_results.items():
            if isinstance(result, dict):
                status_class = "success" if result.get("success") else "failure"
                status_text = "✅ Working" if result.get("success") else "❌ Failed"
                
                html_content += f"""
            <div class="test-result {status_class}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span>{result.get('name', endpoint)}</span>
                    <span class="status-badge status-{'success' if result.get('success') else 'failure'}">{status_text}</span>
                </div>
                <div style="margin-top: 0.5rem; font-size: 0.9rem; color: #6b7280;">
                    Endpoint: {endpoint} | 
                    Content Length: {result.get('content_length', 0)} chars |
                    Has OAuth: {'Yes' if result.get('has_oauth') else 'No'} |
                    Has iFrame: {'Yes' if result.get('has_iframe') else 'No'}
                </div>
            </div>
"""
        
        html_content += f"""
        </div>
        
        <div class="test-section">
            <div class="section-title">🎯 Key Features Status</div>
            <div class="feature-grid">
"""
        
        # Add feature status
        features = summary["key_features_working"]
        feature_names = {
            "service_configuration": "Service Configuration",
            "embedded_interfaces": "Embedded Interfaces", 
            "oauth_authentication": "OAuth Authentication",
            "api_integration": "API Integration",
            "intelligent_routing": "Intelligent Routing"
        }
        
        for feature_key, working in features.items():
            feature_name = feature_names.get(feature_key, feature_key)
            icon = "✅" if working else "❌"
            
            html_content += f"""
                <div class="feature-item">
                    <span class="feature-icon">{icon}</span>
                    <span>{feature_name}</span>
                </div>
"""
        
        html_content += """
            </div>
        </div>
    </div>
</body>
</html>
"""
        
        return html_content

async def main():
    """Run the implementation validation."""
    
    async with ImplementationValidator() as validator:
        # Run validation
        results = await validator.run_validation()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"validation_results_{timestamp}.json"
        report_file = f"validation_report_{timestamp}.html"
        
        # Save JSON results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Generate and save HTML report
        html_report = validator.generate_validation_report(results)
        with open(report_file, 'w') as f:
            f.write(html_report)
        
        # Print summary
        summary = results["summary"]
        
        print(f"\n🧪 AIRDOCS Implementation Validation Results")
        print(f"=" * 50)
        print(f"Tests Passed: {summary['passed_tests']}/{summary['total_tests']} ({summary['success_rate']:.1f}%)")
        print(f"Dual Architecture Implemented: {'✅ YES' if summary['dual_architecture_implemented'] else '❌ NO'}")
        print(f"Total Services Configured: {summary['total_services_configured']}")
        print(f"API Services: {summary['api_services_available']}")
        print(f"Embedded Services: {summary['embedded_services_available']}")
        print(f"Categories Supported: {summary['categories_supported']}")
        
        print(f"\n🎯 Key Features Status:")
        for feature, working in summary["key_features_working"].items():
            status = "✅ Working" if working else "❌ Failed"
            print(f"  {feature.replace('_', ' ').title()}: {status}")
        
        print(f"\n📄 Detailed report: {report_file}")
        
        return results

if __name__ == "__main__":
    asyncio.run(main())
