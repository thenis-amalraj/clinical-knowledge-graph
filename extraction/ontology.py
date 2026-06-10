"""Pydantic V2 ontology models for clinical knowledge graph extraction."""

from typing import Literal

from pydantic import BaseModel, Field


class Entity(BaseModel):
    id: str = Field(
        description=(
            "Canonical lowercase snake_case identifier after full disambiguation. "
            "Examples: 'type_2_diabetes_mellitus', 'metformin', 'hyperglycemia'."
        )
    )
    name: str = Field(description="Human-readable canonical display name.")
    type: Literal["Disease", "Drug", "Symptom"] = Field(
        description="Ontological class: Disease, Drug, or Symptom."
    )


class Relationship(BaseModel):
    source_id: str = Field(description="id of the source entity.")
    target_id: str = Field(description="id of the target entity.")
    type: Literal["TREATS", "CAUSES_SIDE_EFFECT", "HAS_SYMPTOM"] = Field(
        description=(
            "TREATS: Drug→Disease. "
            "CAUSES_SIDE_EFFECT: Drug→Symptom. "
            "HAS_SYMPTOM: Disease→Symptom."
        )
    )


class GraphExtraction(BaseModel):
    entities: list[Entity] = Field(
        default_factory=list,
        description="All distinct clinical entities extracted from the text.",
    )
    relationships: list[Relationship] = Field(
        default_factory=list,
        description="All clinical relationships between extracted entities.",
    )
