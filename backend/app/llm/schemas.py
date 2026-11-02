"""Pydantic schemas for LLM structured outputs."""
from __future__ import annotations
import json
from pydantic import BaseModel, Field, field_validator


class AssessmentOutput(BaseModel):
    understanding_level: int = Field(ge=0, le=3)
    justification: str
    confidence: float = Field(ge=0.0, le=1.0)
    misconceptions: list[str] = Field(default_factory=list)
    recommended_hint_depth: int = Field(ge=1, le=4)


class VerifierOutput(BaseModel):
    verdict: str  # correct | partially_correct | incorrect | uncertain
    justification: str
    confidence: float = Field(ge=0.0, le=1.0)
    key_points_identified: list[str] = Field(default_factory=list)
    key_points_missing: list[str] = Field(default_factory=list)

    @field_validator("verdict")
    @classmethod
    def validate_verdict(cls, v: str) -> str:
        allowed = {"correct", "partially_correct", "incorrect", "uncertain"}
        if v not in allowed:
            raise ValueError(f"verdict must be one of {allowed}")
        return v


class InstructorOutput(BaseModel):
    question: str
    question_type: str  # root | child | sibling
    targets_concept: str
    reasoning: str  # internal only — not exposed to students

    @field_validator("question_type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"root", "child", "sibling"}
        if v not in allowed:
            raise ValueError(f"question_type must be one of {allowed}")
        return v


class FixValidatorOutput(BaseModel):
    is_correct: bool
    partially_correct: bool
    explanation: str
    remaining_issues: list[str] = Field(default_factory=list)
    syntax_notes: str = ""


def parse_json_output(raw: str, model_class):
    """
    Attempt to parse LLM JSON output into a Pydantic model.
    Strips markdown fences if present.
    """
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    data = json.loads(cleaned)
    return model_class.model_validate(data)

