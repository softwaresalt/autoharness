---
title: "SHIP-6 — Template variable-resolution correctness"
date: 2026-08-31
slug: template-variable-resolution-correctness
doc_type: plan
source_stash: "D00CB293, 57A43F55"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-6"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-6 — Template variable-resolution correctness

## Problem

Two defects in the template authoring and variable-resolution layer. Both render
text that is *syntactically* fine and *semantically* wrong, which is why neither
is caught by the existing unresolved-`{{...}}` scan.

### D00CB293 — unconfigured-gate sentinel strings are emitted as tool names

`.github/skills/fix-ci/SKILL.md:13` renders text of the form "the configured
quality gate …" where the interpolated value is a **sentinel comment string**
standing for *"no gate is configured"*. The rendered prose then instructs the
agent to verify that string is on `PATH`. An agent following the instruction
literally searches for a tool whose name is a comment.

The defect lives in the template authoring and variable-resolution layer that
produced the text, **not** in the installed copy. Patching
`.github/skills/fix-ci/SKILL.md` in place would diverge the installed artifact
from its template and be silently reverted by the next install or tune run.
Deferred under P-021 C1 from PR #409, whose authorized change was installing the
13 pipeline skills from existing templates.

### 57A43F55 — tool-scoped branches render the *active* tool's values

Skill templates use the generic `{{OP_CREATE_MCP}}` / `{{STATUS_*}}` variables
**inside branches explicitly scoped to a non-active backlog tool**. A branch
introduced by "When backlog-md is the installed backlog tool" is rendered with
**backlogit** values whenever backlogit is the active registry — which is every
workspace in practice. The branch is therefore wrong in every workspace it
appears in, including the one where it is supposed to be the fallback.

Deferred under P-021 C1 from PR #409: correcting the *rendered output* of the
installed artifacts was the same contract surface and was fixed in place;
changing the **template variable scheme** is template-authoring architecture.

Note the coupling to decision **D3** (portfolio deliberation): the escape hatch
`56803680` option (a) would have provided — "eliminate the second tool entirely
and the trap disappears" — is **not available**, because D3 selected keep-but-
demote. `57A43F55` therefore needs its real fix, here.

## Direction

**`D00CB293`: omit, do not interpolate.** When a gate is unconfigured, the
rendering must drop the entire clause — the sentence, its list item, and any
surrounding instruction — rather than substituting a placeholder into prose that
presumes a gate exists. The sentinel string must never reach rendered output.

**`57A43F55`: resolve tool-scoped variables against the branch's tool, not the
active tool.** Two shapes were considered:

* **(A) Per-tool tokens** — introduce `{{OP_CREATE_MCP_BACKLOG_MD}}`,
  `{{STATUS_QUEUED_BACKLOG_MD}}`, … alongside the active-tool tokens.
* **(B) Installer-resolved conditional block** — make the tool-scoped branch a
  block the installer resolves per tool, so the generic tokens inside it bind to
  that block's tool.

**Selected: (B), with (A) rejected.** (A) multiplies the variable table by the
number of supported tools, and every new token is a new opportunity for the
unresolved-`{{...}}` class. (B) keeps one token set and makes the *binding
context* explicit, which is also the shape that generalises if a third registry
is ever added. (B) additionally makes the defect *detectable*: a tool-scoped
block with no declared tool binding is a structural error the renderer can
reject, whereas under (A) using the wrong token is indistinguishable from using
the right one.

## Hardening (P-006)

Triggered: template variable scheme change, cross-cutting across template
families.

* **H1 (binding).** Fail closed on an unbound tool-scoped block. If a block
  declares a tool the registry set does not contain, or declares none, rendering
  must **error** rather than fall back to the active tool. Silent fallback is the
  present defect.
* **H2 (binding).** No unresolved `{{...}}` may survive in any rendered artifact,
  for **every** supported tool binding — not only the active one. This is the
  existing repository invariant and the change must not weaken it.
* **H3 (binding).** Existing templates that do **not** use tool-scoped blocks must
  render byte-identically before and after. The change is opt-in at the block
  level; a whole-corpus render diff is the acceptance evidence.
* **H4.** No schema change, no registry-file change, no change to which tools are
  supported. This shipment changes only how a template *expresses* a tool-scoped
  branch.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Omit unconfigured quality gates from rendered output instead of interpolating sentinel strings | M | medium | template rendering + `templates/skills/fix-ci/SKILL.md.tmpl` and peers |
| 2 | Resolve tool-scoped template branches against the branch's declared tool, with fail-closed binding and a whole-corpus render-parity test | M | high | `src/autoharness/` renderer, affected skill templates, `tests/` |

Two tasks, not three: the render tests for both classes are the acceptance
evidence for their own task and do not constitute separable work. Task 2 carries
the corpus-parity test because **H3** is its own riskiest property.

## Non-goals

* No per-tool token proliferation (option A, rejected).
* No change to the supported-tool set — that is D3's territory and it decided
  keep-but-demote.
* No repair of `.github/**` installed copies by hand. Both fixes are
  template-first; installed artifacts are regenerated.
* No new quality gates. Task 1 changes how an *unconfigured* gate renders, not
  which gates exist.

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`;
whole-corpus render for each supported tool binding, asserting (a) zero
unresolved `{{`, (b) zero sentinel strings in output, (c) byte-identical output
for templates with no tool-scoped block (**H3**).

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Template integrity | **P1** | Omitting a clause (task 1) can leave dangling structure — an empty bullet, an orphaned "and" clause, or a heading with no body — which is a different kind of broken output. | **Resolved.** Task 1's acceptance requires omission at the **smallest enclosing complete structure** (whole list item, whole sentence, or whole section) and adds a rendered-markdown structural assertion: no empty list items, no headings with empty bodies, in any produced artifact. |
| 2 | Architecture | **P1** | Introducing an installer-resolved conditional block is a **new template language construct**. That is framework growth, which this run's ordering policy warns against. | **Accepted with bound.** The construct is the minimum that makes the defect expressible; option (A) was rejected precisely because it grows the *variable table* instead, which is larger and less checkable. The bound is **H4**: exactly one new construct, no general templating language, no expression evaluation, no nesting beyond one level. Recorded as a binding constraint on task 2. |
| 3 | Correctness | **P1** | A whole-corpus render-parity assertion (**H3**) will be defeated by incidental formatting churn and will be weakened to a soft check the first time it fails. | **Resolved.** Parity is asserted on **normalized** output (trailing-whitespace and line-ending normalized) and the assertion enumerates the templates it covers, so an intentional change is a visible edit to that enumeration rather than a silent relaxation. |
| 4 | Maintainability | P2 | Two defects with different root causes in one shipment. | Accepted: both live in the same variable-resolution layer and share the same render-test harness. Splitting duplicates that harness. |
| 5 | Schema/CLI/docs coupling | P2 | Template authoring documentation will describe the old scheme. | Task 2's acceptance includes updating the template-authoring guidance wherever the tool-scoped-branch pattern is documented. Scoped to documents that already describe this pattern; no broader docs sweep. |
| 6 | Scope | P2 | Task 2 could grow into fixing every tool-scoped branch in the corpus. | Bounded: fix the **mechanism**, and convert only the branches that currently render wrong. A branch that renders correctly today is left alone. |
| 7 | Security | P3 | A new renderer construct could enable injection from template content. | Resolution is pure lookup against a fixed registry-derived table with no expression evaluation (**H4**). No `eval`, no shell, no path resolution from template content. |

**Verdict: PASS.** 3 P1 raised, all 3 resolved. Zero unresolved P0/P1. Two
review-fix cycles of three.
