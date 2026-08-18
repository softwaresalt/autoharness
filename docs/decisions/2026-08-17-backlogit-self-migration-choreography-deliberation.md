---
title: Backlogit self-migration choreography deliberation
description: Choosing a self-hosting-safe choreography to migrate this repository's live Backlogit storage root from .backlogit to .backlog
doc_type: decision
source: docs/decisions/2026-08-17-backlogit-self-migration-choreography-deliberation.md
status: decided
date: 2026-08-17
stash_source: BED0DDED
supersedes_scope_of: docs/plans/2026-08-14-backlog-storage-root-adoption-hardening.md (H5)
route: claude-opus-5/anthropic/high
---

# Backlogit self-migration choreography deliberation

## Problem frame

Stash entry `BED0DDED` has one residual, operator-gated deliverable: migrate
**this repository's own live Backlogit storage root** from `.backlogit` to
`.backlog`, and bring every follower reference into agreement in the same
bounded change.

The follower *product* surface (resolver, templates, schemas, docs, tests,
installer/tuner) already shipped as `126-F` / `135-S` (PR #345, merge
`9851cc3`). This deliberation covers only the residual self-migration, which is
uniquely hard because **the tool being migrated is the tool that records the
work of migrating it**. The shipment manifest that authorizes the change lives
inside the directory the change relocates.

Prior hardening `H5` excluded this from automation. The operator has now
explicitly directed the full lifecycle, so the question is no longer *whether*
to plan it but *whether a provably safe choreography exists under current
primitives* — and to halt with evidence if it does not.

## Evidence established this session (read-only)

All facts below were established by direct observation in this workspace or by
probes in throwaway directories outside it. No repository file was mutated, and
`backlogit migrate` was **not** executed in any form (including `--dry-run`).

### E1 — The storage root is git-tracked, and far wider than "one directory"

`git ls-files .backlogit` returns **1613 tracked files** (1656 files on disk).
The migration is therefore simultaneously an operational move *and* a
1613-file git rename. It cannot be performed "out of band" from version
control.

### E2 — Live processes hold exclusive Windows locks on the storage root

Three `backlogit.exe` processes (PIDs 1740, 6548, 11364 from
`D:\Tools\backlogit.exe`) are running. An exclusive-open probe
(`FileShare.None`) against all three SQLite files failed:

```text
LOCKED by another process: .backlogit\backlogit.db
LOCKED by another process: .backlogit\backlogit.db-wal
LOCKED by another process: .backlogit\backlogit.db-shm
```

On Windows a directory rename fails with a sharing violation while any
contained file has an open handle. **The migration cannot succeed while the
MCP servers run.** This is a hard precondition that no prior annotation of
`BED0DDED` recorded.

### E3 — `.gitignore` rules are path-literal and would leak a 14 MB database

`.gitignore` lines 10–13 are keyed to the literal old path:

```gitignore
.backlogit/*.db
.backlogit/hooks_queue.jsonl
.backlogit/*.db-shm
.backlogit/*.db-wal
```

After a rename, `.backlog/backlogit.db` (8.09 MB), `.backlog/backlogit.db-wal`
(6.26 MB), `.backlog/backlogit.db-shm` and `.backlog/hooks_queue.jsonl` match
**no** ignore rule. A routine `git add -A` would commit ~14 MB of binary
SQLite/WAL state. This hazard was not previously recorded.

### E4 — CI has a stale path filter

`.github/workflows/ci.yml` line 71 carries `- '!.backlogit/**'` in the
fail-closed `paths-filter` denylist. After migration, backlog-only changes
would stop matching the exclusion and would be misclassified as code changes,
needlessly running the expensive gate. Not previously recorded.

### E5 — Four config surfaces and three manifest checksums must move together

| File | Reference |
|---|---|
| `.autoharness/backlog-registry.yaml` | `directory: ".backlogit"` |
| `.autoharness/config.yaml` | L28 `directory: ".backlogit"` |
| `.autoharness/workspace-profile.yaml` | L142, L145, L236, L240 |
| `.engram/registry.yaml` | L16 `path: .backlogit` |
| `.autoharness/harness-manifest.yaml` | L307 `BACKLOG_DIRECTORY: ".backlogit"` |

`harness-manifest.yaml` additionally records **checksums** for
`backlog-registry.yaml`, `config.yaml` and `workspace-profile.yaml`. Editing
those three without refreshing their checksums produces verify/tune drift
failures. The `note:` prose fields at L166/L171 are historical record and must
**not** be rewritten.

### E6 — `scripts/ci-topology-check.sh` already resolves correctly

Lines 82–105 implement override validation, both-present fail-closed, then
`.backlog`-first precedence. **No change required.** This is shipped
`126-F` behavior working as designed.

### E7 — backlogit never auto-creates a storage root

In an empty throwaway directory, `backlogit list` returns
`workspace storage root not found` and creates nothing. Critically, this means
**an MCP server respawning during the migration window cannot fabricate a
second root**, eliminating the most feared interleaving failure.

Also observed: a bare empty directory is *not* a root upstream — a root is
recognized by its `config.yaml` marker.

### E8 — Dual-root fails closed, and the override is a verified escape hatch

With two populated roots present in a throwaway workspace:

```text
Error: open workspace: resolve workspace root: ambiguous workspace root:
both .backlog and .backlogit exist; set BACKLOGIT_WORKSPACE_DIR to one of
the supported names or remove one
```

With `BACKLOGIT_WORKSPACE_DIR=.backlog` (and independently `.backlogit`), the
same workspace resolved cleanly and listed items. The autoharness-side Python
resolver matches this precedence: `src/autoharness/backlog_root.py` returns on
the validated override at line 126, **before** the ambiguity check at line 136.

This is the decisive finding: **a partial or residual dual-root state is
recoverable, not terminal.**

### E9 — The residue hazard (new, and the main reason this is delicate)

Because the DB files are *ignored*, they are not removed by `git checkout`.
If anyone checks out a **pre-migration ref** after the migration commit exists,
git deletes `.backlog/`'s tracked files and restores `.backlogit/`, but leaves
`.backlog/` on disk containing only the ignored database residue. Result:

* Upstream `backlogit` still resolves (no `config.yaml` in the residue, so
  `.backlog` is not a root) — **engine survives**.
* `src/autoharness/backlog_root.py` and `scripts/ci-topology-check.sh` test
  bare directory existence — **both fail closed**.

So a stray branch switch degrades harness tooling and the CI topology gate
while leaving the engine working. Recoverable by deleting the residual
directory or setting the override, but it must be explicitly forbidden and
documented.

## Options considered

### Option 1 — Reject again; keep deferring

Faithful to `H5`, but `H5`'s stated rationale is *"the Orchestrator, Stage and
Ship are concurrently reading and writing during a dark-factory run."* That
premise is **false in this session**: normal sequential mode, exactly one
worktree, zero queued/active shipments, zero active checkpoints, operator
present and explicitly directing. Continuing to defer on a premise that no
longer holds would be cargo-culting a guard rather than applying it. **Rejected.**

### Option 2 — Operator performs the move manually, outside any shipment

Superficially attractive, but **E1** kills it: 1613 tracked files change, so
the move must be committed regardless. A manual move produces an enormous
uncommitted diff with no plan, no review and no rollback task. It moves risk
out of the governed pipeline rather than reducing it. **Rejected.**

### Option 3 — Two shipments (prep PR, then migration PR)

Merge the `.gitignore`/CI preparation first, then migrate in a second PR.
Safer-sounding, but the prep commit is causally meaningless on its own — it
exists solely to make the migration safe — and **P-001** forces the shipments
to run sequentially anyway. It yields the same single post-migration merge
while adding an extra branch-creation/merge/ref-transition cycle, and every
extra ref transition is an **E9** exposure. **Rejected as strictly worse.**

### Option 4 (CHOSEN) — One shipment, one PR, two ordered commits

A single shipment and PR containing:

* **Commit A — root-agnostic superset prep.** Rewrite `.gitignore` and
  `ci.yml` to cover **both** `.backlogit/**` and `.backlog/**`. This commit is
  correct before *and* after the rename, so it creates no ordering hazard and
  closes **E3**/**E4** in advance.
* **Commit B — the atomic switch.** Stop MCP servers, dry-run, back up outside
  the repo, migrate, verify parity, flip the four config surfaces, refresh the
  three manifest checksums, re-verify via CLI, rebuild the index, commit.

## Decision

**Proceed with Option 4.** A self-hosting-safe path exists and is executable
under current primitives. The self-hosting paradox dissolves for three
independently-verified reasons:

1. **The manifest survives its own relocation.** `backlogit` resolves its root
   *fresh per process* with no cross-move caching, and the shipment manifest
   (`queue/NNN-S.md`) moves with the rest of the root. Once the MCP servers
   are stopped (**E2**) and restarted, the shipment remains addressable by the
   same ID at the new path.
2. **No process can fabricate a competing root** during the window (**E7**).
3. **Any partial state is recoverable** via `BACKLOGIT_WORKSPACE_DIR`
   (**E8**), which short-circuits the ambiguity check in both the engine and
   the harness resolver.

The ordering constraint that makes it safe is that **Commit A is a superset**,
not a switch. Nothing in the repository is ever in a state where the ignore
rules or CI filters disagree with the directory actually on disk.

`H5` is **narrowed, not overridden**: its exclusion remains fully in force for
dark-factory/unattended runs and for any run with concurrent agents. This
choreography is authorized only under the explicit idle-gated, operator-present
conditions enumerated in the plan.

## Open questions and residual risks

* **Ship loses MCP mid-shipment.** Between stopping the servers and their
  restart, Ship has no backlogit MCP tools. The registry declares CLI
  fallbacks for the operations Ship needs (`move`, `shipment claim/ship/get`,
  `sync`, `dep`, `checkpoint`, `query`), but **not** for `add_to_shipment`,
  `append_comment`, `save_memory`, `create_checkpoint` or `archive_item`.
  *Mitigation:* Stage performs all MCP-only shipment assembly now; Ship defers
  remaining MCP-only operations until after restart.
* **E9 branch-switch residue.** Mitigated by an explicit prohibition plus a
  documented recovery runbook, and by using `git checkout -B main origin/main`
  after fetch so Ship never lands on a stale pre-migration `main`.
* **`migrate --rollback` scope is unverified by us.** We deliberately did not
  execute it. The plan therefore does **not** rely on it as the primary
  recovery mechanism; an in-repo, containment-gated filesystem backup (H4) is
  primary, with `--rollback` as a secondary convenience only — and every
  recovery action is non-destructive and operator-gated (H16).
* **Stale lock residue.** `.backlogit/queue/.128.001-T.md.lock`,
  `.128.002-T.md.lock` and `.locks/.137-S.lock` are leftovers from closed work.
  They will migrate harmlessly; cleaning them is explicitly out of scope to
  keep the change bounded.
