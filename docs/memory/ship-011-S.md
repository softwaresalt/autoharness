---
session: ship-011-S
shipment: 011-S
branch: feat/011-S-external-pattern-evaluation
pr: 41
merged_at: "2026-05-07T07:12:00Z"
merge_sha: fb49c783632dca316451a3e71c8d75d43915a332
status: shipped
---

# Ship Session Memory — 011-S

## What was shipped

Four spike research findings evaluating external patterns from ATV's starterkit
for potential adoption into autoharness.

## Tasks completed

- **011.001-T**: Karpathy coding-discipline guidelines vs. constitution gap analysis
  → ADOPT as `coding-discipline.instructions.md.tmpl` (fills gap constitution explicitly leaves open)
- **011.002-T**: ATV 28-persona review catalog vs. autoharness review agent set
  → ADOPT-SUBSET: correctness + maintainability always-on; 5 conditional personas
- **011.003-T**: SDK `intelligence.go` rate-limiting / circuit-breaker / offline-degradation patterns
  → PARTIAL-ADOPT: time-based cooldown mechanism only (circuit-breaker and concurrency
  instructions are already universal guardrails; offline degradation is SDK-specific)
- **011.004-T**: plugingen audit portability pattern → ADOPT as new PORTABILITY_ASSERTIONS
  group in `verify_workspace.py`, targeting installed artifacts for environment-specific
  references (local-agents dir, VS Code paths, IDE-specific config paths)

## Key decisions

- Karpathy guidelines fit cleanly as a new `.instructions.md.tmpl` file because every
  rule targets a real LLM failure mode and the constitution explicitly excludes coding style
- ATV's 28 personas include many that overlap with autoharness reviewers; only net-new
  personas (migration-safety, dependency-hygiene, observability, type-safety, async-hygiene)
  were proposed as conditional additions
- SDK intelligence patterns: time-based cooldown (exponential backoff) was the only
  genuinely new pattern; circuit-breaker is already a universal guardrail in autoharness
- Portability audit: the allow-list contract uses `(rule, file_glob)` tuples with `fnmatch`
  matching — not content-pattern matching — so exemptions are path-scoped, not text-scoped

## Copilot review rounds

### Round 1 (6 threads, all resolved)
- Renamed "Absolute autoharness home" → "Hardcoded autoharness home" (tilde is shell-expanded)
- Removed "unparameterized tool names" from Category C (template-lint concern, not portability scan)
- Redesigned allow-list contract to `(rule, file_glob)` tuple list with `fnmatch`
- Clarified `circuitBreakerCool` naming

### Round 2 (4 threads, all resolved)
- Fixed nested code fence: switched outer fence from triple-backtick to 4-backtick
  so inner plan example triple-backtick renders without literal backslash escaping
- Category B "Regex" column: removed descriptive text; kept only the regex pattern;
  moved scope context to "What it catches"; "templates" → "installed harness artifacts"
- Fixed shipment status `review` → `active` (shipment type only allows queued/active/shipped/abandoned)
- Updated PR description to include backlogit tracking artifact changes

## Files created

- `docs/spikes/011.001-coding-discipline-instructions.md`
- `docs/spikes/011.002-review-persona-expansion.md`
- `docs/spikes/011.003-sdk-guardrail-patterns.md`
- `docs/spikes/011.004-portability-audit-pattern.md`

## Files modified

- `.backlogit/queue/011-S.md` — status changes during session
- `.backlogit/archive/011.001-T.md` through `011.004-T.md` — task archive records

## Next steps

The four ADOPT/ADOPT-SUBSET/PARTIAL-ADOPT spike findings should each seed a backlog
task for implementation:
- 012-S (already staged) covers implementation of these findings
