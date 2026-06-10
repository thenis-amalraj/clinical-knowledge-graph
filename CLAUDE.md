# Project Overview
[cite_start]Clinical Knowledge Graph is an end-to-end, local-first GraphRAG pipeline[cite: 44]. [cite_start]It ingests PubMed abstracts via Airflow, extracts entities using a local LLM (Ollama) with Pydantic structured outputs, stores relationships in Neo4j, and serves a Streamlit chatbot via FastAPI[cite: 44, 49, 144].

# Commands
- Docker Stack: `docker-compose up -d --build`
- Start local LLM: `docker exec -it ollama ollama run llama3`
- Airflow UI: `http://localhost:8080`
- Neo4j Browser: `http://localhost:7474`
- FastAPI Docs: `http://localhost:8000/docs`
- Streamlit UI: `http://localhost:8501`

# Architecture
- [cite_start]**Ingestion:** Airflow queries PubMed Entrez API (`esearch.fcgi` & `efetch.fcgi`) using the History Server (`usehistory=y`) for pagination[cite: 51, 57].
- [cite_start]**Extraction:** LangChain + Ollama uses `with_structured_output` and syntactic XML bounding to force rigid JSON schema adherence[cite: 144, 183].
- [cite_start]**Storage:** Neo4j (LPG) utilizes full-text and vector indexes for hybrid retrieval[cite: 214, 231, 234]. [cite_start]Batch ingestion uses `UNWIND` + `MERGE` with strict locks to prevent race conditions[cite: 238, 246].
- [cite_start]**Application:** FastAPI serves the `HybridCypherRetriever`[cite: 259]; [cite_start]Streamlit renders the interactive network using `streamlit-agraph` and explicit `st.session_state` management[cite: 272, 276].

# Conventions
- **Simplicity First:** Write the minimum code required. No speculative features.
- **Python:** Use Python 3.11+. Strict type hinting is mandatory using Pydantic V2.
- [cite_start]**Idempotency:** Airflow DAGs and Cypher queries MUST be idempotent[cite: 134]. [cite_start]Parse XML safely using `xml.etree.ElementTree` and XPath to handle missing nodes gracefully[cite: 79, 84].
- **Security:** Use parameterized Cypher queries to prevent injection. Never hardcode credentials.

# Gotchas
- [cite_start]**Ollama limits:** Local models lack native function calling; you must use XML tags `<system>`, `<ontology>`, `<input>` and 0.0 temperature in prompts[cite: 183, 193].
- [cite_start]**Neo4j Race Conditions:** Concurrent batch loading requires separating node creation from edge creation within transactions to acquire hard write locks[cite: 241, 243, 244].
- **Streamlit Volatility:** `agraph` click events trigger full script reruns. [cite_start]You must bind the clicked node ID to `st.session_state` to prevent the UI from resetting[cite: 315, 316, 320].

# Compaction Instructions
When compacting memory, preserve: the modified file list, current test commands, and key architecture decisions.