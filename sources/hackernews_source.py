"""
Hacker News source for trending AI discussions.
Uses the official Hacker News API (no key required).
"""

import requests
from datetime import datetime, timedelta
from typing import List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from .arxiv_source import Article


class HackerNewsSource:
    """Fetches AI-related stories from Hacker News."""
    
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    def __init__(self, keywords: List[str] = None, min_score: int = 20, max_results: int = 30):
        self.keywords = keywords or [
            'ai', 'llm', 'gpt', 'chatgpt', 'claude', 'gemini',
            'openai', 'anthropic', 'machine learning', 'neural',
            'transformer', 'language model', 'artificial intelligence',
            'deep learning', 'ai agent', 'agentic',
        ]
        self.min_score = min_score
        self.max_results = max_results
    
    def fetch(self, days_back: int = 1) -> List[Article]:
        """
        Fetch trending AI stories from Hacker News.
        
        Args:
            days_back: Number of days to look back.
            
        Returns:
            List of Article objects.
        """
        articles = []
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        try:
            # Get top and new story IDs
            top_ids = self._get_story_ids('topstories', limit=200)
            new_ids = self._get_story_ids('newstories', limit=200)
            
            # Combine and dedupe
            all_ids = list(dict.fromkeys(top_ids + new_ids))
            
            # Fetch stories in parallel
            stories = self._fetch_stories_parallel(all_ids[:300])
            
            for story in stories:
                if not story:
                    continue
                
                # Filter by date
                time = story.get('time', 0)
                if time < cutoff_timestamp:
                    continue
                
                # Filter by score
                score = story.get('score', 0)
                if score < self.min_score:
                    continue
                
                # Check relevance
                title = story.get('title', '')
                if not self._is_relevant(title):
                    continue
                
                # Create article
                url = story.get('url', f"https://news.ycombinator.com/item?id={story['id']}")
                article = Article(
                    title=title,
                    url=url,
                    source='Hacker News',
                    published=datetime.fromtimestamp(time),
                    summary=f"Score: {score} points | {story.get('descendants', 0)} comments",
                    authors=[story.get('by', 'Anonymous')],
                    score=self._calculate_relevance(title, score),
                )
                articles.append(article)
            
        except Exception as e:
            print(f"Error fetching from Hacker News: {e}")
        
        # Sort by relevance score
        articles.sort(key=lambda x: x.score, reverse=True)
        return articles[:self.max_results]
    
    def _get_story_ids(self, endpoint: str, limit: int = 100) -> List[int]:
        """Get story IDs from a HN endpoint."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/{endpoint}.json",
                timeout=10
            )
            response.raise_for_status()
            return response.json()[:limit]
        except:
            return []
    
    def _fetch_story(self, story_id: int) -> dict:
        """Fetch a single story by ID."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/item/{story_id}.json",
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def _fetch_stories_parallel(self, story_ids: List[int], max_workers: int = 10) -> List[dict]:
        """Fetch multiple stories in parallel."""
        stories = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_id = {executor.submit(self._fetch_story, sid): sid for sid in story_ids}
            for future in as_completed(future_to_id):
                result = future.result()
                if result:
                    stories.append(result)
        return stories
    
    def _is_relevant(self, title: str) -> bool:
        """Check if a story title is AI-related using word boundaries."""
        title_lower = title.lower()
        
        for kw in self.keywords:
            # Use regex for whole word matching to avoid partial matches
            if re.search(r'\b' + re.escape(kw.lower()) + r'\b', title_lower):
                return True
        return False
    
    def _calculate_relevance(self, title: str, score: int) -> float:
        """Calculate relevance score based on keywords and HN score."""
        title_lower = title.lower()
        relevance = 0.0
        
        # High-value terms
        high_value = [
            'llm', 'large language model', 'ai agent', 'agentic', 'gpt-4', 'claude', 'o1',
            'autonomous agent', 'reasoning model', 'multi-agent', 'test-time compute',
            'long-horizon planning', 'memory-augmented', 'retrieval-augmented', 'rag',
            'reasoning pipeline', 'agent framework', 'agent architecture'
        ]
        for term in high_value:
            if term in title_lower:
                relevance += 3.0
        
        # Medium-value terms
        medium_value = ['openai', 'anthropic', 'chatgpt', 'gemini', 'deepmind']
        for term in medium_value:
            if term in title_lower:
                relevance += 2.0
        
        # Add HN score as a factor (normalized)
        relevance += min(score / 100, 5.0)
        
        return relevance


# Quick test
if __name__ == '__main__':
    source = HackerNewsSource()
    articles = source.fetch(days_back=3)
    print(f"Found {len(articles)} AI-related stories")
    for article in articles[:10]:
        print(f"\n🔥 {article.title}")
        print(f"   {article.summary}")
        print(f"   URL: {article.url}")
