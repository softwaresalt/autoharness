---
title: "BOOTSTRAP-A durable evidence record — 173-S entry (decision D6)"
status: recorded
date: 2026-09-13
shipment_id: 173-S
feature_id: 165-F
authorizing_decision: D6
related_docs:
  - docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md
  - docs/plans/2026-09-12-dag-authoritative-predecessor-derivation-plan.md
  - docs/memory/2026-09-12/stage-dag-authoritative-predecessor-derivation.md
---

# BOOTSTRAP-A durable evidence record — `173-S` entry

This is the durable, version-controlled authorization record for the one-time
operator-run `173-S` entry, per plan §H6 ("Durable evidence (B5)") under
decision **D6** (`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`,
§"D6 — Bootstrap disposition for `173-S`"). `.autoharness/gates/` is
gitignored in this repository, so the local force-audit log is not by itself
reviewable authorization evidence; this document, committed on the `173-S`
shipment branch, is the authorization record of record.

## Manifest (11 items, exact order)

The `173-S` shipment manifest, `custom_fields.items`, in exact declared order:

1. `165-F`
2. `165.001-T`
3. `165.002-T`
4. `165.003-T`
5. `165.004-T`
6. `165.005-T`
7. `165.006-T`
8. `165.008-T`
9. `165.011-T`
10. `165.012-T`
11. `165.009-T`

## B0 — unforced verify, `main` (mirrors Orchestrator route-to-Ship site)

- Vantage: `main`
- HEAD: `dffb02f9eb9e8df3bd62d88f48efe2a29f0b2bb2`
- Command: `autoharness gate pipeline-topology --mode agent --phase pre_claim --shipment 173-S --json` (unforced)
- Result: exit code `1`
- Sole blocking token: `PREDECESSOR_NOT_SHIPPED`
- Detail: predecessor `172-S`, observed status `queued`
- Disposition: verified condition-matched block; forced re-run authorized under D6 and executed

### B0 force-audit record (durably logged)

Present verbatim in `.autoharness/gates/pipeline-topology-force-audit.log`:

```json
{"timestamp": "2026-09-13T20:17:45.279406+00:00", "actor": "dewilliams", "reason": "--force override", "mode": "agent", "phase": "pre_claim", "target_shipment_id": "173-S", "token": "PREDECESSOR_NOT_SHIPPED", "message": "PREDECESSOR_NOT_SHIPPED: predecessor 172-S is not in a shipped terminal state"}
```

(`2026-09-13T20:17:45.279406+00:00` UTC = `2026-09-13T13:17:45.279406-07:00` local, matching the operator-reported B0 force timestamp.)

## B1 — unforced verify, `main` (mirrors Ship's pre-branch site)

- Vantage: `main`
- HEAD: `dffb02f9eb9e8df3bd62d88f48efe2a29f0b2bb2`
- Command: `autoharness gate pipeline-topology --mode agent --phase pre_claim --shipment 173-S --json` (unforced)
- Result: exit code `1`
- Sole blocking token: `PREDECESSOR_NOT_SHIPPED`
- Detail: predecessor `172-S`, observed status `queued` — **the same exact payload as B0**, same HEAD.
- Disposition: verified condition-matched block; forced re-run authorized under D6

### B1 force-audit record — ACCEPTED RESIDUAL PROVENANCE GAP

**No corresponding local audit line survives in
`.autoharness/gates/pipeline-topology-force-audit.log` for B1.** The log
contains exactly two `pre_claim`/`173-S`/`PREDECESSOR_NOT_SHIPPED` force
entries — the B0 entry above and the B2 entry below — with no third entry
between them. The operator supplied a forced-B1 result payload in chat (exit
`0`, `forced: true`, the same sole token `PREDECESSOR_NOT_SHIPPED` and
predecessor `172-S`, and a `force_audit_log` path), but **that payload is
operator-supplied and unverified by the local audit log**; it is recorded
here exactly as reported, with no fabricated timestamp and no fabricated
audit identity, and no replay of the missing local audit line.

**Operator disposition (explicit, verbatim from chat):**

> "I accept the missing B1 audit record as documented residual risk and
> proceed with B5/B6."

This is recorded as an **accepted, one-time residual provenance gap**: the
B1 forced-pre_claim event for `173-S` occurred (per the operator's own report
and per the B0→B2 sequencing this record establishes) but its local durable
audit trail does not independently corroborate it. This document does not
claim full three-line audit provenance for BOOTSTRAP-A; it claims exactly
**two** durably audited force lines (B0, B2) plus **one** operator-reported,
audit-unconfirmed force result (B1), and records that gap honestly rather
than inventing a matching log line.

## B2 — unforced verify, `173-S` shipment branch (immediately before claim, TOCTOU narrowing)

- Vantage: canonical `173-S` shipment branch
- HEAD: `dffb02f9eb9e8df3bd62d88f48efe2a29f0b2bb2`
- Command: `autoharness gate pipeline-topology --mode agent --phase pre_claim --shipment 173-S --json` (unforced)
- Result: exit code `1`
- Sole blocking token: `PREDECESSOR_NOT_SHIPPED`
- Detail: predecessor `172-S`, observed status `queued` — **the same exact payload as B0/B1**, same HEAD.
- Disposition: verified condition-matched block; forced re-run authorized under D6 and executed

### B2 force-audit record (durably logged)

Present verbatim in `.autoharness/gates/pipeline-topology-force-audit.log`:

```json
{"timestamp": "2026-09-13T21:31:14.625551+00:00", "actor": "dewilliams", "reason": "--force override", "mode": "agent", "phase": "pre_claim", "target_shipment_id": "173-S", "token": "PREDECESSOR_NOT_SHIPPED", "message": "PREDECESSOR_NOT_SHIPPED: predecessor 172-S is not in a shipped terminal state"}
```

(`2026-09-13T21:31:14.625551+00:00` UTC = `2026-09-13T14:31:14.625551-07:00` local, matching the operator-reported B2 force timestamp.)

## Audit-record summary (honest provenance accounting)

| Step | Unforced result | Force authorized (D6) | Local durable audit line |
|---|---|---|---|
| B0 | exit 1, `PREDECESSOR_NOT_SHIPPED`/`172-S` | Yes | **Present** — `2026-09-13T20:17:45.279406Z` |
| B1 | exit 1, `PREDECESSOR_NOT_SHIPPED`/`172-S` (same payload) | Yes | **Absent** — operator-supplied/unverified (accepted residual risk) |
| B2 | exit 1, `PREDECESSOR_NOT_SHIPPED`/`172-S` (same payload) | Yes | **Present** — `2026-09-13T21:31:14.625551Z` |

Only **two** of the three authorized force invocations have independent local
audit corroboration. This record does not claim otherwise.

## B3 — claim

- Command: `backlogit shipment claim 173-S`
- Result: shipment `173-S` and all 11 manifest items transitioned to `active`.
- Observed post-claim statuses (verified against `.backlogit/queue/*.md`, not
  assumed): `173-S` → `active`; `165-F` → `active`; `165.001-T` through
  `165.012-T` (all manifest task members: `165.001-T`, `165.002-T`,
  `165.003-T`, `165.004-T`, `165.005-T`, `165.006-T`, `165.008-T`,
  `165.009-T`, `165.011-T`, `165.012-T`) → `active`.

## Initial B4 — unforced `post_claim` verify (FAILED)

- Vantage: `173-S` shipment branch
- Command: `autoharness gate pipeline-topology --mode agent --phase post_claim --shipment 173-S --json` (unforced; no force is authorized at `post_claim`)
- Result: **non-zero**, blocking token `PREDECESSOR_NOT_SHIPPED` for predecessor
  `172-S`, even though the claim to `173-S` had already succeeded.
- Root cause diagnosed: `_shipment_readiness_check` in
  `src/autoharness/gates/topology.py` incorrectly re-applied
  claim-**eligibility** predecessor sequencing during `post_claim` (and
  `lifecycle`). Predecessor sequencing exists to keep an unshipped
  predecessor from being claimed out of order and belongs to `pre_claim`
  only; `post_claim`/`lifecycle` run strictly after a claim has already
  succeeded (their phase requirement already enforces `live_status ==
  "active"` for the target), so a still-unshipped predecessor cannot
  retroactively un-claim an already-active target.
- Per plan §H6 B4 failure contract: `173-S` was **left `active`**; B5/B6 were
  not performed until remediation converged; no forced re-run was attempted
  (BOOTSTRAP-A's force authority had already expired at the successful B3
  claim); no `active` → `queued` reversal was attempted (no such transition
  exists in backlogit).
- Operator-selected remediation path: **(a) diagnose and converge** — the
  expected path per plan §H6 — resolve the defect, re-run B4 unforced until
  it exits 0, then resume at B5. `173-S` remained `active` throughout; this
  was a forward fix, not a rollback.

## Remediation — diff and test evidence

Bounded source/test change, present in the working tree at the time of this
evidence record and verified in this same session:

- `src/autoharness/gates/topology.py`: `_shipment_readiness_check` now
  short-circuits with a `passed` result (`predecessor_ids: []`) when
  `phase in ("post_claim", "lifecycle")`, before evaluating explicit
  `blocking_predecessor_ids` or the implicit numeric-adjacency
  `_prior_shipment_id` heuristic. `ambient` is intentionally excluded from
  this bypass (no claim-success precondition of its own; predecessor-check
  scope unchanged for that phase).
- `tests/test_gates_topology.py`: two new tests added to
  `PostClaimVerifyTests`:
  - `test_active_target_passes_post_claim_despite_unshipped_explicit_predecessor`
    — proves an active target passes `post_claim` despite an unshipped
    explicit declared-dependency predecessor, and that the **identical**
    fixture still blocks at `pre_claim` (proving this is a phase-scoping fix,
    not a removal of the predecessor check).
  - `test_active_target_passes_post_claim_despite_unshipped_implicit_numeric_predecessor`
    — same phase-scoping guarantee for the implicit numeric-adjacency
    heuristic (`_prior_shipment_id`).
- Test evidence (as reported and reconfirmed in this session): the two new
  tests observed RED before the fix; after the fix, targeted topology tests
  passed (115 tests, 113 subtests) and the full suite passed (2141 passed,
  51 skipped, 1882 subtests). Reconfirmed in this session:
  `uv run python -m pytest tests/test_gates_topology.py -q` →
  **115 passed, 113 subtests passed**.

## Successful unforced B4 rerun (POST-REMEDIATION)

- Vantage: `173-S` shipment branch (this branch)
- Command: `autoharness gate pipeline-topology --mode agent --phase post_claim --shipment 173-S --json` (unforced)
- Result: exit code `0`
- `forced: false`
- All five topology checks passed.
- `173-S` confirmed sole active shipment.
- `shipment_readiness` check: `predecessor_ids: []` (empty) — the fixed
  phase-scoping behavior.

This B4 rerun was executed exactly once after the remediation landed and is
not re-run by this document; current working-tree and test-suite state is
unchanged since that run (verified in this session by re-confirming file
diffs and re-running the targeted topology test module, which reproduced the
identical 115-passed/113-subtests result).

## Decision D6

Authorizing decision: **D6 — Bootstrap disposition for `173-S`**
(`docs/decisions/2026-09-12-dag-authoritative-predecessor-derivation-deliberation.md`).
D6 authorizes forcing `pre_claim` for `173-S` only, at most three times, bound
to token `PREDECESSOR_NOT_SHIPPED` and predecessor `172-S`. No force is
authorized at `post_claim`; the initial B4 failure was resolved by diagnosing
and fixing the defect (operator-selected remediation path (a), "diagnose and
converge"), never by forcing `post_claim`. BOOTSTRAP-A's force authority
expired at the successful B3 claim; no agent-side force, grant, or gate
bypass is authorized in B5/B6.

## Honest provenance disposition (summary)

This record does **not** claim complete independent audit-log provenance for
all three authorized BOOTSTRAP-A force invocations. It claims:

- **B0**: durably audited locally, timestamp verified.
- **B2**: durably audited locally, timestamp verified.
- **B1**: authorized under D6 and reported by the operator as executed
  successfully (exit 0, forced true, same sole token/predecessor), but with
  **no surviving local audit-log corroboration**. This is recorded, per
  explicit operator instruction, as an **accepted one-time documented
  residual provenance gap** — not fabricated, not backfilled, and not
  replayed into the audit log.
