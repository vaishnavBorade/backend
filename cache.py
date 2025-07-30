import sqlite3
import hashlib
import pickle
import os
import asyncio
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")

DB_PATH = "resume_cache.db"
MAX_CACHE_ENTRIES = 500  # Adjust this as needed

async def init_db():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                hash TEXT PRIMARY KEY,
                vector BLOB
            )
        """)
        conn.commit()
        conn.close()

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

async def get_embedding_with_cache(text: str):
    text_hash = sha256(text)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT vector FROM embeddings WHERE hash = ?", (text_hash,))
    row = cursor.fetchone()
    if row:
        conn.close()
        return pickle.loads(row[0])  # Return cached

    # Compute if not cached
    embedding = model.encode(text)
    pickled = pickle.dumps(embedding)
    cursor.execute("INSERT OR REPLACE INTO embeddings (hash, vector) VALUES (?, ?)", (text_hash, pickled))
    conn.commit()

    # Enforce max cache size
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    count = cursor.fetchone()[0]
    if count > MAX_CACHE_ENTRIES:
        cursor.execute("""
            DELETE FROM embeddings WHERE hash NOT IN (
                SELECT hash FROM embeddings ORDER BY rowid DESC LIMIT ?
            )
        """, (MAX_CACHE_ENTRIES,))
        conn.commit()

    conn.close()
    return embedding
