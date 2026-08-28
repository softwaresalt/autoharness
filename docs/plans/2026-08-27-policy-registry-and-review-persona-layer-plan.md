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
  is the sole downstream owner of that entry. **The entry was consumed and
  archived during staging on 2026-08-28T04:14:26Z, before execution begins —
  archival is COMPLETE, not a pending shipment step.** Ship MUST NOT attempt to
  archive it again; a re-archive attempt will fail (`stash get 336F3AB7` already
  returns `not found`) and is not a shipment obligation.
* **Stash disposition traceability (reverse lineage).** `336F3AB7` was archived
  on 2026-08-28T04:14:26Z. The archived record in
  `.backlogit/archive/stash.jsonl` carries only `id`, `priority`, `kind`, `text`,
  `created_at`, `archived_at`, and `reason: "archived"` — it has **no forward
  disposition field**, and backlogit exposes **no official operation to update an
  archived stash entry** (`stash edit`/`stash archive`/`stash get` operate on the
  active stash only; `stash get 336F3AB7` returns `not found`). Rather than
  hand-edit tool-owned state, the lineage is recorded here and is fully
  reconstructible in reverse:

  ```text
  336F3AB7  ->  031-DL (deliberation, done)
            ->  docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md
            ->  148-F (feature, queued)  ->  148.001-T .. 148.008-T
            ->  156-S (shipment, queued)
  ```

  Every one of those artifacts cites `336F3AB7` by ID (this plan's frontmatter
  `source_stash`, `148-F`'s label and description, and the `note` field of each
  manifest entry U1/U7 will write), so the archived entry is reachable from its
  successors even though it cannot point forward at them. **Corroboration**: the
  archived entry's own text independently lists all 12 persona templates under
  `templates/agents/review/` — *including* `technology-reviewer` — which is direct
  primary evidence against the "no `python-reviewer` template exists" premise this
  plan previously carried.
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
* **Measured reference set** actually cited by installed skills and agents, by
  installed path: `agent-native-parity-reviewer`, `architecture-strategist`,
  `concurrency-reviewer`, `constitution-reviewer`, `learnings-researcher`,
  `python-reviewer`, `schema-cli-docs-coupling-reviewer`,
  `scope-boundary-auditor`, `security-lens-reviewer`, `security-reviewer`,
  `template-integrity-reviewer` — **plus a twelfth path-shaped citation that is
  the literal token `{{PRIMARY_LANGUAGE_LOWER}}-reviewer`** (installed
  `install-harness/SKILL.md` L1203). That twelfth citation is *installer
  guidance describing the render mapping*, not a live route, and must be
  expanded or exempted rather than resolved raw (U8 scenario 2).

* **Template availability audit — CORRECTED 2026-08-28.** The prior revision of
  this plan asserted that `python-reviewer` had no template and that three
  templates had no reader. Both claims were wrong; the corrected audit is:

  * All 11 installed identities have a template source. 9 render 1:1 from
    `templates/agents/review/`; `learnings-researcher` renders from
    `templates/agents/**research**/` (different directory; a naive
    `review/`-only installer misses it — RK-D).
  * **`python-reviewer` is a RENDER TARGET, not a missing template.** The
    canonical source is
    `templates/agents/review/technology-reviewer.agent.md.tmpl`, which installed
    `.github/skills/install-harness/SKILL.md` L1203 maps to
    `.github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`.
    `.autoharness/harness-manifest.yaml` L394 binds
    `PRIMARY_LANGUAGE_LOWER: "python"`, so in this workspace that mapping
    renders exactly `python-reviewer.agent.md`. **No new template is required**,
    and authoring a fixed Python-specific duplicate would fork the canonical
    technology-reviewer surface — the precise drift this shipment exists to
    close.
  * **`correctness-reviewer` and `maintainability-reviewer` DO have named
    readers.** They are cited by bare filename rather than by installed path:
    installed `install-harness/SKILL.md` L1200-L1201 designates both
    **"Always-on"**, and installed `tune-harness/SKILL.md` L462-L469 classifies a
    review layer that *lacks* either one as real **local-first review drift**. A
    path-shaped (`.github/agents/subagents/...`) grep cannot see a bare-filename
    citation, which is exactly how the earlier revision mis-classified them as
    unread.
  * **Corrected conclusion: the exclusion set is EMPTY.** All 12
    `templates/agents/review/` templates plus `learnings-researcher` are
    installed, yielding **13 persona artifacts** (14 installed artifacts total,
    including the policy registry).

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
| R4 | GAP 2: `python-reviewer` route must resolve | Render the **existing** `technology-reviewer` template through the installed L1203 mapping to `python-reviewer.agent.md`; author nothing new | **U3** (mapping), **U5** (render) |
| R5 | GAP 2: install the cited persona identities | Render 13 personas -> `.github/agents/subagents/` | **U4, U5, U6** |
| R6 | Installed artifacts must be manifest-tracked with checksums | Register 13 persona artifacts | **U7** |
| R7 | `031-DL` Law 2 — no artifact without a reader | Verify every installed persona has a named reader (installed path citation **or** bare-filename citation in the install/tune drift contract). Corrected result: **all 13 qualify; the exclusion set is empty** | **U6** (decision), **U8** (assert) |
| R8 | Verification that both gaps are closed | Targeted `verify-workspace` checks + placeholder scan + route-resolution test with declared placeholder handling | **U8** |
| R9 | Stale manifest DANGLING notes must not survive the conditions they assert | Reconcile **all three** notes (L255, L265, **L275**) | **U7** |

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
* **No installation of persona templates that have no reader** (Law 2). After the
  corrected audit this set is **empty**, so nothing is excluded on these grounds —
  but the Law-2 test in U8 stays, so a future unread template cannot be installed
  silently.
* **No authoring of a Python-specific reviewer template.** `python-reviewer` is a
  render target of the existing `technology-reviewer` template; duplicating it
  would fork the canonical surface.
* **No generalization of persona routing.** Installed skills cite the literal
  `python-reviewer.agent.md`; making every citation language-parameterized is a
  separate change with blast radius across all stack packs.
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

### U3 — Resolve and pin the `technology-reviewer` -> `python-reviewer` render mapping

* **Domain**: render mapping + recorded decision. **Files: 0 new templates.**
* **Rationale (CORRECTED)**: the earlier revision of this plan claimed
  `python-reviewer` had no template and scheduled authoring a new one. That was a
  false premise. `templates/agents/review/technology-reviewer.agent.md.tmpl`
  **already exists** and is the canonical source; installed
  `.github/skills/install-harness/SKILL.md` L1203 declares the mapping
  `technology-reviewer.agent.md` ->
  `.github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`.
* **Work**:
  * Confirm `PRIMARY_LANGUAGE_LOWER` resolves to `python` from
    `.autoharness/harness-manifest.yaml` L394 (cross-check
    `workspace-profile.yaml` `languages.primary: "python"`).
  * Enumerate `technology-reviewer.agent.md.tmpl`'s placeholders and pin each
    binding so U5's render is mechanical and reviewable.
  * **Extended 2026-08-28 (P2-2)**: also pin `{{CONCURRENCY_PATTERNS}}` for
    `concurrency-reviewer.agent.md.tmpl`, which U6 renders. U3 is now the
    **single binding-pin unit for every synthesized persona variable in S0**,
    regardless of which unit performs the render.
  * Record the corrected decision **D4** below, and new decision **D8**.

#### D8 — Pinned bindings for the 5 synthesized persona variables (added 2026-08-28)

**The defect this closes.** Five placeholders in the S0 persona set are classed
by installed `install-harness/SKILL.md` L329-L333 as *"Synthesized from language
… model"* — i.e. the installer is expected to **invent** their content. A
"mechanical render" instruction over a synthesized placeholder is a
contradiction: Ship would either emit unresolved `{{...}}` (failing the U8
placeholder scan and the INV-1/DoD zero-placeholder rule) or improvise
**unreviewed persona content** into a normative review surface. Both are
unacceptable. All five are therefore **pinned here, with a reviewed in-repo
derivation, before any render occurs.**

| # | Variable | Template | Pinned value | Derivation (reviewed, in-repo) |
|---|---|---|---|---|
| 1 | `{{CONCURRENCY_PATTERNS}}` | `concurrency-reviewer.agent.md.tmpl` L31 | `asyncio, task, queue, thread, process` | **Code-backed, deterministic.** `src/autoharness/verify_workspace.py` `_language_defaults("python")["concurrency_patterns"]` (L2200), wired by `variables.setdefault("CONCURRENCY_PATTERNS", language_defaults["concurrency_patterns"])` (L2885). **Not synthesized** — copied verbatim from the shipped resolver. |
| 2 | `{{LANGUAGE_SAFETY_CHECKS}}` | `technology-reviewer.agent.md.tmpl` L21 | see D8-B below | `_language_defaults("python")` `unsafe_policy` + `lint_policy` (L2196-L2197), plus `constitution.instructions.md` §I *Safety-First Python*. |
| 3 | `{{LANGUAGE_IDIOM_CHECKS}}` | `technology-reviewer.agent.md.tmpl` L25 | see D8-B below | `_language_defaults("python")` `naming_conventions` + `documentation_conventions` (L2199-L2200), plus `constitution.instructions.md` §I (prefer stdlib / existing project dependencies). |
| 4 | `{{LANGUAGE_ERROR_HANDLING_CHECKS}}` | `technology-reviewer.agent.md.tmpl` L29 | see D8-B below | `_language_defaults("python")` `error_handling_policy` + `error_handling_conventions` + `error_pattern` (`raise/except`), plus `constitution.instructions.md` §I *"Explicit error handling is required; silent failures are forbidden."* |
| 5 | `{{LANGUAGE_PERFORMANCE_CHECKS}}` | `technology-reviewer.agent.md.tmpl` L33 | see D8-B below | **Weakest derivation — see RK-J.** `_language_defaults` has **no** `performance` key, so there is no language-model source. Derived instead from `constitution.instructions.md` §X *Agent Context Efficiency* and §I (prefer the standard library and existing project dependencies). |

**D8-A — Binding #1 is a copy, not a judgement.** `{{CONCURRENCY_PATTERNS}}`
already has a shipped, reviewed resolver. Ship MUST bind the literal
`asyncio, task, queue, thread, process` and MUST NOT re-synthesize it. If the
value read from `_language_defaults` at execution time differs from this pin,
that is a **hard stop** for U3 (the resolver changed under the plan), not a
licence to improvise.

**D8-B — Bindings #2-#5 are pinned to this exact reviewed content.** Each is a
Markdown bullet list rendered verbatim into the corresponding section. This
content is reviewed here, in the plan, so that U5's render stays mechanical:

```text
{{LANGUAGE_SAFETY_CHECKS}}
* Prefer typed, explicit Python over dynamic shortcuts that hide failure modes.
* Silent failures are forbidden; every failure path must be explicit and observable.
* Prefer the standard library and existing project dependencies over new ones.
* Lint and format failures block the change until corrected.

{{LANGUAGE_IDIOM_CHECKS}}
* Use snake_case for modules, functions, and variables; PascalCase for classes.
* Use docstrings for public modules, classes, and functions.
* Prefer standard-library constructs over hand-rolled equivalents.
* Keep each module to a single responsibility.

{{LANGUAGE_ERROR_HANDLING_CHECKS}}
* Raise specific exceptions and handle them at clear boundaries.
* Use explicit exceptions with contextual messages; avoid bare `except` blocks.
* Do not swallow exceptions — a caught exception must be handled, re-raised, or logged with context.
* Preserve the original error context when wrapping or re-raising.

{{LANGUAGE_PERFORMANCE_CHECKS}}
* Return minimal, targeted data; avoid bulk file reads or directory scans where a structured query suffices.
* Prefer a structured query over directory scanning when both are available.
* Avoid repeated I/O or re-parsing inside loops; read once and reuse.
* Flag unbounded in-memory accumulation over workspace-sized inputs.
```

**D8-C — Technology-agnostic template discipline is preserved.** These values are
bound at **render time into installed artifacts**; the templates
`technology-reviewer.agent.md.tmpl` and `concurrency-reviewer.agent.md.tmpl`
**keep their placeholders unchanged** and remain language-neutral. **No template
file is edited by U3, U5, or U6.** Hard-coding Python content into a `.tmpl` is
forbidden — this is the exact defect already recorded at
`verify_workspace.py` L2172-L2180 (the generic `error_pattern` fallback comment).

**D8-D — Scope of the pin.** These five are the **complete** set of unbound
synthesized variables across the 13 S0 personas. `{{PRIMARY_LANGUAGE}}`,
`{{PRIMARY_LANGUAGE_LOWER}}`, `{{TIER_1_FAMILY}}`, `{{TIER_1_PROVIDER}}`, and
`{{TIER_1_REASONING_EFFORT}}` are already manifest/config-bound and need no pin.
`{{file_path}}` and `{{line_number}}` are **JSON output-schema exemplars inside a
fenced code block**, not render variables — they are intended to survive into the
installed artifact literally. **U8's zero-`{{...}}` placeholder scan MUST exempt
fenced-code-block output exemplars by a named rule, or it will false-positive on
every persona.** (This is a distinct exemption from U8 scenario 2's route
exemption; do not conflate the three.)

* **Explicitly NOT done here**: authoring
  `templates/agents/review/python-reviewer.agent.md.tmpl`. Creating a fixed
  Python-specific duplicate of an existing generic template is forbidden in this
  shipment. Likewise, **editing any `.tmpl` to inline the D8 values is forbidden**.
* **Tests**: the mapping is asserted by U8 scenario 2 (route resolution) and
  scenario 3 (rendered-from-technology-reviewer provenance); the D8 pins are
  asserted by U8 scenario 5 (added 2026-08-28).

### U4 — Install the 4 always-on personas

* **Domain**: installed artifacts. **Files: 4.**
* Render into `.github/agents/subagents/`:
  `constitution-reviewer`, `scope-boundary-auditor`, `architecture-strategist`
  (from `templates/agents/review/`), and `learnings-researcher` (from
  `templates/agents/**research**/` — note the different source directory).
* **Execution posture**: mechanical render, LF-only, no hand-patching.

### U5 — Install the 4 security and parity personas

* **Domain**: installed artifacts. **Files: 4.**
* Render `python-reviewer` (**from the existing
  `templates/agents/review/technology-reviewer.agent.md.tmpl`**, per the U3
  mapping), `security-reviewer`, `security-lens-reviewer`,
  `agent-native-parity-reviewer`.
* **Depends on U3** (mapping pinned before the render, not template authoring).
* **Binding contract (added 2026-08-28, P2-2)**: the `python-reviewer` render
  MUST bind `{{LANGUAGE_SAFETY_CHECKS}}`, `{{LANGUAGE_IDIOM_CHECKS}}`,
  `{{LANGUAGE_ERROR_HANDLING_CHECKS}}`, and `{{LANGUAGE_PERFORMANCE_CHECKS}}` to
  the **verbatim D8-B values**. Ship MUST NOT synthesize, paraphrase, extend, or
  reorder them, and MUST NOT emit them unresolved. Any deviation is a hard stop.

### U6 — Install the 3 domain personas and the 2 always-on personas, and record the Law-2 result

* **Domain**: installed artifacts. **Files: 5.**
* Render `template-integrity-reviewer`, `schema-cli-docs-coupling-reviewer`,
  `concurrency-reviewer`, and — **added by the 2026-08-28 correction** —
  `correctness-reviewer` and `maintainability-reviewer`.
* **Why the two additions belong in S0.** S0's stated purpose is to *restore the
  review-persona layer*. Installed `install-harness/SKILL.md` L1200-L1201
  designates `correctness-reviewer` and `maintainability-reviewer` **"Always-on"**,
  and installed `tune-harness/SKILL.md` L462-L469 classifies a review layer that
  lacks either one as real **local-first review drift**. Shipping S0 without them
  would leave the layer in a state the workspace's own installed drift contract
  reports as drifted — i.e. S0 would not have closed GAP 2.
* **Decision D5 recorded in-unit — the Law-2 result is now an EMPTY exclusion
  set.** The earlier revision excluded `correctness-reviewer`,
  `maintainability-reviewer`, and `technology-reviewer` as "uncited". All three
  classifications were wrong:
  * `technology-reviewer` is not a separate identity to exclude — it is the
    **source template** for the installed `python-reviewer.agent.md` (U3/U5).
  * `correctness-reviewer` and `maintainability-reviewer` are cited by **bare
    filename** in the install/tune drift contract, which a path-shaped grep
    cannot see.
  * Law 2 ("no artifact without a named reader") is therefore **satisfied** by
    all 13 installed personas, not violated.
* **Execution posture**: mechanical render, LF-only, no hand-patching.
* **Binding contract (added 2026-08-28, P2-2)**: the `concurrency-reviewer`
  render MUST bind `{{CONCURRENCY_PATTERNS}}` to the verbatim D8 pin
  `asyncio, task, queue, thread, process`. Ship MUST NOT synthesize it and MUST
  NOT emit it unresolved. **U6 therefore now depends on U3** — the pin must exist
  before the render. This edge did not exist before the correction.

### U7 — Register the 13 persona artifacts and reconcile the three stale DANGLING notes

* **Domain**: config. **Files: 1** (`.autoharness/harness-manifest.yaml`).
* One entry per installed persona with `path`, `primitive`, `template`,
  `checksum` (SHA-256 over raw LF bytes), `note` citing `336F3AB7`.
  * The `python-reviewer.agent.md` entry records
    `template: "agents/review/technology-reviewer.agent.md.tmpl"` — the installed
    filename and its template basename intentionally differ, per the L1203
    mapping. A future checksum/provenance check must not treat that as drift.
* **Also — reconcile ALL THREE stale DANGLING notes** (the earlier revision
  named only two):
  1. **L255** (`plan-review/SKILL.md`) — declares seven personas NOT installed.
     Resolved by U4-U6.
  2. **L265** (`review/SKILL.md`) — declares `security-reviewer`,
     `template-integrity-reviewer`, `schema-cli-docs-coupling-reviewer` NOT
     installed. Resolved by U4-U6.
  3. **L275** (`shipment-reconcile/SKILL.md`) — **added by the 2026-08-28
     correction.** Its `DANGLING (partial, narrowed)` note states that the
     `.github/policies/workflow-policies.md` citation *"remains dangling — the
     policy registry layer is a separate, still-open install gap tracked by stash
     336F3AB7."* **U1 installs that exact file, and `336F3AB7` was ALREADY
     ARCHIVED during staging (2026-08-28T04:14:26Z) — so the stash half of that
     sentence is false as of now, and the registry half becomes false the moment
     U1 lands.** Both halves must be reconciled. **No archive action is required
     of Ship.**
     Leaving it is the same stale-normative-surface defect U2 fixes.
* **Provenance is amended, never erased**: each note records the resolution AND
  retains the original gap history.
* **Depends on U1** (the registry entry and the L275 note both live in this file,
  and L275 cannot be truthfully reconciled until U1 has installed the registry),
  **and on U4, U5, U6** (register once over a complete persona set).

### U8 — Verification and regression tests

* **Domain**: tests. **Files: <=3** under `tests/`.
* **Scenarios (4)**:
  1. `.github/policies/workflow-policies.md` exists, contains P-001…P-021 and
     the `dark_factory_policy_contract` `must_contain` tokens (`P-017`,
     `Run pipeline in dark mode`, `DARK_MODE_ACTIVE`, `BRAINSTORM_HANDOFF_READY`,
     `DARK_MODE_COMPLETE`), and has **zero unresolved `{{...}}`**.
  2. **Route-resolution test with declared placeholder handling.** Every persona
     path cited by any installed skill/agent under `.github/agents/subagents/`
     **resolves**. This is a *property* test, not a hardcoded list, so it will not
     rot as skills change — but the raw citation scan also yields the literal
     token `.github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`
     from installed `install-harness/SKILL.md` L1203, which **can never resolve as
     a raw path**. The test MUST therefore do one of the following, explicitly and
     by name — asserting raw resolution of a placeholder path is an impossible
     assertion and is forbidden:
     * **(preferred) EXPAND**: substitute `{{PRIMARY_LANGUAGE_LOWER}}` from
       `.autoharness/harness-manifest.yaml` `variables.PRIMARY_LANGUAGE_LOWER`
       (= `python`) before resolving, so the citation resolves to the real
       installed `python-reviewer.agent.md`. This is stronger because it also
       proves the L1203 mapping itself is satisfied.
     * **(fallback) EXEMPT**: skip citations containing an unexpanded `{{...}}`
       segment via a named, commented allow-rule identifying them as installer
       guidance rather than live routes.
     Whichever branch is taken, the test records which one and why; a silent
     regex that happens to miss the token is not acceptable.
  3. **Law-2 / provenance test (INVERTED by the 2026-08-28 correction).** The
     earlier revision asserted three personas were ABSENT. That assertion is now
     wrong and must not be written — it would fail against the corrected S0 and
     would re-encode the false premise as a permanent regression test. Assert
     instead:
     * every installed persona under `.github/agents/subagents/` has a **named
       reader** — an installed-path citation **or** a bare-filename citation in
       the install/tune drift contract;
     * `correctness-reviewer.agent.md` and `maintainability-reviewer.agent.md`
       are **PRESENT**, so the `tune-harness` L462-L469 local-first review drift
       condition does not trigger;
     * `python-reviewer.agent.md` is present and its manifest entry records
       `technology-reviewer.agent.md.tmpl` as its template source.
  4. `_resolve_policy_registry` precedence (installed-first, template-fallback).
  5. **Pinned-binding conformance (ADDED 2026-08-28, P2-2).** For each of the five
     D8 variables, assert the **installed** artifact contains the pinned value
     **verbatim** and contains no residual placeholder token:
     * `python-reviewer.agent.md` carries the D8-B `{{LANGUAGE_SAFETY_CHECKS}}`,
       `{{LANGUAGE_IDIOM_CHECKS}}`, `{{LANGUAGE_ERROR_HANDLING_CHECKS}}`, and
       `{{LANGUAGE_PERFORMANCE_CHECKS}}` bullet lists exactly as recorded in D8-B;
     * `concurrency-reviewer.agent.md` carries
       `asyncio, task, queue, thread, process`, and that string equals
       `_language_defaults("python")["concurrency_patterns"]` read at test time
       (**cross-check assertion** — it fails if the resolver and the pin diverge);
     * the source templates `technology-reviewer.agent.md.tmpl` and
       `concurrency-reviewer.agent.md.tmpl` **still contain their five
       placeholders unmodified** (D8-C: proves no template was hard-coded).
     This scenario is what prevents unreviewed persona content from reaching a
     normative review surface. A render that merely "looks reasonable" fails it.
* **Placeholder-scan exemption (ADDED 2026-08-28, D8-D)**: the zero-`{{...}}`
  scan MUST exempt **fenced-code-block output-schema exemplars** (`{{file_path}}`,
  `{{line_number}}`) by a named, commented rule. These are intended literal
  content of the installed persona, not unbound variables. This is a **third,
  distinct** exemption — do not conflate it with scenario 2's route exemption or
  apply either to real unbound variables.
* **Carried-forward finding (recorded, not fixed)**: `workspace-profile.yaml`
  still declares `test.runner: pytest` while Q5 names
  `PYTHONPATH=src python -m unittest discover -s tests` as authoritative. Emit
  this as a documented follow-up, not a code change.
* **Gate command** (Q5): `PYTHONPATH=src python -m unittest discover -s tests`.

## Dependency Graph

```text
U1 ──> U2                     (registry must exist before the engine's contract is reconciled)
U1 ──> U7                     (manifest edits serialize on one file; and the L275 note cannot be
                               truthfully reconciled until U1 has installed the registry)
U3 ──> U5                     (technology-reviewer -> python-reviewer mapping + D8-B bindings
                               pinned before its render)
U3 ──> U6                     (ADDED 2026-08-28: the D8 {{CONCURRENCY_PATTERNS}} pin must exist
                               before concurrency-reviewer is rendered)
U4, U5, U6 ──> U7             (all personas installed before registration)
U2, U7 ──> U8                 (verification last)
U4                            (no inbound edge beyond U1's file serialization)
```

Serial order: `U1 -> U2 -> U3 -> U4 -> U5 -> U6 -> U7 -> U8`.

## Decisions and Rationale

| # | Decision | Rationale |
|---|---|---|
| D1 | Render the registry rather than author policy text | The template is the SSOT; authoring here would fork it and create the drift the registry exists to prevent. |
| D2 | Bind `{{TEST_COMMAND}}` from **Q5**, not from `workspace-profile.yaml` | The profile is the stale side of a known F03a ambiguity; Q5 resolved it against `ci.yml` L112. |
| D3 | Keep the template-fallback branch in `_resolve_policy_registry` | Target installs may legitimately have no mirror; deleting the branch would convert a tolerant resolution into a false failure. |
| D4 | `python-reviewer` is **rendered from the existing `technology-reviewer` template**, not authored as a new fixed template | **Corrected 2026-08-28.** The prior D4 rested on a false premise (no template exists). `templates/agents/review/technology-reviewer.agent.md.tmpl` exists and installed `install-harness/SKILL.md` L1203 already maps it to `{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md` = `python-reviewer.agent.md` here. Authoring a Python-specific duplicate would fork the canonical surface and create the drift this shipment closes. Routing generalization remains out of scope. |
| D5 | Install **all 13** personas; the Law-2 exclusion set is **empty** | **Corrected 2026-08-28.** `technology-reviewer` is a source template, not a separate identity; `correctness-reviewer` and `maintainability-reviewer` are cited by bare filename in `install-harness` L1200-L1201 ("Always-on") and `tune-harness` L462-L469 (local-first review drift). Law 2 is satisfied by all 13. U8 scenario 3 now asserts *reader existence*, not absence. |
| D6 | Reconcile **all three** stale DANGLING manifest notes in U7 (L255, L265, L275) | **Corrected 2026-08-28.** A note asserting a now-false condition is itself a stale normative surface. L275 was missed by the earlier revision: installing the registry (U1) falsifies its registry claim, and `336F3AB7` **was already archived during staging (2026-08-28T04:14:26Z)**, which falsifies its stash claim as of now. Ship reconciles the note; Ship does **not** archive the stash. |
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
| RK-G | The persona citation scan yields the literal `{{PRIMARY_LANGUAGE_LOWER}}-reviewer` token, which cannot resolve as a raw path; a naive route-resolution test either fails permanently or is silently weakened to pass | U8 scenario 2 requires an explicit, named EXPAND (preferred) or EXEMPT branch and records which was used. A silent regex miss is called out as unacceptable. |
| RK-H | **Premise risk (realized once already).** A path-shaped grep cannot see bare-filename citations, and a template whose render target is renamed by a mapping looks "missing" under a filename search. Both produced false conclusions in the prior revision of this plan. | The audit is now cited to primary evidence with file+line (`install-harness` L1200-L1203, `tune-harness` L462-L469, `harness-manifest` L394), and U8 scenario 3 tests reader existence rather than a frozen exclusion list. |
| RK-I | `python-reviewer.agent.md` installs from a template with a different basename (`technology-reviewer.agent.md.tmpl`); a provenance or checksum check assuming name equality misreads this as drift | U7 records the template source explicitly in the manifest entry; U8 scenario 3 asserts the mapping. |
| RK-J | **Unbound synthesized persona content (2026-08-28, P2-2).** Five placeholders are classed by `install-harness/SKILL.md` L329-L333 as *"Synthesized from language … model"*. A "mechanical render" over a synthesized placeholder would force Ship either to emit unresolved `{{...}}` or to **improvise unreviewed persona content into a normative review surface**. `{{LANGUAGE_PERFORMANCE_CHECKS}}` is the weakest case: `_language_defaults` has **no** performance key, so no language-model source exists at all. | All five pinned verbatim in **D8/D8-B** with a reviewed in-repo derivation, before any render. U5/U6 carry an explicit verbatim-binding contract; U8 scenario 5 asserts conformance and cross-checks the concurrency pin against the live resolver. **Residual**: the #2-#5 wording is Stage-reviewed prose, not code-derived — it is authoritative *for this shipment only*, and a follow-up should add `safety/idiom/error/performance_checks` keys to `_language_defaults` so a future render derives them deterministically. Out of S0 scope (would change the resolver, blast radius beyond the persona layer). |
| RK-K | **Superseded resolved checkpoint cannot be amended (2026-08-28, P3).** Resolved checkpoint `checkpoint-20260828-041509.json` records the pre-correction S0 state (false `python-reviewer` template premise, 11-persona set). backlogit exposes **no official amendment path for a resolved checkpoint** — `backlogit_create_checkpoint` only creates, `backlogit_resolve_checkpoint` only resolves. | **Accepted bounded residual risk.** Hand-editing tool-owned state is forbidden, so the stale checkpoint is left byte-intact. Containment: (a) it is **resolved**, so the recovery protocol's candidate scan (active-only) will never select it; (b) the superseding checkpoint names it in `supersedes_checkpoint`; (c) the correction is recorded in `docs/memory/2026-08-28-stage-156s-blocked-review-repair.md` and in this plan. **Bound**: the only exposure is an operator reading the resolved checkpoint directly and out of context. Not a gate on execution. |

## Plan Hardening Signals (REQUIRED)

* **Public API, schema, or contract change** — **PRESENT**. `.autoharness/harness-manifest.yaml`
  gains 14 artifact entries and three reconciled notes; `_resolve_policy_registry`'s
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
* **Operational closure artifact**: closure record listing the 14 installed
  paths, their checksums, the **empty** Law-2 exclusion set (with the corrected
  reader evidence for `correctness-reviewer`, `maintainability-reviewer`, and the
  `technology-reviewer` -> `python-reviewer` mapping), the three reconciled
  DANGLING notes, the RK-B status-change
  findings (if any), and the two carried-forward items (profile staleness;
  `8AC574F1` residual).
* **Rollback trigger**: if RK-B surfaces assertion failures that cannot be
  resolved as findings, delete `.github/policies/workflow-policies.md` and its
  manifest entry to restore the prior (masked) state; persona installs are
  independently reversible.

---

## Plan Hardening

**Hardening pass — 2026-08-27. Triggered by 4 of 5 signals present (P-006).**
**Re-hardened 2026-08-28** after the current-HEAD local review of `1bafd85e`
returned BLOCKED (P0=0, P1=1, P2=6, P3=2). The P1 was a false premise about
`python-reviewer`; INV-4, the risky-actions table, the forbidden list, and RK-G
through RK-I were revised accordingly. Signal count is unchanged at 4 of 5 —
the corrections narrow scope (one fewer authored template) while widening the
installed set (11 -> 13 personas), so hardening remains required.

### Risk triggers and protected invariants

| Invariant | Why protected | Guard added |
|---|---|---|
| **INV-1** — The policy registry's *content* is the template's content, unmodified | A hand-edited installed registry forks the SSOT and re-creates the exact drift condition `336F3AB7` reports | U1 is render-only. Verification asserts the rendered body is byte-identical to the template modulo the 9 bound placeholders. **Any diff beyond placeholder substitution fails the unit.** |
| **INV-2** — The template-fallback branch of `_resolve_policy_registry` survives | Target installs without a mirror must keep resolving | U2 is characterization-first: the fallback test is written and passing **before** the docstring/branch is touched |
| **INV-3** — No check is promoted to blocking | `031-DL` D7 / RK4: report-only programmes become enforcing by accretion | U2 changes documentation and precedence commentary only. **No `required` flag, severity, or exit code is edited in this shipment.** Verification asserts exit-code behavior of `verify-workspace` is unchanged. |
| **INV-4** — Every installed persona has a named reader | An unread persona is a write-only artifact; but "unread" must be measured correctly, by installed-path **and** bare-filename citation | U8 scenario 3 asserts *reader existence* for each installed persona (not absence of a fixed list), so a genuinely unread future install still fails a test — without re-encoding the falsified "3 excluded" premise |
| **INV-5** — Installed artifacts are LF-only and checksum-consistent | CRLF drift silently invalidates every manifest checksum on Windows | Explicit write contract; checksum computed over raw LF bytes |

### Risky actions (ProposedAction / ActionRisk / ActionResult)

| ProposedAction | ActionRisk | Required ActionResult |
|---|---|---|
| Create `.github/policies/workflow-policies.md` (83 KB, new authoritative surface) | **MEDIUM** — un-masks a `required: True` assertion; publishes policy text as authoritative | File present, zero unresolved `{{...}}`, 27 `P-0NN` headings, `must_contain` tokens present, byte-identical to template modulo placeholders |
| Amend the three existing manifest `note` fields declaring DANGLING references (L255, L265, L275) | **LOW-MEDIUM** — edits historical install provenance | Notes updated to record resolution **and retain the original gap history**; provenance is amended, never erased |
| Create `.github/agents/subagents/` with 13 identities | **MEDIUM** — makes reviewer dispatch newly available, changing downstream review behavior | All 13 present, every cited route resolves (with `{{PRIMARY_LANGUAGE_LOWER}}` expanded or exempted by a named rule), every installed persona has a named reader |
| Render `python-reviewer.agent.md` from `technology-reviewer.agent.md.tmpl` (installed filename differs from template basename) | **LOW-MEDIUM** — a provenance check that assumes name equality could misread this as drift | Manifest entry records the template source explicitly; U8 scenario 3 asserts the mapping |
| Touch `verify_workspace.py` (226 KB, high-traffic module) | **MEDIUM** — regression risk in a widely-depended module | Change confined to one function's docstring/comments; characterization tests green before and after |

**Explicitly forbidden in this shipment**: editing policy text; changing any
`required` flag; changing `workspace-profile.yaml`; deleting any manifest note;
installing a persona that has no named reader; **authoring a Python-specific
duplicate of the existing `technology-reviewer` template**; **writing a test that
asserts raw resolution of a `{{...}}` placeholder path**; **asserting the absence
of `correctness-reviewer` or `maintainability-reviewer`**; promoting any check to
blocking; touching `8AC574F1`'s scope.

### Added verification detail

1. **Pre-flight**: capture `verify-workspace` output **before** U1 so RK-B
   status-changes are attributable rather than guessed.
2. **Placeholder scan**: zero `{{...}}` across all 14 newly installed artifacts,
   not just the registry.
3. **Checksum round-trip**: recompute each manifest checksum from the installed
   file and compare, catching CRLF drift (INV-5).
4. **Exit-code invariance** (INV-3): `verify-workspace` exit-code behavior
   compared pre/post; a change is a **hard stop**, not a finding.
5. **Post-flight diff**: `verify-workspace` after vs. before; every delta
   classified as *expected status-change* or *finding*.

### Rollback and monitoring

* **Rollback order** (reverse dependency): U7 manifest entries -> U6/U5/U4
  persona files -> ~~U3 template~~ **U3 pinned-bindings record** -> U2 docstring
  -> U1 registry. Each step is a file deletion or revert; no data migration,
  nothing irreversible.
  * **Corrected 2026-08-28 (P3):** the step formerly labelled *"U3 template"* was
    obsolete. **U3 creates no template and writes no file** — it produces the
    render-mapping and D8 binding pins recorded in this plan and in the closure
    record. There is consequently **nothing to delete or revert for U3**; the step
    is retained in the ordering only as a no-op placeholder so the reverse-dependency
    sequence stays readable. Ship MUST NOT look for, or attempt to remove, a
    `templates/agents/review/python-reviewer.agent.md.tmpl` during rollback —
    it never existed and is forbidden to create.
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

**Reviewed**: 2026-08-28 (re-review after correction) · **Supersedes**: the
2026-08-27 review below · **Plan**: `docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md`

### Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
  — the reviewer identities under `.github/agents/subagents/` still do not exist
  (this plan's GAP 2 is not yet shipped). Re-probed by direct path existence check
  on 2026-08-28; **not** assumed. `.github/agents/subagents` is absent.
* `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
* `TOOL_DEGRADED: agent-intercom — operator visibility reduced`
* `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` — file-based retrieval used.

**Every selected persona was covered inline.** No persona was dropped.

```text
dispatch_mode: single-agent-declared-degradation
```

### Correction verification (2026-08-28)

Each finding from the BLOCKED review of `1bafd85e` was re-checked against primary
evidence before re-scoring:

| Finding | Primary evidence re-checked | Status |
|---|---|---|
| P1 — false `python-reviewer` premise | `templates/agents/review/technology-reviewer.agent.md.tmpl` exists; `install-harness/SKILL.md` L1203 maps it to `.github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`; `harness-manifest.yaml` L394 binds `python` | **Corrected** — U3 repurposed to mapping, U5 renders from the existing template, no new template authored |
| P2.2 — missing `U7 -> U1` edge | Both units write `.autoharness/harness-manifest.yaml`; L275 depends on U1's install | **Corrected** — edge added and read back |
| P2.3 — only 2 of 3 DANGLING notes reconciled | Manifest L275 asserts `.github/policies/workflow-policies.md` still dangling and `336F3AB7` still open; U1 installs that file, and that stash was already archived during staging | **Corrected** — U7 now reconciles L255, L265, L275 |
| P2.4 — impossible raw-path assertion | Citation scan emits the literal `{{PRIMARY_LANGUAGE_LOWER}}-reviewer` token | **Corrected** — U8 scenario 2 requires a named EXPAND or EXEMPT branch |
| P2.5 — correctness/maintainability wrongly excluded | `install-harness` L1200-L1201 ("Always-on"); `tune-harness` L462-L469 (local-first review drift) | **Corrected** — both installed in U6; exclusion set now empty |

### Persona findings (P0-P3)

| Persona | Finding | Sev | Disposition |
|---|---|---|---|
| Constitution Reviewer | Plan installs the authoritative P-001…P-021 surface without editing it; no policy is created, weakened, or self-granted. Law 1 respected. | — | PASS |
| Constitution Reviewer | Law 2 is now *satisfied by measurement* rather than by an asserted exclusion list. The corrected reading (bare-filename citations count as readers) is the stronger one — it prevents a real reader from being ignored because of grep shape. | — | PASS (strength) |
| Constitution Reviewer | INV-3 still forbids any `required`-flag or exit-code change, so widening the install set does not become a silent enforcement promotion. | P3 | Accepted as written |
| Python Reviewer | U2 touches a 226 KB module. Characterization-first ordering plus a 2-scenario precedence test is the right minimum; change is docstring/comment-scoped. | P2 | Accepted — mitigated by INV-2 |
| Python Reviewer | U8 scenario 2 now asserts a *route-resolution property* with an explicit placeholder-handling branch. The preferred EXPAND branch is strictly stronger than an exemption because it also proves the L1203 mapping holds. | — | PASS |
| Python Reviewer | `python-reviewer.agent.md` installs from a differently-named template. Recording the template source in the manifest entry (U7) is required or a provenance check misreads it as drift. | P2 | **Addressed** — RK-I plus an explicit U7 acceptance item |
| Scope Boundary Auditor | The prior P2 "U3 authors a new template" scope expansion is **withdrawn** — U3 no longer authors anything. Net scope is *narrower* on the template surface. | — | Resolved |
| Scope Boundary Auditor | U6 grows from 3 to 5 renders by adding `correctness-reviewer` and `maintainability-reviewer`. This is scope *widening*. | P2 | **Justified**: S0's stated purpose is restoring the review-persona layer, and the workspace's own installed `tune-harness` drift contract (L462-L469) reports the layer as drifted without them. Excluding them would mean S0 does not close GAP 2. Renders are mechanical; U6 stays well inside the 2-hour rule. |
| Scope Boundary Auditor | Profile re-discovery, `8AC574F1`, policy authoring, and routing generalization all remain explicitly excluded with named owners. No S1 detector work leaks in. | — | PASS |
| Learnings Researcher | `docs/compound/012-S-portability-scan-allow-list.md` — new rules over an existing corpus carry historical blast radius. Applies to RK-B. | P2 | **Addressed** by hardening step 1 (pre-flight capture) and step 5 (delta classification). |
| Learnings Researcher | `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` — the "defined but not wired" class. Installing persona files without the routes resolving would repeat it. | P2 | **Addressed** by U8 scenario 2, which tests the *route*, not file presence. |
| Learnings Researcher | New: the P1 was a *measurement-shape* defect — a path-shaped grep could not see bare-filename citations. This is a reusable failure class worth compounding after the shipment lands. | P3 | Recorded as a post-shipment compound-library candidate; not a code change here. |
| Architecture Strategist | The plan fixes the GAP 1 contradiction (tolerant `_resolve_policy_registry` vs. `required: True`) rather than only the symptom. | — | PASS (strength) |
| Architecture Strategist | Manifest-file serialization: U1 and U7 both edit `harness-manifest.yaml`, and the ordering is now an explicit dependency edge rather than an implicit convention. | — | Resolved (was P3) |
| Agent-Native Parity Reviewer | Installing 13 personas changes agent-facing capability more than the prior 11. Still flagged as intended effect (RK-E) with no exit-code change. | P3 | Accepted |
| Security Lens Reviewer | The installed registry becomes the authoritative text for destructive-approval and merge-authority policies. U1 is render-only and content-identical to the template, so no policy is silently weakened. | P1 -> mitigated | **Addressed** by INV-1's byte-identity assertion. |
| Security Lens Reviewer | Security personas (`security-reviewer`, `security-lens-reviewer`) are unchanged by this correction and remain in U5. No secrets or external trust boundaries involved. | — | PASS |
| Template Integrity Reviewer | The corrected plan no longer proposes a duplicate of an existing template — the single highest-value template-integrity outcome of this correction. | — | PASS (strength) |
| Template Integrity Reviewer | U8's placeholder scan must not itself be defeated by the `{{PRIMARY_LANGUAGE_LOWER}}` citation it is designed to tolerate: the EXEMPT branch applies to *route resolution*, not to the zero-unresolved-placeholder scan over installed artifacts. | P2 | **Addressed** — the two checks are separately specified (hardening step 2 vs. U8 scenario 2) and operate on different inputs. |

### Verdict rationale

No P0 findings. The prior P1 (false `python-reviewer` premise) is **resolved at
the root**, not patched: the plan now renders the existing canonical template
instead of authoring a duplicate, which also withdraws the prior scope-expansion
P2. The remaining P1-class concern (silent policy weakening) is structurally
mitigated by INV-1, unchanged from the prior pass.

All six P2 findings from the BLOCKED review are corrected and re-verified against
file-and-line primary evidence. The one *new* P2 introduced by this correction
(U6 scope widening) is justified by the workspace's own installed drift contract
and is bounded to two mechanical renders. Both P3s are accepted or recorded as
follow-ups.

Task granularity remains within budget: 8 units, max 5 files each, max 4 test
scenarios, single domain per unit. U6 at 5 files and U8 at 4 scenarios are the
widest, both comfortably inside the 2-hour rule.

Q1, Q5, and Q7 operator approvals are preserved exactly: report persistence
allowed with named consumers; authoritative test command
`PYTHONPATH=src python -m unittest discover -s tests`; S0 is not waived.

```text
decision: PASS
```

---

### Superseded review — 2026-08-27

The original review below returned PASS on a plan that rested on the false
`python-reviewer` premise. It is retained for provenance and is **not** the
operative verdict.

**Reviewed**: 2026-08-27 · **Plan**: `docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md`

#### Dispatch capability (P-012)

* `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
  — the reviewer identities under `.github/agents/subagents/` do not exist (this
  plan's GAP 2). Probed by direct path existence check; **not** assumed.
* `TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
* `TOOL_DEGRADED: agent-intercom — operator visibility reduced`
* `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` — file-based retrieval used.

**Every selected persona was covered inline.** No persona was dropped.

Superseded dispatch marker: `single-agent-declared-degradation`.

#### Superseded persona findings (P0-P3)

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

#### Superseded verdict rationale

No P0 findings. The two P1-class concerns (silent policy weakening; masked-assertion
backlog) are both structurally mitigated by hardening invariants that were added
**before** review, not promised as follow-ups. All P2 findings are either
justified in-plan or already addressed by an explicit verification step. Task
granularity is within budget: 8 units, max 4 files each, max 4 test scenarios,
single domain per unit.

Superseded verdict marker: `PASS` (2026-08-27) — **not operative**; superseded by
the 2026-08-28 re-review above, which is the governing verdict for this plan.

---

## Plan Review Outcome (OPERATIVE)

Governing verdict for this plan, restated at the end of the document so the
operative gate markers are unambiguous and terminal. These markers correspond to
the **2026-08-28 re-review** and supersede the 2026-08-27 pass.

* **Reviewed**: 2026-08-28 (re-review after BLOCKED correction of `1bafd85e`)
* **Findings**: P0=0, P1=0 (the prior P1 is resolved at the root), P2=0 outstanding
  from the BLOCKED review (all six corrected and re-verified), P3 accepted/recorded
* **Operator approvals preserved**: Q1 (report persistence with named consumers),
  Q5 (`PYTHONPATH=src python -m unittest discover -s tests`), Q7 (S0 not waived)
* **Status**: cleared for harvest and shipment assembly; execution remains with Ship

### Amendment record — review-fix cycle 2 (2026-08-28, `f54152ec`)

A second local review of `chore/stage-156-S` at `f54152ec` returned P2×2 + P3×3
against the **staging artifacts**. Those fixes are applied above. **The PASS
verdict is RETAINED, not re-run.** Justification that this is a *contract
completion*, not a scope change:

| Test | Result |
|---|---|
| New implementation unit added? | **No** — U1-U8 unchanged. |
| Files created/modified changed? | **No** — still 1 registry + 13 personas + 1 manifest + ≤3 test files + 1 docstring; still **0 new templates**. |
| Protected invariants INV-1…INV-5 changed? | **No.** |
| Operator approvals (Q1/Q5/Q7) re-interpreted? | **No** — Q5's command is unchanged and still authoritative. |
| Ship's discretion widened? | **No — strictly NARROWED.** D8 replaces "synthesize these five values" with "bind these five exact values". |
| Was the amended obligation already in the contract? | **Yes.** The DoD and U8 already demanded **zero unresolved `{{...}}`** across all 14 installed artifacts. D8 does not add that obligation — it makes it *satisfiable* by naming what to bind. The plan previously required an outcome it gave no reviewed means of reaching; that is a gap in the contract, and D8 closes it. |
| Anything new entering the product? | **One item, gated.** The D8-B prose becomes installed persona content. It is Stage-reviewed, derived from named in-repo reviewed sources, and gated by new U8 scenario 5 (verbatim conformance + live-resolver cross-check + template-unmodified assertion). Its residual weakness (`LANGUAGE_PERFORMANCE_CHECKS` has no code-derived source) is recorded as **RK-J**, not concealed. |

The P3 fixes (obsolete U3-template rollback step, `336F3AB7` past-tense
restatement, RK-K checkpoint residual) are documentation-accuracy corrections to
statements that were false or stale; none alters an executable obligation.

**Conclusion**: `decision: PASS` stands, unchanged, on the corrected document.
Re-running plan-review would re-litigate an unchanged implementation contract and
would consume one of the three review-fix cycles without a contract delta to
review.

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```
