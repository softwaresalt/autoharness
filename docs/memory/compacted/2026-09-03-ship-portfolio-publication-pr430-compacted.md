# Compacted: Ship portfolio publication (PR #430) — SHIP-1..SHIP-10

Date: 2026-09-03/04. Verbose original: `docs/archive/memory/2026-09-03-ship-portfolio-publication-pr430.md`.

**Outcome:** PR #430 merged to `main` via merge commit `431527c8` (merge-commit
strategy, two parents). Published 10 shipment manifests (`159-S`..`168-S`),
queued/unclaimed. No shipment executed.

**Key decisions:** Fixed mechanical inconsistencies (EOF whitespace, plan
line-count self-report, disagreeing readiness statements) directly. Verified
one Copilot finding against actual gate/skill source
(`shipment_closure.py`/`shipment-reconcile SKILL.md`) before acting — confirmed
a genuine future `168-S` closure blocker from the archived `160.019-T`'s
retained `parent_id`, corrected the plan's "cosmetic rollup" mischaracterization,
captured `3CA122AC`. Six other out-of-scope findings (pytest/unittest CI-runner
design conflict, manifest dependency-graph modeling gap, checkpoint schema
defects) captured as P-021 deferred entries rather than fixed, since all
required either Stage planning decisions or fresh operator authorization
beyond this session's scope.

**Failed approach / lesson:** PowerShell double-quoted here-strings interpret
backtick as an escape character — a reply body containing `` `archived_status` ``
got corrupted into a BEL character mid-word on first attempt. Fixed by
switching to single-quoted here-strings (`@'...'@`) for all subsequent GitHub
API reply bodies.

**Deferred entries captured this session:** `3CA122AC` (high, 168-S closure
blocker), `2940EA5F` (medium, dependency-graph gap), `F9FA90B1` (high,
pytest/unittest conflict), `445C1DFB` (low, checkpoint missing resume_hint),
`7AD60E4F` (medium, 8 checkpoints with schema-nesting violation). Pre-existing
open: `76EBDE6D`, `0B83AC8F`, `60C207F1`, `99818C6D`.

**Next session:** 168-S not claimable until `76EBDE6D` + `F9FA90B1`
dispositioned by Stage. Execution order: `159-S -> 160-S -> 161-S -> 162-S ->
163-S -> 164-S -> 165-S -> 166-S -> 168-S -> 167-S`. See compound learning
`docs/compound/2026-09-03-copilot-review-surfaces-latent-parent-id-closure-blocker.md`
for the full verified-vs-trusted review methodology writeup.

**Pointers:** PR https://github.com/softwaresalt/autoharness/pull/430, merge
`431527c849b617d675c5d4efc7b44281fcbbbb43`, plan
`docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md`.
