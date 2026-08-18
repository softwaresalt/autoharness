---
shipment: 138-S
feature: 129-F
tasks: [129.001-T, 129.002-T, 129.003-T, 129.004-T, 129.005-T, 129.006-T, 129.007-T, 129.008-T, 129.009-T]
disposition: CANCELLED
shipment_status: abandoned
feature_status: rejected
task_status: rejected
predecessor_shipments: [139-S, 140-S, 137-S]
predecessor_status: archived (shipped)
scope_correction_decision: docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md
stash_lineage: BED0DDED (deliberation 018-DL) — remains active pending Stage archival after this abandonment is durable
claim_timestamp: "2026-08-18T18:10:04.0668911Z"
abandoned_timestamp: "2026-08-18T18:10:56.0929182Z"
migration_executed: false
storage_root_before: ".backlogit"
storage_root_after: ".backlogit"
build_applicability: not_applicable
compaction_status: degraded
closure_status: READY
rollback: NOT_APPLICABLE
---

# 138-S / 129-F Cancellation Closure — `.backlogit` → `.backlog` Self-Migration Abandoned (Operator Scope Correction, BED0DDED)

## 1. Disposition summary

This is a **cancellation closure**, not a delivery closure. No template,
schema, CLI, or documentation migration work was implemented or shipped.
Shipment `138-S` ("Migrate live Backlogit storage root `.backlogit` ->
`.backlog`") is **abandoned** and its covering feature `129-F` plus all nine
child tasks `129.001-T`…`129.009-T` remain **rejected**, per the binding
operator decision recorded in
`docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`:

* `.backlogit` remains an acceptable, permanently supported Backlogit
  storage root. It is not deprecated and not scheduled for removal.
* `.backlog` is the default only for **newly initialized** workspaces.
* This (or any other) existing `.backlogit`-rooted workspace has **no**
  migration obligation.

No `.backlogit`/`.backlog` rename, copy, delete, or config flip occurred at
any point in this closure. `storage_root_before` == `storage_root_after` ==
`.backlogit`; `.backlog` does not exist in this workspace before or after
this closure.

## 2. Pre-flight verification (before claim)

| Check | Result |
|---|---|
| P-001 — no other top-level release unit (feature/chore) `Active` in the backlog | **PASS** — full scan of `.backlogit/queue/*.md` found zero `status: active` feature/chore/shipment records before claim |
| P-016 — worktree topology | **PASS** — `git worktree list --porcelain` shows exactly one worktree (`D:/Source/GitHub/autoharness`); no parallel/second worktree created at any point |
| Crash-resumption / checkpoint scan | Unfiltered scan of all 35 checkpoint files under `.backlogit/checkpoints/`: 35 valid, 0 anomalies, 0 `status: active` — zero-candidate normal startup, no recovery needed |
| Dependency satisfaction | `138-S.dependencies = [139-S, 140-S]`; both `archived_status: shipped` / `status: archived`. Gate-reported `shipment_readiness` also surfaced a third predecessor, `137-S` (also `archived_status: shipped` / `status: archived`) |
| Predecessor `closure_complete` | `139-S` and `140-S` both confirmed closed via their archived shipment records (`archived_status: shipped`) prior to this claim |
| 129-F / 129.001-T…129.009-T current status | All ten already `rejected` (Stage disposition, prior session) — reconfirmed unchanged before and after this closure |

### Topology gate evidence

The installed `autoharness` CLI (`autoharness.exe`, PATH-resolved) does not
expose a `gate` subcommand (pre-1.x install; confirmed via
`autoharness gate --help` -> `Unknown command: gate`). Per the documented
bootstrap exemption, the **source-tree** gate
(`src/autoharness/gates/topology.py` + `src/autoharness/cli.py`) was invoked
directly via `python` with `PYTHONPATH=src`:

```
python -c "from autoharness import cli; cli.main(['gate','pipeline-topology','--mode','agent','--shipment','138-S','--phase','pre_claim','--json'])"
```

Run while still on the pre-existing `post-merge/131-f-topology-gate-directional-predicate-hotfix`
branch (itself the just-merged PR #361 branch, tree-identical to `main`):
**exit 0, `blocked: false`**. All five checks passed:
`detect_before_consistency`, `active_shipment_invariant` (`active_shipment_ids: []`),
`branch_ownership` (`BRANCH_POST_MERGE_CLOSURE_ELIGIBLE`), `worktree_topology`
(`WORKTREE_TOPOLOGY_OK`), and `shipment_readiness` (predecessors `139-S`,
`140-S`, `137-S` all satisfied).

After creating the dedicated cancellation branch `chore/abandon-138-s` (see
§3), the same gate invocation returned **exit 1**, `token: BRANCH_MISMATCH`.
**Corrected characterization** (an earlier draft of this document
mischaracterized this as a cancellation-specific gate coverage gap;
Copilot review on PR #362 correctly flagged that as inaccurate): the gate
is purpose-agnostic and is not designed around implementation vs.
cancellation intent at all. Per `_branch_aliases`
(`src/autoharness/gates/topology.py:1040-1048`), it accepts only branches
of the form `feat/{slug}` / `chore/{slug}` or `feat/{shipment-id}-{slug}` /
`chore/{shipment-id}-{slug}` — i.e. the shipment ID, when present in the
branch name at all, must appear as a **leading** token, e.g.
`chore/138-s-migrate-live-backlogit-storage-root-backlogit-backlog`.
`chore/abandon-138-s` matches neither form: it reverses the expected
token order (a literal prefix `abandon-` followed by the ID in the middle
of the string). This is a genuine, correctly-detected `BRANCH_MISMATCH`
under the gate's existing, purpose-agnostic naming rule — not a missing
"cancellation branch" feature and not a limitation this closure needed to
route around.

The reason this branch was used anyway is a **specific, current-session
operator authorization**, not a gate workaround: the operator's
cancellation-lifecycle instructions for this session explicitly named
`chore/abandon-138-s` as the branch to create, superseding both (a) the
gate's canonical naming convention and (b) the pre-existing Stage
instruction in §5 of
`docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`
that Ship must not create *any* branch for `138-S` (see that document's
§8 for the disclosed supersession). The branch exists solely as a commit
target for this cancellation-closure evidence — no file within
`129-F`/`129.001-T`…`129.009-T`'s scope was touched, and no storage root
was touched. The substantive topology-gate checks that are
branch-name-independent (`active_shipment_invariant`, `worktree_topology`,
`shipment_readiness`) were independently re-confirmed unchanged (single
worktree; zero active shipments in `.backlogit/queue/`; predecessor set
unchanged) immediately after branch creation, so the underlying safety
invariants the gate protects were never at risk despite the
`branch_ownership` mismatch. `--force` was never used (operator-only,
never reachable from an agent surface, and not needed here since the
underlying invariants were already independently proven and the branch
name itself was operator-authorized rather than gate-bypassed).

## 3. Cancellation branch and preserved operator changes

A dedicated cancellation branch, `chore/abandon-138-s`, was created from
local `main` (`99b8ead601a72642ed9791cb99258ac4f2e1bd8e`, confirmed identical
to `origin/main`). Before switching, `git diff main HEAD --stat` against the
previously-checked-out `post-merge/131-f-topology-gate-directional-predicate-hotfix`
branch returned **no output** — the two branches' committed trees are
byte-identical — so the branch switch changed zero tracked file content.

Unrelated operator-staged changes present before the switch
(`.gitmodules` modified; `references/skillopt`, `references/waza`,
`references/witr` added as submodule gitlinks) were captured via
`git ls-files -s` (2502 entries) immediately before the checkout and
re-captured immediately after: **`Compare-Object` of the two full index
listings returned zero differences.** Staged blob hashes were also
independently re-verified identical post-checkout:

| Path | Staged blob (before == after) |
|---|---|
| `.gitmodules` | `4e0b9c4cb2d2c18737ecb16525383d2c1dd179de` |
| `references/skillopt` (gitlink) | `9c776fcb51ae681c046d6f619b55e5f337d4f900` |
| `references/waza` (gitlink) | `23cad910e93dd687f36f533da893c8552a4e76b6` |
| `references/witr` (gitlink) | `dc4fa1da82d3e266fcbd928641b4f30b3077c64f` |

`.backlogit/stash.jsonl` showed as worktree-modified (` M`) both before and
after the switch. `git hash-object` of the worktree copy vs.
`git rev-parse HEAD:.backlogit/stash.jsonl` were identical
(`9f051304b3a10b60c7fedaba9a019593cc85ab63`) in both checks — confirming
this is a stale stat/CRLF-normalization artifact with **no real content
drift**, not unexpected mutation. No `git add`, `git stash`, `git reset`,
or `git clean` was ever run against any of these paths; they remain exactly
as the operator left them, untouched, throughout this entire cancellation
lifecycle.

## 4. Shipment state transition (mechanical prerequisite only)

Backlogit 1.9.0 exposes no `shipment abandon` command; the only valid
shipment transitions are `queued -> active`, `active -> shipped`, and
`active -> abandoned` (`internal/core/shipment.go::isValidShipmentTransition`,
per `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`).
There is no direct `queued -> abandoned` transition, so the claim below is a
**mechanical state-machine prerequisite only** — never an execution intent,
and no implementation task was ever moved toward `done`.

```
backlogit shipment claim 138-S      # queued -> active  (2026-08-18T18:10:04.0668911Z)
backlogit move 138-S --status abandoned   # active -> abandoned (2026-08-18T18:10:56.0929182Z)
backlogit get 138-S --format json   # verified: "status": "abandoned"
```

Both commands returned exit 0. `backlogit get 138-S` confirms
`"status": "abandoned"`. Per `.backlogit/registry.yaml`, neither `queued`,
`active`, `blocked`, `review` (routed to `queue/`) nor `done`, `accepted`,
`rejected`, `archived` (routed to `archive/`) lists `abandoned` — the record
therefore remains at `.backlogit/queue/138-S.md` with `status: abandoned`.
This is **expected and correct**: `abandoned` is a valid terminal
`ShipmentStatus` per backlogit 1.9.0, but the registry's directory-routing
rules were authored before `abandoned` existed as a shipment terminal state
and have no matching condition for it, so the file location does not change
on this transition. The status field itself (not file location) is the
source of truth here, and it correctly reads `abandoned`. No implementation
task (`129.001-T`…`129.009-T`) was moved to `active`, `review`, or `done` at
any point — all nine remain `rejected`, unchanged from before this session.

`backlogit sync` was run after the mutation (`Indexed 858 artifacts`) to
keep the SQLite index consistent with the on-disk state.

### Audit-log discrepancy, disclosed not fabricated

`.backlogit/logs/138-S.jsonl` records the `queued -> active` claim event
(`shipment_status_changed`, `delta.status: active`) but contains **no**
corresponding event for the subsequent `active -> abandoned` transition —
the log stops at `active` even though `.backlogit/queue/138-S.md`'s
`status` field and every `backlogit get 138-S` query in this session
confirm `abandoned`. Unlike the `queued -> active` claim (which appended a
log line), `backlogit move --status abandoned` did not append a
corresponding item-log entry in this backlogit build (v1.9.0-39-g17530fe3).
This was verified directly: the file has exactly 3 lines both before and
after the `move` command ran, and no 4th line was ever written. The final
state is correct and independently re-verified multiple times via
`backlogit get 138-S --format json` (`"status": "abandoned"`); the
discrepancy is isolated to the append-only audit log's completeness for
this transition type, not to the correctness of the terminal state. Per
the precedent set in
`docs/closure/136-S-127-F-post-merge-closure.md` (its own "Addendum: a
backlog audit-log discrepancy, noted but not fabricated" section), Ship
does **not** hand-author a synthetic log entry to paper over this gap —
doing so would itself corrupt the append-only trail's integrity. This is
recorded here as a known discrepancy for the backlogit maintainers/Stage
to investigate, and the "complete, traceable cancellation lifecycle"
framing used for this task is narrowed accordingly: the backlog **state**
transition is complete and traceable via direct queries at each step; the
**append-only event log** for this shipment is missing one event.

## 5. Rollback / non-applicability

No migration was implemented, no template/schema/CLI/skill/documentation
code changed, and no storage root was touched. There is **nothing to roll
back**: the `.backlogit` root is exactly as it was before this closure
began, modulo the backlog-state transitions recorded in §4, which are
themselves the **intended terminal outcome** of this closure, not a defect
requiring rollback. **Correction**: `abandoned` is a terminal state under
backlogit 1.9.0's shipment state machine — the only valid transitions are
`queued -> active`, `active -> shipped`, and `active -> abandoned`
(`internal/core/shipment.go::isValidShipmentTransition`; see §4 and
`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`).
There is **no** `abandoned -> active` (or any other) transition out of
`abandoned` defined anywhere in that state machine, so this is not a
reversible-by-re-claim outcome. If a future operator wishes to reopen this
work, that requires a fresh, separate decision and a new shipment/feature
record — not a re-claim of `138-S` — and is explicitly out of scope for,
and not attempted by, this closure.

## 6. Full local build

This is a **backlog- and documentation-only** change (no source, schema,
template, or CLI code touched). Per Step 4.1, full-build non-applicability
is recorded instead of a full local build run.  A CLI smoke test
(`autoharness --help`, and the source-tree `gate pipeline-topology`
invocation above) was exercised as part of gate verification, not as a
build-validation requirement for this change.

## 7. Review, CI, and merge evidence

See PR record (filled in at merge; local review readiness recorded in the PR
body's `## Local Review Readiness` block per P-014, current HEAD at PR
open/merge time). No hosted Copilot review blocking action beyond standard
patient wait/resolve was required beyond what is recorded on the PR.

## 8. Compaction (P-020)

`compact-context` (`templates/skills/compact-context/SKILL.md.tmpl` — this
self-hosting repository does not carry a resolved `.github/skills/`
installed copy) was invoked with `target: all`. Phase 1 assessment:
`docs/memory/` holds 68 files totaling ~573 KB, exceeding both the
`max_files` (40) and `max_size_kb` (500) manual triggers. Given this
cancellation closure's explicitly bounded scope (abandon `138-S` only; do
not touch any other stash/queue item; do not create P-015 follow-ups), a
full consolidation pass over all 68 pre-existing memory files was
**deliberately deferred** rather than expanded into this PR's diff — that
is a separate, larger compaction effort outside this task's bounded stop.
Invocation is recorded as **mandatory and satisfied**; outcome is recorded
as **`compaction: degraded`** (scan-only; no files moved/compacted this
cycle) per the explicit "degraded allowed, invocation mandatory" allowance.
This is non-blocking: the shipment is already safe-abandoned per §4
regardless of compaction depth.

## 9. Cross-references

* Operator decision: `docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`
* Shipment status constraints: `docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`
* Stash lineage: `BED0DDED` (deliberation `018-DL`) — remains active at high priority pending Stage-owned archival once this abandonment is confirmed durable (out of scope for Ship; not archived by this closure)
* Predecessors: `139-S` (PR merge `9bb3a24b`), `140-S` (PR #361), `137-S`
