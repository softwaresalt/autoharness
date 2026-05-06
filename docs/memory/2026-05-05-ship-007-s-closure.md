---
title: "Ship 007-S: Browser & Experimentation Skill Templates"
date: 2026-05-05
shipment: 007-S
branch: feat/browser-experiment-skills
pr: 31
merge_commit: 9f7b5dd
status: shipped
---

# Ship 007-S Closure — Browser & Experimentation Skill Templates

## What Was Shipped

Two new optional skill templates added to autoharness, plus wiring in install-harness and verification infrastructure.

| Task | Artifact |
|---|---|
| 007.001-T | `templates/skills/browser-automation/SKILL.md.tmpl` |
| 007.002-T | `templates/skills/iterative-experiment/SKILL.md.tmpl` |
| 007.003-T | install-harness SKILL.md wiring (variables, manifest, overlay table, config write-back) |
| 007.004-T | `verify_workspace.py` FOUNDATION_ASSERTIONS + `test_verify_workspace.py` (29/29 tests) |

## Copilot Review Rounds

Two rounds of Copilot review feedback (13 + 6 comments = 19 total). All addressed and resolved.

### Round 1 Key Fixes (13 comments)
- Added `steps:` and `fields:` args to browser-automation invocation
- Made `auth:none` skip unconditional in Phase 2
- Clarified TSV gitignore semantics (untracked ≠ dirty)
- Fixed detached HEAD: `git reset --hard` not `git checkout <hash>`
- Added `browser:` and `experiments:` sections to harness-config.yaml.tmpl
- Strengthened FOUNDATION_ASSERTIONS with section-specific phrases
- Normalized `EXPERIMENT_BRANCH_PREFIX` trailing `/`
- Validated `EXPERIMENT_RESULTS_DIR` for absolute/traversal paths
- Derived `BROWSER_CLI` from workspace profile (config override first)
- Fixed archive timestamps (updated_at was before created_at)
- Split chained `git add && git commit`

### Round 2 Key Fixes (6 comments)
- Switched browser CLI detection from `profile.tools` (object) to `runtime_surfaces.browser_tooling` (array)
- Strengthened traversal check: `".." in Path.parts` vs `startswith("..")`
- Corrected resolution-order docs (config override first, not detection first)
- Narrowed `BROWSER_HEADLESS_FLAG` docs (default `--headless`, override for non-standard CLIs)
- Added `none` to auth options in browser-automation invocation line
- Made `goal` unbracketed (required) in iterative-experiment invocation

## Compound Learnings Written

Six entries in `docs/compound/`:

1. `2026-05-05-runtime-surfaces-browser-tooling-detection.md` — Use `runtime_surfaces.browser_tooling` not `profile.tools`
2. `2026-05-05-path-traversal-validation-parts.md` — Use `".." in Path.parts` not `startswith("..")`
3. `2026-05-05-foundation-assertion-anchoring.md` — Anchor assertions to section-specific phrases
4. `2026-05-05-git-reset-hard-vs-checkout-hash.md` — Use `git reset --hard` not `git checkout <hash>`
5. `2026-05-05-harness-config-round-trip-requirement.md` — Always add new vars to harness-config.yaml.tmpl
6. `2026-05-05-resolution-order-config-first-not-detection-first.md` — Config override beats auto-detection

## Technical Notes

- Test runner: `$env:PYTHONPATH = "src"; D:\Python314\Scripts\pytest.exe tests/test_verify_workspace.py -q`
- Backlogit mutation serialization required (lock file collisions on parallel runs)
- Base branch was `chore/007-s-restage-learnings` (restaged 007-S with 006-S learnings)
- Merge commit: `9f7b5dd` on main
