---
title: "Markdownlint enforcement contract: what is release-blocking for v1.5.0 and what is a separate contract surface"
date: 2026-08-29
doc_type: decision
stash_id: D1A46B8C
agent: "Stage (planning only - Ship executes)"
classification: "bug / quality-gate enforcement"
blast_radius: "medium (CI composition + hook semantics + shipped install/tune contract) - deliberately reduced to zero for v1.5.0"
route: "claude-opus-5 / anthropic / high"
---

# Deliberation - markdownlint enforcement contract (`D1A46B8C`)

Date: 2026-08-29
Agent: Stage (planning only - Ship executes)
Stash source: `D1A46B8C` (high, bug, P-021 C2 `DEFERRED SCOPE EXPANSION`)
Source refs: PR #409; Copilot review thread finding [1]; addendum thread
`PRRT_kwDORzpWpM6cToXP`; follows `.markdownlint.json` install in commit `b109bbc8`
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Decision (one line)

**Split three ways.** The **enforcement redesign** (CI markdownlint job +
fail-closed pre-push hook + mechanism standardization) is **NOT release-blocking
and is deferred** to a post-v1.5.0 shipment. The **shipped install/tune contract
is already coherent** and requires no change — the pre-commit script templates
exist and ship. The v1.5.0 release instead adopts a **narrow, procedural,
fail-closed markdown gate** executed once as a release-prep verification step.

## Problem statement

`D1A46B8C` asserts three coupled defects:

1. markdownlint is not enforced in CI, so a contributor without
   `markdownlint-cli` can merge Markdown violating MD001/MD025/MD041.
2. `.githooks/pre-push.sh` **fails open** when the binary is absent.
3. An addendum: registering `.markdownlint.json` as a manifest artifact
   activated two previously-inert validation clauses in `install-harness`
   SKILL.md step 5c and `tune-harness` SKILL.md "Markdownlint config drift"
   step 3, both of which require `scripts/pre-commit-markdownlint.sh` **and**
   `scripts/pre-commit-markdownlint.ps1` — reported absent.

The release question is narrow: **which of these, if any, must be fixed before
publishing v1.5.0?**

## Research findings (verified this session, not taken on assertion)

**Claim 1 — CONFIRMED.** `.github/workflows/` contains exactly `ci.yml` and
`release.yml`. The only `markdownlint` occurrence in either is a *comment* at
`ci.yml:23`. There is no markdownlint job. CI enforcement is genuinely absent.

**Claim 2 — CONFIRMED.** `.githooks/pre-push.sh` L29–L38:

```sh
if command -v markdownlint >/dev/null 2>&1; then
  ...
else
  echo "WARNING: markdownlint not found — skipping Markdown lint gate." >&2
```

The hook skips with a warning and does not set `FAILED=1`. Fail-open confirmed.

**Claim 3 — CONFIRMED LOCALLY, BUT REFUTED AS A SHIPPED DEFECT.** This is the
decisive finding and it inverts the entry's implied severity.

* `scripts/pre-commit-markdownlint.sh` and `.ps1` are indeed **absent from this
  repository's own `scripts/` directory**.
* **However**, `templates/scripts/pre-commit-markdownlint.sh.tmpl` and
  `templates/scripts/pre-commit-markdownlint.ps1.tmpl` **both exist and both
  ship.** `pyproject.toml` force-includes `templates` →
  `src/autoharness/data/templates` in the wheel.

Therefore a **fresh install of v1.5.0 into a target workspace renders both
scripts and satisfies the install/tune contract**. The shipped product is
internally coherent. The failure the addendum predicts ("a fresh install would
report FAIL") does **not** occur for users; it occurs only in *this* repository,
which historically enforces markdownlint through `.githooks/pre-push.sh` and
never rendered the two templates into its own `scripts/`.

This is **dogfood-workspace drift, not a product defect.**

**Blast-radius boundary.** The wheel is `packages = ["src/autoharness"]` plus
**ten** `force-include` mappings (`pyproject.toml` L35–L45): `templates`,
`schemas`, `.github/agents`, `.github/skills`, `.github/instructions`,
`.github/prompts`, `.github/copilot-instructions.md`,
`.github/copilot-review-instructions.md`, `docs`, and `AGENTS.md`. **None of
those ten mappings covers `.github/workflows/`, `.githooks/`, or `scripts/`** —
note in particular that the `.github` inclusions are specific subdirectories and
two named files, not `.github` wholesale. Those three paths are therefore not in
the wheel, and no part of claims 1–3 reaches the published artifact. (The
conclusion is unchanged from the original analysis; the stated reason is
corrected here — the earlier "templates force-include only" phrasing understated
the package boundary and must not be reused as evidence.)

## Options evaluated

### Option A: Full fail-closed enforcement before v1.5.0

Add a CI markdownlint job, flip the hook to fail-closed, and render the
pre-commit script pair into `scripts/`.

*Pro*: closes the gap permanently; P-008 becomes genuinely enforced.
*Con*: changes **CI composition** and **hook semantics for every contributor**
— exactly the two surfaces P-021 C1 declares out of scope for this entry. Adding
`scripts/pre-commit-markdownlint.*` alongside the existing pre-push mechanism
introduces a **second, duplicate enforcement mechanism**, which the entry itself
flags as the wrong move absent a standardization decision. Large, contested, and
unrelated to publishing a package.

### Option B: Narrow procedural gate for v1.5.0; defer the redesign (SELECTED)

Treat the release's markdown obligation as a **one-time verification**, not a
permanent mechanism change: during release prep, run `markdownlint` explicitly
over the repository and require **zero violations**; if the binary is absent,
the release **halts** rather than skipping.

*Pro*: makes the release's own markdown gate genuinely fail-closed without
touching CI composition or hook control flow. Zero blast radius on contributors.
Respects P-021 C1. Unblocks v1.5.0 immediately.
*Con*: does not fix the systemic gap — deliberately, since that is a separate
contract surface with its own deliberation.

### Option C: Defer entirely, no markdown gate for the release

*Pro*: smallest possible scope.
*Con*: the release plan explicitly requires a markdown quality gate, and the
v1.5.0 changelog adds a large hand-authored Markdown section — precisely the
content most likely to introduce MD001/MD025/MD041 violations. Leaving it
unverified is an unforced risk. **Rejected.**

### Option D: Render the pre-commit script pair into `scripts/` only

*Pro*: silences the install/tune self-check FAIL in this workspace.
*Con*: creates the duplicate second mechanism the entry warns against, and
resolves by accident a standardization question that deserves an explicit
decision. **Rejected** — it would prejudge the deferred deliberation.

## Trade-off comparison

| Option | Release risk closed | Blast radius | P-021 C1 compliant | v1.5.0 fit |
|---|---|---|---|---|
| A | Yes | High (CI + all contributors) | No | Poor |
| B | Yes (for this release) | None | Yes | **Best** |
| C | No | None | Yes | Poor |
| D | No | Medium (duplicate mechanism) | No | Poor |

## Decision

Adopt **Option B**.

The **narrow release-blocking contract** for v1.5.0 is exactly this: *the
release branch's Markdown must be verified clean by an actual markdownlint run,
and the absence of the linter is a stop condition, not a skip.* Nothing about
CI composition, hook control flow, or the pre-commit/pre-push mechanism choice
is in scope for v1.5.0.

The enforcement redesign (Option A's substance) is **deferred** and remains
tracked by `D1A46B8C`, which stays **ACTIVE** in the stash with this
deliberation linked. It is a genuine, high-value follow-up — just not a release
blocker.

## Rejected alternatives

Options A, C, and D above, for the recorded reasons.

## Unresolved questions (deferred, explicitly not decided here)

1. Should CI install `markdownlint-cli` itself or rely on a preinstalled image?
2. Should the harness standardize on pre-commit scripts, the pre-push hook, or
   accept either as an equivalent enforcement surface?
3. Should `install-harness`/`tune-harness` accept a pre-push hook as satisfying
   the markdownlint enforcement clause, rather than requiring the script pair?
4. Should this repository render the shipped pre-commit templates into its own
   `scripts/` to end the dogfood drift, and if so, does the pre-push hook's
   markdownlint block get removed to avoid duplication?

These four questions are the deferred deliberation's agenda.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Markdown violations land in the curated v1.5.0 changelog | The procedural gate runs *after* the changelog is authored, over the whole repo |
| markdownlint binary unavailable on the release machine | Gate is fail-closed: halt and report, never skip (this is the direct inverse of the `pre-push.sh` fail-open defect) |
| Deferring the redesign lets the gap persist | `D1A46B8C` stays ACTIVE with this artifact linked; the four open questions are recorded above |

## Traceability

* Stash: `D1A46B8C` (remains ACTIVE — deferred, not consumed)
* Disposition: **NON-BLOCKER for v1.5.0**; narrow procedural gate adopted instead
* Consumed into: release-prep plan task for the markdown quality gate
