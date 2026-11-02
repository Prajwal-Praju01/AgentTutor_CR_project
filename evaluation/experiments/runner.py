"""CLI for summarizing recorded evaluation outcomes.

This runner deliberately does not call an LLM. Capture results with the
application under test, then pass the JSON records to this command.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from evaluation.metrics.calculators import summarize_records


def load_records(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array of per-problem outcome records."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        raise ValueError("Results file must contain a JSON array of objects")
    return payload


def build_report(input_path: Path, experiment: str, condition: str) -> dict[str, Any]:
    records = load_records(input_path)
    return {
        "experiment_name": experiment,
        "condition": condition,
        "source_file": str(input_path),
        "results": summarize_records(records),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON array of recorded outcomes")
    parser.add_argument("--experiment", required=True)
    parser.add_argument("--condition", choices=("A", "B", "C", "D", "E"), required=True)
    parser.add_argument("--output", type=Path, help="Optional path for the JSON report")
    args = parser.parse_args()

    report = build_report(args.input, args.experiment, args.condition)
    serialized = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    else:
        print(serialized)


if __name__ == "__main__":
    main()