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
        'AI',
        'ML',
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
    
    # YouTube Feeds (Channels)
    youtube_feeds: List[dict] = field(default_factory=lambda: [
        {'name': 'Two Minute Papers', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCbfYPyITQ-7l4upoX8nvctg'},
        {'name': 'AI Explained', 'url': 'https://www.youtube.com/feeds/videos.xml?channel_id=UCcnJ8uNYChtmbCtleKrQKAL'},
    ])
    
    # Product Hunt
    product_hunt_rss: str = "https://www.producthunt.com/feed?category=artificial-intelligence"
    
    # Reddit Feeds (RSS)
    reddit_feeds: List[dict] = field(default_factory=lambda: [
        {'name': 'r/artificial', 'url': 'https://www.reddit.com/r/artificial/.rss'},
        {'name': 'r/MachineLearning', 'url': 'https://www.reddit.com/r/MachineLearning/.rss'},
        {'name': 'r/LocalLLaMA', 'url': 'https://www.reddit.com/r/LocalLLaMA/.rss'},
        {'name': 'r/ChatGPT', 'url': 'https://www.reddit.com/r/ChatGPT/.rss'},
        {'name': 'r/OpenAI', 'url': 'https://www.reddit.com/r/OpenAI/.rss'},
        {'name': 'r/StableDiffusion', 'url': 'https://www.reddit.com/r/StableDiffusion/.rss'},
        {'name': 'r/ArtificialInteligence', 'url': 'https://www.reddit.com/r/ArtificialInteligence/.rss'},
        {'name': 'r/AItools', 'url': 'https://www.reddit.com/r/AItools/.rss'},
        {'name': 'r/singularity', 'url': 'https://www.reddit.com/r/singularity/.rss'},
        {'name': 'r/PromptEngineering', 'url': 'https://www.reddit.com/r/PromptEngineering/.rss'},
        {'name': 'r/ClaudeAI', 'url': 'https://www.reddit.com/r/ClaudeAI/.rss'},
        {'name': 'r/Midjourney', 'url': 'https://www.reddit.com/r/Midjourney/.rss'},
        {'name': 'r/LLM', 'url': 'https://www.reddit.com/r/LLM/.rss'},
        {'name': 'r/GenerativeAI', 'url': 'https://www.reddit.com/r/GenerativeAI/.rss'},
        {'name': 'r/DeepLearning', 'url': 'https://www.reddit.com/r/DeepLearning/.rss'},
        {'name': 'r/learnmachinelearning', 'url': 'https://www.reddit.com/r/learnmachinelearning/.rss'},
    ])
    
    # RSS Feeds to monitor
    rss_feeds: List[dict] = field(default_factory=lambda: [
        {'name': 'MIT Tech Review AI', 'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed'},
        {'name': 'OpenAI Blog', 'url': 'https://openai.com/blog/rss.xml'},
        {'name': 'Anthropic Research', 'url': 'https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml'},
        {'name': 'Hugging Face Blog', 'url': 'https://huggingface.co/blog/feed.xml'},
        {'name': 'Google DeepMind', 'url': 'https://deepmind.com/blog/feed/basic/'},
        {'name': 'NVIDIA Developer', 'url': 'https://developer.nvidia.com/blog/feed/'},
        {'name': 'AWS Machine Learning', 'url': 'http://feeds.feedburner.com/amazon/AWSAI'},
        {'name': 'Berkeley AI Research', 'url': 'https://bair.berkeley.edu/blog/feed.xml'},
        {'name': 'Microsoft Research', 'url': 'https://www.microsoft.com/en-us/research/feed/'},
        {'name': 'Wired AI', 'url': 'https://www.wired.com/feed/tag/ai/latest/rss'},
        {'name': 'TechCrunch AI', 'url': 'https://techcrunch.com/category/artificial-intelligence/feed/'},
        {'name': 'BBC News', 'url': 'https://feeds.bbci.co.uk/news/rss.xml'},
        {'name': 'GitHub Blog', 'url': 'https://github.blog/feed'},
        {'name': 'HF Trending', 'url': 'https://zernel.github.io/huggingface-trending-feed/feed.xml'},
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
    

    
    # Credentials directory (for future extensions)
    credentials_dir: Path = field(default_factory=lambda: Path(__file__).parent / 'credentials')
    
    def ensure_credentials_dir(self):
        """Create credentials directory if it doesn't exist."""
        self.credentials_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
