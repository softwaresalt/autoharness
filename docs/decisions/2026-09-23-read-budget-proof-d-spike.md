---
title: "Proof D - read-budget equation: findings (FAIL)"
source: "docs/decisions/2026-09-23-read-budget-proof-d-spike.md"
doc_type: decision
description: "Stage-authored Proof D findings under charter PE-1.1 section 6.6. Stage derived the closed-form file-slot claim count C(N,U,rho) = 4(N+1) + 3U(1+rho) read-only from frozen plan revision 12, and Ship ran one disposable scratch script that exhaustively checked all 2048 admitted combinations against an individually simulated claim sequence, with negative controls. The script exited 0, which only confirms the model and a counterexample: at N=62, U=1, rho=1 the count is 258 > max_files=256, and at N=64 every U/rho variant exceeds the limit, while plan revision 12 admits N up to 512 (C=2058). Under section 6.6 any admitted N over budget is FAIL, so Proof D is FAIL, not PASS. PE-DATA-03 and PE-SAFETY-04 are not satisfied. The frozen plan also defines no explicit closed reducer class for budget exhaustion. The admitted-bound, budget and read-plan decision and the exhaustion-reducer decision are reopened to architecture/charter per section 6.1; no plan revision 13 or review attempt 12. The one disposable scratch file still exists: its cleanup is blocked and needs operator action."
docline:
  type: spike
  date: 2026-09-23
  time_box: "45m"
  conclusion: "pivot"
  confidence: "high"
  linked_parent_work_item: "181-F"
  promoted_to: ["none"]
  tags:
    - "read-budget"
    - "file-count-limit"
    - "reducer"
    - "proof-entry"
    - "ship-lifecycle"
proof: D
proof_verdict: FAIL
charter: docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md
charter_version: "1.1"
matrix_id: PE-1.1
matrix_rows: [PE-DATA-03, PE-SAFETY-04]
branch: chore/stage-176-s-workflow-defects
head_at_authoring: 3df0509f
feature_id: 181-F
shipment_id: 187-S
shipment_claim_ready: false
actor_invoked: false
review_scheduled: false
backlog_item_created: false
plan_changed: false
fail_route: architecture-or-charter
time_bound_status: not-established
file_bound_status: met
scratch_cleanup_status: blocked-operator-action-required
---

# Proof D findings - read-budget equation

## Verdict

| Field | Value |
|---|---|
| Verdict | **`FAIL`** |
| Fail criterion (charter section 6.6) | "Any admitted `N` exceeds the budget": **met**. The first counterexample is `N=62, U=1, rho=1`, with `C=258 > 256`. At `N=512` the count is between 2052 and 2058 |
| Pass criterion (charter section 6.6) | Not met. `C(N_max)` does not fit `max_files=256`, and the frozen plan names no explicit reducer class for budget exhaustion |
| Meaning of the script's exit 0 | The equation model, the exhaustive check and the negative controls held, and an admitted over-budget input was shown. **Exit 0 is not a product `PASS`.** It is the evidence for the `FAIL` |
| Time bound (charter sections 6.1, 6.2) | 45m, Stage plus Ship combined: **not established** (see Time and File Bounds). This does not change the verdict, which is already `FAIL` |
| File bound | 1 disposable: **met** (one script). It has **not been cleaned up** (see Scratch Hygiene) |
| Matrix rows | `PE-DATA-03`: **not satisfied**. `PE-SAFETY-04`: **not satisfied** (its Proof D half fails, whatever Proof G finds) |
| Route (charter section 6.1) | `FAIL` goes back to architecture or charter (Phase 0), with the reopened decisions named below. It does **not** trigger plan revision 13, review attempt 12 or a prose plan rewrite |

## Goal

Answer charter section 6.6: can the admitted maximum membership exhaust the
read budget by itself? Use a closed-form claim count over every claim source
and inputs from frozen plan revision 12 (diagnostic only): `max_files=256`,
admitted membership `1..512`, and the real `187-S` membership of seventeen
items.

## Success Criteria

* **Pass**: `C(N)` is checked for every admitted `N` and for `N=17`.
  `C(N_max)` fits the file and byte limits with a recorded margin, and budget
  exhaustion maps to an explicit reducer class that yields `UNRESOLVED`, never
  `NO_HARNESS`.
* **Fail**: any admitted `N` goes over the budget, or the time or file bound
  is exceeded (charter section 6.1).
* **Blocked**: a per-invocation gate rejected Ship's verification-only
  execution, or a required environment was not available.

## Scope Constraints

* Stage did read-only analysis only. It ran no fixture command, build, test
  suite or linter (P-010; charter section 6.1). Stage did not run the scratch
  script. It only read the script and hashed it.
* This findings artifact is the only tracked change. No plan, review,
  backlog, shipment, policy, schema, charter, source, template or
  configuration file was changed.
* No claim, pull request, push, plan revision 13 or review attempt 12 took
  place. One worktree was used, and the P-016 exception was not used.
* **Amend disclosure (correction).** An earlier version of this artifact
  said no amend took place. That was false. Stage amended its own first
  local, unpushed commit `6a85ad4` into `b3fca43` to fix the
  `Co-authored-by` trailer. Only the commit message changed; the artifact
  content was the same in both commits. This correction is a new local
  commit. It does not amend, rebase or rewrite history.
* Nothing is in scope beyond Proof D.

## Session and Tool State

| Item | State |
|---|---|
| Backlog tool | backlogit MCP `TOOL_OK` (read-only version probe; `1.10.1-0.20260823032255-b07729386a31+dirty`) |
| Stage checkpoints | 67 enumerated with no status or agent filter; 0 anomalies; 0 active `stage`-owned. This is a normal startup with zero candidates |
| Engram | Circuit open; not retried (operator instruction). `ENGRAM_DEGRADED` |
| Intercom | Unavailable. `INTERCOM_DEGRADED` |
| Graphtor-docs | Unavailable. `GRAPHTOR_UNAVAILABLE`; `docs/` read from files |
| Worktree at Stage authoring | One worktree; HEAD `3df0509f5db9edadabe44966306359cc701e0405`; `git status --porcelain` showed only `?? .proof-scratch/proof-d-20260923-231729/d_budget.py` |

## Derivation (Stage, Read-Only)

These plan revision 12 rules, all frozen diagnostic inputs, produce the
count:

* Session budgets: "Each lexically valid request claims one file slot before
  root/adapter work. The claim is never refunded."
* Request lookup: for the shipment and for every member, the resolver
  consults **both** `queue/<id>.md` and `archive/<id>.md`, and "Both present
  and stable-absent observations enter the ledger."
* Observation ledger: "After a provisional result, the resolver re-observes
  the ledger through the same trust-root session." Each re-observation is a
  new request, so it claims a new slot.
* Surfaces: when the surface union is non-empty (`U=1`; one-entry
  `SurfaceSpec`), the reads are the manifest, the template and the installed
  file. The plan does not say whether the ledger recheck covers those three
  reads. That is the parameter `rho` in `{0,1}`.

This gives:

```text
C(N, U, rho) = 2(N+1)        initial queue+archive claims, shipment + N members
             + 2(N+1)        ledger rechecks of those candidates
             + 3U            manifest, template, installed
             + 3U*rho        surface rechecks
             = 4(N+1) + 3U(1+rho)
```

| Case | `C` | Against `max_files=256` |
|---|---|---|
| `187-S`, `N=17`, `U=1`, `rho=1` | 78 | Fits (margin 178) |
| `N=61`, every `U`/`rho` | at most 254 | Fits |
| `N=62`, `U=1`, `rho=1` | **258** | **Over by 2** (first counterexample) |
| `N=62`, `U=1`, `rho=0` | 255 | Fits |
| `N=63`, `U=0` | 256 | Fits with zero margin (charter requires a recorded margin) |
| `N=63`, `U=1`, `rho=0` / `rho=1` | 259 / 262 | Over, whatever `rho` is |
| `N=64`, every `U`/`rho` | at least 260 | Over for every variant |
| `N=512`, `U=0` / `U=1,rho=0` / `U=1,rho=1` | 2052 / 2055 / 2058 | Over by about 8x |

The largest `N` that fits every `U`/`rho` variant under the plan's current
read plan is 61. The plan admits 512.

Byte limits (`max_file_bytes`, `max_total_bytes`) were not evaluated. The
file-count limit already fails, and nothing here makes a byte-fit claim.

## Evidence Provenance (Ship Verification-Only Invocation)

Ship produced all execution evidence under charter section 6.1. Stage records
it as reported and did not run it again.

| Gate / fact | Result |
|---|---|
| P-001 / P-002 / P-011 / P-016 | Satisfied before the write (Ship-reported); no claim |
| Worktree before scratch | Clean (Ship-reported); HEAD `3df0509f5db9edadabe44966306359cc701e0405` |
| Host | Windows 11; Python 3.14.3 |
| Scratch | `.proof-scratch/proof-d-20260923-231729/` inside the current worktree |
| Command | `python .proof-scratch/proof-d-20260923-231729/d_budget.py` |
| Exit status | Native exit 0 |
| Timestamp / runtime | 2026-09-23T23:18:09-07:00; 1.126488 s script runtime |
| Fixture listing | One file, `d_budget.py`, 9102 bytes, SHA-256 `726315233c2774564f4a4518e6519ba795756500375979eff4470434e944ae12` |
| Stage read-only confirmation | Stage hashed the file again at authoring: same size and same SHA-256. The scratch directory holds only this file |
| Raw stdout / stderr | Not included verbatim in the handoff; the key values were reported. Because the script's assertions are fixed in the hashed source, exit 0 shows they all held (next section) |

### What the Script Checked (from the Hashed Source)

* It enumerates every `N` in `1..512`, `U` in `{0,1}` and `rho` in `{0,1}`,
  which is 2048 cases. For each case it simulates each non-refundable slot
  claim one at a time. The fixture has the queue candidate present and the
  archive candidate stably absent. Both are separate requests, and rechecks
  are new requests. The script asserts that the simulated count equals the
  closed form.
* It asserts `cases == 2048` and that the first over-budget case is
  `(62, 1, 1, 258)`.
* It asserts boundary tables for `N` = 17, 61, 62 and 512, including
  `N=17, U=1, rho=1` = 78.
* It asserts the `rho`-independent counterexample (`N=63, U=1`: 259 and 262),
  that every variant is over at `N=64`, and that every variant fits at
  `N=61`.
* It prints `"charter_verdict": "FAIL"`, and states that exit 0 "does not mean
  Proof D passes".

### Negative Controls

Each control changes the claim model and asserts that the change is caught.
Exit 0 means all four were caught. The mutant counts below for
`N=17, U=1, rho=1` (correct value 78) are what the hashed source computes.
Stage derived them from the source, not from stdout.

| Control | Mutant count | Caught |
|---|---|---|
| Stable-absent candidates not charged | 42 | Yes |
| Ledger rechecks skipped | 39 | Yes |
| All three surface files re-read per task (`+3NU`) | 129 | Yes |
| Off-by-one (+1 / -1) | 79 / 77 | Yes |

The script also asserts, within a narrow scope, two plan rules: a lexical
rejection changes the slot count by zero, and invalid IDs are validated
before any candidate lookup. It makes no other claim about resolver or
session cost.

## Findings

1. **Admitted bound and file budget are inconsistent.** Plan revision 12
   admits memberships up to 512 (`MEMBERS_TOO_MANY` above that) and fixes
   `max_files=256`, with non-refundable claims for both candidates and every
   recheck. Starting at `N=62`, a valid, fully admitted shipment can use up
   the file budget by itself. The real `187-S` (`N=17`, `C=78`) fits, but the
   pass criterion covers every admitted `N`.
2. **No explicit closed reducer class for budget exhaustion.**
   `FILE_COUNT_LIMIT` and `TOTAL_SIZE_LIMIT` exist as `ReadErrorCode` values.
   The reducer precedence (plan section "Reducer precedence", classes 1-8)
   has only the generic class 2 ("request, root, shipment, membership or
   member-record error -> `UNRESOLVED / 2`") and no class or reason for
   budget exhaustion. The plan text does not decide how exhaustion is
   classified at the stages where it first occurs. Two examples: during the
   ledger recheck (for `U=1, rho=1` at `N=62`, the first over-limit slot is a
   surface recheck), where the only defined dominant class is mutation; and
   during the installed-file read, where the nearest rule says "Missing
   installed bytes are `MISSING`", which reduces to `NO_HARNESS / 1`. So
   "exhaustion yields `UNRESOLVED`, never `NO_HARNESS`" cannot be shown from
   the frozen text. **This artifact creates no closed reason code.**
3. **Threat-model note.** The plan's adversarial handle-relative traversal
   design is frozen diagnostic material only. Under the operator-approved
   Option B+D (charter section 5), ordinary static containment applies, and
   nothing here claims race, TOCTOU or hardlink-alias resistance.

### Matrix Row Status (Proof D Only; Not a Proof-Exit Audit)

| Row | Criterion | Status |
|---|---|---|
| `PE-DATA-03` | `C(N) <= max_files` for every admitted `N`; exhaustion yields `UNRESOLVED` | **Not satisfied**. Fails at `N >= 62`, and no exhaustion reducer class is defined |
| `PE-SAFETY-04` | Proof D equation passes, and Proof G bound cases pass | **Not satisfied**. Proof D half fails. Proof G was not assessed here |

## Time and File Bounds

| Component | Elapsed |
|---|---|
| Stage earlier read-only D derivation | About 9m (approximate; not measured exactly) |
| Ship invocation | **Not reported.** Only the script runtime (1.126488 s) is known, not Ship's whole invocation time |
| Stage authoring (this session, host clock, 23:20:52 to the pre-commit check at 23:24:03 local) | About 3m11s |
| **Combined** | **Not established.** Stage does not claim the 45m bound was met |

File bound: one disposable file, as Ship reported and Stage confirmed by
read-only listing. The bound was not exceeded, but the file still exists.

## Scratch Hygiene (Cleanup Blocker)

* **State.** `.proof-scratch/proof-d-20260923-231729/d_budget.py` (9102 bytes,
  SHA-256 `726315233c2774564f4a4518e6519ba795756500375979eff4470434e944ae12`)
  still exists, untracked. `git status --porcelain` shows only this path
  (`?? .proof-scratch/`).
* **Why it is blocked.** Ship did not delete the file on the first
  invocation. A second Ship cleanup invocation confirmed that the file is the
  only item in the resolved in-repo directory
  `C:\Source\GitHub\autoharness\.proof-scratch\proof-d-20260923-231729`, but
  its P-010 fail-closed check refused a direct delete. Ship held the
  deletion P-010 FORBIDDEN even though the operator had already given a
  "Proceed" approval. Intercom was unavailable, so no intercom auto-check
  could run either. Giving the same approval to Ship again does not change
  the role boundary.
* **Stage disposition.** Stage did not delete, stage or commit the scratch
  file. Stage's commit stages only this findings artifact by explicit path.
  The untracked scratch file is not part of it.
* **Operator-action path (only this verified scratch).** Under the current
  role boundary, no agent deletes this file. That includes Orchestrator,
  Stage and Ship. An earlier version of this artifact offered a "Ship
  deletes after operator approval" option. That option does not work and is
  withdrawn. The operator has two options:
  1. **Delete it personally.** Check that the resolved path is exactly
     `C:\Source\GitHub\autoharness\.proof-scratch\proof-d-20260923-231729`.
     Check that it holds only `d_budget.py`, 9102 bytes, with the SHA-256
     above. Delete only that file. Then delete that directory once it is
     empty. Delete the `.proof-scratch/` parent only if it is also empty.
     Confirm that `git status --porcelain` is empty. Delete nothing else.
  2. **Change the contract first.** In a separate, authorized work unit,
     change the higher-order role or policy contract (P-010 and the agent
     role boundaries) so that a named agent may delete this scratch. The
     deletion can happen only after that change. This artifact does not make
     that change.

  Until one of these happens, the hygiene state is **open**. It does not
  change the verdict and is not a product `PASS`.

## Reopened Decisions (Charter Section 6.1 FAIL Routing)

These go to architecture or charter (Phase 0). **None is chosen here.**

| Decision | Options (charter section 6.6) | Status |
|---|---|---|
| Proof D reopened decision 1: admitted membership bound, file budget, or read plan | (a) lower the admitted maximum (no more than 61 under the current read plan, with a recorded margin); (b) raise `max_files` (above 2058 for `N=512` under the current read plan, with margin); (c) replan reads, for example by changing absence charging, recheck scope, or per-request slot accounting | Open; operator/architecture decision |
| Proof D reopened decision 2: explicit closed reducer class for budget exhaustion, giving `UNRESOLVED`, never `NO_HARNESS`, at every stage including rechecks and surface reads | To be defined in the chosen architecture; no code is created here | Open; operator/architecture decision |

After a decision, a new Proof D run against the chosen parameters must be
chartered. It is not a revision of the frozen plan.

## Recommendation

**Pivot**, through architecture or charter only. The frozen revision 12
budget and membership parameters together fail. Keep plan revision 12 and
review attempt 11 frozen. Do not open plan revision 13 or review attempt 12.
Present the two reopened decisions to the operator.

## Next Steps

* Operator: personally check and delete only the hash-matched scratch file
  and the empty directories (Scratch Hygiene, option 1). The alternative is
  to first change the role or policy contract in a separate, authorized work
  unit (option 2). Under the current boundary, Orchestrator, Stage and Ship
  do not delete it, and approving Ship again does not resolve this.
* Operator/architecture: settle Proof D reopened decisions 1 and 2, then
  charter a new Proof D run.
* Record this `FAIL` and its route in the proof-exit report (charter section
  8). `187-S` stays `queued` and is not claim-ready.

## References

* `docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md` (sections
  5, 6.1, 6.2, 6.6, 7.6 row `PE-SAFETY-04`, 7.7 row `PE-DATA-03`, 8)
* `docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md`
  (revision 12, frozen: `ReadErrorCode`, `ReadLimits`, Session budgets,
  Request/root/record lookup, Observation ledger, Reducer precedence)
* `docs/decisions/2026-09-23-staged-blob-checksum-proof-f-spike.md` (format)
* `.github/skills/spike/SKILL.md`
* `.github/agents/_stage.agent.md`
* `.github/agents/_ship.agent.md`
