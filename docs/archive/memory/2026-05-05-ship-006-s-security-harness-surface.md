# 2026-05-05 Ship Memory: 006-S Security Harness Surface

## Scope Executed

Shipment `006-S` — Security Harness Surface. 8 tasks across 4 new template files, 2 skill wirings, variable registration, and verify_workspace assertions.

## Changes Landed

**New templates:**
- `templates/agents/review/security-reviewer.agent.md.tmpl` — Conditional code review persona (confidence 0.60+; JSON output; Tier 2)
- `templates/agents/review/security-lens-reviewer.agent.md.tmpl` — Plan review persona with HIGH/MODERATE/LOW/suppress confidence tiers
- `templates/agents/security-sentinel.agent.md.tmpl` — Standalone Tier 3 audit agent; writes report to `{{DOCS_SECURITY}}/YYYY-MM-DD-HH-MM-security-sentinel.md`
- `templates/skills/security-audit/SKILL.md.tmpl` — 8-phase audit skill (modes: report/fix; scopes: full/config/owasp/stride/<path>); writes to `{{DOCS_SECURITY}}/YYYY-MM-DD-HH-MM-security-audit.md`

**Wired into:**
- `templates/skills/review/SKILL.md.tmpl` — Security Reviewer in conditional persona table + Step 2 routing
- `templates/skills/plan-review/SKILL.md.tmpl` — Security Lens Reviewer in cross-model table + Step 2 trigger conditions

**Variables registered (7):**
`AGENTIC_CONFIG_GLOB`, `SOURCE_GLOB`, `DOCS_SECURITY`, `SECURITY_CONFIG_RULES`, `SECURITY_OWASP_PATTERNS`, `SECURITY_SCAN_PATTERNS`, `SECURITY_REVIEW_PATTERNS` — in `.github/skills/install-harness/SKILL.md` Steps 2.4, 2.5, and variable table.

**Verification:**
- 2 new `FOUNDATION_ASSERTIONS` + 2 new pytest methods in `verify_workspace.py` / `test_verify_workspace.py`
- 27 tests pass

## PR

PR #30: `feat/security-harness-surface` → `main`. 3 commits:
1. `feat(security): add security harness surface templates and verification`
2. `fix(security): address review-gate findings on security surface templates`
3. `fix(security): address copilot review comments on security surface templates`

## Compound Learnings Written

- `docs/compound/2026-05-05-multi-phase-skill-scope-matrix.md` — Phase 1 always runs; each phase has its own skip condition
- `docs/compound/2026-05-05-stride-evidence-anchor-pattern.md` — STRIDE findings use evidence anchors, not file:line
- `docs/compound/2026-05-05-agent-tool-list-completeness.md` — agents that write files must declare `edit` in tools list
- `docs/compound/2026-05-05-assertion-specificity-agent-file-names.md` — assertions should check agent file names, not persona labels

## Validation

- Command: `$env:PYTHONPATH="src"; D:\Python314\Scripts\pytest.exe tests/test_verify_workspace.py -q`
- Result: `27 passed, 10 subtests passed`

## Notes

- Rubber-duck review caught 2 blocking and 4 non-blocking issues before the first PR; all were resolved in commit 2.
- Copilot PR reviewer caught 7 additional issues: 4 substantive (filename collision ×2, missing edit tool, exec plan drift), 2 advisory (future shipments in commit), 1 typo — all resolved in commit 3.
- Shipment `006-S` closed via `backlogit shipment ship 006-S` on 2026-05-05.
