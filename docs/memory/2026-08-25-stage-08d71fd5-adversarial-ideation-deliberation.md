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

**The repeat-deferral trigger does not exist.** Verified against `.backlogit/stash.jsonl`
— the markdown/JSONL **source of truth** (13 active entries, field union
`created_at, deliberation_id, id, kind, priority, text`):

- `deliberation_id` is a **scalar** — `34AAF1C7` holds only `028-DL` despite 4+ documented
  re-triages. Prior deliberation IDs are **destroyed by the schema**.
- No `triage_count`, no `deferral_count`, no per-triage event record.
- `created_at` **exists and is correctly populated** (distinct, monotonic: `34AAF1C7`
  08-12, `08D71FD5` 08-25 20:08, `7628C291` 08-25 21:05); the CLI even derives `age_days`.
  **But age is not triage count** — it cannot distinguish "deferred five times over two
  weeks" from "sat untouched for two weeks," which is the discrimination the trigger needs.
- Deferral history survives only as Stage-narrated prose (`[STAGE DARK-FACTORY RE-TRIAGE …]`)
  inside the `text` blob = `029-DL` cell 3 (read-but-tolerated, 0→18→59→**41%**, decaying).
- **Root cause: surface asymmetry.** `items` have `item_log_entries` (a full event log);
  stash entries have exactly one timestamp and **no log table**. Age is a *point*, deferral
  count is a *sequence* — no point-valued field encodes a sequence however correctly
  populated. The missing thing is an **event log**, not a broken field.

Producer precedent already live in `.backlogit/hooks.yaml`:
`event_thresholds.blocked_stale_days: 7` + `agent_subscriptions.stage: [blocked_stale]`.
It works on items because it thresholds over an event history the stash surface lacks.

Durability options: **D1** upstream schema change — rejected as a *dependency*
(backlogit is external; `tool_name: backlogit`, v1.10.1; no source in repo — all 66 `.go`
files are in gitignored `references/`). **D2** counter via `item_log_entries`
`event_type='deferred'` + **D3** `verify-harness` FAIL check (verify-harness IS installed
here) → ship with the agent.

## CORRECTION ROUND — cache-vs-source-of-truth hazard, demonstrated

The first version of this finding claimed "no `created_at`" and "`updated_at` is identical
across all three live entries — a re-index stamp." **Both were wrong**, because both were
read from the **SQLite index** rather than `stash.jsonl`. Operator caught it. Verdict
unaffected; the corrected facts are *stronger*.

The three surfaces disagree, and the cache diverges in **both directions**:

| Surface | Fields |
|---|---|
| `stash.jsonl` (**source of truth**) | `created_at`, `deliberation_id`, `id`, `kind`, `priority`, `text` |
| CLI `stash get` | `id`, `priority`, `kind`, `text`, `age_days` (+`deliberation_id`) |
| SQLite `stash_entries` (**cache**) | `stash_id`, `priority`, `kind`, `text`, `deliberation_id`, `state`, `source_path`, `updated_at` |

The cache **invents** `updated_at` (absent from source — rehydration bookkeeping) and
**drops** `created_at` (present in source), which produced the false negative.

**The clincher**: the uniform timestamp cited as evidence (`20:55:46.09`) was written by
**my own Step 0.1 `backlogit sync`** at session start; on re-query it had moved to
`21:07:10.12`. The column also mixes timezone representations across rows. I measured my
own tool invocation and reported it as a property of the domain — two sessions after
writing the `029-DL` storage correction that says exactly this.

**Transferable rule**: *the SQLite index may be used to find and count things; it may
never be used to establish **absence** of a field, because it is lossy in both directions.
Schema absence claims must be verified against markdown/JSONL.* A field whose values are
suspiciously uniform across unrelated rows is rehydration bookkeeping until proven
otherwise. Confidence in a schema claim may not exceed the authority of the surface it was
read from. → Candidate for `docs/compound/`, independent of whether the agent is built.

## ROUND-2 ADDENDUM — the trigger substrate was wrong; replaced

**Operator found a real hole.** Stash entries have **no `status` field**, so `blocked_stale`
(a blocked-status staleness threshold) can never fire on one. And `item_log_entries` is an
*items* table — `34AAF1C7` accrued its re-triages while still a stash entry, never
harvested, so it would have zero rows. **The trigger as specified would not have fired on
the case it was designed to catch.** Same error class as the cache read, one layer up:
there I read the wrong *storage* surface; here I proposed against the wrong *entity* surface.

**Replacement substrate — the reverse index, which already has a machine producer.**
`backlogit deliberate <stash-id>` writes `custom_fields.linked_stash_id` into the `-DL`
item. Measured across all 33 `-DL` items:

| Creation path | Carries `linked_stash_id` |
|---|---|
| `backlogit deliberate <stash-id>` | **29 / 29 (100%)** |
| generic `create_item` / `add` | **0 / 4 (0%)** (`029-DL`, `044.001`, `045.001`, `053.001`) |
| **Total** | **29 / 33 (88%)** |

The producer never fails when invoked — it is simply **bypassable**. This session is the
controlled demo: `030-DL` created via `create_item` (no ref), deleted, re-created via
`deliberate 08D71FD5` (ref present).

**Two corrections to the addendum itself:** (1) `-DL` items are **not** at 0 back-references
— they are at 88%; the operator grepped for `source_stash`/`stash_id` and the field is
`custom_fields.linked_stash_id`. (2) The durability requirement is therefore **not**
"make `source_stash` machine-produced from 7%" but **"mandate the existing code path and
penalize the bypass, from 88%"** — materially cheaper. `source_stash:` in `docs/decisions/`
(3/43, 7%) is retained as a secondary human-readable index only.

**Undercount, two layers (both recorded honestly):**
- **Layer 1 — bypass (fixable).** 4/33 = 12% missing. `34AAF1C7` has two formal
  deliberations (`028-DL`, `029-DL`) but `linked_stash_id` finds only `028-DL`;
  `source_stash` finds both. **Neither index alone returns 2 — only their union does.**
- **Layer 2 — structural (NOT fixable by the index).** A re-triage that produces no
  deliberation artifact is invisible to any deliberation-artifact counter. `34AAF1C7`'s
  08-14 and 08-15 re-triages emitted only prose. True count ~5, union index returns 2.
  **The counter counts deliberations, not deferrals.** Closing this requires making the
  *defer decision itself* producing — which promotes the P-006 analogue from complement to
  necessary second half (gate component C).
- Bias is adverse and compounds: both layers undercount worst on old, repeatedly-deferred
  entries — the ones most needing the trigger.
- Threshold ≥2 is a **lower bound**: safe against false positives, prone to false negatives.
  Correct failure direction for a gate that forces extra work. Do not lower to 1.

**Gate expands from 2 components to 4** (§4.6): (A) the union counter; (B) the bypass
penalty — `verify-harness` FAILs on a new `-DL` without `linked_stash_id`, enforce-on-new-only
so day-one blast radius is zero; (C) defer-emits-an-artifact, per Layer 2; (D) the
`verify-harness` FAIL on ≥2 deferrals with no ideation artifact.

**VERDICT RE-CONFIRMED UNCHANGED: CONDITIONAL BUILD.** The hole was in the substrate, not
the argument — it is one more surface that cannot see the phenomenon, reinforcing §4.1.
The replacement is *cheaper* (88% producer already exists vs. building one). The one thing
that genuinely got harder: Layer 2 was invisible in v1, and component (C) is new work.

Also: this artifact now carries its own `source_stash: 08D71FD5` frontmatter, dogfooding
the convention it mandates.

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
