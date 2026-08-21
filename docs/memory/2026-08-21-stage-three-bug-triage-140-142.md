---
title: "Stage session - three-bug triage, deliberation, planning and harvest (8FA8FC22 / E8158860 / F73BA065)"
date: 2026-08-21
agent: Stage
route: "claude-opus-5 / anthropic / high (P-013.5, inherited)"
shipments: [148-S, 149-S, 150-S]
features: [140-F, 141-F, 142-F]
deliberations: [023-DL, 024-DL, 025-DL]
---

# Stage Session Memory - 2026-08-21

Operator selection: "We should work on resolving the following three bugs:
8FA8FC22, E8158860, F73BA065." All three treated as explicitly selected for
planning and shipment assembly. None omitted.

## Session gates

* `TOOL_OK: backlogit 1.10.0`; registry `.autoharness/backlog-registry.yaml` present,
  root `.backlogit`. `INDEX_SYNC_OK` at start (915 indexed) and at close.
* `ENGRAM_DEGRADED`, `GRAPHTOR_UNAVAILABLE`, `INTERCOM_DEGRADED` - none of those
  MCP surfaces was available in this session. All discovery, learnings retrieval
  and impact analysis were done file-based. No operator broadcasts were possible;
  only safe, non-destructive Stage work was performed and no approval-dependent
  destructive operation was bypassed.
* Crash-resumption scan: 7 checkpoints enumerated with NO `agent`/`status` filter;
  `needs_quarantine: 0`, `quarantined: 0`, no validation anomalies; zero ACTIVE
  `stage`-owned candidates. Normal startup, not a failure, not an operator handoff.

## Grouping decision (Step 1.5) - THREE features, not one

All three entries carry the literal `DEFERRED SCOPE EXPANSION` marker, so the
Step 1 precedence rule FORCED the `deliberate` route for each regardless of shape
or size (P-021 C6). They were deliberately NOT grouped into one covering feature:
they touch three disjoint surfaces (Python CLI install correctness / `tests/`
isolation / `docs/` corpus), carry three different risk profiles, and grouping
them would breach width isolation (P-003) and produce an incoherent release unit.

Instead: an explicit dependency-ordered shipment sequence
**148-S -> 149-S -> 150-S**, matching this repository's single-active serial
operating model. Rationale for the order is genuine, not cosmetic:

1. **148-S first** - smallest, mechanical, zero-risk, and it restores a
   trustworthy `backlogit docs lint` signal that later shipments' Gate 1 evidence
   depends on. 72 of 73 files failing makes that gate's signal useless today.
2. **149-S second** - makes the canonical local test gate green, so 150-S's
   verification evidence is not contaminated by five pre-existing failures.
3. **150-S last** - highest blast radius, and it EXTENDS
   `test_scope_containment_policy_contract.py`, the very module implicated as the
   polluting set in 149-S. Landing both concurrently would confound the bisect.

## P-021 obligations discharged

* **Duplicate detection (unconditional, C5):** run over ALL THREE entries against
  all 187 stash entries (14 active + 173 archived). **CLEAN in all three cases.**
  Nearest neighbours examined and explicitly rejected: 7852CE0D (twice),
  34D50F2D, 90F2A9F8, 395EBE60. No `DISCOVERY-STATUS` tokens present.
* **Late-identifier reconciliation (C6):**
  * 8FA8FC22 - performed, NO RESULT; `PR: N/A` / `review-thread: N/A` stand as
    truthful terminal records (pre-PR Stage spike). Corroborating Ship record
    located: `docs/closure/145-S-137-F-post-merge-closure.md`.
  * E8158860 - performed, **RESULT FOUND**; PR reconciled `N/A -> #376` from
    `docs/closure/146-S-138-F-post-merge-closure.md`, which cites the entry by ID.
    `review-thread: N/A` stands.
  * F73BA065 - performed, NO RESULT; `task: N/A` stands truthfully (147-S manifest
    is `[139-F, 139.001-T, 139.002-T]`; the doc was authored during shipment-level
    post-merge closure, which has no task record). `PR=380` NOT overwritten.
  All reconciliations applied IN PLACE; no second entry created anywhere.

## Substantive findings Stage added beyond the entries

1. **8FA8FC22 was under-scoped by ~4x.** Re-measured from
   `.autoharness/staging/verify-workspace-report.json`: 83 unresolved occurrences
   across **62 distinct variables** in 10 staged files, versus the entry's 4-pair
   / 21-occurrence figure. `{{DEFAULT_BRANCH}}` alone is 12.
2. **The likely root cause of 8FA8FC22, found at plan review:**
   `config.model_routing` is POLYMORPHIC - `tier2`, `tier3` and `orchestrator` are
   SCALAR STRINGS while `tier1`, `stage`, `ship` and `escalation` are MAPPINGS. A
   mapping-only derivation returns nothing for exactly the variables the entry
   cited as evidence. Captured as amendment B6.
3. **Option (c) for 8FA8FC22 is refuted, not merely unattractive.** The
   verify_workspace renderer produces the `.autoharness/staging/` refresh tree,
   the same module raises unresolved placeholders as hard errors
   (verify_workspace.py:3494, :3689), and the P-021 parity contract test imports
   it directly. Declaring it non-authoritative would retire a live gate.
4. **E8158860's own hypotheses are refuted.** There is no `os.chdir` anywhere in
   `tests/`, no bare `os.environ[...]` assignment, and every `patch.dict` is
   context-managed. Leading structural suspect instead: 58
   `tempfile.TemporaryDirectory(dir=Path.cwd())` sites creating temp trees inside
   the live working tree.
5. **E8158860's open question is answered.** Windows-local and CI-invisible, but
   it DOES reproduce on the canonical `unittest discover` gate. That raises
   priority - a defect invisible to CI is exactly the class that erodes local-gate
   trust, and it has already contaminated three consecutive shipments' evidence.
6. **F73BA065 is not external.** `backlogit docs scope` maps `docs/compound/` to
   `learning` (so `doc_type` is path-derived), `backlogit docs migrate` is a
   first-party idempotent migration, and its dry-run plans
   `body_bytes_changed: false` for every file. The "make it optional locally"
   lever the entry hoped for does not exist (no docline config in this repo), so
   option (b)/(d) collapse into (c) - and (c) fails because the gap is
   self-closable today.

## Gate outcomes

| Entry | Deliberation | Hardening (P-006) | Review | Unresolved P0/P1 | Cycles |
|---|---|---|---|---|---|
| F73BA065 | 025-DL | NO (reasoned, not defaulted) | PASS | 0 | 1 of 3 |
| E8158860 | 024-DL | YES - HARDENED (A1-A3) | PASS (A4-A5) | 0 | 1 of 3 |
| 8FA8FC22 | 023-DL | YES - HARDENED (B1-B4) | PASS (B5-B7) | 0 | 1 of 3 |

## Verification performed at close

* `backlogit doctor`: 62 pre-existing findings, **ZERO touching any ID created
  this session** (140/141/142/148/149/150/023-DL/024-DL/025-DL).
* Shipment manifests verified by read-back; item counts match the harvested
  hierarchies exactly (3 / 6 / 7).
* Dependency chain verified acyclic: `149-S -> 148-S`, `150-S -> 149-S`.
* Ready-shipment queue returns **148-S alone** as claimable - single-active
  preserved.
* All 13 tasks carry BOTH `size` and `complexity` as structured fields, written
  through the three-call sequence the registry requires (create with no sizing;
  `--size` + `--size-source` + `--size-ruleset-version` together; `--complexity`
  alone). Verified by SQL read-back.
* All new queue artifacts parse; no dangling references.

## Role-boundary statement

Stage made NO source, test, template, or config edit; ran NO build, test suite,
or linter; created NO branch, commit, push, or PR; claimed NO shipment; created
NO worktree (P-016 topology unchanged, still one worktree on `main`). The only
read-only external invocations were `backlogit docs scope`, `backlogit docs
migrate` in DRY-RUN (plan-only, zero writes), and `--help` probes. Operator
working-tree changes to `.backlogit/stash.jsonl` and `.mcp.json` were preserved;
`.mcp.json` was not touched. Publication of the `.backlogit` bookkeeping belongs
to Orchestrator/Ship, not Stage.

## Review-fix cycle 1 (PR #386, Copilot review - 17 threads)

Performed by Stage on the staging artifacts only; PR #386 CI green, P-018 blocked
on 17 unresolved Copilot threads. Corrections left UNCOMMITTED for Orchestrator to
publish. Route honoured: claude-opus-5 / anthropic / high (P-013.5).

**P-021 C1 classification: all 17 = SAME-CONTRACT-SURFACE COMPLETION -> fix, not
defer.** Verified rather than assumed: every flagged path appears in this session's
own HEAD commit `3e42d115` (the three plans, the derivation review, deliberations
024-DL/025-DL, features/tasks under 140-142, and the archived stash line this
session wrote). No finding required a new deferred entry.

Four defect classes, each fixed on EVERY duplicated surface so plan, review,
deliberation and task contracts stay consistent:

1. **Unsatisfiable containment AC** (threads 1-3 area): AC6/AC-F5 forbade every file
   outside `docs/compound/` while the same task mandates creating
   `tests/test_docs_compound_frontmatter_contract.py`. Exempted the contract test
   as an in-scope deliverable in 140-F, 140.001-T and the plan.
2. **Non-runnable exclusion protocol**: `python -m unittest` has no deselect flag,
   so "rerun with the three modules excluded" was unexecutable. Replaced with a
   deterministic POSITIVE dotted-name generator (82 of 85 modules, `Sort-Object`
   for reproducible ordering) in 141.001-T, the isolation plan (incl. amendment A5
   and the baseline wording) and 024-DL.
3. **Model-routing contract inversions** (the substantive cluster). Re-verified
   against `.github/skills/install-harness/SKILL.md` rows 414-453 and a FULL-TREE
   consumer search:
   * Scalar `orchestrator` keeps the **Tier 2** provider/effort fallback (rows
     426-427, line 452); only TIER scalars empty their metadata. `ORCHESTRATOR_FAMILY`
     keeps its own `gpt-5.4` default (row 428).
   * `{{STAGE_*}}`/`{{SHIP_*}}` are **RESOLVED-FROM-SOURCE with per-sub-field tier
     fallback**, NOT raw/empty. The prior claim that they occur only in
     `harness-config.yaml.tmpl` was FALSE - `_orchestrator.agent.md.tmpl` lines
     527-533 consume all six and its prose demands concrete values. Review finding
     **P2-1 WITHDRAWN**, replaced by **P1-4**, RESOLVED.
   * `graphtor_docs.binary_path: null` resolves through PATH -> local candidates ->
     final `graphtor`, never `""` (rows 875/881, line 1088).
   Surfaces corrected: 142.001-T, 142.002-T, 142.003-T, 142.005-T, the derivation
   plan (B6 + Task 1 + Task 3) and the derivation review (P1-1 + P2-1/P1-4 + verdict).
4. **Encoding corruption**: a lone `\b` in F73BA065's text decodes as BACKSPACE in
   both the JSON stash line and 025-DL's double-quoted YAML scalar. Fixed at both
   the archived source-of-truth and the deliberation; index re-synced (935 items)
   after the out-of-band edit.

**Lesson (candidate for `docs/compound/`).** The review's own P2-1 generalised from
ONE template to the whole tree and inverted a contract as a result. A claim of the
form "variable X occurs ONLY in file Y" is a full-tree search obligation, not an
inference from the file you happened to open.

**Re-gate.** Derivation review re-gated **PASS**, 0 unresolved P0/P1, cycle 1 of 3.
The other two reviews needed no verdict change (their findings were AC-text defects,
not verdict-bearing). Integrity re-verified after edits: all 13 YAML frontmatters
parse, 0 leading/trailing-space references repo-wide, both stash JSONL files valid
(176 archived / 12 active lines), manifests unchanged at 148-S (3) -> 149-S (6) ->
150-S (7) with 148-S alone claimable, and no task ID or scope lost.

**Residual risk (new, accepted and recorded, not silently resolved).** Storing a
RESOLVED role-route value in `harness-config.yaml.tmpl` materialises a concrete
value where the operator declared none, so later `tier3`/`tier2` changes stop
propagating through that stored file. The contract mandates the fallback, and the
template comment "falls back to tier3/tier2 when empty" describes CONSUMER
behaviour on an empty field - so the two are consistent. Changing it would be a
SKILL.md contract change and re-enters P-021 capture; it does not block 150-S.

**Out of scope, verified benign.** Active entry `84D8E6AB` carries a `\r` inside a
multi-line text field - legitimate CRLF, not corruption, and untouched by this
work. Pre-existing `\\b` sequences elsewhere in the archive are correctly escaped
Windows paths. `.mcp.json` preserved untouched.

**Role boundary re-affirmed.** No commit, push, PR-body edit, thread reply/resolve,
merge, shipment claim, source/test/template edit, build/test run, or branch/worktree
creation. No new checkpoint created: the session checkpoint is already
`resolved`/`complete` and must not become a recovery candidate for finished work.

## Next actions for Ship

Claim **148-S** first. Do not claim 149-S or 150-S until their predecessor has
shipped - the dependency edges enforce this and the ready queue already reflects
it.
