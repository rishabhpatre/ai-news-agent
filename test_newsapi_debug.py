import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from sources.newsapi_source import NewsAPISource
from config.settings import Settings

settings = Settings()
print(f"DEBUG: NewsAPI Key length: {len(settings.news_api_key) if settings.news_api_key else 'None'}")

if settings.news_api_key:
    source = NewsAPISource(settings.news_api_key)
    try:
        articles = source.fetch(days_back=3)
        print(f"DEBUG: Successfully fetched {len(articles)} articles")
        for article in articles[:3]:
            print(f"DEBUG: Article: {article.title} - {article.source}")
    except Exception as e:
        print(f"DEBUG: Fetch error: {e}")
else:
    print("DEBUG: No NewsAPI key found")
