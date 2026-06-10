# System Design: Clinical Knowledge Graph

## 1. Architectural Philosophy
[cite_start]This project establishes a highly deterministic pipeline environment on localized, edge-capable infrastructure[cite: 42, 43]. [cite_start]By completely circumventing cloud APIs, it ensures absolute data sovereignty and zero recurrent computational costs[cite: 43]. 

## 2. Ingestion Layer (Airflow)
Data is sourced from PubMed via the NCBI Entrez API. 
- [cite_start]**Methodology:** We decouple search and retrieval using `esearch.fcgi` (to establish a remote session via `<QueryKey>` and `<WebEnv>`) and `efetch.fcgi` (to pull the XML payload)[cite: 54, 58, 59].
- [cite_start]**Resilience:** An NCBI API key allows 10 requests/second[cite: 66]. [cite_start]Airflow PythonOperators utilize exponential backoff with randomized jitter to prevent the "thundering herd" phenomenon during API limits[cite: 71, 73].
- [cite_start]**Parsing:** Nested MEDLINE XML is flattened into dictionaries using `xml.etree.ElementTree` with dynamic XPath queries, then serialized to localized JSON Lines/Parquet files to preserve pipeline idempotency[cite: 79, 84, 134].

## 3. Semantic Extraction Layer (Ollama)
[cite_start]Local LLMs (Llama 3) perform Entity Disambiguation and extraction[cite: 138, 196].
- [cite_start]**Ontology Enforcement:** We utilize LangChain's `with_structured_output` coupled with Pydantic models for `Disease`, `Drug`, `Symptom`, and specific relationships (`TREATS`, `CAUSES_SIDE_EFFECT`)[cite: 144, 147, 148].
- [cite_start]**Prompt Engineering:** Prompts use explicit XML bounding boxes (`<ontology>`, `<instructions>`), Few-Shot JSON framing, and zero-temperature sampling to prevent conversational hallucinations[cite: 183, 194, 195].
- [cite_start]**Entity Resolution:** The LLM normalizes semantic variance (e.g., standardizing "T2D" to "type_2_diabetes_mellitus") utilizing its pre-trained biomedical representations before database ingestion[cite: 206, 208, 211].

## 4. Storage Layer (Neo4j LPG)
[cite_start]Neo4j bridges Semantic Web theory with practical engineering using a Labeled Property Graph (LPG)[cite: 214, 218].
- [cite_start]**Schema & Indexes:** Explicit uniqueness constraints enforce schema[cite: 222]. [cite_start]Full-text indexes support keyword searches, and vector indexes support cosine similarity for semantic matching[cite: 231, 234].
- [cite_start]**Ingestion Execution:** We utilize the `UNWIND` clause for batched transactions (5,000-10,000 records)[cite: 238, 239]. [cite_start]To prevent phantom duplicate nodes from concurrent Airflow workers, queries explicitly separate node locking (`MATCH`) from edge creation (`MERGE`)[cite: 242, 244, 246].

## 5. Application Layer (FastAPI & Streamlit)
- **GraphRAG:** FastAPI executes a dual-pronged retrieval using `Neo4jVector`. [cite_start]It combines vector similarity search with full-text keyword matching to find entry nodes, traverses the subgraph, and passes the strict structural evidence to the local LLM to synthesize an answer[cite: 259, 263, 266, 269].
- [cite_start]**Visualization:** Streamlit renders the network using `streamlit-agraph`[cite: 272]. [cite_start]We manage the ephemeral nature of Streamlit reruns by persisting the `agraph` node click events into `st.session_state`, ensuring asynchronous metadata queries do not crash the React DOM[cite: 275, 315, 320].