
import feedparser
import requests

feeds = [
    # OpenAI Alternatives
    {'name': 'OpenAI (Feed)', 'url': 'https://openai.com/feed'},
    {'name': 'OpenAI (Blog RSS)', 'url': 'https://openai.com/blog/rss.xml'},
    {'name': 'OpenAI (Search Proxy)', 'url': 'https://rsshub.app/openai/blog'},
    
    # DeepMind Alternatives
    {'name': 'DeepMind (Feedburner)', 'url': 'https://feeds.feedburner.com/DeepMind'},
    {'name': 'DeepMind (Basic)', 'url': 'https://deepmind.com/blog/feed/basic/'},
    
    # AWS Alternatives
    {'name': 'AWS ML (Feedburner)', 'url': 'http://feeds.feedburner.com/amazon/AWSAI'},
    
    # NVIDIA
    {'name': 'NVIDIA Developer', 'url': 'https://developer.nvidia.com/blog/feed/'},
    {'name': 'NVIDIA Blog', 'url': 'http://feeds.feedburner.com/nvidiablog'},
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

print(f"🔍 Testing {len(feeds)} RSS Feeds...\n")

for feed in feeds:
    print(f"👉 Testing {feed['name']}...")
    try:
        response = requests.get(feed['url'], headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            d = feedparser.parse(response.content)
            print(f"   Entries: {len(d.entries)}")
            if d.entries:
                print(f"   Latest: {d.entries[0].title}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    print("-" * 40)
