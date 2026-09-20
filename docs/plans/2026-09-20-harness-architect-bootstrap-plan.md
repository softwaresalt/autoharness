---
title: "BOOTSTRAP-0: one-time installation of the harness-architect actor"
description: "Installs the actor that P-002 and P-004 name, without assuming that actor already exists and without depending on any code-bearing shipment. Resolves the 187-S bootstrap deadlock at its root: 187-S delivered both the actor and the lifecycle automation that invokes it, while itself depending on code-bearing 184-S, so no policy-compliant route existed to execute either. This unit separates the two: it installs ONLY the actor, under an explicit, one-time, token-bounded bootstrap authority whose red phase is produced by the same mechanical commands P-004 already names. At revision 2 that authority carries a FIFTH bound - an explicit, non-inheritable CLAIM carve-out admitting exactly 182.001-T and 182.002-T to Ship's ready queue without the harness-ready label, because the label's only producer is the actor under installation - so the deadlock is closed at the task layer as well as the shipment layer. 187-S keeps the lifecycle automation and becomes ordinary harness-backed work. Every code-bearing implementation shipment in the portfolio gains a dependency on this unit's completion."
doc_type: plan
source: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
date: 2026-09-20
plan_id: harness-architect-bootstrap
plan_path: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
plan_role: active
revision: 3
verdict: null
disposition: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 3 remediates independent plan-review attempt 02 (ADVISORY/PROCEED-WITH-ADVISORY, P0 0 / P1 0 / P2 1 / P3 1). B2 (P2, carried from attempt 01 and NOT closed at attempt 02) is addressed at its root: the nonexistent 'row for that language' lookup against install-harness SKILL.md:335 is REMOVED and replaced with the actual two-surface derivation - :335 supplies the KEYING RULE only (it has no per-language row), :130's Example (Python) column is the sole per-language VALUE source, and the two are reconciled by their common detectable token. The exact Python marker is stated as a verbatim transcription rather than improvised, and the fail-closed trigger is rewritten to be mechanically evaluable, halting on unsupported or ambiguous language mapping. B4 (P3, raised at attempt 02) is PRESERVED as a non-blocking follow-up in stash 1D0033E0, outside this shipment's scope; it is not closed, not downgraded, and not folded into any task here. The verdict field is NULL because revision 3 has NOT been reviewed; REMEDIATED-PENDING-REVIEW is a DISPOSITION and never a verdict. Stage asserts no PASS, closes no finding, and has performed no self-review. Finding closure is the independent reviewer's call at attempt 03. This unit is NOT publication-eligible and NOT claimable."
awaiting_attempt: 3
review_manifest: docs/reviews/2026-09-20-harness-architect-bootstrap-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 3
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
hardening_rationale: "This unit defines a one-time execution authority that stands temporarily in place of an installed policy actor, and — at revision 2 — a one-time claim carve-out that admits exactly two tasks to Ship's ready queue without the label whose only producer is the actor under installation. An authority that is too wide, or that fails to expire, is indistinguishable from the waiver this portfolio has refused four times. The boundary of both permissions, their shared expiry token, and their non-inheritance are the hardening subject."
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
| 4 | `187-S` additionally declares `depends_on: 184-S`, which is code-bearing | `184-S` needs the same absent actor, so the deadlock is also a graph cycle in the policy sense |

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
| **Split the actor from the automation, and install the actor under a narrow, expiring, evidence-complete authority** | **CHOSEN** |

## The chosen route

**The actor and the automation are two different deliverables, and only the
first is a bootstrap problem.**

* **This unit (`188-S`) installs the ACTOR only** — it generates
  `.github/skills/harness-architect/SKILL.md` from its authoritative template.
  No Python module, no agent-lifecycle edit, no policy edit.
* **`187-S` keeps the AUTOMATION** — the harness-surface resolver, the Ship
  pre-task lifecycle phase, and the `HARNESS_READY`/`NO_HARNESS` state
  contract. After this unit, those are ordinary implementation tasks that a
  real installed actor can harness. `187-S` stops being self-referential.

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

* **No gate is suspended.** Both channels are observed.
* **No severity is lowered.** A failing observation halts the unit.
* **No evidence is assumed.** The postcondition
  (`Compilation: PASS`, `Red Phase: CONFIRMED`) is recorded from the run.
* **Nothing is skipped.** The only difference from steady state is *which copy
  of the procedure text the executor read* — and erasing that difference
  permanently is this unit's entire purpose.

A waiver produces **less** evidence than the policy demands. This produces
**exactly** the evidence the policy demands, from a template-resident
procedure, once.

### How RED and GREEN are produced during bootstrap

| Phase | Task | What is observed |
|---|---|---|
| RED authored | `182.001-T` | A conformance assertion that `.github/skills/harness-architect/SKILL.md` exists, carries valid YAML frontmatter with `name: harness-architect`, contains no unresolved `{{...}}` double-brace variable, and contains no unresolved single-brace suffix placeholder `{SUFFIX_FEATURE}` or `{SUFFIX_TASK}`. Authored to FAIL, because the skill is absent. **Admitted to the ready queue under the Claim bound.** |
| RED confirmed | `182.002-T` | The two P-004 commands are run verbatim. `py_compile` exits 0 (compilation channel). `unittest discover` exits non-zero and `182.001-T`'s assertion is present in the failure set with its expected marker (red-phase channel). Recorded to `.autoharness/harness-manifest.yaml`. `harness-ready` applied to this unit's remaining tasks. **This is the one and only exercise of the bootstrap authority, and the last task admitted under the Claim bound.** |
| GREEN | `182.003-T` | One commit generates the skill from its template. The assertion flips to passing. **Claimed under the ORDINARY P-002 label applied by `182.002-T` — not under the carve-out.** |
| VERIFY + EXPIRE | `182.004-T` | Installed/template parity re-derived; the expiry token emitted, terminating all five bounds. **Claimed under the ordinary label.** |

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
reads the *whole* discovered suite. This unit records **both** readings: the
scoped observation over its own declared harness set, and the unscoped suite
result exactly as returned. It does **not** redefine the precondition, and it
does **not** pre-empt `176-S`, which owns the scoping of the red-phase
precondition to the declared harness set and its three-channel observation.
If the two readings disagree, that disagreement is recorded as evidence and
the unit halts for operator disposition rather than choosing the convenient
one.

## The one-time boundary

The bootstrap authority is bounded on **five** independent axes. All five hold
simultaneously; none is sufficient alone. The first four bound **execution of
the harness-architect procedure**; the fifth bounds **admission to Ship's ready
queue**. They are stated separately because they are different permissions, and
folding either into the other would make one of them unauditable.

| Axis | Bound |
|---|---|
| **Scope** | Exactly the tasks of `188-S` / feature `182-F`. No other shipment, feature or task may invoke it, directly or by inheritance. |
| **Count** | Exercised exactly once, by `182.002-T`. Re-running `182.002-T` after expiry is prohibited. |
| **Deliverable** | Only `.github/skills/harness-architect/SKILL.md`, generated from its existing authoritative template. Generating any other absent surface is out of scope. |
| **Expiry** | Terminated by the emission of `HARNESS_ARCHITECT_INSTALLED` by `182.004-T`. |
| **Claim** | Exactly `182.001-T` and `182.002-T` may be admitted to Ship's ready queue and claimed without carrying the `harness-ready` label. No other task, feature or shipment, directly or by inheritance. Terminated by the same `HARNESS_ARCHITECT_INSTALLED` token. |

### The claim carve-out, and why it is a separate bound

P-002 is not only an evidence gate. Its live text gates **claiming**:

> **Gate Point**: Queue building (Step 2) and task claiming (Step 3)
> **Precondition** (ship): The task carries the `harness-ready` label.
> **Enforcement** (ship): Filter ready queue to only tasks carrying the
> `harness-ready` label.
> **Violation Action**: Halt and suggest running the harness-architect.

The only declared producer of `harness-ready` is the harness-architect — the
actor this unit installs. So before this unit runs, P-002's ordinary filter
admits **zero** tasks, and its Violation Action suggests running an actor that
does not exist. The first four bounds authorize `182.002-T` to *execute the
procedure*; none of them lets Ship *claim* `182.001-T` or `182.002-T` in the
first place. Without a fifth bound the shipment-level deadlock is simply
reproduced one layer down, at task claiming.

**The carve-out, stated exactly.** `182.001-T` and `182.002-T` — those two task
IDs and no others — may be admitted to Ship's ready queue and claimed without
the `harness-ready` label, for the stated reason that the label's only producer
is the actor under installation.

* **It authorizes admission and nothing else.** It confers no authority to
  execute the harness-architect procedure — that is the Count axis, exercised
  once by `182.002-T`. A task admitted under the carve-out gains no other
  permission of any kind.
* **It is not inheritable and not extensible.** It names two task IDs
  literally. No successor task, no other feature, no other shipment, and no
  future re-slice inherits it. Stage does not hold it and cannot widen or
  re-date it.
* **`182.003-T` and `182.004-T` are NOT covered.** `182.002-T` applies
  `harness-ready` to this unit's remaining tasks per the template's Step 6,
  before either is reached. They are admitted by the **ordinary** P-002 filter,
  which is the point: the carve-out is exhausted the moment the actor can do
  its own job.
* **It expires on the same token.** `182.004-T`'s emission of
  `HARNESS_ARCHITECT_INSTALLED` terminates all five bounds together. It is
  equally non-re-enterable, and for the same reason: after installation the
  label has a real producer, so the condition that justified the carve-out no
  longer exists.

**Why this is not a waiver of P-002.** P-002's Statement governs claiming *and
implementing*. Neither carved-out task implements anything: `182.001-T` authors
the failing assertion and writes no production code, and `182.002-T` produces
the full P-004 evidence and writes no production code. The only commit in this
unit, `182.003-T`, is claimed under the **ordinary** label, with the harness
authored and the red phase confirmed before it starts. No task is claimed whose
harness evidence is required and missing. Less evidence is not produced
anywhere.

**What it is not.** It is not a bootstrap grant — it consumes no
`.autoharness/bootstrap-grants/` file, writes none, and touches no force-audit
log. It is not a `--force` override. It is not an undocumented operator
exemption. It is not a policy edit: P-002's text is correct as written and is
not amended by this unit. It is a plan-declared, review-gated, token-expiring
exception recorded identically in this plan, in `182-F`, in `188-S`, in the
`182.001-T` and `182.002-T` records, and in decision `D9` at revision 3.

**After expiry, every unit routes through the installed actor — including a
re-run of this one.** If `188-S` must ever be re-executed, the installed skill
at `.github/skills/harness-architect/` already exists and is used; the
template-resident route is not re-entered and the claim carve-out is not
revived. The authority is therefore not merely time-boxed, it is **not
re-enterable**, because the condition that justified it (the actor's absence)
is exactly the condition this unit destroys.

**Stage cannot extend this authority and does not hold it.** It is declared in
a reviewed plan, exercised by Ship, and expires on a token. It is **not** the
`pre_claim` bootstrap grant described in `.github/agents/_ship.agent.md`; it
consumes no grant, writes no grant, and touches no force-audit log. No agent
may author, widen or re-date it.

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
| `182.001-T` | RED | author the harness-surface conformance assertion, observed failing | S | low |
| `182.002-T` | RED CONFIRM | exercise the one-time bootstrap authority: run both P-004 channels verbatim, record the manifest postcondition, apply `harness-ready` | S | medium |
| `182.003-T` | ACTIVATE | one commit: generate `.github/skills/harness-architect/SKILL.md` from its template, binding every variable from its named authoritative source | S | medium |
| `182.004-T` | VERIFY | re-derive installed/template parity, emit the expiry token | XS | low |

**Claim admission.** `182.001-T` and `182.002-T` are admitted under the Claim
bound, without `harness-ready`. `182.003-T` and `182.004-T` are admitted by the
ordinary P-002 filter, using the label `182.002-T` applies. No task is added,
removed, resized or resequenced by the carve-out.

Edges: `182.001-T` → `182.002-T` → `182.003-T` → `182.004-T`. Three edges, one
chain, no cycle, no successor task inside the unit.

## DAG position

`188-S` is a **DAG root**. It has no precursor shipment: it needs no operation
substrate, no transport decision, no isolation characterization and no schema
migration. It reads one template and writes one generated file.

It becomes the precursor of **every code-bearing implementation shipment** in
the portfolio:

```text
188-S ─┬─▶ 184-S (withheld — also gated on TRANSPORT_DECIDED)
       ├─▶ 185-S ─┬─▶ 186-S
       │          ├─▶ 178-S
       │          └─▶ 180-S
       ├─▶ 187-S
       └─▶ 176-S
```

It is **not** a precursor of `177-S`, `182-S` or `183-S`. Those three are DAG
roots and remain so:

* `182-S` and `183-S` are bounded spikes that land no production code — their
  deliverable is a findings artifact, and `176.001-T` states "NO production
  code" explicitly.
* `177-S` carries its own PREPARE/RED/VERIFY/ACTIVATE machinery: its five RED
  tasks author their own failing assertions and its `169.017-T` gate adjudicates
  them before activation. It consumes no `HARNESS_READY` from the Ship pre-task
  lifecycle.

Adding a bootstrap edge to any of those three would re-introduce the false
serial dependency that decision D8 withdrew.

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

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | The authority is read as a general precedent for skipping P-004, or the claim carve-out as a precedent for skipping P-002 | All five boundary axes are stated in the plan, in `182-F`, in `188-S`, in `182.002-T`'s record and — for the claim carve-out — in `182.001-T`'s record as well, and expiry is mechanical rather than narrative. |
| R6 | The claim carve-out is read as covering more than its two named tasks | It names `182.001-T` and `182.002-T` literally on every surface, states on each that `182.003-T` and `182.004-T` are excluded, and expires on the same token as the other four bounds. `182.002-T` applies `harness-ready` before either excluded task is reached, so the carve-out is exhausted rather than merely unused. |
| R7 | `UNIMPLEMENTED_MARKER` is improvised because it is derived rather than stored | The derivation names **both** install-harness surfaces and their distinct roles — `:335` supplies the key, `:130`'s `Example (Python)` column supplies the value — and the bound literal is fixed as a verbatim transcription rather than a value the executor composes. Unavailability is fail-closed on five mechanically evaluable triggers (F1–F5), including unsupported and ambiguous language mapping: no file is touched, no commit is made, and the unit returns to Stage rather than substituting a plausible marker. |
| R2 | The `harness-architect` template is stale relative to current skill conventions | `182.001-T`'s assertion validates frontmatter, `name`, and placeholder resolution. A stale template fails the assertion at `182.003-T` and never reaches `INSTALLED`. |
| R3 | The authority is exercised, then the unit stalls before expiry | `HARNESS_ARCHITECT_NOT_OBSERVED` is the fail-closed default; no successor may treat a missing token as satisfied. |
| R4 | The unscoped suite reading is non-zero for unrelated reasons, masking the red-phase signal | Both readings are recorded; disagreement halts for operator disposition rather than resolving in the passing direction. |
| R5 | A reader concludes the actor's installation also installed the lifecycle | `182-F`, `188-S` and this plan state the split explicitly, and `187-S` retains the automation in its own manifest. |

## Hardening review

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is this a waiver with extra words? | No. A waiver produces less evidence than the policy demands. This produces exactly the evidence P-004 names — both channels, recorded to the manifest — from a template-resident procedure. The gate is satisfied, not suspended. |
| H2 | What stops the authority being reused? | Five independent bounds: scope (this shipment's tasks), count (one task, once), deliverable (one named file), expiry (a token), and claim (two named task IDs, admission only). It is also not re-enterable, because installing the actor destroys the condition that justified it. |
| H3 | Could an agent widen or re-date the authority? | No. It lives in a review-gated plan and expires on a token emitted by a task, not on a date. Stage does not hold it and cannot extend it. It is not the `pre_claim` bootstrap grant and consumes none. |
| H4 | Why is `188-S` a root when `187-S` was not? | Because installing the actor requires reading one template and writing one file. It needs no substrate, no transport decision and no isolation result. `187-S` was not a root because its automation genuinely needs the substrate — that dependency was never the defect. |
| H5 | Does this let `187-S` become claimable early? | No. `187-S` keeps its `184-S` dependency, and `184-S` is withheld pending `TRANSPORT_DECIDED`. `188-S` removes the *self-bootstrap*, not the *substrate prerequisite*. |
| H6 | Is the red phase real, or a formality? | Real. `182.001-T`'s assertion fails against the current workspace for the intended reason — the skill is absent — and passes only after `182.003-T` generates it. The transition is observed on both sides. |
| H7 | Does this unit need the actor to harness itself? | Its single harness artifact is one conformance assertion over a generated file. `182.002-T` produces the P-004 **evidence** for it by executing the template-resident procedure. That is the evidence half; the **claim** half is answered separately at `H9`, because answering only this one is what left revision 1 blocked. |
| H8 | What if generation succeeds but produces a non-conforming skill? | `HARNESS_ARCHITECT_ABSENT`. No token is emitted, the unit halts, and no successor becomes claimable. |
| H9 | Does the authority reach P-002's CLAIM precondition, or only its evidence precondition? | At revision 1 it reached only the evidence precondition, and the unit was blocked for it. The fifth **Claim** bound closes it: `182.001-T` and `182.002-T` — exactly those two IDs — are admissible to Ship's ready queue without `harness-ready`. Every other task in the unit is admitted by the ordinary filter after `182.002-T` applies the label. |
| H10 | Could the claim carve-out be inherited, widened or reused as precedent? | No. It names two literal task IDs, confers admission only, expires on the same `HARNESS_ARCHITECT_INSTALLED` token as the other four bounds, and is non-re-enterable for the same reason. It is declared in a review-gated plan, not held by Stage, and no agent may author, widen or re-date it. It is not a grant, not a `--force` path, and not a policy edit. |
| H11 | Is the carve-out a waiver of P-002 wearing a different word? | No. P-002's Statement governs claiming *and implementing*. Neither carved-out task implements anything — one authors a failing assertion, the other runs two commands and records their output. The unit's only commit, `182.003-T`, is claimed under the ordinary label with the red phase already confirmed. No task anywhere is claimed with required harness evidence missing. |

### Blast radius

One new generated file under `.github/skills/`, one gitignored gate artifact,
and one recorded manifest postcondition. No Python module, no agent template,
no installed agent mirror, no policy text, no CI workflow. This is the
narrowest surface any unit in this portfolio touches — deliberately, because a
bootstrap authority should not be attached to a wide change.

### Rollback

`182.001-T`–`182.002-T` are inert (a failing test and a recorded observation).
`182.003-T` reverts as a unit: deleting the generated skill returns the
workspace to the pre-bootstrap state, and the conformance assertion returns to
failing, which is its authored state. The expiry token in
`.autoharness/gates/` is never committed and is re-derived rather than
restored. Rollback restores the deadlock rather than leaving a partial state —
which is correct, because a partially-bootstrapped actor is the one state no
consumer can interpret.

### Verification floor

`HARNESS_ARCHITECT_INSTALLED` and `HARNESS_ARCHITECT_ABSENT` both observed
reachable, and the failing side of `182.001-T` observed before the passing
side. A unit that has never observed its own failure state has not tested its
precondition.

**Claim-admission floor.** Before `182.001-T` starts, Ship records that both
carved-out tasks are admissible: each is named in the Claim bound, neither
carries `harness-ready`, and no other task is admitted without the label. After
`182.002-T` applies the label, Ship records that `182.003-T` and `182.004-T`
are admitted by the **ordinary** filter rather than by the carve-out. After
`182.004-T` emits `HARNESS_ARCHITECT_INSTALLED`, the carve-out is spent: any
subsequent admission decision — including a re-run of this unit — routes
through the ordinary `harness-ready` filter produced by the installed actor.
Each of those three observations is recorded; none is assumed.
