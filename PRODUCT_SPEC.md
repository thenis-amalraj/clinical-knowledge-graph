# Product Specification: Clinical Knowledge Graph & GraphRAG System

## 1. Executive Summary
**Vision:** Deliver a 100% local, offline-capable medical intelligence platform. The system will autonomously ingest scientific literature, extract deterministic clinical relationships using constrained local language models, and serve those insights via an interactive GraphRAG (Graph Retrieval-Augmented Generation) application.
**Core Objective:** Eliminate LLM hallucinations in the medical domain by grounding all AI responses strictly in a Labeled Property Graph (LPG), while maintaining zero cloud API dependencies (simulating strict data privacy compliance).

---

## 2. System Architecture & Tech Stack
The platform is designed as a containerized microservices architecture.
* **Orchestration & DevOps:** Docker Compose (local deployment), GitHub Actions (CI/CD).
* **Data Pipeline:** Apache Airflow (scheduled batch ingestion).
* **AI Inference:** Ollama (running `llama3` locally for extraction and synthesis).
* **Database:** Neo4j (Labeled Property Graph, handling structural and vector indexes).
* **Backend:** FastAPI (RESTful API, LangChain orchestration, Cypher query generation).
* **Frontend:** Streamlit (conversational UI, interactive `streamlit-agraph` network visualization).

---

## 3. Data Engineering & Ingestion (Airflow DAGs)
The system must automatically acquire and normalize data without human intervention.

* **Source:** NCBI PubMed Entrez API (`esearch.fcgi` and `efetch.fcgi`).
* **Idempotency & Resilience:**
    * DAGs must implement exponential backoff with jitter (e.g., using `tenacity`) to respect NCBI's 10 requests/second API limits.
    * Utilize the NCBI History Server (`usehistory=y`) for stateful pagination across tens of thousands of abstracts.
* **Parsing:**
    * Raw MEDLINE XML must be flattened using `xml.etree.ElementTree`.
    * Data must be staged locally as JSON Lines (`.jsonl`) files. The database must *never* be updated directly from the API response to prevent locking failures.

---

## 4. Semantic Extraction Layer (Ollama + LangChain)
Raw text must be converted into strict semantic structures.

* **Ontology Requirements:** * **Nodes:** `Disease`, `Drug`, `Symptom`, `Document`.
    * **Edges:** `TREATS`, `CAUSES_SIDE_EFFECT`, `HAS_SYMPTOM`, `MENTIONS`.
* **LLM Constraints:**
    * The local LLM must be constrained using LangChain's `with_structured_output` and Pydantic V2 models.
    * Prompts must utilize syntactic XML bounding tags (`<ontology>`, `<instructions>`, `<input>`) to prevent the LLM from outputting conversational filler.
    * **Entity Disambiguation:** The LLM prompt must instruct the model to normalize acronyms and synonyms (e.g., mapping "T2D" and "Type II Diabetes" to a single `type_2_diabetes` ID) before generating the JSON payload.

---

## 5. Graph Engineering (Neo4j)
The database must mathematically guarantee data integrity and support high-speed retrieval.

* **Schema Enforcement:** Explicit uniqueness constraints must be applied to the `id` property of all clinical entities and the `pubmed_id` of Documents.
* **Indexes:**
    * Full-text indexes must be established across node `name` properties for fast keyword searching.
    * Vector indexes must be established to support cosine-similarity semantic searches.
* **Ingestion Logic:**
    * Batch loading must use the Cypher `UNWIND` clause (processing 5,000+ records simultaneously).
    * To prevent race conditions from concurrent Airflow workers, Cypher transactions must decouple node matching/locking from relationship `MERGE` commands.

---

## 6. Backend API (FastAPI)
The backend acts as the bridge between the graph, the LLM, and the user interface.

* **Framework:** FastAPI with Pydantic for request/response validation.
* **GraphRAG Workflow (`HybridCypherRetriever`):**
    1.  Receive natural language query from Frontend.
    2.  Vectorize the query using a local embedding model via Ollama.
    3.  Execute a hybrid search (Vector Similarity + Full-Text Keyword) against Neo4j to identify starting nodes.
    4.  Generate and execute a Cypher traversal to pull the surrounding sub-graph.
    5.  Pass the precise sub-graph context + the user query to the local LLM.
    6.  Return the synthesized, hallucination-free response.

---

## 7. Frontend User Interface (Streamlit)
The interface must be highly responsive and intuitive for clinical researchers.

* **Conversational Chat:** A standard chat interface where users can ask complex questions (e.g., "What drugs treat asthma but do not cause insomnia?").
* **Interactive Visualizer:**
    * Utilize `streamlit-agraph` to render the sub-graph returned by the backend.
    * Nodes must be color-coded by ontological class (e.g., Drugs = Blue, Diseases = Red).
    * **State Management:** Node click events from the React component must be captured and stored in `st.session_state` to prevent the Streamlit application from resetting the physics layout upon interaction.
* **Metadata Sidebar:** Clicking a node in the visualizer must trigger a side panel displaying detailed properties and source PubMed literature.

---

## 8. DevOps & CI/CD Pipeline
While the application runs locally, it must adhere to enterprise deployment standards.

* **Dockerization:** A root `docker-compose.yml` must orchestrate Neo4j, Ollama, Airflow, the FastAPI backend, and the Streamlit frontend. Volume mounts must ensure database and LLM model persistence across container restarts.
* **GitHub Actions (CI):**
    * On PR creation: Run `ruff check` (linting) and `ruff format --check`.
    * Run static type checking (`mypy`).
    * Execute unit tests (`pytest`) against backend extraction logic.
* **Local Claude Tooling:**
    * Implement `.claude/scripts/post-edit.sh` to automatically run `ruff` on any Python file modified by Claude within 2 seconds of the edit.

---

## 9. Development Phases
* **Phase 1:** Infrastructure & Docker orchestration.
* **Phase 2:** Airflow DAG development & PubMed API integration.
* **Phase 3:** Pydantic ontology definition & Ollama local extraction pipeline.
* **Phase 4:** Neo4j constraint initialization & idempotent Cypher ingestion.
* **Phase 5:** FastAPI GraphRAG endpoints.
* **Phase 6:** Streamlit frontend, interactive `agraph` rendering, and session state tuning.
