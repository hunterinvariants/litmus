# Litmus scoring specification v1

## Artifact contracts

- Cases: `schema/case.v1.schema.json`
- Tool findings: `schema/findings.v1.schema.json`
- Scorecards: `schema/scorecard.v1.schema.json`

Breaking shape changes require a new schema file. Existing v1 artifacts remain immutable.

## Matching

A finding matches a ground-truth label when it names the same case and contract, uses the same or an
explicitly aliased vulnerability class, and, when both sides name a function, names the same function.
The first match is a true positive; additional matches to that label are duplicates. An unmatched
finding is a false positive. An unmatched label is a false negative.

## Metrics

- `precision = TP / (TP + FP)`
- `recall = TP / (TP + FN)`
- `F1 = 2 * precision * recall / (precision + recall)`
- `false_positives_per_case = FP / selected cases`

Metrics are rounded to six decimal places in deterministic JSON scorecards. Findings outside an
explicit `--only` scope are excluded rather than counted against a tool for unselected cases.

## Ground-truth admission

Ground truth requires either a runnable exploit/safe-control proof or an immutable external teaching
corpus with documented intended vulnerabilities. A scored tool's output is never sufficient evidence
for adding or changing a label.