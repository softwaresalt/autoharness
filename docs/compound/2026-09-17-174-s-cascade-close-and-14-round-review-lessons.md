---
title: "174-S closure: INV-6 path-specific narrowing, ClosePathDecision descendant-ID exposure, and four operational pitfalls from a 14-round P-018 cycle"
problem_type: review-coverage-gap
category: hosted-review-pattern-learning
root_cause: "Round-7's fix to the P-015 cascade-close gate introduced a new path-specific narrowing rule (only truly-archived out-of-manifest descendants block CASCADE) without updating the older, broader INV-6 invariant text that still unconditionally forced SAFE_CLOSE whenever any live/required validated_linked_deliberations(S) member existed — leaving the two rules inconsistent across the installed skill, its template mirror, and doc references. Separately, ClosePathDecision's classifier computed out_of_manifest_descendant_ids internally but never returned it in the public dataclass shape, forcing any caller needing to baseline/fingerprint that set to re-derive it out-of-band (a forbidden re-derivation per the skill's own INV-7/INV-10 invariants)."
resolution_type: code+process
severity: medium
component: "shipment_closure gate (src/autoharness/gates/shipment_closure.py) / shipment-reconcile skill (installed + template) / workflow-policies"
related_pr: 454
related_shipment: 174-S
related_feature: 166-F
doc_type: learning
source: docs/compound/2026-09-17-174-s-cascade-close-and-14-round-review-lessons.md
tags:
  - copilot-review
  - review-pattern
  - p-015
  - p-018
  - p-021
  - compound-learning
  - closure-evidence
  - cascade-close
  - classifier-shape
  - invariant-consistency
  - powershell-pitfall
citations:
  - "PR #454 (174-S: flat-manifest shipment closure), 14 rounds of Copilot review, 52 threads (52 resolved)"
  - "src/autoharness/gates/shipment_closure.py (classify_shipment_close_path, ClosePathDecision)"
  - ".github/skills/shipment-reconcile/SKILL.md + templates/skills/shipment-reconcile/SKILL.md.tmpl (Cascade Close Sub-Procedure)"
  - ".backlogit/reconcile/174-S-safe-close-20260917-062522.md (this shipment's own cascade-close report, produced under the corrected rules)"
---

## Summary

Shipment 174-S ("flat-manifest shipment closure") shipped a new P-015
`classify_shipment_close_path` gate distinguishing a narrow `CASCADE` exception from the
default `SAFE_CLOSE` path, plus hardened invariant text in the `shipment-reconcile` skill.
Getting this right took 14 rounds of hosted Copilot review (52 threads) on PR #454. Round 8
surfaced two genuine same-contract-surface defects in the round-7 fix itself (fixed under
explicit operator authorization to extend past the normal 3-cycle review-fix limit, per
P-021 C1/C3). This entry captures those two fixes plus four operational pitfalls hit along
the way, so future sessions do not have to rediscover them.

## Lesson 1 — INV-6 must be narrowed to match the new path-specific CASCADE exception

**Problem**: INV-6 (as introduced pre-174-S) said, in effect: "if any live/required
`validated_linked_deliberations(S)` member exists, SAFE_CLOSE is forced." Round 7 introduced
`classify_shipment_close_path`'s CASCADE path specifically to *permit* cascading through such
members when they are legitimately reachable and archivable as part of the qualifying
feature's closure — but INV-6's prose was never updated to say "...unless the classifier's
CASCADE path applies," so the invariant text (both installed skill and template mirror) still
read as an unconditional block, contradicting the code it was supposed to describe.

**Fix**: Re-scoped INV-6's text in both `.github/skills/shipment-reconcile/SKILL.md` and
`templates/skills/shipment-reconcile/SKILL.md.tmpl` (kept at parity in the same commit) to
read as a SAFE_CLOSE-path-specific rule: it still unconditionally blocks *SAFE_CLOSE* from
archiving a live/required linked-deliberation member, but explicitly defers to the
classifier's CASCADE verdict when `classify_shipment_close_path` has independently determined
the member is a qualifying, engine-inert-satisfying descendant. This is a **narrowing**, not a
weakening: SAFE_CLOSE's behavior is unchanged; only the previously-contradictory prose is
corrected to match what CASCADE was already coded to do.

**Generalization**: whenever a new classifier exception path is added to a closure/gating
skill, grep the skill text (and its template mirror) for every existing invariant/prose
statement that makes an unconditional claim the new path is designed to override, and update
each one explicitly — do not assume a new code path is self-documenting against pre-existing
prose written before it existed.

## Lesson 2 — ClosePathDecision must expose the classified descendant-ID set, not force re-derivation

**Problem**: `classify_shipment_close_path` computes `out_of_manifest_descendant_ids`
internally (to decide whether every such descendant is engine-inert) but the returned
`ClosePathDecision` dataclass did not expose this set as a field. Every caller needing to
baseline-fingerprint that set for the INV-7/INV-10 invariance check (the Cascade Close
Sub-Procedure's baseline-fingerprint-capture and post-invocation-invariance steps) had no
sanctioned way to obtain it except re-deriving it independently — which is itself a violation
of the skill's own "never re-derive, always reuse the classifier's own output" rule, since two
independent derivations can silently drift apart (the exact class of bug INV-7/INV-10 exist to
prevent).

**Fix**: Added `out_of_manifest_descendant_ids: tuple[str, ...]` as a public field on
`ClosePathDecision`, populated with the same set already computed internally (no new
computation, no behavior change to the classification decision itself — purely an
information-exposure fix). Added test-first coverage asserting the field is populated
correctly for both a CASCADE decision with a non-empty descendant set and a CASCADE decision
with an empty one (174-S's own case), plus a SAFE_CLOSE decision (where the field should still
be populated/empty as appropriate, never omitted).

**Generalization**: any classifier/gate function whose internal working set feeds a
downstream invariant check must expose that same set as part of its return shape — "compute
once, reuse everywhere" is not just a performance rule here, it is a correctness invariant
against classification drift.

## Lesson 3 — PowerShell here-string backtick-escaping corrupts inline code spans in GitHub API bodies

Inside a **double-quoted** here-string (`@"..."@`), the backtick remains PowerShell's escape
character. A markdown inline-code span like `` `validated_linked_deliberations(S)` `` can get
silently corrupted if the character immediately following an internal backtick happens to form
a recognized escape sequence (e.g. `` `v `` → vertical tab, `` `n `` → newline, `` `t `` →
tab). This produced a mangled Copilot-reply comment mid-cycle, caught only because the
comment rendered with an unexpected control character. **Fix/rule**: always use
**single-quoted** here-strings (`@'...'@`) for any GitHub API comment/PR body text that
contains inline code spans — single-quoted here-strings perform no escape processing at all.

## Lesson 4 — `last_code_affecting_head` anchor must bump for skill-text (procedure) changes, not just `.py` source

A recurring assumption (present through rounds 12-13 of this same cycle) was that only
`.py` source changes are "code-affecting" for a closure artifact's `last_code_affecting_head`
frontmatter anchor, and that changes to `.github/skills/*/SKILL.md` prose are "documentation
only" and don't require bumping it. Round 14 review correctly identified this as wrong: a
`SKILL.md` file *is* the executable procedure text an agent follows — changing its Cascade
Close Sub-Procedure steps changes actual closure behavior just as much as changing the Python
gate it partially describes. **Rule going forward**: any edit to an agent-executed skill
procedure (not just its narrated prose/examples) counts as code-affecting for anchor-currency
purposes, exactly like a `.py`/`.go` source change.

## Lesson 5 — `classify_shipment_close_path` returns CASCADE (not SAFE_CLOSE) when the out-of-manifest descendant set is empty

Confirmed (not a new code change, but worth recording as a non-obvious classifier behavior):
a qualifying feature with **zero** out-of-manifest descendants satisfies the "every
out-of-manifest descendant is engine-inert" condition **vacuously**, so the classifier
selects `CASCADE`, not the more conservative `SAFE_CLOSE`. This was 174-S's own case
(feature `166-F`'s only descendants were its 6 manifest tasks, already all inside the
manifest) — CASCADE was the *correct* verdict, not evidence of a bug. Future sessions should
not be surprised by, or attempt to "fix," this vacuous-truth behavior; it is intentional and
now covered by regression tests added under Lesson 2's test-first work.

## Lesson 6 — the `file-lock` skill's `scripts/` subdirectory can be missing from an installed mirror

In this workspace, `.github/skills/file-lock/SKILL.md` is installed but the accompanying
`scripts/{acquire,release}_lock.ps1` (and `.sh` variants) were never rendered/copied there —
only the `templates/skills/file-lock/scripts/` source exists. The template script's own
workspace-root auto-detection assumes it is invoked from an installed
`{root}/scripts/{name}.ps1` location and fails closed with a "widening guard" error when run
from the nested template path. Workaround used successfully: pass `-WorkspaceRoot` explicitly
to override auto-detection. This is a pre-existing install-completeness gap, out of scope for
174-S itself, but worth flagging for a future harness-install audit.

## Outcome

All fixes were applied under explicit operator authorization to extend past the normal
3-review-fix-cycle limit for genuinely in-scope (same-contract-surface) findings, per P-021
C1/C3. PR #454 reached Copilot review round 15 with `SATISFIED` (zero new threads), merged via
merge-commit strategy (`d8615e9d5eb93a1d1616a735ca1433236868bee1`), and shipment 174-S was
subsequently closed via the (now-corrected) CASCADE path — the first live production use of
the corrected INV-6 text and the exposed `out_of_manifest_descendant_ids` field.
