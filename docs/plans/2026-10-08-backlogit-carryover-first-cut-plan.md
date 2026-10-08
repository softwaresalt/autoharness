---
title: "backlogit requirements carryover — first release cut (P1 + P3 + FB6F9FE0 + P7)"
date: 2026-10-08
created_at: 2026-10-08T21:10:00Z
status: reviewed
source_stash: [50DCCBED, 8675D546, FB6F9FE0, 38DCC612, F2D11D61]
source_doc: docs/design-docs/2026-10-07-autoharness-requirements-carryover.md
predecessor_shipment: 208-S
---

# backlogit requirements carryover — first release cut

## Source and Triage Record

Canonical source: `docs/design-docs/2026-10-07-autoharness-requirements-carryover.md`
(committed; paired stash entry F2D11D61 — its "local scratch, not committed" note in
the derived entries is superseded). Release-cut guidance in that doc: cut P1 + P3 + P7
first, R1 in a follow-up release.

| Stash | Row | Kind | Disposition this session |
|---|---|---|---|
| 50DCCBED | P1 gate-aware eligibility | task | **This cut** — Feature A (operator-approved first) |
| 8675D546 | P3 dark-mode activation preflight | task | **This cut** — Feature A (operator-approved first) |
| FB6F9FE0 | stash-referenced companion-doc carry-forward | feature | **This cut** — Feature B (see rationale below) |
| 38DCC612 | P7 UTC mandatory + lint | feature | **This cut** — Feature C |
| F2D11D61 | pairing entry (canonical doc) | task | Consumed as source; triage of the eight derived rows recorded here |
| FD5BE5EA | P2 closure conditions as backlog items | — | Not first cut per doc; left in stash |
| E9595107 | P4 session-start READY_WITH_CONDITIONS surfacing | — | Not first cut per doc; left in stash |
| 3E1939FD | P5 Stage Step 5.5 predecessor-condition check | — | Not first cut per doc; left in stash |
| 9DC3BFCF | P6 closure-condition fields + lint | — | Not first cut per doc; left in stash |
| 21F8C04A | R1 external scheduler marker consumption | — | Excluded (separate Stage invocation; follow-up release) |

No entry carries the `DEFERRED SCOPE EXPANSION` marker, so P-021 C6 forced
deliberation does not apply. Overlap with 34AAF1C7, 808BAB5E, 3B67029C, 2940EA5F,
C327A8DE was checked at capture (none duplicates); a backlog search for gate-aware
eligibility / stash-referenced carry-forward found no existing item. 059-F (done)
introduced the output-timestamp instruction that Feature C extends.

**Routing**: no deliberation. P1/P3 are operator-approved and precisely specified;
FB6F9FE0 lists its open design questions explicitly as "design constraints to plan",
which this plan resolves under Decisions and Rationale.

**FB6F9FE0 inclusion rationale**: P1 makes the Orchestrator run the `pre_claim` gate
for every DAG-ready candidate at session start. `worktree_cleanliness` is a
workspace-global check, so a single uncommitted stash companion document (the exact
F2D11D61 situation) would report EVERY candidate ineligible as `WORKTREE_DIRTY`. P1's
eligibility report is therefore only truthful once FB6F9FE0 lands. Same release,
separate feature/shipment (it changes CLI gate code + P-011 + Ship/Stage, a different
width than the Orchestrator-template work).

**Grouping and shipment order** (one feature per shipment, chained with `blocks`):

`208-S` → **A** (P1 + P3, Orchestrator) → **B** (FB6F9FE0, gate + P-011) → **C** (P7, UTC)

A runs first because P1/P3 are the operator-approved-first rows. B follows because it
closes the global false-`WORKTREE_DIRTY` gap that A's eligibility report surfaces. C
has no file overlap with A or B and closes the cut.

## Problem Frame

1. **P1**: Orchestrator Step 0 (`templates/agents/_orchestrator.agent.md.tmpl`, State
   Assessment) lists queued shipments but only runs `pipeline-topology --phase pre_claim`
   for the single chosen candidate in Step 2a. A DAG-ready candidate whose predecessor
   closed `READY_WITH_CONDITIONS` with an unsatisfied condition is reported as ready and
   only halts later (`PREDECESSOR_CLOSURE_INCOMPLETE`, the backlogit 153-S halt).
2. **P3**: The Dark Factory Mode Trigger Semantics section records `DARK_MODE_ACTIVE`
   before any gate runs, so a dark run can be activated on a gate-blocked scope head and
   halt immediately after activation. `templates/prompts/feature-flow-dark.prompt.md.tmpl`
   step 1 mirrors this ordering.
3. **FB6F9FE0**: `src/autoharness/gates/topology.py::_worktree_cleanliness_check` accepts
   only paths under `carry_forward_prefixes()` (`f"{backlog_dir.name}/"` from
   `resolve_backlog_root`). Any uncommitted companion document referenced by a stash entry
   blocks `pre_claim` as `WORKTREE_DIRTY`, and Ship's carry-forward commit (Ship step
   "Carry-forward commit") cannot carry it.
4. **P7**: `templates/instructions/output-timestamps.instructions.md.tmpl` requires UTC
   only for output stamps. Memory folder names (`copilot-instructions.md.tmpl` line ~86
   `{{DOCS_MEMORY}}/{YYYY-MM-DD}/`), compact-context filenames, frontmatter dates,
   comments, and logs have no UTC rule, and no check prevents local-offset times.

## Requirements Trace

| Requirement | Units |
|---|---|
| P1: per-candidate `pre_claim` in Step 0; gate-blocked → ineligible with token | A1, A4 |
| P1 acceptance: unsatisfied `READY_WITH_CONDITIONS` predecessor → ineligible, not DAG-ready | A1, A4 |
| P3: gate scope head before recording `DARK_MODE_ACTIVE`; later in-scope waits `PENDING`; external blockers surfaced | A2, A3, A4 |
| P3 acceptance: gate-blocked scope head halts before `DARK_MODE_ACTIVE` is recorded | A2, A3, A4 |
| FB6F9FE0: stash-referenced uncommitted doc is carry-forward eligible (exact path, contained) | B1, B2, B3 |
| FB6F9FE0: prefixes and stash lookup derive from resolved backlog root (override/default/legacy/both-roots) | B1, B2 |
| FB6F9FE0: report `stash_referenced_paths` in details | B1, B2, B4 |
| FB6F9FE0: P-011, Ship carry-forward (claim + mid-cycle intake), Stage commit guidance | B5, B6, B7 |
| FB6F9FE0: intake only — no triage, no shipment-scope change (P-021) | B5, B6, B7 |
| P7: UTC mandatory for all recorded dates/times | C1, C2, C3 |
| P7: lint check; acceptance no local-offset times, date folders use UTC date | C4 |

## Implementation Units

Every template unit edits `templates/...` AND its dogfood mirror under `.github/...`,
then refreshes the mirror's checksum in `.autoharness/harness-manifest.yaml`. Every unit's
verification gate is the canonical suite: `PYTHONPATH=src python -m unittest discover -s tests`
(not pytest), run by Ship.

### Feature A — Gate-aware eligibility and dark-mode activation preflight (P1 + P3)

**A1 — Orchestrator Step 0 gate-aware eligibility (P1)** — size M, complexity medium,
posture: characterization-first (read Step 0 / Step 2 / Step 2a / Step 3 cursor text).
Files: `templates/agents/_orchestrator.agent.md.tmpl`, `.github/agents/_orchestrator.agent.md`, manifest.
* Add a Step 0 sub-step after "queued shipments": for each DAG-ready candidate (same
  dependency/queue-order source Step 2 uses), run
  `autoharness gate pipeline-topology --mode agent --shipment {id} --phase pre_claim --json`
  — **never** with `--bootstrap-grant-invocation` or `--force` (Step 2a stays the ONLY
  grant-consumption site).
* Classify: exit 0 → `ELIGIBLE`; exit 1/2 → `INELIGIBLE: {token}` (gate token + message
  verbatim); blocked AND `.autoharness/bootstrap-grants/{id}.yaml` present →
  `INELIGIBLE: {token} (bootstrap grant present — evaluated only at Step 2a)`.
* Report workspace-global blockers (`worktree_cleanliness`, `worktree_topology`,
  `branch_ownership`) ONCE as `GLOBAL_GATE_BLOCK: {token}` rather than repeating them per
  candidate (learning: 2026-08-16 multiple-worktrees-blocks-gate-globally).
* Extend the `ORCHESTRATOR STATE` block with `Eligible shipments` / `Gate-blocked
  shipments: {id: token}`; Step 2 first-pass candidate selection skips gate-blocked
  candidates (Step 2a re-check still runs; this is advisory pre-filtering, not a substitute).
* Gate-not-installed bootstrap exemption mirrors Step 2a (skip, log `ELIGIBILITY_GATE_SKIPPED`).
* Read-only: no claim, no grant consumption, no branch switch.

**A2 — Orchestrator dark-mode activation preflight (P3)** — size S, complexity medium,
depends on A1 (same file). Files: same as A1.
* In Dark Factory Mode Trigger Semantics: after resolving `scope` and BEFORE recording
  `DARK_MODE_ACTIVE`, run the A1 probe on the **scope head** (first in-scope shipment in
  dependency/queue order).
* Head blocked → halt with `DARK_MODE_PREFLIGHT_BLOCKED: {id} {token}`; do NOT record
  `DARK_MODE_ACTIVE`; surface to operator.
* Later in-scope shipments whose only block is an in-scope predecessor (sequencing wait)
  → report `PENDING`, not blocked.
* Later in-scope shipments blocked by anything outside the scope (out-of-scope
  predecessor, unattested closure condition, external dependency) → list as
  `EXTERNAL_BLOCKER: {id} {token}` in the activation record (new optional field
  `preflight`), surfaced at activation; activation may proceed when the head is eligible.
* Stash-only scope (no shipment yet) → `preflight: not_applicable (no shipment in scope)`.

**A3 — feature-flow-dark prompt preflight (P3)** — size XS, complexity low, depends on A2.
Files: `templates/prompts/feature-flow-dark.prompt.md.tmpl`, `.github/prompts/feature-flow-dark.prompt.md`, manifest.
* Step 1 becomes: activate only through the Orchestrator, which preflights the scope head
  and records `DARK_MODE_ACTIVE` only on a passing head; cite the A2 tokens.

**A4 — Contract test for P1/P3 text** — size S, complexity low, depends on A1–A3.
File: `tests/test_orchestrator_gate_aware_eligibility_contract.py` (new).
* Assert, in template AND installed mirror: Step 0 per-candidate `--phase pre_claim`
  probe without `--bootstrap-grant-invocation`; `INELIGIBLE` + token reporting;
  `GLOBAL_GATE_BLOCK`; preflight ordering (probe text precedes the "record
  `DARK_MODE_ACTIVE`" instruction); `DARK_MODE_PREFLIGHT_BLOCKED`, `PENDING`,
  `EXTERNAL_BLOCKER`; prompt cites preflight. ≤4 scenarios.

### Feature B — Stash-referenced companion-document carry-forward (FB6F9FE0)

**B1 — Gate: stash-referenced carry-forward classification** — size M, complexity medium,
posture: test-first with B2 fixtures in mind. File: `src/autoharness/gates/topology.py`.
* New reader method `stash_referenced_paths(candidates)` on the default readers (optional
  protocol member, `getattr` fallback → empty, same pattern as `carry_forward_prefixes`).
  Reads the working-copy `{backlog_dir}/stash.jsonl` where `backlog_dir` comes from the
  existing `resolve_backlog_root` binding (override → `.backlog/` → `.backlogit/`;
  both-roots-present already raises `BacklogUnavailableError` → existing fail-closed path).
* Matching is **membership only**: a dirty path qualifies iff the exact repo-relative
  string occurs as a whole token in the `text` of an active stash entry (token boundaries:
  whitespace, backticks, quotes, parentheses, trailing `.,;:`). No glob, no prefix, no
  directory widening.
* Containment (each must pass): repo-relative, no `..` segment, no leading `/` or drive,
  not under `.git/`, `Path(workspace, p).resolve()` is inside `workspace.resolve()`, and
  neither the file nor any parent within the workspace is a symlink.
* Qualifying set (decision D2): only **new** files (untracked `??` or staged-added) under
  `docs/`. Modified tracked files never qualify.
* Unreadable/malformed `stash.jsonl` (or a malformed line) → no paths qualify from that
  input (fail closed: the doc stays blocking) and `details.stash_reference_warning` names
  the reason.
* `_worktree_cleanliness_check`: qualifying paths join `carry_forward_paths`; existing
  divergent-staged-content and status-unavailable rules apply to them unchanged;
  `details.stash_referenced_paths` lists them; message wording becomes "only backlog state
  and stash-referenced documents are uncommitted".

**B2 — Tests: backlog-root resolution and reporting** — size S, complexity low, depends on B1.
File: `tests/test_gates_topology.py`.
* Scenarios: `BACKLOGIT_WORKSPACE_DIR` override; default `.backlog/`; legacy `.backlogit/`;
  both-roots-present fails closed. Each asserts prefixes AND the stash lookup location
  derive from the resolved root, and `details.stash_referenced_paths` content.

**B3 — Tests: exact-match, containment, fail-closed** — size S, complexity medium, depends on B1.
File: `tests/test_gates_topology.py`.
* Scenarios: (1) prefix/glob-like near-miss paths stay blocking; (2) traversal, `.git/`,
  outside-root and symlink paths stay blocking; (3) modified tracked doc and non-`docs/`
  file stay blocking; (4) malformed stash + divergent staged doc → `WORKTREE_DIRTY` with
  warning.

**B4 — Gate documentation** — size XS, complexity trivial, depends on B1.
File: `docs/pipeline-topology-gate.md` — document `stash_referenced_paths`,
`stash_reference_warning`, qualifying rules (D2), containment, and the intake-only rule.

**B5 — P-011 policy text** — size S, complexity low, depends on B1.
Files: `templates/policies/workflow-policies.md.tmpl`, `.github/policies/workflow-policies.md`, manifest.
* P-011 carry-forward set = backlog state + stash-referenced new `docs/` documents;
  intake-only (no triage, no scope change; P-021 triage stays with Stage). **Shared with
  208-S** (P-018 text in the same file) — rebase onto merged 208-S; touch only P-011.

**B6 — Ship carry-forward and mid-cycle intake** — size M, complexity medium, depends on B5.
Files: `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`, manifest.
* Carry-forward commit consumes `details.carry_forward_paths` (now including
  stash-referenced docs); the porcelain fallback also admits a path only when it appears in
  `details.stash_referenced_paths` (fallback with the check absent keeps the
  `{{BACKLOG_DIRECTORY}}/`-only rule — fail closed).
* Mid-cycle intake: new stash entries + their referenced docs appearing on the active
  shipment branch are committed as an isolated `chore(backlog): carry forward stash intake`
  commit; never a dedicated branch/PR; never triaged or added to scope. **Shared with 208-S**
  (Ship step 7c) — touch only the carry-forward step and the intake note.

**B7 — Stage commit guidance** — size S, complexity low, depends on B5.
Files: `templates/agents/_stage.agent.md.tmpl`, `.github/agents/_stage.agent.md`, manifest.
* When Stage commits stash entries, it commits each entry's referenced companion documents
  in the same commit; archived entries keep their doc references.

### Feature C — UTC mandatory for recorded dates and times (P7)

**C1 — Output-timestamp instruction: UTC everywhere** — size S, complexity low.
Files: `templates/instructions/output-timestamps.instructions.md.tmpl`, `.github/instructions/output-timestamps.instructions.md`, manifest.
* Scope the rule to ALL recorded dates/times: date-named folders and filenames (UTC date),
  frontmatter `date`/`created_at`, comments, logs, output stamps. Times use `Z`; derive from
  UTC sources (`date -u`, `[DateTime]::UtcNow`/`Get-Date -AsUTC`, `datetime.now(timezone.utc)`).
  Local-offset values are forbidden; convert tool output that reports local offsets.

**C2 — Foundation templates** — size S, complexity low, depends on C1.
Files: `templates/foundation/copilot-instructions.md.tmpl`, `templates/foundation/AGENTS.md.tmpl`
(+ installed mirrors `.github/copilot-instructions.md`, `AGENTS.md` where dogfooded), manifest.
* Memory file convention states `{YYYY-MM-DD}` is the UTC date; one-line UTC rule with a
  pointer to the output-timestamps instruction.

**C3 — compact-context skill** — size XS, complexity trivial, depends on C1.
Files: `templates/skills/compact-context/SKILL.md.tmpl`, `.github/skills/compact-context/SKILL.md`, manifest.
* `{YYYY-MM-DD}` in compacted/decided-plan/closure filenames is the UTC date.

**C4 — UTC lint check** — size S, complexity medium, depends on C1–C3.
File: `tests/test_utc_timestamp_contract.py` (new).
* (1) Scan `templates/**` and installed mirrors for ISO-8601 date-time literals carrying a
  numeric offset (`T\d{2}:\d{2}(:\d{2})?(\.\d+)?[+-]\d{2}:?\d{2}`) — fail with file:line.
  (2) Assert the four P7 targets (and mirrors) carry the UTC rule. ≤4 scenarios. If (1)
  finds pre-existing violations, fix them in this unit only when ≤3 files; otherwise stop
  and stash a follow-up (no allowlist widening).

## Dependency Graph

```text
208-S ──blocks──▶ Shipment A: A1 → A2 → A3 → A4
Shipment A ──blocks──▶ Shipment B: B1 → {B2, B3, B4, B5}; B5 → {B6, B7}
Shipment B ──blocks──▶ Shipment C: C1 → {C2, C3} → C4
```

## Decisions and Rationale

* **D1 — Step 0 probe is advisory pre-filtering**: Step 2a remains the binding pre-claim
  gate and the only bootstrap-grant consumption site; the probe never consumes grants.
* **D2 — Qualifying companion docs = new files under `docs/` only**: matches the operator
  intent (requirements docs pulled in as-is) with the smallest widening of P-011.
  Modified tracked files are edits, not intake, and stay blocking (fail closed). Widening
  to other roots is a future stash decision.
* **D3 — Exact-token membership, not path extraction**: the gate never synthesizes paths
  from stash text; it only tests whether each dirty path appears verbatim, which removes
  glob/prefix ambiguity.
* **D4 — P7 lint is a repo contract test**, run by the canonical unittest gate; a
  consumer-side `verify-workspace` lint over generated artifacts is out of scope for this
  cut (existing artifacts may carry offsets; would need a migration decision).
* **D5 — Three shipments**: different widths (Orchestrator template / CLI gate + policy /
  UTC templates) and reviewable PR size; order per the triage record.

## Risks and Caveats

* **Shared files with 208-S** (`templates/agents/_ship.agent.md.tmpl`,
  `templates/policies/workflow-policies.md.tmpl`, their `.github/` mirrors, and
  `.autoharness/harness-manifest.yaml`): shipment B is sequenced after 208-S and must
  rebase onto merged 208-S; B5/B6 touch only P-011 and the carry-forward step.
* `.autoharness/harness-manifest.yaml` checksums are touched by every template unit;
  serial execution within a shipment avoids conflicts.
* A1's probe count scales with DAG-ready candidates; global blockers are reported once.
* B1 symlink checks must not follow links during containment evaluation.
* C4 may surface pre-existing offset literals (bounded remediation rule above).

## Plan Hardening Signals (REQUIRED)

* public API, schema, or contract change — **present**: new gate `details` keys and a
  widened `CARRY_FORWARD_ELIGIBLE` contract; P-011 policy change.
* security, auth, permission, or compliance-sensitive behavior — **present**: path
  containment / symlink escape in B1.
* migration, backfill, destructive data/config action, or irreversible step — absent.
* external integration, operator checkpoint, or external dependency — **present**: dark
  activation operator checkpoint (A2); backlogit consumption of the release.
* high runtime, rollout, or rollback risk — **present (moderate)**: gate behaviour affects
  every Ship claim.

Requires plan hardening: yes

## Runtime Verification and Closure

* A1–A3: agent-instruction surfaces only; verification = A4 contract test + dogfood parity.
* B1: CLI runtime surface (`autoharness gate pipeline-topology`). Verify with B2/B3 plus a
  manual `--phase pre_claim --json` run in a scratch repo with an untracked stash-referenced
  `docs/` file → `CARRY_FORWARD_ELIGIBLE` with `stash_referenced_paths`.
* C1–C4: instruction surfaces; verification = C4.
* Closure: post-merge, release note lists P1/P3/P7/FB6F9FE0; backlogit follow-up per the
  source doc ("backlogit follow-up after autoharness release").

## Plan Hardening

Hardening required: yes (contract, security, operator-checkpoint, rollout signals).

Learnings and instructions consulted: `docs/compound/2026-08-16-multiple-implementation-worktrees-blocks-topology-gate-globally.md`
(global gate blockers → A1 `GLOBAL_GATE_BLOCK`); Ship carry-forward step text (literal
pathspecs, byte-exact verification); Orchestrator Step 2a bootstrap-grant rules.

Protected invariants:
1. Step 2a is the ONLY bootstrap-grant consumption site (A1/A2 never pass the flag).
2. Fail-closed `worktree_cleanliness` rules (divergent staged content, status unavailable,
   not-top-level, both-roots-present) are unchanged for all paths including stash-referenced ones.
3. Carry-forward is intake only: no triage, no shipment scope change (P-021 C5/C6 untouched).
4. Carry-forward prefixes and stash lookup derive from `resolve_backlog_root`; no hardcoded `.backlogit/`.
5. Dogfood parity: every template edit is mirrored and checksummed.

| ProposedAction | ActionRisk | Approval | Verification / rollback |
|---|---|---|---|
| Widen `CARRY_FORWARD_ELIGIBLE` to stash-referenced docs (B1) | medium | plan-review | B2/B3 containment + fail-closed tests; rollback = revert B1 (prefix-only behaviour returns) |
| Run `pre_claim` per candidate at Step 0 (A1) | low | plan-review | A4 asserts no grant flag; rollback = revert template |
| Gate dark activation on head preflight (A2) | low | plan-review | A4 ordering assertion; rollback = revert template |
| Ship mid-cycle stash intake commit (B6) | medium | plan-review | literal pathspecs + byte-exact `git show` check reused; rollback = revert template |

Blocked-path handling: B1 any containment failure → path stays blocking (no partial carry);
A2 head blocked → no `DARK_MODE_ACTIVE` record. Monitoring signal: `WORKTREE_DIRTY` halts
citing a `docs/` path referenced by stash should disappear after B ships. Owner: Ship per
shipment; validation window: first two Ship claims after B merges.

Review-gate capability risk: no reviewer subagent dispatch tool is exposed in this Stage
session → plan review must record `dispatch_mode: single-agent-declared-degradation` and
cover every selected persona inline. No unresolved operator decisions block execution.

## Plan Review

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`
`TOOL_DEGRADED: model-specific-review-routing — declared fallback: same-model rubric pass`
Personas covered inline (all selected): Constitution Reviewer, Python Reviewer, Scope
Boundary Auditor, Learnings Researcher, Architecture Strategist, Security Lens Reviewer
(triggered by B1 path containment). Agent-Native Parity Reviewer not triggered (no MCP
tool surface change).

Findings (P0–P3), remediated in-plan during this review cycle (cycle 1 of 3):

* **P2 (Security Lens)** — B1 initially admitted any non-source path; narrowed to new
  files under `docs/` (D2) with explicit symlink/traversal/`.git/` rejection. Resolved.
* **P2 (Architecture)** — A1 per-candidate probing would repeat workspace-global blocks
  for every candidate; added `GLOBAL_GATE_BLOCK` once-only reporting. Resolved.
* **P2 (Constitution / P-001, P-014)** — A1 must not become a second bootstrap-grant
  consumption site; D1 + invariant 1 + A4 assertion added. Resolved.
* **P2 (Scope Boundary)** — B6 mid-cycle intake could be read as Ship triaging new
  entries; intake-only wording + invariant 3 added. Resolved.
* **P3 (Python)** — B1 should keep the optional-reader `getattr` pattern so fake readers
  in existing tests stay valid. Recorded in B1.
* **P3 (Learnings)** — 2026-08-16 worktree learning applied (A1). No conflicting prior
  solution found for stash-referenced docs.
* **P3 (Scope Boundary)** — C4 pre-existing-violation handling bounded (≤3 files, else
  stash follow-up). Recorded.
* **P3 (Architecture)** — shared-file overlap with 208-S (Ship template, workflow policies,
  manifest) documented; shipment B sequenced after 208-S.

No P0/P1 findings. Every unit satisfies the 2-hour rule and width isolation (template
units are single-family + mirror + checksum; code and tests are separate units).

dispatch_mode: single-agent-declared-degradation
decision: PASS
