# Methodology and non-claims

Litmus measures submitted findings against versioned ground truth. A match
requires the same case and contract, a compatible vulnerability class, and,
when both sides name one, the same function. Duplicate matches do not improve a
score. Unmatched findings are false positives.

Ground truth requires an executable PoC or an immutable external teaching
corpus with documented vulnerable behavior. Tool output never creates ground
truth.

## Non-claims

- A high score is not an audit, safety certificate, or production-readiness proof.
- Recall applies only to included labels; unknown production bugs are not counted.
- Precision depends on corpus composition and must not be generalized statistically.
- The EIP-7702 comparison is maintained by the same owner as Aegis-7702 and is
  not independent validation.
- Stock Slither is a general analyzer; the comparison measures this corpus, not
  which tool is universally better.
