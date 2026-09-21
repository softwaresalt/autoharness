---
title: "Foundation: Ship pre-task harness-generation lifecycle"
description: "Installs the Ship pre-task harness-generation LIFECYCLE that invokes the actor policy P-004 already names. This unit owns the LIFECYCLE ONLY: a read-only harness-surface resolver with a typed result, a safe deterministic CLI, and the Ship template and installed-mirror wiring that consumes it across both harness generation and crash recovery. It does NOT author, install, re-render or repair the harness-architect actor; that actor is already installed and P-004 conformant through external Ship commits."
doc_type: plan
source: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
date: 2026-09-18
plan_id: ship-harness-lifecycle-foundation
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_role: active
revision: 10
revision_scope: full-rewrite-current-state-addressing-attempt-08-findings
revision_10_note: "Revision 10 is a REWRITE as a current-state contract, not a correction log and not an appended errata section. Chronology lives in the review manifest and the immutable attempt artifacts; this document states only what is true now. THREE STRUCTURAL CHANGES. (1) The prerequisite release unit 191-S / 185-F that revision 9 created is RETIRED, never claimed and never executed: its premise - an install-time variable precedence defect - was false, its deliverable was satisfied directly by Ship commits 1cb0dc81 and b8ac632a, and attempt-08 finding S26 held it structurally unexecutable. The 187-S -> 191-S edge is withdrawn and 187-S is restored as an explicit dag-root with an empty dependency set. (2) The resolver is specified as a complete executable boundary: a public module, a typed result with an exact JSON schema, a single classification rule used everywhere, separated trust roots, fail-closed containment with no-follow identity validation, a registered CLI owned by a named task, and recomputation wired into both the P-004 gate path and the crash-recovery surface. (3) Every live carrier is pointer-only for mutable review state. S14 is CLOSED by external evidence. S13 and S15-S34 are ADDRESSED AND REMAIN OPEN pending independent attempt 09."
verdict: null
verdict_is_pass: false
verdict_revision: null
verdict_asserted_against_revision: null
disposition: PENDING-INDEPENDENT-REVIEW
publication_eligible: false
publication_eligible_basis: "No independent review has judged revision 10. Attempt 08 returned FAIL against revision 9."
historical_verdict_is_not_carried_forward: true
last_independent_verdict: FAIL
last_independent_verdict_attempt: 8
last_independent_verdict_revision: 9
verdict_note: "NO VERDICT IS ASSERTED AGAINST REVISION 10. The verdict manifest at review_manifest is the SOLE AUTHORITY for review state; this field is a pointer, not a second record. Revision 10 remediates S13 and S15-S34 but CLOSES NOTHING: findings are closed by an independent attempt that verifies the closure, never by the authoring agent. S14 alone is closed, and was closed at attempt 08 on external evidence."
awaiting_attempt: 9
awaiting_attempt_against_revision: 10
latest_attempt: 8
latest_attempt_reviewed_revision: 9
review_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 7
source_stash_ids:
  - 76EBDE6D
source_stash_note: "This unit is SINGLE-SOURCE. The governing decision's portfolio table assigns 76EBDE6D to row 'P4 | 187-S | 181-F | foundation', and every live carrier cites it. 76EBDE6D is an archived stash entry - 'P-021 RELIABILITY FOLLOW-UP: P-004 red-phase precondition is unsatisfiable on this workspace' - which is this unit's genuine origin. The value 3EF5AAF2 that appeared before revision 4 was a mis-citation belonging to 177-S / 169-F, not a second source."
feature_id: 181-F
shipment_id: 187-S
unit_role: lifecycle-only
unit_scope_note: "This unit owns the LIFECYCLE ONLY. It does not author, install, re-render or repair the harness-architect actor."
depends_on_shipments: []
dag_root: true
dag_root_restored_at_revision: 10
dag_root_note: "187-S declares an EMPTY dependency set and carries the dag-root label so pre_claim derives declared_root rather than blocking as UNSEQUENCED_SHIPMENT. The revision-9 edge on 191-S is withdrawn because 191-S is RETIRED, never claimed and never executed. Root status is a GRAPH FACT and confers NO claim authority: ordinary pre-claim, this unit's own P-002/P-004 harness generation, independent review, CI and closure all still apply."
removed_depends_on_shipments:
  - 184-S
  - 188-S
  - 191-S
actor_installed_in_baseline: true
actor_behaviorally_conformant: true
actor_structural_installation_commit: 07b4be79263252b1820701fd123d0aed85c1db2a
actor_behavioral_conformance_commits:
  - 1cb0dc8140a809d63c3193d58431cd14408788b7
  - b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3
actor_conformance_note: "STRUCTURAL INSTALLATION AND BEHAVIOURAL CONFORMANCE ARE DISTINCT AND ARE KEPT DISTINCT. 07b4be79 placed .github/skills/harness-architect/SKILL.md on disk and registered it in .autoharness/harness-manifest.yaml at checksum parity; it is recorded as STRUCTURAL INSTALLATION ONLY and is never cited as P-004 conformance evidence. Conformance rests on 1cb0dc81 - which replaced the installed pytest invocation with the canonical command, mirrored it into the authoritative template with placeholders preserved, required per-test expected-marker correlation, added the contract test and refreshed the manifest checksum - and b8ac632a, which seeded the manifest variable the render requires. Evidence: canonical suite 2358 passed / 0 failed / 54 skipped, manifest parity holding."
actor_artifact: .github/skills/harness-architect/SKILL.md
retired_prerequisite_shipment: 191-S
retired_prerequisite_feature: 185-F
retired_prerequisite_note: "RETIRED, NEVER CLAIMED, NEVER EXECUTED, NEVER SHIPPED. Nothing in this plan may be read as claiming 191-S shipped."
bootstrap_precursor_plan: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
bootstrap_precursor_status: RETIRED-SUPERSEDED-COMPLETED-EXTERNALLY
resolver_module: src/autoharness/harness_surfaces.py
resolver_entry_point: "resolve_harness_surfaces(*, workspace_root: Path, autoharness_home: Path, shipment_id: str) -> HarnessResolution"
resolver_cli: "autoharness harness resolve --workspace . --autoharness-home <resolved-or-default> --shipment <id> --json"
resolver_persists_state: false
resolver_owner_task: 181.002-T
freshness_carrier: recomputation
parity_criteria_vocabulary: PAR-1..PAR-6b
gates: []
requires_plan_hardening: true
hardening_rationale: "Modifies the Ship agent lifecycle itself - every future shipment traverses the phase this unit installs - and adds a new public Python module, a new CLI subcommand and a new manifest-tracked activation. Blast radius spans the Ship template, its installed mirror, the harness manifest and the crash-recovery surface."
tags:
  - foundation
  - ship-lifecycle
  - harness-architect
  - p-004
---

# Foundation: Ship pre-task harness-generation lifecycle

## Problem frame — current state

P-004 requires that, before Ship executes a task, a harness exists and is
observed RED. The policy names an actor that performs that generation. Until
recently that actor was a template that had never been installed, so the
requirement was unsatisfiable on this workspace — the origin recorded in stash
`76EBDE6D`.

**That gap is closed, and it was closed outside this unit.** The
`harness-architect` actor is installed at
`.github/skills/harness-architect/SKILL.md`, manifest-registered at checksum
parity, and **behaviourally conformant with P-004**. See
`actor_structural_installation_commit` and
`actor_behavioral_conformance_commits` in this document's frontmatter for the
exact commits and the distinction this plan preserves between the two
properties.

**What remains missing is the lifecycle that calls it.** Ship has no phase that
decides *whether* a task needs a harness, *which* surface supplies it, or
*whether that surface is usable right now* — and no machine-checkable answer it
can hand to P-004. Today that question is answered by agent prose. This unit
replaces the prose with an executable boundary.

### What this unit owns

| Owns | Does not own |
|---|---|
| A read-only harness-surface resolver, as a public Python module with a typed result | The harness-architect actor's content, installation or conformance |
| A safe deterministic CLI over that resolver | The P-004 gate implementation itself (a separate, withheld unit) |
| Ship template and installed-mirror wiring, in harness generation **and** crash recovery | Any operation registry, result model or transport (`184-S` scope) |
| The manifest refresh that accompanies the activation | Any MCP surface |

### What is no longer authorized here

* **No bootstrap exception, in any form.** No carve-out, no grant, no
  `--force`, no force-audit entry, no expiring authority, no
  self-authorization. `PRE-0` is withdrawn as an execution path and is not
  re-described or re-scoped.
* **No claim that a retired unit executed.** `188-S` / `182-F` and
  `191-S` / `185-F` are archived, were never claimed and never executed.
* **No prerequisite release unit.** Revision 9 created one and it is retired;
  `187-S` is a root again.

### Historical material — non-authoritative

The bootstrap split, the staged `harness-ready` admission apparatus and the
revision-9 prerequisite-unit design are **historical and non-authoritative**.
They are not restated here. They are reachable through
`bootstrap_precursor_plan`, through decision `D9`, and through the immutable
review-history artifacts. Nothing in those documents authorizes an action in
this plan.

## What P-004 already requires

### The canonical commands, quoted exactly

Compilation:

```
python -m py_compile src/autoharness/cli.py
```

Test execution:

```
PYTHONPATH=src python -m unittest discover -s tests
```

These are quoted verbatim from the installed policy. This unit does not change
them, does not paraphrase them and does not substitute an ecosystem runner for
them.

## The resolver, stated as an executable boundary

### Module and entry point

Public module `src/autoharness/harness_surfaces.py`. Sole public entry point,
keyword-only:

```python
def resolve_harness_surfaces(
    *,
    workspace_root: Path,
    autoharness_home: Path,
    shipment_id: str,
) -> HarnessResolution: ...
```

Public types:

```python
class HarnessState(str, Enum):
    HARNESS_READY = "HARNESS_READY"
    NO_HARNESS = "NO_HARNESS"
    UNRESOLVED = "UNRESOLVED"

class SurfaceStatus(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    STALE = "STALE"
    INVALID = "INVALID"

@dataclass(frozen=True)
class SurfaceResolution:
    surface_id: str
    status: SurfaceStatus
    reason_code: str
    installed_path: str | None      # root-relative, redacted
    template_path: str | None       # root-relative, redacted
    manifest_checksum: str | None
    installed_digest: str | None
    rendered_digest: str | None

@dataclass(frozen=True)
class HarnessResolution:
    schema_version: int
    state: HarnessState
    reason_code: str
    shipment_id: str
    surfaces: tuple[SurfaceResolution, ...]
    declaring_tasks: tuple[str, ...]
    inputs_sha256: str | None
    errors: tuple[str, ...]
```

**The resolver is READ-ONLY.** It writes no file, creates no directory, sets no
environment variable, spawns no process and mutates no backlog record. It is
safe to call repeatedly and safe to call during crash recovery.

### Canonical shipment and task source

The backlog root is resolved with the **existing** helper
`resolve_backlog_root` from `src/autoharness/backlog_root.py`. The resolver
does not re-implement root discovery and does not accept a backlog path
argument.

* The shipment record for `shipment_id` supplies its membership through
  `custom_fields.items`, which is **authoritative**. No other membership source
  is consulted.
* For each member ID, **exactly one** record must exist across the live queue
  and the archive, combined. **Zero records, more than one record, or a record
  whose front matter does not parse is `UNRESOLVED`.**
* The same one-record rule applies to the shipment record itself.

### Declaration grammar

Harness requirements are declared **only** on task records, as labels:

* Either **one or more unique** labels matching `harness-surface:<id>`,
* **or exactly one** label `harness-surface:none`,
* **never both**, and **never** a duplicate `<id>` within one task.

`<id>` matches `^[a-z0-9]+(-[a-z0-9]+)*$`. Any label violating this grammar
makes the resolution `UNRESOLVED`. A task carrying **no** `harness-surface:`
label at all is `UNRESOLVED` — absence is not consent.

Tasks `181.001-T` … `181.005-T` carry `harness-surface:harness-architect`.

### Surface mapping and manifest match — one classification rule

For a declared `<id>`:

1. The installed path is **deterministically** `.github/skills/<id>/SKILL.md`,
   relative to the canonical `workspace_root`. No search, no glob, no
   fallback.
2. The manifest `.autoharness/harness-manifest.yaml` must contain **exactly
   one** entry under `artifacts:` whose `path` equals that exact path **and**
   whose `template` equals the exact string `skills/<id>/SKILL.md.tmpl`.

| Condition | State | Exit |
|---|---|---|
| Zero manifest entries match | `UNRESOLVED` | 2 |
| More than one manifest entry matches | `UNRESOLVED` | 2 |
| Entry matches on `path` but not on `template`, or vice versa | `UNRESOLVED` | 2 |
| Exactly one entry matches, but the installed file is absent | `NO_HARNESS` | 1 |
| Exactly one entry matches, but the template is absent | `NO_HARNESS` | 1 |
| Exactly one entry matches, both files present, parity holds | `PRESENT` → `HARNESS_READY` | 0 |
| Exactly one entry matches, both files present, parity fails | `NO_HARNESS` (`STALE`) | 1 |

**This table is the single classification rule.** It is not restated with
different wording anywhere else in this plan, in any carrier, or in the Ship
phase text.

### Rendering and canonical bytes

* Placeholders rendered are **uppercase only** — `{{NAME}}` where `NAME`
  matches `^[A-Z][A-Z0-9_]*$` — and their values come **solely** from the
  matched manifest entry's `variables_used`.
* A placeholder present in the template with **no** value in `variables_used`
  makes the resolution `UNRESOLVED`. Lowercase or mixed-case brace sequences
  are left untouched and are not treated as placeholders.
* **Canonical bytes:** decode as UTF-8, then translate `CRLF` → `LF` and any
  remaining lone `CR` → `LF`. Nothing else is normalized — no trailing-space
  stripping, no final-newline insertion, no Unicode normalization. A decode
  failure is `UNRESOLVED`.
* **`PRESENT` requires both:** the rendered canonical bytes equal the installed
  canonical bytes, **and** the manifest `checksum` equals the SHA-256 of the
  installed canonical bytes. Either alone is `STALE`.

### Trust roots — separated

| Input | Canonical root |
|---|---|
| Backlog records, `.autoharness/harness-manifest.yaml`, installed `.github/skills/**` | `workspace_root` |
| Templates `skills/<id>/SKILL.md.tmpl` | `autoharness_home` |

The two roots are canonicalized independently and **never substituted for one
another**. A path resolved under the wrong root is `UNRESOLVED`, even if a file
happens to exist there.

### Containment — fail closed, before any read

1. **Lexical rejection first**, on the declared `<id>` and every derived
   relative path, before touching the filesystem: reject absolute paths, drive
   letters, UNC prefixes, environment-variable syntax, `~` home expansion, and
   any `..` component.
2. **Canonical containment**: resolve the candidate and its intended root, then
   require that the candidate is the root or a descendant of it **by path
   component**, never by string prefix — `/ws-evil` is not inside `/ws`.
3. **No-follow**: no component at or below either canonical root may be a
   symlink, junction or other reparse point. A reparse component is
   `UNRESOLVED`.
4. **One handle, verified**: each file is read through a **single opened
   handle**. Identity and size metadata are captured before and after the read
   and must match. Any mismatch, any unreadable or non-regular file, and any
   indeterminate result is `UNRESOLVED`, and **no read outside a canonical root
   is ever performed.**

### The CLI

```
autoharness harness resolve --workspace . --autoharness-home <resolved-or-default> --shipment <id> --json
```

| Exit | Meaning |
|---|---|
| `0` | `HARNESS_READY` |
| `1` | `NO_HARNESS` — adjudicated absence |
| `2` | `UNRESOLVED` — invalid, unsafe, ambiguous or raced input |

The CLI is **deterministic and side-effect free**. `--autoharness-home`
defaults to the installation home the CLI already resolves. `--json` emits the
result document described below on stdout; diagnostics go to stderr. This unit
adds **no** MCP surface and registers **no** operation in any operation
framework — that substrate is `184-S` scope.

### Result document and digests

The `--json` document is exactly the `HarnessResolution` dataclass, serialized
with:

* `schema_version: 1`;
* enum values as their stable string names;
* `surfaces` ordered by `surface_id` ascending, and `declaring_tasks` ordered by
  task ID ascending — **stable, not insertion-ordered**;
* every path emitted **root-relative and redacted**; no absolute path, no user
  directory and no machine name appears in output;
* `reason_code` drawn from a closed, documented set, one code per row of the
  classification table plus one per containment failure mode.

`inputs_sha256` binds, in canonical JSON with domain separation between fields:
the shipment record bytes, the canonical JSON of the derived declaration set,
the manifest bytes, and the digest of **each** template and **each** installed
file consulted. It is emitted on **every** outcome — `HARNESS_READY`,
`NO_HARNESS` and `UNRESOLVED` alike — whenever the inputs it binds were
readable; where an input could not be read, the field is `null` and the reason
is recorded in `errors`.

### Freshness is recomputation, not storage

**No readiness state is ever persisted.** There is no cache file, no gate token
file and no backlog field recording readiness.

* Ship and human callers invoke the **CLI** freshly at the moment they need an
  answer.
* The future P-004 gate calls the **Python function directly** and emits the
  returned `inputs_sha256` into its own evidence.
* **Crash recovery**: after the operator selects a checkpoint and Stage or Ship
  restores it, the resolver is re-invoked **before** the task cursor and phase
  execution are restored. A stored token, digest or `inputs_sha256` carried in a
  checkpoint is **evidence of what was once observed and never an
  authorization**; it is compared, never trusted.
* A second read that disagrees with the first is a race and yields
  `UNRESOLVED`.

### Both non-ready states halt, and they stay distinct

`NO_HARNESS` and `UNRESOLVED` **both** halt before task partition. They are not
merged: they carry different states, different exit codes and different reason
codes, because "this surface is adjudicated absent" and "I could not safely
determine anything" require different operator responses.

## The ACTIVATE contract

`181.005-T` performs a single atomic activation across **exactly three files**,
refreshing **exactly one** manifest entry:

| File | Change |
|---|---|
| `templates/agents/ship.md.tmpl` | Add the pre-task harness-generation phase **and** the crash-recovery recomputation rule |
| `.github/agents/ship.md` | The identical change, rendered |
| `.autoharness/harness-manifest.yaml` | Refresh the **one** entry for the installed Ship agent |

This is decision `D11` applied: the manifest is a **member of the commit and of
the rollback unit**, and checksum parity is verified against the on-disk file
after the refresh. Templates are not manifest-tracked, so the
template-and-mirror pair refreshes **one** entry, not two.

### Parity criteria — `PAR-1` … `PAR-6b`

| ID | Criterion |
|---|---|
| `PAR-1` | The mirror section's heading text and heading level match the template's exactly |
| `PAR-2` | The section appears at the same ordinal position within its parent section |
| `PAR-3` | Every non-placeholder line is byte-identical after canonicalization |
| `PAR-4` | Every `{{UPPERCASE}}` placeholder in the template has a rendered value in the mirror |
| `PAR-5` | No placeholder syntax survives in the mirror |
| `PAR-6a` | The manifest entry's `checksum` equals the SHA-256 of the mirror's canonical bytes |
| `PAR-6b` | The manifest entry's `template` names the authoritative template the mirror was rendered from |

These names replace the earlier `P4`-prefixed criterion labels, which collided
with the unit alias `P4` used in the governing decision. **Immutable
review-history artifacts, policy IDs and finding severity IDs are not renamed.**

## Rollback

Rollback is a `git revert` of the single ACTIVATE commit, restoring the
template, the mirror and the manifest entry together.

**It requires FRESH, LIVE operator approval, obtained immediately before the
revert command is issued, and bound to the exact activation commit SHA.** The
approval must name that SHA. It is re-validated in the moment the command is
about to run; an approval obtained earlier in the session, or for a different
SHA, is not an approval. If the operator is unreachable, dark or AFK, the agent
**halts and reports** — it does not revert. Proceeding without that approval is
a P-005 violation. There is no unconditional revert path anywhere in this unit.

## Tasks

| ID | Role | Files | Size | Complexity |
|---|---|---|---|---|
| `181.001-T` | RED | `tests/test_harness_surfaces.py`, `tests/test_harness_resolve_cli.py` | M | high |
| `181.002-T` | PREPARE | `src/autoharness/harness_surfaces.py`, `src/autoharness/cli.py` | L | high |
| `181.003-T` | PREPARE | `tests/fixtures/harness_surfaces/` | S | medium |
| `181.004-T` | VERIFY | evidence only | S | medium |
| `181.005-T` | ACTIVATE | `templates/agents/ship.md.tmpl`, `.github/agents/ship.md`, `.autoharness/harness-manifest.yaml` | M | high |

**`181.001-T` (RED)** owns the failing tests for the resolver, the CLI, the
containment rules, the race detection and the JSON document. The tests must be
**import-safe assertion failures** — the module and CLI entry point must be
importable and the failures must be assertion failures about behaviour, **not**
`ImportError` or `ModuleNotFoundError`. A RED phase that fails at import proves
nothing about the contract.

Targeted RED command:

```
PYTHONPATH=src python -m unittest tests.test_harness_surfaces tests.test_harness_resolve_cli
```

**`181.002-T` (PREPARE)** owns **both** `src/autoharness/harness_surfaces.py`
and the `cli.py` routing for `autoharness harness resolve`, including exit-code
mapping. There is **no unnamed follow-on task** for the CLI: the surface this
plan activates is owned, in this plan, by this task. Two files is the bound.

**`181.003-T` (PREPARE)** owns fixtures. The fixtures contain the **literal**
CLI invocation string and its exit-code handling, and the checkpoint-resume
recomputation rule, so both are exercised rather than described.

**`181.004-T` (VERIFY)** produces evidence covering **every row** of the
classification table and **every** containment failure mode. Commands:

```
PYTHONPATH=src python -m unittest tests.test_harness_surfaces tests.test_harness_resolve_cli
PYTHONPATH=src python -m unittest discover -s tests
python -m py_compile src/autoharness/cli.py
```

**`181.005-T` (ACTIVATE)** performs the three-file, one-manifest-entry
activation above, updating **both** the harness-generation and the
crash-recovery sections of the Ship template and its installed mirror, and
carries the full fresh-live SHA-bound approval text before any revert.

## Out of scope

The harness-architect actor's content; the P-004 gate implementation; any
operation registry, result model or transport; any MCP surface; any change to
the canonical commands; any change to P-002, P-004, gate semantics, grants,
`--force` or waivers.

## Risks

| Risk | Mitigation |
|---|---|
| The resolver becomes a second source of truth about readiness | It persists nothing; recomputation is the only freshness carrier |
| Path checks pass but the file read races | One handle, pre/post identity and size validation, second-read disagreement → `UNRESOLVED` |
| `NO_HARNESS` is silently treated as ready | Distinct state, distinct exit code, distinct reason code; both non-ready states halt before partition |
| The activation leaves the manifest stale | `D11`: the manifest is a member of the commit and the rollback unit, with parity verified after refresh |
| Rollback destroys working state without consent | Fresh, live, SHA-bound approval revalidated immediately before the command; halt if unreachable |

## Hardening review

### Adversarial questions

* *Can a task declare a surface outside the workspace?* No — lexical rejection
  precedes any filesystem access, and canonical containment is component-wise.
* *Can a symlink redirect a read below a canonical root?* No — reparse
  components below either root are `UNRESOLVED`.
* *Can a caller supply a readiness answer?* No — the resolver derives
  everything from the shipment record, task labels, the manifest and the two
  file trees. There is no caller-supplied declaration.
* *Can a checkpoint authorize execution after a crash?* No — the stored digest
  is compared, never trusted, and the resolver runs before the task cursor is
  restored.
* *Can this unit's own tasks bootstrap themselves?* Yes — the actor is already
  installed and conformant in this publication branch, so `187-S`'s own
  P-002/P-004 harness generation has a real producer. That is precisely why
  `191-S` had no subject and why this shipment is a genuine root.

### Blast radius

The Ship agent template and its installed mirror; the harness manifest; one new
public Python module; one new CLI subcommand. Every future shipment traverses
the installed phase, so a defect here is systemic — which is why the activation
is one reviewed atomic commit with a verified manifest refresh and an
approval-gated rollback.

### Verification floor

Targeted RED and GREEN on the two new test modules; the full canonical suite;
the canonical compile command; and evidence covering every classification-table
row and every containment failure mode.
