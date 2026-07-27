# Evidence report

Generated from versioned scorecards. Do not edit by hand.

## EIP-7702 external-corpus comparison

| Tool | TP | FP | FN | Precision | Recall | F1 | FP/case |
|---|---:|---:|---:|---:|---:|---:|---:|
| slither-eip7702 | 18 | 0 | 0 | 1.000 | 1.000 | 1.000 | 0.000 |
| slither | 1 | 41 | 17 | 0.024 | 0.056 | 0.033 | 41.000 |

Ground truth is the external `7702-goat` teaching corpus at commit `5626163a3ebbda450cb94df28735b8e09595a212`. Raw tool artifacts, normalized findings, and scorecards are committed under `evidence/`.

## Limitations

- This one-case comparison is illustrative, not statistically representative.
- Aegis-7702 and Litmus share a maintainer; this is reproducible integration, not independent validation.
- Stock Slither is general-purpose and is not expected to model EIP-7702-specific semantics.
- A benchmark score is not an audit or safety certificate.
