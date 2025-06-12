import os
import re
import json
import numpy as np
import faiss
import requests
from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

API_KEY  = os.getenv("AIPIPE_TOKEN")
API_BASE = os.getenv("API_BASE_URL")
if not API_KEY or not API_BASE:
    raise RuntimeError("AIPIPE_TOKEN and API_BASE_URL must be set in .env")

model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.read_index('vector_index.faiss')
with open('chunked_data_with_embeddings.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

def normalize_discourse_url(url: str) -> str:
    if "discourse.onlinedegree.iitm.ac.in" in url:
        m = re.match(r"(https://discourse\.onlinedegree\.iitm\.ac\.in/t/[^/]+/\d+)(?:/\d+)?/?$", url)
        if m:
            return m.group(1)
    return url

def rewrite_markdown_url(url: str) -> str:
    prefix = "https://tds.s-anand.net/"
    if url.startswith(prefix) and url.endswith(".md"):
        tail = url[len(prefix):].split("?",1)[0].split("#",1)[0]
        slug = os.path.splitext(tail)[0].lower().replace("_","-")
        return f"{prefix}#/{slug}"
    return url

@app.route('/api', methods=['POST'])
def answer_question():
    data = request.get_json(force=True)
    question      = data.get('question', '').strip()
    provided_link = data.get('link', '').strip()

    if not question:
        return jsonify(answer="No question provided.", links=[]), 400

    q_emb, = model.encode([question])
    _, idxs = index.search(np.array([q_emb], dtype=np.float32), 5)
    selected = idxs[0].tolist()

    context = ""
    for i, idx in enumerate(selected, 1):
        c = chunks[idx]
        context += f"{i}. [Source: {c['url']}] {c['content']}\n\n"

    prompt = (
        f"Context:\n{context}\n"
        f"Question: {question}\n\n"
        "Answer strictly from the context above. If unknown, say so. "
        "Return exactly JSON {\"answer\":\"...\",\"used_sources\":[...]}. No URLs."
    )
    resp = requests.post(
        API_BASE,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0}
    )
    resp.raise_for_status()
    content = resp.json()['choices'][0]['message']['content']
    try:
        out = json.loads(content)
        answer = out.get("answer", "")
        used   = out.get("used_sources", [])
        if not isinstance(used, list):
            used = []
    except json.JSONDecodeError:
        return jsonify(answer="Failed to parse LLM response.", links=[]), 500

    links = []
    for num in used:
        if 1 <= num <= len(selected):
            raw = chunks[selected[num-1]]['url']
            url = normalize_discourse_url(raw)
            url = rewrite_markdown_url(url)
            links.append({"url": url, "text": chunks[selected[num-1]]['content'][:200] + "..."})

    if provided_link:
        norm = normalize_discourse_url(provided_link)
        norm = rewrite_markdown_url(norm)
        if not any(l['url'] == norm for l in links):
            links.append({"url": norm, "text": "Provided reference link..."})

    # Fallback: if no provided_link, append first chunk URL
    if not provided_link and links:
        fallback = links[0]['url']
        if not any(l['url'] == fallback for l in links):
            links.append({"url": fallback, "text": "Fallback reference link..."})

    return jsonify(answer=answer, links=links)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
