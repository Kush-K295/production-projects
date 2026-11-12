import argparse
import json
import os
import time

import requests

# ---------- paths ----------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_base.json')
OUTPUT_FILE = os.path.join(BASE_DIR, 'data', 'books_enriched.json')

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.1:8b"

# enrich_version 2 = Hindi-aware prompt. Hindi books without it get redone.
HINDI_VERSION = 2
GENERAL_VERSION = 1
SAVE_EVERY = 50

# ---------- structured output schemas (Ollama enforces these) ----------
KEYWORDS = {"type": "array", "items": {"type": "string"}, "minItems": 5, "maxItems": 5}

GENERAL_SCHEMA = {
    "type": "object",
    "properties": {"summary": {"type": "string"}, "keywords": KEYWORDS},
    "required": ["summary", "keywords"],
}
HINDI_SCHEMA = {
    "type": "object",
    "properties": {
        "title_english": {"type": "string"},
        "summary": {"type": "string"},
        "keywords": KEYWORDS,
    },
    "required": ["title_english", "summary", "keywords"],
}


# ---------- prompts ----------
def general_prompt(book):
    return f"""You are a university librarian. Based on this book information:
Title: {book.get('title') or 'N/A'}
Author: {book.get('author') or 'N/A'}
Publisher: {book.get('publisher') or 'N/A'}

Write a 2-sentence summary of what this book teaches, and 5 subject keywords.
If you do not recognise the specific book, base the answer only on the title and do not invent details."""


def hindi_prompt(book):
    return f"""You are a university librarian in India. The book below is from the library's HINDI SECTION.
Its title is most likely Hindi written in English letters (romanized Hindi), not English.

Title: {book.get('title') or 'N/A'}
Author: {book.get('author') or 'N/A'}
Publisher: {book.get('publisher') or 'N/A'}

Do this:
1. title_english: translate the title into English, word by word. Example: "Ram ki Kahani" means "Ram's Story".
2. summary: write 2 sentences about what the book is about, in English.
3. keywords: 5 English subject keywords that a student might search for.

If you are not sure what the book is about, base the summary only on the meaning of the title and do not invent plot, characters or facts."""


# ---------- helpers ----------
def dot(text):
    """Make sure a piece of text ends with exactly one period."""
    text = (text or "").strip().rstrip(".").strip()
    return text + "." if text else ""


def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_json(data, path):
    tmp = path + ".tmp"
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    os.replace(tmp, path)  # never leaves a half-written file


def needs_work(base_book, done):
    """done = existing enriched record for this id (or None)."""
    if done is None or not done.get("enriched_text"):
        return True
    if base_book.get("is_hindi") and done.get("enrich_version") != HINDI_VERSION:
        return True
    return False


def bad_summary(summary, title):
    """True for useless model output: too short, cut off, or just the title again."""
    s = (summary or "").strip()
    if len(s) < 60 or s[-1] not in '.!?)"\'':
        return True
    return s.rstrip(".").lower() == (title or "").strip().rstrip(".").lower()


def generate(book):
    hindi = bool(book.get("is_hindi"))
    for temperature in (0.2, 0.6, 0.9):        # retry with more variety if the answer is useless
        payload = {
            "model": MODEL_NAME,
            "prompt": hindi_prompt(book) if hindi else general_prompt(book),
            "stream": False,
            "format": HINDI_SCHEMA if hindi else GENERAL_SCHEMA,
            "options": {"temperature": temperature, "num_ctx": 2048},
            "keep_alive": "30m",
        }
        try:
            r = requests.post(OLLAMA_URL, json=payload, timeout=180)
            r.raise_for_status()
            data = json.loads(r.json()["response"])

            summary = data["summary"].strip()
            keywords = [k.strip().strip(".") for k in data["keywords"] if k.strip()]
            if bad_summary(summary, book.get("title")) or not keywords:
                continue                        # try again

            parts = [f"Title: {dot(book['title'])}"]
            title_en = (data.get("title_english") or "").strip() if hindi else None
            if hindi and title_en:
                parts.append(f"English title: {dot(title_en)}")
            if book.get("author"):
                parts.append(f"Author: {dot(book['author'])}")
            parts.append(f"Summary: {summary}")
            parts.append(f"Keywords: {', '.join(keywords)}")

            return {                                   # same keys, same order for every book
                "summary": summary,
                "keywords": keywords,
                "title_english": title_en if hindi else None,
                "enriched_text": " ".join(parts),
                "enrich_version": HINDI_VERSION if hindi else GENERAL_VERSION,
            }
        except Exception as e:
            print(f"  ERROR on id {book['id']} '{book.get('title')}': {e}")
            return None
    print(f"  GAVE UP on id {book['id']} '{book.get('title')}' (3 bad answers) - will retry next run")
    return None


# ---------- main ----------
def main(hindi_only, limit):
    base_books = load_json(INPUT_FILE)
    enriched = {b["id"]: b for b in load_json(OUTPUT_FILE)}   # keyed by ID, not title

    # keep section flags on already-enriched records too
    for b in base_books:
        if b["id"] in enriched:
            enriched[b["id"]]["sections"] = b.get("sections")
            enriched[b["id"]]["is_hindi"] = b.get("is_hindi", False)

    todo = [b for b in base_books if needs_work(b, enriched.get(b["id"]))]
    if hindi_only:
        todo = [b for b in todo if b.get("is_hindi")]
    todo.sort(key=lambda b: (not b.get("is_hindi"), b["id"]))   # Hindi first, so you can check them early
    if limit:
        todo = todo[:limit]

    n_hindi = sum(1 for b in todo if b.get("is_hindi"))
    print(f"{len(enriched)} already done. {len(todo)} to process ({n_hindi} Hindi).")

    unsaved = 0
    try:
        for i, book in enumerate(todo, 1):
            t0 = time.time()
            result = generate(book)
            if result is None:
                continue                       # stays in the to-do list for the next run
            record = dict(book)
            record.update(result)
            enriched[book["id"]] = record
            unsaved += 1
            tag = "HI" if book.get("is_hindi") else "  "
            print(f"[{i}/{len(todo)}] {tag} {book['title'][:60]}  ({time.time() - t0:.1f}s)")

            if unsaved >= SAVE_EVERY:
                save_json([enriched[k] for k in sorted(enriched)], OUTPUT_FILE)
                print(f"  checkpoint saved ({len(enriched)} total)")
                unsaved = 0
    except KeyboardInterrupt:
        print("\nPaused (Ctrl+C).")
    finally:
        if unsaved or not os.path.exists(OUTPUT_FILE):
            save_json([enriched[k] for k in sorted(enriched)], OUTPUT_FILE)
            print(f"Saved {len(enriched)} books.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--hindi-only", action="store_true", help="only (re)do the 95 Hindi-section books")
    ap.add_argument("--limit", type=int, default=0, help="process at most N books (for testing)")
    args = ap.parse_args()
    main(args.hindi_only, args.limit)
