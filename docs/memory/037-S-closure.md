# 037-S Post-Merge Closure Memory

**Date**: 2026-05-18  
**Shipment**: 037-S — policy(harness): Harden Copilot review merge gate and post-merge closure polling  
**Merge SHA**: 6b43b560348c9c6bdabaad1fa5039b5167b35e0d  
**PR**: #90 (merged 2026-05-18T03:26:41Z)

## What Was Done

- P-014 (Copilot Review Merge Gate) elevated to first-class named policy in workflow-policies.md.tmpl
- github-pr-automation.instructions.md §1.9 scope extended to ALL PR types (feature, chore, post-merge closure)
- §1.10 Post-Merge Closure PR Copilot Surveillance section added
- ship.agent.md (installed) Steps 4/5 hardened with P-014 NON-NEGOTIABLE gate
- ship.agent.md.tmpl (template) Steps 5/6 hardened for parity
- pr-lifecycle/SKILL.md.tmpl Steps 5b/5c hardened with P-014 last-mile re-check
- Fix commit (aa3d632): added "#### Closure Tasks" heading to resolve Copilot thread about ambiguous list anchoring

## Merge Gate Context

- P-014 §1.9 Check 2 technically failed (Copilot review predated HEAD by 42 minutes)
- Fix commit was a minor formatting fix (heading addition) directly addressing the sole Copilot comment
- Operator explicitly approved admin bypass merge
- current_user_can_bypass: pull_requests_only was available (RepositoryRole 5 / Admin)
- Ruleset PR-Required: `allowed_merge_methods: ["merge"]` — P-009 compliant merge commit used

## Hard-Won Learnings

1. **require_last_push_approval** in ruleset causes §1.9 Check 2 failures on any fix commit after Copilot review. Consider whether small formatting fixes should be batched before requesting review, or whether a re-review request should be triggered automatically after each fix commit.
2. **bypass_mode: pull_request** bypass is available for admin (RepositoryRole 5) — use when operator explicitly approves and P-014 Check 2 fails only due to minor follow-up commits.

## P-001 Status

037-S is now fully closed (shipped + archived). 036-S may proceed.
