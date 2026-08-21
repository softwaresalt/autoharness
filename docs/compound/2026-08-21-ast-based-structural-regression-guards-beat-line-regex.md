++ D:\Source\GitHub\autoharness\docs\compound\2026-08-21-ast-based-structural-regression-guards-beat-line-regex.md
---
problem_type: structural_regression_guard_coverage_gap
category: testing
root_cause: A line-oriented regex scanning raw source text for a hardcoded path-construction pattern only matches the exact textual shapes it was written against; structurally equivalent code (a call whose arguments are split across lines, or a different join API) evades it entirely.
tags: [testing, ast, regression-guard, p-021, review-fix]
shipment: 146-S
task: 138.001-T
date: 2026-08-21
---

# AST-Based Structural Regression Guards Beat Line-Oriented Regex

## Problem

138.001-T added Regression Guard 2 to `tests/test_scope_containment_policy_contract.py`:
a structural assertion that no P-021 contract-test module constructs a
hardcoded, lifecycle-volatile `.backlogit/queue/019-DL.md`-style path outside
the shared `_resolve_backlog_artifact` resolver. The first implementation was
a line-oriented regex (`["\']queue["\']\s*/|/\s*["\']queue["\']`, later
widened to also match a single embedded string literal) applied to raw
source text with comments/docstrings stripped via `tokenize`/`ast`.

Two review passes each found a real coverage gap in the SAME guard:

1. Local review (code-review agent, pre-PR): the initial regex only matched
   the split path-join style (`"queue" / expr`), missing a single string/
   f-string literal embedding `queue/`.
2. Copilot review (PR #376, thread PRRT_kwDORzpWpM6bGnEd), on the widened
   regex: `backlog_root.joinpath("queue", "019-DL.md")` — especially with
   arguments split across lines — contains neither shape, so it would pass
   undetected despite violating the guard's stated invariant.

## Root Cause

A regex over raw text (even after comment/docstring stripping) can only
encode the textual shapes its author anticipated. Path construction can take
arbitrarily many equivalent forms (`/` operator chains, `.joinpath()`,
`.join()`, `os.path.join()`, f-strings, multi-line calls with split
arguments) that all reduce to the same semantic operation but do not share a
common textual pattern. Each round of "widen the regex" fixes the reported
shape but leaves the next unanticipated shape uncaught — a whack-a-mole
pattern, not closure.

## Fix

Rewrote the guard as an `ast.NodeVisitor` (`_QueuePathAstVisitor`) that walks
the parsed tree for `ast.Constant` string nodes equal to `"queue"` or
embedding `"queue/"`/`"/queue"`, reached via ORDINARY tree traversal
regardless of the surrounding structure (`BinOp` Div, `Call` args to any
method name, `JoinedStr` f-string segments, etc.). This closes the
whack-a-mole problem structurally: the visitor does not need to enumerate
every join API, because it inspects the underlying string constant directly,
wherever it appears in the expression tree.

Two side benefits fell out of the rewrite:

* `#` comments are never part of the parsed tree, so the guard no longer
  needs a separate `tokenize`-based comment-stripping pass — only a
  `visit_Expr` override to skip standalone string-literal statements
  (docstrings / comment-style bare strings) is needed.
* The exemption for the guard's own literal building blocks (the resolver's
  definition and its `_is_queue_like_string` helper, which necessarily
  contains the literal `"queue"`) is still done by function-name lookup via
  AST (`_function_definition_line_range`), unchanged in spirit from the
  regex-era exemption mechanism — a guard checking for "this specific
  literal/pattern used elsewhere" must always exempt its own definition, AST
  or not.

## Generalizable Lesson

When writing a "no hardcoded X outside the shared resolver" regression
guard, prefer walking the parsed AST for the underlying literal value over
scanning raw text for the literal's known textual shapes. A regex-based
guard is verifiably incomplete as soon as a second review pass finds a new
equivalent construction it misses; an AST-based guard keyed on the
underlying constant value is robust to the join API and line-wrapping
choices used to combine it, and to `#` comments without any extra
machinery.

## Verification

Sanity-checked the new visitor against a throwaway sample reproducing the
exact `backlog_root.joinpath("queue", "019-DL.md")` shape (arguments split
across lines) that the widened regex still missed; confirmed detection.
Full `tests/test_scope_containment_*.py` suite remained green (100 passed,
337 subtests) across all three review-fix iterations, and the canonical CI
gate (`PYTHONPATH=src python -m unittest discover -s tests`) reproduced only
pre-existing, already-deferred failures unrelated to this change.
