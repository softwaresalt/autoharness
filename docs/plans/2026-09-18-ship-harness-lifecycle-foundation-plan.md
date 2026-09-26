---
title: "Ship pre-task harness-generation lifecycle"
description: "Revision 12 current-state implementation plan for secure harness-surface resolution and Ship activation."
doc_type: plan
source: docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
date: 2026-09-20
plan_id: ship-harness-lifecycle-foundation
plan_role: active
revision: 12
revision_scope: coherent-current-state-rewrite-after-attempt-10
status: pending-independent-review
review_manifest: docs/reviews/2026-09-18-ship-harness-lifecycle-foundation-plan-review.md
latest_independent_attempt: 10
latest_independent_verdict: FAIL
latest_attempt_artifact: docs/reviews/review-history/2026-09-18-ship-harness-lifecycle-foundation-plan-review-attempt-10.md
latest_attempt_commit: e363aebb
awaiting_attempt: 11
publication_eligible: false
requires_plan_hardening: yes
hardening_status: integrated
feature_id: 181-F
shipment_id: 187-S
source_stash_id: 76EBDE6D
governing_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
governing_decision_revision: 9
labels:
  - ship-lifecycle
  - harness-architect
  - secure-reader
  - resolver
  - p-004
---

# Ship pre-task harness-generation lifecycle

## Current state and authority

This revision is one coherent current-state contract. It replaces revision 11; it is not a correction log. Independent attempt 10 reviewed revision 11 and recorded immutable **FAIL / BLOCK** at commit `e363aebb` with findings `S53`–`S68`. Revision 12 addresses those findings but asserts no closure and no verdict. The mutable review manifest is the sole current review pointer and must show revision 12 awaiting independent attempt 11.

Ship commit `d8b04112` directly fixed P-004's impossible global RED quantifier. Current policy requires scoped RED evidence only for the harness tests generated for the current implementation task. This plan does not modify the P-004 plan or review, does not perform or schedule P-004 attempt 03, and preserves all P-004 blocked language. The P-004 plan remains blocked on its stated prerequisites.

`187-S` is queued, dependency-free and labeled `dag-root`. Root status is graph metadata, not claim authority. Ordinary P-001, P-002, P-004, review, CI and closure gates still apply. The harness-architect actor is already installed and behaviorally conformant through `07b4be79`, `1cb0dc81`, `b8ac632a` and the current policy correction `d8b04112`; no corrective `191-S` work is part of this plan.

`181.001-T` is retired and archived as superseded before execution. It was never claimed, done or shipped. A standalone RED-test task is redundant and creates import-laundering pressure; harness-architect instead generates and observes a valid task-scoped harness immediately before every live implementation task.

## Outcome and boundaries

This feature delivers:

1. a fail-closed secure byte reader for workspace and autoharness trust roots;
2. a deterministic shipment/member/declaration/manifest resolver;
3. versioned JSON schemas and schema-contract registration for the resolver result;
4. a CLI adapter whose post-parse JSON contract exactly reflects the resolver result; and
5. a three-file Ship activation that resolves the actor, obtains scoped RED evidence and prevents checkpoint restoration before fresh resolution.

It does not implement the later P-004 observation gate, change P-002/P-004 policy, add an MCP transport, generalize the secure reader for `185-S`, modify harness-architect, claim or ship `187-S`, run attempt 11, or touch source/templates/tests during Stage.

## Task-scoped harness invariant

Before each implementation task, Ship invokes harness-architect for that task's declared acceptance scenario and unique marker. The generated test module must import and collect successfully. The expected-RED roster contains only marker-bearing assertion failures for the current task.

* Import, collection, syntax, parser-escape and unavailable-platform errors are `NO_OBSERVATION`; they are never caught and relabeled as RED.
* A generated harness may use `importlib.util.find_spec` or filesystem assertions to test the required existence of a not-yet-created module without causing collection failure.
* Characterization assertions may pass, but they are recorded separately and excluded from the expected-RED roster.
* The observed marker, command, failing assertion and task ID are retained as evidence. A missing marker, zero expected failures, or any unexpected error halts before implementation.
* After the task, the same marker must be green. Harness generation is not a standalone backlog task.

## Secure-reader contract

### Public API

`src/autoharness/harness_read.py` exposes only the following public contract:

* `PlatformFamily`: `POSIX`, `WINDOWS`.
* `TrustRoot`: `WORKSPACE`, `AUTOHARNESS`.
* `ReadStage`: `LEXICAL`, `BUDGET`, `ROOT_RESOLVE`, `ROOT_OPEN`, `COMPONENT_OPEN`, `PRE_SNAPSHOT`, `READ`, `POST_SNAPSHOT`, `CLOSE`.
* `ReadErrorCode`: `LEXICAL_INVALID`, `ROOT_RESOLVE_FAILED`, `ROOT_OPEN_FAILED`, `PATH_NOT_FOUND`, `REPARSE_POINT`, `NOT_REGULAR_FILE`, `OUTSIDE_TRUST_ROOT`, `FILE_SIZE_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_COUNT_LIMIT`, `COMPONENT_LIMIT`, `IDENTITY_MISMATCH`, `RACE`, `IO`, `SESSION_CLOSED`, `PLATFORM_INVARIANT_UNAVAILABLE`.
* Frozen `ReadLimits` with defaults `max_file_bytes=4*1024*1024`, `max_total_bytes=32*1024*1024`, `max_files=256`, `max_components=32`, `chunk_bytes=64*1024`.
* Frozen `ReadUsage`, `FileIdentity`, `FileSnapshot`, `ReadError`, `ReadResult` and `CloseResult`.
* `TraversalAdapter` protocol. Platform adapters and syscall/API tables remain private.
* Keyword-only `open_secure_reader(*, workspace_root, autoharness_root, limits=None, adapter=None) -> SecureReader`.
* `SecureReader.read_bytes(root, relative_path)`, read-only `usage`, and idempotent `close() -> CloseResult`.

`ReadResult.data` is bytes only on success. Any error returns no data. Runtime filesystem failures are typed; no exception text, absolute user path or machine identifier enters a public diagnostic.

### Lexical validation

Lexical validation runs before budget mutation, root opening or any adapter call. It tokenizes both slash styles and rejects:

* empty input, absolute POSIX paths, drive-qualified paths, UNC/device/extended prefixes;
* environment or home expansion syntax;
* empty, `.` or `..` components;
* NUL and all control characters;
* Windows device stems even with extensions, alternate data streams, and trailing-dot/trailing-space aliases; and
* more than 32 components.

A lexical rejection leaves `ReadUsage` unchanged and records `LEXICAL_INVALID` or `COMPONENT_LIMIT` at `ReadStage.LEXICAL`.

### Session budgets and bounded read

Each lexically valid request claims one file slot before root/adapter work. The claim is never refunded. A lazy handle is retained for each trust root used by the session. After a regular-file pre-snapshot, the reader reserves the exact advertised size against file and aggregate byte limits; that reservation is never refunded even if a later stage fails.

Reads request no more than 64 KiB at a time and never retain bytes beyond the advertised pre-size. After exactly that size, the reader performs one one-byte EOF probe. Early EOF, probe data, size/version change or an inconsistent pre/post snapshot is `RACE`; identity change is `IDENTITY_MISMATCH`; ordinary read failure is `IO`. Post-snapshot is mandatory. Every failure discards accumulated bytes.

### POSIX adapter

`src/autoharness/_harness_read_posix.py` uses an injectable syscall table. It opens the filesystem anchor and then opens every canonical trust-root and descendant component relative to an already held parent descriptor. Required flags are `O_NOFOLLOW`, `O_DIRECTORY` where applicable and `O_CLOEXEC`; `dir_fd` support is mandatory. After the anchor, no absolute full-root or descendant path is opened. The final descriptor must be regular. Missing flags or capabilities fail `PLATFORM_INVARIANT_UNAVAILABLE`; no `Path.open`, built-in `open`, `read_text` or path-stat fallback exists.

POSIX identity is `(st_dev, st_ino)` and version is `(st_size, st_mtime_ns, st_ctime_ns)` from held descriptors.

### Windows adapter

`src/autoharness/_harness_read_windows.py` uses an injectable API table with mandatory bindings. It establishes a verified trust-root handle, then opens every descendant one component at a time relative to the parent through `NtCreateFile` `RootDirectory` with `OBJ_DONT_REPARSE` and `FILE_OPEN_REPARSE_POINT`. Every handle is queried for reparse state and final path before use. Missing APIs or guarantees fail closed.

Windows identity is `(volume_serial, file_index_high, file_index_low)` and version is `(size, last_write_time, change_time)`. Same-size in-place mutation is therefore observable. No unchecked string-path descendant open or pathlib/stat fallback is permitted.

### Ownership and cleanup

The session owns every adapter handle it acquires. Close occurs in exact reverse acquisition order. Close failures are typed at `ReadStage.CLOSE`; cleanup continues for remaining handles. `close()` is idempotent, and a read after close returns `SESSION_CLOSED` without adapter activity.

## Resolver and aggregation contract

### Public result

`src/autoharness/harness_surfaces.py` exposes a keyword-only resolver and frozen result types. `HarnessResolution` has exactly these fields in this order:

1. `schema_version` — literal string `1.0.0`;
2. `state`;
3. `reason_code`;
4. `exit_code`;
5. `shipment_id`;
6. `backlog_root`;
7. `surfaces`;
8. `declarations`;
9. `inputs_sha256`;
10. `diagnostics`.

Paths are redacted and root-relative. Declarations sort by task ID, surfaces by surface ID, and diagnostics by deterministic generation order.

### Request, root and record lookup

One resolver invocation creates one `SecureReader` and uses its aggregate budget throughout.

`custom_fields.items` must be a list of 1..512 unique strings. IDs are validated before lookup. Supported members are explicit feature IDs and task IDs only; duplicates and every other kind are rejected with closed member reason codes. At least one explicit task member is required. Feature members are validated and digested but never expand child tasks. A task-only shipment is valid.

For the shipment and every member, the resolver consults both exact candidates:

* `<backlog-root>/queue/<id>.md`
* `<backlog-root>/archive/<id>.md`

Both present and stable-absent observations enter the ledger. Exactly one candidate must exist. The selected frontmatter `id` must equal the requested ID, and `artifact_type` must agree with the ID suffix. Closed membership reasons are `MEMBERS_INVALID`, `MEMBERS_EMPTY`, `MEMBERS_TOO_MANY`, `MEMBER_ID_INVALID`, `MEMBER_DUPLICATE`, `MEMBER_NOT_FOUND`, `MEMBER_AMBIGUOUS`, `MEMBER_RECORD_INVALID`, `MEMBER_ID_MISMATCH`, `MEMBER_KIND_UNSUPPORTED`, and `NO_TASK_MEMBERS`; shipment equivalents are separately named.

### Declarations

Each explicit task must declare exactly one supported `harness-surface:<surface-id>` label or an explicit `harness-surface:none`. Missing, duplicate, malformed or mixed declarations are invalid. Feature members never declare surfaces. The surface union is deduplicated and sorted.

### ManifestSnapshot

One `ManifestSnapshot` loader is the sole YAML and projection authority. It runs only after request/root/shipment/membership/member records and declarations are valid, and only when the surface union is nonempty. A global manifest failure produces diagnostics but no synthetic per-surface rows.

For each surface, classification order is fixed:

1. zero manifest path matches -> `MISSING` / `MANIFEST_ENTRY_NOT_FOUND`;
2. more than one path match -> `INVALID` / `MANIFEST_ENTRY_AMBIGUOUS`;
3. one path match with template mismatch -> `INVALID` / `MANIFEST_TEMPLATE_MISMATCH`;
4. then classify template read/render and installed-file state.

Rendering uses the manifest's one top-level variables mapping, UTF-8 and canonical LF newlines. Missing installed bytes are `MISSING`; unresolved variables, unreadable templates or invalid projections are `INVALID`; rendered/checksum disagreement is `STALE`; both render equality and checksum equality are required for `PRESENT`.

### Observation ledger and digest

Every exact present or absent candidate consulted is ledgered. After a provisional result, the resolver re-observes the ledger through the same trust-root session. Any disagreement dominates all other outcomes as `UNRESOLVED / 2 / INPUT_CHANGED_DURING_RESOLUTION`. When mutation occurs, both first and recheck observations are bound.

After a syntactically valid invocation, `inputs_sha256` is always 64 lowercase hexadecimal characters. Its domain-separated canonical preimage binds:

* `shipment_id` and request/root/environment observations;
* both queue/archive candidates for the shipment;
* both candidates for every member, including stable absence;
* raw selected shipment, feature and task records;
* manifest, template and installed-file observations;
* normalized declarations; and
* the final evidence projection, excluding only `inputs_sha256` itself.

Stable deterministic ordering is mandatory.

### Reducer precedence

The reducer stops at the first applicable class:

1. mutation -> `UNRESOLVED / 2 / INPUT_CHANGED_DURING_RESOLUTION`;
2. request, root, shipment, membership or member-record error -> `UNRESOLVED / 2`;
3. declaration error -> `UNRESOLVED / 2`;
4. valid task set with empty surface union -> `HARNESS_READY / 0 / NO_SURFACES_REQUIRED`;
5. global manifest error -> `UNRESOLVED / 2`;
6. any `INVALID` surface -> `UNRESOLVED / 2`;
7. any `MISSING` or `STALE` surface -> `NO_HARNESS / 1`;
8. all surfaces `PRESENT` -> `HARNESS_READY / 0 / ALL_SURFACES_PRESENT`.

## Schema and CLI contract

`181.017-T` creates `schemas/harness-resolution.schema.json` and `schemas/harness-resolution/1.0.0.schema.json` and registers them in `src/autoharness/schema_contracts.py`. The schemas are semantically identical, use `additionalProperties: false`, closed enums and `oneOf` branches for state/reason/exit consistency. Runtime tests prove sorting.

CLI usage is:

```text
PYTHONPATH=src python -m autoharness.cli harness resolve --workspace . --shipment 187-S --json
```

PowerShell operational equivalent:

```powershell
$env:PYTHONPATH='src'; python -m autoharness.cli harness resolve --workspace . --shipment 187-S --json
```

Missing, unknown or malformed arguments use normal redacted parser usage on stderr and exit 2 outside resolver JSON. `--help` remains normal help. After successful parse, `--json` emits exactly one result document and exits with `result.exit_code`; human output is bounded. The direct caller and CLI share resolver semantics, but no byte-identical direct-caller claim is made.

## Ship activation contract

The activation owns exactly:

1. `templates/agents/_ship.agent.md.tmpl`;
2. `.github/agents/_ship.agent.md`;
3. `.autoharness/harness-manifest.yaml`.

The template updates the existing `### Step 2: Harness Generation (P-002 / P-004)` between template-specific anchors. The mirror inserts `### Step 1.5: Harness Generation (P-002 / P-004)` immediately before its existing `### Step 2: Task Execution Loop`. Tests assert per-file anchors and semantic rendered-body parity, not equal numbering or placement.

The canonical body resolves the actor surface first. Exit 0 invokes harness-architect for applicable implementation tasks and requires the current task's valid marker-bearing RED evidence before partition. Exit 1 halts as `NO_HARNESS`; exit 2 halts as `UNRESOLVED`; they remain distinct.

Checkpoint handling is replacement, not additive correction. Remove the template's current early sentence that restores memory context before checkpoint validation. In both template and mirror, replace the owner-confirmed restore step so it loads and validates the payload, extracts a nonempty `shipment_id`, executes a fresh resolver, and halts on exit 1 or 2 before restoring cursor, phase or next-action intent. Tests prove the prior cursor-first text/path is absent and no later bypass exists.

Refresh only the existing manifest entry for `.github/agents/_ship.agent.md`; preserve its template sentinel and update checksum/note for the exact installed bytes.

## Serial DAG and file budgets

`181.001-T` is archived and is not a shipment member. Live order is:

```text
181.002-T -> 181.008-T -> 181.009-T -> 181.010-T -> 181.011-T ->
181.012-T -> 181.006-T -> 181.013-T -> 181.014-T -> 181.015-T ->
181.016-T -> 181.017-T -> 181.007-T -> 181.003-T -> 181.004-T ->
181.005-T
```

`181.007-T` explicitly depends on both `181.016-T` and `181.017-T`; the serial edge from `181.016-T` to `181.017-T` keeps the graph acyclic.

| Task | Concern | Exact repository file budget | Estimate | Size / complexity | Harness marker |
|---|---|---|---:|---|---|
| `181.002-T` | public read contracts + lexical validation | `src/autoharness/harness_read.py`; `tests/test_harness_read.py` | 90m | S / medium | `AH181002_READ_CONTRACT_LEXICAL` |
| `181.008-T` | budgets + bounded read orchestration | same two files | 105m | S / medium | `AH181008_READ_BUDGETS` |
| `181.009-T` | POSIX adapter | `src/autoharness/_harness_read_posix.py`; `tests/test_harness_read_posix.py` | 90m | S / medium | `AH181009_POSIX_HANDLE_WALK` |
| `181.010-T` | Windows bindings + root | `src/autoharness/_harness_read_windows.py`; `tests/test_harness_read_windows.py` | 100m | S / medium | `AH181010_WINDOWS_ROOT_BINDINGS` |
| `181.011-T` | Windows traversal/snapshots/read | same two Windows files | 110m | S / medium | `AH181011_WINDOWS_PARENT_TRAVERSAL` |
| `181.012-T` | read integration/error mapping/cleanup | `src/autoharness/harness_read.py`; `tests/test_harness_read.py` | 90m | S / medium | `AH181012_READ_INTEGRATION_CLEANUP` |
| `181.006-T` | resolver facade/reason registry | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces.py` | 75m | S / medium | `AH181006_RESOLVER_CONTRACTS` |
| `181.013-T` | backlog/shipment/member/declarations | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces_records.py` | 100m | S / medium | `AH181013_RECORD_MEMBERSHIP` |
| `181.014-T` | manifest/render/classification | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces_manifest.py` | 100m | S / medium | `AH181014_MANIFEST_SNAPSHOT` |
| `181.015-T` | ledger/recheck/digest | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces_digest.py` | 110m | S / medium | `AH181015_LEDGER_DIGEST` |
| `181.016-T` | final resolver/reducer | `src/autoharness/harness_surfaces.py`; `tests/test_harness_surfaces.py` | 90m | S / medium | `AH181016_RESOLVER_REDUCER` |
| `181.017-T` | schema mirrors + registration | two schema files; `src/autoharness/schema_contracts.py`; `tests/test_harness_resolution_schema.py` | 75m | S / medium | `AH181017_SCHEMA_CONTRACT` |
| `181.007-T` | CLI adapter | `src/autoharness/cli.py`; `tests/test_harness_resolve_cli.py` | 90m | S / medium | `AH181007_CLI_ENVELOPE` |
| `181.003-T` | Ship fixtures/assertions | fixture + `tests/test_ship_harness_activation.py` | 90m | S / medium | `AH181003_SHIP_TEXT` |
| `181.004-T` | pre-activation evidence | no repository files | 60m | XS / low | evidence roster |
| `181.005-T` | activation + manifest | the three activation files above | 110m | S / medium | `AH181005_SHIP_ACTIVATION` |

## Runtime verification matrix

Ship records exact commands and outcomes; Stage runs none.

```text
PYTHONPATH=src python -m unittest tests.test_harness_read tests.test_harness_read_posix tests.test_harness_read_windows
PYTHONPATH=src python -m unittest tests.test_harness_surfaces tests.test_harness_surfaces_records tests.test_harness_surfaces_manifest tests.test_harness_surfaces_digest
PYTHONPATH=src python -m unittest tests.test_harness_resolution_schema tests.test_harness_resolve_cli
PYTHONPATH=src python -m unittest tests.test_ship_harness_activation
PYTHONPATH=src python -m unittest discover -s tests
```

The PowerShell equivalent prefixes each command with `$env:PYTHONPATH='src';`. Platform adapter tests are injected and must positively prove both adapter paths executed; unsupported live-host facilities do not convert into skips. Before `181.005-T`, its scoped structural marker must be valid RED. After activation, the same marker and targeted suite must be green, followed by the whole suite with no regression.

## Rollback

Activation is one three-file commit. Rollback is only `git revert <activation-sha>`. Approval must be fresh live non-repository operator/session evidence bound to the exact activation SHA immediately before revert. No fourth repository file, task-record mutation or pre-recorded approval is permitted. Without valid approval, halt and report. After an approved revert, rerun targeted structural verification and manifest checksum validation.

## Operational closure

A successful implementation requires all task-scoped markers green, both schema mirrors registered and equivalent, deterministic resolver output, exact shipment membership, no external dependency on `187-S`, three-file activation parity, canonical command evidence, and independent plan-review passage. This revision itself supplies none of those runtime or review verdicts. Attempt 11 is not created or run here.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| path race or reparse escape | handle-relative traversal, mandatory capabilities, pre/post identity and version checks |
| budget bypass by growth | exact reservation, bounded chunks and one-byte EOF probe |
| mutation during resolution | same-session ledger recheck dominates as `INPUT_CHANGED_DURING_RESOLUTION` |
| duplicate or implicit membership | explicit unique list, exact queue/archive candidates, no feature expansion |
| manifest failure duplicated per surface | one loader; global failure emits no surface rows |
| invalid RED evidence | marker-only assertion roster; all import/collection/syntax errors are `NO_OBSERVATION` |
| checkpoint bypass survives | replace early restore paths and assert old sequence absent |
| asymmetric Ship files drift | per-file anchors plus semantic body parity |
| rollback expands scope | fresh external approval and exact-SHA revert only |
| task exceeds two hours | serial split, explicit estimates, no high-complexity live task |

## Out of scope

P-004 plan/review edits or attempt 03; attempt 11 execution; source/template/test implementation by Stage; harness-architect changes; MCP transport; generalized `185-S` safe primitives; shipment claim/ship/PR activity; changes outside the listed plan, review manifest, decision and `181`/`187` backlog carriers.
