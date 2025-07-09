# GreyBrain Bank - AI Model Aggregation Platform

![GreyBrain Bank Logo](frontend/assets/logo.svg)

**Advanced AI Model Aggregation Platform - 88+ AI models for intelligent content generation**

*Made by [GreyBrain.ai](https://greybrain.ai)*

## 🚀 Overview

GreyBrain Bank is a comprehensive AI model aggregation platform that provides access to 88+ AI models across multiple categories including enterprise AI, academic writing tools, research assistants, and specialized AI services. The platform offers intelligent content generation, real-time health monitoring, and scientific model discovery.

## 🎯 Key Features

- **88+ AI Models**: Comprehensive coverage across all major AI providers
- **7 Content Categories**: Reports, Marketing, Presentations, Communications, Documentation, Academic, Research
- **Scientific Model Discovery**: Automated discovery from 7 authoritative sources
- **Real-time Health Monitoring**: Live status tracking for all AI models
- **Academic Writing AI**: Complete integration with Paperpal, Jenni AI, SciSpace, Semantic Scholar, FutureHouse, and more
- **Enterprise-Ready**: Professional admin dashboard with business intelligence
- **Multi-format Output**: PDF, Word, HTML, and more

## 🔬 Supported AI Models

### Enterprise AI (25+ models)
- **OpenAI**: GPT-4, GPT-4-turbo, GPT-4o, GPT-3.5-turbo variants
- **Anthropic**: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Google**: Gemini-ultra, Gemini-pro, Palm-2, Bard
- **Enterprise Platforms**: Azure-OpenAI, AWS-Bedrock, Vertex-AI

### Academic & Research Writing AI (30+ models)
- **Writing Assistants**: Paperpal, Jenni AI, SciSpace, Writefull, Trinka
- **Research Tools**: Semantic Scholar, Elicit, Consensus, FutureHouse
- **Discovery Platforms**: Research Rabbit, Connected Papers, Litmaps
- **Analysis Tools**: Scholarcy, Iris AI, Scite, Zeta Alpha

### Specialized AI Services (15+ models)
- **Search & Research**: Genspark, Perplexity AI, Context AI
- **Code Generation**: Codex, Copilot, Codestral, Code-llama
- **Multimodal**: DALL-E-3, Midjourney, Stable-diffusion, Whisper

### Open Source Models (18+ models)
- **Meta LLaMA**: LLaMA-2 (7B, 13B, 70B), LLaMA-3 (8B, 70B)
- **Mistral AI**: Mistral-7B, Mistral-8x7B, Mistral-large
- **Research Models**: Vicuna, Alpaca, WizardLM, Orca-2, Phi-2

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.8+
- **AI Integration**: 88+ AI model connectors
- **Health Monitoring**: Real-time model status tracking
- **Scientific Discovery**: Automated model discovery system
- **Admin API**: Comprehensive management endpoints

### Frontend (Vanilla JavaScript)
- **Interface**: Modern, responsive web application
- **Admin Dashboard**: Real-time monitoring and analytics
- **Content Generation**: Multi-category content creation
- **File Management**: Upload, download, and format conversion

## 📦 Installation

### Prerequisites
- Python 3.8+
- Node.js 16+ (for development)
- Git

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/satishskid/greybrain-bank.git
cd greybrain-bank
```

2. **Install backend dependencies**
```bash
cd backend
pip install -r requirements.txt
```

3. **Start the backend server**
```bash
python app.py
```

4. **Open the frontend**
```bash
cd ../frontend
# Open index.html in your browser or serve with a local server
python -m http.server 8080
```

5. **Access the application**
- Main Interface: http://localhost:8080
- Admin Dashboard: http://localhost:8080/admin-dashboard.html
- API Documentation: http://localhost:8001/docs

## 🔧 Configuration

### Environment Variables
```bash
# API Configuration
API_HOST=localhost
API_PORT=8001
DEBUG=true

# AI Model Configuration
MODEL_DISCOVERY_INTERVAL=300  # 5 minutes
HEALTH_CHECK_INTERVAL=60      # 1 minute

# Security
ADMIN_API_KEY=your_admin_key_here
CORS_ORIGINS=http://localhost:8080
```

### Model Configuration
The platform automatically discovers and configures AI models from multiple sources:
- LMSYS Chatbot Arena Leaderboard
- Enterprise AI Providers
- HuggingFace Trending Models
- Academic & Research Writing AI
- Specialized AI Services
- Open Source AI Models

## 📚 API Documentation

### Content Generation
```bash
POST /generate-content
{
  "search_query": "Create a research paper on AI",
  "document_title": "AI Research Paper",
  "content_category": "academic",
  "template_id": "research-paper",
  "quality_level": 3,
  "output_formats": ["pdf", "word"]
}
```

### Model Health Check
```bash
POST /admin/models/{model_name}/test
GET /admin/dashboard
GET /admin/models/discovery
```

### Content Categories
```bash
GET /content-categories
GET /templates/{category}
```

## 🎓 Academic AI Integration

GreyBrain Bank provides comprehensive integration with academic writing AI tools:

### Research Writing
- **Paperpal**: Academic writing enhancement
- **Jenni AI**: AI-powered academic writing
- **SciSpace**: Research assistant and literature review

### Research Discovery
- **Semantic Scholar**: Academic search and discovery
- **Elicit**: Research question answering
- **Consensus**: Evidence-based research
- **FutureHouse**: Research automation platform

### Citation and Analysis
- **Research Rabbit**: Literature discovery
- **Connected Papers**: Citation network analysis
- **Scite**: Citation context analysis
- **Scholarcy**: Paper summarization

## 🔍 Admin Dashboard

The admin dashboard provides comprehensive monitoring and management:

- **System Overview**: Health status, uptime, model count
- **Model Performance**: Success rates, response times, revenue
- **Discovery Analytics**: Model discovery from scientific sources
- **Business Intelligence**: Usage metrics, revenue tracking
- **Health Monitoring**: Real-time status of all 88+ models

## 🚀 Deployment

### Recommended Platforms

#### Backend Deployment
- **Railway**: Easy FastAPI deployment
- **Heroku**: Simple Python app hosting
- **DigitalOcean App Platform**: Scalable container deployment
- **AWS Elastic Beanstalk**: Enterprise-grade hosting
- **Google Cloud Run**: Serverless container deployment

#### Frontend Deployment
- **Vercel**: Optimal for static sites with API integration
- **Netlify**: Simple static site deployment
- **GitHub Pages**: Free hosting for static content
- **AWS S3 + CloudFront**: Enterprise CDN deployment

### Docker Deployment
```dockerfile
# Backend Dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8001
CMD ["python", "app.py"]
```

## 🔒 Security

- **API Authentication**: Admin endpoints protected with API keys
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API quota management
- **Health Monitoring**: Automated security health checks

## 📊 Monitoring & Analytics

- **Real-time Metrics**: Live model performance tracking
- **Business Intelligence**: Revenue and usage analytics
- **Health Dashboards**: System status monitoring
- **Discovery Analytics**: Model discovery insights
- **Performance Optimization**: Automated load balancing

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Full API Documentation](http://localhost:8001/docs)
- **Issues**: [GitHub Issues](https://github.com/satishskid/greybrain-bank/issues)
- **Contact**: support@greybrain.ai

## 🏆 Acknowledgments

- **AI Providers**: OpenAI, Anthropic, Google, Meta, Mistral AI, and all open-source contributors
- **Academic Tools**: Paperpal, Jenni AI, SciSpace, Semantic Scholar, FutureHouse, and research community
- **Scientific Sources**: LMSYS Arena, HuggingFace, academic institutions

---

**Made with ❤️ by [GreyBrain.ai](https://greybrain.ai)**

*Empowering businesses with the world's most comprehensive AI model aggregation platform*
