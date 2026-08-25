# Stage session memory — 2026-08-25 — 08D71FD5 adversarial-ideation deliberation (030-DL)

## Scope

Deliberation-only on stash `08D71FD5` (interactive-ideation primitive). No harvest, no
shipment, no branch, no worktree (P-016). Invoked by Orchestrator; route
claude-opus-5 / anthropic / high (P-013.5).

## Artifacts produced

| Artifact | ID / path |
|---|---|
| Decision artifact | `docs/decisions/2026-08-25-adversarial-ideation-trigger-before-primitive-deliberation.md` |
| Deliberation item | `030-DL` (queued), linked to stash `08D71FD5` via `deliberation_id` |
| Links | `030-DL` --informs--> `029-DL`, `030-DL` --informs--> `028-DL` |
| Spun-off stash | `7628C291` (bug, medium) — leaf-executor rule contradiction |

## Conclusion

**CONDITIONAL BUILD** a new `adversarial-ideation` **agent**. Gate criterion: it MUST NOT
be harvested or shipped unless the same unit of work also delivers (a) a machine-written
deferral counter and (b) a `verify-harness` check that FAILs on ≥2 deferrals with no
linked ideation artifact. **If descoped, the recommendation inverts to DO NOT BUILD.**

## Decisions and their evidence

1. **Agent, not skill — but the intake's premise was false.** The intake justified
   "agent" with "skills are leaf executors and cannot dispatch." That is contradicted by
   `templates/skills/review/SKILL.md.tmpl` L33-35 and `plan-review/SKILL.md.tmpl` L11-13,
   which both spawn cross-model persona subagents. Conclusion re-derived on the sound
   premise: **route-declaration authority** (P-013.5 — skills cannot declare
   `model_family`/`model_provider` frontmatter, which is why `review/SKILL.md` L136 must
   hedge "cross-model preferred but *not blocking*"). A skill-shaped ideation loop
   degrades to self-challenge silently and undetectably.
2. **Not Orchestrator-embedded** (operator position upheld) — but also **not an elective
   agent**, because that contract says elective agents are "operator-initiated only,
   never invoked autonomously" (`_orchestrator.agent.md` L120), which directly
   contradicts the required autonomous gate trigger. It is a Stage-invoked pipeline
   subagent plus an Orchestrator trigger phrase. New routing category needed.
3. **Partial reuse of adversarial-review, not wholesale.** Its consensus tiering weights
   unique findings LOW=1 vs consensus HIGH=3 — agreement-seeking, which is *inverted* for
   divergent ideation and is itself a conservatism amplifier. Reuse dispatch + routing +
   structured returns; reuse consensus tiering only in convergent pruning; replace the
   capped re-review with a monotone measure.

## THE KEY FINDING (durability — reusable beyond this design)

**The repeat-deferral trigger does not exist.** Verified against the live schema, not prose:

- `stash_entries(stash_id, priority, kind, text, deliberation_id, state, source_path, updated_at)`
- `deliberation_id` is a **scalar** — `34AAF1C7` holds only `028-DL` despite 4+ documented
  re-triages. Prior deliberation IDs are **destroyed by the schema**.
- No `triage_count`, no `deferral_count`, no `created_at`.
- `updated_at` is identical across all three active entries (`2026-08-25T20:55:46.09`) —
  a **re-index stamp**, not a mutation stamp. Zero deferral signal.
- Deferral history survives only as Stage-narrated prose (`[STAGE DARK-FACTORY RE-TRIAGE …]`)
  inside the `text` blob = `029-DL` cell 3 (read-but-tolerated, 0→18→59→**41%**, decaying).
- **Root cause: surface asymmetry.** `items` have `item_log_entries`; `stash_entries` has
  **no log table at all**. Deferrals happen on the one surface with no history.

Producer precedent already live in `.backlogit/hooks.yaml`:
`event_thresholds.blocked_stale_days: 7` + `agent_subscriptions.stage: [blocked_stale]`.

Durability options: **D1** upstream stash schema change — rejected as a *dependency*
(backlogit is external; `tool_name: backlogit`, v1.10.1; no source in repo — all 66 `.go`
files are in gitignored `references/`). **D2** counter via `item_log_entries`
`event_type='deferred'` + **D3** `verify-harness` FAIL check (verify-harness IS installed
here) → ship with the agent.

## Termination rule (reuses 028-DL)

`B₀ = R_max = 3`; `B_r = min(B_{r−1} − 1, N_r)`; terminate at `B_r ≤ 0`, where `N_r` counts
**substantive AND novel** challenges. `B_r` is strictly decreasing on ℕ → termination
guaranteed regardless of oracle behaviour; `N_r` only makes it earlier. Reproduces the
observed 8/5/3 session exactly (`B_r` = 2, 1, 0). Degenerate cases: volume-without-novelty
→ `novelty_exhausted`; deadlock → `UNRESOLVED_DISAGREEMENT` with both positions preserved
(never force consensus); `ADVOCACY_COLLAPSE` when the advocate returns zero substantive
positions while the skeptic does not — that round may not return `defer`.

## Gate verdict

Deliberation COMPLETE. Planning gate NOT PASSED — **machinery absent, not failed**:
`impl-plan`, `plan-review`, `harvest`, `deliberate` are not installed (stash `8AC574F1`);
only 4 engine skills are (`install-harness`, `tune-harness`, `verify-harness`,
`workspace-discovery`). No impl-plan output fabricated, no plan-review verdict claimed.

## Next steps

1. Operator decides whether the §4.6 gate criterion is acceptable scope.
2. If yes → plan D2 + D3 **first**; the agent is the payload, the trigger is the deliverable.
3. If the durability mechanism is descoped → do not build; the reasoned negative is §4.6.
4. Triage spun-off stash `7628C291` (leaf-executor rule contradiction) separately.
5. Stash `08D71FD5` remains **active** — deliberated, not consumed into a backlog item, so
   not archived.

## State notes

`INDEX_SYNC_OK` (967 artifacts) at session start. `.mcp.json` and `.backlogit/runtime/`
deliberately left untouched (pre-existing operator state). No checkpoint left active.
