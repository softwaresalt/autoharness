---
title: "S0 — Policy registry and review-persona layer install/restore"
date: 2026-08-27
slug: policy-registry-and-review-persona-layer
source_stash: "336F3AB7"
source_decision: "docs/decisions/2026-08-27-pre-review-evidence-dag-shipment-portfolio-deliberation.md"
shipment_unit: "S0"
status: reviewed
---

# S0 — Policy Registry and Review-Persona Layer Install/Restore

## Provenance and lineage

* **Source stash**: `336F3AB7` (critical bug, age 2 days) — *"Policy registry and
  review-persona layer are cited repo-wide but were never installed."* This plan
  is the sole downstream owner of that entry; the entry is consumed and archived
  only after shipment verification succeeds.
* **Authoritative portfolio**: `031-DL`
  `docs/decisions/2026-08-27-pre-review-evidence-dag-shipment-portfolio-deliberation.md`
  §"Shipment Portfolio" -> **S0 — Prerequisite closure**, and §R3 (hidden
  prerequisites, must not be duplicated).
* **Operator authority consumed**: **Q7 APPROVED — clear S0, do not waive it.**
  S0 must be staged before S1. **Q5 APPROVED** — the authoritative test command
  is `PYTHONPATH=src python -m unittest discover -s tests`; this is directly
  load-bearing here because the policy-registry template carries a
  `{{TEST_COMMAND}}` placeholder (see U1).
* **Not re-owned here**: `8AC574F1` (skill install, 18/29 present) is a separate
  entry and is untouched by this plan (`031-DL` §R3, Next Step 4).

## Problem Frame

Two install gaps, both **pre-existing** and both verified against the tree at
`d2e9a7e6`:

**GAP 1 — the policy registry is cited but absent.**

* `templates/policies/workflow-policies.md.tmpl` exists (83,467 bytes, 27
  `P-0NN` headings covering P-001 … P-021 plus sub-clauses).
* `.github/policies/` **does not exist** in this workspace.
* Policy IDs P-001 … P-021 are cited by ID across `AGENTS.md`, every pipeline
  agent, the instruction set, and the 14 installed skills.
* `src/autoharness/verify_workspace.py` `DARK_FACTORY_ASSERTIONS` declares
  `dark_factory_policy_contract` with `"path": ".github/policies/workflow-policies.md"`
  and **`"required": True`** (L866-L877), so the engine itself reports the file
  missing.
* `.autoharness/harness-manifest.yaml` L275 records the gap explicitly and
  attributes it to **stash `336F3AB7`**.

**GAP 2 — the review-persona layer is routed to but absent.**

* `.github/agents/subagents/` **does not exist**.
* Installed `plan-review/SKILL.md` and `review/SKILL.md` route to personas by
  installed path (`.github/agents/subagents/<name>.agent.md`). Those routes are
  dangling today. The manifest (L255, L265) records them as knowingly emitted
  dangling references.
* **Measured reference set (11 personas)** actually cited by installed skills
  and agents: `agent-native-parity-reviewer`, `architecture-strategist`,
  `concurrency-reviewer`, `constitution-reviewer`, `learnings-researcher`,
  `python-reviewer`, `schema-cli-docs-coupling-reviewer`,
  `scope-boundary-auditor`, `security-lens-reviewer`, `security-reviewer`,
  `template-integrity-reviewer`.
* **Template availability audit**:
  * 10 of 11 have a template — 9 under `templates/agents/review/`, plus
    `learnings-researcher` under `templates/agents/**research**/` (different
    directory; a naive `review/`-only installer misses it).
  * **`python-reviewer` has NO template anywhere in the tree.** Confirmed by
    exhaustive filename search across `templates/`. `language-engineer.agent.md.tmpl`
    is an *implementation* agent, not a reviewer, so it is not a substitute.
  * 3 templates under `templates/agents/review/` have **no citing reader**:
    `correctness-reviewer`, `maintainability-reviewer`, `technology-reviewer`.

**Why this is a prerequisite rather than housekeeping.** S2 plan-soundness
diagnostics and S10 persona routing both cite policy IDs and personas that must
resolve. Beyond the portfolio, the gap is self-referential: **this very plan's
`plan-review` gate cannot dispatch reviewer subagents because the identities it
routes to do not exist** — the degraded dispatch mode recorded in the Plan Review
section below is itself direct evidence of GAP 2.

## Requirements Trace

| # | Requirement (source) | Implementation action | Unit |
|---|---|---|---|
| R1 | GAP 1: install the policy registry (`336F3AB7`, "run the elective installer for the policy registry first — GAP 1 is load-bearing for every agent") | Render `templates/policies/workflow-policies.md.tmpl` -> `.github/policies/workflow-policies.md`; register in manifest | **U1** |
| R2 | Q5 APPROVED: authoritative test command | Bind `{{TEST_COMMAND}}` to `PYTHONPATH=src python -m unittest discover -s tests` at render; do **not** take the profile's stale `pytest` | **U1** |
| R3 | The engine must stop reporting the registry missing (`dark_factory_policy_contract`) | Reconcile `_resolve_policy_registry` precedence + docstring; re-run targeted check | **U2** |
| R4 | GAP 2: `python-reviewer` route must resolve | Author the missing persona template | **U3** |
| R5 | GAP 2: install the cited persona identities | Render 11 personas -> `.github/agents/subagents/` | **U4, U5, U6** |
| R6 | Installed artifacts must be manifest-tracked with checksums | Register 11 persona artifacts | **U7** |
| R7 | `031-DL` Law 2 — no artifact without a reader | Explicitly **do not** install the 3 uncited persona templates; record the exclusion | **U6** (decision), **U8** (assert) |
| R8 | Verification that both gaps are closed | Targeted `verify-workspace` checks + placeholder scan + route-resolution test | **U8** |

## Non-goals

* **No policy text authoring or revision.** U1 is a *render*, not an edit. The
  template is the source of truth; if the rendered registry disagrees with agent
  prose, that is a finding for a later shipment, not a fix here.
* **No re-owning `8AC574F1`** (residual skill install gap) and no downgrade of
  its priority — that is operator-visible and out of scope (`031-DL` Next Step 4).
* **No `workspace-profile.yaml` re-discovery.** `336F3AB7` notes the profile
  carries stale `test.runner: pytest` / `test.command: pytest` values. Q5
  resolves which value is authoritative **for rendering**; correcting the profile
  itself is a separate change with its own blast radius (it feeds `profile_hash`).
  Recorded as a carried-forward finding in U8, not fixed here.
* **No installation of the 3 uncited persona templates** (Law 2).
* **No detector, no gate, no DAG work** — that is S1.
* **No promotion of any check to blocking.**

## Implementation Units

### U1 — Render and install the policy registry, and register it

* **Domain**: installed artifact + manifest (config). **Files: 2.**
* **Changes**:
  * Create `.github/policies/workflow-policies.md` by rendering
    `templates/policies/workflow-policies.md.tmpl`.
  * Bind the 9 placeholders present in the template:
    `{{TEST_COMMAND}}` = `PYTHONPATH=src python -m unittest discover -s tests`
    (**Q5**); `{{BUILD_CHECK_COMMAND}}` = `pip install -e .` (profile
    `build.command`); `{{DEFAULT_BRANCH}}` = `main`;
    `{{BACKLOG_TOOL_NAME}}` = `backlogit`; `{{BACKLOG_DIRECTORY}}` = `.backlogit`;
    `{{STATUS_DONE}}` = `done`; `{{FEATURE_SHIPMENTS}}` = `true`;
    `{{OP_SHIP_SHIPMENT_MCP}}` = `backlogit_ship_shipment`; `{{DATE}}` =
    install date.
  * Write **LF-only**; append a manifest entry with `path`, `primitive`,
    `template: "policies/workflow-policies.md.tmpl"`, `checksum` (SHA-256 over
    raw LF bytes), and a `note` citing `336F3AB7`.
* **Execution posture**: migration-first — the artifact must exist before U2
  changes what the engine asserts about it.
* **Tests**: covered in U8 (this unit is a render; its own assertion is
  "zero unresolved `{{...}}` and 27 `P-0NN` headings present").

### U2 — Reconcile the policy-registry resolution contradiction

* **Domain**: code. **Files: 1** (`src/autoharness/verify_workspace.py`).
* **Problem being fixed**: the file contains two contradictory contracts about
  the same path.
  * `_resolve_policy_registry` (L4027-L4045) documents *"the dogfood self-install
    **never** installs a policies mirror"* and falls back to the template.
  * `DARK_FACTORY_ASSERTIONS[dark_factory_policy_contract]` (L866) sets
    `required: True` on that exact path.
  * After U1 the first statement becomes **factually false**, so its docstring
    and the assumption it encodes must be corrected or it becomes a stale
    normative surface (family F03a — the very class this program exists to catch).
* **Changes**: correct the docstring to state installed-first precedence with
  template fallback retained for *target* workspaces that legitimately have no
  mirror; keep the fallback branch intact (removing it would break non-mirrored
  installs). No behavior change to the precedence order itself.
* **Execution posture**: characterization-first — capture current resolution
  behavior in a test **before** touching the docstring/branch so the fallback is
  demonstrably preserved.
* **Tests**: 2 scenarios (installed present -> installed wins; installed absent
  + home present -> template wins).

### U3 — Author the missing `python-reviewer` persona template

* **Domain**: template authoring. **Files: 1**
  (`templates/agents/review/python-reviewer.agent.md.tmpl`).
* **Rationale**: this is the only cited persona with no source. Without it,
  R5 cannot close and `plan-review`'s always-on set stays permanently degraded.
* **Shape**: follow the sibling review-persona template contract exactly —
  YAML frontmatter (`name`, `description`, `maturity`, `tools`,
  `max_subagent_tier`, `reasoning_effort`, `model_provider`, `model_family`,
  `subagent_depth`), then a focused rubric. Focus per the `plan-review` Persona
  Rubric Adapter: *"Evaluate proposed Python type signatures, error handling,
  package boundaries, and verification steps."*
* **Decision recorded**: authored as a **fixed `python-reviewer`**, not a
  `{{PRIMARY_LANGUAGE}}`-parameterized template. Reason: the installed skills
  cite the literal filename `python-reviewer.agent.md`; a parameterized template
  would render `<lang>-reviewer.agent.md` and re-dangle the route for every
  non-Python workspace. Generalizing the routing is a separate concern with its
  own blast radius across all stack packs.
* **Tests**: covered by the template-shape assertion in U8.

### U4 — Install the 4 always-on personas

* **Domain**: installed artifacts. **Files: 4.**
* Render into `.github/agents/subagents/`:
  `constitution-reviewer`, `scope-boundary-auditor`, `architecture-strategist`
  (from `templates/agents/review/`), and `learnings-researcher` (from
  `templates/agents/**research**/` — note the different source directory).
* **Execution posture**: mechanical render, LF-only, no hand-patching.

### U5 — Install the 4 security and parity personas

* **Domain**: installed artifacts. **Files: 4.**
* Render `python-reviewer` (from the U3 template), `security-reviewer`,
  `security-lens-reviewer`, `agent-native-parity-reviewer`.
* **Depends on U3.**

### U6 — Install the 3 domain personas, and record the Law-2 exclusion

* **Domain**: installed artifacts. **Files: 3.**
* Render `template-integrity-reviewer`, `schema-cli-docs-coupling-reviewer`,
  `concurrency-reviewer`.
* **Decision recorded in-unit**: `correctness-reviewer`,
  `maintainability-reviewer`, and `technology-reviewer` are **deliberately not
  installed** — no installed skill or agent cites them, and `031-DL` Law 2
  ("no artifact without a named reader") forbids installing an identity nothing
  routes to. The exclusion is recorded, not silent.

### U7 — Register the 11 persona artifacts in the harness manifest

* **Domain**: config. **Files: 1** (`.autoharness/harness-manifest.yaml`).
* One entry per installed persona with `path`, `primitive`, `template`,
  `checksum` (SHA-256 over raw LF bytes), `note` citing `336F3AB7`.
* **Also**: amend the two existing `note` fields at L255 and L265 that declare
  these references DANGLING, since after U4-U6 they resolve. Leaving a stale
  "DANGLING" note is the same stale-normative-surface defect U2 fixes.
* **Depends on U4, U5, U6.**

### U8 — Verification and regression tests

* **Domain**: tests. **Files: <=3** under `tests/`.
* **Scenarios (4)**:
  1. `.github/policies/workflow-policies.md` exists, contains P-001…P-021 and
     the `dark_factory_policy_contract` `must_contain` tokens (`P-017`,
     `Run pipeline in dark mode`, `DARK_MODE_ACTIVE`, `BRAINSTORM_HANDOFF_READY`,
     `DARK_MODE_COMPLETE`), and has **zero unresolved `{{...}}`**.
  2. Every persona path cited by any installed skill/agent under
     `.github/agents/subagents/` **resolves** (route-resolution test — this is
     the direct anti-regression for GAP 2).
  3. The 3 Law-2-excluded personas are **absent**, asserting the exclusion is
     intentional and stays intentional.
  4. `_resolve_policy_registry` precedence (installed-first, template-fallback).
* **Carried-forward finding (recorded, not fixed)**: `workspace-profile.yaml`
  still declares `test.runner: pytest` while Q5 names
  `PYTHONPATH=src python -m unittest discover -s tests` as authoritative. Emit
  this as a documented follow-up, not a code change.
* **Gate command** (Q5): `PYTHONPATH=src python -m unittest discover -s tests`.

## Dependency Graph

```text
U1 ──> U2                     (registry must exist before the engine's contract is reconciled)
U1 ──> U7                     (manifest edits serialize on one file)
U3 ──> U5                     (python-reviewer template before its render)
U4, U5, U6 ──> U7             (all personas installed before registration)
U2, U7 ──> U8                 (verification last)
U4, U6                        (no inbound edge beyond U1's file serialization)
```

Serial order: `U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7 -> U8`.

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| D1 | Render the registry rather than author policy text | The template is the SSOT; authoring here would fork it and create the drift the registry exists to prevent. |
| D2 | Bind `{{TEST_COMMAND}}` from **Q5**, not from `workspace-profile.yaml` | The profile is the stale side of a known F03a ambiguity; Q5 resolved it against `ci.yml` L112. |
| D3 | Keep the template-fallback branch in `_resolve_policy_registry` | Target installs may legitimately have no mirror; deleting the branch would convert a tolerant resolution into a false failure. |
| D4 | `python-reviewer` authored as a fixed, non-parameterized template | Installed skills cite the literal filename; parameterizing re-dangles the route for non-Python workspaces. |
| D5 | Install exactly the 11 **cited** personas; exclude 3 uncited | `031-DL` Law 2. Installing unrouted identities is the write-only-artifact failure mode this program targets. |
| D6 | Amend the stale DANGLING manifest notes in U7 | A note asserting a now-false condition is itself a stale normative surface. |
| D7 | Do not fix `workspace-profile.yaml` in this shipment | It feeds `profile_hash`; changing it has manifest-wide blast radius disproportionate to S0's purpose. |

## Risks and Caveats

| # | Risk | Mitigation |
|---|---|---|
| RK-A | Rendering an 83 KB registry with a wrong variable binding silently publishes a wrong authoritative policy | U8 scenario 1 asserts zero unresolved placeholders **and** the exact `must_contain` token set; D2 pins the one contested binding. |
| RK-B | Installing the registry flips `dark_factory_policy_contract` from missing to *evaluated*, which may surface **new** assertion failures that were previously masked by the missing file | Expected and desirable, but it is a **status-change, not a regression**. U8 runs the targeted check and any newly-surfaced failure is reported as a finding rather than silently patched. |
| RK-C | Manifest checksum computed over CRLF on Windows would mismatch CI | Explicit LF-only + SHA-256-over-raw-LF-bytes contract, matching the existing manifest note convention. |
| RK-D | `learnings-researcher` lives in a different template directory and is missed by a `review/`-only installer | Called out explicitly in U4. |
| RK-E | Installing personas makes `plan-review` dispatch *available*, changing future review behavior mid-programme | This is the intended effect and is what unblocks S2/S10. It changes no exit code and promotes nothing to blocking. |
| RK-F | Scope creep into policy authoring or profile re-discovery | Both named as explicit non-goals with owning follow-ups. |

## Plan Hardening Signals (REQUIRED)

* **Public API, schema, or contract change** — **PRESENT**. `.autoharness/harness-manifest.yaml`
  gains 12 artifact entries and two amended notes; `_resolve_policy_registry`'s
  documented contract changes.
* **Security, auth, permission, or compliance-sensitive behavior** — **PRESENT**.
  The installed registry becomes the authoritative definition surface for
  P-001…P-021, including the destructive-approval and merge-authority policies.
  Security personas become dispatchable.
* **Migration, backfill, destructive data/config action, or irreversible step** —
  **PRESENT**. Creating `.github/policies/` reverses a standing install invariant
  ("the dogfood self-install never installs a policies mirror") and un-masks a
  `required: True` assertion that has been vacuously unevaluated.
* **External integration, operator checkpoint, or external dependency** —
  **PRESENT**. D4 and D5 are operator-visible scoping decisions about which
  persona identities exist in the workspace.
* **High runtime, rollout, or rollback risk** — **ABSENT**. All artifacts are
  additive files under `.github/` and are removable; no runtime code path changes
  behavior, no exit code changes.

**Requires plan hardening: yes**

## Runtime Verification and Closure

* **Runtime surface changed?** No CLI/API/UI surface changes. `verify-workspace`
  *reporting* changes (a previously-missing required assertion becomes
  evaluable). No exit-code semantics change.
* **Runtime verification**: `PYTHONPATH=src python -m unittest discover -s tests`
  (Q5) plus the `verify-workspace` targeted checks
  `dark_factory_policy_contract`, `p013_policy_in_workflow_policies`, and
  `p014_local_review_policy`.
* **Operational closure artifact**: closure record listing the 12 installed
  paths, their checksums, the 3 Law-2 exclusions, the RK-B status-change
  findings (if any), and the two carried-forward items (profile staleness;
  `8AC574F1` residual).
* **Rollback trigger**: if RK-B surfaces assertion failures that cannot be
  resolved as findings, delete `.github/policies/workflow-policies.md` and its
  manifest entry to restore the prior (masked) state; persona installs are
  independently reversible.

---

## Plan Hardening

**Hardening pass — 2026-08-27. Triggered by 4 of 5 signals present (P-006).**

### Risk triggers and protected invariants

| Invariant | Why protected | Guard added |
|---|---|---|
| **INV-1** — The policy registry's *content* is the template's content, unmodified | A hand-edited installed registry forks the SSOT and re-creates the exact drift condition `336F3AB7` reports | U1 is render-only. Verification asserts the rendered body is byte-identical to the template modulo the 9 bound placeholders. **Any diff beyond placeholder substitution fails the unit.** |
| **INV-2** — The template-fallback branch of `_resolve_policy_registry` survives | Target installs without a mirror must keep resolving | U2 is characterization-first: the fallback test is written and passing **before** the docstring/branch is touched |
| **INV-3** — No check is promoted to blocking | `031-DL` D7 / RK4: report-only programmes become enforcing by accretion | U2 changes documentation and precedence commentary only. **No `required` flag, severity, or exit code is edited in this shipment.** Verification asserts exit-code behavior of `verify-workspace` is unchanged. |
| **INV-4** — Law 2 exclusions stay excluded | An unrouted persona is a write-only artifact | U8 scenario 3 asserts absence, so a future accidental install fails a test |
| **INV-5** — Installed artifacts are LF-only and checksum-consistent | CRLF drift silently invalidates every manifest checksum on Windows | Explicit write contract; checksum computed over raw LF bytes |

### Risky actions (ProposedAction / ActionRisk / ActionResult)

| ProposedAction | ActionRisk | Required ActionResult |
|---|---|---|
| Create `.github/policies/workflow-policies.md` (83 KB, new authoritative surface) | **MEDIUM** — un-masks a `required: True` assertion; publishes policy text as authoritative | File present, zero unresolved `{{...}}`, 27 `P-0NN` headings, `must_contain` tokens present, byte-identical to template modulo placeholders |
| Amend two existing manifest `note` fields declaring DANGLING references (L255, L265) | **LOW-MEDIUM** — edits historical install provenance | Notes updated to record resolution **and retain the original gap history**; provenance is amended, never erased |
| Create `.github/agents/subagents/` with 11 identities | **MEDIUM** — makes reviewer dispatch newly available, changing downstream review behavior | All 11 present, every cited route resolves, 3 excluded absent |
| Author a new persona template (U3) | **LOW** — new template in the product surface | Frontmatter valid, no unresolved placeholders, matches sibling contract |
| Touch `verify_workspace.py` (226 KB, high-traffic module) | **MEDIUM** — regression risk in a widely-depended module | Change confined to one function's docstring/comments; characterization tests green before and after |

**Explicitly forbidden in this shipment**: editing policy text; changing any
`required` flag; changing `workspace-profile.yaml`; deleting any manifest note;
installing an uncited persona; promoting any check to blocking; touching
`8AC574F1`'s scope.

### Added verification detail

1. **Pre-flight**: capture `verify-workspace` output **before** U1 so RK-B
   status-changes are attributable rather than guessed.
2. **Placeholder scan**: zero `{{...}}` across all 12 newly installed artifacts,
   not just the registry.
3. **Checksum round-trip**: recompute each manifest checksum from the installed
   file and compare, catching CRLF drift (INV-5).
4. **Exit-code invariance** (INV-3): `verify-workspace` exit-code behavior
   compared pre/post; a change is a **hard stop**, not a finding.
5. **Post-flight diff**: `verify-workspace` after vs. before; every delta
   classified as *expected status-change* or *finding*.

### Rollback and monitoring

* **Rollback order** (reverse dependency): U7 manifest entries -> U6/U5/U4
  persona files -> U3 template -> U2 docstring -> U1 registry. Each step is a
  file deletion or revert; no data migration, nothing irreversible.
* **Rollback trigger**: exit-code invariance broken (INV-3), or RK-B findings
  that cannot be dispositioned as findings within this shipment.
* **Monitoring window**: the next `verify-workspace` run and the next
  `plan-review` invocation — the first consumer that actually dispatches the
  newly installed personas.

### Review-gate capability risk (P-012), carried into plan review

**This plan's own review gate is degraded by the very gap it closes.** The
persona identities `plan-review` routes to (`.github/agents/subagents/*.agent.md`)
do not exist yet, so reviewer **subagent dispatch is genuinely unavailable** —
not skipped, not silently downgraded. Plan review MUST therefore:

* record `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`;
* set `dispatch_mode: single-agent-declared-degradation`;
* cover **every** selected persona inline (a persona may not be dropped because
  dispatch failed); and
* emit literal `dispatch_mode:` and `decision:` markers.

This condition is **expected to disappear after this shipment lands** — S1's
review gate should be able to use real dispatch, and if it still cannot, that is
evidence S0 did not actually close GAP 2.

---

## Plan Review

**Reviewed**: 2026-08-27 · **Plan**: `docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md`

### Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
  — the reviewer identities under `.github/agents/subagents/` do not exist (this
  plan's GAP 2). Probed by direct path existence check; **not** assumed.
* `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
* `TOOL_DEGRADED: agent-intercom — operator visibility reduced`
* `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` — file-based retrieval used.

**Every selected persona was covered inline.** No persona was dropped.

```text
dispatch_mode: single-agent-declared-degradation
```

### Persona findings (P0-P3)

| Persona | Finding | Sev | Disposition |
|---|---|---|---|
| Constitution Reviewer | Plan installs the authoritative P-001…P-021 surface without editing it; no policy is created, weakened, or self-granted. Law 1/Law 2 respected (D5). | — | PASS |
| Constitution Reviewer | INV-3 correctly forbids any `required`-flag or exit-code change, preventing an install from becoming a silent enforcement promotion. | P3 | Accepted as written |
| Python Reviewer | U2 touches a 226 KB module. Characterization-first ordering plus a 2-scenario precedence test is the right minimum; change is docstring/comment-scoped. | P2 | Accepted — mitigated by INV-2 |
| Python Reviewer | U8 asserts a *route-resolution* property (every cited persona path resolves) rather than a hardcoded list — this is the correct anti-regression shape and will not rot as skills change. | — | PASS |
| Scope Boundary Auditor | Profile re-discovery, `8AC574F1`, and policy authoring are all explicitly excluded with named owners. No S1/S2 detector work leaks in. | — | PASS |
| Scope Boundary Auditor | U3 authors a **new** template — genuine scope expansion beyond "install what exists". | P2 | **Justified**: `python-reviewer` is cited by installed skills and has no source; without it R5 cannot close. Bounded to one file with a recorded decision (D4). |
| Learnings Researcher | `docs/compound/012-S-portability-scan-allow-list.md` — new rules over an existing corpus carry historical blast radius. Applies to RK-B: un-masking a required assertion over an existing tree can surface a backlog of failures. | P2 | **Addressed** by hardening step 1 (pre-flight capture) and step 5 (delta classification). |
| Learnings Researcher | `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` — the "defined but not wired" class. Directly analogous: installing persona files without the routes resolving would repeat it. | P2 | **Addressed** by U8 scenario 2, which tests the *route*, not file presence. |
| Architecture Strategist | The plan correctly identifies that GAP 1 has two contradictory in-repo contracts (tolerant `_resolve_policy_registry` vs. `required: True`) and fixes the contradiction rather than only the symptom. | — | PASS (strength) |
| Architecture Strategist | Manifest-file serialization (U1 and U7 both edit `harness-manifest.yaml`) is handled by ordering, not by locking. | P3 | Acceptable — execution is strictly serial (P-001). |
| Agent-Native Parity Reviewer | Installing personas changes agent-facing capability. The plan flags this (RK-E) as intended effect and asserts no exit-code change. | P3 | Accepted |
| Security Lens Reviewer | The installed registry becomes the authoritative text for destructive-approval and merge-authority policies. Because U1 is render-only and content-identical to the template, no policy is silently weakened. | P1 -> mitigated | **Addressed** by INV-1's byte-identity assertion. Without INV-1 this would be a P1 blocker. |
| Security Lens Reviewer | No secrets, credentials, or external trust boundaries are involved. Persona templates are static markdown. | — | PASS |

### Verdict rationale

No P0 findings. The two P1-class concerns (silent policy weakening; masked-assertion
backlog) are both structurally mitigated by hardening invariants that were added
**before** review, not promised as follow-ups. All P2 findings are either
justified in-plan or already addressed by an explicit verification step. Task
granularity is within budget: 8 units, max 4 files each, max 4 test scenarios,
single domain per unit.

```text
decision: PASS
```
