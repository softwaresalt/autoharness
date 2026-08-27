---
source: docs/plans/2026-07-27-multi-model-adversarial-review-routing-decided-plan.md
title: "Multi-model adversarial review routing enhancements"
doc_type: decided-plan
status: reviewed
created: 2026-07-27
source_stash_ids:
  - "E929B1C9"
  - "CB6A0EC6"
supersedes:
  - docs/archive/plans/2026-07-27-multi-model-adversarial-review-routing-plan.md
---

# Decided Plan: Multi-model adversarial review routing enhancements

**Outcome:** Reviewed under `dispatch_mode: single-agent-declared-degradation`.
`TOOL_DEGRADED: reviewer-subagent-dispatch` forced the plan review to run inline,
and the final plan-review decision was `PASS` with P0 = 0 and P1 = 0. The source
plan records a hardened reviewed design but no PR or merge evidence, so this
decided-plan preserves the reviewed state rather than claiming shipment. This
replaces the verbose original, archived for traceability at
`docs/archive/plans/2026-07-27-multi-model-adversarial-review-routing-plan.md`.

## Problem (settled)

Add GPT-5.6 Sol as a first-class anchor reviewer and back-port capability-aware
plan-review routing improvements without breaking environment agnosticism,
consensus-based finding assembly, or the fail-closed tool-availability model.

## Decisions

1. **Add a first-class anchor route.** The new route belongs in
   `model_routing.anchor_review`; it is not an overload of `ALT_REVIEW_*`, which
   already means an optional alternate-provider slot.
2. **Split global skill behavior from installed template variables.**
   `.github/skills/verify-harness/SKILL.md` is source-controlled and must read
   the anchor route from `<workspace>/.autoharness/config.yaml` at runtime,
   while rendered templates may use `{{ANCHOR_REVIEW_PROVIDER}}` /
   `{{ANCHOR_REVIEW_FAMILY}}` placeholders resolved at install time.
3. **Make review-dispatch degradation explicit and machine-readable.**
   `plan-review` must record `dispatch_mode:` and `decision:` markers whether it
   dispatches personas or runs them inline under declared degradation; `harvest`
   and `plan-harden` must consume those markers as gate inputs.
4. **Generalize P-012 to required workflow capabilities.** Backlog-tool fallback
   rules stay intact, but reviewer dispatch and similar non-registry capabilities
   must also resolve to `TOOL_OK`, `TOOL_DEGRADED`, or `TOOL_UNAVAILABLE` before
   a skill relies on them.
5. **Normalize the backlogit back-port to autoharness conventions.** Persona
   adapters use `{{DOCS_PLANS}}`, `{{DOCS_COMPOUND}}`, `{{PRIMARY_LANGUAGE}}`,
   `{{PRIMARY_LANGUAGE_LOWER}}`, and canonical
   `.github/agents/subagents/*.agent.md` paths; no Go-specific names or
   `docs/exec-plans` literals survive.
6. **Keep deterministic verification hermetic.** Schema, template, variable,
   cross-reference, and manifest checks prove the routing contract; no
   deterministic validation path may depend on a live GPT-5.6 Sol call.

## Implementation (8 units)

- **Unit A — P-012 capability clause:** generalize the workflow-policy template
  so required workflow capabilities, not only backlog-registry tools, must
  declare availability or degradation before use.
- **Unit B — Anchor review config contract:** extend harness-config schemas and
  template defaults with a first-class `anchor_review` route.
- **Unit C — Verify-harness + adversarial-review anchor slot:** add an explicit
  anchor reviewer while keeping reviewer counts, consensus minimums, and
  fallback behavior intact; refresh manifest checksums for edited global skills.
- **Unit D — Plan-review and review anchor persona routing:** let one eligible
  cross-model persona use the anchor route when model override dispatch is
  available, with declared inline fallback when it is not.
- **Unit E — Plan-review dispatch/degradation + persona adapter back-port:**
  port the capability-aware dispatch and rubric-adapter sections from backlogit,
  but parameterize them for autoharness paths and language profiles.
- **Unit F — Plan-harden and harvest companion gates:** ensure elevated review
  capability risks carry forward and harvest rejects missing or failed
  machine-readable plan-review verdicts.
- **Unit G — Review persona identity mapping:** sweep reviewer identity paths so
  generated references match the canonical flat `subagents/` install layout.
- **Unit H — Install-harness variable table + docs:** document every new anchor
  review variable and default, and refresh manifest checksums for edited
  source-controlled install-harness docs.

## Key constraints preserved

- Review gates must never be silently skipped; every selected persona path ends
  in either real dispatch or declared inline degradation.
- GPT-5.6 Sol is the default anchor only through provider/family/reasoning
  fields; if the environment cannot route to it, generated artifacts must say so
  explicitly and continue only when reviewer-count and consensus minimums are
  still satisfied.
- Consensus, majority/unique finding handling, confidence weighting, and P0/P1
  blocking semantics remain unchanged.
- Source-controlled global skills may not carry unresolved
  `{{ANCHOR_REVIEW_*}}` placeholders, and installed output may not retain any
  unresolved variables.
- No deterministic CI or template-validation path may rely on a live external
  model call.

## Rejected alternatives

- **Overload `ALT_REVIEW_*` to mean the anchor reviewer** — rejected because it
  makes the anchor route ambiguous and harder to verify.
- **Change consensus/confidence math along with model routing** — rejected; the
  request changes reviewer routing, not the consensus engine.
- **Silently fall back when reviewer dispatch is unavailable** — rejected;
  degradation must be declared locally and under P-012 rather than implied.
- **Paste the backlogit plan-review copy verbatim** — rejected because it would
  leak Go-specific names, `docs/exec-plans`, and stale identity paths into a
  multi-language harness.
- **Require live GPT-5.6 Sol calls in deterministic verification** — rejected;
  runtime model dispatch belongs to the skill behavior, not to hermetic tests.

## Review findings that changed the plan

The inline review ran under declared degradation because reviewer-subagent
dispatch was unavailable, so the plan had to make degradation explicit rather
than assuming it. Review also tightened two implementation details that changed
the original draft: the source-controlled `verify-harness` skill must load the
anchor route from target-workspace config rather than carry unresolved
install-time placeholders, and the persona adapter must target the canonical
`.github/agents/subagents/` layout rather than the retired categorized
`review/` / `research/` paths. Finally, the plan turned `dispatch_mode:` and
`decision:` into downstream gate markers that `harvest` must enforce.