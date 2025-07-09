"""
Scientific Model Discovery Service for ContentPro
Discovers AI models from leaderboards, repositories, and scientific sources
"""

import requests
import json
from typing import List, Dict, Optional
from datetime import datetime

class ModelDiscoveryService:
    """Scientific discovery service for AI models from various leaderboards and repositories."""
    
    def __init__(self):
        self.discovered_models = {}
        self.leaderboard_sources = {
            "lmsys_chatbot_arena": "https://huggingface.co/spaces/lmsys/chatbot-arena-leaderboard",
            "huggingface_trending": "https://huggingface.co/api/models",
            "openai_models": "https://api.openai.com/v1/models",
            "anthropic_models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
            "google_models": ["gemini-ultra", "gemini-pro", "palm-2"],
            "meta_models": ["llama-2-70b", "llama-2-13b", "llama-2-7b"],
            "mistral_models": ["mistral-large", "mistral-medium", "mistral-7b"]
        }
    
    def discover_huggingface_models(self, limit: int = 50) -> List[Dict]:
        """Discover trending models from Hugging Face."""
        try:
            # Get trending models from HuggingFace API
            response = requests.get(
                "https://huggingface.co/api/models",
                params={
                    "sort": "trending",
                    "limit": limit,
                    "filter": "text-generation"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                models = response.json()
                discovered = []
                
                for model in models:
                    model_info = {
                        "name": model.get("id", "").replace("/", "-"),
                        "full_name": model.get("id", ""),
                        "source": "huggingface",
                        "downloads": model.get("downloads", 0),
                        "likes": model.get("likes", 0),
                        "tags": model.get("tags", []),
                        "pipeline_tag": model.get("pipeline_tag", ""),
                        "library_name": model.get("library_name", ""),
                        "created_at": model.get("createdAt", ""),
                        "updated_at": model.get("lastModified", "")
                    }
                    discovered.append(model_info)
                
                return discovered
                
        except Exception as e:
            print(f"Error discovering HuggingFace models: {e}")
            
        return []
    
    def get_lmsys_arena_models(self) -> List[Dict]:
        """Get models from LMSYS Chatbot Arena leaderboard."""
        # Popular models from LMSYS Arena (manually curated from leaderboard)
        arena_models = [
            {"name": "gpt-4-turbo", "elo_rating": 1251, "source": "lmsys_arena", "provider": "openai"},
            {"name": "claude-3-opus", "elo_rating": 1248, "source": "lmsys_arena", "provider": "anthropic"},
            {"name": "gpt-4", "elo_rating": 1169, "source": "lmsys_arena", "provider": "openai"},
            {"name": "claude-3-sonnet", "elo_rating": 1187, "source": "lmsys_arena", "provider": "anthropic"},
            {"name": "gemini-pro", "elo_rating": 1111, "source": "lmsys_arena", "provider": "google"},
            {"name": "claude-3-haiku", "elo_rating": 1169, "source": "lmsys_arena", "provider": "anthropic"},
            {"name": "gpt-3.5-turbo", "elo_rating": 1105, "source": "lmsys_arena", "provider": "openai"},
            {"name": "llama-2-70b-chat", "elo_rating": 1076, "source": "lmsys_arena", "provider": "meta"},
            {"name": "mixtral-8x7b", "elo_rating": 1114, "source": "lmsys_arena", "provider": "mistral"},
            {"name": "yi-34b-chat", "elo_rating": 1102, "source": "lmsys_arena", "provider": "01-ai"},
            {"name": "solar-10.7b", "elo_rating": 1090, "source": "lmsys_arena", "provider": "upstage"},
            {"name": "wizardlm-70b", "elo_rating": 1087, "source": "lmsys_arena", "provider": "microsoft"},
            {"name": "vicuna-33b", "elo_rating": 1083, "source": "lmsys_arena", "provider": "lmsys"},
            {"name": "starling-lm-7b", "elo_rating": 1083, "source": "lmsys_arena", "provider": "berkeley"},
            {"name": "openchat-3.5", "elo_rating": 1077, "source": "lmsys_arena", "provider": "openchat"},
            {"name": "deepseek-llm-67b", "elo_rating": 1076, "source": "lmsys_arena", "provider": "deepseek"},
            {"name": "qwen-72b-chat", "elo_rating": 1075, "source": "lmsys_arena", "provider": "alibaba"},
            {"name": "nous-hermes-2-mixtral", "elo_rating": 1074, "source": "lmsys_arena", "provider": "nous"},
        ]
        return arena_models
    
    def get_enterprise_models(self) -> List[Dict]:
        """Get enterprise and specialized AI models."""
        enterprise_models = [
            # OpenAI Models
            {"name": "gpt-4o", "provider": "openai", "type": "multimodal", "source": "enterprise"},
            {"name": "gpt-4o-mini", "provider": "openai", "type": "efficient", "source": "enterprise"},
            {"name": "gpt-4-turbo-preview", "provider": "openai", "type": "preview", "source": "enterprise"},
            {"name": "gpt-3.5-turbo-16k", "provider": "openai", "type": "extended", "source": "enterprise"},
            
            # Anthropic Models
            {"name": "claude-2.1", "provider": "anthropic", "type": "legacy", "source": "enterprise"},
            {"name": "claude-instant", "provider": "anthropic", "type": "fast", "source": "enterprise"},
            
            # Google Models
            {"name": "gemini-ultra", "provider": "google", "type": "flagship", "source": "enterprise"},
            {"name": "gemini-pro-vision", "provider": "google", "type": "multimodal", "source": "enterprise"},
            {"name": "palm-2", "provider": "google", "type": "legacy", "source": "enterprise"},
            {"name": "bard", "provider": "google", "type": "conversational", "source": "enterprise"},
            
            # Specialized Models
            {"name": "genspark", "provider": "genspark", "type": "search", "source": "specialized"},
            {"name": "perplexity-ai", "provider": "perplexity", "type": "research", "source": "specialized"},
            {"name": "context-ai", "provider": "context", "type": "context", "source": "specialized"},
            {"name": "skywork-13b", "provider": "skywork", "type": "multilingual", "source": "specialized"},
            {"name": "you-com", "provider": "you", "type": "search", "source": "specialized"},
            {"name": "phind", "provider": "phind", "type": "code", "source": "specialized"},
            
            # Code Models
            {"name": "codex", "provider": "openai", "type": "code", "source": "specialized"},
            {"name": "copilot", "provider": "github", "type": "code", "source": "specialized"},
            {"name": "codestral", "provider": "mistral", "type": "code", "source": "specialized"},
            {"name": "code-llama", "provider": "meta", "type": "code", "source": "specialized"},
            {"name": "replit-code", "provider": "replit", "type": "code", "source": "specialized"},
            {"name": "tabnine", "provider": "tabnine", "type": "code", "source": "specialized"},
            
            # Multimodal Models
            {"name": "dall-e-3", "provider": "openai", "type": "image", "source": "specialized"},
            {"name": "midjourney", "provider": "midjourney", "type": "image", "source": "specialized"},
            {"name": "stable-diffusion", "provider": "stability", "type": "image", "source": "specialized"},
            {"name": "whisper", "provider": "openai", "type": "audio", "source": "specialized"},
            
            # Open Source Leaders
            {"name": "llama-3-70b", "provider": "meta", "type": "open_source", "source": "open_source"},
            {"name": "mistral-8x22b", "provider": "mistral", "type": "open_source", "source": "open_source"},
            {"name": "falcon-180b", "provider": "tii", "type": "open_source", "source": "open_source"},
            {"name": "phi-3-medium", "provider": "microsoft", "type": "open_source", "source": "open_source"},
        ]
        return enterprise_models
    
    def get_academic_writing_models(self) -> List[Dict]:
        """Get academic and research writing AI tools."""
        academic_models = [
            # Academic Writing Assistants
            {"name": "paperpal", "provider": "paperpal", "type": "academic_writing", "source": "academic"},
            {"name": "jenni-ai", "provider": "jenni", "type": "academic_writing", "source": "academic"},
            {"name": "scispace", "provider": "scispace", "type": "research_assistant", "source": "academic"},
            {"name": "semantic-scholar", "provider": "allen-institute", "type": "research_search", "source": "academic"},
            {"name": "futurehouse", "provider": "futurehouse", "type": "research_automation", "source": "academic"},

            # Research & Citation Tools
            {"name": "elicit", "provider": "elicit", "type": "research_assistant", "source": "academic"},
            {"name": "consensus", "provider": "consensus", "type": "research_search", "source": "academic"},
            {"name": "research-rabbit", "provider": "research-rabbit", "type": "literature_discovery", "source": "academic"},
            {"name": "connected-papers", "provider": "connected-papers", "type": "citation_network", "source": "academic"},
            {"name": "inciteful", "provider": "inciteful", "type": "citation_analysis", "source": "academic"},

            # Academic Writing Enhancement
            {"name": "writefull", "provider": "writefull", "type": "academic_writing", "source": "academic"},
            {"name": "trinka", "provider": "trinka", "type": "academic_editing", "source": "academic"},
            {"name": "wordtune", "provider": "wordtune", "type": "writing_enhancement", "source": "academic"},
            {"name": "quillbot", "provider": "quillbot", "type": "paraphrasing", "source": "academic"},
            {"name": "ref-n-write", "provider": "ref-n-write", "type": "academic_writing", "source": "academic"},

            # Research Data & Analysis
            {"name": "scholarcy", "provider": "scholarcy", "type": "paper_summarization", "source": "academic"},
            {"name": "iris-ai", "provider": "iris", "type": "research_assistant", "source": "academic"},
            {"name": "scite", "provider": "scite", "type": "citation_context", "source": "academic"},
            {"name": "typeset", "provider": "typeset", "type": "manuscript_formatting", "source": "academic"},
            {"name": "researcher", "provider": "researcher", "type": "research_automation", "source": "academic"},

            # Specialized Academic AI
            {"name": "litmaps", "provider": "litmaps", "type": "literature_mapping", "source": "academic"},
            {"name": "zeta-alpha", "provider": "zeta-alpha", "type": "research_discovery", "source": "academic"},
            {"name": "ought", "provider": "ought", "type": "research_reasoning", "source": "academic"},
            {"name": "metaphor", "provider": "metaphor", "type": "research_search", "source": "academic"},
            {"name": "perplexity-pages", "provider": "perplexity", "type": "research_compilation", "source": "academic"},

            # Academic Collaboration
            {"name": "notion-ai", "provider": "notion", "type": "research_organization", "source": "academic"},
            {"name": "obsidian-ai", "provider": "obsidian", "type": "knowledge_management", "source": "academic"},
            {"name": "roam-research", "provider": "roam", "type": "knowledge_graph", "source": "academic"},
            {"name": "logseq", "provider": "logseq", "type": "knowledge_management", "source": "academic"},
            {"name": "remnote", "provider": "remnote", "type": "spaced_repetition", "source": "academic"},
        ]
        return academic_models

    def get_research_models(self) -> List[Dict]:
        """Get cutting-edge research models."""
        research_models = [
            # Research Labs
            {"name": "gpt-5-preview", "provider": "openai", "type": "research", "source": "research"},
            {"name": "claude-4-preview", "provider": "anthropic", "type": "research", "source": "research"},
            {"name": "gemini-2-ultra", "provider": "google", "type": "research", "source": "research"},

            # Academic Models
            {"name": "alpaca-65b", "provider": "stanford", "type": "academic", "source": "research"},
            {"name": "vicuna-13b", "provider": "uc-berkeley", "type": "academic", "source": "research"},
            {"name": "koala-13b", "provider": "berkeley", "type": "academic", "source": "research"},

            # Specialized Research
            {"name": "toolformer", "provider": "meta", "type": "tool_use", "source": "research"},
            {"name": "react-llm", "provider": "princeton", "type": "reasoning", "source": "research"},
            {"name": "chain-of-thought", "provider": "google", "type": "reasoning", "source": "research"},
        ]
        return research_models
    
    def discover_all_models(self) -> Dict[str, Dict]:
        """Comprehensive model discovery from all sources."""
        all_models = {}
        
        print("🔍 Discovering AI models from scientific sources...")
        
        # Get models from LMSYS Arena
        arena_models = self.get_lmsys_arena_models()
        for model in arena_models:
            all_models[model["name"]] = model
        print(f"   📊 LMSYS Arena: {len(arena_models)} models")
        
        # Get enterprise models
        enterprise_models = self.get_enterprise_models()
        for model in enterprise_models:
            all_models[model["name"]] = model
        print(f"   🏢 Enterprise: {len(enterprise_models)} models")
        
        # Get academic writing models
        academic_models = self.get_academic_writing_models()
        for model in academic_models:
            all_models[model["name"]] = model
        print(f"   📚 Academic Writing: {len(academic_models)} models")

        # Get research models
        research_models = self.get_research_models()
        for model in research_models:
            all_models[model["name"]] = model
        print(f"   🔬 Research: {len(research_models)} models")
        
        # Try to get HuggingFace models (with fallback)
        try:
            hf_models = self.discover_huggingface_models(30)
            hf_count = 0
            for model in hf_models:
                if model["name"] not in all_models:
                    all_models[model["name"]] = model
                    hf_count += 1
            print(f"   🤗 HuggingFace: {hf_count} models")
        except Exception as e:
            print(f"   ⚠️ HuggingFace discovery failed: {e}")
        
        self.discovered_models = all_models
        print(f"✅ Total discovered: {len(all_models)} AI models")
        return all_models
    
    def get_model_metadata(self, model_name: str) -> Dict:
        """Get detailed metadata for a specific model."""
        if model_name in self.discovered_models:
            return self.discovered_models[model_name]
        return {"name": model_name, "source": "unknown"}
    
    def get_models_by_provider(self, provider: str) -> List[Dict]:
        """Get all models from a specific provider."""
        return [model for model in self.discovered_models.values() 
                if model.get("provider") == provider]
    
    def get_top_models_by_rating(self, limit: int = 10) -> List[Dict]:
        """Get top models by ELO rating."""
        rated_models = [model for model in self.discovered_models.values() 
                       if model.get("elo_rating", 0) > 0]
        return sorted(rated_models, key=lambda x: x.get("elo_rating", 0), reverse=True)[:limit]

# Global instance
model_discovery_service = ModelDiscoveryService()
