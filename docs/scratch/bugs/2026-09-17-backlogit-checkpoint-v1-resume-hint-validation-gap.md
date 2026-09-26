---
type: bug-report
kind: bug-report
date: 2026-09-17
agent: Stage
subject: "backlogit bug report — CheckpointV1 accepts payloads with no top-level resume_hint"
status: OPEN
component: "backlogit checkpoint schema validator (CheckpointV1) + `checkpoint create` CLI help/example"
target_workspace: backlogit
severity: medium
source_workspace: autoharness
related_stash: ["71200CBB"]
portable: true
---

# backlogit bug — `CheckpointV1` accepts a checkpoint with no top-level `resume_hint`

> **Portability note.** This report is written to be copied verbatim into the
> backlogit workspace. It cites only backlogit-observable behavior plus the
> consumer impact that motivated the filing. It deliberately makes no claim about
> backlogit's internal implementation, and no claim about the intent of any
> checkpoint author.

## TL;DR

Under `schema_version: 1`, `backlogit checkpoint create` accepts a state dump that
omits the modeled top-level `resume_hint` field, and `backlogit checkpoint get`
subsequently reports `"valid": true` for the resulting record. `resume_hint` is the
only field in the payload that carries the "what do I do next" recovery signal, so a
record without it is structurally valid but recovery-useless. Consumers that treat
`resume_hint` as required must then choose between failing closed on a record
backlogit calls valid, or silently accepting an unrecoverable checkpoint.

## Component / ownership boundary

**In scope for backlogit (this report):**

- the `CheckpointV1` schema / validator behavior for the top-level `resume_hint` field
  (whether it is required, conditionally required, or optional-by-design);
- the `checkpoint create --help` text, which lists `resume_hint` among the modeled
  top-level keys but does not state whether it is required;
- the `checkpoint create --help` example payload, which omits `resume_hint` entirely
  and therefore demonstrates the under-specified shape as the canonical usage;
- whatever migration/compatibility stance backlogit wants for already-written records
  if the field becomes required.

**Explicitly out of scope for backlogit:** any change to the *producing* agents in the
autoharness harness (ensuring harness checkpoint producers always emit a specific
`resume_hint`), harness-side validation/tests, and harness-side policy for historical
resolved records. That work is tracked separately in the autoharness workspace under
stash ID `71200CBB`.

## Observed behavior

1. A `schema_version: 1` state dump that omits `resume_hint` is accepted by
   `backlogit checkpoint create` and written to the workspace checkpoints directory.
2. Reading that record back with `backlogit checkpoint get <filename>` returns
   `"valid": true`.
3. The persisted record has no top-level `resume_hint` key at all — the field is not
   auto-populated, not defaulted, and not flagged.

Per `backlogit checkpoint create --help` (v1.10.1), only `created_at`, `updated_at`,
and `status` are auto-populated when missing. `resume_hint` is not in that
auto-populated set.

### Verified in-the-wild instance

Observed 2026-09-17 in the autoharness workspace on a real record:

- File: `.backlogit/checkpoints/checkpoint-20260916-064310.json`
- Shape: `schema_version: 1`, `agent: "stage"`, `status: "resolved"`, populated
  `context` object, **no top-level `resume_hint` key**
- `backlogit checkpoint get checkpoint-20260916-064310.json` →  `"valid": true`

No error, warning, or quarantine flag was emitted for the missing field.

## Expected behavior

One of the following, chosen deliberately by backlogit and then stated explicitly in
the CLI help and schema docs:

- **(A) `resume_hint` is required for `schema_version: 1`.** `checkpoint create`
  rejects a V1 dump that omits it (naming the missing field, consistent with the
  existing unknown-field rejection style), and `checkpoint get` does not report
  `"valid": true` for a record lacking it; **or**
- **(B) `resume_hint` is intentionally optional.** The CLI help and schema docs say so
  in as many words, so downstream consumers can rely on optionality rather than
  inferring a contract from an example payload.

Either resolution is acceptable to the reporting workspace. The defect is the current
*silence*: the field is modeled, is the sole recovery-intent carrier, is omitted from
the canonical example, and its requiredness is undocumented — so neither producers nor
consumers can derive the intended contract.

## Minimal reproduction

Run in a disposable workspace (do not run against a workspace whose real checkpoint
records matter — this writes a new checkpoint file).

```sh
# 1. schema_version 1 payload that omits resume_hint
backlogit checkpoint create --state-dump '{"schema_version":1,"agent":"stage","session_id":"repro-resume-hint","phase":"harvest","context":{"feature_id":"000-F"}}'

# 2. read the record back using the filename returned by step 1
backlogit checkpoint get checkpoint-<TIMESTAMP>.json
```

**Actual result:**

- step 1 succeeds and writes the record;
- step 2 reports `"valid": true`;
- the returned checkpoint object contains no top-level `resume_hint`.

**Expected result** under resolution (A): step 1 fails closed naming `resume_hint`, or
step 2 does not report the record as valid.

> The in-the-wild instance above was verified empirically in this session against a
> pre-existing record. The two-command sequence is stated as the minimal synthetic
> reproduction; it was not executed in the reporting workspace because that workspace's
> checkpoint records were under a no-mutation constraint at the time of filing.

## Version evidence

- `backlogit version 1.10.1-0.20260823032255-b07729386a31+dirty`
- `backlogit checkpoint create --help` (v1.10.1) states that for a `schema_version=1`
  dump the top level is a **closed** schema namespace whose modeled keys are
  `schema_version, agent, session_id, phase, status, created_at, updated_at, context,
  progress, resume_hint`, and that "missing `created_at`, `updated_at`, and `status`
  fields are auto-populated". It does **not** state that `resume_hint` is required.
- The `--help` example payload omits `resume_hint`:
  `backlogit checkpoint create --state-dump '{"schema_version":1,"agent":"ship","session_id":"s1","phase":"build","context":{"shipment_id":"129-S","pr_number":372}}'`

## Why this creates a cross-workspace recovery/startup failure

Checkpoints are a crash-resumption mechanism consumed by agent harnesses. In the
autoharness harness:

- the checkpoint payload contract requires every `schema_version: 1` payload to carry a
  `resume_hint` "specific enough to support a later recovery decision"; and
- startup recovery is **fail-closed**: a checkpoint record with a missing or malformed
  required field is surfaced as a validation/quarantine anomaly and routed to operator
  handoff rather than skipped — and that scan deliberately does not filter out records
  whose `status` is `resolved`.

Because backlogit reports such a record as `"valid": true`, the two sides disagree:
backlogit says the record is fine, the consumer says it is anomalous. The consequences
are (a) a consumer that enforces the stricter contract can be pushed into an operator
handoff on startup by a record backlogit blessed, and (b) a consumer that trusts
backlogit's `valid: true` will happily persist checkpoints from which no agent can
actually resume — the failure only appears later, at the moment recovery is attempted
and there is no next-step signal.

Severity is assessed **medium**, not high: the field's absence does not corrupt the
record or break `checkpoint create`/`get` themselves, and a record can still be read
and inspected. The cost is degraded recoverability plus a contract ambiguity that every
downstream consumer must resolve independently.

## Proposed acceptance criteria

1. Backlogit states, in the `checkpoint create --help` text and in the CheckpointV1
   schema documentation, whether top-level `resume_hint` is **required** or
   **optional** for `schema_version: 1`.
2. If required: `checkpoint create` rejects a V1 dump omitting `resume_hint` with an
   error naming the missing field, in the same style as the existing unknown-field
   rejection; and `checkpoint get` reports such a record as not valid (or flags it),
   rather than `"valid": true`.
3. If optional: the help text says so explicitly, and `checkpoint get` output makes the
   absence machine-detectable for consumers that enforce a stricter contract.
4. The `checkpoint create --help` example payload includes a representative
   `resume_hint` value, so the canonical example demonstrates the intended shape.
5. A stated compatibility/migration position for already-written records that lack the
   field, including whether `status: resolved` records are exempt from any new
   requiredness check.
6. Regression coverage for the chosen behavior: a V1 dump without `resume_hint`
   produces the documented outcome deterministically at both `create` and `get`.

## Related tracking

- autoharness stash `71200CBB` — the autoharness-owned half: harness checkpoint
  producers must always emit a specific `resume_hint`, deterministic harness-side
  validation/tests, and a safe policy/migration for historical resolved records so
  fail-closed startup is not permanently deadlocked. That entry explicitly excludes the
  backlogit validator change described here and points back at this report.

## Non-claims

- No claim is made about why the observed record lacks `resume_hint`. The record was
  created and resolved roughly ten seconds apart, which is *consistent with* a minimal
  completion checkpoint, but the author's intent is unproven and is not asserted.
- No claim is made about backlogit's internal validator implementation, only about its
  externally observed CLI behavior and published help text at v1.10.1.
