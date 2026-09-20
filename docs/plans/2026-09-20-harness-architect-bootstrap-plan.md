---
title: "BOOTSTRAP-0: one-time installation of the harness-architect actor"
description: "Installs the actor that P-002 and P-004 name, without assuming that actor already exists and without depending on any code-bearing shipment. Resolves the 187-S bootstrap deadlock at its root: 187-S delivered both the actor and the lifecycle automation that invokes it, while itself depending on code-bearing 184-S, so no policy-compliant route existed to execute either. This unit separates the two: it installs ONLY the actor, and registers it in the harness manifest in the same commit. The revision-2/3 bootstrap authority and its CLAIM carve-out are WITHDRAWN IN FULL. The admission path is machine-admissible and, at revision 5, MECHANICALLY ORDERED: the harness-architect procedure HAS BEEN EXECUTED once from its authoritative template as this unit's producer-side entry precondition PRE-0; both P-004 channels were observed and recorded in a committed immutable evidence artifact; and only afterwards were the four harness-ready labels applied, in a commit whose parent is the labels-absent base the evidence was produced against. Evidence precedes label application in git history, which is a fact a reader can re-derive rather than a claim a plan asserts. No exemption, no carve-out, no expiring authority, no Ship or gate edit. 187-S keeps the lifecycle automation and becomes ordinary harness-backed work, eligible to be claimed once this unit ships. Every code-bearing implementation shipment in the portfolio gains a dependency on this unit's completion."
doc_type: plan
source: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
date: 2026-09-20
plan_id: harness-architect-bootstrap
plan_path: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
plan_role: active
revision: 5
verdict: null
disposition: ORDERING-REPAIRED-AWAITING-INDEPENDENT-ATTEMPT-05
verdict_note: "THE VERDICT FIELD IS NULL BECAUSE REVISION 5 HAS NOT BEEN INDEPENDENTLY REVIEWED. A DISPOSITION IS NEVER A VERDICT; Stage asserts no PASS and closes no finding of its own judgement. Revision 5 repairs ONE P1 DEFECT that every prior revision carried: the contract asserted that PRE-0 produces P-004 evidence and applies the harness-ready label FROM it, while the four labels were already committed at eabcecc8 and NO durable carrier held any compilation or red-phase observation - the required ordering was asserted in prose and contradicted by the tree. THE REPAIR IS IN THE COMMIT GRAPH, NOT IN PROSE: the labels were withdrawn and committed (labels-absent base 3ad5fcc7); PRE-0 was executed against that base, giving python -m py_compile src/autoharness/cli.py exit 0 and a red-phase run over the declared harness set at 5 failures / 0 errors with every failure carrying HARNESS_ARCHITECT_SURFACE_ABSENT; the evidence was persisted to the immutable artifact docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md; and only then were the labels re-applied, in a DESCENDANT commit. So P-004 evidence PRECEDES label application in history while P-002 queue-building and claiming SEE the labels now. Revision 5 also relocates the durable postcondition carrier from .autoharness/harness-manifest.yaml to that artifact, because D11 authorizes no staging-time manifest edit and PRE-0 is a staging-side act - a postcondition its own author may not write is not a postcondition; the manifest is still written by 182.003-T alone under D11. ONE LIMITATION IS RECORDED RATHER THAN SMOOTHED: the WHOLE-SUITE literal form of P-004's precondition was NOT satisfied at PRE-0 (the unscoped suite returned exit 0, Ran 2344 tests, OK, skipped=54, because the assertion was authored outside the working tree); the form the harness-architect template prescribes at Step 5.2 WAS satisfied, and the whole-suite form is gated at 182.002-T, the first point it is observable. A Stage-executed TARGETED TERMINAL REVIEW of this repair is recorded at docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-targeted-terminal-review-01.md; it is EXPLICITLY NOT an independent attempt, asserts NO verdict and consumes no attempt number. It found P0 0 / P1 0 / P2 0, closed the P1 ordering defect ONLY on machine-re-derivable commit-graph evidence, and raised two non-blocking P3s (C3, C4). REVISION 5 AWAITS INDEPENDENT ATTEMPT 05."
review_manifest: docs/reviews/2026-09-20-harness-architect-bootstrap-plan-review.md
awaiting_attempt: 5
latest_attempt: 4
pre0_status: EXECUTED
pre0_evidence_artifact: docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md
targeted_terminal_review: docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-targeted-terminal-review-01.md
pre0_labels_absent_base: 3ad5fcc7fec87e5306df0f899025a8a1a3cdbbe4
pre0_expected_failure_marker: HARNESS_ARCHITECT_SURFACE_ABSENT
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 5
source_stash_ids:
  - 76EBDE6D
feature_id: 182-F
shipment_id: 188-S
unit_role: bootstrap-precursor
depends_on_shipments: []
gates:
  - 184-S
  - 185-S
  - 186-S
  - 187-S
  - 176-S
  - 178-S
  - 180-S
requires_plan_hardening: true
hardening_rationale: "This unit installs the actor that two live policies name, in a workspace where that actor does not yet exist. The hardening subject is that the bootstrap route is MECHANICALLY ADMISSIBLE rather than narratively excused: that P-004's evidence is genuinely produced by the two commands the policy names, that the harness-ready label Ship's filter reads is REALLY PRESENT on every task record rather than asserted to be unnecessary, and that the generated artifact and its manifest registration move as one atomic unit. An exception that an installed filter cannot see is indistinguishable from the waiver this portfolio has refused four times — which is why this plan declares none. Revision 5 adds the ordering limb the earlier revisions asserted rather than established: the evidence must be shown to PRECEDE the label in the commit graph, not merely claimed to."
tags:
  - bootstrap
  - harness-architect
  - p-002
  - p-004
  - precursor
  - dag-root
---

# BOOTSTRAP-0: one-time installation of the harness-architect actor

## Problem frame

Installed policy `.github/policies/workflow-policies.md` names an actor twice:

> **P-002** — Applies To: `ship` (consumer; harness-architect skill is the producer)
> **P-004** — Applies To: `ship` (via harness-architect skill)

`templates/skills/harness-architect/SKILL.md.tmpl` exists. The workspace
contains eighteen installed skills under `.github/skills/`, and
**`harness-architect` is not one of them.**

`187-S` (feature `181-F`) was written to close this. It cannot, as sequenced:

| # | Fact | Consequence |
|---|---|---|
| 1 | `187-S` delivers both the installed actor *and* the Ship pre-task lifecycle that invokes it | The actor's existence is an output of `187-S` |
| 2 | `187-S`'s own tasks write Python modules under `src/` | They are implementation tasks, so P-004 requires a confirmed red phase and P-002 requires a `harness-ready` label before Ship may claim them |
| 3 | The only declared producer of that label is the actor from fact 1 | `187-S` must consume its own output before producing it |
| 4 | `187-S` **as originally sequenced** additionally declared `depends_on: 184-S`, which is code-bearing | `184-S` needs the same absent actor, so the deadlock was also a graph cycle in the policy sense. That edge is now **withdrawn**: `187-S` declares `188-S` and nothing else, and only `185-S` retains a technical edge on the archived `184-S`. |

Fact 4 alone would be repaired by reversing an edge. **Facts 1–3 would not.**
Reversing `187-S → 184-S` leaves `187-S` still required to bootstrap itself
through an actor that does not exist. This is why edge reversal was rejected.

## Options evaluated

| Option | Verdict |
|---|---|
| Waiver for `187-S` | **Rejected.** Suspends P-004 for exactly the case it exists to catch. Already rejected at decision D4. |
| `--force` flag on the P-004 gate | **Rejected.** An override reachable by the agent it constrains is not a gate. Already rejected at D4. |
| Edit P-002/P-004 to drop the actor | **Rejected.** Deletes the requirement instead of satisfying it. Already rejected at D4. |
| Reverse the `187-S → 184-S` edge | **Rejected.** Repairs fact 4 and leaves facts 1–3 untouched. The self-bootstrap remains. |
| Declare `187-S` exempt by operator note | **Rejected.** An undocumented waiver wearing a different word. |
| Declare a plan-level **claim carve-out** admitting two named task IDs without the label | **Rejected.** Carried at revisions 2–3 and withdrawn: P-002's Enforcement is an installed, mechanical ready-queue filter, and a carve-out written in a plan is invisible to it. See "Why the carve-out was withdrawn". |
| **Split the actor from the automation, and install the actor through the producer-side procedure that P-002 already names** | **CHOSEN** |

## The chosen route

**The actor and the automation are two different deliverables, and only the
first is a bootstrap problem.**

* **This unit (`188-S`) installs the ACTOR only** — it generates
  `.github/skills/harness-architect/SKILL.md` from its authoritative template
  and registers that file in `.autoharness/harness-manifest.yaml` in the same
  commit (decision `D11`). No Python module, no agent-lifecycle edit, no policy
  edit.
* **`187-S` keeps the AUTOMATION** — the harness-surface resolver, the Ship
  pre-task lifecycle phase, and the `HARNESS_READY`/`NO_HARNESS` state
  contract. After this unit, those are ordinary implementation tasks that a
  real installed actor can harness. `187-S` stops being self-referential.

### Why the carve-out was withdrawn

Revisions 2 and 3 admitted `182.001-T` and `182.002-T` to Ship's ready queue
through a plan-declared **claim carve-out**. The current-HEAD review of Push A
found that carve-out **not executable**, and the finding is accepted at its
stated severity without downgrade:

> P-002's Enforcement is mechanical — *"filter ready queue to only tasks
> carrying the `harness-ready` label"* — and its Gate Point is *"queue building
> (Step 2) and task claiming (Step 3)"*. The installed Ship agent contains no
> `188-S` exception and no task-ID exception, and this plan forbids editing
> Ship, P-002, P-004 or any gate. **Backlog and plan prose cannot waive an
> installed filter.** An unlabelled task is simply not admitted, whatever any
> record says about it.

The defect was **structural, not narrative**. Revisions 2–3 placed
*producer-side* work — generating the harness, observing both P-004 channels
and applying the label — inside Ship's *consumer-side* P-002 queue, and then
needed an exception to get it back out. P-002's own `Applies To` row states the
separation: `ship` is the **consumer**; the harness-architect is the
**producer**. The producer is never admitted through Ship's ready-queue filter,
so it never needed an exception in the first place.

Withdrawn in full, and not re-described anywhere: the claim carve-out, the four
execution bounds, the "one-time bootstrap authority" framing, the
non-re-enterability argument built on it, and every exemption, carve-out and
authority-expiry claim. `HARNESS_ARCHITECT_INSTALLED` is **retained**, but
strictly as the composed-state **completion** token of decision `D6` — not as
the expiry of an authority, because this plan declares no authority.

### `PRE-0` — the producer-side entry precondition, **executed**

`PRE-0` is a **completed act with a committed trace**, not a step this plan
asks someone to perform later. The harness-architect procedure was executed
**once**, read directly from its authoritative template
`templates/skills/harness-architect/SKILL.md.tmpl`, which is complete and
self-contained. In the template's own order:

| Step | Template step | What was done | Result |
|---|---|---|---|
| 1 | harness generation | Authored the harness-surface conformance assertion over `.github/skills/harness-architect/SKILL.md` — five limbs, expected failure marker `HARNESS_ARCHITECT_SURFACE_ABSENT`. This is the unit's **declared harness set**, and it is the whole of it. | authored |
| 2 | 5.1 compilation | `python -m py_compile src/autoharness/cli.py` | exit `0` — **`Compilation: PASS`** |
| 3 | 5.2 red phase | `PYTHONPATH=src python -m unittest discover` over the declared harness set — the form template Step 5.2 names | exit non-zero, 5 failures, 0 errors, every failure carrying `HARNESS_ARCHITECT_SURFACE_ABSENT` — **`Red Phase: CONFIRMED`** |
| 4 | postcondition | Recorded `Compilation: PASS` and `Red Phase: CONFIRMED`, with both commands, both exit codes, the unscoped reading and the assertion source, into the immutable artifact `docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md`. | recorded |
| 5 | 6 labelling | Applied the real `harness-ready` label to all four tasks of `182-F`. | applied |

**`PRE-0` is not, and is nowhere claimed to be, an installed Ship step.** No
phase of `.github/agents/_ship.agent.md` performs it, no installed automation
invokes it, and nothing in this plan schedules it to run inside Ship. It was
performed by Stage, on the producer side of P-002's own `Applies To` split
(`ship` is the **consumer**; the harness-architect is the **producer**), and
its only durable trace is the committed evidence artifact named above. A reader
who wants to know whether it happened reads that file, not a promise.

#### Why the evidence lives in a committed artifact and not in the harness manifest

Earlier revisions said `PRE-0` records its postcondition into
`.autoharness/harness-manifest.yaml`. That carrier was **unavailable to the
only actor that could write it**: decision `D11` states explicitly that it
"authorizes **no** edit to `.autoharness/harness-manifest.yaml` by any staging
session", and `PRE-0` is a staging-side act. A postcondition that its author is
forbidden to write is not a postcondition.

The carrier is therefore the **immutable, committed** artifact
`docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md`.
It is written once, never edited, versioned in the branch, and readable by
`182.001-T` at execution time. `.autoharness/harness-manifest.yaml` is
untouched by this plan at staging time and is written only by `182.003-T`, in
its own ACTIVATE commit, under `D11`.

#### The ordering is a property of the commit graph, not of the prose

A label cannot prove when it was applied, so this unit does not ask anyone to
take its word for it. The ordering was established by construction:

| # | Fact | How to re-derive it |
|---|---|---|
| O1 | The four `harness-ready` labels were **withdrawn** and the withdrawal committed. That commit, `3ad5fcc7`, is the **labels-absent base**. | `git show 3ad5fcc7:.backlogit/queue/182.001-T.md` — and the same for `182.002-T`, `182.003-T`, `182.004-T` — shows no `harness-ready` entry in the `labels:` list. |
| O2 | Both P-004 channels were executed **against that base**, with the labels absent, and their raw output recorded. | The evidence artifact records `3ad5fcc7` as its base, both verbatim commands, both exit codes and the failure set. |
| O3 | The labels were re-applied **only afterwards**, in a commit descended from `3ad5fcc7`. | `git log --oneline -S"harness-ready" -- .backlogit/queue/182.001-T.md` shows the withdrawal at `3ad5fcc7` and the re-application in its descendant. |

So **P-004's evidence precedes the label application in the commit graph**, and
**P-002's filter sees the label** at queue building and at claim, because it is
on the record now. Both preconditions are satisfied, in the order P-004
prescribes, and neither is satisfied by assertion.

#### The label opens the queue; the recorded evidence authorizes the work

The four task records carry `harness-ready` in their `labels` list, because a
queue record's labels are authored by Stage and a plan cannot ask Ship's filter
to read a label that is not there. That presence is **queue admission and
nothing else.** Authorization is separate and is enforced by a fail-closed read,
in the same shape `169.015-T` uses:

> **`182.001-T`'s first action, before it opens any file for writing, is to
> read `docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md`**
> and confirm, affirmatively and all of them: exactly one `PRE0_STATE:` line
> carrying the token `PRE0_EVIDENCE_RECORDED`; `Compilation: PASS`;
> `Red Phase: CONFIRMED`; the recorded expected failure marker
> `HARNESS_ARCHITECT_SURFACE_ABSENT`; and a recorded
> `labels_absent_base` commit that is an ancestor of `HEAD` and at which none of
> the four `182.00x-T` records carries `harness-ready` in its `labels` list. If
> the artifact is missing, unreadable, carries no `PRE0_STATE:` line, carries
> more than one, carries an unrecognised token, or fails **any** of those
> checks, the task touches no file, makes no commit, exits non-zero and returns
> the unit to Stage.

A record carrying the label while that artifact does not affirm all five is a
**defect to halt on**, never a permission. This is P-004's ordering requirement
enforced mechanically at execution time as well as established in history.

### Why this is not a waiver

P-004's precondition is **mechanical and actor-independent**:

> `python -m py_compile src/autoharness/cli.py` exits 0 AND
> `PYTHONPATH=src python -m unittest discover -s tests` exits non-zero with
> expected failure markers

Nothing in that sentence requires the *installed copy* of the skill to be the
thing that runs it. The skill file is the **procedure specification**; the
commands are the **evidence**. During bootstrap the procedure is executed
directly from its authoritative template,
`templates/skills/harness-architect/SKILL.md.tmpl`, which is complete and
self-contained — it specifies the posture selection, the harness generation,
the compilation check (Step 5.1), the red-phase check (Step 5.2) and the
`harness-ready` labelling (Step 6).

So:

* **No gate is suspended.** Both channels were observed.
* **No severity is lowered.** A failing observation halts the unit.
* **No evidence is assumed.** The postcondition
  (`Compilation: PASS`, `Red Phase: CONFIRMED`) is recorded from the run, in a
  committed artifact, with both commands, both exit codes and the failure set.
* **Nothing is skipped.** The label was applied *after* the red phase was
  confirmed, never before — which is P-004's whole ordering requirement, and
  here it is a fact about the commit graph rather than a claim about intent. The
  only difference from steady state is *which copy of the procedure text the
  executor read* — and erasing that difference permanently is this unit's
  entire purpose.

A waiver produces **less** evidence than the policy demands. This produces
**exactly** the evidence the policy demands, from a template-resident
procedure, once.

### How P-002 is satisfied — mechanically, not by prose

Every task of `182-F` — `182.001-T`, `182.002-T`, `182.003-T` and
`182.004-T` — **carries the `harness-ready` label on its own record**, applied
at `PRE-0` template Step 6 from the evidence recorded at `PRE-0` Step 4, in a
commit descended from the labels-absent base `3ad5fcc7`. Ship's ordinary,
unmodified ready-queue filter admits all four by the ordinary rule.
`182.001-T`'s fail-closed first-action read of the committed `PRE-0` evidence
artifact is what keeps that admission honest: the label opens the queue, the
recorded evidence authorizes the work, and neither substitutes for the other.

There is nothing for an installed filter to know about `188-S`, because `188-S`
no longer asks it for anything unusual. Concretely, and each independently
checkable:

* **No Ship edit.** `.github/agents/_ship.agent.md` and
  `templates/agents/_ship.agent.md.tmpl` are untouched by this unit.
* **No policy edit.** P-002 and P-004 are correct as written and are satisfied,
  not amended.
* **No gate edit.** The `pre_claim` topology gate and its bootstrap-grant
  mechanism are untouched.
* **No grant, no force, no audit entry.** No `.autoharness/bootstrap-grants/`
  file is consumed or written, no `--force` is used, no force-audit log is
  touched, and no operator exemption note exists.
* **No self-authorization.** Stage declares no authority here and holds none.

### How RED and GREEN are produced

| Phase | Task | What is observed |
|---|---|---|
| RED committed | `182.001-T` | The `PRE-0`-authored conformance assertion is **committed** to `tests/`, byte-identical to the source recorded in the `PRE-0` evidence artifact, together with its recorded failing output. The assertion checks that `.github/skills/harness-architect/SKILL.md` exists, carries valid YAML frontmatter with `name: harness-architect`, contains no unresolved `{{...}}` double-brace variable, and contains no unresolved single-brace suffix placeholder `{SUFFIX_FEATURE}` or `{SUFFIX_TASK}`. Every limb fails with the marker `HARNESS_ARCHITECT_SURFACE_ABSENT`, because the skill is absent. **Admitted by the ordinary P-002 filter on the label applied at `PRE-0` Step 6.** |
| RED re-confirmed | `182.002-T` | The two P-004 commands are re-run verbatim against the **committed** tree: `py_compile` exits 0 (compilation channel); `PYTHONPATH=src python -m unittest discover -s tests` now exits non-zero with the assertion in the failure set carrying `HARNESS_ARCHITECT_SURFACE_ABSENT` (red-phase channel, **whole-suite form**, which becomes observable here because `182.001-T` put the assertion in `tests/`). The scoped reading is re-taken too, and the committed `PRE-0` evidence artifact is verified to match. Both readings recorded. **Admitted by the ordinary filter.** |
| GREEN | `182.003-T` | One commit generates the skill from its template **and registers it in `.autoharness/harness-manifest.yaml`** (`D11`). The assertion flips to passing. **Admitted by the ordinary filter.** |
| VERIFY | `182.004-T` | Installed/template parity and manifest checksum parity re-derived; the `HARNESS_ARCHITECT_INSTALLED` completion token emitted. **Admitted by the ordinary filter.** |

**Why every repository mutation is still inside a claimed, revertible task.**
`PRE-0` authored the harness in a scratch location outside the repository
working tree and observed it there — Stage writes no test or source file —
and `182.001-T` is what **authors it into `tests/` and commits it**, from the
verbatim source recorded in the evidence artifact. That split is deliberate and
is a strengthening rather than a convenience: no file enters the branch outside
a claimed task, so the unit's rollback story stays a sequence of single-commit
reverts.

### The declared harness set, and both red-phase readings

This unit's **declared harness set is exactly one module**: the harness-surface
conformance assertion described above. `PRE-0` recorded **both** readings, and
the plan records both rather than the convenient one:

| Reading | Command | Result at `PRE-0` |
|---|---|---|
| **Scoped** — the declared harness set, which is what template Step 5.2 names (*"Run `{{TEST_COMMAND}}` for the harness tests"*) | `PYTHONPATH=src python -m unittest discover` over the declared harness set | **exit non-zero**; 5 failures, **0 errors**; every failure carries `HARNESS_ARCHITECT_SURFACE_ABSENT`; no collection, import or syntax error. **This is the marker-carrying red-phase evidence.** |
| **Unscoped** — the whole discovered suite | `PYTHONPATH=src python -m unittest discover -s tests` | **exit 0**, `Ran 2344 tests`, `OK (skipped=54)`. |

**The unscoped reading is green at `PRE-0`, and that is expected rather than a
contradiction.** `PRE-0` authors the assertion outside the repository working
tree, so it is not in `tests/` yet and `discover -s tests` cannot see it. The
unscoped suite goes red — carrying `HARNESS_ARCHITECT_SURFACE_ABSENT` — at
`182.001-T`, which is the task that puts the assertion on the branch, and
`182.002-T` re-runs **both** commands verbatim against that committed tree and
records both.

**The stated consequence, without softening it.** P-004's precondition as
literally written reads the *whole* discovered suite. At `PRE-0` that literal
whole-suite form is **not** satisfied, and this plan does not claim it is. What
is satisfied at `PRE-0` is the form the harness-architect template itself
prescribes at Step 5.2 — the harness tests — and that reading is non-zero with
the expected marker. The whole-suite form becomes satisfied at `182.002-T`, on
the committed tree, and `182.002-T` is gated on it. The distinction is recorded
in the evidence artifact rather than smoothed over, and this unit does **not**
redefine P-004's precondition and does **not** pre-empt `176-S`, which owns the
scoping of the red-phase precondition to the declared harness set.

**Two unscoped observations were taken, and they disagreed.** The first
returned exit 1 with `errors=1` — a Windows temp-directory teardown race
(`PermissionError: [WinError 32]` inside `shutil.rmtree`) carrying **no**
`HARNESS_ARCHITECT_SURFACE_ABSENT` marker. The second, taken under the same
conditions, returned exit 0 / `OK`. The disagreement is adjudicated **against**
the convenient direction: the exit-1 observation is recorded but is **not**
counted as red-phase evidence, because a non-zero exit without the expected
marker is not the signal P-004 asks for, and a flaky teardown race is not a
harness failure. Both observations are in the evidence artifact verbatim.

### Where the template variables come from

`182.003-T` must resolve every template variable, and the sources are not all
the same kind of source. Naming them imprecisely is how an executor reaches a
variable its stated source does not contain and improvises a value — and an
improvised `UNIMPLEMENTED_MARKER` would silently weaken `182.002-T`'s red-phase
marker check, which is this unit's core evidence.

| Variable | Authoritative source | Resolves to |
|---|---|---|
| `{{BUILD_CHECK_COMMAND}}` | `.autoharness/harness-manifest.yaml` → `variables_used` | `python -m py_compile src/autoharness/cli.py` |
| `{{TEST_COMMAND}}` | `.autoharness/harness-manifest.yaml` → `variables_used` | `PYTHONPATH=src python -m unittest discover -s tests` |
| `{{SOURCE_DIR}}` | `.autoharness/harness-manifest.yaml` → `variables_used` | `src/autoharness` |
| `{{TEST_DIR}}` | `.autoharness/harness-manifest.yaml` → `variables_used` | `tests` |
| `{{UNIMPLEMENTED_MARKER}}` | **Derived, not stored — two install-harness surfaces, reconciled below.** `.github/skills/install-harness/SKILL.md:130`, in the table headed at `:100` (`Template Variable \| Source \| Example (Rust) \| Example (TypeScript) \| Example (Python)`), is the **only** table in that file that carries per-language `UNIMPLEMENTED_MARKER` values, and is therefore the **value source**. `:335`, in the *Review Persona Variables* table headed at `:327` (`Template Variable \| Source \| Purpose`), supplies the **keying rule** — "Derived from `languages.primary`" — and nothing else. `languages.primary` reads `python` from `.autoharness/workspace-profile.yaml:7`, selecting the `Example (Python)` column of `:130`. | `raise NotImplementedError("...")` — transcribed **verbatim** from `:130`'s `Example (Python)` column |
| `{SUFFIX_FEATURE}` / `{SUFFIX_TASK}` | `.autoharness/config.yaml` → `backlog.suffix_map`, per `.github/skills/install-harness/SKILL.md:262,264` | `F` / `T` |

#### The `UNIMPLEMENTED_MARKER` derivation, stated exactly

`UNIMPLEMENTED_MARKER` is **absent from `.autoharness/` entirely** — it appears
in neither `harness-manifest.yaml`'s `variables_used` nor anywhere else under
that directory. It is a derivation, and the derivation below is the only
authorized route to a value.

**Two install-harness surfaces are involved, and they are complementary rather
than competing.** Naming only one of them, or asserting a per-language lookup
against the one that has no per-language rows, is what leaves an executor with
no referent and invites an improvised marker.

| Surface | What it actually is | What it supplies |
|---|---|---|
| `.github/skills/install-harness/SKILL.md:335` | A row in the *Review Persona Variables* table headed at `:327`, whose columns are `Template Variable \| Source \| Purpose`. It is keyed **one row per variable** and has **no language columns and no language rows**. Its `Purpose` cell holds an abbreviated illustrative `e.g.` list. | The **keying rule** only: `Derived from `languages.primary``. It is **never** a value source, and its `e.g.` list must never be transcribed as a marker. |
| `.github/skills/install-harness/SKILL.md:130` | A row in the table headed at `:100`, whose columns are `Template Variable \| Source \| Example (Rust) \| Example (TypeScript) \| Example (Python)`. This is the **only** table in the file carrying per-language `UNIMPLEMENTED_MARKER` values. | The **value**, selected by the column matching the key. |

**Derivation, in order.** Read `languages.primary` from
`.autoharness/workspace-profile.yaml` (line 7, `primary: "python"`). Use it to
select the matching `Example (…)` column of the `:100` table. Read the
`{{UNIMPLEMENTED_MARKER}}` row at `:130` in that column. Transcribe the cell
**verbatim**.

**The exact value for this workspace.** `languages.primary` is `python`, so the
`Example (Python)` column applies and the bound value of
`{{UNIMPLEMENTED_MARKER}}` is exactly:

```text
raise NotImplementedError("...")
```

Transcribed character-for-character from `:130`. **The message slot is not a
prompt to invent text.** `182.003-T` binds the literal as written — it does not
re-spell it, does not shorten it to `raise NotImplementedError`, and does not
substitute a stub-specific message. Varying the message is a template-authoring
decision this unit does not own; if it is wanted it is a separate plan revision.

**Why the two surfaces do not disagree.** `:335`'s `e.g.` list shows
`raise NotImplementedError` and `:130`'s Python column shows
`raise NotImplementedError("...")`. These differ **only** in whether the message
slot is displayed. The **detectable token** — the substring `182.002-T`'s
red-phase marker check asserts against the failure set — is
`NotImplementedError`, and it is identical in both. The value source is `:130`;
`:335` is used solely to confirm the key and to corroborate the token.

**Fail closed — mechanically evaluable triggers.** `182.003-T` touches no file,
makes no commit, exits non-zero and returns the unit to Stage if **any** of the
following holds. Each is a check against a real artifact, not against a
structure that does not exist:

| # | Trigger | Disposition |
|---|---|---|
| F1 | `.autoharness/workspace-profile.yaml` is missing or unreadable, or `languages.primary` is absent or empty | HALT — key unresolvable |
| F2 | `languages.primary` does not case-insensitively match any `Example (…)` column header of the `:100` table (today exactly `Rust`, `TypeScript`, `Python`) | HALT — **unsupported language mapping**. Do not fall back to another column, to `:335`'s `e.g.` list, or to a plausible idiom for that language. |
| F3 | The `{{UNIMPLEMENTED_MARKER}}` row is absent from the `:100` table, or its cell for the selected column is empty or `_(N/A)_` | HALT — value unresolvable |
| F4 | The selected cell and `:335`'s `e.g.` entry for the same language share **no** common detectable token | HALT — **ambiguous language mapping**. Two authoritative surfaces disagreeing on the token is a repository defect, not a choice for the executor to arbitrate. |
| F5 | `config.backlog.suffix_map` in `.autoharness/config.yaml` is missing a required key | HALT — suffix binding unresolvable |

**No trigger fires for this workspace.** `languages.primary` is `python` (F1
clear); `Example (Python)` is a declared column of the `:100` table (F2 clear);
`:130`'s Python cell is non-empty (F3 clear); both surfaces carry
`NotImplementedError` (F4 clear); `suffix_map` supplies `F` and `T` (F5 clear).
The guard is therefore a real check that passes here, not a condition that is
unconditionally true and halts every run.

**DO NOT IMPROVISE, DO NOT GUESS, DO NOT SUBSTITUTE A PLAUSIBLE VALUE.** An
improvised `UNIMPLEMENTED_MARKER` would silently weaken `182.002-T`'s red-phase
marker check, which is this unit's core evidence.

The two `SUFFIX_*` tokens appear in the template's frontmatter `argument-hint`
in **single**-brace form, which the `{{...}}` limb does not match — hence the
assertion's separate fifth limb. They are not exemplar tokens of the
`{YYYY-MM-DD}` kind: they are defined, bound harness variables that every other
carrier in the repository spells in double-brace form
(`templates/backlog/config.yml.tmpl`, `templates/harness-config.yaml.tmpl`,
`templates/agents/_ship.agent.md.tmpl:352`,
`templates/skills/shipment-reconcile/SKILL.md.tmpl:567`). `182.003-T` binds
them from `suffix_map` at generation time. Correcting the **template's** own
single-brace spelling is a template-source change, out of scope for this unit,
and is carried as a non-blocking follow-up in the stash.

**Scope honesty on the red-phase channel.** P-004's precondition as written
reads the *whole* discovered suite. This unit records **both** readings — see
"The declared harness set, and both red-phase readings" above — and names which
one carries the marker. It does **not** redefine the precondition, and it does
**not** pre-empt `176-S`. If a future reading of either channel contradicts the
recorded evidence, that disagreement is recorded as evidence and the unit halts
for operator disposition rather than resolving in the convenient direction.

## The bounds that remain

This plan declares **no authority, no exemption and no carve-out**, so there is
nothing to bound on a permission axis and nothing to expire. What remains are
two ordinary plan-scope bounds, both checkable against the repository:

| Axis | Bound |
|---|---|
| **Deliverable** | Exactly one generated file, `.github/skills/harness-architect/SKILL.md`, produced from its existing authoritative template, plus that file's registration in `.autoharness/harness-manifest.yaml` under decision `D11`. Generating any other absent surface is out of scope. |
| **Procedure source** | The harness-architect procedure text **was read** from `templates/skills/harness-architect/SKILL.md.tmpl` exactly once, at `PRE-0`, for the single reason that no installed copy existed. Once `182.003-T` lands, every unit — including any re-run of `188-S` — reads the installed copy at `.github/skills/harness-architect/`. |

Neither bound is a permission. The Deliverable bound is the unit's scope
statement; the Procedure-source bound is a statement of **fact about which file
the executor opened**, which is not a gate, not an override, and not something
any policy grants. It is recorded because it is the one respect in which this
unit differs from steady state, and it is stated here so that difference is
visible rather than buried.

### What P-002 requires, and how each requirement is met

P-002 is not only an evidence gate. Its live text gates **claiming**:

> **Gate Point**: Queue building (Step 2) and task claiming (Step 3)
> **Precondition** (ship): The task carries the `harness-ready` label.
> **Enforcement** (ship): Filter ready queue to only tasks carrying the
> `harness-ready` label.
> **Violation Action**: Halt and suggest running the harness-architect.

| P-002 element | How this unit satisfies it |
|---|---|
| Gate Point — queue building | All four task records carry `harness-ready` **before** the queue is built, applied at `PRE-0` Step 6 in a commit that precedes any queue construction for this unit. |
| Gate Point — task claiming | The same four records still carry the label at claim time. Nothing removes it. |
| Precondition | Satisfied literally: the label is on the record, not asserted to be unnecessary. |
| Enforcement | The ordinary filter runs unmodified and admits all four by the ordinary rule. No exception is requested and none is needed. |
| Violation Action | Never reached for this unit. It is also no longer vacuous for the portfolio: once `182.003-T` lands, "run the harness-architect" names an actor that exists. |

**Why this is not a waiver of P-002.** A waiver would admit a task whose
required harness evidence is missing. Here the evidence was produced first —
both P-004 channels observed, the postcondition recorded in a committed
artifact — and the label was applied from that evidence, in P-004's own order,
in a commit descended from the labels-absent base. Every task in this unit,
including `182.003-T`, the only commit that writes production content, is
admitted under the ordinary label. Less evidence is not produced anywhere;
strictly more is.

**What this unit is not.** It is not a bootstrap grant — it consumes no
`.autoharness/bootstrap-grants/` file, writes none, and touches no force-audit
log. It is not a `--force` override. It is not an undocumented operator
exemption. It is not a policy edit: P-002's and P-004's text are correct as
written and are not amended here. It is not the `pre_claim` bootstrap grant
described in `.github/agents/_ship.agent.md`, and it consumes none. Stage
declares no authority in this plan and holds none.

**A re-run needs nothing special.** If `188-S` must ever be re-executed, the
installed skill at `.github/skills/harness-architect/` already exists and is
used; the template-resident route at `PRE-0` is simply not the shortest path any
more. There is no revived permission, because there was never a permission.

## Composed-state check (decision D6)

| Field | Value |
|---|---|
| Pass state | `HARNESS_ARCHITECT_INSTALLED` — the skill exists at `.github/skills/harness-architect/SKILL.md`, its frontmatter parses, `name` is `harness-architect`, it carries no unresolved `{{...}}` double-brace variable and no unresolved single-brace `{SUFFIX_FEATURE}` / `{SUFFIX_TASK}` token, and it derives from `templates/skills/harness-architect/SKILL.md.tmpl`. The only authorizing token. |
| Fail state | `HARNESS_ARCHITECT_ABSENT` — generation was attempted and the result is missing or non-conforming. An explicit failed precondition. |
| No-observation state | `HARNESS_ARCHITECT_NOT_OBSERVED` — artifact missing, unreadable, empty, carrying no `BOOTSTRAP_STATE:` line, carrying more than one, or carrying an unrecognised token. **Never a pass.** |
| Artifact | `.autoharness/gates/harness-architect-bootstrap.txt` (inside the existing gitignored `.autoharness/gates/` boundary, `.gitignore:7`; adds no new ignored path) |
| Line form | Exactly one line, `BOOTSTRAP_STATE: <token> | skill_sha256=<hex> | template_sha256=<hex> | head_commit=<sha> | checked=<RFC3339-UTC>` |
| Producer | `182.004-T`, sole writer, whole-file atomic replace via same-directory temp plus rename |
| Consumer | Stage, when re-sequencing the code-bearing shipments; and `187-S`, whose lifecycle step must find the actor already present |
| Activation commit | `182.003-T` |

Resolution is a **total function**, evaluated in this order, first match wins:
`HARNESS_ARCHITECT_NOT_OBSERVED`, `HARNESS_ARCHITECT_ABSENT`,
`HARNESS_ARCHITECT_INSTALLED`. Fail-closed: anything not affirmatively
conforming is not `INSTALLED`.

## Tasks

| ID | Phase | Task | Size | Cx |
|---|---|---|---|---|
| `182.001-T` | RED | commit the `PRE-0`-authored harness-surface conformance assertion together with its recorded failing observation | S | low |
| `182.002-T` | RED CONFIRM | re-run both P-004 channels verbatim against the committed tree and verify the recorded manifest postcondition | S | medium |
| `182.003-T` | ACTIVATE | one commit: generate `.github/skills/harness-architect/SKILL.md` from its template, binding every variable from its named authoritative source, **and register the file and its checksum in `.autoharness/harness-manifest.yaml`** | S | medium |
| `182.004-T` | VERIFY | re-derive installed/template parity **and manifest checksum parity**, emit the `HARNESS_ARCHITECT_INSTALLED` completion token | XS | low |

**Claim admission.** All four tasks carry the `harness-ready` label, applied at
`PRE-0` template Step 6 on the P-004 evidence recorded at `PRE-0` Step 4, in a
commit descended from the labels-absent base `3ad5fcc7`. All four are admitted
by the **ordinary** P-002 filter. There is no carve-out, no exception and no
special case. No task is added, removed, resized or resequenced by revision 5:
the sizing is unchanged (S / S / S / XS, none unsized) and the chain is intact.

Edges: `182.001-T` → `182.002-T` → `182.003-T` → `182.004-T`. Three edges, one
chain, no cycle, no successor task inside the unit.

## DAG position

`188-S` is a **DAG root**. It has no precursor shipment: it needs no operation
substrate, no transport decision, no isolation characterization and no schema
migration. It reads one template, writes one generated file, and refreshes one
manifest entry.

### The dependency matrix — exact, and the authoritative statement

This table is the **complete** `dependencies:` frontmatter of every shipment in
the portfolio, read from the records themselves. It is the authoritative
statement of the graph; anything drawn below is subordinate to it.

| Shipment | Status | Declared `dependencies:` | Root? |
|---|---|---|---|
| `176-S` | queued | `185-S`, `187-S`, `188-S` | no |
| `177-S` | queued | *(none)* | **yes** (`dag-root`) |
| `178-S` | queued | `185-S`, `188-S` | no |
| `180-S` | queued | `185-S`, `188-S` | no |
| `181-S` | **archived** | `183-S` | no |
| `182-S` | queued | *(none)* | **yes** (`dag-root`) |
| `183-S` | queued | *(none)* | **yes** (`dag-root`) |
| `184-S` | **archived** | `182-S`, `188-S` | no |
| `185-S` | queued | `184-S`, `188-S` | no |
| `186-S` | queued | `185-S`, `188-S` | no |
| `187-S` | queued | `188-S` | no |
| `188-S` | queued | *(none)* | **yes** (`dag-root`) |
| `189-S` | queued | *(none)* | **yes** (`dag-root`) |

**Acyclicity.** Every edge points from a shipment to a strict predecessor, and
the relation admits the topological order
`188-S`, `182-S`, `183-S`, `177-S`, `189-S`, `181-S`, `184-S`, `185-S`,
`187-S`, `186-S`, `178-S`, `180-S`, `176-S`.
A valid topological order exists, therefore the graph is acyclic. No shipment
appears in its own transitive predecessor set.

**`188-S`'s out-edges, exactly.** `188-S` is a declared predecessor of
`176-S`, `178-S`, `180-S`, `184-S`, `185-S`, `186-S` and `187-S` — seven
shipments, every code-bearing implementation shipment in the portfolio. It is
**not** a predecessor of `177-S`, `181-S`, `182-S`, `183-S` or `189-S`. `181-S`,
also archived under `D10`, depends on `183-S` alone and consumes no harness
state: its activation touches `.github/workflows/ci.yml` and `docs/`, neither
manifest-tracked, which is why `D11` does not cover it either.

### Projection — `188-S`'s out-edges only

The diagram below is a **projection, not the graph.** It draws `188-S`'s
out-edges and the `185-S` fan-out for readability, and it deliberately **omits**
edges that the matrix above carries: `182-S → 184-S`, `183-S → 181-S`,
`184-S → 185-S`, `185-S → 176-S` and `187-S → 176-S`. Read the matrix for the dependency
relation; read this only for shape.

```text
PROJECTION (188-S out-edges; NOT the full edge set — see the matrix above)

188-S ─┬─▶ 184-S   (archived/withheld — also gated on TRANSPORT_DECIDED; also depends on 182-S)
       ├─▶ 185-S ─┬─▶ 186-S            (185-S also depends on 184-S)
       │          ├─▶ 178-S
       │          └─▶ 180-S
       ├─▶ 187-S
       └─▶ 176-S   (176-S also depends on 185-S and 187-S)
```

`177-S`, `182-S`, `183-S` and `189-S` are DAG roots and remain so:

* `182-S` and `183-S` are bounded spikes that land no production code — their
  deliverable is a findings artifact, and `176.001-T` states "NO production
  code" explicitly.
* `177-S` carries its own PREPARE/RED/VERIFY/ACTIVATE machinery: its five RED
  tasks author their own failing assertions and its `169.017-T` gate adjudicates
  them before activation. It consumes no `HARNESS_READY` from the Ship pre-task
  lifecycle.
* `189-S` is a test-only synchronization repair and lands no production code.

Adding a bootstrap edge to any of those would re-introduce the false serial
dependency that decision D8 withdrew.

### `187-S`'s position, stated against the executable graph

`187-S` declares **one** dependency: `188-S`. The `187-S → 184-S` edge was
withdrawn at decision `D9` revision 2 as **never technical** — `181-F` delivers
the harness-surface resolver, the Ship pre-task lifecycle phase and the state
contract, and consumes none of `184-S`'s operation registry, result model or
transport substrate. That withdrawal is **not** reversed here, and the edge is
**not** restored.

The consequence is deliberate and is the correct one: **`187-S` is intentionally
eligible to be claimed once `188-S` ships.** It is the harness-lifecycle
foundation of this portfolio, not substrate-dependent work, so nothing about the
transport question gates it. Withholding it behind `TRANSPORT_DECIDED` would be
withholding the lifecycle foundation behind a decision it does not consume —
which is exactly the false serial dependency `D8` withdrew, re-introduced one
shipment later.

What is preserved unchanged is the *task-level* gate: **every task of `181-F`
remains dependency-blocked until `188-S` reaches `shipped`.** `187-S`'s
eligibility is eligibility to be *claimed*, not permission to execute ahead of
its precursor, and `187-S`'s own record states that it is queued and not
claimable until `188-S` ships.

## Out of scope

* The Ship pre-task harness-generation lifecycle, the harness-surface resolver
  and the `HARNESS_READY`/`NO_HARNESS` contract — `187-S` owns all three and
  keeps them.
* The P-004 gate's three-channel observation logic and the scoping of the
  red-phase precondition to the declared harness set — `176-S` owns both.
* Any edit to P-002 or P-004 text. Both are correct as written; this unit
  satisfies them.
* Generating any absent skill surface other than `harness-architect`.
* Any change to the `pre_claim` topology gate or its bootstrap-grant mechanism.
* Any manifest entry other than the one this unit's own deliverable requires.
  `182.003-T` registers `.github/skills/harness-architect/SKILL.md` and nothing
  else; it refreshes no other checksum and rewrites no other entry.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The template-resident procedure source is read as a general precedent for skipping P-004 | Nothing was skipped: both P-004 channels were executed verbatim and their outcomes recorded in a committed artifact, and the `harness-ready` label was applied only afterwards, from that evidence, in a commit descended from the labels-absent base. Revision 5 declares no authority, so there is no permission to generalise from. The Procedure-source bound is a statement of fact about which file the executor opened, not a gate. |
| R2 | The `harness-architect` template is stale relative to current skill conventions | The conformance assertion validates frontmatter, `name`, and placeholder resolution. A stale template fails the assertion at `182.003-T` and never reaches `INSTALLED`. |
| R3 | `PRE-0` ran, then the unit stalls before `182.004-T` | `HARNESS_ARCHITECT_NOT_OBSERVED` is the fail-closed default; no successor may treat a missing token as satisfied. |
| R4 | A red-phase reading is non-zero for unrelated reasons, masking or faking the signal | This already happened once and was caught: an unscoped observation returned exit 1 on a Windows temp-directory teardown race carrying no marker, and a second returned exit 0. Neither is counted as red-phase evidence, because the evidence rule is **marker-carrying**, not merely non-zero. Both observations are recorded verbatim. A future disagreement halts for operator disposition rather than resolving in the passing direction. |
| R5 | A reader concludes the actor's installation also installed the lifecycle | `182-F`, `188-S` and this plan state the split explicitly, and `187-S` retains the automation in its own manifest. |
| R6 | A reader believes some task in this unit is admitted to Ship's queue without `harness-ready` | No task is. All four records carry the label — applied at `PRE-0` Step 6 from the recorded evidence, after it — and all four are admitted by the ordinary filter. The label's *presence* is not read as evidence: `182.001-T`'s fail-closed first action reads the committed `PRE-0` evidence artifact and halts the unit before its first write if any of its five checks fails. The revision-2/3 claim carve-out is withdrawn in full and is restated nowhere — in this plan, in `182-F`, in `188-S`, in any task record, or in decision `D9`. |
| R7 | `UNIMPLEMENTED_MARKER` is improvised because it is derived rather than stored | The derivation names **both** install-harness surfaces and their distinct roles — `:335` supplies the key, `:130`'s `Example (Python)` column supplies the value — and the bound literal is fixed as a verbatim transcription rather than a value the executor composes. Unavailability is fail-closed on five mechanically evaluable triggers (F1–F5), including unsupported and ambiguous language mapping: no file is touched, no commit is made, and the unit returns to Stage rather than substituting a plausible marker. |
| R8 | The skill is generated but its manifest entry is not registered, leaving a false installed-state record | Decision `D11`: `182.003-T` registers the entry and its checksum in the **same commit and rollback unit** as the generated file, and `182.004-T` re-derives checksum parity. A commit carrying one without the other is an immediate revert. |

## Hardening review

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is this a waiver with extra words? | No. A waiver produces less evidence than the policy demands. This produces exactly the evidence P-004 names — both channels, recorded to the manifest — from a template-resident procedure. The gate is satisfied, not suspended. |
| H2 | What stops the procedure-source route being reused as a permission? | It is not a permission, so there is nothing to reuse. This plan declares no authority, no exemption and no carve-out. `PRE-0` read the template for the single reason that no installed copy exists; once `182.003-T` lands, the installed copy exists and is what every unit reads. |
| H3 | Could an agent widen or re-date anything declared here? | There is nothing to widen or re-date. The two surviving bounds are ordinary plan scope — one named deliverable, and which file `PRE-0` opens. Stage declares no authority in this plan and holds none, and this unit is not the `pre_claim` bootstrap grant and consumes none. |
| H4 | Why is `188-S` a root when `187-S` was not? | Because installing the actor requires reading one template, writing one file and refreshing one manifest entry. It needs no substrate, no transport decision and no isolation result. `187-S` was not a root because it could not bootstrap itself through an absent actor — that was the defect, and it is what this unit removes. |
| H5 | Does this let `187-S` become claimable early? | **It makes `187-S` eligible after `188-S` ships, and that is intended, not a leak.** `187-S` declares exactly one dependency, `188-S`. Its `184-S` edge was withdrawn at `D9` revision 2 as never technical — `181-F` consumes no operation registry, result model or transport substrate — and is not restored here. `187-S` is the harness-lifecycle **foundation** of this portfolio, so gating it behind `TRANSPORT_DECIDED` would withhold the foundation behind a decision it does not consume, which is the false serial dependency `D8` withdrew. What is preserved is the task-level gate: every task of `181-F` remains dependency-blocked until `188-S` reaches `shipped`, and `187-S`'s own record states it is queued and not claimable until then. Eligibility to be claimed is not permission to execute ahead of its precursor. |
| H6 | Is the red phase real, or a formality? | Real. The conformance assertion fails against the current workspace for the intended reason — the skill is absent — observed at `PRE-0` and re-observed on the committed tree at `182.002-T`, and passes only after `182.003-T` generates the file. The transition is observed on both sides. |
| H7 | Does this unit need the actor to harness itself? | No, and the apparent circularity was a role confusion rather than a real one. Generating the harness, observing both channels and applying the label are the **producer's** steps, and P-002 gates the **consumer**. `PRE-0` performs the producer's steps from the authoritative template; Ship then claims four ordinarily-labelled tasks. Neither half needs an exception. |
| H8 | What if generation succeeds but produces a non-conforming skill? | `HARNESS_ARCHITECT_ABSENT`. No token is emitted, the unit halts, and no successor becomes claimable. |
| H9 | Does this route reach P-002's CLAIM precondition, or only its evidence precondition? | Both, and in the right order. `PRE-0` Step 4 satisfied the evidence precondition and recorded it in a committed artifact; `PRE-0` Step 5 then applied the real `harness-ready` label, which satisfies the claim precondition **literally** — the label is on each record, so the ordinary filter admits it. The order is not asserted: the evidence's base commit `3ad5fcc7` carries no label and the label-bearing commit descends from it. Revision 1 reached only the evidence precondition; revisions 2–3 tried to reach the claim precondition with prose an installed filter cannot read; revision 4 reached both but in an order the tree contradicted. Revision 5 reaches both in an order the tree records. |
| H10 | Is anything here invisible to the installed enforcement? | No, and this is the test the withdrawn carve-out failed. Every claim this plan makes about admission is checkable against artifacts the filter actually reads: the `labels` list on each of the four task records. Nothing asks Ship, P-002, P-004, `pre_claim` or any gate to behave differently from its installed text, and none of them is edited. |
| H11 | Is this a waiver of P-002 wearing a different word? | No. A waiver admits a task whose required harness evidence is missing. Here the evidence is produced **first** and the label is derived **from** it, in P-004's own order. Every task in this unit, including `182.003-T`, the only commit that writes production content, is admitted under the ordinary label. Less evidence is produced nowhere; strictly more is produced than a waiver would. |
| H12 | Could `182.003-T` land the generated skill without its manifest entry? | Not conformantly. Decision `D11` makes the manifest entry a member of the same commit and the same rollback unit, `182.003-T`'s scope statement names both files, and `182.004-T` re-derives checksum parity as a VERIFY condition. Either file without the other is a revert. |
| H13 | The four records carry `harness-ready`. Is that a pre-dated P-004 observation? | **No, and this is the defect revision 5 repaired rather than argued away.** Every earlier revision asserted the ordering while the tree contradicted it: the labels were committed and no `PRE-0` evidence existed anywhere durable. The repair is mechanical. The labels were withdrawn and the withdrawal committed at `3ad5fcc7`; both P-004 channels were executed against that labels-absent base and recorded in a committed immutable artifact; the labels were re-applied only afterwards, in a descendant commit. `git show 3ad5fcc7:.backlogit/queue/182.001-T.md` shows no `harness-ready` in the `labels:` list, and the evidence artifact names `3ad5fcc7` as its base. The ordering is therefore a property of the commit graph, re-derivable by any reader, and `182.001-T`'s fail-closed first action re-checks it at execution time. |
| H14 | Does anything here claim that `PRE-0` runs inside installed Ship? | **No, and it must not.** `PRE-0` is a completed Stage-side producer act with a committed trace. `.github/agents/_ship.agent.md` contains no phase that performs it, no installed automation invokes it, and no carrier schedules it to run inside Ship. What Ship does with this unit is exactly what Ship does with any unit: build its ready queue, apply the ordinary P-002 label filter, and claim four labelled tasks. |
| H15 | The `PRE-0` postcondition moved out of `.autoharness/harness-manifest.yaml`. Is that a weakening? | **No — the previous carrier was unwritable by its own author.** `D11` states that it authorizes no edit to the harness manifest by any staging session, and `PRE-0` is a staging-side act, so the manifest could never have held the record the contract demanded of it. The replacement carrier is committed, immutable, in-branch, and readable by `182.001-T` at execution time, and it carries strictly more than the two-field postcondition did: both verbatim commands, both exit codes, the full failure set, the assertion source and its digest, the base commit, and both unscoped observations including the one that disagreed. The manifest remains untouched at staging time and is written only by `182.003-T` under `D11`. |

### Blast radius

One new generated file under `.github/skills/`, one new entry in
`.autoharness/harness-manifest.yaml`, one gitignored gate artifact, one
committed test module, and one committed immutable `PRE-0` evidence artifact
under `docs/reviews/review-history/`. No Python module under `src/`, no agent
template, no installed agent mirror, no policy text, no CI workflow. This is
the narrowest surface any unit in this portfolio touches — deliberately,
because the unit that unblocks the portfolio should not also be the unit that
changes the most.

### Rollback

`182.001-T`–`182.002-T` are inert (a committed failing test and a recorded
observation). `182.003-T` reverts as a unit: the single revert removes the
generated skill **and** its manifest entry together, returning the workspace to
the pre-bootstrap state, and the conformance assertion returns to failing,
which is its authored state. A revert that removed one without the other is the
divergent state `D11` exists to prevent. The completion token in
`.autoharness/gates/` is never committed and is re-derived rather than
restored. Rollback restores the deadlock rather than leaving a partial state —
which is correct, because a partially-bootstrapped actor is the one state no
consumer can interpret.

### Verification floor

`HARNESS_ARCHITECT_INSTALLED` and `HARNESS_ARCHITECT_ABSENT` both observed
reachable, and the failing side of the conformance assertion observed before
the passing side. A unit that has never observed its own failure state has not
tested its precondition.

**`PRE-0` evidence floor — SATISFIED, and re-derivable.** Three observations
were **recorded, never assumed**, in the committed evidence artifact:
`py_compile` exit `0`; the red-phase run over the declared harness set exiting
non-zero with every failure carrying `HARNESS_ARCHITECT_SURFACE_ABSENT`; and
the resulting `Compilation: PASS` / `Red Phase: CONFIRMED` postcondition. Had
either channel not held, the label would **not** have been applied, `188-S`'s
tasks would therefore **not** have been admitted by the ordinary filter, and
the unit would have halted — which is P-004's Violation Action reached by its
ordinary mechanism rather than by a special rule.

**Claim-admission floor.** Before `182.001-T` is claimed, Ship's ordinary queue
build is observed to admit all four tasks of `182-F` **on their labels**, and no
task anywhere is observed admitted without one. This is an observation of the
ordinary filter doing its ordinary job; there is no exception to audit, because
none is declared.

**Ordering floor — two limbs, both mechanical.**

*Limb 1, historical, already satisfied.* The evidence's base commit `3ad5fcc7`
is inspected and shown to carry **no** `harness-ready` entry in the `labels:`
list of any of the four `182.00x-T` records, and the label-bearing commit is
shown to be its descendant. This is the observation that the gate was genuinely
**closed** before it was opened: a contract whose ordering has never been
observed in the closed state has not been tested.

*Limb 2, at execution time.* `182.001-T`'s fail-closed first-action read of the
committed `PRE-0` evidence artifact is observed to **close** on a workspace
where that artifact is absent, incomplete, or fails any of its five checks, and
to **open** only where all five hold affirmatively. Together the two limbs are
what prevent the `harness-ready` label from being read as evidence in its own
right.

**Manifest-parity floor (`D11`).** After `182.003-T`, the recorded checksum of
`.github/skills/harness-architect/SKILL.md` is re-derived from the on-disk file
and compared to its manifest entry. `182.004-T` re-observes that parity
alongside installed/template parity, and a mismatch resolves the unit to
`HARNESS_ARCHITECT_ABSENT`.
