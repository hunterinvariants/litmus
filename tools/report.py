#!/usr/bin/env python3
"""Generate the evidence report from committed scorecards."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    scores = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "evidence/scorecards").glob("*.json"))
    ]
    lines = [
        "# Evidence report",
        "",
        "Generated from versioned scorecards. Do not edit by hand.",
        "",
        "## EIP-7702 external-corpus comparison",
        "",
        "| Tool | TP | FP | FN | Precision | Recall | F1 | FP/case |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for score in scores:
        c, m = score["counts"], score["metrics"]
        lines.append(
            f"| {score['tool']} | {c['true_positive']} | {c['false_positive']} | "
            f"{c['false_negative']} | {m['precision']:.3f} | {m['recall']:.3f} | "
            f"{m['f1']:.3f} | {m['false_positives_per_case']:.3f} |"
        )
    lines += [
        "",
        "Ground truth is the external `7702-goat` teaching corpus at commit "
        "`5626163a3ebbda450cb94df28735b8e09595a212`. Raw tool artifacts, normalized "
        "findings, and scorecards are committed under `evidence/`.",
        "",
        "## Limitations",
        "",
        "- This one-case comparison is illustrative, not statistically representative.",
        "- Aegis-7702 and Litmus share a maintainer; this is reproducible integration, not independent validation.",
        "- Stock Slither is general-purpose and is not expected to model EIP-7702-specific semantics.",
        "- A benchmark score is not an audit or safety certificate.",
        "",
    ]
    output = "\n".join(lines)
    destination = ROOT / args.out
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(output, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
