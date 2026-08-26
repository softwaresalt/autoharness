---
title: "Compacted memory — 34D50F2D candidate (a) composability spike + Copilot CLI Supervisor/Control-Plane Plan 1 (117-F/118-F/119-F/120-F, 127-S/128-S/129-S, PR #325)"
doc_type: memory
memory_class: compacted
created: 2026-08-09
scope: release-unit-saga
shipment: [127-S, 128-S, 129-S]
feature: [117-F, 118-F, 119-F, 120-F]
pr: [325]
tracker: 34D50F2D
consolidates:
  - docs/archive/memory/2026-08-09-stage-34d50f2d-candidate-a-composability-spike.md
  - docs/archive/memory/2026-08-09-stage-copilot-supervisor-plan1-fasttrack.md
---

# Compacted: Composability spike → Copilot CLI Supervisor/Control-Plane Plan 1 (2026-08-09 → 2026-08-12)

## Spike — 34D50F2D candidate (a): composability (2026-08-09)

Bounded Stage research spike (read-only, no implementation) on the unified CLI/MCP/library
composability question.

**Headline findings**: (1) the CLI is the **only real surface** — autoharness exposes no MCP
server of its own; the `mcp` tokens present in `src/` are two unrelated non-server
vocabularies (backlog-registry validation codes, 31 occurrences; telemetry `tool_surface`
enum value, 1 occurrence) — not server-framework identifiers. (2) The Python library surface
is nominal (zero external consumers, no `__all__`, no declared public API). (3) **Policy is
leaked into the CLI adapter** (verdict mutation on `--force`, audit-log authorship, the sole
telemetry-event construction site, verify pass/fail definition, a CLI-exclusive `degraded`
gate outcome). (4) Largest genuine duplication is **prose-vs-code**: template-variable
derivation is specified in `install-harness/SKILL.md`'s table and independently
re-implemented in `verify_workspace.py`, with nothing forcing agreement. (5) The core is
already dependency-injected and well tested — the actual gap is that policy sits above the
core, not that the core is untestable. (6) `setup-*` has no core module at all.

**Verdict**: `PARTIAL GAP` / `CONDITIONAL PROCEED` (medium-high confidence), conditioned on
scoping (a) as *consolidation of existing logic*. If the product spec's §3 (an in-process
action/observation execution engine with sequential pipelining and stderr-to-model routing)
was wanted literally, the verdict would be **NO-GO** — that is agent-runtime territory, not
autoharness's. Candidate (c) (from the same `34D50F2D` tracker) benefits from (a) but does
**not** depend on it — kept sequenced, not blocked.

**PR #325 correction cycle (7 findings, research-artifact-only)**: fixed a wrong CLI-command
count ("11 commands" → corrected convention: **10 top-level / 17 executable leaf paths**),
narrowed an overstated MCP-vocabulary claim (disproven by `tool_event.py:35`), repointed a
broken artifact link, repaired an impossible checkpoint `created_at > updated_at` chronology,
and appended a correction to the still-active `34D50F2D` tracker. Core spike conclusion
unchanged.

## Operator product decision — the bright line

The operator issued an authoritative decision reframing the question: autoharness becomes a
**local Copilot CLI supervisor / control-plane runtime** for long-horizon workloads,
preserving Copilot CLI as the reasoning/execution engine.

> **Supervising an external agent runtime is IN SCOPE.
> Implementing a new agent runtime is OUT OF SCOPE.**

The original NO-GO (in-process action/observation engine) was **narrowed, not overturned** —
supervising an external Copilot child process is a categorically different activity, and
matches the spike's "consolidation of existing logic" condition: `start.ps1`/`start.sh`
already perform bootstrap, sidecar preflight, resolution, and launch as an untested,
duplicated two-language supervisor. Two corrections were required for coherence: (1) MCP
parity is **not** recommended — a native MCP server stays an explicit non-goal absent a
concrete consumer; (2) process-supervision scope is **not** wholly rejected — only the
in-process model-reasoning loop, sequential model pipelining, and stderr-to-model routing
remain out of scope. Gradio, devtunnel, remote UI/control/auth/approvals, and browser
terminal streaming are excluded and deferred to a separate **Plan 2**.

## Architecture decided

New package `src/autoharness/supervise/` (`result.py`, `errors.py`, `redact.py`,
`locking.py`, `process.py`/`process_pty.py`, `session.py`, `events.py`, `journal.py`,
`recovery.py`, `bootstrap.py`, `sidecar.py`, `resolve.py`, `approvals.py`, `app.py` with the
sole orchestrator `run_session()`). Sole adapter: `autoharness run` in `cli.py`;
`start.ps1`/`start.sh` become thin compatibility shims with no surviving policy duplication.
Python-first, no Python+Go split (Go reevaluated only if a future persistent multi-workspace
daemon needs it). Session state machine: `INIT → LOCKING → BOOTSTRAPPING → PREFLIGHT →
RESOLVING → LAUNCHING → RUNNING → {CANCELLING | RESTARTING | DRAINING} → {EXITED | FAILED |
REFUSED}` (later extended — see the Cycle 26 ruling below). `REFUSED` (lock contention) is
distinct from `FAILED`; `DRAINING` is the only path from `RUNNING` to a terminal state.
Authority boundaries unchanged: Engram read-only/no-authority; backlogit owns backlog items
and agent checkpoints (the supervisor's own session journal is gitignored local state and is
explicitly **never** a checkpoint); graphtor owns docs.

**Feature/shipment structure**: product umbrella `117-F` ("Local Copilot CLI supervisor /
control-plane runtime") is a **childless** covering feature (see F14 below) containing three
sub-features: `118-F` (S1 — safety contracts + characterization baseline, zero behavior
change, critical/P0) → shipment `127-S`; `119-F` (S2 — supervision core, unwired library,
critical/P0) → shipment `128-S`, `depends_on 127-S`; `120-F` (S3 — application services,
adapters, `start.ps1`/`start.sh` migration, **the only behavior-changing shipment**, high/P1,
also carries `117-F` as its last member) → shipment `129-S`, `depends_on 128-S`. `127-S` is
the sole eligible cursor throughout the saga.

## PR #325 — a ~26-cycle Copilot review-fix saga (2026-08-10 → 2026-08-12)

Far more review cycles ran here than the standard 3-cycle limit, under standing
dark-factory/operator authorization (mirroring the PR #296 pattern in the topology-gate saga).
Representative, non-exhaustive waypoints (each was a genuinely new, valid structural finding,
not a repeat):

* **F14 — childless-umbrella structural fix**: an earlier cycle-2 "fix" required Ship to
  re-adopt orphaned tasks via `backlogit_adopt_item` after each predecessor shipment closed —
  **rejected on reopening (F14-R)** because it was operationally invalid (not in Ship's role,
  and unenforceable). Eliminated structurally instead: `117-F` became a childless umbrella
  whose 19 tasks live under three new root covering features (`118-F`/`119-F`/`120-F`), so no
  shipment close ever needs to walk through `117-F` to reach live children.
* **Cascade-hazard catch**: an interim shipment `124-S` listed covering feature `117-F`
  directly in its manifest alongside 5 unrelated items — closing it would have marked `117-F`
  **done and archived it** while 14 of its 19 descendant tasks were still open. Caught and
  corrected before merge: `117-F` removed from that manifest; the only safe place for it is as
  the **last** member of the **final** shipment (`129-S`), once genuinely childless.
* **F19/F20 — circular ordering and an authority-boundary contradiction**, each independently
  gating `128-S`/`129-S`; both fixed without touching the F14 structural elimination or the
  three-shipment chain.
* **F24/F25 — "capabilities nobody has to make real"**: `119.005-T` referenced a gitignore
  template that did not exist anywhere in `templates/`; `120.006-T` (the only CLI-touching
  task) never specified which flags `autoharness run` accepts, even though two *other* tasks
  independently introduced flags (`--force-unlock`, `--max-restarts`/resume) that had nowhere
  documented. Individually arguable, **jointly severe** — this pairing pattern (a lockout trap
  paired with a removed, undocumented escape hatch) recurred and is explicitly called out as
  worth watching for.
* **Cycle 17 — a recorded PASS was falsified by its own confirmatory review**: Stage recorded
  a PASS, then ran the required confirmatory review of the same commit — which returned 4 new
  P1s and falsified the just-recorded PASS. Per standing operator instruction, Stage **halted,
  fixed nothing, and withdrew the PASS** rather than patching around it. Three of the four
  findings survived further scrutiny (`F30`, `F31`, `F32`/`F33`).
* **P1-D — checkpoint corruption root cause**: a checkpoint was created by applying `resolve`
  to a **raw state dump with no CheckpointV1 envelope**, so missing fields silently normalized
  to `schema_version: 0` and a zero timestamp. Repaired to a valid envelope preserving state
  verbatim; the durable fix is **"write the envelope at create time,"** not just repairing
  after the fact — the same class of checkpoint-lifecycle discipline established independently
  in the topology-gate saga (never hand-amend; here, never resolve an unenveloped dump).
* **Cycle 21–23 — a three-part escalating lesson set** (verbatim-preserved, high value):
  1. *(Cycle 21, engine-identity pinning)* recording a change is only half the work — the
     other half is sweeping every surface that predicates on the old value.
  2. *(Cycle 22, P1-2)* **"choosing not to raise an observation does not license asserting its
     negation."** Noticing a fact and judging it out of scope is defensible; simultaneously
     letting an unrelated claim stand that the very observation falsifies is not.
  3. *(Cycle 23, P1-3)* an acceptance criterion that **consumes** an artifact is not
     self-satisfying — something must be **obliged to produce it**. "Declared once in
     `contracts.py`" named a location, not an owner.
  General form (stated explicitly in the source): **"a claim is only as good as the surface
  that is obliged to make it true. Location ≠ ownership; observation ≠ assertion; a recorded
  fact ≠ its dependents."**
* **Cycle 26 — operator ruling: `CANCELLED` is a distinct fourth terminal state.** The
  cancellation terminal state had been defined three incompatible ways across the plan diagram,
  the plan outcome table, and two different task/feature bodies (some ending cancellation in
  `EXITED`, others in a dedicated `CANCELLED`). Stage verified the contradiction but declined to
  resolve it unilaterally — **choosing a terminal state is a product decision**. Operator
  ruled: terminal set is exactly `{EXITED, FAILED, REFUSED, CANCELLED}`; cancellation flows
  `<post-LOCKING phase> → CANCELLING → DRAINING → CANCELLED`, entering `CANCELLED` only after
  child termination, journal flush, and lock release **complete**; there is no direct
  `CANCELLING → CANCELLED` edge (raises `ILLEGAL_TRANSITION`, mirroring the existing
  `CANCELLING → EXITED` prohibition). Rationale: collapsing cancellation into `EXITED` would
  make a deliberately operator-cancelled session indistinguishable from a normal completion in
  the state itself — the same reasoning already accepted for `REFUSED` vs `FAILED`. Acceptance
  tests were strengthened (not just wording): cancellation and normal-completion runs must
  assert **different** terminal values; a negative control asserts the direct `CANCELLING →
  CANCELLED` transition is absent; the existing graph-property test now covers `CANCELLED` on
  equal footing with every other terminal. **Lesson (verbatim):** *"A contradiction can hide
  behind three surfaces that are each internally coherent"* — the plan diagram, the
  transition-table task, and the recovery task each read as self-consistent in isolation; only
  reading them **against each other** exposed that no two agreed on where cancellation ends.
  The durable fix is the paired differing-value assertion, not just corrected wording.

## Final authoritative state (end of saga)

Verifier 221/221 and simulation 66/66 green against the live engine; 30 task-level `blocks`
edges (a closed, verifier-enforced set); shipment memberships 8/7/10 (`127-S`/`128-S`/`129-S`);
chain `127-S → 128-S → 129-S` intact; checkpoints ~29–30 with 0 malformed/quarantined/active;
CI passing; P-018 satisfied at the reviewed HEAD. `127-S` remains the sole structurally
eligible cursor — explicitly noted as **"eligibility is not clearance"**: no shipment was
claimed or closed, nothing merged, no product code touched by Stage at any point in this saga.

## Cross-cutting learnings (this saga — high value, must not be dropped)

1. **A childless umbrella feature, listed only as the last member of the final shipment in a
   serial chain, is the safe pattern for a "grouping that must not gain lifecycle authority"**
   — nesting sub-features under a covering parent looks natural but creates a cascade hazard
   where an early shipment close can orphan or prematurely archive the parent.
2. **"Choosing not to raise an observation does not license asserting its negation"** — a
   general discipline for any compression/summarization step: an out-of-scope fact that
   contradicts a stated claim means the claim must be weakened, not silently left standing.
3. **A claim is only as good as the surface obligated to make it true** — location (e.g. "this
   is declared once, here") is not the same as ownership (something must actually be required
   to produce/enforce it).
4. **A recorded PASS must survive its own confirmatory re-review, or be withdrawn outright** —
   patching around a falsified PASS rather than withdrawing it was explicitly rejected by
   standing operator policy.
5. **Checkpoint envelopes must be written at creation time, not repaired after the fact** —
   applying `resolve` to a raw, unenveloped state dump silently normalizes missing fields to
   invalid defaults (`schema_version: 0`, zero timestamp). Same family of lesson as the
   topology-gate saga's "never hand-amend a checkpoint," applied to a different corruption
   vector (creation-time, not amendment-time).
6. **A contradiction can hide behind three individually self-consistent surfaces** — only
   cross-reading plan/task/feature documents against each other (not reviewing each in
   isolation) surfaces genuine disagreement; the durable fix is a differing-value assertion
   test, not corrected prose.
7. **Individually arguable findings can compound into joint severity** — a lockout trap and an
   undocumented escape hatch, each defensible alone, become a real hazard together (F24/F25).

## Outcome

Spike `34D50F2D` candidate (a) consumed by the harvested Plan 1 work; candidate (c) remains
deferred on the same tracker, sequenced-but-not-blocked. Plan 1 (feature `117-F` + sub-features
`118-F`/`119-F`/`120-F`, shipments `127-S`/`128-S`/`129-S`) fully planned, hardened (P-006,
H1–H10), and reviewed to PASS after an extended (~26-cycle) Copilot review saga on PR #325, all
under standing operator authorization to continue past the normal 3-cycle limit. No shipment
claimed, no product code touched, no merge performed by Stage — `127-S` is the handoff token to
Ship, gate-clear but explicitly not yet "clearance" in the sense of an executed claim.
