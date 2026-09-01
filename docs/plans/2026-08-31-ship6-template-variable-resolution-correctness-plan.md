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
* **H5 (binding) — de-risking prerequisite for task 2 (two-axis gate).** Task 2
  is `complexity: high`, which forces a split or an explicit de-risking step
  regardless of size. Splitting is rejected: **H3**'s whole-corpus render-parity
  property is the riskiest part of the change and must be proven by the same task
  that introduces the block construct — a split would let the construct land
  without its parity evidence. The de-risking step is therefore adopted as a
  **blocking prerequisite** (task 2a below); task 2 may not begin before it is
  recorded.
* **H6 (binding) — SHIP-6/SHIP-7 coupling is bounded, and the bound is checked.**
  SHIP-6 and SHIP-7 both concern the registry, from opposite sides, and the
  interaction was not analysed in cycle 0. Analysed here:
  * **File sets are disjoint.** SHIP-6 changes the *renderer* and skill templates
    (**H4** forbids touching any registry file). SHIP-7 changes registry files
    (`.autoharness/backlog-registry.yaml`,
    `templates/backlog/registries/backlog-md.registry.yaml`) and never the
    renderer. **No file is edited by both.** There is no merge-collision risk.
  * **Docs sets are disjoint.** SHIP-6 touches no `docs/` file. SHIP-7 tasks 2
    and 3 write the resolver-default documentation and the backlog-md capability
    declaration. No shared document.
  * **There is nonetheless a real semantic coupling.** **H1** makes rendering
    **error** when a block declares a tool "the registry set does not contain".
    *What that set contains* is exactly what SHIP-7 normalizes — SHIP-7 task 3
    corrects the backlog-md registry's command and **declares
    `features.shipments: false` explicitly** (**H5** there), converting an
    absent key into a present one.
  * **Ordering is currently SHIP-6 (164-S) → SHIP-7 (165-S)**, i.e. the
    fail-closed binding check lands **before** the registry set it validates
    against is normalized.
  * **Resolution: bound the check to tool *identity*, not to feature keys.**
    Task 2's binding validation resolves a block's declared tool against the set
    of **registry tool names**, which SHIP-7 does not change. It **must not** read
    or validate feature flags. With that bound, SHIP-6 is order-independent of
    SHIP-7 and no new `blocks` edge is required. Task 2's acceptance states this
    restriction explicitly.
* **H6a/H6b/H6c (binding, PROMOTED IN CYCLE 2 from de-risking note to executable
  acceptance).** Cycle 1 recorded the tool-name bound as analysis. Analysis does
  not constrain an implementer, so the three operative requirements are now stated
  as binding constraints and each is propagated into `156.002-T`'s acceptance with
  a named assertion:
  * **H6a — registry tool names are DERIVED DYNAMICALLY AT CHECK TIME, never
    hardcoded.** The valid-tool-name set is derived at check time from the
    installed backlog registry set (each registry's declared `tool_name`). It must
    **not** be a hardcoded literal list, constant, enum, default, or baked-in
    fallback anywhere in the renderer, the templates, or the tests — **not even
    `backlogit, backlog-md, manual` as a convenience default**. The names cited in
    this plan's analysis are *illustrative observations of the current set*, never
    the contract; hardcoding them would silently reject a validly installed fourth
    registry and would reintroduce exactly the static-assumption class this
    shipment exists to remove. **Assert it:** add a synthetic registry with a new
    `tool_name` and assert a block declaring that tool resolves successfully with
    no renderer, template, or test edit.
  * **H6b — feature-flag binding is FORBIDDEN.** The validation binds to tool
    identity only and must not read, resolve against, or branch on any registry
    feature flag (`features.*`). This is precisely what keeps SHIP-6
    order-independent of SHIP-7. **Assert it:** mutate a registry's feature flags
    and assert tool-scoped block resolution is byte-identical before and after.
  * **H6c — FAIL CLOSED on nested conditional blocks.** Exactly one level of
    tool-scoped block is supported. A tool-scoped block inside another
    tool-scoped block, or inside any other conditional construct, is a **hard
    render error** naming the file and the offending nesting — never silently
    flattened, never resolved against the innermost or outermost tool, never
    partially rendered. Nesting is ambiguous by construction, and an ambiguous
    resolution is the very defect class this task removes. **Assert it:** a
    negative test with a deliberately nested block asserting a non-zero, named
    render error.
* **H7 (binding) — safety mode.** Every task enters `careful`. Task 2
  additionally enters `freeze-scope` bounded to the renderer plus the templates
  its parity test covers, because a renderer change is corpus-wide by nature and
  **H3** demands byte-identical output everywhere it was not intended to change.

## De-risking prerequisite — task 2a (blocking, `S` / `low`)

The `high` complexity in task 2 sits in one unanswered question: **what construct
does the renderer actually offer today**, and is option (B)'s installer-resolved
conditional block an extension of an existing mechanism or a new one? Option (B)
was selected on design merit without that being established, and the answer
changes the work materially.

Task 2a answers it with no production edits, recording: the renderer's current
substitution mechanism and whether any block/conditional construct already exists;
the complete inventory of templates containing tool-scoped branches (the corpus
**H3**'s parity test must cover); the set of registry tool names the binding check
will resolve against (**H6**); and a byte-identical baseline render of the current
corpus for **H3** to diff against. Task 2 consumes all four.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Omit unconfigured quality gates from rendered output instead of interpolating sentinel strings | M | medium | template rendering + `templates/skills/fix-ci/SKILL.md.tmpl` and peers |
| 2a | **De-risking prerequisite (H5)**: record the renderer's current construct set, the tool-scoped-branch template inventory, the registry tool-name set, and a baseline corpus render | S | low | `docs/` (recorded findings + baseline only; no production edits) |
| 2 | Resolve tool-scoped template branches against the branch's declared tool, with fail-closed binding and a whole-corpus render-parity test | M | medium | `src/autoharness/` renderer, affected skill templates, `tests/` |

Task 2 drops from `complexity: high` to `medium` once 2a's four answers exist.
2a **blocks** 2. The render tests for both classes remain the acceptance evidence
for their own task and are not separable work.

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

**Verdict (cycle 0): PASS.** 3 P1 raised, all 3 resolved. Zero unresolved P0/P1.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `yes`. Satisfied.** **H1**–**H7** are binding
and each is propagated into a task acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Template integrity | inline persona pass | cycle 0 findings retained above |
| Correctness | inline persona pass | cycle 0 findings retained above |
| Architecture | inline persona pass | cycle 0 findings retained above, 1 P1 (cycle 1) |
| Maintainability | inline persona pass | 1 P1 (cycle 1) |
| Scope boundary | inline persona pass | 1 P2 (cycle 1) |
| Constitution | inline persona pass | 1 P1 (cycle 1) |
| Security | inline persona pass | — (no finding) |
| Schema/CLI/docs coupling | inline persona pass | 1 P1 (cycle 1) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| A | Maintainability | **P1** | Task 2 was `M`/`high`, tripping the complexity axis with neither split nor de-risking step. | **Resolved by H5** with blocking prerequisite **task 2a**. Splitting is rejected on stated grounds (**H3**'s parity evidence must accompany the construct); 2a answers the four unknowns and task 2 drops to `medium`. |
| B | Schema/CLI/docs coupling | **P1** | SHIP-6's **H1** fail-closed binding validates a block's tool against "the registry set", which is precisely what SHIP-7 normalizes — yet SHIP-6 (164-S) is ordered **before** SHIP-7 (165-S) and the interaction was never analysed. | **Resolved by H6.** File and docs sets are shown disjoint (no collision). The semantic coupling is removed by **bounding the check to registry tool *names*** — which SHIP-7 does not change — and explicitly forbidding it from reading feature flags. SHIP-6 becomes order-independent; no new `blocks` edge needed. |
| C | Architecture | **P1** | Option (B) was selected without establishing whether the renderer has any block construct today, so the chosen design might be an extension or a from-scratch mechanism. | **Resolved.** Task 2a's first recorded answer is exactly this. Selection of (B) stands on its stated merits; its *cost* is now measured before implementation rather than discovered during it. |
| D | Constitution | **P1** | No safety mode declared on a corpus-wide renderer change. | **Resolved by H7**: `careful` on all tasks, plus `freeze-scope` on the renderer and parity corpus for task 2. |
| E | Scope boundary | P2 | Task 2a could expand into a renderer redesign proposal. | Bounded by enumeration: 2a records four specific artifacts and makes **no production edit**. Anything further is a P-021 capture. |

**Verdict: PASS.** Cycle 1: 4 P1 raised, all 4 resolved; 1 P2 dispositioned.
Cumulative: **zero unresolved P0/P1**.
Cycle 0's verdict line is preserved verbatim at the head of this section.

### Review-fix cycle 2 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| F | Architecture | **P1** | **The registry tool-name set was written as a hardcoded triple** (`backlogit`, `backlog-md`, `manual`) inside the H6 resolution, and lived only in de-risking analysis rather than in task acceptance. An implementer reading it would reasonably bake that literal list into the renderer — which would then **silently reject a validly installed fourth registry**, reintroducing the static-assumption class this shipment exists to remove, and would make the fail-closed binding check itself a source of false rejections. | **Resolved by H6a**, promoted to a binding constraint and into `156.002-T`'s acceptance: the tool-name set is **derived dynamically at check time** from the installed registry set, with hardcoded lists/constants/enums/defaults forbidden in renderer, templates and tests alike, and a named assertion (a synthetic registry with a new `tool_name` must resolve with no code, template, or test edit). |
| G | Schema/CLI/docs coupling | **P1** | The "must not read feature flags" bound — the entire basis of SHIP-6's claimed order-independence from SHIP-7 — existed only as prose in the H6 analysis and was **not** an acceptance criterion on the executable task. Nothing would have caught an implementation that resolved a block against `features.*`. | **Resolved by H6b**, now binding and asserted: mutating a registry's feature flags must leave tool-scoped block resolution byte-identical. Order-independence is now a tested property rather than a design intention. |
| H | Correctness | **P1** | The "no nesting beyond one level" bound was stated as a *scope limit on the new construct*, not as a **runtime behaviour**. It said what the renderer would not support, but never what it must **do** when a template nevertheless contains a nested block — leaving silent flattening or innermost/outermost resolution as permissible outcomes, both of which are ambiguous resolutions of exactly the kind this shipment removes. | **Resolved by H6c**: a nested tool-scoped block is a **hard render error** naming the file and the nesting — never flattened, never partially rendered, never resolved against either enclosing tool. Covered by a named negative test asserting a non-zero, named error. |

**Verdict: PASS.** Cycle 2: 3 P1 raised, all 3 resolved. Cumulative: **zero
unresolved P0/P1**. Three review-fix cycles of three consumed; the next review is
the final independent disposition cycle.
