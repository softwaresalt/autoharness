---
title: "Bounded spike: network-denied Linux container isolation for external binary conformance"
description: "Time-boxed spike determining whether the isolation required to execute an untrusted external release binary is achievable on this repository's CI: no credentials of any kind in the job environment, network egress denied after asset acquisition completes, repository absent or mounted read-only, disposable mounts, a TOCTOU-resistant handle across the verify-execute boundary, hardlink and symlink substitution resistance, and a redirect rule derived from observed acquisition behaviour. Every property has an assigned determining task that records objective evidence, including credential absence, which is determined by inspecting the actual job environment, and the redirect rule, which is derived from one observed release-asset acquisition rather than from assumption. Credential absence (I1) is determined FIRST and gates every untrusted acquisition and containment probe on an ACHIEVABLE VERDICT, not merely on predecessor completion: the gated tasks read a machine-readable I1 gate line as their first action and fail closed to NOT DETERMINED - FLOOR INVOKED, naming I1 as the blocker, on anything other than ACHIEVABLE, so the composed state can never be a pass while credential absence is unverified or falsified. The GitHub-hosted-runner probe workflow the determining tasks require is committed, and its owner, exact path, creation, dispatch, removal, rollback and branch-cleanliness evidence are declared rather than left implicit. Branch cleanup is an EXECUTABLE LIMB OF THE FINAL PREDICATE rather than a prose expectation, and its lifecycle is TWO STEPS so that every recorded value is observable BEFORE it is recorded: 177.003-T removes the workflow and commits, 177.007-T then observes that already-existing removal commit and writes a fixed-shape CLEANUP_ evidence block in its own separate evidence commit, and 177.006-T evaluates the block as checks C1-C6 while independently re-observing the CURRENT branch tip, which is the final branch-state authority. No field of the block ever names the commit that records it, no SHA is guessed and no clean-tree claim is made from inside the change that makes the tree clean, so a spec-conformant FIRST emission exists and the pass state is reachable in one normal run without a waiver or a corrective cycle. A coverage gate that checks every property for a determining task and captured evidence resolves the unit to exactly one of FIVE composed states: ISOLATION_CHARACTERIZED, ISOLATION_FLOOR_ONLY, ISOLATION_CLEANUP_FAILED, ISOLATION_UNDETERMINED or ISOLATION_NOT_OBSERVED, evaluated in a declared precedence so the result is a total function. ISOLATION_CHARACTERIZED is unreachable unless the exact probe-workflow path is absent at the branch tip AND the creation, dispatch and removal evidence is present and internally consistent. Successor eligibility is stated per state and no state presents the isolation floor as proven. No conformance fixture and no production code ships. Gates the reduced SAFE_CLOSE unit."
doc_type: plan
source: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
date: 2026-09-18
plan_id: conformance-isolation-spike
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_role: active
revision: 6
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "verdict is null because no independent reviewer has judged revision 6. REMEDIATED-PENDING-REVIEW is recorded under disposition, where it belongs: it states what Stage produced, never what a reviewer found. Revision 6 is the product of one operator-authorized bounded Stage remediation cycle scoped to attempt 05's single open P2, L1 - the cleanup evidence block was mandated to be written in the same commit that removes the probe workflow, while two of its eight lines carried values that only that commit's own creation defines, so no spec-conformant first emission existed and at least one spurious ISOLATION_CLEANUP_FAILED cycle was forced on every execution of the unit as written. Revision 6 closes L1 by splitting the cleanup lifecycle in two: 177.003-T removes the workflow and commits (the removal commit) and writes no CLEANUP_ line, and a new bounded task 177.007-T then observes that already-existing commit and writes the eight-line block in its own separate evidence commit. Every recorded value is observable before it is recorded, the tip-observation field names the tip that was observed rather than the commit that records it, and the evaluator's independent re-observation of the CURRENT tip remains the final branch-state authority. The five-state vocabulary, ISOLATION_CLEANUP_FAILED and its five-token reason vocabulary, the I1 verdict gate, the no-credential/no-secret evidence rule, the acquisition-then-no-network model, the workflow rollback and the per-state 181-S eligibility rules are all preserved unchanged. Attempt 05's three open P3 findings K5, K6 and L2 were NOT in scope for this cycle and remain open and unaddressed; they are carried as non-blocking follow-ups in the backlogit stash. Attempt 05 independently closed K3 and K4, and neither is carried. Where this cycle's mechanically necessary edits touch text L2 also concerns, no claim of L2 closure is made or implied: the C6 reason token WORKFLOW_PRESENT_AT_TIP is deliberately left raised on a dirty working tree as well as on a present path. Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 6
review_manifest: docs/reviews/2026-09-18-conformance-isolation-spike-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 1
source_stash_ids:
  - 7F9CB5E9
feature_id: 177-F
shipment_id: 183-S
unit_role: precursor-spike
dag_role: root
depends_on_shipments: []
gates: 181-S
external_tracker: 002-C
external_tracker_state: blocked-outside-shipment
requires_plan_hardening: true
hardening_rationale: "The spike researches the containment boundary for executing an untrusted third-party binary. Getting the question set wrong produces a foundation plan that under-specifies isolation, so the question set itself warrants adversarial review even though the spike ships no production code. The hardening pass includes a structural coverage question, because attempt 01 found a declared property with no determining task and the original pass did not ask whether one existed. It includes an ordering-enforcement question, because attempt 02 found the probe-safety answer resting on an I1-before-probe ordering that no dependency edge enforced. It now also includes a VERDICT-PREDICATE question (H12) and a gate-reachability question (H13), because attempt 03 found the restored blocks edge gating on predecessor COMPLETION while 177.004-T completes on two further outcomes that leave credential absence unverified or falsified; a committed-surface question (H14), because the spike commits a GitHub-hosted-runner probe workflow that the previous blast-radius and rollback statements described as mutating nothing and as uncommitted; an EXPRESSIBILITY question (H15), because attempt 04 found H14's branch-cleanliness expectation stated only in prose while the composed-state vocabulary could not express its failure, so the check was a claim rather than an executable predicate; and a CONSTRUCTIBILITY question (H16), because attempt 05 found the resulting fixed-shape evidence block mandated to be written at a point that could not supply two of its own fields, so the predicate was expressible but its input contract was unsatisfiable on a first pass."
tags:
  - spike
  - ci-isolation
  - supply-chain
  - safe-close
  - precursor
---

# Bounded spike: network-denied Linux container conformance isolation

## Problem frame

The SAFE_CLOSE unit must observe how an external `backlogit` release binary
behaves on a record transition. Attempt-08 recorded two findings that no
rewording can close.

* `B3` — "the provisioned external binary has no OS sandbox and no
  race-resistant handle containment." The write-then-verify-then-execute
  sequence is open to substitution **between verification and execution**, and
  the binary runs with the full privileges of the test process.
* `B4` — "the authoring platform cannot execute the authoritative baseline."
  The `linux-amd64` ELF binary was designated authoritative while the authoring
  workstation is Windows. A Windows host cannot execute it.

The architecture decision resolves both by **moving execution** to an isolated
Linux CI container rather than by adding another check on the workstation. But
whether that container can actually provide the required properties on
GitHub-hosted runners is **not known**, and a plan that assumes it would repeat
the portfolio's core error.

A third finding is also in frame. `B6` recorded that the rule "a redirect off
`github.com` halts" is unsatisfiable, because GitHub release-asset downloads
normally redirect to an object-storage host. The transport rule must be
re-derived from what acquisition actually does — which means an acquisition
must actually be observed. A replacement rule derived the same way the broken
rule was derived is `B6` under a new sentence, so this unit observes one real
acquisition before it writes any redirect rule.

## Security model

This model is a constraint on the spike's conclusions, not a question it may
reopen. The spike determines whether each property is achievable; it never
determines whether a property is required.

* **Isolated Linux container.** Conformance execution happens only there.
  Neither this spike nor `181-S` executes the untrusted binary on a developer
  workstation.
* **No credentials.** The job environment carries no token, key, or credential
  file of any kind.
* **Restricted mounts.** The repository is absent or mounted read-only; every
  mount is disposable and no state survives the job.
* **Post-acquisition network denial.** Egress is permitted for asset
  acquisition and denied before the binary executes.
* **Containment over verification.** Digest verification answers *what did I
  download*. It does not answer *what am I about to execute* or *what can it
  reach*.

If a property proves NOT ACHIEVABLE, the model is not weakened to accommodate
it: `181-S` degrades to evidence-and-documentation only, which is the
decision's declared floor.

**I1 is load-bearing for the spike's own safety, not only for `181-S`'s.** The
determining tasks acquire a real untrusted asset and probe containment against
it, so a job environment whose credential absence is unverified or falsified
must not reach that work at all. I1 is therefore determined first and gates the
acquisition and the probe on an **ACHIEVABLE verdict** — see *I1 gate*. On any
other I1 outcome the spike stops short of the untrusted work and records the
gated properties as unproven; it never proceeds and never composes to a pass.

## Required isolation properties

Each is classified **ACHIEVABLE** or **NOT ACHIEVABLE** by this spike. None is
assumed, and none is classified by the authoring task.

| # | Property | Why it is required |
|---|---|---|
| I1 | No credentials of any kind in the job environment | The executed binary is untrusted; a token in the environment is a token it can read |
| I2 | Network egress denied **after** acquisition completes | Digest verification answers *what did I download*; egress denial answers *what can it reach* |
| I3 | Repository absent, or mounted read-only | A writable checkout is a mutation surface for an untrusted process |
| I4 | Disposable mounts | No state survives the job |
| I5 | TOCTOU-resistant handle across verify→execute | Closes the substitution window `B3` identified |
| I6 | Hardlink/symlink substitution resistance | The acquisition path must not be redirectable by a pre-placed link |
| I7 | A correct redirect rule derived from observed acquisition behaviour | Replaces the unsatisfiable `B6` rule |

## Property coverage

Every property has exactly one determining task and one named evidence shape. A
property whose evidence is a documentation citation is **not determined**; H2
and R3 make that binding, and the coverage gate enforces it.

| # | Determining task | Evidence that constitutes a verdict |
|---|---|---|
| I1 | `177.004-T` | A recorded inventory of the actual job environment — environment-variable **names** present, credential-bearing filesystem paths present or absent, and the checkout's credential-persistence setting — taken inside the job, plus the mechanism that produces the absence |
| I2 | `177.001-T` | A recorded egress attempt to a known-reachable host, made **after** the acquisition observed in `177.005-T` completes, with its outcome and the mechanism that denied it |
| I3 | `177.001-T` | A recorded job run with the repository omitted, and a recorded write attempt against a read-only checkout, with both outcomes |
| I4 | `177.002-T` | A recorded observation that mount state does not survive the job, naming the mount type and the mechanism |
| I5 | `177.002-T` | A recorded substitution attempt against the verified handle between verification and execution, with its outcome |
| I6 | `177.002-T` | A recorded hardlink and symlink substitution attempt against the acquisition path, with its outcome |
| I7 | `177.005-T` observes; `177.003-T` transcribes | The observed redirect chain of one real release-asset acquisition — each hop's host, and the terminal host — recorded verbatim, from which the rule is read off |

`177.003-T` **transcribes** verdicts; it determines none. That separation is
the direct fix for the defect attempt 01 recorded: an authoring task cannot
produce an observation, so a property assigned only to authoring is a property
that will be asserted rather than determined.

## Out of scope

* Any conformance fixture. The four fixtures belong to `181-S`, after this
  spike says whether they can run under containment.
* Any change to `002-C`. It stays `blocked`, outside every manifest, with no
  dependency edge in either direction, and is not transitioned by this unit.
* Any administrative-close transition or rollback. The decision forbids one
  until a supported, tested transition *and* rollback exist; none does.
* Executing the untrusted binary. The spike characterizes containment and runs
  no conformance workload. `177.005-T` acquires an asset and records its
  transport behaviour; it does not execute what it acquires.

## Tasks

| ID | Task | Determines | Size | Complexity | Elapsed bound |
|---|---|---|---|---|---|
| `177.004-T` | Determine credential absence by inspecting the actual job environment | I1 | S | medium | 90 min |
| `177.005-T` | Observe one real release-asset acquisition and record its redirect chain | I7 input; the acquisition phase I2 is defined against | S | medium | 90 min |
| `177.001-T` | Determine post-acquisition egress denial and repository absence/read-only | I2, I3 | S | medium | 120 min |
| `177.002-T` | Determine disposable mounts and TOCTOU/hardlink-resistant containment | I4, I5, I6 | S | high | 120 min |
| `177.003-T` | Author the findings artifact; transcribe every verdict and read off the I7 rule; remove the probe workflow in the same commit | — | XS | low | 45 min |
| `177.007-T` | Observe the committed removal and emit the `CLEANUP_` evidence block in its own commit | — | XS | low | 30 min |
| `177.006-T` | Coverage, I1-gate and cleanup validation; emit the composed-state verdict | — | XS | low | 30 min |

Sequence: `177.004-T` → `177.005-T` → `177.001-T`, and `177.004-T` →
`177.002-T`. All four determining tasks block `177.003-T`, which blocks
`177.007-T`, which blocks `177.006-T`. The pre-existing `177.003-T` → `177.006-T`
edge is retained alongside the new chain; it is now transitively implied and is
kept rather than removed, so no existing edge in the DAG was deleted by this
revision.

**The closing sequence is three tasks, and that is a correction, not a
decomposition preference.** Through revision 5 removal and evidence emission
were one task and one commit, which attempt 05 finding `L1` (P2) showed to be
unsatisfiable — see *Why cleanup evidence is emitted in a second step* below.

**`177.004-T` runs first, and that precedence is enforced by a verdict, not by
completion alone.** It is the predecessor of both untrusted-acquisition and
containment-probe work: `177.005-T`, which pulls a real external release asset
onto a runner, and `177.002-T`, which probes containment against a real handle.
Neither may perform its acquisition or probe until I1 — "no credentials of any
kind in the job environment" — has been **determined by observation and found
ACHIEVABLE**, because a probe or acquisition job that carried credentials would
be a privileged process handling an untrusted artifact even without executing
it (H7). `177.001-T` inherits the same precedence transitively through
`177.005-T`.

The `blocks` edges in `item_deps` express the *ordering*. They are necessary
and they are not sufficient: a `blocks` edge clears on predecessor
**completion**, and `177.004-T` completes on three distinct outcomes, only one
of which is safe. The **verdict predicate** that closes that gap is specified
under *I1 gate* below and is carried inside the gated tasks themselves. A
version of this plan in which the records call these tasks "independent", or in
which the edge alone is offered as the safety argument, is a defect, not a
variant.

`177.005-T` precedes `177.001-T` because I2 is defined as egress denial *after*
acquisition completes. A task that establishes egress denial without ever
performing the acquisition it is defined relative to has not characterized I2.

### On `177.002-T` carrying `complexity: high`

Recorded rather than left implicit, because the harvest contract requires
`complexity: high` to force a split or a declared de-risking step.

The de-risking step **is this task**: I5 and I6 are adversarial containment
probes whose outcome is unknown in advance, and their uncertainty is the reason
a spike exists rather than a plan. Splitting I4 away would not reduce that
uncertainty — I4 is the low-uncertainty member and carrying it alongside costs
nothing, while I5 and I6 are one investigation against one handle and splitting
them would duplicate the setup rather than divide the risk.

The size axis is bounded independently: `S` at a 120-minute elapsed bound, with
the recorded-and-stop rule below. If the bound is reached, the unreached
property is recorded `NOT DETERMINED — FLOOR INVOKED` with what was attempted,
what blocked it, and the floor invocation in writing, which is a legitimate and
useful outcome; it is not a reason to extend.

## I1 gate: a verdict predicate, not a completion predicate

`177.004-T` completes on **three** distinct outcomes. Only one of them makes an
untrusted acquisition or a containment probe safe to run:

| I1 outcome | Gate token | May `177.005-T` / `177.002-T` acquire or probe? |
|---|---|---|
| `DETERMINED`, verdict **ACHIEVABLE** | `ACHIEVABLE` | **Yes** — credential absence was observed, with a mechanism |
| `DETERMINED`, verdict **NOT ACHIEVABLE** (R6) | `NOT_ACHIEVABLE` | **No** — credentials are affirmatively present |
| `NOT DETERMINED — FLOOR INVOKED` at the 90-minute bound (R9) | `FLOOR_INVOKED` | **No** — credential absence is unverified |

A `blocks` edge clears on **completion** and therefore clears on all three. The
edge is the ordering mechanism; it is **not** the safety mechanism, and it is
never offered as one.

### The gate artifact

`177.004-T` writes exactly one line to
`docs/spikes/2026-09-18-conformance-isolation-i1-gate.md`, creating the file,
as the **last** action of its own run. It is the sole writer. The line is:

```text
I1_GATE: ACHIEVABLE | verdict=DETERMINED | mechanism=<mechanism-name> | checked=2026-09-DD
I1_GATE: NOT_ACHIEVABLE | verdict=DETERMINED | reason=<short-reason> | checked=2026-09-DD
I1_GATE: FLOOR_INVOKED | verdict=NOT DETERMINED — FLOOR INVOKED | blocked_by=<short-reason> | checked=2026-09-DD
```

The line carries **names and mechanisms only**. No environment-variable value,
token, key fragment or credential content appears in it, in the findings
artifact, or in any job log — the same binding evidence rule that governs the
I1 inventory itself (R6, *Evidence handling*). `<mechanism-name>`,
`<short-reason>` and `<blocked_by>` are short non-secret identifiers.

### The predicate, and where it executes

**`177.005-T` and `177.002-T` each read this file as their first action, before
any acquisition, download, handle creation or substitution attempt.** Each
resolves the gate to exactly one of two results:

* **OPEN** — the file exists, is readable, contains exactly one `I1_GATE:`
  line, and that line's token is `ACHIEVABLE`. The task proceeds normally.
* **CLOSED** — **everything else**, including a missing file, an unreadable
  file, no `I1_GATE:` line, more than one `I1_GATE:` line, an unrecognised
  token, and the tokens `NOT_ACHIEVABLE` and `FLOOR_INVOKED`.

**On CLOSED the task does not run the untrusted acquisition or the probe at
all.** It is not deferred, retried or narrowed. The task instead records each
of its properties as `NOT DETERMINED — FLOOR INVOKED`, **naming `I1` as the
blocker**, together with the three parts the ledger requires: what was
attempted (the gate read), what blocked it (the observed `I1_GATE` token), and
the explicit written statement that the property is **unproven** and that
`181-S` is held at the evidence-and-documentation floor for that property's
scope. A CLOSED gate is a **legitimate recorded outcome**, not a failure to
report and not a reason to extend a bound.

### Which properties fail closed, and which do not

| Task | Properties recorded `NOT DETERMINED — FLOOR INVOKED` on CLOSED | Blocker named |
|---|---|---|
| `177.005-T` | I7 | `I1` |
| `177.002-T` | I4, I5, I6 | `I1` |
| `177.001-T` | I2 | `I1`, via the acquisition that never ran |
| `177.001-T` | **I3 is not gated** — repository absence/read-only is observable without acquiring or probing anything untrusted, so it is determined normally | — |

`177.001-T` is downstream of `177.005-T` and performs no untrusted acquisition
of its own, so it carries no gate read. I2 is defined as *egress denial after
acquisition completes*; when the acquisition did not run, I2 has nothing to be
defined against and is floor-invoked for that reason, with `I1` named as the
root blocker. I3 is independent of both the acquisition and the probe and is
determined on its own evidence.

### The composed state this forces

A CLOSED gate leaves at least one property `NOT DETERMINED — FLOOR INVOKED` and
none `ABSENT`, provided every gated task records its three required parts. By
the *Composed-state check* table that is **`ISOLATION_FLOOR_ONLY`** when
cleanup resolves to `CLEANUP_PROVEN`, and `ISOLATION_CLEANUP_FAILED` when it
does not. **Neither is a pass**, and the I1 gate's guarantee is independent of
which of the two lands.

**`ISOLATION_CHARACTERIZED` is unreachable whenever the gate is CLOSED**, and
that is a structural consequence rather than a rule that has to be remembered:
`ISOLATION_CHARACTERIZED` requires all seven properties `DETERMINED`, and a
CLOSED gate guarantees at least one is not. `ISOLATION_FLOOR_ONLY` is **not a
pass** and asserts nothing about the isolation. A gated task that ran its
acquisition or probe anyway, or that recorded a `DETERMINED` verdict for a
gated property while the gate was CLOSED, is a **defect and a finding**, not a
variant reading.

If a gated task records fewer than the three required parts, its row is
`ABSENT` by the ledger's own rule and the unit composes to
`ISOLATION_UNDETERMINED`, which blocks harvest outright. Neither path reaches a
pass.

## Probe workflow lifecycle

Four determining tasks — `177.004-T`, `177.005-T`, `177.001-T` and `177.002-T`
— require jobs on a GitHub-hosted Linux runner. **GitHub executes only
workflows that exist in the repository on a branch, so the probe workflow must
be committed.** It is stated here as a committed surface rather than described
as a throwaway, because describing it as uncommitted would be false and would
make the blast-radius and rollback statements false with it.

| Stage | Owner | What holds |
|---|---|---|
| Created | `177.004-T` | One workflow at the exact path `.github/workflows/spike-177-isolation-probe.yml`, committed to `chore/stage-176-s-workflow-defects` in its own commit. No other workflow file is added, and no existing workflow is modified |
| Dispatched | `177.004-T`, `177.005-T`, `177.001-T`, `177.002-T` | All four determining tasks reuse that **single** workflow via `workflow_dispatch`, selecting their probe by input (`i1-credentials`, `i7-acquisition`, `i2-i3-egress`, `i4-i6-containment`). No task adds a second workflow file |
| Removed | `177.003-T` | At spike close, after every determining task has reported, `177.003-T` deletes the file in the **same commit** that lands the findings artifact. That commit is **the removal commit**. `177.003-T` writes no `CLEANUP_` line |
| Evidence recorded | `177.007-T` | After the removal commit **already exists**, `177.007-T` observes it and writes the eight-line `CLEANUP_` block into the findings artifact in its **own separate commit** — **the evidence commit**. It removes nothing and determines nothing |
| Rolled back | `177.003-T` | If the spike aborts before close, `177.003-T` removes the workflow anyway and `177.007-T` still emits the block against that removal commit. Rollback is `git revert` of the single creation commit, or deletion of the single added path — there is no other change to undo |

**Declared constraints on the workflow itself.** It declares an explicit
minimal `permissions:` block, is passed no secrets, and runs only on
`workflow_dispatch` — never on `push`, `pull_request` or `schedule`, so it
cannot fire on unrelated branch activity. These constraints are what
`177.004-T` inspects to determine I1; they are not an assumption that I1 holds.

**Acquisition-then-no-network is preserved.** The workflow performs asset
acquisition only inside `177.005-T`'s dispatch, and every containment probe
runs after egress is denied. No credentials are present in any dispatch, and no
network access is required after acquisition completes.

**Evidence, recorded in the findings artifact by `177.007-T`.** The creation
commit SHA and the added path; each dispatch's workflow-run ID and URL, with
its input; the removal commit SHA; and a `git status --porcelain` observation,
taken **after the removal commit landed and before the evidence write was
staged**, showing the working tree clean and
`.github/workflows/spike-177-isolation-probe.yml` absent from the branch tip
that was observed. These are recorded in the fixed eight-line form defined
under *Cleanup evidence block* below, so they are machine-readable by
`177.006-T` rather than prose.

**Branch cleanliness is an executable limb of the final predicate, not an
expectation.** The branch carries the findings artifact and the I1 gate
artifact under `docs/spikes/`, and carries **no** probe workflow. A branch that
still contains the probe workflow at spike close is an **unclosed spike**, and
the unit composes to `ISOLATION_CLEANUP_FAILED` — a non-pass,
harvest-blocking state with its own verdict line and reason vocabulary. See
*Cleanup evidence block* and *Composed-state check* below. Through revision 4
this expectation was stated only in prose while the composed-state vocabulary,
defined exhaustively over the coverage ledger, had no token able to express its
failure; that was attempt 04 finding `K3` (P2).

### Why cleanup evidence is emitted in a second step

Through revision 5 the plan and `177.003-T`'s record both mandated that the
`CLEANUP_` block be written **in the same commit that removes the workflow**.
That instruction cannot be followed, and attempt 05 finding `L1` (P2) recorded
why:

| Field | Value required | Available when |
|---|---|---|
| `CLEANUP_REMOVED_COMMIT` | the SHA of the commit that removes the workflow | only **after** that commit exists — a commit's identity is a function of its content, so a commit whose content names its own SHA is not constructible |
| `CLEANUP_TIP_OBSERVATION` | a clean `git status --porcelain` and a tip SHA | only **after** that commit exists — the tree is dirty until the change is committed, and the tip is that commit |

Two of the eight lines therefore carried values that only the write point's own
creation defines. `C4` and `C5` could not be satisfied by a conformant first
emission, cleanup resolved `CLEANUP_FAILED`, and **at least one spurious
`ISOLATION_CLEANUP_FAILED` cycle was forced on every execution of the unit as
written**. The failure was fail-closed and the pass state was reachable on a
second emission, which is why it was graded `P2` rather than `P1` — but a
mandatory spurious cycle is a defect in the predicate's input contract, not an
acceptable cost.

**The fix is ordering, not relaxation.** Removal and evidence emission are
separated into two tasks and two commits:

1. `177.003-T` lands the findings artifact and deletes the workflow — **the
   removal commit**. It writes no `CLEANUP_` line.
2. `177.007-T` runs against that **already-existing** commit, observes it, and
   writes the block — **the evidence commit**, whose parent is the removal
   commit.

Every value the block carries is therefore **observable before it is
recorded**. Nothing in the block names the commit that records it, no SHA is
guessed or pre-computed, and no clean-tree claim is made from inside the staged
change that makes the tree clean. No check was weakened to achieve this: `C1`–
`C6` still hold, `C6` still re-observes the branch tip independently, and the
five-state vocabulary and precedence are unchanged.

### Cleanup evidence block

`177.007-T` is the **sole writer** of this block and writes it into
`docs/spikes/2026-09-18-conformance-isolation-findings.md` in its **own commit,
after `177.003-T`'s removal commit already exists**. `177.003-T` writes no line
of it. `177.006-T` is the **sole evaluator**. `181-S` reads neither the block
nor its checks — it reads only the composed-state token.

The block is **exactly eight lines**, in this order, each beginning at column
zero with the literal prefix shown:

```text
CLEANUP_WORKFLOW_PATH: .github/workflows/spike-177-isolation-probe.yml
CLEANUP_CREATED_COMMIT: <40-lowercase-hex>
CLEANUP_DISPATCH: i1-credentials | run_id=<digits> | url=<run-url>
CLEANUP_DISPATCH: i7-acquisition | run_id=<digits> | url=<run-url>
CLEANUP_DISPATCH: i2-i3-egress | run_id=<digits> | url=<run-url>
CLEANUP_DISPATCH: i4-i6-containment | run_id=<digits> | url=<run-url>
CLEANUP_REMOVED_COMMIT: <40-lowercase-hex>
CLEANUP_TIP_OBSERVATION: WORKFLOW_ABSENT | observed_tip=<40-lowercase-hex> | porcelain_empty_at_observation=yes | observed_at=2026-09-DD
```

**What each SHA means, stated so no field can be read as self-reference.**

| Field | Names | Never names |
|---|---|---|
| `CLEANUP_CREATED_COMMIT` | `177.004-T`'s creation commit — the commit that **adds** the exact path | anything else |
| `CLEANUP_REMOVED_COMMIT` | `177.003-T`'s removal commit — the commit that **deletes** the exact path, and which already exists when `177.007-T` reads it | the evidence commit that records this block |
| `observed_tip` | the branch tip `177.007-T` **actually observed** before it staged its own edit. On a normal run this is the removal commit, and it is the **parent** of the evidence commit | the evidence commit that records this block |

`porcelain_empty_at_observation=yes` records that the working tree was clean
**at that observation**, before `177.007-T` staged anything. It makes — and
needs — no claim about the tree after the block is written. The recorded
observation is **evidence of what was seen, not the authority on current branch
state**: that authority is `C6`, `177.006-T`'s own independent re-observation of
the **current** tip.

**Observation order is binding.** `177.007-T` confirms, in this order, that the
removal commit exists and is the current tip; that the exact path is absent at
that tip; that `git status --porcelain` is empty; and that the creation SHA and
the four dispatch identifiers are readable from the records already produced.
Only then does it compose and write.

**The write is atomic and all-or-nothing.** The eight lines are written as one
contiguous block in one commit. **If any required value cannot be observed, no
block is written at all** — no partial block, no placeholder line, and never a
guessed, invented or pre-computed SHA. A wholly absent block resolves to
`CLEANUP_FAILED | cleanup=EVIDENCE_MISSING`, the unit composes to
`ISOLATION_CLEANUP_FAILED`, and that is the correct fail-closed outcome. A
fabricated SHA would resolve `EVIDENCE_INCONSISTENT` and is forbidden outright.

**The artifact carries exactly one `CLEANUP_` block at all times.** A
re-emission **replaces** the block in place rather than appending beside it, and
more than one `CLEANUP_WORKFLOW_PATH:`, `CLEANUP_CREATED_COMMIT:`,
`CLEANUP_REMOVED_COMMIT:` or `CLEANUP_TIP_OBSERVATION:` line is
`EVIDENCE_MALFORMED`. This is the same single-instance rule the
`COMPOSED_STATE:` line carries.

The block carries **paths, commit identities, run identifiers, URLs and a date
only**. No environment-variable value, token, key fragment or credential
content appears in it — the same binding evidence rule that governs the I1
inventory and the I1 gate line (R6, *Evidence handling*). `177.007-T` is local,
offline and credential-free: it reads the local repository and already-recorded
run identifiers, dispatches nothing, acquires nothing and probes nothing. It
carries **no I1 gate read** for that reason and is unaffected by whether the
gate was OPEN or CLOSED — on a CLOSED gate `177.003-T` still removes the
workflow and `177.007-T` still emits the block, so cleanup can resolve
`CLEANUP_PROVEN` while the unit composes to `ISOLATION_FLOOR_ONLY`.

### The cleanup predicate

`177.006-T` resolves cleanup to exactly one of two results by evaluating six
checks. **`C6` is evaluated first, because it is the only limb that does not
depend on the artifact's own word.**

| # | Check | Holds when |
|---|---|---|
| `C6` | **Tip re-observation** | `177.006-T` observes the **current** branch tip itself, **before staging its own verdict-line edit**, and finds `.github/workflows/spike-177-isolation-probe.yml` **absent**: `git ls-files --error-unmatch <path>` exits non-zero and `git status --porcelain` is empty. The task does **not** take this from `CLEANUP_TIP_OBSERVATION`, and does not take it from `CLEANUP_REMOVED_COMMIT` |
| `C1` | **Path** | Exactly one `CLEANUP_WORKFLOW_PATH:` line, whose value is byte-identical to `.github/workflows/spike-177-isolation-probe.yml` |
| `C2` | **Creation** | Exactly one `CLEANUP_CREATED_COMMIT:` line carrying a 40-character lowercase hex SHA, naming a commit that **adds exactly that path** and adds or modifies no other workflow file |
| `C3` | **Dispatch** | Exactly four `CLEANUP_DISPATCH:` lines whose input fields are exactly the set `i1-credentials`, `i7-acquisition`, `i2-i3-egress`, `i4-i6-containment` — no duplicate, no omission, no unrecognised input — each carrying a non-empty `run_id` and a non-empty `url` |
| `C4` | **Removal** | Exactly one `CLEANUP_REMOVED_COMMIT:` line carrying a 40-character lowercase hex SHA, naming a commit that **deletes exactly that path**, that is a descendant of the `C2` commit on this branch, and that is **already reachable from the current branch tip**. It names `177.003-T`'s removal commit and never the evidence commit that records the block |
| `C5` | **Recorded observation** | Exactly one `CLEANUP_TIP_OBSERVATION:` line whose first field is the literal `WORKFLOW_ABSENT` and which carries `observed_tip=<40-character lowercase hex>`, `porcelain_empty_at_observation=yes` and `observed_at=<date>`. `observed_tip` must be reachable from the current branch tip, must be the `C4` removal commit or a descendant of it, and the exact `C1` path must be **absent from `observed_tip`'s tree**. `observed_tip` is **never required to equal the current tip** — `C6`, not this line, is the current-state authority |

Cleanup resolves to **`CLEANUP_PROVEN`** only when **all six** hold. Otherwise
it resolves to **`CLEANUP_FAILED`**, carrying the reason token of the **first**
check that failed in the order `C6, C1, C2, C3, C4, C5`:

| Reason token | Raised when |
|---|---|
| `WORKFLOW_PRESENT_AT_TIP` | `C6` — the exact path is present at the branch tip, or the working tree is dirty |
| `TIP_UNOBSERVABLE` | `C6` — the tip cannot be observed at all |
| `EVIDENCE_MISSING` | `C1`–`C5` — a required line is absent, or a required `CLEANUP_DISPATCH:` input is omitted |
| `EVIDENCE_MALFORMED` | `C1`–`C5` — a required line is present but not in the declared form: wrong field count, non-hex SHA, empty `run_id` or `url`, unrecognised token, or more than one of a single-instance line |
| `EVIDENCE_INCONSISTENT` | `C2`–`C5` — the lines are well-formed but disagree with the repository or with each other: a creation commit that does not add the path, a removal commit that does not delete it, a removal commit that is not a descendant of the creation commit or is not reachable from the current tip, an `observed_tip` that is unreachable, is not the removal commit or a descendant of it, or still carries the path, or a duplicate dispatch input |

**`ISOLATION_CHARACTERIZED` is reachable on one normal run, and that is
derived rather than asserted.** Taking the states of the six checks in
execution order against the two-step lifecycle:

1. `177.004-T` commits the workflow. The creation SHA now exists and is
   readable, so `C2`'s input exists.
2. The four determining tasks dispatch that one workflow. Four run IDs and URLs
   now exist, so `C3`'s input exists.
3. `177.003-T` lands the findings artifact and deletes the workflow in one
   commit. The removal SHA now exists, so `C4`'s input exists.
4. `177.007-T` observes that commit as the current tip, confirms the path
   absent and the tree clean, and writes all eight lines — **every one of them
   from a value that already existed before the write**. So `C1` and `C5`'s
   inputs exist, and `C5`'s `observed_tip` equals the `C4` removal commit,
   which satisfies the descendant-or-equal relation exactly.
5. `177.006-T` observes the current tip — now the evidence commit, whose tree
   still lacks the workflow and whose working tree is clean before the
   evaluator stages anything — so `C6` holds; then `C1`–`C5` hold against the
   repository.

Cleanup therefore resolves `CLEANUP_PROVEN` on the **first** emission. With all
seven ledger rows `DETERMINED`, the unit composes to `ISOLATION_CHARACTERIZED`
with **no self-referential field, no waiver, no guessed SHA and no corrective
cycle**. Nothing in this derivation makes the pass state easier to reach on bad
input: `C6` is still an independent observation of the current tip, and the
precedence order still places cleanup above the pass state.

**Absence of the whole block is `CLEANUP_FAILED | cleanup=EVIDENCE_MISSING`,
never `ISOLATION_NOT_OBSERVED`** — the coverage ledger may be complete and
correct while the cleanup evidence is simply missing, and those are different
facts that must not collapse into one token.

**The cleanup check is local, offline and credential-free.** Every limb reads
the local repository at the branch tip. It performs no network request,
requires no credential, and runs after every determining task has reported, so
it neither weakens nor interacts with the I1 gate or the
acquisition-then-no-network model.

**`181-S` still owns every durable committed CI surface.** This workflow is a
spike-owned, dispatch-only, transient surface with a declared removal owner and
a declared removal point. It is not a CI capability, nothing depends on it, and
it does not survive the unit that created it.

## Deliverable

`docs/spikes/2026-09-18-conformance-isolation-findings.md`, listing I1–I7 with
a verdict and either the supporting mechanism and observation or the blocking
reason, plus the completed coverage ledger below.

A second, single-line artifact,
`docs/spikes/2026-09-18-conformance-isolation-i1-gate.md`, is written by
`177.004-T` and read by `177.005-T` and `177.002-T`. It is the executable I1
verdict predicate specified under *I1 gate* above, not a summary of the
findings artifact, and it exists because the gated tasks run **before** the
findings artifact is authored.

**If any of I1–I6 is NOT ACHIEVABLE, the findings artifact must state
explicitly that `181-S` degrades to evidence-and-documentation only.** That
floor is already the decision's position; the spike determines whether the unit
rises above it, never whether it drops below it.

### Evidence handling

The I1 inventory records environment-variable **names only** and the presence
or absence of credential-bearing paths. No value, no token, no key fragment is
written to the findings artifact, to the I1 gate artifact, or to any job log.
An inventory that would require recording a secret value to be meaningful is
itself the finding that I1 is NOT ACHIEVABLE.

The same rule binds the `I1_GATE:` line: it carries a token, a verdict, a short
non-secret mechanism or reason identifier, and a date. The gate is a
**non-secret invariant** by construction — a reader learns whether credential
absence was established, never what any credential is.

### Coverage ledger

`177.003-T` writes this table into the findings artifact; `177.006-T` reads it.
Each property resolves to exactly one of:

* **`DETERMINED`** — a verdict is present *and* the evidence named in the
  Property coverage table is present in the artifact;
* **`NOT DETERMINED — FLOOR INVOKED`** — the determining task reached its
  elapsed bound or was blocked, and the artifact records **all three** of: what
  was attempted, what blocked it, and an explicit written statement that the
  property is **unproven** and that `181-S` is therefore held at the
  evidence-and-documentation floor for that property's scope. All three are
  required; a row carrying fewer is `ABSENT`;
* **`ABSENT`** — anything else, including a verdict supported only by a
  documentation citation, and including a bare "not determined" with no floor
  invocation.

`NOT DETERMINED — FLOOR INVOKED` is **not a pass value and asserts nothing
about the isolation**. It records that the property was not established and
that the consuming unit is consequently confined to the floor. Its only effect
is to distinguish an honestly recorded non-conclusion from silence, which is
what makes successor eligibility decidable rather than guessed.

| Property | Determining task | State | Verdict | Evidence location |
|---|---|---|---|---|
| I1 | `177.004-T` | | | |
| I2 | `177.001-T` | | | |
| I3 | `177.001-T` | | | |
| I4 | `177.002-T` | | | |
| I5 | `177.002-T` | | | |
| I6 | `177.002-T` | | | |
| I7 | `177.005-T` / `177.003-T` | | | |

## Composed-state check

The unit resolves to exactly one of **five** states. Exactly one is a pass. No
state asserts that the isolation floor has been *proven*, and no state is
reachable by silence.

| Field | Value |
|---|---|
| Pass state | `ISOLATION_CHARACTERIZED` — every property I1–I7 is `DETERMINED` in the coverage ledger (an assigned determining task, a verdict, and the named evidence) **and** cleanup resolves to `CLEANUP_PROVEN`. This is the only pass state |
| Qualified state | `ISOLATION_FLOOR_ONLY` — no property is `ABSENT`, at least one is `NOT DETERMINED — FLOOR INVOKED`, and cleanup resolves to `CLEANUP_PROVEN`. **Not a pass.** The unqualified properties are unproven and are recorded as unproven. **A CLOSED I1 gate lands here by construction** — see *I1 gate* above |
| Cleanup-failed state | `ISOLATION_CLEANUP_FAILED` — cleanup resolves to `CLEANUP_FAILED` for any reason in the vocabulary above. **Not a pass**, whatever the ledger says. This is the state that expresses *evidence complete, spike not closed* |
| Fail state | `ISOLATION_UNDETERMINED` — one or more properties is `ABSENT`, named individually |
| Not-observed state | `ISOLATION_NOT_OBSERVED` — the findings artifact does not exist, exists without a completed coverage ledger, or carries more than one `COMPOSED_STATE:` line. Distinct from `ISOLATION_UNDETERMINED` and never a pass |
| Producer | `docs/spikes/2026-09-18-conformance-isolation-findings.md` (created in `183-S` by `177.003-T`), whose final line is the verdict token written by `177.006-T` |
| Consumer | `docs/plans/2026-09-18-safe-close-conformance-plan.md` (`181-S`), which reads the verdict token before harvest |
| Activation commit | None — the spike activates nothing. The gate is read at `181-S` harvest time |

**Precedence makes the resolution a total function.** `177.006-T` evaluates the
five states in this order and emits the **first** that matches, so exactly one
state is reachable for any input:

1. `ISOLATION_NOT_OBSERVED` — artifact missing, unparseable, ledger-less, or
   carrying more than one `COMPOSED_STATE:` line;
2. `ISOLATION_UNDETERMINED` — any ledger row resolves to `ABSENT`;
3. `ISOLATION_CLEANUP_FAILED` — cleanup is not `CLEANUP_PROVEN`;
4. `ISOLATION_FLOOR_ONLY` — no row `ABSENT`, at least one floor-invoked;
5. `ISOLATION_CHARACTERIZED` — all seven rows `DETERMINED`.

**`ISOLATION_CHARACTERIZED` is therefore structurally unreachable while the
probe workflow is present at the branch tip, or while its creation, dispatch or
removal evidence is missing, malformed or inconsistent** — the pass state sits
below the cleanup test in the precedence order, so no ledger, however complete,
can reach it past a `CLEANUP_FAILED` resolution. This is the same shape as the
I1 gate's guarantee: a structural consequence rather than a rule to remember.
It is equally the case that **the pass state IS reachable on one normal run**
when cleanup genuinely holds — see the derivation under *The cleanup
predicate*. Unreachable-on-bad-input and reachable-on-good-input are both
required; revision 5 had only the first.

A partially-classified result is never a partial pass. An unclassified property
would be inherited by `181-S` as an assumption, which is the failure mode this
whole redesign exists to stop.

### Successor eligibility, stated per state

This table is the whole of `181-S`'s harvest authority. It is stated here so
`181-S` reads an eligibility rule rather than inferring one from two sentences
that disagree.

| State | May `181-S` harvest? | What it may harvest |
|---|---|---|
| `ISOLATION_CHARACTERIZED` | Yes | Every task the findings support. Whether the unit rises above the floor is decided by the *verdicts*, not by the gate |
| `ISOLATION_FLOOR_ONLY` | Yes, **floor-only** | Only the evidence-and-documentation floor tasks. No task that assumes, relies on, or asserts an unproven property may be harvested, and the findings artifact names which properties those are |
| `ISOLATION_CLEANUP_FAILED` | **No** | Nothing. The spike is unclosed. The remedy is inside this unit and is cheap: remove the workflow from the branch tip if it survives, have `177.007-T` re-emit a complete and consistent cleanup evidence block against the removal commit, and re-run `177.006-T`, which **replaces** the verdict line. Unlike `ISOLATION_UNDETERMINED` this needs no further determining run and no waiver, because no property observation is missing |
| `ISOLATION_UNDETERMINED` | **No** | Nothing. Harvest is blocked outright until a further determining run or an explicit, recorded operator waiver resolves every `ABSENT` row |
| `ISOLATION_NOT_OBSERVED` | **No** | Nothing. There is no observation to read |

**Fail-closed default.** Any ledger row that is not affirmatively
`DETERMINED` or `NOT DETERMINED — FLOOR INVOKED` is `ABSENT`; any cleanup
result that is not affirmatively `CLEANUP_PROVEN` is `CLEANUP_FAILED`; and any
artifact that is missing, unparseable, or carries no verdict line is
`ISOLATION_NOT_OBSERVED`. Silence never produces eligibility.

**The floor is never presented as proven.** `002-C` stays `blocked` under every
one of the five states, and the decision's evidence-and-documentation floor for
`181-S` is unchanged by any of them. What differs between states is only
whether `181-S` may harvest, and how much — never what the isolation is known
to do. `ISOLATION_FLOOR_ONLY` in particular records an *absence of knowledge*
about the unqualified properties; it does not record that the floor was
achieved.

**The transition is executable and auditable.** `177.006-T` performs it
mechanically, in four checks, in this order:

1. **Coverage.** Every property I1–I7 has an assigned determining task in the
   Property coverage table, and that task is a **determining** task, never
   `177.003-T` alone and never `177.007-T`, which determines nothing. A
   property whose only assignment is an authoring or evidence-emission task
   fails this check outright.
2. **Evidence.** Every property's ledger row resolves to `DETERMINED`,
   `NOT DETERMINED — FLOOR INVOKED`, or `ABSENT` by the definitions above.
3. **I1 gate.** The observed `I1_GATE` token transcribed into the findings
   artifact is read, and a `DETERMINED` verdict on a gated property under a
   CLOSED gate is itself a fail — see *I1 gate*, H13 and R10.
4. **Cleanup.** The cleanup predicate `C1`–`C6` is evaluated over the block
   `177.007-T` wrote, resolving to `CLEANUP_PROVEN` or `CLEANUP_FAILED` with a
   reason token — see *The cleanup predicate*, H15, H16, R11 and R12.

It then writes exactly one verdict line to the findings artifact. The artifact
carries **exactly one** `COMPOSED_STATE:` line at all times: a re-run
**replaces** that line rather than appending beside it, and more than one such
line is `ISOLATION_NOT_OBSERVED`.

```text
COMPOSED_STATE: ISOLATION_CHARACTERIZED | determined=7 | floor_invoked=0 | absent=0 | cleanup=PROVEN | checked=2026-09-DD
```

```text
COMPOSED_STATE: ISOLATION_FLOOR_ONLY | determined=<n> | floor_invoked=<m> | absent=0 | floor_properties=I<x>,I<y> | cleanup=PROVEN | checked=2026-09-DD
```

```text
COMPOSED_STATE: ISOLATION_CLEANUP_FAILED | determined=<n> | floor_invoked=<m> | absent=0 | cleanup=<reason> | workflow_path=.github/workflows/spike-177-isolation-probe.yml | checked=2026-09-DD
```

```text
COMPOSED_STATE: ISOLATION_UNDETERMINED | absent=<n> | properties=I<x>,I<y>
```

Each form names the properties at issue, so a reader can check the verdict
against the ledger without re-running the spike. A verdict line whose counts
disagree with the ledger is itself a fail, and the counts must sum to 7. In the
`ISOLATION_CLEANUP_FAILED` form `<reason>` is exactly one of
`WORKFLOW_PRESENT_AT_TIP`, `TIP_UNOBSERVABLE`, `EVIDENCE_MISSING`,
`EVIDENCE_MALFORMED` or `EVIDENCE_INCONSISTENT`; the two passing-shape forms
carry `cleanup=PROVEN` and no other value is valid in them.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Hosted runners cannot deny egress post-acquisition | This is a *conclusion*, so I2 resolves `DETERMINED` with a `NOT ACHIEVABLE` verdict and the gate passes normally. `181-S` degrades to evidence-and-documentation only, which the decision already names as the floor. `002-C` stays blocked either way, so no downstream record becomes false. |
| R2 | The spike drifts into building the fixtures | Deliverable is a document; no fixture task exists in this unit, and `181-S` owns all four fixtures. |
| R3 | A property is recorded ACHIEVABLE on a mechanism that is not actually exercised | Each verdict must cite the mechanism and the observation that demonstrated it, not a documentation reference alone. The coverage gate resolves a documentation-only verdict to `ABSENT`. |
| R4 | A declared property has no determining task, so the pass state is unreachable | Every property carries an assigned determining task in the Property coverage table, and `177.006-T` checks that assignment structurally before it checks evidence. The authoring task determines nothing. |
| R5 | The I7 rule is re-derived from assumption, reproducing `B6` | `177.005-T` performs one real acquisition and records the observed redirect chain. `177.003-T` reads the rule off that record; it may not invent one. An I7 row with no recorded chain is `ABSENT`. |
| R6 | The I1 inventory leaks a credential into the findings artifact or a job log | Names-only recording is binding. An inventory that would require a value to be meaningful is itself a NOT ACHIEVABLE verdict for I1. |
| R7 | The acquisition task is mistaken for a conformance run | `177.005-T` acquires and observes transport behaviour only. It does not execute the acquired binary, and no task in this unit does. |
| R8 | A probe or acquisition job runs before credential absence is determined | Enforced by a **verdict predicate**, not by ordering alone. `177.004-T` emits the `I1_GATE:` line; `177.005-T` and `177.002-T` read it as their first action and perform no acquisition, download, handle creation or substitution attempt unless the token is `ACHIEVABLE`. The `blocks` edges in `item_deps` sequence the tasks and are **not** offered as the guarantee, because they clear on completion. `177.001-T` inherits the precedence through `177.005-T`. Every affected task record states the gate as a fail-closed precondition rather than as an edge. |
| R9 | A determining task times out and the result is read as either a pass or a silent gap | Neither is reachable. A timed-out property is `NOT DETERMINED — FLOOR INVOKED` only if it records what was attempted, what blocked it, and the floor invocation in writing; otherwise it is `ABSENT`. The first yields `ISOLATION_FLOOR_ONLY`, which is explicitly not a pass and permits only floor-only harvest; the second yields `ISOLATION_UNDETERMINED`, which blocks harvest outright. |
| R10 | `177.004-T` completes with I1 `NOT ACHIEVABLE` or `NOT DETERMINED — FLOOR INVOKED`, the `blocks` edge clears, and the gated tasks run anyway | This is the attempt-03 `K1` defect and it is closed by making the predicate a **verdict** rather than a completion. Both gated tasks fail closed on every non-`ACHIEVABLE` outcome and on every unreadable, absent, malformed or multi-line gate file, record their properties `NOT DETERMINED — FLOOR INVOKED` naming `I1` as the blocker, and force `ISOLATION_FLOOR_ONLY`. `ISOLATION_CHARACTERIZED` is structurally unreachable while the gate is CLOSED, because it requires all seven properties `DETERMINED`. A gated task that acquires or probes on a CLOSED gate, or that records a `DETERMINED` verdict for a gated property, is a defect and a finding. |
| R11 | The committed probe workflow is left on the branch, or fires outside the spike | It has one owner for creation (`177.004-T`), one exact path, one removal owner and point (`177.003-T`, at spike close, in the findings commit), one cleanup-evidence owner (`177.007-T`, in a separate commit afterwards), and a fixed-shape `CLEANUP_` evidence block recorded in the findings artifact. It is `workflow_dispatch`-only, so it never fires on `push`, `pull_request` or `schedule`. **The leftover case is closed by a predicate, not by a note.** `177.006-T` evaluates checks `C1`–`C6`, independently re-observing the current branch tip rather than trusting the recorded observation, and a branch still carrying the workflow — or evidence that is missing, malformed or inconsistent with the repository — resolves cleanup to `CLEANUP_FAILED` and forces the composed state to `ISOLATION_CLEANUP_FAILED`, which **withholds the pass and blocks `181-S` harvest outright**. Through revision 4 this risk was mitigated only by a prose expectation the composed-state vocabulary could not express; that was attempt 04 finding `K3` (P2). |
| R12 | The cleanup evidence block cannot be written where it is mandated to be written, so the predicate fails on a correct execution | This was attempt 05 finding `L1` (P2): the block was mandated to be written in the removal commit while `CLEANUP_REMOVED_COMMIT` and `CLEANUP_TIP_OBSERVATION` carried values that only that commit's own creation defines, making a conformant first emission impossible and forcing at least one spurious `ISOLATION_CLEANUP_FAILED` cycle. It is closed by **ordering, not by relaxation**: `177.003-T` removes and commits; `177.007-T` then observes that already-existing commit and writes the block in a separate evidence commit, so every recorded value exists before it is recorded. `observed_tip` names the tip that was observed — the removal commit, the parent of the evidence commit — and no field names the commit that records it. The write is atomic: if any value cannot be observed, no block is written, which resolves `EVIDENCE_MISSING` and remains fail-closed. A guessed or pre-computed SHA is forbidden and would resolve `EVIDENCE_INCONSISTENT`. No check was weakened and `C6` remains an independent observation of the current tip. |

## Hardening review

Adversarial pass over this spike's failure modes and boundaries.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Can a spike that executes an external binary be unsafe in itself? | Yes, which is why this spike executes none. It characterizes isolation **before** any conformance run, acquires an asset without running it, and probes a handle without executing what the handle refers to. Its output is a document. |
| H2 | Is a property verified by reading CI documentation? | No. Each verdict must cite the mechanism and an observation that demonstrated it. Documentation alone resolves to `ABSENT`, which yields `ISOLATION_UNDETERMINED`. |
| H3 | What stops the spike from growing into the implementation? | The deliverable is a findings artifact, the unit contains no fixture or CI-definition task, `181-S` owns all of those, and every task carries an individual elapsed bound with a recorded-and-stop rule. |
| H4 | Is a partially classified result usable? | Only in the one shape that records its own limits. A property left `ABSENT` is a fail: it would be inherited by `181-S` as an assumption, which is the frame error this redesign exists to eliminate. A property recorded `NOT DETERMINED — FLOOR INVOKED` carries what was attempted, what blocked it, and the floor invocation in writing, which yields `ISOLATION_FLOOR_ONLY` — not a pass, and eligible only for floor-only harvest. |
| H5 | Does every declared property have a task that determines it, and does every task's output name the property it closes? | Yes, and it is checked structurally rather than assumed. The Property coverage table assigns each of I1–I7 a determining task and an evidence shape, every task's title names the properties it closes, and `177.006-T` checks the assignment before it checks the evidence. This question exists because the previous revision's hardening pass interrogated scope, evidence quality and partial results without ever asking whether the decomposition could reach its own pass state — and it could not. |
| H6 | Can the authoring task absorb a property that has no determining task? | No. `177.003-T` transcribes verdicts and reads the I7 rule off a recorded chain; it determines nothing. An authoring-derived verdict rests on assertion, which R3 and H2 have already ruled insufficient, and the coverage check in `177.006-T` rejects it structurally. |
| H7 | Is the I5/I6 probe itself an execution of the untrusted binary? | No. Probing a file handle and attempting a substitution against it is not executing the file's contents. The boundary is stated here rather than left implicit, and I1's determination is what keeps the probe honest: a probe job that carried credentials would be a privileged process handling an untrusted artifact even without executing it. That premise is **enforced by a verdict predicate**, not assumed and not merely ordered — see H9 and H12. |
| H8 | Does an unachievable property weaken the security model? | No. The model is a constraint, not a question. An unachievable property moves `181-S` to the evidence-and-documentation floor; it never relaxes the requirement. |
| H9 | Is the I1-before-probe ordering that H7 relies on actually enforced, or only asserted? | Enforced, and by two mechanisms that do different jobs. **Ordering**: `177.004-T` is a `blocks` predecessor of `177.002-T` (the containment probe) and of `177.005-T` (the untrusted acquisition) in `item_deps`, and `177.001-T` inherits it transitively through `177.005-T`. **Safety**: the `I1_GATE:` verdict predicate that both gated tasks evaluate as their first action. Every affected task record states both rather than claiming independence. This question exists because a previous revision made H7's answer rest on an ordering that the task table, three task records and `item_deps` all denied. |
| H12 | Does the `blocks` edge by itself carry the probe-safety guarantee? | **No, and treating it as though it did was the attempt-03 `K1` defect.** A `blocks` edge is a predicate over predecessor **completion**, and `177.004-T` completes on three outcomes: `DETERMINED`/ACHIEVABLE, `DETERMINED`/NOT ACHIEVABLE (R6), and `NOT DETERMINED — FLOOR INVOKED` at the 90-minute bound (R9). Two of the three leave credential absence unverified or affirmatively falsified, and all three clear the edge. The guarantee is therefore carried by a **verdict predicate** inside the gated tasks: they read the `I1_GATE:` line first and fail closed to `NOT DETERMINED — FLOOR INVOKED` naming `I1` on anything but `ACHIEVABLE`, including an absent, unreadable, malformed or multi-line gate file. The edge remains — it is how the gate artifact is guaranteed to exist before the read — but it is never offered as the safety argument. See *I1 gate*, R8 and R10. |
| H13 | Can a CLOSED I1 gate still produce a pass? | No, structurally. A CLOSED gate leaves at least one of I2, I4, I5, I6 or I7 `NOT DETERMINED — FLOOR INVOKED`, and `ISOLATION_CHARACTERIZED` — the only pass state — requires **all seven** properties `DETERMINED`. The unit therefore composes to `ISOLATION_FLOOR_ONLY` (or to `ISOLATION_CLEANUP_FAILED`, if cleanup also fails), neither of which is a pass; `ISOLATION_FLOOR_ONLY` asserts nothing about the isolation and authorizes only floor-only harvest in `181-S`, and `ISOLATION_CLEANUP_FAILED` authorizes nothing. If a gated task records fewer than the three required floor-invocation parts, its row is `ABSENT` and the unit composes to `ISOLATION_UNDETERMINED`, which blocks harvest outright. There is no path to a pass. |
| H15 | Is the branch-cleanliness expectation H14 states an executable predicate, or a claim? | **It is now a predicate; through revision 4 it was a claim, which was attempt 04 finding `K3` (P2).** The composed states were defined exhaustively as functions of the seven-entry coverage ledger, in which branch state appeared nowhere and for which no verdict-line field existed — so an all-`DETERMINED` ledger on a branch still carrying the probe workflow forced `ISOLATION_CHARACTERIZED` while `177.006-T`'s record forbade a pass, and no token could express the outcome the record demanded. Revision 5 closes this by giving cleanup a **sole writer** of the eight-line `CLEANUP_` block, a **sole evaluator** (`177.006-T`, checks `C1`–`C6`, with `C6` independently re-observing the branch tip rather than trusting the artifact's own word), a **fifth composed state** `ISOLATION_CLEANUP_FAILED` with its own line form and five-token reason vocabulary, a **declared precedence** placing the cleanup test above both `ISOLATION_FLOOR_ONLY` and `ISOLATION_CHARACTERIZED`, and a **per-state eligibility row** that blocks `181-S` harvest outright. That sole writer was `177.003-T` at revision 5 and is `177.007-T` at revision 6; whether the block could be *written at all* at its revision-5 write point is a separate question — see H16. The pass state is therefore unreachable while the exact path is present at the branch tip or its creation, dispatch or removal evidence is missing, malformed or inconsistent. The check is local, offline and credential-free, so it neither weakens nor interacts with the I1 gate. |
| H16 | Can the fixed-shape evidence block H15 introduces actually be written at the point where it is mandated to be written? | **Not as revision 5 specified it, and that was attempt 05 finding `L1` (P2).** H15 asserted the cleanup evidence was producible; it never derived that it was. Two of the eight lines — `CLEANUP_REMOVED_COMMIT` and `CLEANUP_TIP_OBSERVATION` — carried values that only the mandated write point's own creation defines. A commit's identity is a function of its content, so a commit cannot contain its own SHA, and a working tree cannot be observed clean from inside the staged change that makes it clean. `C4` and `C5` were unsatisfiable on a first emission, cleanup resolved `CLEANUP_FAILED`, and a spurious `ISOLATION_CLEANUP_FAILED` cycle was forced on every execution of the unit as written. Revision 6 closes it by **separating removal from evidence**: `177.003-T` removes and commits and writes no `CLEANUP_` line; `177.007-T` observes the already-existing removal commit and writes the block in its own evidence commit. Every value is observable before it is recorded; `observed_tip` names the tip that was observed rather than the commit that records it; the write is atomic and no SHA may be guessed; and `C6` — the evaluator's independent observation of the **current** tip — remains the final branch-state authority. The generalisable question this adds to the pass is: **for every field of every machine-written record, does a point in the lifecycle exist at which that field's value is already observable?** |
| H14 | Does committing the probe workflow contradict the blast-radius and rollback statements? | It did, and that was the attempt-03 `K2` defect; both statements are now truthful. GitHub executes only workflows that exist on a branch, so the probe workflow **is committed** and the plan says so. *Probe workflow lifecycle* gives it one owning task (`177.004-T`), one exact path (`.github/workflows/spike-177-isolation-probe.yml`), one removal owner and point (`177.003-T`, at spike close, in the findings commit), a rollback (revert the single creation commit), and an eight-line `CLEANUP_` evidence block as removal evidence. Whether that expectation is *enforced* rather than merely stated is a separate question — see H15. `181-S` still owns every **durable** committed CI surface; this one is dispatch-only, carries a minimal `permissions:` block and no secrets, and does not survive its unit. |
| H10 | Can the gate pass with nothing determined? | No. `ISOLATION_CHARACTERIZED` requires all seven properties `DETERMINED` **and** `CLEANUP_PROVEN`, and it is the only pass state. An all-fallback ledger is `ISOLATION_FLOOR_ONLY`, which is explicitly not a pass and authorizes only floor-only harvest; an unclosed branch is `ISOLATION_CLEANUP_FAILED`, which authorizes nothing; and an empty or missing ledger is `ISOLATION_NOT_OBSERVED`, which authorizes nothing. |

### Blast radius

**One tracked surface is mutated, transiently, and it is named.** The spike
commits `.github/workflows/spike-177-isolation-probe.yml` to
`chore/stage-176-s-workflow-defects` so GitHub will run the determining jobs at
all, and `177.003-T` deletes it at spike close in the same commit that lands
the findings artifact. `177.007-T` then records the lifecycle evidence for that
removal in a separate, documents-only commit. See *Probe workflow lifecycle*
above for the owner, dispatch model, removal point, evidence point, rollback
and branch-cleanliness evidence, and *The cleanup predicate* for the checks
that make removal an enforced outcome rather than a stated intention.
Describing that workflow as uncommitted would be false: GitHub executes only
workflows that exist on a branch.

Apart from that one path and its removal, the spike produces documents and
activates nothing. It installs nothing, registers nothing, and mutates no other
tracked surface outside `docs/spikes/`. The workflow is dispatch-only, carries
an explicit minimal `permissions:` block, is passed no secrets, and never fires
on `push`, `pull_request` or `schedule`.

Its remaining risk is **decisional** — a wrong finding propagates into
`181-S`'s isolation design — and **operational** in one narrow respect: the
determining tasks run CI jobs that acquire a real external asset and probe
containment. The job that does so carries no credentials, executes nothing it
acquires, and leaves no surviving state.

**The credential claim in that sentence is load-bearing, so it is enforced by a
verdict rather than by an ordering.** `177.004-T` determines I1 and emits the
`I1_GATE:` line; `177.005-T` (the acquisition) and `177.002-T` (the containment
probe) each read that line as their first action and **do not acquire or probe
at all** unless its token is `ACHIEVABLE`. The `blocks` edges in `item_deps`
sequence these tasks but do **not** carry the guarantee, because a `blocks`
edge clears on predecessor completion and `177.004-T` completes on
`NOT_ACHIEVABLE` and `FLOOR_INVOKED` as well. On a CLOSED gate the gated
properties are recorded `NOT DETERMINED — FLOOR INVOKED` naming `I1`, and the
unit composes to `ISOLATION_FLOOR_ONLY` — or to `ISOLATION_CLEANUP_FAILED` if
the probe workflow also survives at the branch tip — neither of which is a
pass. See *I1 gate*, H7, H9, H12, H15, R8, R10 and R11.

### Rollback

**Two things can need undoing, and both have a declared owner.**

The probe workflow: `177.003-T` deletes
`.github/workflows/spike-177-isolation-probe.yml` at spike close, and removes
it anyway if the spike aborts before close; `177.007-T` records the evidence of
that removal afterwards, against the commit that performed it. Rollback is
`git revert` of the single creation commit, or deletion of the single added
path — there is no other change to undo, and no other workflow was touched.
**Removal is verified, not assumed:** `177.006-T`'s cleanup predicate
re-observes the current branch tip itself, and a surviving workflow forces
`ISOLATION_CLEANUP_FAILED`, which withholds the pass and blocks `181-S` harvest
until the removal is actually performed, the `CLEANUP_` evidence block
re-emitted by `177.007-T`, and `177.006-T` re-run.

Everything else: not applicable. No further workspace state changes, and the
findings artifact and the I1 gate artifact are additive documents under
`docs/spikes/`. `181-S` still owns every **durable** committed CI surface; the
probe workflow is transient, dispatch-only, and does not survive the unit that
created it.

### Verification floor

Every property is recorded only with the evidence shape named in the Property
coverage table. A verdict without that evidence is `ABSENT`. The gate verdict
is written by a task whose only job is to write it, and its counts are
checkable against the ledger by a reader who did not run the spike.
