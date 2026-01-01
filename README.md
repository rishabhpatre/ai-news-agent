# AI News Agent

An autonomous Python agent that scans the web daily for the latest LLM, AI tools, and agentic AI content, then sends a beautifully formatted email digest to your Gmail.

## Features

- 📰 **Multi-Source Aggregation**: ArXiv papers, NewsAPI, RSS feeds, Hacker News
- 🤖 **AI-Powered Summaries**: Uses LLM for intelligent content summarization
- 🔄 **Smart Deduplication**: Removes duplicate articles across sources
- 📧 **Beautiful Email Digests**: Mobile-responsive HTML emails
- ⏰ **Daily Scheduling**: Configurable send time

## Quick Start

### 1. Install Dependencies

```bash
cd ai-news-agent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Setup Gmail OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the Gmail API
4. Go to Credentials → Create Credentials → OAuth client ID
5. Select "Desktop app" as application type
6. Download the JSON and save as `config/credentials/credentials.json`

### 4. First Run (OAuth Authorization)

```bash
python agent.py
```

This will open a browser for Gmail authorization. After authorizing, the token is saved locally.

### 5. Schedule Daily Runs

**Option A: Using the built-in scheduler**
```bash
python scheduler.py
```

**Option B: Using system cron (Linux/Mac)**
```bash
# Edit crontab
crontab -e

# Add this line for 8:00 AM daily
0 8 * * * cd /path/to/ai-news-agent && python agent.py
```

## Configuration

Edit `.env` file:

```env
# Required
RECIPIENT_EMAIL=your.email@gmail.com

# Optional - for LLM summaries
OPENAI_API_KEY=sk-...
# OR
GEMINI_API_KEY=...

# Optional - for more news sources
NEWS_API_KEY=...

# Schedule (24-hour format)
SEND_TIME=08:00
```

## Usage

```bash
# Run once (sends email immediately)
python agent.py

# Dry run (preview without sending)
python agent.py --dry-run

# Run with scheduler (ongoing)
python scheduler.py
```

## Project Structure

```
ai-news-agent/
├── config/
│   ├── settings.py          # Configuration management
│   └── credentials/          # OAuth tokens (gitignored)
├── sources/
│   ├── arxiv_source.py       # ArXiv research papers
│   ├── newsapi_source.py     # NewsAPI.org integration
│   ├── rss_source.py         # RSS feed parser
│   └── hackernews_source.py  # Hacker News API
├── processing/
│   ├── deduplicator.py       # Remove duplicate articles
│   └── summarizer.py         # AI-powered summarization
├── email_client/
│   ├── gmail_client.py       # Gmail API OAuth2 client
│   └── templates/
│       └── digest.html       # HTML email template
├── agent.py                  # Main orchestrator
├── scheduler.py              # Daily scheduling
└── requirements.txt
```

## ☁️ Cloud Deployment (Daily Digests Without Your Laptop)

The easiest way to run daily digests automatically is **GitHub Actions** - completely free!

### Step 1: Push to GitHub

```bash
cd /Applications/AntigravityProjects/ai-news-agent
git init
git add .
git commit -m "Initial commit"
gh repo create ai-news-agent --private --push
```

### Step 2: Add Secrets

Go to your GitHub repo → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:
| Secret Name | Value |
|-------------|-------|
| `RECIPIENT_EMAIL` | your.email@gmail.com |
| `SMTP_EMAIL` | your.email@gmail.com |
| `SMTP_PASSWORD` | your-app-password |
| `NEWS_API_KEY` | your-newsapi-key |

### Step 3: Done!

The workflow runs daily at **8:00 AM IST**. You can also trigger it manually from the Actions tab.

---

## License

MIT
