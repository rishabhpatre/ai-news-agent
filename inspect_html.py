from agent import AINewsAgent
from config import settings
import os

agent = AINewsAgent()
content = agent.collect_content(days_back=1)
processed = agent.process_content(content)

# Manually call _render_template to get the HTML
html = agent.email_client._render_template(
    papers=processed['papers'],
    news_api=processed['news_api'],
    rss_news=processed['rss_news'],
    reddit_posts=processed['reddit_posts'],
    videos=processed['videos'],
    tools=processed['tools'],
    discussions=processed['discussions'],
    hf_news=processed['hf_news']
)

with open("debug_email.html", "w") as f:
    f.write(html)

print(f"HTML saved to debug_email.html. Items: {len(processed['news_api'])}")
if "Global Headlines" in html:
    print("Found 'Global Headlines' in HTML!")
else:
    print("'Global Headlines' NOT FOUND in HTML!")

