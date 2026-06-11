"""Phase 5 verification: hit the live /chat endpoint and assert a valid response."""

from __future__ import annotations

import json
import sys

import requests

BASE = "http://localhost:8000"


def check(label: str, condition: bool, detail: str = "") -> None:
    mark = "OK" if condition else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail else ""))
    if not condition:
        sys.exit(1)


# ── Health ────────────────────────────────────────────────────────────────────
print("1. Health check ...")
r = requests.get(f"{BASE}/health", timeout=5)
check("GET /health → 200", r.status_code == 200)
check("body has status:ok", r.json().get("status") == "ok")

# ── Chat ──────────────────────────────────────────────────────────────────────
QUERY = "What are the symptoms of Diabetes?"
print(f'\n2. POST /chat  query="{QUERY}" ...')
r = requests.post(f"{BASE}/chat", json={"query": QUERY}, timeout=90)
check("POST /chat → 200", r.status_code == 200, r.text[:200] if r.status_code != 200 else "")

data = r.json()
check("response has 'answer'", "answer" in data)
check("answer is non-empty string", isinstance(data["answer"], str) and len(data["answer"]) > 0)
check("response has 'nodes' list", isinstance(data.get("nodes"), list))
check("response has 'relationships' list", isinstance(data.get("relationships"), list))

# Every node must have id, name, label
for i, n in enumerate(data["nodes"]):
    check(f"node[{i}] has id/name/label", {"id", "name", "label"} <= n.keys())
    check(f"node[{i}] label is valid", n["label"] in {"Disease", "Drug", "Symptom", "Document"})

# Every relationship must have source, target, type
for i, rel in enumerate(data["relationships"]):
    check(f"rel[{i}] has source/target/type", {"source", "target", "type"} <= rel.keys())
    node_ids = {n["id"] for n in data["nodes"]}
    check(f"rel[{i}] source exists", rel["source"] in node_ids)
    check(f"rel[{i}] target exists", rel["target"] in node_ids)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n── Response ────────────────────────────────────────────────")
print(f"Answer:\n  {data['answer']}\n")
print(f"Nodes ({len(data['nodes'])}):")
for n in data["nodes"]:
    print(f"  {n['label']:<10} {n['id']}")
print(f"\nRelationships ({len(data['relationships'])}):")
for rel in data["relationships"]:
    print(f"  {rel['source']} --[{rel['type']}]--> {rel['target']}")

print("\nAll assertions passed. Phase 5 verified.")
