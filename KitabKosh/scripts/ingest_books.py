import json
import sys
import os

# Build the absolute path from the project root (Claude's fix #7)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

from sentence_transformers import SentenceTransformer
from app.services.vector_store import db_manager

# Force the embedding model to the CPU so it doesn't fight Ollama for VRAM (Claude's fix #6)
print("Loading multilingual model on CPU...")
model = SentenceTransformer('intfloat/multilingual-e5-base', device="cuda")

data_path = os.path.join(BASE_DIR, "data", "books_enriched.json")
print(f"Loading enriched JSON data from {data_path}...")

# Force UTF-8 for Windows so Hindi characters don't crash the script (Claude's fix #1)
with open(data_path, "r", encoding="utf-8") as f:
    books = json.load(f)

documents = []
metadatas = []
ids = []
texts_for_embedding = []

print("Structuring data...")
for book in books:
    if "enriched_text" in book:
        clean_text = book["enriched_text"]
        texts_for_embedding.append("passage: " + clean_text)
        documents.append(clean_text)
        ids.append(f"book_{book['id']}")
        
        # Safely handle nulls and include extra fields (Claude's fix #3)
        metadatas.append({
            "title": str(book.get("title") or ""), 
            "author": str(book.get("author") or ""),
            "edition": str(book.get("edition") or ""),
            "publisher": str(book.get("publisher") or ""),
            "year": str(book.get("year") or ""),
            "accession_nos": ", ".join(book.get("accession_nos") or [])
        })

batch_size = 200
total_books = len(documents)

print(f"Vectorizing and inserting {total_books} books into ChromaDB...")

for i in range(0, total_books, batch_size):
    batch_docs = documents[i : i + batch_size]
    batch_meta = metadatas[i : i + batch_size]
    batch_ids = ids[i : i + batch_size]
    batch_embed_texts = texts_for_embedding[i : i + batch_size]
    
    # Normalize for cosine similarity and batch size for RAM control (Claude's fixes #5 & #7)
    batch_embeddings = model.encode(
        batch_embed_texts, 
        normalize_embeddings=True, 
        batch_size=32, 
        show_progress_bar=True
    ).tolist()
    
    db_manager.add_books(
        embeddings=batch_embeddings,
        documents=batch_docs,
        ids=batch_ids,
        metadatas=batch_meta
    )
    
    print(f"Successfully inserted batch {i} to {min(i + batch_size, total_books)}")

print("Database ingestion completely finished!")