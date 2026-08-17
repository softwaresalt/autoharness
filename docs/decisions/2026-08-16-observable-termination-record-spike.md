---
title: "Is observable termination separable from reasoning-state identity?"
source: docs/decisions/2026-08-16-observable-termination-record-spike.md
doc_type: decision
description: "Read-only Stage spike for stash 34AAF1C7 (reasoning DAG / anti-spinning). Tests whether a machine-checkable termination-record contract over the harness's already-existing repetition bounds is separable from the unsolved reasoning-state-identity problem, and whether it is safe to harvest."
docline:
  type: spike
  date: 2026-08-16
  time_box: "single Stage session, read-only"
  conclusion: "defer"
  confidence: "high"
  linked_parent_work_item: null
  promoted_to: ["none"]
  tags:
    - "agents"
    - "reliability"
    - "telemetry"
    - "anti-spinning"
---

## Goal

The 2026-08-15 re-triage of stash `34AAF1C7` named a specific, repository-answerable
entry point and recommended it as the spike's first question:

> Determine whether a termination-record contract over the ALREADY-EXISTING bounds
> delivers most of the reliability benefit at a fraction of the blast radius, and
> only then decide whether duplicate-state detection and a full DAG/visited-set
> traversal are warranted.

This spike answers exactly that question and nothing wider. It deliberately does
**not** attempt to define reasoning-state identity, which remains unanswerable
without instrumented agent runs that do not exist in this workspace.

## Method and constraints

Read-only inspection of this repository only. No source, template, schema, or
config file was modified. No branch, worktree, commit, or PR was created. No
external repository was mutated. No spike/research worktree was created (P-016).

Evidence gathered by direct token scans across `src/autoharness/`, `schemas/`,
`.github/`, `templates/`, `scripts/`, and `tests/`.

## Findings

### F1 — Every repetition bound in this harness is asserted in prose only. CONFIRMED.

A scan for `termination_record`, `TERMINATION`, `frontier_exhaust`, `stop_condition`,
`stop_reason`, `circuit_open`, and `circuit_breaker` across `src/autoharness/`,
`schemas/`, and `.github/` returns **no machine-readable termination construct**.
The only non-prose hit is `verify_workspace.py:2213`, and it is a *template variable
default*, not a runtime bound:

```python
variables.setdefault("CIRCUIT_BREAKER_COOLDOWN", "5 minutes")
```

`.github/skills/install-harness/SKILL.md:380` makes the prose-only status explicit
and intentional:

> Keep the value human-readable because it is rendered into instruction prose
> rather than parsed as machine configuration.

The four bounds that actually govern agent repetition — the circuit-breaker retry
threshold, the 3-consecutive-failure escalation protocol, the 3-cycle plan-review
limit, and the Stage 20-task / 3-failure stop conditions — are therefore all
narrative contracts. Nothing emits, records, or verifies that a bound was reached.

### F2 — A structured emission substrate already exists and is unused for this. CONFIRMED.

`src/autoharness/telemetry/` is a large, mature subsystem (`record.py`, `epoch.py`,
`tool_event.py`, `jsonl_sink.py`, `sqlite_sink.py`, plus schema contracts and ~20
test modules). It already emits structured JSONL/SQLite events with an established
degrade-open discipline — `record.py` states that journal composition failures
"must never block task completion."

So the *mechanical* cost of emitting a termination record is genuinely low, and a
correct non-blocking failure posture is already precedent. This is the part of the
2026-08-15 hypothesis that **holds**.

### F3 — Observable termination is genuinely separable from state identity. CONFIRMED.

Recording *that a bound was reached, which bound, and with what counter value* requires
no notion of whether two reasoning states are "the same." The three candidate-scope
elements from the original intake are confirmed separable, and observable termination
is the one that does not depend on the unsolved problem. The 2026-08-15 framing is
correct on this point.

### F4 — The blast radius is NOT small, contrary to the hypothesis. REFUTED.

This is the finding that changes the verdict. "A fraction of the blast radius" assumed
the change is additive telemetry. It is not. Because the bounds live in *prose*, an
emission contract can only be introduced by editing the prose that declares them —
`constitution.instructions.md`, `circuit-breaker.instructions.md`,
`escalation-protocol.instructions.md`, and the Stop Conditions section of every agent
template — plus their `templates/` counterparts, plus a schema addition, plus verifier
coverage. That is a simultaneous change to the core behavioural contract surface of
every agent the product generates. Measured against this repository's own width-isolation
rule, that is a broad multi-family change, not a narrow one.

### F5 — There is no consumer, so emission would be write-only. DECISIVE.

Nothing in the repository would read a termination record. There is no analyzer, gate,
report, or verifier that would consume it, and none is in scope. Emitting evidence that
nothing checks yields no reliability benefit — it yields the *appearance* of one. The
2026-08-15 annotation warned about precisely this failure mode in a different guise
("a PROCEED verdict backed by no measurement would then be treated downstream as a gate
that had been passed"); shipping write-only termination records reproduces that error at
the artifact level.

### F6 — The motivating evidence is real but does not discriminate.

The PR #325 case (15+ review passes, no fixed point, terminated by operator authority)
is genuine, and this stash's own history is a second instance: four consecutive Stage
sessions have re-triaged the same six entries and reached materially identical
conclusions. Both are real non-termination.

But neither failure was caused by *missing termination evidence*. In both cases a human
could see the loop plainly. They were caused by the absence of an *enforced* bound, which
is exactly the authority-expanding mechanism the entry's own safety note reserves for
operator consent. So the observable-termination slice does not address the motivating
evidence; only the enforcing mechanism would, and that one is gated.

## Conclusion

**DEFER** (confidence: high).

The 2026-08-15 hypothesis is **half-confirmed and half-refuted**. Observable termination
*is* separable from reasoning-state identity (F3) and the emission substrate *does*
exist (F2). But the premise that it delivers "most of the reliability benefit at a
fraction of the blast radius" does not survive contact with the evidence: the blast
radius is the full agent-contract prose surface (F4), the benefit is zero without a
consumer (F5), and the observed failures would not have been prevented by recording
alone (F6).

Harvesting a record-only slice now would produce a broad, cross-cutting prose change
across every agent template in exchange for telemetry nothing reads. That is worse than
deferring, and it would burn the credibility of the eventual real fix.

This is a **narrowing** result, not a restatement of the prior deferral: the recommended
entry point has now been tested against evidence and is **withdrawn as a first slice**.

## What would change this verdict

A future slice becomes worth harvesting when it carries a consumer with it. The
recommended shape, for whoever picks this up:

1. **Pick one bound, not all four.** The plan-review 3-cycle limit is the best candidate:
   it is already the most mechanical, it is Stage-owned, and it has a natural artifact
   (the review document) to carry the record. This avoids the F4 multi-family blast radius.
2. **Ship the reader in the same slice.** A record plus the check that reads it, or
   neither. This directly answers F5.
3. **Keep it record-only and degrade-open**, following the `record.py` precedent — never
   block task completion on emission failure.
4. **Do not attempt duplicate-state detection or a DAG/visited-set traversal** until (1)–(3)
   have shipped and produced real measurements. Reasoning-state identity remains
   unanswerable from static repository evidence, and this spike did not attempt it.

## Safety note (unchanged and reaffirmed)

Any mechanism that *governs* when agents stop reasoning — as opposed to recording that
they did — is authority-expanding runtime behaviour and requires explicit operator
consent regardless of how strong the evidence is. F6 shows the enforcing variant is the
one that would actually address the motivating failures, which makes operator consent a
hard gate on the valuable half of this idea, not a formality.

## Disposition

Stash `34AAF1C7` stays **ACTIVE at MEDIUM priority** as the living tracker. Nothing was
harvested. No shipment was created. This artifact supersedes the 2026-08-15 recommended
entry point with a tested, narrower one.
