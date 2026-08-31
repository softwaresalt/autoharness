---
title: "SHIP-5 — Fail-closed harness verification gates"
date: 2026-08-31
slug: fail-closed-harness-gates
doc_type: plan
source_stash: "D1A46B8C, 5CBA0A85, 11BCE865"
source_decision: "docs/decisions/2026-08-31-dark-factory-staging-triage-and-shipment-portfolio.md"
shipment_unit: "SHIP-5"
route: "claude-opus-5 / anthropic / high"
status: reviewed
requires_plan_hardening: "yes"
plan_review_verdict: "PASS"
---

# SHIP-5 — Fail-closed harness verification gates

## Problem

Three gates that report success when they have not actually checked anything.
Governing law, inherited from `029-DL`: **a convention survives iff a machine
produces it or penalizes its absence.** All three of these penalize nothing.

### D1A46B8C — markdownlint is installed but not enforced

`.markdownlint.json` exists and P-008 is therefore *enforceable*, but:

* `.githooks/pre-push.sh` L29 guards the lint behind
  `if command -v markdownlint >/dev/null 2>&1;` and L36-L37 emit
  `WARNING: markdownlint not found — skipping Markdown lint gate.` and exit
  successfully. **The gate is absent on every machine that has not installed
  `markdownlint-cli`.**
* There is no markdownlint job in CI at all, so the hook is the only carrier and
  it fails open.

Source ref: PR #409 review; deferred under P-021 C1 because changing hook control
flow alters hook *semantics* for every contributor and adding a CI job changes CI
*composition* — both different contract surfaces from "install the missing config
file".

### 5CBA0A85 — no fail-closed agent→skill dangling-reference check

This is the residual open question carried out of `8AC574F1` ("13 skills
referenced by installed pipeline agents are not installed"), which Stage archived
on 2026-08-29 as SATISFIED. The installation half is genuinely done —
`.github/skills/` now installs 18 skills and all 13 previously-missing pipeline
skills are verified present. But the closing question was not satisfied by that
installation: **nothing prevents the regression from recurring.** The gap was
found by inspection, not by a gate.

### 11BCE865 — silent frontmatter truncation is undetectable

Ten `docs/` files carry silently truncated frontmatter values. The failure mode
is distinct from, and nastier than, a decode failure: an unquoted YAML scalar
containing **space-hash** triggers YAML's comment rule, so the value is silently
cut at the `#` and the document still parses. `tests/test_docs_frontmatter_decodes.py`
asserts the frontmatter *decodes* — which it does — so the guard cannot see this
class at all. None of the ten were introduced by the P-020 compaction that found
them.

## Direction

Make each gate penalize absence:

1. Add a markdownlint CI job that runs on every PR, and change the pre-push hook
   from skip-on-missing to **fail**-on-missing.
2. Add a fail-closed cross-reference check to `verify-harness` that resolves
   every skill named by an installed agent and fails when one is not installed.
3. Repair the ten truncated values and extend the frontmatter guard to detect
   truncation, not merely decode failure.

## Hardening (P-006)

Triggered: changes CI composition and hook semantics for every contributor.

* **H1 (binding).** The pre-push hook's fail-on-missing message must name the
  exact install command (`npm install -g markdownlint-cli`) and an explicit,
  documented escape hatch (`git push --no-verify`), so the change is a *gate*,
  not a wall. A contributor who cannot install the linter must still be able to
  push deliberately and visibly.
* **H2 (binding).** The CI job must land **before or with** the hook change. If
  the hook starts failing while CI still has no markdownlint job, the only
  enforcement lives on developer machines — strictly worse than today for anyone
  who cannot install it.
* **H3 (binding).** The CI job must lint the **same glob with the same config**
  as the hook (`**/*.md` with `.markdownlint.json`). Two gates with different
  scopes produce green-locally/red-in-CI, which trains contributors to ignore the
  local gate.
* **H4 (binding).** The new `verify-harness` check must be *additive and
  fail-closed for the check itself*: if the agent set or skill set cannot be
  enumerated, the check must fail rather than pass vacuously. A cross-reference
  check that silently finds zero references is the same bug it exists to catch.
* **H5.** Repairing the ten truncated values is a **content-preserving** edit:
  quote the scalar so the full value survives. Do not rewrite or shorten the
  values, and do not touch files outside the enumerated ten.
* **H6 (binding) — the hook change drags its generators and its policy with it.**
  Cycle 0 named only `.githooks/pre-push.sh`. That is the *dogfood instance*. The
  surfaces that **generate** and **govern** warn-and-skip were omitted, so a fix
  applied only to the checked-in hook would be silently regenerated away on the
  next install. Verified:
  * `templates/scripts/pre-push-quality-gates.sh.tmpl:13-14` and
    `templates/scripts/pre-push-quality-gates.ps1.tmpl:12-13` state as a design
    rule: *"If a gate's tool is not installed on this machine, the gate is SKIPPED
    with a warning (tool-not-found -> warn+skip), never a hard failure."* The
    generic probe helper (`.sh.tmpl:70-71`, `.ps1.tmpl:73-74`) implements it.
  * `.github/skills/install-harness/SKILL.md:163` instructs the installer to
    resolve each gate's probe as the tool *"whose **absence should skip** the gate
    (warn-and-skip, P-019)"*. **There is no `templates/skills/install-harness/`** —
    this skill is global-only, so `.github/skills/install-harness/SKILL.md` is the
    single authoritative surface, not a dogfood mirror. Recorded so the paired-edit
    contract is not applied where no pair exists.
  * **P-019 itself is the governing conflict** and is the reason this cannot be a
    hook-only edit. `templates/policies/workflow-policies.md.tmpl:628` (mirror
    `.github/policies/workflow-policies.md`) states: *"A gate whose tool is not
    installed is **skipped with a warning**, never treated as a failure, so a
    partial toolchain never wedges a contributor's push."* Its Postcondition
    repeats it. Shipping a fail-on-missing hook without amending P-019 puts the
    harness in direct violation of its own published policy.
* **H7 (binding) — P-019 is amended narrowly, by carve-out, not by reversal.**
  The general warn-and-skip rule is **correct** and stays: a partial toolchain must
  not wedge a push. The amendment adds one bounded exception — a gate may be
  declared **required**, and a required gate's absent tool is a failure carrying
  the named install command and the `--no-verify` escape (**H1**). `markdownlint`
  is the first and only gate declared required by this shipment. A blanket
  reversal of P-019 is forbidden.
* **H8 (binding) — render tests, not just file edits.** Because the generators are
  now in scope, the acceptance is on **rendered output**: render both
  `pre-push-quality-gates.{sh,ps1}.tmpl` and assert (i) a required gate with an
  absent tool exits non-zero, (ii) a non-required gate with an absent tool still
  warns and skips (**H7** preserved), and (iii) no unresolved `{{...}}` remains in
  either render. Editing the checked-in `.githooks/` copy without this is the
  drift the whole shipment exists to remove.
* **H9 (binding) — safety mode.** Every task enters `careful`. The task carrying
  the P-019 amendment additionally enters `freeze-scope` bounded to the P-019
  section, since the policy governs every contributor's push.
* **H10 (binding) — pack-awareness de-risking for the `verify-harness` check.**
  See §Decision P below. This is a **blocking prerequisite**, not advice.

## Decision P — pack-awareness is a precondition of the cross-reference check (binding)

`5CBA0A85` cannot be implemented as "every skill an agent names must exist in
`.github/skills/`". Measured directly in this workspace, **15 skills exist as
templates and are correctly not installed**, because they belong to capability
packs this composition did not select:

```text
brainstorm, browser-automation, build-feature, compound, compound-refresh,
doc-review, evolve, harness-architect, harness-doctor, iterative-experiment,
learn, observe, safety-modes, security-audit, skill-search
```

and **4 skills are installed with no template at all** (`install-harness`,
`tune-harness`, `verify-harness`, `workspace-discovery` — global skills). A naive
check would emit false positives on the first set the moment any agent references
`observe`, `learn`, `evolve`, or `safety-modes`, and a check that is loud and
wrong is disabled within a week. That would convert `5CBA0A85`'s fail-closed gate
into net-negative noise.

* **P1 — resolution is three-valued, not two-valued.** Every agent→skill edge
  resolves to exactly one of: **INSTALLED** (present in `.github/skills/`, pass);
  **PACK-GATED** (absent, but attributable to a capability pack this composition
  did not select, pass **with the pack named in the report**); or **DANGLING**
  (absent and not attributable, **fail**). Only DANGLING fails.
* **P2 — attribution must come from a declared source, never a hardcoded
  allowlist.** The check derives pack membership from the capability-pack
  declarations the workspace already carries (workspace profile / capability-pack
  enforcement instruction / pack manifests). A literal list of 15 skill names
  baked into a test is forbidden: it is the maintenance trap SHIP-4's
  finding 3 identified, and it silently rots as packs change.
* **P3 — unattributable absence fails; this is where H4 bites.** If a skill is
  absent **and** no declared pack claims it, the result is DANGLING and the check
  fails. If the pack declarations themselves cannot be enumerated, the check
  **fails** (it does not degrade to two-valued), per **H4**.
* **P4 — resolution is a hard prerequisite, not a runtime guess.** The
  pack-attribution source must be identified and demonstrated to classify all 15
  measured template-only skills as PACK-GATED, and to classify a deliberately
  broken reference as DANGLING, **before** the check is written. This is the
  de-risking step **H10** requires for the `high`-complexity task.
* **P5 — acceptance criteria (mandatory, on the check task).**
  1. A fixture referencing each of the 15 measured pack-gated skills produces
     **zero** failures and reports each as PACK-GATED with its pack named.
  2. A fixture referencing a skill that is absent and unattributable produces
     **exactly one** failure, naming the referencing file and line.
  3. A fixture where `.github/skills/` is absent or empty **fails** (**H4**).
  4. A fixture where pack declarations cannot be enumerated **fails** (**P3**).
  5. Each of the 4 installed-without-template global skills resolves INSTALLED.

## Tasks

| # | Title | Size | Complexity | Surface |
|---|---|---|---|---|
| 1 | Add a fail-closed markdownlint CI job and make required-gate tools fail the pre-push hook when missing | M | medium | `.github/workflows/`, `.githooks/pre-push.sh` |
| 1b | Propagate required-gate fail-on-missing into the pre-push **generators**, amend P-019 by carve-out, correct the install-harness probe guidance, and add render tests | M | medium | `templates/scripts/pre-push-quality-gates.{sh,ps1}.tmpl`, `templates/policies/workflow-policies.md.tmpl` + `.github/policies/` mirror, `.github/skills/install-harness/SKILL.md`, `tests/` |
| 2a | **De-risking prerequisite (H10/P4)**: identify and validate the capability-pack attribution source for skill resolution | S | low | `docs/` (recorded findings only; no production edits) |
| 2b | Add the pack-aware three-valued fail-closed agent→skill cross-reference check to `verify-harness` | M | medium | `src/autoharness/`, `tests/` |
| 3a | Extend the docs frontmatter guard to detect silent space-hash truncation | S | medium | `tests/test_docs_frontmatter_decodes.py` |
| 3b | Repair truncated frontmatter — batch 1 of 2 (5 files) | S | low | `docs/**` |
| 3c | Repair truncated frontmatter — batch 2 of 2 (5 files) | S | low | `docs/**` |

**Task 1 / 1b split (H6).** Task 1 keeps the CI job and the checked-in hook
together to honour **H2**/**H3**. Task 1b carries the generator, policy, and
guidance surfaces **H6** added, plus the **H8** render tests. 1b is sequenced
immediately after 1 and **must land in the same shipment**: a repository whose
hook fails-on-missing while P-019 still forbids exactly that is a self-violating
harness. Splitting rather than bundling keeps each inside the 2-hour rule now that
six surfaces are in play.

**Task 2a / 2b split (H10, P4, two-axis gate).** Cycle 0's task 2 was `M`/`high`,
tripping the complexity axis with no split and no de-risking step. The `high`
complexity was concentrated entirely in the unanswered pack-attribution question
(**Decision P**). 2a answers it and produces the evidence; 2b then implements
against a known answer at `M`/`medium`. 2a **blocks** 2b.

**Task 3a / 3b / 3c split (width).** Cycle 0's task 3 repaired ten documents *and*
extended a test guard in one task — two different widths and two different review
lenses in one unit. Now: 3a ships the guard alone (**red before green**: the guard
must be observed failing against the unrepaired corpus); 3b and 3c then repair the
ten files in two bounded batches of five, each verified green by 3a's guard.
Sequenced 3a → 3b → 3c. Each obeys the width constraint — one concern per task.

## Non-goals

* No new markdownlint rules and no change to `.markdownlint.json`. If the
  repository does not currently lint clean under the existing config, driving the
  count to zero is in scope only for files this shipment already touches;
  anything broader is a P-021 capture.
* No general cross-reference framework. Task 2b checks exactly one edge type:
  installed agent → named skill. Path, anchor and `file:line` citation resolution
  belongs to portfolio unit **S4** (D-PROV, `PROV-04`), which already owns it.
* No change to which skills are installed. **Decision P** makes the check aware of
  pack-gated absence; it never installs a skill to satisfy itself.
* **No blanket reversal of P-019.** The amendment is a bounded required-gate
  carve-out (**H7**).
* **No new required gate beyond `markdownlint`.** The carve-out mechanism is
  general; this shipment declares exactly one gate required.
* **No hardcoded skill allowlist** (**P2**).

## Deferred scope (P-021, captured not silently broadened)

| Ref | Capture | Residual risk if never built |
|---|---|---|
| DSE-S5-1 | If **task 2a** finds that no declared, machine-readable pack-attribution source exists in this workspace, then *creating* one is a new product capability and is **out of scope**. 2a records the finding and 2b is re-scoped by the operator rather than inventing a source. | **Medium, and explicitly gated.** Without an attribution source the check cannot be built as specified. This is why 2a is a **blocking** prerequisite: the shipment discovers this before writing code, not after. **P2** forbids the tempting shortcut (a hardcoded list), so the failure mode is a recorded halt, not a rotting allowlist. |
| DSE-S5-2 | Extending the resolver to agent→**instruction** edges (SHIP-4's DSE-S4-1 is the same class from the other side). | **Medium.** Two rendered subagents keep citing absent instruction files. 2b establishes the three-valued resolver shape that a later run extends. |
| DSE-S5-3 | Driving the repository-wide markdownlint violation count to zero. Task 1's ordered acceptance scopes CI to changed files while the count is non-zero. | **Low.** Enforcement is real on changed files from day one; the repository-wide sweep is deferred until the count is measured and reduced. Recorded rather than assumed, per cycle-0 finding 1. |

## Verification

`PYTHONPATH=src python -m unittest discover -s tests`; `verify-harness`;
`markdownlint "**/*.md"` locally and in CI; a deliberate negative test for each
gate (uninstall/mask the linter → hook must fail; remove a skill → verify-harness
must fail; introduce a space-hash scalar → frontmatter guard must fail).

## Plan review — multi-persona adversarial gate

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 1 | Correctness | **P0** | Turning markdownlint fail-closed in CI **before** the repository lints clean would make `main` permanently red and block every PR in this run's own portfolio. | **Resolved.** Task 1's acceptance is ordered: (a) run the linter over the current tree and record the violation count; (b) if non-zero, the job lands scoped to **changed files** on PRs, with a repository-wide run added only once the count reaches zero. The count must be measured, not assumed. This is recorded as a hard precondition, not a suggestion. |
| 2 | Correctness | **P1** | Hook fail-on-missing plus no escape hatch would hard-block any contributor without Node.js. | **Resolved** as binding **H1**: named install command plus documented `--no-verify` escape. |
| 3 | Architecture | **P1** | A `verify-harness` check that enumerates skills by scanning `.github/skills/` will pass vacuously in a workspace where the directory is absent. | **Resolved** as binding **H4**: inability to enumerate either side is a **failure**, not a skip. Task 2's acceptance includes a negative test for the empty/absent-directory case. |
| 4 | Maintainability | **P1** | Task 2 must parse agent markdown to find skill references; a naive regex will produce false positives on prose that merely mentions a skill name. | **Resolved.** Task 2's acceptance restricts detection to **structured invocation references** (the documented `invoke the X skill` / explicit `.github/skills/<name>` path forms) and requires the check to report the exact file and line of each unresolved reference, so a false positive is immediately diagnosable rather than mysterious. |
| 5 | Template integrity | P2 | Repairing docs frontmatter could alter values that downstream tooling reads. | **H5**: quote-only, content-preserving. Task 3's acceptance asserts the decoded value after repair equals the *intended* full value, and that the file still decodes. |
| 6 | Scope | P2 | Task 3 could expand into a repository-wide frontmatter audit. | Bounded to the ten enumerated files plus the guard extension. Any eleventh file the extended guard reveals is a P-021 capture. |
| 7 | Security | P3 | A CI job that runs `npm install -g` pulls a third-party toolchain into the pipeline. | Pin the `markdownlint-cli` version and use the existing Node setup action already present in the workflow ecosystem; no unpinned global installs. Recorded as an acceptance criterion on task 1. |
| 8 | Constitution | P3 | Changing hook semantics affects every contributor without their consent. | Principle-conformant: the change adds a gate with a documented escape and is announced by the failure message itself. **H1**. |

**Verdict: PASS.** 1 P0 and 3 P1 raised; all four resolved before harvest. Zero
unresolved P0/P1. Two review-fix cycles of three.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

`TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass.`
Every selected persona was covered inline against the Persona Rubric Adapter and normalized to
the P0–P3 scale; no persona was skipped. Declared, not silent.

**Plan hardening (P-006): required — `yes`. Satisfied.** **H1**–**H10** and
**Decision P** (**P1**–**P5**) are binding and each is propagated into a task
acceptance criterion.

### Persona coverage

| Persona | Mode | Findings |
|---|---|---|
| Correctness | inline persona pass | 1 P0 + 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Architecture | inline persona pass | 1 P1 (cycle 0) |
| Maintainability | inline persona pass | 1 P1 (cycle 0), 1 P1 (cycle 1) |
| Template integrity | inline persona pass | 1 P2 (cycle 0), 1 P1 (cycle 1) |
| Scope boundary | inline persona pass | 1 P2 (cycle 0) |
| Security | inline persona pass | 1 P3 (cycle 0) |
| Constitution | inline persona pass | 1 P3 (cycle 0), 1 P1 (cycle 1) |
| Schema/CLI/docs coupling | inline persona pass | 1 P1 (cycle 1) |

### Review-fix cycle 1 — findings on the revised plan

| # | Persona | Sev | Finding | Resolution |
|---|---|---|---|---|
| 9 | Template integrity | **P1** | The plan changed only the checked-in `.githooks/pre-push.sh`, leaving the two `templates/scripts/pre-push-quality-gates.*.tmpl` generators asserting warn-and-skip as a design rule. The next install would silently regenerate the fail-open behaviour. | **Resolved by H6/H8.** Both generators are in scope as task 1b, with render tests asserting required-gate failure, non-required-gate skip preservation, and no unresolved `{{...}}`. |
| 10 | Schema/CLI/docs coupling | **P1** | **P-019 explicitly mandates** that an absent gate tool is *"skipped with a warning, never treated as a failure"* (`workflow-policies.md.tmpl:628` + mirror), and `.github/skills/install-harness/SKILL.md:163` instructs the installer accordingly. Shipping a fail-on-missing hook would put the harness in violation of its own published policy. | **Resolved by H7.** P-019 gains a bounded **required-gate carve-out** rather than a reversal; the install-harness probe guidance is corrected in the same task (1b). Recorded that install-harness is global-only with **no** template pair, so no phantom paired edit is attempted. |
| 11 | Correctness | **P1** | Task 2's `5CBA0A85` check would false-positive on 15 measured template-only skills (`observe`, `learn`, `evolve`, `safety-modes`, and 11 others) that are *correctly* absent because their capability packs were not selected. A noisy check gets disabled. | **Resolved by Decision P.** Resolution is three-valued (INSTALLED / PACK-GATED / DANGLING); only DANGLING fails. Attribution comes from declared pack sources, never a hardcoded list (**P2**); unattributable absence and un-enumerable declarations both fail (**P3**). **P5** fixes the acceptance fixtures. |
| 12 | Maintainability | **P1** | Task 2 was `M`/`high` (two-axis gate) and task 3 repaired ten documents plus a test guard in one unit (width). | **Resolved.** 2a/2b split with 2a as a blocking de-risking prerequisite (**H10**/**P4**); 3a/3b/3c split separating the guard from two bounded five-file repair batches. Every resulting task is `S`/`M` with `low`/`medium` complexity. |
| 13 | Constitution | **P1** | No safety mode declared on a shipment that changes push semantics for every contributor and amends a published policy. | **Resolved by H9**: `careful` on all tasks; `freeze-scope` on the P-019 section for task 1b. |

**Verdict: PASS.** Cycle 1: 5 P1 raised, all 5 resolved. Cumulative: **zero
unresolved P0/P1**. Two review-fix cycles of three consumed.
