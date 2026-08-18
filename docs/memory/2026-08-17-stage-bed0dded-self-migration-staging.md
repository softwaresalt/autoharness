---
title: Stage session — BED0DDED self-migration staging
description: Stage session record for the full-lifecycle staging of the Backlogit storage-root self-migration
doc_type: memory
source: docs/memory/2026-08-17-stage-bed0dded-self-migration-staging.md
date: 2026-08-17
agent: stage
mode: normal-sequential
route: claude-opus-5/anthropic/high
stash_source: BED0DDED
---

# Stage session — BED0DDED self-migration staging

## Mode and authority

**Normal sequential pipeline mode — NOT P-017 dark mode.** The operator typed
`dark factor mode`, which is not the exact P-017 trigger, and the Orchestrator
explicitly did not activate dark mode. The operator did explicitly direct the
full Stage→Ship lifecycle for `BED0DDED`, which satisfies the operator gate
that every prior session correctly refused to invent.

Intercom unavailable → `INTERCOM_DEGRADED`. Engram and graphtor-docs MCP tools
were not exposed this session → `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE`;
file-based exploration used throughout per the documented fallback.

## Gates

| Gate | Result |
|---|---|
| Tool availability (P-012) | `TOOL_OK: backlogit` (v1.9.0-39-g17530fe3-dirty) |
| Index sync | `INDEX_SYNC_OK` (834 indexed) |
| Checkpoint recovery | 32 stage checkpoints, 30 resolved + 2 abandoned, **0 active**, `needs_quarantine=0` → zero-candidate normal startup, no recovery |
| Git state | single worktree, `main`, clean, HEAD = origin/main = `6fc2861f` |
| Shipments | zero queued/active; `137-S` shipped/closed; P-001 clear |

## Decision

A self-hosting-safe path **exists**. **One shipment, one PR, two ordered
commits.**

* **Commit A** — root-agnostic *superset*: `.gitignore` and CI path filters
  cover **both** roots, plus the resolver fix for the live-root test binding.
  Correct before *and* after the rename, so it creates no ordering hazard.
* **Commit B** — the atomic switch: stop MCP → dry-run → contained in-repo
  backup (H4) →
  migrate → single-root assertion → parity verify → flip five config surfaces →
  refresh three manifest checksums → CLI verify → index rebuild.

Two PRs was evaluated and **rejected as strictly worse**: P-001 serializes them
anyway, so both designs contain exactly one post-migration merge, while two PRs
add an extra ref transition — and after finding F4, every extra ref transition
is a live residue hazard.

### Why the self-hosting paradox dissolves

1. `backlogit` resolves its storage root **fresh per process**, with no
   cross-move caching, so the shipment manifest survives its own relocation
   once the MCP servers are stopped.
2. A fresh `backlogit` process in a rootless directory **creates nothing** and
   simply errors — no respawn can fabricate a competing root.
3. Any partial state is recoverable via `BACKLOGIT_WORKSPACE_DIR`.

## New evidence (none of it recorded by prior sessions)

Each of the following would have caused a failure or an outage had the
migration been attempted from the prior plan:

* **E1** — `.backlogit` is **git-tracked**: 1613 tracked files of 1656 on disk.
  The migration is simultaneously an operational move and a 1613-file git
  rename; it can never be done "out of band".
* **E2** — Three live `backlogit.exe` processes (PIDs 1740/6548/11364) hold
  **exclusive** Windows locks on `backlogit.db`/`-wal`/`-shm`, proven by a
  `FileShare.None` probe that failed on all three. A Windows directory rename
  cannot succeed against an open handle — **the migration would simply have
  failed.**
* **E3** — `.gitignore` rules are path-literal, so post-rename the 8.09 MB
  database and 6.26 MB WAL match **no** rule; `git add -A` would commit ~14 MB
  of binary SQLite state.
* **E4** — `ci.yml:71` carries a stale `- '!.backlogit/**'` paths-filter entry.
* **E5** — `tests/test_gates_sizing.py:72` binds to the **live repo root** via a
  hardcoded literal — the only such binding repo-wide. Post-migration it raises
  `FileNotFoundError` and would have turned the migration PR **red immediately
  after the irreversible step**.

The operative follower surface is **five** config files, not one, and three of
them carry recorded manifest checksums requiring LF-normalized refresh.

### Verified in throwaway directories (repo not mutated, external repo untouched)

* Two populated roots → `ambiguous workspace root: both .backlog and
  .backlogit exist`.
* `BACKLOGIT_WORKSPACE_DIR=.backlog` and `=.backlogit` each resolve cleanly.
* `src/autoharness/backlog_root.py` returns on the validated override at
  line 126, **before** the ambiguity check at line 136.

`backlogit migrate` was **never executed**, not even `--dry-run`, per the
session contract.

## Artifacts

| Kind | Path | Verdict |
|---|---|---|
| Deliberation | `docs/decisions/2026-08-17-backlogit-self-migration-choreography-deliberation.md` | decided |
| Plan | `docs/plans/2026-08-17-backlogit-self-migration-plan.md` | 9 tasks |
| Hardening (P-006) | `docs/plans/2026-08-17-backlogit-self-migration-hardening.md` | HARDENED, H1–H16 |
| Review | `docs/reviews/2026-08-17-backlogit-self-migration-review.md` | **PASS, 0 P0 / 0 P1** (+ correction pass: PASS, 0 P0 / 0 P1) |

Review raised 8 findings across 6 personas; all 6 P1s resolved before the
verdict (F1→H13, F3→H2 rewrite, F4→H6, F5→T001+H11, F6→T002+H14, F8→H5
narrowing). F2 resolved as H15; F7 (stale root-level `out.json`/`res.json`/
`results.json` scratch artifacts pointing at the external repo) recorded as
out-of-scope hygiene.

## Harvest

**Feature `129-F`**, tasks `129.001-T`–`129.009-T`, **shipment `138-S`**
(queued, high, 10 items, size composition 7×S + 2×XS, **0 unsized**).

Dependency order:

```text
129.001-T ─┐
129.002-T ─┼─> 129.004-T ─> 129.005-T ─> 129.006-T ─> 129.007-T ─> 129.008-T ─> 129.009-T
129.003-T ─┘
```

`129.006-T` is `complexity: high`. It was deliberately **not** split — the
`migrate --workspace-dir` invocation is atomic and decomposing it would create
the partial-migration window the plan exists to prevent. Instead three
de-risking tasks are wired as hard blockers (runbook, backup, dry-run), and the
disposition is recorded on the task rather than laundered away.

## H5 narrowing

The 2026-08-14 hardening `H5` automation exclusion **remains in force** for
dark-factory, unattended and concurrent-agent runs. It is relaxed only for the
explicitly gated case, because H5's stated rationale — concurrent agents
reading and writing during a dark-factory run — is verifiably false this
session.

## BED0DDED disposition

**Not archived. Remains ACTIVE at high priority as the living tracker.** The
residual is now converted to backlog scope but **not yet delivered**;
`129.006-T` can legitimately halt and return to Stage. Since `018-DL`
explicitly excluded the self-migration from its scope, this entry is the sole
owner of the residual. Retire it only when `138-S` is shipped, merged and
`129.009-T` verification has passed.

The stash update was proven **strictly append-only**: the prior text is an
exact prefix of the new text (12578 → 18108 chars, +5530).

## Next steps for Ship

See the handoff constraints in the hardening document — H2 (prove lock release,
not just process exit), **H4 (contained in-repo backup behind gates G1–G6, with
bounded inventory verification, `git clean -x/-X` prohibited, and a mandatory
backup re-assertion immediately before `129.006-T`)**, H6 (no pre-migration ref
transitions after Commit B; use `git checkout -B main origin/main`), H7 (MCP
outage window scheduling), H11 (explicit-path staging, never `git add -A`),
**H15 (operator-gated disposal; do not clear Copilot session state until
disposal is approved)** and **H16 (failure recovery is non-destructive,
evidence-first and operator-gated — never auto-delete a root, never broad
`git checkout -- .`, never guess authority)**.

## Correction pass — 2026-08-17 (post-Orchestrator review)

This memory's original record described an **out-of-tree `$env:TEMP` backup**
and an automatic destructive rollback. Both were P1 defects. They are corrected
in the plan, hardening, review, deliberation and tasks; this section records
the correction rather than erasing the original account.

### C1 — Containment (Constitution Principle IV)

Writing outside the current working directory tree is forbidden. The backup is
now **in-repo**, outside both root-level storage candidates:

```text
.copilot\session-state\7ced3fcb-faba-47fb-81f9-09e0670a393f\files\backlog-premigration-<UTC>\
```

Six containment gates were run this session and **all passed**: G1 canonical
containment; G2 no reparse point on any segment; G3 gitignored
(`.gitignore:4:*.copilot`); G4 unstageable (`git add` exit 1, nothing staged);
G5 non-candidate naming; G6 resolver-undiscoverable.

**New evidence (E10)** — root selection is by directory **name**: the resolver
does not recurse downward and the engine does not walk up ancestors
(`backlogit --cwd <rootless-subdir> list` → `workspace storage root not found`,
exit 1, nothing created). A **negative control** confirmed G5 is load-bearing:
creating `files\.backlogit\` made `resolve_backlog_root(files)` return it.
Hence the backup copies the **contents** of `.backlogit\*`, never the directory.

**New evidence (E11)** — the backup is gitignored and would therefore be
destroyed by `git clean -x`/`-X` (finding **F12**). Now prohibited for the whole
backup window, with a mandatory pre-`T006` re-assertion.

### C2 — Non-destructive failure recovery (H16)

`delete .backlog` + `git checkout -- .` was not only unauthorized breadth — it
was **provably incorrect**. Because `.backlogit` is git-tracked (**E1**),
`git checkout -- .` after the rename restores `.backlogit` from HEAD while
`.backlog` persists on disk, manufacturing the exact dual-root state **H10**
exists to prevent. Replaced by preserve → evidence → HALT → explicit operator
approval, with enumerated-path-only restoration thereafter.

### Correction-pass review

Personas 7–12 re-reviewed the corrected safety contract: **five P1 findings
(F9–F12, F14) raised and all resolved**, one P2 accepted with gated mitigation
(**F13**, CLI-managed session-state durability — 27 session dirs persisting
since 2026-04-22 evidence low pruning risk; fallback `.autoharness/staging/`).

**Verdict: PASS — 0 unresolved P0, 0 unresolved P1.** Hardening is now
**H1–H16**. `138-S` remains queued with 10 items, unchanged dependency order,
sizes and complexities — and is now shippable.
