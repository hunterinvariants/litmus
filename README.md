# Litmus

A benchmark for smart-contract vulnerability detectors, scored on the metric that decides whether a
tool is usable in practice: how much noise it makes. Every bug in the corpus is a runnable Foundry
PoC, so a label is trusted because `forge test` reproduces the exploit, not because someone tagged it.

## Why

Auto and AI-assisted auditors get measured on recall -- did it find the bug. The cost that actually
breaks triage is the other side: false positives. A tool that reports fifty criticals to surface one
real bug buries the signal and burns the reviewer's time. Open contests routinely take in thousands
of submissions that collapse, after judging, to a handful of unique valid issues; the rest is noise.
No widely-used benchmark scores that noise. This one does.

## What it is

A corpus of vulnerabilities where every label is proven, not asserted:

- a scan target -- the contract source a tool analyses.
- a runnable Foundry PoC -- an executable exploit; a passing test means the bug is real.
- machine-readable ground truth -- the exact location and class of each vulnerability.

Plus a scoring harness any tool can run against, reporting precision, recall, and the number that
matters: false alarms per case. A label is only added once its PoC runs, so the ground truth is code
that executes, not a human's tag.

## How to run

    git init -q && forge install foundry-rs/forge-std
    forge test -vv          # synthetic cases (001-003), no network

    # the real on-chain case (004, Euler) forks mainnet -- point it at an archive RPC:
    ETH_RPC_URL=<your-mainnet-rpc> forge test -vv

    # score a tool's findings against the ground truth:
    python harness/score.py --findings harness/example-findings.json

The findings format a tool must emit is in `SPEC.md`, with an example in `harness/example-findings.json`.

## The corpus

| Case | Class | Source | PoC |
|------|-------|--------|-----|
| 001  | rounding / precision | ERC-4626 first-depositor inflation (synthetic) | runnable |
| 002  | reentrancy / temporal | read-only reentrancy in an LP price oracle (synthetic) | runnable |
| 003  | accounting-desync | cached total vs. fee-on-transfer real balance (synthetic) | runnable |
| 004  | accounting-desync (missing solvency check) | Euler Finance, real, $197M | fork (needs `ETH_RPC_URL`) |

Case 004 is a real on-chain exploit -- the March 2023 Euler $197M loss -- reproduced against the
deployed mainnet bytecode, not a mock. The other three are self-contained reproductions of a known
bug class.

## First result: stock Slither

Stock Slither (standard detectors, no plugins), scored through the harness on the source-analyzable
cases:

| Tool | recall | precision | FP rate (alarms / case) |
|------|:------:|:---------:|:-----------------------:|
| Slither (stock) | 0.33 | 0.14 | 2.0 |

It catches the read-only reentrancy -- pattern-matching is its strength -- but is blind to the
inflation attack (001) and the accounting-desync (003): it ships no detector for either, because
both need reasoning about economic intent, not syntax. Of three PoC-proven exploits it flags one,
and none of its other results points at the two that drain the vault. (A couple of those extra flags
are real low-severity smells, not pure noise -- but none is the exploitable bug, which is the point:
recall on real impact is what counts, and a low false-positive rate is what makes a tool's output
worth reading.)

    slither . --filter-paths "lib/|test/" --json slither-out.json
    python harness/adapters/slither_to_litmus.py slither-out.json > slither-findings.json
    python harness/score.py --findings slither-findings.json --only case001,case002,case003

AI-assisted auditors next.

## Status

v0: the case format (`SPEC.md`), the scoring harness, the Slither adapter, and four cases -- three
synthetic plus the real Euler fork -- wired end to end. It grows from here: more of the eight-class
taxonomy (reentrancy/temporal, rounding/precision, economic/game-theory, oracle, init/upgrade,
accounting-desync, signature/replay, liveness/DoS), more real historical exploits, and output
adapters for common static and AI tools.

## License

MIT. Contributions welcome -- the case format is in `SPEC.md`.
