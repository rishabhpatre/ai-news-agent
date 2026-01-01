"""
SMTP email client for sending digests without API setup.
Uses Gmail's SMTP server with App Passwords - no GCP required!
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader

# Import Article from sources
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from sources.arxiv_source import Article


class SMTPClient:
    """
    Simple SMTP client for sending emails.
    
    For Gmail, you need an App Password (not your regular password):
    1. Enable 2-Factor Authentication on your Google account
    2. Go to: https://myaccount.google.com/apppasswords
    3. Generate an App Password for "Mail"
    4. Use that 16-character password in SMTP_PASSWORD
    """
    
    # SMTP server configurations
    SMTP_SERVERS = {
        'gmail': ('smtp.gmail.com', 587),
        'outlook': ('smtp.office365.com', 587),
        'yahoo': ('smtp.mail.yahoo.com', 587),
    }
    
    def __init__(
        self,
        email: str,
        password: str,
        provider: str = 'gmail',
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize SMTP client.
        
        Args:
            email: Your email address (sender).
            password: App Password (NOT your regular password).
            provider: Email provider ('gmail', 'outlook', 'yahoo').
            template_dir: Directory containing email templates.
        """
        self.email = email
        self.password = password
        self.provider = provider.lower()
        self.template_dir = template_dir or Path(__file__).parent / 'templates'
        
        if self.provider not in self.SMTP_SERVERS:
            raise ValueError(f"Unknown provider: {provider}. Use: {list(self.SMTP_SERVERS.keys())}")
        
        self.smtp_host, self.smtp_port = self.SMTP_SERVERS[self.provider]
        
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
        )
    
    def send_digest(
        self,
        to_email: str,
        papers: List[Article],
        news_api: List[Article],
        rss_news: List[Article],
        reddit_posts: List[Article],
        videos: List[Article],
        tools: List[Article],
        discussions: List[Article],
        hf_news: List[Article],
        dry_run: bool = False,
    ) -> bool:
        """
        Send the daily AI news digest email.
        
        Args:
            to_email: Recipient email address.
            papers: List of research paper articles.
            news_api: List of global news articles.
            rss_news: List of community/blog updates.
            reddit_posts: List of Reddit posts.
            videos: List of video articles.
            tools: List of tool articles.
            discussions: List of HN discussions.
            dry_run: If True, print email instead of sending.
            
        Returns:
            True if email sent successfully.
        """
        # Render HTML template
        html_content = self._render_template(
            papers=papers,
            news_api=news_api,
            rss_news=rss_news,
            reddit_posts=reddit_posts,
            videos=videos,
            tools=tools,
            discussions=discussions,
            hf_news=hf_news,
        )
        
        # Handle multiple recipients
        if ',' in to_email:
            recipients = [e.strip() for e in to_email.split(',')]
            to_header = ', '.join(recipients)
        else:
            recipients = [to_email]
            to_header = to_email
        
        # Create email message
        subject = f"🤖 AI Daily Digest - {datetime.now().strftime('%B %d, %Y')}"
        
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = self.email
        message['To'] = to_header
        
        # Plain text fallback
        plain_text = self._create_plain_text(papers, news_api, rss_news, reddit_posts, videos, tools, discussions, hf_news)
        message.attach(MIMEText(plain_text, 'plain'))
        
        # HTML content
        message.attach(MIMEText(html_content, 'html'))
        
        if dry_run:
            print(f"\n{'='*60}")
            print(f"DRY RUN - Email Preview")
            print(f"{'='*60}")
            print(f"To: {to_header}")
            print(f"Subject: {subject}")
            print(f"{'='*60}")
            print(plain_text)
            print(f"{'='*60}\n")
            return True
        
        # Send email via SMTP
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.email, self.password)
                server.send_message(message)
            
            print(f"✅ Digest sent to {len(recipients)} recipient(s): {to_header}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Authentication failed!")
            print(f"   Make sure you're using an App Password, not your regular password.")
            print(f"   Get one at: https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    def _render_template(
        self,
        papers: List[Article],
        news_api: List[Article],
        rss_news: List[Article],
        reddit_posts: List[Article],
        videos: List[Article],
        tools: List[Article],
        discussions: List[Article],
        hf_news: List[Article],
    ) -> str:
        """Render the HTML email template."""
        try:
            total_count = len(papers) + len(news_api) + len(rss_news) + len(reddit_posts) + len(videos) + len(tools) + len(discussions) + len(hf_news)
            template = self._jinja_env.get_template('digest.html')
            return template.render(
                date=datetime.now().strftime('%B %d, %Y'),
                papers=papers,
                news_api=news_api,
                rss_news=rss_news,
                hf_news=hf_news,
                reddit_posts=reddit_posts,
                videos=videos,
                tools=tools,
                discussions=discussions,
                total_count=total_count,
            )
        except Exception as e:
            print(f"Template rendering failed: {e}")
            return "<h1>Error rendering template</h1><p>But we have results!</p>" 
    
    def _create_basic_html(
        self,
        papers: List[Article],
        news_api: List[Article],
        rss_news: List[Article],
        discussions: List[Article],
    ) -> str:
        """Create basic HTML if template fails."""
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1>🤖 AI Daily Digest</h1>
        <p>{datetime.now().strftime('%B %d, %Y')}</p>
        """
        
        if papers:
            html += "<h2>📄 Research Papers</h2><ul>"
            for p in papers[:10]:
                html += f'<li><a href="{p.url}">{p.title}</a></li>'
            html += "</ul>"
        
        if news_api:
            html += "<h2>📰 Global Headlines</h2><ul>"
            for n in news_api[:10]:
                html += f'<li><a href="{n.url}">{n.title}</a> ({n.source})</li>'
            html += "</ul>"
            
        if rss_news:
            html += "<h2>🌐 Community Updates</h2><ul>"
            for n in rss_news[:10]:
                html += f'<li><a href="{n.url}">{n.title}</a> ({n.source})</li>'
            html += "</ul>"
        
        if discussions:
            html += "<h2>🔥 Trending Discussions</h2><ul>"
            for d in discussions[:5]:
                html += f'<li><a href="{d.url}">{d.title}</a></li>'
            html += "</ul>"
        
        html += "</body></html>"
        return html
    def _create_plain_text(
        self,
        papers: List[Article],
        news_api: List[Article],
        rss_news: List[Article],
        reddit_posts: List[Article],
        videos: List[Article],
        tools: List[Article],
        discussions: List[Article],
        hf_news: List[Article],
    ) -> str:
        """Create plain text version of the digest."""
        lines = [
            f"🤖 AI Daily Digest - {datetime.now().strftime('%B %d, %Y')}",
            "=" * 50,
            "",
        ]
        
        if rss_news:
            lines.append("🌐 COMMUNITY UPDATES")
            lines.append("-" * 30)
            for n in rss_news[:10]:
                lines.append(f"• {n.title} ({n.source})")
                if n.summary:
                    lines.append(f"  {n.summary}")
                lines.append(f"  {n.url}")
                lines.append("")

        if papers:
            lines.append("📄 RESEARCH PAPERS")
            lines.append("-" * 30)
            for p in papers[:10]:
                lines.append(f"• {p.title}")
                if p.summary:
                    lines.append(f"  {p.summary}")
                lines.append(f"  {p.url}")
                lines.append("")
        
        if news_api:
            lines.append("📰 GLOBAL HEADLINES")
            lines.append("-" * 30)
            for n in news_api[:10]:
                lines.append(f"• {n.title} ({n.source})")
                if n.summary:
                    lines.append(f"  {n.summary}")
                lines.append(f"  {n.url}")
                lines.append("")

        if reddit_posts:
            lines.append("👽 REDDIT DISCUSSIONS")
            lines.append("-" * 30)
            for r in reddit_posts[:5]:
                lines.append(f"• {r.title} ({r.source})")
                if r.summary:
                    lines.append(f"  {r.summary}")
                lines.append(f"  {r.url}")
                lines.append("")

        if hf_news:
            lines.append("🤗 HUGGING FACE HUB")
            lines.append("-" * 30)
            for h in hf_news[:10]:
                lines.append(f"• {h.title}")
                if h.summary:
                    lines.append(f"  {h.summary}")
                lines.append(f"  {h.url}")
                lines.append("")
        
        if videos:
            lines.append("📺 WATCH LIST")
            lines.append("-" * 30)
            for v in videos[:10]:
                lines.append(f"• {v.title} ({v.source})")
                if v.summary:
                    lines.append(f"  {v.summary}")
                lines.append(f"  {v.url}")
                lines.append("")

        if tools:
            lines.append("🚀 NEW TOOLS (Product Hunt)")
            lines.append("-" * 30)
            for t in tools[:10]:
                lines.append(f"• {t.title}")
                if t.summary:
                    lines.append(f"  {t.summary}")
                lines.append(f"  {t.url}")
                lines.append("")
        
        if discussions:
            lines.append("🔥 HACKER NEWS")
            lines.append("-" * 30)
            for d in discussions[:10]:
                lines.append(f"• {d.title}")
                if d.summary:
                    lines.append(f"  {d.summary}")
                lines.append(f"  {d.url}")
                lines.append("")
        
        lines.append("=" * 50)
        lines.append("Powered by AI News Agent")
        
        return "\n".join(lines)
    
    def send_test(self, to_email: str) -> bool:
        """Send a test email to verify setup."""
        message = MIMEMultipart()
        message['Subject'] = '✅ AI News Agent - Test Email'
        message['From'] = self.email
        message['To'] = to_email
        
        body = "This is a test email from AI News Agent.\n\nSetup successful! 🎉"
        message.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(message)
            
            print(f"✅ Test email sent to {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            print(f"❌ Authentication failed! Use an App Password.")
            print(f"   Get one at: https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            print(f"❌ Failed to send test email: {e}")
            return False


# Quick test
if __name__ == '__main__':
    import os
    
    email = os.getenv('SMTP_EMAIL')
    password = os.getenv('SMTP_PASSWORD')
    
    if email and password:
        client = SMTPClient(email=email, password=password)
        client.send_test(email)
    else:
        print("Set SMTP_EMAIL and SMTP_PASSWORD environment variables to test")
        print("\nFor Gmail App Password:")
        print("1. Enable 2FA: https://myaccount.google.com/security")
        print("2. Get App Password: https://myaccount.google.com/apppasswords")
