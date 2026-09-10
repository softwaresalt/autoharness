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
plan_review_cycles: 4
revision: "R1 (2026-09-10) — Step 0(c) evidence-anchor mechanism redesign. Replaces the self-reported `collection_completed_at` ordering proof with an engine-written append-only anchor. Amends U1a, U1b, U1c, U2, U3. Requirements RQ-1/RQ-2/RQ-3 are UNCHANGED; only the mechanism satisfying RQ-2's 'provably pre-mutation' clause is redesigned. See the Revision R1 section below. R1-11 (added 2026-09-10, review-fix cycle 1) splits local runtime ordering proof (L1, gate-bearing) from repository audit evidence (L2, never gate-bearing) and adds the bounded tracked-engine-log closure obligation; U4 is corrected from create to update. R1-12 (added 2026-09-10, review-fix cycle 2) corrects R1-11's false git-state premise, supersedes the residual pre-R1 timestamp-ordering comparison, and gives the L2 obligation a real executor — new unit U6 / task 163.008-T. R1-12 GOVERNS over R1-11 and R1 where they conflict."
decision_label_namespacing: "Two artifacts in this set both number their decisions D-1..D-8 and the sequences are NOT the same. Cite them qualified: `plan D-n` means the Decisions and Rationale table in THIS file; `redesign decision D-n` means docs/decisions/2026-09-10-step-0c-evidence-anchor-mechanism-redesign-deliberation.md. Bare `D-n` is ambiguous and MUST NOT be used. Notable collisions: plan D-5 (state the requirement once) vs. redesign decision D-5 (2-hour rule and two-axis sizing); plan D-7 (no Python source change) vs. redesign decision D-7 (L1/L2 durability split)."
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

> **Durability scope — read with R1-11 as corrected by R1-12.** The claim above is
> about **local filesystem** retention only: it says the log survives archival, not
> that it reaches the repository. Whether a given shipment log is repository-durable
> depends on that path's **tracking state**, which R1-12 establishes by direct
> inspection rather than by assumption — most shipment logs in this repository are
> **already tracked**. R1-11 splits the two concerns and states the closure
> obligation that makes the claim auditable from a clean clone; R1-12 corrects how
> that obligation is discharged. R1-1 remains the **only** gate-bearing proof.

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

**Timestamp-comparison supersession (stated once; R1-12 makes it binding).** Under R1
`collection_completed_at` is **corroborating only**. Its **absence** may still fire
`..._EVIDENCE_STALE`, because the contract requires the field to be present — that is
a **content/completeness** failure, not an ordering determination. But a
`collection_completed_at` that is present and **not strictly before** the cascade
invocation MUST **NOT** by itself reject, provided a valid digest-bound anchor
precedes the mutation events in append order. The pre-R1 `collection_completed_at <
cascade_invocation` comparison is **superseded and removed from the load-bearing
path** everywhere it appears in this plan and in the harvested tasks. **The ordering
assertion uses engine-log append order and nothing else.** Any surviving sentence
that describes an ordering family as "unchanged" must be read as narrowed by this
paragraph.

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

The **explicit-empty** assertion family is unchanged. The **ordering** assertion
family is **narrowed, not unchanged** (corrected by R1-12): it keeps its name and its
"no evidence record at the cascade invocation is a rejection" clause, but its
`collection_completed_at`-versus-cascade-timestamp comparison is **superseded and
removed** per R1-2's timestamp-comparison supersession. It now asserts **engine-log
append order only**. An earlier revision of this paragraph said the ordering family
was "unchanged"; that was inaccurate and is retained here only as corrected history.

### R1-6 — U1c guard additionally asserts the R1 contract text

Same section-scoped technique, no file-wide regex. Within the resolved Step 0(c)
slice, assert: the anchor emission obligation; all four token names; the
`collection_completed_at` demotion sentence; the strengthened anti-reconstruction
clause; and the R1-11 **L1/L2 durability-split sentence** — specifically that the
engine log is the sole gate input and that the tracked-log closure obligation is
explicitly *not* a gate and *not* a fallback — and (added by R1-12) the **U6
publication step** with its non-`PRECASCADE` reportable-condition name. The
single-statement rule (**plan D-5**) extends to the anchor obligation, to the L2
obligation and to the U6 step — each stated once, referenced from the Cascade
Sub-Procedure.

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
it once in the Step 0(c) extension (**plan D-5**) and, if the quality criteria mention
it at all, mention it as a closure obligation explicitly marked non-gating.

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
tamper-evident **to a reader who can see the engine log**. Whether a repository
reader can see it depends on that log path's **tracking state**, not on an assumed
blanket ignore rule — see R1-12, which replaces the incorrect "`.backlogit/logs/` is
`.gitignore`d, therefore invisible" premise with a per-path conditional. R1-11 states
the L1/L2 split and R1-12 gives it an executor, so the evidence reaches a fresh clone
in every tracking state. Do not describe the anchor as "durable" or "auditable"
without naming which of the two audiences is meant.

### R1-9 — What R1 does NOT change

No Python source change (Non-Goal preserved). No new artifact **kind**: R1-11's L2
obligation creates no file — it publishes an engine log that the close already
produces, committing it in the same closure commit as the already-tracked evidence
record. No `.gitignore` change, and no widening of `.backlogit/logs/` publication
beyond the single shipment being closed. No change to `169-S`/`161-F` or
`170-S`/`162-F` scope. No re-opening of the 856B6770 disposition. **No
retroactive-compliance claim for 159-S** — it remains a permanently disclosed
deviation, and R1 is forward-only. The `blocks` dependency on `169-S` is unchanged;
U2 is still authored against post-169-S text. Every H-3 protected invariant stands,
and R1-11 adds, removes, renames, or merges **no halt token** — the gate surface is
exactly the four tokens of R1-2.

> **NARROWED BY R1-12 (2026-09-10, review-fix cycle 2).** This section previously
> also claimed "no new implementation units, no new task". That was true of R1 and
> R1-11 as authored, and it is **no longer true of the plan as a whole**: R1-12 adds
> exactly **one** unit (**U6**) and **one** task (`163.008-T`) to give the L2
> obligation an executor, because a normative obligation with no implementation
> surface is unenforceable. The original wording is retained above, minus the
> now-false clause, rather than erased. Everything else in this section still
> stands, including the four-token gate surface: U6 adds **no** halt token and
> **no** `PRECASCADE` token.

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

R1-1 asserted the anchor is durable and auditable. That was **overstated**: it named
no audience. Local-filesystem retention is not repository publication, and a reviewer
holding only a fresh clone needs the evidence to be *in the repository*. R1-11 removes
that gap **without** relaxing the gate.

> **R1-11's original premise was factually wrong, and R1-12 corrects it.** R1-11 as
> first written asserted that `.backlogit/logs/` "is covered by a workspace
> `.gitignore` rule", that a shipment log is therefore "not repository-durable by
> default", and that "a fresh-clone reviewer cannot see it at all". Direct
> verification (2026-09-10, review-fix cycle 2) refutes the categorical form of that
> claim; the corrected premise is stated in R1-12 below. R1-11's **conclusion** —
> name L1 and L2 separately, keep L1 the sole gate input, and make L2 a closure
> obligation — survives the correction. Only the mechanism by which L2 is discharged
> changes.

The two concerns are now separately named. They are **not** interchangeable and
neither substitutes for the other.

| Layer | Artifact | Written by | Audience | Gate-bearing? |
|---|---|---|---|---|
| **L1 — local runtime ordering proof** | `PRECASCADE_EVIDENCE_ANCHOR` event in `.backlogit/logs/{shipment_id}.jsonl` | the **engine** (timestamp, actor, append position) | the closing workspace, at close time | **YES — the sole gate input.** All four R1-2 tokens evaluate L1 and only L1 |
| **L2 — repository audit evidence** | the same engine log, **published in the closure commit** by whichever staging action that path's tracking state requires, alongside the already-tracked evidence record under `.backlogit/reconcile/` | the **engine** (bytes are the engine's, verbatim and unmodified); the closing agent performs only the staging | a fresh-clone reviewer, after the close | **NO — never a gate input, never a fallback** |

**L1 is unchanged.** The four tokens in R1-2 read the live engine log inside the
existing lock, before the cascade invocation. Nothing in R1-11 or R1-12 adds, removes,
renames, merges, or weakens a token; nothing in either is consulted by the gate; and
the absence, failure, or unavailability of L2 **never** authorizes a close, never
downgrades a halt, and never produces a fallback path. L2 is written **after** the
mutation the gate already permitted, so it is structurally incapable of being a
pre-mutation gate.

### R1-12 — Corrected git-state premise, and the conditional L2 publication contract

**Verified by direct inspection on 2026-09-10 (review-fix cycle 2), not recalled:**

| Fact | Evidence |
|---|---|
| `origin/main`'s `.gitignore` contains **no** `.backlogit/logs/` rule | `git show origin/main:.gitignore` — the `.backlogit/` block is `*.db`, `hooks_queue.jsonl`, `*.db-shm`, `*.db-wal`, `runtime/` |
| Shipment and item logs are **already tracked** in `origin/main` | `git ls-files .backlogit/logs/` lists 993 of 1016 local logs, including `150-S`, `159-S`, `163.006-T`, `169-S` and **`171-S`** — this feature's own shipment |
| The `.backlogit/logs/` ignore rule exists **only** as an uncommitted working-tree edit | `git diff .gitignore` shows it as a local addition at line 15; it is not in `origin/main` |
| A `.gitignore` rule **never** hides an already-tracked path | git ignore rules apply to untracked paths only. `git check-ignore` confirms this asymmetry: it reports nothing for the tracked `171-S.jsonl` without `--no-index`, while the untracked `161.001-T.jsonl` matches `.gitignore:15` |

Therefore R1-11's "the log is invisible to a fresh clone, so force-add it" framing is
**not** the general case, and an unconditional `git add -f` is the wrong instruction:
for the already-tracked majority it is a no-op dressed up as an integrity control, and
it silently implies an ignore rule this plan does not own and must not depend on.

**Conditional publication contract (replaces the unconditional force-add).** At the
closure commit for a shipment closed through the cascade path, the closing agent
resolves `.backlogit/logs/{shipment_id}.jsonl` into exactly one of three cases and
acts accordingly:

| Case | Detection | Action |
|---|---|---|
| **A — already tracked** (the state of `171-S` today) | `git ls-files --error-unmatch <path>` exits `0` | Commit its mutation **normally**. No force-add is performed or authorized |
| **B — untracked, not ignored** | `ls-files` misses **and** `git check-ignore -q --no-index <path>` exits non-zero | `git add <path>` — an ordinary add of that exact path |
| **C — untracked and ignored** | `ls-files` misses **and** `check-ignore --no-index` exits `0` | `git add -f <path>` — force-add **limited to that one shipment log** |

**The durable postcondition is identical in all three cases, and it — not the staging
verb — is the obligation:** *the engine-authored bytes that L1 evaluated for this
shipment are present in the closure commit, byte-unmodified.* The case analysis only
selects the mechanically correct way to reach that postcondition from whatever state
the repository is actually in. Nothing here reads, requires, or modifies `.gitignore`.

**Verification criteria (each case is detected, not assumed).** The closure check
MUST record which case applied and MUST verify:

1. **Presence** — `git cat-file -e {closure_commit}:.backlogit/logs/{shipment_id}.jsonl`
   succeeds. This is the postcondition, and it is case-independent.
2. **Fidelity** — the committed blob is byte-identical to the engine log the gate
   read. A diff of any kind is a failure, not a warning.
3. **Ordering survives publication** — in the *committed* bytes, the
   `PRECASCADE_EVIDENCE_ANCHOR` line precedes the engine-written
   `shipment_status_changed` / `commit_tracked` / `archived` lines in append order.
4. **Boundedness, without reference to `.gitignore`** — the closure commit adds **at
   most one** newly-tracked path under `.backlogit/logs/`, and it is this shipment's
   own log. The commit contains **no** `.gitignore` modification. This is the bound,
   and it is asserted against the commit's own contents, so it holds whether the log
   was already tracked, newly untracked, or ignored.
5. **Case record** — the detected case (A, B or C) is written into the reconcile
   report, so a reviewer can tell a legitimate no-op (Case A) from an omitted
   publication.

**Why the engine's own bytes, and not an agent-written export.** A transcription,
summary, or excerpt would reintroduce exactly the defect R1-0 identified: an artifact
whose fields are written by the agent whose compliance is being checked. Committing
the engine's own bytes keeps the property that makes the anchor worth anything —
**no field the collecting agent authors is load-bearing**. Staging is an action over
bytes the agent did not write; it cannot alter append order, and any alteration is a
content change visible in the diff.

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

**Lifecycle ownership — the obligation has an executor (R1-12).** R1-11 declared a
missing L2 to be a **P-001 incomplete-closure** condition but assigned no
implementation surface, leaving a normative obligation nothing could enforce. R1-12
closes that gap by keeping the obligation **normative** and giving it an owner:

* **Owner:** the closing agent executing the `shipment-reconcile` cascade path — Ship,
  at operational closure. Not Stage, which never closes a shipment.
* **Implementation unit:** **U6** (new), harvested as task **`163.008-T`**, a paired
  prose edit to the same two files U2 already edits. It adds a **Post-Cascade
  Publication step** to the Cascade Close Sub-Procedure's closure section that
  performs the Case A/B/C detection, stages accordingly, runs verification criteria
  1–5, and records the outcome and the detected case in the reconcile report.
* **Reportable condition:** `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE`. This is a
  **P-001 incomplete-closure report**, not a halt token. Its name deliberately omits
  the `RECONCILE_FAIL_PRECASCADE_` prefix so that `163.003-T`'s "no fifth
  `PRECASCADE` token" negative assertion continues to pass, and so no reader can
  mistake it for a gate input.
* **What it never does:** it never authorizes a close, never downgrades or re-runs
  the L1 gate, never acts as a fallback for a failed L1 check, and never blocks the
  cascade. The mechanical close stands; only the *publication* is unfinished.

**Explicitly rejected.** Adding a fifth pre-cascade token for L2 (it would gate on an
artifact that cannot exist yet); un-ignoring `.backlogit/logs/` wholesale, or making
any `.gitignore` change at all (unbounded repository growth, and a dependency on
working-tree state this plan does not own); an agent-authored anchor excerpt or audit
summary (reintroduces self-reported evidence — R1-0); and leaving L2 **advisory** to
avoid the ownership problem (that would have required deleting every P-001 and
fail-closed claim attached to it, and would have left the fresh-clone auditability
hole the authorized redesign exists to close — so the obligation was given an
executor instead of being weakened).

**Propagated to** `163-F`, `163.003-T`, `163.004-T`, `163.005-T`, `163.006-T`,
**`163.007-T`** and the new `163.008-T`, and to `033-DL`.

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
   invocation with no pre-existing evidence record. **SUPERSEDED IN PART BY R1-2 AND
   R1-12:** the original clause continued "…a trace in which the evidence record's
   `collection_completed_at` is absent, or is **not strictly before** the cascade
   invocation timestamp, must be rejected", and that timestamp comparison is
   **removed from the load-bearing path**. Under R1 the ordering assertion is made
   **against engine-log append order only**. An **absent** `collection_completed_at`
   may still be rejected — as a content/completeness failure under
   `..._EVIDENCE_STALE`, because the contract requires the field — but a
   `collection_completed_at` that is present and **not strictly before** the cascade
   MUST NOT by itself reject when a valid digest-bound anchor precedes the mutation
   events in append order.
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
2. **Single-statement rule (plan D-5)** — the obligation is stated **once**; the Cascade
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

**(e) L2 repository audit evidence obligation (added by R1-11, corrected by R1-12;
NOT a gate).** State once, in the same Step 0(c) extension, that at the closure commit
for a shipment closed through the cascade path the closing agent publishes (i) the
evidence record under `.backlogit/reconcile/` and (ii) **that shipment's own** engine
log `.backlogit/logs/{shipment_id}.jsonl`, **verbatim and byte-unmodified**, using the
staging action that path's **tracking state** requires — an ordinary commit of its
mutation when the path is already tracked, an ordinary `git add` when it is untracked
and not ignored, and a `git add -f` bounded to that one log when it is untracked and
ignored (R1-12 Cases A/B/C). The durable postcondition, identical in all three cases,
is that the engine-authored bytes L1 evaluated are present in the closure commit.
State in the same place that this obligation is **not** a halt token, **not** a gate
input, and **not** a fallback: the four tokens of R1-2 read the live engine log only,
and a missing L2 makes the closure *publication* incomplete (a reportable P-001
condition) without ever authorizing, re-running, or weakening the L1 gate. Bounded to
one shipment at its own closure — **no `.gitignore` change**, no historical backfill,
no other log. The step that **performs and verifies** this obligation is **U6**; U2
only states it.

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

### U4 — Diagram currency (single canonical path, satisfiable from a clean clone)

**Canonical path — single and stable:**
`docs/diagrams/05-shipment-reconcile-cascade-premode.mmd`. This is the one and only
diagram this unit touches, and the path does not vary with the repository's state.

**Satisfiability rule (R1-12).** U4 must be executable from a clean clone of
`origin/main`, where `docs/diagrams/` does **not** yet exist — it was authored and
operator-approved on 2026-09-07 under gate `G-DIAG-REVIEW`, is recorded in the
`15A02E21` deliberation's `linked_artifacts`, and is currently present only as an
**untracked working-tree artifact** (verified 2026-09-10, review-fix cycle 2). U4
therefore resolves the canonical path at execution time:

* **present** (published by an unrelated change, or carried in the working tree) →
  **update it in place**;
* **absent** → **create that same canonical file**, at that same path, with the
  required content.

Either way the outcome is one file at one path. U4 **must never** create a second or
parallel diagram beside it, and must not branch the path on whether the file was
found. An earlier revision framed this as create-only, then as update-only; both were
wrong for the same reason — each assumed a repository state rather than resolving it.

**Optional verification, never a dependency.** `scripts/check_eraser_diagrams.py` is
**untracked and absent from `origin/main`** (verified 2026-09-10). Treat it as
**optional**: run it only if it is published and wired at execution time, and do not
make U4's completion, acceptance, or verification depend on an untracked file.

The diagram must draw, on the **pre-mutation** side of the cascade invocation:

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
* the R1-11 **L1/L2 split**, with L2 and the U6 publication step drawn on the
  post-close side and visibly **not** wired into any gate decision, so no reader
  infers a fifth halt token.

Per lesson 2 of the composed-state-machine learning, the diagram is where the seam
becomes reviewable.

### U6 — L2 publication step: the executor for the repository audit evidence obligation

**Added by R1-12 (2026-09-10, review-fix cycle 2).** U2(e) *states* the L2 obligation;
before R1-12 nothing *performed or verified* it, leaving a normative P-001 obligation
with no implementation surface. U6 is that surface.

**Paired edit, SAME COMMIT**, same two files U2 edits:
`.github/skills/shipment-reconcile/SKILL.md` **AND**
`templates/skills/shipment-reconcile/SKILL.md.tmpl`. No new file, no Python source
change, no `.gitignore` change.

Add a **Post-Cascade Publication step** to the Cascade Close Sub-Procedure's closure
section — stated **once** (**plan D-5**) and referenced, never restated — that the
closing agent (Ship, at operational closure) performs:

1. **Detect the tracking case** for `.backlogit/logs/{shipment_id}.jsonl` — Case A
   (tracked), B (untracked, not ignored) or C (untracked, ignored) per R1-12.
2. **Stage accordingly** — normal commit of the mutation (A), `git add` (B), or
   `git add -f` bounded to that one log (C). Never a bulk or wildcard add.
3. **Verify criteria 1–5 of R1-12** — presence in the closure commit, byte fidelity to
   the engine log, anchor-precedes-mutation append order *in the committed bytes*,
   boundedness asserted against the commit's own contents (at most one newly-tracked
   `.backlogit/logs/` path, and no `.gitignore` modification in the commit), and the
   detected case recorded.
4. **Record the outcome in the reconcile report** as an explicit published/not-published
   result plus the detected case, so a legitimate Case-A no-op is distinguishable from
   an omitted publication.
5. **On failure, emit `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE`** — a **P-001
   incomplete-closure report**, not a halt token. Its name deliberately omits the
   `RECONCILE_FAIL_PRECASCADE_` prefix so `163.003-T`'s "no fifth `PRECASCADE` token"
   negative assertion still passes.

**Hard constraints.** U6 adds **no** halt token and **no** `PRECASCADE` token; the
pre-cascade gate surface stays at exactly the four tokens of R1-2. It runs **outside
and after** the single-writer lock window, introduces no new lock and no second
writer, and it never authorizes a close, never downgrades or re-runs the L1 gate, and
is never a fallback for a failed L1 check.

**Depends on U2** (the obligation must be stated before it can be performed) and is a
dependency of **U5** (U5 consumes every prior edit's bytes for the checksum recompute).
Harvested as task `163.008-T`.

### U5 — Checksum recompute and GREEN

Recompute `.autoharness/harness-manifest.yaml` checksums for the edited skill and
template, and run the full suite green.

## Dependency Graph

```text
U1a (fixture)  ──┐
U1b (assertions) ┼──> U2 (ATOMIC CORE) ──> U3 ──┐
U1c (guards)   ──┘                     ──> U4 ──┼──> U5
                                       ──> U6 ──┘
```

RED units land first and must fail for the stated reason before U2; U6 (added by
R1-12) follows U2 because it performs an obligation U2 states; U5 is last because it
consumes every prior edit's bytes.

**Shipment-level:** this shipment carries a `blocks` dependency on **169-S**. Both edit
the same `SKILL.md` Step 0 region; 169-S is a sealed, plan-reviewed decomposition whose
`161.003-T` is marked *R-4 INDIVISIBLE ATOMIC CORE* and cannot be re-opened (PR #436 is
at its hard 3-cycle limit, P-018 blocked). Sequencing, not merging.

## Decisions and Rationale

> **Decision-label namespacing (R1-12).** These `D-n` labels are **this plan's**.
> `docs/decisions/2026-09-10-step-0c-evidence-anchor-mechanism-redesign-deliberation.md`
> has its own, unrelated `D-1..D-8` sequence. Cite them qualified — **`plan D-n`** for
> the table below, **`redesign decision D-n`** for the deliberation. Bare `D-n` is
> ambiguous and must not be used. The live collisions are **plan D-5** (state the
> requirement once) vs. **redesign decision D-5** (2-hour rule and two-axis sizing),
> and **plan D-7** (no Python source change) vs. **redesign decision D-7** (L1/L2
> durability split).

| # | Decision | Rationale |
|---|---|---|
| plan D-1 | Evidence record lives at `.backlogit/reconcile/`, the skill's existing report surface | Additive write to a location the skill already owns; no new storage contract, no backlog-state mutation |
| plan D-2 | The check tests **pre-existence**, not reproducibility | Reproducibility is Purpose 1, already satisfied in 159-S. Purpose 2 is the one that failed |
| plan D-3 | Empty result must be recorded explicitly | An unrecorded empty scan is indistinguishable from no scan — the precise 159-S failure |
| plan D-4 | Two separate halt tokens, independently evaluated | Merging two questions into one condition is the documented root cause of `B57F9E24`. **SUPERSEDED BY R1-2 (2026-09-10):** the *never-merge* principle stands and is unchanged; the *count* does not. The gate now carries **four** separately labelled, independently failing tokens — `..._EVIDENCE_MISSING`, `..._EVIDENCE_STALE`, `..._ANCHOR_MISSING`, `..._ANCHOR_NOT_PRE_MUTATION`. Read "two" here as pre-R1 history |
| plan D-5 | Requirement stated **once**, referenced elsewhere | Independent restatements drift; that is how `15A02E21` arose. Extended by R1 to the anchor obligation, by R1-11 to the L2 obligation, and by R1-12 to the U6 publication step |
| plan D-6 | Separate shipment, sequenced after 169-S | Different contract surface; 169-S's plan is sealed and cannot be re-reviewed |
| plan D-7 | No Python source change | The classifier already exposes everything Step 0(c) references |
| plan D-8 | The L2 obligation stays **normative** and gains an **executor** (U6 / `163.008-T`), rather than being softened to advisory | R1-11 attached P-001 incomplete-closure semantics to L2 but named no implementation surface, so nothing could enforce it. The two honest resolutions were "give it an owner" or "strip every P-001 and fail-closed claim from it". Stripping them would have re-opened the fresh-clone auditability hole the authorized redesign exists to close, so the obligation was given an owner: Ship, at operational closure, via a Post-Cascade Publication step in the same paired-edit surface. The reportable condition is deliberately named outside the `RECONCILE_FAIL_PRECASCADE_` namespace so the pre-cascade gate surface stays at four tokens (R1-12) |

## Risks and Caveats

| Risk | Mitigation |
|---|---|
| **Unsatisfiable gate** — the check can never pass | U3 names a concrete legitimate passing state (the empty-set 159-S shape). Lesson 6 check applied below |
| **Merge conflict with 169-S** in the same Step 0 region | `blocks` dependency on 169-S; U2 is authored against post-169-S text |
| **Guard passes on a phrase appearing elsewhere** in an 1082-line file | Section-scoped assertions (U1c), never file-wide regex |
| **Dogfood-parity drift** between resolved copy and template | Paired edit in the same commit; parity assertion in U1c; checksums in U5 |
| **Scope creep into 169-S or 170-S** | Explicit `related_but_distinct` frontmatter; separate feature, separate shipment |
| **Retroactive-compliance claim** | The plan and every harvested task state that 159-S remains a recorded, permanently disclosed deviation. This fix is forward-only |
| **A normative obligation with no executor** (R1-12) | L2 carried P-001 incomplete-closure semantics with no implementation surface. Closed by giving it an owner (Ship, at operational closure) and a unit (U6 / `163.008-T`) rather than softening it to advisory — plan D-8 |
| **Contract depending on uncommitted working-tree state** (R1-12) | R1-11 rested on a local, uncommitted `.gitignore` rule. Replaced by the Case A/B/C tracking-state conditional, with boundedness asserted against the closure commit's own contents; the plan now reads no ignore rule and changes none |
| **U4 unsatisfiable from a clean clone** (R1-12) | U4 previously assumed the diagram existed (it is untracked and absent from `origin/main`). Now resolves one canonical path at execution time — update if present, create that same path if absent, never a parallel diagram — and treats `scripts/check_eraser_diagrams.py` as optional |

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
no file either — it publishes, at the closure commit, an engine log the close already
writes, bounded to the single shipment being closed; it changes no `.gitignore` rule
and touches no other log. **R1-12 adds no file either**, but it does add one unit
(U6) and one task (`163.008-T`) inside the same two hand-edited files — see R1-12-H6.

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
| **Contract/protocol reviewer** | Requirement stated once, referenced elsewhere (plan D-5). No fourth restatement. **PASS** |
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
  contains the evidence record and that shipment's own engine log, byte-identical to
  the engine's bytes. Reachable with an ordinary commit, an ordinary `git add`, or a
  bounded `git add -f`, depending on the path's tracking case (R1-12) — no engine
  change, no network. For `171-S` itself the log is **already tracked**, so the
  passing state is reached by an ordinary commit.
* **Failing (L2):** the same close published without the engine log. Reported as an
  **incomplete closure** (P-001) by U6's `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE`
  condition — not as a halt, not as a gate failure, and never as grounds to re-run or
  weaken the L1 check.
* **L1 unchanged:** R1-H2's passing and failing states stand verbatim.

### R1-11-H3 — Protected invariants (re-checked against R1-11)

All H-3 invariants stand and none is touched: R1-11 adds no source, no matcher, no
status-inference, and no lock. Additionally re-verified: **token count is exactly
four** (R1-11 adds none and `163.003-T`'s guard now *fails* if a fifth PRECASCADE
halt token appears); **no field the collecting agent authors becomes load-bearing**
(L2 commits the engine's bytes, not a transcription); **`collection_completed_at`
stays demoted** (it is consulted in none of the three fresh-clone verification
steps); and the **plan D-5 single-statement rule** extends to the L2 obligation rather
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
| Staging a log path that may be covered by an ignore rule | Scope creep into a general un-ignoring of `.backlogit/logs/`, or an unrelated `.gitignore` edit | Bound stated three times and asserted by the guard: **one shipment's log, at its own closure commit, unmodified.** No `.gitignore` change is authorized by this plan. **R1-12 hardens this:** the bound is asserted against the *closure commit's own contents* (at most one newly-tracked `.backlogit/logs/` path, no `.gitignore` modification), so it holds without consulting any ignore rule |
| Publishing an engine log into the repository | Repository growth; accidental publication of unrelated shipment logs | Bounded to the closed shipment only; historical backfill explicitly out of scope |
| A reader mistaking L2 for a gate | Fail-closed posture appears to move to a post-close artifact | L2 is labelled non-gating in the skill text, asserted as non-gating by `163.003-T`, drawn as unwired in the diagram (`163.006-T`), and excluded from the scenario matrix (`163.005-T`). **R1-12:** U6's condition is named outside the `RECONCILE_FAIL_PRECASCADE_` namespace, and the guard's no-fifth-`PRECASCADE`-token assertion still passes |

### R1-11-H6 — Blast radius

Unchanged file set. R1-11 adds **no file, no token, no `.gitignore` change, and no
Python source change**; it adds contract text to the two already-edited copies and
assertions to already-existing tasks.

> **NARROWED BY R1-12.** This paragraph previously also said R1-11 adds "no unit, no
> task". That remains true of R1-11 itself. It is **not** true of the plan after
> R1-12, which adds exactly one unit (U6) and one task (`163.008-T`). The **file
> set** is still unchanged — U6 edits the same two files U2 edits.

### R1-11-H7 — Unresolved decisions

**None blocking.** **CORRECTED BY R1-12:** this section previously described "the
`.gitignore` rule for `.backlogit/logs/`" as "an existing workspace state" and said
R1-11 "works with the rule as-is via a bounded force-add". Both clauses rested on a
premise that direct inspection refutes — the rule exists only as an **uncommitted**
working-tree edit, `origin/main` has no such rule, and most shipment logs (including
`171-S`'s own) are **already tracked**, which no ignore rule can affect. R1-12
replaces the unconditional force-add with the Case A/B/C conditional and asserts
boundedness against the closure commit's contents, so the plan now depends on **no**
`.gitignore` state at all. Whether that local rule should be committed is a separate
operator question, and it is **not** a prerequisite for anything in this plan.

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


## Plan Hardening — R1-12 (2026-09-10, review-fix cycle 2)

R1-12 corrects a **false premise** underneath a fail-closed gate's evidence surface
and adds an implementation unit on an irreversible destructive path, so the
`requires_plan_hardening: yes` signal is reinforced again. A **fourth** hardening pass
was run over R1-12 only. (The plan has now had four hardening passes: original, R1,
R1-11, R1-12 — any statement of "two" is stale and superseded.)

### R1-12-H1 - Does R1-12 create an unsatisfiable gate? (the `15A02E21` check)

**No, and the check drove two of the three changes.**

* **U6** is placed at the closure/publication boundary, exactly where R1-11-H1 placed
  the obligation, and it emits a **report**, not a halt token. It gates nothing. Had
  it been added as a fifth `PRECASCADE` token it would have been the `15A02E21`
  mistake; it was deliberately named outside that namespace so the guard's
  no-fifth-token assertion keeps holding.
* **U4** was previously unsatisfiable from a clean clone in the literal sense: it said
  the diagram "exists" and instructed *update*, while the file is untracked and absent
  from `origin/main`. An agent starting from a clean clone would have had no
  satisfiable instruction. Resolving the canonical path at execution time makes the
  unit satisfiable in **both** repository states without introducing a parallel file.
* **L2** is satisfiable in all three tracking cases, and for `171-S` specifically it is
  satisfiable by an ordinary commit, because its log is already tracked.

### R1-12-H2 - Lesson 6: name a passing state AND a failing state

* **Passing (U6):** a cascade close whose closure commit contains the evidence record
  and the shipment's own engine log, byte-identical to the engine's bytes, with the
  anchor preceding the mutation lines in the committed bytes, at most one newly-tracked
  `.backlogit/logs/` path, no `.gitignore` modification in the commit, and the detected
  case recorded in the reconcile report.
* **Failing (U6):** the same close published without the engine log, or with bytes that
  differ from the engine's. Reported as `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE`, a
  P-001 incomplete-closure condition - never a halt, never a gate failure, never
  grounds to re-run or weaken L1.
* **L1 unchanged:** R1-H2's passing and failing states stand verbatim; R1-12 removes
  the residual `collection_completed_at` timestamp comparison from the ordering family
  but adds, removes and renames **no** token.

### R1-12-H3 - Protected invariants (re-checked against R1-12)

All H-3 invariants stand. Additionally re-verified: **token count is exactly four**
(U6 adds none, and its condition name is outside the `RECONCILE_FAIL_PRECASCADE_`
namespace precisely so `163.003-T`'s negative assertion still fires on a genuine fifth
token); **no field the collecting agent authors becomes load-bearing** (U6 stages the
engine's bytes and verifies them, it does not transcribe them); **`collection_completed_at`
stays demoted**, and R1-12 completes that demotion by removing the last surviving
timestamp comparison from U1b and `163.002-T`; and the **plan D-5** single-statement
rule extends to the U6 step rather than being bypassed by it.

### R1-12-H4 - Ordering and lock invariants

U6 runs at the closure commit, **outside and after** the single-writer lock window,
exactly as R1-11-H4 requires of L2. It introduces no new lock, no second writer, and no
new failure window, and it cannot be hoisted into the lock window - the log it
publishes is not complete until the cascade's own mutation events have been appended.
The R1-12 verification criteria read the **committed** bytes, which likewise only exist
after the lock is released.

### R1-12-H5 - Risky actions

| Action | Risk | Control |
|---|---|---|
| Adding a unit to a plan already at its review-cycle budget | Scope creep dressed as remediation | U6 edits **no new file** - it is a paired prose edit to the same two files U2 already edits, discharging an obligation this plan already declared normative. Operator-authorized under P-021 C1 as same-contract-surface completion |
| A conditional staging procedure | An agent picks the wrong case and force-adds unnecessarily, or misses a required force-add | Detection is mechanical (`git ls-files --error-unmatch`, then `git check-ignore --no-index`), the case is recorded in the reconcile report, and the postcondition is verified against the commit rather than inferred from the action taken |
| Correcting a premise that earlier cycles reasoned from | Silent history rewriting | Every corrected statement is marked **CORRECTED/NARROWED BY R1-12** in place, with the superseded wording retained. Cycles 1-3 remain intact and are not re-litigated |

### R1-12-H6 - Blast radius

**File set unchanged.** U6 touches the same two hand-edited files (skill + template)
that U2 edits. R1-12 adds **no file, no schema, no CLI, no Python source, no template
family, no halt token, and no `.gitignore` change**. It adds **one unit (U6)** and
**one task (`163.008-T`)**, taking the task count from 7 to 8, and it re-sizes
`163.003-T` (`S`->`M`) for the guard assertions accumulated across R1-11 and R1-12.
Because the affected **surfaces** did not expand - same two files, same shipment, same
feature - this hardening pass is the appropriate depth; no re-hardening of R1 or R1-11
was required.

### R1-12-H7 - Unresolved decisions

**None blocking.** Two carried items, both pre-existing and neither created here:

* the dedicated engine-side anchor event type (a backlogit feature request, strictly
  stronger, out of scope) and backlogit's log-retention behaviour, both recorded as
  Open Questions in the redesign decision artifact;
* stash **`904C47BC`** - the checkpoint payload contract conflict - remains **active
  and undispositioned**, with `requires deliberation: yes` unmet. It is carried
  forward as an explicit residual risk. No tool-owned checkpoint payload was read for
  edit, hand-edited, quarantined, or repaired by this cycle.

## Plan Review - Cycle 4 (review-fix cycle 2 remediation, 2026-09-10)

**Cycle-budget disclosure (stated plainly, not fabricated).** Cycle 3 closed the
3-cycle review-fix budget. This cycle exists **only** because the operator explicitly
directed a fresh full plan review as part of code-review fix cycle 2 over the
unpublished range `origin/main..8731383f`, which is the operator disposition the
circuit-breaker protocol names ("extend the cycle-count limit"). Per **P-021 C4**, that
extension authorizes **another pass over same-contract findings only** - it does not
make any out-of-scope expansion in-scope. Every change reviewed here passes the P-021
C1 same-contract-surface test: each one completes the exact evidence-gate contract this
plan already authorized. This section is labelled **Cycle 4** and appended; cycles 1-3
are retained verbatim and were not rewritten.

Scope of this cycle: **the review-fix cycle 2 remediation only** - the R1-2/R1-12
timestamp-ordering supersession, the corrected git-state premise, the L2 executor (U6 /
`163.008-T`), the U4 clean-clone satisfiability rule, decision-label namespacing, the
sizing-table corrections, and the propagation-list completion.

### Capability probe (P-012)

`backlogit` MCP transport **available** - `TOOL_OK: backlogit`; `INDEX_SYNC_OK`
(1185 items). `agent-intercom` callable surface **unavailable** -
`INTERCOM_DEGRADED`, operator visibility reduced; no phase broadcasts emitted and no
approval-dependent destructive action attempted. Engram and graphtor-docs MCP tools
not exposed - `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`; file-based exploration used
throughout. **Every git-state claim in this cycle was produced by running the command
named beside it** (`git ls-files`, `git show origin/main:.gitignore`, `git diff
.gitignore`, `git check-ignore -v [--no-index]`), not recalled and not inherited from
a prior cycle.

### Persona coverage

| Persona | Finding |
|---|---|
| **Contract/protocol reviewer** | The timestamp comparison is now superseded in one authoritative place (R1-2) and referenced from U1b, R1-5 and `163.002-T`, so the ordering rule is stated once rather than contradicted in three places. Decision labels are namespaced (`plan D-n` / `redesign decision D-n`), removing the D-5 and D-7 collisions. Plan D-5's single-statement rule now covers the anchor, L2 and U6 obligations. **PASS** |
| **Fail-closed design reviewer** | L1 remains the sole gate input; token count is still exactly four, unchanged in name and independence. U6 emits a **report**, not a token, and its name is deliberately outside the `RECONCILE_FAIL_PRECASCADE_` namespace so the guard's no-fifth-token assertion still fires on a real regression. A missing L2 still cannot authorize a close, downgrade a halt, or act as a fallback. **PASS** |
| **Evidence-consistency reviewer** | The false premise is corrected against direct evidence rather than argued away: `origin/main` carries no `.backlogit/logs/` ignore rule, 993 of 1016 logs are already tracked (including `171-S`'s own), and ignore rules never hide tracked paths. The uncommitted `.gitignore` edit is now a dependency of nothing and is left untouched. Superseded wording is marked in place, not deleted. **PASS** |
| **Lifecycle-ownership reviewer** | The P-001 obligation now has a named owner (Ship, at operational closure), an implementation unit (U6), a harvested task (`163.008-T`), an ordered position (after U2, before U5), and a recorded outcome in the reconcile report. The alternative - demoting L2 to advisory - was considered and rejected in plan D-8 with its consequence stated: it would have required deleting every P-001 and fail-closed claim and would have reopened the fresh-clone auditability hole. No normative obligation is left without an executor. **PASS** |
| **Satisfiability reviewer** | U4 is now executable from a clean clone and from a dirty working tree by the same instruction, against one canonical path, with an explicit never-create-a-parallel-diagram bound. `scripts/check_eraser_diagrams.py` is downgraded to optional, so no unit depends on an untracked file. **PASS** |
| **Scope/width reviewer** | One new unit, one new task, **no new file**, no Python source, no schema, no CLI, no `.gitignore` change. Task count 7 -> 8; `163.003-T` `S`->`M` for accumulated guard assertions; `163.006-T` corrected to `S`/`low` in the sizing table to match the record. Every task remains inside the 2-hour rule on both axes. **PASS** |
| **Traceability reviewer** | `163.007-T` is now present in every R1-11/R1-12 propagation list - plan, redesign decision D-7, and `033-DL` - closing the omission that left a task carrying an R1-11 note while absent from the lists that enumerate who carries one. `033-DL`'s post-terminal amendment now states the gate that authorized it. **PASS** |

### Findings

* **P0 - none. P1 - none unresolved.**
* **P1-2 (resolved, this cycle):** the plan asserted both "the ordering family is
  unchanged" and "the ordering family now asserts append order, not timestamp
  comparison", in U1b, R1-5 and `163.002-T`. Under a mechanism whose whole point is
  that agent-authored timestamps are not load-bearing, a surviving `collection_completed_at
  < cascade_invocation` rejection is a live contradiction: it can reject a legitimate
  close that has a valid anchor. Resolved by stating the supersession once in R1-2 -
  absence may still fail as a content/completeness defect, a present-but-late value may
  not reject on its own - and narrowing every "unchanged" sentence to say exactly what
  it now means.
* **P1-3 (resolved, this cycle):** R1-11 and redesign decision D-7 rested on the claim
  that `.backlogit/logs/` is ignored and therefore invisible to a fresh clone. Direct
  inspection refutes it for tracked paths, which are the majority and include this
  feature's own shipment log. Resolved by the Case A/B/C conditional, the
  tracking-state-independent durable postcondition, and boundedness asserted against
  the closure commit's contents. The plan now depends on no `.gitignore` state.
* **P1-4 (resolved, this cycle):** L2 carried P-001 fail-closed semantics with no
  implementation surface - an obligation nothing could execute or verify. Resolved by
  plan D-8 / U6 / `163.008-T` rather than by weakening the obligation.
* **P2-7 (resolved):** U4 assumed a repository state instead of resolving one, making
  it unsatisfiable from a clean clone. Now a single canonical path resolved at
  execution time, with the optional-script rule stated.
* **P2-8 (resolved):** `D-n` labels collided across the plan and the redesign decision
  (`D-5` and `D-7` each meant two different things). Resolved by a namespacing note in
  the frontmatter and in both decision tables, plus qualified live citations. Historical
  review sections (cycles 1-3) retain their bare labels as history and are governed by
  the namespacing note rather than rewritten.
* **P2-9 (resolved):** redesign decision D-5's sizing table was stale - it listed
  `163.006-T` as "unchanged" after cycle 3 had re-sized it `XS`->`S` / `trivial`->`low`.
  Corrected, `163.003-T` re-confirmed at `M`/`medium` for its accumulated R1-11 and
  R1-12 guard assertions, `163.008-T` added, and `163-F`'s stale "two hardening passes"
  count corrected to four.
* **P2-10 (resolved):** `163.007-T` was missing from the R1-11 propagation lists in the
  plan, in redesign decision D-7 and in `033-DL`, despite carrying an R1-11 note.
  Added to all three.
* **P2-11 (resolved):** `033-DL`'s post-terminal amendment did not record what
  authorized a `done` artifact to be amended. It now states that the amendment was
  gated by the third hardening pass (R1-11) and plan-review cycle 3, and its `done`
  status is preserved.
* **P3-6 (accepted, tracked as residual risk - stash `904C47BC`):** the checkpoint
  payload contract conflict remains **active and undispositioned**, `requires
  deliberation: yes` unmet. Carried forward unchanged. No tool-owned historical
  checkpoint payload was edited, quarantined, or repaired by this cycle, and
  `checkpoint-20260908-195611.json` (Ship-owned) was not touched.
* **P3-7 (accepted):** the local uncommitted `.gitignore` addition of
  `.backlogit/logs/` is left exactly as found. Whether to commit it is an operator
  question that this plan neither answers nor depends on.

### Gate decision

**PASS** - zero P0, zero unresolved P1. Cycle 4, run under explicit operator
authorization extending the 3-cycle budget for same-contract findings only. Every
finding raised in this cycle passed the P-021 C1 same-contract-surface test and was
fixed rather than deferred; no `DEFERRED SCOPE EXPANSION` capture was required.
`904C47BC` is pre-existing, separately captured, and carried as residual risk - not a
deferral created by this cycle.
