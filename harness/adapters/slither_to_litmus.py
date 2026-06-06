#!/usr/bin/env python3
"""Adapter: convert Slither JSON output into Litmus findings.

Usage:
    slither . --json slither-out.json
    python harness/adapters/slither_to_litmus.py slither-out.json > slither-findings.json
    python harness/score.py --findings slither-findings.json --only case001,case002,case003

Fairness rules baked in:
  * Only High/Medium impact results are kept. Slither's informational, low and
    optimization detectors are linting, not vulnerability claims, so counting them
    as false positives would strawman the tool -- they are excluded.
  * A result is kept only if it lands on a benchmark scan-target contract. Findings
    on mocks, test helpers, and libraries are out of scope and dropped.
  * Reentrancy detectors map to the Litmus 'reentrancy' class; divide-before-multiply
    maps to 'rounding-precision'. Any other check keeps its own Slither name as the
    class, so it scores as a true positive ONLY if it genuinely matches a label --
    the adapter neither flatters nor strawmans.
"""
import glob
import json
import os
import sys

SLITHER_TO_CLASS = {
    "reentrancy-eth": "reentrancy",
    "reentrancy-no-eth": "reentrancy",
    "reentrancy-benign": "reentrancy",
    "reentrancy-events": "reentrancy",
    "reentrancy-unlimited-gas": "reentrancy",
    "divide-before-multiply": "rounding-precision",
}

KEEP_IMPACT = {"High", "Medium"}


def load_target_contracts(bench_dir):
    """contract name -> case_id, taken from the benchmark ground truth."""
    m = {}
    for path in sorted(glob.glob(os.path.join(bench_dir, "*.json"))):
        with open(path) as f:
            case = json.load(f)
        for g in case.get("ground_truth", []):
            c = g.get("contract")
            if c:
                m[c] = case["id"]
    return m


def contract_and_function(elements):
    for el in elements or []:
        if el.get("type") == "function":
            parent = (el.get("type_specific_fields") or {}).get("parent") or {}
            contract = parent.get("name") if parent.get("type") == "contract" else None
            return contract, el.get("name")
    for el in elements or []:
        if el.get("type") == "contract":
            return el.get("name"), None
    return None, None


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: slither_to_litmus.py <slither-output.json>\n")
        sys.exit(2)

    bench_dir = os.path.join(os.path.dirname(__file__), "..", "..", "bench")
    targets = load_target_contracts(bench_dir)

    with open(sys.argv[1]) as f:
        slither = json.load(f)

    detectors = (slither.get("results") or {}).get("detectors") or []
    findings = []
    for d in detectors:
        if d.get("impact") not in KEEP_IMPACT:
            continue
        contract, function = contract_and_function(d.get("elements"))
        if contract not in targets:
            continue  # out of scope: mock, test helper, library, or unlabeled contract
        check = d.get("check", "")
        findings.append({
            "case_id": targets[contract],
            "contract": contract,
            "function": function,
            "vuln_class": SLITHER_TO_CLASS.get(check, check),
            "severity": d.get("impact"),
            "note": "slither: {}".format(check),
        })

    json.dump({"tool": "slither", "findings": findings}, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
