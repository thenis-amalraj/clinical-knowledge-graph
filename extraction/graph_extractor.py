"""Clinical entity and relationship extractor using Ollama llama3 via LangChain."""

from __future__ import annotations

import json
import os
import re

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from extraction.ontology import GraphExtraction

_OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# ── Prompt ────────────────────────────────────────────────────────────────────
# XML bounding tags structure the prompt to prevent conversational filler.
# The few-shot example locks the exact output shape into the model's context.

_SYSTEM = """\
You are a biomedical knowledge graph extraction engine. Your sole task is to \
extract clinical entities and relationships from a scientific abstract and output \
them as a strict JSON object matching the schema below.

<ontology>
ENTITY TYPES — extract only these three:
  - Disease : Medical conditions and diagnoses
  - Drug    : Pharmaceutical compounds and therapeutic interventions
  - Symptom : Clinical signs, symptoms, lab markers, and adverse effects

RELATIONSHIP TYPES — extract only these three:
  - TREATS            : Drug → Disease  (the drug treats or manages the disease)
  - CAUSES_SIDE_EFFECT: Drug → Symptom  (the drug causes this adverse effect)
  - HAS_SYMPTOM       : Disease → Symptom (the disease presents with this finding)
</ontology>

<instructions>
DISAMBIGUATION — apply before writing any id:
  All entity ids MUST be lowercase snake_case canonical forms. Normalize every
  synonym and acronym to a single canonical id:
    "T2D" | "Type II Diabetes" | "type 2 diabetes" | "T2DM" → type_2_diabetes_mellitus
    "HbA1c" | "A1C" | "glycated hemoglobin" | "glycosylated hemoglobin" → glycated_hemoglobin_hba1c
    "metformin" | "Metformin HCl" | "metformin hydrochloride" → metformin
    "insulin" | "insulin therapy" | "basal insulin" → insulin
    "hyperglycemia" | "elevated blood glucose" | "high blood sugar" → hyperglycemia
    "GLP-1" | "GLP-1 receptor agonist" | "liraglutide" → liraglutide (keep brand-generic distinct)

OUTPUT RULES:
  1. Output ONLY a raw JSON object — no markdown fences, no prose, no explanation.
  2. Every relationship source_id and target_id MUST exactly match an entity id in
     the entities list.
  3. Only extract entities and relationships EXPLICITLY stated in the text.
  4. If no clinical entities exist, output: {{"entities": [], "relationships": []}}
</instructions>

<example>
Input: "Metformin significantly reduces HbA1c in T2D patients. Nausea is a common \
side effect of metformin. T2D patients frequently present with polyuria."
Output: {{"entities": [{{"id": "metformin", "name": "Metformin", "type": "Drug"}}, \
{{"id": "type_2_diabetes_mellitus", "name": "Type 2 Diabetes Mellitus", "type": "Disease"}}, \
{{"id": "glycated_hemoglobin_hba1c", "name": "Glycated Hemoglobin HbA1c", "type": "Symptom"}}, \
{{"id": "nausea", "name": "Nausea", "type": "Symptom"}}, \
{{"id": "polyuria", "name": "Polyuria", "type": "Symptom"}}], \
"relationships": [{{"source_id": "metformin", "target_id": "type_2_diabetes_mellitus", "type": "TREATS"}}, \
{{"source_id": "metformin", "target_id": "glycated_hemoglobin_hba1c", "type": "CAUSES_SIDE_EFFECT"}}, \
{{"source_id": "metformin", "target_id": "nausea", "type": "CAUSES_SIDE_EFFECT"}}, \
{{"source_id": "type_2_diabetes_mellitus", "target_id": "polyuria", "type": "HAS_SYMPTOM"}}]}}
</example>"""

_HUMAN = """\
<input>
{abstract}
</input>"""

# ── Chain ─────────────────────────────────────────────────────────────────────
# llama3 (pre-3.1) has no native tool/function-calling support. Setting
# format="json" on ChatOllama activates Ollama's server-side JSON enforcement —
# the grammar sampler guarantees valid JSON output regardless of model stubbornness.
# We then validate the raw JSON against the Pydantic schema explicitly, which is
# the functional equivalent of with_structured_output for tool-calling-capable models.

_llm = ChatOllama(model="llama3.2:1b", temperature=0.0, base_url=_OLLAMA_URL, format="json")
_prompt = ChatPromptTemplate.from_messages([
    ("system", _SYSTEM),
    ("human", _HUMAN),
])
_chain = _prompt | _llm | StrOutputParser()

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```")


def _prune_dangling(extraction: GraphExtraction) -> GraphExtraction:
    """Drop relationships whose source_id or target_id don't match any entity.

    Small local models occasionally emit a relationship type as an entity ID
    (e.g. target_id="has_symptom"). Pruning keeps the graph structurally valid.
    """
    entity_ids = {e.id for e in extraction.entities}
    valid = [
        r for r in extraction.relationships
        if r.source_id in entity_ids and r.target_id in entity_ids
    ]
    return GraphExtraction(entities=extraction.entities, relationships=valid)


def extract_graph(abstract: str) -> GraphExtraction:
    """Extract entities and relationships from a PubMed abstract.

    Invokes llama3.2:1b via Ollama JSON mode, validates the response against the
    GraphExtraction Pydantic schema, and prunes any dangling relationships.
    """
    raw = _chain.invoke({"abstract": abstract})
    clean = _FENCE_RE.sub("", raw).strip()
    extraction = GraphExtraction.model_validate(json.loads(clean))
    return _prune_dangling(extraction)
