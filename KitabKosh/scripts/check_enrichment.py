"""
Checks data/books_enriched.json against data/books_base.json.
Run from the project root:  python scripts/check_enrichment.py
Read-only: it never changes your files.
"""
import json
import os
import re
from collections import Counter

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BASE = os.path.join(BASE_DIR, 'data', 'books_base.json')
ENRICHED = os.path.join(BASE_DIR, 'data', 'books_enriched.json')
HINDI_VERSION = 2


def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def show(label, items, n=8):
    print(f"  {label}: {len(items)}")
    for x in items[:n]:
        print("     -", x)
    if len(items) > n:
        print(f"     ... and {len(items) - n} more")


def main():
    base = load(BASE)
    enriched = load(ENRICHED)
    base_ids = {b["id"] for b in base}
    by_id = {b["id"]: b for b in base}

    id_counts = Counter(b["id"] for b in enriched)
    done = {b["id"]: b for b in enriched}

    missing = [b for b in base if b["id"] not in done or not done[b["id"]].get("enriched_text")]
    hindi_total = [b for b in base if b.get("is_hindi")]
    hindi_not_redone = [b for b in hindi_total
                        if b["id"] in done and done[b["id"]].get("enrich_version") != HINDI_VERSION]
    hindi_missing = [b for b in hindi_total if b["id"] not in done]
    duplicates = [i for i, c in id_counts.items() if c > 1]
    unknown = [i for i in done if i not in base_ids]
    short = [b for b in enriched if len((b.get("enriched_text") or "")) < 80]
    chatty_re = re.compile(r"(?<![a-z])(here is|here's|sure,|as an ai)", re.I)   # not "there is" / "measure,"
    chatty = [b for b in enriched if chatty_re.search(b.get("enriched_text") or "")]
    bad_kw = [b for b in enriched
              if b.get("keywords") is not None and len(b["keywords"]) != 5]

    print("=" * 52)
    print(f"Books in base file      : {len(base)}")
    print(f"Books in enriched file  : {len(done)}")
    print(f"Hindi-section books     : {len(hindi_total)}")
    print("=" * 52)

    print("\nPROBLEMS (should all be 0 when finished)")
    show("Left out / not enriched yet", [f"id {b['id']}: {b['title'][:60]}" for b in missing])
    show("Hindi books still on the old prompt",
         [f"id {b['id']}: {b['title'][:60]}" for b in hindi_not_redone])
    show("Duplicate ids in enriched file", duplicates)
    show("Ids not in base file", unknown)

    print("\nQUALITY WARNINGS (look at a few by hand)")
    show("Very short enriched_text", [f"id {b['id']}: {b['title'][:50]}" for b in short])
    show("Contains chatty text like 'Here is'", [f"id {b['id']}: {b['title'][:50]}" for b in chatty])
    show("Keyword list not exactly 5", [f"id {b['id']}: {b['title'][:50]}" for b in bad_kw])

    print("\nRESULT")
    if not (missing or hindi_not_redone or duplicates or unknown):
        print("  All books are enriched. Safe to move on to indexing.")
    else:
        pct = 100 * (len(base) - len(missing)) / len(base)
        print(f"  {pct:.1f}% done. Run  python scripts/enrich_books.py  again to finish the rest.")


if __name__ == "__main__":
    main()
