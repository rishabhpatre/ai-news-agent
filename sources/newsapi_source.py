"""
NewsAPI source for fetching AI-related news articles.
Requires a NewsAPI.org API key (free tier available).
"""

import requests
from datetime import datetime, timedelta
from typing import List, Optional
from .arxiv_source import Article


class NewsAPISource:
    """Fetches AI news from NewsAPI.org."""
    
    BASE_URL = "https://newsapi.org/v2/everything"
    
    def __init__(self, api_key: Optional[str] = None, max_results: int = 20):
        self.api_key = api_key
        self.max_results = max_results
    
    def fetch(self, days_back: int = 1) -> List[Article]:
        """
        Fetch recent AI news articles.
        
        Args:
            days_back: Number of days to look back.
            
        Returns:
            List of Article objects.
        """
        if not self.api_key:
            print("NewsAPI key not configured, skipping...")
            return []
        
        articles = []
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        
        # Queries tailored for AI news
        queries = [
            '"artificial intelligence"',
            '"large language model" OR "LLM"',
            '"AI agent" OR "agentic AI"',
            'ChatGPT OR GPT-4 OR Claude OR Gemini',
        ]
        
        seen_urls = set()
        
        for query in queries:
            try:
                params = {
                    'q': query,
                    'from': from_date,
                    'language': 'en',
                    'sortBy': 'publishedAt',
                    'pageSize': min(self.max_results, 50),  # NewsAPI limit
                    'apiKey': self.api_key,
                }
                
                response = requests.get(self.BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data.get('status') != 'ok':
                    print(f"NewsAPI error: {data.get('message', 'Unknown error')}")
                    continue
                
                for item in data.get('articles', []):
                    url = item.get('url', '')
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)
                    
                    # Parse published date
                    published = None
                    if item.get('publishedAt'):
                        try:
                            published = datetime.fromisoformat(
                                item['publishedAt'].replace('Z', '+00:00')
                            ).replace(tzinfo=None)
                        except:
                            published = datetime.now()
                    
                    # Build summary from description
                    summary = item.get('description', '') or ''
                    if len(summary) > 300:
                        summary = summary[:297] + '...'
                    
                    article = Article(
                        title=item.get('title', 'Untitled'),
                        url=url,
                        source=item.get('source', {}).get('name', 'NewsAPI'),
                        published=published or datetime.now(),
                        summary=summary,
                        authors=[item.get('author')] if item.get('author') else [],
                        score=self._calculate_relevance(item),
                    )
                    articles.append(article)
                    
            except requests.RequestException as e:
                print(f"Error fetching from NewsAPI: {e}")
            except Exception as e:
                print(f"Error processing NewsAPI response: {e}")
        
        # Sort by score and limit
        articles.sort(key=lambda x: x.score, reverse=True)
        return articles[:self.max_results]
    
    def _calculate_relevance(self, item: dict) -> float:
        """Calculate relevance score."""
        score = 0.0
        text = ((item.get('title') or '') + ' ' + (item.get('description') or '')).lower()
        
        # High-value terms
        if any(term in text for term in ['llm', 'large language model', 'ai agent']):
            score += 3.0
        
        # Brand mentions
        if any(term in text for term in ['openai', 'anthropic', 'google ai', 'deepmind']):
            score += 2.0
        
        # General AI terms
        if any(term in text for term in ['chatgpt', 'gpt-4', 'claude', 'gemini']):
            score += 1.5
            
        # Deprioritize specific sources
        source_name = item.get('source', {}).get('name', '')
        if 'pypi.org' in source_name.lower():
            score -= 10.0
        
        return score


# Quick test
if __name__ == '__main__':
    import os
    api_key = os.getenv('NEWS_API_KEY')
    
    if api_key:
        source = NewsAPISource(api_key=api_key)
        articles = source.fetch(days_back=3)
        print(f"Found {len(articles)} articles")
        for article in articles[:5]:
            print(f"\n📰 {article.title}")
            print(f"   Source: {article.source}")
            print(f"   URL: {article.url}")
    else:
        print("Set NEWS_API_KEY environment variable to test")
