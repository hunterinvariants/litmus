# Litmus

*A false-positive-aware benchmark for smart-contract vulnerability detection.*

> Working name - provisional.

## Why

Automated and AI-assisted auditors are almost always measured on one axis: **recall** -
*did it find the bug?* But the cost that actually breaks triage is the other axis:
**false positives.** A tool that reports fifty "criticals" to surface one real bug is worse
than useless - it buries the signal and burns reviewer time. Open contests routinely collect
thousands of submissions that collapse, after judging, to a handful of unique valid issues;
the rest is noise.

No widely-used benchmark scores that noise. Litmus does.

## What it is

A corpus of smart-contract vulnerabilities where every label is **proven, not asserted**:

- **A scan target** - the contract source a tool analyses.
- **A runnable Foundry PoC** - an executable exploit. A *passing* test means the bug is real.
  The ground truth is justified by code that runs, not by a human's tag.
- **Machine-readable ground truth** - the exact location and class of each vulnerability.

…plus a **scoring harness** any tool can be run against, reporting precision, recall, and the
headline metric: **false alarms per case.**

## How to run

```bash
# 1. Verify every label is backed by a real, runnable exploit:
git init -q && forge install foundry-rs/forge-std
forge test -vv          # synthetic cases (001-003) run with no network

# The real on-chain case (004, Euler) forks mainnet -- point it at an archive RPC:
ETH_RPC_URL=<your-mainnet-rpc> forge test -vv

# 2. Score a tool's output against the ground truth:
python harness/score.py --findings harness/example-findings.json
```

The findings format a tool must emit is defined in [SPEC.md](SPEC.md); an example lives in
`harness/example-findings.json`.

## Design principle

**Every ground-truth label is backed by an executable PoC.** This is what separates Litmus
from static vulnerability datasets: a label isn't trusted because someone tagged it - it's
trusted because `forge test` reproduces the exploit on demand. A tool's recall is measured
against bugs that demonstrably exist, and its noise is measured against the same fixed corpus.

## Status - v0

This is the v0 corpus: the case format, the scoring harness, and four cases wired end-to-end -
three synthetic plus one real, on-chain exploit. The corpus scales from here.

| Case | Class | Source | PoC |
|------|-------|--------|-----|
| 001  | rounding / precision | ERC4626 first-depositor inflation (synthetic) | runnable |
| 002  | reentrancy / temporal | read-only reentrancy in an LP price oracle (synthetic) | runnable |
| 003  | accounting-desync | cached total vs. fee-on-transfer real balance (synthetic) | runnable |
| 004  | accounting-desync (missing solvency check) | **Euler Finance — real, $197M** | fork (needs `ETH_RPC_URL`) |

The corpus already includes one **real, on-chain exploit** - the March 2023 **Euler Finance
$197M** loss - reproduced against deployed mainnet bytecode, not a mock. Every other label is a
self-contained synthetic reproduction of a known bug class.

**Roadmap:** grow the corpus across the eight-class taxonomy (reentrancy/temporal,
rounding/precision, economic/game-theory, oracle, init/upgrade, accounting-desync,
signature/replay, liveness/DoS); add more real historical exploits alongside Euler; and ship
output adapters for common static and AI tools.

## First result - stock Slither

Stock Slither (standard detectors, no plugins), scored through the harness on the
source-analyzable cases:

| Tool | recall | precision | FP rate (alarms / case) |
|------|:------:|:---------:|:-----------------------:|
| Slither (stock) | 0.33 | 0.14 | 2.0 |

It catches the **read-only reentrancy** - pattern-matching is exactly its strength - but is
**blind to the inflation attack (001) and the accounting-desync (003)**: it ships no detector
for either, because both require reasoning about economic intent rather than syntax. Of three
PoC-proven exploits it flags one, and none of its other results points at the two that actually
drain the vault.

(In fairness, a couple of those extra flags are legitimate low-severity smells, not pure noise -
but none is the exploitable bug. That's the point: recall on *real impact* is what matters, and a
low false-positive rate is what makes a tool's output worth reading.)

Reproduce:

```
slither . --filter-paths "lib/|test/" --json slither-out.json
python harness/adapters/slither_to_litmus.py slither-out.json > slither-findings.json
python harness/score.py --findings slither-findings.json --only case001,case002,case003
```

AI-assisted auditors next.

## License

MIT. Contributions welcome - see [SPEC.md](SPEC.md) for the case format.
