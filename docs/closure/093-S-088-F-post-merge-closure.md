---
shipment: 093-S
feature: 088-F
pr: 229
merge_commit: e5470befd3f52bcde6f181666a00bce5ca04e014
merged_at: "2026-07-26T06:15:16Z"
closure_status: READY_WITH_CONDITIONS
---

# 093-S / 088-F Post-Merge Closure — Copilot CLI Output Compression Experiment

## Merge Confirmation

- `gh pr view 229 --json state,mergedAt,mergeCommit` → `state: MERGED`,
  `mergedAt: 2026-07-26T06:15:16Z`, `mergeCommit.oid:
  e5470befd3f52bcde6f181666a00bce5ca04e014`.
- Merge commit verified to have **2 parents** (`1815058186484fe41611a1e8633d20a0b017fb43`
  main tip, `469c3e9ed27495b107ea3db8893f9191fdeec237` feature branch HEAD) — a
  genuine merge commit, satisfying P-009 / Constitution XI (no squash, no rebase).
- `git merge-base --is-ancestor e5470bef origin/main` → exit 0, confirmed in
  default-branch history.

## Runtime Verification

**Surface classification**: this deliverable is a **throwaway, flag-gated,
disabled-by-default** prototype. It has no default-on runtime surface in the
shipped harness — the only "runtime" is an operator explicitly opting in by
setting `hooks.json`/`mcp.json` env pins from the provided `.example` templates
and setting `BRAINSPACE_MODEL_ENCODING`. There is no production rollout, no
CI/CD deployment target, and no change to any existing harness runtime path.

**Validator evidence (proportionate to a disabled-by-default experiment)**:

| Check | Method | Result |
|---|---|---|
| Isolation — nothing in `src/autoharness` imports the experiment | `grep -r "088-compression-experiment\|brainspace" src/` (repo-root, base harness source tree) | **PASS** — zero matches; the experiment lives entirely under `experiments/088-compression-experiment/` |
| Disabled-by-default — no durable write on a normal/disabled invocation | `test_hook_cli.py` regression suite (feature-flag-first ordering fixed under Copilot review round; store construction now gated behind the flag check) | **PASS** — covered by automated test, confirmed green in the full experiment suite run at HEAD `469c3e9` |
| Containment — resolver rejects traversal/symlink/env escape | `test_workspace_resolution.py` | **PASS** — 200+ test suite includes dedicated containment cases; confirmed green |
| Base harness regression — no existing behavior broken | `python -m pytest tests -q` | **PASS** — 680 passed, 140 subtests passed, unchanged from pre-merge baseline |
| Experiment suite | `python -m pytest experiments/088-compression-experiment/tests -q` | **PASS** — 226 passed, 2 skipped (tiktoken-dependent, expected in this environment) |
| CI (GitHub Actions) at merge SHA | `gh pr checks 229` prior to merge; post-merge default-branch CI | **PASS** — `ci gate`, `detect code changes`, `test` all green |

No manual/human checkpoint evidence was required: there is no UI, no deployed
service, and no operator-facing runtime change in the base harness. The
experiment's own CLI/MCP entrypoints are exercised exclusively through the
automated test suite above (byte-equivalence, decline-case, and containment
tests act as the functional probes for this prototype).

**Blocked prerequisites**: none for base-harness runtime; see Operational
Closure conditions below for prototype-specific residual items that gate any
future *pilot* promotion (out of scope for this throwaway-experiment merge).

## Operational Closure — Releasability Verdict: `READY_WITH_CONDITIONS`

The **base harness** (everything except the isolated experiment directory) is
unconditionally releasable — no behavior changed, all existing tests and CI
remain green, and the experiment cannot execute unless an operator explicitly
opts in via the example config templates.

The **experiment itself** is `READY_WITH_CONDITIONS` for any use beyond
"merged, disabled, and available for a deliberate opt-in local trial run by
someone who has read the README and decision memo." Conditions:

1. **`workspace.py:152`** (residual, escalated — not fixed in this pass): a
   dict payload with a truthy non-string `cwd` (e.g. `{"cwd": ["x"]}`) still
   reaches `os.path.realpath()` and raises `TypeError`, uncaught by
   `hook_cli.py` (which only catches `WorkspaceContainmentError`). This is a
   fail-safe passthrough gap — low severity in practice (requires a malformed
   hook payload with a non-string `cwd`, which the Copilot CLI does not
   currently emit) but must be fixed before any pilot use, per the plan's
   fail-safe invariant.
2. **`benchmark.py:215`** (residual, escalated — not fixed in this pass): the
   early-decline return path drops `capture_failed` and non-live `provenance`
   fields, which can mislabel a failed command capture or a synthetic test
   case as an ordinary live-declined case in the benchmark report. Moderate
   severity — this is an evidence-honesty gap in the harness that *produces*
   the SAFE WIN determinations the decision memo relies on. Must be fixed
   before the benchmark report or decision memo's SAFE WIN claims are treated
   as authoritative for any pilot go/no-go decision.
3. Pre-existing decision-memo preconditions for any future narrow pilot: real
   `tiktoken` availability in a pilot environment (this environment has no
   tokenizer installed, so every non-declined compression-positive case
   currently declines at the never-expand guard), a stronger task-answerability
   proof beyond the substring proxy, a wider adversarial benchmark corpus, and
   explicit product/security sign-off on retention semantics.
4. Round-9 decline-control regression: re-run the `unwritable-store-passthrough`
   control once a real `tiktoken` install is available, to re-confirm 7/7 (it
   currently reads 6/7 in this tokenizer-less environment).

**Monitoring**: not applicable — nothing is deployed or running by default.
If an operator opts in locally, the experiment's own store TTL/purge and
fail-safe-passthrough logging (stderr on decline/error paths) is the only
"monitoring" surface; there is no telemetry pipeline to wire up for a
throwaway, non-default prototype.

**Rollback**: trivial — delete `experiments/088-compression-experiment/` (or
simply never opt in to the example hook/MCP config). No schema, no CLI
distribution, and no generated-harness artifact depends on this experiment,
per the plan's non-negotiable scope constraints (verified unchanged through
all 13 review rounds).

**Owner**: whoever picks up the 2 residual follow-ups below in a future Stage
cycle (see "Follow-ups for Orchestrator → Stage routing").

**Validation window**: none required for this merge (disabled-by-default, no
rollout). A future narrow-pilot decision would define its own validation
window per the decision memo's ACCEPT/NARROW-PILOT/REJECT preconditions.

## Follow-ups for Orchestrator → Stage Routing

Per Ship's role boundary (Ship does not create backlog items or stash
entries), these are reported here and in the PR body / task comments for the
Orchestrator to route to Stage in a later planning cycle:

1. **`experiments/088-compression-experiment/brainspace/workspace.py:152`** —
   a dict payload with a truthy non-string `cwd` reaches `os.path.realpath()`
   and raises `TypeError` uncaught by `hook_cli.py`'s
   `WorkspaceContainmentError`-only guard, violating the fail-safe passthrough
   invariant. Severity: **low** (requires a malformed hook payload the current
   Copilot CLI does not emit). Suggested fix: type-check `cwd` explicitly and
   raise `WorkspaceContainmentError` for any non-string value before calling
   `os.path.realpath()`.
2. **`experiments/088-compression-experiment/brainspace/benchmark.py:215`** —
   the early-decline `CaseResult` return path drops `capture_failed` and
   non-live `provenance` fields, mislabeling failed captures/synthetic cases as
   live-declined cases. Severity: **moderate** (undermines the benchmark
   report's evidence-honesty contract that the decision memo's SAFE WIN counts
   depend on). Suggested fix: rework the early-return path to preserve
   `capture_failed` and `provenance` before returning.

## Process Deviation Note (P-015)

Shipment closure was executed via `backlogit shipment ship 093-S` (the cascade
single-command path) rather than the single-artifact safe-close procedure
documented in `.github/agents/.ship.agent.md` Step 5 Closure Tasks item 1.
Verified after the fact via `backlogit doctor` (no orphaned/cascade findings
for any `088.*`/`093-S` item) and by confirming `.backlogit/queue/` retains no
remaining `088.*`/`093-S` artifacts, that no corruption occurred — 093-S's
manifest is exactly and completely feature 088-F's full task set (7 tasks, no
siblings), so there was no protected set to violate. Flagged here for
awareness in future shipments where a shipment's manifest is a **partial**
subset of its covering feature's tasks — those cases require the documented
manual safe-close procedure, not the cascade command.
