++ D:\Source\GitHub\autoharness\docs\closure\146-S-138-F-post-merge-closure.md
---
shipment: 146-S
feature: 138-F
feature_pr: 376
merge_commit: 77ee301a
merged_at: "2026-08-21T09:38:35Z"
closure_status: READY
---

# 146-S / 138-F Post-Merge Closure — Gate-Atomic Baseline Repair

Shipment 146-S repaired both baseline blockers that kept Ship's mandatory
gates red: a malformed YAML frontmatter scalar in a plan document (Gate 1)
and a hardcoded, lifecycle-volatile `.backlogit/queue/019-DL.md` path in two
P-021 contract-test modules (the configured pytest/unittest suite).

## Merge Confirmation

- PR #376 merged to `main` at `2026-08-21T09:38:35Z` with merge commit
  `77ee301a`.
- The merge commit has two parents, `b9d91b18` (prior `main`) and `d2add94c`
  (feature branch tip), preserving the P-009 merge-commit strategy.
- Closure began from synced `main` at `77ee301a`.

## Runtime Verification

**Surface**: `cli` — the only workspace-configured runtime validator surface
for this repository. This shipment touched a docs plan file and three
`tests/` modules only; no `src/autoharness/` runtime, CLI, API, or UI code
changed.

### Structured Validator Evidence

| Field | Evidence |
| --- | --- |
| Validator | Ship post-merge runtime verification |
| Surface adapter | `command` (`.autoharness/workspace-profile.yaml` `runtime_validation.validator_manifest`) |
| Runtime probe | `uv run autoharness --help` |
| Result | **PASS** — exit 0 |
| Canonical gate | `PYTHONPATH=src python -m unittest discover -s tests` |
| Result | `Ran 1681 tests ... FAILED (failures=3, errors=2, skipped=20)` — all 5 are the pre-existing, already-deferred (P-021 stash entry `E8158860`) full-suite test-isolation failures; confirmed to reproduce identically on merge-base `b9d91b18` with this shipment's changes fully stashed out, and zero new failures introduced |
| Hosted CI | `test`, `pipeline-topology (ambient)`, `detect code changes`, `ci gate` — all green on PR #376's Linux runner (the 5 pre-existing failures did not reproduce there) |
| Verdict | **PASS** for runtime-verification purposes; the 5 pre-existing failures are tracked as a follow-up, not a blocker |

## Review-Fix History

- Local review (code-review agent, pre-PR): one P2 finding on the structural
  regression guard's regex coverage. Fixed pre-PR.
- Copilot review (PR #376): two threads. Thread 1 found the widened regex
  still missed a `.joinpath("queue", ...)` call split across lines; resolved
  by replacing the regex/tokenize scanner with an AST-based visitor. Thread 2
  found the PR's own readiness evidence described a failing local test run as
  unqualified "successful" without citing the repository's canonical CI gate;
  resolved by re-running and citing `PYTHONPATH=src python -m unittest
  discover -s tests` directly and rewording the readiness block. Both threads
  replied-to and resolved before merge; P-018 gate returned `SATISFIED` at the
  final HEAD.

## Backlog Reconciliation

The P-015 verified fully-covered-root exception applied: the deterministic
classifier (`classify_shipment_close_path`) confirmed `138-F` is a fully
covered root feature (its sole child `138.001-T` is a manifest member), so
the cascade `backlogit shipment ship 146-S` command was used in place of
manual safe-close.

| Verification | Result |
| --- | --- |
| `returned_ids` | `[]` (empty, matches classifier precondition) |
| `archived_ids` | `["138.001-T", "138-F", "146-S"]` — exactly the manifest's task item, the qualifying feature member, and the shipment record; nothing more, nothing less |
| `parent_id` preservation | `138.001-T.parent_id` re-read as `138-F`, unchanged from the pre-close snapshot |
| Gate decision | `CLOSED` |

| Item | Final state |
| --- | --- |
| `138.001-T` | archived with `archived_status: done` |
| `138-F` | archived with `archived_status: done` |
| `146-S` | archived with `archived_status: shipped`; manifest preserved |

`backlogit sync` completed after the cascade-close operation (914 artifacts
indexed). Source stash `7852CE0D` was already archived by Stage during
harvest (confirmed via `checkpoint-20260821-031602.json` and absence from the
active stash) — no further Ship-side retirement was needed.

## Operational Closure

- **Healthy signals**:
  - Feature PR #376 merged with a merge commit; both P-014 and P-018 gates
    passed at the final HEAD before merge.
  - Canonical local verification passed: `PYTHONPATH=src python -m unittest
    discover -s tests` reproduces only the 5 pre-existing, already-deferred
    failures — zero new failures.
  - CI was green at the feature PR merge gate (`ci gate`, `detect code
    changes`, `pipeline-topology (ambient)`, and `test`).
  - Backlog cascade-close archived the shipment, feature, and task correctly,
    with `returned_ids` empty and `archived_ids` matching the manifest
    exactly.
- **Failure signals to watch**:
  - Any future contract-test module reintroducing a hardcoded
    `.backlogit/queue/<id>.md` path instead of calling
    `_resolve_backlog_artifact` — Regression Guard 2 (AST-based) should catch
    this at authoring time.
  - The full-suite test-isolation pollution tracked under stash `E8158860`
    resurfacing on hosted CI (it currently reproduces only on this
    Windows dev-box run of the full `tests/` suite, not on CI's Linux runner).
- **Validation window**: immediate post-merge closure on 2026-08-21 after
  `main` synced to merge commit `77ee301a`, merged at `2026-08-21T09:38:35Z`.
- **Rollback trigger**: revert merge commit `77ee301a` if the frontmatter
  quoting change regresses `backlogit docs lint` parsing of
  `docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`, or
  if the `_resolve_backlog_artifact` resolver change causes either P-021
  contract-test sibling to fail to locate a backlog artifact it previously
  found via the hardcoded path.
- **Owner**: Ship agent for closure evidence; operator `@softwaresalt` for
  merge approval and release follow-up routing.
- **Residual follow-up**: full-suite test-isolation pollution across four
  unrelated test modules is tracked as P-021 deferred stash entry `E8158860`
  (requires deliberation; Stage-owned triage/harvest, not actioned by Ship
  per the role boundary).

**Closure verdict: READY.** Runtime verification passed, both Copilot review
threads were resolved before merge, backlog cascade-close is complete and
verified, and the full-suite test-isolation follow-up is tracked as stash
entry `E8158860` under Stage/Ship role separation.
