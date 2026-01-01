"""
Gmail client for sending email digests.
Uses OAuth2 for authentication with the Gmail API.
"""

import os
import pickle
import base64
from pathlib import Path
from typing import Optional, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from jinja2 import Environment, FileSystemLoader

from sources.arxiv_source import Article


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.send']


class GmailClient:
    """Gmail client for sending email digests."""
    
    def __init__(
        self,
        credentials_path: Path,
        token_path: Path,
        template_dir: Optional[Path] = None,
    ):
        """
        Initialize Gmail client.
        
        Args:
            credentials_path: Path to OAuth credentials.json file.
            token_path: Path to save/load the auth token.
            template_dir: Directory containing email templates.
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.template_dir = template_dir or Path(__file__).parent / 'templates'
        
        self._service = None
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
        )
    
    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.
        
        Will open a browser for initial authorization if needed.
        
        Returns:
            True if authentication successful.
        """
        creds = None
        
        # Load existing token
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    creds = None
            
            if not creds:
                if not self.credentials_path.exists():
                    print(f"ERROR: Credentials file not found at {self.credentials_path}")
                    print("Please download OAuth credentials from Google Cloud Console")
                    return False
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save token for future use
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build Gmail service
        self._service = build('gmail', 'v1', credentials=creds)
        return True
    
    def send_digest(
        self,
        to_email: str,
        papers: List[Article],
        news: List[Article],
        discussions: List[Article],
        dry_run: bool = False,
    ) -> bool:
        """
        Send the daily AI news digest email.
        
        Args:
            to_email: Recipient email address.
            papers: List of research paper articles.
            news: List of news articles.
            discussions: List of HN discussions.
            dry_run: If True, print email instead of sending.
            
        Returns:
            True if email sent successfully.
        """
        # Render HTML template
        html_content = self._render_template(
            papers=papers,
            news=news,
            discussions=discussions,
        )
        
        # Create email message
        subject = f"🤖 AI Daily Digest - {datetime.now().strftime('%B %d, %Y')}"
        
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['To'] = to_email
        message['From'] = 'me'  # Gmail API handles this
        
        # Plain text fallback
        plain_text = self._create_plain_text(papers, news, discussions)
        message.attach(MIMEText(plain_text, 'plain'))
        
        # HTML content
        message.attach(MIMEText(html_content, 'html'))
        
        if dry_run:
            print(f"\n{'='*60}")
            print(f"DRY RUN - Email Preview")
            print(f"{'='*60}")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"{'='*60}")
            print(plain_text)
            print(f"{'='*60}\n")
            return True
        
        # Send email
        if not self._service:
            if not self.authenticate():
                return False
        
        try:
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            self._service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            print(f"✅ Digest sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def _render_template(
        self,
        papers: List[Article],
        news: List[Article],
        discussions: List[Article],
    ) -> str:
        """Render the HTML email template."""
        try:
            template = self._jinja_env.get_template('digest.html')
            return template.render(
                date=datetime.now().strftime('%B %d, %Y'),
                papers=papers,
                news=news,
                discussions=discussions,
                total_count=len(papers) + len(news) + len(discussions),
            )
        except Exception as e:
            print(f"Template rendering failed: {e}")
            # Fallback to basic HTML
            return self._create_basic_html(papers, news, discussions)
    
    def _create_basic_html(
        self,
        papers: List[Article],
        news: List[Article],
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
                html += f'<li><a href="{p.url}">{p.title}</a><br><small>{p.summary[:100]}...</small></li>'
            html += "</ul>"
        
        if news:
            html += "<h2>📰 Industry News</h2><ul>"
            for n in news[:10]:
                html += f'<li><a href="{n.url}">{n.title}</a> ({n.source})</li>'
            html += "</ul>"
        
        if discussions:
            html += "<h2>🔥 Trending Discussions</h2><ul>"
            for d in discussions[:5]:
                html += f'<li><a href="{d.url}">{d.title}</a><br><small>{d.summary}</small></li>'
            html += "</ul>"
        
        html += "</body></html>"
        return html
    
    def _create_plain_text(
        self,
        papers: List[Article],
        news: List[Article],
        discussions: List[Article],
    ) -> str:
        """Create plain text version of the digest."""
        lines = [
            f"🤖 AI Daily Digest - {datetime.now().strftime('%B %d, %Y')}",
            "=" * 50,
            "",
        ]
        
        if papers:
            lines.append("📄 RESEARCH PAPERS")
            lines.append("-" * 30)
            for p in papers[:10]:
                lines.append(f"• {p.title}")
                lines.append(f"  {p.url}")
                if p.authors:
                    lines.append(f"  Authors: {', '.join(p.authors[:3])}")
                lines.append("")
        
        if news:
            lines.append("📰 INDUSTRY NEWS")
            lines.append("-" * 30)
            for n in news[:10]:
                lines.append(f"• {n.title} ({n.source})")
                lines.append(f"  {n.url}")
                lines.append("")
        
        if discussions:
            lines.append("🔥 TRENDING DISCUSSIONS")
            lines.append("-" * 30)
            for d in discussions[:5]:
                lines.append(f"• {d.title}")
                lines.append(f"  {d.summary}")
                lines.append(f"  {d.url}")
                lines.append("")
        
        lines.append("=" * 50)
        lines.append("Powered by AI News Agent")
        
        return "\n".join(lines)
    
    def send_test(self, to_email: str) -> bool:
        """Send a test email to verify setup."""
        message = MIMEText("This is a test email from AI News Agent. Setup successful! 🎉")
        message['Subject'] = '✅ AI News Agent - Test Email'
        message['To'] = to_email
        message['From'] = 'me'
        
        if not self._service:
            if not self.authenticate():
                return False
        
        try:
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            self._service.users().messages().send(
                userId='me',
                body={'raw': raw}
            ).execute()
            print(f"✅ Test email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send test email: {e}")
            return False


# Quick test
if __name__ == '__main__':
    from config import settings
    
    client = GmailClient(
        credentials_path=settings.credentials_path,
        token_path=settings.token_path,
    )
    
    if settings.recipient_email:
        # Test authentication
        if client.authenticate():
            print("✅ Gmail authentication successful!")
            # client.send_test(settings.recipient_email)
    else:
        print("Set RECIPIENT_EMAIL in .env to test")
