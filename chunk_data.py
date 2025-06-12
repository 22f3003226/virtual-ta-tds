import json
import re
from bs4 import BeautifulSoup

def split_into_chunks(text, chunk_size=200):
    import re
    words = re.findall(r'\w+', text)
    chunks, cur, cnt = [], [], 0
    for w in words:
        cur.append(w); cnt += 1
        if cnt >= chunk_size:
            chunks.append(' '.join(cur)); cur, cnt = [], 0
    if cur: chunks.append(' '.join(cur))
    return chunks

def normalize_discourse_url(url):
    # Keep https://.../topic_id, strip trailing /post_number only
    if "discourse.onlinedegree.iitm.ac.in" in url:
        m = re.match(r"(https://discourse\.onlinedegree\.iitm\.ac\.in/t/[^/]+/\d+)(?:/\d+)?/?$", url)
        if m: return m.group(1)
    return url

data = json.load(open('consolidated_data.json','r',encoding='utf-8'))
out = []
for item in data:
    raw = item['url']
    if "discourse.onlinedegree.iitm.ac.in" in raw:
        url = normalize_discourse_url(raw)
    else:
        url = raw

    text = BeautifulSoup(item['text'], 'html.parser').get_text()
    for i, chunk in enumerate(split_into_chunks(text)):
        out.append({
            "url": url,
            "source": item['source'],
            "author": item['author'],
            "created_at": item['created_at'],
            "topic_title": item['topic_title'],
            "content": chunk,
            "chunk_id": f"{item['source']}_{url.split('/')[-1]}_{i}"
        })

with open('chunked_data.json','w',encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=2)

print(f"Created {len(out)} chunks.")
