from agent import AINewsAgent
from config import settings

agent = AINewsAgent()
content = agent.collect_content(days_back=1)
processed = agent.process_content(content)

print("\n--- DEBUG: Dictionary Keys ---")
print(processed.keys())

for key, items in processed.items():
    print(f"Key: {key}, Count: {len(items)}")
    if len(items) > 0:
        print(f"  First item title: {items[0].title}")

print("\n--- DEBUG: NewsAPI Check ---")
if 'news_api' in processed:
    print(f"news_api found! Count: {len(processed['news_api'])}")
else:
    print("news_api NOT FOUND in processed dictionary!")

