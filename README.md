# Clinical Knowledge Graph

An end-to-end, local-first **GraphRAG** pipeline that ingests PubMed biomedical literature, extracts clinical entities via a local LLM, stores a labeled property graph in Neo4j, and serves a hybrid retrieval-augmented chat interface.

---

## Architecture

```
PubMed Entrez API
      │  esearch (History Server) + efetch (batch XML)
      ▼
Apache Airflow DAG  ──►  JSONL staging file  (./data/)
      │
      ▼
LangChain + Ollama (llama3.2:1b)
      │  XML-bounded prompt → JSON mode grammar sampler → Pydantic V2 validation
      ▼
graph_db/ingest_graph.py
      │  Two-phase UNWIND+MERGE (node locks → edge locks)
      ▼
Neo4j 5 (LPG)
      │  Uniqueness constraints + Lucene full-text index + bolt://
      ▼
FastAPI  /chat
      │  Lucene sanitizer → full-text search → 1-hop OPTIONAL MATCH traversal
      │  → context string → llama3.2:1b → structured JSON response
      ▼
Streamlit  :8501
      │  streamlit-agraph visualization + st.session_state click persistence
      ▼
Browser
```

---

## Stack

| Layer | Technology | Role |
|---|---|---|
| Orchestration | Apache Airflow 2.9.2 | Scheduled DAG: `pubmed_ingestion` runs `@daily` |
| Ingestion | NCBI Entrez API (`esearch.fcgi` + `efetch.fcgi`) | PubMed abstract retrieval with History Server pagination |
| HTTP retry | `tenacity` | Exponential backoff + jitter on NCBI rate-limited endpoints |
| XML parsing | `xml.etree.ElementTree` + XPath | Safe MEDLINE XML parsing; missing tags return `None`, never raise |
| LLM runtime | Ollama (`llama3.2:1b`) | Local inference — no external API calls, no data egress |
| LLM orchestration | LangChain (`langchain-ollama`) | Prompt templates, chain composition, `StrOutputParser` |
| JSON enforcement | Ollama `format="json"` grammar sampler | Forces valid JSON from models without native tool-calling |
| Schema validation | Pydantic V2 (`BaseModel`, `Literal`) | `GraphExtraction` → `Entity` / `Relationship` typed models |
| Graph database | Neo4j 5 (LPG) | Stores Disease / Drug / Symptom / Document nodes + semantic edges |
| Graph driver | `neo4j` Python driver | `execute_write()` transaction functions, parameterized Cypher |
| Cypher pattern | `UNWIND` + `MERGE` (two-phase) | Phase 1: node MERGE acquires write locks; Phase 2: MATCH+MERGE edges |
| Full-text search | Neo4j Lucene index (`entity_name_fulltext`) | Sub-millisecond entity lookup across Disease\|Drug\|Symptom labels |
| API | FastAPI + Uvicorn | `/health` + `/chat` endpoints; `ChatRequest` / `ChatResponse` Pydantic models |
| Retrieval | Custom `HybridRetriever` | Full-text search → 1-hop `OPTIONAL MATCH` subgraph traversal |
| Frontend | Streamlit + `streamlit-agraph` | Chat UI + interactive force-directed graph |
| State management | `st.session_state` | Persists `clicked_node` across full-script reruns triggered by agraph |
| Containerization | Docker Compose | Seven-service stack with healthcheck-gated `depends_on` |

---

## Ontology

**Node labels**

| Label | Uniqueness key | Description |
|---|---|---|
| `Disease` | `id` (snake_case canonical) | Medical conditions and diagnoses |
| `Drug` | `id` (snake_case canonical) | Pharmaceutical compounds and interventions |
| `Symptom` | `id` (snake_case canonical) | Clinical signs, lab markers, adverse effects |
| `Document` | `pubmed_id` | Source PubMed abstract |

**Relationship types**

| Type | Direction | Meaning |
|---|---|---|
| `TREATS` | Drug → Disease | Drug manages or treats the disease |
| `CAUSES_SIDE_EFFECT` | Drug → Symptom | Drug causes this adverse effect |
| `HAS_SYMPTOM` | Disease → Symptom | Disease presents with this finding |
| `MENTIONS` | Document → Entity | Abstract is the provenance source for the entity |

**Entity ID canonicalization** — all synonyms are collapsed to a single `lowercase_snake_case` ID at extraction time (e.g. `"T2D"`, `"Type II Diabetes"`, `"T2DM"` → `type_2_diabetes_mellitus`). This prevents duplicate nodes from synonym drift.

---

## Neo4j Schema

```cypher
-- Uniqueness constraints (idempotent via IF NOT EXISTS)
CREATE CONSTRAINT entity_disease_id  IF NOT EXISTS FOR (n:Disease)  REQUIRE n.id IS UNIQUE
CREATE CONSTRAINT entity_drug_id     IF NOT EXISTS FOR (n:Drug)     REQUIRE n.id IS UNIQUE
CREATE CONSTRAINT entity_symptom_id  IF NOT EXISTS FOR (n:Symptom)  REQUIRE n.id IS UNIQUE
CREATE CONSTRAINT document_pubmed_id IF NOT EXISTS FOR (n:Document) REQUIRE n.pubmed_id IS UNIQUE

-- Full-text index (Lucene, multi-label)
CREATE FULLTEXT INDEX entity_name_fulltext IF NOT EXISTS
  FOR (n:Disease|Drug|Symptom) ON EACH [n.name]
```

---

## Retrieval Pipeline (`/chat`)

1. **Lucene sanitization** — strips special Lucene operators (`+`, `-`, `!`, `?`, `*`, `~`, `^`, `"`, `:`, `(`, `)`, `{`, `}`, `[`, `]`, `\`, `/`, `|`, `&`) from the raw natural-language query.
2. **Full-text search** — `CALL db.index.fulltext.queryNodes("entity_name_fulltext", $q) LIMIT 5` returns top-scored entity node IDs.
3. **1-hop subgraph traversal** — `OPTIONAL MATCH (n)-[r:TREATS|CAUSES_SIDE_EFFECT|HAS_SYMPTOM]-(m)` over the matched entities. `OPTIONAL MATCH` preserves entry nodes that have no semantic edges yet.
4. **Context serialization** — nodes and relationships serialized to a structured string.
5. **LLM synthesis** — XML-bounded prompt (`<instructions>`, `<context>`, `<question>`) at `temperature=0.0` passed to `llama3.2:1b`. The instructions forbid hallucination and mandate fallback to a canned "insufficient information" response when context is empty.
6. **Response** — `ChatResponse` returns `answer: str`, `nodes: list[dict]`, `relationships: list[dict]`.

`GraphCypherQAChain` was deliberately avoided — `llama3.2:1b` cannot reliably generate valid Cypher at 1B parameters. All Cypher is pre-written and parameterized.

---

## Race-Condition-Safe Batch Ingestion

Concurrent Airflow tasks loading the same abstract batch would create duplicate nodes without explicit lock acquisition. The two-phase pattern prevents this:

```
Phase 1 (single transaction)
  UNWIND $nodes → MERGE (n:Disease {id: …})   ← write lock acquired on node
  UNWIND $nodes → MERGE (n:Drug    {id: …})
  UNWIND $nodes → MERGE (n:Symptom {id: …})
  UNWIND $docs  → MERGE (n:Document {pubmed_id: …})

Phase 2 (separate transaction)
  UNWIND $rels → MATCH (src:Drug {id: …})     ← relies on already-locked nodes
                 MATCH (tgt:Disease {id: …})
                 MERGE (src)-[:TREATS]->(tgt)
```

Separating node creation from edge creation means Phase 2 never needs to re-acquire node locks mid-transaction, eliminating the deadlock window.

---

## Services

| Service | Port | URL |
|---|---|---|
| Streamlit UI | 8501 | http://localhost:8501 |
| FastAPI | 8000 | http://localhost:8000/docs |
| Airflow Webserver | 8080 | http://localhost:8080 |
| Neo4j Browser | 7474 | http://localhost:7474 |
| Ollama | 11434 | http://localhost:11434 |

---

## Quick Start

```bash
# 1. Start the full stack
docker-compose up -d --build

# 2. Wait for Ollama to pull the model (~1-2 min on first run)
docker logs clinical-knowledge-graph-ollama-init-1 -f

# 3. Initialize Neo4j schema (run once)
docker exec clinical-knowledge-graph-api-1 python graph_db/init_schema.py

# 4. Trigger the ingestion DAG
#    Airflow UI → pubmed_ingestion → Trigger DAG
#    Credentials: airflow / airflow

# 5. Run extraction + graph load (after DAG completes)
docker exec clinical-knowledge-graph-api-1 python graph_db/ingest_graph.py

# 6. Chat with the graph
open http://localhost:8501
```

---

## Project Structure

```
.
├── dags/
│   └── pubmed_ingestion_dag.py     # Airflow DAG: PubMed → JSONL
├── extraction/
│   ├── ontology.py                 # Pydantic V2 models: Entity, Relationship, GraphExtraction
│   ├── graph_extractor.py          # LangChain + Ollama NER pipeline
│   └── pubmed_fetcher.py           # NCBI Entrez API client with tenacity retry
├── graph_db/
│   ├── init_schema.py              # Neo4j constraints + full-text index
│   └── ingest_graph.py             # Two-phase UNWIND+MERGE batch ingestion
├── api/
│   └── main.py                     # FastAPI: /health + /chat (HybridRetriever)
├── frontend/
│   └── app.py                      # Streamlit chat UI + streamlit-agraph visualization
├── data/                           # JSONL staging files (gitignored)
├── docker-compose.yml
└── requirements.txt
```

---

## Key Design Decisions

**Local-first** — Ollama runs entirely in Docker. No OpenAI, no Anthropic, no data leaves the machine.

**No Cypher generation** — The LLM synthesizes natural language answers from pre-retrieved graph context. Cypher is written by humans and parameterized, never generated by the model.

**Idempotent everything** — All Cypher uses `MERGE` + `IF NOT EXISTS`. Re-running the DAG or ingest script on the same data is safe.

**XML bounding in prompts** — `<ontology>`, `<instructions>`, `<example>`, `<input>`, `<context>`, `<question>` tags structure model input and suppress conversational filler from small local models.

**Pydantic V2 as the contract** — `GraphExtraction` is the single source of truth for what the LLM must return. Validation happens after JSON parsing; dangling relationships (source/target IDs not in entity list) are pruned before graph ingestion.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `NEO4J_URI` | `bolt://neo4j:7687` | Neo4j Bolt connection string |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password (change for non-local deployments) |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | Ollama HTTP base URL |
| `API_BASE_URL` | `http://api:8000` | FastAPI base URL (used by Streamlit) |
