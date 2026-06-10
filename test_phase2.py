"""Standalone test: verify PubMed fetch + XML parsing produces valid JSONL."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extraction.pubmed_fetcher import fetch_and_save

OUTPUT = "data/pubmed_t2d_abstracts.jsonl"

print("Fetching 50 abstracts for 'Type 2 Diabetes' ...")
count = fetch_and_save("Type 2 Diabetes", OUTPUT, max_results=50)
print(f"Wrote {count} records to {OUTPUT}")

assert count > 0, "No records written — something went wrong"

with open(OUTPUT, encoding="utf-8") as f:
    lines = f.readlines()

assert len(lines) == count, f"Line count mismatch: {len(lines)} lines vs {count} records"

first = json.loads(lines[0])
print("\nSample record:")
print(f"  pmid    : {first.get('pmid')}")
print(f"  title   : {first.get('title', '')[:80]}")
print(f"  abstract: {first.get('abstract', '')[:120]}...")
print(f"  authors : {first.get('authors', [])[:2]}")
print(f"  journal : {first.get('journal')}")
print(f"  year    : {first.get('pub_year')}")
print(f"  mesh    : {first.get('mesh_terms', [])[:3]}")

required = {"pmid", "title", "abstract"}
for i, line in enumerate(lines):
    rec = json.loads(line)
    missing = required - rec.keys()
    assert not missing, f"Record {i} missing fields: {missing}"

print(f"\nAll {count} records valid. Phase 2 extraction verified.")
