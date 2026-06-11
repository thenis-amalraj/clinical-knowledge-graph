"""Clinical Knowledge Graph — FastAPI backend with hybrid graph-RAG retrieval."""

from __future__ import annotations

import os
import re
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from neo4j import GraphDatabase
from pydantic import BaseModel

# ── Config ────────────────────────────────────────────────────────────────────
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")

# ── Shared singletons (lazy-connected) ────────────────────────────────────────
_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

_llm = ChatOllama(model="llama3.2:1b", temperature=0.0, base_url=OLLAMA_BASE_URL)

# ── Prompt ────────────────────────────────────────────────────────────────────
# XML bounding tags prevent conversational filler from the local model.
# The instructions explicitly forbid fabrication so 1B hallucination is minimized.
_SYSTEM = """\
You are a clinical knowledge graph assistant. Answer questions using ONLY the \
graph context provided below.

<instructions>
1. Base your answer exclusively on the entities and relationships in the context.
2. If the context is empty or irrelevant, reply: "The knowledge graph does not \
contain sufficient information about this topic."
3. Be concise and factual. Do not invent entities, drug names, or relationships.
4. Mention entity types (Disease / Drug / Symptom) when relevant.
</instructions>"""

_HUMAN = """\
<context>
{context}
</context>

<question>
{question}
</question>"""

_prompt = ChatPromptTemplate.from_messages([("system", _SYSTEM), ("human", _HUMAN)])
_chain = _prompt | _llm | StrOutputParser()

# ── Cypher ────────────────────────────────────────────────────────────────────
# Phase 1: full-text search → entity IDs (Lucene query against entity_name_fulltext)
_FTS_QUERY = """
CALL db.index.fulltext.queryNodes("entity_name_fulltext", $q)
YIELD node, score
WITH node, score ORDER BY score DESC LIMIT 5
RETURN node.id AS id
"""

# Phase 2: 1-hop subgraph traversal restricted to semantic relationship types.
# OPTIONAL MATCH keeps entry nodes even when they have no semantic edges yet.
_SUBGRAPH_QUERY = """
UNWIND $ids AS eid
MATCH (n) WHERE n.id = eid
OPTIONAL MATCH (n)-[r:TREATS|CAUSES_SIDE_EFFECT|HAS_SYMPTOM]-(m)
RETURN
  n.id      AS src_id,
  n.name    AS src_name,
  labels(n) AS src_labels,
  type(r)   AS rel_type,
  m.id      AS tgt_id,
  m.name    AS tgt_name,
  labels(m) AS tgt_labels
"""

# ── Helpers ───────────────────────────────────────────────────────────────────
_LUCENE_SPECIAL = re.compile(r'[+\-!(){}[\]^"~*?:\\/|&]')


def _lucene_safe(text: str) -> str:
    """Strip Lucene special characters so a natural-language query doesn't error."""
    return " ".join(_LUCENE_SPECIAL.sub(" ", text).split())


def _primary_label(labels: list[str]) -> str:
    for lbl in ("Disease", "Drug", "Symptom", "Document"):
        if lbl in labels:
            return lbl
    return labels[0] if labels else "Unknown"


def _retrieve_subgraph(query: str) -> tuple[list[dict], list[dict]]:
    """Full-text search → 1-hop traversal → (nodes, relationships)."""
    safe_q = _lucene_safe(query)
    with _driver.session() as session:
        ids = [r["id"] for r in session.run(_FTS_QUERY, q=safe_q).data()]
        if not ids:
            return [], []
        rows = session.run(_SUBGRAPH_QUERY, ids=ids).data()

    node_map: dict[str, dict] = {}
    edges: list[dict] = []

    for row in rows:
        if row["src_id"] and row["src_id"] not in node_map:
            node_map[row["src_id"]] = {
                "id": row["src_id"],
                "name": row["src_name"] or row["src_id"],
                "label": _primary_label(row["src_labels"] or []),
            }
        if row["tgt_id"] and row["tgt_id"] not in node_map:
            node_map[row["tgt_id"]] = {
                "id": row["tgt_id"],
                "name": row["tgt_name"] or row["tgt_id"],
                "label": _primary_label(row["tgt_labels"] or []),
            }
        if row["rel_type"] and row["src_id"] and row["tgt_id"]:
            edge = {"source": row["src_id"], "target": row["tgt_id"], "type": row["rel_type"]}
            if edge not in edges:
                edges.append(edge)

    return list(node_map.values()), edges


def _build_context(nodes: list[dict], relationships: list[dict]) -> str:
    if not nodes:
        return "No relevant entities found in the knowledge graph."
    lines = ["Entities found in the knowledge graph:"]
    for n in nodes:
        lines.append(f"  - {n['name']} (id: {n['id']}, type: {n['label']})")
    if relationships:
        lines.append("\nRelationships:")
        for r in relationships:
            lines.append(f"  - {r['source']} --[{r['type']}]--> {r['target']}")
    return "\n".join(lines)


# ── Schemas ───────────────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    answer: str
    nodes: list[dict[str, Any]]
    relationships: list[dict[str, Any]]


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="Clinical Knowledge Graph API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    try:
        nodes, relationships = _retrieve_subgraph(req.query)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Graph retrieval failed: {exc}") from exc

    context = _build_context(nodes, relationships)

    try:
        answer = _chain.invoke({"context": context, "question": req.query})
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"LLM inference failed: {exc}") from exc

    return ChatResponse(answer=answer, nodes=nodes, relationships=relationships)
