---
title: "v1.5.0 release preparation and publish"
date: 2026-08-29
doc_type: plan
agent: "Stage (planning only - Ship executes)"
baseline: "main @ 484da671e218cd7d17a659e0950388d010fae436"
target_version: "1.5.0"
previous_release: "v1.4.11 (2026-07-08, acef3bd8)"
blast_radius: "HIGH - irreversible PyPI publish + CLI distribution + all template families"
requires_plan_hardening: yes
route: "claude-opus-5 / anthropic / high"
---

# Implementation Plan - v1.5.0 Release Preparation and Publish

Date: 2026-08-29
Agent: Stage (planning only — **Ship executes all of it**)
Baseline: `main` @ `484da671`, clean worktree, single worktree, CI green
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Objective

Publish `autoharness` **v1.5.0** — the first release since `v1.4.11`
(2026-07-08) — covering a delta of **1,629 commits / 246 merge commits /
237 `feat` / 500 `fix` / 2,205 files changed**, with a curated changelog, a
synchronized version bump, a full pre-merge dry run, and monitored publication
with rollback conditions.

**Version target: `1.5.0` (minor).** Justified: 237 `feat` commits and 24
shipped features rule out a patch; compatibility paths were generally preserved
and schema evolution used additive versioned mirrors (e.g. `harness-config`
1.0.0 preserved byte-exact, additions published as 1.1.0), ruling out a major.

## Release-blocker triage (decided — see §Blocker dispositions)

Two blockers accepted, three waived/deferred, one external. Full rationale and
evidence in the Stage session summary and the two linked deliberations.

## Preconditions (Ship MUST verify before starting)

1. `main` == `origin/main` == `484da671`; worktree clean; **exactly one
   worktree** (P-016).
2. No queued/active shipment other than this one.
3. `uv`, `python 3.12`, `markdownlint` all present. **Absence of `markdownlint`
   is a STOP condition, not a skip** (per the `D1A46B8C` deliberation).

## Work breakdown

### T1 — Circuit-breaker checkpoint format hardening (blocker)

Consumes stash `8CB31EFB` + `1BDBD08B` (the latter explicitly recommends
folding both; same prescribed format block, same file pair, one checksum
refresh).

* Add an H1 (`# Circuit Breaker - {operation}`) between the frontmatter and
  `## Failure Chain` in the prescribed checkpoint format.
* Double-quote the four free-form frontmatter values (`agent`, `skill`,
  `operation`, `identity`).
* **Paired edit**: `templates/instructions/circuit-breaker.instructions.md.tmpl`
  **and** `.github/instructions/circuit-breaker.instructions.md`.
* Refresh the manifest checksum for the installed file (LF-normalized, computed
  from the committed git blob per the established `.gitattributes` eol=lf
  convention).

*Why blocking*: the template **ships** in the wheel. The space-hash truncation
mode is **demonstrated in the wild**, and the colon-space mode can abort docline
lint **repo-wide** — directly threatening this release's own markdown gate.

### T2 — Refresh stale `workspace-discovery` manifest checksum (blocker)

Consumes stash `1CD4E96F`. Verified this session: manifest L179 records
`24657cad…`; actual LF-normalized SHA-256 is `e38f2fb9…`; file is pure LF and
byte-identical to HEAD (last changed `c37ad959`, 2026-08-15).

* Confirm the drift is legitimate committed content (diff the file against its
  history), then **re-record** the checksum with an explanatory note in the
  established style.
* **Depends on T1** — both edit `.autoharness/harness-manifest.yaml`; sequence
  to avoid conflicts.

*Why blocking*: `verify_workspace` checksum_scan reports the file
"user-modified" when it is not. Running a release whose own verification step
emits a false drift signal makes every other drift result untrustworthy.

### T3 — Curated CHANGELOG `1.5.0` section

* Author a **curated, user-facing** `## 1.5.0 - {date}` section grouped by theme
  (Added / Changed / Fixed / Deprecated), written for users of the tool.
* **Source basis: the 34 closure records in `docs/closure/`** (shipments
  `134-S`→`157-S` / features `125-F`→`149-F`, plus 10 thematic closure
  summaries) — **not** 241 raw PR lines.
* Fold the existing `## Unreleased` content (L3–L104) into the new section and
  leave `## Unreleased` empty or removed.
* **Hard constraint**: `release.yml` L47–L67 extracts the section by exact
  version match via `awk` and **fails the release if no section for `1.5.0`
  exists**. The heading must be literally `## 1.5.0 - YYYY-MM-DD`, matching the
  existing `## 1.4.11 - 2026-07-08` shape.

### T4 — Synchronized version bump to 1.5.0

Update **all six** version surfaces across five files:

| # | File | Locus |
|---|---|---|
| 1 | `pyproject.toml` | L7 `version = "1.4.11"` |
| 2 | `src/autoharness/__init__.py` | L7 fallback `"1.4.11"` |
| 3 | `plugin.json` | L4 `"version"` |
| 4 | `.github/plugin/marketplace.json` | L9 `"version"` |
| 5 | `.github/plugin/marketplace.json` | **L15 `"version"` — second occurrence, easy to miss** |
| 6 | `uv.lock` | L16 `version = "1.4.11"` (regenerate via `uv lock`, do not hand-edit) |

*Hard constraint*: `release.yml` L26–L45 **fails the release** unless the tag
version exactly equals `pyproject.toml`'s version.

### T5 — Release dry run A: build and package integrity

* **Clean `dist/` first.** `dist/` currently contains **stale `1.4.11`
  artifacts** (`autoharness-1.4.11-py3-none-any.whl`,
  `autoharness-1.4.11.tar.gz`). Remove them before building. This is not
  housekeeping — it is correctness:
  * `uvx twine check dist/*` would otherwise validate the **old** artifacts and
    report a misleading PASS.
  * an isolated install from a `dist/*.whl` glob could install **1.4.11** while
    the operator believes 1.5.0 was verified.
* `uv build`
* Confirm exactly two freshly-built artifacts exist and both carry `1.5.0` in
  their filenames; **fail if any non-`1.5.0` artifact is present** in `dist/`.
* `uvx twine check dist/*`
* Install the **explicitly named `1.5.0` wheel** (never a glob) into an isolated
  environment — not the source tree
* Verify `autoharness version` outputs **exactly** `1.5.0`
* Verify `autoharness home` resolves
* Verify **bundled data**: `src/autoharness/data/templates` is present in the
  wheel and populated (this is the `force-include` surface — the most likely
  packaging regression)

**Learning applied** (`docs/compound/2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md`):
assert on **exact string equality** of the version output and on the command's
**own exit status**. Do **not** infer success from non-empty output, and do not
mask failures with a trailing `|| true`.

### T6 — Release dry run B: quality gates

* Full existing test suite (`PYTHONPATH=src python -m unittest discover -s tests`)
  — the canonical gate; the last recorded closure measured **2,018 passing**.
* **Markdown quality gate per the resolved policy** (`D1A46B8C` deliberation,
  Option B): run `markdownlint` over the repository and require **zero**
  violations. If the binary is missing, **HALT** — do not skip.
* `verify-workspace` / template / schema checks; confirm **no new** checksum
  drift beyond the two entries deliberately re-recorded in T1/T2.

### T7 — PR readiness

* Single PR from a single branch (P-016: **no parallel worktrees**).
* All CI green; the changelog section and version surfaces consistent.

### T8 — Post-merge annotated tag `v1.5.0`

* **Only after merge to `main`.**
* Annotated tag `v1.5.0` on the merge commit; push the tag to trigger `release.yml`.
* Pre-push assertion: tag name minus `v` **exactly equals** `pyproject.toml`
  version, and a `## 1.5.0` changelog section exists.

### T9 — Publish monitoring, smoke evidence, and rollback

* Monitor `release.yml`: version validation → changelog extraction → `uv build`
  → `twine check` → PyPI pre-publish state → publish → PyPI smoke → GitHub Release.
* Capture **published-package smoke evidence**: the workflow runs
  `uv tool run --isolated --no-config --from "autoharness==1.5.0" autoharness version`
  and requires exact equality with `1.5.0`, then `autoharness home`.
* Record the GitHub Release URL and the PyPI page as closure evidence.

## Rollback and stop conditions (BINDING on Ship)

| Condition | Action |
|---|---|
| Any dry-run gate (T5/T6) fails | **STOP.** Do not open the PR. Fix and re-run the full gate set from the start. |
| `markdownlint` binary absent | **STOP.** Fail closed; never skip (this is the exact inverse of the `pre-push.sh` fail-open defect). |
| CI red on the PR | **STOP.** Do not merge, do not tag. |
| Tag/pyproject version mismatch | **STOP** before pushing the tag; `release.yml` will reject it anyway. |
| No `## 1.5.0` changelog section | **STOP**; `release.yml` L67 aborts the release. |
| `release.yml` fails **before** the PyPI publish step | Safe. Delete the tag (`git push --delete origin v1.5.0`), fix, re-tag. No version is burned. |
| `release.yml` fails **at or after** the PyPI publish step | **PyPI is immutable — 1.5.0 is permanently consumed. Do NOT retry the same version.** Do not delete the tag. Escalate to the operator. Any remediation ships as **1.5.1**. |
| PyPI reports 1.5.0 already exists at pre-publish | **STOP** and escalate — indicates the version was already burned. |
| Published smoke test fails after a successful publish | Do **not** yank reflexively. Capture evidence, escalate to the operator, prepare 1.5.1. |

**Irreversibility notice**: everything through T7 is reversible; **T8 (tag
push) arms an irreversible publish.** Ship must treat the T7→T8 boundary as the
point of no return and re-confirm all gates before crossing it.

## Out of scope (explicitly NOT in this release)

Recorded so scope cannot drift during execution:

* markdownlint CI job / fail-closed hook redesign (`D1A46B8C` — deferred)
* Engram env-injection mechanism redesign (`B698F01B` — waived, operator WIP)
* file-lock script security hardening (`74C62374`)
* review-persona suppression-rule changes (`BA035180`, `701073F9`, `F0ADCC03`)
* docs frontmatter truncation repairs (`11BCE865`)
* backlog-md registry defect (`0A86267A`) — gated on deliberation `56803680`
* the pre-review evidence epic and its 8 features (`D911A3B2`, `39AA674D`,
  `926FEA6D`, `A02280C8`, `3F80F8A3`, `C327A8DE`, `7A3F570B`, `89E833E1`,
  `8CB5A9B9`)
* capability-pack runtime installer (`47971057`)
* any multi-repo / WSL / external-tool-integration work

## Requires plan hardening

**yes** — irreversible PyPI publish, CLI distribution surface, and all template
families are in the blast radius. P-006 hardening gate applies before
plan-review.

## Plan Hardening

**Hardening required: YES.** Signals: irreversible external publish (PyPI),
distribution surface change (wheel/sdist/CLI), all shipped template families in
the blast radius, and a tag-push action that arms an unattended workflow.
`strict-safety` is **not** enabled in `.autoharness/config.yaml`, so
`ProposedAction`/`ActionRisk` classification is not mandatory — it is supplied
anyway because the blast radius is elevated.

### Learnings consulted (`docs/compound/`)

| Learning | Applied to |
|---|---|
| `2026-08-08-shell-pipeline-exit-status-masking-in-version-probes.md` | T5 — version probes must assert **exact string equality** and the command's **own exit status**; no `\|\| true`, no "non-empty output means success" |
| `2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md` | New invariant INV-4 — a release must never mutate a published versioned schema mirror in place |
| `2026-08-18-lifecycle-gate-must-precede-safe-close-mutation.md` | Gate ordering — **all** gates must pass *before* the terminal, irreversible mutation (here: the tag push) |
| `097-S-canonical-unittest-gate.md` | T6 — the stdlib unittest suite is the canonical gate; do not substitute a narrower run |
| `2026-08-16-multiple-implementation-worktrees-blocks-topology-gate-globally.md` | P-016 — single worktree for the whole release; a second worktree breaks the topology gate globally |
| `2026-05-06-p012-tool-availability-gate-and-dispatch.md` | Preconditions — probe `uv` / `python` / `markdownlint` up front rather than discovering absence mid-release |

### Invariants to preserve

* **INV-1** — Tag version, `pyproject.toml` version, and the changelog section
  heading must denote the identical version `1.5.0`. Enforced independently by
  `release.yml` L39 and L67; Ship must assert it *before* pushing.
* **INV-2** — Exactly one worktree, one branch, one PR for the entire release
  (P-016).
* **INV-3** — Every one of the six version surfaces moves together. A partial
  bump is a silent defect: `release.yml` only validates `pyproject.toml`, so
  `plugin.json` / `marketplace.json` (**both** occurrences) / `__init__.py`
  fallback / `uv.lock` can drift **undetected by CI**.
* **INV-4** — No published versioned schema mirror under `schemas/` is mutated
  in place by this release. Confirm `git diff` touches no
  `schemas/**/<version>.schema.json` file.
* **INV-5** — The two manifest checksum re-records (T1, T2) are the **only**
  permitted checksum changes. Any additional drift is a genuine finding and a
  STOP condition, not something to re-record for convenience.

### Risky actions

| ID | Action | ActionRisk | Approval | Notes |
|---|---|---|---|---|
| **PA-1** | Push annotated tag `v1.5.0` (T8) | **CRITICAL** | **Operator approval required** | Arms the unattended publish workflow. This is the point of no return. |
| **PA-2** | PyPI publish (T9, automated by `release.yml`) | **CRITICAL** | Implied by PA-1 | **Irreversible.** PyPI never permits re-uploading a consumed version. |
| **PA-3** | Re-record manifest checksums (T1, T2) | **MEDIUM** | No | A checksum re-record can *mask* real drift. Each must be justified against committed content before rewriting (INV-5). |
| **PA-4** | Regenerate `uv.lock` (T4) | **MEDIUM** | No | `uv lock` may opportunistically bump **unrelated dependencies**. See mitigation below. |
| **PA-5** | Fold/remove `## Unreleased` (T3) | **MEDIUM** | No | Mis-folding silently drops already-written release notes. Content must be *moved*, never deleted. |
| **PA-6** | Paired template/installed edit (T1) | **MEDIUM** | No | Editing only one side creates template↔dogfood divergence, the exact class `1CD4E96F` documents. |

### Added operational detail

**Environment prechecks (before any work).** Probe and record versions of `uv`,
`python` (must be 3.12-compatible), `git`, and `markdownlint`. A missing
`markdownlint` is a **STOP**, per the `D1A46B8C` deliberation.

**PA-4 mitigation (uv.lock).** Regenerate with `uv lock` and then **inspect the
diff**: it must touch only the `autoharness` `version` field. If any other
package's version, hash, or resolution marker changes, **revert and escalate** —
a dependency bump is not in this release's scope and would silently widen the
blast radius of a "version bump" task.

**T5 bundled-data verification depth.** Do not merely assert the wheel exists.
Inspect the wheel's contents and confirm `autoharness/data/templates/` is
present **and non-empty**, then confirm from the *isolated install* that
`autoharness home` resolves and templates are readable. The `force-include`
mapping (`templates` → `src/autoharness/data/templates`) is the single most
likely packaging regression and is invisible to the test suite, which runs from
the source tree via `pythonpath = ["src"]`.

**T5 version assertion (learning-driven).** Assert
`autoharness version` output `== "1.5.0"` exactly **and** that the command
exited zero. Additionally confirm the installed distribution metadata reports
`1.5.0`, since `__init__.py` prefers `importlib.metadata.version()` and only
falls back to the literal — a stale fallback would otherwise stay hidden.

**Blocked-path handling.** If any dry-run step cannot run (tool missing,
network unavailable for `uvx twine check`), Ship records `TOOL_UNAVAILABLE` and
**halts**. It must not substitute a weaker check or proceed on partial evidence.

**Monitoring signals (T9).** Watch, in order: tag-version validation → changelog
extraction (non-empty notes file) → `uv build` → `twine check` → PyPI
pre-publish state probe → publish → PyPI JSON probe → isolated smoke → GitHub
Release creation. Record the conclusion of each.

**Validation window.** The published smoke test polls PyPI for up to **280
seconds** (`release.yml` L127). Ship must allow the full window before declaring
failure — a slow PyPI CDN propagation is *not* a publish failure and must not
trigger rollback.

**Owner.** Ship executes T1–T9. The operator owns the PA-1 approval decision and
any post-publish escalation.

**Rollback coupling.** The rollback table distinguishes pre-publish (safe:
delete tag, re-tag) from at/after-publish (**version permanently burned;
remediate as 1.5.1, never retry 1.5.0**). Ship must determine *which side of the
publish step* a failure occurred on before taking any action — deleting a tag
after a successful publish does **not** unpublish and creates a misleading
history.

### Review-gate capability risk (carried forward)

Subagent dispatch is **not available** in this environment (no reviewer-persona
dispatch tool is surfaced; `agent-engram`, `agent-intercom`, and `graphtor-docs`
MCP servers all probed unavailable this session). `plan-review` therefore **must**
run its persona rubrics inline, **must** declare the degradation, and **must**
emit literal `dispatch_mode:` and `decision:` markers before `harvest` may
proceed.

### Unresolved operator decisions that still gate safe execution

1. **PA-1 approval** — explicit operator go/no-go before the `v1.5.0` tag push.
2. **Release date** — the `## 1.5.0 - YYYY-MM-DD` heading needs a concrete date
   fixed at authoring time; `release.yml`'s `awk` extraction matches on version,
   but the date must not be left as a placeholder.

## Plan Review

`dispatch_mode: same-model-declared-degradation`
`decision: PASS`

**Declared degradation**: no reviewer-persona subagent dispatch tool is available
in this environment, and the `agent-engram`, `agent-intercom`, and
`graphtor-docs` MCP servers all probed unavailable at session start
(`ENGRAM_DEGRADED`, `INTERCOM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`). All personas
were therefore applied **inline with the caller's model**
(claude-opus-5/anthropic/high), keeping one finding list per persona so coverage
remains auditable. The anchor-review route was not dispatchable; the Architecture
Strategist rubric was applied inline instead of being skipped.

**Plan hardening**: required (irreversible publish, distribution surface, all
template families) and **satisfied** — a `## Plan Hardening` section is present
with invariants INV-1..INV-5, six classified `ProposedAction`/`ActionRisk`
entries, learnings applied, monitoring signals, validation window, owner, and
rollback coupling. `strict-safety` is not enabled, so explicit action
classification was optional; it was supplied regardless.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Constitution Reviewer | inline (same-model) | 1 (P2) |
| Python Reviewer | inline (same-model) | 2 (P1, P3) |
| Scope Boundary Auditor | inline (same-model) | 1 (P2) |
| Learnings Researcher | inline (same-model) | 0 |
| Architecture Strategist | inline (anchor route unavailable) | 1 (P2) |
| Agent-Native Parity Reviewer | inline (triggered: ships agent templates/skills) | 1 (P3) |
| Security Lens Reviewer | inline (triggered: external publish + credentials) | 1 (P2) |

### Cycle 1 — decision: FAIL

**P1-1 (Python Reviewer) — stale `dist/` artifacts would invalidate the entire
dry run.** `dist/` was verified this session to contain
`autoharness-1.4.11-py3-none-any.whl` and `autoharness-1.4.11.tar.gz`. As
originally written, T5 ran `uvx twine check dist/*` and installed "the built
wheel" without cleaning `dist/` or pinning the filename. Consequences: `twine
check` would validate the stale 1.4.11 artifacts and report a misleading PASS,
and an isolated install from a `dist/*.whl` glob could install **1.4.11** while
the operator believed 1.5.0 had been verified — defeating the purpose of the
gate immediately before an irreversible publish.

**Resolution applied**: T5 now requires cleaning `dist/` before `uv build`,
asserting that exactly two freshly-built `1.5.0` artifacts exist, failing if any
non-`1.5.0` artifact remains, and installing the **explicitly named** `1.5.0`
wheel rather than a glob.

### Cycle 2 — decision: PASS

P1-1 verified resolved in the revised T5. No P0 or P1 findings remain.

### Remaining findings (P2 — advisory, accepted)

* **P2-1 (Security Lens)** — the plan does not verify the PyPI publish
  credential/OIDC trusted-publishing configuration before arming PA-1. A bad
  credential fails *before* upload, so **no version is burned**, which caps the
  severity at P2. Positive note: the publish action is SHA-pinned
  (`pypa/gh-action-pypi-publish@cef2210…`), which is correct supply-chain
  practice. *Accepted*: Ship should confirm the publish credential is configured
  when reviewing `release.yml` at T9, but this does not block harvest.
* **P2-2 (Constitution)** — T9 may require deleting a remote tag during
  rollback, a destructive git operation. *Accepted with condition*: tag deletion
  is permitted **only** on the documented pre-publish path and requires operator
  confirmation; it is explicitly forbidden after a successful publish (already
  stated in the rollback table).
* **P2-3 (Scope Boundary Auditor)** — T1 folds `1BDBD08B` (medium) in alongside
  `8CB31EFB` (high); `1BDBD08B` was not in the operator's named triage list.
  *Accepted with rationale*: `1BDBD08B` explicitly recommends this grouping
  ("Suggested grouping: stash 8CB31EFB already targets this same file … Fold
  both into one shipment rather than two passes over the same file"), both are
  defects in the **same prescribed checkpoint format block**, and both require
  the **same** manifest checksum refresh. Splitting them would mean two passes
  over one file and two checksum rewrites. This is same-contract-surface
  consolidation, not scope creep.
* **P2-4 (Architecture Strategist)** — task dependency ordering is stated only
  for T1→T2. *Accepted*: the remaining order is enforced structurally at harvest
  via explicit backlog dependencies and the sequential shipment manifest.

### Acknowledged (P3 — awareness only)

* **P3-1 (Python Reviewer)** — `uv.lock` regeneration risk is real but already
  mitigated by PA-4's diff-inspection requirement.
* **P3-2 (Agent-Native Parity)** — T1 changes a prescribed agent-authored
  checkpoint format. No migration burden: the format is prescriptive
  going-forward, and the two pre-existing non-conforming files were already
  hand-fixed.

### Runtime verification and operational closure

Both present and adequate: T5/T6 supply build, package-integrity,
isolated-install, test-suite, markdown, and workspace/template/schema
verification; T9 supplies monitoring signals, published-package smoke evidence,
a 280-second validation window, an owner, and a pre-/post-publish rollback
split.

**Gate: PASS — cleared to proceed to `harvest`.**
