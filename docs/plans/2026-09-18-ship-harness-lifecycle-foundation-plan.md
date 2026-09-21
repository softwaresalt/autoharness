---
title: "Foundation: Ship pre-task harness-generation lifecycle"
description: "Installs the Ship pre-task harness-generation LIFECYCLE that invokes the actor policy P-004 already names. This unit owns the LIFECYCLE ONLY: a handle-bound secure-read primitive, a read-only harness-surface resolver with a typed result and an exact JSON schema, a deterministic CLI over that resolver, and the Ship template and installed-mirror wiring that consumes it in harness generation AND crash recovery. It does NOT author, install, re-render or repair the harness-architect actor; that actor is already installed and P-004 conformant through external Ship commits."
doc_type: plan
source: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
date: 2026-09-18
plan_id: ship-harness-lifecycle-foundation
plan_path: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
plan_role: active
revision: 11
revision_scope: full-rewrite-current-state-addressing-attempt-09-findings
revision_11_note: "Revision 11 is a REWRITE as a current-state contract, not a correction log. FIVE STRUCTURAL CHANGES. (1) EVERY ACTIVATION PATH IS CORRECTED TO A PATH THAT EXISTS: templates/agents/_ship.agent.md.tmpl, .github/agents/_ship.agent.md and .autoharness/harness-manifest.yaml, with the single existing manifest entry for the installed mirror named exactly (S35). (2) Rendering draws from the manifest's SINGLE TOP-LEVEL variables_used mapping, which is what the manifest actually carries; a matched artifacts entry supplies only path, template and checksum (S36). (3) The declaration and aggregation model is TOTAL: every task resolves to surfaces, none or invalid, and a deterministic four-step precedence maps the aggregate to exactly one state, exit code and reason code drawn from a closed enumerated set (S37, S47). (4) Containment is specified as handle-bound traversal with named platform primitives and a fail-closed PLATFORM_INVARIANT_UNAVAILABLE outcome, replacing the check-then-open race (S38). (5) The oversized 181.002-T is split into three tasks - a secure-read primitive, the resolver core and the CLI/JSON adapter - and the RED, fixture, verify and activation tasks are re-scoped so no task depends on an artifact that does not yet exist at its own start (S40, S43, S48). S14 remains CLOSED on external Ship evidence. S13, S15-S34 and S35-S52 are ADDRESSED AND REMAIN OPEN pending independent attempt 10."
verdict: null
verdict_is_pass: false
verdict_revision: null
verdict_asserted_against_revision: null
disposition: PENDING-INDEPENDENT-REVIEW
publication_eligible: false
publication_eligible_basis: "No independent review has judged revision 11. Attempt 09 returned FAIL against revision 10."
historical_verdict_is_not_carried_forward: true
last_independent_verdict: FAIL
last_independent_verdict_attempt: 9
last_independent_verdict_revision: 10
verdict_note: "NO VERDICT IS ASSERTED AGAINST REVISION 11. The verdict manifest at review_manifest is the SOLE AUTHORITY for review state; these fields are POINTERS, not a second record. Revision 11 remediates S13, S15-S34 and S35-S52 but CLOSES NOTHING: findings are closed by an independent attempt that verifies the closure, never by the authoring agent. S14 alone is closed, and was closed at attempt 08 on external evidence."
awaiting_attempt: 10
awaiting_attempt_against_revision: 11
latest_attempt: 9
latest_attempt_reviewed_revision: 10
review_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 8
source_stash_ids:
  - 76EBDE6D
source_stash_note: "This unit is SINGLE-SOURCE. The governing decision's portfolio table assigns 76EBDE6D to row 'P4 | 187-S | 181-F | foundation', and every live carrier cites it. 76EBDE6D is an archived stash entry - 'P-021 RELIABILITY FOLLOW-UP: P-004 red-phase precondition is unsatisfiable on this workspace' - which is this unit's genuine origin."
feature_id: 181-F
shipment_id: 187-S
unit_role: lifecycle-only
unit_scope_note: "This unit owns the LIFECYCLE ONLY. It does not author, install, re-render or repair the harness-architect actor."
depends_on_shipments: []
dag_root: true
dag_root_note: "187-S declares an EMPTY dependency set and carries the dag-root label so pre_claim derives declared_root rather than blocking as UNSEQUENCED_SHIPMENT. Root status is a GRAPH FACT and confers NO claim authority: ordinary pre-claim, this unit's own P-002/P-004 harness generation, independent review, CI and closure all still apply."
removed_depends_on_shipments:
  - 184-S
  - 188-S
  - 191-S
secure_read_module: src/autoharness/harness_read.py
secure_read_owner_task: 181.002-T
resolver_module: src/autoharness/harness_surfaces.py
resolver_owner_task: 181.006-T
resolver_entry_point: "resolve_harness_surfaces(*, workspace_root: Path, autoharness_home: Path, shipment_id: str) -> HarnessResolution"
cli_owner_task: 181.007-T
resolver_cli_default_form: "autoharness harness resolve --workspace . --shipment {shipment_id} --json"
resolver_persists_state: false
freshness_carrier: recomputation
primitive_locality_note: "This unit's secure-read primitive is LOCAL to this unit and deliberately duplicates nothing it can import today. 185-S / 179-F will later deliver a general safe-primitive substrate (atomic write, path containment, fixed-argv exec, bounded reader). NO EDGE ON 185-S IS CREATED OR IMPLIED: 187-S remains a dag-root, and consolidating onto the general substrate is future work for whichever unit ships second, not a prerequisite of this one."
activation_template_path: templates/agents/_ship.agent.md.tmpl
activation_mirror_path: .github/agents/_ship.agent.md
activation_manifest_path: .autoharness/harness-manifest.yaml
activation_manifest_entry_path: .github/agents/_ship.agent.md
activation_manifest_entry_template_field: "global agent definition"
activation_manifest_entry_count: 1
activation_file_count: 3
activation_owner_task: 181.005-T
parity_criteria_vocabulary: PAR-1..PAR-6b
actor_installed_in_baseline: true
actor_behaviorally_conformant: true
actor_structural_installation_commit: 07b4be79263252b1820701fd123d0aed85c1db2a
actor_behavioral_conformance_commits:
  - 1cb0dc8140a809d63c3193d58431cd14408788b7
  - b8ac632a93751fb29c51a8e5bf0f5e036b65cfb3
actor_conformance_note: "STRUCTURAL INSTALLATION AND BEHAVIOURAL CONFORMANCE ARE DISTINCT AND ARE KEPT DISTINCT. 07b4be79 placed .github/skills/harness-architect/SKILL.md on disk and registered it in .autoharness/harness-manifest.yaml at checksum parity; it is recorded as STRUCTURAL INSTALLATION ONLY and is never cited as P-004 conformance evidence. Conformance rests on 1cb0dc81 and b8ac632a. Evidence: canonical suite 2358 passed / 0 failed / 54 skipped, manifest parity holding."
actor_artifact: .github/skills/harness-architect/SKILL.md
retired_prerequisite_shipment: 191-S
retired_prerequisite_feature: 185-F
retired_prerequisite_note: "RETIRED, NEVER CLAIMED, NEVER EXECUTED, NEVER SHIPPED. Nothing in this plan may be read as claiming 191-S shipped."
bootstrap_precursor_plan: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
bootstrap_precursor_status: RETIRED-SUPERSEDED-COMPLETED-EXTERNALLY
gates: []
requires_plan_hardening: true
hardening_rationale: "Modifies the Ship agent lifecycle itself - every future shipment traverses the phase this unit installs - and adds two new public Python modules, a new CLI subcommand and a new manifest-tracked activation. Blast radius spans the Ship template, its installed mirror, the harness manifest and the crash-recovery surface."
tags:
  - foundation
  - ship-lifecycle
  - harness-architect
  - p-004
---

# Foundation: Ship pre-task harness-generation lifecycle

## Problem frame - current state

P-004 requires that, before Ship executes a task, a harness exists and is
observed RED. The policy names an actor that performs that generation. Until
recently that actor was a template that had never been installed, so the
requirement was unsatisfiable on this workspace - the origin recorded in stash
`76EBDE6D`.

**That gap is closed, and it was closed outside this unit.** The
`harness-architect` actor is installed at
`.github/skills/harness-architect/SKILL.md`, manifest-registered at checksum
parity, and **behaviourally conformant with P-004**. See
`actor_structural_installation_commit` and
`actor_behavioral_conformance_commits` for the exact commits and the
distinction this plan preserves between the two properties.

**What remains missing is the lifecycle that calls it.** Ship has no phase that
decides *whether* a task needs a harness, *which* surface supplies it, or
*whether that surface is usable right now* - and no machine-checkable answer it
can hand to P-004. Today that question is answered by agent prose. This unit
replaces the prose with an executable boundary.

### What this unit owns

| Owns | Does not own |
|---|---|
| A handle-bound secure-read primitive, local to this unit | The harness-architect actor's content, installation or conformance |
| A read-only harness-surface resolver with a typed result | The P-004 gate implementation itself (a separate, blocked unit) |
| A deterministic CLI over that resolver | Any operation registry, result model or transport (`184-S` scope) |
| Ship template and installed-mirror wiring, in harness generation **and** crash recovery | Any MCP surface |
| The manifest refresh that accompanies the activation | Any change to P-002, P-004, gate semantics, grants, `--force` or waivers |

### What is no longer authorized here

* **No bootstrap exception, in any form.** No carve-out, no grant, no
  `--force`, no force-audit entry, no expiring authority, no
  self-authorization. `PRE-0` is withdrawn as an execution path and is not
  re-described or re-scoped.
* **No claim that a retired unit executed.** `188-S` / `182-F` and
  `191-S` / `185-F` are archived, were never claimed and never executed.
* **No prerequisite release unit.** Revision 9 created one and it is retired;
  `187-S` is a root.

### Historical material - non-authoritative

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

## Module 1 - the secure-read primitive

Public module `src/autoharness/harness_read.py`, owned by `181.002-T`. It is
the **only** way this unit touches the filesystem. The resolver never calls
`open`, `Path.read_text`, `os.stat` or `os.listdir` directly.

### Why a primitive, and why local

A containment check followed by a separate `open` is a **check-then-open
race**: the path that was validated is not provably the path that is read. The
primitive removes the gap by making the *handle* the unit of trust - every
check is performed on an already-open handle, and the bytes are read from that
same handle.

The primitive is **local to this unit**. `185-S` / `179-F` will later deliver a
general safe-primitive substrate. **No edge on `185-S` is created or implied**;
`187-S` remains a `dag-root`, and consolidation is future work for whichever
unit ships second.

### Roots are canonicalized once; descendants never traverse links

Each trust root is resolved **exactly once**, at entry, with
`Path.resolve(strict=True)`. A root may itself lie behind a symlink - that is
normal on macOS and in container mounts, and rejecting it would make the tool
unusable. **Below a canonical root, no component may be a link.**

### Lexical rejection, before any handle is opened

Applied to every declared `<id>` and every derived relative path:

reject absolute paths; reject a drive letter (`^[A-Za-z]:`); reject a UNC or
extended prefix (`\\`, `\\?\`, `\\.\`); reject environment-variable
syntax (`$NAME`, `${NAME}`, `%NAME%`); reject `~` home expansion; reject any
`..` component; reject an empty or `.` component; reject NUL and any control
character; reject a component that is a reserved Windows device name
(`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`), case-insensitively
and with any extension.

Failure is `PATH_LEXICALLY_REJECTED`. **No filesystem call has occurred.**

### POSIX traversal - component-relative, no-follow

```python
root_fd = os.open(canonical_root, os.O_RDONLY | os.O_DIRECTORY)
# for each intermediate component, relative to the parent directory fd:
child_fd = os.open(component, os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                   dir_fd=parent_fd)
# for the final component:
file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent_fd)
```

`O_NOFOLLOW` on the final component raises `ELOOP` when it is a symlink;
`O_NOFOLLOW | O_DIRECTORY` does the same for intermediates. Because every
`os.open` is **relative to the parent directory's file descriptor**, no path
string is ever re-resolved by the kernel and there is no window in which a
component can be swapped for a link.

`os.fstat(file_fd)` then supplies the identity tuple
`(st_dev, st_ino, st_size, st_mtime_ns)`. `stat.S_ISREG` must hold; a
directory, FIFO, socket, device or anything else is `PATH_NOT_REGULAR_FILE`.

### Windows traversal - handle-bound, reparse-rejecting

```
CreateFileW(path,
            dwDesiredAccess       = GENERIC_READ,
            dwShareMode           = FILE_SHARE_READ,
            dwCreationDisposition = OPEN_EXISTING,
            dwFlagsAndAttributes  = FILE_FLAG_OPEN_REPARSE_POINT
                                  | FILE_FLAG_BACKUP_SEMANTICS)
```

`FILE_FLAG_OPEN_REPARSE_POINT` opens the **link itself** rather than its
target, so a junction or symlink cannot silently redirect the read.

1. `GetFileInformationByHandle` - if `dwFileAttributes` carries
   `FILE_ATTRIBUTE_REPARSE_POINT`, fail `PATH_REPARSE_COMPONENT`. If it carries
   `FILE_ATTRIBUTE_DIRECTORY` for a final component, fail
   `PATH_NOT_REGULAR_FILE`.
2. `GetFinalPathNameByHandle(h, VOLUME_NAME_DOS)` - normalize the returned
   path, strip the `\\?\` prefix, and require **component-wise** containment
   under the canonical root. This is the identity check: it asks what the
   handle actually points at, not what the caller asked for.
3. Identity tuple is
   `(dwVolumeSerialNumber, nFileIndexHigh, nFileIndexLow, nFileSizeHigh, nFileSizeLow)`.

### Containment is component-wise, never by string prefix

`/ws-evil/x` is **not** inside `/ws`. Containment compares resolved path
**components**, so a sibling whose name merely shares a prefix is rejected
(`PATH_OUTSIDE_ROOT`).

### Read, then re-verify

Bytes are read from the already-open handle. The identity tuple is captured
**before** and **after** the read and must be equal; a mismatch is
`READ_IDENTITY_MISMATCH`. Any exception during the read that is not a
recognized containment failure is `READ_RACE_DETECTED`.

### Bounds

| Bound | Value | Violation |
|---|---|---|
| Per-file bytes | `4_194_304` (4 MiB) | `READ_SIZE_EXCEEDED` |
| Aggregate bytes per resolution | `33_554_432` (32 MiB) | `READ_AGGREGATE_EXCEEDED` |
| Files opened per resolution | `256` | `READ_AGGREGATE_EXCEEDED` |
| Shipment member IDs | `512` | `SHIPMENT_ITEMS_ABSENT` when 0; `READ_AGGREGATE_EXCEEDED` when over |
| Path components below a root | `32` | `PATH_LEXICALLY_REJECTED` |

The per-file bound is enforced **from the `fstat`/`GetFileInformationByHandle`
size before reading**, not by reading and then measuring.

### When the invariant is unavailable, fail - never degrade

If `O_NOFOLLOW` or `dir_fd` support is absent, if `ctypes` cannot bind
`CreateFileW` or `GetFinalPathNameByHandle`, or if any required primitive
raises `NotImplementedError` or `AttributeError`, the read fails
`PLATFORM_INVARIANT_UNAVAILABLE` and the resolution is `UNRESOLVED`.

**There is no unchecked fallback read anywhere in this unit.**

### Platform coverage cannot skip

The primitive takes a **platform adapter** - the narrow set of calls above
behind one injectable interface. `181.001-T` exercises **both** the POSIX and
the Windows branch on **every** platform by injecting a deterministic mock
adapter that returns scripted results, including the reparse, identity-mismatch
and invariant-unavailable cases.

A real-filesystem symlink/junction test is **additional**, and may be skipped
where the OS forbids creating links without elevation. The mocked tests are
**not** skippable, so the security-critical branches always run.

## Module 2 - the resolver

Public module `src/autoharness/harness_surfaces.py`, owned by `181.006-T`.
Sole public entry point, keyword-only:

```python
def resolve_harness_surfaces(
    *,
    workspace_root: Path,
    autoharness_home: Path,
    shipment_id: str,
) -> HarnessResolution: ...
```

**The resolver is READ-ONLY.** It writes no file, creates no directory, sets no
environment variable, spawns no process and mutates no backlog record. It is
safe to call repeatedly and safe to call during crash recovery.

### Public types

```python
class HarnessState(str, Enum):
    HARNESS_READY = "HARNESS_READY"
    NO_HARNESS    = "NO_HARNESS"
    UNRESOLVED    = "UNRESOLVED"

class SurfaceStatus(str, Enum):
    PRESENT = "PRESENT"
    MISSING = "MISSING"
    STALE   = "STALE"
    INVALID = "INVALID"

class DeclarationKind(str, Enum):
    SURFACES = "SURFACES"
    NONE     = "NONE"
    INVALID  = "INVALID"

@dataclass(frozen=True)
class TaskDeclaration:
    task_id: str
    kind: DeclarationKind
    surface_ids: tuple[str, ...]
    reason_code: str | None

@dataclass(frozen=True)
class SurfaceResolution:
    surface_id: str
    status: SurfaceStatus
    reason_code: str
    installed_path: str | None
    template_path: str | None
    manifest_checksum: str | None
    installed_digest: str | None
    rendered_digest: str | None

@dataclass(frozen=True)
class Diagnostic:
    reason_code: str
    subject_kind: str
    subject: str | None
    detail: str | None

@dataclass(frozen=True)
class HarnessResolution:
    schema_version: int
    state: HarnessState
    reason_code: str
    exit_code: int
    shipment_id: str
    surfaces: tuple[SurfaceResolution, ...]
    declarations: tuple[TaskDeclaration, ...]
    backlog_root: str | None
    inputs_sha256: str | None
    diagnostics: tuple[Diagnostic, ...]
```

`Diagnostic` replaces the free-text `errors` tuple of revision 10. It is
**structured and redacted**: `reason_code` is drawn from the closed set below,
`subject_kind` is one of `shipment`, `task`, `surface`, `manifest`, `template`,
`installed`, `backlog_root`, `platform`, and `detail` is a short
**machine-authored** phrase. **No raw exception text, no traceback, no absolute
path, no user directory and no machine name is ever placed in a `Diagnostic`.**

### Canonical shipment and task source

The backlog root is resolved with the **existing** helper `resolve_backlog_root`
from `src/autoharness/backlog_root.py`. The resolver does not re-implement root
discovery and does not accept a backlog path argument.

**Ambient environment is read exactly once, through a frozen allowlist.**

```python
_BACKLOG_ENV_ALLOWLIST: tuple[str, ...] = ("BACKLOGIT_WORKSPACE_DIR",)
```

At entry the resolver captures
`{k: os.environ.get(k) for k in _BACKLOG_ENV_ALLOWLIST}` as an immutable
snapshot, calls `resolve_backlog_root` **exactly once** under that snapshot, and
never reads `os.environ` again. Two consequences:

* the same resolution cannot see two different roots, and
* the override is **evidence**: the snapshot is bound into `inputs_sha256`, so a
  result produced under a redirected root is distinguishable from one that was
  not.

The returned root is then **validated**: it must be a component-wise descendant
of the canonical `workspace_root`, or the resolution is `UNRESOLVED` with
`BACKLOG_ROOT_OUTSIDE_WORKSPACE`. A root that cannot be resolved at all is
`BACKLOG_ROOT_UNRESOLVED`. The selected root is emitted **root-relative** in
`backlog_root`.

Record lookup, applied to the shipment record and to every member ID:

* **exactly one** record must exist across the live queue and the archive,
  combined;
* zero records, more than one record, or front matter that does not parse is
  `UNRESOLVED`;
* the shipment's membership comes **solely** from `custom_fields.items`.

### Declaration grammar - total, with no silent default

Harness requirements are declared **only** on task records, as labels.

A task declaration is computed by a **total** function - every member task
yields exactly one `TaskDeclaration`:

| Task's `harness-surface:` labels | `kind` | `surface_ids` |
|---|---|---|
| One or more, all matching `harness-surface:<id>`, all `<id>` unique | `SURFACES` | those IDs, sorted |
| Exactly one label `harness-surface:none`, and no other | `NONE` | `()` |
| Both `harness-surface:none` and a `harness-surface:<id>` | `INVALID` (`DECLARATION_MIXED`) | `()` |
| The same `<id>` twice | `INVALID` (`DECLARATION_DUPLICATE`) | `()` |
| Any `<id>` failing `^[a-z0-9]+(-[a-z0-9]+)*$` | `INVALID` (`DECLARATION_ID_MALFORMED`) | `()` |
| More than one `harness-surface:none` | `INVALID` (`DECLARATION_DUPLICATE`) | `()` |
| No `harness-surface:` label at all | `INVALID` (`DECLARATION_ABSENT`) | `()` |

**Absence is not consent.** A task with no declaration is `INVALID`, never an
implicit `none`.

Only `-T` task records are consulted. A member ID that is a feature (`-F`) is
**not** a declaration site and contributes no `TaskDeclaration`; it is still
subject to the exactly-one-record rule.

Tasks `181.001-T` ... `181.007-T` carry `harness-surface:harness-architect`.

### Surface mapping and manifest match - one classification rule

For a declared `<id>`:

1. The installed path is **deterministically** `.github/skills/<id>/SKILL.md`,
   under the canonical `workspace_root`. No search, no glob, no fallback.
2. The manifest `.autoharness/harness-manifest.yaml` must contain **exactly
   one** entry under `artifacts:` whose `path` equals that exact string **and**
   whose `template` equals the exact string `skills/<id>/SKILL.md.tmpl`.
3. The template path is that `template` value, under the canonical
   `autoharness_home`.

| Condition | `SurfaceStatus` | Surface `reason_code` |
|---|---|---|
| Manifest unreadable or not parseable | `INVALID` | `MANIFEST_UNREADABLE` / `MANIFEST_MALFORMED` |
| Zero `artifacts` entries match | `INVALID` | `MANIFEST_ENTRY_NOT_FOUND` |
| More than one entry matches | `INVALID` | `MANIFEST_ENTRY_AMBIGUOUS` |
| An entry matches `path` but not `template` | `INVALID` | `MANIFEST_ENTRY_TEMPLATE_MISMATCH` |
| Exactly one entry; installed file absent | `MISSING` | `SURFACE_NOT_INSTALLED` |
| Exactly one entry; template absent | `MISSING` | `SURFACE_TEMPLATE_ABSENT` |
| Any containment, identity, bounds or platform failure on either file | `INVALID` | that failure's own code |
| Either file fails UTF-8 decoding | `INVALID` | `TEMPLATE_DECODE_FAILED` / `INSTALLED_DECODE_FAILED` |
| A required placeholder has no value | `INVALID` | `VARIABLE_UNRESOLVED` |
| Exactly one entry, both files read, parity holds | `PRESENT` | `SURFACE_PRESENT` |
| Exactly one entry, both files read, parity fails | `STALE` | `SURFACE_STALE` |

**This table is the single classification rule.** It is not restated with
different wording anywhere else in this plan, in any carrier, or in the Ship
phase text.

### Rendering - the manifest's top-level `variables_used`

`.autoharness/harness-manifest.yaml` carries **one top-level `variables_used`
mapping** that applies to the whole manifest. Entries under `artifacts:` carry
`path`, `primitive`, `template`, `checksum` and an optional `note` - **they do
not carry `variables_used`**, and the resolver must not look for it there.

* The value source for rendering is the **top-level** `variables_used` mapping.
* The matched `artifacts` entry supplies **only** `path`, `template` and
  `checksum`.
* Placeholders rendered are **uppercase only** - `{{NAME}}` where `NAME`
  matches `^[A-Z][A-Z0-9_]*$`. Lowercase or mixed-case brace sequences are left
  untouched and are not treated as placeholders.
* A placeholder present in the template with **no** key in the top-level
  `variables_used` is `VARIABLE_UNRESOLVED` -> `INVALID`.
* The **whole** top-level `variables_used` mapping is bound into
  `inputs_sha256`, not merely the keys a given template happened to consume, so
  a change to an unused variable is still visible as an input change.
* **Canonical bytes:** decode as UTF-8, then translate `CRLF` -> `LF` and any
  remaining lone `CR` -> `LF`. Nothing else is normalized - no trailing-space
  stripping, no final-newline insertion, no Unicode normalization.
* **`PRESENT` requires both:** the rendered canonical bytes equal the installed
  canonical bytes, **and** the manifest `checksum` equals the SHA-256 of the
  installed canonical bytes. Either alone is `STALE`.

### Trust roots - separated, never substituted

| Input | Canonical root |
|---|---|
| Backlog records, `.autoharness/harness-manifest.yaml`, installed `.github/skills/**` | `workspace_root` |
| Templates `skills/<id>/SKILL.md.tmpl` | `autoharness_home` |

The two roots are canonicalized independently and **never substituted for one
another**. A path resolved under the wrong root is `PATH_OUTSIDE_ROOT`, even if
a file happens to exist there. When the two roots are the same directory - as
they are in this self-hosting repository - each read still declares which root
it is asserting containment against, so the separation is preserved in the
evidence even when the paths coincide.

## Aggregation - total, deterministic, and stated once

The resolution state is computed by evaluating these rules **in order** and
stopping at the first that matches. This is the only place the aggregate state
is derived.

| # | Condition | `state` | `exit_code` | `reason_code` |
|---|---|---|---|---|
| A1 | Any precondition failed: shipment record, backlog root, member lookup, or manifest load | `UNRESOLVED` | `2` | that failure's own code |
| A2 | Any `TaskDeclaration.kind` is `INVALID` | `UNRESOLVED` | `2` | that declaration's own code |
| A3 | Any `SurfaceResolution.status` is `INVALID` | `UNRESOLVED` | `2` | that surface's own code |
| A4 | The union of declared surface IDs is **empty** (every member task declared `none`) | `HARNESS_READY` | `0` | `NO_SURFACES_REQUIRED` |
| A5 | Any `SurfaceResolution.status` is `MISSING` or `STALE` | `NO_HARNESS` | `1` | that surface's own code |
| A6 | Every `SurfaceResolution.status` is `PRESENT` | `HARNESS_READY` | `0` | `ALL_SURFACES_PRESENT` |

**The rules are total**: A1-A6 partition every reachable combination, and A6 is
reached only when at least one surface exists and all are `PRESENT`.

**Invalid dominates.** A2 and A3 precede A4, so a shipment in which one task is
malformed and every other declared `none` is `UNRESOLVED`, never a vacuous
ready.

**`NO_SURFACES_REQUIRED` is a real ready state**, with `surfaces == ()` and
`exit_code == 0`. A shipment whose every task legitimately needs no harness is
**not** an error and **not** `NO_HARNESS`.

**Ties are resolved deterministically.** When several entries satisfy the same
rule, the reported `reason_code` is taken from the **first** in the emitted
order - declarations by ascending `task_id`, surfaces by ascending
`surface_id`. The same inputs always produce the same `reason_code`.

**`SurfaceStatus.INVALID` is reachable.** Revision 10 defined it and no rule
produced it; here rows 1-4 and 7-9 of the classification table produce it and
`A3` consumes it.

### The closed reason-code set

Every `reason_code` emitted anywhere - on the resolution, on a surface, on a
declaration, in a `Diagnostic` - is drawn from this set and no other.

| Code | Terminal state |
|---|---|
| `ALL_SURFACES_PRESENT` | `HARNESS_READY` |
| `NO_SURFACES_REQUIRED` | `HARNESS_READY` |
| `SURFACE_PRESENT` | (surface only) |
| `SURFACE_NOT_INSTALLED` | `NO_HARNESS` |
| `SURFACE_TEMPLATE_ABSENT` | `NO_HARNESS` |
| `SURFACE_STALE` | `NO_HARNESS` |
| `SHIPMENT_RECORD_NOT_FOUND` | `UNRESOLVED` |
| `SHIPMENT_RECORD_AMBIGUOUS` | `UNRESOLVED` |
| `SHIPMENT_RECORD_MALFORMED` | `UNRESOLVED` |
| `SHIPMENT_ITEMS_ABSENT` | `UNRESOLVED` |
| `TASK_RECORD_NOT_FOUND` | `UNRESOLVED` |
| `TASK_RECORD_AMBIGUOUS` | `UNRESOLVED` |
| `TASK_RECORD_MALFORMED` | `UNRESOLVED` |
| `DECLARATION_ABSENT` | `UNRESOLVED` |
| `DECLARATION_MIXED` | `UNRESOLVED` |
| `DECLARATION_DUPLICATE` | `UNRESOLVED` |
| `DECLARATION_ID_MALFORMED` | `UNRESOLVED` |
| `MANIFEST_UNREADABLE` | `UNRESOLVED` |
| `MANIFEST_MALFORMED` | `UNRESOLVED` |
| `MANIFEST_ENTRY_NOT_FOUND` | `UNRESOLVED` |
| `MANIFEST_ENTRY_AMBIGUOUS` | `UNRESOLVED` |
| `MANIFEST_ENTRY_TEMPLATE_MISMATCH` | `UNRESOLVED` |
| `VARIABLE_UNRESOLVED` | `UNRESOLVED` |
| `TEMPLATE_DECODE_FAILED` | `UNRESOLVED` |
| `INSTALLED_DECODE_FAILED` | `UNRESOLVED` |
| `PATH_LEXICALLY_REJECTED` | `UNRESOLVED` |
| `PATH_OUTSIDE_ROOT` | `UNRESOLVED` |
| `PATH_REPARSE_COMPONENT` | `UNRESOLVED` |
| `PATH_NOT_REGULAR_FILE` | `UNRESOLVED` |
| `READ_IDENTITY_MISMATCH` | `UNRESOLVED` |
| `READ_SIZE_EXCEEDED` | `UNRESOLVED` |
| `READ_AGGREGATE_EXCEEDED` | `UNRESOLVED` |
| `READ_RACE_DETECTED` | `UNRESOLVED` |
| `PLATFORM_INVARIANT_UNAVAILABLE` | `UNRESOLVED` |
| `BACKLOG_ROOT_UNRESOLVED` | `UNRESOLVED` |
| `BACKLOG_ROOT_OUTSIDE_WORKSPACE` | `UNRESOLVED` |

## The JSON document

`--json` emits exactly this object on stdout, and nothing else.

| Field | JSON type | Notes |
|---|---|---|
| `schema_version` | integer | always `1` |
| `state` | string | a `HarnessState` name |
| `reason_code` | string | from the closed set |
| `exit_code` | integer | `0`, `1` or `2`; equals the process exit code |
| `shipment_id` | string | as supplied |
| `backlog_root` | string or null | **root-relative** |
| `surfaces` | array of object | sorted by `surface_id` ascending |
| `declarations` | array of object | sorted by `task_id` ascending |
| `inputs_sha256` | string or null | 64 lowercase hex characters |
| `diagnostics` | array of object | emitted order, stable |

`surfaces[]` objects: `surface_id` (string), `status` (string),
`reason_code` (string), `installed_path` (string or null, root-relative),
`template_path` (string or null, root-relative), `manifest_checksum`
(string or null), `installed_digest` (string or null), `rendered_digest`
(string or null).

`declarations[]` objects: `task_id` (string), `kind` (string),
`surface_ids` (array of string, sorted ascending), `reason_code`
(string or null).

`diagnostics[]` objects: `reason_code` (string), `subject_kind` (string),
`subject` (string or null, root-relative when it is a path),
`detail` (string or null).

**Tuples serialize as JSON arrays.** Python `tuple` has no JSON representation;
every `tuple[...]` field in the dataclasses above is emitted as an array, and a
consumer must not expect a fixed-length structure.

**Every field is always present.** Absence is expressed as `null`, never by
omitting the key, so a consumer may index without probing.

**Redaction is structural, not best-effort.** Paths are emitted root-relative
with POSIX separators. A value that cannot be made root-relative is emitted as
`null` with a `Diagnostic` naming the reason - it is never emitted absolute.

### Canonical JSON and digests

Canonical JSON, used for **every** digest preimage:

```python
json.dumps(obj, sort_keys=True, separators=(",", ":"),
           ensure_ascii=True).encode("utf-8")
```

Each bound input contributes one record:

```json
{"label": "<label>", "sha256": "<64 hex>"}
```

or, when the input could not be read:

```json
{"label": "<label>", "sha256": null, "absent": "<REASON_CODE>"}
```

`absent` is the **explicit absence sentinel**. A missing input is never
silently skipped and never conflated with an empty one - an unreadable manifest
and a zero-byte manifest produce different preimages.

The bound input list, in this fixed label order:

| Order | `label` | Payload |
|---|---|---|
| 1 | `env_snapshot` | canonical JSON of the frozen allowlisted environment snapshot |
| 2 | `backlog_root` | UTF-8 bytes of the root-relative backlog root |
| 3 | `shipment_record` | raw bytes of the shipment record |
| 4 | `declarations` | canonical JSON of the derived `declarations` array |
| 5 | `manifest` | raw bytes of `.autoharness/harness-manifest.yaml` |
| 6 | `manifest_variables_used` | canonical JSON of the **whole** top-level `variables_used` mapping |
| 7... | `template:<surface_id>` | canonical bytes of each template, ascending by `surface_id` |
| ... | `installed:<surface_id>` | canonical bytes of each installed file, ascending by `surface_id` |

```
inputs_sha256 = sha256(
    b"autoharness/harness-surfaces/inputs/v1\x00" +
    canonical_json(bound_input_list)
).hexdigest()
```

**Domain separation** is the constant prefix plus the NUL byte, and the `label`
field inside each record. Two different inputs with identical bytes cannot
collide, because their labels differ.

**`inputs_sha256` excludes itself.** It is computed over the bound input list
**only** - never over the result document, never over any field of
`HarnessResolution`. There is no self-referential digest anywhere in this unit.

It is emitted on **every** outcome - `HARNESS_READY`, `NO_HARNESS` and
`UNRESOLVED` alike - whenever at least the first two inputs were obtainable.
When the resolution fails so early that even the environment snapshot is
unavailable, the field is `null` and a `Diagnostic` records why.

## The CLI

Owned by `181.007-T`. The **runnable default form**, which is what Ship and
human callers use:

```
autoharness harness resolve --workspace . --shipment 187-S --json
```

`--autoharness-home` is **optional**. When omitted, the installation home is
resolved by the precedence the CLI already implements. It exists for API,
`--help` and test-fixture use:

```
autoharness harness resolve --workspace . --autoharness-home PATH --shipment ID --json
```

Here `PATH` and `ID` are **metavariables in help output**, not literal text. No
angle-bracket placeholder such as `<resolved-or-default>` ever appears in Ship
prose, in a fixture, or in any command a reader is expected to run - a command
that cannot be pasted and executed is not a specification.

| Exit | State |
|---|---|
| `0` | `HARNESS_READY` |
| `1` | `NO_HARNESS` - adjudicated absence |
| `2` | `UNRESOLVED` - invalid, unsafe, ambiguous or raced input |

The process exit code **always equals** the `exit_code` field of the emitted
document. The CLI is **deterministic and side-effect free**. `--json` writes the
document to stdout; human-readable diagnostics go to stderr and are redacted by
the same rule. This unit adds **no** MCP surface and registers **no** operation
in any operation framework - that substrate is `184-S` scope.

## Freshness is recomputation, not storage

**No readiness state is ever persisted.** There is no cache file, no gate token
file and no backlog field recording readiness.

* Ship and human callers invoke the **CLI** freshly at the moment they need an
  answer.
* The future P-004 gate calls the **Python function directly** and emits the
  returned `inputs_sha256` into its own evidence.
* A stored token, digest or `inputs_sha256` carried in a checkpoint is
  **evidence of what was once observed and never an authorization**. It is
  compared, never trusted. No code path accepts a caller-supplied digest as a
  substitute for recomputation.
* A second read that disagrees with the first is a race and yields
  `UNRESOLVED`.

### Both non-ready states halt, and they stay distinct

`NO_HARNESS` and `UNRESOLVED` **both** halt before task partition. They are not
merged: different states, different exit codes, different reason codes, because
"this surface is adjudicated absent" and "I could not safely determine
anything" require different operator responses.

## The ACTIVATE contract

`181.005-T` performs a single atomic activation across **exactly three files**,
refreshing **exactly one** manifest entry.

| File | Exists today | Change |
|---|---|---|
| `templates/agents/_ship.agent.md.tmpl` | yes | Update the **one existing** harness-generation section; update the **one existing** crash-resumption section |
| `.github/agents/_ship.agent.md` | yes | Insert **one new** harness-generation section; update the **one existing** crash-resumption section |
| `.autoharness/harness-manifest.yaml` | yes | Refresh the **one** entry whose `path` is `.github/agents/_ship.agent.md` |

These are the real paths. `templates/agents/ship.md.tmpl` and
`.github/agents/ship.md` **do not exist** and are named nowhere in this unit.

This is decision `D11` applied: the manifest is a **member of the commit and of
the rollback unit**, and checksum parity is verified against the on-disk file
after the refresh. Templates are not manifest-tracked, so the
template-and-mirror pair refreshes **one** entry, not two.

### The two files are asymmetric, and the contract respects that

The template and its installed mirror have **diverged structurally** over many
shipments. The template carries a harness-generation step; the mirror never
received one. Activation therefore performs **different edits** on the two
files, and the plan states each exactly rather than pretending to a
re-render.

**Template - update in place at its current anchor.**

The heading

```
### Step 2: Harness Generation (P-002 / P-004)
```

occurs **exactly once**. The activation rewrites that section's body. It does
**not** add a section, does not move it and does not renumber anything.

**Mirror - insert exactly one new section, renumbering nothing.**

The mirror has `### Step 1: Pre-Flight Checks` followed directly by
`### Step 2: Task Execution Loop`. The new section is inserted **immediately
before**

```
### Step 2: Task Execution Loop
```

with the heading

```
### Step 1.5: Harness Generation (P-002 / P-004)
```

`Step 1.5` is chosen because decimal sub-steps are **already this file's
style** - it carries `Step 0.0`, `Step 0.1`, `Step 0.1b`, `Step 0.1c`,
`Step 0.1d` and `Step 0.5`. Inserting at `1.5` leaves `Step 2` and every later
step **unrenumbered**, so no cross-reference anywhere in the workspace breaks
and no reader encounters two different `Step 2`s.

**Crash-resumption - one existing section in each file.**

```
### Crash-Resumption / Startup Recovery Protocol (fail-closed, owner-exclusive)
```

occurs **exactly once** in each file. Both are updated. Neither is added.

### The Ship-only restore sequence

Inserted into both crash-resumption sections, as an ordered sequence:

1. Load the selected checkpoint payload and validate it against the checkpoint
   schema. A payload that fails validation halts.
2. **Require `shipment_id`.** A checkpoint with no shipment context cannot be
   resolved against, and halts.
3. **Recompute**: invoke the resolver CLI freshly for that `shipment_id`. Any
   digest or token stored in the checkpoint is **compared for reporting only**
   and carries no authority.
4. **Halt on exit `1` or `2`**, reporting the `state` and `reason_code`. Only
   exit `0` continues.
5. **Only then** restore the task cursor, the phase and the next-step intent.

The resolver runs **before** step 5, so a crash cannot resume execution into a
workspace whose harness surface has since become absent or unverifiable.

**This sequence is Ship's alone.** Stage has no harness surface, performs no
task partition and executes no harness-gated work, so no Stage behaviour is
described, promised or required here. Revision 10's claim that the rule also
governed Stage is withdrawn as unimplementable.

### Structural tests enforce the shape

`181.003-T` provides the canonical expected section text as fixtures and the
structural tests over it. The tests assert, mechanically:

| Assertion | Why |
|---|---|
| `### Step 2: Harness Generation (P-002 / P-004)` occurs **exactly once** in the template | no duplicate gate |
| `### Step 1.5: Harness Generation (P-002 / P-004)` occurs **exactly once** in the mirror | no duplicate gate |
| The mirror's `Step 1.5` heading appears **before** `### Step 2: Task Execution Loop`, with no other `###` between them | correct insertion point |
| `### Step 2: Task Execution Loop` still occurs exactly once, and no `### Step 2:` heading was renumbered | nothing else moved |
| The crash-resumption heading occurs **exactly once** per file | no duplicate recovery path |
| Each file's harness section names all three of exit `0`, `1` and `2` and the halt rule for `1` and `2` | complete exit handling |
| No file asserts that a stored token, digest or `inputs_sha256` authorizes execution | no stored-token authority |
| No file contains `templates/agents/ship.md.tmpl` or `.github/agents/ship.md` | no phantom paths |
| No file contains a literal `<resolved-or-default>` or any other angle-bracket placeholder inside a fenced command | commands are runnable |
| The manifest contains **exactly one** entry whose `path` is `.github/agents/_ship.agent.md` | the D11 target is unambiguous |
| That entry's `checksum` equals the SHA-256 of the mirror's canonical bytes | D11 parity |

### Parity criteria - `PAR-1` ... `PAR-6b`

| ID | Criterion |
|---|---|
| `PAR-1` | The mirror section's heading text matches the template's apart from the step number, and the heading level is identical |
| `PAR-2` | The section occupies the equivalent position: last before the task-execution step in both files |
| `PAR-3` | Every non-placeholder line of the section body is byte-identical after canonicalization |
| `PAR-4` | Every uppercase `{{NAME}}` placeholder in the template section has a rendered value in the mirror section |
| `PAR-5` | No placeholder syntax survives in the mirror |
| `PAR-6a` | The manifest entry's `checksum` equals the SHA-256 of the mirror's canonical bytes |
| `PAR-6b` | The manifest entry's `template` field is left **unchanged** at its current literal value `global agent definition` |

**`PAR-6b` states the truth about this entry.** The manifest's Ship-agent entry
does not name a `.tmpl` path; its `template` field carries the literal sentinel
`global agent definition`, marking a global agent definition rather than a
rendered-from-template artifact. Requiring the field to name the authoritative
template would be **unsatisfiable** for this entry and would turn activation
into an unreviewed manifest-contract change. Activation therefore refreshes
`checksum` and **nothing else** in that entry.

`PAR-1` deliberately permits the step numbers to differ - `Step 2` in the
template, `Step 1.5` in the mirror - because the two files' step sequences
already differ. Semantic parity is asserted; byte parity of the heading is not.

These names replace the earlier `P4`-prefixed criterion labels, which collided
with the unit alias `P4` used in the governing decision. **Immutable
review-history artifacts, policy IDs and finding severity IDs are not
renamed.**

## Rollback

Rollback is a `git revert` of the single ACTIVATE commit, restoring the
template, the mirror and the manifest entry together.

**It requires FRESH, LIVE operator approval, obtained immediately before the
revert command is issued, and bound to the exact activation commit SHA.** The
approval must name that SHA. It is re-validated in the moment the command is
about to run; an approval obtained earlier in the session, or for a different
SHA, is not an approval. If the operator is unreachable, dark or AFK, the agent
**halts and reports** - it does not revert. Proceeding without that approval is
a P-005 violation. **There is no unconditional revert path anywhere in this
unit.**

Before any rollback the agent enters **careful mode with frozen scope**: the
only paths it may touch are the three activation files, and the only command it
may issue is the approved revert.

## Tasks

| ID | Role | Files | Size | Complexity |
|---|---|---|---|---|
| `181.001-T` | RED | `tests/test_harness_read.py`, `tests/test_harness_surfaces.py`, `tests/test_harness_resolve_cli.py` | M | high |
| `181.002-T` | PREPARE | `src/autoharness/harness_read.py` | M | high |
| `181.006-T` | PREPARE | `src/autoharness/harness_surfaces.py` | M | high |
| `181.007-T` | PREPARE | `src/autoharness/cli.py` | S | medium |
| `181.003-T` | PREPARE | `tests/fixtures/ship_harness_generation.md`, `tests/test_ship_harness_activation.py` | S | medium |
| `181.004-T` | VERIFY | evidence only | S | medium |
| `181.005-T` | ACTIVATE | `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`, `.autoharness/harness-manifest.yaml` | M | high |

Execution order is `181.001-T` -> `181.002-T` -> `181.006-T` -> `181.007-T` ->
`181.003-T` -> `181.004-T` -> `181.005-T`. **No task exceeds three files.**

### `181.001-T` (RED) - all failing tests, no external fixtures

Owns **every** test module this unit adds. It runs **first**, so it must not
depend on anything a later task produces.

* **Fixtures are created programmatically**, in `tempfile.TemporaryDirectory`,
  by helper functions inside the test modules. `181.001-T` reads no file from
  `tests/fixtures/`, so it does not depend on `181.003-T`.
* **Imports are lazy and local to each test method**, not at module scope:

```python
def _load(name):
    import importlib
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise AssertionError(
            f"{name} is not implemented yet: {type(exc).__name__}"
        ) from None
```

  An absent module therefore produces an **`AssertionError` inside a running
  test**, not a collection-time `ImportError` that aborts discovery. The RED
  phase is a set of intentional assertion failures over a suite that still
  collects cleanly.
* Coverage: every row of the classification table; every row of the aggregation
  table `A1`-`A6`; every reason code in the closed set; both platform adapter
  branches through the deterministic mock; the lexical rejection list; the
  sibling-prefix case; identity mismatch and race; every bound; the JSON
  document's field presence, types, ordering and redaction; `inputs_sha256`
  determinism, self-exclusion and absence sentinels; and all three CLI exit
  codes.

Targeted RED command:

```
PYTHONPATH=src python -m unittest tests.test_harness_read tests.test_harness_surfaces tests.test_harness_resolve_cli
```

### `181.002-T` (PREPARE) - the secure-read primitive

One file: `src/autoharness/harness_read.py`. Delivers the platform adapter
interface, both platform implementations, lexical rejection, component-wise
containment, handle-bound traversal, pre/post identity verification and the
bounds table. **No resolver logic and no backlog knowledge.**

### `181.006-T` (PREPARE) - the resolver core

One file: `src/autoharness/harness_surfaces.py`. Delivers the public types, the
frozen environment snapshot and backlog-root validation, record lookup, the
total declaration function, the classification table, rendering from the
manifest's top-level `variables_used`, the `A1`-`A6` aggregation and the digest
construction. It reads the filesystem **only** through `harness_read`.

### `181.007-T` (PREPARE) - the CLI and JSON adapter

One file: `src/autoharness/cli.py`. Adds the `harness resolve` subcommand, the
argument surface, the dataclass-to-JSON projection, stable ordering, redaction
and the exit-code mapping. **The surface this plan activates is owned, in this
plan, by this task.** There is no unnamed follow-on and no deferred CLI work.

### `181.003-T` (PREPARE) - agent-text fixtures and structural tests

Runs **after** the executable boundary exists, because the canonical section
text it freezes contains the real CLI invocation. Owns the canonical expected
section text for both Ship files and the structural tests that enforce the
assertion table above. **Contains no resolver logic.**

### `181.004-T` (VERIFY) - evidence, including proof the structural tests are RED

Evidence only; no production file. It produces:

1. GREEN over the resolver, primitive and CLI test modules;
2. evidence covering **every** classification-table row, **every** aggregation
   row and **every** containment failure mode;
3. **proof that the activation-structural tests from `181.003-T` are RED** -
   they must fail **before** `181.005-T` runs, because the sections they assert
   do not exist yet.

```
PYTHONPATH=src python -m unittest tests.test_harness_read tests.test_harness_surfaces tests.test_harness_resolve_cli
PYTHONPATH=src python -m unittest tests.test_ship_harness_activation
PYTHONPATH=src python -m unittest discover -s tests
python -m py_compile src/autoharness/cli.py
```

The second command is expected to **fail** at this task. That failure is the
evidence. Revision 10 placed activation verification before activation and
called it verification; here the pre-activation run is explicitly a RED proof
and the post-activation run is the verification.

### `181.005-T` (ACTIVATE) - the three-file atomic activation

Performs the edits above, then **runs the verification after the change**:

```
PYTHONPATH=src python -m unittest tests.test_ship_harness_activation
PYTHONPATH=src python -m unittest discover -s tests
```

The first must now pass - the same tests that were RED at `181.004-T`. The
second is the full canonical suite. The task carries the complete fresh-live
SHA-bound approval text and the careful/freeze-scope safety mode before any
revert.

## Out of scope

The harness-architect actor's content; the P-004 gate implementation; any
operation registry, result model or transport; any MCP surface; any change to
the canonical commands; any change to P-002, P-004, gate semantics, grants,
`--force` or waivers; any consolidation onto the future `185-S` primitive
substrate.

## Risks

| Risk | Mitigation |
|---|---|
| The resolver becomes a second source of truth about readiness | It persists nothing; recomputation is the only freshness carrier |
| Path checks pass but the file read races | Handle-bound traversal; pre/post identity and size verification; disagreement -> `UNRESOLVED` |
| A platform lacks the security primitive and the tool degrades silently | `PLATFORM_INVARIANT_UNAVAILABLE` -> `UNRESOLVED`; there is no unchecked fallback read |
| Security-critical branches are skipped on the CI platform | Both platform branches are exercised through a deterministic injected mock that cannot skip |
| `NO_HARNESS` is silently treated as ready | Distinct state, exit code and reason code; both non-ready states halt before partition |
| A vacuous ready is produced from a malformed shipment | `A2`/`A3` precede `A4`, so any invalid declaration or surface dominates |
| The activation leaves the manifest stale | `D11`: the manifest is a member of the commit and the rollback unit, parity verified after refresh |
| The activation edits a file that does not exist | Every path is verified present in this revision; structural tests assert the phantom paths appear nowhere |
| The mirror insertion creates a duplicate or ambiguous gate | Exact-count assertions on both headings, and `Step 1.5` renumbers nothing |
| Rollback destroys working state without consent | Fresh, live, SHA-bound approval revalidated immediately before the command; careful mode with frozen scope; halt if unreachable |

## Hardening review

### Adversarial questions

* *Can a task declare a surface outside the workspace?* No - lexical rejection
  precedes any filesystem access, and containment is component-wise on an
  already-open handle.
* *Can a symlink or junction redirect a read below a canonical root?* No -
  `O_NOFOLLOW` per component on POSIX, `FILE_FLAG_OPEN_REPARSE_POINT` plus
  attribute rejection and `GetFinalPathNameByHandle` containment on Windows.
* *Can the path be swapped between the check and the read?* No - there is no
  gap: the check is performed on the handle the bytes are read from, and
  identity is re-verified afterwards.
* *Can an ambient environment variable silently redirect the backlog root?*
  It can redirect it, as it always could - but only once, through a frozen
  allowlist; the result must lie under the workspace; and the snapshot is bound
  into `inputs_sha256`, so the redirection is visible in the evidence.
* *Can a caller supply a readiness answer?* No - the resolver derives
  everything from the shipment record, task labels, the manifest and the two
  file trees. There is no caller-supplied declaration.
* *Can a checkpoint authorize execution after a crash?* No - the stored digest
  is compared, never trusted, and the resolver runs before the cursor is
  restored.
* *Can a shipment with no harness needs be mistaken for a failure?* No -
  `NO_SURFACES_REQUIRED` is an explicit ready state with `exit 0` and empty
  `surfaces`.
* *Can this unit's own tasks bootstrap themselves?* Yes - the actor is already
  installed and conformant in this publication branch, so `187-S`'s own
  P-002/P-004 harness generation has a real producer. That is why `191-S` had
  no subject and why this shipment is a genuine root.

### Blast radius

The Ship agent template and its installed mirror; the harness manifest; two new
public Python modules; one new CLI subcommand. Every future shipment traverses
the installed phase, so a defect here is systemic - which is why the activation
is one reviewed atomic commit with a verified manifest refresh and an
approval-gated rollback.

### Verification floor

Targeted RED and GREEN on the three resolver test modules; a demonstrated RED
then GREEN transition on the activation-structural module across the activation
boundary; the full canonical suite; the canonical compile command; and evidence
covering every classification-table row, every aggregation row and every
containment failure mode.
