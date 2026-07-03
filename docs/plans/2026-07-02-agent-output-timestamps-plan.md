---
title: "Agent Output Timestamps for Phase Transitions — Implementation Plan"
description: "Make agents emit an ISO-8601 timestamp with a delta-since-previous-stamp at phase transitions and long-running operations, via (a) a general universal instruction template and (b) the agent-intercom Progress Protocol, with installed mirrors updated to match."
source_documents:
  - "templates/instructions/agent-intercom.instructions.md.tmpl"
  - ".github/instructions/agent-intercom.instructions.md"
  - ".github/skills/install-harness/SKILL.md"
feature: "059-F"
tasks:
  - "059.001-T"
  - "059.002-T"
source_stash_ids:
  - "C414C5C6"
scope: "Instruction-template authoring (base universal instruction + agent-intercom capability-pack overlay) and their installed mirrors — single domain"
primitives:
  - "6 - Injection Points & Dynamic Reminders"
  - "7 - Observability & Evaluation"
tags:
  - "template-authoring"
  - "instructions"
  - "observability"
  - "agent-intercom"
  - "primitive-6"
  - "primitive-7"
---

## Problem Frame

Operators cannot see how long elapses between an agent's work outputs. Stash
`C414C5C6` requested a date/time stamp after each work output so elapsed
duration between outputs is visible. The entry was deferred pending scope
clarification; the operator has now resolved all three ambiguities (surface,
trigger scope, format). This is a **Primitive 6** (injection points / dynamic
reminders) plus **Primitive 7** (observability) concern, tightly coupled to the
agent-intercom Progress Protocol.

Because autoharness follows "templates are the product", the primary change must
live in **templates** so every installed workspace receives it. autoharness
dogfoods its own harness, so the installed `.github/instructions/` mirrors must
be updated to match the template changes.

## Clarified Requirement (operator-confirmed 2026-07-02)

### 1. Surface — BOTH

* **(a) Agent broadcast:** the intercom-style progress broadcasts (see
  `.github/instructions/agent-intercom.instructions.md` → Progress Protocol)
  must carry the stamp. This is the capability-pack overlay surface — it only
  applies when the `agent-intercom` pack is enabled.
* **(b) General instruction-template rule:** a base rule so agents emit the
  stamp **regardless of the intercom pack**. This must live in a universal
  (always-installed) instruction so pack-less installs still get the behavior.

### 2. Trigger scope

Stamp at **phase transitions** and/or **long-running operations** — NOT every
trivial line of output. Phase transitions include (illustrative, not
exhaustive):

* planning started / plan ready / plan blocked
* build loop started / task claimed / task completed / task blocked
* review started / review complete / findings require intervention
* runtime verification started / passed / follow-up needed / failed
* operational closure ready / ready with conditions / blocked

Long-running operations (builds, test suites, multi-file generation, CI polling)
are also stamp points. Trivial intermediate lines are explicitly excluded to
avoid output noise.

### 3. Format

ISO-8601 UTC timestamp followed by the delta since the previous stamp in
parentheses:

```text
2026-07-02T18:49:41Z (+2m13s)
```

**First-stamp rule:** the first stamp of a session has no prior stamp to
diff against. Emit it either with a zero delta `(+0s)` or omit the
parenthetical entirely, e.g.:

```text
2026-07-02T18:47:28Z (+0s)
2026-07-02T18:47:28Z
```

Delta formatting is human-legible compound duration (e.g. `+2m13s`, `+45s`,
`+1h04m`), measured from the immediately preceding stamp in the same session.

## Affected Artifacts

### Templates (the product — primary changes)

| Artifact | Change |
|---|---|
| **NEW** `templates/instructions/output-timestamps.instructions.md.tmpl` | New universal (base) instruction, `applyTo: '**'`, defining the phase-transition timestamp rule: when to stamp (phase transitions + long-running ops, not trivial lines), the ISO-8601 + delta format, and the first-stamp rule. Environment-agnostic; no technology-specific content. |
| `templates/instructions/agent-intercom.instructions.md.tmpl` | Extend the **Progress Protocol** section (currently lines 32–42) so each broadcast at a meaningful transition carries the stamp. Cross-reference the general rule as the format authority so the two surfaces stay consistent (single source of truth for the format). |

### Install wiring

| Artifact | Change |
|---|---|
| `.github/skills/install-harness/SKILL.md` | Register the new base instruction in the **Universal instructions** list (Step 2.2 §2, lines 851–866, alongside `coding-discipline`/`circuit-breaker`/`context-efficiency`). Mention it under the Primitive mapping table (lines 779–790) for Primitive 6 (Injection Points) and Primitive 7 (Observability). No new `{{VARIABLE}}` is introduced (the format is fixed), so **no** variable-resolution-table change is required — note this explicitly in the task. |

### Installed mirrors (autoharness dogfoods its own harness)

| Artifact | Change |
|---|---|
| **NEW** `.github/instructions/output-timestamps.instructions.md` | Rendered mirror of the new universal template (this workspace's base instruction set currently has 7 mirrors; this adds the 8th). |
| `.github/instructions/agent-intercom.instructions.md` | Mirror the Progress Protocol stamp addition to match the template. |

### Explicitly out of scope (avoid scope creep)

* The per-message broadcast literal tables in `templates/agents/.stage.agent.md.tmpl`,
  `.ship.agent.md.tmpl`, and `_orchestrator.agent.md.tmpl` (the "Remote Operator
  Integration" tables). The stamp rule is applied **once** in the intercom
  Progress Protocol and the universal instruction; the agent broadcast tables
  inherit it by reference. Rewriting every literal broadcast string is
  unnecessary churn and is not required to satisfy the requirement.
* Foundation docs (`AGENTS.md`, `copilot-instructions`), constitution, and
  schemas — no structural change needed; the injected instruction is sufficient.
* CLI stdout of `autoharness` commands — the operator scoped this to agent
  broadcast + instruction-rule surfaces, not CLI command output.

## Task Breakdown (2-hour rule + width isolation)

Both tasks are instruction-template authoring (single skill domain → width
isolation satisfied). They are split so each stays comfortably under the 2-hour
rule: authoring a **new base universal instruction with install-harness
registration** is meaningfully separate from **weaving the stamp into the
capability-pack overlay**. Task 2 depends on Task 1 because Task 1 defines the
canonical format that Task 2 references.

### 059.001-T — Universal output-timestamp instruction + install registration + mirror (surface b)

* **Domain:** base (universal) instruction-template authoring.
* **Changes:**
  * Author `templates/instructions/output-timestamps.instructions.md.tmpl`
    (`applyTo: '**'`) with: trigger scope (phase transitions + long-running
    ops, exclude trivial lines), the ISO-8601 + delta format spec with worked
    examples, and the first-stamp rule.
  * Register it in `install-harness/SKILL.md` Universal instructions list and
    reference it in the Primitive 6/7 mapping. Confirm no new template variable
    is needed (no variable-resolution-table change).
  * Install the rendered mirror `.github/instructions/output-timestamps.instructions.md`.
* **Acceptance:** template has valid YAML frontmatter; renders valid Markdown
  with no unresolved `{{...}}`; the format spec + first-stamp rule + trigger
  scope are all present with examples; install-harness lists the new base
  instruction; installed mirror exists and matches the rendered template.
* **Width:** single instruction-authoring concern. Est. ~1–1.25h.

### 059.002-T — Weave the stamp into the agent-intercom Progress Protocol + mirror (surface a)

* **Domain:** capability-pack (agent-intercom) instruction-template authoring.
* **Depends on:** 059.001-T (format authority).
* **Changes:**
  * Extend the Progress Protocol section of
    `templates/instructions/agent-intercom.instructions.md.tmpl` so meaningful-
    transition broadcasts carry the stamp, cross-referencing the universal rule
    for the format (single source of truth).
  * Mirror the change to `.github/instructions/agent-intercom.instructions.md`.
* **Acceptance:** intercom template + mirror both state that Progress Protocol
  broadcasts carry the ISO-8601 + delta stamp; the format is referenced from
  (not duplicated/divergent with) the universal instruction; frontmatter valid;
  no unresolved `{{...}}`; cross-reference to the universal instruction resolves.
* **Width:** single instruction-authoring concern. Est. ~0.75–1h.

## Verification Approach (quality gates)

Templates are documentation artifacts; quality is verified via the standard
gates, not application-code tests:

1. **YAML frontmatter validity** — new template + edited templates parse.
2. **Markdown structure** — heading hierarchy (MD001/MD025/MD041), fenced code
   blocks, tables; `markdownlint "**/*.md"`.
3. **Variable completeness** — no unresolved `{{...}}` remain in the installed
   mirrors (`.github/instructions/output-timestamps.instructions.md`,
   `.github/instructions/agent-intercom.instructions.md`).
4. **Cross-reference integrity** — the intercom Progress Protocol reference to
   the universal instruction resolves to an existing installed file; install-
   harness references to the new template resolve.
5. **Existing suite** — run `uv run python -m pytest tests/test_verify_workspace.py`
   green before and after. If any test enumerates the installed base-instruction
   set (see `tests/test_verify_workspace.py` instruction assertions), extend it
   to include the new mirror. Ship owns any test change.
6. **Format-spec dogfood check** — confirm the worked examples in the new
   instruction render exactly as specified (`2026-07-02T18:49:41Z (+2m13s)` and
   the first-stamp `(+0s)` / omitted-parenthetical forms).

## Sequencing Note (P-001)

This feature is left **queued and plan-ready**. It is NOT assembled into a
shipment: shipment `057-S` (closure cascade guard) is the current release unit,
and P-001 permits only one release unit at a time. Ship should pick 059-F up in
a later cycle after 057-S completes.

## Out of Scope

* No source/test/config edits in this plan (Stage plans; Ship implements).
* No shipment assembly (P-001 — 057-S is the active release unit).
* No changes to agent broadcast literal tables, foundation docs, schemas, or CLI
  stdout formatting.
