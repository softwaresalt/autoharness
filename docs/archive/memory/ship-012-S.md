# Ship 012-S: Auto-Tune Dynamic Policy Generation + Portability Scan

**Date**: 2026-05-07
**PR**: #44 — merged `8c51c2c8`
**Branch**: `feat/012-auto-tune-dynamic-policy`

## Summary

Shipped two capabilities:

1. **Portability scan** — `verify_workspace.py` now scans installed harness artifacts for hardcoded
   environment-specific paths (user-home paths, `local-agents` dir, MCP plugin tool names,
   hardcoded `~/.autoharness/`). Surfaces findings as warnings and a dedicated report section.

2. **Dynamic policy proposal generation** — `tune-harness` Step 1.8.5 detects policy-gap
   candidates (3+ compound entries sharing `problem_type`/`root_cause`/`category` with no
   matching installed policy). Step 2.4 generates draft proposals to `.autoharness/policy-proposals/`
   for operator review. Template `templates/policies/policy-proposal.md.tmpl` created.

## Key Decisions

- **Allow-list over exclusion globs**: Engine/meta-skill files (auto-mergeinstall, auto-tune,
  install-harness, tune-harness, workspace-discovery, copilot-instructions.md) legitimately
  reference `~/.autoharness/` as instructional text. Allow-list of `(rule, file_glob)` tuples
  prevents false positives without silencing rules globally.

- **Proposals are operator-review artifacts**: Dynamic policy proposals are never auto-installed.
  Operator copies accepted proposals to `.github/policies/` or appends to
  `.github/policies/workflow-policies.md`. This preserves human oversight over policy changes.

- **Explicit single-file scan targets**: `.github/copilot-instructions.md` added as explicit
  target alongside recursive directory scans. This was a Copilot review finding.

- **`_warning_group_key()` includes rule name**: Prevents multi-rule warnings on the same file
  from collapsing into one undifferentiated group. Critical for portability finding legibility.

## Files Changed

| File | Change |
| --- | --- |
| `src/autoharness/verify_workspace.py` | Portability scan + 2 foundation assertions |
| `tests/test_verify_workspace.py` | 12 new PortabilityTests (31→43 total) |
| `.github/skills/tune-harness/SKILL.md` | Steps 1.8.5 + 2.4 |
| `.github/agents/auto-tune.agent.md` | Step 6 policy proposal bullet |
| `.github/skills/install-harness/SKILL.md` | Phase 4 portability scan mention |
| `templates/policies/policy-proposal.md.tmpl` | New template |

## Copilot Review Fixes (6 threads resolved)

1. `except (OSError, UnicodeDecodeError)` — non-UTF8 files skipped cleanly
2. Removed `evidence_refs: []` from template frontmatter (authoritative field is body)
3. `workflow-policies.md` → `.github/policies/workflow-policies.md` (full path)
4. `.github/copilot-instructions.md` added as explicit single-file scan target
5. `{policy_id}` → `{suggested_policy_id}` in Step 2.4 acceptance path
6. `rule` field added to `_warning_group_key()` tuple

## Test Count

31 (pre-012) → 43 (post-012). All pass including `test_dogfood_baseline_has_no_portability_findings`.
