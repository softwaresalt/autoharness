# Plan Review — P-015 cascade pre-archived manifest members (multi-persona adversarial)

Date: 2026-08-18
Agent: Stage (plan-review gate)
Plan: `docs/plans/2026-08-18-p015-cascade-pre-archived-member-plan.md`
Hardening: `docs/plans/2026-08-18-p015-cascade-pre-archived-member-hardening.md` (HARDENED, H1-H8)
Spike: `docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`
Scope: `132-F` / `132.001-T`-`132.003-T` / `141-S`
Review rounds: 1 (six personas)

## Summary

A contract-only change closing the P-015 cascade close-path gap that produced the
140-S classifier-override deviation. Three width-isolated tasks: skill contract,
policy mirror, regression tests. No gate code changes; no invariant relaxed.

**Verdict: PASS — 0 unresolved P0, 0 unresolved P1.**
Seven findings raised (4xP1, 2xP2, 1xP3). All four P1s resolved before this
verdict. P2s resolved. P3 accepted with rationale.

---

## Persona 1 — Close-path safety adversary

*"Show me how this change lets an unsafe close through."*

The change adds tolerance language only. It relaxes no gate: step 2
(`returned_ids` empty), step 3 (`archived_ids` exact match), step 4 (`parent_id`
preserved) and step 6 (gate decision) are all untouched, and the hardening makes
that a binding acceptance constraint (H6). The classifier's preconditions are
untouched (H2).

### F1 (P1) — Incentive attack: pre-archive deliberately to escape safe-close's stricter checks

Safe-close enforces a protected set with a verify-after-each invariant; cascade
does not. If tolerance is documented, could a session deliberately pre-archive
manifest members to steer closure onto the weaker-looking cascade path?

**Resolved — structurally impossible.** Path selection is made by the classifier,
not by archival state. Cascade requires **every** feature member to be a root and
**fully covered**, with the manifest containing nothing beyond qualifying roots
and their children. A manifest with any unshipped sibling — the only situation
where a protected set exists — fails full-coverage and falls back to safe-close
regardless of what was archived. Pre-archiving cannot manufacture eligibility;
the spike's arms 2 and 3 confirm archival state does not move the verdict.
Correspondingly, a qualifying cascade manifest has no protected set by
construction, which H3 requires the new text to state explicitly.

### F2 (P1) — Does documenting tolerance weaken detection of a *real* stray archival?

If pre-archived members are "expected", does an artifact wrongly archived by some
earlier bug now get waved through?

**Resolved.** Tolerance is scoped to **manifest members only** (H3). A stray
archival of a **non-manifest** artifact is still caught by step 3's exact-match
check, which is explicitly preserved. A stray archival of a manifest member is,
by definition, in scope for this closure. No detection is lost.

---

## Persona 2 — Contract-drift / cross-reference adversary

*"What silently breaks elsewhere in the document?"*

### F3 (P1) — Numeric cross-reference breakage

Raised and resolved in hardening **H1**: line 379 references the sub-procedure's
"step 4" from outside it. The unnumbered-preamble placement requirement preserves
all existing numbering. Verified by grep that line 379 is the only external
numeric reference into the sub-procedure, and that lines 543/552/555 reference
`Step 0(b)` (safe-close numbering, unaffected).

Policy-side equivalent handled by **H7** (append as item 7, never insert among
1-5, preserving item 5's "any of the preconditions above" semantics).

---

## Persona 3 — Evidence adversary

*"Did the spike actually prove what the plan claims?"*

### F4 (P1) — Spike ran against a `.backlog` root; the live workspace is legacy `.backlogit`

`backlogit init` created the new-default `.backlog` storage root, but this
workspace runs the legacy `.backlogit` root. If the classifier or the ship
operation branched on root name, the spike would not transfer.

**Resolved — verified by source reading.** `classify_shipment_close_path` takes
`workspace_backlog_dir` as a parameter and resolves children purely as
`backlog_dir / "queue"` and `backlog_dir / "archive"`; it contains no reference
to either root name and no branching on it. `_read_artifact_record` likewise
scans the two fixed subdirectories of the passed-in path. The spike additionally
invoked the classifier with an explicit path, exercising exactly that
parameterisation. Root naming is therefore not a variable in this behaviour.

The residual — that the spike observed `backlogit v1.9.0` behaviour rather than a
documented API guarantee — is explicitly carried by **H6**, which requires the
contract to cite the spike as provenance and to rely on step 3 as the live
fail-closed guard against a future engine regression.

### F5 (P2) — Only one manifest shape was exercised

The spike used a single root feature with one child. Multi-child and multi-feature
manifests were not shipped in the spike.

**Resolved by task design.** The behaviour under test is per-item idempotency of
archival, which does not vary with manifest cardinality, and the classifier's
cardinality handling is already covered by the existing test module.
`132.003-T` additionally adds multi-member and mixed queued/pre-archived cases,
covering the gap at test level where it is cheap, rather than by re-running a
broader live spike.

---

## Persona 4 — Scope-discipline adversary (P-010 / P-016 / operator scope)

*"Where does this exceed the authorised scope?"*

The operator scoped surfaces to the shipment-reconcile skill template, the
workflow-policy template/mirrors *if required*, and the gate code *only if
evidence proves code behaviour needs change*.

* Gate code: **excluded**, and the exclusion is evidence-backed rather than
  assumed — the spike positively demonstrates correct existing behaviour.
* Ship agent template + its checksum-tracked mirror: **excluded**. Verified that
  `templates/agents/_ship.agent.md.tmpl:714` already states "select the close path
  from the verified check, never from prose alone", so the classifier-authority
  rule is present there. Including it would have forced a `harness-manifest.yaml`
  checksum refresh — real width expansion for no correctness gain.
* No mirror files exist for the two edited templates (verified: no
  `.github/skills/shipment-reconcile/` and no `.github` workflow-policy mirror),
  so "mirrors if required" resolves to none.

### F6 (P2) — Stale disproven remedy left in the compound library

The evidence doc recommends relaxing step 3 — now disproven. Leaving it uncorrected
invites a future session to implement the rejected Option A.

**Resolved.** The plan now carries a **Post-merge obligation** section binding Ship
to invoke compound-refresh on that entry during Step 6 closure, with the four
specific corrections enumerated. This uses Ship's existing compound-refresh
obligation rather than adding a task, keeping the shipment width-isolated.

---

## Persona 5 — Ship-executability adversary

*"Can Ship actually execute each task inside 2 hours, and is width isolated?"*

| Task | Surface | Family | Size / Complexity | Within 2h |
|---|---|---|---|---|
| `132.001-T` | `templates/skills/shipment-reconcile/SKILL.md.tmpl` | skill template | S / medium | yes |
| `132.002-T` | `templates/policies/workflow-policies.md.tmpl` | policy template | XS / low | yes |
| `132.003-T` | `tests/test_shipment_closure_classification.py` | tests | S / low | yes |

Each task touches exactly one file in one family. No task mixes template work
with CLI or schema work. Acceptance criteria are mechanically checkable.
Dependencies (`132.001-T` blocks the other two) reflect genuine wording
dependence, not artificial serialisation.

### F7 (P3) — `132.002-T` and `132.003-T` could run in parallel

Both depend only on `132.001-T`. Ship executes serially within a shipment.

**Accepted.** No change; serial execution of two small tasks costs little and
keeps the review surface ordered.

---

## Persona 6 — Regression / test adversary

*"Would these tests actually fail if the contract were violated?"*

A naive test suite asserting only "pre-archived yields CASCADE" would pass against
a classifier that ignored archival state entirely and would not detect an
over-grant. **H8** binds `132.003-T` to include the two negative cases
(out-of-manifest child discovered in `archive/`; pre-archived non-root feature
member), constraining the grant from both sides, plus hermetic `tmp_path`
fixtures with no access to the live `.backlogit/` tree.

One further observation, folded into `132.003-T`'s acceptance: the module's
existing cases must continue to pass **unchanged**, so shared helpers may be
extended but not re-specified.

---

## Findings ledger

| ID | Severity | Title | Status |
|---|---|---|---|
| F1 | P1 | Incentive attack via deliberate pre-archival | Resolved (structural) |
| F2 | P1 | Tolerance weakening stray-archival detection | Resolved (scoped to manifest) |
| F3 | P1 | Numeric cross-reference breakage | Resolved (H1 / H7) |
| F4 | P1 | Spike root-name transferability | Resolved (source-verified) |
| F5 | P2 | Single manifest shape in spike | Resolved (covered in tests) |
| F6 | P2 | Stale disproven remedy in compound library | Resolved (Ship compound-refresh) |
| F7 | P3 | Parallelisable tasks run serially | Accepted |

## Verdict

**PASS.** 0 unresolved P0, 0 unresolved P1. Cleared for harvest into `132-F` /
`141-S`.
