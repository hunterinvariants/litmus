# Contributing

Case and label changes must include provenance, an executable PoC or immutable
external-corpus basis, schema-valid metadata, and regenerated scorecards.

Run:

```text
python scripts/verify_evidence.py
forge test -vv
```

Disclose any relationship to a scored tool. Tool-maintainer contributions are
welcome, but ground truth changes require evidence independent of tool output.
