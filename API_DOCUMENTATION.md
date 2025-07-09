# GreyBrain Bank API Documentation

## 🚀 Overview

The GreyBrain Bank API provides access to 88+ AI models for intelligent content generation across 7 categories. This RESTful API supports real-time health monitoring, scientific model discovery, and comprehensive admin management.

**Base URL**: `http://localhost:8001` (development) | `https://your-domain.com` (production)

## 🔐 Authentication

### Admin Endpoints
Admin endpoints require Bearer token authentication:

```bash
Authorization: Bearer greybrain-admin-key-2024
```

### Rate Limiting
- **General API**: 100 requests per minute per IP
- **Admin API**: 5 requests per minute per IP

## 📚 API Endpoints

### 🏠 **Core Endpoints**

#### GET `/`
Serves the frontend application or returns basic API information.

**Response:**
```json
{
  "message": "GreyBrain Bank AI Aggregation Platform",
  "status": "running"
}
```

#### GET `/health`
Comprehensive health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-07-09T19:15:00.000Z",
  "version": "1.0.0",
  "uptime": "2h 30m 45s",
  "system": {
    "cpu_percent": 15.2,
    "memory_percent": 45.8,
    "disk_percent": 23.1,
    "available_memory_gb": 8.5,
    "free_disk_gb": 120.3
  },
  "models": {
    "total": 88,
    "healthy": 75,
    "health_percentage": 85.2
  },
  "services": {
    "model_discovery": "healthy",
    "api": "healthy",
    "logging": "healthy"
  }
}
```

### 🤖 **AI Models**

#### GET `/models`
Get all available AI models with their capabilities and status.

**Response:**
```json
{
  "models": [
    {
      "name": "gpt-4",
      "provider": "openai",
      "type": "language_model",
      "capabilities": ["text_generation", "analysis"],
      "status": "healthy",
      "credits_remaining": 1000,
      "last_health_check": "2024-07-09T19:10:00.000Z"
    }
  ],
  "total_models": 88,
  "healthy_models": 75
}
```

#### GET `/models/{model_name}`
Get detailed information about a specific model.

**Parameters:**
- `model_name` (path): Name of the AI model

**Response:**
```json
{
  "name": "gpt-4",
  "provider": "openai",
  "type": "language_model",
  "capabilities": ["text_generation", "analysis"],
  "status": "healthy",
  "performance": {
    "total_requests": 1250,
    "success_rate": 98.4,
    "avg_response_time": 1.2,
    "last_24h_requests": 45
  },
  "metadata": {
    "max_tokens": 8192,
    "cost_per_request": 0.03,
    "supported_formats": ["text", "json"]
  }
}
```

### 📝 **Content Generation**

#### POST `/generate-content`
Generate content using AI models across different categories.

**Request Body:**
```json
{
  "search_query": "Create a research paper on AI ethics",
  "document_title": "AI Ethics Research Paper",
  "additional_context": "Focus on bias and fairness in AI systems",
  "content_category": "academic",
  "template_id": "research-paper",
  "quality_level": 3,
  "output_formats": ["pdf", "word"],
  "model_preference": "gpt-4"
}
```

**Response:**
```json
{
  "success": true,
  "content": "# AI Ethics Research Paper\n\n## Abstract\n...",
  "metadata": {
    "document_title": "AI Ethics Research Paper",
    "content_category": "academic",
    "template_id": "research-paper",
    "quality_level": 3,
    "model_used": "gpt-4",
    "estimated_time": 8,
    "output_formats": ["pdf", "word"],
    "timestamp": "2024-07-09T19:15:00.000Z",
    "word_count": 2500,
    "character_count": 15000
  }
}
```

### 📋 **Content Categories**

#### GET `/content-categories`
Get all available content categories and their templates.

**Response:**
```json
{
  "categories": {
    "reports": {
      "name": "Business Reports",
      "description": "Professional business reports and analysis",
      "templates": ["quarterly-sales", "market-analysis", "financial-report"],
      "quality_models": {
        "1": ["gpt-3.5-turbo"],
        "2": ["gpt-4"],
        "3": ["gpt-4", "claude-3-opus"]
      }
    },
    "academic": {
      "name": "Academic Writing",
      "description": "Research papers and academic content",
      "templates": ["research-paper", "literature-review", "thesis"],
      "quality_models": {
        "1": ["paperpal"],
        "2": ["jenni-ai", "scispace"],
        "3": ["futurehouse", "semantic-scholar"]
      }
    }
  }
}
```

#### GET `/templates/{category}`
Get templates for a specific content category.

**Parameters:**
- `category` (path): Content category name

**Response:**
```json
{
  "category": "academic",
  "templates": [
    {
      "id": "research-paper",
      "name": "Research Paper",
      "description": "Comprehensive academic research paper",
      "sections": ["abstract", "introduction", "methodology", "results", "conclusion"],
      "estimated_length": "5000-8000 words",
      "recommended_models": ["futurehouse", "semantic-scholar"]
    }
  ]
}
```

### 🔧 **Admin Endpoints** (Authentication Required)

#### GET `/admin/dashboard`
Get comprehensive admin dashboard data.

**Headers:**
```
Authorization: Bearer greybrain-admin-key-2024
```

**Response:**
```json
{
  "system_overview": {
    "status": "healthy",
    "uptime": "99.9%",
    "total_models": 88,
    "healthy_models": 75,
    "system_health_percentage": 85.2,
    "total_requests_24h": 1250,
    "active_users": 45,
    "total_documents": 2340,
    "total_revenue": 1250.75
  },
  "model_performance": {
    "gpt-4": {
      "status": "healthy",
      "total_requests": 450,
      "success_rate": 98.4,
      "avg_response_time": 1.2,
      "credits_consumed": 1350,
      "revenue_generated": 40.5,
      "last_health_check": "2024-07-09T19:10:00.000Z"
    }
  },
  "timestamp": "2024-07-09T19:15:00.000Z"
}
```

#### POST `/admin/models/{model_name}/test`
Manually test a specific model's health.

**Headers:**
```
Authorization: Bearer greybrain-admin-key-2024
```

**Parameters:**
- `model_name` (path): Name of the model to test

**Response:**
```json
{
  "model_name": "gpt-4",
  "test_result": "success",
  "response_time": 1.2,
  "error_message": null,
  "model_source": "openai",
  "model_metadata": {
    "version": "gpt-4-0613",
    "max_tokens": 8192
  },
  "timestamp": "2024-07-09T19:15:00.000Z"
}
```

#### GET `/admin/models/discovery`
Get information about discovered models and their sources.

**Headers:**
```
Authorization: Bearer greybrain-admin-key-2024
```

**Response:**
```json
{
  "discovery_summary": {
    "total_discovered": 88,
    "sources": ["lmsys_arena", "huggingface", "academic", "enterprise"],
    "providers": {
      "openai": 12,
      "anthropic": 8,
      "google": 10,
      "academic_tools": 25
    },
    "discovery_timestamp": "2024-07-09T19:00:00.000Z"
  },
  "models_by_source": {
    "lmsys_arena": [
      {
        "name": "gpt-4",
        "provider": "openai",
        "ranking": 1,
        "elo_score": 1250
      }
    ],
    "academic": [
      {
        "name": "paperpal",
        "provider": "paperpal",
        "type": "academic_writing",
        "specialization": "grammar_enhancement"
      }
    ]
  },
  "top_rated_models": [
    {
      "name": "gpt-4",
      "provider": "openai",
      "score": 95.2,
      "category": "general"
    }
  ]
}
```

## 🔍 **Model Categories**

### Enterprise AI Models (25+)
- **OpenAI**: GPT-4, GPT-4-turbo, GPT-4o, GPT-3.5-turbo variants
- **Anthropic**: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Google**: Gemini-ultra, Gemini-pro, Palm-2, Bard
- **Enterprise**: Azure-OpenAI, AWS-Bedrock, Vertex-AI

### Academic & Research Writing AI (30+)
- **Writing Assistants**: Paperpal, Jenni AI, SciSpace, Writefull, Trinka
- **Research Tools**: Semantic Scholar, Elicit, Consensus, FutureHouse
- **Discovery**: Research Rabbit, Connected Papers, Litmaps
- **Analysis**: Scholarcy, Iris AI, Scite, Zeta Alpha

### Specialized AI Services (15+)
- **Search & Research**: Genspark, Perplexity AI, Context AI
- **Code Generation**: Codex, Copilot, Codestral, Code-llama
- **Multimodal**: DALL-E-3, Midjourney, Stable-diffusion, Whisper

### Open Source Models (18+)
- **Meta LLaMA**: LLaMA-2 (7B, 13B, 70B), LLaMA-3 (8B, 70B)
- **Mistral AI**: Mistral-7B, Mistral-8x7B, Mistral-large
- **Research**: Vicuna, Alpaca, WizardLM, Orca-2, Phi-2

## 📊 **Quality Levels**

### Level 1 (Fast)
- **Speed**: 3-5 seconds
- **Models**: GPT-3.5-turbo, basic academic tools
- **Use Case**: Quick drafts, basic content

### Level 2 (Balanced)
- **Speed**: 5-10 seconds
- **Models**: GPT-4, mid-tier academic tools
- **Use Case**: Professional content, detailed analysis

### Level 3 (Premium)
- **Speed**: 10-15 seconds
- **Models**: GPT-4, Claude-3-opus, FutureHouse, top academic tools
- **Use Case**: High-quality research, comprehensive analysis

## 🚨 **Error Codes**

| Code | Description | Solution |
|------|-------------|----------|
| 400 | Bad Request | Check request format and required fields |
| 401 | Unauthorized | Provide valid admin API key |
| 429 | Rate Limited | Reduce request frequency |
| 500 | Server Error | Check server logs, contact support |
| 503 | Service Unavailable | Model temporarily unavailable |

## 📝 **Usage Examples**

### Generate Academic Content
```bash
curl -X POST http://localhost:8001/generate-content \
  -H "Content-Type: application/json" \
  -d '{
    "search_query": "Machine learning bias detection",
    "document_title": "ML Bias Detection Research",
    "content_category": "academic",
    "template_id": "research-paper",
    "quality_level": 3
  }'
```

### Check System Health
```bash
curl -X GET http://localhost:8001/health
```

### Admin Dashboard Access
```bash
curl -X GET http://localhost:8001/admin/dashboard \
  -H "Authorization: Bearer greybrain-admin-key-2024"
```

### Test Model Health
```bash
curl -X POST http://localhost:8001/admin/models/gpt-4/test \
  -H "Authorization: Bearer greybrain-admin-key-2024"
```

## 🔗 **SDKs and Libraries**

### Python SDK Example
```python
import requests

class GreyBrainClient:
    def __init__(self, base_url="http://localhost:8001", admin_key=None):
        self.base_url = base_url
        self.admin_key = admin_key
    
    def generate_content(self, query, category="reports", quality=2):
        response = requests.post(f"{self.base_url}/generate-content", json={
            "search_query": query,
            "content_category": category,
            "quality_level": quality
        })
        return response.json()
    
    def get_health(self):
        response = requests.get(f"{self.base_url}/health")
        return response.json()

# Usage
client = GreyBrainClient()
result = client.generate_content("Q4 sales analysis", "reports", 3)
```

### JavaScript SDK Example
```javascript
class GreyBrainAPI {
    constructor(baseUrl = 'http://localhost:8001', adminKey = null) {
        this.baseUrl = baseUrl;
        this.adminKey = adminKey;
    }
    
    async generateContent(query, category = 'reports', quality = 2) {
        const response = await fetch(`${this.baseUrl}/generate-content`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                search_query: query,
                content_category: category,
                quality_level: quality
            })
        });
        return response.json();
    }
    
    async getHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.json();
    }
}

// Usage
const api = new GreyBrainAPI();
const result = await api.generateContent('Marketing strategy', 'marketing', 3);
```

## 📞 **Support**

- **Documentation**: [Full API Docs](http://localhost:8001/docs)
- **GitHub**: [Issues & Feature Requests](https://github.com/satishskid/greybrain-bank/issues)
- **Email**: support@greybrain.ai

---

**Made with ❤️ by [GreyBrain.ai](https://greybrain.ai)**
