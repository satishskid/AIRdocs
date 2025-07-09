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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Depends, Form, File, UploadFile, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import scientific model discovery
from model_discovery import model_discovery_service

# Initialize FastAPI app
app = FastAPI(
    title="GreyBrain Bank",
    description="Advanced AI Model Aggregation Platform - 88+ AI models for intelligent content generation. Made by GreyBrain.ai",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
models_data: Dict[str, Any] = {}
prompts_data: List[Dict[str, Any]] = []
last_models_update = 0
last_prompts_update = 0

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
MODELS_DIR = Path("../models")
PROMPTS_DIR = Path("../prompts")
FRONTEND_DIR = Path("../frontend")

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
    """Simulate AI content generation. Replace with actual AI API calls."""

    # Quality-based content variations
    quality_indicators = {
        1: "This is a fast-generated response with essential information.",
        2: "This is a balanced response with good detail and structure.",
        3: "This is a high-quality response with comprehensive analysis and insights."
    }

    # Simulate different response lengths based on quality
    base_content = f"""
# Professional Content Generated

{quality_indicators[quality_level]}

## Executive Summary

Based on your requirements, this document provides a comprehensive analysis and recommendations. The content has been structured to meet professional standards and business requirements.

## Key Findings

1. **Strategic Insights**: The analysis reveals important trends and opportunities that align with your objectives.

2. **Recommendations**: Based on the data and context provided, we recommend a multi-faceted approach that addresses both immediate needs and long-term goals.

3. **Implementation Plan**: A structured approach to implementation will ensure successful outcomes and measurable results.

## Detailed Analysis

The comprehensive review of your requirements indicates several key areas for focus:

- **Market Positioning**: Understanding your competitive landscape and unique value proposition
- **Operational Excellence**: Streamlining processes for maximum efficiency
- **Growth Opportunities**: Identifying and capitalizing on emerging trends
- **Risk Management**: Proactive identification and mitigation of potential challenges

## Conclusion

This analysis provides a solid foundation for decision-making and strategic planning. The recommendations are designed to deliver measurable value and support your business objectives.

## Next Steps

1. Review the recommendations with key stakeholders
2. Develop an implementation timeline
3. Establish success metrics and monitoring processes
4. Begin execution with regular progress reviews

---

*This document was generated using advanced AI technology optimized for {model} with quality level {quality_level}.*
"""

    # Add more content for higher quality levels
    if quality_level >= 2:
        base_content += """

## Additional Considerations

### Market Analysis
The current market conditions present both opportunities and challenges. Our analysis suggests that timing and execution will be critical factors in achieving success.

### Resource Requirements
Implementation will require careful resource allocation and stakeholder alignment. Consider the following resource categories:
- Human capital and expertise
- Technology infrastructure
- Financial investment
- Time and project management

### Success Metrics
Key performance indicators should include:
- Quantitative measures of progress
- Qualitative assessments of impact
- Stakeholder satisfaction metrics
- Return on investment calculations
"""

    if quality_level == 3:
        base_content += """

## Advanced Strategic Framework

### Competitive Intelligence
Deep market analysis reveals positioning opportunities that can provide sustainable competitive advantages. The strategic framework should incorporate:

1. **Market Dynamics**: Understanding evolving customer needs and preferences
2. **Technology Trends**: Leveraging emerging technologies for operational advantage
3. **Regulatory Environment**: Ensuring compliance while maximizing opportunities
4. **Partnership Strategies**: Building strategic alliances for mutual benefit

### Risk Assessment Matrix
Comprehensive risk evaluation across multiple dimensions:
- **Operational Risks**: Process, technology, and human resource considerations
- **Market Risks**: Competition, demand fluctuation, and economic factors
- **Financial Risks**: Investment requirements, cash flow, and profitability
- **Strategic Risks**: Long-term positioning and sustainability

### Implementation Roadmap
Detailed phased approach with specific milestones:
- **Phase 1**: Foundation building and initial implementation
- **Phase 2**: Scaling and optimization
- **Phase 3**: Advanced features and market expansion
- **Phase 4**: Continuous improvement and innovation

This comprehensive approach ensures sustainable success and measurable value creation.
"""

    return base_content.strip()

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
    return {"message": "AI Credit Aggregator API", "status": "running"}

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
    """Generate professional content based on ContentPro workflow."""
    try:
        # Validate content category
        if request.content_category not in CONTENT_CATEGORY_CONFIGS:
            raise HTTPException(status_code=400, detail=f"Invalid content category: {request.content_category}")

        # Get optimal model for the request
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
            }
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
async def get_admin_dashboard():
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
async def test_model_health(model_name: str):
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
async def get_model_discovery_info():
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
