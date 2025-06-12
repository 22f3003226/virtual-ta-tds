import json
import glob
import os
import frontmatter
from bs4 import BeautifulSoup

def rewrite_markdown_url(url: str) -> str:
    prefix = "https://tds.s-anand.net/"
    if url.startswith(prefix) and url.endswith(".md"):
        tail = url[len(prefix):].split("?",1)[0].split("#",1)[0]
        slug = os.path.splitext(tail)[0].lower().replace("_","-")
        return f"{prefix}#/{slug}"
    return url

discourse_data = []

# 1️⃣ Gather Discourse threads
for fp in glob.glob('downloaded_threads/topic_*.json'):
    with open(fp, 'r', encoding='utf-8') as f:
        thread = json.load(f)
    tid = thread.get("id"); slug = thread.get("slug")
    base = "https://discourse.onlinedegree.iitm.ac.in"
    for post in thread['post_stream']['posts']:
        num = post.get("post_number")
        url = f"{base}/t/{slug}/{tid}/{num}"
        discourse_data.append({
            "url": url,
            "author": post.get("name"),
            "created_at": post.get("created_at"),
            "text": post.get("cooked"),
            "topic_title": slug,
            "source": "discourse"
        })

# 2️⃣ Gather Markdown files
for fp in glob.glob('markdown_files/*.md'):
    post = frontmatter.load(fp)
    raw_url = post.get("original_url", "unknown")
    url = rewrite_markdown_url(raw_url)  # Transform URL here
    title = post.get("title", os.path.basename(fp).replace('.md',''))
    created = post.get("downloaded_at", "unknown")
    html = post.content
    text = BeautifulSoup(html, 'html.parser').get_text(separator="\n")
    discourse_data.append({
        "url": url,
        "author": "markdown",
        "created_at": created,
        "text": text,
        "topic_title": title,
        "source": "markdown"
    })

with open('consolidated_data.json', 'w', encoding='utf-8') as f:
    json.dump(discourse_data, f, ensure_ascii=False, indent=2)

print(f"Consolidated {len(discourse_data)} documents.")