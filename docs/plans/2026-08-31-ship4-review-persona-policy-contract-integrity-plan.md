---
title: "SHIP-4 — Review-persona, policy, and agent-architecture contract integrity"
date: 2026-08-31
slug: review-persona-policy-contract-integrity
doc_type: plan
source_stash: "BA035180, C0EA1175, 701073F9, F0ADCC03, 7628C291"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-4"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-4 — Review-persona, policy, and agent-architecture contract integrity

## Problem

Five defects in the documents that define how review, policy enforcement, and
agent composition behave. All five are template-side; all five were deferred
under P-021 C1 from PRs #415/#417 and the `156-S` local review because the
templates were pre-existing content rather than the authorized change.

| ID | Defect | Source ref |
|---|---|---|
| `BA035180` | **Security reviewer suppresses findings not tied to the feature's declared purpose.** A concrete vulnerability introduced by the diff can be filtered out *before it is ever reported to the coordinator for disposition*. | `templates/agents/review/security-reviewer.agent.md.tmpl`; PR #417 Copilot review, HEAD `3450837f` |
| `C0EA1175` | **P-007's violation-remediation step instructs an automatic `git restore .backlogit/archive/` with no approval or safety-mode gate**, conflicting with Constitution Principle VII's destructive-command approval rule — `git restore` overwrites working-tree state. | `templates/policies/workflow-policies.md.tmpl`; Constitution Reviewer, local review `156-S`/`336F3AB7`, HEAD `b0c2f98a` |
| `701073F9` | **Constitution reviewer's checklist stops at Principle IX**, omitting Principle X (Agent Context Efficiency) and the NON-NEGOTIABLE Principle XI (Merge Commit History Preservation), both defined at `.github/instructions/constitution.instructions.md:76-86`. | `templates/agents/review/constitution-reviewer.agent.md.tmpl`; PR #417, HEAD `3450837f` |
| `F0ADCC03` | **A rendered reviewer cites a style guide that was never installed.** `.github/agents/subagents/python-reviewer.agent.md:68` references the workspace's `python.instructions.md`; `.github/instructions/python.instructions.md` does not exist. Dangling cross-reference **in the rendered artifact**. | `templates/agents/review/technology-reviewer.agent.md.tmpl` L56 → `.github/agents/subagents/python-reviewer.agent.md` L68; PR #417, HEAD `8b7dae51` |

**Corrected characterisation of `F0ADCC03` (review-fix cycle 1).** The original
statement of this defect was wrong in a way that would have produced the wrong
fix, and is corrected here on direct evidence:

* The **template is not defective**. `templates/agents/review/technology-reviewer.agent.md.tmpl:56`
  reads ``Reference the workspace's `{{PRIMARY_LANGUAGE_LOWER}}.instructions.md` as the
  authoritative style guide`` — a generic placeholder, not a hard-coded `python.instructions.md`.
* The **template → installed-name mapping is documented and correct**, not assumed.
  `.github/skills/install-harness/SKILL.md:1057` states that technology instructions install
  as `{language}.instructions.md` from the language variant template
  (`technology-python.instructions.md.tmpl` → `python.instructions.md`). The earlier plan text
  treated this mapping as an unverified assumption; it is a documented install contract, and
  this cycle verified it at that line.
* The **actual defect is a co-installation gap**: this workspace installed the technology
  *reviewer* for `PRIMARY_LANGUAGE=Python` without installing the matching technology
  *instruction*, so the rendered reference dangles. Nothing about the reference text is wrong.
* The defect is a **class, not an instance**. The identical shape exists at
  `.github/agents/subagents/agent-native-parity-reviewer.agent.md:57`, which references
  `mcp-server.instructions.md` (template present at `templates/instructions/mcp-server.instructions.md.tmpl`,
  installed file absent). See §Deferred scope.
| `7628C291` | **The leaf-executor rule is contradicted by two shipped skills.** `harness-architecture.instructions.md` L163 and `role-enforcement.instructions.md` L81 forbid skills from spawning subagents; `templates/skills/review/SKILL.md.tmpl` L33-35 declares its own *Subagent Depth Constraint* and L159 spawns five always-on personas. | Direct verification |

## Direction

`BA035180`, `701073F9`, `F0ADCC03` and `C0EA1175` are unambiguous — the documents
are wrong and the fixes are additive or subtractive edits to prose. `7628C291` is
an architecture decision, taken as **D4** in the portfolio deliberation and
restated here as binding:

> **Amend the two instruction templates to state a bounded, explicit one-hop
> exception for the review family. Do not change skill behaviour.**

Making the skills conform would delete the multi-persona adversarial review
capability the whole pipeline depends on, to satisfy prose. The shipped skill
already carries the correct bound ("maximum depth: review skill → persona
subagent, 1 hop"; personas may not spawn). The rule is wrong, not the code.

The exception must be **bounded, not general**: named review-family skills only,
depth 1, spawned subagents remain leaf executors, and the P-013.5
model-inheritance clause is unchanged — persona subagents still declare no
`model_family`/`model_provider`/`reasoning_effort` frontmatter of their own and
still inherit the invoking agent's route.

## Hardening (P-006)

Triggered: security-persona semantics, policy text, and an architecture-rule
amendment.

* **H1 (binding).** `BA035180` removes the *purpose-based exclusion* only. The
  concrete-location requirement and the confidence requirement are **retained** —
  they are what keep the persona from emitting speculative noise. Removing them
  would trade one failure mode for a worse one.
* **H2 (binding).** `C0EA1175` must not simply delete the remediation step. P-007
  needs a remediation path; the fix is to gate it behind explicit operator
  approval (and to make the gate honour whatever safety-mode signal the workspace
  already exposes), not to leave the violation unremediable.
* **H3 (binding).** `7628C291`'s amendment is an **enumerated allowlist**, not a
  general "skills may spawn subagents when useful". A general relaxation would
  make depth unbounded and defeat the rule entirely.
* **H4 (binding).** Every template edited here has an installed dogfood mirror
  under `.github/`. Template and mirror must move together, and manifest
  checksums must be refreshed in the same shipment, or `verify-harness` breaks.
* **H5 — SUPERSEDED by the explicit decision in §Decision F: `F0ADCC03` reference
  strategy.** The earlier "install it or repoint it, installing preferred" wording
  left the strategy unchosen and therefore unharvestable. It is decided below.

## Decision F — `F0ADCC03` install path and reference strategy (binding)

The three candidate strategies, and why two are rejected:

| Strategy | Verdict |
|---|---|
| **(a) Install `python.instructions.md` into this repository** | **Rejected.** It treats one instance of a class defect. It also adds a tracked artifact that requires install-unit registration and a manifest entry for a consumer that only exists because of a rendering accident, and it would not stop the next reviewer/instruction pair from dangling. |
| **(b) Repoint the reference to `technology-python.instructions.md`** | **Rejected — it would be factually wrong.** `technology-python.instructions.md` is a *template* filename. The installed filename is `python.instructions.md` per `.github/skills/install-harness/SKILL.md:1057`. Repointing would create a reference that resolves in **no** workspace. |
| **(c) Co-installation invariant + graceful reference** | **ADOPTED.** |

**Decision F (binding).** Adopt (c), in two parts. *Restated in review-fix cycle 1
(Orchestrator local-review finding 11) to remove a contradiction: the earlier text
required the reviewer to be withheld when no language instruction resolved, while
simultaneously asserting that this repository's reviewer "degrades". Both could not
hold. The contract below defines three non-overlapping conditions, each with exactly
one disposition.*

| # | Condition | Disposition |
|---|---|---|
| **A** | `PRIMARY_LANGUAGE = L` is declared **and** the technology-reviewer is selected for the composition | **F1 co-installation.** Install `{L}.instructions.md` in the same composition. |
| **B** | The technology-reviewer is **not** selected | Nothing to install and nothing to reference. Out of Decision F entirely. |
| **C** | An **already-composed** workspace carries a technology-reviewer with no matching instruction file | **F2 graceful reference.** The rendered reviewer degrades to generic coding-discipline guidance. **This repository is Condition C.** |

* **F1 — install-harness co-installation invariant (Condition A).**
  `.github/skills/install-harness/SKILL.md` step 1057 is amended to state, as a MUST:
  when `technology-reviewer.agent.md.tmpl` is rendered for `PRIMARY_LANGUAGE = L`, the
  matching `{L}.instructions.md` MUST be installed in the same composition — from
  `technology-{L}.instructions.md.tmpl` when a variant exists, otherwise from the
  generic `technology.instructions.md.tmpl` skeleton. If **neither** template exists in
  the template set, the composition **halts with a named error** identifying both
  missing templates. It does **not** silently drop the reviewer, and it does **not**
  silently install a dangling one. *(Measured: this repository's template set contains
  `technology-{go,python,rust,typescript}.instructions.md.tmpl` **and** the generic
  `technology.instructions.md.tmpl`, so the halt branch is unreachable here and exists
  only to fail closed on a broken template set.)*
* **F1-scope — F1 is forward, at composition time, and is not retroactive.** F1
  governs what `/install-harness` **does when it composes a workspace**. It does not
  re-compose workspaces that already exist, and this shipment does not run a
  composition against this repository. That is what makes Condition C a real, ongoing
  case rather than a transitional one.
* **F2 — graceful reference text (Condition C).**
  `templates/agents/review/technology-reviewer.agent.md.tmpl:56` keeps the
  `{{PRIMARY_LANGUAGE_LOWER}}.instructions.md` placeholder — it is correct — and gains
  an explicit fallback clause so a rendered reviewer whose composition ships no
  language instruction degrades to the generic coding-discipline guidance instead of
  citing a file that is not there. **F2 alone closes `F0ADCC03`** for this repository:
  re-rendering the mirror at `.github/agents/subagents/python-reviewer.agent.md`
  removes the dangling reference **without** creating `python.instructions.md`.

**Explicitly NOT part of Decision F:** no `python.instructions.md` is created in this
repository by this shipment. Because F1 is forward-only (F1-scope) and F2 closes the
dangling reference on its own, this repository ends the shipment **consistent** —
Condition C, reviewer installed, reference graceful, nothing dangling — rather than
either *broken* (reviewer dangles) or *withheld* (reviewer silently missing). Whether
this repository should **additionally** install a Python instruction file is a
composition choice for a later run, captured as deferred entry `9B5FD7D5`.

**Propagation.** F1, F1-scope, and F2 are carried into task 4's acceptance criteria
verbatim; harvested task `154.004-T` restates all three and is gated on them.
Task 4's acceptance additionally requires a **negative assertion**: after re-render,
`.github/agents/subagents/python-reviewer.agent.md` contains **no** unconditional
reference to a non-existent `.github/instructions/python.instructions.md`, and
`.github/instructions/python.instructions.md` is **still absent** — proving the fix
was F2's graceful reference, not an accidental slide into rejected strategy (a).

## Decision G — P-007 destructive-restore authorization (binding, REVISED in cycle 2)

Plan review finding 2 gated the P-007 `git restore` remediation behind "explicit operator
approval" without naming what that approval *is*. An unnamed approval is unverifiable, so the
gate would have been prose that any agent could self-satisfy. Cycle 1 named a **backlogit
comment** as the approval artifact.

**That is withdrawn as the authorization source.** `backlogit_append_comment` /
`backlogit append-comment` is an operation **the executing agent itself can call**. An agent
could write `APPROVAL: P-007-ARCHIVE-RESTORE …` onto the shipment and then read its own writing
back as authorization. A gate whose token the gated party can mint is not a gate — it is the
same self-satisfiable shape cycle 0 was trying to remove, relocated one layer down. The
tool-owned, auditable properties cycle 1 relied on are real, but they establish
**non-repudiation of a record**, not **independence of an authority**.

* **G1 — the authorization source is a direct runtime operator approval.** Authorization is a
  **live approval result** obtained at the moment of the request over an **independent operator
  channel the executing agent cannot synthesize**: the intercom approval/clearance operation, an
  interactive operator ask/confirm prompt, or the operator session channel. The defining
  property is **non-synthesizability** — the approving act originates outside the agent's own
  writable surface, and the agent has no operation that produces the affirmative result on its
  own behalf.
* **G2 — the backlog comment is evidence only, never authority.** *After* a G1 result is
  obtained, the agent SHOULD record an `APPROVAL: P-007-ARCHIVE-RESTORE` comment on the shipment
  item carrying the shipment ID, the exact archive paths, the operator actor identity, the
  approval timestamp, and **the channel the approval came over**. That record exists for audit
  and traceability. It MUST NOT be read back as authorization, MUST NOT substitute for a live G1
  result, and MUST NOT cache, shorten, or pre-satisfy any future approval — each remediation
  attempt requires its own fresh G1.
* **G3 — no independent channel means halt, do not restore.** When no independent approval
  channel is available — intercom degraded or unreachable, no interactive operator session,
  ask/confirm unavailable, or the channel present but unanswered — the agent **halts and does
  not restore**. Absence of a channel is never implicit approval and never a fallback to the
  comment path. The ungated path is unchanged and mandatory: detect the violation, halt, record
  it through P-005 telemetry with the exact remediation command for a human to run, and leave
  the working tree untouched.
* **G4 — dark-mode behaviour is fail-closed (preserved).** In dark-factory/AFK mode no operator
  is present to give a G1 approval, so `git restore` **never runs**. A dark-mode run always
  reports and never restores — the Principle VII-conformant outcome, not a degradation, and the
  answer to cycle-0 finding 2's AFK-stall objection. Cycle 2 *strengthens* this: G3 makes "no
  channel" a halt in **all** modes, so dark mode becomes the specific case of a general rule
  rather than a special exception.
* **G5 — verification is a read of a live result, not an inference.** The agent must match the
  approval result to the current shipment ID and the exact archive paths. Mismatch, absence,
  ambiguity, timeout, or an unreadable channel is a **refusal**, never a pass.
* **G6 — no admin authority is invented.** G1 is an operator-performed act the agent merely
  receives. The agent cannot create it, cannot mark it satisfied on its own behalf, and gains no
  new authority. Merge preauthorization does not imply destructive-command preauthorization.
* **G7 — deterministic negative tests (mandatory acceptance, four cases).** Task 2 ships tests
  driving the P-007 remediation path, each observed red before the gate exists (**H7**):
  (i) **no approval of any kind** — assert no `git restore` is issued, the violation is
  recorded, and the exit is a refusal; (ii) **approval with a non-matching shipment ID** —
  assert the same refusal; (iii) **self-authored-comment coverage (the defect this revision
  closes)** — a well-formed, fully-matching `APPROVAL: P-007-ARCHIVE-RESTORE` comment authored
  by the executing agent itself, with **no** live G1 approval — assert the remediation **still
  refuses**, no `git restore` is issued, and the refusal explicitly states that a backlog
  comment is evidence only and not an authorization source; (iv) **no independent channel
  available** with any combination of comments present — assert halt without restore per
  G3/G4.
* **G8 — the refusal message** names the missing authorization channel and the exact command a
  human can run themselves, so a legitimate operator is never stranded without a remedy.
* **G9 — no new approval store, file format, or CLI is introduced.** G1 uses approval channels
  the harness already has; G2 uses the existing tool-owned comment surface for audit only.

* **H6 (binding).** Every task in this shipment enters safety mode
  `careful` (`.github/skills/safety-modes` equivalent; the skill is template-only in this
  workspace, so the mode is entered as an explicit declared posture rather than by skill
  invocation). Task 2 additionally enters `freeze-scope` bounded to
  `templates/policies/workflow-policies.md.tmpl` and its `.github/policies/` mirror, because it
  edits policy text that governs other agents' destructive behaviour.
* **H7 (binding) — contract tests for new behaviour.** Tasks 2, 3 and 4 each introduce new
  *behaviour* (an approval gate, a depth-constraint property, a co-installation invariant), so
  each ships a contract test demonstrated **red before green**. A test written after the change
  and never observed failing does not satisfy this.

## Decision H — the leaf-executor exception is a *bounded verifier*, not a claim (binding)

Plan review finding 3 resolved the maintenance-trap objection by asserting the exception could
be stated as "a machine-checkable condition". That was **overclaimed**: as written it was
self-declared prose, and nothing read it. Prose that calls itself machine-checkable is worse
than prose that admits it is prose, because it stops anyone from building the check. Corrected:

* **H-a — the exception is stated as a property with a fixed, checkable form.** A skill
  qualifies for the one-hop review-family exception iff its `SKILL.md` contains a
  `## Subagent Depth Constraint` section whose body states (i) a maximum depth of 1 hop and
  (ii) that spawned subagents are leaf executors that MUST NOT spawn further subagents.
  Current members (`plan-review`, `review`) are listed as **examples**, never as the definition.
* **H-b — a bounded verifier makes it real (mandatory acceptance on task 3).** Extend the
  **existing** `tests/` suite with one test that, over `.github/skills/*/SKILL.md` and
  `templates/skills/*/SKILL.md.tmpl`, asserts exactly three properties:
  1. **Undeclared spawning is detected.** Any skill whose text spawns a subagent (the documented
     spawn forms) **without** a conforming `## Subagent Depth Constraint` section is a FAILURE.
     This is the detector the original wording promised and did not deliver.
  2. **Constraint form is valid.** A `## Subagent Depth Constraint` section that does not state
     both the depth bound and the leaf-executor clause is a FAILURE (malformed constraint).
  3. **Depth is valid.** A declared depth other than 1 is a FAILURE. Depth > 1 is exactly the
     unbounded-nesting outcome **H3** forbids.
* **H-c — bounded by construction; this is not a new runtime framework.** The verifier is a
  single test in the existing `unittest` suite. It performs **static text inspection of
  `SKILL.md` files only**. It introduces **no** runtime interception, **no** spawn-time
  enforcement, **no** new CLI surface, **no** new package, and **no** agent-runtime hook. It
  cannot observe actual runtime spawning and does not claim to.
* **H-d — the residual governance limitation is recorded, not hidden.** The verifier checks
  *declarations in skill text*. An agent that spawns a subagent at runtime **without** it being
  visible in `SKILL.md` text is **not detected**. The exception is therefore enforced at the
  **document layer only**. Task 3's acceptance requires this limitation to be written into the
  amended instruction text itself, so the next reader is not misled the way this plan's first
  draft was. Runtime enforcement is out of scope and is recorded in §Deferred scope.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Remove the purpose-based finding-suppression rule from the security-reviewer persona | S | medium | `templates/agents/review/security-reviewer.agent.md.tmpl` + mirror |
| 2 | Gate the P-007 `git restore` remediation behind the named `APPROVAL: P-007-ARCHIVE-RESTORE` signal, and complete the constitution-reviewer principle checklist | M | medium | `templates/policies/workflow-policies.md.tmpl`, `templates/agents/review/constitution-reviewer.agent.md.tmpl` + mirrors, `tests/` |
| 3 | Resolve the leaf-executor contradiction with a bounded one-hop review-family exception **and ship the bounded depth-constraint verifier** | M | medium | `.github/instructions/harness-architecture.instructions.md` (direct — not template-backed, see below), `templates/instructions/role-enforcement.instructions.md.tmpl` + mirror, `tests/` |
| 4 | Close the technology-reviewer → language-instruction dangling reference via the Decision F co-installation invariant | S | low | `.github/skills/install-harness/SKILL.md`, `templates/agents/review/technology-reviewer.agent.md.tmpl` + mirror, `tests/` |

**Authoring-surface correction (review-fix cycle 1).** The two instruction
artifacts amended by task 3 **do not share an authoring surface**, and the
original wording ("amend the two INSTRUCTION templates") wrongly implied they
did. `role-enforcement.instructions.md` is template-backed — its manifest entry
names `template: "instructions/role-enforcement.instructions.md.tmpl"` — so it
is amended at the template and re-rendered to its installed mirror.
`harness-architecture.instructions.md` is **not** template-backed: it is the
sole manifest entry whose template field reads
`template: "global instruction definition"`, and
`templates/instructions/harness-architecture.instructions.md.tmpl` **does not
exist**. It is therefore amended directly at
`.github/instructions/harness-architecture.instructions.md` with a manifest
checksum refresh. A `.tmpl` **must not** be invented for it — that would fork
the artifact from its declared install contract. This is the same defect class
as the wrong-installed-path finding corrected in `154.001-T`.

**Split recorded (review-fix cycle 1).** The original task 3 bundled the
architecture-rule amendment with the dangling-reference fix. Plan review finding 4
accepted that bundling on manifest-churn grounds; that trade is **reversed** here.
The two halves have different blast radii — one amends a governance rule that
constrains every skill in the harness, the other corrects one install contract —
and bundling them makes the governance amendment **unrevertable without also
reverting the reference fix**. Revertability outranks one extra checksum refresh
on a change of this class. They are now tasks 3 and 4, sequenced 3→4 so the
manifest refresh in 4 lands last.

Tasks 2, 3 and 4 each ship the contract test **H7** requires. Task 1 remains
isolated because it is the only one with security-persona semantics.

## Non-goals

* No change to what the security reviewer *reports on* beyond removing the
  exclusion — no new detector classes, no new severity scheme.
* No change to P-007's violation *detection*; only its remediation gating.
* No general relaxation of the leaf-executor rule (**H3**).
* No change to P-013.5 model inheritance.
* No new review persona.
* **No runtime spawn enforcement.** The **H-b** verifier is static text inspection only
  (**H-c**, **H-d**).
* **No new `python.instructions.md` in this repository** (**Decision F**).

## Deferred scope (P-021, captured not silently broadened)

**Ref column = backlogit stash entry ID.** Each row below is backed by a compliant
P-021 C2 capture-only stash entry carrying the literal `DEFERRED SCOPE EXPANSION`
token, the expansion statement, the C1 out-of-scope reasoning, per-field source
refs, a `requires deliberation: true` flag, and kind + provisional priority. Read
one with `backlogit stash get <id>`. These IDs replace the pseudo-IDs used in the
first draft, which were in-plan labels with no backing stash record (a P-021 C2
shortfall corrected in review-fix cycle 1).
Three items surfaced during review-fix cycle 1 that require **new product capability** rather
than completion of this staged contract. Each is captured with its residual risk; none is
built here.

| Ref | Capture | Residual risk if never built |
|---|---|---|
| 24374649 | `.github/agents/subagents/agent-native-parity-reviewer.agent.md:57` references `mcp-server.instructions.md`, which is not installed — the same class as `F0ADCC03`. Decision F's co-installation invariant covers the *technology-reviewer* pair only; a general agent→instruction reference check is a new detector. | **Medium.** One rendered reviewer continues to cite a non-existent style guide. Behaviour degrades silently (the reviewer proceeds without the guide); it does not fail closed. Bounded to one subagent, and the parallel agent→**skill** check landing in SHIP-5 task 2 establishes the detector shape a later run can extend. |
| A4DAC571 | Runtime enforcement of the subagent depth constraint. **H-b** enforces at the document layer only (**H-d**). A spawn that never appears in `SKILL.md` text is undetectable by any static check. | **Medium-low.** Depth violations remain possible at runtime and are caught only by review. Accepted deliberately: a runtime interception layer is an unbounded new framework and is exactly what **H-c** refuses to start here. |
| 05877865 | A parity check between `constitution.instructions.md`'s principle list and the constitution-reviewer's checklist (carried forward from plan review finding 6). Owned by portfolio unit **S3** (D-PAR). | **Low.** The two can drift again. Task 2 resyncs them now; S3 owns the detector. |
| 9B5FD7D5 | Recompose **this** dogfood workspace under Decision F1 — install `.github/instructions/python.instructions.md` alongside the already-installed `python-reviewer`, with install-unit registration and a manifest checksum. Rejected strategy (a) by name; F1-scope makes F1 forward-only, so this repository stays Condition C. *(Added in review-fix cycle 1: Decision F claimed this was "recorded in §Deferred scope" but no row and no backing stash entry existed.)* | **Low.** F2's graceful reference closes the `F0ADCC03` dangling reference either way. What remains is only that this workspace's Python reviewer operates without a Python-specific style guide — a capability gap, not a broken reference. |

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`
(manifest checksum validation); markdownlint on every changed markdown surface;
a render check confirming no unresolved `{{...}}` in any regenerated artifact.

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Security | **P1** | Removing the purpose-based exclusion will increase security-reviewer output volume; if the coordinator has no disposition path for out-of-scope findings, reviewers will start ignoring the persona and the fix becomes net-negative. | **Resolved.** The disposition path already exists and is P-021: an out-of-scope security finding is *captured* as a deferred scope expansion, not silently dropped. Task 1's acceptance requires the persona text to say exactly that — **report first, classify scope afterwards** — so the increased volume lands in a defined channel. |
| 2 | Constitution | **P1** | Gating P-007 remediation behind operator approval makes P-007 unenforceable in dark-factory/AFK mode, where no operator is available — converting an automatic remediation into a permanent stall. | **Resolved.** The gate is on the **destructive `git restore`** only. Task 2's acceptance requires the ungated path to remain: *detect, halt, and record the violation with the exact remediation command*. Under Principle VII a destructive command needs approval; recording the violation and halting does not. AFK mode therefore still detects and reports — it just does not silently overwrite working-tree state, which is precisely the behaviour Principle VII forbids. |
| 3 | Architecture | **P1** | An enumerated allowlist of review-family skills is a maintenance trap — a new review-family skill added later silently violates the rule again. | **Resolved.** Task 3's acceptance requires the exception to be stated as a **property** ("skills that declare a `## Subagent Depth Constraint` section bounding depth to 1, whose spawned subagents are leaf executors") with the current members listed as *examples*, not as the definition. A future skill qualifies by declaring the constraint, which is a machine-checkable condition rather than a list to remember. |
| 4 | Maintainability | P2 | Task 3 bundles an architecture-rule amendment with a dangling-reference fix. | Accepted: both are instruction-template edits sharing one mirror-and-checksum refresh, and the dangling-reference half is `S`/low on its own. Splitting would triple the manifest churn for no review benefit. |
| 5 | Template integrity | P2 | Installing `python.instructions.md` as a new tracked artifact could break `verify-harness` if the install unit is not registered. | **H5**; task 3's acceptance includes the install-unit registration and the manifest entry, gated by `verify-harness`. |
| 6 | Schema/CLI/docs coupling | P2 | The constitution reviewer's checklist and `constitution.instructions.md` can drift again. | Recorded as a P-021 capture candidate: a parity check between the principle list and the reviewer checklist belongs to portfolio unit **S3** (D-PAR, enumeration agreement), which already owns exactly this detector class. Not built here. |
| 7 | Correctness | P3 | Principle XI is NON-NEGOTIABLE; adding it to a checklist that the persona may treat as advisory could weaken it. | Task 2's acceptance requires Principle XI to carry its NON-NEGOTIABLE marker verbatim in the checklist entry. |

**Verdict: PASS.** 3 P1 raised, all 3 resolved. Zero unresolved P0/P1. Two
review-fix cycles of three.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
This run operates in dark-factory mode with `agent-intercom` unavailable and no reviewer
subagent dispatch surface probed available; every selected persona was covered inline against
the Persona Rubric Adapter and all findings were normalized to the P0–P3 scale. No persona was
skipped. This is a **declared** degradation, recorded before the gate decision, not a silent
fallback.

**Plan hardening (P-006): required — `yes`. Satisfied.** Hardening constraints **H1**–**H7**
plus Decisions **F**, **G**, and **H** are present and binding, and every one is propagated
into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Security | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Constitution | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Architecture | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Correctness | inline persona pass | 1 P3 (cycle 0), 1 P1 (cycle 1) |
| Maintainability | inline persona pass | 1 P2 (cycle 0) |
| Template integrity | inline persona pass | 1 P2 (cycle 0) |
| Schema/CLI/docs coupling | inline persona pass | 1 P2 (cycle 0) |
| Scope boundary | inline persona pass | 1 P2 (cycle 1) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 8 | Correctness | **P1** | The plan asserted the reference fix "assumes `technology-python.instructions.md` reaches `python.instructions.md`" without ever verifying it, and mis-stated the template as hard-coding `python.instructions.md`. Both would have produced the wrong fix. | **Resolved.** Verified at `.github/skills/install-harness/SKILL.md:1057` (documented mapping) and `templates/agents/review/technology-reviewer.agent.md.tmpl:56` (generic `{{PRIMARY_LANGUAGE_LOWER}}` placeholder). The defect is restated as a co-installation gap and the strategy is fixed by **Decision F**, propagated into task 4. |
| 9 | Security | **P1** | "Explicit operator approval" for the P-007 `git restore` named no artifact, so the gate was self-satisfiable prose. | **Partially resolved by Decision G (cycle 1)**, and **fully resolved in cycle 2 by finding 14** — the named artifact chosen in cycle 1 was itself agent-authorable, so the self-satisfiability was relocated rather than removed. |
| 10 | Architecture | **P1** | The leaf-executor exception was called "machine-checkable" while being self-declared prose that nothing read. | **Resolved by Decision H.** A bounded static verifier (**H-b**) detects undeclared spawning, malformed constraint form, and invalid depth. Its limits are stated explicitly (**H-c**/**H-d**) so no machine-enforcement claim survives beyond what the test actually does. |
| 11 | Constitution | **P1** | The plan carried no explicit safety-mode declaration despite editing policy text that governs other agents' destructive behaviour. | **Resolved by H6**: `careful` for every task; `freeze-scope` on the policy surface for task 2. |
| 12 | Maintainability | P2 | Bundling the architecture-rule amendment with the dangling-reference fix makes the governance amendment unrevertable on its own. | **Resolved.** Cycle 0's finding 4 is reversed; tasks 3 and 4 are now separate, sequenced 3→4. |
| 13 | Scope boundary | P2 | `mcp-server.instructions.md` is the same defect class and could pull a general reference checker into this shipment. | **Resolved.** Captured as `24374649` with residual risk. Decision F is bounded to the technology-reviewer pair. Not built here. |

**Verdict: PASS.** Cycle 1: 4 P1 raised, all 4 resolved; 2 P2 raised, both
dispositioned. Cumulative: **zero unresolved P0/P1**.

### Review-fix cycle 2 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 14 | Security | **P1** | **The Decision G approval artifact was authorable by the gated party.** G1 designated a backlogit comment written via `backlogit_append_comment` as the authorization signal — but that is an operation the executing agent can call. The agent could write a perfectly well-formed, shipment-matching `APPROVAL: P-007-ARCHIVE-RESTORE` comment and then satisfy G2 by reading its own writing. The gate was therefore still self-satisfiable; cycle 1 moved the defect one layer down rather than closing it. Being tool-owned and auditable gives **non-repudiation of a record**, which is not **independence of an authority**. | **Resolved by G1–G9.** The authorization source is now a **direct runtime operator approval** — a live result over an intercom/ask/operator-session channel the agent **cannot synthesize** — and the backlog comment is demoted to **evidence only**, explicitly forbidden from being read back as authorization or from caching a future approval. **G3** makes an unavailable channel a **halt without restore** in all modes, never an implicit approval and never a fallback to the comment path. **G7(iii)** adds the specific **self-authored-comment negative test**: a fully-matching agent-written comment with no live approval must still refuse, and the refusal must say why. **G4** preserves the dark/AFK fail-closed behaviour verbatim, now as a special case of the general G3 rule rather than a standalone exception. **G6** re-affirms that no admin authority is created. |
| 15 | Constitution | P2 | Cycle 1's G3 justified dark-mode no-restore by the *absence of an operator to record a comment*. With the comment demoted to evidence, that justification no longer carries the conclusion on its own. | **Resolved.** G4's dark-mode rule is re-derived from **G3**: no independent approval channel exists in AFK mode, therefore no G1 result can exist, therefore no restore. The conclusion is unchanged and now rests on a stronger premise. |

**Verdict: PASS.** Cycle 2: 1 P1 and 1 P2 raised, both resolved. Cumulative:
**zero unresolved P0/P1**. Three review-fix cycles of three consumed; the next
review is the final independent disposition cycle.
