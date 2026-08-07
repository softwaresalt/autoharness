---
title: "Crash-Resumption + Prune-on-Restore Protocol (111-F / 119-S)"
feature: 111-F
shipment: 119-S
tasks:
  - 111.001-T
  - 111.002-T
  - 111.003-T
  - 111.004-T
  - 111.005-T
  - 111.006-T
  - 111.007-T
status: implemented
---

# Operator-Confirmed Crash-Resumption + Prune-on-Restore Protocol

## Purpose

Define a fail-closed, owner-exclusive protocol for recovering from an
interrupted (crashed / abandoned) Orchestrator, Stage, or Ship session using
the existing `backlogit` checkpoint substrate, without introducing a new
checkpoint schema field, a new execution engine, or any automatic/heuristic
resume behavior.

## Core contracts

1. **Zero valid candidates → normal startup.** If no active checkpoint owned
   by the relevant role exists, there is nothing to recover. This is
   EXPLICITLY NOT a failure and NOT an operator handoff — it is the expected
   steady state on almost every session start. Enumeration that determines
   this MUST be unfiltered at the API-call level (see point 11 below) so a
   malformed/quarantined checkpoint can never be silently excluded and
   mistaken for a genuine zero-candidate state.
2. **When candidates exist, the operator selects an explicit filename.**
   Never auto-pick, even when exactly one candidate is returned.
3. **Validate CheckpointV1 ownership.** The `agent` field is
   `required,oneof=ship stage`. A missing/empty/mismatched value fails closed
   to operator handoff.
4. **The Orchestrator routes exclusively; it never performs owner work
   directly.** Restore/resume/prune/resolve work for a selected checkpoint is
   routed to the owning agent (Stage for `agent: stage`, Ship for
   `agent: ship`) — the Orchestrator never executes that work itself. This
   preserves P-001 role separation.
5. **Resolve only the selected, owner-matched checkpoint, and only after a
   confirmed successful owner resume.** `resolve_checkpoint` is invoked ONLY
   AFTER the owning agent confirms a successful resume of the selected
   checkpoint — never before, never on ambiguous or torn state. There is no
   bulk or cross-role resolution sweep.
6. **No dead-session auto-recovery.** CheckpointV1 exposes no heartbeat,
   session-lock, or lease field (only `created_at`/`updated_at`), so age alone
   can never prove a prior session dead. The protocol therefore never
   auto-resumes and never hijacks a possibly-live session under any
   condition.
7. **Fail closed on invalid/ambiguous reads — no fresh-start fallback.** An
   invalid, ambiguous, torn, malformed, or unreadable checkpoint read fails
   closed to operator handoff. The prior behavior of silently discarding an
   invalid/ambiguous checkpoint and starting a fresh session has been
   removed entirely. This fail-closed path applies only among *existing*
   candidates — it is never triggered by the zero-candidate case.
8. **Bounded prune-on-restore, engram-pack-gated.** The owner sequence is
   restore → prune/gate → resume, never restore → resume → prune. After the
   checkpoint's `state_dump` is loaded (restore) but BEFORE execution
   resumes, the owning agent applies a bounded read-select-summarize prune
   of superseded action-observation history via the existing engram-bound
   context substrate — but ONLY when the `agent-engram` capability pack is
   installed/active. A backlogit-only installation (no `agent-engram`) is a
   supported, non-degraded no-op: restore proceeds directly to resume with
   no prune/gate step, because there is no engram-bound state to summarize.
   The prune allowlist never drops the active-shipment/active-task cursor,
   the unresolved-checkpoint pointer, or recorded gate verdicts. If
   `agent-engram` IS installed but unreachable during this prune/gate step,
   the protocol fails closed to operator handoff — no prune, no resume
   (resume only ever follows a completed prune/gate step), and no
   file-based-prune degradation fallback (that path was never proven safe
   and is explicitly not used). The engram-not-installed no-op and the
   engram-installed-but-unreachable fail-closed case are deliberately
   distinct: a backlogit-only workspace is never forced into the fail-closed
   path merely for lacking the engram pack.
9. **Single-active preserved.** On confirmed resume, the owning agent picks
   up the same single-active cursor recorded in the checkpoint — no parallel
   resume, no new worktree (P-001/P-016).
10. **Environment/technology agnosticism and existing role boundaries are
    preserved.** No new checkpoint-schema fields, no new runtime/execution
    engine, no provider or binary hardcoding.
11. **Unfiltered enumeration + anomaly-first fail-closed check.** Checkpoint
    enumeration at the API-call level never applies a `status`/`agent`
    filter, because some backlog-tool implementations return a parse-failure
    or schema-invalid checkpoint as a quarantined summary with an empty
    `agent`/`status` — a downstream filter would silently exclude it,
    letting the enumerating agent (Orchestrator, Stage, or Ship) incorrectly
    conclude zero candidates exist while an unresolved malformed checkpoint
    is present. Every enumerated summary is inspected for a validation error,
    quarantine flag, or missing/malformed required field FIRST; any such
    anomaly fails closed to operator handoff immediately. Only after that
    anomaly check finds nothing does the agent partition to the valid,
    owner-matched, active records for the zero-candidate/selection logic in
    points 1–2 above.
12. **`cleanup_checkpoints` sequenced after recovery adjudication.**
    `cleanup_checkpoints` (retention-based archival) can remove still-active
    checkpoints purely for being older than the retention cutoff — the same
    class of record this protocol says must never be excluded by age. It is
    therefore invoked only after every active checkpoint in the enumerated
    population has reached an explicit resolution (via `resolve_checkpoint`
    after a confirmed resume, or an explicit operator handoff decision) —
    never against a checkpoint population that has not yet been enumerated
    and dispositioned by this protocol.

## Where this lives

| Concern | Artifact |
|---|---|
| Orchestrator detection + owner-exclusive routing | `templates/agents/_orchestrator.agent.md.tmpl` → Step 0.0b; installed mirror `.github/agents/_orchestrator.agent.md` |
| Stage owner-scoped recovery (agent: stage) | `templates/agents/_stage.agent.md.tmpl` → Crash-Resumption / Startup Recovery Protocol; installed mirror `.github/agents/_stage.agent.md` |
| Ship owner-scoped recovery (agent: ship) | `templates/agents/_ship.agent.md.tmpl` → Crash-Resumption / Startup Recovery Protocol; installed mirror `.github/agents/_ship.agent.md` |
| Bounded prune-on-restore + degraded engram-unreachable fallback | `templates/instructions/backlogit.instructions.md.tmpl` → Checkpoint-Recovery / Prune-on-Restore Protocol; installed mirror `.github/instructions/backlogit.instructions.md` |
| Install/verify/tune wiring | `.github/skills/install-harness/SKILL.md` (Formal Overlay Contract: `backlogit`), `.github/skills/tune-harness/SKILL.md` (backlogit overlay coherence checks), `src/autoharness/verify_workspace.py` (`PACK_ASSERTIONS["backlogit"]`: `backlogit_checkpoint_recovery_protocol`, `orchestrator_crash_resumption_protocol`, `stage_crash_resumption_protocol`, `ship_crash_resumption_protocol`) |
| Structural tests | `tests/test_crash_resumption_protocol.py` |
| Manifest checksums | `.autoharness/harness-manifest.yaml` (single `checksum` field per artifact — never a dual installed/source split) |

## Scoping decisions made during 119-S execution

* **Installed-mirror sync scope**: at the time of this shipment, all three
  installed dogfood agent mirrors (`.github/agents/_orchestrator.agent.md`,
  `_stage.agent.md`, `_ship.agent.md`) already carried substantial pre-existing
  drift relative to their source templates, unrelated to crash-resumption
  (older/missing Steps such as Deliberation, Plan Hardening Gate,
  sub-epic/task harvest, Pre-Summary Verification Gate, Remote Operator
  Integration, etc.). Performing a full mechanical re-render from the current
  templates would have pulled all of that unrelated pre-existing drift into
  this shipment's diff. Consistent with width-isolation, only the new
  crash-resumption / owner-agent recovery section content (with all
  `{{VARIABLE}}` customization points resolved to this workspace's concrete
  values) was inserted into each installed mirror at the template's
  equivalent structural location. The broader mirror/template drift remains a
  known, pre-existing, out-of-scope gap for a future dedicated tune-harness
  refresh cycle.
* **`.gitattributes` eol=lf pin extended** to
  `.github/instructions/backlogit.instructions.md` (newly installed this
  shipment) to keep its manifest checksum deterministic across Windows/CI
  checkouts, per the established CRLF/LF checksum-computation pattern (see
  `docs/compound/115-S-109-F-checksum-and-branch-ownership-patterns.md`).

## Deferred (living tracker 34D50F2D)

Candidates (a) a unified CLI/MCP action-observation execution abstraction and
(c) a background Verification & Compaction layer remain explicitly DEFERRED.
This protocol introduces no new checkpoint-schema fields and no new runtime
engine, and does not resolve or narrow either deferred candidate.
