---
title: "shipment-reconcile Step 0(c): replace the self-reported pre-mutation timestamp with an engine-anchored append-only ordering proof"
description: "Stage deliberation resolving stash DDBF283E (the Step 0(c) pre-existence proof is forgeable by a post-hoc reconstruction that backdates collection_completed_at) and stash EB23D1B9 (that redesign prerequisite is not encoded in 171-S's claim-eligibility graph). Decides the anchor mechanism, the containment boundary, and the blocker encoding."
date: 2026-09-10
status: decided
decided_by: "Stage (session 8964a988), under operator authorization 2026-09-10"
stash_entries:
  - "DDBF283E — Step 0(c) evidence-mechanism redesign (REQUIRES DELIBERATION: yes). Source: PR 437 HEAD e78e3f00e6f3303ae2c070a2d8a5a8434736fa49, Copilot round-1 review, thread PRRT_kwDORzpWpM6gdwXD; feature 151-F; shipment N/A; task N/A."
  - "EB23D1B9 — encode the DDBF283E prerequisite as a real blocking predecessor in 171-S's dependency graph (REQUIRES DELIBERATION: yes). Source: PR 437 HEAD 42783ce42c8dfd352662fe44d2c12eb325340968, Copilot round-4 review, thread PRRT_kwDORzpWpM6ge79q; feature 151-F; shipment N/A; task N/A."
revises:
  - "docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md (U1a, U1b, U1c, U2, U3)"
  - "163.001-T, 163.002-T, 163.003-T, 163.004-T, 163.005-T (feature 163-F, shipment 171-S)"
supersedes_mechanism_in:
  - "docs/decisions/2026-09-07-step-0c-pre-mutation-guard-reconstruction-disposition.md — the Option A remediation REQUIREMENTS (RQ-1/RQ-2/RQ-3) are unchanged and remain binding; only the MECHANISM by which RQ-2's 'provably pre-mutation' is satisfied is redesigned here."
compound_learnings:
  - "docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md — validate protocols as a composed state machine over the tool lifecycle they sit on"
  - "docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md — the engine's item log is an independent record of what the engine actually did"
  - "docs/compound/2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md"
  - "docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md"
  - "docs/compound/2026-09-07-copilot-review-finding-pattern-taxonomy.md"
policies:
  - "P-005 — process deviation must halt, not degrade"
  - "P-015 — shipment safe-close / cascade contract"
  - "P-021 — deferred scope expansion capture and disposition"
tags: [decision, deliberation, shipment-reconcile, pre-mutation-gate, tamper-evidence, fail-closed-design, p-005, p-015, p-021]
---

# Step 0(c) evidence-anchor mechanism redesign

## Problem Frame

The reviewed plan
`docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md`
(U2, harvested as task `163.004-T` under feature `163-F` / shipment `171-S`) makes
live execution of the Step 0(c) linked-deliberation collection *provable* by
requiring a durable evidence record written before the P-015 cascade invocation, and
by failing closed when that record is absent or "not provably pre-mutation".

**The finding (DDBF283E).** The record's pre-existence is proved by fields the
*agent itself writes into the record through the ordinary protocol surface*:

| Field | Written by | Forgeable after the mutation? |
|---|---|---|
| `collection_completed_at` | the agent | **Yes** — a post-hoc reconstruction writes any timestamp it likes |
| git `HEAD` SHA at collection time | the agent | **Yes** — the pre-close SHA is still readable afterwards |
| manifest item list | the agent | **Yes** — preserved in the archived manifest |
| validated linked-deliberation ID set | the agent | **Yes** — that is precisely what 159-S reconstructed |

A byte-identical post-hoc reconstruction that backdates `collection_completed_at`
satisfies every clause of the check. The gate therefore re-creates, one level up,
the exact defect it exists to close: it still cannot distinguish history A (scan ran
at `T0`, cascade at `T1 > T0`) from history B (cascade at `T1`, scan reconstructed at
`T2 > T1`). The plan's own anti-reconstruction clause states the right *rule* — "the
check is on the record's **pre-existence**, never on its **reproducibility**" — but
the mechanism supplies no evidence of pre-existence that is independent of the party
whose compliance is being checked.

This is the composed-state-machine failure mode again, in its dual form. `15A02E21`
was a gate no legitimate state could *satisfy*; this is a gate no illegitimate state
can *fail*.

**The second finding (EB23D1B9).** Shipment `171-S` declares exactly one dependency,
`blocks 169-S`. Once `169-S` ships, normal claim-eligibility logic makes `171-S`
immediately claimable — even though its core acceptance criteria were already known,
via DDBF283E, to require this redesign first. The prerequisite existed only as prose
in a stash entry, which the eligibility graph does not read.

## Threat Model (stated explicitly, because the honest scope of the fix depends on it)

The adversary is **not** a malicious operator with shell access. Against that
adversary no purely local mechanism is sound: anything on disk can be rewritten.
Chasing tamper-*proofness* here would buy nothing and would justify an unbounded
amount of machinery.

The actual threat is the **159-S failure mode**: a good-faith agent that did not run
the step at the required time, and then reconstructs equivalent-looking evidence
afterwards, sincerely believing content equality is what the contract asks for. That
agent follows the protocol surface it is given.

The design target is therefore:

> Make the reconstruction path **unreachable through the agent's normal tool
> surface**, so that forging the proof requires a deliberate, out-of-protocol act
> that is itself independently detectable and is itself a P-005 violation.

Tamper-**evident** and out-of-protocol, not tamper-**proof**. Any claim stronger than
this would be dishonest, and this document explicitly declines to make one.

## Options Considered

### O1 — Status quo: keep `collection_completed_at` as the ordering proof

**Rejected.** The finding is valid. The one field that carries the entire
pre-existence claim is written by the checked party through the ordinary protocol
surface, with no other party involved at any point.

### O2 — External trusted timestamp (RFC 3161 TSA, or a public notary/transparency log)

**Rejected.** Genuinely unforgeable, and genuinely wrong here. It injects a hard
network dependency into a *fail-closed* irreversible close path: with the gate
failing closed, an offline or rate-limited operator could no longer close any
shipment. That converts an integrity control into an availability outage, and the
harness is explicitly a locally-operating tool. Disproportionate to the threat model.

### O3 — Git-commit ancestry anchor

Commit the evidence record before the cascade; afterwards prove
`git merge-base --is-ancestor <evidence-commit> <close-commit>`. The DAG is
genuinely monotonic and ancestry cannot be forged by backdating (commit *dates* are
forgeable; commit *ancestry* is not).

**Rejected as the primary mechanism, adopted as an optional corroborating one.** It
requires the close path to produce a commit at a specific mid-close moment, which
Ship's close path does not currently guarantee and which is undesirable to mandate
(closes legitimately occur on branches where an extra commit is unwanted). Making
the gate depend on it would make the gate unsatisfiable in legitimate states — the
`15A02E21` mistake. Recorded as an OPTIONAL strengthening field, never a
pass condition.

### O4 — Engine-written append-only event-log anchor **(CHOSEN)**

Step 0(c) appends an evidence-anchor event to the shipment's own backlogit item log
`.backlogit/logs/{shipment_id}.jsonl` through backlogit's append operation. The
decisive property is **who writes what**:

* the **agent** supplies only the comment payload (a digest and a short descriptor);
* the **engine** writes the `timestamp`, the `actor`, the `event_type`, and — the
  part that matters — **appends the line at end-of-file**.

The P-015 cascade mutation subsequently appends its own engine-written events to
**the same file**: `shipment_status_changed`, `commit_tracked`, and finally
`archived`. Ordering is then proved by **relative append position in a file the
engine owns**, corroborated by engine-written timestamps — not by any value the
agent authored.

**Verified against live data (2026-09-10), not assumed:**

* Engine authorship and event vocabulary confirmed by direct inspection of
  `.backlogit/logs/150-S.jsonl`, `151-S.jsonl`, `152-S.jsonl`: every lifecycle event
  carries `"actor":"backlogit"`, ending in `archived`.
* `comment` events land in the same log with engine-written timestamps
  (`005-F.jsonl`, `005-S.jsonl`, `011-DL.jsonl`).
* **The proof artifact survives the mutation it proves.** Shipped shipments retain
  their logs with `archived` as the final line, so the anchor remains readable and
  auditable after the close. A proof that vanished with the archival would be
  useless.
* **The negative case is directly observable in the real failure.**
  `.backlogit/logs/159-S.jsonl` contains nine engine events and **no** evidence
  anchor anywhere before `archived`. The 159-S history the plan exists to reject is
  visibly, mechanically distinguishable under this mechanism — and was not
  distinguishable under `collection_completed_at`.

To forge this anchor, an agent must hand-edit an engine-owned append-only JSONL and
splice a line into the middle of it. That is not reachable through any tool the
agent is given; it is an out-of-protocol act, and it is exactly the boundary P-005
draws. Under O1 the same forgery required nothing but writing a different string
into a file the agent was already authoring.

**Digest binding (closes the residual seam).** An anchor alone would permit "append
a generic anchor early, fabricate the record afterwards." The anchor payload
therefore carries the **SHA-256 of the evidence record's bytes**, and the check
recomputes that digest from the record on disk and requires equality. The anchor and
the record are thereby bound to each other, and both to a moment the engine
witnessed.

**No Python source change**, preserving the plan's existing Non-Goal: this uses
backlogit's already-published append operation from the skill's own protocol, at a
surface the skill already owns.

### O5 — Skill-maintained hash chain / Merkle log over reconcile records

**Rejected.** The agent would own the chain, so it is self-reported at one remove:
an agent that can reconstruct a record can equally recompute the chain over it. It
adds a new persistent structure, a new corruption-and-recovery failure mode, and a
new thing to keep in dogfood parity, in exchange for no additional trust.

## Chosen Direction

**Adopt O4 (engine-anchored append-only ordering proof, with digest binding), with
O3 as an optional corroborating field. Retain `collection_completed_at` as
corroborating metadata only — explicitly demoted from authoritative.**

### D-1 — The authoritative ordering proof is the engine-written anchor event

Step 0(c), on the CASCADE path, inside the existing single-writer lock and before
the Cascade Close Sub-Procedure's step 1 invocation:

1. writes the evidence record at
   `.backlogit/reconcile/{shipment_id}-precascade-snapshot-{timestamp}.md`
   (contents unchanged from the reviewed plan's U2(a) items 1–6);
2. computes `sha256` over that record's bytes;
3. appends an anchor event to `.backlogit/logs/{shipment_id}.jsonl` via backlogit's
   append operation, with a payload carrying the literal token
   `PRECASCADE_EVIDENCE_ANCHOR`, the `shipment_id`, the record's relative path, and
   its `sha256`.

`collection_completed_at` remains in the record — it is useful corroboration and a
useful human-readable field — but the contract must state, in one sentence, that it
is **not** the ordering proof and that agreement between it and the anchor is not
required for PASS.

### D-2 — Four separately labelled, independently failing halt tokens

The plan's existing rule (never merge independently failing conditions into one
test — the documented root cause of `B57F9E24`) applies. The four genuinely distinct
failure modes are kept distinct, because collapsing them destroys the diagnostic
that this whole shipment exists to produce — "you never ran Step 0(c)" must not be
reported identically to "you reconstructed it afterwards":

| Token | Fires when |
|---|---|
| `RECONCILE_FAIL_PRECASCADE_EVIDENCE_MISSING` | no evidence record exists for this `shipment_id` |
| `RECONCILE_FAIL_PRECASCADE_EVIDENCE_STALE` | a record exists but does not describe the state being closed: `HEAD` SHA or manifest item list mismatch, or `collection_completed_at` absent |
| `RECONCILE_FAIL_PRECASCADE_ANCHOR_MISSING` | no `PRECASCADE_EVIDENCE_ANCHOR` event for this `shipment_id` in the engine log, **or** its `sha256` does not match the record on disk |
| `RECONCILE_FAIL_PRECASCADE_ANCHOR_NOT_PRE_MUTATION` | the anchor event exists but does not precede the earliest engine-written mutation event for this shipment in append order |

All four emit a P-005 violation and halt. None authorizes a fallback to safe-close.
The two pre-existing tokens keep their names and their semantics is *narrowed*, not
redefined; the two new tokens are additive.

### D-3 — The negative test DDBF283E asks for

Added to the scenario matrix and to the replay assertions:

> **Backdated reconstruction.** An evidence record exists whose
> `collection_completed_at` is strictly *before* the cascade invocation and whose
> `HEAD` SHA and manifest list both match the closed state — i.e. a perfect forgery
> under the O1 mechanism — but whose anchor event is absent from the engine log, or
> appears *after* the mutation events. This MUST be **rejected**, and rejected with
> `..._ANCHOR_MISSING` / `..._ANCHOR_NOT_PRE_MUTATION`, **never** with
> `..._EVIDENCE_STALE`.

The token asserted matters as much as the rejection: it is what proves the ordering
proof, and not a content comparison, is doing the work. This is the direct executable
counterpart of the anti-reconstruction clause, and it is the assertion that would
have failed against the mechanism as originally planned.

The legitimate passing state is restated so the gate is provably satisfiable (lesson
6, and the `15A02E21` unreachable-gate lesson): record present with
`scan_performed: true` and `linked_deliberation_ids: []` (the 159-S *shape*), anchor
event present, anchor digest matching, anchor preceding all mutation events ⇒ PASS.

### D-4 — Containment: revise `171-S` in place; do NOT create a predecessor shipment

Both were evaluated seriously. **Revision in place is chosen**, for one decisive
reason and two supporting ones:

* **Decisive — region contention.** A predecessor shipment implementing the anchor
  would edit *the same paragraphs* of
  `.github/skills/shipment-reconcile/SKILL.md` Step 0(c) that `171-S`'s U2 edits.
  That shipment would write the anchor contract and `171-S` would then rewrite it.
  `171-S` already contends with `169-S` for the surrounding Step 0 region; adding a
  third contender for the identical paragraphs multiplies conflict risk and creates
  exactly the two-independent-restatements-drift condition that *produced* `15A02E21`.
  Splitting here would import the defect class this feature exists to remove.
* The redesign is a **design decision, not a work product**. Once decided (this
  document), nothing remains to "implement separately" — it changes `171-S`'s
  acceptance criteria. A predecessor shipment would have an empty implementation
  surface of its own.
* The unit structure, file set, task count, and paired-edit shape are all
  **unchanged**. This is a substitution inside U2's existing (a)/(b), plus assertion
  and scenario additions — not new units.

**The revision is not silently absorbed.** `171-S` is a sealed, plan-reviewed
decomposition, so the revised plan re-enters the full gate: plan hardening (already
`requires_plan_hardening: yes`, and this change is gate-shaped on an irreversible
path, so the signal is only reinforced) followed by `plan-review`. `171-S`'s scope
boundary is preserved: no new files, no Python source change, no change to `169-S` /
`161-F` or `170-S` / `162-F` scope, no re-opening of the 856B6770 disposition, and no
retroactive-compliance claim for 159-S.

### D-5 — 2-hour rule and the two-axis gate

| Task | Size | Complexity | Change |
|---|---|---|---|
| `163.001-T` U1a fixture | S → **M** | medium | fixture must model engine-log append order, not just file presence |
| `163.002-T` U1b assertions | S → **M** | medium | adds the backdated-reconstruction rejection family and token-identity assertions |
| `163.003-T` U1c guards | S | medium | guard additionally asserts the anchor clause and demotion sentence, same section-scoped technique |
| `163.004-T` U2 atomic core | **M** | medium → **high** | anchor emission + digest binding + four tokens, still a paired prose edit to two files |
| `163.005-T` U3 scenario matrix | S | low | two additional scenario rows |
| `163.006-T`, `163.007-T` | unchanged | unchanged | unchanged |

Every task remains within the 2-hour rule; `M` is "several files or functions, a few
test scenarios" and `163.004-T` remains a bounded paired edit across exactly two
files. **No size crosses the 2-hour threshold, so no split is forced on the size
axis.**

`163.004-T` rises to `complexity: high`, which under the Stage two-axis gate forces a
split **or a de-risking step**. It is explicitly **not** split: the task is declared
`DO NOT SPLIT` / INDIVISIBLE, and the plan's indivisibility argument survives the
redesign intact and is in fact strengthened — the anchor *is* the record's proof, so
emission and check are more tightly bound than before, and shipping either half alone
still yields either an artifact nobody consults or an unsatisfiable gate. The
de-risking taken instead, as the gate permits:

1. **this deliberation**, which fixes the mechanism before implementation;
2. **RED-first ordering** — `163.001-T`/`163.002-T`/`163.003-T` land the anchor
   semantics as executable, failing assertions *before* `163.004-T` edits any
   contract text, so the atomic core is written against a specification that already
   exists in code;
3. **a fresh plan-review gate** over the revised plan.

### D-6 — EB23D1B9: encode the prerequisite as a real graph edge

The prerequisite is encoded with **real backlogit dependency operations over a real
artifact type**. No `blocked` shipment lifecycle is invented, and no dependency is
declared on a shipment that does not exist:

* the redesign is recorded as a first-class backlogit **deliberation** artifact
  (`-DL`, an existing configured type with established precedent in this workspace);
* `171-S` gains a second `blocks` dependency on that deliberation artifact, so the
  prerequisite is visible to the same claim-eligibility logic EB23D1B9 cited, rather
  than living only as prose in a stash entry;
* that edge is satisfied **only** when the deliberation artifact reaches a terminal
  state, which happens only after the revised plan passes `plan-review`.

`171-S` therefore remains unclaimable until the revision gate is genuinely complete,
by the ordinary dependency mechanism and not by a special case. The edge is retained
after satisfaction as a permanent audit record that `171-S`'s contract was gated on,
and corrected by, this redesign.

## Open Questions

* **Anchor event vocabulary.** The anchor is carried as a `comment` event with a
  literal `PRECASCADE_EVIDENCE_ANCHOR` token in its payload, because that uses only
  backlogit's already-published append operation and requires no engine change. A
  dedicated engine-side event type would be cleaner and strictly stronger (the agent
  could not author the event type at all). That is a **backlogit feature request,
  not a blocker**, and is deliberately out of scope here; the token-in-comment form
  is sufficient under the stated threat model. Not captured as a stash entry by this
  session — recorded here as the canonical statement of the follow-up.
* **Cross-tool durability.** The proof depends on backlogit continuing to retain item
  logs after archival. That is true today and verified above, but it is a property of
  a third-party tool, not of this harness — precisely the composed-state-machine
  seam. `163.003-T`'s guard asserts the *contract text*; nothing asserts the *engine
  behaviour*. A future regression in backlogit's log retention would silently weaken
  this gate.
* **169-S interaction.** Unchanged from the original plan: sequencing only, never
  merging. `171-S` continues to `blocks`-depend on `169-S`, and U2 is still authored
  against post-169-S text.
