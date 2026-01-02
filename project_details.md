# AI News Agent - Project Overview

## 🚀 One-Liner
A "Zero-Maintenance" Python agent that automates your daily AI reading list by aggregating, filtering, and delivering a compact email digest every morning.

## 🛠️ Tech Stack
*   **Language:** Python 3.10+
*   **Hosting/Automation:** GitHub Actions (Running on a daily cron schedule)
*   **Email:** SMTP (Gmail) + Jinja2 Templates (HTML rendering)
*   **Key Libraries:** `feedparser` (RSS), `arxiv` (Research), `requests` (API), `fuzzywuzzy` (Deduplication)
*   **Cost:** $0 (Runs entirely on free tier infrastructure)

## 📡 Data Sources (The "Input")
The agent scans 7 distinct verticals to ensure full coverage:
1.  **Research:** ArXiv API (Categories: cs.AI, cs.LG, cs.CL)
2.  **Global News:** NewsAPI (TechCrunch, The Verge, Wired)
3.  **YouTube:** RSS feeds from top channels (Two Minute Papers, AI Explained, etc.)
4.  **Community:** RSS blogs (OpenAI, Google AI, Anthropic, Hugging Face)
5.  **Social:** Reddit (r/MachineLearning, r/LocalLLaMA) & Hacker News
6.  **Tools:** Product Hunt RSS
7.  **Models:** Hugging Face Daily Papers

## 🧠 Smart Processing (The "Brain")
*   **Tiered Lookback:** Scans last 2 days for high-frequency sources (News) and 7 days for slower sources (YouTube/Blogs) to ensure nothing is missed over weekends.
*   **Deduplication:** Uses fuzzy string matching to remove duplicate stories covered by multiple outlets.
*   **Relevance Scoring:** keyword-based scoring system (e.g., "LLM", "Agent", "Transformer") to prioritize signal over noise.
*   **Zero LLM Dependency:** Deliberately designed *without* LLM summarization to eliminate API costs and latency. It relies on source abstracts and metadata.

## 🎨 The "Compact" Design (The "Output")
Solved the "newsletter fatigue" problem with a hybrid layout:
*   **Quick Links (TOC):** Jump links at the top (Papers • Community • Headlines • Watch List).
*   **Top 5 Highlights:** The most relevant 5 items in each category are shown with full details (Source, Title, 3-line Summary).
*   **Compact List:** Everything else is rolled up into a "More X" section as a single-line dense list.
*   **Visuals:** YouTube videos display thumbnail images in a 2-column grid.
*   **Brevity:** CSS line-clamping enforces a strict 3-line limit on all text to keep the email scannable.

##  workflow (How it runs)
1.  **Trigger:** GitHub Actions wakes up at 7:00 AM UTC.
2.  **Collect:** Scripts fire off parallel requests to all APIs/RSS feeds.
3.  **Process:** Data is cleaned, sorted by relevance score, and deduplicated.
4.  **Render:** Jinja2 injects data into the `digest.html` template.
5.  **Send:** SMTP client dispatches the HTML email to subscribers.
