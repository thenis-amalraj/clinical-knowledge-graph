"""Batch-ingest extracted graph data from test_extracted_graph.json into Neo4j.

Race-condition safety (CLAUDE.md §Gotchas):
  Phase 1 — MERGE all nodes in a dedicated transaction. Neo4j acquires write
             locks on each node during MERGE, preventing concurrent duplicates.
  Phase 2 — MATCH (not MERGE) source and target nodes, then MERGE the edge.
             Using MATCH forces the planner to rely on the already-locked nodes
             rather than re-acquiring locks or creating phantom nodes.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from neo4j import GraphDatabase, ManagedTransaction

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

INPUT = "data/test_extracted_graph.json"

# ── Phase 1 queries: node MERGE (one per label for clean lock semantics) ──────

_MERGE_DOCUMENTS = """
UNWIND $docs AS d
MERGE (n:Document {pubmed_id: d.pubmed_id})
SET n.title = d.title
"""

_MERGE_DISEASES = """
UNWIND $entities AS e
MERGE (n:Disease {id: e.id})
SET n.name = e.name
"""

_MERGE_DRUGS = """
UNWIND $entities AS e
MERGE (n:Drug {id: e.id})
SET n.name = e.name
"""

_MERGE_SYMPTOMS = """
UNWIND $entities AS e
MERGE (n:Symptom {id: e.id})
SET n.name = e.name
"""

# ── Phase 2 queries: edge MERGE (MATCH nodes — no lock re-acquisition) ────────

_MERGE_TREATS = """
UNWIND $rels AS r
MATCH (src:Drug    {id: r.source_id})
MATCH (tgt:Disease {id: r.target_id})
MERGE (src)-[:TREATS]->(tgt)
"""

_MERGE_CAUSES_SIDE_EFFECT = """
UNWIND $rels AS r
MATCH (src:Drug    {id: r.source_id})
MATCH (tgt:Symptom {id: r.target_id})
MERGE (src)-[:CAUSES_SIDE_EFFECT]->(tgt)
"""

_MERGE_HAS_SYMPTOM = """
UNWIND $rels AS r
MATCH (src:Disease {id: r.source_id})
MATCH (tgt:Symptom {id: r.target_id})
MERGE (src)-[:HAS_SYMPTOM]->(tgt)
"""

_MERGE_MENTIONED_IN = """
UNWIND $links AS l
MATCH (e   {id: l.entity_id})
MATCH (doc:Document {pubmed_id: l.pubmed_id})
MERGE (doc)-[:MENTIONS]->(e)
"""


def _phase1_nodes(tx: ManagedTransaction, docs, diseases, drugs, symptoms) -> None:
    if docs:
        tx.run(_MERGE_DOCUMENTS, docs=docs)
    if diseases:
        tx.run(_MERGE_DISEASES, entities=diseases)
    if drugs:
        tx.run(_MERGE_DRUGS, entities=drugs)
    if symptoms:
        tx.run(_MERGE_SYMPTOMS, entities=symptoms)


def _phase2_edges(tx: ManagedTransaction, treats, side_effects, has_symptoms, mentions) -> None:
    if treats:
        tx.run(_MERGE_TREATS, rels=treats)
    if side_effects:
        tx.run(_MERGE_CAUSES_SIDE_EFFECT, rels=side_effects)
    if has_symptoms:
        tx.run(_MERGE_HAS_SYMPTOM, rels=has_symptoms)
    if mentions:
        tx.run(_MERGE_MENTIONED_IN, links=mentions)


def ingest(records: list[dict]) -> None:
    docs: list[dict] = []
    diseases: list[dict] = []
    drugs: list[dict] = []
    symptoms: list[dict] = []
    treats: list[dict] = []
    side_effects: list[dict] = []
    has_symptoms: list[dict] = []
    mentions: list[dict] = []

    for rec in records:
        pmid = str(rec["pmid"])
        docs.append({"pubmed_id": pmid, "title": rec.get("title", "")})

        for e in rec["entities"]:
            mentions.append({"entity_id": e["id"], "pubmed_id": pmid})
            if e["type"] == "Disease":
                diseases.append(e)
            elif e["type"] == "Drug":
                drugs.append(e)
            elif e["type"] == "Symptom":
                symptoms.append(e)

        for r in rec["relationships"]:
            if r["type"] == "TREATS":
                treats.append(r)
            elif r["type"] == "CAUSES_SIDE_EFFECT":
                side_effects.append(r)
            elif r["type"] == "HAS_SYMPTOM":
                has_symptoms.append(r)

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            # Phase 1: all node MERGE in a single transaction → write locks acquired
            session.execute_write(_phase1_nodes, docs, diseases, drugs, symptoms)
            print(
                f"  nodes merged: {len(docs)} Document, "
                f"{len(diseases)} Disease, {len(drugs)} Drug, {len(symptoms)} Symptom"
            )

            # Phase 2: all edge MERGE in a separate transaction → MATCH relies on locked nodes
            session.execute_write(_phase2_edges, treats, side_effects, has_symptoms, mentions)
            print(
                f"  edges merged: {len(treats)} TREATS, "
                f"{len(side_effects)} CAUSES_SIDE_EFFECT, "
                f"{len(has_symptoms)} HAS_SYMPTOM, "
                f"{len(mentions)} MENTIONS"
            )
    finally:
        driver.close()


def _print_counts() -> None:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            node_rows = session.run(
                "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt ORDER BY label"
            ).data()
            rel_rows = session.run(
                "MATCH ()-[r]->() RETURN type(r) AS type, count(r) AS cnt ORDER BY type"
            ).data()

        print("\n── Node counts ─────────────────────────────────")
        for row in node_rows:
            print(f"  {row['label']:<20} {row['cnt']}")

        print("\n── Relationship counts ──────────────────────────")
        for row in rel_rows:
            print(f"  {row['type']:<25} {row['cnt']}")

        total_nodes = sum(r["cnt"] for r in node_rows)
        total_rels = sum(r["cnt"] for r in rel_rows)
        print(f"\n  TOTAL nodes: {total_nodes}   TOTAL relationships: {total_rels}")
    finally:
        driver.close()


if __name__ == "__main__":
    data = json.loads(Path(INPUT).read_text(encoding="utf-8"))
    print(f"Ingesting {len(data)} records from {INPUT} ...\n")
    ingest(data)
    print("\nValidating — querying live Neo4j counts ...")
    _print_counts()
    print("\nPhase 4 complete.")
