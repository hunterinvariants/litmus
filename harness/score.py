#!/usr/bin/env python3
"""Litmus scoring harness.

Reads ground-truth labels from bench/*.json and a tool's findings (JSON),
matches findings to labels, and reports precision, recall and -- the metric
that actually matters -- the false-positive rate (false alarms per case).

Usage:
    python harness/score.py --findings path/to/tool-output.json
    python harness/score.py --findings harness/example-findings.json
"""
import argparse
import glob
import json
import os

# Map synonymous class names onto a canonical key so a tool is not penalised
# merely for using different vocabulary than the label.
CLASS_ALIASES = {
    "reentrancy": "reentrancy", "temporal": "reentrancy", "read-only-reentrancy": "reentrancy",
    "callback": "reentrancy",
    "rounding": "rounding-precision", "precision": "rounding-precision",
    "rounding-precision": "rounding-precision", "truncation": "rounding-precision",
    "economic": "economic", "game-theory": "economic", "incentive": "economic",
    "oracle": "oracle", "pricing": "oracle", "price": "oracle",
    "init": "init-upgrade", "upgrade": "init-upgrade", "init-upgrade": "init-upgrade",
    "initialization": "init-upgrade",
    "accounting": "accounting-desync", "accounting-desync": "accounting-desync",
    "conservation": "accounting-desync", "desync": "accounting-desync",
    "signature": "signature-replay", "replay": "signature-replay", "merkle": "signature-replay",
    "signature-replay": "signature-replay",
    "dos": "liveness-dos", "liveness": "liveness-dos", "liveness-dos": "liveness-dos",
}


def canon(c):
    if not c:
        return ""
    return CLASS_ALIASES.get(c.strip().lower(), c.strip().lower())


def load_ground_truth(bench_dir):
    gt = {}
    for path in sorted(glob.glob(os.path.join(bench_dir, "*.json"))):
        with open(path) as f:
            case = json.load(f)
        cid = case["id"]
        gt[cid] = []
        for g in case.get("ground_truth", []):
            gt[cid].append({
                "contract": (g.get("contract") or "").lower(),
                "function": (g.get("function") or "").lower(),
                "class": canon(g.get("class")),
                "detected": False,
            })
    return gt


def finding_matches(finding, g):
    if (finding.get("contract") or "").lower() != g["contract"]:
        return False
    fclass = canon(finding.get("vuln_class"))
    if g["class"] and fclass and fclass != g["class"]:
        return False
    ffunc = (finding.get("function") or "").lower()
    if g["function"] and ffunc and ffunc != g["function"]:
        return False
    return True


def score(gt, findings):
    tp = fp = dup = 0
    for fnd in findings:
        cid = fnd.get("case_id")
        hit = None
        for g in gt.get(cid, []):
            if finding_matches(fnd, g):
                hit = g
                break
        if hit is None:
            fp += 1
        elif hit["detected"]:
            dup += 1
        else:
            hit["detected"] = True
            tp += 1
    fn = sum(1 for cands in gt.values() for g in cands if not g["detected"])
    return tp, fp, fn, dup


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--findings", required=True)
    ap.add_argument("--bench", default=os.path.join(os.path.dirname(__file__), "..", "bench"))
    ap.add_argument("--only", default="",
                    help="comma-separated case ids to score against (e.g. for a static tool that "
                         "cannot run the fork-cases). Default: all cases.")
    args = ap.parse_args()

    gt = load_ground_truth(args.bench)
    if args.only:
        keep = set(s.strip() for s in args.only.split(",") if s.strip())
        gt = {k: v for k, v in gt.items() if k in keep}
    num_cases = len(gt)
    total_labels = sum(len(v) for v in gt.values())

    with open(args.findings) as f:
        data = json.load(f)
    tool = data.get("tool", "unknown")
    findings = data.get("findings", [])

    tp, fp, fn, dup = score(gt, findings)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    fp_per_case = fp / num_cases if num_cases else 0.0

    print("Litmus scorecard -- tool: {}".format(tool))
    print("  cases: {}   ground-truth labels: {}   findings submitted: {}".format(
        num_cases, total_labels, len(findings)))
    print("  true positives : {}".format(tp))
    print("  false positives: {}   (duplicates ignored: {})".format(fp, dup))
    print("  false negatives: {}".format(fn))
    print("  precision      : {:.3f}".format(precision))
    print("  recall         : {:.3f}".format(recall))
    print("  F1             : {:.3f}".format(f1))
    print("  FP rate        : {:.3f} false alarms per case   <-- the metric that matters".format(fp_per_case))


if __name__ == "__main__":
    main()
