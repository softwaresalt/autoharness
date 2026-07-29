---
problem_type: regex-detector-hardening
category: failure-signal-false-positives
root_cause: optional-separator-and-newline-spanning-whitespace
tags: [decline-detector, compression-experiment, copilot-review, p-018, regex, evidence-oracle, ship-agent, 093-F, false-positive]
shipment: 098-S
feature: 093-F
pr: 244
merged_at: "2026-07-28T00:00:00Z"
---

# 098-S / PR #244: Colon-Optional Separators Silently Widen a Failure Detector Too Far

## Problem

Feature 093-F broadened the compression-experiment failure-bearing-SUCCESS
decline detector to recognize colon-agnostic forms (`exit code 1` as well as
`exit code: 1`). The first implementation expressed "colon optional, then
any whitespace" as `:?\s*` — for example `exit code:?\s*\d+`. Copilot review
flagged two genuine false-positive classes that this form introduced across
all three surfaces (`policy._FAILURE_BEARING_PATTERNS`,
`hook._EVIDENCE_LINE_PATTERNS`, `evidence_oracle._FACT_PATTERNS`):

1. **Concatenated form** — `:?` makes the separator *optional*, so
   `exit code1` (a digit fused directly to the marker, no separator at all)
   matched and was wrongly classified as a failure signal.
2. **Cross-line form** — `\s*` matches newlines, so `exit code\n1 item
   completed` matched: the marker at the end of one line was stitched to a
   digit that merely *started the next, unrelated line*. This is especially
   dangerous in `evidence_oracle.py`, which scans the **entire multi-line
   capture** with `finditer` — the regex can synthesize a spurious
   "exit code 1" required-fact out of two unrelated lines, corrupting what
   the oracle believes must be preserved.

Both are fail-*unsafe* in the evidence direction: the oracle one can
manufacture a required fact that never existed, and the policy/hook ones can
decline (refuse to compress) benign successful output.

## Solution — A Horizontal-Only, Mandatory Separator

Replace `:?\s*` with an explicit separator token that (a) is **mandatory**
and (b) **never matches a newline**:

```python
_SEP    = r"(?::[ \t]*|[ \t]+)"   # colon+optional h-space  OR  one-or-more h-space
_RC_SEP = r"(?:=[ \t]*|[ \t]+)"   # returncode's '=' form   OR  one-or-more h-space
```

Then `exit code{_SEP}\d+`, `returncode{_RC_SEP}\d+`, etc. The separator now
requires a colon-or-horizontal-whitespace delimiter on the **same line**:
`exit code1` no longer matches (no separator), and `exit code\n1` no longer
matches (`[ \t]` excludes `\n`). This keeps every detection same-line and
explicitly delimited while preserving all the intended broadened forms.

## Key Lesson: Broaden With an Explicit Separator Token, Never `:?\s*`

When widening a token-based detector to accept an optional punctuation
separator, do **not** reach for `:?\s*` (or `[=\s]\s*`). Two independent
hazards ride along:

- `?` on the separator quietly makes the separator *absent-able*, matching
  concatenated garbage. If a separator is semantically required, keep it
  required — express "colon OR space" as a mandatory alternation, not
  "colon optional then whitespace".
- `\s` / `\s*` spans newlines by default. Any detector that runs over a
  multi-line string (`finditer`, `re.MULTILINE`, or just a big captured
  blob) will cross-line-stitch. Use `[ \t]` for "horizontal whitespace on
  this line" whenever the match must stay line-local. Reserve `\s`/newline
  spanning for patterns that genuinely intend to cross lines.

## Key Lesson: Preserve Each Surface's Intentional Differences During Parity

The three surfaces are in *semantic* parity for the broadened forms, **not**
literal set-equality. When applying the same `_SEP` fix, the intentional
per-surface differences had to be preserved:

- `policy.py` uses `[1-9]\d*` (declines only **non-zero** exit forms — a
  successful `exit code 0` must stay compressible).
- `hook.py` and `evidence_oracle.py` use `\d+` (they also protect zero-exit
  forms by design — evidence preservation is form-based, not verdict-based).
- `evidence_oracle.py` keeps a **whole-line** match for `npm ERR!`
  (`(?im)^.*npm ERR!.*$`) so the full marker line becomes the required fact.

A blind copy-paste "make all three identical" would have regressed these
deliberate differences. Parity means *the broadened forms behave
consistently*, not *the pattern lists are byte-identical*.

## Key Lesson: Ship Negative Controls With Every Detector Broadening

The original change added only positive controls (the new forms are
detected). The false positives slipped through because there were no
**negative** controls asserting the boundary. The fix added, in each of the
three test files, explicit negative controls for both hazard classes:

- concatenated: `exit code1` / `exit status1` / `returncode1` → not a signal
- cross-line: `exit code\n1 item completed` → not a signal / no synthesized
  fact

A detector-broadening PR is incomplete without negative controls that pin
the new boundary; positive-only coverage cannot catch an *over*-broadening.

## Process Note: Resolving Threads Never Re-Triggers; Pushing Does

Consistent with 093-S: the fix was one consolidated `git push` (which
re-armed exactly one fresh Copilot pass that came back clean), followed by
GraphQL `resolveReviewThread` on both threads and a `gh pr edit --body-file`
readiness-block update — neither of which re-triggers review. Drive
unresolved-thread count to zero via reply+resolve after you stop pushing
code, and the P-018 gate converges deterministically.
