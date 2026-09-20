---
title: "Foundation: review-authority compatibility and atomic recording"
description: "Makes the verdict manifest the single authority for latest attempt and verdict, compatibly with the records that already exist. Delivers a versioned total normalizer accepting all three live manifest shapes, a canonical form open at the boundary and closed at the core, strict validation downstream of normalization only, an atomic review-result recorder on the 185-S atomic writer, and a mechanical consumer-inventory rule. Migrates all four review-verdict consumer surfaces in one activation commit, including Harvest, which today reads an inline decision marker from the plan body and never opens the manifest. Absorbs the scope of the archived 179-S."
doc_type: plan
source: docs/plans/2026-09-18-review-authority-foundation-plan.md
date: 2026-09-18
plan_id: review-authority-foundation
plan_path: docs/plans/2026-09-18-review-authority-foundation-plan.md
plan_role: active
revision: 2
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document authored under the strategic redesign, not a remediation of a prior revision. It carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review. Revision 2 remediates one finding of the PR #457 current-HEAD Copilot review of Push A, a P-021 C1 in-scope completion of this already-published plan: the ACTIVATE commit modifies manifest-tracked installed artifacts and the Rollout section omitted the atomic .autoharness/harness-manifest.yaml checksum refresh those edits require. The Rollout section now binds decision D11 - the affected manifest entries refreshed in the same commit and the same rollback unit, followed by a checksum-parity re-digest - and states that the refreshes are commit members rather than activation surfaces, so no surface, consumer or gate count in this plan moves. No task is added and the live manifest is not edited: this is a future implementation contract. It still carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-review-authority-foundation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 4
source_stash_ids:
  - C9CD24F3
feature_id: 180-F
shipment_id: 186-S
unit_role: precursor-foundation
depends_on_shipments:
  - 185-S
supersedes_plan: docs/plans/2026-09-17-single-governing-plan-contract-plan.md
absorbs_shipment: 179-S
absorbs_feature: 171-F
self_hosting: true
requires_plan_hardening: true
hardening_rationale: "This unit changes the review gate that governs this unit, migrates four consumer surfaces in one commit, and must remain compatible with every verdict manifest in the repository including one governing an untouched shipment. Self-hosting plus cross-surface activation is the highest-risk combination in the portfolio."
tags:
  - foundation
  - review-authority
  - manifest-compatibility
  - atomic-recording
  - self-hosting
  - precursor
---

# Foundation: review-authority compatibility and atomic recording

## Problem frame

`179-S` was blocked at terminal attempt 08 with one P0 and seven P1 findings.
It is **archived and absorbed here**, not abandoned: its central defects were
not local errors but missing producers.

| Attempt-08 finding | Why it could not be patched in place |
|---|---|
| `A1` (P0) — Harvest omitted from the consumer migration | Harvest reads an inline marker; migrating it needs a manifest reader that tolerates the live corpus |
| `B1` — the closed eight-key format rejects the live manifests | Needs a normalization layer that did not exist |
| `B2` — pre-review manifests carry nulls the closed format cannot accept | Same |
| `B3` — `link_supersession()` can create two active documents | Needs an atomic writer that did not exist |
| `B5` — no atomic review-result recorder | Same |
| `B4` — the consumer graph is stale | Needs a mechanical inventory rule, not a hand-maintained list |
| `B6` — the token contract is six in one place, eight in another | Resolved by a single canonical schema |
| `B7` — template/mirror pairs declared atomic are split across commits | Resolved by the ACTIVATE rule: one task, one commit |

Source stash `C9CD24F3` carries forward unchanged.

## The load-bearing defect

`.github/skills/harvest/SKILL.md` Phase 1, step 3–4:

> Locate the latest `## Plan Review` section and require literal
> machine-readable markers: `dispatch_mode:` and `decision:` …
> `decision: PASS` — proceed.

Harvest reads an **inline marker inside the plan document**. It never opens the
verdict manifest. A stale or superseded inline `PASS` admits a plan to
decomposition **today** — and Harvest is precisely the consumer whose
misreading has executable consequence, because it is the step that creates
work.

## The compatibility problem, measured

Seven verdict manifests are live in `docs/reviews/`. Their top-level key sets
are **not uniform**:

| Family | Count | Shape |
|---|---|---|
| A — attempt-roster | 6 | 21 keys: `plan_id`, `latest_attempt`, `review_terminal`, `awaiting_attempt`, `gate_result`, `verdict`, `remediation_authorization`, `latest_remediation_revision`, `latest_disposition`, `latest_artifact`, `attempts`, `carried_forward_context`, … |
| B — cycle-record | 1 | 17 keys: `source_decision`, `decision_revision`, `source_stash_id`, `deferred_scope_expansions`, `review_cycle`, `review_cycles_remaining`, `review_cycle_authorization`, `dispatch_mode`, `decision`, … |
| C — pre-review | 0 live | `latest_attempt: null`, `latest_artifact: null`, `attempts: []` — the legitimate state of a plan authored but not yet reviewed |

Family B is `2026-09-17-closure-evidence-naming-contract-plan-review.md`, which
governs `175-S` — **a shipment this work must not touch**. A normalizer that
has only ever seen Family A will meet Family B in production.

A closed eight-key format would reject all seven. That is `B1` and `B2`, and it
is why the canonical form is **open at the boundary and closed at the core**: a
fixed required set plus a preserved-extras map, so `gate_result`, `p0_open`,
`latest_remediation_revision`, `review_terminal`, `awaiting_attempt` and the
roster extras survive the round trip instead of being rejected.

## Contract

```text
raw manifest ──▶ normalize() ──▶ canonical ──▶ strict validate
                     │
                     └── unnormalizable ──▶ QUARANTINE (typed)
```

`normalize()` is **versioned and total**: it accepts every shape in the pinned
corpus, never raises, and never silently drops a field. Strict validation runs
**only downstream of normalization**, and only against newly authored records.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `HARVEST_ADMITTED` — normalized manifest reports `verdict: PASS` at `latest_attempt`, and that attempt was taken against the plan's current revision |
| Fail state | `HARVEST_REFUSED` — manifest absent, non-`PASS`, or `PASS` against a superseded revision |
| Third state | `MANIFEST_QUARANTINED` — classified **fail**, never absence |
| Producer | the atomic review-result recorder (`180.007-T`) |
| Consumer | `harvest` and `plan-review`, template **and** installed mirror — four surfaces |
| Activation commit | `180.010-T` |

`HARVEST_ADMITTED` is reachable: Family-A manifests already carry `verdict` and
`latest_attempt` in the required positions.

### Self-hosting

**This unit changes the review gate that governs this unit.** It is therefore
authored and reviewed under the **current inline-marker system**, and its
ACTIVATE commit is what switches the workspace onto the manifest system. The
new gate never admits its own plan. Any sequencing that would have the new gate
evaluate `186-S` is a defect.

## The consumer inventory is a rule, not a list

`B4` blocked on a stale hand-maintained consumer graph. The inventory is
therefore **mechanical**: tracked files matching the review-verdict marker set,
minus generated paths.

`.autoharness/staging/` is excluded **by rule**. It contains copies of both
skills but is gitignored (`.gitignore:6`) and is a generated `verify-workspace`
artifact, not a mirror. Excluding it by oversight rather than by rule is how a
future inventory drifts.

The regression asserts the rule currently returns **exactly four** surfaces:

```text
templates/skills/harvest/SKILL.md.tmpl
templates/skills/plan-review/SKILL.md.tmpl
.github/skills/harvest/SKILL.md
.github/skills/plan-review/SKILL.md
```

A forgotten consumer then fails a test instead of being silently exempted.

## Rollout

**PREPARE (inert).** `180.001-T` through `180.008-T`. The normalizer, schema,
validator, recorder and inventory rule all exist and are tested while **no
consumer calls them**. Harvest and plan-review continue reading the inline
marker throughout, so live behaviour is unchanged.

**VERIFY.** `180.009-T` — every RED assertion observed failing, the same
assertions observed passing, and all eight pinned fixtures normalized and
validated without error.

**ACTIVATE.** `180.010-T` — **one task, one commit** migrating all four
surfaces simultaneously. Sequential edges are not atomic: a commit between two
migration tasks is a state in which Harvest reads the manifest while
plan-review still writes only the inline marker, or a mirror has drifted from
its template. All four move together or none do.

**Manifest parity is part of that same atomic unit (decision `D11`).** Two of
the four migrated surfaces — `.github/skills/harvest/SKILL.md` and
`.github/skills/plan-review/SKILL.md` — are **manifest-tracked installed
artifacts**, each with an `artifacts:` entry in
`.autoharness/harness-manifest.yaml` recording a `sha256` of its pre-migration
content. The two templates are not tracked, so `180.010-T` refreshes **exactly
two** manifest entries and its commit contains **six files while migrating four
consumers**. In the **same commit** and the **same rollback unit**, rewrite
each of those two checksums to the `sha256` of the installed file *as written
by this commit*, then **verify checksum parity** by re-digesting both installed
files and comparing against the recorded values. A commit that migrates either
installed skill without its manifest refresh leaves the manifest asserting a
digest of a file the same commit has already rewritten — an installed-artifact
parity hole in the very file this unit is making the single review authority —
and is an **immediate revert**, not a fixup commit. The refreshes are **commit
members, not consumer surfaces**: the consumer count stays **four**, no gate
arity moves, and the normalizer's fixture set is untouched. This binds a
**future implementation commit**; it authorizes no staging-time edit to the
live manifest, and none has occurred.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `180.001-T` | PREPARE | pin seven live manifests + synthetic Family C fixture | S | low |
| `180.002-T` | RED | normalizer totality tests over every pinned fixture | M | medium |
| `180.003-T` | IMPL | versioned normalizer: Family A/B/C → canonical | M | high |
| `180.004-T` | RED | canonical strict-validation tests incl. extras preservation | S | medium |
| `180.005-T` | IMPL | canonical schema + strict validator | S | medium |
| `180.006-T` | RED | atomic recorder tests: partial write unreachable across four surfaces | M | high |
| `180.007-T` | IMPL | atomic review-result recorder on the `185-S` atomic writer | M | high |
| `180.008-T` | IMPL | consumer inventory rule + four-surface regression | S | medium |
| `180.009-T` | VERIFY | full evidence set across all eight fixtures | S | low |
| `180.010-T` | ACTIVATE | one commit migrating all four consumers | M | high |

Edges: `180.001-T` → `180.002-T` → `180.003-T`; `180.004-T` → `180.005-T`;
`180.006-T` → `180.007-T`; `180.008-T` independent. All four chains converge on
`180.009-T` → `180.010-T`. The chains are **not** serialized against each
other.

## Out of scope

* Repository-wide plan migration, its regression suite, compact-context
  auto-consolidation, and the plan-budget contract. Moved out by revision 3 of
  the superseded portfolio decision; they stay out.
* Any rewrite of `docs/reviews/review-history/`. **Immutable history is never
  rewritten**, including the manifests whose `description` wording attempt-08
  recorded as `C1`. That wording is corrected in the mutable manifest only, and
  only as part of `180.010-T`.
* `175-S` and its Family-B manifest are **read as a fixture and never mutated**.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Self-hosting: the new gate evaluates its own plan | Explicit sequencing rule above; `186-S` is reviewed under the current system, and the activation commit is the switch. |
| R2 | A third manifest family appears after fixtures are pinned | `normalize()` is total by contract: an unrecognized shape yields `QUARANTINE` with a reason, never a crash and never a silent pass. |
| R3 | Migrating Harvest breaks decomposition for in-flight plans | Every live plan's manifest is a pinned fixture, so admission behaviour is observed before activation rather than discovered after it. |
| R4 | The activation task exceeds two hours | Four files, one contract change each, with the reader already built and verified. If it does not fit, the contract is too wide and must be re-scoped — it must **not** be split across commits. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Could the new gate ever evaluate this unit's own plan? | It must not, and this is the unit's defining hazard. `186-S` is authored and reviewed under the **current inline-marker** system; the ACTIVATE commit is the switch. Any sequencing in which the manifest gate admits `186-S` is a defect, not a convenience. |
| H2 | What happens the first time `normalize()` meets an eighth manifest shape? | It returns `QUARANTINE` with a reason. Totality is the contract: `normalize()` never raises, so an unknown shape degrades to a classified failure instead of breaking Harvest for every plan. |
| H3 | Does the canonical form lose Family-A roster fields? | No. The core is closed on a required set, but the boundary is open and extras are preserved in a map. A round-trip test asserts `gate_result`, `review_terminal`, `awaiting_attempt` and `latest_remediation_revision` survive. |
| H4 | Is the Family-B manifest at risk of mutation? | No. `2026-09-17-closure-evidence-naming-contract-plan-review.md` governs `175-S` and is read as a **frozen fixture only**. No task in this unit writes to it. |
| H5 | Could a stale inline `PASS` still admit a plan after activation? | Only if a consumer was missed. The inventory is a rule over tracked files with generated paths excluded by rule, and the regression pins the current count at exactly four. A missed consumer fails a test. |
| H6 | Is `.autoharness/staging/` a fifth consumer? | No. It contains copies of both skills but is gitignored generated `verify-workspace` output. It is excluded **by rule**, not by oversight — an oversight-based exclusion would drift the moment the rule was re-derived. |
| H7 | What if ACTIVATE does not fit in two hours? | Then the contract is too wide and must be re-scoped. It must **not** be split across commits: a commit boundary inside the migration is a reachable state where Harvest reads the manifest while plan-review writes only the inline marker. |

### Blast radius

The review gate governing every plan in the repository, plus two skills in both
template and installed form. A defect either admits an unreviewed plan to
decomposition or blocks every reviewed plan. Both are workspace-wide.

### Rollback

`180.001-T`–`180.009-T` are inert and revert cleanly. `180.010-T` reverts as a
unit, restoring inline-marker reading across all four surfaces simultaneously —
possible only because they moved together.

### Verification floor

All eight fixtures (seven live manifests plus the synthetic Family C) normalized
and strictly validated, extras preserved, and the four-surface inventory count
asserted. A green suite that exercises only Family A has not verified the
compatibility decision.
