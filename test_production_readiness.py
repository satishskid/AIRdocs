#!/usr/bin/env python3
"""
AI Document Factory - Production Readiness Testing Suite
Comprehensive testing for all 7 content categories and business workflows
"""

import requests
import json
import time
import os
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_RESULTS = []

def log_test(test_name, status, details=""):
    """Log test results"""
    result = {
        "test": test_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details
    }
    TEST_RESULTS.append(result)
    print(f"{'✅' if status == 'PASS' else '❌'} {test_name}: {status}")
    if details:
        print(f"   Details: {details}")

def test_health_check():
    """Test system health and availability"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            log_test("Health Check", "PASS", f"System status: {health_data.get('status', 'unknown')}")
            return True
        else:
            log_test("Health Check", "FAIL", f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test("Health Check", "FAIL", str(e))
        return False

def test_category_generation(category, title, query, template_id):
    """Test document generation for a specific category"""
    try:
        payload = {
            "search_query": query,
            "document_title": title,
            "content_category": category,
            "template_id": template_id,
            "quality_level": 3,
            "output_formats": ["pdf", "pptx", "docx"]
        }
        
        start_time = time.time()
        response = requests.post(f"{BASE_URL}/generate-content", 
                               json=payload, 
                               timeout=30)
        generation_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                # Check if all formats were generated
                documents = data.get("documents", {})
                formats_generated = list(documents.keys())
                
                log_test(f"{category.title()} Generation", "PASS", 
                        f"Generated {len(formats_generated)} formats in {generation_time:.1f}s")
                
                # Test download links
                for format_type, doc_info in documents.items():
                    download_url = doc_info.get("download_url")
                    if download_url:
                        test_download(category, format_type, download_url)
                
                return True
            else:
                log_test(f"{category.title()} Generation", "FAIL", "Success=False in response")
                return False
        else:
            log_test(f"{category.title()} Generation", "FAIL", f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        log_test(f"{category.title()} Generation", "FAIL", str(e))
        return False

def test_download(category, format_type, download_url):
    """Test document download functionality"""
    try:
        response = requests.head(f"{BASE_URL}{download_url}", timeout=10)
        if response.status_code == 200:
            file_size = response.headers.get('content-length', 'unknown')
            log_test(f"{category.title()} {format_type.upper()} Download", "PASS", 
                    f"File size: {file_size} bytes")
            return True
        else:
            log_test(f"{category.title()} {format_type.upper()} Download", "FAIL", 
                    f"HTTP {response.status_code}")
            return False
    except Exception as e:
        log_test(f"{category.title()} {format_type.upper()} Download", "FAIL", str(e))
        return False

def run_comprehensive_tests():
    """Run all production readiness tests"""
    print("🏭 AI Document Factory - Production Readiness Testing")
    print("=" * 60)
    
    # Test 1: System Health
    if not test_health_check():
        print("❌ System health check failed. Aborting tests.")
        return False
    
    # Test 2: All 7 Content Categories
    test_scenarios = [
        {
            "category": "reports",
            "title": "Q4 Business Performance Analysis",
            "query": "Generate a comprehensive quarterly business report with financial metrics, market analysis, competitive positioning, and strategic recommendations for the next quarter.",
            "template_id": "quarterly-business-report"
        },
        {
            "category": "marketing",
            "title": "Product Launch Campaign Package",
            "query": "Create a complete product launch marketing campaign including email sequences, social media content, press releases, and sales enablement materials for a new AI analytics platform.",
            "template_id": "product-launch-campaign"
        },
        {
            "category": "presentations",
            "title": "Investor Pitch Deck",
            "query": "Develop a compelling investor presentation for a Series A funding round, including market opportunity, business model, traction metrics, and funding requirements.",
            "template_id": "investor-pitch"
        },
        {
            "category": "communications",
            "title": "Executive Project Proposal",
            "query": "Create a comprehensive project proposal for implementing AI automation across enterprise operations, including scope, timeline, budget, and ROI projections.",
            "template_id": "project-proposal"
        },
        {
            "category": "documentation",
            "title": "API Integration Guide",
            "query": "Develop a complete technical documentation package for API integration, including setup instructions, code examples, troubleshooting, and best practices.",
            "template_id": "technical-guide"
        },
        {
            "category": "academic",
            "title": "AI Ethics Research Paper",
            "query": "Write a comprehensive academic research paper on AI ethics in business applications, including literature review, methodology, findings, and recommendations.",
            "template_id": "research-paper"
        },
        {
            "category": "research",
            "title": "Market Research Analysis",
            "query": "Conduct a systematic market research analysis of the AI document generation industry, including competitive landscape, market size, trends, and opportunities.",
            "template_id": "market-analysis"
        }
    ]
    
    successful_tests = 0
    total_tests = len(test_scenarios)
    
    for scenario in test_scenarios:
        if test_category_generation(**scenario):
            successful_tests += 1
        time.sleep(2)  # Brief pause between tests
    
    # Test 3: Performance Metrics
    print("\n📊 Performance Summary")
    print("-" * 40)
    print(f"Categories Tested: {total_tests}")
    print(f"Successful Generations: {successful_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    # Test 4: Generate Summary Report
    generate_test_report()
    
    return successful_tests == total_tests

def generate_test_report():
    """Generate a comprehensive test report"""
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    summary = {
        "test_suite": "AI Document Factory Production Readiness",
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(TEST_RESULTS),
        "passed_tests": len([r for r in TEST_RESULTS if r["status"] == "PASS"]),
        "failed_tests": len([r for r in TEST_RESULTS if r["status"] == "FAIL"]),
        "results": TEST_RESULTS
    }
    
    with open(report_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📋 Test report saved: {report_file}")
    
    # Print summary
    print(f"\n🎯 Final Results:")
    print(f"   Total Tests: {summary['total_tests']}")
    print(f"   Passed: {summary['passed_tests']}")
    print(f"   Failed: {summary['failed_tests']}")
    print(f"   Success Rate: {(summary['passed_tests']/summary['total_tests'])*100:.1f}%")

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)
