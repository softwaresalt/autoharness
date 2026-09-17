---
title: "Closure-evidence producer/consumer naming contract reconciliation"
description: "Decision to establish a single authoritative closure-evidence naming contract in code (one canonical WRITE pattern, one closed and explicitly enumerated RECOGNIZED-READ set), rewire the pipeline-topology closure consumer onto it, add write-time validation plus name-mismatch diagnostics, and pin the producer/consumer pair with a composed state-machine test — without weakening the fail-closed closure gate, modifying any committed closure artifact, or authoring a competing closure record for 162-S."
doc_type: decision
source: docs/decisions/2026-09-17-closure-evidence-naming-contract-deliberation.md
date: 2026-09-17
status: decided
depth: deep
deciders: operator, Stage
decision_status: decided
promoted_to: plan
revision: 4
revision_note: "Decisions D1-D9 and risks R1-R9 are stated in their current, authoritative form. No decision has been reopened, reversed, added, or removed since adoption; where a decision body has been refined, it is edited in place so this record presents exactly one binding statement per decision rather than a succession of variants. The `## Options Evaluated`, `## Trade-off Comparison`, and `## Rejected Alternatives` sections are retained as explicitly non-binding historical analysis — the binding output of this deliberation is the `## Decision` section alone."
source_stash_id: FD0CCB42
stash_ids:
  - FD0CCB42
source_bug_report: docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md
linked_artifacts:
  - docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md
prior_learnings:
  - docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md
source_refs:
  originating_task_id: 165.007-T
  originating_feature_id: 165-F
  originating_shipment_id: 173-S
  pr_number: "N/A"
  review_thread_id: "N/A"
tags:
  - "closure"
  - "contract-drift"
  - "producer-consumer"
  - "pipeline-topology"
  - "composed-state-machine"
  - "p-021"
  - "fail-closed-design"
---

# Closure-Evidence Producer/Consumer Naming Contract

## P-021 C6 Compliance Statement

Stash entry `FD0CCB42` carries the literal `DEFERRED SCOPE EXPANSION` marker.
Per the Stage Step 1 precedence rule, that marker **forces** the `deliberate`
route regardless of the entry's apparent shape, size, priority, or triviality,
and the entry may not proceed to Step 3 planning without this artifact. This
document is that artifact.

### Triage obligations discharged

| Obligation | Trigger | Outcome |
|---|---|---|
| **(A) Duplicate detection** | Unconditional | **CLEAN.** Re-run 2026-09-17 over all 110 active stash entries on the exact keys `post-merge-closure`, `closure_complete`, `PREDECESSOR_CLOSURE_INCOMPLETE`, `docs/closure/{`, `naming contract`, `filename pattern`. Nearest neighbours `24E3E464`, `C395CFE3`, `0C094AED`, `63C5C305`, `5A537510` are all about the **content, prose, or supersession metadata of specific closure records**, not the producer/consumer naming contract or the gate's discovery glob. `7F93FA0C` — cited in `docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md` as the tracking identity for this same defect class — was explicitly checked and is **not present in this workspace's active stash** (it belongs to the sibling harness workspace whose bug report is vendored at `docs/bugs/2026-09-06-...`). No duplicate exists. `FD0CCB42` remains the sole tracking identity. |
| **(B) Late-identifier reconciliation** | `pr_number: N/A`, `review_thread_id: N/A` | **NO-OP (second confirmation).** Re-run 2026-09-17 across every Ship-owned residual-risk record citing `FD0CCB42` (`docs/memory/compacted/2026-09-14-ship-173-s-165-f-full-lifecycle-compacted.md` L124-127, `docs/closure/173-S-165-F-post-merge-closure.md`, `.backlogit/archive/173-S.md`, `.backlogit/archive/165.007-T.md`, `.backlogit/logs/165.007-T.jsonl`). The expansion originated in a **pre-PR Stage staging session** with an **operator-delivered** plan-review finding, so no PR number and no hosted review thread ever existed for its point of discovery. The later 173-S implementation PRs (#448 → #450, closure PR #451) are the shipment's PRs, not this expansion's origin, and citing them would be a false attribution. The recorded `N/A` values **STAND as truthful terminal records**. Not a gate on deliberation, planning, or harvest. |

Grouping analysis (Stage Step 1.5) is **not applicable**: the session targets a
single entry, and a deferred-scope-expansion entry is excluded from grouping
until its deliberation exists.

## Problem Frame

### The defect

Post-merge closure evidence has a **producer** and a **consumer**, and they
specify the artifact's filename incompatibly.

**Baseline producer/consumer surfaces**, as they stand in the committed tree.
The template column carries the unrendered `{{DOCS_CLOSURE}}` placeholder
because templates are the product; the installed dogfood mirror carries the
rendered literal `docs/closure`. That difference is correct and is preserved by
this decision — it is not part of the drift.

| Role | Location | Contract as committed | Placeholder or literal |
|---|---|---|---|
| Producer skill (template — the product) | `templates/skills/operational-closure/SKILL.md.tmpl:23` | `{{DOCS_CLOSURE}}/{YYYY-MM-DD}-{slug}-closure.md` | `{{DOCS_CLOSURE}}` placeholder |
| Producer skill (installed dogfood mirror) | `.github/skills/operational-closure/SKILL.md:23` | `docs/closure/{YYYY-MM-DD}-{slug}-closure.md` | rendered literal |
| Ship agent (template — the product) | `templates/agents/_ship.agent.md.tmpl:863` | names the output **directory** `{{DOCS_CLOSURE}}/` only, with no filename contract, and lists `compaction status` without `closure_status` | `{{DOCS_CLOSURE}}` placeholder |
| Ship agent (installed dogfood mirror) | `.github/agents/_ship.agent.md` (post-merge closure step) | same omission, rendered | rendered literal |
| Consumer | `src/autoharness/gates/topology.py:718` (`FilesystemTopologyReaders.closure_complete`) | `docs/closure/` glob `{shipment_id}-*-post-merge-closure.md` | literal in source |
| Consumer predicate | `src/autoharness/gates/topology.py:303` (`_closure_artifact_complete`) | `compaction_status ∈ {done, degraded}` **and** (`closure_status == READY` or `READY_WITH_CONDITIONS` with a fully-satisfied `conditions:` block); returns a **boolean**, never a reason | — |
| Gate | `src/autoharness/gates/topology.py:1866-1882` (`_shipment_readiness_check`) | emits `PREDECESSOR_CLOSURE_INCOMPLETE` whenever the reader returns anything other than `True` | — |

No string satisfies both the producer's date-prefixed/`-closure.md` shape and
the consumer's ID-anchored/`-post-merge-closure.md` glob. Discovery is
**filename-driven and precedes content inspection**: the glob runs first, and a
non-matching file is never opened. A perfectly correct closure record is
therefore not *rejected* — it is **never seen**, and collapses into a silent
`None` that is indistinguishable from "closure was never performed."

### Verified, reproducible impact in this workspace

Read-only probes executed 2026-09-17 against the committed tree
(`FilesystemTopologyReaders(Path('.')).closure_complete(...)`):

```text
162-S -> None      # docs/closure/2026-09-11-162-s-154-f-closure.md EXISTS and is correct
173-S -> True      # only because a second, ID-anchored artifact was hand-authored
161-S -> True      # legacy ID-anchored naming
160-S -> True      # legacy ID-anchored naming
174-S -> None      # docs/closure/2026-09-16-174-s-166-f-closure.md EXISTS and is correct
```

```text
$ autoharness gate pipeline-topology --mode manual --shipment 163-S --phase pre_claim --json
  "exit_code": 1, "blocked": true,
  "token": "PREDECESSOR_CLOSURE_INCOMPLETE",
  "message": "PREDECESSOR_CLOSURE_INCOMPLETE: predecessor 162-S is terminal but missing required closure evidence",
  "details": { "predecessor_source": "explicit",
               "predecessor_ids": ["162-S"], "closure_complete": null }
```

`.backlogit/archive/162-S.md` declares `status: archived`,
`archived_status: shipped`. `.backlogit/queue/163-S.md` declares
`dependencies: [162-S]`. Predecessor derivation is therefore **correct and
explicit** — `predecessor_source: "explicit"`, not numeric inference. The sole
cause of the block is that `closure_complete("162-S")` is `null`.

**This confirms the stash entry's central claim exactly: retiring numeric
predecessor inference does not unblock `163-S`; only this naming reconciliation
does.**

### Exact drift point

`docs/closure/` holds 54 files, of which 30 are shipment-scoped closure records:

* **ID-anchored (`{ID}-{FEAT}-post-merge-closure.md`)** — `134-S` … `161-S`
  (28 files, contiguous), plus `173-S`.
* **Date-prefixed (`{YYYY-MM-DD}-{id}-{feat}-closure.md`)** — `2026-09-06-159-s-151-f-closure.md`,
  `2026-09-11-162-s-154-f-closure.md`, `2026-09-14-173-s-165-f-closure.md`,
  `2026-09-16-174-s-166-f-closure.md`.
* **`162-S` is the first shipment closed under date-prefixed naming with no
  ID-anchored counterpart** (`159-S` and `173-S` have both; `162-S` and `174-S`
  have only the date-prefixed form).

The producer's convention changed at `162-S`; the consumer glob was never
updated. `173-S` was repaired by hand-authoring a **superseding** ID-anchored
artifact carrying `supersedes: docs/closure/2026-09-14-173-s-165-f-closure.md`.
That is the fourth instance of the per-artifact workaround this defect keeps
generating, and `174-S` has already reproduced the defect again.

### Why this is a class, not an incident

`docs/bugs/2026-09-06-closure-evidence-producer-consumer-contract-mismatch.md`
records the *same* defect in the sibling harness, repaired reactively **three
times** (`001-S` rename, `005-S` frontmatter, `008-S` rename + frontmatter)
before it was ever written up. Counting this workspace's `173-S` rename and the
live `162-S`/`174-S` instances, the class has now produced **six** occurrences
across two workspaces. Every repair targeted an artifact; none targeted the
contract.

### Success criteria

1. `closure_complete("162-S")` returns `True` from the committed tree with **no
   closure artifact created, renamed, or modified**, and
   `pipeline-topology --shipment 163-S --phase pre_claim` no longer emits
   `PREDECESSOR_CLOSURE_INCOMPLETE`.
2. The filename contract is stated in **exactly one** machine-readable place;
   both producer documentation and consumer code derive from it.
3. A non-conforming closure artifact fails at **write time**, when the author has
   full context — not at a successor shipment's pre-claim gate weeks later.
4. The three failure modes (absent / present-but-unrecognized-name /
   recognized-name-but-invalid-metadata) are **separately diagnosable**, and the
   unrecognized-name case names the candidate path it found and the pattern it
   expected.
5. A test drives the **documented producer path** into the **real consumer
   reader** and fails if either side changes alone.
6. The gate remains fail-closed. No predicate is relaxed.

### Explicit scope boundaries

**IN scope** — the naming contract and its enforcement:
single-source-of-truth contract module; consumer rewiring; discovery
diagnostics; write-time validation of path + required frontmatter keys;
producer-spec reconciliation (template + installed mirror, atomically); Ship
agent reference alignment; composed producer/consumer state-machine test; a
non-drift guard between the documented pattern and the code constant.

**OUT of scope** — explicitly excluded, and NOT to be absorbed:

* Any change to `_closure_artifact_complete`'s validity predicate. Requiring
  both `compaction_status` and `closure_status` is deliberate fail-closed
  behaviour and is preserved verbatim.
* Creating, renaming, editing, or deleting **any** file under `docs/closure/`.
  Zero closure artifacts change. In particular, authoring a competing
  ID-anchored record for `162-S` is **forbidden** — it would make the symptom
  disappear while leaving the contract broken, exactly as the previous five
  repairs did.
* A full canonical closure-artifact **writer** (generating body content and the
  complete frontmatter document). The contract module exposes a path builder and
  a validator; generating the artifact's prose remains the skill's job. Recorded
  as follow-up **OQ-1** and captured as deferred stash `AE612665`.
* Unification of the closure-evidence **frontmatter schema** into
  `schemas/`. Recorded as follow-up **OQ-2**.
* Adjacent closure-hygiene stash entries (`24E3E464`, `C395CFE3`, `0C094AED`,
  `63C5C305`, `5A537510`, `9E404C49`, `4702E1F6`, `71200CBB`). Each is about the
  *content* of a specific closure record. They stay in the stash, untouched.
* Stash entry `3EF5AAF2` (shipment-claim vs wave-admission contract conflict).
  Unrelated surface, capture-only, not triaged by this session.
* The `dag-readiness` / `pre_claim` divergence over closure evidence
  (`dag-readiness` reports `163-S` ready while `pre_claim` blocks it). Observed
  and recorded below as **OQ-3**; not repaired here.

## Research Findings

### Prior learning retrieved (Stage Step 1.8)

`docs/compound/2026-09-06-composed-workflow-protocol-state-machine-validation.md`
— confidence **high**, direct hit. Its "wider pattern" table names this exact
defect as row 2 of a recurring class, and its lessons are directly binding here:

* **Lesson 1 / 6** — validate protocols as a **composed state machine**; for
  every gate, name a concrete legitimate state that passes and one that fails.
  Applied below in the Decision's discovery-outcome table.
* **Lesson 3** — model the tool lifecycle explicitly; never assume a transition
  a component does not perform.
* **Lesson 4** — where one check applies a scoping rule, enumerate every sibling
  site that should also apply it. Applied: the contract module has an enumerated
  consumer list, and the non-drift guard enforces it.
* **Lesson 8, "One authoritative statement"** — *"State a class's valid /
  tolerated / halting statuses once; reference it everywhere else. Two
  independent restatements drift, and the drift stays invisible until a state
  arises that only one of them anticipated."* This is the generative cause of
  the present defect and is the direct basis for Decision **D1**.
* **Lesson 8, "Unrecognised is loud"** — every consumer of a vocabulary must
  fail closed **and loudly** on a value it does not recognise. Silent
  fall-through turns a vocabulary extension into an undetected behaviour change.
  This is the direct basis for Decision **D4** (the `None` that means
  "unrecognized name" must stop being indistinguishable from the `None` that
  means "absent").

The source bug report's acceptance criteria 1-7 are adopted as requirements,
with criteria 2 and the frontmatter half of 3 bounded per the scope fence above.

### Codebase facts established by inspection

* The consumer glob is a single expression at `topology.py:718`; nothing else in
  `src/` constructs or parses a closure filename. `grep` over `src/`, `tests/`,
  `templates/`, `.github/`, `schemas/`, `scripts/`, `build_support/` finds the
  ID-anchored pattern only in `topology.py`, in `tests/test_gates_topology.py`
  fixtures, and in the closure artifacts themselves.
* `src/autoharness/gates/` already hosts sibling contract modules
  (`shipment_closure.py`, `bootstrap_grant.py`, `sizing.py`), so a new
  `closure_contract.py` matches the established module shape and requires no
  architectural change.
* The CLI gate dispatcher (`src/autoharness/cli.py:369-389`) is a flat
  `if/elif` over subcommand names; adding `closure-evidence` is additive and
  touches no existing branch.
* `DOCS_CLOSURE` is an existing template variable with default `docs/closure`
  (`src/autoharness/verify_workspace.py:1976`), so the contract can be expressed
  relative to it without inventing a new variable.
* **Every existing topology closure test hand-writes a conforming fixture**
  (`tests/test_gates_topology.py:353, 371, 433` all use
  `114-S-2026-08-05-post-merge-closure.md`). This is precisely the anti-pattern
  the source report's criterion 6 calls out: such a test "would have passed
  throughout the entire history of this defect." It cannot detect producer
  drift, and never did.
* Precedent for the two-surface atomicity requirement: `165.010-T` was merged
  into `165.008-T` specifically so that template source and installed dogfood
  mirror land **in one commit**, closing a wrong-contract-window risk. The same
  constraint applies to the producer-spec change here.

### Sequencing facts established by inspection

* `autoharness gate dag-readiness --json` reports `cycle_detected: false`,
  `ready_set: ["163-S"]`, `next_eligible: "163-S"`.
* `_predecessor_source` (`topology.py:1577-1582`) resolves to `explicit` when
  blocking edges exist, `declared_root` when the record carries the
  **`dag-root`** label (`topology.py:102-103`), `genesis` when it is the sole
  physical shipment record, else **`unsequenced`**.
* `unsequenced` shipments are **excluded from `ready_set` entirely** and are
  blocked at `pre_claim` with `UNSEQUENCED_SHIPMENT`. `169-S` is a live example:
  no dependencies, no `dag-root` label, therefore not claim-eligible.
* The gate itself enumerates exactly two truthful remediations
  (`_SEQUENCING_REMEDIATION_OPTIONS`, `topology.py:1543-1546`): *"record the real
  blocks edge"* or *"declare the shipment a root"*.
* `dag-root` has established, reviewed precedent in this workspace:
  `.backlogit/archive/173-S.md:22` and `.backlogit/archive/174-S.md:18`.

## Options Evaluated

> **Non-binding historical analysis.** This section, `## Trade-off Comparison`,
> and `## Rejected Alternatives` record how the decision was reached. They are
> **superseded by the `## Decision` section**, which is the only binding output
> of this deliberation. Where an option sketch below differs in detail from
> D1-D9, **D1-D9 govern**.

### Option A — Widen the consumer glob only

Extend `closure_complete`'s discovery to also match the date-prefixed shape;
change nothing else.

* **Pros**: smallest diff; unblocks `162-S`/`174-S` immediately; touches no
  closure artifact; no producer change.
* **Cons**: leaves **two** independently-stated contracts, which is the
  generative cause the compound learning names explicitly — the next producer
  convention change drifts again, silently. No write-time validation, so a
  malformed name is still discovered weeks later at a successor's gate. No
  composed test, so the pair can still diverge unnoticed. Matching
  `2026-09-11-162-s-154-f-closure.md` for shipment `162-S` requires
  case-insensitive, delimiter-anchored ID matching inside the filename; done as
  a loose glob this risks `16-S` matching `162-S`'s record. Silent-`None`
  diagnostic ambiguity persists.
* **Effort**: low. **Fit**: fails success criteria 2, 3, 4, 5.

### Option B — Change the producer back to the consumer's pattern only

Revert `operational-closure`'s documented output to
`{shipment_id}-{feature_id}-post-merge-closure.md`; change no code.

* **Pros**: zero code risk; preserves all 28 historical ID-anchored artifacts;
  restores a single de facto pattern going forward.
* **Cons**: **does not unblock `163-S`.** `162-S` and `174-S` are already
  committed under date-prefixed names, and the scope fence forbids renaming them
  or authoring competing records — so the consumer would still return `None` for
  both. Still two independent restatements of the pattern (prose in a skill, a
  glob in Python) with nothing tying them together. No write-time validation, no
  diagnostics, no composed test. Discards the date-ordering property the newer
  convention was adopted for without ever recording why.
* **Effort**: very low. **Fit**: fails success criteria 1, 2, 3, 4, 5.

### Option C — Single authoritative contract in code, asymmetric write/read, enforced at write time and pinned by a composed test *(recommended)*

1. A new module `src/autoharness/gates/closure_contract.py` is the **sole**
   definition of closure-evidence naming: one **canonical WRITE pattern**, one
   **closed, explicitly enumerated set of RECOGNIZED READ patterns**, a path
   builder, an anchored filename matcher, and deterministic multi-match rules.
2. `topology.py::closure_complete` is rewired to consume that module and to
   return a **structured discovery outcome** rather than a bare tri-state, so
   absent / unrecognized-name / invalid-metadata become separately reportable.
3. `_shipment_readiness_check` surfaces the distinction in its gate token and
   `details`, naming the candidate path found and the pattern expected.
4. `autoharness gate closure-evidence` validates a closure artifact's path and
   required frontmatter keys at **write time**, and the producer skill is
   required to invoke it.
5. The producer spec (`templates/skills/operational-closure/SKILL.md.tmpl` and
   the installed `.github/skills/operational-closure/SKILL.md`) is reconciled to
   the canonical pattern **in one atomic change**, and the Ship agent template +
   installed mirror are aligned the same way.
6. A **composed producer/consumer state-machine test** drives the documented
   producer path's constructed filename into the real consumer reader, using
   temporary fixtures only, plus regression coverage for each historical
   failure shape.
7. A **non-drift guard** asserts the pattern text documented in the skill files
   equals the constant in the contract module, so prose and code cannot diverge.

* **Pros**: satisfies every success criterion; kills the defect class rather
  than the instance; unblocks `162-S`/`174-S` without touching a single closure
  artifact; keeps the gate fail-closed (the recognized-read set is a **closed
  enumeration**, never a wildcard); makes the next producer convention change a
  deliberate, single-site, test-enforced edit.
* **Cons**: largest surface — a new module, a rewired fail-closed gate, a new
  CLI subcommand, two template families, and a new test class. Requires
  `plan-harden`. Introduces an asymmetry (write one pattern, read several) that
  must be documented precisely or it will itself become the next ambiguity.
* **Effort**: medium-high (**12 bounded tasks** in the reviewed plan; estimated
  as 8 during deliberation, before planning split the path builder, the
  write-time validator's semantic battery, and the regression battery into
  separately bounded units). **Fit**: full.

## Trade-off Comparison

| Criterion | Option A (widen glob) | Option B (revert producer) | **Option C (contract module)** |
|---|---|---|---|
| Unblocks `163-S` without touching closure artifacts | Yes | **No** | **Yes** |
| Unblocks `174-S`'s future dependents | Yes | No | **Yes** |
| Single source of truth (criterion 2) | No | No | **Yes** |
| Write-time validation (criterion 3) | No | No | **Yes** |
| Distinguishable diagnostics (criterion 4) | No | No | **Yes** |
| Composed producer/consumer test (criterion 5) | No | No | **Yes** |
| Gate stays fail-closed (criterion 6) | Risk: loose glob broadens discovery | Yes | **Yes — closed enumeration** |
| Prevents the 7th recurrence | No | No | **Yes** |
| Blast radius | Very low | Very low | Medium-high |
| Requires plan hardening | No | No | **Yes** |

## Decision

**Option C is adopted.** The following decisions are binding on the plan.

### D1 — One authoritative definition, in code, with an enumerated consumer list

The closure-evidence naming contract is defined **exactly once**, in
`src/autoharness/gates/closure_contract.py`. Producer documentation and consumer
code both derive from it. This directly applies the compound learning's "One
authoritative statement" rule, whose violation generated this defect.

The module carries an explicit, in-source **enumerated list of its consumer
sites** (the topology reader, the validation CLI, the producer skill files, the
Ship agent files). Adding a consumer without adding it to that list is a defect
the non-drift guard must catch. *(Compound lesson 4.)*

### D2 — Canonical WRITE pattern: ID-anchored

The single pattern any **new** closure artifact may be written under is:

```text
{DOCS_CLOSURE}/{shipment_id}-{feature_id}-post-merge-closure.md
```

Rationale, in order of weight:

1. **Discovery is by shipment ID.** An ID-anchored prefix makes lookup
   deterministic and unambiguous. A date-anchored name forces an ID search
   inside the filename, which is what introduces the `16-S`/`162-S` prefix
   hazard.
2. **The corpus already conforms.** 29 of 30 shipment-scoped closure records
   carry this shape.
3. **The repository already converged here de facto.** When `173-S` had to be
   made discoverable, the chosen repair was to author the ID-anchored name and
   point `supersedes:` at the date-prefixed one — not the reverse.
4. **Case-stability.** The date-prefixed corpus lowercases the shipment ID
   (`162-s`), which is a case-sensitivity hazard on non-Windows filesystems. The
   canonical form preserves the ID's declared case.

The closure **date** is not lost: it is carried in the artifact's frontmatter,
which is machine-readable and already parsed, rather than in the filename, which
is not.

### D3 — RECOGNIZED READ set: permanent, closed, and explicitly enumerated

This resolves the stash entry's open question **(b)** — permanent recognition or
transitional?

**Permanent, for read only.** The recognized-read set is:

| # | Pattern | Identifier match rule | Purpose |
|---|---|---|---|
| R1 | `{shipment_id}-{feature_id}-post-merge-closure.md`, both identifiers **uppercase-only** and composed from the write grammars | **exact, case-sensitive** whole-captured-group equality | canonical (also the write pattern) |
| R2 | `{YYYY-MM-DD}-{shipment_id}-{suffix}-closure.md`, shipment kind letter `[Ss]`, suffix free-form | **case-folded** whole-captured-group equality | legacy date-prefixed corpus (`162-S`, `174-S`, `159-S`, `173-S`) |

**There is exactly one canonical identifier domain.** The write grammars are
uppercase-only and case-sensitive, and R1 is composed from them, so R1's
accepted domain and the path builder's accepted domain are the same set in
**both** directions. **Lowercase tolerance exists only in R2**, because the
legacy corpus lowercases identifiers (`2026-09-11-162-s-154-f-closure.md`). No
claim of domain coincidence is made for R2 in either direction; the only
cross-pattern property asserted for it is one-directional and structurally
provable — **no builder output can ever match R2**, because R2's second
hyphen-delimited token must satisfy `\d{2}` while a builder name's second token
is the literal kind letter.

Reasons the read set is permanent rather than transitional:

* Committed closure evidence is **immutable historical record**. A transitional
  window would mean the corpus must eventually be rewritten — which is precisely
  the per-artifact remedy this decision exists to end, and which the source bug
  report lists as a non-goal.
* `162-S` and `174-S` can be unblocked **only** by recognition. Any other route
  requires creating or renaming an artifact, which the scope fence forbids.

Reasons this does **not** weaken the gate:

* The set is a **closed enumeration of two anchored regexes**, not a widened
  wildcard. An unrecognized name is still not evidence, and still blocks.
* The **write** contract stays singular. Recognition is read-side tolerance of
  history; it never authorizes writing R2.
* Candidate attribution **parses the shipment identifier from the position the
  anchored grammar reserves for it** — immediately after the date prefix for R2,
  leading for R1 — and compares that single parsed group. The requested
  identifier is never searched for elsewhere in a filename, and in particular
  never inside an R2 free-form suffix, so neither `16-S` nor `162-S` can be
  attributed to the other's record in either direction, and a foreign record
  whose suffix happens to contain the requested token is not attributed at all.
* The validity predicate `_closure_artifact_complete` is untouched. A recognized
  filename still must carry passing `compaction_status` **and** `closure_status`.

**Composed-state-machine check (compound lesson 6) — a legitimate state that
passes and a legitimate state that fails, named concretely for every outcome:**

| Discovery outcome | A concrete legitimate state | Gate result |
|---|---|---|
| Canonical match, valid | `161-S-153-F-post-merge-closure.md` | PASS |
| Legacy match, valid | `2026-09-11-162-s-154-f-closure.md` | PASS *(new; today it silently fails)* |
| Both present, both valid | `173-S` (`173-S-165-F-post-merge-closure.md` + `2026-09-14-173-s-165-f-closure.md`) | PASS, canonical wins |
| No candidate at all | any shipment with an empty `docs/closure/` | BLOCK — **absent** |
| Candidate present, name unrecognized | a file named `162-S-notes.md` | BLOCK — **unrecognized name**, path + expected pattern reported |
| Recognized name, `closure_status: BLOCKED` | pre-repair `2026-09-14-173-s-165-f-closure.md` | BLOCK — **invalid metadata** |
| Recognized name, malformed frontmatter | — | raise → `BACKLOG_UNAVAILABLE` *(unchanged)* |

Every row names a real or constructible state. No gate row is unreachable.

### D4 — Discovery outcomes are distinguishable; unrecognized is loud

`closure_complete`'s bare `bool | None` conflates "no closure exists" with "a
closure exists but I could not see it" — and the compound learning's
"Unrecognised is loud" rule makes that conflation the defect's real damage. The
reader returns a structured outcome; the gate reports:

* `PREDECESSOR_CLOSURE_INCOMPLETE` — genuinely absent (token preserved, so no
  existing consumer of the token breaks).
* `PREDECESSOR_CLOSURE_UNRECOGNIZED` — one or more candidate files exist in the
  closure directory for this shipment but match no recognized pattern. The
  message and `details` **name the candidate path(s) found and the canonical
  pattern expected**. This is the single most actionable change in the fix: it
  converts six occurrences' worth of silent misdiagnosis into a one-line answer.
* `PREDECESSOR_CLOSURE_INCOMPLETE` — recognized but the validity predicate
  failed (existing behaviour, unchanged).

`details.closure_complete` is retained for backward compatibility; new fields
are added alongside it.

### D5 — Deterministic multi-match resolution

Given a shipment ID, discovery resolves to exactly one effective verdict:

1. Partition candidates into canonical (R1) and legacy (R2).
2. If any canonical candidate exists, legacy candidates are **ignored for the
   verdict** (they are still reported in `details` for transparency). This makes
   the `supersedes:` repair already applied to `173-S` behave correctly without
   the reader needing to interpret supersession chains.
3. Within a partition, evaluate candidates in a deterministic sorted order and
   accept on the first that satisfies the unchanged validity predicate —
   preserving today's "any valid match wins" semantics exactly.
4. Zero candidates in both partitions → **absent**.
5. Candidate files exist for the shipment but match neither pattern →
   **unrecognized**.

### D6 — Write-time validation, invoked by the producer

`autoharness gate closure-evidence --path <file> [--shipment <id>]
[--workspace <path>] [--json]` validates (a) the filename against the canonical
write pattern, (b) that the artifact's frontmatter satisfies the **complete
consumer acceptance predicate** — not a scalar key/enum check — and (c) that the
artifact is discoverable for its declared shipment. It exits non-zero on any
failure.

**(b) is binding in its complete form.** A scalar-only formulation — checking
only "the presence and permitted values of the required frontmatter keys
`closure_status` and `compaction_status`" — is **rejected**: it accepts a
`closure_status: READY_WITH_CONDITIONS` artifact whose `conditions:` block is
absent or unsatisfied, which the consumer rejects. That is a second, weaker
definition of validity for the same contract, which is precisely the generative
failure this feature exists to remove. The write-time gate MUST therefore accept
an artifact **if and only if** the read-time consumer would accept it, which
means (b) covers the whole predicate:

* `compaction_status` present, a string, and — after stripping and case-folding
  — one of `done` / `degraded`; including the consumer's **legacy `compaction:`
  alias** fallback, because rejecting an alias the consumer honours is itself a
  divergent second definition;
* `closure_status` present, a string, and non-blank;
* `closure_status: READY` accepted;
* `closure_status: READY_WITH_CONDITIONS` accepted **only** when the
  `conditions:` block is a **non-empty list**, every entry is a mapping, every
  entry's `satisfied` is the **literal boolean `True`** (not a truthy string),
  and every entry's `evidence` is a non-empty string;
* every other `closure_status` value, including `BLOCKED`, rejected.

**The predicate itself is not changed by this decision.** The gate reuses the
consumer's existing `_closure_artifact_complete` / `_closure_conditions_satisfied`
**by import**, leaving them byte-identical; this decision specifies *what the
gate must check*, not a new or altered rule. Equivalence is proven across every
branch enumerated above rather than at a single sampled point.

**Diagnostic granularity follows from that reuse.** The authoritative predicate
returns a **boolean**: it reports whether an artifact is acceptable, not why it
was refused. A field- or reason-specific explanation of a frontmatter rejection
could therefore only be produced by a second implementation of the validity
logic — the exact defect this decision removes. The gate's diagnostics are
consequently partitioned by ownership:

* checks the gate itself owns — filename pattern (a), discoverability (c), and
  an absent, unreadable, or unparseable `--path` — emit **specific** messages
  naming the offending filename, shipment, or path;
* the frontmatter check (b) emits a **generic authoritative-predicate
  rejection**: it names the artifact path, names the deciding predicate, and
  quotes a single contract-owned summary of the predicate's documented
  requirements, without asserting which field or which condition failed.

This is the minimal-scope resolution and is binding. Introducing a structured
validator that reports per-field reasons would be a widening of this decision,
not an implementation detail of it, and would require a new deliberation.

The producer skill is amended to require this invocation before the closure
artifact is committed. This satisfies criterion 3 and moves failure from a
successor's gate back to the author's keyboard.

### D7 — Composed test is mandatory and must be real

A hand-written conforming fixture **does not satisfy** this decision; such a
test would have passed throughout the entire six-occurrence history of this
defect. The composed test must construct the canonical closure filename
**through the contract module's path builder as the producer documentation
directs**, feed the result to the **real**
`FilesystemTopologyReaders.closure_complete`, and assert acceptance — so that
changing either side alone breaks it.

**Fixture provenance.** The composed test's fixtures are built into a
**temporary scratch workspace**. Durable tests do **not** assert against the
committed `docs/closure/` corpus: that couples the normal suite to mutable
repository history which unrelated shipments continue to archive, rename, and
extend, and it is unsatisfiable as written —
`docs/closure/138-S-129-F-cancellation-closure.md` matches neither recognized
pattern. The non-simulatable proof that `closure_complete("162-S")` and
`closure_complete("174-S")` are `True` against the real corpus is **retained**,
but as **one-time publication/runtime evidence** captured at execution time into
this work's post-merge closure artifact, which is where point-in-time proof
belongs.

**Explicit legacy-shape exception.** The construction rule binds the
**canonical** half of the contract only, because the canonical builder cannot
emit an R2 name — by D3 no builder output can ever match R2. Requiring a
builder-created legacy fixture would therefore be an unsatisfiable demand.
Instead:

* **R1 (canonical) fixture names MUST come from the path builder.** A
  hand-written canonical literal remains a defect.
* **R2 (legacy) fixture names come from exactly one dedicated, test-only legacy
  filename helper**, defined once in the test tree, never part of the contract
  module, and never imported by production code.

Both halves remain temporary fixtures in scratch workspaces; no durable test
reads or writes `docs/closure/`.

### D8 — Zero closure artifacts are modified

No file under `docs/closure/` is created, renamed, edited, or deleted by this
work. This is an **invariant**, asserted by the plan's verification step, not an
aspiration. It is the difference between fixing the contract and performing the
per-artifact workaround for the seventh time.

### D9 — Sequencing: the fix's shipment is a declared DAG root; `163-S` waits on it

The shipment carrying this fix declares itself a **root** by carrying the
`dag-root` label, and `163-S` gains an explicit `blocks` edge on it.

**Why `dag-root` is the truthful declaration, not a convenience:**

* The gate itself offers exactly two remediations for a shipment with no blocks
  edge: record the real edge, or declare it a root. There is no real blocking
  edge to record — this work depends on **no queued shipment**. Its natural
  chronological neighbour `174-S` is already `archived` / `shipped`, i.e.
  terminal, i.e. not a blocker.
* Manufacturing an explicit edge on `174-S` would be **actively wrong and
  self-defeating**: `closure_complete("174-S")` is `None` *because of the very
  defect under repair*, so the fix's own shipment would be blocked by the bug it
  exists to fix — a bootstrap deadlock created by a false declaration.
* Leaving it unlabelled yields `unsequenced` (19 live shipment records exist, so
  `genesis` cannot apply), which is excluded from `ready_set` and blocked at
  `pre_claim` with `UNSEQUENCED_SHIPMENT` — the outcome the operator explicitly
  requires this session to avoid.
* Precedent is established and reviewed: `173-S` and `174-S` both shipped
  carrying `dag-root`.

**Why `163-S` must wait**, rather than simply being unblocked: `163-S` cannot
pass `pre_claim` until `162-S`'s closure becomes visible, and that visibility is
*produced by this fix*. Recording `163-S → blocks → {this shipment}` makes the
real execution order explicit and machine-checked, instead of leaving a human to
remember it. It also repairs the secondary gap the workspace has already
suffered: dependents queued without declaring a blocking edge on the correction
they actually need.

**No `blocked` shipment status is invented.** `163-S` remains `queued`. The wait
is expressed purely as a backlogit-native `blocks` dependency edge, which is
what the topology gate already reads.

**Bootstrap note (recorded deliberately):** this fix's own closure artifact will
be written *after* the fix merges, so the merged contract governs it. Under D3
it is discoverable whether Ship writes R1 or R2 — so `163-S`'s new edge cannot
deadlock on the same defect. Had the read set been transitional or
canonical-only, this would have been a live deadlock risk; it is called out here
so the reasoning survives.

## Rejected Alternatives

* **Option A (widen the glob)** — rejected: it repairs the symptom while
  preserving the exact structure that generated it. Two independent restatements
  of one pattern is the generative cause named in the compound learning; leaving
  them in place guarantees a seventh occurrence at the next convention change.
* **Option B (revert the producer)** — rejected: it does not even fix the
  symptom. `162-S` and `174-S` stay undiscoverable, so `163-S` stays blocked,
  unless closure artifacts are rewritten — which the scope fence forbids.
* **Author a competing ID-anchored closure record for `162-S`** — rejected and
  explicitly forbidden by the stash entry. It is the sixth instance of the
  workaround, it makes the blocker vanish without fixing anything, and it
  pollutes the closure corpus with duplicate records.
* **Relax or bypass the closure gate to unblock `163-S`** — rejected. Closure
  evidence must remain a fail-closed requirement. The compound learning's
  second-order-damage section is explicit that each gate override manufactures
  precedent for the next one.
* **Make legacy recognition transitional with a deprecation window** — rejected.
  A window implies eventually rewriting committed history, which is the
  per-artifact remedy under a longer name. Read-side recognition is permanent;
  write-side canonicity is singular. That asymmetry is the decision.
* **Fold this into `165-F` / `173-S`** — rejected; already settled. `FD0CCB42`
  holds exclusive ownership of this surface per decision D4 of the DAG
  deliberation. `173-S` shipped with every closure
  cell removed, including read-only reuse, precisely so this work is free to
  redefine the surface without negotiating with an installed dependent.

## Unresolved Questions

| ID | Question | Disposition |
|---|---|---|
| **OQ-1** | Should Ship emit closure artifacts through a full canonical **writer** (path *and* body *and* frontmatter generated from the shared definition), per the source report's criterion 2? | **Deferred, out of scope.** This decision delivers a path builder and a validator, which closes the naming axis. A full writer is a content-generation surface with its own design space. **Captured as deferred stash entry `AE612665`** under P-021 C1, `REQUIRES DELIBERATION: yes`, after an unconditional duplicate scan returned `DISCOVERY-STATUS: CLEAN`. |
| **OQ-2** | Should the closure-evidence **frontmatter schema** move into `schemas/` as a versioned JSON schema alongside the other seven? | **Deferred, out of scope.** The metadata axis is currently satisfied (all live artifacts carry valid keys). Bundling schema work would cross into schema evolution and materially widen blast radius. |
| **OQ-3** | `dag-readiness` reports `163-S` in `ready_set` while `pre_claim` blocks it, because the advisory view does not consult closure evidence. Should the advisory view be closure-aware? | **Observed, not repaired here.** Recorded as a real divergence. `165.004-T` already flagged it as a motivating divergence; touching it would re-import a surface `173-S` was deliberately cleared of. |
| **OQ-4** | Should `PREDECESSOR_CLOSURE_UNRECOGNIZED` be a **blocking** token or a **warning** when a valid legacy artifact also exists? | **Resolved by D5**: recognition is attempted first; `UNRECOGNIZED` is emitted only when *no* recognized candidate exists, so it is unambiguously blocking. Recorded here because it was a live ambiguity during deliberation. |
| **OQ-5** | Does any downstream tool parse the closure filename for its date? | **Checked, none found.** `grep` across `src/`, `tests/`, `scripts/`, `build_support/` finds no date extraction from closure filenames. If one is added later, the contract module is the place it must read from. |

## Risks and Mitigations

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Widening read recognition silently weakens a fail-closed gate | Medium | **High** | Read set is a **closed enumeration of two anchored regexes**, never a wildcard. `_closure_artifact_complete` is byte-unchanged. Regression tests assert an unrecognized name still blocks and that `closure_status: BLOCKED` still fails. Plan-harden must re-verify this specifically. |
| R2 | R2's in-filename ID match false-positives across shipments (`16-S` vs `162-S`) | Medium | High | Fully-anchored, full-filename regexes with whole-captured-group comparison — never a substring or loose glob. Candidate attribution additionally **parses the identifier at the position the grammar reserves for it** and compares that single parsed group, so a requested token appearing in a foreign record's free-form suffix is never attributed. A dedicated bidirectional adversarial test asserts `16-S` does not match `162-S`'s artifact and vice versa, in primary positions and in foreign suffixes. |
| R3 | Rewiring a fail-closed gate regresses `BACKLOG_UNAVAILABLE` on malformed frontmatter into a silent skip | Low | **High** | Explicit non-goal, carried from the source report. `_frontmatter`'s raise path is untouched; a regression test asserts malformed frontmatter still raises. |
| R4 | Template and installed dogfood mirror land in separate commits, opening a wrong-contract window | Medium | Medium | Producer-spec change is **one atomic task** covering `.tmpl` + installed mirror, per the `165.008-T`/`165.010-T` precedent. Same rule for the Ship agent pair. |
| R5 | The composed test degenerates into another hand-written fixture and pins nothing | Medium | **High** | D7 makes the construction path binding for the canonical half: the canonical filename must come from the contract module's builder, so a hand-written canonical literal cannot satisfy the test. The legacy half — which the builder cannot emit by construction — comes from one dedicated, test-only legacy filename helper whose non-builder provenance is explicit. **All durable fixtures are temporary**, written to scratch workspaces; no durable test reads `docs/closure/`. The real-corpus proof for `162-S`/`174-S` is retained as **one-time publication/runtime evidence** captured into this work's closure artifact, not as a durable assertion. Called out as a mandatory plan-review check. |
| R6 | Scope creep into closure artifact content, frontmatter schema, or adjacent stash entries | Medium | Medium | D8 (zero artifact modifications, verified) plus the explicit OUT-of-scope list plus named excluded stash IDs. Plan-review must verify no task touches `docs/closure/`. |
| R7 | The new `blocks` edge on `163-S` introduces a cycle or an unsatisfiable wait | Low | High | The fix's shipment is `dag-root` with **no outgoing** blocks edges, so no cycle is topologically possible. Validated by re-running `dag-readiness` (`cycle_detected` must stay `false`) after the edge is added. D9's bootstrap note establishes the wait is satisfiable. |
| R8 | A future producer convention change drifts again | Medium | High | The non-drift guard asserts the documented pattern text equals the contract constant, so the change fails CI unless made at the single source. |
| R9 | New CLI subcommand regresses existing gate dispatch | Low | Medium | Dispatch is a flat `if/elif`; the change is additive. Existing gate CLI tests must pass unchanged. |

## Promotion

`promote_to: plan` — handed to `impl-plan` with this artifact as `source`.
Produced plan: `docs/plans/2026-09-17-closure-evidence-naming-contract-plan.md`.
