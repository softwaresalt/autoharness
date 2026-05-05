# Security Harness Surface — Implementation Plan

**Date**: 2026-05-05
**Source stash entries**: `ED5BBE3A` (security audit skill), `5394EFAF` (security-reviewer persona), `DE94031D` (security-lens plan reviewer), `EFC65EB9` (security-sentinel agent)
**Covering feature**: Security Harness Surface
**Risk level**: Moderate — additive templates to skill, agent, and instruction surfaces
**Requires plan hardening**: no (additive only, no schema changes, no CLI changes)

---

## Objective

Add a comprehensive security surface to the autoharness template system spanning
three layers:

1. **Security audit skill** — An on-demand security scanning workflow
2. **Security review personas** — Conditional reviewer agents for code and plan review
3. **Security sentinel agent** — A user-invocable comprehensive audit agent

This fills a clear gap: autoharness has `ci-security.instructions.md.tmpl` and
`strict-safety.instructions.md.tmpl` for safety posture, but no dedicated
security scanning, security code review persona, or security plan review lens.

The security surface deepens Primitive 5 (Safety/Guardrails), Primitive 7
(Observability/Review), and Primitive 10 (Operational Closure).

## Design Principles

- **Technology-agnostic**: All templates use `{{VARIABLE}}` placeholders for
  language/framework-specific patterns
- **Conditional activation**: Security reviewers activate based on diff content,
  not unconditionally
- **Layered scanning**: Tier 1 (deterministic regex) + Tier 2 (LLM-assessed)
- **No runtime dependency**: The security skill is a workflow template, not a CLI tool
- **Environment-agnostic**: Works in any AI coding environment, not just VS Code/Copilot

## Source Material

All adapted from atv-starterkit, with significant autoharness-native redesign:

- `atv-starterkit/pkg/scaffold/templates/skills/atv-security/SKILL.md` (719 lines)
- `atv-starterkit/.github/agents/security-reviewer.agent.md`
- `atv-starterkit/.github/agents/security-lens-reviewer.agent.md`
- `atv-starterkit/.github/agents/security-sentinel.agent.md`

---

## Task 1: Create security-reviewer conditional persona template

**Files**: `templates/agents/review/security-reviewer.agent.md.tmpl` (new)
**Scope**: Create a conditional review persona that activates when diffs touch
auth middleware, public endpoints, user input handling, or permission checks.
The reviewer hunts for:

- Injection vectors (SQL, XSS, command, template)
- Auth/authz bypasses
- Secrets in code or logs
- Insecure deserialization
- SSRF and path traversal

Design requirements:

- Confidence threshold: 0.60 (lower than other personas due to security cost asymmetry)
- Must NOT flag defense-in-depth on already-protected code
- Must NOT flag theoretical attacks requiring physical access
- Must NOT produce generic hardening advice without a specific exploitable finding
- Output format: structured JSON findings matching review skill schema
- Uses `{{SECURITY_REVIEW_PATTERNS}}` for language-specific grep patterns
- Leaf executor (subagent_depth: 0)

**Acceptance**: Template has valid YAML frontmatter, uses proper `{{VARIABLE}}`
placeholders, produces valid Markdown when resolved, and follows the same
structural pattern as existing conditional reviewer templates.

## Task 2: Wire security-reviewer into review skill conditional persona table

**Files**: `templates/skills/review/SKILL.md.tmpl` (modify)
**Scope**: Add a row to the "Conditional (based on changed files)" table:

```
| **Security Reviewer** | Auth middleware, public endpoints, input handling, permission checks, secret management | Different from caller |
```

Also add logic in Step 2 (Route Personas) for selecting the Security Reviewer
based on file path patterns and content signals.

**Acceptance**: The security reviewer appears in the conditional persona table
with activation criteria. No unresolved variables introduced.

## Task 3: Create security-lens plan reviewer persona template

**Files**: `templates/agents/review/security-lens-reviewer.agent.md.tmpl` (new)
**Scope**: Create a plan-review persona that evaluates planning documents for
security gaps at the plan level:

- Attack surface inventory (new endpoints, data stores, integrations, inputs)
- Auth/authz gaps (missing access control decisions)
- Data exposure (PII, credentials, financial data handling)
- Third-party trust boundaries
- Secrets and credentials management
- Lightweight 3-threat model (most likely, highest impact, most subtle)

Design requirements:

- Confidence: HIGH (0.80+) when plan introduces unmitigated attack surface
- Confidence: MODERATE (0.60-0.79) when concern likely but may be addressed later
- Below 0.50: suppress
- Must NOT flag code quality, non-security architecture, business logic, or style
- Leaf executor (subagent_depth: 0)

**Acceptance**: Template has valid YAML frontmatter, follows reviewer agent
pattern, uses `{{VARIABLE}}` placeholders where needed.

## Task 4: Wire security-lens into plan-review persona routing

**Files**: `templates/skills/plan-review/SKILL.md.tmpl` (modify)
**Scope**: Add security-lens-reviewer to the plan-review persona catalog as a
conditional persona that activates when plans touch:

- Authentication or authorization systems
- API surfaces or public endpoints
- Data stores with sensitive data
- External integrations crossing trust boundaries
- Secrets, credentials, or key management

**Acceptance**: Security lens appears in plan-review persona routing with clear
activation criteria.

## Task 5: Create security-audit skill template

**Files**: `templates/skills/security-audit/SKILL.md.tmpl` (new)
**Scope**: Create a user-invocable security audit skill adapted from ATV's
atv-security pattern. The skill performs a multi-phase audit:

- Phase 1: Discovery — detect agentic config surfaces + app source stack
- Phase 2: Config Tier 1 — deterministic regex scan of `.github/`, `.vscode/`
- Phase 3: Config Tier 2 — LLM-assessed config rules
- Phase 4: OWASP Top 10 — application source code scan
- Phase 5: STRIDE — threat model
- Phase 6: Score & Grade — weighted aggregate with N/A semantics
- Phase 7: Output — structured report
- Phase 8: Persist — save to `{{DOCS_SECURITY}}/` directory

Design requirements:

- Config rules use `{{AGENTIC_CONFIG_GLOB}}` for config file patterns
- Source patterns use `{{SOURCE_GLOB}}` and `{{PRIMARY_LANGUAGE}}`
- Scoring uses the same deduction model (critical: -15, high: -10, medium: -5, low: -2)
- Report persists to `{{DOCS_SECURITY}}/YYYY-MM-DD-security-report.md`
- Mode: `report` (default) or `fix` (opt-in, config findings only)
- Scope: `full` | `config` | `owasp` | `stride` | `<path>`
- No auto-fix of application source code (OWASP/STRIDE findings are report-only)
- Technology-agnostic: rule sets must be parameterized, not hardcoded for Node/Rails/Python

Variables needed:

- `{{AGENTIC_CONFIG_GLOB}}` — patterns for agentic config locations
- `{{SOURCE_GLOB}}` — application source file patterns
- `{{PRIMARY_LANGUAGE}}` — primary language for pattern selection
- `{{DOCS_SECURITY}}` — security report output directory
- `{{SECURITY_CONFIG_RULES}}` — per-environment config rule table
- `{{SECURITY_OWASP_PATTERNS}}` — language-specific OWASP detection patterns

**Acceptance**: Template produces a coherent multi-phase audit workflow when all
variables are resolved. Valid YAML frontmatter. No unresolved `{{...}}` in
output. Phase structure matches the 8-phase pattern with clear skip conditions.

## Task 6: Create security-sentinel agent template

**Files**: `templates/agents/security-sentinel.agent.md.tmpl` (new)
**Scope**: Create a user-invocable agent that performs comprehensive security
audits with structured reporting. The sentinel:

- Performs input validation analysis
- Assesses SQL injection / injection risk
- Detects XSS vulnerabilities
- Audits authentication & authorization
- Scans for sensitive data exposure
- Checks OWASP Top 10 compliance

Output: Executive summary, detailed findings with severity/location/remediation,
risk matrix, and prioritized remediation roadmap.

Design requirements:

- User-invocable (not part of automated pipeline)
- Uses `{{SECURITY_SCAN_PATTERNS}}` for language-specific patterns
- Leaf executor with `tools: read, search, terminal`
- Model routing: Tier 3 (Frontier) — complex analytical task
- Subagent depth: 0

**Acceptance**: Template has valid YAML frontmatter, follows agent definition
pattern, produces actionable security reports.

## Task 7: Register security-audit variables in install-harness

**Files**: `.github/skills/install-harness/SKILL.md` (modify)
**Scope**: Add the following variables to the install-harness variable
resolution table:

- `{{AGENTIC_CONFIG_GLOB}}` — resolved from workspace profile `agentic.config_paths`
- `{{SOURCE_GLOB}}` — resolved from workspace profile `source.include_patterns`
- `{{DOCS_SECURITY}}` — resolved as `docs/security` (default)
- `{{SECURITY_CONFIG_RULES}}` — resolved based on detected agentic environment
- `{{SECURITY_OWASP_PATTERNS}}` — resolved based on primary language
- `{{SECURITY_SCAN_PATTERNS}}` — resolved based on detected stack
- `{{SECURITY_REVIEW_PATTERNS}}` — resolved based on primary language

Also add `security-audit` to the skill installation manifest and `security-reviewer`,
`security-lens-reviewer`, `security-sentinel` to the agent installation manifest.

**Acceptance**: All new variables appear in the resolution table with source
field, default value, and resolution logic.

## Task 8: Add verify_workspace assertions for security surface

**Files**: `src/autoharness/verify_workspace.py` (modify),
`tests/test_verify_workspace.py` (modify)
**Scope**: Add verification assertions that confirm:

- `security-reviewer.agent.md.tmpl` exists in `templates/agents/review/`
- `security-lens-reviewer.agent.md.tmpl` exists in `templates/agents/review/`
- `security-sentinel.agent.md.tmpl` exists in `templates/agents/`
- `security-audit/SKILL.md.tmpl` exists in `templates/skills/`
- Review skill template references security-reviewer in conditional table
- Plan-review skill template references security-lens-reviewer

Add corresponding test cases.

**Acceptance**: `pytest tests/test_verify_workspace.py` passes with new
assertions.

---

## Dependency Graph

```
Task 1 (security-reviewer persona)     → Task 2 (wire into review skill)
Task 3 (security-lens persona)         → Task 4 (wire into plan-review)
Task 5 (security-audit skill)          → Task 7 (register variables)
Task 6 (security-sentinel agent)       → Task 7 (register variables)
Tasks 1-6                              → Task 8 (verify_workspace assertions)
```

Tasks 1, 3, 5, 6 can proceed in parallel (independent template creation).
Tasks 2, 4 depend on their respective persona templates.
Task 7 depends on Tasks 5 and 6 (needs variable names from skill/agent).
Task 8 depends on all prior tasks.

## Out of Scope

- Schema changes to workspace-profile or harness-config
- CLI distribution changes
- Capability pack registration (security is a core surface, not an overlay)
- Runtime execution of security scans (template only)
- ATV-specific features (marketplace, plugin generator, TUI)
