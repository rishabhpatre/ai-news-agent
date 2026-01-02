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
from sources.arxiv_source import ArxivSource
from sources.newsapi_source import NewsAPISource
from sources.rss_source import RSSSource
from sources.hackernews_source import HackerNewsSource
from processing.deduplicator import Deduplicator
from processing.summarizer import Summarizer
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
            groq_api_key=settings.groq_api_key,
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
        print(f"📡 Collecting content from sources (Lookback: {days_back} days standard, 7 days for tools/video)...")
        
        # 1. ArXiv Papers (High frequency - keep tight, but cover weekends)
        print("  • ArXiv papers...")
        # Ensure at least 3 days for ArXiv to cover weekends
        arxiv_days = max(3, days_back)
        papers = self.arxiv_source.fetch(days_back=arxiv_days)
        print(f"    Found {len(papers)} papers")
        
        # 2. Global News (NewsAPI)
        print("  • Global Headlines...")
        news_api = []
        if settings.has_news_api:
            try:
                news_api = self.newsapi_source.fetch(days_back=days_back)
                print(f"    Found {len(news_api)} articles")
            except Exception as e:
                print(f"    Error fetching NewsAPI: {e}")
        else:
            print("    Skipping NewsAPI (no key configured)")
        
        # === SLOW NEWS SOURCES (Blogs, Reddit, YouTube) ===
        # These don't post daily, so we look back 7 days to avoid "empty" sections
        extended_days = max(7, days_back)
        
        # 3. RSS Feeds (Blogs)
        print("  • RSS feeds...")
        rss_news = self.rss_source.fetch(days_back=days_back)
        print(f"    Found {len(rss_news)} articles")

        # 3b. Hugging Face (Isolated)
        print("  • Hugging Face feeds...")
        hf_source = RSSSource(settings.hf_feeds)
        hf_news = hf_source.fetch(days_back=days_back, check_relevance=False)
        print(f"    Found {len(hf_news)} articles")
        
        # 4. Reddit (Via RSS)
        reddit_posts = []
        print("  • Reddit...")
        for feed in settings.reddit_feeds:
            try:
                # Use RSSSource for each subreddit
                r_source = RSSSource([feed])
                posts = r_source.fetch(days_back=days_back)
                # Ensure source is labeled correctly (e.g. "r/MachineLearning")
                for p in posts:
                    p.source = feed['name']
                reddit_posts.extend(posts)
            except Exception as e:
                print(f"    Error fetching {feed['name']}: {e}")
        print(f"    Found {len(reddit_posts)} posts")

        # 5. YouTube (via RSS)
        print("  • YouTube...")
        videos = []
        for feed in settings.youtube_feeds:
            try:
                # RSSSource expects list of dicts
                v_source = RSSSource([feed]) 
                # Fetch videos (bypass relevance check for curated channels)
                v_items = v_source.fetch(days_back=extended_days, check_relevance=False)
                # Add channel name to source (redundant if RSSSource does it, but safe)
                for v in v_items:
                    v.source = feed['name']
                videos.extend(v_items)
            except Exception as e:
                print(f"    Error fetching {feed['name']}: {e}")
        print(f"    Found {len(videos)} videos")
        
        # 6. Product Hunt (via RSS)
        print("  • Product Hunt...")
        tools = []
        try:
            ph_feed = [{'name': 'Product Hunt', 'url': settings.product_hunt_rss}]
            ph_source = RSSSource(ph_feed)
            tools = ph_source.fetch(days_back=extended_days)
            print(f"    Found {len(tools)} tools")
        except Exception as e:
            print(f"    Error fetching Product Hunt: {e}")

        # Hackernews (High frequency - keep tight, or maybe extended? HN moves fast, keeping 1 day is better)
        print("  • Hacker News discussions...")
        discussions = self.hn_source.fetch(days_back=days_back)
        print(f"    Found {len(discussions)} discussions")
        
        # Return separate lists
        return {
            'papers': papers,
            'news_api': news_api,
            'rss_news': rss_news,
            'reddit_posts': reddit_posts,
            'videos': videos,
            'tools': tools,
            'discussions': discussions,
            'hf_news': hf_news
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
        
        # Deduplicate NewsAPI
        print("  • Deduplicating headlines...")
        news_api = self.deduplicator.deduplicate_all(content['news_api'])
        news_api = news_api[:settings.max_news]
        print(f"    {len(content['news_api'])} → {len(news_api)}")

        # Deduplicate RSS
        print("  • Deduplicating RSS feeds...")
        rss_news = self.deduplicator.deduplicate_all(content['rss_news'])
        rss_news = rss_news[:settings.max_news]
        print(f"    {len(content['rss_news'])} → {len(rss_news)}")
        
        # Deduplicate Reddit
        print("  • Deduplicating Reddit...")
        reddit_posts = self.deduplicator.deduplicate_all(content['reddit_posts'])
        reddit_posts = reddit_posts[:5] # Hard limit for now
        print(f"    {len(content['reddit_posts'])} → {len(reddit_posts)}")

        # Deduplicate Videos
        print("  • Deduplicating Videos...")
        videos = self.deduplicator.deduplicate_all(content['videos'])
        videos = videos[:10] 
        print(f"    {len(content['videos'])} → {len(videos)}")
        
        # Deduplicate Tools
        print("  • Deduplicating Tools...")
        tools = self.deduplicator.deduplicate_all(content['tools'])
        tools = tools[:5] 
        print(f"    {len(content['tools'])} → {len(tools)}")
        
        # Deduplicate discussions
        print("  • Deduplicating discussions...")
        discussions = self.deduplicator.deduplicate_all(content['discussions'])
        discussions = discussions[:settings.max_discussions]
        print(f"    {len(content['discussions'])} → {len(discussions)}")

        # Deduplicate Hugging Face
        print("  • Deduplicating Hugging Face...")
        hf_news = self.deduplicator.deduplicate_all(content['hf_news'])
        hf_news = hf_news[:settings.max_news]
        print(f"    {len(content['hf_news'])} → {len(hf_news)}")
        
        # Generate summaries if LLM is available (DISABLED - Bottleneck)
        # if self.summarizer.has_llm:
        #     print("  • Generating AI summaries...")
        #     papers = self.summarizer.summarize_batch(papers)
        #     news_api = self.summarizer.summarize_batch(news_api)
        #     rss_news = self.summarizer.summarize_batch(rss_news)
        #     hf_news = self.summarizer.summarize_batch(hf_news)
        #     reddit_posts = self.summarizer.summarize_batch(reddit_posts)
        #     videos = self.summarizer.summarize_batch(videos)
        #     discussions = self.summarizer.summarize_batch(discussions)
        #     tools = self.summarizer.summarize_batch(tools)
        
        return {
            'papers': papers,
            'news_api': news_api,
            'rss_news': rss_news,
            'reddit_posts': reddit_posts,
            'videos': videos,
            'tools': tools,
            'discussions': discussions,
            'hf_news': hf_news,
        }
    
    def send_digest(self, content: dict, dry_run: bool = False) -> bool:
        """
        Send the digest email.
        
        Args:
            content: Processed content dict.
            dry_run: If True, print email instead of sending.
            
        Returns:
            True if successful.
        """
        if not dry_run and not settings.recipient_email:
            print("\n❌ ERROR: RECIPIENT_EMAIL not set in .env")
            return False
        
        total = sum(len(v) for v in content.values())
        print(f"\n📧 {'Previewing' if dry_run else 'Sending'} digest with {total} items...")
        
        # Define readable labels
        lookback_labels = {
            'papers': f"Past {max(3, settings.default_lookback)} days",
            'news': f"Past {settings.default_lookback} days",
            'default': "Past 7 days", # For extended lookback sources
        }

        return self.email_client.send_digest(
            to_email=settings.recipient_email,
            papers=content['papers'],
            news_api=content['news_api'],
            rss_news=content['rss_news'],
            hf_news=content['hf_news'], # Added hf_news
            reddit_posts=content['reddit_posts'],
            videos=content['videos'],
            tools=content['tools'],
            discussions=content['discussions'],
            lookback_labels=lookback_labels,
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
        default=2,
        help='Number of days to look back (default: 2)',
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
