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

## Key finding - both backlogit tool surfaces expose the archive operation

> **CORRECTED (review-fix cycle 3, 2026-08-20).** A mid-session addendum claimed
> the two surfaces were *inverted* and that `backlogit_stash_archive` was not
> exposed on MCP. That was **false**, and the CLI-canonical-plus-deprecated-alias-MCP-fallback
> direction it produced has been retracted from the deliberation, the plan, and
> tasks `137.003-T` / `137.005-T`.

Verified read-only against installed `backlogit v1.10.0`:

| Surface | `stash_archive` | `stash_remove` |
|---|---|---|
| MCP | **exposed - primary** (`backlogit_stash_archive`) | exposed, self-described `[Deprecated: use backlogit_stash_archive]` |
| CLI | **exposed - canonical** (`backlogit stash archive`) | alias of `archive`, same handler |

`.mcp.json` runs `backlogit mcp` with `tools: ["*"]`, so the archive tool is
reachable. The migration is therefore a direct rename: **MCP primary
`backlogit_stash_archive`, CLI fallback `backlogit stash archive`**, with
`backlogit_stash_remove` never named as a prescriptive execution path. Hardening
H5 ("deprecate in place, do not delete" in the registry) still holds, but as a
**descriptive** registry obligation only.

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

---

## ADDENDUM (Stage review-fix, 2026-08-20) - additive; nothing above is modified

Two P1 review findings were confirmed against the artifacts staged in this
session and resolved. The record above is left intact; this addendum supersedes
the specific statements it names.

### Finding 1 - the 137.* task graph could not pass Ship's per-task quality gate

Line 76's note that "tasks `137.003-T` / `137.005-T`" must land together
understated the problem, and line 105's "`145-S` -> `137-F` + 6 tasks" is now
stale.

Ship evaluates the full configured suite before completing **each** task, but the
staged contracts admitted predecessor tasks would leave the verifier, contract
tests, and manifest checksum red until a later task repaired them. The
mutually-breaking set was {old 137.003-T, 137.005-T, 137.006-T}, and old
137.006-T could not go green before its own predecessors - a deadlock.

**Resolved** by collapsing that set into one atomic task:

* `137.003-T` **survives**, rewritten as the atomic migration (template + dogfood
  mirror + verifier marker + contract tests + manifest checksum). Size `S` -> `M`,
  complexity `medium`.
* `137.005-T`, `137.006-T` - **superseded by `137.003-T`**, stamped with
  superseded-by pointers and archived (not deleted).
* `137.004-T` re-verified as independently gate-green and order-independent; its
  former inbound edge from `137.006-T` was not carried over.
* `137.001-T`, `137.002-T` unchanged.

**Corrected shipment line** (supersedes line 105): `145-S` -> `137-F` + **4**
tasks (`137.002-T`, `137.001-T`, `137.003-T`, `137.004-T`). Line 106 still holds:
`145-S` blocks on `144-S`.

**Dependency graph after restructure** - acyclic, no orphans:

```
137.002-T  (no deps)
   |-> 137.001-T
   |-> 137.003-T   [ATOMIC]
137.004-T  (no deps, order-independent)
```

Every remaining task leaves the full configured suite green at its own completion
gate. No task depends on a temporarily red predecessor.

### Finding 2 - archived provenance carried a false CLI-alias assertion

Archived stash record `8D570CF8` asserted, in both its capture text and its
reconciliation, that the backlogit CLI no longer exposes a `stash remove`
subcommand. That is false.

A clearly labeled **factual retraction** was appended to that record. All original
capture text, source refs, reconciliation notes, forward destination refs, archive
state, ID and timestamps are preserved unmodified; the retraction is purely
additive. Corrected fact: v1.10.0's canonical `stash --help` lists `archive`, and
`backlogit stash remove` remains reachable as a **deprecated alias** of archive.
Canonical execution is MCP `backlogit_stash_archive` with CLI `backlogit stash
archive`; the deprecated alias is not prescribed. The entry's conclusion is
unaffected - the operation is deprecated, not absent, so the migration remains
warranted.

The same factual correction is carried into `137.003-T` (which must fix the
matching false comments in `tests/test_scope_containment_boundary_contract.py`)
and into the hardening record's addendum.

### Disposition

Both findings pass P-021 C1 (same contract surface as the staged work) and were
fixed in place. **No deferred entries were created for either.**

---

## ADDENDUM 2 (Stage, 2026-08-20, later session) - execution order superseded

**The "Next step" section above is superseded on one point: ordering.**

A later Stage session found a baseline-red defect that blocks BOTH shipments
staged here, and inserted a new prerequisite shipment ahead of them.

**Corrected execution order:**

```text
146-S  (NEW prerequisite)  ->  144-S  ->  145-S
```

`144-S` is no longer claimable until `146-S` ships. Enforced by the dependency
edge `144-S depends on 146-S (blocks)`. The `145-S depends on 144-S (blocks)`
edge recorded above is preserved unmodified.

**Cause:** `tests/test_scope_containment_boundary_contract.py:127` and
`tests/test_scope_containment_semantics_contract.py:137` hard-load
`.backlogit/queue/019-DL.md`, which was archived to `.backlogit/archive/019-DL.md`
by merge `f72109e2` (PR #374). Both modules collapse in `setUpClass`, so the
configured suite is red before `144-S` starts and no task here can pass Ship's
per-task green gate.

**Not absorbed** - fails P-021 C1 against both `136-F` and `137-F` surfaces.
Captured as stash `7852CE0D`, deliberated as `021-DL`, harvested to feature
`138-F` / task `138.001-T` / shipment `146-S`.

**Relevant to `137.003-T` in this session's `145-S`:** it also edits
`tests/test_scope_containment_boundary_contract.py`. Since `146-S` merges first,
`137.003-T` rebases onto the repaired file. Line ranges are disjoint (path
resolution and 019-DL citations vs. `stash remove`/`archive` CLI-alias comments),
so this is a trivial textual rebase. **No re-plan of `145-S` is warranted** and
nothing else in this memory changes.

Full record: `docs/memory/2026-08-20-stage-7852ce0d-baseline-red-prerequisite.md`.
