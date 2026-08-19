# Stage Session — B48A482A → 143-S (P-021 Bounded Fix-Cycle Scope Containment)

| Field | Value |
|---|---|
| Date | 2026-08-18 |
| Agent | Stage |
| Route | `claude-opus-5` / `anthropic` / `high` |
| Mode | Normal sequential (NOT dark factory) |
| Source stash | `B48A482A` |
| Deliberation | `019-DL` |
| Feature | `134-F` |
| Tasks | `134.001-T` … `134.011-T` |
| Shipment | **`143-S`** (queued) |
| Review verdict | **PASS** (1 cycle, 2 P1 findings applied) |

## Session start state

* Backlogit v1.9.0-39 at `.backlogit`; index synced (`869` indexed).
* No queued or active shipments before this session (all prior shipments `done`,
  `138-S` `abandoned`).
* Checkpoint enumeration: 35 records, zero validation/quarantine anomalies, zero
  active `stage`-owned recovery candidates → zero-candidate normal startup.
* One worktree, `main` @ `62a8fb2`.
* `agent-intercom` configured but unavailable → `INTERCOM_DEGRADED`; local
  operator-visible reporting used, no approval bypass for destructive actions.

## Pipeline executed

1. **Triage** — `B48A482A` is feature-shaped (`kind: feature`), intake-only,
   explicitly flagged as requiring mandatory deliberation/research. Single-entry
   target → Step 1.5 grouping skipped (feature-shaped entries bypass grouping).
2. **Learnings retrieval** — direct high-confidence hit in `docs/compound/`:
   `2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`
   (PR #348). It supplies the "same contract surface vs. same file" test and the
   reply/resolve/disclose closure pattern. Promoted from advisory prose to
   normative policy by this feature.
3. **Deliberation** — `019-DL`. Four options; chose a new named policy P-021
   carried across all coherent surfaces.
4. **Plan** — `docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-plan.md`.
5. **Hardening (P-006, required)** —
   `docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-hardening.md`,
   13 items (H1–H13), verdict PROCEED, all folded into task acceptance criteria.
6. **Review (plan-review gate)** —
   `docs/reviews/2026-08-18-bounded-fix-cycle-scope-containment-review.md`,
   verdict **PASS**. R1 (canonical unittest gate invocation) and R2 (missing
   CHANGELOG obligation) applied to the plan; R3 applied to the backlog;
   R4/R5/R6 accepted and disclosed.
7. **Harvest** — feature `134-F` + 11 tasks, all sized and complexity-rated,
   dependency edges enumerated discretely.
8. **Shipment** — `143-S`, 12 members, verified: `histogram {M:8, S:3}`,
   `unsized: 0`, `skipped: []`, covering feature `134-F`.

## Key findings worth remembering

* **Latent P-010 contradiction in the Ship template.** `_ship.agent.md.tmpl`
  line 38 lists "stash operations" in Ship's **Forbidden** column, while Ship
  pre-merge Step 9 and post-merge Step 6 **already require** Ship to create stash
  entries, and `role-enforcement.instructions.md` mandates a fail-closed halt +
  P-010 violation on any forbidden-column operation. Tasks `134.002-T` /
  `134.003-T` repair it as a narrow, enumerated capture-only carve-out. These are
  load-bearing: without them the rest of the feature would mandate a violation.
* **Dogfood coupling is a three-part atomic unit.** Template edit + byte-identical
  LF-normalized re-render + manifest checksum refresh (`git cat-file -p :<path>
  | sha256`, 115-S procedure) + manifest `note:` provenance. 8 dogfood artifacts
  are touched. `tests/test_circuit_breaker_policy_contract.py` enforces byte
  identity and checksum match.
* **`workflow-policies.md.tmpl` is template-only** — `.github/policies/` does not
  exist. Same for `pr-lifecycle` / `fix-ci` skills (`.github/skills/` holds only
  the four global skills).
* **Pre-existing staleness found:** `HARNESS_ENFORCED_SUMMARY` reads "P-001
  through P-019" although P-020 shipped. Bumping to P-021 also fixes it; carried
  as a disclosed mechanical consequence (task `134.010-T`, hardening H10).
* **Canonical gate is `unittest`, not root `pytest`** —
  `$env:PYTHONPATH='src'; python -m unittest discover -s tests`
  (`docs/compound/097-S-canonical-unittest-gate.md`).

## Handoff to Ship

* Claim **`143-S`**. Execute `134.001-T` first (it is the sole upstream dependency
  of every carrier surface).
* **Serialization (H4):** `134.002-T` and `134.004-T` both edit
  `_ship.agent.md.tmpl`, its dogfood, and the same manifest checksum line. Run 002
  fully (including checksum refresh) before 004; 004 must recompute from the
  post-002 blob.
* **H13 — working-tree hygiene:** unrelated operator changes are staged
  (`.gitmodules`, `references/skillopt`, `references/waza`, `references/witr`).
  Every commit MUST stage an explicit enumerated path list. `git add -A`,
  `git add .`, and `git commit -a` are prohibited for this shipment. Verify with
  `git --no-pager diff --cached --name-only` before each commit.

## Not done by Stage (deliberately)

* No source, template, or config file was modified. Only planning artifacts
  (`docs/plans/`, `docs/reviews/`, `docs/memory/`) and backlogit-managed files.
* Shipment `143-S` left `queued` — **not claimed**. Ship owns claiming.
* `B48A482A` **not archived/removed**. It carries a `[CONSUMED …]` forward
  reference to `019-DL` / `134-F` / `143-S`, and `134-F` carries
  `custom_fields.source_stash_id=B48A482A` +
  `source_deliberation_id=019-DL`. Retirement is Ship's post-merge Step 7
  source-artifact cleanup — the repository's established mechanism. Stage did not
  perform the destructive `stash_remove` because `agent-intercom` was unavailable
  and destructive backlog operations require operator clearance in degraded mode.
* Pre-existing backlogit doctor legacy orphan / self-reference findings were left
  untouched, per operator direction — and consistent with P-021 itself.

## Staging-gate corrections (2026-08-18, post-`474a1438`)

Local staging-PR readiness review of the committed staging HEAD `474a1438`
(local `main`, remote `chore/stage-143-S`) surfaced two findings. Both were
corrected by Stage and left **uncommitted** for the Orchestrator staging gate.

### P1 (blocking) — `134.006-T` sequenced reply before capture

`.backlogit/queue/134.006-T.md` specified the out-of-scope disposition as
*(a) thread reply → (b) capture → (c) resolve → (d) residual-risk record*, and
did not require the reply to cite the generated deferred expansion ID. That
contradicted two clauses of the very policy the task authors:

* **C2** — "Capture is a precondition for closing the finding." A reply-first
  ordering closes the finding before the precondition exists.
* **C3** — "reference the deferred entry ID in the review-thread reply." A reply
  authored before capture cannot cite an ID that has not been generated yet.

It also diverged from `134.004-T`, which already carried the correct
capture-first ordering for the Ship agent surface — so the shipment would have
authored two contradictory orderings for the same policy.

**Correction applied.** Acceptance criteria now mandate capture-first:
C2 capture (full payload) → substantive reply citing the generated deferred
entry ID → thread resolution → PR residual-risk record naming the same ID.
Three criteria were added: an explicit prohibition on replying/resolving before
the capture exists, an explicit consistency constraint against `134.004-T`, and
the C5 provisional-priority / Stage-only-triage bound that `134.004-T` already
carried. Implementation notes record the defect and require the template text to
mirror `134.004-T` so the two surfaces cannot drift. A comment event was appended
to the item history for traceability.

### P2 — missing docline frontmatter on three planning artifacts

The plan, hardening, and review artifacts were authored without YAML
frontmatter, failing the docline base contract on required fields `title`,
`source`, and `doc_type`. Conforming frontmatter was added following the
`2026-08-17-backlogit-self-migration` triad precedent (`doc_type: plan` for both
plan and hardening; `doc_type: review` for the review; `source` = the doc's own
repo-relative path), plus the repository's customary `description`, `status`,
`date`, `stash_source`, `deliberation`, `feature`, `shipment`, `route` and
verdict/count fields. Document bodies were not otherwise altered.

**Validation.** `backlogit docs lint --path <file>` (default `authoring`
profile) returns **OK (0 violations)** for all three, exit `0`. The linter
enforces a closed `doc_type` vocabulary — `plan` and `review` are both members.

### Deferred, not fixed (P-021 discipline applied to this session)

* The `ingestion` profile additionally requires `ingested_at`. That field is
  absent from **every** authored doc in this repository, including the
  conforming `2026-08-17` precedent — it is populated by the ingestion pipeline,
  not at authoring time. Not a regression introduced here; not in scope.
* `docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md` has
  malformed YAML frontmatter (an unquoted scalar containing a colon-space
  sequence in `blast_radius:`) that makes the **workspace-wide**
  `backlogit docs lint` abort
  with a decode error and emit no report. This is a pre-existing defect in an
  unrelated file. Per P-021 C1 it is out of scope for this correction pass, so
  per-file `--path` targeting was used instead. Captured as deferred stash entry
  **`395EBE60`** (`kind: bug`, `priority: medium`, `requires deliberation: yes`)
  rather than silently fixed.

## Follow-up candidates (not carried)

1. Deterministic `autoharness gate scope-containment` — no reliable machine
   signal today; possible telemetry-based detection comparing the touched-file
   set against the plan's declared file map.
2. Structured backlogit `custom_fields.deferred_scope_expansion` field instead of
   a free-text marker (belongs to the `backlogit` product; width isolation).
3. Broader Orchestrator fix-cycle routing semantics beyond the dark-mode
   non-bypass clause.

## Staging-readiness remediation (2026-08-19, post-`ed345cb5`)

The 2026-08-18 staging gate ran three review-fix cycles and tripped the
circuit breaker with unresolved P1 findings (`docs/memory/2026-08-18/
circuit-break-stage-pr-readiness.md`, preserved unchanged as historical
evidence apart from the addition of a required top-level heading). The
operator then authorized one fresh bounded Stage remediation operation. This
section records that operation. Ship was still not invoked; shipment `143-S`
remains `queued`.

**Checkpoint recovery.** Stage-owned checkpoint
`checkpoint-20260819-033817.json` (`phase: staging-readiness-blocked`,
`shipment 143-S`, `feature 134-F`, `branch chore/stage-143-S`) validated
`valid: true` with `agent: stage`, so the ownership gate passed. Engram was
reachable (`engram.exe` v0.2.0, daemon PID live, workspace bound to
`D:\Source\GitHub\autoharness`, `stale_files: false`), so the restore →
prune/gate → resume order was honoured with a bounded read-select-summarize
context prune. The active cursor (`143-S` / `134-F`), the unresolved-checkpoint
pointer, and the recorded gate verdicts (the three `BLOCKED` review verdicts
and the earlier `PASS` plan-review verdict) were all preserved, not pruned.

### P1 (blocking) — `134.004-T` mandated a forbidden post-capture stash edit

`.backlogit/queue/134.004-T.md`'s thread-present path ordered the disposition
as C2 capture first and only *afterwards* "record the PR number and
review-thread ID in the captured entry's source refs". That step was
unsatisfiable by construction: the C5 capture-only carve-out authored by
`134.002-T` / `134.003-T` grants Ship stash-entry **creation** only and
explicitly forbids Ship from editing a captured entry. The mandated back-fill
would therefore have been a P-010 violation the moment Ship performed it —
the same class of self-contradiction this feature exists to repair.

**Correction applied.** The contract is now closed under a **single-write
capture invariant**:

* The C2 capture is the only write Ship ever makes to the deferred entry.
  Ship may not edit, amend, back-fill, re-classify or re-prioritize it, and
  may not create a second entry for the same expansion.
* Source refs are populated **in full at capture time** — task, feature and
  shipment IDs always; PR number and review-thread ID whenever the finding
  already has them — with any identifier that does not exist at capture
  recorded as an explicit `N/A` rather than left blank or deferred.
* The thread-present path now carries **no write-back step**: reply citing the
  generated entry ID → resolve the thread → name the same ID in the
  PR/closure residual-risk record.
* A new **late-surfacing-thread** criterion states that a thread appearing
  after a threadless capture is handled by citing the *existing* entry ID in
  the reply and in the Ship-owned residual-risk record — never by editing the
  entry's `N/A` fields and never by duplicating it. Reconciling the entry is
  Stage's C6 intake responsibility.

Preserved unchanged: the six-field payload, the C1-cited out-of-scope
rationale, the mandatory capture-first ordering, and the provisional-priority
/ Stage-only reprioritization rule.

**Cross-surface consistency re-verified.** `134.006-T` and `134.007-T` were
checked for the same defect and are clean — both already populate source refs
at capture and neither mandates a post-capture edit. This correction brings
`134.004-T` *into* agreement with its sibling carriers rather than diverging
from them, so neither sibling needed a change.

### P1 (blocking) — Markdown gate

Targeted repository markdownlint (`MD001`/`MD025`/`MD041`, per `AGENTS.md`
P-008 and `templates/scripts/.markdownlint.json.tmpl`) reported four `MD025`
frontmatter-title / body-H1 conflicts. All four were resolved with the
repository-established scoped suppression
`<!-- markdownlint-disable-next-line MD025 -->` placed immediately before the
affected body H1, matching the existing precedent in
`docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md` and
`docs/spikes/2026-07-13-brainspace-compression-feasibility.md`.

A repo-wide baseline was taken first to separate genuine defects from house
style: established documents exhibit only `MD013` and `MD060`, so those two
are repository convention and were left alone, while `MD022`, `MD004`,
`MD032`, `MD012` and `MD038` — absent from the baseline — were confirmed as
defects introduced by these Stage artifacts and corrected:

* **Hardening doc** — six `## H*` headings had wrapped onto a second line, so
  each heading rendered truncated and its remainder became stray body text
  (`H1`, `H2`, `H6`, `H7`, `H8`, `H9`). Re-joined onto single lines. A
  line-wrap had also left `+ role-enforcement;` at column 0, which Markdown
  parsed as a stray unordered-list item mid-paragraph; rewrapped.
* **`019-DL`** — three lists were not preceded by a blank line and so did not
  render as lists; blank lines inserted. `git cat-file -p :<path> | sha256`
  was unwrapped prose, so `<path>` was parsed as inline HTML and vanished on
  render; now wrapped in a code span.
* **Breaker record** — had no top-level heading (`MD041`); a title heading was
  added. Its frontmatter, failure chain and context are otherwise byte-identical.
* **This memory file** — the closing follow-up list had lost its heading and
  sat orphaned after two blank lines; the `## Follow-up candidates (not
  carried)` heading was restored.

**Result:** the targeted gate is clean (exit `0`, zero violations) across all
seven changed Stage Markdown artifacts. No unrelated pre-existing Markdown was
touched, including the known malformed frontmatter in
`docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`
(deferred as `395EBE60`).

### Current state at handoff

* Shipment `143-S` — `queued`, 12 members, `histogram {M:8, S:3}`,
  `unsized: 0`, `skipped: []`, covering feature `134-F`. **Not claimed**;
  claiming remains Ship's.
* All remediation edits are **uncommitted**, for Orchestrator publication.
* Unrelated staged operator changes remain untouched and uncommitted:
  `.gitmodules`, `references/azd-backlogbuilder`,
  `references/azd-backlogloader`, `references/skillopt`, `references/waza`,
  `references/witr`. The H13 enumerated-path commit rule still applies —
  `git add -A`, `git add .` and `git commit -a` remain prohibited.
* No source, template, config or test file was modified by this pass; only
  backlogit-managed backlog artifacts and `docs/` planning/review/memory
  artifacts.

## Fix cycle 1 (2026-08-19, review of `0facdf01`) — per-field source-ref availability

`134.004-T`'s threadless path mandated **both** the PR number and the
review-thread ID as `N/A` in a single blanket pairing. That is wrong for
build/CI findings, because `fix-ci` runs against an **open PR** — the PR number
is known at capture and only the thread ID is unavailable. Since the
single-write invariant forbids supplying a value later, marking a known PR
number `N/A` would have permanently discarded a real identifier.

Corrected so source-ref availability is judged **independently per field**: the
review-thread ID is `N/A` whenever no thread exists; the PR number carries its
actual value whenever a PR is open and is `N/A` only for a genuinely pre-PR
finding; both are `N/A` together only in that pre-PR case. A dedicated
criterion now states `N/A` is a per-field availability marker and never a
path-level default. This brought `134.004-T` into agreement with `134.007-T`,
which had always marked only the `review-thread ID` not applicable.

## Fix cycle 2 (2026-08-19, review of `5882fb4d`) — C3 conditional on thread availability

The **authoritative** C3 clause in `134.001-T` still required a review-thread
reply unconditionally, as did the plan's normative clause table. The carriers
(`134.004-T`, `134.007-T`) had already been corrected to support threadless
findings, so the authoritative definition had become the stale outlier — the
inverse of the usual drift, and the more dangerous direction, since carriers
are supposed to quote the authority rather than correct it.

An unconditional C3 is unsatisfiable on two surfaces the policy governs: Ship's
local review runs **before** PR creation, and build/CI findings have no review
thread even on an open PR. It would have forced Ship either to violate the
clause or to fabricate a thread.

**Correction applied.** C3's reference obligation is now **conditional on
actual thread availability**:

* **Thread exists** — reference the deferred entry ID in the review-thread
  reply, posted *before* the thread is resolved, and in the PR/closure
  residual-risk record.
* **No thread exists** (pre-PR local review, build/CI) — the obligation is
  discharged **in full** by citing the deferred entry ID in the task-level,
  run-level and closure residual-risk record. The absent reply is explicitly
  **not** a C3 shortfall.

The P-018 relationship was made precise at the same time: P-018 governs review
threads only, so a threadless C3 discharge leaves no unresolved thread and
raises no P-018 obligation. Preserved unchanged: C1, C2, C4–C7, capture-first
ordering, the single-write capture invariant, per-field ID availability, and
Stage-only reprioritization.

**Artifacts corrected for coherence:** `134.001-T` (authoritative C3 + P-018
relationship), the plan's clause table and its `004` summary, `134-F`'s
policy restatement, and `019-DL` clause 3 — the last amended in place with an
appended `C3 AMENDMENT` annotation so the decision record shows the change
rather than being silently rewritten. The deliberated decision (Option C)
is unchanged.

**Deliberately not changed.** The operator's verbatim direction is preserved
everywhere it appears (`019-DL` frontmatter and problem frame, `134-F`
description, `stash.jsonl`) — those are the operator's words, not policy text.
The `134.006-T` / `134.007-T` ordering-consistency notes quote the *old* C3
wording as historical record of an earlier correction and were left intact.

**Disclosed, not fixed (P-021 C1 applied to this cycle).**

* The plan's clause table states C2's source refs as "PR + review-thread ID"
  without the "when applicable" qualifier that the authoritative `134.001-T`
  C2 criterion already carries. That is a C2 surface, not C3, so under the C1
  same-contract-surface test it is out of scope for this cycle. Low risk,
  because the authoritative clause governs.
* `134-F` line 41 renders `git cat-file -p :<path> | sha256` as unwrapped
  prose, so `<path>` is parsed as inline HTML (`MD033`) and disappears on
  render — the same class of defect corrected in `019-DL` last cycle. Verified
  **pre-existing at HEAD** and untouched by this cycle's one-line edit at line
  53. It is a different surface from the C3 correction, so C1 defers it;
  `MD033` is also outside the enforced `MD001`/`MD025`/`MD041` gate.

Both are recorded here rather than silently expanded into. Neither was
captured as a deferred stash entry because Stage owns these artifacts directly
and can schedule them in a normal cycle; C2 capture governs Ship's in-cycle
findings, not Stage's own disclosed backlog observations.

## Fix cycle 3 (2026-08-19, review of `2ec55865`) — task-level citation in the fix-ci carrier

`134.007-T`'s threadless fix-ci disposition cited the deferred entry ID only in
the "run/closure residual-risk record", omitting the **task-level** citation
that authoritative C3 (`134.001-T`) and `134.004-T`'s threadless path both
require — all three records: task-level, run-level and closure.

This mattered more than a wording slip. On a threadless surface those
residual-risk citations are the *entire* discharge of C3's reference
obligation, because there is no thread reply to carry the ID. Dropping one of
the three named records weakened the only mechanism keeping the deferred entry
traceable back to the task that spawned it.

**Correction applied.** Both the fix-ci acceptance criterion and the `fix-ci
CARRIER NUANCE` implementation note now name all three records, with the
criterion stating explicitly that this is the complete set authoritative C3
requires for a threadless discharge. Preserved unchanged: the six-field
capture payload, per-field source-ID availability (`review-thread ID` not
applicable while the PR number stays concrete), the single-write capture
invariant, capture-first ordering, the C5 capture-only role-boundary carve-out,
and provisional-priority / Stage-only reprioritization.

**Targeted consistency check.** Every `residual-risk` mention across
`134.001-T`, `134.004-T`, `134.006-T`, `134.007-T`, `134-F`, `019-DL` and the
plan was classified. All threadless discharges now name the identical
three-record set; all thread-present dispositions correctly retain the
PR/closure form (a thread reply plus PR record already carries the ID there).
No divergence remains. Operator-direction quotations and historical correction
notes were left untouched.

### Cycle budget

This was **cycle 3 of the 3-cycle bound** for this remediation. The three
cycles addressed genuinely distinct defects rather than re-litigating one
finding: per-field source-ID availability (cycle 1), the conditional C3
thread obligation (cycle 2), and the completeness of the threadless citation
set (cycle 3). All three trace to the same root cause — the policy was first
authored assuming every finding arrives on a PR review thread, and each cycle
removed one more consequence of that assumption. The budget is now exhausted;
any further finding is accepted and recorded rather than fixed in this
remediation, per the Stop Conditions rule.

## Operator-directed contract replanning (2026-08-19, checkpoint `checkpoint-20260819-064401.json`)

After the three-cycle remediation budget was exhausted, the terminal readiness
gate on HEAD `046adef8` returned `BLOCKED (P0=0, P1=2)` with a P2. The operator
authorized a comprehensive **contract replan** rather than a fourth incremental
fix cycle. This section records that replan.

### Why replanning rather than another fix cycle

The three prior cycles each corrected a real defect, but all three were
symptoms of one root cause: the policy was first authored assuming every
finding arrives on a PR review thread. Incremental cycles kept removing one
consequence at a time. The terminal findings were structurally different — a
*missing verification surface* and a *dangling obligation* — which no wording
fix could close.

### P1-1 — contract-test matrix was not exhaustive (`134.011-T`)

The clause-to-carrier matrix under-listed carriers: C2 omitted
`github-pr-automation`, and C3 omitted both `fix-ci` and `_ship.agent.md.tmpl`
even though `134.004-T` authors both C3 dispositions in Ship. The consequence
is the important part: **the matrix as written would not have detected any of
the three prior fix-cycle defects**, because each defect lived on a surface not
listed as a carrier of the clause it broke.

Corrected the matrix to be exhaustive and added a carrier-completeness guard
tying it to the tasks that author each clause. Then split the task: `134.011-T`
keeps structural coverage (byte identity, checksums, presence matrix), and new
sibling **`134.012-T`** carries the semantic regression suite. The split was
required by the 2-hour rule — roughly a dozen behavioural assertions, each
needing stable marker strings across eight-plus template surfaces, does not fit
alongside the existing byte-identity and seven-clause matrix work.

`134.012-T` maps every historical defect to a named failing test (conditional
C3, threadless discharge, three-record citation, per-field IDs, fused-ref
guard, single-write capture, capture-first, six-field payload, Stage-only
reprioritization, reconciliation consumer) and adds a
`NO-PR/NO-THREAD-ASSUMPTION` guard aimed at the root cause itself rather than
only its known symptoms. Its negative guards must be validated by temporarily
reintroducing the historical defective wording — a negative guard that cannot
be shown to fail is worthless.

### P1-2 — dangling reconciliation obligation (`134.008-T`)

`134.004-T`'s LATE-SURFACING THREAD criterion correctly forbids Ship from
touching a captured entry and delegates reconciliation to "Stage's C6 intake
responsibility" — but **no task defined that responsibility**. Ship correctly
refused to reconcile and nothing was obliged to pick it up, so under the
single-write invariant every `N/A` recorded on the threadless path would have
become permanent, silently discarding identifiers that later became known.

Defined the workflow in `134.008-T`: triggered by any `N/A` source ref during
deliberation/triage; retrieves late identifiers from the Ship-owned
residual-risk records using the deferred entry ID as join key; reconciles in
place under Stage's own pre-existing stash authority (**no Ship write, C5
carve-out and single-write invariant both unweakened**); anti-duplication
(earliest-captured entry is the stable identity); non-blocking when no late
identifier ever surfaces; and idempotent. Added the `134.004-T` dependency —
a genuine content-ordering prerequisite, not a checksum-serialization edge.
Size raised M → L for honest scope growth. `134.007-T` was deliberately *not*
added as a dependency (fix-ci is threadless by nature and originates no late
identifier).

### P2 — H13 staged-change inventory

Added `references/azd-backlogbuilder` and `references/azd-backlogloader`, and
recorded explicitly that the inventory is *illustrative*: because staging is an
enumerated allowlist of the feature's own surfaces, containment does not depend
on the inventory being complete. An out-of-date inventory is a documentation
defect, not a containment failure. The allowlist safety rule is preserved
unchanged.

### Holistic C1–C7 self-review — one further root-cause defect found and fixed

The directed sweep for "assumptions that every finding has a PR or thread"
found a real one in the **authoritative** C2 payload. `134.001-T` qualified only
the review-thread ID with "when applicable" while stating the PR number
unconditionally — false for a pre-PR local-review finding, since Ship's local
review runs before PR creation. Tracing upstream, `019-DL` clause 2 fused both
into a single `PR/thread ID` token and the plan clause table carried
`PR + review-thread ID` unqualified. **That fused token is the root form of the
paired-`N/A` defect fix cycle 1 had to repair downstream in the carriers.**

This is the same inverse-drift shape as fix cycle 2: carriers correct,
authority stale. All three surfaces were corrected together to independent
per-field availability with the fused form prohibited, and a `FUSED-REF` guard
was added to `134.012-T` so the root form cannot reappear. Carriers `134.006-T`
and `134.007-T` were checked and correctly left unchanged — both operate only
where a PR exists, so their unconditional PR wording is accurate there.

Because the operator directed a comprehensive replan explicitly hunting this
assumption class, this was **fixed rather than disclosed**.

### Disposition

Shipment `143-S` now spans **12 tasks**. Checkpoint resolved after successful
completion. Changes left uncommitted for Orchestrator publication.

## Post-replanning readiness fix cycle 1 (2026-08-19, review of HEAD `1dad725a`)

Review returned `BLOCKED (P0=0, P1=3)` plus P2/P3 coherence notes. One bounded
correction pass; all three P1s shared a single structural cause.

### P1.1 — carrier matrix still incomplete, and duplicated

My replanning correction to the matrix was itself incomplete, in the same way
and for the same reason. C2 omitted **both** authoritative
`workflow-policies.md.tmpl` and `circuit-breaker.instructions.md.tmpl` —
`134.005-T` criterion 6 states the C2 capture-before-close requirement outright.
C3 omitted `circuit-breaker.instructions.md.tmpl`, whose criterion 7 carries the
H12 symmetric guard. The registry was listed inconsistently: named in C3 and C7
but absent from C2, C4, C5 and C6 despite authoring all seven clauses.

Two root causes, both now fixed rather than patched:

1. **Derivation method.** The matrix was built by reading carrier tasks ad hoc
   instead of *inverting the authoring set*. Hardening H11 now carries a binding
   derivation rule requiring inversion.
2. **Duplication.** Three independently maintained copies existed — `134.011-T`,
   H11, and `134.012-T`'s carrier lists — so fixing one left the others stale.
   That is exactly what happened: the replanning pass fixed 011 while H11 kept
   the original incomplete pairings. `134.011-T` is now the **single source of
   truth**; H11 and `134.012-T` reference it and are forbidden from restating it.

Added a `C3-SYMMETRIC-GUARD` test to `134.012-T` — circuit-breaker was a carrier
the matrix had omitted *entirely*, and the guard it carries protects against
scope **contraction**, the mirror of the expansion P-021 exists to prevent.

### P1.2 — authoritative C5 forbade a correct, already-shipped Ship behaviour

Authoritative C5 (plan clause table and `019-DL`) prohibited Ship removal
without qualification. But `134.002-T` retains only **discretionary** removal in
the Forbidden column, and H2 requires the distinction to be drawn by
**provenance, not verb**, because Ship's post-merge Step 7 already performs a
correct `backlogit_stash_remove` on `custom_fields.source_stash_id` to retire the
source stash entry that fed the shipped scope.

Read literally, the unamended clause would have forbidden existing shipped
behaviour and made **every future shipment closure a C5 violation**. Corrected on
all three authoritative surfaces (plan, `019-DL`, and `134.001-T` — whose C5
criterion previously read only "C5 Ship capture-only carve-out present", too weak
to constrain the wording at all). Added a `C5-EXCEPTION` contract test asserting
the policy text and Ship Role Boundary agree on the provenance distinction, plus
a negative guard against an unqualified "or remove" — so the exception cannot
regress silently. Ship stays capture-only; Stage keeps sole triage and
reconciliation authority.

### The recurring shape, now named

This is the **third** inverse-drift instance in this feature — carriers correct,
authority stale — after the C3 amendment (fix cycle 2) and the C2 fused-ref
amendment (replanning). The pattern is consistent enough to state plainly: when a
clause is corrected, the correction lands on the surface where the defect was
*observed* (a carrier), not on the surface that *defines* it. `019-DL` now carries
C2, C3 and C5 amendment annotations recording all three.

### P1.3 and coherence notes

`docs/memory/2026-08-18/circuit-break-stage-remediation-143-S.md` gained an H1
after frontmatter for MD041 — **structure only, no finding text altered**;
it remains historical evidence.

`134-F` goal 3 previously said the deferred ID is cited in the task/run/closure
record "in every case", conflating the surfaces: thread-present discharges via
the **PR/closure** record, threadless via **task/run/closure**. Now states that a
deferred ID is referenced in every case while the record *set* differs by surface.

Stale 11-task / one-test summaries updated to 12 tasks / two contract-test files
where they describe current state (`134-F` scope line, `019-DL` S11 surface map).
The two **verdict** sections — the hardening verdict and the plan-review
decomposition PASS — were given dated addenda rather than rewrites, so they stand
as issued evidence with current state recorded alongside. `019-DL`'s original
sizing rationale was marked as-deliberated with a pointer rather than edited.

### Matrix verification performed

A complete inversion sweep over all 12 tasks for C2/C3/C5 confirms the matrix is
now closed: C2 and C3 each = registry + 004 + 005 + 006 + 007(×2); C5 = registry
plus 002 plus 003. `134.002-T` and `134.003-T` explicitly *reference* C2 rather
than restate it (their own criteria say so), so they are C5 carriers only;
`134.008-T` references C3/C5 but authors C6.

## Post-replanning readiness fix cycle 2 (2026-08-19, review of HEAD `b449dcbf`)

Review returned `BLOCKED (P0=0, P1=4, P2=1)`. All four P1s were the same defect
viewed from different angles, and the angle matters more than any individual fix.

### The completeness guard was scoped to the defects already found

Fix cycle 1 corrected the matrix by hand and added a carrier-completeness guard.
But the guard checked **C2 and C3 only**, and its own expected set omitted
`134.005-T` — the carrier cycle 1 had just finished adding by hand. So the guard
could not have caught the omission it was written in response to, and it could
not look at C1, C4, C5, C6 or C7 at all.

That is the whole lesson of this cycle: **a guard derived from the clauses where
defects were found cannot detect defects in the clauses nobody has re-derived.**
Cycles 1 and 2 both re-inverted only C2/C3/C5. C1 and C4 had never been
re-derived since the original authoring pass.

A full inversion across all seven rows found exactly what that predicts:

* **C1** listed only the registry and circuit-breaker, though `134.004-T`,
  `134.006-T` and `134.007-T` all gate their loops on C1 classification.
* **C4** listed only 004 and 009, though `134.006-T` and `134.007-T` both carry
  the cycle-exhaustion annotation in their Stop Conditions rows.
* **C5** listed only the two carve-out surfaces, though four procedural surfaces
  carry Stage-only reprioritization and `134.008-T` carries the Stage-side
  authority statement.

H11 now binds the guard to all seven rows and to an inverted `AUTHORING_TASKS`
constant covering tasks 001–009.

### Expanding the rows required fixing the assertion model first

This is the part I would have got wrong by only widening the matrix. Once C1, C4
and C5 include their procedural carriers, asserting **one identical marker per
row** becomes actively harmful, and three of the newly added pairings would have
been unsatisfiable or unfaithful:

* H5 **forbids** 004/006/007 from restating the C1 test text that 005 is
  specifically designated to carry.
* `github-pr-automation` has no threadless case — every finding on that surface
  is a PR review comment.
* `fix-ci` has no thread to reply on.

Demanding thread-reply ordering from `fix-ci`, or threadless discharge from
`github-pr-automation`, would have forced a contract contradicting the surface's
own subject matter — **the precise failure mode that produced the paired-`N/A`
defect in the first place.** Widening coverage without this would have
manufactured a fourth instance of the original root cause while appearing to fix
the third.

So the matrix now carries two things instead of one:

1. **Carrier roles** — `[A]` authoritative, `[N]` normative restatement, `[P]`
   procedural, `[G]` guard-only — determining *which* marker is asserted where.
2. **A clause → behaviour → carrier-subset mapping (B1–B17)** — the justified
   subsets, each narrowing recorded with its reason at the point of declaration.

`134.012-T` now resolves every assertion by behaviour ID and carries a
`SUBSET-FIDELITY` guard that fails if a behaviour is asserted against a carrier
the mapping excludes. Both live in the single-source block in `134.011-T`; the
subsets were deliberately **not** given a second home, since duplicated
definitions caused the drift this feature keeps rediscovering.

### Coverage added, and one mislabel

The C3 symmetric guard (B9) now asserts on all four authoring surfaces —
registry, Ship, circuit-breaker, `fix-ci` — instead of two. The prior
two-surface assertion left the two loops that *actually run fix cycles*
unguarded against scope contraction.

New semantic coverage for the previously un-derived clauses: `C1-GATE` (B1),
`C4-NON-BYPASS` (B10), `C5-BOUNDARY` (B11) and `THREAD-PRESENT-ORDERING` (B7).
B7 is split out of capture-first precisely so circuit-breaker and `fix-ci` are
not asked to satisfy an ordering step they carry no thread for.

While inverting, I found the authoritative task labelled the guard **`C12`** —
not a clause in this policy, which has C1–C7 only. Every other carrier calls it
`C3 symmetric guard`. Left alone, the authoritative surface would have been the
one place B9's marker did not match. Corrected.

### Sizing

`134.012-T` M → **L**. Five assertions were added this cycle; the suite is now
~16 assertions over nine surfaces. The estimate sits near the 2-hour bound rather
than safely inside it, so the split line is **declared in advance** in the task
(capture-and-discharge semantics vs. clause-boundary semantics) rather than
improvised mid-execution. A pre-emptive split was rejected because it would
duplicate the carrier-resolution table — the exact duplication this cycle removed.

### P2 current-state drift

`.backlogit/stash.jsonl` (B48A482A consumption prefix), `.backlogit/memories.json`
and the plan surface map S11 all still described 11 tasks and one contract test.
Updated to 12 tasks and two named test files. The memories entry follows the
repository's existing append-only convention — an `[UPDATED … STALE FACTS …]`
prefix with the original preserved beneath, matching the `[SUPERSEDED …]`
precedent already in that file. The verbatim operator direction in the stash
entry was left byte-identical and verified as such after the edit.

## Post-replanning readiness fix cycle 3 of 3 (2026-08-19, review of HEAD `904c46b9`)

Review returned `BLOCKED (P0=0, P1=1)`: `fix-ci` was modelled as threadless-only.
I verified the claim read-only against `templates/skills/fix-ci/SKILL.md.tmpl`
before changing anything, and the review is right.

### The evidence

The template's own frontmatter description is "Detect CI pipeline failures **and
review comments**". It carries:

* **Step 2.5** — Copilot review-comment detection, building a full thread
  inventory with per-thread reply status.
* **Step 3** — categorize review comments valid / partial / invalid.
* **Step 6** — reply to the thread using the github-pr-automation reply
  templates, then resolve Copilot threads via the GraphQL `resolveReviewThread`
  mutation.
* **Step 6.5** — a **NON-NEGOTIABLE reply gate**: no commit may be pushed while
  any open thread is unreplied.

A surface with a mandatory reply gate is the last one that should have been
excluded from thread-present reply ordering. `circuit-breaker` was re-checked in
the same pass and has no thread operation at all, so it remains the only
legitimately excluded surface.

### Why the previous method could not catch this

This is a genuinely new root cause, not a fourth instance of the previous three.

Every earlier correction re-derived the matrix by **inverting the authoring set**
— reading what the backlog tasks claim to author. That is the right method for
finding an *under-listed carrier*, and it worked. But it inherits any factual
error the criteria already contain. `134.007-T` correctly said "a CI/build
failure has no review thread" — true of a **finding** — and that got silently
generalized into a claim about the **surface**. Inversion cannot detect that,
because the authoring set is exactly where the wrong premise lives.

The fix is a rule about how a carrier's path set is determined at all:

> **DUAL-PATH SURFACES.** A carrier's path set is determined by the FINDING KINDS
> it actually handles, verified against the template — never by the loop's name
> or its primary purpose.

Two carriers are dual-path: `_ship.agent.md.tmpl` (already modelled correctly)
and `fix-ci/SKILL.md.tmpl` (was not).

### Changes

B7 now includes `fix-ci`; B8 scopes `fix-ci` to its CI-finding path specifically
rather than to the whole surface. `134.007-T` gains a thread-present criterion
for the review-comment path and an **existing-entry reuse** rule — a dual-path
surface is precisely where duplicate deferred capture is most likely, since the
same finding can arrive twice through two intake paths in one run. Two new tests
in `134.012-T`: `FIX-CI-DUAL-PATH` (with a negative guard that must fail against
the historical wording "a review thread never surfaces inside a fix-ci run") and
`FIX-CI-ENTRY-REUSE`.

### A dependency that existed only because of the false premise

`134.008-T` explicitly excluded a `134.007-T` dependency on the stated ground
that fix-ci "originates no late identifier". That was reasoning *from* the wrong
premise. Since Step 6.5 re-queries for threads opened during the fix phase, a CI
finding captured with `review-thread ID: N/A` can gain a thread **inside the same
run** — making fix-ci a genuine originator of late identifiers and its
run/closure records a retrieval source Stage must search. Edge added; the
retrieval-source criterion now names those records.

`134.007-T` complexity raised low → **medium**: the dual-path distinction is the
thing four consecutive cycles got wrong, so "low" was no longer credible.

### Handling of the superseded rationale

The cycle-2 `CARRIER-ROLE RATIONALE` contains the sentence "and fix-ci has no
thread to reply on". I did **not** delete it. It is annotated `[SUPERSEDED IN
PART]` pointing at correction 4, because it is the recorded reasoning that this
correction had to overturn — and the reasoning around it (role-appropriate
markers) is still sound. Only the example was wrong.

### Incidental defect from my own cycle-2 edit

The `MATRIX CORRECTION` paragraph in `134.011-T` had been **duplicated verbatim**
by my cycle-2 replacement. Removed. Worth noting as a self-inflicted class:
large block replacements that re-include their own anchor text.

## Stage correction operation — B16/B17 behaviour registration (2026-08-19)

Resumed `checkpoint-20260819-165602.json` (stage-owned, sole active, 0 anomalies
across 36 enumerated records). Engram bound and fresh (`stale_files: false`,
scan 15601/15601 complete); bounded prune selected an empty set — no stale
working-context records existed that were not protected — with cursor `143-S`,
the checkpoint pointer, and all gate verdicts preserved untouched.

### The defect

Fix cycle 3 added `FIX-CI-DUAL-PATH` and `FIX-CI-ENTRY-REUSE` to `134.012-T`
with correct substance and correct carriers, but **without behaviour IDs**. The
authoritative mapping still ended at B15 while the suite exercised seventeen
behaviours. The two newest assertions — guarding the most recently discovered
defect class — sat *outside* the audit entirely: unchecked by `SUBSET-FIDELITY`,
uncounted by any completeness assertion, free to drift from the matrix without
failing anything.

### Root cause — distinct from the previous four

Every prior correction fixed the **content** of the map and its guards, but the
guards only ever policed entries **already in** the map. Nothing asserted the
map was *complete with respect to the suite*. An unnumbered assertion is not a
wrong entry, it is a **missing** one, and a guard that validates existing
entries is structurally blind to it.

This is MATRIX CORRECTION 3's finding one level up. That one said: a guard
scoped to the clauses where defects were already found cannot see the clauses
nobody looked at. This one says: a guard scoped to the behaviours already
registered cannot see the assertions nobody registered. Same shape, higher
altitude.

### The correction

* **B16 `c3-dual-path-selection`** — DERIVED as `B7 INTERSECT B8` =
  {001[A], 004, 007-fix-ci}. Defined as a derivation, not a list, so it cannot
  drift from its parents; a carrier gaining a second disposition enters B16
  automatically.
* **B17 `c2-existing-entry-reuse`** — DERIVED as `B6 UNION {007-fix-ci}` =
  {004, 007-fix-ci, 008}. Inherits B6's carriers *and* B6's declared exemption
  from the clause-row subset check, for the same reason: it descends from the
  single-write invariant, a Ship ROLE property rather than a registry clause,
  which is why 008 may appear despite being absent from the C2 row.
  `007-fix-ci` is added because Step 6.5 re-queries for threads opened since
  Step 2.5 — the only surface where a thread can surface *after* the capture
  write inside a single run.
* Three guards in `134.012-T` now govern B16/B17 exactly like B1–B15:
  `SUBSET-FIDELITY` (extended to B1–B17, exemption list asserted to be exactly
  `{B6, B17}` so nothing can quietly opt out), a new `RANGE-COMPLETENESS` guard
  (range is exactly B1–B17, every ID exercised, **no assertion without an ID**),
  and a new `DERIVED-SUBSET` guard (recomputes each derivation from its parents).

### Carrier verification (read-only)

B16's membership was re-confirmed against `templates/skills/fix-ci/SKILL.md.tmpl`
rather than inferred. B17's fix-ci membership rests on Step 6.5 line 169, which
extends the thread inventory with "any additional threads opened since Step 2.5
ran (re-query)" — the mechanical basis for a late-surfacing thread within one run.

### Range statements aligned (no map duplication)

Plan §S11 narrative, hardening H11, and this file's summary all state the range
`B1–B17` and point at the single-source block in `134.011-T`. None restates the
map — the alignment is a pointer plus a range, which is what kept this from
becoming a fourth copy.

### The new guard immediately found more than it was written for

Running the RANGE-COMPLETENESS check against its own task exposed **seven more
unnumbered semantic criteria** in `134.012-T` (C5-EXCEPTION, CONDITIONAL-C3,
THREE-RECORD-CITATION, FUSED-REF, SINGLE-WRITE, NO-PR/NO-THREAD-ASSUMPTION,
RECONCILIATION-CONSUMER). B16/B17 were not the only assertions outside the
audit — they were merely the two most recently added. Every one mapped cleanly
onto an existing behaviour (B11, B16, B8, B5, B6, B3, B14 respectively), so all
were bound rather than the guard being weakened.

Two structural refinements fell out of doing that honestly:

* **UNIVERSAL scope.** `FUSED-REF` (B5) and `NO-PR/NO-THREAD-ASSUMPTION` (B3)
  are negative guards that deliberately run across *all* carriers rather than a
  behaviour's subset, because the error they forbid is wrong wherever it
  appears. They are now ID-bound *and* labelled `UNIVERSAL scope`, so
  SUBSET-FIDELITY cannot misread their breadth as a subset violation. Without
  the label, binding them would have created a false failure.
* **Cross-file allocation.** My first draft of the guard demanded `134.012-T`
  name all seventeen IDs. That was wrong in the opposite direction: **B2, B13
  and B15** are correctly discharged by `134.011-T`'s literal-clause,
  precedence and policy-registry tests. Demanding one file cover the whole
  range would have forced the exact duplication that caused the original matrix
  drift. The guard now checks the union across both files, with `OWNED` and
  `DISCHARGED_ELSEWHERE` constants required to be disjoint and to sum to
  B1–B17; the allocation is declared once in `134.011-T` and the three
  criteria in that file now carry their IDs, so it is checkable from both sides.

Verified programmatically: allocation disjoint, union exactly B1–B17, nothing
claimed twice, nothing orphaned, and the only unnumbered criteria remaining are
the four structural ones the guard explicitly exempts.

## B16/B17 correction review cycle 1 (2026-08-19, HEAD 77d1a7e0)

Two P1s, **both introduced by my own correction-5 pass**. Worth stating plainly:
the guard written to stop over-generalization was itself an over-generalization.

### P1.1 — B16 selector contradicted the authoritative rule

I had defined B16 as selecting between the two C3 dispositions **by finding
kind**. The authoritative selector is **actual thread availability**: 001 states
C3 as `WHERE A REVIEW THREAD EXISTS` / `WHERE NO REVIEW THREAD EXISTS`, and 004
states its threadless path as `no review thread exists for the finding at the
moment it is classified`.

The disproof is a single case: a **pre-PR local-review finding** is
*review-kind* yet has **no thread**, because Ship's local review runs before PR
creation. A finding-kind selector routes it to the thread-present disposition
and demands a reply on a thread that does not exist — the exact error class this
whole feature exists to prevent.

**Root cause.** Correction 4 established that a surface's *path set* is
determined by the finding kinds it handles. That is a **presence** rule. I
lifted it into a **selection** rule. `fix-ci`'s path split is a faithful
*implementation* of thread availability on that surface — path there determines
whether a thread exists — so it looked general when it was local.

Fixed by renaming the behaviour to `c3-dual-disposition-carriage` (shared
behaviour = dual **carriage**; selector is carrier-specific), stating the
presence/selection distinction inside the DUAL-PATH SURFACES rule, and scoping
`134.007-T`'s dual-path sentence — the likely origin of the lift — so it cannot
seed the same generalization again.

### P1.2 — discharge was attribution, not coverage

The allocation counted B2/B13/B15 as discharged because the IDs appeared in the
right constant. The owning tests covered only part of each:

* **B2** (subset `{001, 005}`) — asserted on circuit-breaker alone, with three
  of four not-sufficient phrases and none of the three worked cases.
* **B13** (subset `{001, 008}`) — asserted on the Stage agent alone, leaving the
  authoritative clause itself unguarded.
* **B15** — a structural section-presence check that would pass against a
  registry whose C7 action had been weakened to **telemetry without halt**.

**Root cause — an asymmetry between the two halves of the audit.** For
behaviours a file *owns*, SUBSET-FIDELITY already checks asserted carriers
against the declared subset. For behaviours marked `DISCHARGED_ELSEWHERE`,
**nothing did**. A partially-covered behaviour reported green is worse than an
uncovered one: the uncovered case at least fails a count.

Fixed by making discharge a **coverage claim** cross-checked against the declared
subset and mapped clause text, expanding all three tests to their full subsets,
and recording that allocation and coverage are separate properties — a file may
legitimately own a behaviour it under-covers, and that is a coverage defect that
must be reported rather than passing on attribution.

### Incidental gap found while checking

The non-vacuity rule (validate each negative guard by reintroducing the old
wording) existed only in `134.012-T`. Now that `134.011-T` owns B2/B13/B15 and
carries its own negative guard, it needed the rule too — added, with an explicit
note that this is the one *deliberate* duplication between the two files, since
it is a testing-practice rule each must honour independently rather than a
carrier mapping.

## Correction cycle 2 of 3 (2026-08-19, HEAD 663205a6)

Two P1s and one P2. Both P1s are the **inverse** of every earlier finding: the
semantic test was right and the **carrier task it tests** was wrong. Every prior
cycle fixed tests against correct carriers; this one fixed carriers against a
correct test.

### P1.1 — C1's fifth discriminator

Authoritative C1 declares **five** insufficient discriminators: `same file`,
`same function`, `same PR`, `same subsystem`, **`related`**. `134.005-T`'s
operational restatement carried four, and my B2 assertion demanded four.

**Root cause, and it is uncomfortable.** Last cycle I raised B2 from three
phrases to four — by reading the **restatement** (005) and counting what was
there, instead of reading the **authoritative clause** (001) and counting what
should be. That is exactly the defect the authority/restatement split exists to
prevent, committed inside the fix for it. The restating carrier is *by
definition* the surface that can drift, so it can never be the source of truth
for its own completeness. B2 now resolves the count from 001 explicitly, and
says so in the criterion.

### P1.2 — half a symmetric guard

The C3 symmetric guard is a **two-part** clause: (i) a same-contract-surface
completion IS in scope and must be fixed, not deferred; **and** (ii) deferring
one without a captured entry *and a residual-risk record* is itself a violation.

`134.004-T` and `134.007-T` carried only part (i). `134.005-T` carried part (ii)
but dropped the residual-risk record from it.

The B9 test in `134.012-T` already demanded the complete form — so **the suite
was unsatisfiable against its own carrier contracts**. That contradiction would
have surfaced at implementation time, when whoever wrote the tests would have
had to either weaken the test or edit contracts mid-build. Neither is a good
outcome; the second is how contract drift starts.

**Root cause.** A compound clause treated as its memorable half. Part (i)
forbids under-fixing and *sounds* like the point of the guard. Part (ii) forbids
silent deferral — and is the part that makes it **symmetric** at all.

Fixed in all four mapped carriers, with the **B9 subset deliberately unchanged**:
the correction is to what each mapped carrier must state, not to which carriers
state it, so no obligation lands on `006` or `pr-lifecycle`.

### P2 — stale ordering, in two places

The plan's task-006 summary listed reply → resolve → capture → residual-risk.
`134.006-T` mandates **capture-first**: capture → reply citing the deferred ID →
resolve → residual-risk record. The summary put capture *third*, inverting the
single invariant this feature is built around. The task-table row carried the
same stale ordering (`reply / resolve / capture / reference`), which the review
did not flag — both corrected.

### Pattern worth naming

Three of the last four defects share one shape: **a rule correct at one scope
applied at another** (presence→selection), **a check correct on one half of a
partition** (owned→discharged), and now **a count taken from the derived surface
instead of the authoritative one** (restatement→authority). All three are
failures to ask *which artifact is the source of truth for this particular
claim*.

## Correction cycle 3 of 3 — systematic authority audit (2026-08-19)

The operator adopted the recommendation that closed cycle 2: stop fixing
reported instances and audit the *whole* surface against its authorities.
Every acceptance criterion in `134.011-T` (12) and `134.012-T` (26) was
resolved against the artifact that owns its claim.

**Mismatches proven and fixed.**

* `134.011-T` H1 guard omitted **archival**. Owner `134.002-T` L32 declares
  "discretionary removal/**archival**". A guard checking only removal passes
  against a Role Boundary that lets Ship discretionarily archive a
  Stage-owned deferred entry — the exact loss C5 exists to prevent.
* `134.012-T` marker-provenance criterion named **three** authoring tasks
  while the suite asserts text authored across **eight**. Now enumerates all
  eight, plus the rule that a marker resolves from the task that *authors*
  the text, never from a restating surface.
* Both remaining negative guards (SINGLE-WRITE, NO-PR/NO-THREAD) named verbs
  and assumptions but **no historically defective wording**, so neither was
  demonstrably non-vacuous. Each now names the wording it must fail against:
  the original "capture first and only afterward record the PR and
  review-thread IDs" flow, and the original "(PR number, review-thread ID
  when applicable, …)" enumeration that qualified only the thread ID.
* `019-DL` S6 row still carried the pre-capture-first ordering
  "reply/resolve/capture/reference" → now "capture/reply/resolve/record",
  with a dated correction note. Decision content untouched.

**Verified correct — recorded so no later cycle re-derives them.**

* Byte-identity list correctly *excludes* workflow-policies (S1) and the two
  skills (S7): the surface map marks both `dogfooded: no`. It matches the
  eight `yes` rows exactly.
* Amendment Log `1.20.0` is right (registry ends at P-020/1.19.0).
* Six-field payload and B4's exclusion of 005 match `134.001-T` and H7.
* Post-merge **Step 7** is cleanup; `134.002-T`'s "Step 6" reference is about
  entry *creation* — not a mismatch, and worth not "fixing" later.
* `134.010-T` is correctly outside `AUTHORING_TASKS` (carries no clause text).
* B3, B7, B11, B12 subsets in `134.012-T` match the map exactly.

**The durable output** is the new **AUTHORITY-OWNER MAP** in `134.011-T`,
naming the owning artifact for every class of claim the two test files
assert. Four consecutive cycles produced defects of one shape — a claim
resolved from a convenient restatement rather than its authority. An
instance fix cannot reach that; a lookup table Ship reads before asserting
anything can. If a future cycle finds a mismatch, suspect the map is missing
a row before suspecting the assertion.

**Honest limitation.** Each guard I write is itself unreviewed until the next
cycle, and this is cycle 3/3 — so the AUTHORITY-OWNER MAP has had no
adversarial read. Its rows were verified individually against their owners,
but the table as a whole is new. That is the residual risk on this handoff.

## Owner-contract reconciliation — six terminal P1 findings (2026-08-19)

Resumed `checkpoint-20260819-183625.json` (cursor `143-S`/`134-F`, branch
`chore/stage-143-S`). One holistic pass rather than six patches, because all
six findings turned out to share a single shape.

**The shape.** CORRECTIONS 1–8 were wrong *content* resolved from the wrong
source. These six are wrong **applicability**: each assertion was individually
true of *some* carrier, then applied to a set its owner never contracted.
Findings 1 and 3 are the same error mirrored — one demanded a per-field
qualifier on surfaces that cannot carry it, the other demanded boundary text on
a surface contracted only to *reference* it. Findings 4, 5 and 6 are its
complement: a subset or a lifetime narrower than the owner's, leaving a mapped
carrier or a real path untested.

* **F1 C2 applicability.** FUSED-REF was declared UNIVERSAL while carrying B5's
  ID, demanding independent per-field qualifiers on 006 and 007-pr-lifecycle —
  exactly the two surfaces B5 excludes, because both IDs always exist there.
  Split: universal *negative* (no fused `PR/thread` token anywhere) + B5-scoped
  *positive*. Scope is now a property of the assertion, not of its behaviour ID.
* **F2 C5 archival.** Authoritative C5 prohibited discretionary *removal* only;
  owner `134.002-T` always said "discretionary removal/**archival**". Archival
  reaches the same loss by a second verb. Both now named under one DISCRETIONARY
  qualifier; the manifest-derived Step 7 exception is untouched.
* **F3 B11 ownership.** B11 listed `003` and asserted the creation grant and
  cleanup exception there — but H5 contracts `134.003-T` to *reference* C5, not
  restate it. The test demanded text a *correct* template must not carry. Split
  into **B18** (`c5-reference-role-recognition`, 003 only), with a negative guard
  forbidding boundary semantics from being demanded on that surface.
* **F4 B6 consumer.** SINGLE-WRITE asserted only Ship. A suite proving Ship
  writes once, without proving anyone may close the resulting gap, passes on a
  policy that permanently strands every `N/A`. Both halves now asserted together.
* **F5 B14 completeness.** B14's subset is `008` alone, so its test is the only
  place the workflow is exercised — and it asserted mere existence. Now asserts
  all six owner-defined obligations, with Stage-authority flagged as what
  discharges 008's cross-clause C5 carriage.
* **F6 B17 lifetime.** Reuse was scoped to "this run", but the commonest real
  path is a CI finding captured in an *earlier* run with `review-thread ID: N/A`
  that gains a thread later. Reuse is now keyed on the stable deferred-entry ID,
  never on run boundaries.

Both P2s resolved: marker provenance said EIGHT while already enumerating NINE
tasks; the review addendum still called `012` size M after it was raised to L.

**Self-inflicted defect caught in-flight.** My two `Set-Content` inserts
rewrote `134.011-T` and `134.012-T` from LF to CRLF file-wide. HEAD is LF for
both. Normalized back and re-verified: diffs are line-scoped (8/3 and 10/9), no
BOM. Worth remembering — `Set-Content` is not line-ending-safe on this repo;
prefer the `edit` tool, which preserved LF on every file it touched.

**Range is now B1–B18.** Audit after changes: 18 IDs defined, no gaps, no
duplicates; allocation disjoint with union exactly B1–B18; all 15 behaviours
owned by `134.012-T` are asserted, none foreign; every negative guard names a
historical defective wording or an explicit defect form.

## Owner-reconciliation review cycle 1 (2026-08-19, HEAD 64b5817b)

Two findings, both mine from the previous pass.

* **Stale allocation-union range.** The RANGE-COMPLETENESS criterion is a single
  3,027-character line containing **two** range statements. My previous edit
  replaced the leading one and left `the union of the two constants MUST equal
  B1–B17 exactly` untouched ~1,400 characters further along the same line. My
  verification swept for the *line*, saw it had been changed, and moved on.
  Fixed, and re-verified by **occurrence count** per file rather than by line
  match — the only method that catches a second instance hiding on a line
  already known to be edited. Result: `134.012-T` zero stale; the three in
  `134.011-T` and six in this file are all inside historical CORRECTION /
  prior-cycle narratives (including CORRECTION 9's deliberate `B1–B17 → B1–B18`
  delta) and are correctly left alone.
* **B14 completeness was still incomplete.** It claimed to assert *every*
  owner-defined obligation while omitting `134.008-T` L45 — reconciled
  identifiers carried into the deliberation artifact, and the reconciliation
  **including the `no late identifier found` outcome** recorded for auditability
  — and L46 (H5 citation style). Added as (7) and (8). (7) is marked a compound
  clause needing both halves: under the NON-BLOCKING rule the no-result
  termination is the *common* case, so the half most likely to be dropped is the
  one covering most real terminations, and dropping it makes a truthful terminal
  `N/A` indistinguishable from a reconciliation never performed.

**Lesson, stated plainly.** Last cycle I fixed a *count* defect by adding an
obligation list, and this cycle that same list was found short by two. Both
failures are the same move: enumerating from memory of the owner instead of
re-reading it end to end. The check that actually works is mechanical — map
every owner criterion line to an asserted obligation and require zero unmapped.
That mapping now runs L39–L46 → (1)–(8) with none unmapped, and the criterion
states that if the owner grows, B14 must grow with it, since B14's
single-carrier subset means nothing else will catch the omission.

## Owner-reconciliation review cycle 2 (2026-08-19, HEAD 53b080fa)

Two P1s, both introduced by the two passes immediately before this one, and both
**verification** failures rather than reasoning failures.

* **B14 owner coverage — third attempt.** Cycle 1 fixed a missing-obligation
  defect by mapping each owner criterion *line* to one obligation and asserting
  zero unmapped. That check passes while a compound clause hides *inside* a
  line — and owner criterion L42 carries **five** obligations, of which only two
  and a half were asserted. The missing part was the whole *remediation* half of
  anti-duplication: detect duplicates, reconcile into the earliest-captured
  entry and **remove** the others, **record the merge**. That gap matters
  because a rule which only forbids *creating* duplicates has nothing to say
  once duplicates exist — and they do: a prior-run capture whose entry isn't
  found on re-query is exactly how a second entry appears. Re-resolving the
  owner atomically instead of patching the count also surfaced a **third**
  omission nobody flagged: L40's negative half, *Stage MUST NOT ask Ship to
  supply the identifiers by editing the entry* — without which obligation (2)
  silently reauthorizes a second Ship write.
* **B18 carrier role.** The B11/B18 split correctly removed the false
  requirement that role-enforcement carry complete C5 boundary semantics, but
  left the carrier tagged `[N]` NORMATIVE RESTATEMENT — a role whose legend
  *explicitly designated role-enforcement for C5* and whose marker resolution
  demands restated clause prose. H5 contracts that surface to **cite** C5, not
  restate it. So the role marker reintroduced, through the legend, precisely the
  false requirement the split had just removed. Added `[R]` REFERENCE-ONLY.

**The pattern, and the method change it forces.** Each defect was a correct fix
whose *verification ran one level coarser than the defect could occupy*:

| Fix | Verified at | Defect lived at |
|---|---|---|
| Range → B1–B18 | line | second occurrence *within* a line |
| B14 obligations | criterion line | compound clause *within* a criterion |
| B11/B18 split | subset membership | role *marker* semantics |

The durable rule: **verify at the granularity the defect can occupy, not the
granularity the artifact is organized in.** Occurrence counts, not line matches.
Atomic obligations, not criterion lines. Role semantics, not subset membership.
B14's completeness rule is now atomic *by construction* — every distinct
MUST/MUST NOT maps to a numbered or lettered obligation, and a sentence carrying
two obligations counts as two. Audit: **22 atomic obligations, zero unmapped.**

## Staging PR #372 Copilot review-fix cycle 1 (2026-08-19, HEAD 1c7e2458)

The first review of this feature by an agent that **did not write it**, and the
finding profile is completely different from the eight self-reviews before it.
Not one of the five is a matrix, subset or allocation defect. Three are places
where the artifacts stated a rule that **could not be executed** — which every
prior cycle's internal-consistency auditing was structurally unable to see,
because the rules were perfectly consistent with each other and simply not
actionable.

* **C4 read as a bypass.** The clause listed the insufficient authorizations and
  closed with *"only explicit operator authorization ... does"* — naming an
  authorization **sufficient to expand the active cycle**, the exact route around
  C1/C2/C6 the Statement forbids. The deliberated intent was always that
  authorization opens *separate* work; the wording never said so. The distinction
  is **temporal direction, not authority**: authorization is a forward act that
  opens new work, never a retroactive one that reclassifies an already-discovered
  expansion as in-scope. Corrected on the authority, the deliberation, the plan
  clause table and the three Stop-Conditions carriers whose halt-and-prompt is
  exactly where an in-cycle "go ahead" gets solicited. Task 009 was deliberately
  **not** touched — its dark surfaces already state the correct rule, and editing
  them would have been the "same clause, therefore in scope" error this whole
  policy exists to prevent.
* **Prior-run entry reuse had no discovery procedure.** B17 and 134.007-T
  required reusing an entry captured in a *prior run* while providing no way to
  find it. In-run reuse holds the ID the capture just returned; across runs that
  handle does not exist. So the "MUST NOT create a second entry" rule was
  unenforceable in precisely the case that produces duplicates. Added
  DEFERRED-ENTRY DISCOVERY (sources, join keys, disposition) and a **two-direction
  fail-safe** to 134.004-T, authored once and referenced by 007. The asymmetry is
  the interesting part: an *ambiguous* match fails **closed** — no entry, cite all
  candidates, defer to Stage — while an *unavailable* lookup **captures**, because
  a duplicate is recoverable through 008's reconciliation and a dropped finding is
  not. One shared default would have been wrong for one of the two.
* **Duplicate remediation said "removes".** Corrected to **archive** on two
  independent grounds: backlogit's CLI exposes `stash archive` and no
  `stash remove` at all, and the MCP `backlogit_stash_remove` is deprecated in
  favour of `backlogit_stash_archive`; and a duplicate is *evidence* that a
  discovery lookup returned a false absence, so destroying it destroys the
  diagnostic along with any source ref the duplicate carries and the survivor
  does not.
* **A breaker record counted a success as a failed attempt.** Attempt 3 of the
  authority-audit breaker recorded the *successful* audit; the actual third
  failure was the BLOCKED review at `c1bfddc8`. Rewritten; the audit moved to
  Context, `attempts: 3` integrity preserved.
* **Task 012 was knowingly oversized**, with a split line declared but not taken.
  The review's point stands: a known-necessary split deferred to implementation
  lands mid-execution, with the bound already breached and the least context
  available to choose the cut. Split taken into **134.013-T**.

**The split, and why the cut is where it is.** The pre-declared line was followed
exactly, extended only by *lineage* for the three behaviours registered after it
was written. **Derived behaviours must sit with their parents** — B16 = `B7 ∩ B8`
and B17 = `B6 ∪ {007-fix-ci}`, so all five stay in 012 or the DERIVED-SUBSET guard
would have to recompute an intersection whose operands live in another module.
**Split behaviours stay with their siblings** — B18 came out of B11 and moves with
it. Allocation is now three-way and the guard **imports** each sibling's
`OWNED_BEHAVIOURS` rather than hardcoding a copy; the import direction is one-way
(011/013 → 012), which is what keeps the check acyclic and why the dependency
edges run 011 → 013 → 012.

**What this cycle actually taught.** Every prior correction tested the artifacts
against *each other*. Findings 1–3 are all cases where the artifacts agreed
perfectly and none of them could be **carried out** by the agent that would have
to execute it: a bypass an agent would reasonably invoke, a lookup with no source
or key, and a verb the tool no longer offers. **Internal consistency is not
executability**, and no amount of cross-artifact auditing detects the difference.
The rule this adds to the granularity lessons of the prior cycles: for every MUST,
ask *who performs it, with what inputs, and whether those inputs exist at that
moment*. A rule whose inputs are unavailable when it fires is not a strict rule —
it is an unenforceable one, and it will be silently skipped rather than loudly
failed.

**Dogfooding note.** While correcting the archive semantics I found that Ship's
post-merge Step 7 is documented as calling the deprecated `backlogit_stash_remove`.
That is a different contract surface and a different kind of work, so it was
**captured, not fixed** — stash `8D570CF8`, with per-field source refs and PR 372
recorded, thread ID `N/A`. This is the first time the policy has been applied to
its own remediation.

## PR #372 review-fix cycle 2 (2026-08-19, HEAD 47d5ad3e)

One P1: the split's **owner provenance inventories** were contradictory in both
directions at once, and both errors have a single cause.

* `134.012-T` still listed `134.002-T` as an authoring task for a
  "provisional-priority carve-out reference" — but 002's only behaviours, **B11**
  (Role Boundary verb list) and the **B12** provisional-priority carve-out, had
  *both* moved to `134.013-T` in cycle 1.
* `134.013-T` omitted `134.005-T` — even though **B1**'s subset includes the
  circuit-breaker `[N]` carrier and 013's own C1-GATE test already asserts the
  gate across *"both policy surfaces"*.

So one file claimed an owner it no longer had while the other disowned an owner
its own test depended on. Neither inventory was re-derived when the split moved
the behaviours; both were carried across as **edited copies of the pre-split
list**, which is stale by construction, because a split moves behaviours and the
owner union moves with them.

**How I fixed it, and why the method mattered more than the answer.** The review
supplied the expected sets. I derived them independently from the B1–B18 mapping
instead of applying them — and the first mechanical parse came back **wrong**,
because the regex swept task numbers out of the `NOT` exclusion clauses (`NOT 005`,
`Deliberately NOT asserted on 001, 006 or 007`). It reported B4 as including 005
and B6 as including 001/006/007, all of which the map explicitly *excludes*. A
parse that reads exclusions as inclusions produces a superset that looks
plausible and is unfalsifiable by eye. Re-parsed with negation handling and an
evidence segment printed per behaviour, the unions came out **012 → {001, 004,
005, 006, 007, 008}** and **013 → all nine**, matching the review. Two narrowings a
hand-edit reliably gets wrong are now written down: 005 owns only B3 and the B9
`[G]` guard in 012 (H7 excludes it from B4; it performs no thread operation so it
is excluded from B7), and 007 contributes B10 to 013 through **pr-lifecycle only**,
not fix-ci.

**Why this is the failure the matrix consolidation was supposed to have ended.**
The CARRIER-SET RESOLUTION rule *already* forbids hardcoding a carrier list — and
these inventories **were** hardcoded carrier lists. They just described carriers
by their *authoring task* rather than by their *surface*, so they did not look
like the thing the rule prohibits. The rule got read as being about the **shape**
of the data rather than about its **provenance**. That is the durable lesson: a
derived value that is *stored* rather than *computed* is a cache, and every cache
needs an invalidation rule. The split was the invalidation event and nothing
recomputed. `134.011-T` now states **OWNER INVENTORIES ARE DERIVED, NEVER
DECLARED** once, in the allocation block, with the three current unions and the
precedence rule: where an inventory and the mapping disagree, **the mapping wins
and the inventory is the defect** — never the evidence.

This also extends the running granularity lesson. Cycle 1's was *internal
consistency is not executability*. This one is narrower and sharper: **consistency
checks that compare two restatements cannot detect that both are restatements.**
Both inventories were internally coherent and mutually plausible; only rederiving
from the owner could tell either was wrong.
