
import feedparser
import requests

feeds = [
    # {'name': 'OpenAI Blog', 'url': 'https://openai.com/news/rss.xml'},
    {'name': 'OpenAI Blog (Alt)', 'url': 'https://openai.com/index/rss.xml'},
    {'name': 'Anthropic Research', 'url': 'https://www.anthropic.com/research/feed'},
    {'name': 'Anthropic (Community)', 'url': 'https://raw.githubusercontent.com/Olshansk/rss-feeds/main/feeds/feed_anthropic_research.xml'},
    {'name': 'DeepMind', 'url': 'https://deepmind.google/discover/blog/rss.xml'},
    {'name': 'AWS ML', 'url': 'https://aws.amazon.com/blogs/machinelearning/feed/'},
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"🔍 Testing {len(feeds)} RSS Feeds...\n")

for feed in feeds:
    print(f"👉 Testing {feed['name']}...")
    try:
        # 1. Check raw response
        response = requests.get(feed['url'], headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Failed to fetch: {response.status_code}")
            continue

        # 2. Parse feed
        d = feedparser.parse(response.content)
        if d.bozo:
             print(f"   ⚠️  Parse Warning: {d.bozo_exception}")
        
        print(f"   Entries: {len(d.entries)}")
        if d.entries:
            print(f"   Latest: {d.entries[0].title}")
        else:
            print("   ⚠️  No entries found.")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print("-" * 40)
