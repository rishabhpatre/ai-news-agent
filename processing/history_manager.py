"""
History Manager for AI News Agent.
Tracks sent articles to prevent duplicates across runs.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Dict
from config import settings
from sources.arxiv_source import Article

class HistoryManager:
    """Manages history of sent articles to prevent duplicates."""
    
    def __init__(self, history_file: Path = None):
        """
        Initialize history manager.
        
        Args:
            history_file: Path to history JSON file.
        """
        if history_file:
            self.history_file = history_file
        else:
            self.history_file = settings.base_dir / 'data' / 'history.json'
            
        self.history: Dict[str, str] = {} # URL -> ISO Date
        self._load()
    
    def _load(self):
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    self.history = json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading history: {e}")
                self.history = {}
        else:
            self.history = {}
            
    def save(self):
        """Save history to file."""
        # Ensure data dir exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            print(f"⚠️ Error saving history: {e}")
            
    def filter_existing(self, articles: List[Article]) -> List[Article]:
        """
        Filter out articles that have already been sent.
        
        Args:
            articles: List of articles to filter.
            
        Returns:
            List of new articles.
        """
        new_articles = []
        for article in articles:
            # Normalize URL for comparison
            url = article.url.strip()
            
            if url not in self.history:
                new_articles.append(article)
        
        return new_articles
        
    def is_sent(self, url: str) -> bool:
        """
        Check if an article URL has arguably been sent.
        
        Args:
            url: Article URL.
            
        Returns:
            True if sent.
        """
        return url.strip() in self.history
        
    def add_articles(self, articles: List[Article]):
        """
        Add articles to history.
        
        Args:
            articles: List of articles to add.
        """
        now = datetime.now().isoformat()
        count = 0
        for article in articles:
            url = article.url.strip()
            if url not in self.history:
                self.history[url] = now
                count += 1
        
        if count > 0:
            self.save()
            
    def cleanup(self, days_to_keep: int = 30):
        """
        Remove old entries from history.
        
        Args:
            days_to_keep: Number of days to keep history.
        """
        cutoff = datetime.now() - timedelta(days=days_to_keep)
        initial_count = len(self.history)
        
        new_history = {}
        for url, date_str in self.history.items():
            try:
                date = datetime.fromisoformat(date_str)
                if date > cutoff:
                    new_history[url] = date_str
            except:
                # If date parse fails, drop it (or keep it? safer to drop if corrupt)
                continue
                
        self.history = new_history
        if len(self.history) < initial_count:
            self.save()
            print(f"🧹 Cleaned up history: {initial_count} -> {len(self.history)} items")
