import json
import sys
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

import torch
from sentence_transformers import SentenceTransformer
from app.services.vector_store import Manager

# Enrichment is finished, so the GPU is free: use it if it's there, else fall back to CPU.
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Loading multilingual model on {device}...")
model = SentenceTransformer('BAAI/bge-m3', device=device)

data_path = os.path.join(BASE_DIR, "data", "books_enriched.json")
print(f"Loading enriched JSON data from {data_path}...")
with open(data_path, "r", encoding="utf-8") as f:
    books = json.load(f)

documents = []
metadatas = []
ids = []
texts_for_embedding = []

print("Structuring data...")
for book in books:
    # Fall back to the plain base string if a book ever has no enriched text
    clean_text = book.get("enriched_text") or book.get("base_string")
    if not clean_text:
        print(f"  skipping id {book.get('id')}: no text at all")
        continue

    # e5 models need the "passage: " prefix on stored text (and "query: " on search queries)
    texts_for_embedding.append(clean_text)
    documents.append(clean_text)
    ids.append(f"book_{book['id']}")
    metadatas.append({
        "title": str(book.get("title") or ""),
        "author": str(book.get("author") or ""),
        "edition": str(book.get("edition") or ""),
        "publisher": str(book.get("publisher") or ""),
        "year": str(book.get("year") or ""),
        "accession_nos": ", ".join(book.get("accession_nos") or []),
    })

batch_size = 200
encode_batch = 64 if device == "cuda" else 32
total_books = len(documents)

print(f"Vectorizing and inserting {total_books} books into ChromaDB...")

for i in range(0, total_books, batch_size):
    batch_embeddings = model.encode(
        texts_for_embedding[i : i + batch_size],
        normalize_embeddings=True,      # needed for cosine similarity
        batch_size=encode_batch,
        show_progress_bar=False,
    ).tolist()

    Manager.addBooks(
        embeddings=batch_embeddings,
        documents=documents[i : i + batch_size],
        ids=ids[i : i + batch_size],
        metadatas=metadatas[i : i + batch_size],
    )
    print(f"Inserted {min(i + batch_size, total_books)}/{total_books}")

print("Database ingestion completely finished!")
