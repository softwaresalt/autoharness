---
title: "Stage dark-factory session — 2026-08-16 stash-to-backlog lifecycle"
source: docs/memory/2026-08-16-stage-dark-factory-session.md
doc_type: memory
description: "Session record for the resumed P-017 dark-factory Stage run: dispositions for all seven scoped stash entries, one queued shipment (137-S), and the artifacts produced."
---

# Stage dark-factory session — 2026-08-16

* **Agent / route**: Stage — `claude-opus-5` / `anthropic` / `high` (P-013.5 honored)
* **Mode**: P-017 dark factory, operator AFK, autonomous judgment authorized
* **Authority**: merge approval pre-authorized; **admin fallback NOT authorized**
* **Visibility**: degraded to local session (`INTERCOM_DEGRADED` — agent-intercom unavailable)
* **Base**: `main`, HEAD `804e0133`

## Tool availability (Step 0.0 / 0.1)

| Probe | Result |
|---|---|
| backlogit MCP | `TOOL_OK` — v1.9.0-39-g17530fe3 |
| Index sync | `INDEX_SYNC_OK` — 831 artifacts |
| Checkpoints | 32 total, **0 active**, 0 quarantined, 0 needing quarantine → zero-candidate normal startup, no recovery needed |
| agent-intercom | `INTERCOM_DEGRADED` |
| agent-engram | `ENGRAM_DEGRADED` — file-based exploration used |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` — file-based doc search used |

Registry note: `.autoharness/backlog-registry.yaml` does **not** declare `features.sizing`
and its `update_task` params omit `size`/`complexity`, but the live `backlogit_update_item`
MCP tool does support them and structured emission succeeded. Recorded as a
**registry/tool capability drift** observation only — no scope created for it.

## Dispositions — all seven scoped entries

| Stash ID | Pri | Kind | Disposition |
|---|---|---|---|
| `BED0DDED` | high | feature | **Deferred — operator-gated.** Active living tracker. |
| `47971057` | high | feature | **Deferred — operator-gated.** Active living tracker. |
| `34AAF1C7` | medium | feature | **Spike run → DEFER.** Active living tracker. |
| `34D50F2D` | medium | feature | **Deferred — candidate (c) unselected.** Active living tracker. |
| `84D8E6AB` | low | bug | **External (backlogit-owned).** Active external tracker. |
| `936C68F3` | low | feature | **Deferred — unsupported upstream.** Active living tracker. |
| `61358124` | low | task | **CONSUMED → harvested as 128-F / 137-S; ARCHIVED.** |

### `BED0DDED` — backlog storage-root rename

Fifth independent verification. The shipped follower surface (`126-F` / `135-S`) was
re-verified live and is genuinely complete: `src/autoharness/backlog_root.py` gives
`.backlog`-first precedence with legacy fallback, override validation mirroring upstream,
symlink **and** Windows reparse-point rejection, and fail-closed `AmbiguousBacklogRootError`;
`scripts/ci-topology-check.sh` resolves equivalently and hard-fails on both-present;
`topology.py` now routes through `resolve_backlog_root`. Corroborated independently by
running `backlogit init` in a throwaway workspace — it created `.backlog`.

**No residual follower work exists.** The residual is the live self-migration plus registry
flip, which is operator-gated: hardening H5 excludes it from automation, a partial migration
leaves the workspace failing closed for every agent, and this session's contract forbids
config mutation. Live state: `.backlogit` exists, `.backlog` does not — no ambiguity today.

Because this entry could not safely produce scope, the session's first shipment covers the
highest-priority coherent group that *was* safe.

### `34AAF1C7` — reasoning DAG / anti-spinning

The one entry whose state genuinely advanced. Ran the read-only spike the 2026-08-15
annotation recommended → `docs/decisions/2026-08-16-observable-termination-record-spike.md`.

Hypothesis **half-confirmed, half-refuted**; recommended first slice **withdrawn**:
confirmed that all repetition bounds are prose-only (F1), that a telemetry substrate exists
(F2), and that observable termination is separable from state identity (F3); refuted that
the blast radius is small (F4 — it is the agent-contract prose surface of every generated
agent) and that benefit exists without a consumer (F5, decisive). F6: the motivating
failures were caused by absent *enforcement*, not absent *evidence*.

Narrowed next slice: one bound (plan-review 3-cycle), reader shipped in the same slice,
record-only and degrade-open, no DAG traversal until measurements exist.

## Shipment produced

**`137-S`** — *Spike skill template docline frontmatter conformance (128-F)* — `queued`,
priority medium, **no predecessor blocks** (queue position 1; the only live shipment).

| Order | Item | Type | Size | Complexity | Status |
|---:|---|---|---|---|---|
| 1 | `128-F` | feature | — | — | queued |
| 2 | `128.001-T` | task | XS | low | queued |
| 3 | `128.002-T` | task | S | low | queued |

Dependency: `128.001-T` **blocks** `128.002-T` (verification follows the template fix).
Manifest verified: 3 items, `size_composition.unsized = 0`.

### Why this was the right group

The defect was confirmed by **measurement**, not assertion: the current spike-template
frontmatter shape yields 2 authoring-lint violations, the target `docline`-nested shape
yields 0 — so *every* findings artifact the template generates currently fails lint.
Under the operator's ordering policy, composability/interoperability supersedes feature
work, which ranks this cross-tool conformance repair ahead of the four deferred
feature-shaped entries.

## Artifacts produced

| Path | Kind |
|---|---|
| `docs/decisions/2026-08-16-observable-termination-record-spike.md` | Spike findings (34AAF1C7) |
| `docs/plans/2026-08-16-spike-template-docline-conformance-plan.md` | Implementation plan (61358124) |
| `docs/reviews/2026-08-16-spike-template-docline-conformance-review.md` | Multi-persona review — PASS |
| `docs/memory/2026-08-16-stage-dark-factory-session.md` | This record |

Backlog paths changed: `.backlogit/queue/128-F.md`, `.backlogit/queue/128.001-T.md`,
`.backlogit/queue/128.002-T.md`, `.backlogit/queue/137-S.md`, `.backlogit/stash.jsonl`
(6 append-only annotations + 1 archive), plus backlogit-managed logs/index.

## Scope discipline

Discovered but **deliberately not harvested** (would be silent scope expansion):

* 10 pre-existing `docs/decisions/*.md` files already failing authoring lint for missing
  `source`/`doc_type`.
* `docs/audits/` using `doc_type: audit`, which is outside the ingestion closed vocabulary.
* Registry/tool sizing-capability drift (above).

## Worktree hygiene

All pre-existing dirty changes preserved — the operator-approved `077-F` abandonment
(`D .backlogit/queue/077-F.md`, `?? .backlogit/archive/077-F.md`), `015-DL` changes,
`.gitmodules`/`references/` submodule updates, `docs/reference-library.md`, and
`tests/test_verify_workspace.py`. Nothing reverted, overwritten, staged, or committed.

The docline probe workspace was created **outside** this repository in `%TEMP%` and deleted.
No branch, worktree, commit, push, or PR was created. No spike/research worktree was created
(P-016). The five stale prunable worktree registrations were left untouched.

## Reconciliation pass — 2026-08-17 (unit 1 of the ordered shipment cursor)

Resumed Stage session re-verified `137-S` end-to-end before handing off to Ship. Startup
gates re-run: `TOOL_OK` (backlogit v1.9.0-39-g17530fe3), `INDEX_SYNC_OK` (834 artifacts),
34 checkpoints with **0 active / 0 anomalies** → zero-candidate normal startup, no
recovery. `INTERCOM_DEGRADED` / `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE` unchanged.
Single worktree on `main` at `804e0133`, in sync with `origin/main`.

### Independent re-verification of the plan's load-bearing claims

Deliberately re-derived rather than restated, because the original evidence was produced
in a throwaway probe workspace that no longer exists:

| Claim | Result |
|---|---|
| `{{DOCS_DECISIONS}}` already registered (no new variable) | **Confirmed** — `install-harness/SKILL.md:281` → `docs/decisions` |
| 10 pre-existing failing decision docs (out of scope) | **Confirmed exactly** — live authoring lint: 10 files, 21 violations |
| Target docline shape passes authoring lint | **Confirmed on a real in-scope artifact** — this session's own `2026-08-16-observable-termination-record-spike.md` uses the nested shape and is *not* among the 10 failures |
| Phase 5 block + Step 4.2 coherence trap present | **Confirmed** — YAML at lines 281–294 (top-level `promoted_to` at 290), Step 4.2 at 226–227 |
| `tests/test_spike_template_docline_frontmatter.py` absent | **Confirmed** — new module, dirty `test_verify_workspace.py` untouched |

The 2 → 0 lint claim is now corroborated against the live linter on a committed in-scope
artifact, which is stronger evidence than the original probe-workspace measurement.

### Review re-confirmation

`PASS`, **0 P0 / 0 P1 unresolved**. All four findings traced to concrete resolutions in
both the plan *and* the task descriptions: P1-1 (`source` substitution → Task 1 item 4),
P1-2 (fixture pinned to `docs/decisions/` → AC 1 and 128.002-T), P1-3 (`doc_type`
vocabulary via `ingestion` profile → AC 2 and 128.002-T), P2-4 (test module named;
`description` recorded as handoff-required but not lint-enforced). P-006 hardening
re-assessed independently: **not required** (one template family, no schema, no CLI).

`128.002-T` **retained** — it carries AC 1–2 acceptance evidence and the partial-fix
regression guard. No policy-valid reason to drop it.

### Defect fixed this pass

Covering feature `128-F` had a **null priority** while `128.001-T`, `128.002-T` and
`137-S` were all `medium`. Set to `medium`; body, labels and references preserved. This
was the only coherence gap found.

Manifest re-verified: 3 items, `size_composition.unsized = 0`, no predecessor blocks,
`137-S` is the **only** live shipment. Blocked `080-F` / `081-F` correctly absent.

### Durability boundary applied

Committed only Stage-owned paths for `128-F` / `137-S` plus this session's planning
artifacts. **Deliberately excluded after provenance inspection** (not this unit's work):
`.backlogit/memories.json` (mixed — also carries the pre-existing `077-F-abandonment`
operator record, and JSON cannot be split without rewriting an operator-touched file),
`.backlogit/archive/015-DL.md`, the `077-F` queue deletion / archive / log files, and the
operator-excluded `.gitmodules`, `docs/reference-library.md`, `references/*`,
`tests/test_verify_workspace.py`. `.gitmodules` and two `references/` submodules were
already **staged** in the index, so the commit used an explicit pathspec to avoid
capturing them. Nothing reverted, stashed, discarded, or force-updated.

## Next session

1. **Operator decisions needed** (blocking, in priority order): `BED0DDED` storage-root
   self-migration; `47971057` provisioning threat-model questions; `34D50F2D` candidate (c)
   lead-selection.
2. `137-S` is queued and ready for **Ship** to claim.
3. `34AAF1C7`'s narrowed slice is documented and can be planned once selected.
4. `.backlogit/memories.json` still carries an uncommitted Stage memory key alongside the
   operator's `077-F` record — needs an operator or Orchestrator decision, not a Stage one.
