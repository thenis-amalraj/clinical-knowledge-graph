# Requirements & Scope Tracking

## Phase 1: Infrastructure
- [ ] Create `docker-compose.yml` (Neo4j, Ollama, Airflow, FastAPI, Streamlit).
- [ ] Configure volume mounts for Neo4j `/data` and Ollama model persistence.
- [ ] Set up `.claude/` structure (rules, skills, settings).

## Phase 2: Idempotent Ingestion (Airflow)
- [ ] Implement `tenacity` exponential backoff for NCBI API limits.
- [ ] Write `esearch` / `efetch` History server pagination logic.
- [ ] Write `xml.etree.ElementTree` parser flattening MEDLINE DTD to local JSONL staging.

## Phase 3: Semantic Extraction (Ollama)
- [ ] Define Pydantic Ontology (`Entity`, `Relationship`, `GraphExtraction`).
- [ ] Implement Langchain `with_structured_output` utilizing local `llama3`.
- [ ] Engineer prompt with syntactic XML tags and zero-temperature constraints.

## Phase 4: Graph Engineering (Neo4j)
- [ ] Create initialization scripts for uniqueness constraints, Full-Text, and Vector indexes.
- [ ] Write race-condition-safe Cypher `UNWIND` ingest queries.

## Phase 5: GraphRAG & Interface (FastAPI + Streamlit)
- [ ] Build FastAPI `HybridCypherRetriever` endpoints.
- [ ] Implement `streamlit-agraph` component mapping node styling to ontology classes.
- [ ] Implement strict `st.session_state` management for node click events.
