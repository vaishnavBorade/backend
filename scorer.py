import faiss
import numpy as np

def build_faiss_index(vectors):
    d = len(vectors[0])
    index = faiss.IndexFlatL2(d)
    index.add(np.array(vectors))
    return index

def search_top_k(index, query_vec, k=10):
    D, I = index.search(np.array([query_vec]), k)
    return I[0], D[0]
