---
title: Compacted memory — Early release batch (093-S/088-F, 094-S/089-F, 095-S/090-F, 096-S/091-F, 098-S/093-F)
doc_type: memory
memory_class: compacted
created: 2026-07-26
scope: release-unit-batch
shipment: [093-S, 094-S, 095-S, 096-S, 098-S]
feature: [088-F, 089-F, 090-F, 091-F, 093-F]
consolidates:
  - docs/archive/memory/ship-093-s-merge-closure.md            # from docs/memory/2026-07-26/
  - docs/archive/memory/stage-088-f-review-followup-hardening.md  # from docs/memory/2026-07-26/
  - docs/archive/memory/ship-095-s-merge-closure.md            # from docs/memory/2026-07-27/
  - docs/archive/memory/stage-multi-model-adversarial-review-routing.md  # from docs/memory/2026-07-27/
  - docs/archive/memory/circuit-break-copilot-review-cycle.md  # from docs/memory/2026-07-28/
  - docs/archive/memory/stage-098-S-088-failure-content-decline-hardening.md  # from docs/memory/2026-07-28/
---

# Compacted: Early release batch (2026-07-26 → 2026-07-28)

Dense consolidation of six Stage/Ship session notes spanning five release units, all
originally filed under the now-removed `docs/memory/2026-07-26/`, `2026-07-27/`, and
`2026-07-28/` date subdirectories. Read `docs/archive/memory/<filename>` for full verbatim
originals.

## 093-S / 088-F — merge + post-merge closure (PR #229)

Merged the throwaway flag-gated Copilot CLI output-compression experiment (merge commit
`e5470bef`, 2 parents, P-009 satisfied). All CI green; 58/58 review threads resolved; final
2 residual hard-blocker findings escalated via reply+resolve rather than a forbidden third
push (operator's bounded-convergence push-cap protocol). `READY_WITH_FOLLOWUPS`.

**Failed approach / process deviation**: Ship ran `backlogit shipment ship 093-S` — the
**forbidden cascade command** per P-015 (single-artifact safe-close should have been used
instead). It happened to be safe only because 093-S's manifest was exactly 088-F's complete
task set (no siblings to protect); verified after the fact via `backlogit doctor` — no
corruption occurred. Recorded as a compound learning (`093-S-review-loop-convergence.md`) and
in the closure doc: **do not treat this as license to use the cascade command generally.**

Residual follow-ups reported to Orchestrator→Stage (not created as backlog items — Role
Boundary): `workspace.py:152` non-string `cwd` fail-safe gap; `benchmark.py:215`
`capture_failed`/provenance dropped on early decline.

## 094-S / 089-F — 088-F review-followup hardening (Stage)

Dark-factory Stage session scoped to exactly the two stash entries above (`A351DB70`,
`C2F7BB15`); no other stash touched. Plan reviewed inline (PASS after descoping an optional
end-to-end test to stay within the 2-Hour Rule; plan-harden skipped — low blast radius).
Harvested feature `089-F` + tasks `089.001-T` (resolver fail-safe) and `089.002-T` (benchmark
provenance hardening); shipment `094-S` created **task-only** (covering feature `089-F`
protected, not a manifest item — 092-S/093-S precedent). Both stash entries archived.

## 095-S / 090-F — merge + post-merge closure (PR #235)

Merged PR #235 (8 file-disjoint TDD tasks, telemetry hardening) with attended operator
approval (merge commit `c6d712b2`, 2 parents). **5 rounds** of Copilot P-018 remediation, each
a genuinely new valid finding on newly-introduced code (no "accept as backlog" option under
P-018): zero-valued-metric quality skip + tz-naive timestamp rejection → additive
`derived_quality` provenance map → fail-closed `_normalize_quality` (fixed an unhashable
`_QUALITY_RANK` crash) → backward-compatible additive fields → same normalization applied to
the report's second quality-computation site. See `docs/compound/095-S-derived-metric-provenance-additive-map.md`.

Post-merge used the **correct single-artifact safe-close** this time (never `shipment ship`):
archived the 8 tasks + shipment record individually; preserved feature `090-F` in queue.

**Failed approach / gotcha (important, recurring risk)**: `backlogit move 090-F --status
done` on the **protected feature** silently **relocated it into `archive/`** (registry
routing sends terminal statuses to archive regardless of artifact type). Caught immediately
before anything was staged/committed; restored `090-F` to queue with `status: active`.
**Lesson: never run `move --status done` on a protected covering feature — leave it
untouched or set a non-terminal status; only manifest task IDs get the move→archive
treatment.**

## 096-S / 091-F — multi-model adversarial review routing (Stage)

backlogit MCP degraded → CLI fallback (`backlogit.exe`). Triaged stash `E929B1C9` +
`CB6A0EC6` under one covering feature. Plan reviewed in `single-agent-declared-degradation`
mode (reviewer subagent dispatch unavailable) → PASS after P-006 hardening. Harvested feature
`091-F` + 8 tasks (`091.001-T`…`091.008-T`: P-012 degradation policy clause, anchor-review
model config contract, persona-identity audit, GPT-5.6 Sol anchor wiring into
verify-harness/adversarial-review, persona routing, plan-review back-port, gate-contract
tightening, install-harness docs). Shipment `096-S` created task-only (dependency-ordered);
`091-F` derived via task prefix at safe-close, not a manifest member.

## Circuit breaker — PR #238 review-fix cycle (096-S/091-F implementation, Ship)

Universal 3-cycle review-fix limit tripped on PR #238: cycle 1 (schema compat + verify-harness
domain mapping + reviewer-count mapping, `8cb5acd`) → cycle 2 (anchor reasoning-effort
dispatch + checksum evidence, `eafdd40`) → cycle 3 (same-model-declared-degradation marker,
`7b810c8`) → still 2 new unresolved threads at the post-limit gate. **Operator authorized two
further bounded extra cycles** (not a silent bypass):

* Extra cycle 1 (`1d7e985`): fixed absent-route default probing + confidence-tier gap for
  even reviewer counts — surfaced **3 more genuinely new** threads.
* Extra cycle 2 / final (`313ea3e`): the 3 threads were all the **same root defect** — a
  previous PR-introduced fix pointed persona identity paths at the **retired categorized
  layout** (`.github/agents/review/`, `.github/agents/research/`) instead of the **canonical
  flat** `.github/agents/subagents/` (per `install-harness/SKILL.md:1339`). Normalized
  plan-review, install-harness, and the regression test to the canonical path. Surfaced one
  final checksum-drift thread (manifest checksum vs PR-description claim mismatch) — fixed,
  and PR #238 merged (`42a5d6b9`, merge commit) with P-018 satisfied before merge. Durable
  learnings graduated to `docs/compound/096-S-template-vs-global-skill-placeholders.md` and
  `docs/compound/096-S-canonical-subagent-install-path.md`.

**Key learning: operator-authorized "one more bounded cycle" extensions are legitimate and
distinct from silently bypassing the circuit breaker — each extension must still be scoped,
logged, and can itself re-trip if genuinely new findings keep surfacing (which they did,
twice, before convergence).**

## 098-S / 093-F — 088 failure-content-in-success decline hardening (Stage)

Triaged the sole HIGH-priority stash entry `3D8724BA` (deliberation `008-DL`); left the other
5 entries for future cycles. Key finding: the DECLINE detector core already shipped
(`088.004-T`, commit `118bf21`) — this is an **extend, not re-implement** unit. Root cause:
`_FAILURE_BEARING_PATTERNS` in `policy.py` is **colon-anchored** (e.g. `exit code:\s*[1-9]`),
so common non-colon phrasings (`exit code 1`, make's `Error 1`, `npm ERR!`) slip through and a
successful tool result embedding them could be compressed, silently dropping failure evidence.
Broadening the detector is **fail-safe-directional** — it can only ever pass MORE originals
through byte-identically, never newly hide evidence.

Harvested feature `093-F` + 3 dependency-ordered tasks: broaden `_FAILURE_BEARING_PATTERNS` +
positive/negative controls (`093.001-T`) → align `hook.py` evidence-line protection and
`evidence_oracle.py` required-fact patterns to the broadened set (`093.002-T`, dep 001) →
reconcile the 088-F compression plan spec with the DECLINE invariant (`093.003-T`, dep
001+002). Shipment `098-S` created task-only (4 items incl. feature). **Recovered an
in-session harvest mishap**: a section-name whitespace error left a partial `093.001-T` +
duplicate `093.002-T`; cleaned up before finalizing the hierarchy.

**Test-surface gotcha for Ship**: the 088 experiment has its own pytest suite under
`experiments/088-compression-experiment/tests` — the repo's `PYTHONPATH=src python -m
unittest discover -s tests` gate does **not** cover it; Ship must run the experiment's own
pytest suite.

Deferred stash entries (untouched, future cycles): `7D1E2F1A` (telemetry JSONL sink
rotation/retention — strong next candidate), `DD75C983` (agent-intercom opt-in, must be its
own shipment, do not bundle), `157C41D0` (agent-file rename, wide blast radius), `9940C563`
(/compact post-merge workflow policy candidate), `8FD768E9` (engram stale HTTP-endpoint fix in
`.claude/instructions.md:4`).

## Cross-cutting learnings (this batch)

1. **P-015 safe-close discipline is not optional even when it "happens to work."** The
   forbidden `backlogit shipment ship` cascade only avoided corruption in 093-S because the
   manifest coincidentally equaled the full feature scope — the correct pattern (used
   correctly in 095-S/098-S) is per-item `move --status done` + `archive`, protected feature
   left untouched in queue.
2. **Never `move --status done` a protected covering feature** — registry routing relocates
   terminal-status artifacts to `archive/` regardless of type; this silently un-protects the
   feature. Verify-after-each catches it if checked immediately.
3. **Canonical non-top-level agent install path is the flat `.github/agents/subagents/`** —
   any reintroduction of a categorized `review/`/`research/` layout is a regression.
4. **Operator-authorized circuit-breaker extensions are bounded, not indefinite** — each
   extra cycle can still legitimately re-trip on genuinely new findings; convergence is not
   guaranteed by the first extension.
5. **Detector-broadening for evidence-integrity gates is fail-safe-directional** — broadening
   a DECLINE/failure-signal detector can only pass more originals through unchanged, never
   newly hide evidence; bounded downside is reduced compression coverage, gated by mandatory
   negative controls.
