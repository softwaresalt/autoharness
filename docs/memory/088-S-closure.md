---
type: operational-closure
shipment: 088-S
feature: 076-F
tasks:
  - 076.001-T
  - 076.002-T
  - 076.003-T
  - 076.004-T
  - 076.005-T
  - 076.006-T
  - 076.007-T
  - 076.008-T
  - 076.009-T
  - 076.010-T
title: "Operational Closure — graphtor-docs as first-class full-preset capability pack"
status: READY_WITH_FOLLOWUPS
staging_pr: 205
staging_merge_commit: 70b33ba1a9ae70ee3c3726f0bdd760fe8c2ec8ae
feature_pr: 206
feature_merge_commit: f0946b926920abb5f85c8f0aa0d47c2280dc8a51
closed_at: 2026-07-12T02:29:35Z
stash_origin: CA76F48B
doc_type: memory
source: docs/memory/088-S-closure.md
tags:
  - capability-packs
  - graphtor-docs
  - full-preset
  - schema-parity
  - dark-factory
  - closure
---

# Operational Closure — 088-S

## Shipment

Complete the `graphtor-docs` capability pack to `agent-engram` parity as a
first-class member of the `full` preset. graphtor-docs was previously the only
pack with `default_in_preset: []` and was missing from the versioned schemas and
from the installation and user-facing surfaces that seed and describe the `full`
preset (install-harness inputs/defaults/prose, install prompt, auto-mergeinstall
agent, README and getting-started catalogs, foundation overlays), while its
sibling retrieval-enforced pack `agent-engram` was fully woven into `full`.
graphtor-docs was already documented in `docs/capability-packs.md` (catalog entry
and formal-overlay section) — a file PR #206 did not change.

Seeded from stash `CA76F48B` ("Add graphtor as a capability pack in the full
suite"). Feature `076-F`, tasks `076.001-T`..`076.010-T`, shipment `088-S`.

## What shipped

- Staging PR **#205** → merged as merge commit `70b33ba` (backlog structure:
  feature 076-F + 10 tasks + shipment 088-S; 3 Copilot rounds — 8, then 2,
  then 4 threads).
- Feature PR **#206** → merged to `main` as merge commit
  `f0946b926920abb5f85c8f0aa0d47c2280dc8a51` (2 parents: `70b33ba` base +
  `bc90c19` head; **P-009 merge-commit satisfied**).

Change surface (excluding `.backlogit/`):

- **Preset wiring**: `templates/packs/capability-pack-registry.yaml`
  graphtor-docs `default_in_preset: [] → ["full"]`; install-harness SKILL input
  list + full-preset default table + prose.
- **Versioned schema parity**: `schemas/harness-config/1.0.0.schema.json`
  (`capability_packs` enum + `graphtor_docs` config block) and
  `schemas/workspace-profile/1.0.0.schema.json` (`graphtor_docs` block), with
  their `graphtor_docs` blocks (and the harness-config `capability_packs` enum)
  brought byte-for-byte deep-equal to the corresponding blocks in the root
  schemas. This scoped parity does not reconcile unrelated pre-existing
  divergence — the versioned profile schema still lacks the root's top-level
  `copilot_review` property (see follow-up 3).
- **User-facing parity**: install-harness prompt, auto-mergeinstall agent (pack
  list + post-install reminder), README pack catalog, getting-started
  (full-preset command, catalog, overlay prose, instructions tree, verify +
  first-use steps), copilot-instructions overlay block.
- **Foundation overlay parity**: constitution template + condensed dogfood
  mirror; AGENTS.md.tmpl overlay section + `agent-engram + graphtor-docs`
  interaction row.
- **Research-skill routing**: brainstorm / deliberate / spike / impl-plan
  templates (Engram = code relationships; graphtor-docs = documentation/API
  concept lookup).
- **TDD**: `tests/test_graphtor_docs_full_suite.py` (6 tests — schema-parity
  deep-equal + preset membership).
- **Manifest**: 5 refreshed CRLF-normalized checksums for touched dogfood
  artifacts.

## Adversarial review (pre-PR, per operator mandate)

Dual review of code and design vs `origin/main` before opening the PR:

- **code-review**: no significant issues; independently verified schema
  byte-equality, checksum recomputation, parity completeness, no false-green
  tests, no unresolved placeholders.
- **rubber-duck**: no blockers; non-blocking findings evaluated. Actioned:
  deploy-harness preflight graphtor parity; AGENTS generic interaction-row
  coherence; schema-parity test hardened to deep-equal.

## Copilot review (feature PR #206)

- **Round 1** (5 threads): getting-started `full` example passed an explicit
  `capability_packs` override that omitted `agent-engram`/`backlogit` (replaced
  with bare `preset=full`); deploy-harness preflight (×4) checked `PATH` only,
  missing the registry-documented `.graphtor/bin/` local location (added). All
  replied after fix-push and resolved via GraphQL.
- **Round 2** (4 threads): the round-1 local-bin check accepted directories
  (`-x` / `Test-Path` also match dirs) — restricted both candidates to regular
  files (`-f && -x` in sh; `-PathType Leaf` in ps1). All replied + resolved.
- **Round 3**: `autoharness gate copilot-review` → **SATISFIED** (complete for
  HEAD `bc90c19`, zero unresolved Copilot threads).

## Runtime verification (depth: composition — no live server)

graphtor-docs is externally tooled; a missing local server DEGRADES
(`GRAPHTOR_UNAVAILABLE` fallback), it does not fail. Verification surface is
harness composition + schema validity + checksum reconciliation, exercised by:

- `python -m pytest tests/` → **506 passed, 138 subtests passed**.
- Dogfood `verify_workspace(".", ".")`:
  `capability_pack_enforcement ok: True`, `unresolved_placeholders: 0`, all
  touched artifacts `unchanged`.
- CI on HEAD `bc90c19`: `ci gate` = pass, `detect code changes` = pass,
  `test` = pass.

## Releasability

**READY_WITH_FOLLOWUPS.** §1.9 gate passed for HEAD `bc90c19` (Reviewed HEAD
match, outcome `READY_WITH_FOLLOWUPS`, `P0=0, P1=0`, full-suite build evidence,
follow-ups explicit); P-018 copilot-review gate SATISFIED; CI green; MERGEABLE
with no required-review block. Merged via merge commit (P-009).

## Backlog closure (P-015 single-artifact ops)

Full-feature shipment — all 10 tasks of 076-F are in the 088-S manifest and were
already archived during build via the feature PR, so there are **no unshipped
siblings** and no partial-feature parent-cascade risk.

- Manifest items `076.001-T`..`076.010-T`: already archived (committed on the
  feature branch). Skipped in the archive loop (pre-archived).
- `088-S` shipment record: `backlogit move --status done` + `backlogit archive`
  (single-artifact, **never** `shipment ship`). Verified: no cascade — 076-F
  remained in queue after this step.
- `076-F` feature: `backlogit move --status done` + `backlogit archive`
  (feature-complete closure). Verified: all 10 tasks intact in archive.
- Stash `CA76F48B`: `backlogit stash archive` (consumed).
- Backlog index resynced (`backlogit sync` → 472 artifacts).

**Deviation from the prior local-only closure pattern (intentional):** unlike
024-S..033-S (whose queue records were left on `main`), this cycle **commits**
the feature+shipment queue→archive relocations and the stash archival to `main`.
`.backlogit/stash.jsonl`, queue, and archive files are git-tracked, so keeping
closure local would be reverted by the routine post-merge `git reset --hard
origin/main` and would resurrect the already-shipped `CA76F48B` stash entry and
leave `088-S` as `status: active` on `main`. Committing produces durable,
consistent backlog state.

## Follow-ups (residual risk, non-blocking)

1. **Manifest checksum EOL convention** (CRLF-raw): on LF checkouts the generic
   raw-bytes `checksum_scan` reports all manifest entries "user-modified"
   (pre-existing, repo-wide, warning-only, not CI-gated). Repo-wide EOL
   renormalization or a `.gitattributes` pin remains deferred.
2. **Preset membership sync** is agent-read prose; no code consumes
   `default_in_preset`. Registry and install-harness SKILL prose are hand-synced
   (both updated). Out of scope: unify registry-backed preset resolution across
   install paths.
3. **Versioned profile schema divergence** (pre-existing, unrelated): versioned
   `workspace-profile/1.0.0.schema.json` lacks the root's top-level
   `copilot_review` property. Surfaced during schema-parity review; not
   attributable to this shipment.
4. **Backlog reconciliation** (owner: next backlog-maintenance pass): the older
   024-S..033-S stale queue records remain on `main` from prior local-only
   closures and could be reconciled to archive.
