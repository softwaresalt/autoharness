---
title: "SHIP-7 — Installed backlog-registry parity restoration and drift guard"
date: 2026-08-31
slug: backlog-registry-parity-restoration
doc_type: plan
source_stash: "2E67938C (enabling condition), 6443A499, 0A86267A, 56803680 (decision D3)"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-7"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-7 — Installed backlog-registry parity restoration and drift guard

## Problem

### The primary defect: the installed registry is 191 lines behind its template

Measured directly at `2661c1c8`:

| File | Lines |
|---|---|
| `templates/backlog/registries/backlogit.registry.yaml` | 460 |
| `.autoharness/backlog-registry.yaml` (installed) | **269** |

A key-set comparison shows the installed registry is missing **22 declared
operations**:

`stash`, `stash_edit`, `stash_get`, `stash_archive`, `fetch_stash`,
`harvest_stash`, `deliberate`, `add_link`, `remove_link`, `get_links`,
`archive_item`, `adopt_item`, `get_metadata_catalog`, `get_wit_metadata`,
`list_types`, `list_templates`, `get_version`, `export_command_map`,
`merge_sync`, `telemetry_harvest`, `doctor`, `cleanup_checkpoints`

plus the entire sizing field map (`size`, `complexity`, `size_source`,
`size_ruleset_version` — absent from both `update_task.params` and
`field_mapping`) and **seven feature flags**: `telemetry_harvest`, `stash`,
`semantic_links`, `deliberation`, `discovery`, `lifecycle_hygiene`, and
**`sizing: true`**.

This is the mechanical cause of three symptoms that have been reported
separately:

1. **P-012 exposure.** The Step 0.0 tool-availability gate is registry-driven. An
   agent that honours the registry concludes that `stash_archive`, `deliberate`,
   `archive_item` and eighteen other operations do not exist, and falls back to
   ad-hoc filesystem work — the exact failure the gate exists to prevent.
2. **`2E67938C` cannot be satisfied.** Its mandate is that Stage "actually USE"
   size and complexity "robustly and enforceably". The installed registry does
   not advertise `features.sizing`, so the enforcement path is unreachable and
   every generated Stage agent takes the documented degradation branch.
3. **Stage's own Step 5.6 and P-021 C5 obligations have no declared binding.**
   The archive-not-delete tool protocol names `backlogit stash archive` /
   `backlogit_stash_archive`; neither is declared in the installed registry.

This finding is recorded **inside `2E67938C`'s existing scope** as its enabling
condition, not as a new work item. `2E67938C` already asserts the fields exist
and must be enforced; this is why they are not. No scope expansion occurred.

### 6443A499 — the resolver default is correct but undeclared and undocumented

The backlog-md registry omits `features.shipments` (and `queue`,
`commit_tracking`) entirely. This is schema-valid and resolves **correctly** —
`src/autoharness/verify_workspace.py:2967` is the only resolution site and reads
`variables.setdefault("FEATURE_SHIPMENTS", str(bool(features.get("shipments", False))).lower())`,
so an omitted key deterministically renders `false`, which is the right value.
An earlier version of the entry claimed an absent key could leave
`{{FEATURE_SHIPMENTS}}` unresolved or produce a permanently-blocked CI job; that
claim is **false** and was retracted via the PR #410 review. This is a hardening
and documentation item, **not a runtime defect** — the correctness currently
depends on an undocumented implicit default.

### 0A86267A — the backlog-md MCP command is wrong in two ways

Verified against the vendored upstream at `references/backlog-md`
(MrLesk/Backlog.md v1.50.1, gitlink `988d27fe`). The registry claims
`mcp_server.command: "bunx backlog-md mcp"`. The npm package is **`backlog.md`
(with a dot)** — `references/backlog-md/package.json` declares
`"name": "backlog.md"` — and `bunx`/`npx` resolve npm package names, so
`bunx backlog-md` does not resolve this tool. Upstream's README carries an
explicit warning about exactly this mistake. autoharness's backlog-md MCP
integration therefore cannot ever have worked.

## Direction

Restore the installed registry from its template, then make the drift
**impossible to reintroduce silently** with a parity test. Fold in the two
backlog-md corrections, which decision **D3** (keep-but-demote) requires: a
demoted-but-supported tool must still have a correct command and an honest,
*declared* capability surface.

## Hardening (P-006)

Triggered: the registry is the resolution substrate for every generated agent.

* **H1 (binding).** The installed registry must be **regenerated from the
  template**, not hand-merged. A hand-merge reproduces the drift class.
* **H2 (binding).** Regeneration must be verified to be **purely additive** for
  this workspace: no existing operation's `mcp_tool`, `cli_command`, or `params`
  mapping may change value, and no feature flag may flip from `true` to `false`.
  Any non-additive delta halts the task for explicit review.
* **H3 (binding).** The parity test must compare **installed ⊇ template** for the
  active tool's operations and feature keys and must **fail closed** if either
  file is unreadable or unparseable. A parity test that skips on a missing file
  is the same fail-open shape being removed.
* **H3a (binding) — key-set containment is not enough; template-owned mappings
  require VALUE equality.** *(Added in review-fix cycle 1, Orchestrator
  local-review finding 13.)* **H2** halts on a value-changed key, but **H2 runs
  once**, inside task 1's regeneration. **H3** as originally written compares only
  key *sets*, so after task 1 completes, a later edit that silently changed
  `mcp_tool: backlogit_create_item` to something else would keep every key present
  and pass the standing parity test forever. The drift class this shipment exists
  to close would be detected on the first day and never again. The parity test
  therefore asserts **value equality**, not merely key presence, over the
  **template-owned** surface.

  **H3a-RECURSIVE (binding; replaces the enumerated surface table in review-fix
  cycle 2, finding 8).** The comparison is **recursive over every leaf path in the
  parsed template registry document**, not a list of selected surfaces. For every
  leaf path present in the template, the installed registry must carry an **equal
  value at the same path**, unless that exact path appears in **H3b**'s closed
  override allow-list. *Default is assert; exemption is by explicit path only.*
  An enumerated surface table is a **denylist wearing an allowlist's clothes** —
  it protects what someone remembered on the day it was written, and every field
  added to the registry template afterwards is unprotected, silently. The cycle-1
  table omitted top-level **`schema_version`** (this workspace's registry declares
  `1.0.0`), the one field whose silent divergence makes every other parity result
  meaningless, because a v1 installed registry compared against a v2 template is
  a comparison between two different contracts. It would equally omit any future
  template-owned key. Under the recursive rule a new template-owned field is
  protected **the moment it is added to the template**, with no test edit.

  Walk semantics, precisely:

  * The walk is **driven by the parsed template document**, so a path present in
    the template and **absent** from the installed registry is a **failure**
    (missing is not equal) — this is what catches a field silently dropped during
    regeneration.
  * It compares **parsed structure, never raw text**, so key ordering, quoting
    style, comment placement, and YAML formatting cannot produce false failures.
  * Every leaf at every depth is compared, including members of nested maps and
    sequences.
  * A path present **only** in the installed registry is reported **INFO** and
    does not fail: the template is authoritative over what it owns, and it does
    not own what it never declared.
  * Interior-whitespace normalization applies to **`cli_command` values only**,
    where it is a formatting artefact. It is **not** global — whitespace inside an
    `mcp_tool` name or a status value *is* a difference.

  The table below now records **consequences** of the recursive rule and the
  reason each matters. It is **not** the definition of the covered surface and is
  **not** a list to be maintained; a template path absent from it is still covered.

  | Surface (consequence, not definition) | Comparison | Rationale |
  |---|---|---|
  | `schema_version` (top level) | **Value equality** | *(Missing in cycle 1.)* A contract-version divergence invalidates every other parity result. |
  | `operations.*.mcp_tool` | **Value equality** | Names a real tool entry point. A wrong value fails at call time, in an agent run, not in CI. |
  | `operations.*.cli_command` | **Value equality** (after normalizing interior whitespace) | The declared CLI fallback P-012 degraded mode depends on. |
  | `operations.*.params` | **Value equality per key** | A wrong param mapping silently writes the wrong field. |
  | `field_mapping.*`, `status_values.*` | **Value equality** | Pure template-owned translation tables with no legitimate local meaning. |
  | `features.*` | **Value equality**, plus **no `true` → `false` flip** | A flag is a capability claim; a silently downgraded flag disarms a gate. Plain equality already fails a flip; the dedicated assertion makes the *diagnostic* name the real hazard. |
  | `tool_name`, `tool_type` | **Value equality** | Identity. **H7** already forbids changing tool names; this makes it testable. |
  | `directory` | **Override-eligible — NOT asserted** | *(Contradiction resolved in cycle 2.)* Cycle 1 listed `directory` here as value-equality **and** in **H3b** as override-eligible; the two clauses disagreed about the same field. It encodes where **this machine** keeps the backlog root — this workspace uses the legacy `.backlogit` root while new installs default to `.backlog` — which is exactly the machine-local class **H3b** exists for. It is exempt. |
  | *any future template-owned path* | **Value equality** | Covered automatically by the recursive walk. This row is the difference between the rule and the list it replaced. |

* **H3b (binding) — the permitted workspace-override list is explicit,
  enumerated, and closed.** Value equality is useless if "workspace customization"
  is an open-ended excuse, and **H2**'s P0 concern (blind regeneration destroying
  deliberate local customization) is real. The two are reconciled by an
  **allow-list of override-eligible fields declared in the test itself**:

  * **Override-eligible (installed MAY differ from template, test reports the
    delta as INFO and passes):** `mcp_server.command`, `mcp_server.transport`,
    `cli.binary`, and `directory` — the four fields that legitimately encode where
    *this machine* finds the tool.
  * **Not override-eligible (installed MUST equal template; any difference
    FAILS):** everything else in the table above.
  * A field is override-eligible **only** by appearing in that enumerated list. An
    unlisted difference is a failure, never a tolerated customization — so
    widening the exemption is a **visible edit to the allow-list** under review,
    which is exactly the property **H2**'s halt-for-review rule wants and cannot
    provide on its own after task 1 finishes.
  * The test must assert the allow-list itself is **non-empty and closed** (a
    fixture adding an unlisted differing field must FAIL), so an accidental
    "allow everything" regression is caught.
* **H4 (binding).** Enabling `features.sizing: true` in the installed registry
  changes Stage's own resolved behaviour. It must land **before** SHIP-8's
  fail-closed sizing enforcement, which is why SHIP-7 `blocks` SHIP-8.
* **H5.** `6443A499` is resolved by **declaring** `features.shipments: false`
  explicitly in the backlog-md registry *and* documenting the
  absent-key-means-false resolver default — belt and braces. Do not change
  `verify_workspace.py:2967`; it is correct.
* **H6.** Per D3's recorded non-goal, **do not** add new `stash` / `queue` /
  `checkpoints` feature flags to the backlog-md registry. That is a schema change
  and is out of this fixed scope.
* **H7 (binding) — SHIP-6 coupling, counterpart to SHIP-6's H6.** SHIP-6's
  fail-closed tool-scoped binding check resolves against **registry tool names
  only** and is forbidden from reading feature flags. This shipment must not
  invalidate that bound: it may add, correct, and explicitly declare **feature
  flags** and **operation mappings** freely, but it must **not add, rename, or
  remove a registry tool name**. `backlogit`, `backlog-md`, and `manual` are the
  fixed set. **H6** already forbids the schema change that would be the usual way
  to breach this; **H7** states the invariant SHIP-6 depends on so a future editor
  cannot break it by accident. File sets and `docs/` sets between the two
  shipments are disjoint (analysed in SHIP-6 **H6**), so no `blocks` edge is
  required in either direction.
* **H8 (binding) — the sizing flag this workspace is missing is in scope here.**
  Measured during review-fix cycle 1: `.autoharness/backlog-registry.yaml`'s
  `features:` block declares 15 keys and **no `sizing` key at all**, while
  `backlogit_update_item` does accept `size`, `size_source`,
  `size_ruleset_version`, and `complexity`. That is exactly the installed↔template
  drift class this shipment exists to close, and it is the blocker SHIP-8 records
  as `D456616B`. Task 1's additive-delta verification (**H2**) must therefore
  explicitly confirm that `features.sizing: true` is present after regeneration,
  and task 2's parity test must cover it. **H4**'s SHIP-7 → SHIP-8 ordering is
  what makes SHIP-8's gate non-inert.
* **H9 (binding) — safety mode.** Every task enters `careful`, and this is
  propagated into each executable task's own body, not merely declared here
  (propagation performed in review-fix cycle 2). Task 1 additionally enters
  `freeze-scope` bounded to `.autoharness/backlog-registry.yaml` **and its
  `.autoharness/harness-manifest.yaml` checksum entry**, because the registry is
  the resolution substrate for every generated agent and **H2** requires any
  non-additive delta to halt rather than be absorbed.
* **H10 (binding, added cycle 2) — manifest checksum coupling is part of the
  regeneration, not a follow-up.** `.autoharness/backlog-registry.yaml` is a
  **manifest-tracked artifact**. Regenerating it changes its content and therefore
  its checksum, so a regeneration that does not refresh
  `.autoharness/harness-manifest.yaml` leaves the workspace in a state where
  **every subsequent `verify-harness` run fails** on manifest integrity. This is a
  current **P0** blocker on task 1, not a hygiene nicety. Required, in strict order,
  **within the same unit of work**:
  1. Regenerate the registry from template (**H1**), after the **H2** additive-only
     diff gate has passed.
  2. **Refresh** the recorded checksum for `.autoharness/backlog-registry.yaml`
     through the harness's own manifest-refresh path — never by hand-computing and
     pasting a digest.
  3. **Verify the coupling** by re-reading the manifest entry and confirming it
     matches the regenerated file on disk.
  4. Run `verify-harness` and confirm it passes.

  The before/after checksum pair is recorded as evidence so the refresh is
  auditable rather than asserted. **Splitting the checksum refresh into a later
  task is forbidden** — the two are one atomic change. The same coupling applies to
  SHIP-3 task 3 and SHIP-5's `155.004-T`; it is called out as P0 here because this
  regeneration is unconditional.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Regenerate the installed backlogit registry from its template and verify the delta is purely additive | M | medium | `.autoharness/backlog-registry.yaml` |
| 2 | Add a fail-closed installed↔template registry parity test and document the absent-key resolver default | M | medium | `tests/`, `docs/` |
| 3 | Correct the backlog-md MCP command and explicitly declare its limited capability surface | S | low | `templates/backlog/registries/backlog-md.registry.yaml`, docs |

## Non-goals

* No change to `verify_workspace.py:2967` — the resolver default is correct.
* No new feature flags (**H6**).
* No removal of backlog-md support — D3 selected keep-but-demote, and DROP was
  recorded as **not autonomously available** because "are there real installs to
  break?" is unanswerable from inside this repository.
* No change to backlogit itself.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`;
`backlogit doctor`; a post-regeneration re-run of Step 0.0's tool-availability
probe confirming `stash_archive`, `deliberate` and `archive_item` now resolve;
and a `bunx backlog.md --help`-equivalent resolution check for task 3 (name
resolution only — no install performed).

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Correctness | **P0** | Regenerating the installed registry could **overwrite legitimate workspace-local customization** that was deliberately made and is not represented in the template. Blind regeneration would silently destroy it. | **Resolved.** **H2** is elevated to a hard precondition: task 1 must first produce and record a full key-level diff, classify every delta as additive / value-changed / removed, and **halt** on any value-changed or removed key rather than proceeding. Only a purely-additive delta may be applied automatically. The measured delta for this workspace is additive-only (22 operations, one field map, seven flags — all absent, none conflicting), but the task must re-derive that rather than trust this plan. |
| 2 | Security | **P1** | Enabling seven feature flags at once expands the operation surface agents will use, including `merge_sync`, `doctor` and `cleanup_checkpoints`, which mutate tool-managed state. | **Resolved.** The flags describe **tool capabilities**, not grants of authority; role boundaries (P-010) and destructive-command approval (Constitution VII) are unchanged and continue to govern who may call what. Task 1's acceptance explicitly records that no policy, role, or approval surface is modified. Additionally, restoring the declarations makes these operations *visible to the gate* rather than reached by ad-hoc fallback — a net reduction in exposure. |
| 3 | Architecture | **P1** | If the installed registry drifted once, the **install/tune path that produces it** is the real defect, and regenerating is treating a symptom. | **Accepted, partially resolved.** Task 2's parity test converts the symptom into a **detected** condition, which is the honest available fix inside this scope. Diagnosing *why* the installer emitted a truncated registry is genuinely a different contract surface; it is captured as compliant P-021 deferred entry `CE441101` and explicitly not attempted here. The parity test guarantees the question cannot be forgotten, because the next drift fails a test instead of passing silently. |
| 4 | Schema/CLI/docs coupling | **P1** | `features.sizing: true` becoming visible will change generated Stage agents' documented behaviour in **existing** installs on their next tune. | **Resolved.** That is the intended outcome of `2E67938C` and is exactly why **H4** sequences SHIP-7 before SHIP-8. Task 1's acceptance requires the compatibility matrix and the operating-model doc to state that sizing is advertised and what the enforcement consequence is, so the behaviour change is documented rather than discovered. |
| 5 | Maintainability | P2 | Task 3 bundles a backlog-md command fix with a capability declaration. | Accepted: one file, one tool, one decision (D3). Splitting produces two PRs touching the same registry. |
| 6 | Correctness | P2 | Task 3 cannot be end-to-end verified without installing backlog-md. | Bounded to **name resolution and declaration correctness**, verified against the vendored `references/backlog-md/package.json`. No install, no runtime test. Recorded as an explicit limitation of the task. |
| 7 | Scope | P3 | The registry-drift discovery could be read as new scope. | Folded into `2E67938C`'s existing text as its enabling condition; no new stash ID, no work outside the fixed 48. Recorded in the portfolio deliberation §"A material discovery". |

**Verdict (cycle 0): PASS.** 1 P0 and 3 P1 raised; all four resolved before harvest.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `yes`. Satisfied.** **H1**–**H9** are binding
and each is propagated into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Correctness | inline persona pass | cycle 0 findings retained above |
| Security | inline persona pass | cycle 0 findings retained above |
| Schema/CLI/docs coupling | inline persona pass | cycle 0 findings retained above, 1 P1 (cycle 1) |
| Architecture | inline persona pass | 1 P1 (cycle 1) |
| Constitution | inline persona pass | 1 P1 (cycle 1) |
| Template integrity | inline persona pass | cycle 0 findings retained above |
| Maintainability | inline persona pass | cycle 0 findings retained above |
| Scope boundary | inline persona pass | 1 P2 (cycle 1) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| A | Schema/CLI/docs coupling | **P1** | The installed registry declares **no `sizing` feature key**, yet SHIP-8's fail-closed gate keys on `features.sizing` being advertised. Without this shipment enabling it, SHIP-8's gate would ship inert in the very workspace that authored it. | **Resolved by H8.** The missing key is measured and named; task 1's additive-delta verification must confirm `features.sizing: true` after regeneration and task 2's parity test must cover it. The existing **H4** SHIP-7 → SHIP-8 `blocks` edge makes the ordering real. |
| B | Architecture | **P1** | SHIP-6's fail-closed binding check depends on the registry **tool-name set** being stable, and SHIP-7 is the shipment that edits registries — an unstated invariant one editor away from breaking. | **Resolved by H7**, the explicit counterpart to SHIP-6's **H6**: feature flags and operation mappings may change freely; the tool-name set (`backlogit`, `backlog-md`, `manual`) is fixed. Disjoint file/docs sets confirmed; no `blocks` edge needed in either direction. |
| C | Constitution | **P1** | No safety mode declared on a shipment that regenerates the resolution substrate for every generated agent. | **Resolved by H9**: `careful` on all tasks, plus `freeze-scope` on `.autoharness/backlog-registry.yaml` for task 1. |
| D | Scope boundary | P2 | **H8** could be read as licence to add whatever feature flags SHIP-8 wants. | Bounded: **H8** names exactly one key (`sizing`), justified by measured installed↔template drift, and **H6** still forbids new backlog-md flags. Any other missing key surfaced by regeneration is reported under **H2**'s halt-for-review rule, not silently added. |

**Verdict: PASS.** Cycle 1: 3 P1 raised, all 3 resolved; 1 P2 dispositioned.
Cumulative: **zero unresolved P0/P1**.

**Cycle 0 verdict (preserved):** PASS — 1 P0 and 3 P1 raised; all four resolved
before harvest. Zero unresolved P0/P1.

### Review-fix cycle 2 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| E | Schema/CLI/docs coupling | **P0** | **Task 1 regenerates a manifest-tracked artifact without refreshing its manifest checksum.** `.autoharness/backlog-registry.yaml` is tracked in `.autoharness/harness-manifest.yaml`; regenerating it necessarily changes its checksum. Neither the plan nor the executable task required the refresh, so the shipment as written would leave the workspace failing **every** subsequent `verify-harness` run on manifest integrity — while SHIP-7 is itself a prerequisite of SHIP-8. A current P0 blocker. | **Resolved by H10.** The refresh is made part of the regeneration, in strict order — regenerate → refresh through the harness's own path → **verify the coupling by read-back** → `verify-harness` passes — with the before/after checksum pair recorded as evidence and splitting it into a later task explicitly forbidden. Propagated into `157.001-T` as mandatory acceptance, and the same coupling is made explicit in SHIP-3's `153.003-T`. |
| F | Correctness | P2 | `157.002-T`'s parity test was ordered after task 1 only in narrative. With no encoded edge it could have been executed against the **truncated** registry — i.e. authored against the very drift it exists to detect. | **Resolved.** `157.002-T` is now encoded as blocked by `157.001-T`, and the task body states why. Verified present in the dependency graph and acyclic. |
| G | Constitution | P2 | **H9** declared `careful` for every task, but none of the three executable tasks carried a safety-mode line in its own body. | **Resolved.** All three tasks now declare their safety mode inline; task 1's `freeze-scope` is extended to cover its manifest checksum entry, matching **H10**. |

**Verdict: PASS.** Cycle 2: 1 P0 and 2 P2 raised, all 3 resolved. Cumulative:
**zero unresolved P0/P1**. Three review-fix cycles of three consumed; the next
review is the final independent disposition cycle.
