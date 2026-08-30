---
type: compound-learning
title: "157-S/149-F Detector SDK: eight Copilot review rounds, a third schema-mutation-in-place occurrence, and NodeResult payload-completeness gaps"
date: 2026-08-30
shipment: 157-S
feature: 149-F
source: docs/compound/2026-08-30-157-s-149-f-detector-sdk-copilot-review-eight-rounds.md
doc_type: learning
tags: [copilot-review, schema-versioning, sdk-boundary-validation, p-021]
---

# 157-S/149-F: Eight Copilot Review Rounds -- Hard-Won Learnings

Shipment 157-S (detector SDK, evidence-node contract, `gate pre-review`)
went through **8 sequential Copilot hosted-review rounds** on PR #420 before
reaching `SATISFIED`. Every one of the ~25 total findings across all 8
rounds was a P-021 C1 same-contract-surface completion (verified via
`git log main..HEAD -- <file>` before classifying each), so zero deferred
stash entries were created for the entire shipment. Three learnings are
durable beyond this shipment.

## 1. `REVIEW_TIMEOUT` with an empty `unresolved_thread_ids` list is not a "clean" signal

Across all 8 rounds this shipment, the pattern was consistent:
`autoharness gate copilot-review --max-wait 180-240` frequently returned
`REVIEW_TIMEOUT` on the first attempt after a push, and a second attempt
with a longer wait (`240-300`) then caught the completed review -- which
**usually surfaced additional findings beyond what had just been fixed**,
not merely confirmation of the prior round. Once (between rounds 6 and 7),
a `REVIEW_TIMEOUT` was observed with an *empty* `unresolved_thread_ids`
list, and the very next retry (still within the same round) surfaced 2 new
threads. **Do not treat a timeout with zero listed threads as a "clean"
signal** -- it means the review had not finished analyzing, not that it
finished and found nothing.

**This retry guidance is bounded, not unbounded**: retry with a longer wait
only within the remaining budget of the same-operation circuit breaker in
`.github/instructions/circuit-breaker.instructions.md` (three failures of
the identical `copilot-review` gate invocation for the same HEAD). Do not
retry past that budget -- once exhausted, halt and escalate (or, per the
Ship pipeline's Fix-CI stop condition, present the PR with the outstanding
`REVIEW_TIMEOUT`/pending state for operator intervention) rather than
issuing a further attempt. Within that bound, prefer a genuine
`SATISFIED`/`UNRESOLVED_THREADS` verdict (not `REVIEW_TIMEOUT`) before
concluding a round is complete.

## 2. Schema-mutation-in-place is a *recurring* bug class -- this is the third occurrence

`docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md`
documents the first occurrence and the repeatable 7-step fix procedure.
157-S round 8 was the **third** occurrence: `149.002-T`'s commit
(`c8ba608a`) added the entire `detectors` schema block directly into the
already-published `schemas/validation-gates/1.0.0.schema.json` mirror
(234 insertions/14 deletions) instead of publishing a new version.

A useful discovery this time: `validation-gates` is **not** registered in
the `SCHEMA_CONTRACTS` dict (`schema_contracts.py`) used by the doc-driven
contracts (`harness-config`, `tool-telemetry-event`, `execution-epoch`,
`manifest`). It is resolved via a **standalone module constant**
(`VALIDATION_GATES_SCHEMA_VERSION`), with no per-document `schema_version`
field selecting which mirror to validate against. This *simplifies* the
fix procedure for this specific contract: there is no
`SCHEMA_CONTRACTS[contract]["current_version"]`/`known_versions` entry to
update, no `CONTRACT_MIGRATIONS` entry to add (purely additive bump) --
just bump the standalone constant and update the coupled file set (3
hardcoded test paths + doc references). **When applying the general 7-step
procedure to a new contract, first check whether that contract is
registered in `SCHEMA_CONTRACTS` at all** -- an unregistered,
constant-resolved contract has a shorter fix path.

**Actionable prevention going forward**: before editing *any* file under
`schemas/{contract}/{version}.schema.json`, check `git log main -- <path>`
first. If the file has commits predating the current shipment, it is an
**already-published, immutable snapshot** -- never edit it directly. Add a
new versioned file instead, exactly as for any other already-published
artifact. This check is now cheap and should be habitual for any shipment
touching `schemas/**`.

## 3. An SDK boundary's "JSON-serializable" check must validate the *complete* contract payload, not just the fields a crash was observed for

Round 7 added a check that `result.details`/`result.provenance` are
JSON-serializable (via `json.dumps`) before accepting a validator's
`NodeResult`. Round 8 found this insufficient on two axes:

- **JSON-serializable is necessary but not sufficient for "this field is
  consumed as a dict downstream."** `report.py`'s `_merged_provenance` calls
  `dict(result.provenance)`, and a plain `list` (e.g. `["x"]`) *is*
  JSON-serializable but still raises there. If a downstream consumer does
  more than `json.dumps` the field verbatim (e.g. reshapes it via `dict()`,
  iterates expecting key/value semantics, etc.), the SDK boundary check
  must validate the **actual required shape** (here: `isinstance(value,
  dict)`), not merely "can this be serialized at all."
- **Checking only the fields a crash was *observed* for under-covers the
  contract.** `message`/`token` are typed `str`/`str | None` on the
  dataclass but are not runtime-enforced -- a detector could still assign a
  `Path` to either, and it would reach `emit_pre_review_report`'s
  `json.dumps(payload)` uncaught. The fix checks the **complete**
  `NodeResult.to_dict()` payload's serializability, not only the two fields
  that happened to be named in the finding. **When hardening an SDK
  boundary against a malformed producer/validator payload, validate the
  full serialized contract surface (the object's own `to_dict()`/
  equivalent canonical serialization), not just the specific field(s) the
  triggering example used** -- a narrower check reliably resurfaces as a
  "found one more bypass" finding in the next review round, as happened
  here.

## Process note: continuous full-suite verification kept iteration cheap

Every one of the 8 rounds' fixes was verified with a full
`PYTHONPATH=src python -m unittest discover -s tests` run (not merely the
targeted new tests) before committing, in addition to the pre-push hook's
own independent full-suite run. This caught zero regressions across all 8
rounds -- each fix was genuinely additive/narrowly-scoped, consistent with
every finding being a true P-021 C1 same-contract-surface completion. The
one recurring cost was a pre-existing, unrelated flaky telemetry test
(`test_two_writers_interleaved_seal_preserve_every_distinct_segment`,
shared-epoch-ID collision across parallel test executions) that required
an isolated retry roughly once every 2-3 full-suite runs; this is a
pre-existing test-suite defect, not caused by 157-S, and is a good
candidate for a future dedicated fix (not captured as a P-021 entry since
no 157-S code path is implicated).
