#!/usr/bin/env python3
"""Deterministically score normalized findings against Litmus ground truth."""

import argparse
import glob
import json
import os
from pathlib import Path

CLASS_ALIASES = {
    "reentrancy": "reentrancy", "temporal": "reentrancy", "read-only-reentrancy": "reentrancy",
    "callback": "reentrancy", "rounding": "rounding-precision", "precision": "rounding-precision",
    "rounding-precision": "rounding-precision", "truncation": "rounding-precision",
    "economic": "economic", "game-theory": "economic", "incentive": "economic",
    "oracle": "oracle", "pricing": "oracle", "price": "oracle",
    "init": "init-upgrade", "upgrade": "init-upgrade", "init-upgrade": "init-upgrade",
    "initialization": "init-upgrade", "accounting": "accounting-desync",
    "accounting-desync": "accounting-desync", "conservation": "accounting-desync",
    "desync": "accounting-desync", "signature": "signature-replay",
    "replay": "signature-replay", "merkle": "signature-replay",
    "signature-replay": "signature-replay", "dos": "liveness-dos",
    "liveness": "liveness-dos", "liveness-dos": "liveness-dos",
}


def canon(value):
    if not value:
        return ""
    normalized = value.strip().lower()
    return CLASS_ALIASES.get(normalized, normalized)


def load_ground_truth(bench_dir):
    ground_truth = {}
    for path in sorted(glob.glob(os.path.join(bench_dir, "case*.json"))):
        case = json.loads(Path(path).read_text(encoding="utf-8"))
        ground_truth[case["id"]] = [
            {
                "contract": (label.get("contract") or "").lower(),
                "function": (label.get("function") or "").lower(),
                "class": canon(label.get("class")),
                "detected": False,
            }
            for label in case.get("ground_truth", [])
        ]
    return ground_truth


def finding_matches(finding, label):
    if (finding.get("contract") or "").lower() != label["contract"]:
        return False
    finding_class = canon(finding.get("vuln_class"))
    if label["class"] and finding_class and finding_class != label["class"]:
        return False
    finding_function = (finding.get("function") or "").lower()
    return not (label["function"] and finding_function and finding_function != label["function"])


def score(ground_truth, findings):
    true_positive = false_positive = duplicates = 0
    for finding in findings:
        match = next(
            (label for label in ground_truth.get(finding.get("case_id"), [])
             if finding_matches(finding, label)),
            None,
        )
        if match is None:
            false_positive += 1
        elif match["detected"]:
            duplicates += 1
        else:
            match["detected"] = True
            true_positive += 1
    false_negative = sum(
        1 for labels in ground_truth.values() for label in labels if not label["detected"]
    )
    return true_positive, false_positive, false_negative, duplicates


def ratio(numerator, denominator):
    return round(numerator / denominator, 6) if denominator else 0.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--findings", required=True, type=Path)
    parser.add_argument("--bench", default=Path(__file__).resolve().parents[1] / "bench", type=Path)
    parser.add_argument("--only", default="")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    ground_truth = load_ground_truth(args.bench)
    if args.only:
        selected = sorted(item.strip() for item in args.only.split(",") if item.strip())
        unknown = sorted(set(selected) - set(ground_truth))
        if unknown:
            raise SystemExit(f"unknown case ids: {', '.join(unknown)}")
        ground_truth = {key: ground_truth[key] for key in selected}
    else:
        selected = sorted(ground_truth)

    document = json.loads(args.findings.read_text(encoding="utf-8"))
    findings = [item for item in document.get("findings", []) if item.get("case_id") in ground_truth]
    tp, fp, fn, duplicates = score(ground_truth, findings)
    cases = len(ground_truth)
    labels = sum(len(items) for items in ground_truth.values())
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    f1 = ratio(2 * precision * recall, precision + recall)
    result = {
        "schema_version": "1.0.0",
        "tool": document.get("tool", "unknown"),
        "scope": {
            "case_ids": selected,
            "cases": cases,
            "ground_truth_labels": labels,
            "findings": len(findings),
        },
        "counts": {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "duplicates": duplicates,
        },
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "false_positives_per_case": ratio(fp, cases),
        },
        "limitations": [
            "Scores apply only to the selected Litmus cases and labels.",
            "A score is not an audit, safety certificate, or production-readiness proof."
        ],
    }
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"Litmus scorecard -- tool: {result['tool']}")
    print(f"  cases: {cases}   ground-truth labels: {labels}   findings submitted: {len(findings)}")
    print(f"  true positives : {tp}")
    print(f"  false positives: {fp}   (duplicates ignored: {duplicates})")
    print(f"  false negatives: {fn}")
    print(f"  precision      : {precision:.3f}")
    print(f"  recall         : {recall:.3f}")
    print(f"  F1             : {f1:.3f}")
    print(f"  FP rate        : {ratio(fp, cases):.3f} false alarms per case")


if __name__ == "__main__":
    main()