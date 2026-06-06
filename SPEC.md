# Litmus - case &amp; scoring specification

## Repository layout

```
src/    <case>/         scan targets — the contract sources a tool analyses
test/   <case>/         runnable Foundry PoCs — a passing test proves the bug
bench/  <case>.json     machine-readable metadata + ground truth
harness/score.py        the scoring harness
```

## Case metadata - `bench/<case>.json`

```json
{
  "id": "case001",
  "title": "ERC4626 first-depositor share inflation",
  "vuln_class": "rounding-precision",
  "class_id": 2,
  "severity": "High",
  "source": { "type": "synthetic", "inspired_by": "..." },
  "scan_target": "src/case001_erc4626_inflation/NaiveVault.sol",
  "poc": "test/case001_erc4626_inflation/InflationPoC.t.sol",
  "poc_test": "test_firstDepositorInflationStealsVictimDeposit",
  "expected": "pass",
  "ground_truth": [
    {
      "contract": "NaiveVault",
      "function": "deposit",
      "lines": [27, 37],
      "class": "rounding-precision",
      "description": "..."
    }
  ]
}
```

`source.type` is `real` (a historical on-chain exploit; the PoC runs against a fork) or
`synthetic` (a minimal, self-contained reproduction of a known bug class).

A `real` case declares `requires_env` (e.g. `["ETH_RPC_URL"]`); its PoC forks mainnet and is
skipped automatically when that RPC is not configured, so the synthetic corpus always runs
offline. The `scan_target` of a `real` case is an abridged excerpt of the deployed source under
`reference/` (not compiled); the proof of the label is the fork PoC running against live bytecode.

## Tool output - what a scored tool must emit

A single JSON document:

```json
{
  "tool": "your-tool-name",
  "findings": [
    {
      "case_id": "case001",
      "contract": "NaiveVault",
      "function": "deposit",
      "lines": [30, 36],
      "vuln_class": "rounding-precision",
      "severity": "High",
      "note": "optional free text"
    }
  ]
}
```

`function` and `lines` are optional but improve match precision. `vuln_class` is matched
through an alias table (see `harness/score.py`) so a tool is not penalised for vocabulary —
`reentrancy` == `temporal`, `rounding` == `precision`, `desync` == `accounting`, and so on.

## Scoring

A finding **matches** a ground-truth label iff:

- same `contract`, **and**
- compatible `vuln_class` (after alias normalisation), **and**
- if both sides specify a `function`, the same function.

From the matches:

- **True positive (TP)** - a ground-truth label matched by at least one finding.
- **False negative (FN)** - a ground-truth label matched by no finding.
- **False positive (FP)** - a finding that matches *no* ground-truth label in its case.
- Extra findings matching an already-matched label are **duplicates** (reported, not penalised).

Metrics:

- `precision = TP / (TP + FP)`
- `recall    = TP / (TP + FN)`
- `F1        = harmonic mean of precision and recall`
- **`FP rate = FP / number-of-cases`** — average false alarms per case, the noise-floor metric.

A strong tool maximises recall **while keeping the FP rate low.** Recall alone is gameable by
flagging everything; Litmus is designed so that strategy scores badly.
