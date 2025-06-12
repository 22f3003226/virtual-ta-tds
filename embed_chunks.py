import json
from sentence_transformers import SentenceTransformer

data = json.load(open('chunked_data.json','r',encoding='utf-8'))
model = SentenceTransformer('all-MiniLM-L6-v2')

texts = [d['content'] for d in data]
embs = model.encode(texts, show_progress_bar=True)

for i, d in enumerate(data):
    d['embedding'] = embs[i].tolist()

with open('chunked_data_with_embeddings.json','w',encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Embedded {len(data)} chunks.")
