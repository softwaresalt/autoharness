---
problem_type: policy_lifecycle_governance
category: auto_tune
root_cause: auto_generated_policies_require_human_review_before_installation
tags: [dynamic-policy, tune-harness, policy-proposal, operator-review]
status: active
created: 2026-05-07
shipment: 012-S
---

# Dynamic Policy Acceptance Path Pattern

## Problem

Auto-tune mines compound learnings and detects recurring problem patterns that don't have a
matching installed workflow policy. If auto-tune were to auto-install generated policies, it would
bypass human oversight for governance decisions — policies control cross-agent sequencing, gate
conditions, and violation handling (Primitive 8), which are high-impact and hard to roll back.

## Solution: Proposals-First, Manual Acceptance

Auto-tune generates policy proposals into `.autoharness/policy-proposals/` as operator-review
artifacts. They are **never auto-installed**. The operator accepts them by copying to
`.github/policies/` or appending to `.github/policies/workflow-policies.md`.

### Detection (Step 1.8.5 — Policy-Gap Detection)

```text
For each compound entry cluster (3+ entries sharing problem_type + root_cause + category):
  Search .github/policies/ for a policy with matching gate_point/applies_to keywords
  If no match found: record as policy-gap candidate
```

Threshold of 3 prevents noise from one-off incidents being promoted to policy.

### Generation (Step 2.4 — Dynamic Policy Proposal Generation)

Proposals are written to `.autoharness/policy-proposals/{suggested_policy_id}.md` using the
`policy-proposal.md.tmpl` template. Template requires 5 mandatory fields:
- `APPLIES_TO` — scope
- `GATE_POINT` — where in the pipeline the policy gates
- `PRECONDITION` — what must be true before proceeding
- `POSTCONDITION` — what must be true after the gate
- `VIOLATION_ACTION` — what happens on violation

### Acceptance Path (as documented in template)

```text
# Option A — standalone policy file
cp .autoharness/policy-proposals/P-NNN-{slug}.md .github/policies/P-NNN-{slug}.md

# Option B — append to workflow-policies.md
# Append the policy block to .github/policies/workflow-policies.md
```

## Template Frontmatter Design

`policy-proposal.md.tmpl` frontmatter fields:
- `policy_id: "{{POLICY_ID}}"` — assigned by tune-harness
- `policy_type: "{{POLICY_TYPE}}"` — e.g., workflow, sequencing
- `status: proposed`
- `proposed_at: "{{PROPOSED_AT}}"`
- `evidence_count: {{EVIDENCE_COUNT}}`

**No `evidence_refs: []` in frontmatter** — the evidence block is in the body `## Evidence` section
so reviewers can read context in one view. This was a Copilot review correction (PR #44).

## Variable Naming

Use `suggested_policy_id` (not `policy_id`) in acceptance instructions embedded in the Step 2.4
workflow text, to distinguish the auto-generated suggestion from the final accepted ID the operator
assigns. Inconsistency here causes confusing acceptance instructions.

## Verification

Foundation assertions verify the wiring:
- `tune_harness_dynamic_policy_generation` — checks 8 phrases in `.github/skills/tune-harness/SKILL.md`
- `auto_tune_dynamic_policy_phase` — checks `policy-gap` and `policy-proposals` in auto-tune agent
