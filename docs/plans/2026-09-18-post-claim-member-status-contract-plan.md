---
title: "Canonical post-claim member-status contract (P-002.7) with RED-first cross-surface evidence, a freshness-bound pre-activation readiness gate and a verdict-gated DOCS step"
description: "Reduced current-state contract for the post-claim member-status defect, stash 3EF5AAF2. Keeps one contract — a canonical member-status vocabulary asserted identically across exactly four enumerated surfaces — and closes the attempt-08 finding that its evidence was GREEN-only by giving every assertion, including mirror-divergence, version-attribution and the negative state-machine rows, its own RED task that records the assertion failing individually and discriminatingly before any production text exists. The rollout is PREPARE, RED, VERIFY, ACTIVATE, CONFIRM, DOCS and conforms to the binding rollout invariant of decision D2, PREPARE then VERIFY then ACTIVATE: this plan's PREPARE and RED together are D2's PREPARE, whose own rule is that tests go RED first then GREEN entirely within the inert surface; 169.017-T is D2's VERIFY, producing the complete evidence set before any activation; 169.015-T is D2's ACTIVATE. 169.017-T is the pre-activation readiness gate: it evaluates absence RED, discriminating RED and INERT GREEN for all five assertion families against the inert candidate, requires the inert precondition resolved_surface_count=0, and emits PREACTIVATION_READY, PREACTIVATION_BLOCKED or PREACTIVATION_NOT_OBSERVED to .autoharness/gates/p002-7-preactivation-readiness.txt. Activation is authorized by that verdict and not by a dependency edge: 169.015-T reads the artifact as its first action and fails closed, and PREACTIVATION_READY is the only token that opens the gate. Activation remains one task and one commit across all four surfaces, because a template and its installed mirror joined by a dependency edge admit a reachable state in which they disagree; it transcribes only, authors nothing, narrows nothing and reinterprets no evidence, and if it cannot fit inside two hours the unit halts and returns to Stage. 169.016-T is the distinct post-activation confirmation, retained and retitled rather than archived: it confirms installed/template parity and active-consumer behaviour, adds no assertion, and emits STATUS_CONTRACT_HELD, STATUS_CONTRACT_DIVERGENT or STATUS_CONTRACT_NOT_OBSERVED to .autoharness/gates/p002-7-status-contract-verdict.txt. It is explicitly not the evidence gate that authorized activation, and its failure has an explicit path: halt, do not proceed to DOCS, revert the single activation commit as a unit, return to Stage. That halt is mechanical and not merely ordered: 169.007-T reads the confirmation artifact as its own first action under the same fail-closed shape 169.015-T uses, and on any reading other than the literal STATUS_CONTRACT_HELD it touches no documentation file, creates no commit and exits non-zero. Both authorization predicates are freshness-bound: each authorizing line carries head_commit, a canonical content digest over a fully enumerated input list, and a binding digest covering checked=, and each consumer recomputes all three against the repository before it acts, so a stale verdict cannot authorize a second activation or a documentation commit on the documented post-revert re-activation path. Both artifacts are gitignored, single-writer, atomically written, whole-file-replaced, hold exactly one verdict line, evaluate absence fail-closed, and exit zero only on their single authorizing or passing token; their paths, line prefixes and token vocabularies are disjoint and are never conflated. Neither is a declared surface, so declared_surface_count stays fixed at 4. No CI workflow is read as a verdict consumer or modified. Carries no dependency on the operation substrate: this unit changes declarations and their conformance test, not execution boundaries, and is the only defect unit that is a DAG root."
doc_type: plan
source: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
date: 2026-09-18
plan_id: post-claim-member-status-contract-v2
plan_path: docs/plans/2026-09-18-post-claim-member-status-contract-plan.md
plan_role: active
revision: 6
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "verdict is null because no independent reviewer has judged revision 6. REMEDIATED-PENDING-REVIEW is recorded under disposition, where it belongs: it states what Stage produced, never what a reviewer found. Revision 6 is the product of one operator-authorized bounded remediation cycle against independent terminal attempt 05, which returned ADVISORY on revision 5 with zero P0, zero P1, two P2 (N1, N2) and four P3 (N3, N4, N5, M4). The cycle is scoped to N1 and N2 and to mechanically necessary consistency edits. N1: the CONFIRM-to-DOCS edge was a completion edge, enforced in prose and by a blocks edge, although the plan asserted in four places that DOCS must not proceed on a non-pass confirmation and applied its own H18 gate-predicate principle only to the ACTIVATE edge. Revision 6 gives 169.007-T a first-action fail-closed whole-file read of the confirmation artifact with a literal STATUS_CONTRACT_HELD comparison, a declared CLOSED enumeration covering absence, malformation and staleness, a zero-documentation-touch and zero-commit guarantee on CLOSED, and a declared non-zero exit. N2: all three readiness line forms carried a checked= vintage field that R12 named as the stale-verdict mitigation while the activation predicate's five conditions never read it. Revision 6 adds the CCD/v1 canonical content digest, the head identity pair, and the B/v1 freshness binding as shared gate primitives defined once and instantiated twice; the readiness READY line and the confirmation HELD line now carry head_commit, a content digest over a fully enumerated input list, an RFC 3339 UTC checked= and a binding= that covers checked=, and both consumers recompute all of them against the repository before acting. N3, N4, N5 and M4 are carried unaddressed and are out of this cycle's scope; M4 remains tool-derived and the item hierarchy was not changed to silence it. Stage asserts no PASS, has performed no self-review, and has decremented no finding count."
awaiting_attempt: 6
review_manifest: docs/reviews/2026-09-18-post-claim-member-status-contract-v2-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 3EF5AAF2
feature_id: 169-F
shipment_id: 177-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-post-claim-member-status-contract-plan.md
depends_on_shipments: []
dag_role: root
declared_surface_count: 4
requires_plan_hardening: true
hardening_rationale: "The unit's four declared surfaces span two template families, templates/policies/ and templates/agents/, plus their two installed mirrors. Stage's planning gate names multiple template families an elevated blast-radius signal, so the flag is declared true rather than argued down: the hardening content below is a gate, not a completeness note. It adds no new executable surface, runs no command and migrates no existing mutable record, which bounds the blast radius but does not remove the signal. The section carries H1-H11, H15-H16 and H17-H22, including the structural coverage questions whose absence let a plan invariant and its own manifest disagree, the composed-state vocabulary question whose absence let the plan and its only verdict-emitting task declare different tokens, the conformance question whose absence let this plan's rollout ordering contradict the binding decision that governs it without either document being wrong on its face, and - added at revision 6 - H21, which asks whether the gate-predicate principle is applied to every edge that crosses a three-token verdict rather than only to the one that guards a mutation, and H22, which asks whether an authorizing verdict is bound to the evidence identity it was computed from rather than only to its own token."
tags:
  - defect-unit
  - p002-7
  - member-status
  - reduced-scope
  - dag-root
---

# Canonical post-claim member-status contract (P-002.7)

## Why this unit is a root

Every other unit in this portfolio waits on a foundation because it needs an
executable boundary that does not yet exist. This one does not. It changes
**declarations** — a status vocabulary and the surfaces that state it — and
asserts their agreement with a conformance test.

Attempt 08, against the superseded revision-7 plan, recorded two P1 findings
and one P2. `B1` was a provenance defect: every executable record in the unit
cited source stash `3EF5AAF9`, an ID present in no stash file live or archived.
It is **closed** by the governing decision's F10 correction — `169-F`, `177-S`
and every `169.x` task record now cite `3EF5AAF2`, which is the real ID and the
one this plan carries throughout. `B2` was the evidence defect, and it is the
open finding this unit exists to close.

Making this unit a root matters: the architecture decision forbids false serial
dependencies among independent successors, and serializing it behind
`182-S` → `184-S` → `185-S` would be exactly that. `177-S` carries no
shipment-level dependency edge in either direction, which is the executable
form of that claim.

## The defect

Stash `3EF5AAF2`: when Ship claims a shipment, the member items' post-claim
status is stated differently on different surfaces. There is no canonical
vocabulary, so each surface asserts its own and the divergence is invisible
until a reconcile step reports an integrity error.

## The evidence defect (attempt-08 `B2`)

The superseded revision's assertions were **GREEN-only**: each was written to
observe the intended end state, and none was observed failing first. Attempt 08
named the specific assertions that entered that way — mirror-divergence
detection, attribution-paragraph presence, and the negative rows of the state
machine.

A GREEN-only assertion cannot distinguish "the contract holds" from "the
assertion does not test the contract". A test that passes before the change and
after it has measured nothing. That is not a stylistic preference about TDD —
it is the same `NO_OBSERVATION`-is-not-`PASS` rule the rest of this portfolio
enforces, applied to this unit's own evidence.

**Every assertion in this unit is observed failing against the current
divergent surfaces before it is observed passing, and every assertion belongs
to a RED task that records that failure individually.** No task after the RED
phase — not VERIFY, not ACTIVATE, not CONFIRM — introduces an assertion. The
three assertion families attempt 08 named are not exceptions to this rule; they
are the reason for it, and each has its own RED task below.

### The discriminating RED rule

An assertion that fails only because the clause text does not exist yet is weak
evidence: absence of a file fails everything, including an assertion that tests
nothing. Each RED task therefore records **two** observations per assertion:

1. **Absence RED** — the assertion executed against the current surfaces,
   failing individually, with its own declared marker in its own failure text.
   An aggregate non-zero suite exit is explicitly insufficient.
2. **Discriminating RED** — the same assertion executed against a synthetic
   near-miss fixture: a copy of the canonical definition mutated in exactly the
   way that assertion exists to catch — a mirror diverged by one word, an
   attribution paragraph removed, a fourth transition row added, a
   cross-reference made one-directional, a fifth surface introduced — and
   observed failing there too.

Observation 2 is what proves the assertion tests the contract rather than the
file's existence. An assertion with only observation 1 recorded has not
satisfied this unit's RED requirement.

**Import safety is binding** for every test module in this unit: it must import
cleanly under `unittest.defaultTestLoader` with zero `loader.errors` and zero
`_FailedTest` placeholders, asserted directly. Not-yet-existing text is read
**inside** the test body through a helper, never at module import time. A
module that raises on import produces a missing observation, not a red one.

## Contract

1. A canonical post-claim member-status vocabulary is defined **once**.
2. Every declared surface states it identically.
3. A conformance test enumerates the surfaces by rule and asserts agreement —
   so a surface added later fails the test rather than silently diverging.
4. The declared surface list is derived by the rule below, is enumerated in
   full, and its count is fixed at **4**.

## Declared surfaces

The rule, its scope, its exclusions and its result, in the shape the governing
decision's F7 uses for the review-verdict consumer inventory.

**Marker set.** A surface is a declaring surface if it carries, or must carry,
the clause anchor `P-002.7` together with either the canonical
post-claim member-status vocabulary block (its three claim-to-admission
transition rows and its observed-version attribution paragraph) or the
bidirectional cross-reference sentence that names the clause.

**Search scope.** Tracked files under `templates/policies/`,
`.github/policies/`, `templates/agents/`, `.github/agents/`.

**Exclusion rule.** Generated and untracked paths are excluded by rule, not by
oversight — specifically `.autoharness/staging/`, which `.gitignore:6` excludes
and which is a generated verify-workspace artifact rather than a mirror, and
`.autoharness/gates/`, which `.gitignore:7` excludes and which holds this
unit's two generated verdict artifacts. A verdict artifact is a *generated
observation about* the declared surfaces, never a declaring surface, so neither
gate artifact can ever be counted as a fifth surface. `docs/` is also outside
the scope: it narrates the contract and does not declare it.

**Result — exactly four surfaces, two authoritative/mirror pairs:**

```text
templates/policies/workflow-policies.md.tmpl   (authoritative)
.github/policies/workflow-policies.md          (installed mirror)
templates/agents/_ship.agent.md.tmpl           (authoritative)
.github/agents/_ship.agent.md                  (installed mirror)
```

**Current marker count: 0.** `P-002.7` appears in no file in the **search
scope** today. It does appear outside that scope — in this plan, its review
artifacts, the deliberation record, and the `169-F`, `177-S` and `169.x`
backlog records that govern the work — and none of those is a declaring
surface, because the search scope is `templates/policies/`,
`.github/policies/`, `templates/agents/` and `.github/agents/` and nothing
else. The load-bearing claim is the scoped one: **count 0 inside the search
scope.**

That zero does two things. It is what makes the absence RED observations real.
And it is the **inert precondition** the pre-activation gate re-checks: while
`resolved_surface_count` is 0, no declared surface has been mutated and the
candidate is still inert, so evidence gathered against it describes a state
that still exists. The count assertion is directional: the conformance test
asserts the marker resolves in **exactly these four paths and no others**, so
both a missed surface and an unlisted fifth surface fail the test rather than
being exempted.

## Gates and verdicts

This unit emits **two verdicts, in two phases, to two artifacts**, and they are
never conflated.

| | Pre-activation readiness | Post-activation confirmation |
|---|---|---|
| Owning task | `169.017-T` (VERIFY) | `169.016-T` (CONFIRM) |
| Runs | **before** the ACTIVATE commit | **after** the ACTIVATE commit |
| Observes | the **inert candidate** as test-owned data, with every declared surface unmutated | the **shipped text** on the installed surfaces |
| Artifact | `.autoharness/gates/p002-7-preactivation-readiness.txt` | `.autoharness/gates/p002-7-status-contract-verdict.txt` |
| Line prefix | `PREACTIVATION_STATE: ` | `COMPOSED_STATE: ` |
| Tokens | `PREACTIVATION_READY` / `PREACTIVATION_BLOCKED` / `PREACTIVATION_NOT_OBSERVED` | `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` / `STATUS_CONTRACT_NOT_OBSERVED` |
| Authorizing token | `PREACTIVATION_READY` | `STATUS_CONTRACT_HELD` |
| Authoritative consumer | `169.015-T` ACTIVATE | `169.007-T` DOCS |
| Consumer's gate predicate | *The activation authorization predicate* | *The documentation authorization predicate* |
| Freshness binding | `head_commit` + `candidate_digest` (`CCD/v1`, seven inputs) + `binding` (`B/v1`, tag `p002-7-preactivation-binding/v1`) | `head_commit` + `surface_digest` (`CCD/v1`, four inputs) + `binding` (`B/v1`, tag `p002-7-confirmation-binding/v1`) |
| Authorizes activation | **yes** — `PREACTIVATION_READY` only | **no, never** |
| Authorizes documentation | **no, never** | **yes** — `STATUS_CONTRACT_HELD` only |
| On failure | activation does not begin; **no declared surface is touched**; `169.015-T` exits non-zero | halt; `169.007-T`'s own fail-closed read is CLOSED so **no documentation file is touched and no commit is made**; revert the activation commit as a unit |

**The two vocabularies are disjoint and the two paths are distinct.** Neither
emitter reads, writes, amends or deletes the other's artifact, and a token from
one vocabulary is never valid in the other's file. `resolved_surface_count` is
`0` in the readiness line and `4` in the confirmation line because the two
steps observe two different phases; that is a property of the ordering, not a
discrepancy.

**Neither artifact is a declared surface.** Both live under
`.autoharness/gates/`, which is outside the surface-enumeration rule's search
scope and is gitignored at `.gitignore:7`, so `declared_surface_count` stays
fixed at **4** and no verdict is ever committed or left in a dirty tree.

**Both edges across a verdict are ordering; both tokens are authorization.**
There are exactly two dependency edges in this unit whose predecessor emits a
three-token verdict — `169.015-T ← 169.017-T` and `169.007-T ← 169.016-T` — and
both predecessors *complete* on all three of their tokens, two of which are
non-authorizing. The principle stated at `H18` therefore applies to **both**
edges identically, and each successor carries its own first-action fail-closed
read. Applying it to one edge and not the other is exactly the gap attempt 05
recorded as `N1`.

### Shared gate primitives

Both gates use the same three primitives, defined **once** here and
instantiated twice, so the two artifacts cannot drift into two different
freshness rules. Each carries an explicit version tag, because a change to
either rule changes every value that is emitted and every value that is
recomputed.

**Canonical content digest — `CCD/v1`.** Defined over an *ordered, fully
enumerated* list of repository-relative POSIX paths:

1. For each path, in list order, read the file's bytes. If the path does not
   exist, or exists but is unreadable, the digest is **undefined**: the
   emitting task resolves to its not-observed token, and a consumer resolves
   its gate **CLOSED**. An undefined digest is never rendered as a placeholder
   value and never omitted from an authorizing line.
2. Normalize each file's bytes by replacing every `CRLF` byte pair with a
   single `LF`. Nothing else is normalized — no trimming, no case folding, no
   encoding conversion, no whitespace collapsing, no reordering.
3. Compute `sha256` over the normalized bytes and render it **lowercase hex**.
4. Build the preimage as the concatenation, in list order, of
   `<path>` `LF` `<file-digest>` `LF` for every entry, encoded UTF-8, where
   `<path>` is the repository-relative path written with `/` separators.
5. The `CCD/v1` value is the lowercase-hex `sha256` of that preimage.

The `CRLF` normalization and the `/`-separated repository-relative paths are
what make the value **environment-agnostic**: the same tree yields the same
digest on a Windows checkout and on a POSIX one, under any working directory,
with no host, user, absolute path or clock input.

**Head identity.** `head_commit` is the full **40-character lowercase hex**
commit ID of `HEAD` at the instant the emitting task evaluates.
`head_committed_at` is that commit's committer timestamp normalized to UTC.
Both are read from the repository itself, never from an environment variable
and never from a file this unit writes.

**Freshness binding — `B/v1`.** The `binding=` value is the lowercase-hex
`sha256` of the UTF-8 encoding of a preimage of exactly five lines, each
terminated by a single `LF`, in exactly this order:

```text
<tag>
head_commit=<value>
content_digest=<value>
resolved_surface_count=<value>
checked=<value>
```

`<tag>` is `p002-7-preactivation-binding/v1` for the readiness artifact and
`p002-7-confirmation-binding/v1` for the confirmation artifact. The preimage
key is always the literal `content_digest=`, whichever field name the emitted
line uses for that value — `candidate_digest=` on readiness, `surface_digest=`
on confirmation. Each `<value>` is the field's value exactly as it appears on
the emitted line, byte for byte.

**`checked=` format.** `YYYY-MM-DDThh:mm:ssZ` — RFC 3339, UTC, seconds
precision, literal `Z`. Revision 5's date-only granularity was insufficient
once `checked=` became an ordered predicate rather than a display field,
because the freshness condition below compares it against a commit timestamp.

**The shared freshness predicate `F1`–`F5`.** A consumer's gate is OPEN only
if, **in addition** to that gate's own token and line-shape conditions, all
five of the following hold. Each is recomputed by the consumer against the
repository; none is taken on the line's own word.

* **`F1` head identity.** `head_commit=` is present exactly once, is 40
  lowercase hex, and is **equal** to the consumer's own reading of `HEAD` at
  the instant it evaluates.
* **`F2` content identity.** The gate's content-digest field is present exactly
  once, is 64 lowercase hex, and is **equal** to the consumer's own `CCD/v1`
  recomputation over that gate's declared input list.
* **`F3` phase identity.** `resolved_surface_count=` is present exactly once
  and equals that gate's phase-expected value — `0` for readiness, `4` for
  confirmation.
* **`F4` vintage ordering.** `checked=` is present exactly once, matches the
  literal RFC 3339 UTC form above, and is **not earlier than**
  `head_committed_at` for the commit named by `head_commit`.
* **`F5` binding integrity.** `binding=` is present exactly once, is 64
  lowercase hex, and is **equal** to the consumer's own `B/v1` recomputation
  from the line's own `head_commit`, content-digest, `resolved_surface_count`
  and `checked` values under that gate's tag.

Any `F1`–`F5` condition failing — including an absent field, a duplicated
field, a lexically malformed value, an unreadable digest input, or an
unresolvable `HEAD` — resolves the gate **CLOSED**. There is no partial
satisfaction and no warning state.

**`checked=` is now consumed, and `F4`/`F5` are what consume it.** `F5` makes a
`checked=` value that was altered after emission unable to reproduce the
`binding=` on its own line, and `F4` gives the field an ordering obligation
against a repository-derived timestamp. Revision 5 declared the field for a
stated safety purpose and then specified a consumer that never read it; that is
the gap attempt 05 recorded as `N2`.

**What this construction is, and what it is not.** It is a **staleness and
mistake-detection** contract. It closes the documented re-activation path,
where a reverted activation leaves the declared surfaces byte-identical to
their pre-activation state — so a content digest over surfaces alone would
still match — while `HEAD` has necessarily advanced to the revert commit, so
`F1` fails and `F4` fails with it. It is **not** a tamper-proof security
boundary: an actor who recomputes the binding can produce a self-consistent
forgery, and this unit claims no protection against that. No wall-clock
"not in the future" condition is imposed, deliberately: clock skew would make
it environment-dependent, and the freshness force is carried by repository
identity rather than by the consumer's clock.

**Why only the authorizing line carries the binding.** `head_commit`, the
content digest and `binding` appear on the **`PREACTIVATION_READY`** form and
the **`STATUS_CONTRACT_HELD`** form only. They are absent from the four
non-authorizing forms, and that asymmetry is recorded rather than an omission:
a not-observed verdict is reachable precisely when the inputs cannot be read,
so a digest over them is undefined by rule 1 above and could not be emitted
truthfully. A non-authorizing line is never consumed as an authorization, so it
has nothing to bind. `checked=` remains on all six forms, because a diagnostic
vintage is useful on every one.

### Pre-activation readiness gate

`169.017-T` is the sole emitter of the readiness verdict. It runs while every
declared surface is still unmutated, and it is the step decision `D2` calls
VERIFY: *"produce the complete evidence set before any activation … VERIFY
produces an evidence record; it changes no behaviour."*

| Field | Value |
|---|---|
| Ready state | `PREACTIVATION_READY` — all five families carry an absence RED, a discriminating RED and a **passing inert GREEN**; the enumeration rule resolves `declared_surface_count=4` with `resolved_surface_count=0`; no assertion exists that was not observed red first. Carries the `F1`–`F5` freshness binding. **The only token that authorizes activation** |
| Blocked state | `PREACTIVATION_BLOCKED` — the evidence set is complete in shape but at least one inert GREEN assertion **failed** against the candidate definition. The line names the family and the gap |
| Not-observed state | `PREACTIVATION_NOT_OBSERVED` — evaluated **first**; absorbs import failure, `loader.errors`, `_FailedTest` placeholders, zero executed assertions, any family missing any of its three observations, and a violated or unresolvable inert precondition. Never ready |
| Producer (observations) | `tests/test_p002_7_member_status_contract.py`, authored by the RED tasks against `169.011-T`'s inert candidate. The module produces the **observations**; `169.017-T` reads them and emits the **verdict line** — the module must not be able to declare its own gate result |
| Producer (verdict) | `169.017-T` — sole writer of the readiness artifact, sole emitter of the readiness line, sole computer of its `head_commit`, `candidate_digest` and `binding` |
| Freshness binding inputs | `CCD/v1` over the **seven** paths enumerated under *Readiness artifact and line format*; `B/v1` under tag `p002-7-preactivation-binding/v1` |
| Consumer (authoritative) | **`169.015-T`.** It reads the artifact as its **first action**, recomputes `F1`–`F5` against the repository, and fails closed. See *The activation authorization predicate* below |
| Exit code | `169.017-T` exits **zero only** on `PREACTIVATION_READY`; non-zero on `PREACTIVATION_BLOCKED` and `PREACTIVATION_NOT_OBSERVED` |
| **Not** a consumer | `.github/workflows/ci.yml`, for the same directional reason as the confirmation verdict below |

**The evidence set, and why it is complete before activation.** For each of the
five assertion families, `169.017-T` resolves three **per-assertion**
observations — never an aggregate:

1. **Absence RED** — the assertion observed failing individually against the
   current unmutated surfaces, with its own declared marker in its own failure
   text.
2. **Discriminating RED** — the same assertion observed failing against its
   named near-miss fixture, which is what proves it tests the *contract*
   rather than a file's existence.
3. **Inert GREEN** — the same assertion executed against `169.011-T`'s
   canonical candidate definition **as test-owned data** and observed
   **passing**. This is `D2`'s *"tests go RED first, then GREEN, entirely
   within the inert surface"*, and it is observable before any declared
   surface changes.

**`D2`'s compatibility limb is inapplicable, and that is recorded rather than
skipped.** `D2`'s third evidence category is *"compatibility evidence (every
pinned fixture from `D3` processed without error)"*. `D3`'s pinned corpus is
the manifest/normalizer corpus; this unit introduces **no normalizer** and
reads **no historical record corpus**, so the limb has no subject here. The
complete evidence set for this unit is therefore absence RED, discriminating
RED and inert GREEN, for all five families.

**The inert precondition.** `169.017-T` also resolves the surface-enumeration
rule and requires `resolved_surface_count = 0`. A non-zero count means a
declared surface has already been mutated, the candidate is no longer inert,
and the evidence set would describe a state that no longer exists; that
resolves to `PREACTIVATION_NOT_OBSERVED` with `reason=surface_not_inert`.

#### Readiness artifact and line format

**Destination — exactly one path.**
`.autoharness/gates/p002-7-preactivation-readiness.txt`

**Format — exactly one line, one of exactly three literal forms.**

```text
PREACTIVATION_STATE: PREACTIVATION_READY | families=5 | absence_red=5 | discriminating_red=5 | inert_green=5 | declared_surface_count=4 | resolved_surface_count=0 | head_commit=<40-hex> | candidate_digest=<64-hex> | checked=<YYYY-MM-DDThh:mm:ssZ> | binding=<64-hex>
PREACTIVATION_STATE: PREACTIVATION_BLOCKED | families=5 | failed=<n> | family=<A|B|C|D|E> | gap=<short-name> | checked=<YYYY-MM-DDThh:mm:ssZ>
PREACTIVATION_STATE: PREACTIVATION_NOT_OBSERVED | reason=<import_error|loader_errors|failed_test_placeholder|zero_assertions|absence_red_unrecorded|discriminating_red_unrecorded|inert_green_unrecorded|family_unrecorded|surface_not_inert|digest_input_unreadable> | checked=<YYYY-MM-DDThh:mm:ssZ>
```

The line begins with the literal prefix `PREACTIVATION_STATE: `, carries the
token as its first field, and separates fields with ` | `. `<n>` is a decimal
integer; `<short-name>` and the `reason=` values are from the closed
vocabularies shown. `<40-hex>` and `<64-hex>` are lowercase hexadecimal of
exactly 40 and exactly 64 characters. A `PREACTIVATION_BLOCKED` line naming
more than one family repeats the `family=` field once per family, still on the
one line. The `READY` form's field **order is fixed exactly as shown**, because
`B/v1` is computed from named values and a consumer parses by field name — the
fixed order is what lets a malformed line be recognised as malformed rather
than reinterpreted.

**The `candidate_digest` input list — `CCD/v1` over exactly these seven paths,
in exactly this order.** No glob, no directory walk, no discovery: the list is
enumerated so that both the emitter and the consumer compute over identical
input, and so that a reviewer can check it.

```text
templates/policies/workflow-policies.md.tmpl
.github/policies/workflow-policies.md
templates/agents/_ship.agent.md.tmpl
.github/agents/_ship.agent.md
tests/p002_7_candidate_definition.py
tests/p002_7_near_miss_fixtures.py
tests/test_p002_7_member_status_contract.py
```

The first four are the declared surfaces, in their enumerated order, observed
**unmutated**. The last three are the unit's test material authored in PREPARE
by `169.011-T`: the canonical candidate definition and enumeration rule, the
near-miss fixture set, and the conformance test module. They are in the list
because the readiness verdict is a statement *about evidence produced from that
material*; if the material changes between VERIFY and ACTIVATE, the adjudicated
evidence no longer describes what exists, and `F2` catches that even when no
commit was made. The two helper modules do not match `unittest discover`'s
default `test*.py` pattern, so naming them here adds no collected test module
and no assertion. None of the three is a declared surface — the enumeration
rule's search scope is `templates/policies/`, `.github/policies/`,
`templates/agents/` and `.github/agents/` — so `declared_surface_count` stays
fixed at **4**.

**`reason=digest_input_unreadable`** is the not-observed reason for rule 1 of
`CCD/v1`: one of the seven inputs is missing or unreadable, so the digest is
undefined and no `PREACTIVATION_READY` line can be emitted truthfully.

**Ownership and write behaviour — single writer, atomic, whole-file replace,
fresh binding on every run.** `169.017-T` is the **sole writer**. No other
task, and not the test module, writes this path. The write is **atomic**: the
line goes to a temporary file in the same directory and is renamed over the
destination, so a reader sees either the previous verdict or the new one and
never a partial line. Each run **replaces the whole file** — never appended to,
holding exactly one `PREACTIVATION_STATE:` line at all times. Because the whole
file is replaced and `head_commit`, `candidate_digest` and `checked` are all
recomputed from scratch on every run, **a re-run necessarily produces a fresh
`binding`**: there is no path by which a re-run preserves a previous run's
binding, and no path by which a previous run's binding survives alongside a new
verdict.

**Absence evaluation — fail closed, and absence is a *reading*, not an error.**
A consumer resolves the artifact to `PREACTIVATION_NOT_OBSERVED` if **any** of
the following holds: the file does not exist; it exists but is unreadable; it
is empty; it contains no line beginning `PREACTIVATION_STATE: `; it contains
**more than one** such line; or the token in the first field is not one of the
three declared.

**Freshness failures are gate failures, not artifact rewrites.** An `F1`–`F5`
failure resolves the **consumer's gate CLOSED**; it does not change the token
in the artifact and it does not authorize any consumer to rewrite, amend or
delete the artifact. The artifact is still owned solely by `169.017-T`, and the
only way to obtain a fresh binding is to re-run `169.017-T`.

**Exit code.** `169.017-T` exits **zero only** when the token it wrote is
`PREACTIVATION_READY`. The exit code and the artifact carry the same verdict by
construction, because one step produces both.

#### Readiness emission conditions

Evaluated in order; exactly one token is emitted. Each is decidable from the
suite's own output without judgement.

1. **`PREACTIVATION_NOT_OBSERVED`** — emitted if *any* of the following holds:
   the test module raised on import under `unittest.defaultTestLoader`;
   `loader.errors` is non-empty; any `_FailedTest` placeholder is present; zero
   assertions executed; any family has no per-assertion **absence RED** record;
   any family has no per-assertion **discriminating RED** record; any family
   has no per-assertion **inert GREEN** record; the inert precondition is
   violated or unresolvable; or any of the seven `candidate_digest` inputs is
   missing or unreadable, or `HEAD` is unresolvable, so the freshness binding
   cannot be computed (`reason=digest_input_unreadable`). Checked **first**,
   because a suite that did not run cannot be distinguished from a suite that
   passed by its exit code.
2. **`PREACTIVATION_BLOCKED`** — emitted if the module imported cleanly, all
   five families recorded both RED observations, and **at least one inert GREEN
   assertion failed** against the candidate definition.
3. **`PREACTIVATION_READY`** — emitted **only** if the module imported cleanly;
   all five families recorded an absence RED, a discriminating RED and a
   passing inert GREEN per assertion; the enumeration rule resolves
   `declared_surface_count=4` with `resolved_surface_count=0`; no assertion
   exists in the suite that was not observed red first; **and** `head_commit`,
   `candidate_digest` and `checked` were all computed successfully and the
   `binding` was derived from them under `B/v1`. The freshness fields are
   computed **last**, immediately before the atomic write, so the binding
   describes the tree state at the moment the verdict was emitted rather than
   at the moment evaluation began.

**Fail-closed.** Any state not affirmatively established by conditions 2 or 3
is `PREACTIVATION_NOT_OBSERVED`. No-observation is never ready.

#### The activation authorization predicate

**Activation depends on the verdict, not on task completion.** This is the
distinction attempt 03's `K1` forced on `177-F`'s `I1` gate, applied here.

A dependency edge clears on **predecessor completion**, and `169.017-T`
*completes* on all three of its tokens — two of which leave the unit unready.
So the edge from `169.015-T` to `169.017-T` supplies **ordering only**: it
guarantees the readiness artifact exists before it is read. The **token** is
the authorization.

`169.015-T`'s **first action**, before any declared surface is opened for
writing, is to read the readiness artifact and fail closed:

* **OPEN** — all of the following hold. **Line conditions:** the file exists,
  is readable, is not empty, its whole content is **exactly one line** (with at
  most one trailing newline and no other content), that line begins
  `PREACTIVATION_STATE: `, and the line's first field is the literal
  `PREACTIVATION_READY`. **Freshness conditions:** `F1`–`F5` of *Shared gate
  primitives*, recomputed by `169.015-T` against the repository, with the
  `candidate_digest` input list as enumerated above,
  `resolved_surface_count = 0`, and tag `p002-7-preactivation-binding/v1`.
* **CLOSED** — everything else: missing, unreadable, empty, more than one line
  of content, no `PREACTIVATION_STATE: ` line, more than one such line, an
  unrecognised token, `PREACTIVATION_BLOCKED`, `PREACTIVATION_NOT_OBSERVED`, or
  any `F1`–`F5` failure — a `head_commit` that is not the current `HEAD`, a
  `candidate_digest` that does not match recomputation, a
  `resolved_surface_count` other than `0`, a `checked=` that is absent,
  malformed or earlier than `head_committed_at`, a `binding=` that does not
  match recomputation, or any of those fields absent or duplicated.

**On a CLOSED gate, `169.015-T` touches no declared surface at all.** It makes
no commit, writes no clause text, writes to neither gate artifact, **exits
non-zero (exit code `1`)**, and the unit returns to Stage. `169.015-T` exits
zero only when the gate was OPEN *and* the single activation commit landed.
`169.015-T` never re-runs the suite, never re-derives or reinterprets the
evidence set, and never writes to either gate artifact.

**Recomputing an identity is not re-deriving evidence.** `F1`–`F5` compute
content and commit identities; they compute **no assertion outcome**, execute
no test, and read no assertion result. `169.015-T` still learns exactly one
thing about the evidence — the token `169.017-T` wrote — and the freshness
conditions only establish that the token still describes the tree in front of
it. `TRANSCRIPTION ONLY — NO AUTHORING` is untouched: the freshness read
authors nothing, narrows nothing, and adds no assertion.

**Why the stale-readiness path is now closed.** On the re-activation path this
plan itself defines — confirmation fails, the activation commit is reverted,
the unit returns to Stage — the four declared surfaces become byte-identical to
their pre-activation state, so the *content* limb alone would still match. `F1`
is what closes it: `git revert` necessarily creates a **new commit**, so `HEAD`
no longer equals the `head_commit` the stale line carries, and the gate is
CLOSED. `F4` closes it a second, independent way, because the stale `checked=`
now precedes the revert commit's timestamp. The remedy is the one six records
already mandate: **re-run `169.017-T`**, which replaces the whole artifact and
emits a fresh binding.

**This is deliberately strict, and the strictness is fail-closed by design.**
Any commit landing between VERIFY and ACTIVATE — even an unrelated one — closes
the gate, because the evidence was adjudicated against a tree that no longer
exists. That is the correct direction of error for a gate guarding an
irreversible four-surface mutation, and the remedy is cheap and already
required: re-run `169.017-T`.

### Post-activation confirmation

`169.016-T` runs **after** the single ACTIVATE commit. It resolves the unit to
exactly one of three states, and it is the sole emitter of that verdict line.

**It is not the evidence gate that authorized activation, and must never be
described as one.** That gate is `169.017-T`. What `169.016-T` adds is the one
thing no inert observation can supply: confirmation that the contract holds on
the **installed** surfaces, as **active** declarations.

| Field | Value |
|---|---|
| Pass state | `STATUS_CONTRACT_HELD` — the `P-002.7` block resolves in exactly the four enumerated paths, byte-identically within each authoritative/mirror pair; the attribution paragraph is present in both policy copies; the cross-reference resolves bidirectionally in both agent copies. Carries the `F1`–`F5` freshness binding. **The only token that authorizes documentation** |
| Fail state | `STATUS_CONTRACT_DIVERGENT` — emitted with the offending surface path and the specific divergence named |
| Not-observed state | `STATUS_CONTRACT_NOT_OBSERVED` — the test module failed to import, or no assertion executed. Distinct from `STATUS_CONTRACT_DIVERGENT` and never a pass |
| What it confirms | (1) **installed/template parity** — byte-identical `P-002.7` blocks for both pairs as shipped; (2) **active-consumer behaviour** — Ship's claim sequence at `.github/agents/_ship.agent.md` item 4 resolves the clause as a live declaration rather than inert fixture data, and the cross-reference resolves in both directions from the *installed* copies; (3) the five RED-proven families, per assertion, passing against the shipped text |
| Producer (observations) | `tests/test_p002_7_member_status_contract.py` — created in `177-S` by `169.009-T` and extended by `169.010-T`, `169.012-T`, `169.013-T` and `169.014-T`. The module produces the **observations**; `169.016-T` reads them and emits the single **verdict line**. Those are two artifacts with two roles, and the split is deliberate: the module must not be able to declare its own gate result |
| Producer (verdict) | `169.016-T` — the sole writer of the verdict artifact named below, the sole emitter of the verdict line, and the sole computer of its `head_commit`, `surface_digest` and `binding` |
| Freshness binding inputs | `CCD/v1` over the **four** declared surfaces, in their enumerated order; `B/v1` under tag `p002-7-confirmation-binding/v1` |
| Verdict artifact | `.autoharness/gates/p002-7-status-contract-verdict.txt` — exactly one line, written atomically by `169.016-T`. See *Confirmation artifact and line format* below |
| Consumer (emitter's own gate) | **`169.016-T`'s own invocation.** It runs the suite, evaluates the emission conditions, writes the verdict artifact, and **exits non-zero unless the token is `STATUS_CONTRACT_HELD`**. This exit code triggers the rollback path; it does not authorize activation, which has already happened |
| Consumer (authoritative, documentation) | **`169.007-T`.** It reads the artifact as its **first action**, recomputes `F1`–`F5` against the repository, and fails closed. See *The documentation authorization predicate* below. This is the second half of `H18`'s principle, applied to the second edge that crosses a three-token verdict |
| Consumer (contract text, not verdict line) | Ship's claim sequence at `.github/agents/_ship.agent.md` item 4, "Claim the shipment via `backlogit_claim_shipment`", with its authoritative template `templates/agents/_ship.agent.md.tmpl`. Ship reads the **`P-002.7` clause** that `169.015-T` writes into that declared surface. It does not read either verdict line, and it is not a gate consumer |
| **Not** a consumer | `.github/workflows/ci.yml`. Its `test` job runs `PYTHONPATH=src python -m unittest discover -s tests` and consumes an **exit code**; the suite *produces* the observations both verdict lines are derived *from*. The direction is the reverse of a verdict-line consumer. **No task in `177-S` modifies `ci.yml`**, and this unit adds no CI gate |
| Activation commit | `169.015-T` — one task, one commit, all four enumerated surfaces, authorized by `169.017-T`'s verdict |

#### Confirmation artifact and line format

An observation with no destination is not an observation (Principle V). The
destination and the literal line form are therefore declared here rather than
left to the emitting task to invent.

**Destination — exactly one path.**
`.autoharness/gates/p002-7-status-contract-verdict.txt`

`.autoharness/gates/` is **gitignored** (`.gitignore:7`), which is deliberate:
the verdict is a *generated observation about* the tracked surfaces, not a
tracked surface itself. It is never committed, never appears in a diff, and
**cannot leave the working tree dirty** after `169.016-T` runs. `169.007-T`
documents the artifact; it does not commit one. This is the **second** of the
unit's two gate artifacts; the first is the readiness artifact above, and the
two are never conflated.

**Format — exactly one line, one of exactly three literal forms.**

```text
COMPOSED_STATE: STATUS_CONTRACT_HELD | families=5 | assertions_passed=<n> | declared_surface_count=4 | resolved_surface_count=4 | head_commit=<40-hex> | surface_digest=<64-hex> | checked=<YYYY-MM-DDThh:mm:ssZ> | binding=<64-hex>
COMPOSED_STATE: STATUS_CONTRACT_DIVERGENT | families=5 | failed=<n> | surface=<declared-surface-path> | divergence=<short-name> | checked=<YYYY-MM-DDThh:mm:ssZ>
COMPOSED_STATE: STATUS_CONTRACT_NOT_OBSERVED | reason=<import_error|loader_errors|failed_test_placeholder|zero_assertions|family_unrecorded|digest_input_unreadable> | checked=<YYYY-MM-DDThh:mm:ssZ>
```

The line begins with the literal prefix `COMPOSED_STATE: `, carries the token
as its first field, and separates fields with ` | `. `<n>` is a decimal
integer; `<declared-surface-path>` is one of the four enumerated surface paths;
`<short-name>` and the `reason=` values are from the closed vocabularies shown;
`<40-hex>` and `<64-hex>` are lowercase hexadecimal of exactly 40 and exactly
64 characters. A `STATUS_CONTRACT_DIVERGENT` line naming more than one
offending surface repeats the `surface=` field once per surface, still on the
one line. The `HELD` form's field **order is fixed exactly as shown**, for the
same reason the `READY` form's is.

**The `surface_digest` input list — `CCD/v1` over exactly these four paths, in
exactly this order**, which is the declared-surface enumeration order:

```text
templates/policies/workflow-policies.md.tmpl
.github/policies/workflow-policies.md
templates/agents/_ship.agent.md.tmpl
.github/agents/_ship.agent.md
```

**Why this list is the four surfaces only, and not the readiness seven.** The
two digests have different subjects because the two gates observe different
things. The readiness digest covers the test material because the readiness
verdict is a statement about evidence produced from it. The confirmation digest
covers the declared surfaces alone because `169.016-T`'s subject is the
**shipped text** and `169.007-T` documents **activated behaviour**; the test
material is neither shipped nor documented as activated, and binding the
documentation gate to it would close the gate on a test-only edit that changes
nothing DOCS describes. The asymmetry is deliberate and recorded, not an
oversight.

**`reason=digest_input_unreadable`** is the not-observed reason for rule 1 of
`CCD/v1`: one of the four surfaces is missing or unreadable, so the digest is
undefined and no `STATUS_CONTRACT_HELD` line can be emitted truthfully.

**Ownership and write behaviour — single writer, atomic, whole-file replace,
fresh binding on every run.** `169.016-T` is the **sole writer**. No other
task, and not the test module, writes this path. The write is **atomic**: the
line is written to a temporary file in the same directory and then renamed over
the destination, so a reader sees either the previous verdict or the new one
and never a partial line. Each run **replaces the whole file** — the artifact
is never appended to, and it holds exactly one `COMPOSED_STATE:` line at all
times. A pre-existing file from an earlier run is overwritten, not merged.
Because the whole file is replaced and `head_commit`, `surface_digest` and
`checked` are recomputed from scratch on every run, **a re-run necessarily
produces a fresh `binding`**, and no previous run's binding can survive
alongside a new verdict.

**Absence evaluation — fail closed, and absence is a *reading*, not an error.**
A consumer resolves the artifact to `STATUS_CONTRACT_NOT_OBSERVED` if **any**
of the following holds: the file does not exist; it exists but is unreadable;
it is empty; it contains no line beginning `COMPOSED_STATE: `; it contains
**more than one** such line; or the token in the first field is not one of the
three declared above. This is the same fail-closed rule the emission conditions
apply, reapplied at the read boundary, and it is what makes the plan's own
statement — that an **absent** verdict line is itself
`STATUS_CONTRACT_NOT_OBSERVED` (`R8`, `H11`) — decidable rather than
ambiguous. Before this destination was named, a reader could not distinguish
*absent* from *present somewhere else*, and the gate was unevaluable as
written.

**Freshness failures are gate failures, not artifact rewrites.** An `F1`–`F5`
failure resolves the **consumer's gate CLOSED**; it does not change the token
in the artifact and it does not authorize `169.007-T` to rewrite, amend or
delete it. The artifact stays owned solely by `169.016-T`, and the only way to
obtain a fresh binding is to re-run `169.016-T`.

**Exit code — the in-unit confirmation gate.** `169.016-T` exits **zero only**
when the token it wrote is `STATUS_CONTRACT_HELD`, and non-zero for
`STATUS_CONTRACT_DIVERGENT` and `STATUS_CONTRACT_NOT_OBSERVED`. The exit code
and the artifact carry the same verdict by construction, because one step
produces both. This is what keeps the unit **self-contained**: both verdicts
are evaluable from their own emitting tasks' invocations alone, with no CI
change, no new workflow and no task outside `177-S`. Note what this exit code
does *not* do — it does not authorize activation, which has already happened by
the time it is computed.

**And note what it is not asked to do alone.** The exit code is one of **two
independent** enforcement mechanisms on the CONFIRM → DOCS edge, and it is the
weaker of the two: it depends on the invoking process observing and honouring
it. The stronger mechanism is `169.007-T`'s own first-action fail-closed read
of the artifact, specified below, which does not depend on any process having
observed `169.016-T`'s exit at all. Through revision 5 only the weaker
mechanism plus a `blocks` edge existed, which is the gap attempt 05 recorded as
`N1`. On a non-zero result the exit code also triggers the rollback path below.

#### Confirmation emission conditions

`169.016-T` evaluates these in order and emits exactly one token. They are
objective: each is decidable from the suite's own output without judgement.


1. **`STATUS_CONTRACT_NOT_OBSERVED`** — emitted if *any* of the following
   holds: the test module raised on import under
   `unittest.defaultTestLoader`; `loader.errors` is non-empty; any
   `_FailedTest` placeholder is present; zero assertions executed; any one
   of the five RED-proven assertion families has no per-assertion executed
   result recorded; or any of the four `surface_digest` inputs is missing or
   unreadable, or `HEAD` is unresolvable, so the freshness binding cannot be
   computed (`reason=digest_input_unreadable`). This is checked **first**,
   because a suite that did not run cannot be distinguished from a suite that
   passed by looking at its exit code.
2. **`STATUS_CONTRACT_DIVERGENT`** — emitted if the module imported cleanly,
   every family executed, and **at least one executed assertion failed**. The
   line names the offending surface path and the specific divergence.
3. **`STATUS_CONTRACT_HELD`** — emitted only if the module imported cleanly,
   all five families executed with a per-assertion passing result recorded,
   installed/template parity holds for **both** pairs, the surface-enumeration
   rule resolves to exactly `declared_surface_count`, no assertion exists
   in the suite that was not observed red first, **and** `head_commit`,
   `surface_digest` and `checked` were all computed successfully and the
   `binding` was derived from them under `B/v1`. The freshness fields are
   computed **last**, immediately before the atomic write.

**No-observation cannot be mistaken for a pass, and the mistake is blocked in
three places.** The not-observed condition is evaluated before the other two,
so it cannot be reached past them. A green aggregate exit code with no
per-assertion record is `STATUS_CONTRACT_NOT_OBSERVED`, not
`STATUS_CONTRACT_HELD` — the aggregate demonstrates that nothing failed, which
is a weaker claim than that each assertion passed. And an **absent** verdict
line is itself `STATUS_CONTRACT_NOT_OBSERVED`: a consumer that finds no token
at `.autoharness/gates/p002-7-status-contract-verdict.txt` has observed nothing
and must treat it as such, never as a default pass. *Confirmation artifact and
line format* above states exactly which read outcomes count as absent.

**Fail-closed.** Any state not affirmatively established by conditions 2 or 3
is `STATUS_CONTRACT_NOT_OBSERVED`. This is the portfolio-wide
`NO_OBSERVATION`-is-not-`PASS` rule (decision D6), applied to this unit's own
gate output.

`STATUS_CONTRACT_HELD` is reachable once the single ACTIVATE commit lands, and
not before — it is a statement about the *activated* surfaces.
`STATUS_CONTRACT_DIVERGENT` is reachable **today**, at marker count 0, which is
what makes the absence RED observations possible and the assertions meaningful.

#### The documentation authorization predicate

**Documentation depends on the verdict, not on task completion.** This is
`H18`'s principle applied to the unit's *second* verdict edge, in exactly the
shape `169.015-T` already uses for the first. Through revision 5 it was applied
only to the ACTIVATE edge; attempt 05 recorded that omission as `N1`.

A dependency edge clears on **predecessor completion**, and `169.016-T`
*completes* on all three of its tokens — two of which are failures. So the edge
from `169.007-T` to `169.016-T` supplies **ordering only**: it guarantees the
confirmation artifact exists before it is read. The **token** is the
authorization.

`169.007-T`'s **first action**, before any documentation file is opened for
writing, is to read `.autoharness/gates/p002-7-status-contract-verdict.txt` and
fail closed:

* **OPEN** — all of the following hold. **Whole-file condition:** the file
  exists, is readable, is not empty, and its **entire content** is exactly one
  line — that is, after stripping at most one trailing newline there is exactly
  one line and no other content, blank or otherwise. **Line conditions:** that
  line begins with the literal prefix `COMPOSED_STATE: `, and its first field
  is the literal token `STATUS_CONTRACT_HELD` — compared as an exact,
  case-sensitive byte-for-byte match against that literal, with no prefix
  match, no substring match, no normalization and no default. **Freshness
  conditions:** `F1`–`F5` of *Shared gate primitives*, recomputed by
  `169.007-T` against the repository, with the `surface_digest` input list as
  enumerated above, `resolved_surface_count = 4`, and tag
  `p002-7-confirmation-binding/v1`.
* **CLOSED — everything else**, enumerated so that absence, malformation,
  staleness and failure are each a *reading* rather than an error:
  * **Absence** — the file does not exist; it exists but is unreadable; it is
    empty.
  * **Malformation** — the content is more than one line; there is no line
    beginning `COMPOSED_STATE: `; there is more than one such line; the first
    field is not one of the three declared tokens; a required field of the
    `HELD` form is absent, duplicated, or lexically malformed.
  * **Staleness** — any `F1`–`F5` failure: a `head_commit` that is not the
    current `HEAD` (which is what a reverted activation always produces), a
    `surface_digest` that does not match recomputation over the four declared
    surfaces, a `resolved_surface_count` other than `4`, a `checked=` that is
    absent, malformed or earlier than `head_committed_at`, or a `binding=` that
    does not match recomputation.
  * **Failure** — the token is the literal `STATUS_CONTRACT_DIVERGENT` or the
    literal `STATUS_CONTRACT_NOT_OBSERVED`.
  * **Foreign vocabulary** — a `PREACTIVATION_*` token, or a
    `PREACTIVATION_STATE: ` prefix, appearing in this file. The two
    vocabularies are disjoint, so a readiness token can never open the
    documentation gate.

**On a CLOSED gate, `169.007-T` touches no documentation at all.** It creates,
modifies and deletes **no file under `docs/`** and **no other file**, makes
**no commit**, writes to **neither gate artifact**, **exits non-zero (exit code
`1`)**, and the unit returns to Stage. `169.007-T` exits zero only when the
gate was OPEN *and* its documentation commit landed. The rule the plan already
stated in four places — *DOCS does not proceed* — is now enforced by the
executing task's own read rather than only by prose, an edge and an exit code
the reader must have observed.

**`169.007-T` produces no evidence and reinterprets none.** It does not run the
suite, does not re-derive the evidence set, does not re-observe any assertion,
does not write to either gate artifact, and never reinterprets a CLOSED gate as
open. Recomputing `F1`–`F5` computes identities, not assertion outcomes — the
same distinction that keeps `169.015-T` transcription-only.

**Why the stale-confirmation path is closed.** On the failure path below the
activation commit is reverted, which necessarily creates a new commit; a
confirmation line left over from before the revert fails `F1` on `head_commit`
and `F4` on `checked=`, and its `surface_digest` no longer matches the reverted
surfaces either. A `STATUS_CONTRACT_HELD` line from a superseded run therefore
cannot authorize a documentation commit describing behaviour that is no longer
installed.

#### Failure path — rollback and halt

**A non-pass confirmation is not a finding to be argued down; it has one path,
stated in advance.** On `STATUS_CONTRACT_DIVERGENT` or
`STATUS_CONTRACT_NOT_OBSERVED`:

1. `169.016-T` **exits non-zero** and the unit **halts**.
2. **`169.007-T` DOCS does not proceed, and that is mechanical.** `169.007-T`'s
   own first action is the fail-closed whole-file read specified under *The
   documentation authorization predicate*: the token is not the literal
   `STATUS_CONTRACT_HELD`, so the gate is CLOSED, and it touches no
   documentation file, makes no commit and exits non-zero (`1`). The halt does
   not depend on any process having observed `169.016-T`'s exit code, nor on
   the `blocks` edge, nor on prose. Documentation follows *confirmed*
   behaviour, never asserted behaviour.
3. The single `169.015-T` activation commit is **reverted as a unit** with
   `git revert`, returning all four declared surfaces to their pre-activation
   divergent state **simultaneously**. That guarantee holds *only* because
   activation is one commit; across two commits joined by an edge, reverting
   the second would leave the workspace in the split state rather than the
   original one.
4. The unit **returns to Stage**.

**The revert closes both gates behind it, mechanically.** `git revert` creates
a new commit, so `HEAD` advances. Any readiness line and any confirmation line
written before the revert now fail `F1` on `head_commit` and `F4` on `checked=`
against that new `HEAD`. Neither a stale `PREACTIVATION_READY` nor a stale
`STATUS_CONTRACT_HELD` can authorize anything after the revert, and neither
consumer needs to be told the revert happened in order to refuse.

`169.016-T` never repairs a declared surface in place, never amends or re-runs
the activation commit, and never adds, weakens or re-scopes an assertion to
reach `STATUS_CONTRACT_HELD`. A divergence discovered here returns to a **RED
task** for re-observation, and the unit **re-runs `169.017-T`** for a fresh
`PREACTIVATION_READY` verdict before any re-activation. A stale readiness
verdict never authorizes a second activation — and since revision 6 that is
enforced by `169.015-T`'s own `F1`–`F5` recomputation, not only mandated in
prose.

## Rollout

**The order is PREPARE → RED → VERIFY → ACTIVATE → CONFIRM → DOCS, and it
conforms to the binding rollout invariant.** Decision `D2` states that every
contract in this portfolio rolls out `PREPARE → VERIFY → ACTIVATE`, with the
complete evidence set produced **before any activation**. This unit's phases
map onto that invariant as follows, and the mapping is recorded here rather
than left implicit:

| This plan's phase | `D2` phase | Why |
|---|---|---|
| PREPARE | `D2` PREPARE | Authors the candidate inert; live behaviour byte-identical before and after |
| RED | `D2` PREPARE | `D2`'s PREPARE is explicit that *"tests go RED first, then GREEN, entirely within the inert surface"*, so RED sits inside PREPARE rather than beside it |
| VERIFY | `D2` VERIFY | Produces the complete evidence set before any activation and changes no behaviour — `169.017-T` |
| ACTIVATE | `D2` ACTIVATE | One task, one commit, every surface flipped together — `169.015-T` |
| CONFIRM | *(post-activation)* | `D2` defines three phases up to activation and neither names nor forbids what follows. Confirmation observes the activated state; it cannot precede activation |
| DOCS | *(post-activation)* | Documentation follows confirmed behaviour, and the dependency is a **verdict**, not a completion edge — `169.007-T` reads the confirmation artifact fail-closed as its first action |

**`D2`'s compatibility limb is inapplicable here, and that is recorded, not
skipped.** `D2` names three evidence categories for VERIFY: RED, GREEN, and
compatibility against the `D3` pinned-fixture corpus. `D3`'s corpus is the
manifest/normalizer corpus; this unit introduces no normalizer and reads no
historical record corpus, so the third limb has no subject. This unit's
complete evidence set is absence RED, discriminating RED and inert GREEN.

**PREPARE (inert).** The canonical vocabulary definition and the conformance
test are authored as test-owned data and test code. No declared surface
changes, no policy clause references the definition, and the workspace's live
behaviour is byte-identical before and after. This is the only phase in which
the clause text is authored; ACTIVATE transcribes it and writes none.

**RED.** Every assertion is observed failing individually against the current
surfaces, and discriminatingly against a near-miss fixture, before any
production text exists. Five RED tasks, one per assertion family.

**VERIFY (inert, pre-activation).** `169.017-T` evaluates the complete evidence
set — absence RED, discriminating RED and **inert GREEN** — for all five
families against `169.011-T`'s candidate definition, while every declared
surface is still unmutated, and re-checks the inert precondition
(`resolved_surface_count = 0`). It adds no assertion and changes no behaviour.
It emits the **pre-activation readiness verdict**, and `PREACTIVATION_READY` is
the only token that authorizes the next phase.

**ACTIVATE.** One task, one commit updating every declared surface — both
authoritative templates and both installed mirrors, together. Splitting them
produces a reachable state in which a mirror states a vocabulary its template
does not, which is the divergence this unit exists to remove. A dependency edge
between two activation tasks does not prevent that state; it permits it, which
is why there is one task and not two joined by an edge.

**Its first action is to read the readiness verdict and fail closed.** The edge
supplies ordering; the token supplies authorization. The read is a whole-file
token comparison **plus** the `F1`–`F5` freshness recomputation, so a readiness
verdict that no longer describes the tree in front of the task is CLOSED even
though its token still says `PREACTIVATION_READY`. On a CLOSED gate no declared
surface is touched at all and the task exits `1`. ACTIVATE transcribes only: it
adds no assertion, narrows no scope, and **reinterprets no evidence** — it
never re-runs the suite, re-derives the evidence set, or re-reads a CLOSED gate
as open. Recomputing a content and commit identity is not re-deriving evidence:
it produces no assertion outcome.

**CONFIRM (post-activation).** `169.016-T` observes the same assertions,
unchanged and unextended, passing against the **shipped** text, and confirms
the two things no inert observation can establish: installed/template parity
across both pairs, and active-consumer behaviour at Ship's claim sequence. A
new assertion appearing here is a defect rather than an improvement, and is
returned to a RED task. **This step is not the evidence gate that authorized
activation**; its failure path is halt, DOCS does not proceed, and revert the
single activation commit as a unit.

**DOCS.** Documents the contract, both verdicts and their non-conflation, and
the explicitly-undelivered downstream detection. **Its first action is to read
the confirmation verdict and fail closed**, in the same shape ACTIVATE uses:
whole-file token comparison against the literal `STATUS_CONTRACT_HELD`, plus
the `F1`–`F5` freshness recomputation. On a CLOSED gate it touches no
documentation, makes no commit and exits `1`. Here too the edge supplies
ordering and the token supplies authorization.

### The 2-hour check on ACTIVATE

ACTIVATE is the widest task in the unit by construction, so the check is
recorded rather than assumed.

Its content is **transcription, not authoring**: the exact clause block, the
attribution paragraph and the cross-reference sentence are frozen in PREPARE
and are inserted verbatim into four files across two document pairs. No design
decision is taken during ACTIVATE, and no evidence is re-derived — the gate
read that opens the task parses one line and recomputes `F1`–`F5`, which is a
bounded, fully-specified sequence of file reads and two `git` queries with no
judgement in it. Sized `M` (several files) at complexity `medium` (mechanical
transcription, plus one correctness-critical predicate), it fits inside two
hours.

**`169.015-T` has exactly two independent halt triggers, and both end with zero
declared surfaces touched.** The first is a CLOSED readiness gate — any token
other than `PREACTIVATION_READY`, an absent or malformed readiness artifact, or
any `F1`–`F5` freshness failure — which halts the task before its first write
with exit code `1`. The second is the two-hour overrun below. Neither is
reducible to the other: a gate can be OPEN on a task that still overruns, and a
task well inside two hours still cannot proceed on a CLOSED gate.


**If it does not fit, the unit halts and returns to Stage. Ship neither narrows
nor splits.** This is the contingency, stated in advance so it is not invented
under pressure:

1. `169.015-T` **stops**. It does not split the commit — splitting is
   prohibited under every circumstance, because a commit boundary mid-migration
   is a reachable state in which a mirror states a vocabulary its template does
   not.
2. It also does not narrow in place. Narrowing the declared surface list
   changes which assertions the contract needs, and **re-deriving an assertion
   is authoring one** — which ACTIVATE's own `TRANSCRIPTION ONLY - NO
   AUTHORING` invariant forbids, and which would put a never-red assertion into
   the suite after the production text exists. That is precisely the
   attempt-08 `B2` shape this unit was re-authored to eliminate.
3. The shipment returns to **Stage** for explicit scope redesign. Stage decides
   whether to reduce `declared_surface_count`, and if it does, it re-plans the
   consequences as ordinary work: retiring `169.010-T`'s bidirectional family
   and its fixture outright (dropping the Ship-agent pair removes the reverse
   half of the cross-reference from every declared surface, so that family does
   not narrow — it disappears), and re-observing `169.014-T`'s closure
   assertion **red** against the new expectation before any activation resumes.
4. `169.017-T` is **re-run** against the redesigned contract, and only a fresh
   `PREACTIVATION_READY` verdict authorizes a revised ACTIVATE — against a
   contract whose every assertion has again been proven red first. The stale
   readiness verdict from before the redesign never carries over.

This is the governing decision's `R5` applied to its purpose rather than to its
letter: a contract touching too many surfaces to activate in one task is too
large a contract, and resizing a contract is a **planning** act, not something
Ship performs mid-task. The machinery already exists in the unit — `169.016-T`
establishes that a gap discovered late "returns to a RED task rather than being
closed in place", and this rule points `R5` at that same machinery.

## Tasks

| ID | Task | Phase | Size | Complexity |
|---|---|---|---|---|
| `169.011-T` | Author the canonical vocabulary definition, the attribution paragraph, the cross-reference sentence, the surface-enumeration rule and the near-miss fixtures as inert test-owned data at two named helper paths | PREPARE | S | medium |
| `169.009-T` | Three claim-to-admission transition-state assertions, each observed failing individually and discriminatingly | RED | S | low |
| `169.010-T` | Bidirectional wiring and cross-reference assertions, each observed failing individually and discriminatingly in both copies | RED | S | low |
| `169.012-T` | Mirror-divergence assertions for both authoritative/mirror pairs, each observed failing individually and discriminatingly | RED | S | low |
| `169.013-T` | Observed-version attribution-paragraph assertions, each observed failing individually and discriminatingly | RED | XS | low |
| `169.014-T` | Negative-row and exactly-four-surface closure assertions, each observed failing individually and discriminatingly | RED | S | medium |
| `169.017-T` | Evaluate the complete inert evidence set for all five families and emit the freshness-bound pre-activation readiness verdict that authorizes activation | VERIFY | S | medium |
| `169.015-T` | One commit across all four enumerated surfaces: clause, attribution paragraph and bidirectional cross-reference, opened by a fail-closed freshness-bound read of the readiness verdict | ACTIVATE | M | medium |
| `169.016-T` | Confirm installed/template parity and active-consumer behaviour against the shipped text and emit the freshness-bound post-activation status-contract verdict; add no assertion | CONFIRM | S | medium |
| `169.007-T` | Document the contract, both verdicts and their non-conflation, and the explicitly-undelivered downstream detection, opened by a fail-closed freshness-bound read of the confirmation verdict | DOCS | S | medium |

**Sequence.** `169.011-T` → all five RED tasks (independent of one another, any
order) → `169.017-T` → `169.015-T` → `169.016-T` → `169.007-T`.

`169.017-T` is the **sole immediate predecessor** of `169.015-T`. The five RED
tasks reach activation only through it, so there is no path by which activation
becomes ready without the readiness verdict having been computed.

**`item_deps` direction, and what each edge does and does not prove.** The live
edges run successor → predecessor: each RED task depends on `169.011-T`;
`169.017-T` depends on all five RED tasks; `169.015-T` depends on `169.017-T`
**alone**; `169.016-T` depends on `169.015-T`; and `169.007-T` depends on
`169.016-T`. Thirteen edges, one topology, no cycle, and `177-S` has no
successor shipment.

Exactly **two** of those thirteen edges cross a three-token verdict:
`169.015-T ← 169.017-T` and `169.007-T ← 169.016-T`. Both predecessors
*complete* on all three of their tokens, two of which are non-authorizing, so
**neither edge is a safety predicate** — each supplies ordering only,
guaranteeing that its verdict artifact exists before it is read. On both edges
the **token plus its `F1`–`F5` freshness binding** is the authorization, read
first-action and fail-closed by the successor itself. The two edges are now
treated identically; through revision 5 only the first was, which is the gap
attempt 05 recorded as `N1`.

The remaining eleven edges cross no verdict: they order authoring before
observation and observation before adjudication, and nothing downstream reads
them as permission.

Ten tasks, none exceeding two hours on either axis. The widest is `M`/`medium`,
justified above; every other task is `S` or `XS`, and no task is `high` on
complexity.

**Sizing re-assessment at revision 6, stated rather than assumed.** Four
records gained work in this cycle, and one rule governs all four: **a record's
`complexity` reflects its highest-uncertainty component, not its bulkiest
one.** Each of the four now owns a correctness-critical predicate — emitting or
recomputing `CCD/v1`, the head identity pair and `B/v1` — whose specification
is complete in *Shared gate primitives* but whose implementation must be exact,
because an off-by-one in a canonicalization rule silently produces a digest
that never matches. So all four move `low` → `medium` while their **sizes are
unchanged**: `169.017-T` `S`, `169.015-T` `M`, `169.016-T` `S`, `169.007-T`
`S`. Volume did not change — the same files are read and the same line is
written or the same documentation authored — so moving `size` would be an
untruthful estimate. All four remain comfortably inside two hours; none is
`high`, so none requires a split or a de-risking step. `169.011-T` keeps
`S`/`medium`: naming two helper paths it was already going to author is a
naming change, not new work. The five RED tasks and their sizes are untouched,
because their responsibilities are untouched.


## Assertion-to-task map

Every assertion in this unit has exactly one RED task. A family absent from
this table has no assertion; an assertion absent from a RED task is a defect.

| Assertion family | RED task | Near-miss fixture that discriminates it |
|---|---|---|
| The three claim-to-admission transition rows | `169.009-T` | A definition with one row's target status altered |
| Bidirectional cross-reference resolves in both copies | `169.010-T` | A definition whose cross-reference names only one direction |
| Template and installed mirror are identical in the `P-002.7` block | `169.012-T` | A mirror diverged from its template by one word |
| Observed-version attribution paragraph is present | `169.013-T` | A definition with the attribution paragraph removed |
| The clause admits exactly three rows and no others; the marker resolves in exactly four surfaces | `169.014-T` | A definition with a fourth transition row added, and a fifth declaring surface introduced |

Neither `169.017-T` nor `169.016-T` introduces an assertion. `169.017-T`
**evaluates** the five families' existing evidence inertly and writes a
verdict; `169.016-T` **observes** the same five families passing against the
shipped text and writes a verdict. Both are prohibited from adding, widening or
re-scoping an assertion, and so are `169.015-T` and `169.007-T`. The GREEN
phase implements only behaviour that was proven red.

**No gate predicate is an assertion.** The `F1`–`F5` freshness conditions that
`169.015-T` and `169.007-T` recompute are **identity checks over file content
and commit IDs**. They execute no test, produce no assertion outcome, and
appear in no assertion family, so they are outside this map by construction and
introduce nothing that must be observed red first. Adding one to the
conformance suite would be a defect; they are gate-read logic in the consuming
tasks, not test code.

## Out of scope

* Any change to the claim mechanism itself.
* Shipment reconcile classification logic.
* The status-transition table. This unit canonicalizes what member status *is*
  after a claim, not which transitions are legal.
* The verify-workspace token implementation and its negative-case suite, which
  belong to the deferred typed-policy-representation entry `E770139B`. The
  documentation task states this plainly rather than implying the detection
  exists.

## Note on an adjacent observation

During this portfolio's research, `backlogit` was observed to reject
`queued → abandoned` and `blocked → abandoned` via its
`validate_status_transition` pre-hook, leaving `abandoned` apparently reachable
only through `active`. That is a transition-table observation about the backlog
tool, **not** a post-claim member-status defect, and it is recorded here only
so it is not lost. It is explicitly **not** in this unit's scope.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The surface list is incomplete | It is derived by the stated rule, enumerated in full above, and asserted at a fixed count of **4** by `169.014-T`, so an unlisted surface fails the test rather than being exempted. |
| R2 | RED observation is claimed rather than recorded | Each assertion's failing observation is recorded individually; an aggregate suite exit code is explicitly insufficient evidence, and every RED task names the assertions it covers. |
| R3 | An assertion fails only because the clause is absent, and would pass against a wrong clause | The discriminating RED rule requires each assertion to be observed failing against a near-miss fixture as well as against absence. The Assertion-to-task map names the fixture for each family. |
| R4 | An assertion enters after the RED phase and is never observed red | Neither `169.017-T`, `169.015-T` nor `169.016-T` may add one, every assertion family has a named RED owner, and a family with no RED owner has no assertion. `169.017-T` evaluates only families that already carry recorded RED evidence, so an assertion invented later has no evidence to evaluate and blocks the readiness verdict rather than riding through it. |
| R5 | ACTIVATE exceeds two hours and is split across commits, or is narrowed mid-flight | Neither is permitted. `169.015-T` halts and the unit returns to **Stage** for explicit scope redesign, per the 2-hour check above. The commit never splits, and no assertion is authored or re-derived inside ACTIVATE; any reduced contract has its assertions retired or re-observed red in the RED phase, and `169.017-T` re-run for a fresh readiness verdict, before activation resumes. |
| R6 | The unit is serialized behind a foundation it does not need | `depends_on_shipments` is empty and `177-S` carries no shipment-level edge in either direction. The root claim is checkable against the executable records, not only against this plan. |
| R7 | The gate token the plan declares is not the token the emitting task produces | *Gates and verdicts* names both vocabularies, each gate's emission conditions state when each token fires, and each gate has exactly one emitter — `169.017-T` for readiness, `169.016-T` for the status contract — whose record reproduces its own vocabulary verbatim. A task record emitting any other token is a defect, not a variant. |
| R8 | A green aggregate suite exit is read as the contract holding | `STATUS_CONTRACT_NOT_OBSERVED` is evaluated first and absorbs every unrun, unimportable and unrecorded case, including a green exit with no per-assertion record. An absent verdict line is also `STATUS_CONTRACT_NOT_OBSERVED`, and *Confirmation artifact and line format* names the one path a reader checks and the closed list of read outcomes that count as absent, so absence is decidable rather than ambiguous. No path reaches `STATUS_CONTRACT_HELD` without a per-assertion passing record for all five families. The same fail-closed construction is applied independently to `PREACTIVATION_NOT_OBSERVED`. |
| R9 | The unit's only gate is emitted after the irreversible activation commit, so activation is authorized by nothing | `169.017-T` emits a **pre-activation** readiness verdict from the complete inert evidence set, and is the sole immediate predecessor of `169.015-T`. `169.015-T`'s first action is a fail-closed read of that verdict, and on any token other than `PREACTIVATION_READY` it touches no declared surface. The post-activation confirmation is retained but no longer carries the authorizing role, which is what `D2` requires. |
| R10 | The two verdicts are conflated, and a post-activation confirmation is read as pre-activation authorization | The two use **disjoint vocabularies** (`PREACTIVATION_*` versus `STATUS_CONTRACT_*`), **distinct paths**, and distinct line prefixes (`PREACTIVATION_STATE: ` versus `COMPOSED_STATE: `), and neither emitter writes the other's file. A `STATUS_CONTRACT_HELD` token can never satisfy `169.015-T`'s predicate, because that predicate matches only the literal `PREACTIVATION_READY`. |
| R11 | Post-activation confirmation fails and the workspace is left mid-migration with no defined path | *Failure path — rollback and halt* states the path in advance: non-zero exit, halt, DOCS does not proceed, `git revert` of the single activation commit as a unit, return to Stage. Reverting is well-defined precisely because activation is one commit. |
| R12 | A stale readiness verdict authorizes a second activation after a revert or a redesign | Mechanical, not procedural. The readiness artifact is whole-file replaced by its sole writer on every run, so a re-run necessarily emits a fresh binding. The `PREACTIVATION_READY` line carries `head_commit`, `candidate_digest` (`CCD/v1` over seven enumerated inputs) and `binding` (`B/v1`), and `169.015-T` **recomputes all of them against the repository** as `F1`–`F5` before its first write. On the documented post-revert path `git revert` creates a new commit, so `F1` fails on `head_commit` and `F4` fails on `checked=`, and the gate is CLOSED even though the four surfaces are byte-identical to their pre-activation state and the token still reads `PREACTIVATION_READY`. `checked=` is consumed by `F4` and `F5` rather than displayed; revision 5 declared it as the mitigation without giving it a consumer, which attempt 05 recorded as `N2`. The procedural mandate to re-run `169.017-T` remains in six records, but it is now the *remedy*, not the guard. |
| R13 | The CONFIRM → DOCS edge is a completion edge, so documentation lands describing unconfirmed behaviour | `169.007-T`'s **first action** is a fail-closed whole-file read of the confirmation artifact, in the same shape `169.015-T` uses: the entire file must be exactly one `COMPOSED_STATE: ` line whose first field is a byte-for-byte match against the literal `STATUS_CONTRACT_HELD`, plus `F1`–`F5` recomputed against the repository. Absence, malformation, staleness, a failure token and a foreign `PREACTIVATION_*` token are each enumerated as CLOSED. On CLOSED it touches no file, makes no commit, and exits `1`. The `blocks` edge supplies ordering only, because `169.016-T` completes on all three of its tokens. Through revision 5 this edge was guarded by prose, an edge and an exit code only, which attempt 05 recorded as `N1`. |
| R14 | The freshness binding is mistaken for a security boundary, or blocks legitimate work | Both directions are stated rather than left to inference. *Not security:* `B/v1` is a staleness and mistake-detection contract; an actor who recomputes the binding can forge a consistent line, and the plan claims no protection against that. *Not blocking:* the only false-close is an unrelated commit landing between a gate and its consumer, which is fail-closed in the correct direction for a gate guarding an irreversible four-surface mutation, and whose remedy — re-run the emitting gate — is cheap and already mandated. No wall-clock "not in the future" condition is imposed, deliberately, because clock skew would make the contract environment-dependent. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.
`requires_plan_hardening` is **`true`**: the four declared surfaces span two
template families — `templates/policies/` and `templates/agents/` — plus their
installed mirrors, and Stage's planning gate names multiple template families
an elevated blast-radius signal. The signal is declared rather than argued
down, so this section is a **gate**. That the unit adds no executable surface,
runs no command and migrates no record bounds the blast radius; it does not
remove the signal.

The structural questions below exist because a plan invariant and its own
manifest were previously able to contradict each other without either document
being wrong on its face, because the plan and its only verdict-emitting task
were able to declare different gate vocabularies for the same gate, and because
the unit's only gate emitter was previously scheduled **after** the single
irreversible activation commit — so the plan's own rollout contradicted the
portfolio's binding rollout invariant while every individual task read as
correct.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Why is this unit not gated behind the substrate foundations? | Because it needs none of them. It changes declarations and asserts their agreement. Serializing it behind `182-S` → `184-S` → `185-S` would be a false dependency, which the architecture decision forbids, and `177-S` carries no such edge. |
| H2 | Is a passing conformance test evidence the contract holds? | Only if it was first observed failing, and failing for the right reason. The attempt-08 defect was GREEN-only assertions; the discriminating RED rule closes the weaker version of the same gap, where an assertion fails merely because nothing exists yet. |
| H3 | Is an aggregate non-zero suite exit sufficient RED evidence? | No. It does not prove that *this* assertion failed. Each assertion's failing observation is recorded individually, with its own declared marker in its own failure text. |
| H4 | What if a surface is added after the contract lands? | The surface list is derived by rule and the count is asserted at 4, so a new surface fails the conformance test rather than diverging silently. |
| H5 | Is the `abandoned`-transition observation in scope? | No. It is a backlog-tool transition-table observation recorded so it is not lost, explicitly outside this unit's contract, which concerns what member status *is* after a claim. |
| H6 | Why one commit across all surfaces? | A commit boundary mid-migration is a reachable state in which a mirror states a vocabulary its template does not — the divergence the unit exists to remove. A dependency edge between two activation tasks does not close that window; it opens it, because an edge permits a commit between its endpoints. Adding a pre-activation gate does not weaken this: `169.017-T` is a predecessor of the single activation task, not a second activation task. |
| H7 | Does every assertion in this unit have a RED task that records it failing? | Yes, and it is checkable rather than asserted: the Assertion-to-task map lists every family with its owning RED task and its discriminating fixture, and the Tasks table lists every task with its phase. A family in neither table has no assertion. This question exists because the previous hardening pass answered H6 correctly in principle without ever checking whether the manifest did it. |
| H8 | Does the plan's task table match the shipment manifest? | It must, and the correspondence is the check: **ten** tasks, in the phases and sizes stated, are the `177-S` manifest members alongside `169-F`, and the manifest is ordered in the same phase sequence. A plan that cannot be checked against the work it governs is the precondition for exactly the contradiction attempt 01 found. |
| H9 | Is the ACTIVATE task within the 2-hour rule? | Yes on both axes, for the reason recorded under the 2-hour check. The added gate read parses one line and recomputes `F1`–`F5` — a bounded, fully-specified sequence of seven file reads and two `git` queries with no judgement in it — which moves `complexity` from `low` to `medium` and leaves `size` at `M`. If it ever is not within the rule, the unit **halts and returns to Stage** for explicit scope redesign. It never splits the commit, and it never narrows or re-derives an assertion inside ACTIVATE — a reduced contract has its affected families retired or re-observed red in the RED phase first, and `169.017-T` re-run. |
| H10 | Does the token this plan declares match the token the emitting task produces? | Yes for both gates, and the correspondence is the check. Each gate has exactly one emitter: `169.017-T` for `PREACTIVATION_READY` / `PREACTIVATION_BLOCKED` / `PREACTIVATION_NOT_OBSERVED`, and `169.016-T` for `STATUS_CONTRACT_HELD` / `STATUS_CONTRACT_DIVERGENT` / `STATUS_CONTRACT_NOT_OBSERVED`. *Gates and verdicts* declares both vocabularies, each gate's emission conditions state objectively when each token fires, and each emitter's record reproduces its own. This question exists because an earlier revision declared a three-token vocabulary in the plan while the only record that produced a verdict emitted an unrelated two-token pair — deleting the not-observed state that decision D6 requires. |
| H11 | Can an unrun or unimportable suite be scored as the contract holding? | No, and the ordering is what prevents it. `STATUS_CONTRACT_NOT_OBSERVED` is evaluated **before** the other two states and absorbs import failure, `loader.errors`, `_FailedTest` placeholders, zero executed assertions, a family with no per-assertion record, and an absent verdict line. `STATUS_CONTRACT_HELD` requires an affirmative per-assertion passing record for all five families; a green aggregate exit cannot produce it. This is the unit's most specific safety property, and it is the one the RED phase's binding import-safety rule exists to detect — so it has a token of its own. |
| H15 | Where does each verdict line go, and can a reader tell absence from presence-elsewhere? | Each goes to exactly one declared path — `.autoharness/gates/p002-7-preactivation-readiness.txt` and `.autoharness/gates/p002-7-status-contract-verdict.txt` — in one of three literal line forms, written atomically by a single declared writer with whole-file replacement. *Readiness artifact and line format* and *Confirmation artifact and line format* each state the destination, the three forms, the single-writer and atomicity rule, and the closed list of read outcomes that resolve to the not-observed token — missing, unreadable, empty, no prefixed line, more than one, or an unrecognised token. This question exists because an earlier revision declared that an *absent* verdict line is itself not-observed while naming no destination, which made absence and presence-elsewhere indistinguishable and the gate unevaluable as written. |
| H16 | Does this unit need a CI change to be evaluable? | No, and it does not make one. Each gate's own emitting task is its authoritative evaluator: it runs or evaluates, writes its verdict artifact, and exits zero **only** on its pass token. `.github/workflows/ci.yml` is a **producer** of the observations — its `test` job runs the stdlib unittest suite and consumes an exit code — not a consumer of either verdict line; an earlier revision had that direction inverted. No task in `177-S` modifies `ci.yml`, no workflow is added, and both gates are self-contained. `.autoharness/gates/` is gitignored, so neither verdict is committed and neither leaves the tree dirty. |
| H17 | Does this unit's rollout conform to `D2`'s `PREPARE → VERIFY → ACTIVATE` invariant? | Yes, and the mapping is recorded in *Rollout* rather than left to inference. PREPARE and RED are both `D2` PREPARE, because `D2`'s PREPARE is explicit that tests go red then green *entirely within the inert surface*. `169.017-T` is `D2` VERIFY: it produces the complete evidence verdict with every declared surface still unmutated. `169.015-T` is `D2` ACTIVATE. CONFIRM and DOCS are post-activation steps `D2` neither names nor forbids. `D2`'s third evidence limb — compatibility against `D3`'s pinned corpus — is recorded **inapplicable** (no normalizer, no historical corpus) rather than silently dropped, because a deviation that is not recorded is indistinguishable from one that was not noticed. |
| H18 | What actually authorizes activation — the dependency edge, or the verdict? | The **verdict**. The edge `169.015-T ← 169.017-T` supplies ordering only; a completed predecessor task proves the task ran, not that it concluded favourably. `169.015-T`'s first action is to read the readiness artifact and compare the token against the literal `PREACTIVATION_READY`, halting before any write on `PREACTIVATION_BLOCKED`, `PREACTIVATION_NOT_OBSERVED`, or any absent-or-malformed read. This distinction is the portfolio's own precedent, recorded against `177-F`'s gate in attempt 03. |
| H19 | Can the post-activation confirmation be mistaken for the authorizing gate? | No, and the separation is structural rather than editorial. Two artifacts at two paths, two disjoint token vocabularies, two distinct line prefixes, two sole writers neither of which writes the other's file, and an authorization predicate that matches one literal token only. A `STATUS_CONTRACT_HELD` line cannot satisfy `169.015-T`'s predicate under any reading, and `169.016-T`'s exit code gates **documentation and rollback**, not activation. The readiness line carries `resolved_surface_count=0` and the confirmation line carries `resolved_surface_count=4`; that difference is a phase property of the two gates, not a discrepancy between them. |
| H20 | If confirmation fails after activation, what happens? | *Failure path — rollback and halt*: `169.016-T` exits non-zero, the unit halts, `169.007-T` DOCS does not proceed, and the single `169.015-T` commit is reverted as a unit so all four surfaces return to their pre-activation state simultaneously. The DOCS halt is **mechanical**: `169.007-T`'s own first action is a fail-closed whole-file read whose token is not the literal `STATUS_CONTRACT_HELD`, so it touches no documentation, makes no commit and exits `1` — it does not depend on any process having observed `169.016-T`'s exit code. The unit returns to Stage; the divergence goes back to a RED task for re-observation, and `169.017-T` is re-run for a fresh readiness verdict before any re-activation. `169.016-T` never repairs a surface in place and never weakens an assertion to reach its pass token. |
| H21 | Is the gate-predicate principle applied to **every** edge that crosses a three-token verdict, or only to the one guarding a mutation? | Every one, and there are exactly two: `169.015-T ← 169.017-T` and `169.007-T ← 169.016-T`. Both predecessors complete on all three of their tokens, so both edges supply ordering only and both successors carry their own first-action fail-closed read against a single literal token plus `F1`–`F5`. The remaining eleven `item_deps` edges cross no verdict and are read as permission by nothing. This question exists because revision 5 stated the principle generally at `H18`, applied it correctly to the ACTIVATE edge, and left the structurally identical DOCS edge on prose, a `blocks` edge and an exit code — a safety property the plan asserted in four places and enforced in none of them mechanically. Attempt 05 recorded that as `N1`. |
| H22 | Is an authorizing verdict bound to the evidence identity it was computed from, or only to its own token? | To the identity. Each authorizing line carries `head_commit`, a `CCD/v1` content digest over a **fully enumerated** input list, and a `B/v1` `binding` that covers `checked=`; each consumer recomputes all of them against the repository as `F1`–`F5` and fails closed on any mismatch, absence or malformation. The decisive case is the plan's own post-revert re-activation path, where the declared surfaces return to byte-identical pre-activation content — a content digest over surfaces alone would still match, and `F1` is what closes it, because `git revert` necessarily advances `HEAD`. This question exists because revision 5 declared a `checked=` vintage field, named it in `R12` as the stale-verdict mitigation, and then specified an activation predicate whose five conditions never read it; the field was declared for a safety purpose and given no consumer. Attempt 05 recorded that as `N2`. The construction is scoped honestly at `R14`: staleness and mistake detection, not a tamper-proof boundary. |

### Blast radius

Four declaration surfaces — two authoritative templates and their two installed
mirrors — plus three test-material files and one documentation page. The test
material is the conformance test module
`tests/test_p002_7_member_status_contract.py` and the two inert helper modules
`tests/p002_7_candidate_definition.py` and `tests/p002_7_near_miss_fixtures.py`
authored in PREPARE. Naming the two helpers explicitly at revision 6 added no
file to the unit — `169.011-T` always authored both — it only made the
`CCD/v1` input list enumerable. Neither helper matches `unittest discover`'s
default `test*.py` pattern, so neither adds a collected test module. None of
the three is a declared surface: the enumeration rule's search scope is
`templates/policies/`, `.github/policies/`, `templates/agents/` and
`.github/agents/`, so `declared_surface_count` stays fixed at **4**.

No executable boundary, no command execution, no migration of existing mutable
records, and no change to any backlog record's schema. The surface count is
fixed and enumerated, which is what makes the blast radius statable rather than
estimated.

Two generated verdict artifacts sit **outside** that radius by construction:
`.autoharness/gates/p002-7-preactivation-readiness.txt` and
`.autoharness/gates/p002-7-status-contract-verdict.txt`. `.autoharness/gates/`
is gitignored, so neither is a declared surface, neither is committed, neither
appears in a diff, and neither can leave the working tree dirty. The revision-6
freshness fields are added **inside** those two existing lines at those two
existing paths; no new artifact, no new directory and no new ignored path was
introduced. They are observations *about* the radius, not part of it.

### Rollback

PREPARE, RED and VERIFY are inert: they add test code and test data and write
verdict artifacts to an ignored path, and change no declared surface. Anything
abandoned before activation rolls back by discarding untracked test material;
no declared surface has moved.

The single ACTIVATE commit reverts as a unit, returning all four surfaces to
their current divergent state simultaneously. That guarantee holds because
activation is one commit; it would not hold across two commits joined by a
dependency edge, where reverting the second leaves the first in place and
returns the workspace to the split state rather than the original one.

A **post-activation confirmation failure uses exactly that revert**, and it is
the reason the one-commit rule is load-bearing rather than stylistic: on
`STATUS_CONTRACT_DIVERGENT` or `STATUS_CONTRACT_NOT_OBSERVED`, `169.016-T`
exits non-zero, `169.007-T`'s own fail-closed read is CLOSED so DOCS touches
nothing and commits nothing, the activation commit is reverted as a unit, and
the unit returns to Stage.

**The revert re-closes both gates without either consumer being told.**
`git revert` creates a new commit, so `HEAD` advances past every
`head_commit` value written before it. Any surviving `PREACTIVATION_READY` line
fails `F1` and `F4` at `169.015-T`, and any surviving `STATUS_CONTRACT_HELD`
line fails `F1` and `F4` at `169.007-T` — and the confirmation line additionally
fails `F2`, because the reverted surfaces no longer match its `surface_digest`.
Re-activation requires a fresh `PREACTIVATION_READY` verdict from a re-run
`169.017-T`; the pre-failure verdict is stale, and since revision 6 its
staleness is **detected** rather than merely forbidden.

### Verification floor

Every assertion recorded failing before it is recorded passing, individually,
and failing against a near-miss fixture as well as against absence. No
assertion enters after the production text exists.

**The complete evidence set is adjudicated before activation, not after.**
`169.017-T` reads the recorded absence RED, discriminating RED and inert GREEN
observations for all five families, confirms the inert precondition still holds
(`resolved_surface_count = 0`), and emits `PREACTIVATION_READY` only if every
family is affirmatively covered. Anything unestablished is
`PREACTIVATION_NOT_OBSERVED`, not a pass. `169.015-T` may not proceed without
that token, so the floor is enforced by a read at the activation boundary
rather than by a report written after it.

**Both boundaries are enforced by a read, and by the same read.** There are two
boundaries in this unit at which a three-token verdict authorizes an
irreversible act — activation, and the documentation commit — and each is
enforced by its own successor's first-action fail-closed read of a single
literal token plus the `F1`–`F5` freshness recomputation. Neither boundary is
enforced by a `blocks` edge, by an exit code the reader must have observed, or
by prose. A verdict that is absent, malformed, non-authorizing or stale fails
both readings identically, and in every one of those cases the successor
touches nothing and exits `1`.
