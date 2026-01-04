"""
Deduplication module for removing duplicate articles across sources.
Uses fuzzy string matching to detect similar headlines.
"""

from typing import List, Dict, Set
from datetime import datetime
from fuzzywuzzy import fuzz
from sources.arxiv_source import Article


class Deduplicator:
    """Removes duplicate articles based on title similarity."""
    
    def __init__(self, similarity_threshold: int = 80):
        """
        Initialize deduplicator.
        
        Args:
            similarity_threshold: Minimum fuzzy match score (0-100) to consider duplicates.
        """
        self.similarity_threshold = similarity_threshold
    
    def deduplicate(self, articles: List[Article]) -> List[Article]:
        """
        Remove duplicate articles from a list.
        
        Keeps the article with the highest relevance score when duplicates are found.
        
        Args:
            articles: List of Article objects.
            
        Returns:
            Deduplicated list of Article objects.
        """
        if not articles:
            return []
        
        # Sort by score (highest first), then by date (newest first)
        # We prioritize score, then freshness, then original list order (stable sort)
        sorted_articles = sorted(
            articles, 
            key=lambda x: (x.score, x.published or datetime.min), 
            reverse=True
        )
        
        unique_articles = []
        seen_titles: List[str] = []
        
        for article in sorted_articles:
            title = article.title.lower().strip()
            
            # Check if similar to any seen title
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = fuzz.ratio(title, seen_title)
                if similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break
                
                # Also check token sort ratio for reordered words
                token_similarity = fuzz.token_sort_ratio(title, seen_title)
                if token_similarity >= self.similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.append(title)
        
        return unique_articles
    
    def deduplicate_by_url(self, articles: List[Article]) -> List[Article]:
        """
        Remove articles with duplicate URLs.
        
        Args:
            articles: List of Article objects.
            
        Returns:
            List with unique URLs.
        """
        seen_urls: Set[str] = set()
        unique = []
        
        for article in articles:
            # Normalize URL
            url = article.url.lower().rstrip('/')
            
            if url not in seen_urls:
                seen_urls.add(url)
                unique.append(article)
        
        return unique
    
    def deduplicate_all(self, articles: List[Article]) -> List[Article]:
        """
        Full deduplication: URL-based first, then title-based.
        
        Args:
            articles: List of Article objects.
            
        Returns:
            Fully deduplicated list.
        """
        # First pass: exact URL matching
        url_deduped = self.deduplicate_by_url(articles)
        
        # Second pass: fuzzy title matching
        title_deduped = self.deduplicate(url_deduped)
        
        return title_deduped


# Quick test
if __name__ == '__main__':
    # Test with sample articles
    test_articles = [
        Article(title="OpenAI Releases GPT-5", url="https://example.com/1", source="News1", published=None, score=5.0),
        Article(title="OpenAI releases GPT-5 model", url="https://example.com/2", source="News2", published=None, score=3.0),
        Article(title="Google Announces Gemini 2.0", url="https://example.com/3", source="News1", published=None, score=4.0),
        Article(title="GPT-5 Released by OpenAI", url="https://example.com/4", source="News3", published=None, score=2.0),
    ]
    
    deduplicator = Deduplicator()
    unique = deduplicator.deduplicate_all(test_articles)
    
    print(f"Original: {len(test_articles)} articles")
    print(f"After dedup: {len(unique)} articles")
    for article in unique:
        print(f"  - {article.title} (score: {article.score})")
