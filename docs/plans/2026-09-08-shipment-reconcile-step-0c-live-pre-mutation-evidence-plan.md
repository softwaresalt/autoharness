---
title: "shipment-reconcile Step 0(c): durable pre-mutation evidence record and fail-closed live-execution check"
description: "Implementation plan for the operator's accepted-with-remediation disposition of stash 856B6770 — make live execution of the Step 0(c) linked-deliberation collection PROVABLE by requiring a durable, timestamped pre-mutation evidence record emitted before the P-015 cascade invocation, failing closed when that record is absent or not provably pre-mutation, and locking the behaviour with a 159-S-pattern replay regression test that rejects post-hoc reconstruction"
source: "docs/decisions/2026-09-07-step-0c-pre-mutation-guard-reconstruction-disposition.md"
date: 2026-09-08
last_revised: 2026-09-10
status: reviewed
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_review_verdict: "PASS"
plan_review_cycles: 3
revision: "R1 (2026-09-10) — Step 0(c) evidence-anchor mechanism redesign. Replaces the self-reported `collection_completed_at` ordering proof with an engine-written append-only anchor. Amends U1a, U1b, U1c, U2, U3. Requirements RQ-1/RQ-2/RQ-3 are UNCHANGED; only the mechanism satisfying RQ-2's 'provably pre-mutation' clause is redesigned. See the Revision R1 section below. R1-11 (added 2026-09-10, review-fix cycle 1) splits local runtime ordering proof (L1, gate-bearing) from repository audit evidence (L2, never gate-bearing) and adds the bounded tracked-engine-log closure obligation; U4 is corrected from create to update."
revision_source: "docs/decisions/2026-09-10-step-0c-evidence-anchor-mechanism-redesign-deliberation.md"
revision_gate: "033-DL — blocking predecessor of 163-F and of tasks 163.001-T, 163.002-T, 163.003-T, 163.004-T, 163.005-T. Feature/task level only: backlogit shipment claim-eligibility evaluates shipment predecessors only, so a 171-S→033-DL shipment edge was correctly rejected by the tool and was NOT recorded. 033-DL reached status done on 2026-09-10, satisfying this gate; 171-S remains queued and unclaimable on its shipment-level blocks dependency on 169-S."
stash_entry: "856B6770"
related_stash_entries:
  - "9E22BFC6 — AF-06: the 856B6770 remediation had no trackable identity. THIS PLAN and its harvested feature/shipment are that identity."
  - "27F9EC8A — AF-07: committed stash currency gap for 856B6770. Part (a) discharged by the Stage stash disposition written alongside this plan; part (b) tracked by 162.011-T in 170-S."
  - "DDBF283E — R1 SOURCE: the U2 pre-existence proof was forgeable by a backdated post-hoc reconstruction. Resolved by Revision R1. PR 437 HEAD e78e3f00, thread PRRT_kwDORzpWpM6gdwXD."
  - "EB23D1B9 — R1 SOURCE: the DDBF283E prerequisite was not encoded in 171-S's claim-eligibility graph. Resolved by Revision R1's gate encoding (033-DL). PR 437 HEAD 42783ce4, thread PRRT_kwDORzpWpM6ge79q."
compound_learnings:
  - "docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md (published 2026-09-10, commit 5171ace1 on main — the 'pending publication' note carried here at planning time is now discharged)"
  - "docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md"
  - "docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md"
  - "docs/compound/2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md"
  - "docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md"
decision_status_at_planning: "decided (operator, 2026-09-08) — Option A accepted-with-remediation P-005 deviation; mechanical outcome final; systemic remedy tracked as a SEPARATE sibling shipment, not folded into 169-S; no merge authorization"
related_but_distinct:
  - "docs/plans/2026-09-07-shipment-reconcile-cascade-premode-member-class-contract-plan.md (stash 15A02E21 — now archived; feature 161-F, shipment 169-S; published 2026-09-10, commit 5171ace1 on main) — RELATED, DISTINCT. 161-F fixes WHAT Pre-Mode compares (member-class status contract). This plan fixes WHETHER Step 0(c) ran live and is evidenced as pre-mutation. Different contract surface, different failure mode, different tests. MUST NOT be merged. Sequencing dependency only, to avoid conflicting edits to the same SKILL.md Step 0 / Cascade Sub-Procedure region."
  - "docs/plans/2026-09-07-review-pattern-learning-methodology-plan.md (feature 162-F, shipment 170-S; published 2026-09-10, commit 922f99bf on main) — RELATED, DISTINCT. Hosted-review learning methodology. MUST NOT absorb this fix."
tags:
  - "plan"
  - "shipment-reconcile"
  - "pre-mutation-gate"
  - "p-005"
  - "p-015"
  - "fail-closed-design"
  - "dogfood-parity"
---

## Problem Frame

For the 159-S close of qualifying feature `151-F`, the Safe-Close **Step 0(c)
linked-deliberation collection** — which the skill requires **three separate times**
to run *before* the destructive cascade invocation — was **reconstructed after** the
cascade from preserved pre-close evidence (commit `1b758a16`), not executed live as a
pre-mutation gate.

The operator has dispositioned this (2026-09-08) as an **accepted-with-remediation
P-005 process deviation**: the mechanical archival outcome stands as verified and
final, Step 0(c) is permanently recorded as not executed as a live pre-mutation gate,
and the systemic fix is tracked here as a **separate** follow-up shipment.

### The specific defect this plan fixes

Step 0(c) is **required** but not **evidenced**. Nothing in the current contract
distinguishes these two histories:

| History | Step 0(c) inputs | Post-close artifact produced |
|---|---|---|
| **A — compliant**: scan ran at `T0`, cascade invoked at `T1 > T0` | read at `T0` | a report asserting the scan happened |
| **B — the 159-S history**: cascade invoked at `T1`, scan reconstructed at `T2 > T1` | read at `T2` from preserved copies | a report asserting the scan happened |

Both produce a byte-identical-looking assertion. **The current contract cannot tell
them apart, and therefore cannot enforce the ordering it states three times.**

This is worse for the *empty* result, which is exactly what 159-S produced: an
unrecorded empty linked-deliberation set is indistinguishable from a scan that never
ran at all.

### Why "the inputs were provably unchanged" does not close it

Step 0(c) serves **two separable purposes** (established in the decision artifact and
**not re-opened here**):

1. **Data supply** — produce the validated linked-deliberation ID set feeding
   `allowed_ids` / `required_ids`. Satisfiable post-hoc *iff* the inputs are provably
   unchanged. For 159-S it **was** satisfied; the archive differed from
   `git show 1b758a16:.backlogit/queue/151-F.md` only in archival bookkeeping fields.
2. **Pre-mutation halt** — detect ambiguous/torn (`RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS`)
   or missing (`RECONCILE_FAIL_SNAPSHOT_MISSING`) records **while not mutating is still
   possible**. **Never** satisfiable post-hoc, because the value of the gate is the
   preserved option to decline an irreversible cascade.

Step 0(c) exists precisely for the case where inputs are **not** recoverable.
Ratifying reconstruction in the easy case (inputs preserved) creates the precedent
that will be cited in the hard case (inputs destroyed). The fix must therefore make
live execution **provable**, not merely **required**.

### Grounded text locations (verified 2026-09-08)

| Surface | Location | Note |
|---|---|---|
| Step 0(c) linked-deliberation extension | `.github/skills/shipment-reconcile/SKILL.md` L456–L500 (`**Linked-deliberation snapshot extension (155-S, PR #407 review).**`) | resolved dogfood copy, 1082 lines |
| Paired template | `templates/skills/shipment-reconcile/SKILL.md.tmpl` L456–L500 | 1082 lines; **same line numbers**, verified |
| The three "before" statements | same files, L473–475, L487–492, L747–749 | explicit and load-bearing |
| Cascade Close Sub-Procedure | same files, L618 (`### Cascade Close Sub-Procedure …`) | step 1 is the destructive invocation |
| Two-set gate consuming the snapshot | same files, L730–L760 (step 3) | reads the Step 0(b)/(c) snapshot |
| Report output surface | same files, L63 — `.backlogit/reconcile/{shipment_id}-{mode}-{timestamp}.md` | the existing durable evidence location |
| Scenario matrix / quality criteria | same files, L1002 / L1011 | where negative scenarios are enumerated |
| Diagram | `docs/diagrams/05-shipment-reconcile-cascade-premode.mmd` — **exists** in the workspace (the `docs/diagrams/` set was authored and operator-approved on 2026-09-07 under gate `G-DIAG-REVIEW`, recorded in the 15A02E21 deliberation's `linked_artifacts`); present as a working-tree artifact, not yet committed to `main` | U4 **updates** this existing diagram, adding the pre-mutation evidence node, the R1 anchor, and all four halt-token exits. It is **not** a new artifact, and U4 must not create a second diagram alongside it |
| Checksum manifest | `.autoharness/harness-manifest.yaml` (shipment-reconcile entries at L126, L201, L272, L274, L396) | skill/template edits invalidate checksums |

## Requirements Trace

Sourced verbatim from the decision artifact's Option A remediation clause. Three
requirements, no more:

| ID | Requirement | Unit |
|---|---|---|
| **RQ-1** | The Step 0(c) linked-deliberation collection MUST emit a **durable, timestamped pre-mutation evidence record** *before* the cascade invocation. | U2 |
| **RQ-2** | Close MUST **fail closed** when that record is absent or not provably pre-mutation — i.e. live execution becomes *provable*, not merely *required*. | U2 |
| **RQ-3** | A **replay/regression test over the 159-S shape** MUST fail if the collection is reconstructible after mutation. | U1a / U1b / U1c |

### Explicitly requiring no Python source change

`src/autoharness/gates/shipment_closure.py` is **not** modified. The classifier already
supplies the qualifying-feature determination Step 0(c) references; the evidence record
is an additive artifact written by the skill's own protocol, at the surface the skill
already owns (`.backlogit/reconcile/`). Same posture as 161-F.

## Revision R1 (2026-09-10) — evidence-anchor mechanism redesign

> **Read this section together with U1a/U1b/U1c/U2/U3 below.** Where R1 conflicts
> with the original text of those units, **R1 governs**. Everything not named here
> — including RQ-1/RQ-2/RQ-3, the unit structure, the file set, the task count, the
> Non-Goals, and every H-3 protected invariant — is **unchanged**.

**Source:** `docs/decisions/2026-09-10-step-0c-evidence-anchor-mechanism-redesign-deliberation.md`
(stash `DDBF283E`, `EB23D1B9`). **Gate:** `033-DL`.

### R1-0 — What was wrong

U2's pre-existence proof rested on `collection_completed_at` plus the `HEAD` SHA and
manifest list — **all three written by the agent whose compliance is being checked,
through the ordinary protocol surface**. A post-hoc reconstruction that backdates the
timestamp satisfies every clause. The gate could not fail the 159-S history it exists
to reject. `15A02E21` was a gate no legitimate state could satisfy; this was its dual
— a gate no illegitimate state could fail.

The **rule** U2(c) stated was right. The **mechanism** did not implement it.

### R1-1 — The authoritative ordering proof is an engine-written anchor event

U2(a) gains a step, performed inside the existing lock, after the record is written
and before the cascade invocation:

* compute `sha256` over the evidence record's bytes;
* append an anchor event to `.backlogit/logs/{shipment_id}.jsonl` via backlogit's
  append operation, carrying the literal token `PRECASCADE_EVIDENCE_ANCHOR`, the
  `shipment_id`, the record's repo-relative path, and that `sha256`.

The **engine**, not the agent, writes the event's `timestamp`, `actor`, and — the
part that carries the proof — its **append position**. The cascade mutation later
appends its own engine-written `shipment_status_changed` / `commit_tracked` /
`archived` events to the same file. Ordering is proved by **relative append position
in a file the engine owns**.

`collection_completed_at` stays in the record but is **demoted to corroborating
metadata**. State this demotion explicitly in one sentence, so no future reader
re-promotes it: agreement between it and the anchor is *not* a PASS condition.

**Verified against live data (2026-09-10):** engine authorship confirmed in
`150-S`/`151-S`/`152-S` logs; `comment` events carry engine timestamps
(`005-F`, `005-S`, `011-DL`); logs **survive archival on the local filesystem**, so
the proof outlives the mutation it proves *for a reviewer working in the closing
workspace*; and `.backlogit/logs/159-S.jsonl` contains **no** anchor before
`archived` — the real failure case is mechanically detectable under R1 and was not
under the original mechanism.

> **Durability scope — read with R1-11.** The claim above is about **local
> filesystem** retention only. `.backlogit/logs/` is covered by a workspace
> `.gitignore` rule, so a shipment log is **not** repository-durable by default and
> a fresh-clone reviewer cannot see it at all. R1-11 splits the two concerns and
> adds the bounded tracked-evidence obligation that makes the closure claim
> auditable from a clean clone. R1-1 remains the **only** gate-bearing proof.

### R1-2 — U2(b) becomes four separately labelled, independently failing tokens

The never-merge rule (root cause of `B57F9E24`) applies. Collapsing these would
destroy the diagnostic this shipment exists to produce: *"you never ran Step 0(c)"*
must not report identically to *"you reconstructed it afterwards."*

| Token | Fires when |
|---|---|
| `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING` | no evidence record for this `shipment_id` |
| `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE` | record exists but does not describe the state being closed: `HEAD` SHA or manifest mismatch, or `collection_completed_at` absent |
| `RECONCILE_FAIL_PRECASCADE_ANCHOR_MISSING` **(new)** | no `PRECASCADE_EVIDENCE_ANCHOR` event for this `shipment_id`, **or** its `sha256` does not match the record on disk |
| `RECONCILE_FAIL_PRECASCADE_ANCHOR_NOT_PRE_MUTATION` **(new)** | anchor exists but does not precede the earliest engine-written mutation event for this shipment in append order |

All four emit **P-005** and halt; none authorizes a safe-close fallback. The two
pre-existing tokens keep their names; their semantics are **narrowed**, not
redefined. The digest match lives in `..._ANCHOR_MISSING` deliberately: an anchor
that does not bind to the record on disk is not an anchor for it.

### R1-3 — U2(c) anti-reconstruction clause is strengthened, not replaced

Keep the existing clause verbatim and append one sentence naming the mechanism that
now enforces it: the pre-existence evidence is the engine-written anchor's position
relative to the engine's own mutation events, and **no field the collecting agent
authors is load-bearing for that determination**.

### R1-4 — U1a fixture must model engine-log append order

The fixture's recorded `(step, timestamp)` sequence is extended to a recorded
**append-ordered engine event log** per shipment, so an assertion can ask *"does the
anchor precede the mutation events in append order?"* — not merely *"is a file
present?"* and not merely *"is one timestamp less than another?"*. Timestamp
comparison alone is exactly what R1 removes from the load-bearing path.

### R1-5 — U1b gains the backdated-reconstruction rejection family

The negative case `DDBF283E` requires:

> An evidence record exists whose `collection_completed_at` is strictly **before**
> the cascade invocation and whose `HEAD` SHA and manifest list both **match** the
> closed state — a perfect forgery under the original mechanism — but whose anchor
> event is **absent**, or appears **after** the mutation events.

MUST be **rejected**, and rejected with `..._ANCHOR_MISSING` /
`..._ANCHOR_NOT_PRE_MUTATION`, **never** with `..._EVIDENCE_STALE`. **Assert the
token identity, not merely the rejection** — that is what proves the ordering proof,
and not a content comparison, is doing the work. This assertion fails against the
pre-R1 mechanism, which is the point of adding it.

The existing ordering and explicit-empty assertion families are unchanged.

### R1-6 — U1c guard additionally asserts the R1 contract text

Same section-scoped technique, no file-wide regex. Within the resolved Step 0(c)
slice, assert: the anchor emission obligation; all four token names; the
`collection_completed_at` demotion sentence; the strengthened anti-reconstruction
clause; and the R1-11 **L1/L2 durability-split sentence** — specifically that the
engine log is the sole gate input and that the tracked-log closure obligation is
explicitly *not* a gate and *not* a fallback. The single-statement rule (D-5)
extends to the anchor obligation and to the L2 obligation — each stated once,
referenced from the Cascade Sub-Procedure.

### R1-7 — U3 scenario matrix gains two rows

* **Negative — backdated reconstruction** (R1-5's case) ⇒ `..._ANCHOR_MISSING` or
  `..._ANCHOR_NOT_PRE_MUTATION`.
* **Positive — the legitimate 159-S shape, restated so the gate is provably
  satisfiable:** record present, `scan_performed: true`,
  `linked_deliberation_ids: []`, anchor present, digest matching, anchor preceding
  all mutation events ⇒ **PASS**.

**No third row for R1-11.** The L2 tracked-log closure obligation is deliberately
**not** added to the scenario matrix: the matrix enumerates pre-cascade gate
outcomes, and L2 is a post-close publication obligation with no gate outcome. State
it once in the Step 0(c) extension (D-5) and, if the quality criteria mention it at
all, mention it as a closure obligation explicitly marked non-gating.

### R1-8 — Threat model (bounds the claim; do not overstate it)

The target is **tamper-evident and out-of-protocol**, not tamper-proof. No purely
local mechanism resists an operator with shell access, and chasing that would buy
nothing. The threat is the 159-S failure mode: a good-faith agent reconstructing
equivalent-looking evidence, sincerely believing content equality is what the
contract asks for. R1 makes that path **unreachable through the agent's normal tool
surface** — forging the anchor requires hand-splicing a line into an engine-owned
append-only JSONL, which is an out-of-protocol act and itself a P-005 violation.
Under the original mechanism the same forgery required only writing a different
string into a file the agent was already authoring.

**The claim is also bounded in *reach*, not only in strength.** The anchor is
tamper-evident **to a reader who can see the engine log**. Because
`.backlogit/logs/` is `.gitignore`d, that reader is — by default — someone working
in the closing workspace, not someone reading the repository. R1-11 states that
split explicitly and adds the bounded obligation that extends the evidence to a
fresh clone. Do not describe the anchor as "durable" or "auditable" without
naming which of the two audiences is meant.

### R1-9 — What R1 does NOT change

No Python source change (Non-Goal preserved). No new implementation units, no new
task, and no new artifact **kind**: R1-11's L2 obligation creates no file — it
force-tracks an engine log that the close already produces, and commits it into the
same closure commit as the already-tracked evidence record. No `.gitignore` change,
and no widening of `.backlogit/logs/` tracking beyond the single shipment being
closed. No change to `169-S`/`161-F` or `170-S`/`162-F` scope. No
re-opening of the 856B6770 disposition. **No retroactive-compliance claim for
159-S** — it remains a permanently disclosed deviation, and R1 is forward-only. The
`blocks` dependency on `169-S` is unchanged; U2 is still authored against post-169-S
text. Every H-3 protected invariant stands, and R1-11 adds, removes, renames, or
merges **no halt token** — the gate surface is exactly the four tokens of R1-2.

### R1-10 — Rejected alternatives (full rationale in the decision artifact)

* **External RFC 3161 timestamp** — injects a network dependency into a fail-closed
  irreversible close path, converting an integrity control into an availability
  outage for offline operators.
* **Git-commit ancestry as the primary anchor** — genuinely monotonic, but requires
  a commit at a specific mid-close moment the close path does not guarantee; making
  the gate depend on it would make it unsatisfiable in legitimate states, the
  `15A02E21` mistake. Retained as an **optional corroborating field only**.
* **Skill-maintained hash chain** — the agent owns the chain, so it is self-reported
  at one remove; new structure and new failure modes for no additional trust.

### R1-11 — Durability split: local runtime ordering proof vs. repository audit evidence

R1-1 asserted the anchor is durable and auditable. That was **overstated**: it is
true of the local workspace and false of the repository, because
`.backlogit/logs/` is covered by a workspace `.gitignore` rule (`.gitignore`,
`.backlogit/logs/`). A reviewer with only a fresh clone therefore cannot see the
anchor at all, and — under the pre-R1-11 contract — would have had nothing to fall
back on except the agent-authored `collection_completed_at` that R1 exists to
demote. R1-11 removes that gap **without** relaxing the gate.

The two concerns are now separately named. They are **not** interchangeable and
neither substitutes for the other.

| Layer | Artifact | Written by | Audience | Gate-bearing? |
|---|---|---|---|---|
| **L1 — local runtime ordering proof** | `PRECASCADE_EVIDENCE_ANCHOR` event in `.backlogit/logs/{shipment_id}.jsonl` | the **engine** (timestamp, actor, append position) | the closing workspace, at close time | **YES — the sole gate input.** All four R1-2 tokens evaluate L1 and only L1 |
| **L2 — repository audit evidence** | the same engine log, **force-tracked** at the closure commit, alongside the already-tracked evidence record under `.backlogit/reconcile/` | the **engine** (bytes are the engine's, verbatim and unmodified); the closing agent performs only the `git add -f` | a fresh-clone reviewer, after the close | **NO — never a gate input, never a fallback** |

**L1 is unchanged.** The four tokens in R1-2 read the live engine log inside the
existing lock, before the cascade invocation. Nothing in R1-11 adds, removes,
renames, merges, or weakens a token; nothing in R1-11 is consulted by the gate; and
the absence, failure, or unavailability of L2 **never** authorizes a close, never
downgrades a halt, and never produces a fallback path. L2 is written **after** the
mutation the gate already permitted, so it is structurally incapable of being a
pre-mutation gate.

**L2 obligation (bounded).** At the closure commit for a shipment closed through the
cascade path, the closing agent MUST commit, into the repository:

1. the evidence record `.backlogit/reconcile/{shipment_id}-precascade-snapshot-{timestamp}.md`
   (already a tracked path — no change); **and**
2. that shipment's **own** engine log `.backlogit/logs/{shipment_id}.jsonl`,
   force-added past the ignore rule (`git add -f`), **verbatim and byte-unmodified**.

The bound is exact and MUST NOT be widened: **one shipment's log, at its own closure
commit, unmodified.** This is not a general un-ignoring of `.backlogit/logs/`, not a
bulk backfill of historical logs, and not a new `.gitignore` change. Logs for
shipments not closed through this path stay ignored and untracked, as today.

**Why force-tracking the engine log, and not an agent-written export.** A
transcription, summary, or excerpt would reintroduce exactly the defect R1-0
identified: an artifact whose fields are written by the agent whose compliance is
being checked. Committing the engine's own bytes keeps the property that makes the
anchor worth anything — **no field the collecting agent authors is load-bearing**.
The `git add -f` is a staging action over bytes the agent did not write; it cannot
alter append order, and any alteration is a content change visible in the diff.

**What a fresh-clone reviewer can then verify, without trusting any agent-authored
timestamp:**

1. recompute `sha256` over the committed evidence record's bytes and compare it to
   the `sha256` carried in the committed anchor event — this binds record to anchor;
2. locate the `PRECASCADE_EVIDENCE_ANCHOR` line in the committed log and confirm it
   precedes the engine-written `shipment_status_changed` / `commit_tracked` /
   `archived` lines **in append order** — this is the ordering proof, and it is
   positional, not temporal;
3. confirm the record's `HEAD` SHA and manifest list describe the state that was
   closed.

`collection_completed_at` is not consulted in any of the three steps. Its R1-1
demotion is preserved exactly.

**Failure behaviour (fail-closed is preserved, and relocated to the correct
boundary).** L2 cannot gate a mutation that has already happened, so it is enforced
where it *can* be enforced: **operational closure is INCOMPLETE until L2 is
committed.** A close whose L1 gate passed but whose L2 evidence was not committed is
a **P-001 incomplete-closure** condition — report it, do not silently accept it, and
do not treat it as a reason to re-run, weaken, or retro-fit the L1 gate. The
mechanical close stands; the *publication* is unfinished until the engine log is in
the repository. This is deliberately the same posture the harness already takes for
other post-merge closure obligations, and it is stated so that no future reader
mistakes L2 for a fifth halt token.

**Explicitly rejected.** Adding a fifth pre-cascade token for L2 (it would gate on an
artifact that cannot exist yet); un-ignoring `.backlogit/logs/` wholesale (unbounded
repository growth and an unrelated `.gitignore` change outside this feature's scope);
and an agent-authored anchor excerpt or audit summary (reintroduces self-reported
evidence — R1-0).

## Implementation Units

### U1a — RED: replay fixture for the 159-S shape

Build a synthetic 159-S-shaped fixture workspace in
`tests/test_shipment_reconcile_precascade_evidence.py`:

* one shipment record, one covering **root** feature declaring `status: active`
  (the only valid pre-close state — the cascade is what archives it), its full
  descendant task set at every depth declaring `status: done`;
* one variant where the covering feature has **no** linked deliberation (the exact
  159-S/`151-F` shape, whose correct validated set is **empty**);
* one variant where it has **one** validated linked deliberation reachable via each
  of the three engine-defined sources in turn.

The fixture must model the **ordering** dimension explicitly: a recorded sequence of
(step, timestamp) events, so an assertion can ask *"did the evidence emission precede
the cascade invocation?"* rather than *"is an evidence file present?"*.

RED: this task lands the fixture plus failing assertions; it does not edit the skill.

### U1b — RED: replay assertions (ordering + reconstruction rejection)

Two assertion families over the U1a fixture:

1. **Ordering** — the documented sequence must not be able to reach the cascade
   invocation with no pre-existing evidence record. A trace in which the evidence
   record's `collection_completed_at` is absent, or is **not strictly before** the
   cascade invocation timestamp, must be rejected.
2. **Reconstruction rejection** — a trace that produces a byte-identical evidence
   record *after* the mutation (the literal 159-S history) must be rejected, and must
   be rejected **for the ordering reason**, not for a content-mismatch reason. This is
   the assertion that encodes the Purpose-1/Purpose-2 distinction: content equality is
   explicitly **not** sufficient.

Also assert the **explicit-empty** rule: an evidence record whose validated set is
empty must record `scan_performed: true` with an explicit empty list — an omitted
field must be rejected, because an unrecorded empty scan is indistinguishable from a
scan that never ran. This is the 159-S failure mode in one assertion.

### U1c — RED: section-scoped contract guard and dogfood-parity guard

A separate guard module asserting, over **both** `.github/skills/shipment-reconcile/SKILL.md`
and `templates/skills/shipment-reconcile/SKILL.md.tmpl`:

1. **Section-scoped contract presence** — the emission obligation, the two halt tokens,
   the explicit-empty rule and the anti-reconstruction clause appear **within the
   resolved Step 0(c) extension block / Cascade Close Sub-Procedure block**, located by
   heading/anchor and then asserted within that slice.
2. **Single-statement rule (D-5)** — the obligation is stated **once**; the Cascade
   Sub-Procedure references it rather than restating it. A second independent
   restatement fails the guard.
3. **Dogfood parity** — the two copies agree on the asserted region.

**Guard construction (per `2026-08-21-ast-based-structural-regression-guards-beat-line-regex`):**
these assertions MUST be **section-scoped** — never a bare file-wide regex, which
passes as soon as the required phrase appears anywhere in an 1082-line document, and
which cannot express the single-statement rule at all.

### U2 — ATOMIC CORE: pre-mutation evidence record + fail-closed live-execution check (INDIVISIBLE)

**Paired edit, SAME COMMIT:** `.github/skills/shipment-reconcile/SKILL.md` **AND**
`templates/skills/shipment-reconcile/SKILL.md.tmpl`, hand-edited in parallel. The
resolved dogfood copy is **NOT** regenerated (096-S).

**Do not split.** The two halves are one contract:

* the record without the check is an artifact nobody consults — the 159-S state, restated;
* the check without the record is an **unsatisfiable gate** — precisely the defect class
  `2026-09-06-composed-workflow-protocol-state-machine-validation` was written about,
  and the one 161-F exists to repair. Shipping half of this reproduces it.

**(a) Emission (RQ-1).** Extend the Step 0(c) linked-deliberation extension so that, on
the `CASCADE` path, before the Cascade Close Sub-Procedure's step 1 invocation, the
collection writes a durable record at
`.backlogit/reconcile/{shipment_id}-precascade-snapshot-{timestamp}.md` containing:

1. `shipment_id`, the manifest item list, and the git `HEAD` SHA at collection time;
2. the qualifying feature member set, **by reference to Step 0(c)'s own
   classification** — never a separate re-derivation (this is the existing
   reference-only rule at L733/L737; do not weaken it);
3. per qualifying feature, the three engine-defined sources read **verbatim**: the
   literal `custom_fields.source_deliberation_id` string, the description-scan matches,
   and the references-scan matches, each recorded with the resolved record location
   (`queue/` or `archive/`) that Step 0(b)'s resolution rule produced;
4. the dedup + existence + `artifact_type: deliberation` validation outcome per
   candidate ID;
5. the resulting validated ID set, recorded **explicitly even when empty**
   (`scan_performed: true`, `linked_deliberation_ids: []`) — never an omitted field;
6. `collection_completed_at`, a UTC timestamp, written and flushed **before** the
   cascade invocation.

**(b) Fail-closed check (RQ-2).** Before the Cascade Close Sub-Procedure step 1
invocation, re-read the record and halt on either of two new, **separately labelled,
independently failing** tokens (never merged into one test — same rule the two-set gate
already states at L753, whose merge is the documented root cause of `B57F9E24`):

* `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING` — no record for this `shipment_id`;
* `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE` — a record exists but does not validate:
  `collection_completed_at` is absent, or is not strictly before the cascade invocation
  timestamp, or its recorded `HEAD` SHA / manifest item list does not match the state
  being closed.

Both emit a **P-005** violation and halt. Neither authorizes a fallback to safe-close.

**(c) The anti-reconstruction clause.** State explicitly, in-skill:

> A post-hoc reconstruction of this collection — **even one provably byte-identical to
> what a live scan would have read** — does NOT satisfy this check. The check is on the
> record's **pre-existence**, never on its **reproducibility**. Step 0(c) supplies data
> *and* preserves the option to decline an irreversible mutation; the second purpose is
> not recoverable after the mutation.

**(d) Single authoritative statement.** State the requirement **once**, in the Step 0(c)
extension, and have the Cascade Close Sub-Procedure **reference** it rather than restate
it. Two independent restatements drift — that is literally how `15A02E21` was born.

**(e) L2 repository audit evidence obligation (added by R1-11; NOT a gate).** State
once, in the same Step 0(c) extension, that at the closure commit for a shipment
closed through the cascade path the closing agent commits (i) the evidence record
under `.backlogit/reconcile/` and (ii) **that shipment's own** engine log
`.backlogit/logs/{shipment_id}.jsonl`, force-added past the workspace ignore rule and
**verbatim and byte-unmodified**. State in the same place that this obligation is
**not** a halt token, **not** a gate input, and **not** a fallback: the four tokens of
R1-2 read the live engine log only, and a missing L2 makes the closure *publication*
incomplete (a reportable P-001 condition) without ever authorizing, re-running, or
weakening the L1 gate. Bounded to one shipment at its own closure — no `.gitignore`
change, no historical backfill, no other log.

### U3 — Scenario matrix and quality criteria currency

> **SUPERSEDED BY R1-7 AND R1-11 where they conflict.** The three bullets below are
> the **pre-R1** two-token formulation, retained verbatim as history. Under R1 the
> matrix carries **four** tokens and **five** rows — see R1-7 for the two added rows
> and for the narrowing of `..._EVIDENCE_STALE` to content mismatch, and R1-11 for
> the explicit statement that L2 repository audit evidence is **not** a matrix gate
> row.

Add the negative scenarios to the Deterministic Safe-Close Scenario Matrix (L1002) and
Quality Criteria (L1011), in both copies:

* **Negative — missing pre-cascade evidence**: cascade path selected, no evidence
  record ⇒ `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING`.
* **Negative — post-hoc reconstruction**: evidence record present but
  `collection_completed_at` is after the cascade invocation ⇒
  `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE`. *(Superseded: under R1 this detection
  belongs to `..._ANCHOR_MISSING` / `..._ANCHOR_NOT_PRE_MUTATION`; `..._EVIDENCE_STALE`
  narrows to `HEAD`/manifest mismatch or an absent `collection_completed_at`.)*
* **Positive — empty validated set (the 159-S shape)**: evidence record present,
  `scan_performed: true`, `linked_deliberation_ids: []`, timestamp strictly before the
  invocation ⇒ **PASS**. This names the legitimate passing state required by lesson 6.
  *(Superseded: under R1 the passing row additionally requires a present anchor whose
  digest matches the record and whose append position precedes every engine-written
  mutation event; the timestamp is corroborating only.)*

### U4 — Diagram currency (updates an existing artifact)

`docs/diagrams/05-shipment-reconcile-cascade-premode.mmd` **exists** — the
`docs/diagrams/` set was authored and operator-approved on 2026-09-07 under gate
`G-DIAG-REVIEW` and is present in the workspace as a working-tree artifact not yet
committed to `main`. U4 **updates** it; it does not create it, and must not add a
parallel diagram beside it. If the diagram set is published by an unrelated change
before U4 runs, U4 still updates the published file.

The update must draw, on the **pre-mutation** side of the cascade invocation:

* the Step 0(c) evidence-record emission node;
* the **R1 anchor** node — the `PRECASCADE_EVIDENCE_ANCHOR` append into the
  engine-owned `.backlogit/logs/{shipment_id}.jsonl`, positioned inside the existing
  single-writer lock and strictly before the cascade invocation, so the append-order
  relationship the gate depends on is visible rather than implied;
* **all four** halt tokens as separately labelled exits —
  `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING`,
  `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE`,
  `RECONCILE_FAIL_PRECASCADE_ANCHOR_MISSING`,
  `RECONCILE_FAIL_PRECASCADE_ANCHOR_NOT_PRE_MUTATION` — never collapsed into a shared
  "fail" exit, which would erase in the diagram the diagnostic R1-2 exists to create;
* the R1-11 **L1/L2 split**, with L2 drawn on the post-close side and visibly **not**
  wired into any gate decision, so no reader infers a fifth halt token.

Per lesson 2 of the composed-state-machine learning, the diagram is where the seam
becomes reviewable.

### U5 — Checksum recompute and GREEN

Recompute `.autoharness/harness-manifest.yaml` checksums for the edited skill and
template, and run the full suite green.

## Dependency Graph

```text
U1a (fixture)  ──┐
U1b (assertions) ┼──> U2 (ATOMIC CORE) ──> U3 ──┐
U1c (guards)   ──┘                     ──> U4 ──┴──> U5
```

RED units land first and must fail for the stated reason before U2; U5 is last because
it consumes every prior edit's bytes.

**Shipment-level:** this shipment carries a `blocks` dependency on **169-S**. Both edit
the same `SKILL.md` Step 0 region; 169-S is a sealed, plan-reviewed decomposition whose
`161.003-T` is marked *R-4 INDIVISIBLE ATOMIC CORE* and cannot be re-opened (PR #436 is
at its hard 3-cycle limit, P-018 blocked). Sequencing, not merging.

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| D-1 | Evidence record lives at `.backlogit/reconcile/`, the skill's existing report surface | Additive write to a location the skill already owns; no new storage contract, no backlog-state mutation |
| D-2 | The check tests **pre-existence**, not reproducibility | Reproducibility is Purpose 1, already satisfied in 159-S. Purpose 2 is the one that failed |
| D-3 | Empty result must be recorded explicitly | An unrecorded empty scan is indistinguishable from no scan — the precise 159-S failure |
| D-4 | Two separate halt tokens, independently evaluated | Merging two questions into one condition is the documented root cause of `B57F9E24`. **SUPERSEDED BY R1-2 (2026-09-10):** the *never-merge* principle stands and is unchanged; the *count* does not. The gate now carries **four** separately labelled, independently failing tokens — `..._EVIDENCE_MISSING`, `..._EVIDENCE_STALE`, `..._ANCHOR_MISSING`, `..._ANCHOR_NOT_PRE_MUTATION`. Read "two" here as pre-R1 history |
| D-5 | Requirement stated **once**, referenced elsewhere | Independent restatements drift; that is how `15A02E21` arose |
| D-6 | Separate shipment, sequenced after 169-S | Different contract surface; 169-S's plan is sealed and cannot be re-reviewed |
| D-7 | No Python source change | The classifier already exposes everything Step 0(c) references |

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| **Unsatisfiable gate** — the check can never pass | U3 names a concrete legitimate passing state (the empty-set 159-S shape). Lesson 6 check applied below |
| **Merge conflict with 169-S** in the same Step 0 region | `blocks` dependency on 169-S; U2 is authored against post-169-S text |
| **Guard passes on a phrase appearing elsewhere** in an 1082-line file | Section-scoped assertions (U1c), never file-wide regex |
| **Dogfood-parity drift** between resolved copy and template | Paired edit in the same commit; parity assertion in U1c; checksums in U5 |
| **Scope creep into 169-S or 170-S** | Explicit `related_but_distinct` frontmatter; separate feature, separate shipment |
| **Retroactive-compliance claim** | The plan and every harvested task state that 159-S remains a recorded, permanently disclosed deviation. This fix is forward-only |

## Non-Goals

* Re-opening the operator's disposition, or any part of the four-axis finding.
* Altering the 159-S mechanical archival outcome (final and verified).
* Any claim that 159-S becomes retroactively compliant. It does not.
* Touching PR #436, its body, its review threads, CI, or Ship-owned closure evidence.
* Any change to 169-S/161-F or 170-S/162-F scope.
* Any Python source change.

## Plan Hardening Signals (REQUIRED)

**Requires plan hardening: yes.** Signals present:

* modifies a **skill contract on an irreversible, destructive execution path**;
* introduces **new fail-closed halt tokens** (a gate-shaped change);
* **paired edit** across a resolved dogfood copy and its template (two template families);
* invalidates **harness manifest checksums**;
* edits a file region **another queued shipment (169-S) also edits**.

## Plan Hardening

### Learnings and instructions consulted

| Source | Bearing |
|---|---|
| `2026-09-06-composed-workflow-protocol-state-machine-validation` | Lessons 1, 2, 6, 8 applied directly. Lesson 6 ("can this gate ever be satisfied?") is discharged in H-2 |
| `2026-08-18-lifecycle-gate-must-precede-safe-close-mutation` | Same root class: a gate whose whole value is its position **before** the mutation, and which can never pass afterwards. Confirms the ordering requirement is not merely stylistic |
| `2026-08-21-ast-based-structural-regression-guards-beat-line-regex` | Guard construction — section-scoped structural assertion, never widen-the-regex whack-a-mole |
| `2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation` | Origin of the Step 0(c) linked-deliberation extension; confirms the three engine-defined sources are the complete input set |
| `2026-09-07-copilot-review-finding-pattern-taxonomy` | RC-5 cross-surface state currency — why U3/U4/U5 (matrix, diagram, checksums) are in scope, not optional polish |
| `2026-08-12-close-path-decisions-must-use-the-classifier-not-summarized-prose` | U2(a)(2) records the qualifying set **by reference to the classifier's determination**, never a prose re-derivation |

### H-1 — The requirement is already stated three times; do not add a fourth statement

L473–475, L487–492 and L747–749 all state the ordering. The defect is **not** that the
requirement is missing — it is that nothing **evidences** it. U2 must therefore add an
**evidence obligation and a check**, and must resist the temptation to add a fourth
prose restatement of "do this before". D-5 makes this binding: state the new obligation
once, reference it from the Cascade Sub-Procedure.

### H-2 — Lesson 6 discharge: name a passing state and a failing state

> **SUPERSEDED BY R1-H2 (2026-09-10) where it conflicts.** The discharge below is the
> **pre-R1** formulation and is retained verbatim as history. It rests on
> `collection_completed_at` ordering, which R1-1 demoted to corroborating metadata,
> and it names `..._EVIDENCE_STALE` as the post-hoc-reconstruction detector, which
> R1-2 reassigned to the two anchor tokens. R1-H2 is the governing discharge; the
> lesson-6 obligation itself is unchanged.

* **Legitimate passing state:** 159-S's own shape, executed correctly — shipment record
  + covering feature `active` + tasks `done`; Step 0(c) runs at `T0`, writes
  `scan_performed: true, linked_deliberation_ids: []`, `collection_completed_at: T0`;
  cascade invoked at `T1 > T0`; HEAD SHA and manifest match. **PASSES.** *(Under R1 this
  state additionally requires a present anchor whose digest matches the record and whose
  append position precedes every engine-written mutation event — see R1-7's positive row.)*
* **Legitimate failing state:** the actual 159-S history — cascade at `T1`, collection
  reconstructed at `T2 > T1`. **FAILS** with
  `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE`, for the ordering reason. *(Under R1 this
  history fails with `..._ANCHOR_MISSING` — `.backlogit/logs/159-S.jsonl` carries no
  anchor before `archived` — and a **backdated** reconstruction, which the pre-R1
  formulation could not fail at all, fails with `..._ANCHOR_MISSING` or
  `..._ANCHOR_NOT_PRE_MUTATION`, never with `..._EVIDENCE_STALE`.)*

The gate is reachable. It is not the 161-F unsatisfiable-gate shape.

### H-3 — Protected invariants (must not regress)

1. The three engine-defined sources and the exact matcher
   `\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b` are unchanged; the evidence record **records**
   them, it does not redefine them.
2. `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS` / `RECONCILE_FAIL_SNAPSHOT_MISSING` semantics are
   unchanged; the two new tokens are additive.
3. The reference-only rule (`allowed_ids` / `required_ids` are defined by reference to
   Step 0(c)'s determination, never re-derived) is preserved.
4. Declared status is read from frontmatter, never inferred from `queue/` vs `archive/`
   location (lesson 8; also 161-F's R-1).
5. The two-set gate's two independently-failing conditions stay unmerged.
6. `mode: detect-mixed-role` remains strictly read-only; the evidence record is written
   only on the safe-close/cascade path.

### H-4 — Ordering and lock invariants

The evidence emission happens **inside** the existing single-writer lock on
`.backlogit/queue/{shipment_id}.md`, between Step 0(c) and the cascade invocation. It
introduces no new lock, no second writer, and no new failure window. It must **not** be
hoisted before lock acquisition, or the record could describe a state another writer
then changed.

### H-5 — Risky actions

| Action | Risk | Control |
|---|---|---|
| Editing the destructive close path's contract | A wrong edit corrupts an irreversible operation | RED-first (U1a/U1b); U2 atomic; no behavioural change to the cascade call itself |
| New halt tokens on a close path | Could block legitimate closures | H-2 names the passing state; U3 encodes it as a positive matrix row |
| Hand-edited resolved copy + template | Divergence | Same-commit paired edit + parity assertion (U1c) + checksum recompute |

### H-6 — Unresolved operator decisions

**None blocking.** The disposition is decided (2026-09-08). This plan carries **no**
merge authorization for PR #436 and requests none; it neither requires nor implies any
further PR #436 review round.

## Plan Hardening — Revision R1 (2026-09-10)

R1 is gate-shaped, on an irreversible destructive path, and adds halt tokens, so the
`requires_plan_hardening: yes` signal is reinforced rather than satisfied. A second
hardening pass was run over the revision only.

### R1-H1 — Does R1 create an unsatisfiable gate? (the `15A02E21` check)

**No — and this was checked first, because it is the failure mode this feature
exists to remove.** The passing state is named concretely in R1-7 and is reachable
today: the anchor uses backlogit's already-published append operation, needs no
network, no new file format, and no engine change. Verified empirically that the
anchor's substrate behaves as required — engine-written events, engine-owned append
order, and **log retention after archival on the local filesystem** (a proof that
vanished with the archival would make the gate unsatisfiable at exactly the moment
it must be audited). R1-11's L2 obligation does **not** re-introduce
unsatisfiability: it is not a gate input, it runs after the close, and its absence
halts nothing — it makes the closure *publication* incomplete, which is a reportable
P-001 condition, not an unreachable gate.

### R1-H2 — Lesson 6: name a passing state AND a failing state

* **Passing:** R1-7's positive row — the legitimate empty-set 159-S *shape* with a
  valid anchor.
* **Failing:** R1-5's backdated reconstruction — a record perfect under the original
  mechanism, rejected under R1 for the ordering reason. Both are executable
  assertions in `163.002-T`, not prose.

### R1-H3 — Protected invariants (re-checked against R1)

All H-3 invariants stand. Specifically re-verified: the three engine-defined sources
and the exact matcher are untouched; `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS/_MISSING`
semantics are untouched (R1's tokens are additive); the reference-only
`allowed_ids`/`required_ids` rule is untouched; declared frontmatter status is still
never inferred from storage location; the two-set gate's conditions stay unmerged —
and R1 **applies** that same rule rather than eroding it, by refusing to collapse its
own four tokens; `mode: detect-mixed-role` stays strictly read-only.

### R1-H4 — Ordering and lock invariants

The anchor append happens **inside** the existing single-writer lock on
`.backlogit/queue/{shipment_id}.md`, in the same window as the record write, between
Step 0(c) and the cascade invocation. It introduces **no new lock, no second writer,
and no new failure window**, and MUST NOT be hoisted before lock acquisition.

**New failure mode considered:** the record is written but the anchor append fails
(engine error). This is a torn state, and it fails **closed** —
`..._ANCHOR_MISSING` fires on the subsequent check and the close halts. That is the
correct outcome and requires no compensating logic; the orphaned record is inert.
The reverse tear (anchor written, record write fails) is caught by the digest
mismatch clause of the same token.

### R1-H5 — Risky actions

Editing halt-token semantics on a destructive path. Mitigated by narrowing rather
than redefining the two pre-existing tokens, keeping their names stable, and adding
the two new tokens additively — no existing caller or test that asserts the old token
names changes meaning.

### R1-H6 — Blast radius

Unchanged from the original plan: two hand-edited files (skill + template), the test
module, the scenario matrix, the diagram, and manifest checksums. **No Python source,
no schema, no CLI, no new template family.** R1 adds no file to the set. R1-11 adds
no file either — it force-tracks, at the closure commit, an engine log the close
already writes, bounded to the single shipment being closed; it changes no
`.gitignore` rule and touches no other log.

### R1-H7 — Unresolved decisions

**None blocking.** Two follow-ups are recorded as Open Questions in the decision
artifact — a dedicated engine-side anchor event type (a backlogit feature request,
strictly stronger but not required under the stated threat model) and the dependence
on backlogit's log-retention behaviour, which `163.003-T`'s guard cannot assert
because it is third-party engine behaviour rather than contract text. Neither blocks
R1.

## Plan Review

### Capability probe (P-012)

`backlogit` MCP transport closed; CLI fallback (`backlogit` v1.10.1) exercised and
functional — `TOOL_DEGRADED: backlogit MCP — CLI fallback: backlogit`. Engram, intercom
and graphtor-docs MCP tools not exposed in this session — `ENGRAM_DEGRADED`,
`INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`; file-based exploration used throughout, and
all cited line numbers were read directly rather than recalled.

**Cycle 2 (2026-09-10) probe:** `backlogit` MCP transport **available** —
`TOOL_OK: backlogit`; `INDEX_SYNC_OK`. Engram, intercom and graphtor-docs remain
unexposed — `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`. All R1
claims about engine log behaviour were verified by direct file inspection rather than
recalled, and are cited by filename in R1-1.

### Persona coverage

| Persona | Finding |
|---|---|
| **Contract/protocol reviewer** | Requirement stated once, referenced elsewhere (D-5). No fourth restatement. **PASS** |
| **Fail-closed design reviewer** | Two tokens, independently evaluated, both P-005, neither authorizes safe-close fallback. Lesson 6 discharged in H-2. **PASS** |
| **Composed-state-machine reviewer** | New gate sits between Step 0(c) and the cascade call, inside the existing lock; no interaction with Pre-Mode's member-class contract (169-S) beyond textual adjacency. **PASS** |
| **Test-quality reviewer** | Section-scoped structural assertions, not file-wide regex. Reconstruction rejection asserted **for the ordering reason**, so a content-equality implementation cannot satisfy it. **PASS** |
| **Scope/width reviewer** | Skill + template + tests + diagram + checksums. No CLI, no schema, no Python source. 7 tasks, each ≤2h. **PASS** |
| **Evidence-consistency reviewer** | Plan asserts no retroactive compliance; 159-S disclosure remains permanent. Traceability to 856B6770, 9E22BFC6, 27F9EC8A carried in frontmatter. **PASS** |

### Findings

* **P1 — none.**
* **P2-1** (in-body, resolved): first draft placed the evidence emission before lock
  acquisition. Corrected in H-4 — emission is inside the lock.
* **P2-2** (in-body, resolved): first draft asserted reconstruction rejection via
  content comparison, which the 159-S history would have **passed** (its content was
  byte-identical). Corrected in U1b — rejection must be on the ordering axis.
* **P3-1** (accepted): U5's checksum task overlaps 169-S's own (absent) checksum step.
  Scoped to this feature's edits only; the `blocks` dependency makes the ordering
  deterministic.

### Gate decision

**PASS** — zero P0, zero P1. Cycle 1. Proceed to harvest.

## Plan Review — Cycle 2 (Revision R1, 2026-09-10)

Scope of this cycle: **the R1 revision only.** Cycle 1's PASS over the unrevised
units stands and was not re-litigated.

### Persona coverage

| Persona | Finding |
|---|---|
| **Contract/protocol reviewer** | Anchor obligation stated once in the Step 0(c) extension; Cascade Sub-Procedure references it. The D-5 single-statement rule is extended to the anchor rather than bypassed. **PASS** |
| **Fail-closed design reviewer** | Four tokens, independently evaluated, all P-005, none authorizes a safe-close fallback. Torn-state analysis (R1-H4) confirms both tear directions fail closed. **PASS** |
| **Composed-state-machine reviewer** | R1 is precisely a composed-state-machine correction: it stops proving an ordering property from agent-authored data and starts proving it from the engine's own append order. Substrate behaviour verified against live logs, including post-archival retention. Residual third-party-behaviour dependence recorded as an Open Question, not hidden. **PASS** |
| **Test-quality reviewer** | R1-5 asserts **token identity**, not merely rejection, so a content-equality implementation cannot satisfy it. The assertion fails against the pre-R1 mechanism — a genuine RED. Section-scoped guards retained. **PASS** |
| **Scope/width reviewer** | No new files, no new units, no new task, no Python source. Task count still 7. Sizes re-evaluated; all within the 2-hour rule. **PASS** |
| **Evidence-consistency reviewer** | Stale "not yet committed to any branch" claims for the 161-F/162-F artifacts corrected to their actual publication commits. No retroactive-compliance claim introduced; 159-S disclosure remains permanent. Traceability to `DDBF283E`/`EB23D1B9` carried in frontmatter and in `033-DL`. **PASS** |
| **Security/integrity reviewer** | The claim is bounded to tamper-**evidence** and explicitly declines a tamper-proofness claim (R1-8). The digest binding closes the anchor-early/fabricate-record-later seam. **PASS** |

### Findings

* **P0 — none. P1 — none.**
* **P2-3** (in-body, resolved): a draft of R1 put the digest match under
  `..._EVIDENCE_STALE`. That would have reported a forged anchor as a stale record,
  losing the very diagnostic R1 exists to create. Moved to `..._ANCHOR_MISSING`
  (R1-2).
* **P2-4** (in-body, resolved): a draft left `collection_completed_at` co-equal with
  the anchor, which would let a future reader re-promote it to load-bearing. R1-1 now
  requires an explicit demotion sentence in-skill, and R1-6 makes the guard assert it.
* **P3-2** (accepted): `163.004-T` rises to `complexity: high`. Not split — the task
  is INDIVISIBLE and the indivisibility argument is *strengthened* by R1 (the anchor
  is the record's proof, binding emission and check more tightly than before).
  De-risked instead, as the two-axis gate permits, by this deliberation, by RED-first
  ordering, and by this review cycle.
* **P3-3** (accepted, tracked as an Open Question): nothing asserts backlogit's
  log-retention behaviour, because it is third-party engine behaviour rather than
  contract text. A future regression there would silently weaken the gate. Accepted
  for this shipment; recorded in the decision artifact.

### Gate decision

**PASS** — zero P0, zero P1. Cycle 2. R1 is accepted; `171-S`'s revised contract is
sealed and `033-DL` may reach its terminal state.

## Plan Hardening — R1-11 (2026-09-10, review-fix cycle 1)

R1-11 touches a fail-closed gate's *evidence* surface on an irreversible destructive
path, so the `requires_plan_hardening: yes` signal is again reinforced. A third
hardening pass was run over R1-11 only.

### R1-11-H1 — Does R1-11 create an unsatisfiable gate? (the `15A02E21` check)

**No, and the check drove the design.** The obvious shape — "add a fifth token that
fails when the tracked log is absent" — *is* the `15A02E21` mistake: it gates the
close on an artifact that cannot exist until after the close. That shape was
explicitly rejected. L2 is placed at the closure/publication boundary, where it is
satisfiable by construction, and the pre-cascade gate surface is left at exactly
four tokens.

### R1-11-H2 — Lesson 6: name a passing state AND a failing state

* **Passing (L2):** a shipment closed through the cascade path whose closure commit
  contains the evidence record and that shipment's own engine log, force-added and
  byte-identical to the engine's bytes. Reachable with `git add -f`, no engine
  change, no network.
* **Failing (L2):** the same close published without the engine log. Reported as an
  **incomplete closure** (P-001), not as a halt, not as a gate failure, and never as
  grounds to re-run or weaken the L1 check.
* **L1 unchanged:** R1-H2's passing and failing states stand verbatim.

### R1-11-H3 — Protected invariants (re-checked against R1-11)

All H-3 invariants stand and none is touched: R1-11 adds no source, no matcher, no
status-inference, and no lock. Additionally re-verified: **token count is exactly
four** (R1-11 adds none and `163.003-T`'s guard now *fails* if a fifth PRECASCADE
halt token appears); **no field the collecting agent authors becomes load-bearing**
(L2 commits the engine's bytes, not a transcription); **`collection_completed_at`
stays demoted** (it is consulted in none of the three fresh-clone verification
steps); and the **D-5 single-statement rule** extends to the L2 obligation rather
than being bypassed by it.

### R1-11-H4 — Ordering and lock invariants

L2 runs at the closure commit, **outside and after** the single-writer lock window,
and touches no file the lock protects. It introduces no new lock, no second writer,
and no new failure window. It cannot be hoisted into the lock window — the log it
publishes is not complete until the cascade's own mutation events have been
appended.

### R1-11-H5 — Risky actions

| Action | Risk | Control |
|---|---|---|
| Force-adding a path covered by `.gitignore` | Scope creep into a general un-ignoring of `.backlogit/logs/`, or an unrelated `.gitignore` edit | Bound stated three times and asserted by the guard: **one shipment's log, at its own closure commit, unmodified.** No `.gitignore` change is authorized by this plan |
| Publishing an engine log into the repository | Repository growth; accidental publication of unrelated shipment logs | Bounded to the closed shipment only; historical backfill explicitly out of scope |
| A reader mistaking L2 for a gate | Fail-closed posture appears to move to a post-close artifact | L2 is labelled non-gating in the skill text, asserted as non-gating by `163.003-T`, drawn as unwired in the diagram (`163.006-T`), and excluded from the scenario matrix (`163.005-T`) |

### R1-11-H6 — Blast radius

Unchanged file set. R1-11 adds **no file, no unit, no task, no token, no
`.gitignore` change, and no Python source change**; it adds contract text to the two
already-edited copies and assertions to already-existing tasks.

### R1-11-H7 — Unresolved decisions

**None blocking.** The `.gitignore` rule for `.backlogit/logs/` is an existing
workspace state that this plan deliberately does **not** change; whether that rule
should be revisited is a separate operator question and is not a prerequisite for
R1-11, which works with the rule as-is via a bounded force-add.

## Plan Review — Cycle 3 (review-fix cycle 1 remediation, 2026-09-10)

Scope of this cycle: **the review-fix cycle 1 remediation only** — the frontmatter
defect, R1-11, the U4 create→update correction, the superseded pre-R1 token wording,
and the `033-DL` dependency-encoding correction. Cycles 1 and 2 stand and were not
re-litigated.

### Capability probe (P-012)

`backlogit` MCP transport **available** — `TOOL_OK: backlogit`; `INDEX_SYNC_OK`.
`agent-intercom` callable surface **unavailable** — `INTERCOM_DEGRADED`, operator
visibility reduced; no phase broadcasts emitted and no approval-dependent
destructive action attempted. Engram and graphtor-docs MCP tools not exposed —
`ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`; file-based exploration used throughout.
Every claim in this cycle about file existence, ignore rules, dependency edges and
checkpoint contents was verified by direct inspection, not recalled.

### Persona coverage

| Persona | Finding |
|---|---|
| **Contract/protocol reviewer** | The L2 obligation is stated once and referenced, extending D-5 rather than bypassing it. Token count is pinned at four in the plan, the guard task, the matrix task and the diagram task, so the four surfaces cannot drift apart. **PASS** |
| **Fail-closed design reviewer** | L1 remains the sole gate input; all four tokens are unchanged in name, count and independence. L2 cannot downgrade a halt, cannot authorize a close, and is not a fallback. Its own failure mode is relocated to the closure boundary as a reportable P-001 condition rather than being dropped. **PASS** |
| **Composed-state-machine reviewer** | The corrected `033-DL` narrative is now consistent with the engine's actual behaviour: backlogit shipment eligibility takes shipment predecessors only, the rejected shipment→deliberation edge is described as rejected, and the real gate is recorded at feature/task level. This is the same composed-contract seam the feature exists to address, so getting the description right matters. **PASS** |
| **Test-quality reviewer** | `163.003-T` gains an assertion that *fails* if a fifth PRECASCADE token appears — a negative assertion, not just a presence check, which is what stops L2 being promoted into the gate by a future editor. **PASS** |
| **Scope/width reviewer** | No new file, no new unit, no new task, no Python source, no schema, no CLI, no `.gitignore` change. Task count still 7. `163.006-T` re-sized `XS`→`S` and `trivial`→`low` to match its grown (four-token + anchor + split) scope; still well inside the 2-hour rule. **PASS** |
| **Evidence-consistency reviewer** | Stale `not yet committed` claims in `163.005-T`/`163.006-T` synchronized with `163.004-T`'s publication wording (commit `5171ace1` on `main`). Elided `Plan: ... U3/U4/U5` references expanded to the full plan path in `163.005-T`/`163.006-T`/`163.007-T`. `170-S` given `priority: high` to match `162-F` and sibling shipment ordering. **PASS** |
| **Security/integrity reviewer** | The durability claim is now scoped to an audience in every place it appears. L2 publishes the engine's own bytes, so the "no agent-authored field is load-bearing" property survives into the repository; an agent-written excerpt was considered and rejected for exactly that reason. Tamper-**evidence** claim unchanged; no tamper-proofness claim introduced. **PASS** |

### Findings

* **P0 — none. P1 — none.**
* **P0-1 (resolved, this cycle):** duplicate `shipment` key in
  `docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md`
  — the harvested shipment `169-S` and the subject shipment `159-S` both claimed
  `shipment:`, so a YAML parser silently kept only the last. Renamed the harvest
  relationship to `harvested_shipment` / `harvested_shipment_status`; subject
  `shipment: 159-S` preserved. Verified by parsing: 29 distinct keys, both values
  now readable. A repository-wide duplicate-key scan over all `docs/**` and
  `.backlogit/**` frontmatter found no other occurrence.
* **P1-1 (resolved, this cycle):** the R1 anchor was described as durable and
  auditable without naming an audience, while `.backlogit/logs/` is `.gitignore`d —
  overstating repository auditability. Resolved inside the R1 evidence-gate contract
  by R1-11's L1/L2 split plus the bounded tracked-log closure obligation. Fail-closed
  behaviour is unchanged and ignored logs are nowhere described as remotely durable.
* **P2-5 (resolved):** `163.006-T` and plan U4 asserted diagram 05 and `docs/diagrams/`
  did not exist and instructed **create**. Both exist (operator-approved 2026-09-07
  under `G-DIAG-REVIEW`, present as working-tree artifacts). Retargeted to **update**,
  and extended to show the R1 anchor and all four halt tokens rather than two.
* **P2-6 (resolved):** `D-4` and `H-2` still carried the pre-R1 two-token and
  `..._EVIDENCE_STALE`-as-reconstruction-detector wording. Marked **superseded** with
  the governing R1 semantics restated in place; the historical text is retained rather
  than erased, per the no-history-erasure rule.
* **P3-4 (accepted, tracked):** the workspace `.gitignore` rule that motivates R1-11
  is itself uncommitted working-tree state at the time of this cycle. R1-11 is
  written to be correct under the rule either way — a bounded force-add is a no-op
  for a path that is already tracked and the required action for a path that is
  ignored — so no dependency on that rule's publication is introduced.
* **P3-5 (accepted, tracked as residual risk — stash `904C47BC`):** the checkpoint
  payload contract conflict. `checkpoint-20260909-232909.json` carries a top-level
  `progress` object, which harness `backlogit.instructions.md` rule 4 forbids and the
  engine's own CheckpointV1 schema explicitly permits as a legal top-level key. This
  is a composed-contract conflict, not a corrupt artifact, and it is **not** resolved
  by this cycle: the tool-owned checkpoint was **not** hand-edited, no file was
  quarantined or repaired, and no self-authorized disposition was made. Full scope,
  duplicate scan and disposition guidance live in `904C47BC`, which remains **active
  and undispositioned** with `requires deliberation: yes` unmet.

### Gate decision

**PASS** — zero unresolved P0, zero unresolved P1. Cycle 3 of a 3-cycle budget.
Every finding raised in this cycle passed the P-021 C1 same-contract-surface test
and was fixed rather than deferred; no `DEFERRED SCOPE EXPANSION` capture was
required. `904C47BC` is pre-existing, separately captured, and carried as residual
risk — not a deferral created by this cycle.

