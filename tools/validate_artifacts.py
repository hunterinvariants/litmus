#!/usr/bin/env python3
"""Validate Litmus cases and evidence artifacts against versioned schemas."""

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def validate(path: Path, schema_path: Path) -> None:
    document = json.loads(path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(document), key=lambda e: list(e.path))
    if errors:
        detail = "\n".join(f"{path}: {'/'.join(map(str, e.path))}: {e.message}" for e in errors)
        raise SystemExit(detail)
    print(f"[OK] {path.relative_to(ROOT)}")


def main() -> None:
    for path in sorted((ROOT / "bench").glob("case*.json")):
        validate(path, ROOT / "schema/case.v1.schema.json")
    for path in sorted((ROOT / "evidence/findings").glob("*.json")):
        validate(path, ROOT / "schema/findings.v1.schema.json")
    for path in sorted((ROOT / "evidence/scorecards").glob("*.json")):
        validate(path, ROOT / "schema/scorecard.v1.schema.json")


if __name__ == "__main__":
    main()
