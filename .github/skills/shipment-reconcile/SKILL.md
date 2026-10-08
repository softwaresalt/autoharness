---
name: shipment-reconcile
description: "GI/GR reconciliation gate for shipment manifests — verifies every manifest item exists in queue (pre-mode) or archive (post-mode) with the expected status, and closes shipments with the single-artifact safe-close procedure that archives ONLY manifest item IDs and closes the shipment record via live `shipped` -> verify -> explicit archive -> verify `archived_status: shipped`, instead of the destructive cascade backlogit_ship_shipment — except for the narrow, machine-verified P-015 engine-inertness case, where the cascade op is the permitted and independently-verified close path."
---

# Shipment Reconcile

Provides a double-entry (GI/GR) integrity check for shipment manifests. Run
`mode: pre` before closing a shipment and `mode: post` after the archive +
restore steps complete. Run `mode: safe-close` **in place of** the destructive
cascade `backlogit_ship_shipment` call to archive only the shipment manifest's
explicit item IDs one artifact at a time, verifying after each that the parent
feature and any unshipped sibling tasks survive — safe-close's own Step 0 first
runs the P-015 verified engine-inertness classification and, only when every
precondition holds, delegates to the Cascade Close Sub-Procedure instead.

> **Why safe-close exists.** `backlogit_ship_shipment` treats a shipment as a
> proxy for its covering feature and cascade-archives the whole feature subtree.
> For **partial-feature** shipments (which intentionally exclude the parent
> feature and some sibling tasks) this is destructive: it archives the parent
> feature and orphans unshipped siblings that are **not in the shipment
> manifest**. Safe-close prevents that corruption instead of merely detecting it
> after the fact. See **P-015** in `workflow-policies` for the governing policy.

## When to Use

* **Ship Step 6 closure** (mandatory): run `mode: pre` with
  `expected_status: done` (the pre-close invocation; any other value skips
  Pre-Mode step 2b and makes every member strict-scalar), then `mode: safe-close`
  **instead of** the cascade `backlogit_ship_shipment` call, then `mode: post`.
  Safe-close's own Step 0 selects the close path from the machine-checkable
  P-015 classification; it archives manifest item IDs individually and never
  calls the cascade op directly **unless** that classification confirms the
  narrow P-015 `CASCADE` exception, in which case the Cascade
  Close Sub-Procedure runs (and is itself independently verified) instead.
* **Ship Step 0.5** (sanity check): pre-mode at intake with `expected_status: queued`
  (or `active` if the shipment was already claimed in a prior session)
  to catch Stage-side over-inclusion before any build work begins. At
  intake every member is strict-scalar, so a `done` member is
  `status-mismatch` even when its record was relocated to `archive/`; a
  resumed session whose tasks have diverged is not an intake case (see Ship's
  Step 0.5 scope note).
* **Ad-hoc audit**: any time an operator suspects manifest drift.
* **`mode: detect-mixed-role`** (operator-invoked, READ-ONLY, no lock, no mutation):
  any time an operator wants a diagnostic scan for the queued-with-active-work /
  mixed-role silently-dropped-claim signature (936C68F3 part 2, re-scoped
  report-only per 013-DL Addendum G / 112-F) across one shipment or ALL
  shipments. Composed entirely from EXISTING read-only backlogit reads
  (`backlogit_list_shipments` + per-shipment/per-task status reads via
  `backlogit_get_shipment` and per-task `backlogit_get_item`). EMITS a report-only
  diagnostic plus operator-remediation guidance. NEVER mutates, NEVER calls
  `backlogit_claim_shipment` or any status-write operation, and needs no
  `file-lock` acquisition because no backlog/shipment artifact is ever
  mutated — the mode's own diagnostic report, audit-log entry, and telemetry
  event (steps 6–8 below) are additive-only writes to non-backlog-state
  locations, never applied to a queue/archive item.

## Inputs

| Parameter | Required | Values | Notes |
|---|---|---|---|
| `mode` | yes | `pre` \| `post` \| `safe-close` \| `detect-mixed-role` | Controls which check/close/detect phase runs |
| `shipment_id` | yes for `pre`/`post`/`safe-close`; optional for `detect-mixed-role` | e.g. `004-S` | The shipment to reconcile; for `detect-mixed-role`, omit to scan ALL shipments via `backlogit_list_shipments` |
| `expected_status` | pre-mode only | `queued` \| `active` \| `done` | `queued` for fresh intake; `active` when shipment already claimed in a prior session; `done` for pre-ship check (the pre-close invocation: enables Pre-Mode step 2b and the Member-Class Status Contract's `qualifying-feature` row) |
| `merge_commit_sha` | post-mode and safe-close | git SHA | The merge commit that closed the PR; recorded on archived items for traceability |

## Output

A structured **reconciliation report** stored at
`.backlogit/reconcile/{shipment_id}-{mode}-{timestamp}.md`.

Every item in the manifest is classified as one of:

| Classification | Pre-Mode Meaning | Post-Mode Meaning |
|---|---|---|
| `matched` | Record present in `queue/` or `archive/` AND its declared status is valid for the item's member class (Member-Class Status Contract below) | Archive file present for this item |
| `pre-archived` | Record declares `status: archived` under the Member-Class Status Contract's `strict-scalar` row — truly archived before this shipment ran; treated as valid | N/A (all items are expected in archive; use `matched` / `missing`) |
| `qualifying-feature-pre-archived-anomaly` | A qualifying feature declares `status: archived` (Member-Class Status Contract below) — accepted, but always reported and named in the recommendation | N/A |
| `missing` | No queue or archive file found for this manifest item | Archive file not found for this manifest item |
| `status-mismatch` | Record present, but its declared status halts under the item's member class (Member-Class Status Contract below), wherever the record resides | N/A (post-mode does not check status fields) |
| `orphan` | Queue file declares this `shipment_id` in its frontmatter but is NOT in the manifest | N/A (post-mode does not scan queue files) |

> Classification semantics are mode-dependent. Pre-mode checks each item's
> declared status, wherever the record resides, against its member class;
> post-mode checks the archive for file presence only. Safe-close step 4 and
> the Cascade Close Sub-Procedure's pre-archived-member preamble still use
> `pre-archived` as a location label (the record resides in `archive/`);
> that usage is unchanged and is not the Pre-Mode class above.

### Member-Class Status Contract (Pre-Mode; authoritative)

<!-- member-class-status-contract:BEGIN -->
This block is the **single authoritative statement** of which declared
`status` values a manifest member may carry when Pre-Mode step 3 classifies
it. The per-item classification table above, Safe-Close Step 0(b), and the
Cascade Close Sub-Procedure apply it by reference and never restate the
declared-status rule or the member-class table. (The "not truly archived"
sentence at Step 0(b) and in the Cascade preamble applies the rule to the
two-set gate; it is deliberate and pinned there by 147-F.)

**Declared-status rule (R-1).** Declared `status` is read from the record's
own frontmatter `status` field — never inferred from, nor substituted by,
which of `queue/`/`archive/` currently holds the record. Location alone is
never sufficient. Where a record was found (`queue` or `archive`) is recorded
as a descriptive **location label** beside the declared status, never
instead of it; a record found in neither directory is `missing`.

**Member-class selection.** The `qualifying-feature` row applies only to the
pre-close invocation (`expected_status: done`) under a Pre-Mode step 2b
`CASCADE` verdict, and only to a member whose ID is in the qualifying
feature set recorded by Pre-Mode step 2b. Membership comes from that set
alone — never from an ID pattern, an `artifact_type` value, or manifest
position. Every other member, and every member of every other invocation
(intake with `expected_status: queued` or `active`, a step 2b `SAFE_CLOSE`
verdict, or any classifier error, ambiguity, or unresolved precondition
recorded as `SAFE_CLOSE`), uses the `strict-scalar` row: the
single-`expected_status` semantics, unchanged. Row selection follows step
2b's classifier verdict, not the path Step 0(c) finally selects: if the
engine-semantics gate then selects `SAFE_CLOSE`, safe-close archives every
manifest member individually, a qualifying feature included, so a feature
accepted here is still closed safely.

| Member class | `matched` | Tolerated — reported, never halts | HALT (`status-mismatch`) |
|---|---|---|---|
| `qualifying-feature` | `active`, `done` | `archived` → `qualifying-feature-pre-archived-anomaly` | `queued`; any other value (R-5) |
| `strict-scalar` | the invocation's `expected_status` | `archived` → `pre-archived` | any other value (R-5) |

"Any other value" is every declared status a row lists in neither its
`matched` nor its tolerated cell — including `blocked`, `review`, a future
lifecycle value such as `parked` or `hold`, an empty or missing `status`, and
a non-string YAML value. Each is an explicit `status-mismatch` HALT (R-5),
never silently absorbed. The `qualifying-feature-pre-archived-anomaly` label
is never folded into `pre-archived`: an archived qualifying feature is
accepted, because the cascade forces every qualifying feature member through
`done` regardless of its pre-close status (Cascade Close Sub-Procedure step
3), but it is always surfaced in the report and the recommendation (R-2).

**Classifier contract (fail closed).** Under a step 2b `CASCADE` verdict, an
empty qualifying feature set (I-2), or a manifest member with
`artifact_type: feature` whose ID is absent from that set (I-1), is a
classifier contract violation: halt with
`RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT`. Neither case ever falls through
to the `strict-scalar` row.

**Shipment record.** Not a manifest member, so no row here: it is classified
only by the Shipment-Record-Status Classification below, with its four labels
(`record-consistent`, `record-queued-with-active-work`,
`record-blocked-with-active-work`, `record-blocked-with-done-work`) and no
parallel terms. Under backlogit, a persisted `blocked` shipment record is a
reportable anomaly, never a waitable state: backlogit's `ShipmentStatus` has
no `blocked` constant, so the record has no legal outbound transition
(`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`). The
report names it; Pre-Mode never waits on, retries, or transitions it.
<!-- member-class-status-contract:END -->

### Shipment-Record-Status Classification (record scope, distinct from the six per-item classifications above)

In addition to the six per-item classifications, pre-mode also classifies the
shipment **record's own** `status` against the aggregate status of its manifest
**task** items. **Task-artifact filter (mandatory)**: the manifest `items` list
is untyped and may include the covering feature id (e.g. a fallback-assembled
manifest); this classification aggregates only items whose `artifact_type` is
`task` (already read from each item's frontmatter during the per-item check
above — no new read), excluding any non-task entry, so a covering feature that
happens to be `active`/`done` outside the shipment's own
scope can never be misread as a "conflicting task". This mirrors the task-artifact
filter the Ship agent's intake early-warning already applies to
`custom_fields.items` (`templates/agents/_ship.agent.md.tmpl`). **Scope**: the
three named inconsistency cases below apply only when the
record's own status is `queued` or `blocked` — the two
statuses where a manifest task already being `active`/`done`
is itself the drift signal (the queued/blocked record has not "caught up" to its
tasks). **`blocked` itself is a non-standard/legacy value**: backlogit
1.8.0's `ShipmentStatus` enum is only `queued|active|shipped|abandoned` (see
`docs/compound/2026-05-07-backlogit-shipment-status-constraints.md`) — a
persisted `blocked` record can still exist in real workspaces from a
historical `backlogit move` CLI defect that silently accepted invalid status
writes. Pre-mode's `record-blocked-with-active-work`/`record-blocked-with-done-work`
cases below classify such a leftover record defensively (it is real data that may
be present); `mode: detect-mixed-role`'s `malformed-legacy` classification
(defined further below, in the mode's own classification section) reports the
identical underlying fact — a non-standard/legacy status value, never a normal
current-day state — for a different manifest scan. Both agree `blocked` is never fabricated or
transitioned into/out of; only the case label differs by mode. When the record's
own status is `active` or `done`
(or archived), the record is **by definition** `record-consistent` for this
check — an `active` record is the normal in-progress state while its
tasks move `queued` → `active` → `done`, and an
`done`/archived record reflects a shipment already closed. This is an
explicit scope boundary, not a silent default: the four cases below are
**mutually exclusive** because they are evaluated in this fixed order and every
record status value maps to exactly one of them.

| Classification | Condition |
|---|---|
| `record-consistent` | Record status is `active` or `done`/archived (always consistent — the normal in-progress/closed lifecycle, out of scope for this check), OR record status is `queued`/`blocked` and none of the three inconsistency conditions below match (e.g. record `queued` with all task items `queued`) |
| `record-queued-with-active-work` | Record status is `queued` AND at least one **task-artifact** manifest item is `active` or `done` — the classic "silently-dropped claim" inconsistency |
| `record-blocked-with-active-work` | Record status is `blocked` AND at least one **task-artifact** manifest item is `active`. **Precedence**: when a `blocked` record has BOTH an `active` task and a `done` task, classify here — active work takes precedence over `record-blocked-with-done-work` below, because it is the more severe/earlier-stage drift signal |
| `record-blocked-with-done-work` | Record status is `blocked` AND no **task-artifact** manifest item is `active` AND at least one **task-artifact** manifest item is `done` |

These four cases are mutually exclusive: every possible record-status value
(`queued`, `active`, `blocked`, `done`)
is covered — `active`/`done` always resolve to
`record-consistent`, and for `queued`/`blocked` the
active-over-done precedence rule (applied only to task-artifact items) guarantees
exactly one of the remaining three cases applies. This check is
**detect-and-report only — NO auto-repair**: it
never mutates the shipment record or any task; operators must manually
reconcile.

The report ends with a `recommendation`:

* `PROCEED` — all items are `matched`, `pre-archived`, or
  `qualifying-feature-pre-archived-anomaly` (named in the recommendation) AND the
  shipment-record-status classification is `record-consistent`; no action needed
* `HALT — operator reconcile required` — one or more missing, status-mismatch, or orphan items, OR a non-`record-consistent` shipment-record-status classification (pre-mode)
* `HALT — restore archives` — missing archive files or unrestored deletions (post-mode)
* `CLOSED` — safe-close archived every manifest item individually, archived the
  shipment record itself, and the observation set (parent feature + unshipped siblings)
  remained baseline-invariant
* `DISPOSITION_COMPLETE` — the Linked-Deliberation Disposition step assigned one
  outcome to every disposition-set deliberation and verified every archive it performed
* `HALT — linked-deliberation disposition failed {id}` — the Linked-Deliberation
  Disposition step failed before post-mode; do not commit a torn disposition
* `HALT — cascade detected, revert required` — safe-close found an observation-set artifact changed outside `closure_scope(S)`; D6 governs any rollback before any commit

For `mode: safe-close`, the report also records the **observation set** (the parent
feature file and every unshipped sibling task file watched for baseline invariance) and,
per manifest item, whether it was `matched` (archived by this run) or
`pre-archived` (already archived before this run; skipped to avoid
double-archival and false-positive cascade flags).

### Mixed-Role Detection Classification (`mode: detect-mixed-role` only, distinct from the record-scope classification above)

This classification is **separate** from the "Shipment-Record-Status
Classification" above: that check compares a single shipment record's own
status against the *aggregate* active/done state of its manifest tasks (four
record-scope cases). This check instead classifies **each manifest task
individually** by its per-task **ROLE**, to precisely describe the
mixed-role "silently-dropped-claim" signature — a `queued` shipment
record whose manifest tasks have kept progressing to `active` and
even fully `done`/archived while the record itself never advanced.
Per **013-DL Addendum G** (re-scoped by Copilot PR #304 finding 1), this
classification is used **ONLY to DESCRIBE** the inconsistency in a report —
**NEVER** to gate a mutation. There is no `--confirm` flag because nothing is
ever mutated.

**Per-task ALLOWED ROLE** (a task-artifact manifest item must be a UNIQUE,
NON-CONFLICTING record for exactly one of these three roles):

| Role | Definition |
|---|---|
| `live-queued` | UNIQUE record in `.backlogit/queue/` with `status: queued`; NO archive record for the same id |
| `live-active` | UNIQUE record in `.backlogit/queue/` with `status: active`; NO archive record for the same id |
| `archived-completed(done)` | UNIQUE record in `.backlogit/archive/` ONLY, in EITHER valid representation: (a) TERMINAL RELOCATION — `status: done` (provenance `archived_status`/`archived_from` NOT required), OR (b) EXPLICIT ARCHIVAL — `status: archived` AND `archived_status: done` AND valid, well-formed `archived_from` provenance; NO conflicting live queue record for the same id |

**Per-item ANOMALY** (fail closed — REPORT and HALT on ANY of these; a
manifest task satisfying none of these is role-clean):

| Anomaly | Definition |
|---|---|
| `duplicate` | Same task id present in BOTH `.backlogit/queue/` AND `.backlogit/archive/` |
| `conflicting` | Queue status disagrees with the declared role, an archive record exists alongside a live queue record, or a live `status: done` record is found in the QUEUE (a completed task lives ONLY in `archive/`, never live-done in `queue/`) |
| `missing` | Manifest task id has no file in either `.backlogit/queue/` or `.backlogit/archive/` |
| `malformed-provenance` | An archive record with `status: archived` is missing or has ill-formed `archived_status`/`archived_from` (a `status: done` archive record legitimately carries no provenance and is NOT malformed) |
| `any-other-archived-status` | An archive record whose status is NEITHER `done` NOR `archived`-with-`archived_status: done` |
| `orphan` | A queue file declares this `shipment_id` in its frontmatter but is NOT present in the manifest `items` list (reuses the pre-mode orphan-scan definition) |
| `out-of-role` | Task status falls outside the allowed lifecycle set `queued` \| `active` \| `done`/`archived` (e.g. a non-lifecycle or otherwise malformed status value) |
| `torn-partial` | Any other ambiguous, incomplete, or inconsistent signal for the task that cannot be cleanly assigned to a role (e.g. partially-written frontmatter) |

**Malformed-legacy shipment record**: backlogit 1.8.0 has NO `blocked`
shipment status (`ShipmentStatus` is only `queued|active|shipped|abandoned`).
A shipment record whose persisted status is anything other than a valid 1.8.0
lifecycle value (e.g. a legacy `blocked` value) is described in the report as
`malformed-legacy` — REPORT it, HALT, and never fabricate a `blocked->queued`
or any other transition. This is the same underlying fact the pre-mode
Shipment-Record-Status Classification table above documents for its own
scan (`record-blocked-with-active-work`/`record-blocked-with-done-work`
defensively classify a leftover legacy `blocked` record because it
may exist in real workspaces); the two modes describe the identical
non-standard value under mode-appropriate labels — never treat a persisted
`blocked` value as a normal current-day state in either mode.

**Mixed-role signature**: a shipment record `queued` whose
task-artifact manifest items (filtered by `artifact_type` to exclude any
non-task entry, e.g. a covering feature id, mirroring the existing
task-artifact filter above) include AT LEAST ONE `live-active` or
`archived-completed(done)` role task, with every task otherwise role-clean
(no anomaly), is the reportable "silently-dropped-claim" signature. On ANY
per-item anomaly (duplicate / conflicting / missing / malformed-provenance /
any-other-archived-status / orphan / out-of-role / torn-partial) or any other
ambiguity, REPORT the specific anomaly and HALT — never mutate, never
attempt to resolve or repair.

**Detection outcomes** (structured audit entry + telemetry event on every
run — see "Mixed-Role Detection Audit + Telemetry" below): exactly one of
`DETECTED` (scan completed; no mixed-role signature or anomaly found —
`record-consistent`, nothing to report), `REPORTED` (scan completed; the
mixed-role signature and/or one or more per-item anomalies were found and
described in the report), or `DEGRADED` (backlogit was unreachable; the
degraded condition is reported and the scan halts). There is **NO**
`succeeded` / `repaired` / `refused` / two-active outcome — nothing is ever
mutated or repaired by this mode.

## Behavioral Constraints

* **Report-and-halt only.** This skill NEVER modifies the shipment manifest or
  queue/archive files **outside the safe-close mode's manifest-scoped archival and the
  separately sanctioned INV-12 Linked-Deliberation Disposition step**.
  In pre- and post-mode it only reports; operators must manually reconcile via
  existing backlog tools and re-invoke Ship Step 6.
* **Manifest-scoped mutation only.** In `mode: safe-close`, the ONLY artifacts
  safe-close steps 1–10 may move or archive are the shipment manifest's explicit item IDs and
  the shipment record itself (`{shipment_id}`). It must NEVER archive the parent
  feature or any sibling task that is not in the manifest. It never calls the cascade
  `backlogit_ship_shipment`; the shipment record is closed as its own single artifact.
  The INV-12 Linked-Deliberation Disposition step is separately sanctioned: it
  runs only after the selected close path returns `recommendation: CLOSED`, never
  widens `closure_scope(S)` or `allowed_ids(S)`, and archives a validated linked
  deliberation only through a single-artifact, non-cascading archive, one ID at a time.
* **No prune / no auto-repair.** Auto-mutation of the manifest itself is reserved
  for a future version. Safe-close never prunes the manifest and never
  auto-deletes non-manifest artifacts; on cascade detection it reverts the
  unintended change and halts.
* **Single-writer lock.** When invoked from Ship Step 6, this skill holds the
  `.backlogit/queue/{shipment_id}.md` file lock (via the `file-lock` skill) for
  the duration of pre-mode → safe-close → post-mode. See lock protocol in the
  Required Protocol section below.
* **Halt on RECONCILE_FAIL.** Do not proceed to safe-close unless pre-mode
  returns `PROCEED`. Do not commit backlog state if safe-close returns
  `HALT — cascade detected, revert required` or if the Linked-Deliberation
  Disposition step returns `HALT — linked-deliberation disposition failed {id}`.
  Surface the report path to the operator.
* **`mode: detect-mixed-role` is strictly READ-ONLY.** It NEVER mutates any
  shipment record or task, NEVER calls `backlogit_claim_shipment` (no
  re-claim, no repair mode — a record-only forward re-claim of a
  queued-with-active-work shipment is UNSUPPORTED by backlogit 1.8.0; see
  "Operator-Remediation Guidance" below), and requires NO `file-lock`
  acquisition because no backlog/shipment artifact is ever mutated (its own
  diagnostic report, audit-log entry, and telemetry event are additive-only
  writes to non-backlog-state locations). DEGRADED (backlogit unreachable)
  is REPORTED and the mode HALTS — it never guesses or acts blind.

## Required Protocol

### Pre-Mode

1. **Acquire single-writer lock** (Ship Step 6 invocations only, not intake):
   Invoke the `file-lock` skill to acquire `.backlogit/queue/{shipment_id}.md`.
   If lock acquisition fails, count as a session stall (circuit-breaker protocol)
   and prompt the operator.

2. **Load manifest** via `backlogit_get_shipment(shipment_id)`.
   Extract the `items` list.

   2b. **Classify the close path for gating** (pre-close invocation only,
   `expected_status: done`): run the machine-checkable P-015 close-path
   classification exactly as Safe-Close Step 0(c) describes it — a
   `classify_shipment_close_path(manifest_items, workspace_backlog_dir)`-shaped function
   where a Python implementation is installed, the equivalent structural
   check against `.backlogit/queue/` + `.backlogit/archive/`
   otherwise — over the manifest loaded in step 2, under the lock acquired in
   step 1. Step 0(c) is the specification; this step does not restate it.
   The in-process run is deliberate: Pre-Mode runs before any closure
   evidence record exists, writes its verdict only to the Pre-Mode report
   (step 6), and only selects contract rows;
   `autoharness shipment cascade-close --classify-only` (Step 0(c)) remains
   the only source of a recorded verdict that a close path acts on.
   Record:
   * the verdict, `CASCADE` or `SAFE_CLOSE` (a classifier error, exception,
     or ambiguous result is recorded as `SAFE_CLOSE`);
   * the qualifying feature set (empty unless the verdict is `CASCADE`);
   * a reason string (R-3): the implementation's own reason, verbatim, where
     it supplies one; otherwise an explicitly authored reason naming the
     precondition that decided the verdict; otherwise the literal label
     `classifier-reason-unavailable` — never a blank field.

   For an intake invocation (`expected_status: queued` or
   `active`) this step does not run: record the verdict
   `not-evaluated` with the reason `intake-invocation`, and every member uses
   the Member-Class Status Contract's `strict-scalar` row. This step is
   **advisory for gating only**: it selects Member-Class Status Contract rows
   and nothing else. Step 0(c) remains authoritative for the pre-close
   snapshot, the engine-semantics gate, close-path selection, and the two-set
   gate, and halts with `RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT` when its own
   classification disagrees with the verdict or qualifying feature set
   recorded here. Classification is read-only, so Pre-Mode stays
   detect-and-report only.

3. **Check each manifest item** (applies the Member-Class Status Contract in
   the Output section above):
   * Locate the record in `.backlogit/queue/{id}.*` and
     `.backlogit/archive/{id}.*`. Record the directory that holds it
     as the item's location label (`queue` or `archive`). If no file exists
     in either location, classify `missing`. A record found in both
     directories, or whose frontmatter cannot be read or parsed, is
     `status-mismatch` with the location label `ambiguous` or `unreadable`
     and its declared status and member class reported as `unavailable`:
     never guess which copy or value is authoritative (Step 0(b) halts on
     the same ambiguity). Step 5 aggregates only members whose frontmatter
     was read; the gate halts on the `status-mismatch` regardless.
   * Otherwise, read its frontmatter (including `status` and `artifact_type`)
     from the one directory that holds it. Location never short-circuits this read:
     an archive-resident record is classified by its declared status exactly
     like a queue-resident one.
   * Select the member's class from the step 2b verdict and qualifying
     feature set, then classify its declared status as `matched`,
     `pre-archived`, `qualifying-feature-pre-archived-anomaly`, or
     `status-mismatch` per the contract. Under a `CASCADE` verdict, an empty
     qualifying feature set or a feature member outside it halts with
     `RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT` instead.

4. **Orphan scan**:
   Scan `.backlogit/queue/` for any files whose YAML frontmatter declares
   `shipment_id: {shipment_id}` but whose ID is NOT present in the manifest `items` list.
   Classify each such file as `orphan`.

5. **Shipment-record-status classification** (reuses in-hand data — NO new scan):
   Using the shipment record's own `status` already loaded via `backlogit_get_shipment`
   in step 2, and the manifest items' statuses already read in step 3, classify the
   record scope per the Shipment-Record-Status Classification table in the Output
   section above, evaluated in this order. **Filter to task artifacts first**: the
   manifest `items` list is untyped and may include the covering feature id (e.g. a
   fallback-assembled manifest); reuse the `artifact_type` already read from each
   item's frontmatter in step 3 to exclude any non-task entry before aggregating
   task statuses below — the same task-artifact filter the Ship agent's intake
   early-warning applies to `custom_fields.items` (`templates/agents/_ship.agent.md.tmpl`)
   — so a covering feature that is `active`/`done` outside the
   shipment's own manifest scope can never be misread as a "conflicting task" and
   falsely halt an otherwise-consistent shipment.
   * Record `active` or `done`/archived →
     `record-consistent` (always — this check is scoped to `queued`/
     `blocked` records only; an active/done record is the normal
     in-progress/closed lifecycle state, not evaluated further).
   * Record `queued` AND any manifest **task** is `active` or
     `done` → `record-queued-with-active-work`.
   * Record `blocked` AND any manifest **task** is `active` →
     `record-blocked-with-active-work` (takes precedence over the case below when
     both an active and a done task are present).
   * Record `blocked` AND no task `active` AND any manifest
     **task** is `done` → `record-blocked-with-done-work`.
   * Record `queued` or `blocked` matching none of the above
     → `record-consistent` (e.g. record `queued` with all tasks
     `queued`).
   This step is **detect-and-report only — NO auto-repair**: it never mutates the
   shipment record or any task.

6. **Produce report** and store at
   `.backlogit/reconcile/{shipment_id}-{mode}-{timestamp}.md`. The
   report records step 2b's verdict, its reason string, and the qualifying
   feature set, and, for every manifest member, its location label, declared
   status, member class, and classification. An archived qualifying feature
   appears under `qualifying-feature-pre-archived-anomaly`, and a persisted
   `blocked` shipment record is named as a legacy anomaly.

7. **Gate decision**:
   * If all items are `matched`, `pre-archived`, or
     `qualifying-feature-pre-archived-anomaly`, no orphans exist, AND the
     shipment-record-status classification is `record-consistent` →
     `recommendation: PROCEED`, naming every
     `qualifying-feature-pre-archived-anomaly` item so the anomaly is reported
     rather than absorbed
   * If step 3 halted with `RECONCILE_FAIL_PREMODE_CLASSIFIER_CONTRACT` →
     `recommendation: HALT — operator reconcile required`, naming the step 2b
     verdict, its reason, the qualifying feature set, and the offending member
   * If any `missing`, `status-mismatch`, or `orphan` items exist, OR the
     shipment-record-status classification is `record-queued-with-active-work`,
     `record-blocked-with-active-work`, or `record-blocked-with-done-work` →
     `recommendation: HALT — operator reconcile required`, naming the shipment id,
     the record's own status, and the conflicting manifest task ids
   * On `HALT`: emit the report path, release the lock, and halt with
     `RECONCILE_FAIL`. Do NOT call `backlogit_ship_shipment`.
   * On `PROCEED` from Ship Step 6: retain the lock until post-mode completes.

### Post-Mode

1. **Verify archive presence**:
   List `.backlogit/archive/` and confirm a file exists for the shipment itself
   (`{shipment_id}.*`).

2. **Per-item archive check**:
   For every item in the manifest, verify a corresponding archive file exists.
   If any are absent, flag them in the report.
   The same per-item check covers every Linked-Deliberation Disposition
   `archived` outcome: verify each such deliberation's archive file exists and
   flag any absence in the report. Retained (`retained_*`) outcomes are not
   archive-checked.

3. **Deleted-file guard** (known `backlogit_ship_shipment` quirk — see P-007):
   Run `git status -- ".backlogit/archive/"` and inspect for deletions.
   If any archive files are reported as deleted, recommend that the invoking agent
   obtain a fresh, live G1 approval (per P-007's G1-G9 approval-gate protocol,
   matched to this shipment ID and the EXACT set of deleted paths just detected),
   revalidate immediately before restoring (re-run this same `git status` check
   and confirm the approved paths still report a deletion with no change to the
   set — a stale approval, where a path was recreated/modified since approval,
   MUST NOT be used), and only then run
   `git restore -- <deleted-path-1> <deleted-path-2> ...` limited
   to that exact pathspec — never the whole `.backlogit/archive/` directory,
   which could discard or stage unrelated tracked modifications below it. Never
   recommend the restore as an unconditional next step, and never recommend an
   unscoped directory-level restore or stage — the recommendation itself is
   evidence-only guidance, not an authorization to run it.
   The queue-to-archive moves made by the Linked-Deliberation Disposition step's
   `archived` outcomes are expected: this guard never flags them as deletions or
   unexpected changes.

4. **Produce post-mode report** per the same schema.

5. **Gate decision**:
   * If all archive files present and no deletions detected → `recommendation: PROCEED`
   * If missing archive files or unrestored deletions detected →
     `recommendation: HALT — restore archives`
   * Retained (`retained_*`) Linked-Deliberation Disposition outcomes never
     change this gate: they are reported by the disposition step, are not
     missing archive files, and are not deletions.
   * On `HALT`: release the lock and report. Ship must restore archives before committing.

6. **Release lock** (acquired in step 1 of pre-mode):
   Invoke `file-lock` release for `.backlogit/queue/{shipment_id}.md`.
   If release fails, log a warning — stale locks are operator-recoverable.

### Safe-Close Mode

Runs **in place of** the destructive cascade `backlogit_ship_shipment` call —
**except** in the narrow P-015 verified engine-inertness case selected by
Step 0 below, where the cascade op is the *permitted* close path and safe-close
steps 1–10 are skipped entirely. Archives only the shipment manifest's explicit
item IDs, one artifact at a time, verifying after each archival that the parent
feature and any unshipped sibling tasks survive. Invoked between pre-mode
(`PROCEED`) and post-mode, under the lock pre-mode already holds. If invoked
standalone, acquire the lock per pre-mode step 1 first and release it on
completion.

0. **Load manifest, snapshot pre-close state, then select close path (P-015
   flat-manifest `CASCADE` exception — select from the verified check,
   never from prose alone)**: safe-close is the default.
   a. **Load the manifest first**, regardless of which path is ultimately
      selected: invoke `backlogit_get_shipment(shipment_id)` and extract the
      `items` list. This load happens here in Step 0 — not deferred to step 1
      below — because the classification in (c) and the cascade
      pre/post-comparison in the Cascade Close Sub-Procedure both require it,
      and the cascade path skips steps 1–10 entirely.
   b. **Snapshot pre-close `parent_id` and declared `status` for
      every explicit manifest member regardless of `artifact_type`** (task,
      feature, or any other explicit member; the flat `required_ids(S)` ranges
      over every manifest item) by reading each member's current frontmatter from
      whichever of `.backlogit/queue/` or
      `.backlogit/archive/` currently contains it — a manifest
      member may already be
      pre-archived when this snapshot runs (see the
      Cascade Close Sub-Procedure's pre-archived-member preamble below), and
      its snapshot must still be captured from wherever it actually resides.
      If a member's record is found in **both** locations (an
      ambiguous/torn state) or in **neither** (missing), halt immediately
      with `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS` or
      `RECONCILE_FAIL_SNAPSHOT_MISSING` respectively — never guess which
      copy or location is authoritative. Retain this snapshot in memory
      for the duration of this close operation; it is the baseline the
      Cascade Close Sub-Procedure's step 4 parent-preservation check and
      step 3 declared-status two-set gate both compare against, and it must
      be captured **before** any mutating call (cascade or otherwise) runs,
      never reconstructed after the fact.

      **Declared `status` follows the Member-Class Status Contract's
      declared-status rule (R-1)** — the same rule Pre-Mode step 3 applies.
      A record residing in
      `.backlogit/archive/` while declaring `status: done` is
      **not** truly archived; only a declared `status: archived` counts as
      truly archived for the Cascade Close Sub-Procedure's step 3 gate
      below. This declared-status
      snapshot MUST be captured here, in Step 0(b), **before** the cascade
      invocation, for the identical reason already stated for `parent_id`:
      `status` is the very field the cascade mutates, so a post-close read
      would report `archived` for everything the cascade just archived,
      collapsing `required_ids` (Cascade Close Sub-Procedure step 3) to
      empty and silently disabling the completeness check entirely. Never a
      freshly-read or assumed value.
   c. **Classify the close path**: run the machine-checkable classification
      described in P-015 over the manifest `items` loaded in (a). Workspaces
      with a Python implementation installed reuse a
      `classify_shipment_close_path(manifest_items, workspace_backlog_dir)`-shaped
      function (this self-hosting repository's own implementation lives at
      `src/autoharness/gates/shipment_closure.py`); other workspaces implement
      the equivalent check directly against `.backlogit/queue/` +
      `.backlogit/archive/`. The classifier has exactly two outcomes here:
      `CASCADE` and `SAFE_CLOSE`.

      This is the **INV-6 engine-inertness containment gate**. The descendant
      walk stays in place because it measures the cascade instrument's reachable
      blast radius, but it does **not** define closure scope: `manifest_scope(S)`
      remains exactly `items(S)`, `closure_scope(S)` remains `items(S) ∪ {S}`,
      `allowed_ids(S)` and `required_ids(S)` remain the flat postcondition sets,
      and an inert out-of-manifest descendant enters none of
      `manifest_scope(S)`, `closure_scope(S)`, `allowed_ids(S)`, or
      `required_ids(S)`.

      `CASCADE` is permitted only when every artifact in the `parent_id`
      descendant set enumerated for each qualifying root feature member —
      i.e., every artifact transitively reachable from that feature via
      `parent_id`, exactly the set `classify_shipment_close_path` returns as
      `out_of_manifest_descendant_ids` — that lies outside `closure_scope(S)`
      is engine-inert. This gate is scoped precisely to that `parent_id`
      descendant set and never to `validated_linked_deliberations(S)`: under
      the verified flat engine-semantics line, backlogit leaves linked
      deliberations independent. Their disposition is governed by **INV-12**
      after the close-path gate, not by this INV-6 engine-inertness gate.
      Engine inertness requires
      the record's own parsed frontmatter value to satisfy
      `isinstance(status, str) and status == "archived"`. This is an exact
      parsed-scalar match: no .lower(), no .strip(), no casefold, no alias
      table, and no str() coercion may broaden it. Non-string parses such as
      `status: yes` or a bare `status:` fail closed and force `SAFE_CLOSE`;
      `Archived`, `ARCHIVED`, and the YAML-quoted literal
      `status: " archived "` also force `SAFE_CLOSE`. Because the comparison
      happens after YAML parsing, lexically distinct but YAML-equivalent values
      that parse to exactly `"archived"` are treated as inert; that is correct
      because the engine also YAML-parses the field.

      Any id that resolves to more than one record, whether torn across
      `queue/` + `archive/` or duplicated within a single root, fails closed and
      forces `SAFE_CLOSE`; a torn or duplicate out-of-manifest descendant can
      never satisfy the inertness predicate because its declared status is
      ambiguous.

      **Engine-behavior rationale (evidence-class labelled; only the first row
      is proven).**

      | Manifest shape | Out-of-manifest descendant | Engine effect | Evidence class |
      |---|---|---|---|
      | has feature member | declares exact canonical `status: archived` | inert — skipped, byte-identical | **PROVEN (ENGINE LAW)** — path-scoped `git diff --stat 358b63b4 e4ca20e5 -- .backlogit/archive/165.007-T.md .backlogit/archive/165.010-T.md` is empty, and `git rev-parse 358b63b4:<path>` / `git rev-parse e4ca20e5:<path>` return identical blob OIDs for both paths. This is the **only** proven row |
      | has feature member | `status: done` | archived (out-of-scope mutation) | **INDICATIVE / UNPROVEN** — not load-bearing: `done` is non-inert and forces `SAFE_CLOSE` regardless |
      | has feature member | live `queued` | archived, with `returned_ids` reported `[]` | **INDICATIVE / UNPROVEN** — rationale only; may never be stated as measured fact and may never authorize `CASCADE` |
      | no feature member | live sibling | returned, with `parent_id` cleared | **INDICATIVE / UNPROVEN** — follow-up `63363CF5`; may never authorize `CASCADE`. For a genuine split-delivery intermediate shipment, see **INV-11** and safe-close step 8's `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` halt, tracked by durable active stash entry `7F9CB5E9` |
      | any | ancestor/parent of a manifest item | untouched (no upward walk) | **INDICATIVE / UNPROVEN** |

      An unproven row may never authorize `CASCADE`. Where engine behavior is
      unproven, the dependent autoharness behavior is the fail-closed one.
      `returned_ids` remains a **secondary, insufficient** verification check:
      it is still checked after a live cascade runs, but it cannot stand as the
      primary guard because the live archival row above reportedly returned `[]`
      while still mutating an out-of-manifest descendant. That report is
      indicative and unproven only; it justifies the pre-mutation inertness gate
      and never authorizes the cascade path.

      **When this classification identifies qualifying feature members**
      (i.e. the classifier verdict is `CASCADE`): the all-member Step 0(b)
      snapshot already holds each qualifying feature member's declared
      status; confirm and extend the same pre-close declared-status
      snapshot from (b) — still **before** the cascade invocation, never
      after — with each qualifying feature member's own declared `status`
      field, read the identical way (frontmatter's own `status` field only,
      never inferred from `queue/`/`archive/` location); because (b) already
      recorded those values, this designates the existing entries and never
      re-reads them. The resulting map (every member status captured in
      (b), with the qualifying feature entries designated here) is the single pre-close declared-status
      snapshot the Cascade Close Sub-Procedure's step 3 two-set gate reads
      from; "qualifying feature members" for that gate means exactly the set
      this classification determines here — never a separate
      re-derivation, and independent of *how* the engine happens to
      transition any given member.

      **Linked-deliberation disposition snapshot.** Compute this snapshot on
      **every** reconcile run and on **both** close paths, before either path
      mutates backlog state. The snapshot uses the planner's
      `validated_linked_deliberations(S)` set definition: inspect every
      explicit manifest member regardless of `artifact_type`; collect link
      candidates from `custom_fields.source_deliberation_id` as a complete
      literal value and from description/references text scanned with the
      identical `\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b` matcher; then
      exclude the shipment record itself and every ID in `closure_scope(S)`
      (H10 — an explicit-member deliberation is an ordinary manifest member,
      not a disposition-set member). For each retained deliberation ID,
      record link kinds, linking manifest members, every record path, the
      record's declared `status` field (frontmatter only, never
      location-inferred), and the SHA-256 of each record path's bytes.

      Validate existence before location: first determine whether the ID
      resolves to any deliberation record at all; only then classify where
      each record path resides. An unresolved ID records
      `unresolved_references` and does **not** halt. A torn or duplicate
      deliberation — multiple record paths across `.backlogit/queue/`,
      `.backlogit/archive/`, or within either root — records
      `retained_ambiguous` and does **not** halt; every discovered record
      path is still fingerprinted so step 5 can enforce byte-identity
      against the captured SHA-256 values. `RECONCILE_FAIL_SNAPSHOT_AMBIGUOUS`
      and `RECONCILE_FAIL_SNAPSHOT_MISSING` apply to manifest members only,
      never to disposition-set deliberations.

      Apply the planner's containment checks before any byte read of a
      record path, matching `shipment_closure.py`: the path must be
      lexically and canonically contained in the backlog root, and it must
      not be a symlink, junction, or other reparse point. A path that fails
      either check is never opened or hashed; record it with outcome
      `retained_read_error`, its workspace-relative `path`, and `reason_code`
      `path_escape` or `symlink_or_reparse_point`, and do **not** halt. An
      unreadable record path records `retained_read_error` with
      `reason_code` `unreadable_file` instead of a hash. A record path that
      passes containment and is read successfully is then parsed exactly as
      the planner's `_read_record` parses it. A record path whose frontmatter
      opens with a `---` delimiter but never closes it records
      `retained_read_error` with `reason_code` `body_unseparable`. A record
      path with missing frontmatter, frontmatter that is not valid YAML or not
      a mapping, or a missing or invalid `id` records `retained_read_error`
      with `reason_code` `malformed_frontmatter`. Such a record cannot supply
      the declared status required above, so it is recorded with its
      workspace-relative `path` and `reason_code` instead of a hash; it is
      never omitted from the disposition set and does **not** halt. Step 5
      compares a read-error record path by its recorded location and
      `reason_code`, never by following it to hash a target.

      Superseded provenance only: the prior 1.10-era contract followed
      Backlogit's removed `linkedDeliberationIDs` helper. Under the verified
      engine-semantics line (`5a4b70dd` / `v1.11.0`), the engine does not
      archive these disposition-set deliberations; their outcome is handled
      by INV-12 after the close-path gate.

      **Engine-semantics gate (P-015 engine-semantics precondition).** Before
      the classifier result is acted on, probe the installed backlogit engine
      on the SAME surface the close path will use: over MCP, call
      `backlogit_get_version` with `no_update_check: true`; over the CLI, run
      `backlogit version --no-update-check --format json`. Record
      `probe_surface` (`mcp` or `cli`), `version`, and `commit` exactly as the
      probe returned them. Workspaces with a Python implementation installed
      apply `assess_cascade_engine_semantics` (this self-hosting repository's
      own implementation lives at `src/autoharness/gates/shipment_closure.py`);
      other workspaces apply the equivalent rules: the probed version is a
      released `X.Y.Z` or `vX.Y.Z` build (no pre-release or build metadata); its `X.Y`
      minor line is listed in P-015's token "Verified engine-semantics lines:
      `1.11`"; and the probe surface equals the surface the close path will
      invoke. Anything else, including a probe failure, timeout, or
      unparseable result, is `UNVERIFIED` with reason
      `ENGINE_SEMANTICS_UNVERIFIED`.

      **Close-path selection.** Select the close path with
      `select_close_path(classifier_decision, engine_decision)` (same
      self-hosting module) or its stated 2x2 table:

      | Classifier verdict | Engine-semantics verdict | Selected path |
      |---|---|---|
      | `CASCADE` | `VERIFIED` | `CASCADE` |
      | `CASCADE` | `UNVERIFIED` | `SAFE_CLOSE`, reason `ENGINE_SEMANTICS_UNVERIFIED` |
      | `SAFE_CLOSE` | `VERIFIED` | `SAFE_CLOSE`, the classifier's reason |
      | `SAFE_CLOSE` | `UNVERIFIED` | `SAFE_CLOSE`, the classifier's reason |

      **Pre-Mode step 2b agreement check.** The `--classify-only` run below is
      followed, before acting on any row of its exit-code routing table, by
      this check: compare the evidence record's `pre_close.classifier_verdict`
      and `pre_close.qualifying_feature_ids` with the step 2b verdict and
      qualifying feature set in this closure's Pre-Mode report (Pre-Mode step
      6), written by the pre-close run whose lock this close operation still
      holds. Any difference halts with
      `RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT`: nothing has been mutated, the
      Pre-Mode member-class decisions no longer rest on the verdict this step
      would act on, and neither path is substituted. When that report's step
      2b verdict is `not-evaluated` (an intake `expected_status`), or no
      Pre-Mode report exists for this closure under the held lock (a
      standalone safe-close), the `qualifying-feature` row was never applied
      and there is nothing to protect: the outcome is
      `agreement-check: not-applicable` and routing proceeds. Ship records the
      outcome (`agreed` or `not-applicable`) in the post-merge closure artifact
      beside `close_path` and `close_evidence`. This step stays
      authoritative; step 2b is advisory for gating only.

      <!-- cascade-close-routing:BEGIN step-0c -->
      **Command routing (192-F): `--classify-only` first, on every close.**
      Every close, on either path, first runs
      `autoharness shipment cascade-close --classify-only --shipment <shipment_id> --feature <feature_id> --sha <merge_commit_sha> --json`,
      where `<feature_id>` is the shipment's covering feature (derived as
      safe-close step 2 derives it). That command performs (a)–(c) above:
      the manifest load, the Step 0(b) snapshot, the classification, the
      engine-semantics gate, the close-path selection, and the
      linked-deliberation disposition snapshot. It records them in the
      evidence record
      `docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json`
      (the fixed path `build_evidence_path` builds), whose
      `pre_close.engine_semantics`, `pre_close.close_path_selection`, and
      `pre_close.linked_deliberation_disposition` fields carry the Step 0(c)
      engine-semantics decision, close-path selection, and disposition
      snapshot. The same record carries the path-specific baseline:
      `pre_close.observation_set` on a selected `SAFE_CLOSE`, and
      `pre_close.out_of_manifest_descendants` on either path. The prose in
      (a)–(c) above stays the specification the command implements; Ship
      never re-derives these values by hand.

      Plain `--classify-only` needs no operator approval: it is no-clobber
      (an existing `pre_close` record exits 2 and is left untouched) and only
      creates a new record. `--classify-only --replace-pre-close` overwrites
      an existing `pre_close` record and needs the same destructive-command
      approval as the mutating run. The mutating
      `autoharness shipment cascade-close` invocation (no `--classify-only`)
      **is** the destructive command: it needs the same operator approval
      that a direct `backlogit shipment ship` call needs (the intercom
      auto-check or explicit operator clearance). A direct
      `backlogit_ship_shipment` MCP or `backlogit shipment ship` CLI call is
      a **P-005 deviation** on either path, and the closure-evidence gate
      refuses the closure it produces, because no valid evidence record
      backs it.

      Route on the command's exit code:

      | Mode | Exit | Skill action |
      |---|---|---|
      | `--classify-only` | 0 (`CASCADE`) | Obtain destructive-command approval, then run the mutating `cascade-close` (Cascade Close Sub-Procedure) |
      | `--classify-only` | 3 (`SAFE_CLOSE` selected: classifier `SAFE_CLOSE`, or engine `UNVERIFIED`) | Safe-close steps 1–10, then the Linked-Deliberation Disposition step, citing the verdict record as `close_evidence` |
      | mutating | 0 | Run the Linked-Deliberation Disposition step with its inputs from the evidence record, then write the closure artifact with `close_path: cascade` and `close_evidence` |
      | mutating | 3 | Reached only when no `cascade`-selected `--classify-only` record preceded the run, which the routing above never does. Nothing was mutated: HALT, operator review, and never `SAFE_CLOSE` on this result (the Cascade Close Sub-Procedure's No-substitution rule). A selected-path change after a `CASCADE` `--classify-only` selection is exit 4, never 3 |
      | either | 2, 4 | HALT. Nothing was mutated. Exit 4 includes an engine re-probe difference and any difference from the `cascade`-selected `--classify-only` record, and is never answered with `SAFE_CLOSE`. Fix the input, or ask the operator |
      | either | 5, 6, 7, 8 | HALT. Operator review. No commit of the backlog root, no retry, no direct call |
      | either | any other or unrecognized exit (including 1) | HALT (CLI too old or unexpected; do not fall back to cascade). Never call `backlogit shipment ship` directly and never substitute `SAFE_CLOSE`; ask the operator |

      **Minimum version**: `autoharness shipment cascade-close` first ships
      in the autoharness release containing 192-F (the first release after
      1.5.0). An older CLI does not recognize the `shipment` command and
      exits 1, which the last row routes to HALT. Upgrade autoharness before
      closing; there is no hand-run fallback.
      <!-- cascade-close-routing:END step-0c -->

   * **CASCADE selected** → skip directly to the **Cascade Close
     Sub-Procedure** below (reusing the manifest and snapshot from (a)/(b)/(c)
     above — do not reload) in place of steps 1–10, then continue to the
     Linked-Deliberation Disposition step.
   * **SAFE_CLOSE selected** (default, including any classifier error,
     ambiguity, or unresolved precondition, and including
     `ENGINE_SEMANTICS_UNVERIFIED`) → continue to step 1 below
     (step 1's own manifest load is idempotent with (a) above — reuse the
     already-loaded manifest rather than issuing a second call).

1. **Load manifest** via `backlogit_get_shipment(shipment_id)`. Extract the
   `items` list. These IDs are the **only** artifacts safe-close steps 1–10 may move or
   archive; the INV-12 Linked-Deliberation Disposition step is separately
   sanctioned and runs only after step 10 returns `recommendation: CLOSED`.

2. **Compute the observation set** (partial-feature detection and baseline watching):
   * Derive the covering feature ID from the manifest item hierarchy
     (e.g. a task `055.002-T` belongs to feature `055-F`).
   * If the covering feature ID is **not** in the manifest `items`, this is a
     **partial-feature shipment**. Add the covering feature to the observation set.
   * Enumerate every task sharing the covering feature's hierarchy prefix whose ID
     is **not** in the manifest `items` (the unshipped siblings) by scanning **both**
     `.backlogit/queue/` **and** `.backlogit/archive/` (plus the feature file's
     declared children when available). Add each to the observation set.
   * The **observation set** is the parent feature plus every unshipped sibling task
     outside `closure_scope(S)`. It is computed from **expected IDs**, not merely the
     files currently present, because INV-7 watches for change relative to baseline,
     not for presence in one preferred directory. Do **NOT** treat sequence position,
     ancestry, or predecessor-shipment folklore as a substitute for this set, and do
     **NOT** exclude a member merely because a prior shipment is believed to have
     handled it. **Sequence-aware exclusion is WITHDRAWN here**: the older
     predecessor-provenance rule (`archived_status: shipped` or normalized legacy
     `done`, with Mere archive-file presence insufficient) no longer subtracts items
     from the observation set.

3. **Baseline-invariance gate** (before archiving anything): Run
   `git status --short -- ".backlogit/"` and record the pre-closure
   working-tree state so any later queue/archive move, deletion, or content drift of an
   observation-set path can be attributed to this procedure. Then fingerprint **every**
   observation-set member by recording its baseline location (`queue`, `archive`, or
   `missing`) plus the content hash of each present file. An artifact already archived,
   descoped, or missing **at baseline** is recorded as baseline state and is explicitly
   **NOT** a halt. Halt fail-closed only if an observation-set id resolves to more than
   one record, cannot be fingerprinted, or otherwise cannot be read consistently enough
   to compare against baseline.

4. **Archive each manifest item individually** (loop over `items` ONLY):
   * If the item's file is in `.backlogit/queue/`: move it to
     `done` via `backlogit_move_item`, then archive that single artifact via
     `backlogit_archive_item` (CLI fallback `backlogit archive {id}`). When the
     backlog registry's `archive_item` operation supports commit metadata, record
     the merge SHA using that tool's configured field (for backlogit, `commit_sha`);
     otherwise record the merge SHA in the closure report. Classify `matched`.
   * If the item's file is already in `.backlogit/archive/`: classify
     `pre-archived` and **skip** — do not re-archive. Reusing the `pre-archived`
     classification prevents false-positive cascade flags on items that were
     legitimately shipped earlier.
   * If the item's file is in neither location: classify `missing`, halt with
     `RECONCILE_FAIL`, and do not continue archiving.

5. **Verify-after-each invariant** (run immediately after each item's archival):
   * Compare **every** observation-set member against the Step 3 baseline fingerprint:
     same baseline location, same content hash, and no new queue/archive twin.
   * Run `git status --short -- ".backlogit/"` and confirm no
     observation-set path shows a queue/archive move, deletion, or content change
     beyond the baseline captured in step 3.
   * Any relative change outside `closure_scope(S)` is a cascade or collateral
     mutation. This includes the indicative `parent_id`-cleared shape tracked by
     `63363CF5`: even if the file still exists, changed frontmatter content violates
     INV-7 and halts fail-closed.

6. **Approval-gated rollback on cascade detection** (D6, exact sequence): If the
   invariant fails:
   1. **capture evidence** first: record the diverging artifact id(s), each
      artifact's baseline vs observed location/hash, the full
      `git status --short -- ".backlogit/"` output, and the exact causing command.
   2. **HALT** immediately. Perform no further mutation of any kind until approval is
      granted.
   3. Emit a **P-005** violation with the captured evidence attached.
   4. Request **EXPLICIT operator approval**, naming the exact paths and what would be
      lost. Notification, silence, or a previous generic instruction is **NOT** approval.
   5. **REVALIDATE** after approval: re-read the workspace and confirm the paths and
      state still match what was approved. If anything changed, **HALT** again and
      request fresh approval.
   6. Execute **ONLY the approved rollback**, restricted to the revalidated paths.

7. **Final invariant re-check**: After the loop completes, re-confirm that every
   observation-set member still matches its Step 3 baseline fingerprint.

8. **Close the shipment record itself** (single artifact, non-cascading; authoritative order):
   * Move **ONLY** the live shipment record to `status: shipped` via the generic,
     non-cascading `backlogit move <shipment_id> --status shipped`.
   * If `backlogit move <shipment_id> --status shipped` is refused (exit 9)
     while Step 0(c)'s **selected** close path is not `CASCADE` (classifier `CASCADE`
     with `ENGINE_SEMANTICS_UNVERIFIED` selects `SAFE_CLOSE`), halt fail-closed with
     `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`. This is **INV-11**: multi-shipment /
     split delivery is **contract-complete** but **operationally blocked** for backlogit
     1.10.1, tracked by durable active stash entry `7F9CB5E9`. There is no known safe
     path from this shape to `archived_status: shipped` without new upstream tooling.
     The cascade op must **NOT** be substituted: the belief that it can return live
     out-of-manifest siblings and clear their `parent_id` remains **INDICATIVE /
     UNPROVEN** rationale only (follow-up `63363CF5`), never measured fact and never
     authorization for a workaround. Archiving an active shipment record instead would
     stamp `archived_status: active` and fail provenance. Escalate to the operator; no
     silent workaround, no retry, no hand-edit.
   * Re-read and verify the live shipment record now reports `status: shipped`. If the
     record remains `active`, is already `archived`, is missing, or resolves to any other
     shape, halt fail-closed with `RECONCILE_FAIL_SHIPMENT_RECORD_LIVE_STATUS`. Do **NOT**
     auto-retry by calling the cascade op, and do not archive an `active` shipment record.
   * Archive **ONLY** the shipment record via `backlogit archive <shipment_id>` (single-
     artifact archive; this stamps `archived_status` from the live status at archive time).
   * Re-read and verify the archived record now reports `archived_status: shipped`.
     A legacy `archived_status: done` is accepted only when it pre-existed as an older,
     already-correct terminal provenance. Missing archive, live+archived duplication,
     generic archived-without-provenance, or any non-shipped archived provenance halt
     fail-closed with `RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`.
   * Re-run the verify-after-each invariant (step 5) to confirm the observation set is
     still baseline-invariant after the shipment-record close sequence.
9. **Produce safe-close report** per the same schema, recording the observation set,
   each item's classification, the shipment-record move-to-shipped verification, the
   shipment-record archived-provenance verification, and the recommendation.

10. **Gate decision**:
    * All manifest items `matched` or `pre-archived`, the shipment record archived,
      and the observation set still baseline-invariant → `recommendation: CLOSED`. Continue to the
      Linked-Deliberation Disposition step, not directly to post-mode; proceed to
      post-mode only after that step returns `recommendation: DISPOSITION_COMPLETE`.
    * Any cascade detected → `recommendation: HALT — cascade detected, revert required`
      (see step 6). Do not proceed to the commit step.

### Cascade Close Sub-Procedure (P-015 `CASCADE` exception ONLY)

Runs **only** when Step 0 of Safe-Close Mode above selects `CASCADE`, and
reuses the manifest and pre-close `parent_id`/declared-`status` snapshot
Step 0 already captured in (a)/(b)/(c) — this sub-procedure never reloads
the manifest or attempts to reconstruct pre-close state after the fact.
Replaces steps 1–10 above entirely for this shipment's closure; there is no
partial mixing of the two paths.

<!-- cascade-close-routing:BEGIN cascade-sub-procedure -->
**Command routing (192-F): the mutating `cascade-close` runs this
sub-procedure.** The pre-invocation revalidation below (the classifier
re-run, the linked-deliberation re-collection, and the engine-semantics
re-probe), the baseline-fingerprint capture, step 1's invocation, and
steps 2–6 are performed by the mutating
`autoharness shipment cascade-close --shipment <shipment_id> --feature <feature_id> --sha <merge_commit_sha> --message <merge_commit_message> --author <merge_commit_author> --json`.
Ship runs it only after the Step 0(c) `--classify-only` run exited 0
(`CASCADE` selected) and only with the destructive-command approval Step
0(c) names. Before it invokes anything, the command re-checks the
`cascade`-selected `--classify-only` record: any difference from that
record, and any engine re-probe difference, exits 4 with nothing mutated.
Its exit 0 is step 7's `recommendation: CLOSED`, and the record it
finalizes (phase `post_close`) is step 6's cascade-close report and the
closure artifact's `close_evidence`. Every other exit follows the Step 0(c)
routing table: HALT, never a `SAFE_CLOSE` substitution. Ship never performs
these steps by hand and never invokes the cascade operation directly: a
direct `backlogit_ship_shipment` MCP or `backlogit shipment ship` CLI call is
a **P-005 deviation**. The command never archives a disposition-set
deliberation; the Linked-Deliberation Disposition step stays its only
archiver. The prose below stays the specification the command implements.

**Timeout sizing (192-F).** The mutating run's `--timeout` is 30-3600
seconds (default 1800). On expiry the command kills the engine mid-cascade
and exits 6 (`mutation_possible: indeterminate`), so Ship sizes it before
the run. Let N = |closure_scope(S)| (the manifest items plus the shipment
record) and compute the budget `B = ceil(1.5 * (F + P * N))` seconds, where
F and P are the fixed and per-artifact `backlogit shipment ship` costs
re-derived from the workspace's own backlogit event logs (reference values,
backlogit 1.11.0: F = 133 s, P = 35 s). If B <= 1800, the default suffices.
If 1800 < B <= 3600, Ship adds `--timeout B` to the invocation above. If
B > 3600, Ship does not start the mutating run and HALTs for an operator
decision; it never invokes the command with a timeout known to be too
short.
The B > 3600 HALT bounds `--timeout`, not the whole command: `--timeout`
bounds only the `backlogit shipment ship` child, and the command's runner
alone owns that child's expiry. The engine probes, preflight, and
revalidation run before that timer starts, and child cleanup, postcondition
checks, evidence persistence, and lock release run after it, so Ship
supervises the command for its supervision budget: the effective timeout (B,
or the 1800 default) + a fixed 600 s supervision margin (two 30 s engine
probes, the bounded kill and reader-join cleanup of each spawned process, at
most 70 s each, and headroom for the untimed workspace reads and writes), at
most 4200 s. Whenever the supervision budget exceeds the agent runtime's
synchronous tool-call limit, Ship MUST start the mutating run in the
runtime's background/async mode, attached to the session (never detached
from it), and poll until the command exits; if the runtime cannot keep the
process alive for the full supervision budget, Ship HALTs before the
mutating run. A runtime that kills the command mid-run leaves `backlogit`
running unsupervised in its own process group, the evidence record at
`invoking`, and the pair lock in place, so the next run exits 7. Ship stays
attached to the run until the command exits and never abandons or kills it
on an agent-tool wait or before the supervision budget elapses. For this run
the supervision budget is the stall bound: the circuit-breaker Stall
Detection table's `autoharness shipment cascade-close` (mutating mode) row
sets it in place of the "Other commands" 5-minute stall timeout.
<!-- cascade-close-routing:END cascade-sub-procedure -->

**Pre-archived manifest members (expected and tolerated)**: before invoking
step 1 below, classify each manifest member's **location** as `queued` or
`pre-archived` by checking whether its record currently resides in
`.backlogit/queue/` or `.backlogit/archive/`, and
retain that location set for the cascade-close report (step 6 below). This
location label is **descriptive only** — it names where the record
currently resides, and is **never** a substitute for, nor evidence of, the
record's own declared `status` field (the Member-Class Status Contract's
declared-status rule, R-1). A record residing in
`.backlogit/archive/` while declaring `status: done` is **not**
truly archived; only a declared `status: archived` is truly archived for
step 3's two-set gate below. The sole authority for "truly archived" is the
declared-status snapshot Step 0(b)/(c) already captured before this
sub-procedure runs.

A `pre-archived` (by location) manifest member is **expected and tolerated
on this path**: it does **not** disqualify the `CASCADE` verdict, does
**not** constitute a classifier ambiguity or unresolved precondition, and
does **not** authorize a fallback to safe-close. Step 0(c)'s classifier
already resolves each manifest member by scanning **both** `queue/` and
`archive/`, so archived inputs were already accounted for when the
verdict was selected — this clause states the execution-time consequence
of that fact and does not add a new classifier precondition; Step 0(c)'s
precondition wording is unchanged.

This tolerance applies to **manifest members only** — it does not
restate, weaken, or cross-apply to the observation set (the Safe-Close
Mode step 2/3 "protected set"): the Safe-Close Mode step 3 baseline-
invariance gate already tolerates an already-archived observation-set
member as baseline state (explicitly "not a halt"), so this sub-procedure
does not additionally claim the observation set has "no pre-archived
exemption" — that older claim is withdrawn as contradicting step 3. The
distinct rule that does apply here is: the observation set is never
manifest-scope, is never itself archived by this procedure, and remains
subject to the same baseline-invariance enforcement — byte-identical to
its captured baseline for the duration of this closure — regardless of
whether that baseline happens to be `archive` or `queue`. A manifest
that qualifies for `CASCADE` has no protected set **in the Safe-Close
sense** (full `CASCADE` eligibility is itself a Step 0(c) precondition,
and this sub-procedure never computes or archives against a Safe-Close-style
protected set on this path) — **this is not the same as saying no
out-of-manifest state requires safeguarding here.** Under the flat-manifest
engine-inertness model, `CASCADE` qualifies precisely in the presence of
out-of-manifest descendants that Step 0(c) found already truly
`status: archived`; those descendants still require an explicit
safeguard, filling exactly the role the protected set fills for
Safe-Close. That safeguard is the baseline-fingerprint capture (before
step 1) and the post-invocation baseline-invariance verification (step 5)
below: every such descendant MUST remain byte-identical to its
classification-time snapshot for the duration of this closure, or the
closure halts fail-closed.

**`archived_ids` is a transition log, not a manifest echo.** The cascade
operation invoked in step 1 below reports, in `archived_ids`, only the
artifacts it **actually transitioned** to archived during that invocation
(backlogit engine source, `internal/core/shipment_lifecycle.go`
`archiveItems()`: an item whose declared `status` is already `archived` is
skipped and never appended to the slice that becomes `archived_ids`). A
non-feature manifest member that was already truly `status: archived`
before the call therefore has no transition to report and is
**correctly absent** from `archived_ids` — this is expected engine behavior, not an anomaly and not a
cascade failure. **This never extends to the shipment record or to a
qualifying feature member itself** (155-S, PR #407 review, thread
PRRT_kwDORzpWpM6b0kit): step 3 below makes both unconditionally required
regardless of their own pre-close declared status, so neither can ever be
"correctly absent" the way a non-feature manifest member can — see
step 3 for the full statement of that rule. The live fail-closed guard
over this result is the two-set `allowed_ids` / `required_ids` gate
specified in step 3 below, evaluated **against the Step 0(b) all-member pre-close
declared-status snapshot** — never against location, and never against a
post-close re-read.

   **SUPERSESSION NOTE (155-S, 2026-08-24).** This paragraph previously
   claimed the cascade operation "is idempotent over pre-archived members",
   citing
   `docs/spikes/2026-08-18-cascade-close-pre-archived-member-behavior.md`
   as authority for the claim that it "returns \[pre-archived members] in
   its `archived_ids` result exactly as it does newly-archived members",
   and stated that step 3's exact-match post-condition, "evaluated against
   the manifest's full item set", "must never be relaxed". **That claim,
   and the spike cited for it, are WITHDRAWN.** The spike's arms were built
   with `move --status done`, which relocates a record but leaves it
   declaring `status: done` — never truly `status: archived` — so none of
   its arms ever exercised the case this paragraph claimed to cover; its
   finding is valid only for relocated-but-`done` records (see the spike's
   own superseded banner). The two safety properties this paragraph
   protected — nothing out-of-scope archived, nothing required left
   unarchived — are now carried, at full strength, by the two-set gate in
   step 3 below, keyed on declared pre-close status rather than a full-set
   echo of the manifest.

**No-substitution rule**: once Step 0 selects `CASCADE`, that verdict is
final for this closure — between the verdict and step 1's invocation
below, substituting manual safe-close is a **P-005 process deviation**,
never a permitted fallback, regardless of the manifest's archival state.
This complements, and does not restate or contradict, step 2's separate
rule against falling back to safe-close **after** a cascade has already
executed: together the two rules close both the pre-execution and
post-execution substitution windows. The asymmetry is intentional and
one-directional — this rule forbids `CASCADE -> manual safe-close`
substitution only; it grants no license to invoke cascade when Step 0
selects `SAFE_CLOSE`, which remains governed by the P-015 default
prohibition. If a genuine unhandled error occurs during the cascade
operation, halt and disclose it per the verification steps below — never
silently switch to safe-close instead.

Ship performs **no** manual per-item archive loop on this path: the
cascade operation in step 1 below performs all remaining archival
itself, consistent with the "no partial mixing of the two paths" rule
above.

**Pre-invocation classifier revalidation (immediately before
Baseline-fingerprint capture, INV-6/INV-7).** A fingerprint of the
current files, by itself, does not prove Step 0(c)'s `CASCADE`
classification still holds: a descendant's declared `status` can change,
or a new live descendant can appear under a qualifying feature, in the
window between Step 0(c)'s classification-time scan and this
pre-invocation point — fingerprinting that already-drifted state would
silently adopt the new state as "baseline" instead of detecting the
drift, and step 5's post-invocation check only guards the window *after*
this point, not the one before it. Immediately before capturing the
baseline fingerprint below, re-run `classify_shipment_close_path` (or the
equivalent full re-scan) **fresh** against the current
`.backlogit/queue/` + `.backlogit/archive/` state — never reusing Step
0(c)'s enumeration for this check — and require the result to be
**identical** to Step 0(c)'s: the same `CASCADE` verdict, the same
qualifying root feature member set, and the same
`out_of_manifest_descendant_ids` set (compared as a set, not merely by
cardinality). Any drift in any of the three halts with
`HALT — cascade pre-invocation revalidation drift detected` and emits a
**P-005** violation; do NOT invoke either close path. This is a halt, not
a substitution to safe-close, and does not conflict with the
No-substitution rule above (which forbids switching to manual safe-close
after a `CASCADE` verdict) — refusing to proceed at all is not a
substitution.

**This classifier re-run does not, by itself, cover the Linked-deliberation
disposition snapshot above**: `classify_shipment_close_path` intentionally
never inspects `validated_linked_deliberations(S)` (see the INV-6 gate's
own scoping above), so a linked deliberation gained or changed on any
explicit manifest member after Step 0(c) — a new
`custom_fields.source_deliberation_id`, a newly added description/reference
match, an added/removed record path, a declared-status change, or a
content-hash change to an already snapshotted record — would leave all
three classifier-compared values identical while still changing the INV-12
disposition evidence. Immediately alongside the classifier re-run above,
independently re-collect the same full disposition set as the Step 0(c)
Linked-deliberation disposition snapshot: every explicit manifest member
regardless of `artifact_type`, using the identical link-source rules
(`custom_fields.source_deliberation_id` and description/references text),
the identical matcher, and the identical exclusion of the shipment record
itself and every ID in `closure_scope(S)`. Require this freshly
re-collected snapshot — deliberation IDs, link kinds, linking members,
every record path, declared statuses, and SHA-256 values together — to be
**identical** to Step 0(c)'s captured disposition snapshot. Any drift halts
with the same
`HALT — cascade pre-invocation revalidation drift detected` message and
**P-005** violation as the classifier-output drift above; do NOT invoke
either close path. Only when both the classifier re-run and this
linked-deliberation re-collection match Step 0(c)'s snapshot exactly does
the Baseline-fingerprint capture below proceed, using the now-reconfirmed
descendant set.

**Engine-semantics re-probe (pre-invocation revalidation).** Alongside the
classifier re-run and the linked-deliberation re-collection above, re-run
the Step 0(c) Engine-semantics gate probe **fresh** on the SAME surface
(`backlogit_get_version` with `no_update_check: true` over MCP, or
`backlogit version --no-update-check --format json` over the CLI) and
compare the RAW `version`, `commit`, and `probe_surface` values and the
resulting engine-semantics verdict against the values Step 0(c) recorded,
by exact string equality, never a normalized or minor-line-only
comparison. Any difference, or a re-probe failure of any kind, halts with
`HALT — cascade pre-invocation revalidation drift detected` and emits a
**P-005** violation; do NOT invoke either close path. Never fall back to
`SAFE_CLOSE` here: after a `CASCADE` selection that would be the
prohibited `CASCADE` → `SAFE_CLOSE` substitution. The Baseline-fingerprint
capture below proceeds only when this re-probe also matches Step 0(c)
exactly.

**Baseline-fingerprint capture (INV-7, before invocation).** Immediately
before step 1's invocation — using the SAME observation set of
out-of-manifest descendants the pre-invocation revalidation above just
reconfirmed as reachable-and-engine-inert (identical to Step 0(c)'s
original enumeration), never a fresh or narrower re-scan at this specific
step — record each such descendant's baseline location (`queue` or
`archive`) plus a content hash of its file. This is the identical
baseline-invariance snapshot P-015's own Precondition already requires to
exist before a cascade invocation; capturing it here, rather than assuming
the revalidation's read still holds an instant later, is required because
classification and invocation are not atomic. Retain this snapshot in
memory for step 5's verification below; it is never reconstructed after
the fact.

1. The mutating `autoharness shipment cascade-close` invokes the cascade
   operation `backlogit_ship_shipment(shipment_id, merge_commit_sha)` itself,
   over its CLI form (`backlogit shipment ship <shipment_id> --sha
   <merge_commit_sha> --message <merge_commit_message> --author
   <merge_commit_author>`). It is the only invoker; Ship never issues this
   call directly.
2. **Verify the result matches the classifier's own precondition**:
   `returned_ids` MUST be empty (`[]`). A non-empty `returned_ids` means the
   live engine found an unreleased descendant the classifier's live-workspace
   enumeration did not — this is a TOCTOU/engine-behavior mismatch, not a
   recoverable state. Halt immediately with
   `HALT — cascade returned non-empty returned_ids, classifier/engine
   mismatch` and emit a **P-005** violation; do NOT retry, do NOT fall back to
   safe-close after a cascade has already executed.
3. **Verify `archived_ids` against the two-set `allowed_ids` / `required_ids`
   gate** (replaces exact full-set equality — see the SUPERSESSION NOTE
   above and the P-015 policy's own supersession note for why):
   * **Compute `allowed_ids`** = `closure_scope(S)`: every explicit manifest
     item ID from `items(S)`, regardless of `artifact_type`, plus the
     shipment record itself. This is the flat set. A disposition-set
     deliberation is **not** added merely because it is linked from a
     manifest member; linked deliberations are handled only by INV-12.
     H10 carve-out: if a deliberation ID is itself an explicit manifest
     member, it is an ordinary `closure_scope(S)` / `allowed_ids` member,
     and its presence in `archived_ids` MUST NOT trip the
     unexpected-artifact check merely because its `artifact_type` is
     `deliberation`.
   * **Compute `required_ids`** = the shipment record and every qualifying
     feature member (**both unconditionally** — never omitted, and never
     conditioned on either artifact's own pre-close declared status) + every
     other manifest item that was **not** truly `status: archived` in the
     Step 0(b) all-member pre-close declared-status snapshot. Because Step
     0(b) snapshots every explicit manifest member regardless of
     `artifact_type`, no Step 0(c) linked-deliberation extension participates
     in this set. A disposition-set deliberation that is not an explicit
     manifest member is never a `required_ids` member. Pre-Mode's
     Member-Class Status Contract agrees with this by construction: it
     accepts a qualifying feature member's pre-close `active`, `done`, or
     `archived` status instead of halting on it, so the status this gate
     disregards is never one Pre-Mode stopped on.
   * **Two separately-labelled, independently-failing conditions.** Neither
     may be evaluated as a precondition of the other, and the two MUST NOT
     be merged into a single combined test (conflating two questions into
     one condition is the documented root cause of external defect
     `B57F9E24`):
     - **Unexpected-artifact check**: if `archived_ids - allowed_ids` is
       non-empty, halt with
       `HALT — cascade archived unexpected artifact {id}` and emit a
       **P-005** violation. A disposition-set deliberation that is not an
       explicit manifest member and appears in `archived_ids` fails this
       check: that is engine drift under the verified flat line.
     - **Missing-required-artifact check**: if `required_ids - archived_ids`
       is non-empty, halt with
       `HALT — cascade did not archive required artifact {id}` and emit a
       **P-005** violation.
   * An `allowed_ids` **non-shipment, non-feature** member (any explicit
     manifest item that is neither the shipment record nor a qualifying
     feature member, including an explicit-member deliberation under H10)
     that was already truly `status: archived` in the Step 0(b) all-member
     pre-close snapshot MAY be included in or omitted from `archived_ids` by
     the engine — neither outcome fails either check (it is outside
     `required_ids` by construction, and if present in `archived_ids` it is
     still inside `allowed_ids`). **This tolerance never extends to the
     shipment record itself**, which is unconditionally a `required_ids`
     member per the computation above regardless of its own pre-close
     declared status: if the shipment record were ever reported pre-close as
     already truly `status: archived` — an anomalous state for an artifact
     this same closure step is actively transitioning to `shipped` — its
     absence from `archived_ids` still fails the missing-required-artifact
     check exactly as any other missing `required_ids` member would; no
     engine behavior toward the shipment record ever gets a pass under this
     tolerance.

     **Nor does it extend to a qualifying feature member itself (155-S, PR
     #407 review, thread PRRT_kwDORzpWpM6bzlFl).** Backlogit's own
     `ShipShipment` (`internal/core/shipment_lifecycle.go`) unconditionally
     calls `setArtifactStatus(featureID, models.StatusDone, "feature
     released")` for every explicit shipment-member feature — regardless of
     that feature's own pre-close declared status, including an already
     truly `status: archived` one — **before** `collectArchiveCandidateIDs`
     runs. `setArtifactStatus` only no-ops when the artifact's current
     status already equals the requested one, and the requested status here
     is `done`, never `archived`, so an already-archived qualifying feature
     is unconditionally relocated to `done` first, with no terminal-status
     bypass of the kind `completeReleaseScope` grants a non-feature manifest
     item already truly `status: archived` (that non-feature skip is exactly
     what makes the tolerance above valid for those members, and it has no
     counterpart in the feature-forcing loop). By the time
     `collectArchiveCandidateIDs` loads the feature, its declared status is
     therefore always `done`, never still `archived` — that function's own
     `feature.Status != models.StatusArchived` check is always true for it
     — so the feature is always appended to the candidate list
     `archiveItems` archives. A qualifying feature member can therefore
     never be "correctly absent" from `archived_ids` the way a truly
     pre-archived non-feature manifest member can — its absence is always an
     anomaly, never expected engine behavior. A qualifying feature member is
     therefore an unconditional `required_ids` member exactly like the
     shipment record, and is never eligible for this tolerance.
4. **Verify no `parent_id` was cleared**: re-read every archived task's
   frontmatter and confirm `parent_id` is unchanged from the pre-close
   snapshot captured in Step 0(b) — never a freshly-read or assumed value,
   since the field being verified is the very one a cascade could have just
   cleared. Any cleared or altered `parent_id` is a
   cascade-detection failure equivalent to step 6 of safe-close: halt with
   `HALT — cascade cleared parent_id on {id}, revert required` and emit a
   **P-005** violation; do NOT commit the mutated backlog state.
5. **Verify out-of-manifest descendant baseline invariance (INV-7/INV-10, after invocation) and linked-deliberation disposition byte identity**: first re-scan every descendant captured in the baseline-fingerprint snapshot above and compare its current location plus content hash against that snapshot. Any change relative to baseline — location change, content-hash change, deletion, rename, new archive presence, or `parent_id` drift on any of these descendants — is a cascade signal exactly as INV-7/the Required Check defines for safe-close: halt with `HALT — cascade modified out-of-manifest descendant {id}, revert required` and emit a **P-005** violation; do NOT commit the mutated backlog state. This is the CASCADE-side counterpart of safe-close's verify-after-each invariant, closing the gap the classification-time INV-6 engine-inertness gate alone does not cover: INV-6 governs whether `CASCADE` may be selected, this step governs whether the postcondition it promised (`allowed_ids(S)`-external byte-identity) actually held once the engine ran. Then re-collect the linked-deliberation disposition snapshot after the cascade, using the same full disposition set, link-source rules, matcher, exclusions and record-location rules as the Step 0(c) snapshot, so a record created during the cascade is seen rather than only the paths captured before invocation. First compare every snapshot field except the per-path hashes against the Step 0(c) snapshot, exactly as the pre-invocation re-collection does: the deliberation IDs, the `unresolved_references` set, and, per deliberation ID, its link kinds, its linking manifest members, its declared status, and the complete set of record paths MUST be identical — a new or vanished deliberation ID, a previously unresolved reference that now resolves to a record, a changed link kind, linking member or declared status, or an added or removed record path for the same deliberation ID is drift, because INV-12 eligibility depends on that link and referrer evidence. Only then compare each record path's current location plus SHA-256 against that snapshot. Every disposition-snapshot record path MUST remain byte-identical after the cascade. Any location or content-hash change, deletion, rename, archive move, queue move, added/removed duplicate record for the same deliberation ID, or any other snapshot-field difference from the post-cascade re-collection halts with `HALT — cascade modified linked deliberation {id} — engine semantics drift` and emits a **P-005** violation; do NOT commit the mutated backlog state. A cascade that mutates a disposition-set deliberation is engine drift under the verified flat line; INV-12 disposition, not the cascade, owns any later single-artifact deliberation archive.
6. **Produce cascade-close report** recording the classifier's verdict, qualifying feature IDs, the Step 0(c) engine-semantics decision (`probe_surface`, `version`, `commit`, and verdict/reason), the Step 0(c) linked-deliberation disposition snapshot, the pre-close declared-status snapshot (Step 0(b)), the `backlogit_ship_shipment` result (`shipment_status`, `archived_ids`, `returned_ids`, `commit_sha`), `allowed_ids`, `required_ids`, and both set differences (`archived_ids - allowed_ids` and `required_ids - archived_ids`) — so a vacuous `required_ids` is visible in the report rather than silent — the parent_id-preservation verification outcome (against the Step 0(b) snapshot), the out-of-manifest descendant baseline-invariance verification outcome, and the linked-deliberation disposition byte-identity outcome from step 5 above.
7. **Gate decision**: `returned_ids` empty, `archived_ids - allowed_ids` empty (no unexpected artifact archived), `required_ids - archived_ids` empty (no required artifact left unarchived), every `parent_id` preserved (against the Step 0(b) snapshot), each out-of-manifest descendant byte-identical to its step-5 baseline fingerprint, and every linked-deliberation disposition snapshot record path byte-identical to its Step 0(c) fingerprint → `recommendation: CLOSED`. Hand off to the Linked-Deliberation Disposition step; proceed to post-mode only after that step returns `recommendation: DISPOSITION_COMPLETE`. Any verification failure above → the corresponding `HALT`; do not proceed to the Linked-Deliberation Disposition step, post-mode, or any commit step.

### Linked-Deliberation Disposition (P-015 INV-12)

Runs once per closure, after the selected close path's gate returns
`recommendation: CLOSED` (safe-close step 10, or Cascade Close Sub-Procedure
step 7) and before post-mode, under the lock pre-mode already holds. The step
is path-independent and separately sanctioned by **INV-12**: it never widens
`closure_scope(S)`, `allowed_ids(S)`, or `required_ids(S)`, and it mutates a
disposition-set deliberation only through a single-artifact, non-cascading
archive, one ID at a time.

0. **Inputs.** The step consumes these values from Step 0 and the selected
   close path, and never substitutes a recomputed set for the snapshot.
   <!-- cascade-close-routing:BEGIN disposition-inputs -->
   It takes every input from the evidence record
   (`docs/closure/evidence/{shipment_id}-{feature_id}-close-evidence.json`,
   written by the Step 0(c) `autoharness shipment cascade-close` run), never
   from in-session Step 0(c) state, and never recomputes one:
   <!-- cascade-close-routing:END disposition-inputs -->
   * the selected close path and its reason (Step 0(c) close-path selection),
     from `pre_close.close_path_selection`;
   * the Step 0(c) engine-semantics decision (`probe_surface`, `version`,
     `commit`, and verdict/reason), from `pre_close.engine_semantics`,
     rebuilt with `engine_semantics_from_record` (this self-hosting
     repository's own implementation lives at
     `src/autoharness/gates/cascade_evidence.py`);
   * the Step 0(c) linked-deliberation disposition snapshot (the
     **disposition snapshot**), from
     `pre_close.linked_deliberation_disposition`;
   * the path-specific baseline: the safe-close step 3 observation-set
     fingerprints, from `pre_close.observation_set` (`SAFE_CLOSE`), or the
     Cascade Close Sub-Procedure's out-of-manifest descendant baseline
     fingerprints, from `pre_close.out_of_manifest_descendants` (`CASCADE`).

   The input source is the only thing the evidence record changes here:
   steps 1–6 below run exactly as stated, with the recorded engine decision
   as step 1's `engine=` argument. Under an `UNVERIFIED` engine the step
   still mutates nothing, and it stays the only archiver of a
   disposition-set deliberation.

1. **Plan.** Workspaces with a Python implementation installed plan each
   disposition-set deliberation's outcome with
   `compute_linked_deliberation_disposition(manifest_items, shipment_id, workspace_backlog_dir, engine=<the Step 0(c) engine-semantics decision>)`
   (this self-hosting repository's own implementation lives at
   `src/autoharness/gates/shipment_closure.py`). The call passes no
   `stash_path`, so the planner reads the active stash file at
   `.backlogit/stash.jsonl`. The planner result is consumed in this order. Check `planning_error` first: when `planning_error` is present, it
   is exempt from the planner-vs-snapshot equality check because the
   planner returns `dispositions=()`; the equality check applies only
   when the planner returns without `planning_error`. Before any archive,
   when the planner returns without `planning_error`, the planner's disposition
   set (deliberation IDs, link kinds, linking members, record paths, and
   record hashes) MUST equal the Step 0(c) disposition snapshot, and for
   every deliberation the snapshot already settled as `retained_read_error`,
   `retained_ambiguous`, or `already-archived`, the planner's outcome and
   `reason_code` (and, for `retained_read_error`, its `path`) MUST equal the
   snapshot's settled outcome data, and the planner's `unresolved_references`
   set (exact `{id, reason_code}` pairs) MUST equal the snapshot's,
   so a fresh plan never upgrades snapshot-settled evidence to a planned
   `archive` or drops snapshot evidence. Any difference halts with `HALT — linked-deliberation disposition failed {id}`;
   emit **P-005** once; no mutation. `{id}` is the first differing
   deliberation ID, or the shipment ID for a set-level added/removed-ID
   difference. Other workspaces apply the same stated rules and
   first-match precedence over the eight `LinkedDeliberationOutcome` values
   that INV-12 names (P-015 Vocabulary and Invariant Summary below). The
   list below is the precedence order; other outcome enumerations in this
   skill are unordered:
   `retained_read_error`, `retained_ambiguous`, `already-archived`,
   `retained_engine_unverified`, `retained_live_status`,
   `retained_shared_reference`, `retained_description_mention`, and otherwise
   a planned `archive`. The planned `archive` is the pre-mutation form of the
   `archived` outcome, which only step 4 below assigns. The disposition set,
   its link kinds, and the shared-reference guard's live-referrer scan all use
   the Step 0(c) matcher, referenced here by name and never restated. The
   shared-reference guard counts, as live referrers when they link the
   deliberation: work items outside
   `closure_scope(S)` that are not truly archived, shipments other than this
   one that are not truly archived, and active stash entries. It never counts
   the deliberation itself, any other deliberation, docs, or archived records.
   A planner `planning_error` carries no planned `archive`. Preserve outcomes
   already settled by the Step 0(c) disposition snapshot (`retained_read_error`,
   `retained_ambiguous`, and `already-archived`); for every remaining snapshot
   deliberation, report outcome `retained_ambiguous` with `reason_code:
   planning_error`, and exclude `already-archived` deliberations from the
   `stranded_linked_deliberation` advisory. Also preserve the snapshot's
   `unresolved_references` set, because the planner returns none on
   `planning_error`.

   **Engine UNVERIFIED means no mutation.** When the Step 0(c)
   engine-semantics verdict is `UNVERIFIED`, every disposition-set
   deliberation that an earlier rule (`retained_read_error`,
   `retained_ambiguous`, `already-archived`) does not settle is
   `retained_engine_unverified`, and nothing is mutated, on every close path.
   This includes a classifier `CASCADE` that Step 0(c) routed to `SAFE_CLOSE`
   with reason `ENGINE_SEMANTICS_UNVERIFIED`.

2. **Disposition baseline.** Before the first archive call, capture the
   disposition baseline from these components:
   * (i) the path-specific set: the safe-close observation-set fingerprints,
     or the CASCADE out-of-manifest descendant fingerprints (disposition step 0);
   * (ii) the disposition snapshot;
   * (iii) a pre-disposition `git status --porcelain -- ".backlogit/"`
     capture, together with a location-and-SHA-256 fingerprint of every
     path under `.backlogit/` other than the exempt paths named below,
     because porcelain status codes alone are not byte identity (a path
     that is already modified or untracked keeps the same entry when its
     bytes change again); enumerate those paths without following any
     symlink, junction, or other reparse point, and before reading any
     path's bytes, at this capture and at every later invariance comparison
     in steps 4 and 6, apply the Step 0(c) containment checks to it (lexical
     and canonical containment in the backlog root, and no symlink,
     junction, or other reparse point);
   * minus the `closure_scope(S)` IDs this run already archived (their
     queue→archive moves are the completed closure, not drift). This
     subtraction applies to the (iii) porcelain capture only: the (iii)
     fingerprint is taken after the closure, so it covers those records'
     post-closure bytes and any later change to them violates the baseline.

   Relative to this baseline, an archive call may change only backlogit
   `ArchiveItem`'s own side effects (verified at `v1.11.0`
   `internal/core/archive.go`):
   * the target deliberation's own queue→archive move;
   * the target's frontmatter keys `status`, `archived_status`, and
     `archived_from`;
   * the gitignored item event log (`.backlogit/logs/`) and backlogit's
     own index, which is exactly `.backlogit/backlogit.db` and its SQLite
     sidecars `.backlogit/backlogit.db-wal`, `.backlogit/backlogit.db-shm`,
     and `.backlogit/backlogit.db-journal` at the backlog storage root
     (no other `.db` file, at the root or below it, is part of the index);
   * lock and hook-queue files.

   `ArchiveItem` also calls `ArchiveLinkedStashEntries`
   (`internal/core/stash.go`), which archives every active stash entry that
   the engine's stash-link index links to the target, rewriting
   `.backlogit/stash.jsonl` and appending to
   `.backlogit/archive/stash.jsonl`. That write is never an allowed side
   effect: the step 3 engine stash-link guard's provenance key check and
   exact relation check together retain every target that carries such a
   link, so the call is a no-op for every archived target. Any
   change to `.backlogit/stash.jsonl` or `.backlogit/archive/stash.jsonl`,
   or to any other path outside these allowed side effects, violates the
   disposition baseline.

   The exempt paths, excluded from the (iii) fingerprint, are only the
   gitignored item event log, the four index paths enumerated above, lock and
   hook-queue files, and this
   run's own closure report path under `.backlogit/reconcile/` (written by
   step 5). Every other `.backlogit/reconcile/` path stays in the baseline.

   A path that fails those checks, or cannot be read, while capturing this
   baseline is never opened or hashed and does not halt: record it in the
   (iii) fingerprint by its workspace-relative path and `reason_code`
   (`path_escape`, `symlink_or_reparse_point`, or `unreadable_file`) instead
   of a SHA-256, as Step 0(c) records a read-error record path. At every later
   comparison in steps 4 and 6, compare such a path by location and
   `reason_code` only, never by following or reading it. Any other path that
   fails those checks at a later comparison, or a recorded path whose
   location or `reason_code` changed, is never read or hashed and fails that
   step's verification (step 4 or step 6).

3. **Archive each planned `archive`, one at a time, in ascending ID order.**
   * Immediately before each call, re-run the SHA-256 check after first
     re-listing the deliberation ID's record
     paths under `.backlogit/queue/` and `.backlogit/archive/` and require
     exactly the disposition snapshot's single path, then reapply the Step
     0(c) containment checks to that record path before reading any of its
     bytes (lexical and canonical containment in the backlog root, and no
     symlink, junction, or other reparse point), then check that record
     path against its disposition-snapshot hash **and** the shared-reference
     guard for that ID, so nothing that changed since
     the snapshot is archived (TOCTOU). Retain the record bytes this re-check
     read; step 4 compares against them.
   * A containment failure at this re-check is never opened, hashed, or
     archived; it halts identically with `HALT — linked-deliberation
     disposition failed {id}`; emit a **P-005** violation once through D6,
     scoped to the disposition archive of {id}; no mutation, and the
     completed close-path closure is never rolled back.
   * A record-path re-list mismatch halts identically with `HALT —
     linked-deliberation disposition failed {id}`; emit a **P-005**
     violation once through D6, scoped to the disposition archive of
     {id}; the completed close-path closure is never rolled back.
   * A hash mismatch halts with `HALT — linked-deliberation disposition failed {id}`;
     emit a **P-005** violation once through D6, scoped to the disposition
     archive of {id}; the completed close-path closure is never rolled back.
   * These retention rules apply in the order listed, and the first that
     applies settles the ID.
   * **Archive-resident target.** A target whose disposition-snapshot record
     path lies under `.backlogit/archive/` rather than
     `.backlogit/queue/` is never archived: record outcome
     `retained_ambiguous` with `reason_code: archive_resident_unarchived` for
     that ID, with no mutation, and the loop continues. For such a record,
     `ArchiveItem` stamps `archived_from` with a path that is not a
     disposition-snapshot queue record path (the engine's canonical queue
     restore path when the record already sits at its archive path), so step
     4 could never verify it.
   * **Engine stash-link guard.** Two checks run in order, and both must
     clear before the target is archived.
     * *Provenance key check.* A target whose retained record bytes declare
       a `custom_fields.source_stash_id` key, with any value, is never
       archived: record outcome `retained_shared_reference` with
       `reason_code: engine_stash_link` and the declared value as its
       referrer for that ID, with no mutation, and the loop continues. In
       `v1.11.0`, `ArchiveLinkedStashEntries` reads the engine's stash-link
       index through `GetStashLinksForItem`; harvest, index rehydration, and
       verified provenance corrections write every production row of that
       index, and each such row names an item whose
       `custom_fields.source_stash_id` equals the linked stash ID. This check
       ignores whether that stash entry still looks active, because the
       index can lag the stash file, so it deliberately retains every
       harvest-created deliberation, even one whose link is no longer
       active, and such a deliberation stays in the
       `stranded_linked_deliberation` advisory.
     * *Exact relation check.* A stash-link row need not carry that key (the
       backlogit `v1.11.0` test `TestArchiveItem_ArchivesLinkedStashEntries`
       links an item that has no `source_stash_id`), so the key check alone
       cannot prove the archive is stash-inert. After the key check clears,
       and immediately before the archive call, run the exact relation that
       `ArchiveLinkedStashEntries` reads through `GetStashLinksForItem`
       (`internal/db/stash.go`) against the engine index
       `.backlogit/backlogit.db`, bound to the target ID:
       `SELECT sl.stash_id FROM stash_links sl JOIN stash_entries se ON se.stash_id = sl.stash_id WHERE sl.item_id = ? AND se.state = 'active'`.
       Open the index **read-only** through the SQLite URI
       `file:.backlogit/backlogit.db?mode=ro` and run only that
       `SELECT`; never write, migrate, sync, rehydrate, or hand-edit the
       index (Data Ownership rule), and never substitute the public stash
       views, which do not expose item links. The index path lies inside the
       backlog storage root that the Step 0(c) containment checks already
       bound; reapply those checks to it before opening it.
       If the query returns any row, the target is never archived: record
       outcome `retained_shared_reference` with `reason_code:
       engine_stash_link` and the returned stash IDs, in ascending order, as
       its referrers for that ID, with no mutation, and the loop continues.
       If the index is missing, fails the containment checks, cannot be
       opened read-only, or lacks the `stash_links` or `stash_entries` table
       or a queried column, so the query cannot run, the target is never
       archived (fail-closed): record outcome `retained_engine_unverified`
       with `reason_code: engine_stash_link_unverifiable` for that ID, with
       no mutation, and the loop continues. Only an error-free query that
       returns zero rows clears this check.
     * Together, the two checks make the `ArchiveLinkedStashEntries` call
       inside `ArchiveItem` a no-op for every archived target. The step 4
       disposition-baseline invariance check, which halts on any change to
       `.backlogit/stash.jsonl` or
       `.backlogit/archive/stash.jsonl`, remains the backstop for a
       link written between the query and the archive call.
   * A new live referrer records `retained_shared_reference: [referrer IDs]`
     for that ID with no mutation, and the loop continues.
   * Otherwise archive that single artifact via `backlogit_archive_item`
     (CLI fallback `backlogit archive {id}`) on the probed surface, the same
     `probe_surface` the Step 0(c) engine-semantics gate recorded. Pass **no
     cascade flag**.

4. **Verify-after-each** (immediately after each archive call). All of the
   following must hold:
   * the queue copy is absent, and the archive copy is present exactly once;
   * the archive copy passes the Step 0(c) containment checks (lexical and
     canonical containment in the backlog root, and no symlink, junction, or
     other reparse point) before any of its bytes are read;
   * the archive copy declares `status: archived`;
   * its `archived_status` equals the deliberation's declared status in the
     disposition snapshot;
   * its `archived_from` provenance is present and well-formed, naming the
     deliberation's disposition-snapshot queue record path by exact string
     match, workspace-relative with `/` separators (step 3 archives only
     queue-resident targets, so that path always exists; missing or
     ill-formed provenance fails verification);
   * its frontmatter, compared **semantically** (parsed YAML, because
     `ArchiveItem` re-serializes it), equals the frontmatter of the record
     bytes retained at the step 3 re-check, except for the three engine keys
     `status`, `archived_status`, and `archived_from`;
   * its Markdown body after the closing frontmatter delimiter is
     **byte-exact** against those retained record bytes;
   * disposition-baseline invariance holds: nothing changed relative to the
     step 2 disposition baseline except that call's allowed `ArchiveItem`
     side effects and the side effects of earlier disposition archives in
     this step that already passed verification.

   Any failure: `HALT — linked-deliberation disposition failed {id}`; follow
   the D6 sequence of safe-close step 6, scoped to the disposition archive of
   {id} (capture evidence → HALT → emit P-005 once → request EXPLICIT
   operator approval → REVALIDATE → execute ONLY the approved rollback). There is no retry and
   no rollback of the completed closure: the close path's gate already
   passed, so the closure is complete and only the disposition is not. Do not
   advance to post-mode, and never commit a torn disposition (a partially
   verified archive state; the self-hosting repository records this lesson in
   `docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md`).

5. **Report.** Add to the closure report (safe-close step 9 or cascade-close
   step 6):
   * `linked_deliberation_disposition: [{id, link_kinds, linking_members, outcome, reason_code, path, referrers, pre_sha256, post_sha256, archived_status}]`,
     one entry per disposition-set deliberation, where `outcome` is a
     `LinkedDeliberationOutcome` value (`archived`, `already-archived`,
     `retained_read_error`, `retained_ambiguous`,
     `retained_engine_unverified`, `retained_live_status`,
     `retained_shared_reference`, or `retained_description_mention`),
     `reason_code` is always present and is copied verbatim from the planner
     for every planner outcome other than the planned `archive` (never
     re-derived; an unknown code is carried as-is), except that a verified
     `archived` outcome carries `reason_code: archived` (the outcome-value
     default, replacing the planner's pre-mutation `archive`), a planned
     `archive` that the step 3 re-check settles as
     `retained_shared_reference` carries `reason_code:
     retained_shared_reference`, one that the step 3 engine stash-link guard
     settles carries `reason_code: engine_stash_link` (or, when its exact
     relation check cannot run, outcome `retained_engine_unverified` with
     `reason_code: engine_stash_link_unverifiable`), one that step 3
     settles as an archive-resident target carries `reason_code:
     archive_resident_unarchived`, an outcome preserved from the Step 0(c)
     disposition snapshot keeps that snapshot's own `reason_code` (for
     example a read error's `path_escape`), and an outcome synthesized for a
     `planning_error` (only the remaining snapshot deliberations) carries
     `reason_code: planning_error`, `path` is present
     for `retained_read_error`, `referrers` lists the live referrer IDs of a
     `retained_shared_reference` (for `engine_stash_link`, the declared
     `source_stash_id` value from the provenance key check, or the stash IDs
     the exact relation check returned), and `post_sha256` and `archived_status` are
     present for an `archived` outcome. Report keys map to planner/code fields
     as follows: `id` → `deliberation_id`, `linking_members` →
     `linking_member_ids`, `referrers` → `referrer_ids`, and `pre_sha256`
     records one pre-archive SHA-256 per record. When the planner reports
     `planning_error`, record the `planning_error`. Preserve outcomes already
     settled by the Step 0(c) disposition snapshot (`retained_read_error`,
     `retained_ambiguous`, and `already-archived`); for every remaining snapshot
     deliberation, report outcome `retained_ambiguous` with `reason_code:
     planning_error`, and exclude `already-archived` deliberations from the
     `stranded_linked_deliberation` advisory, and report the snapshot's
     `unresolved_references` set. An empty disposition set records
     `linked_deliberation_disposition: []`;
   * `unresolved_references` (`{id, reason_code}`), plus every planner read
     failure (`{path, reason_code}`);
   * the durable advisories, carried into the closure summary:
     `ENGINE_SEMANTICS_UNVERIFIED` with the Step 0(c) reason whenever the
     engine-semantics verdict is `UNVERIFIED`, and
     `ENGINE_LINE_UNVERIFIED_ADVISORY` naming the probed version whenever its
     minor line is not a P-015 verified engine-semantics line;
   * a `stranded_linked_deliberation` advisory listing every `retained_*`
     outcome, so a deliberation that stays live across closures stays visible
     to the operator.

6. **Gate decision.**
   * Every disposition-set deliberation has exactly one outcome, every
     `archived` outcome passed step 4, and a final disposition-baseline
     invariance check, run after the step 5 report write, passes (nothing
     changed relative to the step 2 disposition baseline except the allowed
     side effects of the verified disposition archives and this run's own
     closure report path) → `recommendation: DISPOSITION_COMPLETE`.
     Proceed to post-mode. Retained outcomes are reported, never halt, and
     never block this gate. `linked_deliberation_disposition: []` is valid
     only when the Step 0(c) disposition snapshot is empty; a `planning_error`
     over a non-empty snapshot preserves snapshot-settled outcomes and reports
     only the remaining deliberations as `retained_ambiguous` with
     `reason_code: planning_error`.
   * A failure of that final invariance check halts with `HALT —
     linked-deliberation disposition failed {id}`, where `{id}` is the
     shipment ID; follow the D6 sequence of safe-close step 6, scoped to the
     diverging paths plus this run's disposition archives (when the run
     archived nothing, the scope is the diverging paths alone), and emit
     **P-005** once. Do not proceed to post-mode.
   * Any halt above → `recommendation: HALT — linked-deliberation disposition failed {id}`.
     Do not proceed to post-mode or to any commit step. On a disposition HALT,
     keep the shipment lock held through the D6 sequence (approval → REVALIDATE
     → approved rollback) and release it only after D6 finishes — either the
     approved rollback is complete or the operator declines — following
     pre-mode step 7's rule to release the lock on pre-mode HALT while retaining
     it after `PROCEED` from Ship Step 6 until post-mode completes.

**Action risk (ProposedAction / ActionRisk).** `backlogit_archive_item` on a
linked deliberation is ActionRisk **medium**: it is reversible with
`backlogit restore`, and it is gated by the shared-reference guard, the
pre-archive hash re-check, and verify-after-each. The engine-version probe is
ActionRisk **none** (read-only). This step adds no other mutation.

**Sanctioned successor.** This step is the sanctioned successor to the
operator-approved 190-S closure deviation, in which the operator approved a
one-off standalone archive of a linked deliberation that the cascade had left
live. That archive now happens only here, under the guards above; no closure
repeats it as an ad hoc deviation.

### Mixed-Role Detection Mode (`mode: detect-mixed-role`, operator-invoked, READ-ONLY)

No lock is acquired for this mode — no backlog/shipment artifact is ever
mutated. (The mode's own diagnostic report, audit-log entry, and telemetry
event — steps 6, 8 below — ARE writes, but they are additive-only writes to
non-backlog-state locations, never applied to a queue/archive item, so no
`file-lock` is required.) This mode is composed entirely from EXISTING
read-only backlogit reads; it introduces NO new gate/CLI code (single
template family: this SKILL's prose only).

1. **Enumerate shipments**: call `backlogit_list_shipments`. If `shipment_id`
   was given, narrow to that single shipment; otherwise scan every shipment
   returned.

2. **Load each candidate shipment record** via `backlogit_get_shipment`.
   Skip (no report entry) any shipment whose record status is
   `active`, `shipped`, `abandoned`, or archived — those are the
   normal in-progress/closed lifecycle **shipment-record** states and are out
   of scope for this check (mirrors the `record-consistent` scope boundary
   above). Note: `shipped`/`abandoned` are the shipment record's own terminal
   statuses (`ShipmentStatus` enum), distinct from `done` which is
   a **task**-artifact status — a live shipment record is never itself
   `done`. If a candidate's persisted status is not a valid
   backlogit 1.8.0 shipment lifecycle value (e.g. a legacy `blocked` value),
   classify it `malformed-legacy`, add it to the report, and continue to the
   next candidate — never fabricate a transition. Any other unrecognized
   persisted value is likewise `malformed-legacy` rather than silently
   skipped or silently matched to the queued branch below — every possible
   persisted value maps to exactly one of: skip (`active`/
   `shipped`/`abandoned`/archived), scan (`queued`, step 3), or
   `malformed-legacy` (anything else).

3. **Filter to task-artifact manifest items**: for each remaining
   `queued` candidate, read its manifest `items` list and each
   item's frontmatter (`status`, `artifact_type`) via per-item reads
   (`backlogit_get_item` per task id). Exclude any non-task entry (e.g. a covering
   feature id in a fallback-assembled manifest) before classifying — the same
   task-artifact filter the Ship agent's intake early-warning applies to
   `custom_fields.items` (`templates/agents/_ship.agent.md.tmpl`).

4. **Classify each task-artifact manifest item** against the per-task ALLOWED
   ROLE table and the per-item ANOMALY table in the "Mixed-Role Detection
   Classification" section above. Locate each id in
   `.backlogit/queue/` and `.backlogit/archive/` to
   determine role/anomaly; for an archive hit, read `status`, `archived_status`,
   and `archived_from` to distinguish the two valid archived-completed
   representations from `malformed-provenance` / `any-other-archived-status`.

5. **Determine the outcome for each candidate**:
   * If any per-item anomaly was found → `REPORTED`, naming the shipment id,
     the anomalous task id(s), and the specific anomaly for each.
   * Else if the mixed-role signature is present (at least one `live-active`
     or `archived-completed(done)` role task, all tasks otherwise role-clean)
     → `REPORTED`, naming the shipment id, record status, and each task's role.
   * Else (all tasks role-clean and no mixed-role signature — e.g. a
     genuinely fresh `queued` shipment with all-`live-queued`
     tasks) → `DETECTED` with no anomaly/signature to report for that
     candidate.
   * If backlogit is unreachable at any point in steps 1–4 → `DEGRADED`;
     report the degraded condition for the affected candidate(s) and HALT the
     scan. Do not guess or proceed on partial data.

6. **Emit the report-only diagnostic** at
   `.backlogit/reconcile/{shipment_id-or-"all"}-detect-mixed-role-{timestamp}.md`,
   listing per candidate: the shipment id, its record status, the per-task
   role classification, any per-item anomaly, and the outcome (`DETECTED` /
   `REPORTED` / `DEGRADED`).

7. **Emit Operator-Remediation Guidance** inline with any `REPORTED` or
   `DEGRADED` entry — see "Operator-Remediation Guidance" below. This mode
   performs NO mutation of any kind in response to what it finds.

8. **Write the audit entry and emit telemetry** for every candidate's outcome
   — see "Mixed-Role Detection Audit + Telemetry" below.

#### Operator-Remediation Guidance

When this mode reports a mixed-role signature or a per-item anomaly, include
this guidance verbatim (adapted with the specific ids/anomaly found) in the
report:

> autoharness performs **NO auto-repair** of this inconsistency. A
> record-only forward re-claim (`queued` → `active` on
> the shipment record alone) is **UNSUPPORTED** by backlogit 1.8.0: evidence
> (read-only inspection of `C:\Source\GitHub\backlogit`, NOT mutated) —
> `ClaimShipment` (`internal/core/shipment_lifecycle.go`) is **manifest-wide**
> activation (it moves the shipment `queued`→`active`
> AND THEN activates every still-`queued` manifest member,
> cascading parent-feature status, with all-or-nothing rollback on any
> mid-flight failure) and is **STRICTLY SINGLE-SHOT**
> (`isValidShipmentTransition` in `internal/core/shipment.go` permits ONLY
> `queued`→`active` and
> `active`→`{shipped,abandoned}`; a re-claim on an already-`active`
> shipment returns `ErrShipmentConflict`). There is **NO**
> `active`→`queued` transition and **NO** `blocked`
> shipment status in 1.8.0 — never expect or fabricate either. The SUPPORTED
> manual remediation path is entirely through backlogit's own sanctioned
> lifecycle transitions: the operator inspects the shipment and its manifest
> tasks directly (`backlogit get <id>` / `backlogit shipment get <id>`) and
> decides, case by case, whether the tasks are legitimately progressing (in
> which case the operator may let the shipment proceed to closure normally
> once all tasks complete, using this skill's own `mode: pre` →
> `mode: safe-close` → `mode: post` sequence) or whether the state reflects a
> genuinely torn/partial session (in which case the operator investigates and
> resolves the affected tasks manually before any closure attempt). This
> guidance is descriptive only; this skill never performs any of these steps
> itself.

#### Mixed-Role Detection Audit + Telemetry

Mirrors the `pipeline-topology` force-audit + telemetry pattern
(`src/autoharness/cli.py` `_audit_pipeline_topology_force` /
`_emit_pipeline_topology_telemetry`), adapted for a detection-only outcome —
there is NO repair/mutation/confirm/post-condition field, because nothing is
ever mutated.

1. **Audit log**: for EVERY candidate outcome (`DETECTED` / `REPORTED` /
   `DEGRADED`), append one structured JSON line to
   `.autoharness/gates/shipment-reconcile-detection-audit.log` (creating the
   `.autoharness/gates/` directory if needed), containing: `timestamp`
   (UTC ISO-8601), `actor` (the invoking operator/session identity, e.g. from
   `USERNAME`/`USER`), `shipment_id`, `record_status`, `outcome` (`DETECTED` \|
   `REPORTED` \| `DEGRADED`), `per_task_roles` (an array of
   `{task_id, role, anomaly}` — `anomaly` is `null` when the task is
   role-clean), `remediation_guidance_emitted` (boolean), and `report_path`
   (the reconciliation report path from step 6). NO `repair`, `mutation`,
   `confirm`, or `post_condition` field is ever present — those concepts do
   not apply to this read-only mode.
2. **Telemetry event**: emit one telemetry event per candidate outcome,
   mirroring the pipeline-topology `ToolTelemetryEvent` shape
   (`schemas/tool-telemetry-event.schema.json`): `tool_surface: "builtin"`
   (the schema's `tool_surface` enum is `mcp` \| `cli` \| `shell` \| `builtin`
   \| `api` \| `unknown` — `"skill"` is NOT a valid value; `shipment-reconcile`
   is an agent-invoked prose skill with no separate CLI/MCP/API backend of its
   own, so `builtin` is the correct surface),
   `tool_name: "shipment-reconcile"`, `operation: "detect-mixed-role"`,
   `status` mapped from the outcome (`DETECTED` → `success`, `REPORTED` →
   `blocked`, `DEGRADED` → `failed`), `sensitivity: "internal"`,
   `redaction_applied` and `metric_sources`/`metric_quality` set per the
   schema's structural requirements, `shipment_id`/`backlog_item_id` set to
   the candidate shipment id, and `artifact_refs` including the audit log
   path and the report path. When invoked inside an active Ship task epoch
   with a live `context_ref` (from `autoharness telemetry begin`), emit via
   `autoharness telemetry event --context-ref <ref> --from-json <payload>`;
   when invoked standalone (e.g. an ad-hoc operator audit outside any Ship
   task loop, the most common case for this mode) there is no `context_ref`
   to attach to, so telemetry emission for that invocation is skipped and the
   audit log entry (step 1) remains the durable record — this mirrors
   telemetry's existing fail-open, observational contract (an absent or
   unavailable telemetry surface is a no-op and NEVER blocks detection,
   reporting, or the HALT decision).

### Lock-Conflict Scenario

If pre-mode cannot acquire the lock because another process holds it:

1. Retry once after 30 seconds.
2. If retry also fails, count as a session stall and prompt the operator:
   `Shipment lock conflict on {shipment_id}. Another process holds the lock.`
3. Do NOT proceed without the lock. Do NOT call `backlogit_ship_shipment`.


## P-015 Vocabulary and Invariant Summary

* D1a vocabulary used by this skill: `manifest_scope`, `closure_scope`, `allowed_ids`, `required_ids`, `validated_linked_deliberations`.
* This list mirrors the policy's own `INV-1`..`INV-12` numbering and meaning exactly (`.github/policies/workflow-policies.md`, P-015 Invariants) — it is a condensed restatement, never a second/parallel numbering.
* `INV-1` (Flat closure scope): `closure_scope(S) = items(S) ∪ {S}`. Ancestry never adds a member. Linked deliberations do not extend `closure_scope(S)` or `allowed_ids(S)`; they are accounted for only by INV-12.
* `INV-2` (Membership is explicit and exhaustive): an artifact is in `manifest_scope(S)` iff its ID appears in `items(S)`. Absence from `items(S)` is complete evidence that the artifact is not part of this delivery.
* `INV-3` (Exclusion is never a gate): an out-of-manifest descendant may be `queued`, `active`, `blocked`, `done`, `archived`, descoped, or absent, and ancestry alone never makes it a closure blocker or a closure-scope member.
* `INV-4` (Multi-shipment feature delivery): a feature may be delivered across `S1 … Sn`; `S1..Sn-1` carry no feature member; exactly one shipment, the final `Sn`, carries the feature itself as a manifest entry. This is contract-complete but operationally blocked until INV-11's external runtime prerequisite `7F9CB5E9` lands.
* `INV-5` (Feature terminality precondition): the final shipment may carry the feature only when every task actually delivered by `S1..Sn` is terminal. Tasks excluded from every manifest in the sequence are not part of this precondition. This is contract-complete but operationally blocked until INV-11's external runtime prerequisite `7F9CB5E9` lands.
* `INV-6` (Engine-inertness containment gate): `CASCADE` is permitted only when every artifact in the `parent_id` descendant set the classifier enumerates (`out_of_manifest_descendant_ids`) that lies outside `closure_scope(S)` is engine-inert — an exact parsed-scalar `isinstance(status, str) and status == "archived"` match, with no `.lower()`, no `.strip()`, no `casefold`, no alias, and no `str()` coercion, and with any id resolving to more than one record (torn or duplicate) failing closed. This gate never reaches `validated_linked_deliberations(S)`: under the verified engine line the engine leaves linked deliberations independent, so their disposition is INV-12.
* `INV-7` (Baseline invariance replaces baseline presence): safe-close records each observed artifact's baseline location plus content hash and requires nothing outside `closure_scope(S)` changes relative to baseline. Temporal scope: baseline invariance is evaluated at the close-path gate, before INV-12 disposition; INV-12 then applies its own invariance check against the disposition baseline.
* `INV-8` (Manifest ordering is a Stage assembly convention, NOT a closure precondition). Stage may enforce feature-last ordering when assembling new shipments, but Ship MUST NOT treat manifest ordering as a closure precondition.
* `INV-9` (DAG orthogonality): shipment sequencing and pipeline topology are orthogonal to closure scope; closure never consults the DAG when deciding what this shipment may transition.
* `INV-10` (Close-path gate postconditions (evaluated before INV-12 disposition)): at the close-path gate, `archived_ids ⊆ allowed_ids(S)`; `required_ids(S) ⊆ archived_ids`; every artifact outside `allowed_ids(S)` is byte-identical to baseline, including `parent_id`; and the shipment record declares `status: archived` plus `archived_status: shipped`. INV-12's `archived` deliberations are the only artifacts outside `allowed_ids(S)` that may change after the gate, and only through INV-12.
* `INV-11` (External runtime prerequisite): multi-shipment delivery is contract-complete but operationally blocked under backlogit 1.10.1 (the observed line; not re-verified for 1.11; re-verification is owned by the engine-behavior registry). An intermediate shipment carries no feature member, cannot qualify for `CASCADE`, and is therefore a genuine `SAFE_CLOSE` shipment. If `backlogit move <shipment_id> --status shipped` is refused while Step 0(c)'s **selected** close path is not `CASCADE` (classifier `CASCADE` with `ENGINE_SEMANTICS_UNVERIFIED` selects `SAFE_CLOSE`), Ship MUST halt with `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`. The cascade path must NOT be substituted, because `returned_ids` and `parent_id` clearing are indicative and unproven only, and archiving an active shipment record stamps `archived_status: active` rather than `archived_status: shipped`. This is an unresolved upstream tooling gap tracked by durable active stash entry `7F9CB5E9`; no silent workaround, no retry, no hand-edit.
* `INV-12` (Linked-deliberation disposition): after the selected close path's gate passes, the Linked-Deliberation Disposition step assigns each disposition-set member exactly one `LinkedDeliberationOutcome`: `archived`, `already-archived`, `retained_read_error`, `retained_engine_unverified`, `retained_ambiguous`, `retained_live_status`, `retained_shared_reference`, or `retained_description_mention`. Each outcome carries a `reason_code`, which defaults to the outcome value; `retained_read_error` also carries a workspace-relative `path` and a read-error `reason_code` (`path_escape`, `symlink_or_reparse_point`, `unreadable_file`, `malformed_frontmatter`, `body_unseparable`, `malformed_stash_entry`). A read or containment failure yields `retained_read_error` first. A disposition-set member is mutated only by a single-artifact, non-cascading archive, and only when the engine-semantics verdict is VERIFIED, the deliberation is linked from an explicit member's `source_deliberation_id`, its own status is not live (`active`, `blocked`, `review`), it resolves to exactly one record, and it has no live referrer. The step never widens `closure_scope(S)`, is independent of the selected close path, and reports retained outcomes, which never halt; a verification failure halts with P-005 and never advances to post-mode.

## Deterministic Safe-Close Scenario Matrix

* **114-S -> 115-S -> 116-S serial-close success chain**: 114-S safely closes while 115-S/116-S remain in the observation set; once 114-S carries verified `archived_status: shipped` (or legacy `done`), later runs may record that new baseline and continue watching only the still-out-of-scope artifacts.
* **Negative — done-not-archived out-of-manifest child**: a descendant outside `closure_scope(S)` declaring `status: done` selects `SAFE_CLOSE`; the reason must name the observed status, and indicative engine folklore may never authorize `CASCADE`.
* **Negative — live out-of-manifest child**: a descendant outside `closure_scope(S)` declaring a live status such as `queued` selects `SAFE_CLOSE`.
* **Negative — archive-without-status out-of-manifest child**: a record physically in `.backlogit/archive/` but lacking its own declared `status` still selects `SAFE_CLOSE`; location is never a substitute for inertness.
* **Negative — live out-of-manifest grandchild**: a live grandchild outside `closure_scope(S)` selects `SAFE_CLOSE`; ancestry explains blast radius but never expands closure scope.
* **Negative — baseline-archived observation member**: an observation-set artifact already archived, descoped, or missing at baseline is recorded as baseline state and does **NOT** halt by itself.
* **Negative — changed during run**: any observation-set location/hash drift relative to baseline halts and enters the D6 sequence: capture evidence -> HALT -> emit P-005 -> request EXPLICIT operator approval -> REVALIDATE -> execute ONLY the approved rollback.
* **Negative — refused transition with no safe substitution**: if `backlogit move <shipment_id> --status shipped` is refused while Step 0(c) did not select `CASCADE`, halt with `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`; the cascade op must NOT be substituted.
* **Negative — step 2b / Step 0(c) classifier disagreement**: the `--classify-only` record's `classifier_verdict` or `qualifying_feature_ids` differs from Pre-Mode step 2b's recorded values; halt with `RECONCILE_FAIL_PREMODE_CLASSIFIER_DRIFT` before acting on any routing row. Nothing is mutated and no path is substituted.
* **Negative — non-canonical archived variant**: `Archived`, `ARCHIVED`, or the quoted padded YAML scalar `status: " archived "` all select `SAFE_CLOSE`; exact parsed-scalar matching has no normalization path.
* **Negative — torn descendant**: any out-of-manifest id that resolves to more than one record selects `SAFE_CLOSE`.
* **Negative — archive-while-active**: if the shipment record is archived while still `status: active`, producing `archived_status: active`, halt with `RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`.
* **Negative — non-shipped-live-before-archive**: if the shipment record cannot be re-read and verified as live `status: shipped` before the archive step, halt with `RECONCILE_FAIL_SHIPMENT_RECORD_LIVE_STATUS`.
* **Negative — missing archive**: if the archive file for the shipment record is missing after `backlogit archive <shipment_id>`, halt with `RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`.
* **Negative — archived abandoned**: if the shipment record archives with `archived_status: abandoned`, halt with `RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`.
* **Negative — missing provenance**: if the shipment record is archived but lacks `archived_status: shipped|done`, keep out-of-scope artifacts outside `closure_scope(S)` unchanged relative to baseline and halt with `RECONCILE_FAIL_SHIPMENT_RECORD_PROVENANCE`.
* **Linked deliberation (a) — engine unverified**: the classifier returns `CASCADE` but the Step 0(c) engine-semantics verdict is `UNVERIFIED`, so Step 0(c) selects `SAFE_CLOSE` with reason `ENGINE_SEMANTICS_UNVERIFIED`; safe-close steps 1–10 run, and the Linked-Deliberation Disposition step records every linked deliberation that `retained_read_error`, `retained_ambiguous`, or `already-archived` does not settle as `retained_engine_unverified` and mutates none.
* **Linked deliberation (b) — shared reference**: with the engine VERIFIED, a disposition-set deliberation that still has a live referrer outside `closure_scope(S)` is recorded `retained_shared_reference` with its referrer IDs; it is never archived and never halts.
* **Linked deliberation (c) — engine drift**: a cascade that archives a non-manifest disposition-set linked deliberation halts at Cascade Close Sub-Procedure step 3 with `HALT — cascade archived unexpected artifact {id}`; a cascade that modifies but does not archive one halts at step 5 with `HALT — cascade modified linked deliberation {id} — engine semantics drift` and emits a P-005 violation, and neither the Linked-Deliberation Disposition step nor post-mode runs.
* **Linked deliberation (d) — description-only mention**: with the engine VERIFIED, a deliberation ID mentioned only in a member's description/references, never in `custom_fields.source_deliberation_id`, and with no higher-precedence rule matched is recorded `retained_description_mention`; it is never archived and never halts.
* **Linked deliberation (e) — torn deliberation**: a deliberation ID that resolves to more than one record is recorded `retained_ambiguous`; it is never archived and never halts.
* **Linked deliberation (f) — read error**: an unreadable, malformed, or containment-failing deliberation record or stash input found by the Step 0(c) snapshot or the step 1 plan is recorded `retained_read_error` with its `reason_code` and workspace-relative `path`; it is never archived and never halts. A record that passed those checks but fails containment later, at the step 3 pre-archive re-check or as a new or changed failure at the step 4 or step 6 comparison, is not a read-error retention: it halts with `HALT — linked-deliberation disposition failed {id}` through D6, where `{id}` is that step's own halt ID (the re-checked or just-archived deliberation at steps 3 and 4, the shipment ID at step 6).

## Quality Criteria

* `mode: pre` runs before closing a shipment in Ship Step 6
* `mode: pre` with `expected_status: queued` (or `active` for already-claimed shipments) runs at Ship Step 0.5 intake
* `mode: safe-close` runs **in place of** the cascade `backlogit_ship_shipment` call and archives only the manifest item IDs (one artifact at a time) plus the shipment record itself — **except** when Step 0's P-015 flat-manifest classification selects `CASCADE`, in which case the Cascade Close Sub-Procedure runs instead and safe-close steps 1–10 are skipped entirely
* Close-path selection is made **only** from the machine-checkable classification result (Step 0), never inferred from prose or manifest shape alone; any classifier error, ambiguity, or unresolved precondition falls back to safe-close
* Step 0(c)'s engine-inertness containment walk traverses the qualifying feature's **full descendant tree, at every depth** (via a full `parent_id` graph, not a single-level scan of direct children only) — a manifest such as `[feature, task]` where that task has an out-of-manifest subtask must fall back to safe-close, never wrongly qualify for `CASCADE` (155-S, PR #407 review, thread PRRT_kwDORzpWpM6b2MJv)
* The Cascade Close Sub-Procedure independently verifies `returned_ids` is empty, `archived_ids` against the flat two-set `allowed_ids` / `required_ids` gate (step 3: `allowed_ids` = every explicit manifest item regardless of `artifact_type` + the shipment record; `required_ids` = the shipment record and every qualifying feature member, both unconditionally, plus every other manifest item NOT truly `status: archived` in the Step 0(b) all-member pre-close declared-status snapshot; linked deliberations are handled only by INV-12 and enter `allowed_ids` / `required_ids` only when they are explicit manifest members under H10; `archived_ids - allowed_ids` non-empty halts with `HALT — cascade archived unexpected artifact {id}` — including a disposition-set deliberation that is not an explicit manifest member, because that is engine drift under the verified flat line; `required_ids - archived_ids` non-empty halts with `HALT — cascade did not archive required artifact {id}`, evaluated as two independent, never-merged conditions — a truly pre-archived **non-shipment, non-feature** manifest member (including an explicit-member deliberation under H10) has no transition to report and is correctly, expectedly absent from `archived_ids`, never a mismatch, but this tolerance never extends to the shipment record itself, which remains unconditionally required regardless of its own pre-close declared status, nor does it extend to a qualifying feature member itself, which is likewise unconditionally required regardless of its own pre-close declared status — since Backlogit's own `ShipShipment` forces every explicit qualifying feature member through `status: done` before archive-candidate collection ever runs, so it is never still `archived` by that point either), and no `parent_id` was cleared — a mismatch on any of these halts fail-closed with a P-005 violation even though the cascade path was itself permitted
* Safe-close computes an observation set (parent feature + unshipped siblings outside `closure_scope(S)`) from expected IDs and records each member's baseline location/hash before archiving anything
* Safe-close verifies the observation set remains baseline-invariant after every single-item archival and after the shipment-record close sequence
* Safe-close moves the shipment record to live `shipped`, verifies it, explicitly archives only that record, and verifies `archived_status: shipped` before closure completes
* Safe-close archives the shipment record as its own single artifact and never via the cascade op
* Safe-close detects off-scope drift, then follows the D6 approval-gated rollback sequence; it never auto-prunes the manifest
* If `backlogit move <shipment_id> --status shipped` is refused and Step 0(c) did not select `CASCADE`, safe-close halts with `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION`; no substitution, no retry, no hand-edit
* `mode: post` runs after the safe-close archive sequence in Ship Step 6
* After the selected close path returns `recommendation: CLOSED` (safe-close step 10, or Cascade Close Sub-Procedure step 7), the Linked-Deliberation Disposition step runs before post-mode; post-mode runs only after that step returns `recommendation: DISPOSITION_COMPLETE`, never directly after a close-path `CLOSED`
* "Manifest-scoped mutation only" and safe-close step 1 bound only safe-close steps 1–10; the INV-12 Linked-Deliberation Disposition step is separately sanctioned and archives a validated linked deliberation only through a single-artifact, non-cascading archive, one ID at a time
* Safe-close step 8 and the INV-11 summary key the `RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` halt on Step 0(c)'s **selected** close path, so a classifier `CASCADE` with `ENGINE_SEMANTICS_UNVERIFIED`, which selects `SAFE_CLOSE`, is handled as a `SAFE_CLOSE` shipment there
* Post-mode step 2 archive-checks every disposition `archived` outcome, the step 3 deleted-file guard treats their moves as expected, and retained outcomes never change the step 5 gate
* The Deterministic Safe-Close Scenario Matrix covers linked-deliberation rows (a)–(f): engine unverified, shared reference, engine drift, description-only mention, torn deliberation, and read error; row (c) halts, row (f) retains snapshot/plan-time read errors without halting but halts on a late containment or invariance failure, and every retained outcome is reported without halting
* All six item classifications (including `qualifying-feature-pre-archived-anomaly`) are represented in the schema
* `mode: pre` classifies every manifest item by its declared status, wherever the record resides, under the Member-Class Status Contract; step 2b selects the contract row at the pre-close invocation, and its declared-status rule and member-class table are stated once and referenced everywhere else
* Pre-mode adds a shipment-record-status classification (`record-consistent` /
  `record-queued-with-active-work` / `record-blocked-with-active-work` /
  `record-blocked-with-done-work`) comparing the record's own status against its
  manifest **task-artifact** items' statuses (filtered by `artifact_type` to
  exclude any non-task manifest entry, e.g. a covering feature id, before
  aggregating), with the blocked+active-over-blocked+done precedence
  rule stated explicitly; the four cases are mutually exclusive, computed with
  no new scan (reuses data already read in steps 2–3); any non-`record-consistent`
  classification HALTs the pre-mode recommendation, naming the shipment id,
  record status, and conflicting task ids — detect-and-report only, no auto-repair
* Lock is acquired before pre-mode and released after post-mode (or on any halt)
* Report-and-halt in pre/post mode; safe-close mutation is strictly manifest-scoped with no auto-prune, and the separately sanctioned INV-12 Linked-Deliberation Disposition step is the only additional queue/archive mutation
* `mode: detect-mixed-role` is operator-invoked and strictly READ-ONLY: it
  requires NO `file-lock` acquisition, NEVER mutates any shipment record or
  task, and NEVER calls `backlogit_claim_shipment` or any other status-write
* `mode: detect-mixed-role` classifies each task-artifact manifest item into
  exactly one per-task ROLE (`live-queued` / `live-active` /
  `archived-completed(done)` — either the terminal-relocation `status: done`
  representation or the explicit-archival `status: archived` +
  `archived_status: done` + valid `archived_from` representation) or flags a
  per-item ANOMALY (`duplicate` / `conflicting` / `missing` /
  `malformed-provenance` / `any-other-archived-status` / `orphan` /
  `out-of-role` / `torn-partial`); role classification is used ONLY to
  DESCRIBE the inconsistency in the report, NEVER to gate a mutation
  (013-DL Addendum G)
* `mode: detect-mixed-role` produces exactly one outcome per candidate
  shipment — `DETECTED` / `REPORTED` / `DEGRADED` — with NO
  `succeeded`/`repaired`/`refused`/two-active outcome, and writes a
  structured audit entry (`.autoharness/gates/shipment-reconcile-detection-audit.log`)
  plus a best-effort telemetry event for every outcome, mirroring the
  `pipeline-topology` force-audit + telemetry pattern
* `mode: detect-mixed-role` includes inline Operator-Remediation Guidance on
  any `REPORTED`/`DEGRADED` outcome, explicitly stating autoharness performs
  NO auto-repair and that a record-only forward re-claim is UNSUPPORTED by
  backlogit 1.8.0 (`ClaimShipment` is manifest-wide + all-or-nothing +
  STRICTLY SINGLE-SHOT; NO `active`→`queued` edge; NO
  `blocked` shipment status), with the read-only source evidence, and never
  fabricates a `blocked`→`queued` or
  `active`→`queued` transition
* `mode: detect-mixed-role` DEGRADED (backlogit unreachable) reports the
  degraded condition and HALTs — it never guesses or acts on partial data

## Related Artifacts

* `.github/skills/file-lock/SKILL.md` — lock acquisition/release primitives
* `.github/agents/_ship.agent.md` — integration points (Step 0.5, Step 6 safe-close)
* `.github/agents/_stage.agent.md` — scope guard (Step 5.5)
* `.github/policies/workflow-policies.md` — P-007 archive integrity policy; P-015 single-artifact closure (cascade prohibition) plus the flat-manifest `CASCADE` exception
* `src/autoharness/gates/shipment_closure.py` — this self-hosting repository's own `classify_shipment_close_path` implementation, reused by Step 0 of Safe-Close Mode and, advisory and in-process, by Pre-Mode step 2b

## Model Routing

This skill operates at **Tier 2 (Standard)** — file scanning and frontmatter
comparison do not require frontier-level reasoning.

Generated by autoharness | Template: shipment-reconcile/SKILL.md.tmpl
