#!/usr/bin/env python3
"""Convert an Aegis-7702 scan artifact to Litmus findings."""

import argparse
import json
from pathlib import Path

STOCK_CLASS_MAP = {
    "arbitrary-send-eth": "eip7702-unprotected-entrypoint",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--case-id", default="case005")
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8"))
    tool = source["tool"]["name"]
    findings = []
    for finding in source["findings"]:
        check = finding["check"]
        vuln_class = check if tool == "slither-eip7702" else STOCK_CLASS_MAP.get(check, check)
        findings.append({
            "case_id": args.case_id,
            "contract": finding.get("contract") or "<project>",
            "function": finding.get("function"),
            "vuln_class": vuln_class,
            "severity": finding.get("impact"),
            "note": f"{check}: {finding.get('description', '')}",
        })

    result = {
        "schema_version": "1.0.0",
        "tool": tool,
        "tool_version": source["tool"].get("version"),
        "source_artifact": args.input.as_posix(),
        "findings": sorted(
            findings,
            key=lambda item: (
                item["case_id"],
                item["contract"],
                item.get("function") or "",
                item["vuln_class"],
                item.get("note") or "",
            ),
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
