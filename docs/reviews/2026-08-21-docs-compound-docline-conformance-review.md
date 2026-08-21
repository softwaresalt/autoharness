---
title: "Plan review - docs/compound docline conformance"
date: 2026-08-21
plan: docs/plans/2026-08-21-docs-compound-docline-conformance-plan.md
stash_id: F73BA065
deliberation: "025-DL"
verdict: PASS
review_fix_cycle: 4
regated: 2026-08-21
cycle_4_authorization: operator-authorized-extension
---

# Plan Review - docs/compound docline conformance

Date: 2026-08-21
Agent: Stage (plan-review gate)
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Verdict

**PASS (re-gated after review-fix cycle 2).**

*Original pass:* 1 P1 raised and RESOLVED by amendment C1; 2 P2 raised, both
resolved by amendment C2.

*Review-fix cycle 2* (Copilot review on PR #386 at HEAD `c992b2bf`; 1 of the 8
current-head threads landed here - `PRRT_kwDORzpWpM6bSzNc`): **P1-2** raised -
amendment C1 was recorded but never APPLIED to the plan's operative verification
gate, which still demanded zero errors for `source`/`doc_type` only. RESOLVED by
rewriting the operative gate in place.

*Review-fix cycle 4* (Copilot review on PR #386 at HEAD `d098d8a2`; 2 of the 7
current-head threads landed here - `PRRT_kwDORzpWpM6bTooh`, `PRRT_kwDORzpWpM6bToo3`):
**P1-3** raised - the planned base-template edit hard-codes a backlogit-only command
into a base Primitive 1 artifact. RESOLVED by amendment C3.

**0 unresolved P0/P1.** Review-fix cycles used: **4** (3 standard + 1 operator-authorized).

**Cycle-4 authorization (documented per P-005).** The Stage stop-condition table
caps review-fix cycles at 3 per plan. Cycle 4 was performed under an EXPLICIT
OPERATOR AUTHORIZATION extending the Stage review-fix budget for the seven current-head
P-018 blockers, granted 2026-08-21 with the instruction not to stop at planning or
blockers. Same-error-recurrence and universal circuit-breaker limits were NOT relaxed
and remain in force. This is an authorized budget extension, not a self-granted one.

## P1-1 (RESOLVED by amendment C1) - the verification gate proves too little

**Finding.** The shipment verification gate reads "`backlogit docs lint --path
docs/compound` reports zero required-field errors for `source`/`doc_type`."
That is scoped to the two fields the stash entry happened to observe. The docline
base contract may require additional fields that were never reached, because the
linter reports per-file errors and the entry only recorded the first two. If a
third required field exists, this shipment closes reporting success while the
corpus still fails lint - converting a real gap into a believed-closed gap, which
is strictly worse than the current state.

**Why it is P1.** The whole value of this shipment is a trustworthy lint signal
for `docs/compound/`. An acceptance criterion that cannot distinguish "conformant"
from "conformant with respect to two fields I already knew about" does not
deliver that value.

**Resolution (C1).** The gate is rewritten to require ZERO required-field errors
of ANY kind for `docs/compound`. If residual error classes appear, they must be
enumerated by field name and either fixed in Task 1 (if mechanically derivable
like `doc_type`) or captured as a NEW deferred stash entry under P-021 C1 - never
silently accepted.

**Follow-up (cycle 2, P1-2; thread `PRRT_kwDORzpWpM6bSzNc`).** C1 was recorded in
the plan's amendment appendix, but the plan's OPERATIVE "Verification gate for the
shipment" section was left untouched and still read "reports zero required-field
errors for `source`/`doc_type`". An executing agent reading the gate section - the
section that actually governs closure - would have applied the narrow, superseded
predicate and closed the shipment reporting success while a third required-field
class still failed lint: precisely the believed-closed-gap failure C1 exists to
prevent. The operative gate has now been REWRITTEN in place to demand ZERO
required-field errors of ANY kind, with explicit enumerate-by-field-name,
fix-or-capture, and no-silent-acceptance sub-rules, plus a rule that a `90F2A9F8`
hard-abort which prevents complete enumeration means the gate is NOT met. The C1
bullet is now marked as APPLIED rather than merely recorded.

## P2-1 (RESOLVED by amendment C2) - the four no-frontmatter files were left unnamed

**Finding.** The plan says four files have no frontmatter block and requires them
to be enumerated during execution. Stage already has that list; withholding it
makes the executing agent redo Stage's measurement and risks a different count if
the corpus changes.

**Resolution (C2).** The four files are now named in the plan.

## P2-2 (RESOLVED by amendment C2) - test scope must exclude non-markdown

**Finding.** `docs/compound/` contains a `.gitkeep`. The proposed contract test
says "every `*.md`", which is correct, but the plan's prose elsewhere says "every
document". Tighten to `*.md` explicitly so a future non-markdown asset does not
fail the guard spuriously.

**Resolution (C2).** Folded in.

## Confirmed strengths (no action)

* The dry-run-then-gate-then-apply ordering, with a blocking human-readable check
  on the `source` value before any write, is the correct shape for a 73-file
  mechanical migration and is the single most important safety property here.
* Requiring PROOF of body invariance by diff (AC2) rather than trusting the
  tool's own `body_bytes_changed: false` claim is properly sceptical.
* Requiring an idempotence re-run (AC4) is the right acceptance test for a
  migration and is frequently omitted.
* The width isolation between the data migration (Task 1) and the template
  contract edit (Task 2) is correct and should not be collapsed for convenience.
* The `requires_plan_hardening: no` determination is explicitly reasoned rather
  than defaulted, satisfying P-006's fail-safe intent.

## P1-3 (RAISED in review-fix cycle 4; RESOLVED by amendment C3) - a base Primitive 1 template must not hard-code one backlog tool

**Threads.** `PRRT_kwDORzpWpM6bTooh` (140.002-T), `PRRT_kwDORzpWpM6bToo3` (plan Task 2).

**Finding.** Task 2 step 2 required the amended
`templates/skills/compound/SKILL.md.tmpl` to state that `backlogit docs classify
<path>` is the authority for `doc_type`. `compound` is a **base Primitive 1
artifact**: it is installed into workspaces that may have no backlogit, and indeed
no backlog tool at all. In such a workspace that instruction is dead guidance and
the author is left with no resolution path for a REQUIRED frontmatter field - so the
amendment intended to make new documents born-conformant would instead make them
unresolvable. It also breaks autoharness's global-tool / local-output separation:
the backlog tool is global and swappable, the template is the product.

**Why it is P1.** It defeats the purpose of the task. Task 2 exists precisely so the
next compound document is born conformant; guidance that cannot be followed without
one specific tool reopens the gap in every non-backlogit workspace, and does so
silently.

**Resolution (C3).** The template states a CAPABILITY-NEUTRAL AUTHORITY ORDER and
names no tool:

1. the workspace's documentation-classification operation, if its tooling exposes one;
2. otherwise the workspace's configured documentation path map;
3. otherwise the directory convention - which yields `learning` for this skill's own
   output.

Rung 3 always resolves, so no unresolved customization point is left behind - this
is the difference between "capability-conditioned" and "capability-dependent".
Enforced by new **AC8b**: a MECHANICAL scan asserting the template contains no
backlog-tool name or CLI command in the `doc_type`/`source` guidance, so a future
edit cannot quietly reintroduce one.

**Alternatives rejected, with reasons.** A registry-backed template variable
(`{{OP_DOC_CLASSIFY_CLI}}`, following the existing `{{OP_*}}` family at
`.github/skills/install-harness/SKILL.md:240-254` with its empty-string default) is
the right pattern for genuinely tool-shaped values, but here it would require an
install-harness variable-table row in both the template and the installed `SKILL.md`
(paired edit + manifest checksum, breaking AC10), a `_derive_template_variables`
change (**142-F's** surface - a cross-feature width breach under P-003) and a
registry schema key, while contradicting AC8. A backlogit capability-pack overlay
was likewise rejected: the pack layer does not currently cover documentation
classification, so it would need the same paired edit and checksum churn.
`doc_type` is path-derived; it needs no tool indirection at all. Choosing prose over
a variable REMOVED surface rather than adding it, so `requires_plan_hardening: no`
is unchanged.
