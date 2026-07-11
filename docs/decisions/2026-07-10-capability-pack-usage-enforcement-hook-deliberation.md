---
title: "Capability-Pack Usage-Enforcement Hook (Generic, engram + graphtor-docs)"
description: "Deliberation for stash items 909F493D (enforce engram usage) and 8EB5C5D8 (similar hook for graphtor-docs). Decides a single reusable capability-pack usage-enforcement overlay: a Pre-Retrieval Routing Protocol instruction plus a deterministic verifier check, weaving through install and tune, rather than two bespoke mechanisms or an unenforceable runtime interceptor."
topic: "How should the harness deterministically enforce that agents actually USE an installed retrieval-oriented capability pack (engram for code/symbol/semantic search; graphtor-docs for documentation/domain-context lookup) instead of silently falling back to grep or web search?"
depth: "significant"
decision_status: "accepted"
doc_type: decision
source: docs/decisions/2026-07-10-capability-pack-usage-enforcement-hook-deliberation.md
source_stash_ids:
  - "909F493D"
  - "8EB5C5D8"
backlog_items:
  - "075-F"
  - "075.001-T"
  - "075.002-T"
  - "075.003-T"
  - "075.004-T"
  - "075.005-T"
linked_artifacts:
  - "templates/instructions/capability-pack-enforcement.instructions.md.tmpl"
  - ".github/instructions/capability-pack-enforcement.instructions.md"
  - "src/autoharness/verify_workspace.py"
  - "tests/test_capability_pack_enforcement.py"
  - ".github/skills/install-harness/SKILL.md"
  - ".github/skills/tune-harness/SKILL.md"
  - "templates/packs/capability-pack-registry.yaml"
  - "docs/capability-packs.md"
tags:
  - "capability-packs"
  - "agent-engram"
  - "graphtor-docs"
  - "enforcement"
  - "verifier"
  - "primitive-6"
---

# Capability-Pack Usage-Enforcement Hook (Generic, engram + graphtor-docs)

## Decision

Build **one reusable capability-pack usage-enforcement overlay**, not two bespoke
per-pack hooks. It has two deterministic surfaces plus install/tune weaving:

1. **Session-time — a Pre-Retrieval Routing Protocol instruction.** A new
   technology-agnostic template
   `templates/instructions/capability-pack-enforcement.instructions.md.tmpl`
   (installed mirror `.github/instructions/capability-pack-enforcement.instructions.md`)
   modeled on `role-enforcement.instructions.md`. It defines a fail-closed
   routing discipline: before any retrieval operation (code/symbol/structural/
   semantic search, or documentation/domain-context/business-context lookup), the
   agent MUST (a) check the responsible pack's health/freshness with the pack's
   own lifecycle tool, (b) route the query through the pack's most-specific tool,
   and (c) fall back to grep/glob/web **only** after a documented pack-miss or
   pack-unavailability. Deviations (raw grep/web used for a pack-covered query
   class while the pack was installed and reachable) are logged as observability
   events. The instruction contains a query-class → pack routing table so the
   discipline is concrete and generic across retrieval packs.

2. **Install/CI-time — a deterministic verifier check.** A new
   `_check_capability_pack_enforcement` in `src/autoharness/verify_workspace.py`
   (modeled on `_check_copilot_code_review_instruction`). When at least one
   retrieval-enforced pack (`agent-engram`, `graphtor-docs`) is enabled, it
   asserts the enforcement instruction is installed, has valid YAML frontmatter
   with `applyTo: '**'`, references each enabled retrieval pack, contains no
   unresolved `{{PLACEHOLDER}}` tokens, and (when manifest-listed) is present.
   Existence-gated: when no retrieval pack is enabled the check is a no-op.

3. **Install + tune weaving.** `install-harness` installs the enforcement
   instruction whenever any retrieval-enforced pack is selected and records it in
   the manifest; the capability-pack registry marks which packs are
   retrieval-enforced. `tune-harness` detects drift (pack enabled but enforcement
   instruction missing, stale, or no longer referencing the enabled packs).

Telemetry-based retrospective usage auditing (the telemetry epoch already carries
`operations.cli_tools`) is noted as a **future phase**, not built here.

## Rationale

* **Both stash seeds want the same mechanism.** `8EB5C5D8` explicitly says
  graphtor-docs needs a *"similar hook mechanism"* to engram's (`909F493D`). Two
  bespoke mechanisms would drift; one generic overlay parameterized by
  "retrieval-enforced pack" serves both and any future retrieval pack.

* **autoharness cannot intercept an agent's live tool calls.** The product is
  templates + a verifier, not a runtime that sits between the agent and its tools.
  A git `pre-push` hook (P-019) fires on git events and cannot observe mid-session
  tool choices, so it can only check index freshness — a weak proxy for "usage."
  The honest *deterministic* surfaces are therefore **session-time** (an
  instruction protocol the agent self-applies, exactly like role-enforcement's
  pre-mutation protocol) and **install/CI-time** (the verifier). This decision
  builds on both rather than over-promising an interceptor.

* **Reuses three proven patterns**, minimizing novel surface and review risk:
  1. `role-enforcement.instructions.md` — the fail-closed pre-operation protocol
     shape (classify → check → route → fail-closed).
  2. `_check_copilot_code_review_instruction` + tests — the "instruction artifact
     + deterministic verifier + drift/frontmatter/placeholder tests" template.
  3. `PACK_ASSERTIONS` — the manifest/profile-gated per-pack weaving check style.

* **Deterministic where it can be.** Enforcement of an LLM's tool *choice* is
  inherently soft, but the *presence, coherence, and wiring* of the enforcement
  discipline is fully deterministic and CI-catchable. That is the "deterministic
  hook" the stash items are really asking for: the workspace cannot silently drop
  the enforcement discipline without the verifier failing.

## Options considered

| Option | Verdict |
|---|---|
| **A. Two bespoke per-pack hooks** | Rejected — drift risk; contradicts `8EB5C5D8`'s "similar mechanism" framing. |
| **B. Git pre-push hook enforces usage** | Rejected as primary — git hooks cannot observe agent tool choices; only index-freshness proxy. May be a future adjunct under P-019. |
| **C. Runtime interceptor / tool-call gateway** | Rejected — autoharness does not own the agent runtime; out of product scope. |
| **D. Telemetry-based retrospective audit** | Deferred to a future phase — depends on the runtime emitting per-session tool usage into the epoch; useful as evidence, not as prevention. |
| **E. Generic Pre-Retrieval Routing Protocol instruction + deterministic verifier + install/tune weaving** | **Accepted** — native, deterministic where possible, reuses proven patterns, generic across retrieval packs. |

## Scope boundary

* **In scope:** the enforcement instruction template + dogfood mirror; the
  verifier check + tests; install-harness weaving + registry marking; tune drift
  check; `docs/capability-packs.md` + a harness-architecture note; dogfood
  manifest tracking (this repo enables engram + graphtor-docs).
* **Out of scope:** telemetry capture of live tool usage; any git-hook usage
  proxy; changing engram/graphtor-docs pack instruction *content* beyond a
  cross-reference to the enforcement instruction; new schema enums for packs (the
  registry marking is additive and does not change the closed pack enums).

## Verification expectation (for Ship)

* Full unittest suite green, including new `tests/test_capability_pack_enforcement.py`.
* `verify_workspace` on the dogfood repo passes with the enforcement instruction
  installed, manifest-tracked, and referencing engram + graphtor-docs.
* No unresolved `{{VARIABLE}}` in the installed mirror; markdownlint heading
  hierarchy (MD001/MD025/MD041) clean; all cross-references resolve.
* Adversarial review of the routing table (no false "must route" claims that
  would wrongly forbid legitimate grep for literal-text/known-path cases) and of
  the verifier's existence-gating (no false failures when no retrieval pack is
  enabled).
