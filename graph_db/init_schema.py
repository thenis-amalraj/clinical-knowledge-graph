"""Initialize Neo4j schema: uniqueness constraints and full-text indexes."""

from __future__ import annotations

import os

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Neo4j 5 syntax: IF NOT EXISTS makes every statement idempotent.
_CONSTRAINTS = [
    "CREATE CONSTRAINT entity_disease_id IF NOT EXISTS FOR (n:Disease) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT entity_drug_id    IF NOT EXISTS FOR (n:Drug)    REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT entity_symptom_id IF NOT EXISTS FOR (n:Symptom) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT document_pubmed_id IF NOT EXISTS FOR (n:Document) REQUIRE n.pubmed_id IS UNIQUE",
]

# Full-text index over all three entity labels for hybrid retrieval (Phase 5).
_INDEXES = [
    (
        "CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS "
        "FOR (n:Disease|Drug|Symptom) ON EACH [n.name]"
    ),
]


def init_schema() -> None:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    try:
        with driver.session() as session:
            for stmt in _CONSTRAINTS:
                session.run(stmt)
                print(f"  constraint: {stmt.split('FOR')[0].strip()}")
            for stmt in _INDEXES:
                session.run(stmt)
                print(f"  index:      {stmt[:70].strip()}")
        print("\nSchema initialized successfully.")
    finally:
        driver.close()


if __name__ == "__main__":
    init_schema()
