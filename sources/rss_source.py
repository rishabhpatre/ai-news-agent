"""
RSS source for fetching AI news from curated blogs and feeds.
Uses feedparser library to parse RSS/Atom feeds.
"""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
from time import mktime
import re
from .arxiv_source import Article


class RSSSource:
    """Fetches AI news from curated RSS feeds."""
    
    # Default feeds focused on AI/ML
    DEFAULT_FEEDS = [
        {'name': 'OpenAI Blog', 'url': 'https://openai.com/blog/rss.xml'},
        {'name': 'Google AI Blog', 'url': 'https://blog.google/technology/ai/rss/'},
        {'name': 'Anthropic', 'url': 'https://www.anthropic.com/research/rss.xml'},
        {'name': 'Hugging Face Blog', 'url': 'https://huggingface.co/blog/feed.xml'},
        {'name': 'MIT Tech Review AI', 'url': 'https://www.technologyreview.com/topic/artificial-intelligence/feed'},
        {'name': 'The Verge AI', 'url': 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml'},
        {'name': 'Ars Technica AI', 'url': 'https://feeds.arstechnica.com/arstechnica/technology-lab'},
        {'name': 'VentureBeat AI', 'url': 'https://venturebeat.com/category/ai/feed/'},
        {'name': 'The Batch (DeepLearning.AI)', 'url': 'https://www.deeplearning.ai/the-batch/feed/'},
    ]
    
    def __init__(self, feeds: List[Dict[str, str]] = None, keywords: List[str] = None):
        self.feeds = feeds or self.DEFAULT_FEEDS
        self.keywords = keywords or [
            'ai', 'artificial intelligence', 'llm', 'large language model',
            'chatgpt', 'gpt', 'claude', 'gemini', 'machine learning',
            'deep learning', 'neural network', 'transformer', 'ai agent',
        ]
        
        # Reddit requires a specific User-Agent format
        self.headers = {
            'User-Agent': 'python:ai-news-agent:v1.0 (by /u/ai_news_agent_dev)'
        }
    
    def fetch(self, days_back: int = 1, check_relevance: bool = True) -> List[Article]:
        """
        Fetch recent articles from RSS feeds.
        
        Args:
            days_back: Number of days to look back.
            check_relevance: Whether to filter articles by AI keywords.
            
        Returns:
            List of Article objects.
        """
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for feed_info in self.feeds:
            try:
                # Use requests to fetch content first (better header control)
                response = requests.get(feed_info['url'], headers=self.headers, timeout=10)
                
                if response.status_code != 200:
                    print(f"Warning: Failed to fetch {feed_info['name']} (Status: {response.status_code})")
                    continue
                    
                feed = feedparser.parse(response.text)
                
                if feed.bozo and not feed.entries:
                    print(f"Warning: Could not parse feed {feed_info['name']}")
                    continue
                
                for entry in feed.entries:
                    # Parse published date
                    published = self._parse_date(entry)
                    if published and published < cutoff_date:
                        continue
                    
                    # Check relevance (skip non-AI articles from general feeds)
                    title = entry.get('title', '')
                    summary = self._get_summary(entry)
                    if check_relevance and not self._is_relevant(title, summary):
                        continue
                    
                    article = Article(
                        title=title.strip(),
                        url=entry.get('link', ''),
                        source=feed_info['name'],
                        published=published or datetime.now(),
                        summary=summary,
                        authors=self._get_authors(entry),
                        thumbnail=self._get_thumbnail(entry),
                        score=self._calculate_relevance(title, summary, feed_info['name'], published),
                    )
                    articles.append(article)
                    
            except Exception as e:
                print(f"Error fetching RSS feed {feed_info['name']}: {e}")
        
        # Sort by relevance (Score > Date > Feed Order)
        articles.sort(key=lambda x: (x.score, x.published or datetime.min), reverse=True)
        return articles
    
    def _parse_date(self, entry) -> datetime:
        """Parse the published date from an RSS entry."""
        for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
            if hasattr(entry, date_field) and getattr(entry, date_field):
                try:
                    time_struct = getattr(entry, date_field)
                    return datetime.fromtimestamp(mktime(time_struct))
                except:
                    continue
        
        # Try parsing string dates
        for date_field in ['published', 'updated', 'created']:
            if hasattr(entry, date_field) and getattr(entry, date_field):
                try:
                    from email.utils import parsedate_to_datetime
                    return parsedate_to_datetime(getattr(entry, date_field)).replace(tzinfo=None)
                except:
                    continue
        
        return None
    
    def _get_summary(self, entry) -> str:
        """Extract and clean the summary from an RSS entry."""
        # Try summary first, then content
        summary = entry.get('summary', '')
        
        if not summary and entry.get('content'):
            content = entry.content[0] if isinstance(entry.content, list) else entry.content
            summary = content.get('value', '') if isinstance(content, dict) else str(content)
        
        # Strip HTML tags
        summary = re.sub(r'<[^>]+>', '', summary)
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        # Limit length
        if len(summary) > 400:
            summary = summary[:397] + '...'
        
        return summary
    
    def _get_authors(self, entry) -> List[str]:
        """Extract authors from an RSS entry."""
        authors = []
        
        if hasattr(entry, 'author') and entry.author:
            authors.append(entry.author)
        
        if hasattr(entry, 'authors'):
            for author in entry.authors:
                name = author.get('name', '') if isinstance(author, dict) else str(author)
                if name and name not in authors:
                    authors.append(name)
        
        return authors
    
    def _get_thumbnail(self, entry) -> str:
        """Extract thumbnail URL from RSS entry."""
        # Check media_thumbnail (YouTube often uses this)
        if hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
            return entry.media_thumbnail[0]['url']
            
        # Check media_content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('medium') == 'image' or media.get('type', '').startswith('image/'):
                    return media['url']
                    
        # Check links for enclosures/images
        if hasattr(entry, 'links'):
            for link in entry.links:
                if link.get('rel') == 'enclosure' and link.get('type', '').startswith('image/'):
                    return link['href']
                    
        return None
    
    def _is_relevant(self, title: str, summary: str) -> bool:
        """Check if an article is relevant to AI/ML using word boundaries."""
        text = (title + ' ' + summary).lower()
        
        for kw in self.keywords:
            # Use regex for whole word matching to avoid partial matches (e.g. 'ai' in 'said')
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text):
                return True
        return False
    
    def _calculate_relevance(self, title: str, summary: str, source_name: str = '', published: datetime = None) -> float:
        """Calculate relevance score based on keyword matches, source priority, and age."""
        text = (title + ' ' + summary).lower()
        score = 0.0
        
        # Priority Sources (Company Blogs > Media)
        priority_sources = [
            'OpenAI', 'Anthropic', 'Google', 'DeepMind', 'Microsoft', 
            'Hugging Face', 'NVIDIA', 'AWS', 'Meta'
        ]
        
        # Check partial match for source name (e.g. "Google AI Blog" matches "Google")
        if any(company.lower() in source_name.lower() for company in priority_sources):
            score += 3.0
        
        # High-value terms
        high_value = [
            'llm', 'large language model', 'ai agent', 'agentic', 'gpt-4', 'claude',
            'autonomous agent', 'reasoning model', 'multi-agent', 'test-time compute',
            'long-horizon planning', 'memory-augmented', 'retrieval-augmented', 'rag',
            'reasoning pipeline', 'agent framework', 'agent architecture'
        ]
        for term in high_value:
            if term in text:
                score += 2.0
        
        # Medium-value terms
        medium_value = ['chatgpt', 'gemini', 'openai', 'anthropic', 'machine learning']
        for term in medium_value:
            if term in text:
                score += 1.0
        
        # Time Decay: -1.5 points per day old
        if published:
            age = datetime.now() - published
            days_old = max(0, age.total_seconds() / 86400)
            score -= (days_old * 1.5)
            
        return score


# Quick test
if __name__ == '__main__':
    source = RSSSource()
    articles = source.fetch(days_back=7)  # Last week for testing
    print(f"Found {len(articles)} articles")
    for article in articles[:10]:
        print(f"\n📰 {article.title}")
        print(f"   Source: {article.source}")
        print(f"   URL: {article.url}")
