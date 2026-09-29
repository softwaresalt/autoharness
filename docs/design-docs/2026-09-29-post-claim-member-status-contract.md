---
title: "Canonical Post-Claim Member-Status Contract (P-002.7, 169-F / 177-S)"
feature: 169-F
shipment: 177-S
tasks:
  - 169.011-T
  - 169.009-T
  - 169.010-T
  - 169.012-T
  - 169.013-T
  - 169.014-T
  - 169.017-T
  - 169.015-T
  - 169.016-T
  - 169.007-T
status: implemented
plan: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_review: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
stash_id: 3EF5AAF2
---

# Canonical Post-Claim Member-Status Contract (P-002.7)

## Purpose

Immediately after a shipment claim, every queued manifest member legitimately
reads `active`: backlogit's `ClaimShipment` activates the shipment record and
every included queued member in one all-or-nothing operation. Before this unit,
no declared surface said so, and a derived or workspace-local admission rule
could read the post-claim all-active manifest as a blocking residual of prior
partial execution. P-002.7 defines the post-claim member-status vocabulary
**once** and states it identically in every declared surface, and a
conformance suite enumerates those surfaces by rule so a surface added later
fails the suite rather than silently diverging.

The authoritative text lives in the workflow policy registry
(`templates/policies/workflow-policies.md.tmpl`, installed as
`.github/policies/workflow-policies.md`) between the
`<!-- P-002.7:BEGIN … -->` and `<!-- P-002.7:END -->` markers. This document
narrates the contract; it does not declare it.

## The contract

### Canonical vocabulary — exactly three claim-to-admission rows

| Row | Shipment record | Manifest members | Admission outcome |
|-----|-----------------|------------------|-------------------|
| T1 | `active` | all `active`, claim just issued | **admit** — the post-claim cascade state, not a residual |
| T2 | `queued` | at least one `active` or `done` | **halt** `SHIPMENT_STATE_INCONSISTENT` |
| T3 | `active` | mixed `done` / `active` / `queued`, mid-execution | **admit** — not an intake-reconciliation case |

No other row belongs to the contract; a fourth row is a conformance failure.

### The distinction it preserves

A mid-execution partial-active manifest (T3) is a genuinely different state
from the post-claim all-active manifest (T1). Any active-residual gate a
workspace authors for the mid-execution state remains valid and is not
weakened: the discriminator is the **claim boundary**, not member status
alone. The Ship agent's queued-with-active-work early-warning
(`SHIPMENT_STATE_INCONSISTENT`, row T2) is unchanged — P-002.7 does not
suppress, soften, or pre-empt it.

### Observed-version attribution

The cascade is an externally-observed behaviour of a tool this repository does
not own, so the clause carries an attribution paragraph naming the versions it
was observed against: backlogit 1.10.0
(`docs/compound/2026-08-21-backlogit-1-10-shipment-claim-cascades-to-children.md`,
pinned upstream by `TestClaimShipment_ActivatesIncludedScope`) and re-observed
against backlogit 1.11.0 at the 177-S claim. The clause records that observed
range only; it is not a claim about all versions, and the cascade must be
re-verified against the installed backlogit version.

### Bidirectional cross-reference

The policy clause names the Ship agent's **Intake reconciliation check** note,
and that note (in `templates/agents/_ship.agent.md.tmpl` and its installed
mirror `.github/agents/_ship.agent.md`) names P-002.7 in return. The two must
be changed together.

## Declared surfaces and the enumeration rule

**Marker set.** A surface declares the contract if it carries the `P-002.7`
anchor together with the canonical vocabulary block or the cross-reference
sentence naming the clause.

**Search scope.** Tracked files under `templates/policies/`,
`.github/policies/`, `templates/agents/` and `.github/agents/`.

**Exclusions, by rule.** `.autoharness/staging/` (gitignored generated
verify-workspace output, not a mirror) and `.autoharness/gates/` (gitignored,
holds the two generated verdict artifacts below). `docs/` narrates and is out
of scope.

**Result — exactly four surfaces, two authoritative/mirror pairs:**

```text
templates/policies/workflow-policies.md.tmpl   (authoritative)
.github/policies/workflow-policies.md          (installed mirror)
templates/agents/_ship.agent.md.tmpl           (authoritative)
.github/agents/_ship.agent.md                  (installed mirror)
```

`declared_surface_count` is fixed at 4. The conformance module
`tests/test_p002_7_member_status_contract.py` asserts the marker resolves in
exactly these four paths and no others.

## Rollout order and decision D2

The unit rolled out **PREPARE → RED → VERIFY → ACTIVATE → CONFIRM → DOCS**,
which conforms to decision D2's binding invariant **PREPARE → VERIFY →
ACTIVATE** (complete evidence set before any activation):

| Phase | D2 phase | Task(s) |
|---|---|---|
| PREPARE | PREPARE | `169.011-T` — inert candidate definition and near-miss fixtures as test-owned data |
| RED | PREPARE (tests go red, then green, within the inert surface) | `169.009-T`, `169.010-T`, `169.012-T`, `169.013-T`, `169.014-T` |
| VERIFY | VERIFY | `169.017-T` — pre-activation readiness verdict |
| ACTIVATE | ACTIVATE | `169.015-T` — one commit, all four surfaces, plus D11 manifest refresh |
| CONFIRM | post-activation | `169.016-T` — post-activation confirmation verdict |
| DOCS | post-activation | `169.007-T` — this document |

D2's compatibility limb (the D3 pinned-fixture corpus) is inapplicable: this
unit introduces no normalizer and reads no historical record corpus. The
complete evidence set is **absence RED**, **discriminating RED** and **inert
GREEN**, per assertion, for all five families (A transition rows, B
bidirectional cross-reference, C template/mirror identity, D attribution, E
exactly-three-rows and exactly-four-surfaces closure).

**D11.** Two declared surfaces are manifest-tracked installed artifacts, so the
activation commit also refreshed their two `.autoharness/harness-manifest.yaml`
checksums in the same commit and rollback unit — five files, four declared
surfaces. The manifest is a commit member, not a declared surface.

## Two verdicts — never conflated

| | Pre-activation readiness | Post-activation confirmation |
|---|---|---|
| Emitter (sole writer) | `169.017-T`, **before** activation | `169.016-T`, **after** activation |
| Observes | the inert candidate as test-owned data, surfaces unmutated | the shipped text on the installed surfaces |
| Artifact | `.autoharness/gates/p002-7-preactivation-readiness.txt` | `.autoharness/gates/p002-7-status-contract-verdict.txt` |
| Line prefix | `PREACTIVATION_STATE: ` | `COMPOSED_STATE: ` |
| Tokens | `PREACTIVATION_READY` / `PREACTIVATION_BLOCKED` / `PREACTIVATION_NOT_OBSERVED` | `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` / `STATUS_CONTRACT_NOT_OBSERVED` |
| Authorizing token | `PREACTIVATION_READY` — authorizes **activation** only | `STATUS_CONTRACT_HELD` — authorizes **documentation** only |
| Authoritative consumer | `169.015-T` ACTIVATE | `169.007-T` DOCS |
| Binding tag | `p002-7-preactivation-binding/v1` | `p002-7-confirmation-binding/v1` |
| `resolved_surface_count` | `0` (inert precondition) | `4` |

The two vocabularies are disjoint and the two paths are distinct; neither
emitter reads or writes the other's artifact, and a token from one vocabulary
is never valid in the other's file. **The post-activation verdict confirms
installed/template parity and active-consumer behaviour; it is not the
evidence gate that authorized activation.** That gate is the readiness
verdict.

**The edge is ordering; the token is authorization.** Each emitter completes on
all three of its tokens, two of which are non-authorizing, so the dependency
edges `169.015-T ← 169.017-T` and `169.007-T ← 169.016-T` only guarantee the
artifact exists before it is read. Each consumer reads its artifact as its
**first action** and fails closed:

* `169.015-T` opens only on a whole file that is exactly one
  `PREACTIVATION_STATE: PREACTIVATION_READY …` line whose `F1`–`F5` recompute.
  On a CLOSED gate it touches **no declared surface**, makes no commit, writes
  neither artifact, and exits `1`.
* `169.007-T` opens only on a whole file that is exactly one
  `COMPOSED_STATE: STATUS_CONTRACT_HELD …` line whose `F1`–`F5` recompute; a
  `PREACTIVATION_*` token or prefix in that file is foreign vocabulary and
  CLOSED. On a CLOSED gate it touches no documentation, makes no commit, and
  exits `1`.

### Artifact rules (both artifacts)

* **Single writer, atomic, whole-file replace.** The emitter writes a
  temporary file in the same directory and renames it over the destination, so
  a reader never sees a partial line, and the file always holds exactly one
  prefixed line. Because every run recomputes `head_commit`, the content digest
  and `checked`, **a re-run necessarily produces a fresh binding**.
* **Exit code.** Each emitter exits zero only on its single authorizing/passing
  token (`PREACTIVATION_READY`, `STATUS_CONTRACT_HELD`), non-zero otherwise.
* **Absence is a reading.** A consumer resolves an artifact to its
  `*_NOT_OBSERVED` token if the file is missing, unreadable, or empty; has no
  prefixed line or more than one; or carries an unrecognised token.
* **Freshness failures are gate failures, not artifact rewrites.** Only the
  emitter may rewrite its artifact; the remedy for a stale verdict is to re-run
  the emitter.
* **Neither artifact is committed or declared.** Both live under
  `.autoharness/gates/`, gitignored at `.gitignore:7`, outside the enumeration
  rule's search scope, so they never leave the tree dirty and can never be
  counted as a fifth surface.

### Line forms

```text
PREACTIVATION_STATE: PREACTIVATION_READY | families=5 | absence_red=5 | discriminating_red=5 | inert_green=5 | declared_surface_count=4 | resolved_surface_count=0 | head_commit=<40-hex> | candidate_digest=<64-hex> | checked=<YYYY-MM-DDThh:mm:ssZ> | binding=<64-hex>
PREACTIVATION_STATE: PREACTIVATION_BLOCKED | families=5 | failed=<n> | family=<A|B|C|D|E> | gap=<short-name> | checked=<YYYY-MM-DDThh:mm:ssZ>
PREACTIVATION_STATE: PREACTIVATION_NOT_OBSERVED | reason=<reason> | checked=<YYYY-MM-DDThh:mm:ssZ>
COMPOSED_STATE: STATUS_CONTRACT_HELD | families=5 | assertions_passed=<n> | declared_surface_count=4 | resolved_surface_count=4 | head_commit=<40-hex> | surface_digest=<64-hex> | checked=<YYYY-MM-DDThh:mm:ssZ> | binding=<64-hex>
COMPOSED_STATE: STATUS_CONTRACT_DIVERGENT | families=5 | failed=<n> | surface=<declared-surface-path> | divergence=<short-name> | checked=<YYYY-MM-DDThh:mm:ssZ>
COMPOSED_STATE: STATUS_CONTRACT_NOT_OBSERVED | reason=<reason> | checked=<YYYY-MM-DDThh:mm:ssZ>
```

The plan enumerates the closed `reason=` vocabularies. Not-observed is
evaluated **first** and absorbs import failure, loader errors, `_FailedTest`
placeholders, zero executed assertions, missing per-assertion records and an
undefined digest; no-observation is never ready and never held.

## Shared gate primitives and the freshness binding

**`CCD/v1` canonical content digest.** Over an ordered, fully enumerated list
of repository-relative POSIX paths: read each file's bytes (a missing or
unreadable input makes the digest **undefined**, which forces the not-observed
token and closes any consumer gate); replace every CRLF with LF and normalize
nothing else; take the lowercase-hex SHA-256 per file; hash the UTF-8
concatenation of `<path>` LF `<file-digest>` LF in list order. The result is
environment-agnostic across Windows and POSIX checkouts.

* Readiness `candidate_digest` — **seven** inputs: the four declared surfaces,
  `tests/p002_7_candidate_definition.py`, `tests/p002_7_near_miss_fixtures.py`,
  `tests/test_p002_7_member_status_contract.py`.
* Confirmation `surface_digest` — **four** inputs: the declared surfaces only,
  because the confirmation's subject is the shipped text.

**Head identity.** `head_commit` is the full 40-hex `HEAD` at evaluation;
`head_committed_at` is that commit's committer timestamp in UTC. Both are read
from the repository.

**`B/v1` binding.** Lowercase-hex SHA-256 of five LF-terminated lines —
`<tag>`, `head_commit=…`, `content_digest=…` (always this literal key),
`resolved_surface_count=…`, `checked=…` — each value byte-for-byte as emitted.
Because the binding covers `checked`, `checked` is a consumed field rather
than a decorative one. `checked` is RFC 3339 UTC, seconds precision:
`YYYY-MM-DDThh:mm:ssZ`.

**`F1`–`F5`, recomputed by both authorizing consumers.**

* `F1` — `head_commit` present once, 40 lowercase hex, equal to current `HEAD`.
* `F2` — content digest present once, 64 lowercase hex, equal to the
  consumer's own `CCD/v1` over that gate's input list.
* `F3` — `resolved_surface_count` equals `0` (readiness) or `4` (confirmation).
* `F4` — `checked` well-formed and not earlier than `head_committed_at` of the
  commit the line itself names.
* `F5` — `binding` present once, 64 lowercase hex, equal to the consumer's own
  `B/v1` recomputation.

Any failure, absent or duplicated field, malformed value, unreadable input or
unresolvable `HEAD` closes the gate; there is no partial satisfaction.

**Why only the authorizing lines carry the binding.** A not-observed verdict is
reachable precisely when the inputs cannot be read, so its digest is undefined
by rule and could not be emitted truthfully; a non-authorizing line is never
consumed as an authorization, so it has nothing to bind. `checked` remains on
all six forms as a diagnostic vintage.

**Honest scope.** This is a **staleness and mistake-detection** contract, not
a tamper-proof security boundary: an actor who recomputes the binding can forge
a self-consistent line. No wall-clock "not in the future" check is imposed,
because clock skew would make the contract environment-dependent.

## Failure path, rollback and recovery

On `STATUS_CONTRACT_DIVERGENT` or `STATUS_CONTRACT_NOT_OBSERVED`:

1. `169.016-T` exits non-zero and the unit halts.
2. DOCS does not proceed, **mechanically**: `169.007-T`'s own first-action read
   finds a token other than the literal `STATUS_CONTRACT_HELD`, touches no
   documentation, makes no commit and exits `1` — independent of whether any
   process observed `169.016-T`'s exit code.
3. The single `169.015-T` activation commit is reverted **as a unit** with
   `git revert`, restoring all four surfaces and both manifest checksums
   simultaneously — a guarantee that holds only because activation is one
   commit.
4. The unit returns to Stage; any re-activation requires a fresh
   `PREACTIVATION_READY` from a re-run of `169.017-T`.

**The revert re-closes both gates without either consumer being told.**
`git revert` creates a new commit, so `HEAD` advances past every
`head_commit` written before it: a surviving `PREACTIVATION_READY` line fails
**`F1` alone** (sufficient) at `169.015-T`, and a surviving
`STATUS_CONTRACT_HELD` line fails **`F1` and `F2`** at `169.007-T`. **`F4` is
not a post-revert guard** — it is anchored to the commit the line itself
names, which a stale line satisfies. Its real function is rejecting a line
whose vintage precedes its own head commit and, with `F5`, preventing
`checked` from being altered after emission.

**Recovery is merge-friendly only:** `git revert` and new forward commits.
`git reset --hard` to the pre-activation commit, and any rebase or amend that
restores the pre-activation commit identity, are **prohibited and outside this
contract** — they would restore exactly the identity a stale readiness line
names and re-open its gate on evidence that was never re-adjudicated. Any
commit between VERIFY and ACTIVATE (or between CONFIRM and DOCS) closes the
downstream gate by design; the remedy is to re-run the emitter.

## CI, and what is explicitly not delivered

`.github/workflows/ci.yml` is a **producer** of the unittest observations both
verdicts are derived from (its `test` job runs the whole suite, including the
conformance module), never a consumer of either verdict line. No task in this
unit modified `ci.yml`, no CI gate was added, and no verdict artifact is
committed; the unit is self-contained.

**Not delivered here:** a `verify-workspace` token that detects P-002.7
divergence in an installed workspace, and its negative-case suite. That
downstream detection belongs to the deferred typed-policy-representation entry
**E770139B**. Until it lands, divergence is detected only by this repository's
conformance module, not by `autoharness verify` in consuming workspaces.

## Evidence (177-S)

| Gate | Result |
|---|---|
| Readiness (`169.017-T`) | `PREACTIVATION_READY` at `head_commit=5a5dec165d0b9bfc1c89daa572203f22326e14d5`, 30 per-observation results (10 assertions × absence RED / discriminating RED / inert GREEN), `resolved_surface_count=0` |
| Activation (`169.015-T`) | readiness gate OPEN (`F1`–`F5`); one commit, five files (four surfaces + manifest), adjudicated index tree equal to `HEAD^{tree}` |
| Confirmation (`169.016-T`) | `STATUS_CONTRACT_HELD` at the activation commit, `assertions_passed=10`, both mirror pairs byte-identical, four surfaces resolved |
| Documentation (`169.007-T`) | confirmation gate OPEN (`F1`–`F5`) before this document was written |
