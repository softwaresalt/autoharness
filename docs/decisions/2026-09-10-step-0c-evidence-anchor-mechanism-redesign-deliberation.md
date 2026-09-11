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
  - "docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md (U1a, U1b, U1c, U2, U3; and via R1-12: U4, new U6)"
  - "163.001-T, 163.002-T, 163.003-T, 163.004-T, 163.005-T (feature 163-F, shipment 171-S); and via D-7/D-8: 163.006-T, 163.007-T, new 163.008-T"
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
* **The proof artifact survives the mutation it proves — on the local filesystem.**
  Shipped shipments retain their logs with `archived` as the final line, so the
  anchor remains readable and auditable **to a reader working in the closing
  workspace** after the close. A proof that vanished with the archival would be
  useless. **This bullet establishes local durability only** — it says nothing about
  whether the log reaches the repository. Whether a fresh-clone reviewer can see it
  depends on that path's **tracking state**, not on an assumed blanket ignore rule;
  see **D-7** (as premise-corrected in review-fix cycle 2) and plan section **R1-12**
  for the Case A/B/C publication contract and the executor assigned in **D-8**.
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

> **Decision-label namespacing (review-fix cycle 2).** These `D-n` labels are **this
> deliberation's**. The plan
> (`docs/plans/2026-09-08-shipment-reconcile-step-0c-live-pre-mutation-evidence-plan.md`)
> has its own, unrelated `D-1..D-8` sequence. Cite them qualified — **`redesign
> decision D-n`** for this file, **`plan D-n`** for the plan. Bare `D-n` is ambiguous
> and must not be used. Live collisions: **redesign decision D-5** (this section,
> sizing) vs. **plan D-5** (state the requirement once); **redesign decision D-7**
> (durability split) vs. **plan D-7** (no Python source change).

**Sizing table — corrected 2026-09-10 (review-fix cycle 2).** The `163.006-T` /
`163.007-T` "unchanged" row had gone stale: plan-review cycle 3 re-sized `163.006-T`
`XS`→`S` and `trivial`→`low`, and the record already carried those values while this
table still said "unchanged". Each task now has its own row, and `163.008-T` is added.

| Task | Size | Complexity | Change |
|---|---|---|---|
| `163.001-T` U1a fixture | S → **M** | medium | fixture must model engine-log append order, not just file presence; R1-13 adds the `LATE_BUT_ANCHORED` positive variant (one further variant inside a set this task already builds — **no size change**) |
| `163.002-T` U1b assertions | S → **M** | medium | adds the backdated-reconstruction rejection family and token-identity assertions; R1-12 also removes the superseded `collection_completed_at` timestamp comparison from its ordering family (a **deletion**, so no size pressure); R1-13 adds one acceptance assertion over the `LATE_BUT_ANCHORED` variant (**no size change**) |
| `163.003-T` U1c guards | S → **M** | medium | **re-confirmed and re-sized (review-fix cycle 2).** `S` was correct for the R1 assertion set. It is no longer: the guard now additionally asserts the R1-11 L1/L2 split sentence, the negative no-fifth-`PRECASCADE`-token assertion, and the R1-12 U6 publication step with its non-`PRECASCADE` condition name — three additional section-scoped assertion groups across two files. `M` reflects the accumulated set. Complexity stays `medium`: the technique is unchanged, only the surface grew |
| `163.004-T` U2 atomic core | **M** | medium → **high** | anchor emission + digest binding + four tokens, still a paired prose edit to two files |
| `163.005-T` U3 scenario matrix | S | low | two additional scenario rows |
| `163.006-T` U4 diagram | XS → **S** | trivial → **low** | **corrected (review-fix cycle 2); this table previously said "unchanged", which contradicted the record and cycle 3's own finding.** The unit grew from two halt tokens to four, gained the anchor node and the L1/L2 split, and R1-12 added the resolve-canonical-path rule |
| `163.007-T` U5 checksums | XS | low | unchanged in scope; gains one dependency edge (on `163.008-T`) so it still runs last |
| `163.008-T` U6 L2 publication step | **S** | **medium** | **new (review-fix cycle 2, plan D-8).** Paired prose edit to the same two files U2 edits: Case A/B/C detection, staging, five verification criteria, reconcile-report outcome, and the `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE` report. `medium` because the conditional detection and the commit-content assertions require care, not because the surface is large. **Review-fix cycle 3 (R1-13)** corrects its fidelity criterion to the append-only prefix rule, separates its two roles, and adds the remediation path — all clarifications to text this task already writes, so **no size change** |

Every task remains within the 2-hour rule; `M` is "several files or functions, a few
test scenarios" and `163.004-T` remains a bounded paired edit across exactly two
files. **No size crosses the 2-hour threshold, so no split is forced on the size
axis.** Task count is **8** after `163.008-T` (7 before).

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
  (`033-DL`, an existing configured type with established precedent in this
  workspace);
* the blocking edge is declared at the **feature and task level**, where the gated
  work actually lives: `163-F` `blocks`-depends on `033-DL`, as do the five revised
  tasks `163.001-T`, `163.002-T`, `163.003-T`, `163.004-T` and `163.005-T`;
* that edge is satisfied **only** when the deliberation artifact reaches a terminal
  state, which happens only after the revised plan passes `plan-review`.

**Correction (2026-09-10, review-fix cycle 1).** An earlier draft of this decision
stated that `171-S` would "gain a second `blocks` dependency on that deliberation
artifact". That is **not what was implemented, and it is not implementable**:
backlogit shipment claim-eligibility evaluates **shipment predecessors only**, so a
shipment→deliberation edge was correctly rejected by the tool rather than silently
accepted. Recording one anyway would have created a permanently unsatisfiable
shipment edge — the `15A02E21` mistake in a new place. The prerequisite is therefore
gated at feature/task level, which is where it binds: `171-S` cannot be worked
through to completion while `163-F` and its tasks are blocked, and `171-S`'s own
shipment-level eligibility continues to declare exactly one dependency,
`blocks 169-S`.

**Current state.** `033-DL` reached `status: done` on 2026-09-10, so the feature- and
task-level gate is **satisfied**. `171-S` nonetheless remains **queued and not
claimable**, because its shipment-level predecessor `169-S` is still unshipped. The
`033-DL` edges are retained after satisfaction as a permanent audit record that
`171-S`'s contract was gated on, and corrected by, this redesign.

### D-7 — Durability split: local runtime ordering proof vs. repository audit evidence

> **RELOCATED 2026-09-10 (review-fix cycle 2).** D-7 was filed under "Open
> Questions", which mis-stated its status: it is a **decided** correction that was
> propagated into the plan and into six backlog records, not an unresolved question.
> It now sits under **Chosen Direction** alongside D-1..D-6 and D-8. The genuinely
> open items remain in the "Open Questions" section further below.

**Added 2026-09-10 (review-fix cycle 1), correcting an overstatement in O4 and D-1.**
Those sections described the anchor as "durable" and "auditable" without naming the
audience. That was true of the closing workspace and did not, by itself, establish
that the evidence reaches the repository. The decision is corrected, not retracted —
the mechanism is right; the durability claim was scoped wrong.

> **PREMISE CORRECTED 2026-09-10 (review-fix cycle 2).** As first written, this
> section justified the split with the claim that "`.backlogit/logs/` is
> `.gitignore`d, so a reviewer with a fresh clone could see neither the anchor nor the
> append order". Direct inspection refutes the categorical form of that claim:
> `origin/main`'s `.gitignore` carries **no** `.backlogit/logs/` rule; `git ls-files`
> shows **993 of 1016** local logs already tracked, including `150-S`, `159-S`,
> `169-S` and `171-S` itself; the `.backlogit/logs/` ignore rule exists only as an
> **uncommitted** working-tree edit; and a `.gitignore` rule never hides an
> already-tracked path. The L1/L2 **conclusion** survives — publication to the
> repository is still a separate concern from local retention, and still deserves to
> be named separately — but the **mechanism** is now conditional on the path's actual
> tracking state (plan section R1-12, Cases A/B/C) rather than on an assumed blanket
> ignore rule.

Two layers, separately named, neither substitutable for the other:

* **L1 — local runtime ordering proof (gate-bearing).** The
  `PRECASCADE_EVIDENCE_ANCHOR` event in `.backlogit/logs/{shipment_id}.jsonl`,
  written by the engine, read inside the existing lock before the cascade
  invocation. **All four D-2 halt tokens evaluate L1 and only L1.** Unchanged by
  this correction.
* **L2 — repository audit evidence (never gate-bearing).** At the closure commit,
  that **one** shipment's engine log is published into the repository **verbatim and
  byte-unmodified**, beside the already-tracked evidence record under
  `.backlogit/reconcile/`. The staging action follows the path's tracking state
  (plan R1-12): an ordinary commit of its mutation when the path is **already
  tracked** — the actual state of `171-S` — an ordinary `git add` when it is
  untracked and not ignored, and a `git add -f` bounded to that one log when it is
  untracked and ignored. The **durable postcondition is identical in all three
  cases**: the engine-authored bytes L1 evaluated are present in the closure commit.
  Bounded to one shipment at its own closure; not a general un-ignoring of
  `.backlogit/logs/`, not a historical backfill, and not a `.gitignore` change —
  boundedness is asserted against the closure commit's own contents (at most one
  newly-tracked `.backlogit/logs/` path, no `.gitignore` modification), so it holds
  without consulting any ignore rule.

> **FIDELITY CRITERION CORRECTED 2026-09-10 (review-fix cycle 3; plan section R1-13(a)).**
> "Verbatim and byte-unmodified" above means **no pre-existing byte is modified, deleted,
> truncated or reordered** — it does **not** mean the committed blob equals the file the
> gate read, and plan R1-12's original "byte-identical to the engine log the gate read"
> criterion is superseded. The engine appends the cascade's own
> `shipment_status_changed` / `commit_tracked` / `archived` events to the same log
> **after** L1's read and **before** the closure commit (directly observable in
> `.backlogit/logs/150-S.jsonl`), so a byte-identical requirement would fail every
> legitimate close. The satisfiable rule is the **append-only prefix rule**: the exact
> `PRECASCADE_EVIDENCE_ANCHOR` line and all pre-cascade bytes L1 evaluated appear
> byte-unmodified, in unchanged relative order, as the prefix — or a provably unchanged
> ordered leading segment — of the committed log; engine-written post-gate mutation lines
> are **expected** append-only extensions and never a fidelity failure; any modification,
> deletion, truncation or reordering of pre-existing bytes **is** a failure. The separate
> criterion that the mutation lines **follow** the anchor in the committed bytes is
> preserved and is **not** merged into this one.

**Why the engine's own bytes and not an agent-written export.** A transcription or
summary would reintroduce precisely the defect this deliberation exists to remove —
evidence authored by the party whose compliance is being checked. Staging is an
action over bytes the agent did not write; it cannot alter append order, and any
alteration is a content change visible in the diff. A fresh-clone reviewer can then
(1) recompute the record's `sha256` and compare it to the anchor's, (2) confirm
the anchor precedes the engine-written mutation lines **in append order**, and (3)
confirm the record's `HEAD` SHA and manifest describe the closed state — none of
which consults an agent-authored timestamp.

**Fail-closed is preserved and placed where it can act.** L2 is written after a
mutation the gate already permitted, so it cannot be a pre-cascade token; adding a
fifth token for it was considered and **rejected** as an unsatisfiable gate on an
artifact that cannot yet exist. Instead, **operational closure is incomplete until L2
is committed** — a reportable P-001 condition. Missing L2 never authorizes a close,
never downgrades a halt, and is never a fallback for a failed L1 check.

> **EXECUTOR ASSIGNED 2026-09-10 (review-fix cycle 2) — see D-8.** As first written,
> this paragraph attached P-001 incomplete-closure semantics to L2 without naming any
> implementation surface that could perform or verify it, leaving a normative
> obligation with no executor. D-8 assigns one: **Ship, at operational closure**, via
> the Post-Cascade Publication step added by plan unit **U6** and harvested as task
> **`163.008-T`**, reporting `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE`.

**Also rejected:** un-ignoring `.backlogit/logs/` wholesale, or making any
`.gitignore` change at all (unbounded repository growth, plus a dependency on
working-tree state this decision does not own).

Propagated to the plan as **R1-11** (corrected by **R1-12**, and further corrected and
completed by **R1-13**), and to `163-F`, `163.001-T`, `163.002-T`, `163.003-T`,
`163.004-T`, `163.005-T`, `163.006-T`, **`163.007-T`** and the new `163.008-T`, and
recorded in `033-DL`. (`163.001-T` and `163.002-T` carry the R1-12 timestamp-ordering
supersession and the R1-13 `LATE_BUT_ANCHORED` fixture variant and its assertion; they
were absent from this list before review-fix cycle 3.)

### D-8 — The L2 obligation keeps its normative force and gains an executor

**Decided 2026-09-10 (review-fix cycle 2).** D-7 left L2 as a normative P-001
obligation that nothing implemented, performed, or verified. Only two resolutions were
honest:

1. **Give it an owner** — keep the P-001 and fail-closed language and name a real
   implementation surface; or
2. **Make it advisory** — strip every P-001 and fail-closed claim from it and say
   plainly that nothing enforces it.

**Option 1 is chosen.** Option 2 would have reopened the exact fresh-clone
auditability gap the authorized redesign exists to close: with L2 advisory, a close
could be published with no repository-visible ordering proof and no reportable
condition, leaving the only surviving evidence the agent-authored
`collection_completed_at` that D-1 demotes. Softening the obligation to avoid an
ownership question would have been a scope retreat dressed as simplification.

**The assignment:**

| Aspect | Value |
|---|---|
| **Owner — Role 1 (implementer)** | Ship, executing task `163.008-T` in `171-S` as an ordinary build-pipeline task: it writes the Post-Cascade Publication **contract text** into the two paired files. This is a normal RED→GREEN build step, not a close (clarified review-fix cycle 3, plan R1-13(c)) |
| **Owner — Role 2 (runtime actor)** | The closing agent executing the `shipment-reconcile` cascade path at a **future** close — **Ship, at operational closure**. Never Stage, which does not close shipments. "Never Stage" attaches to this role only |
| **Implementation unit** | **U6** — a paired prose edit to the same two files U2 edits (`.github/skills/shipment-reconcile/SKILL.md` and `templates/skills/shipment-reconcile/SKILL.md.tmpl`). No new file, no Python source change, no `.gitignore` change |
| **Backlog item** | **`163.008-T`**, parent `163-F`, member of `171-S`, depends on `163.004-T` (U2 states the obligation) and blocks `163.007-T` (U5 consumes its bytes) |
| **Behaviour** | Detect the tracking case (A/B/C), stage accordingly, verify the five R1-12 criteria against the closure commit — with fidelity evaluated under the **append-only prefix rule** of R1-13(a), never as a byte-identical comparison — and record the outcome and detected case in the reconcile report |
| **Reportable condition** | `RECONCILE_CLOSURE_INCOMPLETE_L2_EVIDENCE` — a **P-001 incomplete-closure report**, not a halt token. Named outside the `RECONCILE_FAIL_PRECASCADE_` namespace so `163.003-T`'s "no fifth `PRECASCADE` token" negative assertion keeps firing on a genuine regression |
| **Remediation when evidence is missing** (added review-fix cycle 3, plan R1-13(d)) | Closure stays **INCOMPLETE**; publish the exact engine log in a **follow-up closure commit** satisfying the same criteria **before** P-001 release-unit completion; **never** amend, rewrite or force-push published history to insert it; **never** mark closure done while it is missing; and if the log cannot be produced at all, report the unremediable gap with its reason rather than substituting an agent-authored transcription |
| **What it never does** | Never authorizes a close, never downgrades or re-runs the L1 gate, never acts as a fallback for a failed L1 check, never blocks the cascade |

The pre-cascade gate surface stays at exactly the **four** D-2 tokens. U6 runs outside
and after the single-writer lock window, so it adds no lock, no second writer, and no
new failure window.

## Open Questions

### Remaining open questions

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
  this gate. **D-7's L2 obligation partially mitigates this after the fact** — once a
  shipment's log is committed at closure, a later engine-side retention regression
  cannot remove the already-published audit evidence — and **D-8 gives that
  mitigation an executor (U6 / `163.008-T`)**, so it is a step someone performs and
  verifies rather than an aspiration. It still does **not** protect a close that has
  not happened yet, so the open question stands for L1.
* **The workspace `.gitignore` addition of `.backlogit/logs/`** is uncommitted
  working-tree state. Whether to commit it is an operator question. It is **not** a
  prerequisite for anything here: after the R1-12 correction, this decision and the
  plan read no ignore rule and change none, and the L2 postcondition is identical in
  all three tracking cases.
* **169-S interaction.** Unchanged from the original plan: sequencing only, never
  merging. `171-S` continues to `blocks`-depend on `169-S`, and U2 is still authored
  against post-169-S text.
