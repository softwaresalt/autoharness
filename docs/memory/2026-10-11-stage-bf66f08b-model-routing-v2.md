---
title: "Stage session 2026-10-11 — BF66F08B model routing v2: deliberation 040-DL, R1-A/R1-B plans, 207-F/208-F, shipments 214-S/215-S"
date: 2026-10-11
agent: stage
session_id: stage-2026-10-11-bf66f08b-model-routing-v2
source_stash: BF66F08B
deliberation: 040-DL
---

# Stage session 2026-10-11: BF66F08B model routing v2

All times are UTC (session started 2026-10-12T04:17:56Z).

## Outcomes

* **Deliberation `040-DL`**, decided: `docs/decisions/2026-10-11-model-routing-v2-deliberation.md`.
  The baseline `docs/design-docs/model-routing-v2.md` does not load (undefined aliases), fails
  the current schema in 7 places when anchors are defined, and names phases and subagents that
  are not invocation boundaries or agents. Chosen design (Option D): one deterministic resolver
  (`src/autoharness/model_routing.py` plus language-neutral JSON vectors), a YAML-anchor-free
  tier-delta route catalog (`model_routing.routes`), manifest-registered subagent site bindings
  (`model_routing.bindings`, `agent:<id>`), drift and unknown-key verification, additive schema
  1.2.0 as a new mirror (1.1.0 preserved). Rejected: baseline as written, phase sites,
  `max_cycles` re-attempt escalation, cross-family as a P-014/P-018 merge gate, `tier3` as the
  GPT route, anchors.
* **Plans** (hardened, plan-review PASS, single-agent declared degradation):
  `docs/plans/2026-10-11-model-routing-resolver-single-source-plan.md` (R1-A) and
  `docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md` (R1-B). Reviews:
  `docs/reviews/2026-10-11-model-routing-*-plan-review.md`. R1-B cycle 1 failed on a P1
  (no render-time site composition unit); fixed by unit B6a, then PASS.
* **Harvest:** feature `207-F` (5 tasks, shipment `214-S`) and feature `208-F` (13 tasks,
  shipment `215-S`). Every task carries `size` and `complexity` with `ah-stage-sizing-v1`
  provenance. Plan unit B6 is `208.008-T` and B6a is `208.007-T`.
* **Sequencing:** `214-S` blocks on `213-S` (shared Orchestrator pair, workflow-policies copies,
  harness manifest with the `209-S` to `213-S` chain); `215-S` blocks on `214-S`. No `dag-root`
  declared, no bootstrap grant authored. `207-S` (hold gate, `039-DL`) is not a predecessor:
  the resolver is authored for Go parity and does not touch the distribution surfaces.
* **Stash:** `BF66F08B` triage note appended and entry archived (content fully consumed).
  Follow-ups created: `C2EA31FA` (R2 escalation chain), `C5801D7B` (R3 invocation directives and
  review diversity), `507B2139` (R4 phase promotion, gated), `56654C18` (tune refresh of the 13
  stale subagent frontmatters after `215-S`). No other stash entry was edited.

## Phase log

| UTC | Delta | Phase |
|---|---|---|
| 2026-10-12T04:17:56Z | +0s | Stage start; Step 0.0 tool gate |
| 2026-10-12T04:19:36Z | +1m40s | Gate, index sync, zero-candidate checkpoint check done |
| 2026-10-12T04:28:44Z | +9m08s | Research complete; `040-DL` created |
| 2026-10-12T04:47:28Z | +18m44s | Both plans hardened and reviewed (PASS) |
| 2026-10-12T04:48:34Z | +1m06s | Harvest started (`207-F`) |
| 2026-10-12T05:03:02Z | +14m28s | Last task created (`208.013-T`) |
| 2026-10-12T05:21:49Z | +18m47s | Shipments `214-S`, `215-S` assembled |
| 2026-10-12T05:24:48Z | +2m59s | `BF66F08B` disposition |

## Operator decisions pending (`040-DL`, defaults recorded)

OQ1 provider mix and data egress (default: no change to Claude Stage), OQ2 review diversity
(preferred, never a merge gate), OQ3 escalation analysis-only (keep), OQ4 catalog names and
values, OQ5 `3C19FA0F` and `1F13DF5E` (untouched), OQ6 flat escalation deprecation (not in this
series), OQ7 Go parity (yes), OQ8 disposition of stash `1E6C8576` (operator), OQ9 dogfood
`schema_version` marker bump (gates `208.006-T` only; default confirm).

## Events and declared degradations

* `TOOL_OK`: backlogit MCP. `INDEX_SYNC_OK` (1821 then 1847 items). Zero active
  stage-owned checkpoints, no quarantine anomalies; normal startup.
* `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`: those tool surfaces were not
  exposed in this session; file-based exploration used, no phase broadcasts.
* `TOOL_DEGRADED: backlogit_stash_archive`: not in the tool set; CLI `backlogit stash archive`
  used (the installed Stage tool list still names the deprecated `backlogit_stash_remove`,
  tracked by `1F13DF5E`).
* Reviewer subagent dispatch and the anchor review route were not dispatchable:
  `single-agent-declared-degradation`, `TOOL_DEGRADED: model-specific-review-routing`.
* Parallel backlogit MCP calls timed out (self-inflicted lock contention). All writes were
  verified afterwards by SQL against `item_deps` and `items`; none was lost or duplicated.
* P-010: not violated. The delegated request asked Stage to push a `chore/stage-*` branch and
  open a PR, but the Stage Role Boundary lists PR creation and push as forbidden. Stage
  committed locally and withheld the push and PR; publication is handed to the Orchestrator's
  Step 1.5. P-021: no Ship-side captures; out-of-scope findings became Stage follow-ups.
* One scratch Python probe was written to the OS temp directory (outside the workspace) while
  gathering frontmatter-drift evidence; later probes ran inline. It is not in the repository.
* markdownlint (P-008) was not run by Stage (linters are outside the Stage boundary); heading
  hierarchy of every new document was inspected manually (one H1, no skipped levels).

## Next steps

1. Orchestrator Step 1.5 publishes the staging commit (push, PR, operator-approved merge).
2. Operator answers `040-DL` OQ1 to OQ9, in particular OQ9 before `208.006-T` and OQ8.
3. Ship works the queue: `214-S` is claimable only after `213-S` ships; `215-S` after `214-S`.
4. After `215-S`: run `tune-harness` (proposals only) for stash `56654C18`; stage R2 and R3.

## Addendum 2026-10-12: operator confirmation of the `040-DL` defaults

Append-only. Supersedes the "Operator decisions pending" section and next step 2 above for
the questions it resolves. The operator answered "2. yes" (accept the recommended defaults for
OQ1 to OQ9, including the OQ9 marker bump), relayed by the Orchestrator and recorded in
`040-DL` under "Operator Confirmation (2026-10-12)".

* Resolved by default: OQ1, OQ2, OQ3, OQ4, OQ6, OQ7. Resolved yes: OQ9 (Ship may bump the
  dogfood `schema_version` marker `1.1.0` to `1.2.0`; marker only, no routing value).
* Still open: OQ5 (its default is "left to the operator", so a yes does not decide
  `3C19FA0F` or `1F13DF5E`) and OQ8 (default accepted; the operator archives `1E6C8576`
  after R2 is staged, which has not happened).
* `208.006-T` and `215-S` are no longer gated on an OQ9 answer. Ship cites the recorded
  confirmation at intake; the edit stays marker-only (one changed line in
  `.autoharness/config.yaml`).

## Addendum 2026-10-12: PR #513 review-fix cycle 1

Append-only. Copilot review `5487147517` on PR #513 (HEAD `cc06f41e`) raised four findings
inside this staging's own artifacts. Stage fixed each at the root, in separate local commits
(no push, no PR comment, no thread resolution: the Role Boundary reserves those for the
Orchestrator). All times UTC.

| UTC | Phase | Commit |
|---|---|---|
| 2026-10-12T17:29:56Z | Session start; tool gate, index sync | |
| 2026-10-12T17:34:45Z | Part 1: operator confirmation recorded | `96a4503b` |
| 2026-10-12T17:36:28Z | Thread `PRRT_kwDORzpWpM6rWUWn`: missing `B3b -> B4` edge | `d12a3979` |
| 2026-10-12T17:38:16Z | Thread `PRRT_kwDORzpWpM6rWUXL`: empty `model_provider` is valid | `82c8308c` |
| 2026-10-12T17:42:50Z | Thread `PRRT_kwDORzpWpM6rWUXr`: disk-first site registry | `78f88268` |
| 2026-10-12T17:46:22Z | Thread `PRRT_kwDORzpWpM6rWUYJ`: resolver purity guard | `b62cb4d1` |

* **Edge audit.** The only missing edge was `208.005-T` depending on `208.004-T`. Every other plan edge
  in both plans and every "Depends on" note in the 18 tasks matched the backlog. Plan graph
  and manifests: no cycle, `214-S` and `215-S` manifest orders honor every task edge, and
  `ready_set` is still `[209-S]`. The R1-B tasks declare no task-level edge to the R1-A
  tasks by design (the dependency is the shipment edge `215-S` after `214-S`).
* **Correction to the original session summary.** The "manifest-registered subagent site
  bindings" wording above meant the registry came from the manifest; it is disk-first, joined
  to the manifest for provenance (workspace-authored agents have none). Plan B2 resized
  `S` to `M` (volume only). The purity claim for the resolver, the A4 CLI, and the B2
  builder is now asserted by tests (guard harness and tree snapshots), not stated.
* **Review records.** Addenda appended to both plan-review records; earlier cycles and the
  PASS verdicts are untouched.
* **Deferred scope expansions:** none. Every change stayed inside this staging's artifacts.
* Still open for the operator: OQ5 and OQ8 (see the previous addendum).

## Addendum 2026-10-12: PR #513 review-fix cycle 2

Append-only. Copilot review `5494415746` on PR #513 (HEAD `e0051e68`) raised three new
threads, all in this staging's own artifacts. Stage verified each against the repository,
fixed it at the root in a separate local commit, and re-ran a delta check (single-agent
declared degradation, same as before). No push, no PR comment, no thread resolution: the Role
Boundary reserves those for the Orchestrator. The repository test suite was not run (Stage
boundary); evidence came from reading the tests and from scratch probes that left no file in
the workspace. All times UTC; the cycle counter is 2 of the 3-cycle limit.

| UTC | Phase | Commit |
|---|---|---|
| 2026-10-12T18:07:34Z (+0s) | Session start; Role Boundary re-read; tool gate, index sync | |
| 2026-10-12T18:14:13Z (+6m39s) | Verification of all three findings against schemas, tests, contracts, plans | |
| 2026-10-12T18:18:44Z (+4m31s) | Thread `PRRT_kwDORzpWpM6rkjC9`: `model_routing` allowlist and unknown-key check | `e21a9502` |
| 2026-10-12T18:28:35Z (+9m51s) | Thread `PRRT_kwDORzpWpM6rkjDk`: atomic 1.2.0 cut-over | `789f5748` |
| 2026-10-12T18:36:35Z (+8m00s) | Thread `PRRT_kwDORzpWpM6rkjEC`: shared raw-YAML guard | `7ba1193a` |
| 2026-10-12T18:37:51Z (+1m16s) | Review and plan addenda, this memory note | the addenda commit |

* **Finding 1 (unknown `model_routing` keys): confirmed.** `model_routing` sets no
  `additionalProperties` in the root schema or the 1.1.0 mirror. Decision: an allowlist (the
  ten existing keys plus `routes` and `bindings`) in the **1.2.0 schema only**, so the published
  1.1.0 mirror stays byte-identical and 1.1.0 configs with extra keys keep validating; a named
  `routing_unknown_keys` check fails at 1.2.0 and warns (never changes `ok`) below, the same
  gate as the anchor check. The constant `MODEL_ROUTING_KNOWN_KEYS` (resolver, B1) is the
  single allowlist and a sync test ties it to the mirror. The `subagents` block the review
  mentions is the baseline's proposed shape; this repository's dogfood config and template
  carry no such key, so the evidence is the schema probe, not an installed workspace.
* **Finding 2 (deliberately red B4/B5 boundary): confirmed.** The four B3 test modules
  validate current-version fixtures and the dogfood config against the root and the current
  mirror; the contract version stays 1.1.0 until B5, so a root const of 1.2.0 in B4 made them
  red. B4 now only publishes the unreferenced mirror; B5 is the single atomic cut-over
  (resized `S` / `low` to `M` / `medium`). Edges: removed `208.005-T` on `208.004-T`, added
  `208.006-T` on `208.004-T`. Audit of the other R1-B units found no second occurrence.
* **Finding 3 (CLI skips the alias guard): confirmed.** `yaml.safe_load` yields plain,
  schema-valid dicts for anchors, aliases, and merge keys; `yaml.parse` still shows them.
  New R1-A task `207.006-T` (unit A2a, `S` / `medium`) owns one shared function called by the
  A4 CLI (before schema validation, exit `2`) and by R1-B B6; a 1.1.0 config with aliases is
  not rejected (D2). Edges: `207.006-T` on `207.002-T`, `207.004-T` on `207.006-T`; `214-S`
  manifest order is `207-F`, `.001`, `.002`, `.003`, `.006`, `.004`, `.005`. No task-level
  cross-shipment edge was added (the shipment edge `215-S` after `214-S` carries it, matching
  B1's dependency on the R1-A resolver).
* **Graph checks.** Both manifests honor every task edge, the task graph is acyclic, and
  `autoharness gate dag-readiness --json` reports `cycle_detected: false` and
  `ready_set: [209-S]`. `214-S` now holds six tasks (`M:4`, `S:2`); `215-S` thirteen
  (`M:8`, `S:5`). The harvested counts in the sections above describe the original state.
* **Review records.** Cycle 2 addenda appended to both plan-review records; earlier cycles and
  both PASS verdicts are untouched and still hold (delta findings A-F9 to A-F11 and B-F11 to
  B-F13, all P3).
* **Deferred scope expansion:** stash `44CB5AE1` (P-021 C2): `workspace-discovery` Phase 0 (and
  the install, tune, and Orchestrator wording that B8, B9, and A5 already rewrite) validates
  an operator config against the root schema file, which carries const 1.2.0 after B5. It is a
  different contract surface, so it is out of scope here; it must route through `deliberate`
  (C6) and be decided before `215-S` is claimed.
* Still open for the operator: OQ5 and OQ8 (see the earlier addenda).
