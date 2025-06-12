import json
import numpy as np
import faiss

data = json.load(open('chunked_data_with_embeddings.json','r',encoding='utf-8'))
X = np.array([d['embedding'] for d in data], dtype=np.float32)
dim = X.shape[1]
index = faiss.IndexFlatL2(dim)
index.add(X)
faiss.write_index(index, 'vector_index.faiss')

print(f"FAISS index with {index.ntotal} vectors.")
