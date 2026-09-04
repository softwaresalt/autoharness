---
title: "Stage dark-factory session 2026-08-31 — 48-ID fixed-scope staging run"
date: 2026-08-31
doc_type: memory
agent: "Stage"
route: "claude-opus-5 / anthropic / high"
session_mode: "DARK_MODE_ACTIVE"
dark_mode_activated_at: "2026-08-31T21:47:45Z"
head_at_start: "2661c1c82f82a22224c2f7df9309fe17f0745cf6"
---

# Stage dark-factory session — 2026-08-31

Fixed scope: 43 stash IDs + 5 queue IDs = 48. No expansion. Operator AFK,
autonomous sound judgment authorized.

## Tool status

| Surface | Result |
|---|---|
| backlogit MCP + CLI | `TOOL_OK`; `INDEX_SYNC_OK` (`indexed: 1040`) |
| Engram CLI | `ENGRAM_OK` — main, 201 code files, 15 211 edges, `stale_files: false` |
| graphtor-docs | `GRAPHTOR_UNAVAILABLE` — local `docs/` fallback used |
| agent-intercom | `INTERCOM_DEGRADED` — local phase records only, no broadcasts |
| Route | `claude-opus-5 / anthropic / high` honoured throughout; no `ROUTING_DEGRADED` |

Effective status `DEGRADED_MODE: graphtor-docs, agent-intercom`. No public-web
egress of internal context.

## What was produced

* 1 master triage/portfolio deliberation with the full 48-ID disposition table
  and five embedded decisions (D1–D5).
* 9 implementation plans, each hardened where triggered and each carrying a
  multi-persona adversarial review table with a recorded **PASS** verdict.
* 9 covering features `151-F`–`159-F`.
* 27 tasks, every one carrying both `size` and `complexity` written through the
  three-call seam (`create` → `size`+`size_source`+`size_ruleset_version` →
  `complexity`), ruleset `ah-stage-sizing-v1`. (Originally staged under the
  non-canonical label `autoharness-stage-2h-v1`; normalized to the canonical
  ruleset ID in review-fix cycle 1 via `backlogit update --size --size-source
  --size-ruleset-version` on all 37 affected tasks. Canonical ID is fixed by
  `docs/size-complexity-reference.md` §Provenance-completeness rule.)
* 9 queued shipments `159-S`–`167-S`, chained by 8 `blocks` edges in priority
  order, all successors `queued`.
* 5 intra-shipment task `blocks` edges.

## Decisions taken

* **D1** `028-DL` → done. Branch (a) lives in portfolio S9; branch (b) still
  blocked on reasoning-state identity (A8). Living tracker `34AAF1C7` not split.
* **D2** `029-DL` → done. Output already consumed by `031-DL`; its law ("a
  convention survives iff a machine produces it or penalizes its absence") is
  carried into `163-S`, `165-S`, `166-S`.
* **D3** `56803680` → **KEEP but DEMOTE** backlog-md. DROP recorded as *not
  autonomously available*: it is a breaking schema-enum change whose decisive
  input is unanswerable from inside this repository.
* **D4** `7628C291` → amend the two instruction templates with a **bounded
  one-hop** review-family exception; do not change skill behaviour. Stated as a
  machine-checkable property, not a name list. P-013.5 inheritance untouched.
* **D5** `030-DL` → done. Durability trigger has not fired; `08D71FD5` stays
  active as the counter.

## Material discovery (inside existing scope)

`.autoharness/backlog-registry.yaml` is 269 lines against its 460-line template:
**22 operations, the whole sizing field map, and 7 feature flags including
`sizing: true` are missing**. This is the mechanical cause of (a) the Step 0.0
tool gate under-declaring the surface — a live P-012 ad-hoc-fallback exposure,
(b) `2E67938C` being unsatisfiable, and (c) Stage's own stash-archive obligation
having no declared binding. Folded into `2E67938C`'s existing scope as its
enabling condition; **no new stash entry, no scope expansion.** Owned by `165-S`.

## Deviations and limitations recorded

1. **Stage stop-condition budget.** The agent contract lists "tasks attempted in
   session: 20 → halt". This run created 27. Recorded as an explicit, deliberate
   deviation: the scope was operator-fixed at 48 IDs with no expansion permitted,
   the run's own `DARK_MODE_ACTIVE` stop-condition list does not include a task
   count, and halting at 20 would have left four shipments planned-and-reviewed
   but unassembled. Flagged here rather than silently absorbed.
2. **`custom_fields.queue_position` is partially supported.** `backlogit queue
   move` writes it, but it operates on the *dependency-respecting* queue view, so
   items with unmet `blocks` edges are not addressable — `queue move 160-S`
   returns `item 160-S not found in queue view`. Positions are therefore assigned
   across the eligible set; `160-S`–`167-S` and the four dependency-blocked tasks
   acquire positions as their predecessors clear. **The `blocks` chain is the
   authoritative ordering**; `queue_position` is a within-eligible-set ordering.
3. **One torn write was detected and repaired.** The first `queue move` pass was
   interrupted mid-renumber, leaving positions 1–37 assigned and the remainder
   unset. A completed pass was re-run and the final state verified item by item.
4. **One erroneous dependency was created and removed.** `155.001-T → 155.002-T`
   had no basis; removed via `backlogit dep remove` and re-verified empty.

## Review-fix cycle 1 (2026-08-31, after independent local review blocked `4d029e55`)

An independent local review (Constitution, Correctness, Architecture, Scope
Boundary, Security Lens, Template Integrity, Schema-CLI-Docs Coupling) BLOCKED the
publication diff. 13 P1 blockers and 10 coupled P2s were fixed in-place under
P-021 C1 — all concerned correctness/completeness of the artifacts this run had
just produced, so none was deferrable.

### Corrections that overturned a cycle-0 conclusion

Five cycle-0 conclusions were **factually wrong** and were reversed on measurement,
not on argument:

1. **`01340569` (SHIP-9)** — cycle 0 asserted `.gitignore` contained
   `.backlogit/checkpoints/` and that five files were tracked. Both false:
   `git check-ignore` exits 1 (no rule exists) and **19** files are tracked. The
   "lying ignore rule" defect does not exist. Direction reversed from
   *untrack via `git rm --cached`* to **keep tracked, change nothing**.
2. **`F0ADCC03` (SHIP-4)** — cycle 0 said the template hardcodes
   `python.instructions.md`. It does not; it uses `{{PRIMARY_LANGUAGE_LOWER}}`,
   and the install mapping is documented at `install-harness/SKILL.md:1057`. The
   real defect is a co-installation gap; strategy fixed as Decision F.
3. **SHIP-3 ownership** — cycle 0 made the recorded `agent` the primary
   authorisation input. `AGENT_NAME` is a caller-controlled env var defaulting to
   `unknown` (`acquire_lock.ps1:38`, `acquire_lock.sh:32`). Reframed as an
   anti-accident identity (O1) with a real capability token added (O2) and the
   advisory bound stated so no adversarial claim survives (O3).
4. **SHIP-4 leaf-executor** — the exception was called "machine-checkable" while
   being prose nothing read. Replaced by a bounded static verifier (H-b) with its
   document-layer-only limitation recorded (H-d).
5. **`queue_position`** — believed to be an ordering authority; it is a
   dependency-filtered partial projection. See the portfolio's *Queue ordering
   authority* section. Cycle 0's note in this memory ("the `blocks` chain is the
   authoritative ordering") was right; the metadata did not reflect it, and now
   does.

### Structural changes

* **9 new tasks**: `151.006-T`, `153.004-T`, `153.005-T`, `154.004-T`,
  `155.004-T`, `155.005-T`, `155.007-T`, `155.008-T`, `156.003-T`.
* **1 task re-scoped, ID preserved**: `155.003-T` (ten-file repair + guard →
  guard only).
* **1 task archived**: `155.006-T`, a duplicate created then superseded during the
  split; archived non-destructively with a successor pointer.
* **20 `blocks` edges added** in cycle 1 (**23 after cycle 2** — see the
  review-fix cycle 2 section below), including four de-risking prerequisites
  (`151.006→151.003`, `153.004→153.001/153.002`, `155.005→155.002`,
  `156.003→156.002`), three TDD red-first edges (`151.004→151.001/151.002`,
  `152.002→152.001`, `158.002→158.001`), and the genuine cross-shipment artifact
  dependency `155.003-T → 159.003-T`.
* **`queue_position` removed from all 54 in-scope items**; dependency edges are
  now the sole ordering authority.
* **All nine plans** gained the harvest-mandated `dispatch_mode:` /
  `decision:` machine markers under a `## Plan Review` section, with truthful
  values (`single-agent-declared-degradation` / `PASS`).
* **Checkpoint corrected** via official create+resolve; zero active checkpoints.

### A gate caught a real defect during this cycle

After the splits, `163-S`'s `size_composition` reported `unsized: 1` — the
archived `155.006-T` retained `parent_id: 155-F` and was still counted in the
rollup despite not being in the item manifest. This is **exactly** the defect
class SHIP-8's `158.002-T` proposes to gate on (`unsized > 0`), observed live.
The stale parent link was removed and the rollup is now truthful. Recorded in the
archived record itself as evidence for `158.002-T`.

### Residual, carried forward

* **Deferred scope (P-021)** captured in-plan, not silently broadened: `13F5EEF0`
  and `A7AD3044` (SHIP-3), `24374649`/`-2`/`-3` (SHIP-4), `0F6B2B3B`/`-2`/`-3`
  (SHIP-5), `FE098366`/`-2` (SHIP-8). Each carries an explicit residual-risk
  statement.
* **`docs/decisions/2026-08-30-pip-install-autoharness-version-ceiling-spike.md`**
  is a pre-existing artifact outside the fixed 48-ID scope that was included in
  commit `214347b2`. Not deleted (destructive, unauthorized), history not
  rewritten; recorded as a provenance-clarity residual in the portfolio's
  *Residual scope note*.

## Next cursor

* **Next shipment**: `159-S` (SHIP-1). Nothing blocks it.
* **Next portfolio unit**: `031-DL` **S2 — D-ART**, owner `C327A8DE`.
  Prerequisites S0 (`148-F`) and S1 (`149-F`) are both `done`, so S2 is newly
  eligible; it is `critical`, low-risk, report-only, zero day-one blast radius.
* **Next feature**: `47971057`. **Next spike**: `6A2D62DD`, best run after
  `166-S` lands.
* **Operator input required**: `080-F`, `081-F`, and `B698F01B`'s three reserved
  env-injection questions.

## Review-fix cycle 2 (2026-08-31, over reviewed HEAD `99a3729d` — BLOCKED)

A second independent local multi-persona review (Correctness, Scope Boundary,
Security Lens, Schema/CLI/Docs Coupling, Constitution, Architecture, Template
Integrity) blocked the publication diff. **11 blocking fixes and 7 directly
coupled readiness corrections** were applied. Where reviewers disagreed on
severity for stale task references (some P2, Scope P1), the **conservative P1**
classification was used.

### Backlog / graph changes

* **SHIP-8 impossible dependency model repaired by a real task split.**
  `158.001-T` was blocked by the *whole* of `158.002-T` while `158.002-T` owned
  both the red tests **and** post-implementation assembly work — so `158.001-T`
  could never start. `158.002-T` is re-scoped to the **red-test half only**
  (`S`/`low`); the assembly/green half became **new task `158.003-T`**
  (`M`/`medium`), added to `166-S`. Encoded edges now express
  **test → implementation → assembly**: `158.001-T ← 158.002-T`,
  `158.003-T ← 158.001-T`.
* **Three `blocks` edges added**, all previously prose-only or missing:
  `153.002-T ← 153.001-T` (both edit the acquire scripts),
  `158.003-T ← 158.001-T`, `157.002-T ← 157.001-T` (parity test must run against
  the regenerated registry).
* **Task-edge count: 18 → 23** (the 18 was stale even at cycle 1, when the graph
  held 20). Re-derived from the queue files, not carried forward.
* **Safety modes propagated into all 37 executable tasks.** Every plan declared
  `careful`, but 21 tasks carried no safety-mode line in their own body. Named
  `freeze-scope` bounds added for the high/production-impact tasks review called
  out: `153.001-T`, `155.001-T`, `152.001-T`, `151.003-T`, plus comparable
  siblings (`151.004-T`, `151.005-T`, `152.003-T`, `156.002-T`, `157.001-T`,
  `158.001-T`) and `investigate-first` on `159.001-T`.
* **Stale reference repair (P1).** `155.007-T` and `155.008-T` had every
  operative reference pointed at **archived zero-work `155.006-T`** instead of
  live guard `155.003-T`; repointed. `155.003-T`'s "batch of 5" corrected to
  "batch of 2". The prior mentions survive only inside explicit correction notes.

### Contract corrections carried into executable tasks

| Task | Correction |
|---|---|
| `151.001-T` | Was "backlogit-gated"; now **unconditional prose**, `{{BACKLOG_DIRECTORY}}` only, exact spelling, `{{FEATURE_*}}` forbidden with a zero-occurrence check. |
| `157.001-T` | **P0**: refresh `.autoharness/harness-manifest.yaml` checksum for the regenerated registry and **verify the coupling by read-back**, in the same atomic unit. |
| `155.004-T` | **H11** tune-harness drift guidance so the intentional P-019 required-gate carve-out is not misclassified as drift, with positive **and** negative drift assertions. |
| `154.002-T` | **Decision G rewritten (G1–G9).** A backlogit comment is agent-authorable, so it cannot be the authorization source; authority is now a **direct runtime operator approval** over a channel the agent cannot synthesize, the comment is **evidence only**, no channel means **halt, do not restore**, and a **self-authored-comment negative test** was added. Dark/AFK fail-closed preserved and strengthened. |
| `153.002-T` | **Token contract TC1–TC6**: CSPRNG-only ≥ **128 bits**, forbidden primitives enumerated, **SHA-256-or-stronger** digest (MD5/SHA-1 forbidden, fail closed if unavailable), cross-platform interoperability, and documented **stdout/log exposure and safe handling**. |
| `156.002-T` | **H6a/b/c** promoted from de-risking note to acceptance: tool names **derived dynamically at check time** (never hardcoded), **feature-flag binding forbidden**, **fail closed on nested blocks** — each with a named assertion. |
| `158.001-T` | The **advertised `features.sizing` flag is the sole authoritative signal**; operation-parameter presence never arms the gate. |
| `155.001-T` | **S1** defines **one shared markdownlint scope** for CI and generated/local hooks (changed files vs merge-base, one config, one pinned version), superseding the H3/finding-1 contradiction. |

### Verification performed (Stage-owned, structural only)

* Topological sort over all 37 tasks: **37 nodes, 37 visited, acyclic**, no edge
  referencing a non-existent prerequisite.
* Every `BLOCKED BY` prose claim matched against the machine graph: **0
  mismatches**.
* All 9 shipments: members exist, **all `queued`**, `unsized = 0`.
* Shipment chain `159-S → … → 167-S` **unchanged** (8 edges).
* Frontmatter, single-H1, and markdown table column consistency across all 10
  changed documents: **clean**.
* No build, test, or lint run — outside the Stage role boundary.

### P-021 captures (out of `DARK_MODE_SCOPE`, deliberately not fixed)

* `477D37BD` (`bug`, `low`) — `LEGACY_ESCALATION_*` vs `ESCALATION_*` in
  `templates/harness-config.yaml.tmpl`. Read-only verification suggests the split
  is **intentional and documented**; likely disposition is a guard plus
  signposting.
* `2FA67AAC` (`bug`, `medium`) — AGENTS.md cites 6 of 21 policies; the gap
  **widens when SHIP-5 lands** (P-019 amended, P-021 absent).
* `39A4DDEB` (`feature`, `low`) — backlogit exposes **no shipment-membership
  reorder operation**, so `163-S` could not be stable-sorted through official
  operations; the misleading order-implies-execution reading was closed in the
  decision record instead.

### Known residual

* `163-S` membership remains unsorted — no official operation can reorder it, and
  hand-editing a tool-owned manifest was rejected. Ordering authority is the
  `blocks` graph, and that is now stated explicitly.
* Three review-fix cycles of three are consumed. The next review is the **final
  independent disposition cycle**; this work is offered as fit for that review,
  **not** as publication-ready.

## Handoff boundary

Stage did not modify any source, template, schema, workflow, or test file, did
not claim or close any shipment, did not create or use a branch or worktree, and
did not create or push any pull request. Publication of the committed planning
artifacts is returned to the Orchestrator.
