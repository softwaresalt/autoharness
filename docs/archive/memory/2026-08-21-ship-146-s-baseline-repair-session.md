# Ship session — 146-S gate-atomic baseline repair (138-F / 138.001-T)

Date: 2026-08-21
Agent: Ship (full lifecycle: claim -> implement -> review -> PR -> merge -> closure)
Branch: `feat/146-s-prerequisite-repair-both-baseline-blockers-malformed-plan-frontmatter-archived-019-dl-contract-test-load`
  (merged), then `post-merge/146-s-baseline-repair` (closure)
PR: #376, merge commit `77ee301a2cb91cda5c244d0d52363a8d95277dc7`

## Outcome

**SHIPPED.** Both baseline-red blockers repaired in one gate-atomic task
(138.001-T): the malformed `blast_radius` YAML scalar in
`docs/archive/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` (Gate 1)
and the hardcoded `.backlogit/queue/019-DL.md` path in two P-021
contract-test modules (pytest/unittest). Shipment cascade-closed via the
P-015 verified fully-covered-root exception.

## What actually happened

1. Zero-candidate crash-resumption check (no `ship`-owned checkpoints existed
   among 7 total, all `stage`-owned) — continued straight to normal intake.
2. Pre-claim topology gate passed twice (before branch creation, immediately
   before claim); claimed 146-S; post-claim topology gate confirmed sole
   active shipment.
3. Implemented Scope A (1-line quoting fix) and Scope B (shared
   `_resolve_backlog_artifact` resolver + two regression guards) exactly as
   staged; confirmed baseline red -> green transition for both blockers.
4. **P-021 defer-capture**: discovered 5 tests fail only when the FULL
   `tests/` suite runs together (cross-test-file pollution), unrelated to
   this task. Ran the discovery lookup (zero matches in active+archived
   stash), captured a fresh threadless C2 entry (`E8158860`) BEFORE closing
   the finding, per the single-write invariant. Confirmed pre-existing via
   git-stash-based A/B testing against merge-base main, twice (once via
   pytest, once via the canonical `unittest discover` gate).
5. Local review (code-review agent) found one P2 (regex guard coverage gap)
   — fixed pre-PR, in scope per C3 (same-contract-surface completion of the
   guard's own stated purpose).
6. PR #376 created; Copilot review found two MORE real gaps in the same
   guard/evidence, both genuinely in scope per C3 (not new expansions):
   a `.joinpath()` call the widened regex still missed (fixed by rewriting
   the guard as an AST visitor — see the compound doc), and readiness
   evidence describing a failing local run as "successful" without citing
   the canonical CI gate (fixed by re-running and citing
   `PYTHONPATH=src python -m unittest discover -s tests` verbatim in the PR
   body, WITHOUT editing the already-captured `E8158860` entry).
7. Both Copilot threads replied-to (citing the fixing commit) then resolved,
   in that order, per C3 thread-present ordering. P-018 gate reached
   `SATISFIED` at the final HEAD; P-014 all-5-checks gate passed.
8. Operator's prior "keep working autonomously" instruction, scoped in the
   task prompt to this bounded shipment sequence, served as the explicit
   normal-mode merge approval signal once P-014/P-018 passed for the exact
   HEAD and merge strategy was confirmed merge-commit-only (repo settings:
   `allow_merge_commit=true`, both others `false`).
9. Merged with `--merge`; verified two parents. Post-merge closure branch
   created (never committed closure work to `main`). Classifier
   (`classify_shipment_close_path`) confirmed `138-F` is a fully-covered
   root -> cascade `backlogit shipment ship 146-S` used instead of manual
   safe-close; all three P-015 post-cascade verifications passed
   (`returned_ids=[]`, `archived_ids` exact match, `parent_id` preserved).

## Key decisions worth remembering

1. **A review-fix that hardens the task's OWN newly-added regression guard
   to actually meet its own stated acceptance criterion is C3 in-scope, not
   a C1 expansion** — even across two separate review passes each finding a
   different real gap in the same guard. The test is "does the fix require
   only completing the exact change already authorized" (the guard's own
   B5 criterion: "fails if a new lifecycle-volatile path literal is
   introduced"), not "did a prior review pass already touch this code."
2. **The single-write invariant on a captured P-021 entry survives even a
   legitimate evidence-completeness finding about that entry.** Copilot's
   second thread was about MY OWN PR readiness evidence being imprecise,
   not about the captured entry's classification being wrong — the fix is
   to correct the PR's own evidence (body/replies), never to edit the
   already-captured stash entry.
3. **`pytest tests/` and `PYTHONPATH=src python -m unittest discover -s
   tests` produce the SAME 5 pre-existing failures in this repo** — the
   canonical CI gate is `unittest discover`, not pytest; citing it directly
   (not just an equivalent pytest invocation) is what a reviewer expects
   as authoritative evidence.
4. **AST-based structural regression guards generalize far better than
   regex-over-text guards** for a "no hardcoded X outside the resolver"
   assertion — see
   `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`.

## Degraded capabilities (P-012)

`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` (packs
installed per `.github/instructions/`, MCP tools not exposed to this
session; backlogit CLI fallback used throughout per the registry's
`cli_command` fields, file-based exploration used for code discovery).

## Follow-ups for the next session

* P-021 deferred entry `E8158860` (full-suite test-isolation pollution
  across `test_gate_pipeline_topology_cli.py`, `test_gates_topology.py`,
  `test_repo_root_artifacts.py`, `test_telemetry_gitignore_template.py`)
  requires Stage deliberation (C6). Does not reproduce on hosted Linux CI;
  reproduces consistently on this Windows dev-box run of the full `tests/`
  suite. Not actioned further by Ship (role boundary).
* 147-S / 144-S / 145-S remain queued behind this shipment in the topology
  chain; `main` is synced to `77ee301a` and ready for Orchestrator reload.
