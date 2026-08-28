---
title: "Which defect patterns recur in both local adversarial review and Copilot PR review, and which are deterministically checkable?"
source: "docs/decisions/2026-08-27-recurring-review-issues-tooling-opportunities-spike.md"
doc_type: decision
description: "Retrospective analysis of 1,980 Copilot PR review findings across 303 PRs and 598 HEAD-keyed review rounds against 27 local adversarial plan-review artifacts and 235 corroborating memory/closure/compound records, identifying 15 cross-source recurring defect families and ranking them by proactive deterministic-tooling feasibility."
docline:
  type: spike
  date: 2026-08-27
  time_box: "4h"
  conclusion: "proceed"
  confidence: "medium"
  linked_parent_work_item: null
  promoted_to: ["none"]
  tags:
    - "review-convergence"
    - "copilot-review"
    - "adversarial-review"
    - "static-analysis"
    - "quality-gates"
---

## Goal

**Which defect patterns have recurred across BOTH local adversarial review findings
and Copilot PR review findings, how frequently, and which are suitable for
proactive deterministic tooling?**

The operating motive: local adversarial review and hosted Copilot review are both
expensive and non-deterministic. This repository has spent **598 distinct HEAD-keyed
Copilot review rounds** across **303 PRs** — with 53 PRs requiring 3+ rounds, 24
requiring 5+, and one (PR #224) requiring 20. Any defect family that (a) recurs, and
(b) is mechanically decidable, is a family that should never have reached a review
cycle at all.

## Success Criteria

A sufficient answer must:

1. Establish a counting methodology that distinguishes finding occurrences, review
   rounds, PRs/shipments/work items, and restatements of one underlying issue.
2. Require dual-source evidence — each listed family must be evidenced at least once
   in local adversarial review AND at least once in Copilot review.
3. Normalise semantically equivalent findings into families while preserving concrete,
   citable examples.
4. Rank tooling opportunities by recurrence × severity × determinism, explicitly
   separating mechanically decidable patterns from semantic/judgment ones.
5. State limitations honestly and not overstate frequency.

## Scope Constraints

* **Read-only historical investigation.** No implementation, no backlog mutation, no
  source/template/config mutation, no PR mutation, no branch/worktree creation.
* **One durable artifact only** — this file.
* **No public web research.** Internal repository history, backlogit state, and
  `gh` read-only API only.
* Stage role boundary (P-010) preserved throughout: no code written, no shipment
  claimed, no stash triaged, no gates bypassed.
* P-016 spike/research worktree exception deliberately **not** exercised — the
  investigation ran read-only on the single existing `main` worktree.

## Investigation Approach

1. **Tool gate + prior work.** Probe backlogit MCP (`TOOL_OK`), sync the index
   (`INDEX_SYNC_OK`, 987 items). Declare degradation for Engram / graphtor-docs /
   intercom (MCP surfaces not exposed this session → file-based fallback per
   `.github/instructions/agent-engram.instructions.md`). Read prior work on this exact
   topic: `028-DL` (`docs/decisions/2026-08-25-pr-review-convergence-finding-ledger-deliberation.md`),
   `docs/decisions/2026-08-16-observable-termination-record-spike.md`, and the three
   compound records that explicitly compare local vs. hosted review outcomes.
2. **Build the Copilot corpus.** Repo-wide `GET /repos/{owner}/{repo}/pulls/comments`
   with `--paginate` → 3,815 comments; partition by author.
3. **Build the local corpus.** Extract explicitly-numbered findings from
   `docs/reviews/*.md` (Tier A) and local-review-bearing sections from
   memory / closure / compound / decision / spike / audit records (Tier B).
4. **Classify both corpora** with one shared, mechanism-anchored (not topic-anchored)
   regex taxonomy; iterate the taxonomy twice against sampled false positives and
   frequent-bigram analysis of the unclassified residue; hand-validate exemplars.
5. **Cross-source intersection + cost weighting** — compute per-family PR recurrence,
   month-span persistence, path-class concentration, and share of findings landing on
   high-round (≥3-round) PRs as a proxy for review-cycle cost.

## Findings

### Counting methodology (declared before any count is read)

| Unit | Definition | Value |
|---|---|---|
| **U1 — Copilot finding occurrence** | One inline review comment authored by `Copilot` (= `copilot-pull-request-reviewer[bot]` on the reviews surface). **Verified**: all 1,980 have `in_reply_to_id == null` (thread roots); all 1,835 `softwaresalt` comments are replies. Comment count therefore equals finding count with **zero reply inflation**. | 1,980 |
| **U2 — Review round** | Distinct `(PR, original_commit_id)` pair — one HEAD-keyed epoch, matching the epoch model ratified in `028-DL` §7. | 598 |
| **U3 — PR recurrence (primary dedup-safe metric)** | Distinct PRs on which a family appeared ≥1 time. Immune to a family being restated many times inside one PR or one review thread. | per family |
| **U4 — Local adversarial finding** | One explicitly-numbered finding heading (`F<n>`, `P0-n`, `P1-n`, `N<n>`) in a `docs/reviews/*.md` plan-review artifact. | 149 |
| **U5 — Local corroboration** | A heading-scoped section in memory/closure/compound/decision/spike/audit records that references local review. Counted at **document** level, never summed with U4, because one finding is routinely restated across plan → review → memory → closure → compound. | 200 docs |

**Deduplication rules applied.** (a) "Total deduplicated occurrences" is
`U3 + U4`, **never** the sum of raw counts. (b) Copilot's own duplicate marker
("this issue also appears on line N of the same file", 91 comments) is one comment =
one finding; it was not multiplied. (c) Families are multi-label — one finding may
belong to several families, so family counts do **not** sum to 1,980. (d) Tier B is
presence-corroboration only and is never added to the finding total.

### Evidence coverage

| Source | Volume examined |
|---|---|
| Copilot PR review findings | **1,980** inline findings, **303 PRs**, **598 HEAD-keyed rounds**, 2026-04-02 → 2026-08-27 |
| Repository PRs (denominator) | 413 (303 = 73% received Copilot inline findings) |
| Local adversarial plan reviews | **27** artifacts in `docs/reviews/`; 23 carry per-finding headings → **149** numbered findings |
| Local corroborating records | **200** documents across `docs/memory` (93), `docs/archive/memory` (110), `docs/closure` (33), `docs/archive/closure` (24), `docs/compound` (77), `docs/decisions` (44), `docs/spikes` (16), `docs/audits` (1) → 448 local-review-bearing sections |
| backlogit work items | **987** indexed; 331 archived + 272 done tasks; 101 archived + 30 shipped + 17 done shipments; 13 `-R` review artifacts |

### What Was Discovered

**Every one of the 15 families below is evidenced on both sides.** No family in the
main list is single-source. Counts are **lower bounds** (see Limitations).

`COP` = Copilot findings (U1). `PRs` = distinct PRs (U3, dedup-safe). `Loc` = numbered
local plan-review findings (U4). `Docs` = corroborating local docs (U5). `Hi%` = share
of that family's Copilot findings landing on ≥3-round PRs (review-cycle cost proxy).
`Det` = deterministic detectability: **M** mechanical, **A** mechanical via AST/coverage,
**S** semantic subset only.

| # | Family / categorical nature | What is wrong | COP | PRs | Loc | Docs | Hi% | Det | Conf |
|---|---|---|---:|---:|---:|---:|---:|:--:|:--:|
| F12 | **Work-item / backlog-artifact conformance** — cross-artifact consistency | Task bodies outside required `<!-- BEGIN:description -->` markers; shipment manifest carries its covering feature against a task-IDs-only safe-close contract; ID shape not validated; granularity/width-isolation violations | 97 | 30 | 20 | 17 | 63% | **M** | high |
| F10 | **Template / placeholder parity** — schema-contract drift on the product surface | Unresolved `{{...}}` shipped to operators; `{{VAR}}` used but absent from the variable-resolution table; template ↔ installed-mirror divergence; template links to a file the installer never copies; installation-specific literals hard-coded into portable templates | 138 | 71 | 12 | 44 | 40% | **M** | high |
| F11 | **Evidence staleness vs. HEAD** — documentation precision / provenance | PR body's reviewed-HEAD ≠ current HEAD; readiness block claims a green suite that actually failed; readiness cites a non-authoritative test command; "asserted, not verified" dispositions | 93 | 66 | 6 | 79 | 52% | **M** | high |
| F05 | **Silent fail-open parsing** — parser robustness | Regex/raw-text parsing where structured parsing is required; container shape validated but not members; missing/malformed value silently coerced to a safe default; broad exception swallow; partial read composed as if complete | 104 | 48 | 13 | 37 | **68%** | **A** | high |
| F01 | **Cross-reference integrity** — cross-artifact consistency | Cited path/file/section/line-range does not exist, was renamed, or points elsewhere | 32 | 28 | 3 | 8 | 50% | **M** | high |
| F09 | **Path traversal / injection / secret leakage** — platform + security | Untrusted id interpolated into `Path.glob`; `..`/absolute paths accepted verbatim; raw exception text (possibly containing the secret) returned from the redaction choke point; symlink escape | 73 | 35 | 10 | 26 | **67%** | **A** | high |
| F02 | **Enumeration / registry drift** — cross-artifact consistency | A table/map/classifier/registry in artifact A omits an entry artifact B requires (template-group map, role classifier, capability-pack registry, variable table, expected-red test enumeration) | 36 | 27 | 1 | 1 | 61% | **M** | med |
| F07 | **Status / outcome conflation** — workflow-state semantics | Invalid or failed outcome recorded as `success`; `set -e` bypassing a documented exit-code contract; PowerShell native-command exit ignored on older hosts; substring presence reported as verification success | 42 | 30 | 7 | 21 | 50% | **A** | med |
| F08 | **Platform / shell portability** — platform safety | POSIX vs. Windows divergence; `set -e` vs. explicit exit mapping; `git ls-files` not root-anchored; cwd-derived repo root; documented OS-matrix variable never present in the template | 106 | 55 | 14 | 41 | 50% | **A** | med |
| F06 | **Vacuous or missing test** — test coverage gap | Test never reaches the asserted code path; acceptance criterion vacuously satisfiable; host-dependent assertion passing on one branch; unused fixture/reader; new surface with zero coverage | 28 | 26 | 3 | 14 | 60% | **A** | med |
| F04 | **Schema / API / capability drift** — schema-contract drift | Implementation stricter or looser than the frozen schema; documented tool-call sequence not executable against the installed tool version; checksum semantics disagree between schema and verifier | 48 | 28 | 3 | 9 | 54% | **S**(M subset) | med |
| F03b | **Claim-vs-reality / unwired derivation** — documentation precision | Prose asserts a guarantee the code cannot provide; a new derivation step is never wired into the variable a later step reads (functional no-op); a metadata flag stands in for the transformation it only labels | 72 | 61 | 8 | 30 | 44% | **S**(M subset) | med |
| F13 | **Lifecycle ordering / precondition** — workflow-state semantics | Gate evaluated after the mutation it guards; a fail-closed enumeration pre-filtered so the anomaly it exists to catch is dropped; a status literal used that is not executable in the lattice → deadlock; non-idempotent resume | 169 | 87 | 27 | 103 | 53% | **S**(M subset) | med |
| F03a | **Normative-surface contradiction** — cross-artifact consistency | Two governed surfaces state conflicting rules about the same policy ID, status enum, variable, or numeric constant; a withdrawn disposition survives on a second owning surface | 262 | **135** | 17 | 32 | 50% | **S**(M subset) | med |
| F14 | **Resource / concurrency** — correctness under concurrency | Acquire/release ordering races; liveness diagnosed outside the critical section (check-then-act); guard leaked on partial failure; "bounded tail" materialising the whole journal; PID reuse before liveness check | 26 | 18 | 8 | 15 | **76%** | **S** | med |

#### Dual-source evidence anchors (one local + one Copilot per family)

| # | Local adversarial anchor | Copilot anchor |
|---|---|---|
| F12 | `docs/reviews/2026-08-24-cascade-close-archived-ids-postcondition-review.md` §7 (2-hour rule / width isolation as a standing review dimension); `2026-08-22-git-config-env-containment-review.md` F8 "`145.002-T` is unbounded above" | PR #234 / #185 / #183 / #189 / #202 / #123 / #213 (missing backlogit section markers); PR #237 & #262 (covering feature in a task-only manifest); PR #224 ("not a granular implementation unit") |
| F10 | `2026-08-16-spike-template-docline-conformance-review.md` P1-1 "`source` placeholder could ship unsubstituted"; `2026-08-21-docs-compound-docline-conformance-review.md` P1-3 | PR #3 (guide says copy a `.tmpl` carrying unresolved `{{...}}` into `config.yaml`); PR #292 (`{{DOCS_ROOT}}/size-complexity-reference.md` linked but never installed); PR #379 (hard-coded `-T` instead of `{{SUFFIX_TASK}}`) |
| F11 | `2026-08-14-backlog-storage-root-adoption-review.md` P0-1 "must rest on primary evidence, not release notes"; `2026-08-16-spike-template-docline-conformance-review.md` P1-3 "assumed, not verified" | PR #212 ("PR body marks `588134e` reviewed, current HEAD is `5cf6f9b`"); PR #230; PR #376 ("readiness calls the run successful; this entry records five failures… omits the authoritative CI gate") |
| F05 | `2026-08-22-git-config-env-containment-review.md` N1 "the precondition outcome would have been swallowed by the failure-set-equality gate"; `2026-08-07-model-routing-hierarchy-dynamic-reload-review.md` F4 | PR #297 (11 findings across the 12-round `topology.py` fail-open hunt); PR #387 (raw-text parser treats `source: null` / `~` / a comment as populated); PR #122 (`models` string → tuple of characters) |
| F01 | `2026-08-09-copilot-cli-supervisor-control-plane-review.md` F24 "targets a gitignore template that does not exist"; `2026-08-18-p015-cascade-pre-archived-member-review.md` F3 | PR #115 (a template comment cited a `docs/reference/…` validation-gates path that never existed; the docs actually landed at `docs/gates-reference.md`); PR #258 (plan lists a nonexistent product template) |
| F09 | `2026-08-17-backlogit-self-migration-review.md` F9/F11/F12 (containment, git ingress, `git clean -x`); `2026-08-18-root-scratch-artifact-removal-review.md` F2 "pathspec-literal, never pattern-based" | PR #326 (`redact.py` fail-closed path interpolates raw exception text — leak vector); PR #53; PR #31; PR #297 round 9 (untrusted id into a glob) |
| F02 | `2026-08-22-git-config-env-containment-review.md` F6 "A2's expected-red enumeration omits the third test"; supervisor review P1-3 "gated-action catalog has a consumer but no producer" | PR #3 (`{{PREFIX_*}}` absent from the variable-resolution table); PR #196 (Primitive-4 map omits `skills/brainstorm`); PR #183 (role classifier omits the new category) |
| F07 | `2026-08-14-tune-startup-script-contract-review.md` P1-2 "Misclassification suppresses future detection" | PR #189 (`$PSNativeCommandUseErrorActionPreference` ineffective on older hosts); `cli.py:735-739` recording `exit_code == 2` as `success` (via `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`) |
| F08 | `2026-08-18-root-scratch-artifact-removal-review.md` F7/F8; supervisor P1-2 "'exactly one migration delta' is false for POSIX" | PR #189 (`set -e` bypasses `invoke_bootstrap \|\| exit 2`); PR #187 (`linux_only: false` unimplemented; `{{CI_ENABLE_OS_MATRIX}}` documented, never in the template) |
| F06 | `2026-08-16-spike-template-docline-conformance-review.md` P1-2 "vacuously satisfiable"; supervisor P1-B "exhaustiveness test is vacuous"; `2026-08-18-topology-gate…-review.md` F1 | PR #398 ("this test never reaches `_collect_git_invocation_error`"); PR #318 (host-dependent assertion); PR #224 (empty gate-code tuple vacuously satisfies "all exit codes 0") |
| F04 | `2026-08-14-backlog-storage-root-adoption-review.md` P1-3 "Schema narrowing risk"; `2026-08-21-verify-workspace-variable-derivation-review.md` P1-1 | PR #292 (create/size/complexity call sequencing against backlogit 1.8.0); PR #53 (checksum = `.tmpl` hash vs. schema's installed-artifact hash); PR #313 (`additionalProperties: false` rejects `x-graphtor-*`) |
| F03b | `2026-08-21-docs-compound-docline-conformance-review.md` P1-1 "the verification gate proves too little"; `2026-08-18-topology-gate…-review.md` F4 "asserted, not verified" | PR #296 ("repeats an impossible observability guarantee"); PR #14 (`{{FEATURE_SHIPMENTS}}` claim with no `.tmpl` usage); PR #314 (`redaction_applied: true` is metadata, not redaction); PR #379 (see `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md`) |
| F13 | `2026-08-14-tune-startup-script-contract-review.md` P0-1 "Ungated shipment left as the claim cursor"; `2026-08-21-full-suite-test-isolation-review.md` P0-1 "the accepted hard-stop resolution deadlocks the shipment" | PR #310 (`list_checkpoints` filter drops quarantined records in a fail-closed scan); PR #386 ("`blocked` is not an executable manifest status… the fallback deadlocks `149-S`"); PR #18 (contradictory step ordering in `fix-ci`) |
| F03a | Supervisor review P1-C "the withdrawn F21 disposition survives on two owning surfaces"; P1-1 "the superseded engine pin survives in three live Ship-facing guards" | PR #187 (installer row contradicts the contract at lines 179-185); PR #38 (Stage Step 0.1 "before any backlog reads" vs. Step 0.0 probes that *are* backlog reads); PR #405; PR #12 |
| F14 | Supervisor review F27 "the single-active lock is never required to be acquired atomically"; Ruling 3 / F31 "atomicity does not transfer between neighbouring operations" | PR #326 (three distinct `locking.py` ordering races); PR #337 (bounded tail materialises the whole journal); PR #328 (SIGTERM before the waitable-child check → PID reuse) |

#### Why review catches these late (mechanism, not opinion)

Three compound records state this directly, and the classifier data corroborates them.

1. **Local review checks internal coherence; it does not execute.**
   `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md`:
   a local adversarial pass returned **READY** on text that was "internally consistent,
   said what it claimed, and didn't contradict itself" — and was a **functional no-op**,
   because no one traced *which variable the later, unedited step reads*. This is the
   generating mechanism for F03b, and it explains why F03b's local count (8) is so far
   below its Copilot count (72).
2. **Hosted review finds a different bug class than local review + green CI.**
   `docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`:
   on PR #326, after local report-only review (2 findings, both fixed) and a fully green
   1,587-test CI run, Copilot surfaced ordering races, fail-open redaction paths, and
   implicit-trust gaps in a destructive classifier. This is F05/F09/F14, and it is why
   those three families carry the highest high-round shares (68% / 67% / 76%) — they are
   *structurally invisible* to a test written by the implementation's own author.
3. **Fixes regenerate the family.** `docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md`
   records three consecutive rounds in which each fix for an unsafe filter introduced a
   subtler unsafe filter. `028-DL` §2 formalises this: the review node set is not fixed,
   so acyclicity cannot imply termination. **A deterministic pre-review checker attacks
   the node-generation rate, which is the only lever that dominates round count.**

#### Concentration — why the top candidates are cheap to build

Family findings are strongly concentrated by path class, which bounds each checker's scope:

* **F12**: 86 of 97 findings land on `.backlogit/**` — a closed, small, template-governed,
  machine-readable surface with a declared shape in `.backlogit/templates/*.md`.
* **F10**: 61 on `templates/**` + 29 on `.github/**` — exactly the template↔installed-mirror
  pair the harness already checksums.
* **F11**: 38 on `docs/**` + 34 on `.backlogit/**` — provenance fields, not logic.
* **F05 / F09**: 48 and 30 on `src/**` — a single Python package, AST-analysable.

#### Persistence

Every top family spans 4–5 of the 5 calendar months in the corpus (2026-04 → 2026-08).
These are standing patterns, not artefacts of one bad month.

### What Was Tried and Failed

* **Topic-keyword taxonomy (v1) — rejected.** Bag-of-words on domain nouns
  (`shipment`, `lock`, `archive`) produced a 609-finding "workflow-state" bucket and a
  116-finding "concurrency" bucket driven almost entirely by the word *lock* appearing in
  the `file-lock` skill. 22% remained unclassified with visibly poor precision. Topic ≠
  mechanism; the taxonomy was rebuilt around defect mechanism.
* **Maximum-recall taxonomy (v2) — measured, then rejected for reporting.** Broadening
  reached 70% Copilot recall but re-introduced a 659-finding `F03` catch-all driven by
  the bare idioms *"even though"* and *"still says"*, and inflated F10 by matching any
  mention of a `templates/` path. **The v3 (precision-tightened) numbers are reported;
  v2's higher recall is disclosed as the reason v3 counts are lower bounds.**
* **Splitting `F03` into contradiction vs. overclaim — partially successful.** The split
  (F03a 262 / F03b 72) is meaningful and both halves validated cleanly on sampling, but
  F03a remains the largest family at 135 PRs and remains predominantly semantic. It could
  not be reduced to a mechanical predicate without discarding most of its members.
* **Reconstructing suppressed findings — failed, structurally.** Copilot findings that
  duplicate an earlier unfixed position are never promoted to an inline thread; they exist
  only in the review's free-text `body`. `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`
  documents at least three such findings on PR #297 alone. The comments API cannot see them.
  Recovering them repo-wide would require a per-PR GraphQL `reviews(last:N){nodes{body}}`
  sweep across 303 PRs — out of time-box, and noted as a data gap rather than estimated.
* **Engram / graphtor-docs indexed retrieval — unavailable.** Both capability packs are
  installed (`.github/instructions/agent-engram.instructions.md`,
  `.github/instructions/graphtor-docs.instructions.md`) but neither MCP surface was exposed
  to this session. Declared `ENGRAM_DEGRADED` / `GRAPHTOR_UNAVAILABLE`; the mandated
  file-based fallback (glob/grep/view over `docs/` and `src/`) was used instead. No
  ad-hoc substitution for a *reachable* tool occurred (P-012 preserved).

### Ranked tooling opportunities

Ranked by `PR recurrence × severity × determinism`. **Tier 1 and Tier 2 are mechanically
decidable. Tier 3 is not** — only the named subsets are, and the general case there needs
semantic review and should stay routed to personas and hosted review.

#### Tier 1 — fully deterministic, closed surface, buildable today

| Rank | Checker | Targets | Recurrence | Why it is decidable |
|---|---|---|---|---|
| 1 | **backlogit artifact linter** | F12 | 30 PRs / 20 local | Assert required `BEGIN:`/`END:` section markers per `.backlogit/templates/*.md`; assert shipment `custom_fields.items` contains task IDs only; assert artifact-id shape per type; assert `size` **and** `complexity` present. Closed vocabulary, declared shape, single directory. |
| 2 | **template/placeholder parity gate** | F10 | 71 PRs / 12 local | (a) no unresolved `{{...}}` in installed output; (b) every `{{VAR}}` in `templates/**` appears in the install-harness variable-resolution table and vice versa; (c) each `templates/<name>.tmpl` and its installed counterpart must be mirror-parity modulo variables; (d) every repo path a template links to is actually installed. A partial control exists (`verify_workspace.py` `upstream_updated`) and PR #53 proves its checksum semantics are wrong — fix and extend rather than build new. |
| 3 | **evidence-freshness gate** | F11 | 66 PRs / 6 local | Assert the PR body's declared `reviewed HEAD` equals current HEAD; assert quoted verification commands match the authoritative CI gate (`PYTHONPATH=src python -m unittest discover -s tests`), not an alternate runner; assert closure/memory records name a HEAD that exists. `gate_evidence.head_sha` is the correct existing pinning precedent (`028-DL` §2.2). |
| 4 | **cross-reference integrity checker** | F01 | 28 PRs / 3 local | Every repo-relative path, anchor, and `file:line-range` citation in `docs/**`, `templates/**`, `.github/**`, `.backlogit/**` must resolve. Pure filesystem predicate. |
| 5 | **enumeration-agreement checker** | F02 | 27 PRs / 1 local | For a small declared registry of "these two lists must agree" pairings (capability-pack registry ↔ manifest ↔ preflight ↔ docs table; role-enforcement categories; Primitive template-group map; variable table), assert set equality. Deterministic once the pairings are declared; the declaration is the only real work. |

#### Tier 2 — deterministic via AST or coverage instrumentation

| Rank | Checker | Targets | Recurrence | Why it is decidable |
|---|---|---|---|---|
| 6 | **fail-open parse guard (AST)** | F05 | 48 PRs / 13 local, **68% high-round** | Flag: bare `except Exception`; `return {}` / `None` / `()` inside an `except` handler; `dict.setdefault` keyed on an artifact id; container shape validated without member validation; regex/line-based frontmatter parsing in a module that also imports `yaml`. Precedent for the technique already exists: `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md`. **Highest value per unit of build effort** — it is the most review-cycle-expensive family with an AST-shaped signature. |
| 7 | **containment / injection guard (AST)** | F09 | 35 PRs / 10 local, 67% high-round | Flag non-literal interpolation into `Path.glob` / `subprocess` / `re.compile`; flag exception text or class name interpolated into a redaction module's return value; require `Path.resolve()` + `relative_to(root)` on every path-bearing external field. The three-layer presence/shape/member checklist in `docs/compound/114-S-109-F-copilot-review-fix-patterns.md` is already written — it just is not enforced. |
| 8 | **vacuous-test detector** | F06 | 26 PRs / 3 local | Fully mechanical subset: run each new/changed test under coverage and assert the new SUT lines are actually executed (this alone catches PR #398's "never reaches"); flag unused fixtures/readers; flag tautological assertions. |
| 9 | **exit-status contract guard** | F07 | 30 PRs / 7 local | Flag shell scripts that declare an exit-code contract while relying on `set -e` without `if`-wrapping; flag PowerShell native-command invocations with no `$LASTEXITCODE` check; assert telemetry outcome mapping switches over the full exit-code domain. |
| 10 | **portability scan extension** | F08 | 55 PRs / 14 local | `verify_workspace.py` already has a portability scan and an allow-list (`docs/compound/012-S-portability-scan-allow-list.md`). Extend with: hard-coded ID prefix/suffix literals in `.tmpl`; `git ls-files` without root anchoring; cwd-derived repo root; documented OS-matrix variables absent from the template they govern. Lowest marginal cost of any item here. |

#### Tier 3 — semantic in general; only the named subset is mechanical

| Rank | Family | Mechanical subset worth building | What must stay human/persona/hosted |
|---|---|---|---|
| 11 | F04 | Assert every backlogit MCP/CLI parameter named in `templates/**`, `.github/agents/**`, `.github/skills/**` exists in the installed tool's advertised `params` map in `.autoharness/backlog-registry.yaml`. **This alone would have caught PR #292 exactly.** Plus: schema keys referenced in docs must exist in the schema where `additionalProperties: false`. | Semantic strictness drift ("the schema says any non-whitespace string; the normalizer forces a UUID"). |
| 12 | F03b | **Dangling-definition check**: a variable/list/step introduced in an agent contract must be referenced by ≥1 later step. **Dead-config check**: a documented config key must be read by ≥1 code path. Both fully mechanical. | "Is this guarantee actually achievable?" — the PR #296 impossible-observability class. |
| 13 | F13 | **Status-lattice conformance**: model the shipment/task status lattice once, then assert every status literal used in an agent contract is in it and every named transition is legal. Catches PR #386's deadlock class directly. | Ordering hazards, TOCTOU windows, fail-closed filter-placement reasoning. |
| 14 | F03a (largest, 135 PRs) | **Single-source-of-truth token check**: when a governed token (policy ID, status enum value, variable name, numeric constant) appears in ≥2 governed surfaces, require the claim-bearing text to be byte-identical or an explicit cross-reference. See `docs/decisions/2026-08-09-composability-single-source-of-truth-spike.md`. | Genuine contradiction detection between differently-worded normative surfaces. Not mechanisable at acceptable precision. |
| 15 | F14 (76% high-round — most expensive per finding) | None. | Route deliberately: make the **Concurrency Reviewer** persona mandatory and hosted review non-optional for diffs touching locking, redaction, process control, or destructive classifiers, per `docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md`. |

### Notable excluded (single-source) patterns

Recorded for completeness; deliberately **not** in the main table because they fail the
dual-source requirement.

* **Copilot-only.** Style/readability nits (e.g. PR #20, JSON key indentation); PR-scope
  observations ("this design doc appears unrelated to the PR's stated goal", PR #63).
  Local adversarial review does not raise these because its scope is the plan, not the diff.
* **Local-only — governance and authority.** Role-boundary findings (`2026-08-18-root-scratch-artifact-removal-review.md`
  F14 "Stage must not perform the deletion"), P-021 scope-containment verdicts,
  review-cycle-budget dispositions, and "who is authorised to perform this mutation".
  **Copilot cannot raise these — it has no model of the harness's role separation.**
  This is the strongest argument that the two reviews are complementary rather than
  redundant, and that deterministic tooling should displace neither wholesale.
* **Local-only — plan-stage granularity.** The 2-hour rule and width-isolation are a
  standing dimension in every plan review, but Copilot only reaches them once a task
  artifact appears in a diff (which is why F12's Copilot count is real but its
  *granularity* sub-slice is small).

### Remaining Unknowns

1. **True family frequencies.** 47% of the Copilot corpus is unclassified under the
   precision-tightened taxonomy. A hand-coded stratified sample (n≈200) would convert
   these lower bounds into confidence-bounded estimates. Not done — out of time-box.
2. **Suppressed-finding volume.** Unknown and structurally unrecoverable from this
   corpus. Requires the per-PR GraphQL review-body sweep.
3. **Local report-only review volume.** By contract the `review` skill in report-only
   mode writes **no artifact**, so the bulk of local adversarial review survives only as
   aggregate counts in closure records. The local side of every count here is a severe
   undercount and cannot be corrected without changing that contract.
4. **Would the proposed checkers actually have fired?** Not validated. Each Tier 1/2
   candidate should be retro-run against the specific commits cited in its evidence
   anchors before any is authorised — the same falsification discipline `028-DL` §9.3
   imposes on the convergence analyzer.
5. **False-positive cost.** Unmeasured. A checker that fires on healthy code converts a
   review cost into a build cost. Each candidate needs a measured precision floor before
   it is allowed to block.

## Recommendation

**Conclusion**: **proceed** — scoped to Tier 1 and Tier 2 only.
**Confidence**: **medium**

The evidence supports the core hypothesis firmly: **15 defect families recur across both
review surfaces, every one persists across 4–5 months of history, and 10 of them have a
mechanically or AST-decidable core.** The five Tier 1 candidates target 71, 66, 30, 28 and
27 distinct PRs on closed, well-bounded surfaces (`.backlogit/**`, `templates/**` ↔
`.github/**`, provenance frontmatter, path citations) where correctness is a filesystem or
set-equality predicate — not a judgment.

Confidence is **medium** rather than high for three specific reasons, each of which
constrains the recommendation rather than undermining it:

* Counts are lexically derived lower bounds with 47% of the Copilot corpus unclassified,
  and both corpora are known to undercount systematically (suppressed comments; unrecorded
  report-only local reviews). **Recurrence ordering is trustworthy; absolute counts are not.**
* The single largest family (F03a, 135 PRs) is **not** deterministically checkable. Any
  expectation that tooling removes the review loop is unsupported. The realistic claim is
  that it reduces the *node-generation rate* that `028-DL` §2 identifies as the reason the
  loop does not terminate.
* No candidate has been retro-validated against the commits that motivated it, and no
  false-positive rate has been measured.

Therefore: **proceed to plan the Tier 1 checkers, gated on retro-validation; do not
authorise Tier 3 general-case tooling at all.**

This spike is **complementary to, not a substitute for, `028-DL`**. `028-DL` measures
whether a review loop is converging; this spike attacks the input rate to that loop. The
round data computed here (598 HEAD-keyed rounds; 53 PRs ≥3 rounds; 24 ≥5; max 20 on
PR #224) is exactly the population `028-DL` §9.3 requires for its falsification test, and
is offered to it as free input.

## Next Steps

Per `promote_to: none`, **no backlog item, plan, shipment, or compound entry was created
by this spike.** The artifact stands in `docs/decisions/` for operator reference. The
following are recommendations for a *future* operator-authorised session, not actions taken:

1. **Retro-validate before planning.** For each Tier 1 candidate, run a prototype against
   the exact commits cited in its evidence anchors and record the true-positive and
   false-positive rate. Any candidate that cannot re-detect its own motivating findings
   should be dropped rather than planned.
2. **Sequence by build cost, not by recurrence.** Start with the backlogit artifact linter
   (#1) — closed surface, 86/97 findings in one directory, declared template shape. Then
   the portability-scan extension (#10), which is a delta on an existing control rather
   than a new one.
3. **Land every checker report-only first.** Follow the precedent `028-DL` §9.1 establishes:
   a reader-only, always-exit-0 first slice; promotion to blocking is a separate,
   authority-expanding decision requiring explicit operator consent.
4. **Do not weaken review routing.** F14 (76% high-round) and the local-only governance
   findings are evidence that neither review surface is redundant. Deterministic tooling
   should be additive.
5. **If frequency precision matters to the decision**, commission the two closed data gaps
   first: a hand-coded stratified sample of the unclassified 47%, and a per-PR GraphQL
   review-body sweep for suppressed findings.

## Limitations and Data Gaps

* **Classifier recall.** 47% of Copilot findings, 39% of local plan-review findings, and
  33% of local corroborating sections are unclassified under the reported taxonomy. All
  counts are lower bounds. A higher-recall variant (70%) was measured and rejected for
  precision.
* **Multi-label counting.** Family counts do not sum to the corpus total; one finding may
  appear in several families.
* **Suppressed Copilot findings are invisible** to the inline-comments API by design
  (evidence: `docs/compound/114-S-109-F-copilot-review-fix-patterns.md`). Copilot counts
  are systematically low by an unmeasured margin.
* **Local report-only reviews write no artifact by contract** (`.github/skills/review/SKILL.md`,
  Report-only mode rules). Local counts are severely low; Tier B corroboration partially
  compensates but is presence-only.
* **5 of 27 plan reviews record only aggregate P0/P1/P2 counts**, contributing zero
  numbered findings to U4.
* **API bounds.** PR enumeration capped at `--limit 500` against 413 PRs (no truncation).
  Comments fetched repo-wide with `--paginate`; totals are self-consistent
  (3,815 = 1,980 Copilot + 1,835 human), so no pagination loss was observed. Absence of
  truncation is inferred from that consistency, not independently proven.
* **Temporal window** is 2026-04-02 → 2026-08-27 only. Month totals vary sharply
  (June = 13 findings vs. July = 786); this tracks PR activity, **not** defect rate. No
  trend should be read from month totals.
* **Severity is not measured.** Copilot inline comments carry no severity field. Severity
  and risk ranking in this artifact are analyst judgment informed by local P0/P1 labels
  and compound records.
* **Degraded retrieval.** `ENGRAM_DEGRADED` and `GRAPHTOR_UNAVAILABLE` for this session;
  file-based fallback used per instruction. Indexed code-graph and documentation retrieval
  might have surfaced additional relationships.
* **No secrets were read or exposed.** Tool-managed state (`.autoharness/sessions/**`,
  `.autoharness/supervise/**`) was inventoried by filename only, not opened.

## References

**Prior work consulted**

* `docs/decisions/2026-08-25-pr-review-convergence-finding-ledger-deliberation.md` (028-DL) — finding ledger, HEAD-keyed epochs, monotone measure; the four non-terminating PRs
* `docs/decisions/2026-08-16-observable-termination-record-spike.md` — DEFER, and the conditions this analysis satisfies
* `docs/decisions/2026-08-09-composability-single-source-of-truth-spike.md` — SSOT precedent for the F03a mechanical subset
* `docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md` — render-parity precedent for F10

**Compound learnings (dual-source mechanism evidence)**

* `docs/compound/2026-08-12-hosted-review-catches-fail-closed-gaps-local-review-and-ci-miss.md` (F05/F09/F14)
* `docs/compound/2026-08-21-ship-executable-set-must-wire-into-actual-loop-variable.md` (F03b/F10)
* `docs/compound/2026-08-07-copilot-review-fix-introduces-new-filter-bug.md` (fix-regenerates-family)
* `docs/compound/114-S-109-F-copilot-review-fix-patterns.md` (F05 three-layer checklist; suppressed comments)
* `docs/compound/107-S-084-F-copilot-review-fix-patterns.md` (F04/F09)
* `docs/compound/093-S-review-loop-convergence.md` (push-cap protocol; 13-round loop)
* `docs/compound/2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md` and `docs/compound/2026-08-22-ast-scope-aware-alias-resolution-legb-pitfalls.md` (Tier 2 technique precedent)
* `docs/compound/012-S-portability-scan-allow-list.md` (F08 existing control)

**Local adversarial review artifacts (27 examined; heavily cited above)**

* `docs/reviews/2026-08-09-copilot-cli-supervisor-control-plane-review.md` (largest; 35 numbered findings)
* `docs/reviews/2026-08-17-backlogit-self-migration-review.md`, `2026-08-18-root-scratch-artifact-removal-review.md`, `2026-08-22-git-config-env-containment-review.md`, `2026-08-21-verify-workspace-variable-derivation-review.md`, `2026-08-24-cascade-close-archived-ids-postcondition-review.md`, and 22 others

**Contracts and controls referenced**

* `.github/skills/review/SKILL.md` — personas, severity scale, report-only artifact policy
* `src/autoharness/gates/copilot_review.py` — current-state P-018 gate (not a convergence measure)
* `src/autoharness/verify_workspace.py` — portability scan, checksum/`upstream_updated`
* `.autoharness/backlog-registry.yaml` — operation/`params` map (F04 mechanical subset source)
* `.backlogit/templates/task.md`, `.backlogit/templates/feature.md` — F12 declared shape

**Primary data (read-only, this session)**

* `gh api repos/softwaresalt/autoharness/pulls/comments --paginate` — 3,815 comments
* `gh api repos/softwaresalt/autoharness/pulls/{n}/reviews` — identity confirmation (`Copilot` ≡ `copilot-pull-request-reviewer[bot]`)
* `backlogit_sync_index` (987 items) and `backlogit_query_sql` over `items` / `item_log_entries`
