---
type: compound-learning
shipment: 157-S
feature: 149-F
task: 149.010-T
date: 2026-08-30
problem_type: sdk_boundary_validation_incomplete
category: best-practices
root_cause: A JSON-serializability check on `NodeResult.details`/`provenance` alone was necessary but not sufficient to guarantee safe downstream consumption -- `report.py`'s `_merged_provenance` calls `dict(result.provenance)` directly, which raises for a JSON-serializable-but-non-dict value such as a list, and `message`/`token` were not checked at all despite being unenforced at runtime.
resolution_type: fix
severity: medium
source: docs/compound/2026-08-30-157-s-149-f-sdk-boundary-payload-completeness.md
doc_type: learning
title: "An SDK boundary's serializability check must validate the complete contract payload, not just the fields a crash was observed for"
citations:
  - src/autoharness/detectors/assembler.py
  - src/autoharness/detectors/report.py
tags:
  - sdk-boundary-validation
  - copilot-review
  - best-practices
---

# An SDK boundary's serializability check must validate the complete contract payload

## Problem

157-S round 7 added a check that `NodeResult.details`/`NodeResult.provenance`
are JSON-serializable (via `json.dumps`) before accepting a validator's
result. Round 8's Copilot hosted review found this insufficient on two axes.

## Root Cause

1. **JSON-serializable is necessary but not sufficient for "this field is
   consumed as a dict downstream."** `report.py`'s `_merged_provenance` calls
   `dict(result.provenance)`, and a plain `list` (e.g. `["x"]`) *is*
   JSON-serializable but still raises there. When a downstream consumer does
   more than `json.dumps` a field verbatim (e.g. reshapes it via `dict()`,
   iterates expecting key/value semantics), the SDK boundary check must
   validate the actual required shape, not merely "can this be serialized at
   all."
2. **Checking only the fields a crash was observed for under-covers the
   contract.** `message`/`token` are typed `str`/`str | None` on the
   dataclass but are not runtime-enforced -- a detector could still assign a
   non-string value to either, and it would reach `emit_pre_review_report`'s
   `json.dumps(payload)` uncaught, because the original check never looked at
   those two fields.

## Resolution

Replaced the narrower `details`/`provenance`-only check with
`_has_malformed_result_payload()`, which requires `details`/`provenance` to
be actual `dict` instances **and** requires the complete
`NodeResult.to_dict()` payload to be JSON-serializable end to end -- catching
non-serializable `message`/`token` values too, despite the unenforced type
hints.

## Prevention

When hardening an SDK boundary against a malformed producer/validator
payload, validate the full serialized contract surface (the object's own
`to_dict()` or equivalent canonical serialization), not just the specific
field(s) the triggering example used. A narrower check reliably resurfaces
as a "found one more bypass" finding in the next review round, exactly as
happened here (round 7's narrower check was superseded by round 8's
complete-payload check).
