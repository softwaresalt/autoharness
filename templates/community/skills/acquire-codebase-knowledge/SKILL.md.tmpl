---
# Source: references/awesome-copilot/skills/acquire-codebase-knowledge/SKILL.md
# License: MIT
name: acquire-codebase-knowledge
description: 'Use this skill when the user asks to map, document, or onboard into an existing codebase. Produces structured documentation covering stack, structure, architecture, conventions, integrations, testing, and concerns. Only documents what is verifiable from files or terminal output — never infers or assumes.'
---

# Acquire Codebase Knowledge

Produces seven documentation files in `{{CODEBASE_DOCS_DIRECTORY}}` covering everything needed to work effectively on the project. Only document what is verifiable from files or terminal output — never infer or assume.

## Output Contract (Required)

Before finishing, all of the following must be true:

1. Exactly these files exist in `{{CODEBASE_DOCS_DIRECTORY}}`: `STACK.md`, `STRUCTURE.md`, `ARCHITECTURE.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `TESTING.md`, `CONCERNS.md`.
2. Every claim is traceable to source files, config, or terminal output.
3. Unknowns are marked as `[TODO]`; intent-dependent decisions are marked `[ASK USER]`.
4. Every document includes a short "evidence" list with concrete file paths.
5. Final response includes numbered `[ASK USER]` questions and intent-vs-reality divergences.

## Workflow

Copy and track this checklist:

```
- [ ] Phase 1: Scan project, read intent documents
- [ ] Phase 2: Investigate each documentation area
- [ ] Phase 3: Populate all seven docs
- [ ] Phase 4: Validate docs, present findings, resolve all [ASK USER] items
```

## Focus Area Mode

If the user supplies a focus area (for example: "architecture only" or "testing and concerns"):

1. Always run Phase 1 in full.
2. Fully complete focus-area documents first.
3. For non-focus documents not yet analyzed, keep required sections present and mark unknowns as `[TODO]`.
4. Still run the Phase 4 validation loop on all seven documents before final output.

### Phase 1: Scan and Read Intent

1. Scan the project structure using available tools (file listing, glob, grep).
2. Search for `PRD`, `TRD`, `README`, `ROADMAP`, `SPEC`, `DESIGN` files and read them.
3. Summarise the stated project intent before reading any source code.

### Phase 2: Investigate

Use the scan output to answer questions for each of the seven documentation areas:

| Document | Key Questions |
|---|---|
| STACK | Languages, runtimes, frameworks, dependencies, build tools |
| STRUCTURE | Directory layout, entry points, key files, generated vs source |
| ARCHITECTURE | Layers, patterns, data flow, domain boundaries |
| CONVENTIONS | Naming, formatting, error handling, import style |
| INTEGRATIONS | External APIs, databases, auth providers, monitoring |
| TESTING | Frameworks, file organization, mocking strategy, coverage |
| CONCERNS | Tech debt, bugs, security risks, performance bottlenecks, high-churn files |

### Phase 3: Populate Documents

Create each document in `{{CODEBASE_DOCS_DIRECTORY}}` in this order:

1. **STACK.md** — language, runtime, frameworks, all dependencies
2. **STRUCTURE.md** — directory layout, entry points, key files
3. **ARCHITECTURE.md** — layers, patterns, data flow
4. **CONVENTIONS.md** — naming, formatting, error handling, imports
5. **INTEGRATIONS.md** — external APIs, databases, auth, monitoring
6. **TESTING.md** — frameworks, file organization, mocking strategy
7. **CONCERNS.md** — tech debt, bugs, security risks, performance bottlenecks

Use `[TODO]` for anything that cannot be determined from code. Use `[ASK USER]` where the right answer requires team intent.

### Phase 4: Validate, Repair, Verify

Run this mandatory validation loop before finalizing:

1. For each non-trivial claim, confirm at least one evidence reference exists.
2. If any required section is missing or unsupported, fix the document and re-validate.
3. Repeat until all seven docs pass.

Then present a summary of all seven documents, list every `[ASK USER]` item as a numbered question, and highlight any intent-vs-reality divergences from Phase 1.

## Gotchas

**Monorepos:** Root manifest may have no source — check for `workspaces`, `packages/`, or `apps/` directories. Each workspace may have independent dependencies and conventions.

**Outdated README:** README often describes intended architecture, not the current one. Cross-reference with actual file structure before treating any README claim as fact.

**Generated/compiled output:** Never document patterns from `dist/`, `build/`, `generated/`, `.next/`, `out/`, or `__pycache__/`. Document source conventions only.

**Config files reveal required config:** Read `.env.example`, `.env.template`, or `.env.sample` to discover required environment variables.

**Dev dependencies are not production stack:** Only production dependencies run in production. Document linters, formatters, and test frameworks separately as dev tooling.

**Test TODOs are not production debt:** TODOs inside test directories are coverage gaps, not production technical debt. Separate them in CONCERNS.md.

**High-churn files signal fragile areas:** Files appearing most in recent git history have the highest modification rate and likely hidden complexity. Note them in CONCERNS.md.

## Anti-Patterns

| Don't | Do instead |
|---|---|
| Claim an architecture pattern without matching directory structure | State only what directory structure actually shows |
| Guess the framework without checking the manifest | Check dependencies first |
| Guess the database from a variable name | Check manifest for database driver dependencies |
| Document patterns from build output directories | Source files only |

Generated by autoharness | Template: community/skills/acquire-codebase-knowledge/SKILL.md.tmpl
