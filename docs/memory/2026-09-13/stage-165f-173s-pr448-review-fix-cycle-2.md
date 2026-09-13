---
title: "Stage session memory — PR #448 review-fix cycle 2 (165-F / 173-S)"
description: "Resolution of five same-contract-surface Copilot threads on staging PR #448: at-most-once grant consumption, bootstrap B4 claim reversal, RED-test mechanism under unittest, genesis narrowness, and a reintroduced audit zero-write assertion."
doc_type: memory
source: docs/memory/2026-09-13/stage-165f-173s-pr448-review-fix-cycle-2.md
date: 2026-09-13
agent: stage
branch: chore/stage-173-S
feature: 165-F
shipment: 173-S
pr: 448
---

# Stage — PR #448 review-fix cycle 2

## Session framing

Focused review-fix cycle on branch `chore/stage-173-S`, intake HEAD `5aec76f2`.
Five Copilot findings, all landing on the **same contract surface** the prior cycle
touched. All five assessed **VALID** and accepted; none was rejected or deferred.

Scope discipline observed throughout: Stage-owned plan/backlog/review/memory
artifacts only. **No** product source, test, template, schema, or config file was
modified; **no** PR API call was made; nothing was pushed; `173-S` was **not**
claimed. Unrelated working-tree files (`.engram/`, `.gitignore`,
`.backlogit/checkpoints/*.json`, untracked `docs/` scratch, `scripts/`) were left
untouched and unstaged. One new non-amended commit.

No plan-review cycle consumed — PR review-fix cycles are a separate counter, and
plan-review cycle 4 remains the authorized final plan-review.

## The five findings and how each was resolved

### `PRRT_kwDORzpWpM6h3fqf` — at-most-once consumption undefined (ACCEPTED)

`165.011-T` required a grant label be consumed "at most once" but defined the
predicate only as "is not already consumed". That is satisfiable by an in-process
set that resets on every CLI invocation — a zero-guarantee at-most-once that would
still have passed review. At-most-once *is* the security value of a bootstrap grant.

**Resolved** with Deliverable 6 (6a–6i): an `O_EXCL` exclusive-create per-grant,
per-label consumption record at
`.autoharness/gates/bootstrap-grant-consumption/{shipment_id}/{label}.json`
(already-gitignored prefix; node-local runtime state, while the **grant** stays
version-controlled and reviewable). Read-then-write existence checks are forbidden
(TOCTOU). The claim happens **after** all non-consumption match conditions and
**before** the force, so a non-matching grant never burns a label. `FileExistsError`
→ fail closed, exit 1, never wait/retry/poll/steal. **No TTL.** `grant_digest`
binding means editing the grant cannot reset consumption. Crash between claim and
audit leaves an intact `claimed` record carrying every audit field;
`claimed`→`consumed` uses temp+`fsync`+`os.replace` so it is never torn. Recovery is
**operator-only and out-of-band** — a CLI reset flag would let an agent re-open an
exhausted grant. Audit is emitted **from the claimed record**, not recomputed.
Malformed/stale record ⇒ treated as **consumed** (fail closed), the deliberate
inverse of a malformed *grant* ⇒ *no grant*; both resolve toward no force.
Containment: IDs/labels validated before path construction, resolved path asserted
inside the resolved root including symlinks.

**Scope bound stated, not hidden**: the guarantee is per workspace clone. Recorded
as accepted residual risk (plan §H5) with `expires_on_claim`, exact-token binding,
and manifest-digest binding as the compensating bounds; documented by `165.009-T`
deliverable 8b.

**Sizing**: `165.011-T` complexity medium → **high** (size unchanged, `M`).
Per the two-axis rule high complexity forces split-or-de-risk; **de-risked in
place**, because Deliverable 6 is inseparable from Deliverable 2's matching rule —
splitting them ships a grant surface whose at-most-once bound is unenforced for the
duration of the gap, which is the defect itself.

### `PRRT_kwDORzpWpM6h3fq1` — BOOTSTRAP-A B4 claim reversal (ACCEPTED)

B4 told the operator to "reverse the claim" on a non-zero `post_claim`. Verified at
this HEAD: `backlogit shipment --help` lists exactly `add`, `claim`, `create`,
`get`, `list`, `return-blocked`, `ship` — no unclaim path — and `queued` is a
create-time default not reachable from `active`. A failure branch that terminates in
an unexecutable step, at the exact moment the workspace sits half-entered, is worse
than none: it reads as a safety net that does not exist.

**Resolved**: halt, `173-S` **remains `active`**, B5/B6 not performed, Ship not
invoked, no forced re-run (force authority already expired on the successful B3
claim). Remediation is operator-owned and explicit — **(a) diagnose and converge**
(most plausibly a second `active` shipment, a P-001 violation; re-run B4 unforced
until exit 0, resume at B5; a forward fix, not a rollback), or **(b) abandon** via
the supported `active` → `abandoned` transition, which **must be verified** by
re-reading the record and is **terminal, not a requeue** — the scope must be
re-shipped under a new shipment record. No artifact promises automatic reversal.

### `PRRT_kwDORzpWpM6h3frC` — RED-test mechanism (ACCEPTED)

Verified: `.github/workflows/ci.yml` runs `PYTHONPATH=src python -m unittest
discover -s tests`, and its own header states autoharness has no pytest configured.
So a `pytest.mark.xfail` marker is an attribute nothing reads — the body runs, the
expectation raises, **CI goes red** — and `unittest.expectedFailure` accepts *any*
exception and takes no reason argument. The cycle-3 instruction ("pin each marker
with an explicit `raises=`/reason") described a pytest capability under a runner
that is not pytest; implemented literally it would have left canonical CI red,
violating the plan's own "every task ends green" rule.

**Resolved** with a stdlib-only `@expect_red(raises=, message_contains=, reason=)`
helper: passes only on the named exception type whose *normalized* message contains
the expected substring; **fails on any other exception**, naming expected vs.
observed (so a broken fixture, import error, or unregistered `--phase` turns the
suite red instead of masquerading as RED); **fails on XPASS**, preserving
`xfail(strict=True)` strictness. No `pytest` import; identical under both runners.
The simpler alternative — RED expectation authored in the same task as its
implementation, with the RED observation recorded in disposition notes — is
permitted explicitly. Every task ends green under both routes.

### `PRRT_kwDORzpWpM6h3frF` — genesis still fail-open (ACCEPTED)

Shipment status enum is {`queued`, `blocked`, `active`, `shipped`, `abandoned`}.
The cycle-2 three-probe rule covered shipped-terminal (G2), nonterminal enumerated
as `queued`/`active` (G3), and abandoned (G4). **`blocked` appeared in none.** A
workspace with one `blocked` record plus an edge-less candidate satisfied all three
and returned `genesis` — an unearned pass. The structural lesson is larger than the
one missing status: enumerating statuses is fragile by construction, since every
future enum member silently re-opens the hole.

**Resolved** with the **sole-record** rule: genesis requires no edges, no
`dag-root`, **and** the candidate being the only shipment record in the workspace —
live and archived counted together, regardless of status or provenance. Counting
records is status-agnostic and cannot be widened by a new status. Absent, empty,
non-string, unparseable, or unrecognized status (including unrecognized
`archived_status`) **counts as disqualifying, fail closed**; enumeration failure
raises rather than concluding sole-extancy from a partial read. Genesis stays
cardinality-1. Secondary win: the shared-snapshot surface drops from three facts to
one, strictly lowering divergence risk between the two gates.

Regression cases added: `165.001-T` N5f (`blocked`, live and archived), N5g
(missing/empty/non-string/unrecognized status and unrecognized `archived_status`,
each asserted independently), N5h (enumeration failure raises), N5e extended to
prove `dag-root` still passes in every such workspace; `165.004-T` P3b widened to
two disqualifier shapes.

### `PRRT_kwDORzpWpM6h3frY` — reintroduced zero-write assertion (ACCEPTED)

A genuine **regression of a cycle-1 correction**. Cycle 1 retracted the absolute
no-write claim from `165.003-T`, `165-F`, `165.008-T`, `165.009-T` on thread
`PRRT_kwDORzpWpM6h3Tgi` — but `165.006-T` deliverable 5, authored in that same
cycle, still demanded "an assertion that the audit render path performs NO WRITE".
False for the same verified reason: `_gate_pipeline_topology_command` calls
`_emit_pipeline_topology_telemetry` unconditionally on every run of every phase.

**Resolved**: absolute assertion removed, narrowed to (a) no backlog mutation,
(b) no migration-state/ledger write, (c) telemetry **explicitly allowed and
positively tested** (with telemetry enabled the event *is* emitted while rendered
output and exit code are identical to a telemetry-disabled run), (d) fail-open
preserved and not made load-bearing. An anti-regression note bars reintroduction.

## Scope of record (corrected this cycle)

Current scope is **10 executable tasks** (`165.001-T`, `165.002-T`, `165.003-T`,
`165.004-T`, `165.005-T`, `165.006-T`, `165.008-T`, `165.011-T`, `165.012-T`,
`165.009-T`) plus covering feature `165-F` — **11 manifest items** — and the
one-time operator entry path **BOOTSTRAP-A steps B0/B1/B2** (forced `pre_claim`),
then B3–B6. **`U0`/`U1`/`U2` are retracted history**, not live steps: they named the
cycle-2/cycle-3 agent-run grant that no installed agent contract can execute.
`165.007-T` and `165.010-T` remain archived and off-manifest.

The **PR #448 body is Orchestrator-owned** and is updated separately; `173-S` and
`165-F` are authoritative for these counts within Stage's ownership.

## What changed

Ten backlog records (`173-S`, `165-F`, `165.001-T`, `165.002-T`, `165.004-T`,
`165.005-T`, `165.006-T`, `165.008-T`, `165.009-T`, `165.011-T`), the plan
(revision 5 → 6), the plan-review (new "PR Review-Fix Cycle 2" section), the
deliberation (two supersession notes added in place, historical bodies preserved
verbatim, revision 5 → 6), and this memory file.

No manifest change, no dependency-edge change, no task added or removed, one
complexity field changed (`165.011-T`, via the structured `backlogit` field).

## Lessons carried forward

* **A coupled-artifact sweep is a standing obligation, not a one-off.** Finding 5
  was a cycle-1 correction regressing into a file authored during that same cycle.
  The sweep table now lives in the review as a recurring check.
* **Verify a tool's capability surface before writing a contract step that depends
  on it.** B4 and the xfail mechanism were both invented plausibly and were both
  unexecutable; one `--help` and one CI-file read each would have caught them.
* **Prefer counting records to enumerating statuses.** An enumeration is a promise
  to revisit every time the enum grows; a cardinality test is not.
* **State scope bounds explicitly rather than letting a strong word imply more than
  the mechanism delivers.** "At most once" now names its per-clone bound in the
  task, the plan's residual-risk section, and the docs task.

## Next steps

1. Orchestrator updates the PR #448 body to the corrected counts (10 executable
   tasks, 11 manifest items, BOOTSTRAP-A B0/B1/B2).
2. Await further PR review; no plan-review cycle remains available.
3. `173-S` stays **queued** and unclaimed. Entry remains the operator-run
   BOOTSTRAP-A path; Stage does not claim.
