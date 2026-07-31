# Litmus

[![benchmark integrity](https://github.com/hunterinvariants/litmus/actions/workflows/ci.yml/badge.svg)](https://github.com/hunterinvariants/litmus/actions/workflows/ci.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![cases](https://img.shields.io/badge/cases-5%20versioned-informational)](#corpus)

A reproducible benchmark for smart-contract vulnerability detectors. Litmus measures precision,
recall, F1, and false alarms per case against versioned ground truth backed by executable Foundry
proofs or immutable external teaching corpora.

Security tools tend to report the findings they caught and stay quiet about the ones they invented,
which makes "it detects X" unfalsifiable. Litmus makes the claim checkable: every case has a proof
you can execute, ground truth you can read, and a score you can regenerate offline.

## What is delivered

- five versioned benchmark cases: three offline synthetic PoCs, one Euler mainnet-fork PoC, and the
  external `7702-goat` corpus pinned to commit `5626163a3ebbda450cb94df28735b8e09595a212`;
- JSON Schemas for cases, normalized findings, and scorecards;
- deterministic machine-readable scoring;
- adapters for stock Slither and [Aegis-7702](https://github.com/hunterinvariants/aegis-7702) scan
  artifacts;
- committed raw inputs, normalized findings, scorecards, and a generated evidence report;
- commit-pinned dependencies and GitHub Actions.

## Reproduce

```text
git clone --recurse-submodules https://github.com/hunterinvariants/litmus.git
cd litmus
python -m pip install -r requirements-dev.txt
python scripts/verify_evidence.py
forge test -vv
```

The Euler fork case runs only when `ETH_RPC_URL` is configured. All other Foundry cases and all
committed scorecards reproduce offline after dependencies are installed.

## Current EIP-7702 comparison

Case 005, the `7702-goat` corpus:

| Tool | TP | FP | FN | Precision | Recall | FP/case |
|---|---:|---:|---:|---:|---:|---:|
| [Aegis-7702](https://github.com/hunterinvariants/aegis-7702) v1.0.0 | 18 | 0 | 0 | 1.000 | 1.000 | 0.000 |
| Stock Slither 0.11.5 | 1 | 41 | 17 | 0.024 | 0.056 | 41.000 |

Read this narrowly. It is one intentionally vulnerable external corpus -- one that Aegis-7702 was
built to catch -- not a representative security-tool ranking. Aegis-7702 and Litmus share a
maintainer, so the result is reproducible integration rather than independent validation. For what
that tool looks like on code nobody chose for it, see its
[measured precision on production delegates](https://github.com/hunterinvariants/aegis-7702/blob/main/docs/EVIDENCE.md)
(0.22). Method and governance here: `docs/EVIDENCE.md`, `docs/METHODOLOGY.md`, `docs/GOVERNANCE.md`.

## Corpus

| Case | Class | Evidence |
|---|---|---|
| 001 | rounding / precision | ERC-4626 inflation PoC |
| 002 | reentrancy / temporal | read-only reentrancy PoC |
| 003 | accounting desynchronization | fee-on-transfer PoC |
| 004 | accounting / solvency | Euler mainnet-fork PoC |
| 005 | EIP-7702 delegation | external `7702-goat` corpus |

## Use another tool

Emit findings conforming to `schema/findings.v1.schema.json`, then run:

```text
python harness/score.py --findings tool-findings.json --json-out tool-scorecard.json
```

The matching and scoring contract is documented in `SPEC.md`.

## Non-claims

Litmus does not audit tools or contracts, prove absence of vulnerabilities, or provide a statistically
representative ranking. Scores apply only to the selected versioned cases and labels.

## License

MIT.