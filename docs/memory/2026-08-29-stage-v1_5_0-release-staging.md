---
title: "Stage session - v1.5.0 release-blocker triage, planning, and shipment assembly"
date: 2026-08-29
doc_type: memory
agent: "Stage"
route: "claude-opus-5 / anthropic / high"
shipment_id: "158-S"
feature_id: "150-F"
baseline: "main @ 484da671e218cd7d17a659e0950388d010fae436"
---

# Stage Session - v1.5.0 Release Staging

Date: 2026-08-29 (UTC 2026-08-30T05:xx)
Route: claude-opus-5 / anthropic / high (P-013.5)
Mode: normal sequential; `DARK_MODE_ACTIVE` inactive
Baseline: `main` @ `484da671`, clean worktree, single worktree, CI green

## Outcome

Assembled exactly one queued shipment **`158-S`** ("v1.5.0 Release Preparation
and Publish") containing covering feature **`150-F`** and **10 tasks**
(`150.001-T` .. `150.010-T`). Handed off to Ship. Stage performed no
implementation, created no branch, ran no build/test/linter, and created no
parallel worktree (P-001 / P-016 preserved).

## Session gates

* `TOOL_OK`: backlogit (registry `.autoharness/backlog-registry.yaml`,
  `features.shipments: true`, `checkpoints: true`)
* `INDEX_SYNC_OK` (1026 at start, 1035 at end)
* `ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE` — no MCP tools
  surfaced for those packs; fell back to file-based exploration throughout
* Crash-resumption: **ZERO-CANDIDATE NORMAL STARTUP**. Enumerated all 14
  checkpoints with no status/agent filter; anomaly scan first (none found); all
  `stage/resolved`; no active recovery candidate. Not a failure.

## Blocker dispositions

| Entry | Disposition | Basis |
|---|---|---|
| `1CD4E96F` | **BLOCKER — accepted** (`150.002-T`) | Manifest L179 `24657cad…` vs actual LF `e38f2fb9…`; pure LF, identical to HEAD. False "user-modified" signal poisons release verification. |
| `8CB31EFB` + `1BDBD08B` | **BLOCKER — accepted** (`150.001-T`, folded) | Shipped template; MD041 push-block + demonstrated YAML truncation / latent repo-wide docline abort. `1BDBD08B` itself recommended the fold. |
| `8AC574F1` | **SATISFIED — archived** | Re-measured: all 13 pipeline skills now installed (18 total). PR #409 did it. |
| `B698F01B` | **WAIVED — stays ACTIVE** | Symptom gone at `484da671` (all 3 guards pass, CI green); orphaned `.pyc` untracked+gitignored so cannot ship; stale comment lives in unpackaged `tests/`. Operator WIP preserved. |
| `D1A46B8C` | **DEFERRED — stays ACTIVE** | Decisive: `templates/scripts/pre-commit-markdownlint.{sh,ps1}.tmpl` **exist and ship**, so the contract gap is dogfood-only, not user-facing. |
| `B57F9E24` | **NON-BLOCKING external — stays ACTIVE** | backlogit-owned; upstream `3A33E404`; workaround held (14/14 checkpoints clean this session). |

Ruled out as release blockers (not pulled in): `74C62374`, `BA035180`,
`701073F9`, `F0ADCC03`, `11BCE865`, `B90A5BBF`, `0A86267A` (gated on
deliberation `56803680`), `47971057`, and the pre-review-evidence epic
`D911A3B2` with its 8 features.

## Key evidence that changed decisions

1. **Packaging boundary** *(corrected post-review — the original entry here was
   wrong; see PR #422 threads)*. The wheel is `packages = ["src/autoharness"]`
   plus **ten** `force-include` mappings (`pyproject.toml` L35–L45):
   `templates`, `schemas`, `.github/agents`, **`.github/skills`**,
   `.github/instructions`, `.github/prompts`,
   `.github/copilot-instructions.md`, `.github/copilot-review-instructions.md`,
   **`docs`**, and `AGENTS.md`. The original claim that `.github/skills/` and
   `docs/` "do not ship" was **false** — both ship. Genuinely absent from the
   wheel are `.github/workflows/`, `.githooks/`, `scripts/`, and `tests/`
   (the `.github` inclusions are specific subdirectories plus two named files,
   not `.github` wholesale).

   **Effect on dispositions: none flip, but two rationales change direction.**
   `1CD4E96F` becomes *stronger*, not weaker — `.github/skills/workspace-discovery/SKILL.md`
   ships, so its stale checksum is user-facing, not merely dogfood. Likewise the
   circuit-breaker fix covers a shipped installed mirror as well as the
   template. `D1A46B8C` and `B698F01B` are unaffected: `scripts/`,
   `.githooks/`, `.github/workflows/`, and `tests/` are all still outside the
   wheel. **Do not reuse the original templates-only boundary as evidence.**
2. **`D1A46B8C` inversion.** The addendum implied a shipped install/tune
   contract break. The pre-commit script *templates* exist and ship — the gap is
   only in this repo's own `scripts/`. Dogfood drift, not a product defect.
3. **`B698F01B` de-escalation.** Its premise was an uncommitted diff. The
   committed tree passes all three guards.
4. **Stale `dist/`.** `dist/` still holds `1.4.11` artifacts — caught in plan
   review as **P1-1** and fixed in the plan before harvest.
5. **`marketplace.json` has two `version` fields** (L9 and L15), so the bump has
   six loci across five files.

## Artifacts created

* `docs/decisions/2026-08-29-markdownlint-enforcement-contract-for-v1_5_0-deliberation.md`
* `docs/decisions/2026-08-29-engram-env-injection-guard-v1_5_0-waiver-deliberation.md`
* `docs/plans/2026-08-29-v1_5_0-release-preparation-plan.md`
  (includes `## Plan Hardening` and `## Plan Review`)

Plan review: `dispatch_mode: same-model-declared-degradation`,
`decision: PASS` after one FAIL→revise cycle on P1-1.

## Stash reconciliation

**Final state: 41 active** (unchanged in count from the 41 at session start, by
coincidence of four archives and four additions).

Sequence: 41 at start → archived 4 (`8CB31EFB`, `1BDBD08B`, `1CD4E96F`,
`8AC574F1`), non-destructively and each with a forward reference → **37** →
created `5CBA0A85` (preserving `8AC574F1`'s residual open question: fail-closed
agent→skill dangling cross-reference check for verify-harness) → **38**, which
was the count at the original reconciliation.

Three entries were added after that point and this record accounts for them:

* `6A2D62DD` (spike, medium) — range-deterministic sizing + one-session-per-cycle
  lifecycle *(operator intake)* → **39**
* `2E67938C` (feature, high) — Stage must integrate/enforce backlogit
  size/complexity metadata *(operator intake)* → **40**
* `8E10B13B` (bug, high) — `release.yml` pre-publish PyPI probe fails open
  *(P-021 C2 capture from PR #422 review)* → **41**

Disposition records were appended to `B698F01B`, `D1A46B8C`, and `B57F9E24`
(all remain active).

P-021 C5 duplicate scan run unconditionally over all consumed entries: **CLEAN**.

## Next steps (Ship)

Claim `158-S`. Execute `150.001-T` → `150.010-T` in dependency order — the chain
is now **fully ordered from a single root** (`150.001-T`), so "in order" is
enforced by the graph rather than only stated in prose.

Hard conditions:

* **Execute from the current synchronized `origin/main` HEAD, not `484da671`.**
  That commit is the *planning* baseline only; merging the staging PR necessarily
  advances `main` past it. Run the plan's "Baseline re-verification" checks at start.
* Single worktree / branch / PR (P-016).
* Markdown gate is fail-closed — halt if `markdownlint` is absent.
* Clean `dist/` before building; verify **all ten** `force-include` destinations,
  not just `templates`.
* `150.008-T` owns the merge to `main` (operator-approved) and records the merge
  commit SHA that `150.009-T` tags.
* `150.009-T` (tag push) requires explicit operator approval, must assert `1.5.0`
  is **absent from PyPI** (fail closed if ambiguous), and is the irreversible
  boundary.
* On publish failure, **probe PyPI to determine actual upload state** — do not
  infer it from the failed step number. After a confirmed publish, `1.5.0` is
  permanently burned and remediation ships as `1.5.1`.
