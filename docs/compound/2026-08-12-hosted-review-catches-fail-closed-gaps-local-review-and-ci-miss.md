---
title: "Hosted (Copilot) PR review caught real safety-critical bugs that local review and CI both missed"
tags: [review, safety, fail-closed, locking, redaction, backlogit, shipment-closure]
provenance: "127-S / 118-F, PR #326"
---

## Summary

Across 4 remediation rounds of hosted Copilot review on PR #326 (21
distinct threads total across 6 raw GitHub review submissions: 16 initial +
5 follow-on), Copilot surfaced genuine race conditions and
fail-closed gaps in three new safety-critical modules
(`src/autoharness/supervise/locking.py`, `src/autoharness/supervise/redact.py`,
`src/autoharness/gates/shipment_closure.py`) that had already passed local
report-only review (2 findings, both fixed) and a full green CI run
(1587 unittest / 1574+13 pytest). This is a concrete, reproducible case for
why the Ship pipeline runs hosted review as an additional gate rather than
treating local review + CI as sufficient for security/safety-critical code.

## What hosted review found that local review + CI did not

1. **`locking.py` — acquire/release/force_unlock ordering races**:
   - `SessionLock.release()` released the OS guard *before* deleting the
     holder record, creating a window where a new acquirer could grab the
     guard while the old (soon-to-be-deleted) record was still readable —
     fixed by reordering to delete-record-then-release-guard.
   - `SessionLock.acquire()` did not clean up state on a record-write
     failure after the guard was already held, leaking a held guard on a
     partial failure — fixed by releasing/resetting state on write failure.
   - `force_unlock()` trusted a liveness diagnosis computed *before* entering
     its own critical section, which is a classic check-then-act race if the
     holder's liveness changed between diagnosis and the critical section —
     fixed by re-diagnosing liveness fresh *inside* the critical section.
2. **`redact.py` — the single secret-redaction choke point had multiple
   fail-open paths**:
   - Unsupported nested value types silently passed through unredacted
     instead of failing closed.
   - Mapping *keys* (not just values) could carry secrets and were not
     redacted at all.
   - The fail-closed warning path interpolated the raw exception text/class
     name into output — an information-leak vector for exactly the kind of
     data this module exists to protect.
   - Non-string mapping keys (round 2) still bypassed key redaction.
3. **`shipment_closure.py` — the new P-015 destructive-gate classifier had
   multiple ambiguity/trust gaps**:
   - No verification that an artifact's frontmatter `id` actually matched
     the file it was glob-matched from (glob-injection / stale-match risk).
   - A missing frontmatter `id` silently fell back to trusting the filename
     stem as the id (round 3 finding) — exactly the kind of implicit trust
     a destructive classifier must never extend.
   - Malformed/ambiguous `parent_id` values were silently dropped instead of
     failing the whole manifest closed.
   - Symlink-following in the backlog lookup path (round 4, explicitly
     deferred as P2 — same risk class as a pre-existing, already-accepted
     symlink tradeoff elsewhere in `locking.py`).

## Generalizable lesson

For newly-introduced security/safety-critical modules (locking primitives,
secret redaction, destructive-operation classifiers), local report-only
review and a green test suite are necessary but demonstrably not sufficient.
Hosted review with a different reviewing model finds a *different class* of
bug than either: it is better at spotting ordering/race conditions across
multiple methods of the same class, silent fail-open defaults in a
choke-point function, and implicit-trust gaps in matching/lookup logic —
none of which a unit test written by the same author who wrote the
implementation is likely to think to assert against. Budget for at least
one full hosted-review round (ideally with the 3-cycle circuit breaker this
pipeline already enforces) on any PR that touches this class of module, even
when local review and CI are both clean.

## Self-correction lesson: verify your own fixes before the next round

While remediating Round 1's 13 findings, a fix introduced a *new* latent bug
(a call to `BacklogUnavailableError(reason=...)` omitting the required
`path` positional argument, which would have raised `TypeError` and masked
the real fail-closed classification path). This was caught and fixed
*before* it was ever flagged by Copilot or a test failure, simply by
re-reading the full diff before the round-2 push. When fixing several
findings under review-cycle time pressure, always re-run the full test
suite (not just the tests for the lines just touched) and re-read the
complete diff once more before pushing — a fix for one review comment can
silently break an unrelated call site.
