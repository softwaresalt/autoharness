---
problem_type: false_positive_suppression
category: static_analysis
root_cause: engine_files_legitimately_reference_installation_paths
tags: [portability-scan, allow-list, verify-workspace, dogfood]
status: active
created: 2026-05-07
shipment: 012-S
---

# Portability Scan Allow-List Design Pattern

## Problem

Portability scan rules that flag hardcoded environment-specific paths (e.g., `~/.[a-zA-Z]`,
`~/.autoharness`, `\.github/local-agents`) immediately fire on autoharness engine files that
**legitimately** reference those paths as instructional documentation text. Without an allow-list,
the dogfood baseline always shows false positives, making the scan useless for detecting real
issues in generated harness artifacts.

## Affected Files (dogfood)

Engine/meta-skill files that legitimately reference installation paths:
- `.github/agents/auto-mergeinstall.agent.md`
- `.github/agents/auto-tune.agent.md`
- `.github/skills/install-harness/SKILL.md`
- `.github/skills/tune-harness/SKILL.md`
- `.github/skills/workspace-discovery/SKILL.md`
- `.github/copilot-instructions.md`

## Solution: `(rule, file_glob)` Allow-List Tuples

Define `PORTABILITY_ALLOW_LIST` as a list of `(rule_name, file_glob_pattern)` tuples.
Before adding a finding, check `fnmatch.fnmatch(rel_path, glob)` for each allow-list entry
where `entry.rule == finding.rule`. Only add the finding if no allow-list entry matches.

```python
PORTABILITY_ALLOW_LIST = [
    ("hardcoded_ah_home", ".github/agents/auto-mergeinstall.agent.md"),
    ("hardcoded_ah_home", ".github/agents/auto-tune.agent.md"),
    ("hardcoded_ah_home", ".github/skills/install-harness/SKILL.md"),
    ("hardcoded_ah_home", ".github/skills/tune-harness/SKILL.md"),
    ("local_agents_dir",  ".github/agents/auto-mergeinstall.agent.md"),
    # ... additional entries as needed
]
```

## Key Design Principles

1. **Specificity**: Allow-list tuples are `(rule, glob)` — not just `glob`. This allows the
   same file to be allowed for one rule but flagged for another.

2. **Dogfood baseline test**: `test_dogfood_baseline_has_no_portability_findings` runs the
   scan against the repository's `.github/` directory (resolved relative to the repo root) to
   confirm the allow-list is complete. This test must stay green.

3. **Allow-list grows with engine files**: When new engine files are added that legitimately
   reference installation paths, add corresponding allow-list entries AND the dogfood test
   will catch the gap immediately.

4. **Warning group key includes rule**: `_warning_group_key()` must include `warning.get("rule")`
   so multi-rule portability findings on the same file do not collapse into one undifferentiated
   group.

## Verification

Run portability scan + dogfood baseline test together:
```
uv run python -m pytest tests/test_verify_workspace.py::PortabilityTests -v
```
