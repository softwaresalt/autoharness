---
title: "SHIP-1 — v1.5.0 shipped-guardrail contract restoration"
date: 2026-08-31
slug: v1_5_0-guardrail-contract-restoration
doc_type: plan
source_stash: "053E2BD2 (primary); B698F01B (documentation-accuracy half only)"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
source_spike: "docs/decisions/2026-08-31-v1_5_0-guardrail-template-contract-mismatch-spike.md"
shipment_unit: "SHIP-1"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-1 — v1.5.0 shipped-guardrail contract restoration

## Problem

Two shipped `verify_workspace` assertions are **unsatisfiable by the templates
that generate the artifacts they check**. Both reproduce in the published v1.5.0
wheel, so they are shipped defects rather than working-tree drift. Every fresh
v1.5.0+ merge-install into a backlogit workspace fails both.

Verified read-only at `main` HEAD `2661c1c8`:

**Defect 1 — `closure_source_artifact_cleanup`.**
`src/autoharness/verify_workspace.py:303-311` (`PACK_ASSERTIONS["backlogit"]`)
requires `.github/skills/operational-closure/SKILL.md` to contain
`Source artifact cleanup`, `source_stash_id`, `source_deliberation_id`.
A token scan of `templates/skills/operational-closure/SKILL.md.tmpl` returns
**0 matches for all three**. The producer side is correct
(`templates/agents/_ship.agent.md.tmpl:856-859` instructs Ship to record archived
and skipped IDs in "the closure artifact's `Source artifact cleanup` section");
the consumer template never defines the section. The verifier is the *correct*
party: `.github/skills/install-harness/SKILL.md:720` and `:1082`,
`docs/backlogit-operating-model.md:49` and
`docs/backlogit-compatibility-matrix.md:55` all already document
operational-closure as the carrier of this contract.

**Defect 2 — `ship_release_closure_sequence`.**
`verify_workspace.py:566-575` requires the literal
`another top-level release unit may not begin yet`.
`templates/agents/_ship.agent.md.tmpl:709` now reads
`do not allow another top-level release unit to begin yet` — semantically
identical, lexically incompatible. **Masked in-repo**: the dogfood copy
`.github/agents/_ship.agent.md:606` still carries the old wording, so this
repository's own verify run passes. Only a foreign install target observes it.

**Root cause.** No test validates a guardrail against a *rendered* template.
`tests/test_verify_workspace.py:1925-1945` writes synthetic fixtures containing
exactly the required tokens and then asserts ok — it passes regardless of real
template content. The only real-artifact test (`:2179-2203`) reads this
repository's installed dogfood copies and covers 2 of 71 table-driven assertions;
dogfood copies are legitimately paired-edit lagging, so checking them cannot
detect template-side drift.

## Scope

In: the two provable defects, plus the render-aware contract test that would have
blocked the v1.5.0 release, plus one documentation-accuracy correction inherited
from `B698F01B`.

Out (recorded, deliberately not guessed):

* The **other two** failures the operator reported. They are not recoverable from
  this repository. Needed target evidence, named for a future session: the target
  workspace's `.autoharness/staging/verify-workspace-report.json`
  `targeted_checks` failures (keys + missing-token lists + reason), its
  `.autoharness/workspace-profile.yaml`, its `.autoharness/backlog-registry.yaml`,
  and the applied wording patches.
* The four wording-brittle-but-satisfiable assertions
  (`stage/ship_index_sync_gate`, `pipeline_topology_gate_ship_agent_wiring`,
  `ship_source_artifact_cleanup`). `053E2BD2` says "separate P3 hardening, do not
  bundle". Not bundled.
* The ten local staging-report failures classified as generated-install dogfood
  drift — the templates satisfy them after render.
* Every reserved `B698F01B` question: the replacement env-injection mechanism,
  whether to relax the guard, whether to delete `src/autoharness/supervise/`.

## Direction

Fix the **template**, not the verifier, for defect 1 — the four documentation
surfaces already describe the intended contract, so relaxing the verifier would
require correcting all of them. Fix the **verifier**, not the template, for
defect 2 — the newer template wording is the better prose and the assertion is a
lexical proxy for it.

## Hardening (P-006)

Triggered: multiple template families, the verifier assertion table, and the
dogfood mirror.

* **H1 (binding).** The dogfood mirror must be updated in the *same* task as its
  template. A template-only change to defect 2 would flip this repository's own
  verify run from pass to fail; a mirror-only change would deepen the drift.
* **H2 (binding).** The render-aware test must resolve each assertion's `path` to
  its **source-of-truth** — the `.tmpl` when one exists, the installed file only
  when it does not — using the verifier's own variable tables. Reading the
  dogfood copy reproduces the exact blindness being fixed.
* **H3 (binding).** The new test must be demonstrated **red before green**: it
  must fail on exactly these two assertions at the pre-fix revision and pass
  after. A test authored after the fix that has never been observed failing
  proves nothing.
* **H4.** No schema, manifest topology, registry, or agent-behaviour change.
  Blast radius is additive and lexical only; existing closure artifacts stay
  valid; backward compatible.
* **H5.** Task 4 touches `tests/test_verify_workspace.py`, as does task 3. They
  are sequenced 3→4 to avoid a same-file collision inside one shipment.
* **H6 (binding) — TDD sequencing: the red test lands FIRST.** **H3** requires the
  render-aware test to be observed failing on exactly the two named assertions
  *before* they are fixed. Cycle 0's task numbering contradicted that by placing
  the two fixes (tasks 1 and 2) ahead of the harness and sweep (3a/3b). Corrected
  execution order, which is the order the harvested tasks are queued in:
  1. **3a — render harness** (`151.003-T`). No assertion outcome depends on it yet.
  2. **3b — assertion sweep** (`151.004-T`). Run it here: it **MUST fail** on
     `closure_source_artifact_cleanup` and `ship_release_closure_sequence`, and on
     nothing else. **Record the observed red result.** A sweep that does not go red
     at this point is not measuring the templates and the shipment halts.
  3. **1 — defect 1 template fix** (`151.001-T`). 3b's first failure turns green.
  4. **2 — defect 2 verifier/mirror fix** (`151.002-T`). 3b's second failure turns
     green.
  5. **4 — comment correction** (`151.005-T`). Independent; last.

  Task 3b's charter is unchanged — it **detects**, it does not remediate (cycle 0
  finding 4). Any *third* assertion it reveals red is a P-021 capture and is
  **not** fixed here; the shipment records it and proceeds.
* **H7 (binding) — safety mode.** Every task enters `careful`. Task 3b
  additionally enters `freeze-scope` bounded to `tests/`, because a sweep that
  reveals unrelated failures is precisely where scope creep starts (cycle 0
  finding 4).

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Define the `Source artifact cleanup` section in the operational-closure skill template | M | medium | `templates/skills/operational-closure/SKILL.md.tmpl` + dogfood mirror |
| 2 | Reconcile the `ship_release_closure_sequence` assertion token with the current agent-template wording | S | medium | `src/autoharness/verify_workspace.py` + `.github/agents/_ship.agent.md` |
| 3 | Add a render-aware template↔verifier contract test over all table-driven assertions | L → split into 3a/3b | high | `tests/` |
| 4 | Correct the stale `autoharness.supervise.bootstrap` citation in the `.mcp.json` guard comment | XS | trivial | `tests/test_verify_workspace.py` |

Task 3 is split because `L` + `high` trips both axes of the two-axis granularity
gate:

* **3a — render harness**: render `templates/**/*.tmpl` with the verifier's own
  variable tables and resolve every assertion `path` to its source-of-truth.
  Size `M`, complexity `high`.
* **3b — assertion sweep**: assert all table-driven assertions
  (`PACK_ASSERTIONS`, `FOUNDATION_ASSERTIONS`, `DARK_FACTORY_ASSERTIONS`) hold
  against the rendered output, with no exemption list. Size `M`, complexity
  `medium`.

### Task 1 detail

Add a **Source artifact cleanup** subsection to the closure-artifact MUST-include
list at Step 2 (currently lines 65-84 of the 124-line template). It must name
`custom_fields.source_stash_id` and `custom_fields.source_deliberation_id` and
require the archived-and-skipped ID record, matching the producer contract at
`_ship.agent.md.tmpl:856-859`. Mirror into
`.github/skills/operational-closure/SKILL.md`.

**Placeholder specification (corrected in review-fix cycle 1 — binding).** Cycle 0
described this as a "`{{FEATURE_...}}`-gated" subsection. **`{{FEATURE_...}}` is
not a real placeholder family — no such variable exists in any autoharness
template or in the install-harness variable tables**, so that instruction was
unimplementable as written and would have produced an unresolved `{{...}}` in
every render. Specified concretely:

* The **only** placeholder this subsection may introduce is **`{{BACKLOG_DIRECTORY}}`**,
  the real variable documented at `.github/skills/install-harness/SKILL.md:205`
  (source `backlog_tool.directory`; resolves to `.backlogit` for a backlogit
  composition and `backlog` for a `backlog-md` composition).
* `{{BACKLOG_DIRECTORY}}` **always resolves** — every composition declares a backlog
  directory, including the `manual` one. It therefore introduces **no** conditional
  gating and **no** unresolved-variable risk, which is exactly what cycle 0's
  finding 1 was worried about.
* The subsection is written as **unconditional prose**. `source_stash_id` and
  `source_deliberation_id` are `custom_fields` names in the closure artifact, not
  variables, and are written literally.
* The template already uses `{{DOCS_CLOSURE}}`; no new placeholder beyond
  `{{BACKLOG_DIRECTORY}}` may be introduced by this task.

Acceptance: the three tokens (`Source artifact cleanup`, `source_stash_id`,
`source_deliberation_id`) are present in both files;
`closure_source_artifact_cleanup` passes against the **rendered** template, not
only against the installed copy; and a render under **both** the backlogit and the
non-backlogit variable sets leaves **no unresolved `{{`** anywhere in the output.

### Task 2 detail

Preferred direction, per the spike: update the **verifier** at
`verify_workspace.py:573` to the newer template wording, then bring the dogfood
`.github/agents/_ship.agent.md:606` into line with
`templates/agents/_ship.agent.md.tmpl:709` so all three agree. Acceptance: the
assertion's `must_contain` entry is satisfied by a fresh render of the template.

### Task 4 detail

`tests/test_verify_workspace.py:259-272` justifies forbidding `env` blocks by
citing `autoharness.supervise.bootstrap` as the value provider. That module does
not exist — `src/autoharness/supervise/` contains only source-less `__pycache__`,
and `ENGRAM_WORKSPACE` appears in exactly one live location repository-wide,
which is this comment. Rewrite the comment to state the *current* rationale
without citing a deleted module. **Comment only.** Do not change any assertion,
do not relax the guard, do not touch `.mcp.json`, and do not delete
`src/autoharness/supervise/` — that directory is untracked and gitignored
(`git ls-files` returns empty) and is therefore not expressible as a repository
change at all.

## Non-goals

Added in review-fix cycle 1 for structural parity with the other eight plans; these
restate and consolidate the exclusions already recorded in §Scope and §Hardening,
and add the cycle-1 ones.

* No relaxation of the `closure_source_artifact_cleanup` verifier assertion —
  defect 1 is fixed **template-side** (§Direction), because four documentation
  surfaces already describe the intended contract.
* No change to the `_ship.agent.md` template wording for defect 2 — the newer
  prose is better; the **verifier** moves to meet it.
* **No `{{FEATURE_...}}` or any other new placeholder.** The only placeholder task 1
  may introduce is `{{BACKLOG_DIRECTORY}}` (Task 1 detail).
* No schema, manifest topology, registry, or agent-behaviour change (**H4**).
* No remediation by task 3b — it **detects** only. A third assertion it reveals red
  is a P-021 capture, explicitly not fixed here.
* No fix for the two operator-reported failures that are not recoverable from this
  repository, and no bundling of the four wording-brittle-but-satisfiable
  assertions (§Scope, per `053E2BD2`).
* No change to any assertion, no relaxation of the `.mcp.json` `env` guard, no edit
  to `.mcp.json`, and no deletion of `src/autoharness/supervise/` (Task 4 detail).
* No answer to any reserved `B698F01B` question.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests` (the authoritative gate,
per `031-DL` Q5). Plus: `verify-harness`, and a fresh-render check of the two
named assertions.

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Template integrity | **P1** | Adding a `{{FEATURE_...}}`-gated section could leave an unresolved `{{...}}` in a non-backlogit render. | Task 1 acceptance extended: assert **no unresolved `{{` remains** in the rendered output for *both* the backlogit and the non-backlogit variable set. |
| 2 | Correctness | **P1** | Fixing the verifier for defect 2 while the dogfood copy still carries the old wording would silently keep this repo green for the wrong reason. | H1 made binding; task 2 explicitly requires all three surfaces (verifier, template, mirror) to agree, and its acceptance is a fresh render, not the mirror. |
| 3 | Schema/CLI/docs coupling | P2 | Relaxing the verifier for defect 1 instead of fixing the template would invalidate four documentation surfaces. | Direction fixed in §Direction: template-side for defect 1. The four docs need no change. |
| 4 | Scope | P2 | Task 3 could balloon into fixing every assertion it discovers failing. | Task 3b's charter is to **detect**, not remediate. Any assertion it newly reveals is a P-021 capture for a later run, and the task explicitly may not fix it. |
| 5 | Maintainability | P2 | A render-aware sweep over 71 assertions may be slow enough to be disabled. | 3a must render once per test class and cache; if wall-clock exceeds the suite budget, the sweep is marked as a single test over a prebuilt render rather than 71 separate cases. |
| 6 | Security | P3 | The render harness executes template substitution over arbitrary `.tmpl` content. | Substitution is pure string replacement from the verifier's own fixed variable tables. No `eval`, no shell, no network. Recorded as a constraint on 3a. |
| 7 | Constitution | P3 | Task 4 edits a file the operator flagged "do NOT auto-fix". | The instruction attaches to `B698F01B`'s **decision questions**. Task 4 is a comment-accuracy correction that changes no behaviour and pre-empts none of the three reserved questions, all of which remain open with the entry ACTIVE. |

**Verdict: PASS.** 2 P1 raised, 2 resolved. Zero unresolved P0/P1. One review-fix
cycle of three.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `yes`. Satisfied.** **H1**–**H7** are binding
and each is propagated into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Template integrity | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Correctness | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Schema/CLI/docs coupling | inline persona pass | 1 P2 (cycle 0) |
| Scope boundary | inline persona pass | 1 P2 (cycle 0) |
| Maintainability | inline persona pass | 1 P2 (cycle 0) |
| Security | inline persona pass | 1 P3 (cycle 0) |
| Constitution | inline persona pass | 1 P3 (cycle 0), 1 P1 (cycle 1) |
| Architecture | inline persona pass | — (no finding) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 8 | Template integrity | **P1** | Task 1 specified a "`{{FEATURE_...}}`-gated" subsection. No `{{FEATURE_...}}` placeholder family exists in any template or in the install-harness variable tables, so the instruction was unimplementable and would have emitted an unresolved `{{...}}` in every render — the exact failure cycle-0 finding 1 tried to prevent. | **Resolved.** The task now names the single real placeholder **`{{BACKLOG_DIRECTORY}}`** (`install-harness/SKILL.md:205`), notes that it always resolves so no conditional gating is introduced, and forbids any other new placeholder. The no-unresolved-`{{` acceptance under both variable sets is retained. |
| 9 | Correctness | **P1** | **H3** demands red-before-green, but the task order placed both fixes ahead of the test that must observe them failing. Executed as numbered, the sweep would have been authored against an already-fixed tree and proved nothing. | **Resolved by H6.** Execution order is now 3a → 3b (**record the red**) → 1 → 2 → 4, matching the queued task order, with an explicit halt if 3b does not go red on exactly the two named assertions. |
| 10 | Constitution | **P1** | No safety mode declared for a shipment whose sweep task deliberately runs 71 assertions across the whole template corpus. | **Resolved by H7**: `careful` on all tasks, plus `freeze-scope` on `tests/` for the sweep task. |

**Verdict: PASS.** Cycle 1: 3 P1 raised, all 3 resolved. Cumulative: **zero
unresolved P0/P1**. Two review-fix cycles of three consumed.
