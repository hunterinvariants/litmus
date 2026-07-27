#!/usr/bin/env python3
"""Regenerate committed adapters, scorecards, and report deterministically."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args: str) -> None:
    subprocess.run([sys.executable, *args], cwd=ROOT, check=True)


def main() -> None:
    provenance = json.loads((ROOT / "evidence/provenance.json").read_text(encoding="utf-8"))
    for artifact in provenance["artifacts"]:
        actual = hashlib.sha256((ROOT / artifact["artifact"]).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if actual != artifact["sha256"]:
            raise SystemExit(f"hash mismatch for {artifact['artifact']}: {actual}")
    pairs = [
        ("evidence/raw/aegis-7702-goat.json", "evidence/findings/aegis-7702.json",
         "evidence/scorecards/aegis-7702.json"),
        ("evidence/raw/stock-slither-goat.json", "evidence/findings/stock-slither.json",
         "evidence/scorecards/stock-slither.json"),
    ]
    for raw, findings, scorecard in pairs:
        run("tools/aegis_to_litmus.py", raw, "--out", findings)
        run("harness/score.py", "--findings", findings, "--only", "case005", "--json-out", scorecard)
    run("tools/validate_artifacts.py")
    run("tools/report.py", "--out", "docs/EVIDENCE.md")


if __name__ == "__main__":
    main()
