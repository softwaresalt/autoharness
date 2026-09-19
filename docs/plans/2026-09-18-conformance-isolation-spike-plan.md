---
title: "Bounded spike: network-denied Linux container isolation for external binary conformance"
description: "Time-boxed spike determining whether the isolation required to execute an untrusted external release binary is achievable on this repository's CI: no credentials of any kind in the job environment, network egress denied after asset acquisition completes, repository absent or mounted read-only, disposable mounts, a TOCTOU-resistant handle across the verify-execute boundary, hardlink and symlink substitution resistance, and a redirect rule derived from observed acquisition behaviour. Every property has an assigned determining task that records objective evidence, including credential absence, which is determined by inspecting the actual job environment, and the redirect rule, which is derived from one observed release-asset acquisition rather than from assumption. A coverage gate checks that every property has a determining task and captured evidence before ISOLATION_CHARACTERIZED is emitted. No conformance fixture and no production code ships. Gates the reduced SAFE_CLOSE unit."
doc_type: plan
source: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
date: 2026-09-18
plan_id: conformance-isolation-spike
plan_path: docs/plans/2026-09-18-conformance-isolation-spike-plan.md
plan_role: active
revision: 2
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "verdict is null because no independent reviewer has judged revision 2. REMEDIATED-PENDING-REVIEW is recorded under disposition, where it belongs: it states what Stage produced, never what a reviewer found. Revision 2 is the product of one authorized Stage remediation cycle against attempt 01, which returned FAIL/BLOCKED on revision 1. Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 2
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
hardening_rationale: "The spike researches the containment boundary for executing an untrusted third-party binary. Getting the question set wrong produces a foundation plan that under-specifies isolation, so the question set itself warrants adversarial review even though the spike ships no code. The hardening pass includes a structural coverage question, because attempt 01 found a declared property with no determining task and the original pass did not ask whether one existed."
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
| `177.003-T` | Author the findings artifact; transcribe every verdict and read off the I7 rule | — | XS | low | 45 min |
| `177.006-T` | Coverage and composed-state validation; emit the gate verdict | — | XS | low | 20 min |

Sequence: `177.005-T` → `177.001-T`. `177.004-T` and `177.002-T` are
independent of both and of each other. All four determining tasks block
`177.003-T`, which blocks `177.006-T`.

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
property is recorded NOT DETERMINED with what was attempted, which is a
legitimate and useful outcome; it is not a reason to extend.

## Deliverable

`docs/spikes/2026-09-18-conformance-isolation-findings.md`, listing I1–I7 with
a verdict and either the supporting mechanism and observation or the blocking
reason, plus the completed coverage ledger below.

**If any of I1–I6 is NOT ACHIEVABLE, the findings artifact must state
explicitly that `181-S` degrades to evidence-and-documentation only.** That
floor is already the decision's position; the spike determines whether the unit
rises above it, never whether it drops below it.

### Evidence handling

The I1 inventory records environment-variable **names only** and the presence
or absence of credential-bearing paths. No value, no token, no key fragment is
written to the findings artifact or to any job log. An inventory that would
require recording a secret value to be meaningful is itself the finding that
I1 is NOT ACHIEVABLE.

### Coverage ledger

`177.003-T` writes this table into the findings artifact; `177.006-T` reads it.
Each property resolves to exactly one of:

* **`DETERMINED`** — a verdict is present *and* the evidence named in the
  Property coverage table is present in the artifact;
* **`NOT DETERMINED`** — the determining task reached its elapsed bound or was
  blocked, and the artifact records what was attempted and what blocked it;
* **`ABSENT`** — anything else, including a verdict supported only by a
  documentation citation.

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

| Field | Value |
|---|---|
| Pass state | `ISOLATION_CHARACTERIZED` — every property I1–I7 is `DETERMINED` in the coverage ledger: an assigned determining task, a verdict, and the named evidence |
| Fail state | `ISOLATION_UNDETERMINED` — one or more properties is `NOT DETERMINED` or `ABSENT`, named individually |
| Not-observed state | `ISOLATION_NOT_OBSERVED` — the findings artifact does not exist, or exists without a completed coverage ledger. Distinct from `ISOLATION_UNDETERMINED` and never a pass |
| Producer | `docs/spikes/2026-09-18-conformance-isolation-findings.md` (created in `183-S` by `177.003-T`), whose final line is the verdict token written by `177.006-T` |
| Consumer | `docs/plans/2026-09-18-safe-close-conformance-plan.md` (`181-S`), which reads the verdict token before harvest |
| Activation commit | None — the spike activates nothing. The gate is read at `181-S` harvest time |

A partially-classified result is a **fail**, not a partial pass. An
unclassified property would be inherited by `181-S` as an assumption, which is
the failure mode this whole redesign exists to stop.

**The transition is executable and auditable.** `177.006-T` performs it
mechanically, in two checks:

1. **Coverage.** Every property I1–I7 has an assigned determining task in the
   Property coverage table, and that task is a **determining** task, never
   `177.003-T` alone. A property whose only assignment is the authoring task
   fails this check outright.
2. **Evidence.** Every property's ledger row is `DETERMINED`.

It then appends a single verdict line to the findings artifact:

```text
COMPOSED_STATE: ISOLATION_CHARACTERIZED | determined=7 | undetermined=0 | checked=2026-09-DD
```

or

```text
COMPOSED_STATE: ISOLATION_UNDETERMINED | undetermined=<n> | properties=I<x>,I<y>
```

`ISOLATION_UNDETERMINED` blocks `181-S` harvest and names which properties are
open, so a reader can check the verdict against the ledger without re-running
the spike. A verdict line whose count disagrees with the ledger is itself a
fail.

**`ISOLATION_UNDETERMINED` is not a blocker on the unit's usefulness.** The
floor stands either way: `181-S` degrades to evidence-and-documentation only
and `002-C` stays blocked. What the fail state prevents is `181-S` inheriting
an undetermined property as an assumption.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Hosted runners cannot deny egress post-acquisition | `181-S` degrades to evidence-and-documentation only, which the decision already names as the floor. `002-C` stays blocked either way, so no downstream record becomes false. |
| R2 | The spike drifts into building the fixtures | Deliverable is a document; no fixture task exists in this unit, and `181-S` owns all four fixtures. |
| R3 | A property is recorded ACHIEVABLE on a mechanism that is not actually exercised | Each verdict must cite the mechanism and the observation that demonstrated it, not a documentation reference alone. The coverage gate resolves a documentation-only verdict to `ABSENT`. |
| R4 | A declared property has no determining task, so the pass state is unreachable | Every property carries an assigned determining task in the Property coverage table, and `177.006-T` checks that assignment structurally before it checks evidence. The authoring task determines nothing. |
| R5 | The I7 rule is re-derived from assumption, reproducing `B6` | `177.005-T` performs one real acquisition and records the observed redirect chain. `177.003-T` reads the rule off that record; it may not invent one. An I7 row with no recorded chain is `ABSENT`. |
| R6 | The I1 inventory leaks a credential into the findings artifact or a job log | Names-only recording is binding. An inventory that would require a value to be meaningful is itself a NOT ACHIEVABLE verdict for I1. |
| R7 | The acquisition task is mistaken for a conformance run | `177.005-T` acquires and observes transport behaviour only. It does not execute the acquired binary, and no task in this unit does. |

## Hardening review

Adversarial pass over this spike's failure modes and boundaries.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Can a spike that executes an external binary be unsafe in itself? | Yes, which is why this spike executes none. It characterizes isolation **before** any conformance run, acquires an asset without running it, and probes a handle without executing what the handle refers to. Its output is a document. |
| H2 | Is a property verified by reading CI documentation? | No. Each verdict must cite the mechanism and an observation that demonstrated it. Documentation alone resolves to `ABSENT`, which yields `ISOLATION_UNDETERMINED`. |
| H3 | What stops the spike from growing into the implementation? | The deliverable is a findings artifact, the unit contains no fixture or CI-definition task, `181-S` owns all of those, and every task carries an individual elapsed bound with a recorded-and-stop rule. |
| H4 | Is a partially classified result usable? | No — it is a fail. An unclassified property would be inherited by `181-S` as an assumption, which is the frame error this redesign exists to eliminate. |
| H5 | Does every declared property have a task that determines it, and does every task's output name the property it closes? | Yes, and it is checked structurally rather than assumed. The Property coverage table assigns each of I1–I7 a determining task and an evidence shape, every task's title names the properties it closes, and `177.006-T` checks the assignment before it checks the evidence. This question exists because the previous revision's hardening pass interrogated scope, evidence quality and partial results without ever asking whether the decomposition could reach its own pass state — and it could not. |
| H6 | Can the authoring task absorb a property that has no determining task? | No. `177.003-T` transcribes verdicts and reads the I7 rule off a recorded chain; it determines nothing. An authoring-derived verdict rests on assertion, which R3 and H2 have already ruled insufficient, and the coverage check in `177.006-T` rejects it structurally. |
| H7 | Is the I5/I6 probe itself an execution of the untrusted binary? | No. Probing a file handle and attempting a substitution against it is not executing the file's contents. The boundary is stated here rather than left implicit, and I1's determination is what keeps the probe honest: a probe job that carried credentials would be a privileged process handling an untrusted artifact even without executing it. |
| H8 | Does an unachievable property weaken the security model? | No. The model is a constraint, not a question. An unachievable property moves `181-S` to the evidence-and-documentation floor; it never relaxes the requirement. |

### Blast radius

None in the workspace: the spike produces a document and activates nothing. It
installs nothing, registers nothing, and mutates no tracked surface outside
`docs/spikes/`.

Its risk is **decisional** — a wrong finding propagates into `181-S`'s
isolation design — and **operational** in one narrow respect: the determining
tasks run CI jobs that acquire a real external asset and probe containment. The
job that does so carries no credentials (I1 is determined before any probe job
is trusted to be safe), executes nothing it acquires, and leaves no surviving
state.

### Rollback

Not applicable. No workspace state changes; the findings artifact is additive.
Any CI definition written to run a determining task is a throwaway probe, not a
committed workflow, and `181-S` owns every committed CI surface.

### Verification floor

Every property is recorded only with the evidence shape named in the Property
coverage table. A verdict without that evidence is `ABSENT`. The gate verdict
is written by a task whose only job is to write it, and its counts are
checkable against the ledger by a reader who did not run the spike.
