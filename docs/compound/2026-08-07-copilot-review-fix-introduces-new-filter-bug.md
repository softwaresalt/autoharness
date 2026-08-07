# Compound Learning: Copilot Review Fixes Can Introduce a New, Subtly Unsafe Filter

**Origin**: PR #310 (119-S / 111-F, crash-resumption + prune-on-restore protocol),
3 rounds of Copilot review across HEADs `17bb889` → `8a504c2` → `753a1ef` → `4d90536`.

## The pattern

Across 3 review rounds, 16 total Copilot inline comments were raised — but the
important structural lesson isn't the comment count, it's that **each round's fix
for a genuine "unsafe filter" finding itself introduced a new, more subtle unsafe
filter**, which the next round's re-armed Copilot review (`autoharness gate
copilot-review` re-arms on every HEAD push) then caught:

1. **Round 1**: `max_age_hours: 168` on checkpoint-listing calls could hide a
   genuinely unresolved active checkpoint older than a week. Fix: remove the age
   filter, add an `agent == stage/ship` post-filter to scope enumeration to the
   agent's own checkpoints.
2. **Round 2**: the round-1 fix's own `agent == stage/ship` post-filter (and the
   Orchestrator's pre-existing `status=active` filter) could silently drop a
   parse-failure/quarantined checkpoint whose `agent`/`status` fields are empty —
   exactly the kind of anomaly a fail-closed protocol must never lose. Fix:
   enumerate with NO filter at the API-call level, check for validation/quarantine
   anomalies FIRST on the full unfiltered result, fail closed on any anomaly, and
   only then partition to the valid/owned/active subset.
3. **Round 3**: the round-2 fix's own `cleanup_checkpoints` sequencing guard
   treated "explicit operator handoff" as an acceptable disposition alongside
   `resolve_checkpoint` — but a fail-closed operator handoff, by definition,
   performs NO resolve and deliberately leaves the checkpoint active/unresolved.
   Treating handoff as sufficient disposition would let retention-based cleanup
   erase the exact checkpoint the handoff existed to protect. Fix: require ONLY
   `resolve_checkpoint` after a confirmed resume, OR a separate, explicit, NAMED
   operator archival/abandonment decision — never handoff alone.

## Why this kept happening

Every fix in this shipment was **adding a filter or a gate condition** to narrow
an unsafe behavior. But narrowing scope by adding a filter is exactly the failure
mode a fail-closed protocol is designed to avoid: a filter applied too early (at
enumeration, or as a disposition-sufficiency test) can silently exclude the
anomalous/unresolved case the protocol exists to catch. The fix for "this filter
hides bad state" is almost never "add a narrower filter" — it's "invert the
check order: enumerate unfiltered, check for anomalies/insufficient-disposition
FIRST, and only filter/exclude AFTER that check clears."

## Generalizable rule for future fail-closed protocol work

When fixing a Copilot (or any reviewer) finding that says "this filter/condition
can hide an unresolved/anomalous case":

1. **Do not just narrow the filter.** Ask: could the *new* filter also exclude an
   anomalous case by the same mechanism (empty/missing field, ambiguous status,
   an action that merely resembles-but-isn't the required disposition)?
2. **Re-run the review gate after every fix-and-push, unconditionally.** Copilot
   review re-arms on every HEAD advance (`autoharness gate copilot-review`), and
   it WILL re-review code the previous round didn't touch, including the fix
   itself. Budget for this — do not assume round N+1 will be clean just because
   round N's specific findings were addressed.
3. **Prefer "unfiltered enumeration + anomaly-first fail-closed check + only-then
   partition"** as the structural pattern for any candidate-selection logic in a
   fail-closed protocol, rather than composing narrower and narrower single-pass
   filters.
4. **Distinguish "no action taken" (fail-closed handoff) from "an action was
   taken that authorizes the next step" (resolve, or an explicit named
   archival/abandonment decision).** A protocol step whose entire purpose is to
   preserve state for later (a handoff) must never be treated as equivalent to a
   step that explicitly disposes of that state. This is a recurring shape:
   watch for it whenever a "fallback"/"degraded"/"handoff" path is later treated,
   even implicitly, as satisfying a downstream gate meant for successful/explicit
   completion.

## Operational note

Because the dark-mode contract for this shipment removed the review-fix-cycle cap
(operator-authorized, task-scoped), this pattern was allowed to run to
completion (3 rounds) rather than being capped at the default max-3 review-fix
cycles. Under the default (non-dark-mode) cap, this shipment's fix pattern would
have been a legitimate candidate for hitting the cap and requiring
`READY_WITH_FOLLOWUPS` with explicit follow-up items rather than full resolution
— worth remembering when scoping future crash-resumption/fail-closed protocol
changes without an uncapped review-fix budget.
