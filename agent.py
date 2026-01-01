#!/usr/bin/env python3
"""
AI News Agent - Main Orchestrator

Collects AI/ML news from multiple sources, processes and deduplicates content,
generates summaries, and sends a daily email digest.

Usage:
    python agent.py              # Run and send digest
    python agent.py --dry-run    # Preview without sending
    python agent.py --test       # Send test email
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import settings
from sources import ArxivSource, NewsAPISource, RSSSource, HackerNewsSource
from processing import Deduplicator, Summarizer
from email_client.smtp_client import SMTPClient


class AINewsAgent:
    """Main AI News Agent that orchestrates the digest pipeline."""
    
    def __init__(self):
        """Initialize the agent with all components."""
        # Initialize sources
        self.arxiv_source = ArxivSource(
            categories=settings.arxiv_categories,
            keywords=settings.ai_topics[:10],
            max_results=settings.max_papers * 3,  # Fetch more, filter later
        )
        
        self.newsapi_source = NewsAPISource(
            api_key=settings.news_api_key,
            max_results=settings.max_news * 2,
        )
        
        self.rss_source = RSSSource(
            feeds=settings.rss_feeds,
            keywords=settings.ai_topics,
        )
        
        self.hn_source = HackerNewsSource(
            keywords=settings.ai_topics[:15],
            min_score=30,
            max_results=settings.max_discussions * 3,
        )
        
        # Initialize processing
        self.deduplicator = Deduplicator(similarity_threshold=75)
        self.summarizer = Summarizer(
            openai_api_key=settings.openai_api_key,
            gemini_api_key=settings.gemini_api_key,
        )
        
        # Initialize email client
        if not settings.has_smtp:
            print("⚠️  SMTP not configured. Email sending will fail.")
            print("Set SMTP_EMAIL and SMTP_PASSWORD in .env")
        
        self.email_client = SMTPClient(
            email=settings.smtp_email or "",
            password=settings.smtp_password or "",
            provider=settings.smtp_provider,
        )
    
    def collect_content(self, days_back: int = 1) -> dict:
        """
        Collect content from all sources.
        
        Args:
            days_back: Number of days to look back.
            
        Returns:
            Dict with 'papers', 'news', and 'discussions' lists.
        """
        print("📡 Collecting content from sources...")
        
        # Fetch from each source
        print("  • ArXiv papers...")
        papers = self.arxiv_source.fetch(days_back=days_back)
        print(f"    Found {len(papers)} papers")
        
        print("  • News articles...")
        news_api = self.newsapi_source.fetch(days_back=days_back)
        print(f"    Found {len(news_api)} from NewsAPI")
        
        print("  • RSS feeds...")
        rss_news = self.rss_source.fetch(days_back=days_back)
        print(f"    Found {len(rss_news)} from RSS")
        
        print("  • Hacker News discussions...")
        discussions = self.hn_source.fetch(days_back=days_back)
        print(f"    Found {len(discussions)} discussions")
        
        # Combine news sources
        all_news = news_api + rss_news
        
        return {
            'papers': papers,
            'news': all_news,
            'discussions': discussions,
        }
    
    def process_content(self, content: dict) -> dict:
        """
        Process and deduplicate collected content.
        
        Args:
            content: Dict from collect_content().
            
        Returns:
            Processed content dict.
        """
        print("\n🔧 Processing content...")
        
        # Deduplicate papers
        print("  • Deduplicating papers...")
        papers = self.deduplicator.deduplicate_all(content['papers'])
        papers = papers[:settings.max_papers]
        print(f"    {len(content['papers'])} → {len(papers)}")
        
        # Deduplicate news
        print("  • Deduplicating news...")
        news = self.deduplicator.deduplicate_all(content['news'])
        news = news[:settings.max_news]
        print(f"    {len(content['news'])} → {len(news)}")
        
        # Deduplicate discussions
        print("  • Deduplicating discussions...")
        discussions = self.deduplicator.deduplicate_all(content['discussions'])
        discussions = discussions[:settings.max_discussions]
        print(f"    {len(content['discussions'])} → {len(discussions)}")
        
        # Generate summaries if LLM is available
        if self.summarizer.has_llm:
            print("  • Generating AI summaries...")
            papers = self.summarizer.summarize_batch(papers)
            news = self.summarizer.summarize_batch(news)
        
        return {
            'papers': papers,
            'news': news,
            'discussions': discussions,
        }
    
    def send_digest(self, content: dict, dry_run: bool = False) -> bool:
        """
        Send the email digest.
        
        Args:
            content: Processed content dict.
            dry_run: If True, preview without sending.
            
        Returns:
            True if successful.
        """
        if not settings.recipient_email:
            print("\n❌ ERROR: RECIPIENT_EMAIL not set in .env")
            return False
        
        total = len(content['papers']) + len(content['news']) + len(content['discussions'])
        print(f"\n📧 {'Previewing' if dry_run else 'Sending'} digest with {total} items...")
        
        return self.email_client.send_digest(
            to_email=settings.recipient_email,
            papers=content['papers'],
            news=content['news'],
            discussions=content['discussions'],
            dry_run=dry_run,
        )
    
    def run(self, dry_run: bool = False, days_back: int = 1) -> bool:
        """
        Run the full digest pipeline.
        
        Args:
            dry_run: Preview without sending.
            days_back: Number of days to look back.
            
        Returns:
            True if successful.
        """
        print(f"\n{'='*60}")
        print(f"🤖 AI News Agent - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*60}\n")
        
        try:
            # Collect
            content = self.collect_content(days_back=days_back)
            
            # Check if we have content
            total = sum(len(v) for v in content.values())
            if total == 0:
                print("\n⚠️  No content found. Try increasing days_back or check sources.")
                return False
            
            # Process
            processed = self.process_content(content)
            
            # Send
            success = self.send_digest(processed, dry_run=dry_run)
            
            if success:
                print(f"\n✅ Digest {'previewed' if dry_run else 'sent'} successfully!")
            else:
                print(f"\n❌ Failed to {'preview' if dry_run else 'send'} digest")
            
            return success
            
        except Exception as e:
            print(f"\n❌ Error running agent: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def send_test_email(self) -> bool:
        """Send a test email to verify setup."""
        if not settings.recipient_email:
            print("❌ RECIPIENT_EMAIL not set in .env")
            return False
        
        print(f"📧 Sending test email to {settings.recipient_email}...")
        return self.email_client.send_test(settings.recipient_email)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='AI News Agent - Daily LLM/AI Digest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Preview digest without sending email',
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='Send a test email to verify setup',
    )
    parser.add_argument(
        '--days', '-n',
        type=int,
        default=1,
        help='Number of days to look back (default: 1)',
    )
    
    args = parser.parse_args()
    
    # Create agent
    agent = AINewsAgent()
    
    if args.test:
        # Test mode
        success = agent.send_test_email()
    else:
        # Normal run
        success = agent.run(dry_run=args.dry_run, days_back=args.days)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
