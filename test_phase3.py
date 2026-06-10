"""Phase 3 verification: extract graph from first 3 PubMed abstracts, save to JSON."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from extraction.graph_extractor import extract_graph

INPUT = "data/pubmed_t2d_abstracts.jsonl"
OUTPUT = "data/test_extracted_graph.json"

print("Reading first 3 abstracts from JSONL ...")
with open(INPUT, encoding="utf-8") as f:
    records = [json.loads(line) for line in f][:3]

print(f"Running extraction on {len(records)} abstracts via Ollama llama3 ...\n")

results = []
for i, rec in enumerate(records, 1):
    pmid = rec.get("pmid", "unknown")
    abstract = rec.get("abstract", "")
    print(f"  [{i}/3] PMID {pmid}  ({len(abstract)} chars)")

    try:
        extraction = extract_graph(abstract)
    except Exception as exc:
        print(f"         ERROR: {exc}")
        traceback.print_exc()
        sys.exit(1)

    results.append({
        "pmid": pmid,
        "title": rec.get("title", ""),
        "entities": [e.model_dump() for e in extraction.entities],
        "relationships": [r.model_dump() for r in extraction.relationships],
    })
    print(f"         → {len(extraction.entities)} entities, "
          f"{len(extraction.relationships)} relationships")

# ── Save ──────────────────────────────────────────────────────────────────────
Path(OUTPUT).parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved → {OUTPUT}")

# ── Sample ────────────────────────────────────────────────────────────────────
print("\n── Sample extraction (record 1) ────────────────────────────────────────")
print(json.dumps(results[0], indent=2))

# ── Validate ──────────────────────────────────────────────────────────────────
print("\n── Validating all records ──────────────────────────────────────────────")
for i, r in enumerate(results):
    assert isinstance(r["entities"], list), f"Record {i}: entities not a list"
    assert isinstance(r["relationships"], list), f"Record {i}: relationships not a list"

    for e in r["entities"]:
        missing = {"id", "name", "type"} - e.keys()
        assert not missing, f"Record {i}: entity missing fields {missing}: {e}"
        assert e["type"] in {"Disease", "Drug", "Symptom"}, \
            f"Record {i}: unknown entity type {e['type']!r}"

    entity_ids = {e["id"] for e in r["entities"]}
    for rel in r["relationships"]:
        assert rel.get("source_id") in entity_ids, \
            f"Record {i}: dangling source_id {rel.get('source_id')!r}"
        assert rel.get("target_id") in entity_ids, \
            f"Record {i}: dangling target_id {rel.get('target_id')!r}"
        assert rel.get("type") in {"TREATS", "CAUSES_SIDE_EFFECT", "HAS_SYMPTOM"}, \
            f"Record {i}: unknown relationship type {rel.get('type')!r}"

print(f"All {len(results)} extractions valid. Phase 3 verified.")
