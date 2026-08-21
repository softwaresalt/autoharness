---
title: "Stage session - docline lint restoration + harness-consistency follow-ups"
date: 2026-08-20
agent: stage
route: "claude-opus-5 / anthropic / high (P-013.5, inherited)"
stash_consumed: [395EBE60, 8D570CF8, 6D62077C]
stash_created: [90F2A9F8, 8FA8FC22]
features: [136-F, 137-F]
shipments: [144-S, 145-S]
terminal_state: "queued; awaiting Orchestrator staging-artifact gate"
---

# Stage session memory - 2026-08-20

## Scope

Operator-selected, exactly three stash entries: `395EBE60`, `8D570CF8`,
`6D62077C`. No other entries triaged. All three carried the literal
`DEFERRED SCOPE EXPANSION` marker, so P-021 C6 precedence forced the
`deliberate` route for each regardless of shape, size or priority.

## Degraded-mode declarations

* `TOOL_OK: backlogit` (MCP + CLI v1.10.0)
* `INDEX_SYNC_OK` (890 items at start)
* `ENGRAM_DEGRADED` - agent-engram pack active, MCP surface unavailable; used
  file-based discovery (grep/view/git) throughout.
* `INTERCOM_DEGRADED` - agent-intercom pack active, MCP surface unavailable;
  phase broadcasts skipped, operator choices carried in the session report.
* `GRAPHTOR_UNAVAILABLE` - graphtor-docs pack active, server unreachable; used
  file-based `docs/` search.
* Checkpoint scan: total 2, both `abandoned`, 0 active, 0 quarantined ->
  ZERO-CANDIDATE NORMAL STARTUP, no recovery performed.

## Triage obligations discharged

**Duplicate detection (unconditional, obligation A)** - run over all three
entries against 11 active stash entries, 170 archived entries, and the 890-item
backlog index. **CLEAN for all three**; no merges, no archival of duplicates.
Recorded explicitly because an unrecorded clean scan is indistinguishable from
a scan that never ran.

**Late-identifier reconciliation (obligation B)** - performed in place under
Stage's own stash authority; no Ship write requested.

| Entry | Recovered | Outcome |
|---|---|---|
| `395EBE60` | PR **#372** | `474a1438` verified via `git merge-base --is-ancestor` to be an ancestor of merge `94898dc7` (PR #372). Review-thread: no late identifier found; absence stands. |
| `8D570CF8` | none | PR #372 already concrete. Review-thread N/A **stands**: an adjacent Copilot thread on closure PR #374 cites the same lines (`_ship.agent.md.tmpl:818-821`) but raises a different concern (execute Step 7, not its deprecation). Recorded as context, not claimed as this entry's thread. |
| `6D62077C` | PR **#373** | Recovered from the Ship-owned closure record's `feature_pr: 373`. Review-thread: none exists; absence stands. |

## Key finding - the spike falsified its own stash entry's premise

`6D62077C` assumed the divergence was conditional stripping (dogfood as a subset
of the rendered template). Measurement showed it is **bidirectional**: for the
`_ship` pair, 508/692 dogfood lines (73%) are absent from the rendered output
**and** 697/880 rendered lines (79%) are absent from the dogfood file. These are
independently-maintained documents, not renderings.

Three distinct causes isolated; the fourth pair (`github-pr-automation`,
725-byte delta, zero conditional markers) is **prose drift**, not conditional
content, so the four pairs are not a homogeneous set.

**Decision: do not extend `_render_template`.** Formalise paired-edit
maintenance instead. The disqualifier for the alternative is that reconciling
~1,200 lines of bidirectional drift requires deciding which side wins for every
drifted normative sentence in the harness's own governing agent contracts -
editorial correctness work, not mechanical refactoring.

## Key finding - the two backlogit tool surfaces are inverted

Found late, while performing this session's own stash archival:

| Surface | `stash_remove` | `stash_archive` |
|---|---|---|
| MCP | exposed, self-described `[Deprecated: use backlogit_stash_archive]` | **not exposed** |
| CLI | **not exposed** | exposed |

A naive rename of Ship's contract to "call `backlogit_stash_archive`" would name
an MCP tool that does not exist. Deliberation, plan, and tasks `137.003-T` /
`137.005-T` were corrected mid-session with an addendum specifying CLI-canonical
plus deprecated-alias MCP fallback. This also independently vindicated hardening
H5 ("deprecate in place, do not delete" in the registry).

## Scope discipline (P-021 C1)

Two findings from Stage's own work were **captured as deferred entries, not
absorbed**:

* `90F2A9F8` - `[EXTERNAL / backlogit-owned]` linter hard-abort product decision
  (width-isolated from this repo; follows the `84D8E6AB` / `3C7AAC71` precedent).
* `8FA8FC22` - `_derive_template_variables` coverage gap leaving unresolved
  `{{...}}` placeholders (install-correctness defect on a different surface).

## Output

* `144-S` -> `136-F` + 3 tasks. Docline lint restoration.
* `145-S` -> `137-F` + 6 tasks. Harness-consistency follow-ups.
* `145-S` blocks on `144-S` (shipment sequencing edge recorded).

Ordering rationale: `144-S` restores the repo-wide docline lint, so `145-S`'s
new and edited documentation can actually be validated workspace-wide.

## Next step

Orchestrator Step 1.5 staging-artifact gate. Stage did **not** commit or push -
the working tree carries operator-managed `.backlogit` bookkeeping that must be
preserved, and publication is the Orchestrator's step.
