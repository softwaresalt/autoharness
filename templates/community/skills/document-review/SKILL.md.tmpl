---
# Source: references/ai-skills/skills/document-review/SKILL.md
# License: MIT
name: document-review
description: 'Structural review of documents for gaps, clarity, completeness, and organization. Use when a brainstorm, plan, spec, ADR, or any doc needs polish before the next workflow step.'
---

# Document Review

Improve brainstorm or plan documents through structured review.

## Step 1: Get the Document

**If a document path is provided:** Read it, then proceed to Step 2.

**If no document is specified:** Ask which document to review, or look for the most recent brainstorm/plan in `{{PLANS_DIRECTORY}}`.

## Step 2: Assess

Read through the document and ask:

- What is unclear?
- What is unnecessary?
- What decision is being avoided?
- What assumptions are unstated?
- Where could scope accidentally expand?
- Is this technically feasible with the current architecture?
- Are there security implications in what's proposed?

These questions surface issues. Don't fix yet -- just note what you find.

## Step 3: Activate Review Lenses

Based on the document's content, activate specialized review perspectives. Scan for signals and apply matching lenses:

| Lens | Signals | What it checks |
|---|---|---|
| **Product** | User-facing features, customer language, market claims, scope decisions | Problem framing, value proposition clarity, whether scope matches stated goals |
| **Design** | UI/UX references, user flows, wireframes, interaction descriptions | Flow completeness, interaction gaps, accessibility considerations |
| **Security** | Auth/authorization, API endpoints, PII, payments, tokens, encryption | Auth model gaps, data exposure risks, missing threat considerations |
| **Scope guardian** | Multiple priority tiers (P0/P1/P2), large requirement count (>8), stretch goals | Scope creep, premature abstractions, features disguised as requirements |
| **Adversarial** | >5 distinct requirements, explicit architectural decisions, high-stakes domains | Unstated assumptions, optimistic estimates, single points of failure, missing failure modes |

Activate a lens when ANY of its signals match. Most documents trigger 1-2 lenses; brainstorm notes may trigger none. When a lens is active, weave its checks into the assessment and evaluation steps rather than running it as a separate pass.

## Step 4: Evaluate

Score the document against these criteria:

| Criterion | What to Check |
|---|---|
| **Clarity** | Problem statement is clear, no vague language ("probably," "consider," "try to") |
| **Completeness** | Required sections present, constraints stated, open questions flagged |
| **Specificity** | Concrete enough for next step (brainstorm → can plan, plan → can implement) |
| **YAGNI** | No hypothetical features, simplest approach chosen |

## Step 5: Identify the Critical Improvement

Among everything found in Steps 2-4, does one issue stand out? If something would significantly improve the document's quality, this is the "must address" item. Highlight it prominently.

## Step 6: Make Changes

Present your findings, then:

1. **Auto-fix** minor issues (vague language, formatting) without asking
2. **Ask approval** before substantive changes (restructuring, removing sections, changing meaning)
3. **Update** the document inline -- no separate files, no metadata sections

### Simplification Guidance

Simplification is purposeful removal of unnecessary complexity, not shortening for its own sake.

**Simplify when:**
- Content serves hypothetical future needs, not current ones
- Sections repeat information already covered elsewhere
- Detail exceeds what's needed to take the next step
- Abstractions or structure add overhead without clarity

**Don't simplify:**
- Constraints or edge cases that affect implementation
- Rationale that explains why alternatives were rejected
- Open questions that need resolution

## Step 7: Reader Test (Optional)

For standalone documents that must be self-contained (onboarding guides, ADRs, external-facing docs), perform a zero-context reread to simulate a first-time reader. Set aside all conversation history and prior context — evaluate the document as if reading it for the first time.

**How to run the test:**

1. **Predict 5-10 reader questions** from the document's stated goals — one per major section or decision. Mix three kinds:
   - Concrete retrieval: "What command sets up the dev environment?"
   - Decision rationale: "Why did we pick X over Y?"
   - Ambiguity probe: "Could a reader interpret <specific phrase> in more than one way?"
2. **Answer each question using only the document text.** Do not draw on conversation history, prior context, or knowledge gained during the review. If the document does not contain enough information to answer, mark it as a gap.
3. **Check for ambiguity and assumptions**: "What feels ambiguous? What prior knowledge does this assume? Are there internal contradictions?"

**Interpret results:**

- Answerable from the document alone → document is self-contained for that question.
- Answer requires outside knowledge → the document has a gap. Fill it.
- Multiple valid interpretations exist → reword for precision.
- Answer contradicts another section → document actively misleads. Highest-priority fix.

Skip for context-dependent docs (brainstorm notes, plan files, internal working docs) where the reader will always have prior context.

## Step 8: Offer Next Action

After changes are complete, ask:

1. **Refine again** - Another review pass
2. **Review complete** - Document is ready

### Iteration Guidance

After 2 refinement passes, recommend completion -- diminishing returns are likely. If the user wants to continue, allow up to 4 passes total. After 4, stop and report "review converged -- further changes require new direction." Do not continue past 4 even on user request without a fresh framing.

Return control to the caller (workflow or user) after selection.

## Constraints

- Fix targeted sections, don't rewrite the whole document. If the structure is fundamentally broken, surface the structural problem and ask for permission to restructure.
- Flag missing sections in your review, but don't add them. The user decides what to include.
- Keep changes minimal. If a paragraph needs tightening, tighten it. Don't expand scope.
- Review inline. No separate review files or metadata sections.

## Success Criteria

- Document read and scored on all four quality criteria
- Relevant review lenses activated and checks applied
- Critical improvements identified with specific suggestions
- User presented with clear next-action choice (refine or complete)
- Revised document saved if changes were approved

Generated by autoharness | Template: community/skills/document-review/SKILL.md.tmpl
