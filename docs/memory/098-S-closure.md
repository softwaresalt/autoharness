---
type: operational-closure
shipment: 098-S
feature: 093-F
tasks:
  - 093.001-T
  - 093.002-T
  - 093.003-T
title: "Operational Closure — decline-detector failure-signal hardening (093-F)"
status: READY
feature_pr: 244
feature_merge_commit: a89797f1e8a680df6b5c4e4f002690e15e4d2552
reviewed_head: 7e51b945685618cd8c9fddd546856d011d564b88
closed_at: 2026-07-28T18:17:58Z
stash_origin: 3D8724BA
doc_type: memory
source: docs/memory/098-S-closure.md
tags:
  - compression-experiment
  - decline-detector
  - failure-signal
  - copilot-review
  - p-018
  - p-015
  - regex-false-positive
  - closure
---

# Operational Closure — 098-S

## Shipment

Task-only shipment covering feature **093-F**: defensive hardening of the
088-F compression-experiment failure-bearing-SUCCESS decline detector. Closes
the colon-anchored coverage gap so a *successful* tool result that embeds
failure evidence is declined (never compressed). Additive and
fail-safe-directional — a DECLINE broadening only ever makes the compressor
more conservative. Traceability chain: stash `3D8724BA` → deliberation
`008-DL` → 2026-07-28 follow-up plan → `093-F` → policy/hook/oracle + tests.

## What shipped

- Feature PR **#244** → merged to `main` as merge commit
  `a89797f1e8a680df6b5c4e4f002690e15e4d2552` (**P-009 merge-commit satisfied**;
  merge=true, squash=false, rebase=false).
- Reviewed HEAD at merge: `7e51b945685618cd8c9fddd546856d011d564b88`.

Change surface (all within `experiments/088-compression-experiment/` + one
plan doc):

- **093.001-T** — `brainspace/policy.py` `_FAILURE_BEARING_PATTERNS`:
  colon-agnostic non-zero-exit / stderr forms (`exit code 1`, `exited with
  code 1`, `Process finished with exit code 1`, make `*** [target] Error 1`,
  `npm ERR!`, bare `returncode 1`); benign zero-exit forms stay compressible;
  `contains_secret` precedence preserved. Controls in
  `test_policy_decline_cases.py` + hook-level passthrough in
  `test_hook_decide_then_stash.py`.
- **093.002-T** — `brainspace/hook.py` `_EVIDENCE_LINE_PATTERNS` and
  `brainspace/evidence_oracle.py` `_FACT_PATTERNS` brought into **semantic**
  parity for the broadened forms (not literal set-equality — policy uses
  `[1-9]\d*`, hook/oracle use `\d+`, oracle keeps whole-line `npm ERR!`).
  Tests + defense-in-depth test in `test_evidence_oracle.py` /
  `test_hook_type_router.py`.
- **093.003-T** — docs-only: reconciled
  `docs/plans/2026-07-15-...-plan.md` (work-breakdown row, task-detail bullet,
  Hardening section, traceability chain); detector+controls recorded as
  shipped in 088.004-T (commit `118bf21`).

## Copilot review (feature PR #244)

- **Round 1** (2 threads, `policy.py` + `evidence_oracle.py`): the broadened
  patterns used `:?\s*`, which (1) made the separator optional so a
  concatenated `exit code1` matched and (2) let `\s*` span newlines so a
  cross-line `exit code\n1 item completed` matched (in the oracle, this
  *synthesizes* a spurious required fact across unrelated lines). Both VALID.
- **Fix** (commit `7e51b94`): horizontal-only mandatory separator
  `_SEP = (?::[ \t]*|[ \t]+)` (`_RC_SEP` for returncode `=`) across all three
  surfaces, preserving each surface's intentional differences; added
  concatenated + cross-line **negative controls** in all three test files.
- Both threads replied after fix-push and resolved via GraphQL
  `resolveReviewThread`. Re-armed Copilot pass on `7e51b94` came back clean.
- `autoharness gate copilot-review 244` → **SATISFIED** (complete for HEAD
  `7e51b94`, zero unresolved Copilot threads).

## Verification

- Experiment suite `uv run pytest experiments/088-compression-experiment/tests`
  → **282 passed, 2 skipped** (baseline 231 → 254 → 270 → 282).
- Top-level CI-equivalent `PYTHONPATH=src python -m unittest discover -s tests`
  → **721 OK**.
- CI on HEAD `7e51b94`: `test`, `ci gate`, `detect code changes`,
  `copilot-pull-request-reviewer` all **pass**.
- §1.9 readiness gate: all 5 checks passed for HEAD `7e51b94`.

## Releasability

**READY.** Operator-approved merge completed as merge commit `a89797f`
(P-009). No blocking findings (P0=0, P1=0).

## Backlog closure (P-015 single-artifact ops)

Task-only shipment — manifest `custom_fields.items` = `093.001-T,
093.002-T, 093.003-T` ONLY. Protected set = covering feature **093-F**.

- Baseline gate: reconciled local `main` to merged `origin/main` (`a89797f`),
  removed only the 7 half-done closure byproducts I had created, confirmed
  clean `.backlogit/` baseline with all manifest tasks + 093-F + 098-S present
  in queue.
- Manifest items `093.001-T`, `093.002-T`, `093.003-T`: `backlogit move
  --status done` + `backlogit archive` each, verified out-of-queue /
  in-archive after each.
- `098-S` shipment record: `backlogit archive` (single-artifact, **never**
  `shipment ship` — cascade would archive the covering feature 093-F, a P-015
  violation).
- **P-015 post-verify: `093-F` RETAINED in queue** (inQueue=True,
  inArchive=False); only `093-F.md` remains among `093*` queue items; all 3
  tasks + 098-S archived. Protected set intact.
- Backlog index resynced (`backlogit sync`).

Consistent with 088-S: the queue→archive relocations are **committed** to
`main` (backlog files are git-tracked; leaving closure local would be reverted
by the routine `git reset --hard origin/main`).

## Compound learning

`docs/compound/098-S-colon-optional-separator-false-positives.md` — never
broaden a token detector with `:?\s*`; use an explicit mandatory,
horizontal-only separator token; preserve intentional per-surface differences
during "parity"; ship negative controls with every detector broadening.

## Follow-ups

None. No P-001/P-007/P-009/P-011/P-015/P-016 issues.
