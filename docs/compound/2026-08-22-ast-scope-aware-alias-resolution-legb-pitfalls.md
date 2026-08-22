---
problem_type: ast_visitor_scope_modeling_gap
category: testing
root_cause: A scope-aware AST alias-resolution visitor that reuses the same push/pop enclosing-scope logic for class bodies as for function bodies, and that visits a def's header (decorators/defaults/annotations) inside the def's own newly-pushed body scope instead of the enclosing scope, produces false negatives on the exact bypass patterns it was built to catch.
tags: [testing, ast, regression-guard, scoping, p-021, review-fix, copilot-review]
shipment: 152-S
task: 144.004-T
date: 2026-08-22
source: docs/compound/2026-08-22-ast-scope-aware-alias-resolution-legb-pitfalls.md
doc_type: learning
title: "AST Scope-Aware Alias Resolution: Three LEGB Pitfalls Found Across Three Copilot Review Rounds"
---

# AST Scope-Aware Alias Resolution: Three LEGB Pitfalls Found Across Three Copilot Review Rounds

## Problem

144.004-T's `_EnvMutationVisitor` (`tests/test_test_suite_isolation_contract.py`)
is an AST-based structural guard forbidding `patch.dict(os.environ, ...)` /
`os.environ.clear()` anywhere under `tests/`, resolving import aliases so the
guard cannot be trivially bypassed by renaming an import. Getting scope-aware
alias resolution *actually correct* to Python's real LEGB (Local, Enclosing,
Global, Built-in) name-resolution rules took **three** rounds of Copilot
review on PR #398, each catching a distinct, real false-negative bug in the
previous round's own fix:

1. **Round 1** (flat map): the original design tracked import aliases in a
   single flat whole-module `dict[str, str]`. An unrelated, *later*,
   function-local `import other as p` would silently overwrite an earlier,
   valid module-level `p` alias in that same flat map, corrupting resolution
   for call sites that had nothing to do with the later import.
   **Fix**: rewrote as a single-pass, scope-aware visitor with a *stack* of
   per-scope alias dicts, merged outermost-to-innermost so inner bindings
   correctly shadow outer ones — genuine LEGB.

2. **Round 2** (class bodies are not enclosing scopes): the round-1 fix
   pushed/popped a new scope for `ClassDef` exactly like `FunctionDef`,
   which incorrectly made a class-body-level import alias (e.g. `import
   json as p` written directly in a `TestCase` class body) visible when
   resolving names *inside that class's own methods*. Real Python does not
   work this way: **a class body is never an enclosing (LEGB) scope for its
   own nested methods or nested classes** — a method resolves free names via
   the module scope or an enclosing *function* scope, never via its
   immediately enclosing class's own namespace (confirmed empirically:
   `class A: x=1; class B: y=x` raises `NameError` in `B`, but `def outer():
   x=1; class C: y=x` correctly resolves — only *function* scopes chain as
   closures, class scopes never do, not even to a nested class).
   **Fix**: `visit_ClassDef` now visits decorators/bases/keywords in the
   *enclosing* scope, then pushes a class-only scope for direct class-body
   statements, but temporarily *pops* that class scope while visiting any
   nested `FunctionDef`/`AsyncFunctionDef`/`ClassDef` **body**.

3. **Round 3** (decorators/headers evaluate in the enclosing scope, not the
   decorated def's own body scope): the round-2 fix still visited a
   function's `decorator_list` via `generic_visit` **inside** the function's
   own freshly-pushed scope — and because `ast.FunctionDef._fields` orders
   `body` *before* `decorator_list`, a later import inside the function's
   own body could silently overwrite an alias the function's *own decorator*
   depended on, before the decorator was even visited. The complementary bug:
   popping the class scope for the **entire** nested def (decorators
   included, per the round-2 fix) hid class-body-level aliases from a
   nested *method's own decorator* — even though a method's decorator
   genuinely **is** evaluated as part of executing its enclosing class's own
   body (class bodies execute top-to-bottom exactly like function bodies; a
   name bound earlier in the same class body is visible to a later
   statement in it, decorators included).
   **Fix**: decorators, parameter defaults, and return/parameter
   annotations are now visited in the **current** (enclosing) scope, before
   pushing anything; only the def's own runtime **body** is pushed as a new
   scope, via a shared `_visit_def_body_scoped()` helper that additionally
   pops an immediately-enclosing *class* scope (if any) for that body only,
   restoring it afterward for subsequent sibling statements.

A fourth round surfaced one more real (but lower-severity) gap — accepted as
documented residual risk rather than fixed, see Disposition below.

## Root Cause

Modeling Python's real LEGB scope-resolution rules inside a visitor requires
getting several *asymmetries* right simultaneously, and each round above
fixed exactly one of them while still getting another wrong:

* Scopes must be a **stack**, not a flat map (round 1) — but a stack alone
  is not sufficient if...
* **Class scopes and function scopes are not interchangeable.** Function
  scopes chain as real closures across arbitrarily many nesting levels;
  class scopes chain to **nothing** — not to methods, not to nested classes,
  not even one level deep (round 2) — but even a stack that treats classes
  specially is not sufficient if...
* **A def's header (decorators, defaults, annotations, bases, keywords)
  evaluates at *definition time*, in the scope enclosing the def — never
  inside the def's own new scope**, regardless of whether that def is a
  function or a class (round 3). Getting the *body* scope right (round 2)
  is a distinct concern from getting the *header* scope right (round 3);
  fixing one does not imply the other is also fixed.

Each of these is independently a source of false negatives in a bypass-
resistance guard: a false negative means the exact offending pattern the
guard exists to catch — `patch.dict(os.environ, ...)` under an alias — can
slip through undetected, which is a correctness failure of the guard itself,
not merely of the code it protects.

## Fix Pattern (final, verified-correct design)

* Maintain `self._scopes: list[dict[str, str]]` (a stack) and merge outermost
  to innermost for resolution at any given point (`_current_alias_map`).
* `visit_Import`/`visit_ImportFrom` always bind into `self._scopes[-1]`
  (the currently active scope, whatever kind it is) — this part needed no
  change across any of the three rounds.
* For **both** `FunctionDef`/`AsyncFunctionDef` and `ClassDef`: visit the
  header (decorators, `args`/`returns` for defs; bases/keywords for classes)
  in the **current** scope, *before* pushing anything.
* Delegate the def's own **body** to one shared `_visit_def_body_scoped(body,
  kind)` helper: if the scope currently on top of the stack is class-tagged,
  temporarily pop it (bodies never inherit an immediately-enclosing class
  scope); push a fresh scope of `kind` (`"function"` or `"class"`); visit the
  body statements; pop the fresh scope; restore the popped class scope (if
  any) for subsequent sibling statements.
* Because `ClassDef` dispatch already pops-and-restores its own class scope
  around any nested def, **at most one class scope is ever live on the stack
  at a time** — so checking only the immediate top-of-stack kind is
  sufficient; there is no need to walk further down the stack hunting for an
  ancestor class scope. This is what lets the fix generalize correctly
  through arbitrary function-in-function (closures preserved), class-in-
  class (isolation preserved, verified empirically to raise `NameError` the
  same way real Python does), and mixed nesting, with one small shared
  helper instead of special-casing every combination.

## Disposition of the Round-4 Finding (accepted residual risk, not fixed)

A fourth Copilot review round found that alias tracking, while now correctly
LEGB-scope-aware, is still **control-flow-insensitive**: both branches of an
`if`/`else` (or `try`/`except`) are visited sequentially into the same
mutable scope dict, so the *last-visited* branch's binding for a name
silently overwrites an earlier branch's binding. In principle, a conditional
import that binds a name to `patch` in one branch and something unrelated in
another could let a genuine `patch.dict(os.environ, ...)` bypass the guard
undetected, if the non-offending branch happens to be visited last in AST
order.

This finding was correctly classified as P-021 C1 **in-scope** (same
contract surface as the guard's own established bypass-resistance goal), but
the PR had already exhausted its 3-cycle review-fix budget (Stop Conditions
table), and severity was assessed as **P2**: no file under `tests/` today
uses conditional/branch-dependent import aliasing anywhere near an
`os.environ` mutation call, so this is a hardening opportunity against a
hypothetical future adversarial pattern, not a live/active defect, and the
guard remains fully sound for every currently-existing offending shape. The
operator explicitly accepted this as documented residual risk (recorded in
PR #398's Local Review Readiness block, thread `PRRT_kwDORzpWpM6bb2je`)
rather than authorizing a 4th fix cycle. A recommended follow-up: make the
tracker control-flow-conservative — treat a name as ambiguously bound (and
resolve it to its most permissive/forbidden candidate origin) whenever more
than one reachable branch could bind it differently.

## Generalizable Lesson

When writing a scope-aware AST alias/name-resolution visitor (for any
purpose — a structural regression guard, a linter, a refactoring tool),
verify against Python's *actual* LEGB semantics empirically, not by
analogy to function nesting:

1. Is the scope a stack (supports shadowing) or a flat map (supports
   shadowing only accidentally, wrongly)?
2. Does the visitor correctly distinguish **class scopes** (visible only to
   the class's own direct body statements and to the *headers* of things
   nested one level within it — never to bodies, never transitively to
   nested classes) from **function scopes** (real closures, chain through
   arbitrary nesting)?
3. Does the visitor visit a def's **header** (decorators, defaults,
   annotations, bases, keywords — everything that evaluates at *definition
   time*) in the scope *enclosing* the def, and only the def's own **body**
   in a freshly pushed scope?

All three are independently necessary; each was found in a separate review
round on this PR precisely because fixing one does not imply the others are
also correct. When in doubt, write a tiny standalone Python snippet and run
it to confirm what real CPython actually resolves, rather than reasoning
from first principles about scoping — `class A: x=1; class B: y=x` failing
with `NameError`, while `def outer(): x=1; class C: y=x` succeeding, is the
kind of asymmetry that is easy to get backwards without empirical
verification.

## Verification

Each of the three fixed rounds added at least one non-vacuity regression
test reproducing the reviewer's exact scenario, verified (before committing)
to **fail** against the pre-fix visitor and **pass** against the fixed one
— not merely added and left unverified. The canonical Windows full suite
was re-run after every round (`python -m unittest discover -s tests`,
`PYTHONPATH=src`), reaching 1830 tests / failures=0 / errors=0 / skipped=20
by the final round, with Linux CI parity independently confirmed via this
PR's own CI run at each HEAD.
