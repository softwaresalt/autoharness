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
| `F0ADCC03` | **Python reviewer cites a style guide that was never rendered.** It references the workspace's `python.instructions.md`, but only `templates/instructions/technology-python.instructions.md.tmpl` exists — no `.github/instructions/python.instructions.md` has ever been installed. Dangling cross-reference. | `templates/agents/review/technology-reviewer.agent.md.tmpl`; PR #417, HEAD `8b7dae51` |
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
* **H5.** `F0ADCC03` may be resolved either by installing the instruction file as
  its own tracked install unit or by repointing the reference. Installing is
  preferred — the template exists and a Python style guide is genuinely useful —
  but installing adds a new tracked artifact, so the install-unit registration
  and the manifest entry are part of the task, not an afterthought.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Remove the purpose-based finding-suppression rule from the security-reviewer persona | S | medium | `templates/agents/review/security-reviewer.agent.md.tmpl` + mirror |
| 2 | Gate the P-007 `git restore` remediation behind explicit operator approval, and complete the constitution-reviewer principle checklist | M | medium | `templates/policies/workflow-policies.md.tmpl`, `templates/agents/review/constitution-reviewer.agent.md.tmpl` + mirrors |
| 3 | Resolve the leaf-executor contradiction with a bounded one-hop review-family exception, and close the python-reviewer dangling reference | M | medium | `templates/instructions/harness-architecture.instructions.md.tmpl`, `templates/instructions/role-enforcement.instructions.md.tmpl`, `templates/instructions/technology-python.instructions.md.tmpl` + mirrors + manifest |

Tasks 2 and 3 each pair two defects that share a review surface and a mirror/
checksum refresh, keeping each task inside the 2-hour rule while avoiding three
separate checksum churns. Task 1 is isolated because it is the only one with
security-persona semantics and warrants its own security review.

## Non-goals

* No change to what the security reviewer *reports on* beyond removing the
  exclusion — no new detector classes, no new severity scheme.
* No change to P-007's violation *detection*; only its remediation gating.
* No general relaxation of the leaf-executor rule (**H3**).
* No change to P-013.5 model inheritance.
* No new review persona.

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
