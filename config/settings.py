"""
Configuration settings for the AI News Agent.
Loads from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import Optional, List

# Load .env file
load_dotenv()


@dataclass
class Settings:
    """Application configuration settings."""
    
    # Email
    recipient_email: str = field(default_factory=lambda: os.getenv('RECIPIENT_EMAIL', ''))
    
    # SMTP Settings (simpler, no API needed)
    smtp_email: Optional[str] = field(default_factory=lambda: os.getenv('SMTP_EMAIL'))
    smtp_password: Optional[str] = field(default_factory=lambda: os.getenv('SMTP_PASSWORD'))
    smtp_provider: str = field(default_factory=lambda: os.getenv('SMTP_PROVIDER', 'gmail'))
    
    # LLM Keys
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv('OPENAI_API_KEY'))
    gemini_api_key: Optional[str] = field(default_factory=lambda: os.getenv('GEMINI_API_KEY'))
    
    # News API
    news_api_key: Optional[str] = field(default_factory=lambda: os.getenv('NEWS_API_KEY'))
    
    # Schedule
    send_time: str = field(default_factory=lambda: os.getenv('SEND_TIME', '08:00'))
    
    # Limits
    max_papers: int = field(default_factory=lambda: int(os.getenv('MAX_PAPERS', '10')))
    max_news: int = field(default_factory=lambda: int(os.getenv('MAX_NEWS', '10')))
    max_discussions: int = field(default_factory=lambda: int(os.getenv('MAX_DISCUSSIONS', '5')))
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent.parent)
    credentials_dir: Path = field(default_factory=lambda: Path(__file__).parent / 'credentials')
    
    # AI Topics to search for
    ai_topics: List[str] = field(default_factory=lambda: [
        'large language model',
        'LLM',
        'AI agent',
        'agentic AI',
        'artificial intelligence',
        'ChatGPT',
        'GPT-4',
        'Claude',
        'Gemini',
        'machine learning',
        'deep learning',
        'transformer',
        'neural network',
        'generative AI',
        'RAG',
        'retrieval augmented generation',
    ])
    
    # ArXiv categories
    arxiv_categories: List[str] = field(default_factory=lambda: [
        'cs.AI',   # Artificial Intelligence
        'cs.CL',   # Computation and Language
        'cs.LG',   # Machine Learning
        'cs.NE',   # Neural and Evolutionary Computing
    ])
    
    # RSS Feeds to monitor
    rss_feeds: List[dict] = field(default_factory=lambda: [
        {'name': 'MIT Tech Review AI', 'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed'},
        {'name': 'The Verge AI', 'url': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml'},
        {'name': 'Ars Technica Tech', 'url': 'https://feeds.arstechnica.com/arstechnica/technology-lab'},
        {'name': 'VentureBeat AI', 'url': 'https://venturebeat.com/category/ai/feed/'},
        {'name': 'Wired AI', 'url': 'https://www.wired.com/feed/tag/ai/latest/rss'},
        {'name': 'TechCrunch AI', 'url': 'https://techcrunch.com/category/artificial-intelligence/feed/'},
    ])
    
    @property
    def has_llm(self) -> bool:
        """Check if any LLM API key is configured."""
        return bool(self.openai_api_key or self.gemini_api_key)
    
    @property
    def has_news_api(self) -> bool:
        """Check if NewsAPI key is configured."""
        return bool(self.news_api_key)
    
    @property
    def has_smtp(self) -> bool:
        """Check if SMTP credentials are configured."""
        return bool(self.smtp_email and self.smtp_password)
    
    @property
    def credentials_path(self) -> Path:
        """Path to OAuth credentials JSON."""
        return self.credentials_dir / 'credentials.json'
    
    @property
    def token_path(self) -> Path:
        """Path to saved OAuth token."""
        return self.credentials_dir / 'token.pickle'
    
    def ensure_credentials_dir(self):
        """Create credentials directory if it doesn't exist."""
        self.credentials_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
