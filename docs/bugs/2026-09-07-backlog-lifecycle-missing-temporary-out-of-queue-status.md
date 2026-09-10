---
title: "Backlog lifecycle has no explicit temporary out-of-queue status, so `archived` is silently overloaded to mean both \"terminal\" and \"set aside, may return\""
description: "backlogit's work-item status vocabulary offers no state meaning 'deliberately taken out of the queue but expected to return'. `blocked` stays in the queue; `archived` routes to the archive but is defined as terminal and has no first-class return path. Operators must therefore encode 'parked' in `archived` and recover the distinction from surrounding context — tacit knowledge that will be lost."
status: "open — requires deliberation; name not yet chosen"
severity: "medium"
priority: "high"
kind: "bug"
defect_class: "contract gap / lifecycle-vocabulary gap"
date: 2026-09-07
raised_by: "operator"
operator_requirement_verbatim: "We also need a status of `parked` or `hold` for items that are taken out of the queue but may be brought back to the queue later, whereas `archived` clearly indicates that the item is done or will not be done. In general, statuses should have explicit meanings rather than rely on tacit contextual interpretation that could vanish."
requires_deliberation: true
stash_entry: "4D3826FE"
name_decided: false
recommended_name: "parked (Stage recommendation with rationale — NOT an operator decision)"
affected_tools:
  - "backlogit (EXTERNAL, separate repository/owner) — status enum, directory routing, transition validation, return-path operation"
  - "autoharness (LOCAL) — backlog-tool-registry schema `status_values`, `.autoharness/backlog-registry.yaml`, gates, skills, agent templates"
change_surface: "BOTH — an upstream backlogit tool/schema change AND a local autoharness protocol/template change. Neither alone is sufficient."
governing_policies: ["P-015", "P-021"]
related_but_distinct:
  - "docs/bugs/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-mismatch.md (stash 15A02E21) — shares the explicit-status-semantics principle and is the downstream consumer of any new status via its member-class matrix, but is a DIFFERENT defect with a DIFFERENT fix in a DIFFERENT tool. MUST NOT be merged into that fix's shipment."
  - "docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md (stash 7F93FA0C) — same defect class (composed-contract failure), different surface."
decision_artifact: "docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md (records this as related-but-distinct; see refinement R-5)"
compound_learning: "docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md (lesson 8 — lifecycle states must be self-describing)"
tags:
  - "bug"
  - "contract-gap"
  - "backlog-lifecycle"
  - "status-semantics"
  - "cross-tool-integration"
  - "backlogit"
  - "requires-deliberation"
---

## Summary

The operator requires a lifecycle status meaning **"deliberately taken out of the queue, may be
brought back later."** No such status exists in either tool.

Today the only two ways to stop an item appearing as active queue work are:

* set it `blocked` — but `blocked` **routes to `queue/`**, so the item is *not* out of the queue,
  and `blocked` already means "involuntarily impeded", not "deliberately set aside"; or
* set it `archived` — which *does* remove it from the queue, but is **defined as terminal** and has
  **no first-class return path**.

So an operator who parks an item must overload `archived`, and the fact that *this particular*
archived item is expected to return survives only as tacit context — in a comment, in a memory
file, or in someone's head. That is precisely the failure mode the operator's second sentence
names: *"statuses should have explicit meanings rather than rely on tacit contextual interpretation
that could vanish."*

This is a **contract gap**, not a bug in any single component's logic. Every component behaves
correctly under its own definitions; the *vocabulary* those definitions draw on is incomplete.

## Evidence — the current, verified status vocabulary

All values below were read from the live workspace on 2026-09-07 (`backlogit` version
`1.10.1-0.20260823032255-b07729386a31+dirty`), not assumed.

**Work items** — `task`, `subtask`, `bug`, `feature`, `chore`, `spike`, `deliberation`, `review`
(source: `backlogit metadata wit <type>`, backed by `.backlogit/header-def.yaml`):

```text
queued | active | blocked | review | done | accepted | rejected | archived     (default: queued)
```

**Shipments** (source: `.backlogit/header-def.yaml`, type `shipment`):

```text
queued | blocked | active | shipped | abandoned                                (default: queued)
```

**Directory routing** (source: `.backlogit/registry.yaml`):

| Directory | Statuses routed there |
|---|---|
| `queue/` | `queued`, `active`, `blocked`, `review` |
| `archive/` | `done`, `accepted`, `rejected`, `archived` |

**Observed distribution** (`backlogit query "SELECT status, COUNT(*) FROM items GROUP BY status"`):
`archived` 610, `done` 354, `queued` 69, `shipped` 30, `rejected` 11, `blocked` 2, `abandoned` 1.

**No temporary/park-like value exists anywhere.** A search of every `.backlogit/*.yaml` for
`parked|hold|paused|deferred|on-hold|suspended` returns no status match.

## Evidence — `archived` is terminal by design, and the return path is not first-class

Three independent confirmations:

1. **`backlogit archive --all-done`** is documented as *"archive all items with **terminal
   status**"*. Archive is explicitly the terminal-status operation.
2. **There is no `unarchive` command.** `backlogit unarchive` returns
   `Error: unknown command "unarchive" for "backlogit"`. The top-level command list contains
   `archive` and no inverse.
3. **`backlogit doctor` treats restoration as a repair path, not a lifecycle path.** It reports 59
   `archived_from_self_ref` issues worded: *"unarchive cannot restore it to the queue without the
   read-time self-heal."* Restoration exists only as internal self-healing machinery keyed off an
   `archived_from` breadcrumb — and that breadcrumb is already provably unreliable on 59 records in
   this very workspace.

**Consequence:** parking an item as `archived` today is not merely semantically wrong, it is
*mechanically* unsupported — there is no operation whose job is to bring it back, and the metadata
that would make a bring-back possible is already corrupt on a large fraction of archived records.

## Why the existing values do not close the gap

| Candidate | Why it fails |
|---|---|
| `blocked` | Routes to `queue/` — the item is still in the queue, which is the exact opposite of the requirement. Semantically it means "impeded by something external", not "deliberately set aside by a decision". Conflating them would make it impossible to distinguish "waiting on a dependency" from "we chose to stop working on this", and would pollute queue views and blocked-work reporting. |
| `archived` | Terminal by definition, no return operation, unreliable `archived_from` breadcrumb (see above). This is the value currently being overloaded, and the overloading is the defect. |
| `rejected` | Explicitly "will not be done" — asserts a decision the operator has *not* made. |
| `accepted` / `done` | Assert completion that did not happen. Falsifies velocity, burn-down and closure evidence. |
| `review` | Means "awaiting review", a distinct in-flight state; queue-resident. |
| shipment `abandoned` | Terminal; no park equivalent exists for shipments at all. |

## Blast radius — what a new status touches

### backlogit (EXTERNAL — separate repository and owner)

* **Status enum**, per work-item type, in `header-def.yaml` (8 types) and, for symmetry, the
  `shipment` enum.
* **Directory routing** in `registry.yaml`. This is the crux: a new status belongs to *neither*
  existing bucket. `queue/` contradicts "out of the queue"; `archive/` re-conflates with terminal.
  A status absent from both lists has **undefined routing** — a real tool-level gap, not a config
  tweak.
* **Transition validation** in `backlogit move`. **RESOLVED 2026-09-07 — `header-def.yaml` is NOT
  authoritative for transition validation.** Verified via
  `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md` (CORRECTION block of
  2026-08-04, checked against backlogit source `internal/core/shipment.go`,
  `isValidShipmentTransition` L336-345 and `MoveShipmentStatus` L107-108): **the Go binary
  hard-codes the transition matrix**, and `backlogit move` **does not validate against the
  schema — it silently accepts invalid status writes.**

  **This materially raises the stakes of this record.** The proof case already exists in the wild:
  `blocked` is declared for shipments in `header-def.yaml` but is *not* a defined `ShipmentStatus`
  constant in the binary, and has **no legal outbound transition**. Real `blocked` shipment records
  were created anyway, precisely because `move` accepted the write — each one a **dead end that can
  never legally transition**.

  Adding `parked`/`hold` by editing `header-def.yaml` alone would reproduce that failure mode
  exactly: a writable status with no legal exit, silently accepted, discovered only when something
  tries to leave it. **An upstream backlogit change (enum constant + transition matrix + validating
  write path) is therefore mandatory, not merely preferable.** This strengthens — and does not
  change — the conclusion below that both tools must change.

  It is also a second instance of this record's own governing principle: **a declared enum is not an
  enforced enum**, and where the declaration and the enforcer disagree, a non-validating write path
  lets the disagreement persist undetected.
* **A first-class return operation** (`park` / `unpark`, or `move --status parked` round-tripping
  cleanly), since `unarchive` does not exist.
* **Queue/list/query filters**, `doctor` integrity rules, and shipment-eligibility logic.

### autoharness (LOCAL)

* `schemas/backlog-tool-registry.schema.json` → `status_values` currently declares only
  `queued`, `active`, `done`, `blocked`. A new abstract status key is required for any
  registry-driven agent to address the state portably.
* `.autoharness/backlog-registry.yaml` → the concrete `status_values` mapping.
* **Gates** — `src/autoharness/gates/topology.py`, `src/autoharness/gates/shipment_closure.py`.
  The P-015 classifier's full-coverage precondition is the sharp edge: **does a parked child count
  as "covered"?** If a feature has one parked child, is it still a fully-covered root? Answering
  "yes" silently ships incomplete features; answering "no" makes parking a child permanently
  block its parent's cascade close. This needs a deliberate decision, not a default.
* **`shipment-reconcile`'s member-class status matrix** — the very table being authored by
  `15A02E21`'s fix. A new status must become an explicit row.
* **Agent templates and skills** that enumerate statuses (`templates/agents/_ship.agent.md.tmpl`,
  `templates/skills/shipment-reconcile/SKILL.md.tmpl`, and their resolved `.github/` pairs).

**Verdict on the operator's question:** adding this status requires **both** an upstream backlogit
tool/schema change **and** a local autoharness protocol/template change. Neither is sufficient
alone — autoharness cannot address a status backlogit will not persist or route, and backlogit
adding the value does not teach autoharness's gates what it means.

## Relationship to `15A02E21` — related, DISTINCT, must not be merged

Assessed deliberately, because the two touch the same table.

| | `15A02E21` | This record |
|---|---|---|
| Defect | An *existing* status (`active`) is rejected by a gate that no legitimate state can satisfy | A *needed* status does not exist in the vocabulary |
| Root cause | Two clauses of one skill contradict each other | The lifecycle vocabulary is incomplete |
| Tool | autoharness only (skill + template + agent, paired edits) | backlogit **and** autoharness |
| Fix | Rewrite Pre-Mode's per-item check to be member-class scoped | Add a status value, route it, define its transitions, teach every consumer |
| Blocking? | Decided and planned; ready to harvest | Requires deliberation; name not chosen |

**They are not the same contract surface.** They *intersect* at exactly one point: the member-class
status matrix `15A02E21` is authoring will, in future, need a row for whatever this status is
named. That intersection is handled by a **forward-compatibility obligation on `15A02E21`, not by
merging scope** — recorded as refinement **R-5** in the decision artifact: the matrix must treat an
unrecognised declared status as an **explicit HALT row**, never a silent fall-through. That costs
`15A02E21` nothing (its fail-closed default already halts on unrecognised values) and guarantees
that introducing a new status later surfaces as a loud, triageable HALT forcing a deliberate
decision, rather than being silently absorbed.

Merging them would couple a decided, ready-to-ship, single-tool fix to an undecided, cross-tool,
externally-blocked design question — delaying the first and under-thinking the second.

## Name recommendation — `parked` (Stage recommendation; NOT an operator decision)

**The operator offered `parked` or `hold` and did not choose between them. No name is decided.**
The choice is deliberation work, because the name is the whole point of the change — an
under-specified name reintroduces the tacit-meaning problem it exists to solve.

Stage recommends **`parked`**, on four grounds:

1. **`hold` collides with existing vocabulary in this codebase.** The `shipment-reconcile` skill
   already uses "hold" for lock ownership — *"this skill **holds** the
   `.backlogit/queue/{shipment_id}.md` file lock"*. A status named `hold` would make "the item is
   on hold" and "the agent holds the lock" ambiguous in exactly the protocol text that most needs
   precision. Introducing a status whose meaning depends on reading context is self-defeating here.
2. **`hold` competes semantically with `blocked`.** "On hold" most naturally reads as "cannot
   proceed" — which is what `blocked` already means. `parked` does not compete: *parked* =
   deliberately set aside by a decision; *blocked* = involuntarily impeded. Keeping those distinct
   is the requirement.
3. **Morphological consistency.** Every existing value is a past participle: `queued`, `blocked`,
   `review`(-ready), `done`, `accepted`, `rejected`, `archived`, `shipped`, `abandoned`. `parked`
   fits; `hold` would be the only bare verb/noun, and `on-hold` would introduce a hyphen used
   nowhere else in the enum.
4. **`parked` implies reversibility.** You park a vehicle intending to drive it again. `hold` is
   agnostic about whether return is expected — and "expected to return" is the defining property
   of the state being added.

**Rejected without prejudice pending deliberation:** `paused` (implies an in-flight process was
interrupted, but a parked item may never have started), `deferred` (already the established meaning
of the *stash*, and would conflate a backlog item with a stash entry), `suspended`, `icebox`.

## Open design questions for deliberation

1. **The name.** `parked` vs `hold` vs an alternative. See recommendation above.
2. **Where does a parked record live?** `queue/` contradicts "out of the queue"; `archive/`
   re-conflates with terminal. A third directory (`parked/`) is the semantically correct answer and
   also the largest change. This is the central design decision.
3. **Is there a shipment-level equivalent?** Shipments have no park state at all. Symmetry argues
   yes; shipments being coarser units argues it may be unnecessary.
4. **Transition matrix.** Which statuses may enter `parked`, and which may it leave to? Is
   `parked → queued` a first-class transition with an explicit operation (it must be — the whole
   point is a supported return path)? May a `done` item be parked (probably not — that is a
   re-open, a different concept)?
5. **P-015 coverage semantics.** Does a parked child count toward a feature's full-coverage
   precondition for CASCADE eligibility? Both answers have real costs (see Blast radius). This is
   the highest-risk interaction and the reason the entry is priority `high`.
6. **Metadata requirements.** Should `parked` mandate a reason and/or a review date, so a parked
   item cannot silently become a permanent one? (Directly serves the operator's anti-tacit-knowledge
   principle: a parked item with no recorded reason is the same information loss in a new costume.)
7. **Migration.** Are any of the 610 currently-`archived` items actually parked? If so, is a
   one-time reclassification in scope, or is the new status forward-only?
8. **Upstream sequencing.** backlogit is a separate repository and owner. The autoharness-side work
   is blocked on the upstream change landing and the installed binary advancing. Following the
   established precedent for backlogit-owned defects (`B57F9E24`, `3C7AAC71`, `90F2A9F8`), the
   backlogit portion is tracked, not harvested into the autoharness backlog.

## Acceptance criteria (provisional — subject to deliberation)

1. A status exists whose declared meaning is exactly "removed from the active queue, expected to be
   reconsidered", distinct from every terminal status and from `blocked`.
2. Its meaning is readable from the value alone — no dependence on storage location, on which agent
   set it, or on which workflow step is reading it.
3. A first-class, documented transition returns a parked item to the queue, not relying on
   archive self-heal machinery.
4. `archived` is narrowed to unambiguously terminal ("done or will not be done") once the new
   status exists.
5. Every autoharness consumer that enumerates statuses handles the new value **explicitly**;
   unrecognised statuses fail closed and loudly (the R-5 rule generalised).
6. The P-015 coverage question (open question 5) has a recorded, justified answer with test
   coverage for both a parked child and a parked sibling.
7. Directory routing for the new status is defined; no status has undefined routing.
8. The `docs/diagrams/` lifecycle set is updated to show the new state and its transitions.

## Non-goals

* Choosing the name unilaterally. Stage recommends `parked`; the operator decides.
* Implementing anything in the backlogit repository. That is a different product, repository and
  owner; width isolation (P-021 C1) applies, per the `B57F9E24` precedent.
* Expanding `15A02E21`'s shipment. The only permitted coupling is forward-compatibility refinement
  R-5, which is already recorded there.
* Re-opening `159-S`, modifying PR #436, or touching any archived record.
* Reclassifying the 610 existing `archived` items before open question 7 is answered.

## References

* `.backlogit/header-def.yaml` — per-type status enums (read 2026-09-07)
* `.backlogit/registry.yaml` — directory routing conditions
* `backlogit metadata wit <type>` — authoritative per-type field metadata
* `backlogit archive --help` — "archive all items with terminal status"
* `backlogit doctor` — 59 `archived_from_self_ref` findings; unarchive/self-heal wording
* `schemas/backlog-tool-registry.schema.json` — `status_values` abstract mapping
* `docs/decisions/2026-09-06-shipment-reconcile-cascade-pre-mode-contract-deliberation.md` — R-5
* `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md` — lesson 8
