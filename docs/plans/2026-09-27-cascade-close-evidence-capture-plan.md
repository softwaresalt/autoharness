---
title: "Automatic, fail-closed CASCADE close-evidence capture"
description: "Replace the agent-discretionary CASCADE close audit trail with an autoharness-owned command that captures the fresh classifier verdict, the out-of-manifest snapshot, and the raw bounded, redacted backlogit close output into a committed evidence record, plus a closure-evidence gate that refuses CASCADE closure without that record."
doc_type: plan
status: reviewed
review_record: docs/reviews/2026-09-27-cascade-close-evidence-capture-plan-review.md
created: 2026-09-27
source_stash: 008F3BCF
source_deliberation: docs/decisions/2026-09-27-close-evidence-frontmatter-context-tier-staging-deliberation.md
provenance: "175-S / 167-F, PR #458 (merge 985e3990), closure PR #459, close commit 5cc5371a, condition operator-accepts-175s-cascade-evidence-deviation"
requires_plan_hardening: "yes"
---

# Automatic, fail-closed CASCADE close-evidence capture

## Problem Frame

P-015 permits the destructive `backlogit shipment ship` cascade only when
`classify_shipment_close_path` (`src/autoharness/gates/shipment_closure.py`) returns
`CASCADE`. The Cascade Close Sub-Procedure in
`templates/skills/shipment-reconcile/SKILL.md.tmpl` (mirrored at
`.github/skills/shipment-reconcile/SKILL.md`) tells the agent to do five things:

* re-run the classifier immediately before the call;
* fingerprint the out-of-manifest descendants;
* invoke the cascade;
* check `returned_ids`, the two-set `allowed_ids` / `required_ids` gate, `parent_id`
  preservation, and baseline invariance;
* write a report.

All of it is prose. During the 175-S close (commit `5cc5371a`), Ship kept none of
the raw evidence. Closure PR #459 halted `BLOCKED` and needed an operator deviation.
The evidence cannot be reproduced after a cascade, because the cascade mutates the
very `status` fields the snapshot records. Nothing in the write-time
`closure-evidence` gate (`src/autoharness/cli.py`,
`src/autoharness/gates/closure_contract.py`) knows which close path ran, so a
missing record is never refused.

## Requirements Trace

| # | Requirement (stash `008F3BCF` / deliberation D-A*) | Unit(s) |
|---|---|---|
| R1 | Record the pre-close classifier verdict automatically, from a fresh re-run | A2 |
| R2 | Record the out-of-manifest snapshot (IDs, locations, content hashes, declared statuses, linked deliberations) before the close | A2 |
| R3 | Record the raw close stdout, stderr, and exit code, bounded and redacted | A1b, A3a, A3 |
| R4 | The evidence file is written before and after the close; if the pre-close write fails, nothing is invoked | A1b, A2, A3 |
| R4a | An interrupted, concurrent, or ambiguous close is detectable and never silently retried (hardening H-B1/H-B2, review cycle 1) | A1b, A3 |
| R5 | The closure-evidence gate refuses a closure whose close path lacks a valid record | A1, A4 |
| R6 | SAFE_CLOSE (D-A3, amended by review cycle 1 — Stage-recommended, pending operator confirmation): verdict record via `--classify-only`, required by the gate | A2, A4 |
| R7 | Surfaces updated: shipment-reconcile (template and mirror), operational-closure (template and mirror), Ship agent (template and mirror), docs | A5, A6, A7 |
| R8 | Upstream half as a portable, non-blocking backlogit request (D-A1) | A7 |
| R9 | Retention and location (D-A2): committed at `docs/closure/evidence/`, and closure discovery is unaffected | A1, A4 |

## Implementation Units

Harness-surface labels: code-bearing units carry `harness-surface:harness-architect`
(P-004 per-task harness generation applies), and docs- or template-only units carry
`harness-surface:none`.

Layering (review cycle 1, AS-F07): the read-only, gate-facing contract and validator
live in `src/autoharness/gates/cascade_evidence.py`. Every write and every subprocess
lives in the new command package `src/autoharness/shipment_close/`, which the gate
never imports. New modules must not restate a closure filename (`*closure.md`,
`post-merge-closure`) outside the contract-derived form, so
`tests/test_closure_contract_nondrift.py` stays green.

### A1 — Evidence record contract and validator (read-only)

* **Files:** `src/autoharness/gates/cascade_evidence.py` (new), and
  `tests/test_cascade_evidence_contract.py` (new).
* **Changes:**
  * `EVIDENCE_SCHEMA_VERSION = 1`.
  * `build_evidence_path(workspace_root, shipment_id, feature_id)` builds
    `docs/closure/evidence/{S}-{F}-close-evidence.json` (one record per pair, for
    either close path), using `closure_contract.validate_closure_id` and
    `assert_path_within_workspace`.
  * `validate_evidence_record(record: Mapping[str, object], *, shipment_id: str,
    feature_id: str, close_path: Literal["cascade", "safe_close"]) -> list[str]`
    is the single validator. The gate and the command both use it. `cascade`
    requires `phase: post_close`, `classifier_verdict: CASCADE`, and
    `postcondition_verdict: pass`, **and** internal consistency (AS-F11):
    `invocation.exit_code == 0`, `timed_out: false`, `mutation_state: completed`,
    no `parse_error`, empty `parsed_result.returned_ids`, empty
    `unexpected_archived`, `missing_required`, and `failures[]`, and `parent_id_preserved`, `baseline_invariant`, and
    `shipment_archived_shipped` all `true`. A `pass` verdict that contradicts any
    of these is rejected. `safe_close` requires `phase: pre_close` and
    `classifier_verdict: SAFE_CLOSE`. Both require the pair to match and every
    required key to be present and well-typed.
  * `CascadeEvidenceError(Exception)` is the single error type. Exit-code
    constants `EXIT_*` (see A3) are defined here once.
* **Record shape:**
  * `schema_version`, `shipment_id`, `feature_id`, `merge_commit_sha`, `run_id`
    (uuid4 hex, fixed by the owning run), and `phase: pre_close | invoking | post_close`;
  * `tool{binary_path, binary_sha256, version_excerpt}` (A3a);
  * `pre_close{classifier_verdict, qualifying_feature_ids, shipment_record{location, sha256, declared_status}, manifest_members[{id, location, sha256, declared_status, parent_id}], out_of_manifest_descendants[{id, location, sha256, declared_status}], linked_deliberations[{id, location, sha256, declared_status}], observation_set[{id, location, sha256, declared_status}] (SAFE_CLOSE only), captured_at}`;
  * `invocation{argv_redacted, started_at, finished_at, exit_code, timed_out, mutation_state: none | completed | indeterminate, stdout{total_bytes, total_lines, sha256, capture_truncated, excerpt, redaction_applied}, stderr{...same}}`
    (both excerpts are always persisted, bounded and redacted, on success and on
    failure, because R3 requires the raw close output — AS-F09);
  * `post_close{parsed_result{shipment_status, archived_ids, returned_ids, commit_sha} | parse_error, shipment_record_status, shipment_record_archived_status, allowed_ids, required_ids, unexpected_archived, missing_required, parent_id_preserved, baseline_invariant, shipment_archived_shipped, postcondition_verdict: pass | fail, failures[]}`.
  * Serialization (Principle IX): `json.dumps(sort_keys=True, indent=2,
    ensure_ascii=False)`, LF line endings, one trailing newline, and every ID list
    sorted.
* **Tests (test-first):** the validator accepts a well-formed record for each close
  path and rejects: a missing `post_close` for `cascade`, a mismatched shipment or
  feature ID, `postcondition_verdict: fail`, a `SAFE_CLOSE` record offered for
  `cascade` (and the reverse), and an unknown `schema_version`. Serialization is
  byte-stable across two writes of the same record.
* **Posture:** test-first. **Size:** S. **Complexity:** low.

### A1b — Evidence persistence: streaming capture, redaction, lock, atomic write

* **Files:** `src/autoharness/shipment_close/__init__.py`,
  `src/autoharness/shipment_close/persist.py` (new), and
  `tests/test_shipment_close_persist.py` (new).
* **Changes:**
  * **Streaming capture:** `StreamCapture` counts bytes and lines and folds every
    byte into a SHA-256. It retains (a) a tail window of the final 64 KiB / 500
    lines plus a 4 KiB leading margin, and (b) for stdout only, an in-memory
    parse buffer of at most 1 MiB that is never persisted. Bytes past 1 MiB /
    10,000 lines are drained and hashed but not retained
    (`capture_truncated: true`). A stdout overflow makes the result unparseable
    (`parse_error: stdout exceeded capture cap`), never silently truncated JSON
    (AS-F03).
  * **Redaction:** `redact(text)` covers bearer or basic `Authorization` values;
    `key=value` credential pairs whose key is `token`, `password`, or `secret`;
    GitHub `gh[pousr]_` and `github_pat_` tokens; and `sk-` style keys. It returns
    the text and a `redaction_applied` flag. It runs over the retained tail window
    **before** the excerpt is sliced (H-B4), and over **every** persisted
    free-text field: argv, version excerpt, `parse_error`, both excerpts, and
    `failures[]` (SL-F04).
  * **Per-pair lock (SL-F01):** `acquire_pair_lock(workspace, S, F, run_id)`
    creates `.autoharness/gates/cascade-close/{S}-{F}.lock` (a gitignored
    runtime directory) with `O_CREAT | O_EXCL` (plus `O_NOFOLLOW` where
    available, following the `gates/bootstrap_grant.py` precedent), holding
    `run_id`, the PID, and `started_at`. Before creating anything, every path
    component from the workspace root to the lock directory, and to
    `docs/closure/evidence/`, is checked: it must be contained in the workspace
    and be a real directory (no symlink, junction, or reparse point). Missing
    components are created one at a time with `mkdir` and re-checked after each
    creation (SL-F06). It is held from the first
    existing-record check through the final write and released in `finally`. An
    existing lock is never broken automatically: it returns exit 7. Removing a
    stale lock is an operator action.
  * **Existing-record check** (the first action under the lock, in every mode):
    an `invoking` record → exit 7; a `post_close` record → exit 2
    (`evidence already finalized`); a `pre_close` record may be replaced.
  * **Owner transition (AS-F01):** `write_evidence_atomic(path, record, *,
    owner_run_id)` permits the owning run (the same `run_id`, holding the lock)
    to move its own record `pre_close → invoking → post_close`. It refuses any
    other writer, and it refuses any transition out of `post_close`.
  * **Atomic write:** a same-directory temp file, flushed and fsynced, then
    `os.replace`. It refuses symlinked or reparse-point targets and parent
    directories (reusing the shipment_closure helpers). On Windows the directory
    fsync is skipped (unsupported), and `os.replace` retries a sharing-violation
    `PermissionError` at most 3 times with bounded backoff. The temp file is
    removed in `finally`.
* **Tests (test-first):** a truncation boundary at 64 KiB and at 500 lines; a 2 MiB
  stream with bounded retained memory; a stdout overflow producing `parse_error`;
  a redaction case, plus a secret split across the excerpt boundary; redaction of
  `failures[]` and `parse_error`; two concurrent acquirers where exactly one
  wins and the other gets exit 7; a symlinked or junctioned lock-directory or
  evidence-directory component is refused before any file is created; the owner transition succeeds for the owning
  `run_id` and fails for a foreign one; an atomic write that leaves no partial file
  on a simulated failure and refuses a symlink target.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### A2 — Pre-close snapshot and `--classify-only`

* **Files:** `src/autoharness/shipment_close/preclose.py` (new), and
  `tests/test_shipment_cascade_close_preclose.py` (new).
* **Changes:**
  * Input validation happens before any read: `shipment_id` / `feature_id` through
    `closure_contract.validate_closure_id`, and `--sha` as a full 40-character
    lowercase hex SHA. Invalid input exits 2 and writes nothing.
  * The lock and existing-record check (A1b) run **before** classification, in
    both modes, so an `invoking` record always wins with exit 7 and can never be
    reclassified into SAFE_CLOSE (AN-F02).
  * `run_preclose(workspace, shipment_id, feature_id) -> PreCloseSnapshot`:
    * it loads the manifest from the shipment record under the detected backlog
      root (`backlog_root.py`; `.backlog/` and `.backlogit/` both present fails
      closed);
    * a shipment that is no longer open (already archived or shipped) exits 2 and
      writes no record, so a verdict record cannot be produced after the fact
      (AN-F01);
    * it runs `classify_shipment_close_path` **fresh**;
    * for CASCADE, `feature_id` must be in the classifier's
      `qualifying_feature_ids`. For SAFE_CLOSE, it must be a manifest member or
      the `parent_id` of one. Otherwise it exits 2 (AS-F08);
    * it captures location, SHA-256, declared status, and `parent_id` for the
      shipment record and for every manifest member (AS-F05);
    * it collects the linked deliberations of each qualifying feature from exactly
      the three engine sources defined in the shipment-reconcile Cascade Close
      Sub-Procedure: the literal `custom_fields.source_deliberation_id`, plus the
      description and references scanned with
      `\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b`, keeping only existing records whose
      `artifact_type` is `deliberation` (compound
      `2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`);
    * it fingerprints `out_of_manifest_descendant_ids` and linked deliberations
      (location plus SHA-256);
    * for a SAFE_CLOSE verdict it also records the **safe-close observation
      set**, each entry with its location (queue or archive), SHA-256, and
      declared status. The set is the union of:
      * the shipment-reconcile `mode: safe-close` observation set: the parent
        feature of each manifest task, plus every unshipped sibling task;
      * every out-of-manifest descendant of each manifest feature member (the
        classifier's traversal helper);
      * the linked deliberations of every feature in the set and of every
        manifest feature member, collected from the same three engine sources
        as CASCADE. A direct cascade would archive these without any qualifying
        feature existing (compound
        `2026-08-20-cascade-close-archives-out-of-manifest-linked-deliberation.md`).
      This covers task-only, partial-feature manifests, which have no manifest
      feature to traverse (AN-F07/AN-F09/AN-F01). If the observation set cannot be established,
      `--classify-only` exits 2 and writes no record. That is fail-closed, and
      it matches the skill's own safe-close, which cannot run without the set;
    * a torn or missing queue/archive member fails closed.
  * `--classify-only` writes a `phase: pre_close` record (for either verdict) and
    exits 0 for CASCADE or 3 for SAFE_CLOSE. It never mutates backlog state.
* **Tests:**
  * a CASCADE fixture writes a pre-close record with every fingerprint;
  * a task-only, partial-feature SAFE_CLOSE fixture records the parent feature and
    the unshipped siblings as the observation set;
  * a SAFE_CLOSE fixture writes a verdict record and returns exit 3;
  * a torn or duplicate member fails closed with no record;
  * a linked deliberation matched by the pattern and not by a substring;
  * an existing `invoking` record returns exit 7 even when the fixture now
    classifies SAFE_CLOSE;
  * an already-shipped shipment returns exit 2 with no record;
  * a `feature_id` outside the qualifying set returns exit 2.
* **Posture:** test-first, using the fixture builders in
  `tests/test_shipment_closure_classification.py`. **Size:** M. **Complexity:** medium.

### A3a — Bounded backlogit subprocess runner

* **Files:** `src/autoharness/shipment_close/runner.py` (new), and
  `tests/test_shipment_close_runner.py` (new).
* **Changes:**
  * `resolve_backlogit_binary(workspace) -> ResolvedBinary` reads `cli.binary` from
    `.autoharness/backlog-registry.yaml` and resolves it with `shutil.which`. It
    refuses (exit 2) when:
    * the binary is unresolved;
    * the resolved path lies inside the workspace root (a working-directory hijack
      on Windows);
    * it is a symlink or reparse point;
    * on Windows, its suffix is not `.exe`. A `.cmd`, `.bat`, or other script
      shim is refused, because batch argument parsing can reinterpret
      metacharacters even with `shell=False` (SL-F02).
  * It records the absolute path, the file's SHA-256, and a bounded, redacted
    `--version` excerpt as `tool{...}`. The spawn always uses that absolute path,
    never the bare name, and A3 re-hashes the file immediately before spawning
    (SL-F03, in-scope part). The trust model equals today's: the current skill
    already runs the first `backlogit` on PATH. Pinning a trusted absolute path
    in the registry would be a new configuration contract. It is out of scope
    under P-021 C1 and is carried as a follow-up.
  * `run_bounded(argv, *, cwd, timeout) -> BoundedRunResult` (a frozen
    dataclass) uses `subprocess.Popen` with `shell=False`, `stdin=DEVNULL`, and
    one reader thread per stream feeding A1b `StreamCapture`. The child starts in
    a new process group (`start_new_session=True` on POSIX, and
    `CREATE_NEW_PROCESS_GROUP` on Windows). On timeout it kills the group
    (`os.killpg` on POSIX; on Windows, the absolute
    `%SystemRoot%\System32\taskkill.exe /T /F /PID <pid>`, by PID only), then
    does a bounded `wait(10)`.
  * `timeout` defaults to 120 s. `--timeout` accepts 30-900 s; out-of-range values
    exit 2.
* **Tests:** a fake binary inside the workspace root is refused; a `.cmd` shim is
  refused on Windows (skipped elsewhere); a fake that sleeps past a 1 s test
  timeout is killed with `timed_out: true`; a fake emitting 2 MiB of stdout is
  drained. Test fakes are real executables outside the workspace, for example a
  tiny compiled or `sys.executable`-launched shim whose resolution is injected
  through the `ResolvedBinary` seam, never a `.cmd`. `ResolvedBinary` carries
  `argv_prefix: tuple[str, ...]`, which is `(absolute_path,)` in production and
  `(sys.executable, fake_script)` in tests. The `.exe` and containment checks
  apply to `argv_prefix[0]`. Reader threads are joined with a bounded timeout
  after the process exits.
* **Posture:** test-first. **Size:** S. **Complexity:** medium.

### A3b — Response parser and pure postcondition evaluator

* **Files:** `src/autoharness/shipment_close/postclose.py` (new), and
  `tests/test_shipment_close_postconditions.py` (new).
* **Changes:**
  * `parse_ship_response(stdout_bytes) -> ParsedResult | ParseError` parses the
    JSON-RPC 2.0 envelope from **stdout only** (backlogit logs to stderr). The
    envelope shape is characterized first: the first test step records
    `backlogit --jsonrpc shipment ship --help` and a canned envelope captured from
    a scratch fixture workspace, and both are committed as test fixtures.
  * `evaluate_postconditions(snapshot, parsed, reread) -> PostCloseResult` is
    pure, with no I/O. `reread` is a post-close read of the shipment record and
    of every fingerprinted file, supplied by A3. It computes `allowed_ids` and
    `required_ids` **exactly as defined** in the shipment-reconcile Cascade Close
    Sub-Procedure step 3, from the pre-close snapshot only (INV-P2). It evaluates
    INV-10 in full:
    * `returned_ids == []`;
    * the unexpected-artifact check and the missing-required check, each
      separately labelled and failing independently (INV-P3);
    * `parent_id` preservation for **every** manifest member, including each
      archived task, whose post-close `parent_id` (read from its archive
      location) must equal the pre-close snapshot (AS-F10);
    * byte-identical baseline invariance for every fingerprinted artifact outside
      `allowed_ids`;
    * the re-read shipment record declares `status: archived` and
      `archived_status: shipped` (AS-F04).
  * `mutation_state` is derived here: `completed` for a parsed success envelope;
    `none` only when every fingerprinted file's SHA-256 is unchanged and no
    fingerprinted ID has gained an archive-location file; otherwise
    `indeterminate`. A timeout or a non-zero exit is never read as "no mutation"
    (compound `2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`).
* **Tests:** a table-driven pass case; a non-empty `returned_ids` case; the two set
  checks failing independently (with both failing at once, both are reported);
  a moved `parent_id` on an archived manifest task and on an out-of-manifest artifact; a modified descendant giving `baseline_invariant: false`;
  a shipment record lacking `archived_status: shipped`; a malformed envelope;
  `mutation_state` for unchanged, changed, and unparsed inputs.
* **Posture:** test-first. **Size:** M. **Complexity:** medium (the high-risk
  envelope uncertainty is de-risked by the characterization step, and the
  function is pure).

### A3 — `cascade-close` orchestration and CLI

* **Files:** `src/autoharness/shipment_close/command.py` (new),
  `src/autoharness/cli.py` (dispatch and usage only), and
  `tests/test_shipment_cascade_close_invoke.py` (new).
* **Changes:**
  * `run_cascade_close(...)` steps, all under the A1b pair lock:
    1. Acquire the lock and run the existing-record check (exit 7 or 2), before
       any classification.
    2. Validate `--message` and `--author`: each must be non-empty, contain no NUL
       or newline, and be at most 1,024 characters. Failure exits 2.
    3. Call `run_preclose`. A non-CASCADE verdict writes the `pre_close` verdict
       record and exits 3 without invoking anything.
    4. Write the `pre_close` record. If that write fails, exit 2 without invoking
       anything.
    5. Revalidate (AS-F02): recompute the **entire** pre-close snapshot (the
       verdict, qualifying set, linked deliberations, every declared status,
       every `parent_id`, and every SHA-256) and compare it with the durable
       record, ignoring only `captured_at`. Any difference exits 4
       (`HALT — cascade pre-invocation revalidation drift detected`).
    6. Re-hash the resolved binary. A mismatch with `tool.binary_sha256` exits 4
       without invoking anything, leaving only the replaceable `pre_close`
       record (AN-F08).
    7. Write the owner-bound `phase: invoking` record (`run_id`,
       `argv_redacted`, `started_at`). If that write fails, exit 2 without
       invoking anything (INV-P1, INV-P7).
    8. Invoke through A3a with the fixed argv
       `[<absolute binary>, "--no-update-check", "--jsonrpc", "--cwd", <workspace root>, "shipment", "ship", S, "--sha", X, "--message", M, "--author", A]`.
    9. Re-read the fingerprinted files, then call A3b `parse_ship_response` and
       `evaluate_postconditions`.
    10. Write the owner-bound `post_close` record. This happens **even when the
        invocation or the parse fails**, so the evidence of a failure is preserved.
        If this write fails, exit 8.
  * Exit codes (one table for the command, including `--classify-only`):

    | Code | Meaning | Mutation possible? | Ship action |
    |---|---|---|---|
    | 0 | Mutating mode: all postconditions passed. `--classify-only`: CASCADE verdict recorded | mutating: yes (completed); classify-only: no | See the A5 routing table |
    | 2 | Input, I/O, no-clobber refusal (`already finalized`), or a pre-invocation write failure | no | HALT; fix the input or ask the operator |
    | 3 | Verdict is not CASCADE; a verdict record is written and nothing is invoked | no | See the A5 routing table |
    | 4 | Pre-invocation revalidation drift, including a binary hash change; nothing invoked | no | HALT; operator |
    | 5 | A postcondition failed; the record names every failure | yes | HALT; operator review |
    | 6 | backlogit exited non-zero, timed out, or stdout did not parse | indeterminate | HALT; operator review |
    | 7 | An existing lock or `invoking` record; nothing invoked | unknown (prior run) | HALT; operator review |
    | 8 | The post-close evidence write failed after invocation | yes | HALT; operator review |

  * Exits 5, 6, 7, and 8 forbid committing the backlog root, re-running
    `cascade-close`, calling `backlogit shipment ship` directly, or substituting
    SAFE_CLOSE (INV-P4) until an operator reviews the backlog state and the record.
  * `--json` output (AN-F06) is one object:
    `{mode, exit_code, evidence_path, phase_written, classifier_verdict,
    mutation_possible: no | yes | indeterminate | unknown, postcondition_verdict,
    failures[], operator_action: none | review_required}`. The exit-2 cases
    always report `mutation_possible: no`, because every post-invocation write
    failure uses exit 8.
  * `cli.py` gains the `shipment` group, the `cascade-close` subcommand, and USAGE
    lines. The USAGE text labels the mutating mode **destructive** and
    `--classify-only` read-only apart from the evidence record (Principle VII).
* **Tests:** a fake `backlogit` (A3a seam) emitting a canned envelope: a pass case;
  a non-empty `returned_ids` case, which exits 5 with the record written; backlogit
  exiting 1 with stderr, where the record keeps redacted stderr and exits 6; a
  pre-existing `invoking` record exits 7 and the fake is never spawned (the fake
  writes a sentinel file when run); drift injected between steps 4 and 5 exits 4
  with no spawn; a simulated post-close write failure exits 8; the argv the fake
  receives equals the fixed argv, including `--cwd`; `--json` fields per exit code.
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### A4 — Closure-evidence gate: `close_path` and the close-evidence requirement

* **Files:** `src/autoharness/cli.py` (the `_evaluate_closure_evidence` path only),
  and `tests/test_cli_gate_closure_evidence.py` (extended).
* **Changes:**
  * The gate is write-time only: no workflow, script, or CI job re-gates committed
    closure artifacts (verified 2026-09-27: no `.github/workflows/` or `scripts/`
    invocation of `closure-evidence`). The new checks therefore apply to every
    invocation, and committed artifacts are unaffected because they are never
    re-gated and the topology reader is unchanged (INV-P5).
  * Check order: the new checks run only **after** the existing
    `frontmatter_predicate` and `discoverability` checks pass. A `BLOCKED`
    artifact therefore still fails at `frontmatter_predicate` exactly as today,
    and the new checks never mask or reorder an existing `failed_check`.
  * Every artifact must carry `close_path: cascade | safe_close`. A missing or
    other value fails as `failed_check: close_path`.
  * Every artifact must carry `close_evidence: <path>`, checked in this order, each
    failure reported as `failed_check: close_evidence`:
    1. textual containment first (a relative POSIX path, no `..`, no drive or UNC
       prefix, under `docs/closure/evidence/`), before any filesystem call
       (compound `2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`);
    2. it equals `build_evidence_path(S, F)` for the artifact's declared pair;
    3. the entry is a regular file (no symlink or reparse point) of at most
       512 KiB. It is opened with `O_NOFOLLOW` where available. **Before any
       byte is read**, its `fstat` identity must equal the pre-open `lstat`, and
       the resolved path of the file and of each parent component is re-checked
       for containment (SL-F05/SL-F07). It is then read once and parsed as JSON.
       The remaining parent-swap race window needs a local attacker with write
       access to the working tree, which is outside this gate's threat model.
       This is accepted and recorded;
    4. `validate_evidence_record(..., close_path=<declared>)` passes;
    5. when the closure artifact carries the `merge_commit` frontmatter key (the
       key committed artifacts already use, for example
       `docs/closure/175-S-167-F-post-merge-closure.md`), the record's
       `merge_commit_sha` must equal it. When the key is absent the gate adds a
       `warnings[]` entry instead: the operational-closure template does not yet
       mandate `merge_commit`, and mandating it is outside this plan's scope.
  * SAFE_CLOSE is fail-closed too (AN-F01, amending D-A3 — Stage-recommended,
    pending operator confirmation). A `safe_close` artifact without a valid
    `SAFE_CLOSE` verdict record fails.
  * SAFE_CLOSE direct-cascade detection (AN-F07/AN-F09): for a `safe_close`
    record, the gate requires every `observation_set` entry to still be at
    exactly its recorded location, with its recorded SHA-256. An entry that was
    already archived at baseline therefore stays valid, and only a change
    relative to the baseline fails. Any difference fails as
    `failed_check: close_evidence`. This is the same baseline invariance that
    safe-close itself asserts, re-checked at write time. An empty observation
    set (only when no manifest task has a parent) passes with a `warnings[]`
    entry saying the check was vacuous.
  * **Guarantee:** a direct cascade can never be accepted under
    `close_path: cascade`. Under `close_path: safe_close`, it is detected whenever
    it changed anything in the observation set (which includes every
    descendant and linked deliberation a cascade could reach), which is exactly the corruption SAFE_CLOSE
    exists to prevent. The undetected residual is a direct cascade whose effect
    equals the safe-close outcome, which by construction left nothing outside
    closure scope changed. It remains a P-005 deviation by skill contract, and
    upstream enforcement is requested in A7. Accepting this benign residual is a
    Stage-recommended decision, pending operator confirmation.
  * `close_path` and `close_evidence` are added to the `failed_check` vocabulary in
    the gate USAGE text and the `--json` description, and `warnings[]` is
    documented there.
  * The pipeline-topology closure reader is **not** modified.
* **Tests:**
  * CASCADE with no record → FAIL;
  * CASCADE with a `fail` verdict record → FAIL;
  * CASCADE with a valid record → PASS;
  * SAFE_CLOSE with no record → FAIL; with a valid SAFE_CLOSE verdict record →
    PASS; with a CASCADE record → FAIL; with an observation-set parent feature or
    sibling now archived or modified (a task-only, partial-feature fixture) →
    FAIL; with a linked deliberation of the parent feature now archived → FAIL;
    with a sibling that was already archived at baseline and is unchanged → PASS;
    with an empty observation set → PASS with the vacuous-check warning;
  * `classify_closure_candidates` ignores a `docs/closure/evidence/` subdirectory
    (a regression pin);
  * a mismatched shipment ID in the record → FAIL;
  * a `..` path, an absolute path, and a symlinked record → FAIL with no read
    outside the workspace;
  * a mismatched `merge_commit_sha` → FAIL;
  * a `BLOCKED` artifact still reports `failed_check: frontmatter_predicate`;
  * the topology gate still accepts a committed fixture artifact that has no
    `close_path` (INV-P5 pin).
* **Posture:** test-first. **Size:** M. **Complexity:** medium.

### A5 — Skill templates and mirrors route CASCADE through the command

* **Files:** `templates/skills/shipment-reconcile/SKILL.md.tmpl`,
  `.github/skills/shipment-reconcile/SKILL.md`,
  `templates/skills/operational-closure/SKILL.md.tmpl`,
  `.github/skills/operational-closure/SKILL.md`, and `.autoharness/harness-manifest.yaml`
  (only the checksums and notes of those two entries).
* **Changes:**
  * shipment-reconcile:
    * Step 0(c) and the Cascade Close Sub-Procedure pre-invocation revalidation,
      baseline capture, step 1 invocation, and steps 2-6 now point at
      `autoharness shipment cascade-close`;
    * every close runs `autoharness shipment cascade-close --classify-only` first;
    * the mutating `cascade-close` invocation **is** the destructive command.
      It needs the same operator approval that the direct `backlogit shipment
      ship` call needs today (intercom auto-check or operator clearance;
      Principle VII). `--classify-only` needs none;
    * a direct `backlogit_ship_shipment` MCP or `backlogit shipment ship` CLI call
      is a **P-005 deviation** on either path (the A4 gate also refuses its
      closure);
    * the prose invariants stay as the specification the command implements.
  * The routing table in the skill (AN-F03/AN-F04):

    | Mode | Exit | Skill action |
    |---|---|---|
    | `--classify-only` | 0 (CASCADE) | Obtain destructive-command approval, then run mutating `cascade-close` |
    | `--classify-only` | 3 (SAFE_CLOSE) | SAFE_CLOSE path, citing the verdict record as `close_evidence` |
    | mutating | 0 | Write the closure artifact with `close_path: cascade` and `close_evidence` |
    | mutating | 3 | The verdict changed after a CASCADE classify-only verdict: HALT and never SAFE_CLOSE (INV-P4) |
    | either | 2, 4 | HALT. Nothing was mutated. Fix the input, or ask the operator |
    | either | 5, 6, 7, 8 | HALT. Operator review. No commit of the backlog root, no retry, no direct call |

  * operational-closure: the closure artifact frontmatter gains `close_path` and
    `close_evidence`, and the evidence JSON is committed with the closure artifact.
* **Tests:**
  * The structural test `tests/test_flat_manifest_closure_docs.py` gains assertions
    that the command, the routing table, the destructive-approval sentence, and the
    P-005 wording appear in both the template and the mirror.
  * AN-F05: a new parity assertion pins LF-normalized equality between the
    rendered template and the installed mirror for each edited section (the
    Step 0(c) block, the Cascade Close Sub-Procedure, and the operational-closure
    frontmatter block). Existing tests cover only the Output bullet, Step 3a, and
    the Ship paragraph.
  * `tests/test_closure_contract_nondrift.py` must stay green unchanged: the
    operational-closure `### Step 3a: Validate the Closure Artifact with the
    Closure-Evidence Gate` heading is kept verbatim, and no edited surface may
    restate a closure filename outside the contract-derived form.
* **Posture:** characterization-first (run the existing doc tests before editing).
  **Size:** M. **Complexity:** low.

### A6 — Ship agent P-015 pointer (template and mirror)

* **Files:** `templates/agents/_ship.agent.md.tmpl`, `.github/agents/_ship.agent.md`,
  and the manifest checksum of that entry.
* **Changes:**
  * In post-merge step 2c, every close starts with `--classify-only`. CASCADE is
    executed only through `autoharness shipment cascade-close`, with the same
    destructive-command approval, and the closure artifact needs `close_path` plus
    `close_evidence`.
  * The closure-evidence contract sentence names the new frontmatter keys.
  * Pointer-level only. The routing table lives in the skill, not here.
  * Frontmatter is **not** touched (C owns it).
* **Tests:** extend the existing Ship structural test that asserts the P-015 pointer,
  in both files, and add a rendered-section parity assertion for step 2c (AN-F05).
  The Ship `**Closure-evidence contract**` paragraph stays a single line in each
  file with rendered template/mirror parity, because
  `tests/test_closure_contract_nondrift.py::test_template_and_installed_mirror_parity`
  asserts exactly one such line. The new keys are added inside that same line.
* **Posture:** characterization-first. **Size:** S. **Complexity:** low.

### A7 — Docs: command reference and the portable upstream backlogit request

* **Files:** `docs/gates-reference.md` (a "Shipment close commands" section that
  explains why it is not a gate, including the A3 exit-code table and `--json`
  fields), and
  `docs/bugs/2026-09-27-backlogit-shipment-ship-structured-evidence-request.md` (new).
* **Changes:**
  * The upstream request is self-contained and copy-ready for the backlogit
    workspace. It asks for:
    * a native `--json` result on `shipment ship`;
    * an optional `--evidence-out <path>` that emits the engine's own pre-close
      candidate set (`collectArchiveCandidateIDs`) and the post-close result;
    * a documented envelope;
    * an opt-in workspace setting that refuses a direct `shipment ship` or
      `backlogit_ship_shipment` unless an evidence path is supplied. This is the
      mutation-boundary enforcement AN-F01 asks for, and autoharness cannot
      implement it itself.
  * It states explicitly that autoharness does not depend on it.
* **Tests:** markdownlint, and `tests/test_docs_frontmatter_decodes.py`.
* **Posture:** docs-only. **Size:** S. **Complexity:** low.

## Dependency Graph

A1 → A1b → A2 → A3a → A3b → A3 → A4 → A5 → A6, and A3 → A7.

* A1b, A2, A3b, and A4 consume A1's contract and validator.
* A3a depends only on A1b's `StreamCapture`. A3b depends only on A1 and on A2's
  snapshot type.
* A3 composes A1b, A2, A3a, and A3b.
* A4 follows A3 so the gate and the command land against one settled record shape.
* A5 and A6 both touch `.autoharness/harness-manifest.yaml`, so they stay serial.
* A4, A5, and A6 must ship in the same release unit (one PR). The stricter gate
  must never land ahead of the skill and agent routing that produces its evidence.
* A7 documents the shipped command behavior.

## Decisions and Rationale

See deliberation D-A1 through D-A6 (all Stage-recommended, pending operator
confirmation).

* The command lives in autoharness, and the upstream request does not block.
* The evidence is committed under `docs/closure/evidence/` and kept permanently.
* SAFE_CLOSE gets a verdict record, and (review cycle 1, amending D-A3 — Stage-recommended,
  pending operator confirmation) the gate requires that record rather than only
  warning. Without it, a self-declared `safe_close` would bypass R5 (AN-F01).
* A machine-readable `close_path` key is added.
* The contract stays in code, not in `schemas/`.

The command does not depend on 179-F / 185-S, which is unclaimable by construction.
It implements minimal local fixed-argv, bounded-read, and atomic-write helpers. When
179-F eventually lands, the follow-up is to converge these onto its primitives, and
that follow-up is recorded here.

## Risks and Caveats

* **The JSON-RPC envelope shape is uncharacterized.** Mitigation: A3b's
  characterization-first step. An unparseable result is written to evidence and
  exits 6. It never passes silently.
* **A CASCADE mutation happened but the post-close write failed** (disk full).
  Mitigation: the `invoking` record already exists. The command exits 8 with
  `HALT — cascade evidence post-close write failed`, and any later run halts with
  exit 7 on that record. The skill forbids committing the backlog state until an
  operator reviews it.
* **An evidence file in the repository could carry secrets.** Mitigation:
  redaction of every persisted free-text field, and bounded excerpts. backlogit's result carries IDs and
  SHAs only, `--no-update-check` removes the only network call, and the evidence
  JSON is part of the reviewed closure PR diff. Residual: a finite redactor cannot
  prove arbitrary stderr is secret-free. This is accepted, because backlogit is a
  local file-backed tool with no credential inputs (SL-F04).
* **A hand-forged evidence record would pass the gate.** The record is an audit
  trail, not an attestation. Forging it is a P-005 violation. Mutation-boundary
  enforcement is requested upstream in A7.
* **PATH trust is unchanged from today** (SL-F03). Pinning a trusted absolute
  binary path in the registry is a follow-up, out of scope under P-021 C1.
* **Windows:** the atomic replace over an open file is covered in A1b's tests, and
  the temp directory is cleaned up with bounded retry (compound 034-DL pattern).
* **Merge overlap** with 192-S / 197-S on `_ship.agent.md*`. They touch different
  sections, and Ship rebases.

## Plan Hardening Signals

* Public API, schema, or contract change — **present** (new CLI command group, new
  closure frontmatter keys, a stricter gate).
* Security or compliance-sensitive behavior — **present** (persisting subprocess
  output; redaction).
* Migration or destructive action — **present** (it wraps the destructive cascade;
  the gate tightens for new artifacts).
* External integration — **present** (backlogit CLI subprocess).
* High runtime or rollback risk — **present** (the closure path used by every
  shipment).

Requires plan hardening: yes

## Runtime Verification and Closure

* A3 and A4 change runtime CLI surfaces.
* Environment precheck: `backlogit --version` resolves outside the workspace root
  and reports the version recorded in A3's characterization step. `git status` of
  the scratch workspace is clean before the run.
* Runtime proof: in a scratch copy of a fixture workspace created under the OS
  temp directory (never the live `.backlogit/` and never inside this repository),
  run `autoharness shipment cascade-close` against the real `backlogit` binary on
  a CASCADE-eligible fixture. Confirm that the record is written,
  `postcondition_verdict: pass` holds, and `autoharness gate closure-evidence`
  returns PASS for an artifact that cites it. Then delete the record and confirm
  the gate FAILs with `failed_check: close_evidence`. Re-run `cascade-close` on
  the same pair and confirm exit 2 (`evidence already finalized`) with no second
  backlogit spawn.
* Blocked path: if the real binary is unavailable or its version differs from the
  characterized one, the runtime proof is recorded as `BLOCKED` with the reason
  (P-012), never as PASS on the fake-binary tests alone.
* Closure: this feature's own closure artifact records `close_path`. If its closure
  is itself a CASCADE, it is the first dogfood use of the command.

## Plan Hardening

* **Hardening required:** yes. All five signals are present.
* **Learnings consulted:**
  * `docs/compound/2026-09-27-175-s-closure-evidence-gate-hardening-lessons.md`
    (textual containment before any filesystem call; regular entries only; truthful
    negative records);
  * `docs/compound/2026-08-23-cascade-close-archived-ids-omits-pre-archived-tasks-on-1101.md`
    (`archived_ids` is a transition log, so the two-set gate is keyed on the
    pre-close snapshot);
  * `docs/compound/2026-08-18-p015-cascade-classifier-override-deviation.md` (a
    classifier verdict is final, with no substitution).
* **Instructions consulted:** `circuit-breaker.instructions.md` (log bounds and
  redaction), `backlogit.instructions.md`, and `constitution.instructions.md`.
* **Protected invariants:**
  * INV-P1: no CASCADE invocation without a durable pre-close record.
  * INV-P2: `allowed_ids` / `required_ids` are computed only from the pre-close
    snapshot, never from a post-close re-read.
  * INV-P3: the two set checks stay separately labelled and fail independently
    (B57F9E24).
  * INV-P4: no fallback to SAFE_CLOSE after a CASCADE verdict. Refusing to run is a
    halt, not a substitution.
  * INV-P5: already-committed closure artifacts and the pipeline-topology consumer
    are unchanged.
  * INV-P6: evidence content is bounded and redacted, and the raw capture beyond the
    excerpt is never persisted.
* **ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | The wrapper invokes the destructive `shipment ship` | high | Same as today (the P-015 classifier authorizes it); no new authority |
  | Tighten the closure-evidence gate for every write-time invocation (CASCADE and, per review cycle 1, SAFE_CLOSE) | medium | Plan-review PASS; the operator can revert with a one-commit rollback of A4 |
  | Persist subprocess output into the repository | medium | Redaction tests in A1 are a merge prerequisite |
  | Edit the skill and agent templates plus mirrors and manifest checksums | low | Checksums refreshed from the raw staged blob (IM-12) |

* **Rollback:** each unit is a separate commit. Reverting A5 and A6 restores the
  prose path. Reverting A4 restores the old gate. The command itself is additive.
  Rollback trigger: any closure that the new gate FAILs incorrectly, or any wrapper
  crash during a real closure. In that case Ship halts and records a P-005 deviation
  rather than falling back silently.
* **Monitoring and validation window:** the next three CASCADE closures after the
  merge record `close_path: cascade` with a PASSing gate. Ship reports any exit 5 or
  6 as a residual-risk record.
* **Review-gate capability risk:** no reviewer subagent tool is exposed in this
  Stage runtime. The review must declare its `dispatch_mode:` and literal
  `decision:` marker. An external-CLI reviewer on the anchor route is preferred.
* **Unresolved operator decisions:** D-A1 through D-A4 (Stage-recommended). None
  blocks safe execution.

### Hardening Pass 2 (2026-09-27, Stage resumption)

The first pass above (written with the plan) recorded triggers and invariants but
left operational gaps. This pass closed them in the unit text. Each item names the
unit it changed.

* **Additional learnings consulted:**
  * `docs/compound/2026-08-30-157-s-copilot-review-timeout-not-a-clean-signal.md`
    (a timeout is not a clean negative signal, so a timed-out cascade is
    `indeterminate`, not "no mutation");
  * `docs/compound/2026-07-01-subprocess-validation-gating.md` (argv-array only,
    no `shell=True`, runtime state out of the tracked tree).
* **Code facts verified for this pass:** the closure-evidence gate
  (`src/autoharness/cli.py` `_evaluate_closure_evidence`) runs
  `frontmatter_predicate` before `discoverability`, and `BLOCKED` already fails
  `topology._closure_artifact_complete`; no workflow or script re-gates committed
  closure artifacts; `backlogit shipment ship` accepts `--sha`, `--message`,
  `--author`, and the global `--cwd`, `--jsonrpc`, `--no-update-check` flags;
  committed closure artifacts use the `merge_commit` frontmatter key;
  `tests/test_closure_contract_nondrift.py` pins the single-line Ship contract
  paragraph and the Step 3a heading.
* **Hardening items:**
  * **H-B1 (A3):** an `invoking` phase is written atomically before spawn, so a
    crash or kill between spawn and the post-close write leaves a detectable
    in-flight record. `mutation_state` is recorded, and a timeout or non-zero
    exit is `indeterminate` unless a byte-level re-read proves otherwise.
  * **H-B2 (A1, A2, A3):** no-clobber. A `post_close` record is never replaced
    (exit 2). An `invoking` record halts with exit 7. Only a `pre_close` record
    may be replaced.
  * **H-B3 (A3):** one exit-code table covering 0/2/3/4/5/6/7 (and 8 after review cycle 1), each with its
    mutation possibility, and a single HALT rule: no retry, no direct
    `backlogit shipment ship`, no SAFE_CLOSE substitution, and no commit of the
    backlog root after 5/6/7 until an operator review.
  * **H-B4 (A1):** redaction runs before the excerpt is sliced, over a margin
    window, so a boundary-split secret cannot leak. The capture is streamed, so
    memory stays bounded.
  * **H-B5 (A2, A3):** input validation (IDs, a 40-hex SHA, message and author
    length with no NUL or newline) happens before any write. backlogit is pinned
    to the workspace with `--cwd`. Only stdout is parsed.
  * **H-B6 (A3a):** the binary is resolved with `shutil.which`. A binary inside
    the workspace root, or a symlinked or reparse-point binary, is refused. The
    resolved path and version are recorded. Timeout kills the process tree by
    PID, and the timeout is bounded to 30-900 s.
  * **H-B7 (decomposition):** the subprocess runner was split out of A3 as A3a, and
    review cycle 1 split further into A1/A1b and A3b/A3
    (S / medium), which keeps A3 inside the 2-hour rule.
  * **H-B8 (A4):** new checks run after the existing checks, so no existing
    `failed_check` is reordered. Evidence-path textual containment runs before any
    filesystem call, followed by a regular-file check and a 512 KiB size cap.
    `merge_commit` is cross-checked when present. The `failed_check` vocabulary
    and `warnings[]` are documented. "New artifacts" is replaced by the verified
    write-time-only fact.
  * **H-B9 (A5, A6):** nondrift constraints are stated explicitly (the single-line
    Ship contract paragraph, the Step 3a heading, and no restated closure
    filenames). The skill's exit-code mapping is spelled out.
  * **H-B10 (runtime verification):** an environment precheck, an OS-temp scratch
    workspace, a re-run no-clobber proof, and an explicit `BLOCKED` path (P-012).
* **Added protected invariant:**
  * INV-P7: a CASCADE invocation leaves exactly one durable record whose phase
    shows how far it got (`pre_close`, `invoking`, or `post_close`). No path
    overwrites a record that reached `invoking` or `post_close`.
* **Additional ProposedAction / ActionRisk:**

  | ProposedAction | ActionRisk | Approval |
  |---|---|---|
  | Kill a timed-out backlogit process tree mid-cascade | high | No new authority: the result is always `indeterminate` and exit 6, followed by an operator review before any further close action |
  | Refuse to run on an existing `invoking` record (exit 7) | low | None. This is a halt, not a mutation |

* **Residual risk (accepted, carried to review):** the evidence record is an audit
  trail, not a cryptographic attestation. A hand-forged record would pass the gate.
  Forging it is a P-005 violation, and detection is left to review and to the
  record's hashes. Cross-checking the live archive state at gate time is out of
  this plan's scope under P-021 C1.
* **Review-gate capability (restated):** reviewer subagent dispatch is not exposed
  in this Stage runtime. Cross-model personas go through the external Copilot CLI
  on the anchor route (`gpt-6-sol`), and the always-on personas are applied inline
  by Stage (`dispatch_mode: same-model-declared-degradation` for inline passes,
  declared in the review record).

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* Review record: `docs/reviews/2026-09-27-cascade-close-evidence-capture-plan-review.md`.
  It is authoritative for findings, dispositions, and persona coverage.
* Gate: **PASS** under severity rule C4, with 0 open P0 and 0 open P1, after three
  review-fix cycles and a bounded fix-verification loop confined to the cycle-3
  fixes.
* Plan hardening was required and is satisfied (the original record plus
  Hardening Pass 2).
* Persona coverage, all seven selected personas:
  * inline passes: Constitution, Python, Scope Boundary, and Learnings;
  * independent anchor-route passes (`gpt-6-sol`, external Copilot CLI):
    Architecture Strategist, Security Lens, and Agent-Native Parity.
  * Declared degradation: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared
    fallback: single-agent persona pass`.
* Stage-recommended decisions pending operator confirmation: the D-A3 amendment
  (SAFE_CLOSE fails closed), acceptance of the benign direct-cascade residual, and
  acceptance of the SL-F04 and SL-F07 residuals.

