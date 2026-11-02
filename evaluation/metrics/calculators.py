"""Deterministic metrics for recorded AgentTutor evaluation outcomes.

The functions in this module only summarize supplied observations. They do not
run a model or infer results for missing samples.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from statistics import mean
from typing import Any


def mean_value(values: Iterable[float]) -> float | None:
    """Return the arithmetic mean, or ``None`` when no observations exist."""
    values = list(values)
    return mean(values) if values else None


def binary_rate(values: Iterable[bool]) -> float | None:
    """Return the proportion of true observations."""
    values = list(values)
    return sum(values) / len(values) if values else None


def repetition_rate(repeated_turns: Iterable[bool]) -> float | None:
    """Return the proportion of turns marked as repetitive."""
    return binary_rate(repeated_turns)


def summarize_records(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize recorded per-problem outcomes using only present fields.

    Supported fields are ``bug_fix_success``, ``tests_passed``,
    ``false_resolution``, ``verifier_correct``, ``question_relevant``,
    ``logical_flow``, ``repeated_turn``, ``turns``, ``retrieval_relevant``,
    ``citation_valid``, ``latency_ms``, and ``token_usage``.
    """
    records = list(records)
    summary: dict[str, Any] = {"sample_size": len(records)}

    for field in (
        "bug_fix_success",
        "tests_passed",
        "false_resolution",
        "verifier_correct",
        "question_relevant",
        "logical_flow",
        "retrieval_relevant",
        "citation_valid",
    ):
        values = [record[field] for record in records if field in record]
        if values:
            summary[field] = binary_rate(values)

    repeated = [record["repeated_turn"] for record in records if "repeated_turn" in record]
    if repeated:
        summary["repetition_rate"] = repetition_rate(repeated)

    for field in ("turns", "latency_ms", "token_usage"):
        values = [record[field] for record in records if field in record]
        if values:
            summary[f"mean_{field}"] = mean_value(values)

    return summary