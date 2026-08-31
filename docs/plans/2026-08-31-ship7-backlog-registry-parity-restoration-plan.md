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
| 3 | Architecture | **P1** | If the installed registry drifted once, the **install/tune path that produces it** is the real defect, and regenerating is treating a symptom. | **Accepted, partially resolved.** Task 2's parity test converts the symptom into a **detected** condition, which is the honest available fix inside this scope. Diagnosing *why* the installer emitted a truncated registry is genuinely a different contract surface; it is recorded as the leading P-021 capture candidate from this shipment and explicitly not attempted here. The parity test guarantees the question cannot be forgotten, because the next drift fails a test instead of passing silently. |
| 4 | Schema/CLI/docs coupling | **P1** | `features.sizing: true` becoming visible will change generated Stage agents' documented behaviour in **existing** installs on their next tune. | **Resolved.** That is the intended outcome of `2E67938C` and is exactly why **H4** sequences SHIP-7 before SHIP-8. Task 1's acceptance requires the compatibility matrix and the operating-model doc to state that sizing is advertised and what the enforcement consequence is, so the behaviour change is documented rather than discovered. |
| 5 | Maintainability | P2 | Task 3 bundles a backlog-md command fix with a capability declaration. | Accepted: one file, one tool, one decision (D3). Splitting produces two PRs touching the same registry. |
| 6 | Correctness | P2 | Task 3 cannot be end-to-end verified without installing backlog-md. | Bounded to **name resolution and declaration correctness**, verified against the vendored `references/backlog-md/package.json`. No install, no runtime test. Recorded as an explicit limitation of the task. |
| 7 | Scope | P3 | The registry-drift discovery could be read as new scope. | Folded into `2E67938C`'s existing text as its enabling condition; no new stash ID, no work outside the fixed 48. Recorded in the portfolio deliberation §"A material discovery". |

**Verdict: PASS.** 1 P0 and 3 P1 raised; all four resolved before harvest. Zero
unresolved P0/P1. Two review-fix cycles of three.
