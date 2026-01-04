"""
ArXiv source for fetching latest AI/ML research papers.
Uses the arxiv Python library to query the arXiv API.
"""

import arxiv
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import dataclass
import re


@dataclass
class Article:
    """Represents a news article or research paper."""
    title: str
    url: str
    source: str
    published: datetime
    summary: str = ""
    authors: List[str] = None
    categories: List[str] = None
    thumbnail: str = None
    score: float = 0.0  # Relevance score
    
    def __post_init__(self):
        if self.authors is None:
            self.authors = []
        if self.categories is None:
            self.categories = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'published': self.published.isoformat() if self.published else None,
            'summary': self.summary,
            'authors': self.authors,
            'authors': self.authors,
            'categories': self.categories,
            'thumbnail': self.thumbnail,
            'score': self.score,
        }


class ArxivSource:
    """Fetches latest AI/ML research papers from ArXiv."""
    
    def __init__(self, categories: List[str] = None, keywords: List[str] = None, max_results: int = 50):
        self.categories = categories or ['cs.AI', 'cs.CL', 'cs.LG']
        self.keywords = keywords or ['LLM', 'large language model', 'AI agent', 'agentic']
        self.max_results = max_results
        self.client = arxiv.Client()
    
    def fetch(self, days_back: int = 1) -> List[Article]:
        """
        Fetch recent papers from ArXiv.
        
        Args:
            days_back: Number of days to look back for papers.
            
        Returns:
            List of Article objects.
        """
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        # Build query for categories
        category_query = ' OR '.join([f'cat:{cat}' for cat in self.categories])
        
        # Build keyword query for better relevance
        keyword_query = ' OR '.join([f'all:"{kw}"' for kw in self.keywords])
        
        # Combine queries
        query = f'({category_query}) AND ({keyword_query})'
        
        try:
            search = arxiv.Search(
                query=query,
                max_results=self.max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            
            for result in self.client.results(search):
                # Filter by date
                published = result.published.replace(tzinfo=None)
                if published < cutoff_date:
                    continue
                
                # Create article
                article = Article(
                    title=result.title.replace('\n', ' ').strip(),
                    url=result.entry_id,
                    source='ArXiv',
                    published=published,
                    summary=self._clean_abstract(result.summary),
                    authors=[author.name for author in result.authors[:5]],  # First 5 authors
                    categories=result.categories,
                    score=self._calculate_relevance(result),
                )
                articles.append(article)
                
        except Exception as e:
            print(f"Error fetching from ArXiv: {e}")
        
        # Sort by relevance score (Score > Date)
        articles.sort(key=lambda x: (x.score, x.published or datetime.min), reverse=True)
        return articles
    
    def _clean_abstract(self, abstract: str) -> str:
        """Clean up abstract text."""
        # Remove newlines and extra spaces
        text = re.sub(r'\s+', ' ', abstract)
        # Limit length
        if len(text) > 500:
            text = text[:497] + '...'
        return text.strip()
    
    def _calculate_relevance(self, result) -> float:
        """Calculate relevance score based on keywords in title and abstract."""
        score = 0.0
        text = (result.title + ' ' + result.summary).lower()
        
        # High-value keywords
        high_value = [
            'llm', 'large language model', 'ai agent', 'agentic', 'gpt', 'transformer',
            'autonomous agent', 'reasoning model', 'multi-agent', 'test-time compute',
            'long-horizon planning', 'memory-augmented', 'retrieval-augmented', 'rag',
            'reasoning pipeline', 'agent framework', 'agent architecture'
        ]
        medium_value = ['reasoning', 'benchmark', 'fine-tuning', 'prompt', 'chain-of-thought']
        
        for kw in high_value:
            if kw in text:
                score += 2.0
        
        for kw in medium_value:
            if kw in text:
                score += 1.0
        
        return score


# Quick test
if __name__ == '__main__':
    source = ArxivSource()
    papers = source.fetch(days_back=7)  # Last week for testing
    print(f"Found {len(papers)} papers")
    for paper in papers[:5]:
        print(f"\n📄 {paper.title}")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   URL: {paper.url}")
