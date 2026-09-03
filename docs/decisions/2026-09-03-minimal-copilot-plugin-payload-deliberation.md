---
title: "Minimal Copilot plugin installation payload"
date: 2026-09-03
slug: minimal-copilot-plugin-payload
doc_type: deliberation
source_stash: "E9E5E6CC"
superseded_stash_ids: "AB387F16 (temporary ID, resolved during stash-file merge; no duplicate entry created)"
route: "claude-opus-5 / anthropic / high"
status: decided
---

# Minimal Copilot plugin installation payload

## Problem

Installing the autoharness Copilot CLI plugin delivers **the entire development
repository** to the consumer, when the plugin needs a small subset. The Python
wheel over-includes independently and differently: it already excludes
`.backlogit/`, `tests/`, `experiments/` and `references/`, but force-includes all
642 `docs/` files and omits two members of the runtime set
(`.github/policies/**` and the skill-referenced `scripts/` subset).

*(Precision added in plan review-fix cycle 5, finding 2. The whole-repository claim
is true of the **plugin** channel, whose `source: "."` is literally the repository
root; it was never true of the wheel, whose `force-include` table has always been
an explicit allowlist. Stating it of both channels would have misclassified the
wheel's baseline-true exclusion tests as red-first work.)*

Stash `E9E5E6CC` (high, feature) asks for: the minimum runtime file set, packaged
and installed as only that set, while preserving install, update, verification,
and cross-environment behavior.

## Evidence

All figures below are measured from tracked files on
`chore/stage-159-167-publication` (commit `05f7f699`), not estimated.

### Channel A — Copilot CLI plugin

`.github/plugin/marketplace.json` declares:

```json
"plugins": [{ "name": "autoharness", "version": "1.5.0", "source": "." }]
```

`source: "."` is the **repository root**. `plugin.json` declares only two agents
and one skills directory, but the marketplace source makes the entire repo the
delivered payload.

Tracked repository content, by top-level directory:

| Directory | Files | Size | Needed by plugin? |
|---|---:|---:|---|
| `docs` | 642 | 6,964 KB | Only `docs/<root>` (21 files, 291 KB) |
| `.backlogit` | 2,110 | 4,907 KB | **No** — workspace backlog state |
| `tests` | 109 | 1,963 KB | **No** |
| `templates` | 140 | 1,217 KB | **Yes** — the product |
| `src` | 54 | 1,011 KB | Python CLI channel only |
| `.github` | 66 | 984 KB | Mostly yes |
| `schemas` | 21 | 454 KB | **Yes** |
| `experiments` | 46 | 277 KB | **No** |
| `scripts` | 8 | 67 KB | Subset (referenced by skills) |
| **Total tracked** | **3,238** | **~18 MB** | |

`docs/` is 642 files but only 21 of them are user-facing guides. The remaining
621 files (6.7 MB) are development history: `archive` (188), `memory` (105),
`compound` (83), `plans` (80), `decisions` (51), `closure` (39), `reviews` (27),
`spikes` (16), plus smaller sets.

`.backlogit/` alone is **2,110 files — 65% of every tracked file in the repo** —
and is this workspace's own backlog records. It has no runtime role in a consumer
install and is the single largest correctness *and* disclosure concern in the
payload.

### Channel B — Python wheel

`pyproject.toml` `[tool.hatch.build.targets.wheel.force-include]` is an **explicit
allowlist**, not a whole-repository sweep. It maps exactly: `templates`, `schemas`,
`.github/agents`, `.github/skills`, `.github/instructions`, `.github/prompts`, both
`copilot-*instructions.md` files, `docs`, and `AGENTS.md`. Two consequences follow
directly from that list, and both matter to the plan's test classification:

1. **`.backlogit/`, `tests/`, `experiments/` and `references/` are already absent
   from the wheel.** The plugin channel's largest disclosure is not a wheel
   problem. Tests asserting these exclusions are *characterization* of existing
   correct behaviour.
2. **`.github/policies/**` and the skill-referenced `scripts/` subset are already
   missing**, so the wheel does **not** currently satisfy the runtime set the plan
   requires. A test asserting the complete runtime set is *red* on the baseline.

The over-inclusion defect is `docs`:

```toml
"docs" = "src/autoharness/data/docs"
```

This force-includes **all 642 docs files / 6.9 MB** into every wheel.

**Runtime necessity was tested, not assumed.** Every `docs/*` path in
`src/autoharness/verify_workspace.py` resolves against `workspace_path` — the
*target workspace* — not the packaged data directory:

* `verify_workspace.py:1949` — `compound_dir = workspace_path / ... "docs/compound"`
* `verify_workspace.py:1976` — `workspace_path / ... "docs/closure"`
* `verify_workspace.py:2892-2912` — `docs_root` derived from workspace config

`cli.py:14-21` sets `_DATA_DIR = _PACKAGE_DIR / "data"` with an editable-install
fallback to the repo root; `_home()` returns it for **templates and schemas**.
No code path reads packaged `docs/`. The force-include is dead weight.

### The docs/ reference false positive

Cross-referencing `.github/skills/**` and `.github/agents/**` shows 23 references
to `docs/compound`, 17 to `docs/plans`, 14 to `docs/memory`, 13 to
`docs/decisions`, 10 to `docs/closure`.

These are **output destinations in the target workspace**, not engine payload.
The `deliberate`/`impl-plan`/`harvest` skills *write* to `docs/plans` in the
consumer's workspace; `learnings-researcher` *reads* the consumer's
`docs/compound`. Shipping autoharness's own `docs/compound` to a consumer would
inject this repository's private development history into their workspace —
which is precisely the anti-goal the stash names ("target workspaces receive only
generated output, not autoharness engine files").

This distinction is the crux of the decision and must be enforced by test, because
a naive dependency scan reads these references as required payload.

### Test coverage

A scan of `tests/` for `packag|plugin|dist|wheel|install` returns **zero matches**.
There is no regression guard on payload composition in either channel. Any fix
that does not add one will silently regress on the next directory added.

## Options considered

**Option 1 — Denylist (exclude `.backlogit`, `tests`, `experiments`).**
Cheapest. Rejected: fails open. A new development directory is delivered by
default; the payload silently re-bloats. This is exactly how the current state
arose.

**Option 2 — Explicit allowlist manifest, single source of truth, both channels.**
A declarative payload manifest enumerates what ships; everything else is excluded
by default. Fails closed. Requires a manifest, wiring into both `pyproject.toml`
and the plugin source, and a test that asserts composition.

**Option 3 — Split the repository (separate distribution repo).**
Maximum payload purity. Rejected: high blast radius, breaks `source: "."` and the
git-clone install path, splits history, and imposes a permanent two-repo sync
burden. Fails the operator's *simplicity supersedes complexity* rule.

**Option 4 — Prune the wheel only, leave the plugin channel alone.**
Rejected: leaves the 2,110-file `.backlogit` disclosure in the plugin payload,
which is the largest single problem.

## Decision

**Adopt Option 2 — an explicit, allowlist-based payload manifest as the single
source of truth for the two in-scope distribution channels — the **Copilot CLI
plugin** and the **Python wheel** — enforced by an automated composition test.**

> **Scope history and current boundary (restored in plan review-fix cycle 5,
> finding 1).** This decision was originally framed over **two** channels, and
> that is again its current scope. Plan review-fix cycle 2 (finding 3) amended it
> to three by absorbing the **sdist**, which review had just discovered was
> untrimmed; cycle 5 **withdraws that amendment** and de-scopes the sdist under
> **P-021 C1**.
>
> The discrimination is on mechanism, not on convenience. The source request
> `E9E5E6CC` is the **Copilot plugin installer payload**. The **wheel** is
> genuinely coupled to it: both are governed by an explicit allowlist
> (`force-include` / `source`), both were measured in this deliberation, both share
> the `_DATA_DIR` → `templates/`/`schemas/` resolution contract, and both carry the
> same `docs/` over-inclusion defect. The **sdist** shares none of that — it is a
> different build target driven by hatchling's *default sweep* rather than by any
> allowlist, producing a different artifact, with a different fragility (its only
> declared key is the `core-metadata-version` pin). It was **discovered during plan
> review**, not deliberated here, and absorbing a review discovery into a
> deliberated scope is precisely what C1 prohibits.
>
> The sdist problem is **real, unfixed, and recorded** — deferred stash entry
> **`99818C6D`** (kind `bug`, priority **high**) carries the full evidence: the
> undeclared target, the `uv build` → `dist/*` publish path that ships it to PyPI
> and attaches it to the GitHub release, the 2,110-file `.backlogit/` disclosure,
> the six retired test cases, and the retired `160.019-T` task tombstone. Nothing
> is discarded; it is moved from executable scope into a capture that must be
> triaged on its own merits.
>
> The *Options considered* section above and the *Channel A* / *Channel B* evidence
> sections are the original two-channel framing and are again **currently
> accurate** rather than merely historical.

Rationale against the operator's prioritization rules:

* *Simplicity supersedes complexity* — one declarative manifest replaces two
  divergent implicit inclusion rules (`source: "."` and the wheel's
  `force-include` table).
* *Composability and interoperability supersede feature delivery* — this is a
  packaging refactor that makes install/update/verify behave consistently across
  the pip, clone, and plugin channels.
* *Reliability and security supersede feature work* — removing `.backlogit`
  (2,110 files of workspace records) from a published payload is a disclosure and
  correctness fix, not a feature.
* *Fail closed* — allowlist over denylist, consistent with existing harness policy.

### Minimum viable payload boundary

**Include (engine runtime):**

* `plugin.json`, `.github/plugin/marketplace.json`
* `.github/agents/**`, `.github/skills/**`, `.github/instructions/**`,
  `.github/prompts/**`, `.github/policies/**`
* `.github/copilot-instructions.md`, `.github/copilot-review-instructions.md`
* `templates/**`, `schemas/**`
* `scripts/**` subset referenced by skills (`deploy-harness.*`,
  `acquire_lock.*`, `release_lock.*`, `ci-topology-check.sh`)
* `AGENTS.md`, `README.md`, `LICENSE`, `CHANGELOG.md`
* `docs/<root>` user guides only (21 files)
* `src/autoharness/**` — wheel channel only

**Exclude (development-only):**

* `.backlogit/**`, `tests/**`, `experiments/**`, `references/**`
* `docs/` history subdirectories: `archive`, `plans`, `memory`, `decisions`,
  `closure`, `compound`, `reviews`, `spikes`, `audits`, `exec-plans`,
  `telemetry`, `design-docs`, `research`, `deferred`, `product-specs`
* `.githooks/**`, `.vscode/**`, `.claude/**`, `.engram/**`, `.graphtor/**`,
  `.autoharness/**`, `uv.lock`, `pyproject.toml` (plugin channel)

Projected: **3,238 → ~350 files** and **~18 MB → ~3 MB** (≈89% fewer files,
≈83% smaller). Exact post-change numbers are to be recorded by the composition
test, not asserted in advance.

## Risks

* **R1 — Under-inclusion breaks install.** A file dropped from the allowlist
  fails at consumer install, not in CI. Mitigation: end-to-end install +
  `verify-workspace` from the built artifact, not from the source tree.
* **R2 — `docs/` reference false positive.** Excluding `docs/compound` etc. could
  be misread as breaking skills. Mitigation: an explicit test asserting these
  resolve to target-workspace paths.
* **R3 — Update-path compatibility.** v1.5.0 consumers upgrading to a trimmed
  payload must not be left with orphaned engine files. Mitigation: explicit
  upgrade-from-1.5.0 test.
* **R4 — `_DATA_DIR` clone fallback.** `cli.py` falls back to repo root; a trimmed
  clone must still resolve `templates/` and `schemas/`. Both are retained.
* **R5 — Manifest drift.** The manifest can rot. Mitigation: the composition test
  fails closed on any tracked path that is neither allowlisted nor explicitly
  excluded.

## Sequencing

This work is a packaging refactor with reliability and disclosure dimensions. It
does **not** supersede the reviewed reliability/security portfolio `159-S`–`166-S`,
which corrects live v1.5.0 contract and fail-closed defects. It **does** supersede
`167-S`, which is backlog/docs record hygiene ("feature work supersedes
documentation-only work").

Deterministic placement: **between `166-S` and `167-S`.**

Final sequence:
`159-S → 160-S → 161-S → 162-S → 163-S → 164-S → 165-S → 166-S → 168-S → 167-S`

## Traceability

* Source stash: `E9E5E6CC` (supersedes temporary `AB387F16`)
* Branch: `chore/stage-159-167-publication` @ `05f7f699`
* Follow-on plan: `docs/plans/2026-09-03-minimal-copilot-plugin-payload-plan.md`
* **Deferred out of this decision's scope:** `99818C6D` — trim the Python sdist
  payload (kind `bug`, priority **high**). Discovered during plan review of the
  follow-on plan, de-scoped under **P-021 C1** in review-fix cycle 5, and carrying
  the full discovery evidence. The sdist remains untrimmed and disclosing until
  that entry is triaged and built; this decision neither fixes nor regresses it.
