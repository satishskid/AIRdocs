#!/usr/bin/env python3
"""
AIRDOCS Dual-Architecture Testing Framework
Comprehensive validation of all 20+ AI services across both architectures
"""

import asyncio
import aiohttp
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestPrompt:
    """Standardized test prompt for each content category."""
    category: str
    prompt: str
    expected_keywords: List[str]
    min_word_count: int
    quality_indicators: List[str]

@dataclass
class ServiceTestResult:
    """Results from testing a single service."""
    service_name: str
    category: str
    prompt: str
    output_content: str
    word_count: int
    response_time: float
    quality_score: int
    access_type: str  # 'api' or 'embedded'
    is_real_ai: bool  # True if real AI, False if template/mock
    specialization_evident: bool
    professional_formatting: bool
    contains_expected_keywords: bool
    unique_content_hash: str
    timestamp: datetime
    error_message: Optional[str] = None

class DualArchitectureTestFramework:
    """Comprehensive testing framework for AIRDOCS dual-architecture implementation."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results: List[ServiceTestResult] = []
        
        # Standardized test prompts for each category
        self.test_prompts = {
            "presentations": TestPrompt(
                category="presentations",
                prompt="Create a comprehensive business presentation about the future of artificial intelligence in healthcare, including market analysis, key technologies, implementation challenges, and ROI projections for hospital systems.",
                expected_keywords=["AI", "healthcare", "market", "ROI", "hospital", "technology", "implementation"],
                min_word_count=800,
                quality_indicators=["executive summary", "market size", "competitive analysis", "financial projections"]
            ),
            "academic_papers": TestPrompt(
                category="academic_papers", 
                prompt="Write a comprehensive academic research paper on the impact of machine learning algorithms on climate change prediction models, including literature review, methodology, results analysis, and future research directions.",
                expected_keywords=["machine learning", "climate change", "prediction models", "methodology", "literature review", "research"],
                min_word_count=2000,
                quality_indicators=["abstract", "introduction", "methodology", "results", "conclusion", "references"]
            ),
            "research_reports": TestPrompt(
                category="research_reports",
                prompt="Conduct comprehensive research on the global renewable energy market trends for 2024-2025, including policy changes, technological breakthroughs, investment flows, and regional market dynamics.",
                expected_keywords=["renewable energy", "market trends", "policy", "investment", "technology", "regional"],
                min_word_count=1500,
                quality_indicators=["executive summary", "market data", "trend analysis", "regional breakdown", "forecasts"]
            ),
            "business_reports": TestPrompt(
                category="business_reports",
                prompt="Analyze the competitive landscape and market opportunities for fintech startups in Southeast Asia, including regulatory environment, key players, funding trends, and strategic recommendations.",
                expected_keywords=["fintech", "Southeast Asia", "competitive landscape", "regulatory", "funding", "strategic"],
                min_word_count=1200,
                quality_indicators=["market analysis", "competitive matrix", "regulatory overview", "recommendations"]
            ),
            "marketing_campaigns": TestPrompt(
                category="marketing_campaigns",
                prompt="Design a comprehensive digital marketing campaign for a B2B SaaS productivity platform targeting remote teams, including messaging strategy, channel selection, content calendar, and performance metrics.",
                expected_keywords=["B2B SaaS", "productivity", "remote teams", "digital marketing", "messaging", "metrics"],
                min_word_count=1000,
                quality_indicators=["target audience", "value proposition", "campaign strategy", "content calendar", "KPIs"]
            )
        }
        
        # Service configuration for testing
        self.services_to_test = {
            "presentations": [
                {"name": "genspark", "quality_score": 95, "access_type": "embedded"},
                {"name": "manus", "quality_score": 93, "access_type": "embedded"},
                {"name": "gamma_app", "quality_score": 91, "access_type": "embedded"},
                {"name": "tome_app", "quality_score": 89, "access_type": "embedded"},
                {"name": "beautiful_ai", "quality_score": 87, "access_type": "embedded"}
            ],
            "academic_papers": [
                {"name": "paperpal", "quality_score": 96, "access_type": "embedded"},
                {"name": "consensus_ai", "quality_score": 95, "access_type": "embedded"},
                {"name": "jenni_ai", "quality_score": 94, "access_type": "embedded"},
                {"name": "elicit_ai", "quality_score": 93, "access_type": "embedded"},
                {"name": "scispace", "quality_score": 92, "access_type": "embedded"},
                {"name": "semantic_scholar", "quality_score": 90, "access_type": "api"}
            ],
            "research_reports": [
                {"name": "perplexity_pro", "quality_score": 94, "access_type": "api"},
                {"name": "you_research", "quality_score": 91, "access_type": "embedded"},
                {"name": "tavily_research", "quality_score": 89, "access_type": "api"}
            ],
            "business_reports": [
                {"name": "pitchbook_ai", "quality_score": 96, "access_type": "embedded"},
                {"name": "cb_insights", "quality_score": 95, "access_type": "embedded"},
                {"name": "analyst_ai", "quality_score": 94, "access_type": "embedded"}
            ],
            "marketing_campaigns": [
                {"name": "persado", "quality_score": 95, "access_type": "embedded"},
                {"name": "jasper_ai", "quality_score": 92, "access_type": "api"},
                {"name": "copy_ai", "quality_score": 89, "access_type": "embedded"}
            ]
        }

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def test_service_output(self, service_name: str, category: str, prompt: str, 
                                 expected_quality_score: int, access_type: str) -> ServiceTestResult:
        """Test a single service with the standardized prompt."""
        logger.info(f"Testing {service_name} ({access_type}) for {category}")
        
        start_time = time.time()
        
        try:
            # Make API call to generate content
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
                    
                    if data.get("success"):
                        content = data.get("content", "")
                        
                        # Analyze the output
                        analysis = self._analyze_output(
                            content, prompt, category, service_name, expected_quality_score
                        )
                        
                        return ServiceTestResult(
                            service_name=service_name,
                            category=category,
                            prompt=prompt,
                            output_content=content,
                            word_count=len(content.split()),
                            response_time=response_time,
                            quality_score=data.get("quality_score", 0),
                            access_type=access_type,
                            is_real_ai=analysis["is_real_ai"],
                            specialization_evident=analysis["specialization_evident"],
                            professional_formatting=analysis["professional_formatting"],
                            contains_expected_keywords=analysis["contains_expected_keywords"],
                            unique_content_hash=hashlib.md5(content.encode()).hexdigest(),
                            timestamp=datetime.now()
                        )
                    else:
                        error_msg = data.get("error", "Unknown error")
                        logger.error(f"Service {service_name} failed: {error_msg}")
                        
                        return ServiceTestResult(
                            service_name=service_name,
                            category=category,
                            prompt=prompt,
                            output_content="",
                            word_count=0,
                            response_time=response_time,
                            quality_score=0,
                            access_type=access_type,
                            is_real_ai=False,
                            specialization_evident=False,
                            professional_formatting=False,
                            contains_expected_keywords=False,
                            unique_content_hash="",
                            timestamp=datetime.now(),
                            error_message=error_msg
                        )
                else:
                    error_msg = f"HTTP {response.status}: {await response.text()}"
                    logger.error(f"HTTP error testing {service_name}: {error_msg}")
                    
                    return ServiceTestResult(
                        service_name=service_name,
                        category=category,
                        prompt=prompt,
                        output_content="",
                        word_count=0,
                        response_time=response_time,
                        quality_score=0,
                        access_type=access_type,
                        is_real_ai=False,
                        specialization_evident=False,
                        professional_formatting=False,
                        contains_expected_keywords=False,
                        unique_content_hash="",
                        timestamp=datetime.now(),
                        error_message=error_msg
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"Exception testing {service_name}: {error_msg}")
            
            return ServiceTestResult(
                service_name=service_name,
                category=category,
                prompt=prompt,
                output_content="",
                word_count=0,
                response_time=response_time,
                quality_score=0,
                access_type=access_type,
                is_real_ai=False,
                specialization_evident=False,
                professional_formatting=False,
                contains_expected_keywords=False,
                unique_content_hash="",
                timestamp=datetime.now(),
                error_message=error_msg
            )

    def _analyze_output(self, content: str, prompt: str, category: str, 
                       service_name: str, expected_quality_score: int) -> Dict[str, bool]:
        """Analyze output to determine if it's real AI vs template/mock content."""
        
        content_lower = content.lower()
        prompt_lower = prompt.lower()
        
        # Get expected keywords for this category
        test_prompt = self.test_prompts[category]
        expected_keywords = test_prompt.expected_keywords
        quality_indicators = test_prompt.quality_indicators
        
        # Check for template/mock indicators
        template_indicators = [
            "enhanced mock content",
            "template content",
            "demo content",
            "placeholder",
            "example content",
            "mock",
            "template",
            "generated by airdocs",
            "note: this is enhanced mock content"
        ]
        
        # Check for real AI indicators
        real_ai_indicators = [
            "real_api: true",
            "model_used:",
            "api_available: true",
            "generated with"
        ]
        
        # Analysis
        is_template = any(indicator in content_lower for indicator in template_indicators)
        has_real_ai_indicators = any(indicator in content_lower for indicator in real_ai_indicators)
        
        # Check keyword coverage
        keyword_matches = sum(1 for keyword in expected_keywords if keyword.lower() in content_lower)
        keyword_coverage = keyword_matches / len(expected_keywords)
        
        # Check quality indicators
        quality_matches = sum(1 for indicator in quality_indicators if indicator.lower() in content_lower)
        quality_coverage = quality_matches / len(quality_indicators)
        
        # Check professional formatting
        professional_formatting = any([
            "##" in content,  # Headers
            "**" in content,  # Bold text
            "•" in content or "-" in content,  # Bullet points
            len(content.split('\n')) > 10,  # Multiple sections
            ":" in content  # Structured content
        ])
        
        # Check for service specialization
        service_specializations = {
            "genspark": ["executive", "strategic", "business"],
            "manus": ["business", "financial", "investor"],
            "gamma_app": ["design", "visual", "interactive"],
            "paperpal": ["academic", "research", "citation"],
            "jenni_ai": ["academic", "writing", "research"],
            "perplexity_pro": ["research", "analysis", "comprehensive"],
            "jasper_ai": ["marketing", "campaign", "conversion"],
            "semantic_scholar": ["academic", "papers", "citations"]
        }
        
        specialization_keywords = service_specializations.get(service_name, [])
        specialization_evident = any(
            spec.lower() in content_lower for spec in specialization_keywords
        ) if specialization_keywords else True
        
        return {
            "is_real_ai": not is_template and (has_real_ai_indicators or keyword_coverage > 0.6),
            "specialization_evident": specialization_evident,
            "professional_formatting": professional_formatting,
            "contains_expected_keywords": keyword_coverage > 0.5,
            "keyword_coverage": keyword_coverage,
            "quality_coverage": quality_coverage
        }

    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run comprehensive tests across all services and categories."""
        logger.info("🧪 Starting comprehensive dual-architecture testing...")
        
        all_results = []
        
        # Test each category
        for category, test_prompt in self.test_prompts.items():
            logger.info(f"\n📋 Testing category: {category.upper()}")
            logger.info(f"Prompt: {test_prompt.prompt[:100]}...")
            
            category_services = self.services_to_test[category]
            
            # Test each service in the category
            for service_config in category_services:
                result = await self.test_service_output(
                    service_name=service_config["name"],
                    category=category,
                    prompt=test_prompt.prompt,
                    expected_quality_score=service_config["quality_score"],
                    access_type=service_config["access_type"]
                )
                
                all_results.append(result)
                self.test_results.append(result)
                
                # Brief result summary
                status = "✅ PASS" if result.is_real_ai else "❌ TEMPLATE"
                logger.info(f"  {result.service_name}: {status} ({result.word_count} words, {result.response_time:.2f}s)")
        
        # Generate comprehensive analysis
        analysis = self._generate_test_analysis(all_results)
        
        return {
            "test_results": all_results,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

    def _generate_test_analysis(self, results: List[ServiceTestResult]) -> Dict[str, Any]:
        """Generate comprehensive analysis of test results."""
        
        total_services = len(results)
        successful_tests = len([r for r in results if r.error_message is None])
        real_ai_services = len([r for r in results if r.is_real_ai])
        template_services = total_services - real_ai_services
        
        # Category analysis
        category_analysis = {}
        for category in self.test_prompts.keys():
            category_results = [r for r in results if r.category == category]
            category_analysis[category] = {
                "total_services": len(category_results),
                "real_ai_count": len([r for r in category_results if r.is_real_ai]),
                "template_count": len([r for r in category_results if not r.is_real_ai]),
                "avg_word_count": sum(r.word_count for r in category_results) / len(category_results) if category_results else 0,
                "avg_response_time": sum(r.response_time for r in category_results) / len(category_results) if category_results else 0,
                "services": [
                    {
                        "name": r.service_name,
                        "quality_score": r.quality_score,
                        "is_real_ai": r.is_real_ai,
                        "word_count": r.word_count,
                        "access_type": r.access_type
                    }
                    for r in category_results
                ]
            }
        
        # Quality correlation analysis
        quality_correlation = self._analyze_quality_correlation(results)
        
        # Uniqueness analysis
        uniqueness_analysis = self._analyze_content_uniqueness(results)
        
        return {
            "overall_stats": {
                "total_services_tested": total_services,
                "successful_tests": successful_tests,
                "real_ai_services": real_ai_services,
                "template_services": template_services,
                "real_ai_percentage": (real_ai_services / total_services * 100) if total_services > 0 else 0
            },
            "category_analysis": category_analysis,
            "quality_correlation": quality_correlation,
            "uniqueness_analysis": uniqueness_analysis
        }

    def _analyze_quality_correlation(self, results: List[ServiceTestResult]) -> Dict[str, Any]:
        """Analyze correlation between claimed quality scores and actual output quality."""
        
        # Group by quality tiers
        premium_services = [r for r in results if r.quality_score >= 95]
        high_quality_services = [r for r in results if 90 <= r.quality_score < 95]
        standard_services = [r for r in results if r.quality_score < 90]
        
        return {
            "premium_tier_95_plus": {
                "count": len(premium_services),
                "real_ai_percentage": len([r for r in premium_services if r.is_real_ai]) / len(premium_services) * 100 if premium_services else 0,
                "avg_word_count": sum(r.word_count for r in premium_services) / len(premium_services) if premium_services else 0
            },
            "high_quality_90_94": {
                "count": len(high_quality_services),
                "real_ai_percentage": len([r for r in high_quality_services if r.is_real_ai]) / len(high_quality_services) * 100 if high_quality_services else 0,
                "avg_word_count": sum(r.word_count for r in high_quality_services) / len(high_quality_services) if high_quality_services else 0
            },
            "standard_85_89": {
                "count": len(standard_services),
                "real_ai_percentage": len([r for r in standard_services if r.is_real_ai]) / len(standard_services) * 100 if standard_services else 0,
                "avg_word_count": sum(r.word_count for r in standard_services) / len(standard_services) if standard_services else 0
            }
        }

    def _analyze_content_uniqueness(self, results: List[ServiceTestResult]) -> Dict[str, Any]:
        """Analyze content uniqueness across services."""
        
        # Group by category
        uniqueness_by_category = {}
        
        for category in self.test_prompts.keys():
            category_results = [r for r in results if r.category == category]
            content_hashes = [r.unique_content_hash for r in category_results if r.unique_content_hash]
            
            unique_hashes = set(content_hashes)
            
            uniqueness_by_category[category] = {
                "total_outputs": len(category_results),
                "unique_outputs": len(unique_hashes),
                "uniqueness_percentage": len(unique_hashes) / len(category_results) * 100 if category_results else 0,
                "duplicate_content_detected": len(content_hashes) != len(unique_hashes)
            }
        
        return uniqueness_by_category

    def generate_html_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive HTML test report."""

        analysis = results["analysis"]
        test_results = results["test_results"]

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AIRDOCS Dual-Architecture Test Report</title>
    <style>
        body {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; margin: 0; padding: 2rem; background: #f8fafc; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ text-align: center; margin-bottom: 3rem; }}
        .title {{ font-size: 2.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem; }}
        .subtitle {{ font-size: 1.2rem; color: #64748b; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 3rem; }}
        .summary-card {{ background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .summary-title {{ font-weight: 600; color: #374151; margin-bottom: 0.5rem; }}
        .summary-value {{ font-size: 2rem; font-weight: 700; color: #667eea; }}
        .summary-label {{ font-size: 0.9rem; color: #6b7280; }}
        .category-section {{ background: white; border-radius: 12px; padding: 2rem; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }}
        .category-title {{ font-size: 1.5rem; font-weight: 600; color: #1e293b; margin-bottom: 1.5rem; }}
        .service-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem; }}
        .service-card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; }}
        .service-card.real-ai {{ border-left: 4px solid #10b981; }}
        .service-card.template {{ border-left: 4px solid #ef4444; }}
        .service-name {{ font-weight: 600; color: #374151; }}
        .service-meta {{ font-size: 0.9rem; color: #6b7280; margin-top: 0.5rem; }}
        .status-badge {{ padding: 0.25rem 0.75rem; border-radius: 12px; font-size: 0.8rem; font-weight: 500; }}
        .status-real {{ background: #dcfce7; color: #166534; }}
        .status-template {{ background: #fee2e2; color: #991b1b; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
        .comparison-table th, .comparison-table td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #e5e7eb; }}
        .comparison-table th {{ background: #f8fafc; font-weight: 600; }}
        .output-preview {{ max-height: 200px; overflow-y: auto; background: #f8fafc; padding: 1rem; border-radius: 8px; font-size: 0.9rem; margin-top: 1rem; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title">🧪 AIRDOCS Dual-Architecture Test Report</div>
            <div class="subtitle">Comprehensive validation of 20+ AI services across both architectures</div>
            <div class="subtitle">Generated: {results["timestamp"]}</div>
        </div>

        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-title">Total Services Tested</div>
                <div class="summary-value">{analysis["overall_stats"]["total_services_tested"]}</div>
                <div class="summary-label">Across 5 content categories</div>
            </div>
            <div class="summary-card">
                <div class="summary-title">Real AI Integration</div>
                <div class="summary-value">{analysis["overall_stats"]["real_ai_services"]}</div>
                <div class="summary-label">{analysis["overall_stats"]["real_ai_percentage"]:.1f}% genuine AI services</div>
            </div>
            <div class="summary-card">
                <div class="summary-title">Template/Mock Content</div>
                <div class="summary-value">{analysis["overall_stats"]["template_services"]}</div>
                <div class="summary-label">Services using template content</div>
            </div>
            <div class="summary-card">
                <div class="summary-title">Test Success Rate</div>
                <div class="summary-value">{(analysis["overall_stats"]["successful_tests"] / analysis["overall_stats"]["total_services_tested"] * 100):.1f}%</div>
                <div class="summary-label">Tests completed successfully</div>
            </div>
        </div>
"""

        # Add category sections
        for category, category_data in analysis["category_analysis"].items():
            category_results = [r for r in test_results if r.category == category]

            html_content += f"""
        <div class="category-section">
            <div class="category-title">📋 {category.replace('_', ' ').title()}</div>
            <div class="service-grid">
"""

            for service_result in category_results:
                status_class = "real-ai" if service_result.is_real_ai else "template"
                status_text = "Real AI" if service_result.is_real_ai else "Template"
                status_badge_class = "status-real" if service_result.is_real_ai else "status-template"

                html_content += f"""
                <div class="service-card {status_class}">
                    <div class="service-name">{service_result.service_name.replace('_', ' ').title()}</div>
                    <div class="service-meta">
                        <span class="status-badge {status_badge_class}">{status_text}</span>
                        Quality: {service_result.quality_score}/100 |
                        Words: {service_result.word_count} |
                        Time: {service_result.response_time:.2f}s |
                        Type: {service_result.access_type.upper()}
                    </div>
                    <div class="output-preview">
                        {service_result.output_content[:500]}{'...' if len(service_result.output_content) > 500 else ''}
                    </div>
                </div>
"""

            html_content += """
            </div>
        </div>
"""

        # Add quality correlation analysis
        quality_corr = analysis["quality_correlation"]
        html_content += f"""
        <div class="category-section">
            <div class="category-title">📊 Quality Score Correlation Analysis</div>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Quality Tier</th>
                        <th>Service Count</th>
                        <th>Real AI %</th>
                        <th>Avg Word Count</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Premium (95-100)</td>
                        <td>{quality_corr["premium_tier_95_plus"]["count"]}</td>
                        <td>{quality_corr["premium_tier_95_plus"]["real_ai_percentage"]:.1f}%</td>
                        <td>{quality_corr["premium_tier_95_plus"]["avg_word_count"]:.0f}</td>
                    </tr>
                    <tr>
                        <td>High Quality (90-94)</td>
                        <td>{quality_corr["high_quality_90_94"]["count"]}</td>
                        <td>{quality_corr["high_quality_90_94"]["real_ai_percentage"]:.1f}%</td>
                        <td>{quality_corr["high_quality_90_94"]["avg_word_count"]:.0f}</td>
                    </tr>
                    <tr>
                        <td>Standard (85-89)</td>
                        <td>{quality_corr["standard_85_89"]["count"]}</td>
                        <td>{quality_corr["standard_85_89"]["real_ai_percentage"]:.1f}%</td>
                        <td>{quality_corr["standard_85_89"]["avg_word_count"]:.0f}</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div class="category-section">
            <div class="category-title">🔍 Content Uniqueness Analysis</div>
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Category</th>
                        <th>Total Outputs</th>
                        <th>Unique Outputs</th>
                        <th>Uniqueness %</th>
                        <th>Duplicate Content</th>
                    </tr>
                </thead>
                <tbody>
"""

        for category, uniqueness_data in analysis["uniqueness_analysis"].items():
            html_content += f"""
                    <tr>
                        <td>{category.replace('_', ' ').title()}</td>
                        <td>{uniqueness_data["total_outputs"]}</td>
                        <td>{uniqueness_data["unique_outputs"]}</td>
                        <td>{uniqueness_data["uniqueness_percentage"]:.1f}%</td>
                        <td>{'Yes' if uniqueness_data["duplicate_content_detected"] else 'No'}</td>
                    </tr>
"""

        html_content += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

        return html_content

async def main():
    """Run the comprehensive testing framework."""
    
    async with DualArchitectureTestFramework() as test_framework:
        # Run comprehensive tests
        results = await test_framework.run_comprehensive_tests()
        
        # Save results to files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"test_results_{timestamp}.json"
        report_file = f"test_report_{timestamp}.html"

        # Save JSON results
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Generate and save HTML report
        html_report = test_framework.generate_html_report(results)
        with open(report_file, 'w') as f:
            f.write(html_report)

        logger.info(f"\n📊 Test results saved to: {results_file}")
        logger.info(f"📄 HTML report saved to: {report_file}")

        # Print summary
        analysis = results["analysis"]
        overall = analysis["overall_stats"]

        print(f"\n🧪 AIRDOCS DUAL-ARCHITECTURE TEST RESULTS")
        print(f"=" * 50)
        print(f"Total Services Tested: {overall['total_services_tested']}")
        print(f"Real AI Services: {overall['real_ai_services']} ({overall['real_ai_percentage']:.1f}%)")
        print(f"Template Services: {overall['template_services']}")
        print(f"Successful Tests: {overall['successful_tests']}")

        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category, data in analysis["category_analysis"].items():
            print(f"  {category.upper()}: {data['real_ai_count']}/{data['total_services']} real AI services")

        print(f"\n🎯 QUALITY CORRELATION:")
        quality_corr = analysis["quality_correlation"]
        print(f"  Premium (95-100): {quality_corr['premium_tier_95_plus']['real_ai_percentage']:.1f}% real AI")
        print(f"  High Quality (90-94): {quality_corr['high_quality_90_94']['real_ai_percentage']:.1f}% real AI")
        print(f"  Standard (85-89): {quality_corr['standard_85_89']['real_ai_percentage']:.1f}% real AI")

        print(f"\n🔍 CONTENT UNIQUENESS:")
        for category, uniqueness_data in analysis["uniqueness_analysis"].items():
            print(f"  {category.upper()}: {uniqueness_data['uniqueness_percentage']:.1f}% unique content")

        print(f"\n📄 View detailed report: {report_file}")

        return results

if __name__ == "__main__":
    asyncio.run(main())
