---
title: "autoharness v1.6.0 release chain: four dependency-gap fixes, engine-line verification and a ready-to-tag release cut"
description: "Umbrella implementation plan staging six linearly ordered shipments (G1 agent-engram guidance, G4 optional-pack assertions, G2 backlog CLI first-class peers, engine-line verification, G3 docs-only task route, release cut) so a new session can run Ship through the chain to a ready-to-tag v1.6.0. One plan, one section per shipment, explicit blocks edges after the shipped 216-S."
date: 2026-10-19
status: reviewed
deliberation: "042-DL (docs/decisions/2026-10-19-docs-only-verification-gated-disposition-deliberation.md; G3 only)"
stash_entries: [29D0ACB7, 3DB3AE91, 9CC3C661, 9AF294A4, E89674F1, 03427861]
follow_up_stash: [B60A27EC]
requires_plan_hardening: "yes"
plan_hardening_status: "hardened"
plan_hardening_record: "docs/plans/2026-10-19-release-1-6-0-staged-chain-plan.md#plan-hardening"
plan_review_verdict: "PASS"
plan_review_cycles: 2
tags: [plan, release, v1.6.0, dag, engram, backlogit, p-012, p-002, capability-packs, dogfood-parity]
---

## Problem Frame

The operator wants a releasable autoharness v1.6.0 as soon as possible. Downstream workspaces (the sibling
`backlogit` and `engram` repositories, both read-only here) found four dependency gaps in autoharness 1.5.0 plus
the already-merged unreleased work (routing catalog 1.2.0, agent-intercom removal, P-002.8, cascade-close
recovery). This plan stages the remaining work as a chain of shipments that Ship can run unattended, ending in a
ready-to-tag release. The git tag and publish step is operator-only.

### Code and sibling-repo facts (read 2026-10-19; sibling repos read-only)

| Concern | Fact | Source |
|---|---|---|
| G1 | `query_graph_neighborhood` is an internal engram helper behind the single registered `query_graph` tool; `query_graph` takes `operation` = `neighborhood` / `find_path` / `transitive_closure` with `root`, `from`, `to`, `direction`, `max_depth`, `max_nodes`, `edge_types`. Engram's catalog has 21 registered tools; our template also names `index_git_history`, which is only present under the `git-graph` build feature | `engram/docs/cli-mcp-parity.md` 42, 73-77; `engram/docs/mcp-tool-reference.md` 75-82; `engram/src/bin/engram.rs` 265-295; `engram/tests/fixtures/mcp_tool_catalog.expected.json` |
| G1 sites | Template lines 26, 56-57, 63-70 (and 117/121 for `index_git_history`); installed mirror same lines; `.claude/instructions.md` 18-19 (hand-maintained, no template); `tests/test_agent_engram_instruction.py` 57 pins the wrong name | `git grep` |
| G2 | backlogit 1.11.0 CLI has `hooks poll --consumer-id`, `hooks ack --consumer-id --seq`, `comment add <id> --actor --comment`, `memory save`, `shipment add <shipment> <item>`, `stash edit/get/archive`, `deliberate`, `metadata`. `backlogit shipment dispose` and the MCP tool `backlogit_dispose_shipment` exist in neither v1.11.0 nor the HEAD checkout (`v1.11.0-829`): backlogit tasks 194.004-T and 194.006-T and features 194-F/185-F are still `queued` | `backlogit --help`; `backlogit/.backlogit/queue/194.006-T.md`; `git grep dispose internal/cli internal/mcp` returns nothing |
| G2 policy | P-012 step 4 treats the registry `cli_command` as a fallback used only after an MCP failure | `templates/policies/workflow-policies.md.tmpl` 407-434 |
| 188-S | backlogit HEAD queue view releases a shipment `blocks` edge only when the predecessor is `shipped`; an archived shipment predecessor without a resolver stays blocking. This is not in v1.11.0 | `backlogit/internal/core/queue.go` diff v1.11.0..HEAD |
| G3 | No gate code reads `harness-ready`; it is template/policy text (P-002 line 46, Ship template 344-349/413/487, harness-architect Step 6, build-feature line 12). `harness-surface:none` already resolves to "no surfaces required" | `git grep`; `src/autoharness/harness_surfaces.py` |
| G4 | `FOUNDATION_ASSERTIONS` entry `copilot_remote_operator_guidance` unconditionally requires `### agent-engram` (verify_workspace.py 436-444). `PACK_ASSERTIONS` already holds conditional per-pack assertions. The template renders `## Remote Operator Integration` / `### agent-engram` unconditionally (copilot-instructions.md.tmpl 185-193). The template engine has no conditionals; pack sections rely on prose guards and installer pruning | `src/autoharness/verify_workspace.py`; template |
| Engine line | `VERIFIED_CASCADE_ENGINE_MINOR_LINES = {(1, 11)}`; unknown lines already return `UNVERIFIED` and select SAFE_CLOSE (tests exist for `1.12.0`). backlogit HEAD changes `archive.go` (+410), `shipment.go`, `queue.go` since v1.11.0 (item-log lock ordering, CAS-guarded stash side effects, shipped-only queue readiness) | `src/autoharness/gates/shipment_closure.py` 546-560; backlogit `git diff v1.11.0 HEAD` |
| Release | Version sites at 1.5.0: `pyproject.toml`, `src/autoharness/__init__.py` fallback, `plugin.json`, `.github/plugin/marketplace.json` (two), `uv.lock`. `release.yml` requires tag == pyproject version and a CHANGELOG section matching `## 1.6.0` (optionally bracketed). CI installs backlogit pinned `v1.9.0` | files; `.github/workflows/*.yml` |

## Requirements Trace

| # | Operator requirement | Shipment |
|---|---|---|
| R1 | G1: registered `query_graph` guidance, no Cypher-style wording, mirror + checksums, sweep of templates/.github/docs/tests/src | S1 |
| R2 | G4: pack assertions and rendered content conditional on enabled packs, tests with and without each pack | S2 |
| R3 | G2: registry hook CLI entries, `dispose` handling, first-class CLI peer P-012, tests, 188-S alignment note | S3, S4 |
| R4 | Engine line: keep 1.11 supported, document the 1.12 probe, never widen without a probe | S4 |
| R5 | G3: deliberation, policy, templates, skills, checker, tests, fail-closed and auditable | S5 |
| R6 | Release cut: versions, CHANGELOG, release notes, upgrade guide, readiness checklist, operator-only tag | S6 |
| R7 | Downstream rollout follow-up, non-blocking | stash B60A27EC |

## Scope Boundaries

* No Ship invocation, no implementation, no change to `references/` submodules, `backlogit` or `engram` repositories.
* `backlogit_dispose_shipment` is not registered (not implemented upstream); it is recorded as deferred. Registering
  an operation the engine cannot execute would make the registry lie (fail-closed rejection, decision D-S3-1).
* No widening of the verified engine line beyond 1.11 (decision D-S4-1).
* Existing queued shipments 207-S and 217-S are untouched. 217-S is an unrelated `dag-root`; it has no edge to this
  chain and creates no ordering conflict (P-001 serializes execution; the chain is claimed in order and 217-S is
  outside the dark-mode scope).
* Stash candidates for a post-release shipment, not folded in: 179E121C (verify_workspace frontmatter model-routing),
  072B7DF6 and 5C870EB2 (upstream template wording defects; 5C870EB2 is high priority and safety-adjacent, so the
  operator may prefer to move it before S6).

## Shipment DAG and Ordering Rationale

```text
216-S (shipped) <-blocks- S1 <-blocks- S2 <-blocks- S3 <-blocks- S4 <-blocks- S5 <-blocks- S6
```

| Pos | Shipment | Gap | Risk | Why here |
|---|---|---|---|---|
| 1 | S1 | G1 | low | Smallest, template wording plus one guard test; lands first so partial progress is releasable and the new guard protects later template edits |
| 2 | S2 | G4 | medium | Narrow (`verify_workspace.py` plus one template); must precede S3 because S3 adds registry checks to the same verifier and the pack-conditionality sweep gives S3 a stable baseline |
| 3 | S3 | G2 | medium | Policy-wide P-012 amendment across Stage/Ship/Orchestrator templates; independent of G3, ordered before it so each policy-version bump (1.38.0, then 1.39.0) lands once and sequentially |
| 4 | S4 | engine line | low | Docs plus pin tests; placed before G3 so every small independent fix is already merged: if G3 stalls, the operator re-points the S6 edge at S4 and still releases |
| 5 | S5 | G3 | high | Largest and riskiest (policy, three template families, a new CLI and schema); last before the cut |
| 6 | S6 | release | medium | Needs everything merged; ends at a ready-to-tag state |

This differs from the suggested order only by placing the engine-line shipment ahead of G3 (the reason is in the
table). Edges are real ordering constraints and not only P-001 serialization: S2/S3 and S3/S5 edit
`templates/policies/workflow-policies.md.tmpl`, the Ship template and `.autoharness/harness-manifest.yaml` checksums;
S1/S2 edit `.autoharness` mirrors and manifest; S6 depends on all.

Placement: the first shipment (S1) gets `blocks` on 216-S (shipped, closure READY), not `dag-root`.

## Shared Conventions (every task)

* One template family or concern per task; dogfood mirror under `.github/` and manifest checksum refresh travel with the
  template edit in the same task (parity tests enforce this).
* Every task is test-first through harness-architect (RED roster per P-004) unless it carries `harness-surface:none`.
* Canonical gate: `PYTHONPATH=src python -m unittest discover -s tests`; Markdown gate: `markdownlint "**/*.md"` (P-008).
* Version history rows in the policy registry use `{{DATE}}` in the template and the concrete UTC date in the mirror.
* Manifest checksums in `.autoharness/harness-manifest.yaml` are computed from the LF-normalized committed git blob
  (`git cat-file -p :<path>`), never from a raw Windows working-tree read and never typed by hand, and the entry's
  `note` records the refreshing task (the convention every prior shipment followed, for example 139-S/130.005-T).
* Sizing uses `size` and `complexity` separately (ruleset `ah-stage-sizing-v1`, source `agent`).

## S1: G1 agent-engram guidance names only registered engram tools

Stash 29D0ACB7. Covering feature F1. Risk low. Est. Ship effort 2-3 h.

* **S1-U1 (S, low)**: rewrite the Search Protocol in `templates/instructions/agent-engram.instructions.md.tmpl`
  (lines 26, 56-57, 63-70, 117, 121) and the installed mirror `.github/instructions/agent-engram.instructions.md`:
  one `query_graph` row ("structured neighborhood, find_path and transitive_closure operations over the combined
  code and backlog graph"), delete the `query_graph_neighborhood` row and the "Cypher-style" sentence, add a short
  parameter note (`operation`, `root`, `from`, `to`, `direction`, `max_depth`, `max_nodes`, `edge_types`), mark
  `index_git_history` as available only when the engram build enables `git-graph`. Update
  `tests/test_agent_engram_instruction.py` (flip the line-57 assertion). Refresh manifest checksums.
  AC: neither file contains `query_graph_neighborhood` or `Cypher`; both name the three operations; parity test green.
* **S1-U2 (XS, trivial)**: `.claude/instructions.md` lines 18-19 (hand-maintained Claude surface, no template): same
  correction. AC: file names only registered tools; new assertion in the guard test (U3) covers it.
* **S1-U3 (S, low)**: guard test `tests/test_engram_tool_surface_guard.py`: pinned list of the 21 registered engram
  tools (source: engram catalog fixture at engram commit `006af541`, with a documented refresh procedure) plus the
  declared feature-gated set; every backticked engram tool name in the template, mirror and `.claude/instructions.md`
  must be in one of the two sets; the forbidden tokens `query_graph_neighborhood` and `Cypher-style` must not appear in
  `templates/`, `.github/` (except archived), `.claude/`, `docs/*.md` or `src/`. Depends on U1, U2.

Done proves: no document, template or test steers an agent to an unregistered engram tool, and a future drift fails CI.

## S2: G4 capability-pack assertions and rendered content conditional on enabled packs

Stash 3DB3AE91. Covering feature F2. Risk medium. Est. Ship effort 4-5 h.

Audit result (this session): the only pack-specific assertion in `FOUNDATION_ASSERTIONS` that names pack content is
`copilot_remote_operator_guidance` (`### agent-engram`). The `continuous-learning` tokens (auto-tune and tune-harness
skills) and the `browser-verification` tokens (install-harness skill) check text in always-installed skills, not pack
overlays, so they stay; `backlogit_claim_shipment` checks the Ship agent, which only exists in the two-agent model. U2
re-verifies this empirically. `schema_contracts.py` lines 54-58 hold the removed-pack table (`agent-intercom`), not an
assertion, and is only covered by the guard in U2.

* **S2-U1 (S, medium)**: `src/autoharness/verify_workspace.py`: move the `### agent-engram` and `sync_workspace`
  requirement into `PACK_ASSERTIONS["agent-engram"]` as `copilot_remote_operator_guidance`; keep the heading
  `## Remote Operator Integration` conditional with it. Update `tests/test_verify_workspace.py` (2095-2143).
  AC: a workspace without agent-engram passes with no `### agent-engram` heading; with the pack enabled the
  assertion still fails when the heading is missing.
* **S2-U2 (M, medium)**: parametrized with/without test over the six packs (`agent-engram`, `backlogit`,
  `graphtor-docs`, `browser-verification`, `continuous-learning`, `strict-safety`) building a minimal rendered
  workspace per case and asserting that a disabled pack yields no pack-derived foundation failure and an enabled pack
  with its content removed still fails; static guard that no `FOUNDATION_ASSERTIONS` entry names a heading or tool that
  belongs to a `PACK_ASSERTIONS` pack and that every `PACK_ASSERTIONS` key is in `SUPPORTED_CAPABILITY_PACKS`. Fix any
  further unconditional assertion the sweep finds. Depends on U1.
* **S2-U3 (S, low)**: `templates/foundation/copilot-instructions.md.tmpl`: scope `## Remote Operator Integration` /
  `### agent-engram` as pack content (explicit pack-scope marker comments and an install-harness rule that disabled
  packs' marked sections are pruned post-render; template engine has no conditionals), update the install-harness skill
  composition text, the dogfood mirror `.github/copilot-instructions.md` and checksums. Depends on U1.

Done proves: a workspace lacking any optional pack verifies green, one with the pack still fails closed when the pack
content is missing, and rendered templates carry explicit pack scope.

## S3: G2 declared backlog CLI operations are first-class peers of MCP

Stash 9CC3C661. Covering feature F3. Risk medium. Est. Ship effort 6-8 h.

Decisions: **D-S3-1** `backlogit_dispose_shipment` and `backlogit shipment dispose` are not registered (not
implemented upstream). The compatibility matrix gets a "deferred until backlogit 194-F ships" row and the follow-up
stash entry (below) tracks it; when upstream ships it the entry is Stage-only per backlogit's G-B condition.
**D-S3-2** CLI-first wording is scoped as in the engram handoff (equal supported surfaces per declared operation,
observable `TOOL_OK: {operation} via {mcp|cli}`, `TOOL_DEGRADED` with failed and selected surfaces, `TOOL_UNAVAILABLE`
when neither works, never an undeclared command or filesystem edit, argument elements not shell interpolation,
first-write result checked before retrying a non-idempotent mutation on another surface). `log_telemetry` stays
MCP-only. **D-S3-3** hook ack stays concrete-sequence-only; derived signals are never acknowledged.

* **S3-U1 (M, low)**: `templates/backlog/registries/backlogit.registry.yaml` and installed
  `.autoharness/backlog-registry.yaml`: add `cli_command` for `poll_hook_events`
  (`backlogit hooks poll --consumer-id {{consumer_id}}`), `ack_hook_events`
  (`backlogit hooks ack --consumer-id {{consumer_id}} --seq {{seq}}`), and, after verifying each against the installed
  CLI `--help`, `append_comment` (`backlogit comment add {{id}} --actor {{actor}} --comment {{comment}}`),
  `save_memory` (`backlogit memory save ...`), `add_to_shipment` (`backlogit shipment add {{shipment_id}} {{item_id}}`),
  `stash_edit`, `stash_get`, `deliberate`, `get_metadata_catalog`/`list_types`/`list_templates`/`get_wit_metadata`
  (`backlogit metadata ...`). No entry for `log_telemetry` or `dispose_shipment`. Checksum refresh. Schema
  `schemas/backlog-tool-registry.schema.json` only if a field is rejected.
* **S3-U2 (M, medium)**: P-012 amendment in `templates/policies/workflow-policies.md.tmpl` and mirror: per-operation
  equal surfaces per D-S3-2/D-S3-3, version row 1.38.0. Tests extend the P-012 contract tests.
* **S3-U3 (M, medium)**: Step 0.0 / Step 1 wording in `templates/agents/_stage.agent.md.tmpl`,
  `_ship.agent.md.tmpl`, `_orchestrator.agent.md.tmpl` and mirrors: per-operation surface choice replaces "prefer MCP"
  and "CLI only on MCP failure"; hook protocol retained. Depends on U2.
* **S3-U4 (S, low)**: `templates/instructions/backlogit.instructions.md.tmpl` / `backlog-integration.instructions.md.tmpl`,
  `docs/backlog-integration.md`, `docs/backlogit-compatibility-matrix.md` (+ mirrors): surface-choice text, the
  dispose deferred row, the 188-S shipped-only readiness note (the Orchestrator already calls the queue listing a first
  filter and `pre_claim` the sole authority, so no change to queue-selection text is needed; the note records that
  backlogit 1.12 hides blocked shipments earlier). Depends on U2.
* **S3-U5 (M, medium)**: verification: `verify-workspace` registry checks assert both hook operations carry
  `cli_command` in a rendered registry, every `cli_command` operation names a CLI that exists in the pinned
  command inventory fixture, and a static test fails any template that restates "CLI only on MCP failure" for a
  declared backlog operation; contract tests for hook poll output preserving `events` and `derived_signals` and ack
  limited to concrete sequence numbers, and fail-closed when neither surface is declared. Depends on U1-U3.

Done proves: a Ship in a host without MCP can run the hook gate through declared CLI commands, selection is observable,
and neither-surface-works fails closed.

## S4: Backlogit engine-line verification (1.11 pinned, 1.12 only after a probe)

Stash 9AF294A4. Covering feature F4. Risk low. Est. Ship effort 2-3 h.

Decision **D-S4-1**: backlogit HEAD is `v1.11.0-829-ga623b0af` and carries no `1.12` marker; the next release line is
unknown and the engine behavior that P-015 depends on changed (archive/ship lock ordering, CAS stash effects,
shipped-only queue readiness). So `(1, 11)` stays the only verified line, and 1.12 support requires a documented probe.

* **S4-U1 (S, low)**: new `docs/engine-line-verification.md` (probe procedure: build or install the candidate,
  `autoharness shipment cascade-close --classify-only` and the engine probe on a throwaway workspace, compare
  `ArchiveItem`/`ShipShipment` cascade semantics against the verified `archive.go` facts, update the constant,
  P-015 token and the shipment-reconcile skill together; what must not be done: widening by version number alone),
  rows in `docs/backlogit-compatibility-matrix.md` (v1.11.0 verified, HEAD unverified with the three change areas,
  dispose deferred, 188-S readiness), and the CI pin finding (`ci.yml` installs backlogit `v1.9.0`; record whether the
  tests need a newer pin, no `ci.yml` change here).
* **S4-U2 (S, low)**: pin tests: `VERIFIED_CASCADE_ENGINE_MINOR_LINES == {(1, 11)}`; `1.12.0`, `1.12.0-rc1`,
  `1.11.0-829-ga623b0af` (build metadata) and a missing version all assess `UNVERIFIED`; the runbook names the same set
  as the constant (drift guard); the Orchestrator template still states the queue listing is not the sole eligibility
  authority. Depends on U1.

Done proves: v1.11 stays supported, 1.12 cannot be silently verified, the procedure to widen is documented and tested.

## S5: G3 verification-gated docs-only task route

Stash E89674F1. Covering feature F5. Risk high. Est. Ship effort 10-13 h. Decisions D-1..D-5 and assumptions AS-1..AS-6 are in
the deliberation. Hardening items H1-H6 below apply.

* **S5-U1 (M, medium)**: `src/autoharness/docs_only_check.py` pure checker per deliberation D-1 item 2/3 and D-3 (path
  normalization, docs root fail-closed, deny list, case-insensitive compare, union of `git diff --name-status
  <start-sha>`, staged, unstaged and untracked paths, rename/copy sources). Tests with temp git repositories.
* **S5-U2 (S, medium)**: CLI `autoharness harness docs-only-check --start-sha --owned --docs-root [--json]`, exit
  0/1/2, JSON schema `schemas/docs-only-check.schema.json` (+ versioned dir and `SCHEMA_CONTRACTS` entry),
  `docs/gates-reference.md` section. Depends on U1.
* **S5-U3 (M, medium)**: P-002 and P-004 amendment in `templates/policies/workflow-policies.md.tmpl` and mirror
  (route qualification, exclusive labels, verification record, anti-loophole, version row 1.39.0). Code route text is
  unchanged except for the explicit "unchanged" sentence. Depends on S3 having landed (sequential policy edits).
* **S5-U4 (M, medium)**: `templates/agents/_ship.agent.md.tmpl` and mirror: Step 2 queue filter and scaffold list
  accept exactly the route matching qualified ownership; Step 3 admit; Step 4.1 start-SHA capture; completion gate runs
  the checker and the recorded verification gates; mismatch halts as P-002 violation with P-005 telemetry. Depends on
  U2, U3.
* **S5-U5 (M, medium)**: `templates/skills/harness-architect/SKILL.md.tmpl` and mirror (classify, validate record,
  apply only the route label, no stub/RED) plus the label vocabulary in `templates/backlog/config.yml.tmpl` and the
  installed `.autoharness` equivalent. Depends on U3.
* **S5-U6 (S, low)**: `templates/skills/build-feature/SKILL.md.tmpl` and mirror (docs-route execution with recorded
  commands) and the `harvest` skill / Stage wording (declare `harness-surface:none` on qualifying candidates; Stage
  never applies either route label). Depends on U3.
* **S5-U7 (S, low)**: interaction test: a task with `harness-surface:none` plus `harness-verification-gated` resolves
  through `autoharness harness resolve` with no surface required; text-contract tests across policy, Ship,
  harness-architect and build-feature that both labels never coexist and the code route is unchanged. Depends on U4-U6.

Done proves: a docs-only task can be claimed and completed without `harness-ready` or RED, only when the owned paths
qualify and the diff is provably confined to them; any violation halts; code tasks are unchanged.

## S6: Release cut for v1.6.0 (ready to tag, tag is operator-only)

Stash 03427861. Covering feature F6. Risk medium. Est. Ship effort 5-7 h.

* **S6-U1 (S, low)**: bump to `1.6.0` in `pyproject.toml`, `src/autoharness/__init__.py` fallback, `plugin.json`,
  `.github/plugin/marketplace.json` (both), `uv.lock` (regenerate with `uv lock` when `uv` is available, otherwise edit
  only the editable `autoharness` package version and confirm with `uv lock --check`); add a version-consistency test
  over all sites; leave the
  dogfood `.autoharness/harness-manifest.yaml` `autoharness_version` to the tool-managed refresh (record the
  stale `1.4.11`).
* **S6-U2 (M, low)**: finalize `CHANGELOG.md`: `## Unreleased` becomes `## 1.6.0 - <UTC date at ship time>`; entries
  for 211-F/218-S, 208-F/215-S, 209-F/216-S, 205-F/212-S (P-002.8), 206-F/213-S, 207-F/214-S, and G1-G4 plus the
  engine-line note; a test reproduces the `release.yml` awk extraction and requires a non-empty body.
* **S6-U3 (M, low)**: `docs/releases/1.6.0-release-notes.md` and `docs/releases/1.6.0-upgrade-guide.md` for
  downstream workspaces (backlogit and engram): reinstall/tune steps, config schema `1.1.0` to `1.2.0`,
  agent-intercom removal tolerance, engram needs a backlogit with the `scheduler_baseline_claim` marker producer, the
  registry `features.scheduler_baseline_claim` enable and tune for P-002.8, CI pin `autoharness==1.5.0` to
  `1.6.0`, removal of local workarounds (140-F, 7DE66A04, 1AD161B8). Link from README.
* **S6-U4 (M, medium)**: `docs/releases/1.6.0-release-readiness-checklist.md` executed with evidence in
  `docs/releases/1.6.0-readiness-evidence.md`: full unittest gate, markdownlint, `autoharness verify-workspace`
  dogfood, `uv build` plus `twine check` and wheel content check (templates and schemas present), `release.yml` dry
  review (tag/version check, changelog extraction, publish path). Ends with the explicit operator instruction: merge,
  pull `main`, confirm clean, create and push `v1.6.0` (annotated) yourself. No agent pushes a tag or publishes.

Done proves: every version site agrees, the changelog extracts for release.yml, the upgrade path is documented, all
gates pass on the release commit, and the only remaining action is the operator tag.

Guardrails: Ship must not create a tag, run `git push --tags`, or trigger `release.yml`. Stash B60A27EC (downstream
rollout) must stay active; the closure must not archive it.

## Backlog Mapping (harvested 2026-10-20)

| Shipment | Covering feature | Tasks | Blocks (predecessor) |
|---|---|---|---|
| 219-S (S1, G1) | 212-F | 212.001-T, 212.002-T, 212.003-T | 216-S (shipped) |
| 220-S (S2, G4) | 213-F | 213.001-T, 213.002-T, 213.003-T | 219-S |
| 221-S (S3, G2) | 214-F | 214.001-T .. 214.005-T | 220-S |
| 222-S (S4, engine line) | 215-F | 215.001-T, 215.002-T | 221-S |
| 223-S (S5, G3) | 216-F (+ 042-DL link) | 216.001-T .. 216.007-T | 222-S |
| 224-S (S6, release) | 217-F | 217.001-T .. 217.004-T | 223-S |

Unit mapping: S1-U1..U3 = 212.001-T..212.003-T; S2-U1..U3 = 213.001-T..213.003-T; S3-U1..U5 = 214.001-T..214.005-T;
S4-U1..U2 = 215.001-T..215.002-T; S5-U1..U7 = 216.001-T..216.007-T; S6-U1..U4 = 217.001-T..217.004-T. Stash entries
29D0ACB7, 3DB3AE91, 9CC3C661, 9AF294A4, E89674F1 and 03427861 were archived as consumed; B60A27EC stays active.

## Dependency Graph

```text
S1-U1 -> S1-U3 <- S1-U2
S2-U1 -> S2-U2 ; S2-U1 -> S2-U3
S3-U1 ; S3-U2 -> S3-U3 ; S3-U2 -> S3-U4 ; (S3-U1,U2,U3) -> S3-U5
S4-U1 -> S4-U2
S5-U1 -> S5-U2 -> S5-U4 ; S5-U3 -> S5-U4/U5/U6 -> S5-U7
S6-U1 -> S6-U2 -> S6-U3 -> S6-U4
Shipments: 216-S <- S1 <- S2 <- S3 <- S4 <- S5 <- S6 (blocks)
```

## Plan Hardening

Hardening record for P-006 (`requires_plan_hardening: yes`: schemas, CLI distribution, multiple template families,
policy text). Single-agent pass; findings and the resulting plan changes:

* **H1 Fail-closed docs route.** Ownership, normalization and deny list are evaluated by one function (U1) used by
  harness-architect, Ship and the completion gate; unresolved or ambiguous input is exit `2`, never a pass.
* **H2 No self-authorized override.** The docs-route label is applied only by harness-architect after qualification;
  Ship re-checks and never applies it. A task cannot change route after implementation starts.
* **H3 Mirror and checksum parity.** Every template edit in S1-S3 and S5 includes its mirror and checksum refresh in the same task;
  existing parity tests are the gate. Checksums follow the blob-derived convention in Shared Conventions.
* **H4 Sequential policy edits.** S3 (1.38.0) before S5 (1.39.0); the S5 policy task depends on S3 having merged.
* **H5 Registry truthfulness.** A registered `cli_command` must exist in the pinned CLI inventory (U5); dispose is not
  registered.
* **H6 Release safety.** The release shipment has no tag/push capability by contract (guardrail above) and ends at an
  operator instruction; evidence records are written by commands, not asserted.
* **H7 Rollback.** Each shipment is independently revertible by a single merge-commit revert; S6 is revertible before
  the operator tags.

## Plan Review

dispatch_mode: single-agent-declared-degradation

decision: PASS

Standalone record: `docs/reviews/2026-10-19-release-1-6-0-staged-chain-plan-review.md` (cycle 1: no P0/P1, three P2
findings fixed in this revision; cycle 2: PASS).
