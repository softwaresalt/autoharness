---
title: "Brainspace Compression Feasibility Spike"
date: "2026-07-13"
description: "Feasibility findings for Option E from the TokenMasterX evaluation: Brainspace-style tool-output compression with a content-addressed reversible store."
topic: "Should autoharness adopt Brainspace-style output compression, and under what host, storage, and safety constraints?"
depth: "spike"
decision_status: "proposed"
doc_type: spike
source: docs/spikes/2026-07-13-brainspace-compression-feasibility.md
tokenmasterx_revision: "9b86c8ac22d8145e751966d92336aa302f4261f9"
backlog_items:
  - "086-F"
linked_artifacts:
  - ".backlogit/archive/086-F.md"
  - "docs/decisions/2026-07-13-tokenmasterx-integration-spike.md"
  - "docs/spikes/058.001-reference-adoption-evaluation.md"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/README.md"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/token-master-plugin/skills/token-master/SKILL.md"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/token-master-plugin/skills/token-master/brainspace/router.py"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/token-master-plugin/skills/token-master/brainspace/ccr.py"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/token-master-plugin/skills/token-master/brainspace_mcp.py"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/token-master-plugin/skills/token-master/brainspace_posttooluse.py"
  - "https://github.com/All-The-Vibes/TokenMasterX/blob/9b86c8ac22d8145e751966d92336aa302f4261f9/token-master-plugin/skills/token-master/brainspace_setup.py"
  - ".github/instructions/constitution.instructions.md"
  - ".github/instructions/harness-architecture.instructions.md"
  - "AGENTS.md"
tags:
  - "brainspace"
  - "ccr"
  - "host-parity"
  - "primitive-1"
  - "primitive-6"
  - "primitive-7"
  - "primitive-10"
  - "operator-decision"
---

<!-- markdownlint-disable MD013 -->

## Brainspace Compression Feasibility Spike

## Status

**PROPOSED — investigation complete; recommendation: DEFER, with a possible
later NARROW pilot.** This spike is Stage-side research for backlog item `086-F`.
It produced findings only: no templates, source, config, backlog status,
shipment, PR, or merge state were changed.

### Evidence provenance

A local TokenMasterX checkout is present at `references/tokenmasterx/` and was
verified at commit `9b86c8ac22d8145e751966d92336aa302f4261f9`, matching the
parent evaluation's reviewed revision. Because `references/` is gitignored, the
frontmatter links prefer upstream permalinks pinned to that commit. Host-parity
claims below distinguish **locally inspected TokenMasterX behavior** from
current host API facts; this spike did not independently verify current hook
APIs for every supported host.

## Problem/Context

The TokenMasterX evaluation accepted Engram-first structural routing work but
left Option E, Brainspace-style compression, as **MAYBE — needs more info**.
Brainspace attacks a different token population than graph routing: bulky tool
outputs that remain in the transcript and are re-sent on later turns.

The concrete design inspected locally has two halves:

* a **PostToolUse hook** for Claude Code that attempts to rewrite tool output
  before the result is appended to the transcript;
* a **Brainspace MCP server** exposing `brainspace_compress`,
  `brainspace_retrieve`, and `brainspace_stats`, backed by a CCR
  content-addressed reversible store.

The router detects JSON, logs, code, and prose, lazy-loads type-specific
compressors, and enforces a central **never-expand** guard in token terms, not
just character length. However, the inspected router calls the compressor with
`stash=...` before applying the character/token reject checks, so rejected
compressions can still leave raw originals in CCR with no transcript placeholder.
That implementation detail materially increases the sensitive-data risk and
would need redesign before any autoharness pilot.

The design is promising for repetitive logs and JSON, but it is higher risk than
the already-accepted graph-routing work because it stores exact raw tool outputs,
because transparent compression depends on host-specific output rewriting, and
because the inspected implementation has reversibility and evidence-preservation
gaps.

## 1. Host parity

Compression-on-write means the host must let a harness transform arbitrary tool
results **before** they enter the transcript. MCP alone is not enough for that:
MCP tools run only when the model elects to call them, typically after some raw
output is already visible in context.

**Important scope note:** the matrix below reflects the local TokenMasterX
implementation and autoharness setup documentation, not a fresh authoritative
survey of every host's current hook API. Before any pilot, autoharness must
confirm current append-boundary/output-rewrite support for each host from that
host's own documentation or SDK. If non-Claude hosts now expose equivalent hooks,
the pilot scope should widen accordingly; do not treat Claude-only as proven
exclusivity.

| Supported host | Compression-on-write support observed in this spike | Reversible expand support | Feasibility finding |
| --- | --- | --- | --- |
| Claude Code | **Implemented by TokenMasterX, host-specific.** `brainspace_posttooluse.py` emits `hookSpecificOutput.updatedToolOutput` for a Claude `PostToolUse` hook. | **Yes, via MCP**, but the advertised MCP retrieval tool truncates large originals; see Section 2. | This is the only locally inspected full model, but it has a material evidence gap: `_extract()` reads only `content`, `output`, `stdout`, or `text` from a dict response, not `stderr` or exit status. A failing command can lose actionable failure evidence if the host payload stores it in sibling fields. |
| GitHub Copilot CLI | **Not independently verified.** TokenMasterX `brainspace_setup.py` assumes Copilot CLI is MCP-only and does not install an auto-compress hook. | **Yes if MCP server is installed**, subject to the MCP truncation limit. | Treat as MCP/manual mode unless current Copilot CLI documentation proves an append-boundary rewrite hook. Do not claim transparent compression savings from the local TokenMasterX assumption alone. |
| VS Code + GitHub Copilot | **Not independently verified.** autoharness registers agents, skills, and prompts through VS Code user settings; this spike did not confirm a Copilot Chat pre-append rewrite API. VS Code background sessions targeting Copilot CLI may inherit the Copilot CLI behavior. | **Maybe, if MCP is available**, subject to the MCP truncation limit. | Treat as unknown/manual until verified against current VS Code + Copilot APIs. |
| Codex | **Not independently verified.** autoharness installs skills into `~/.codex/skills/`; this spike did not confirm an arbitrary tool-output rewrite hook. | **Unknown / host-dependent.** | Treat as unknown until a Codex-specific append-boundary hook or equivalent is proven. |
| Cursor | **Not independently verified.** autoharness can be added as an agent source and can use MCP-style configuration, but this spike did not confirm transparent output rewriting. | **Maybe, if MCP is available**, subject to the MCP truncation limit. | Treat as unknown/manual until verified against current Cursor APIs. |

**Parity conclusion:** A capability that only works transparently in a subset of
hosts would violate autoharness' environment-agnostic principle if installed as
core or if agents relied on it for correctness. It can fit autoharness only as an
**optional/degraded overlay** whose base behavior remains coherent without it.
The transparent mode should be enabled only on hosts with verified
append-boundary rewrite support; MCP/manual mode must be labeled degraded and
must not be used to claim compression-on-write savings.

The overlay contract would need to say that compression changes token economics,
not task correctness. Agents must continue to preserve evidence and complete work
when the pack is disabled, unavailable, MCP-only, or declined for a specific
output.

## 2. CCR reversible-store retention, privacy, security, and deletion

CCR is what makes lossy display compression reversible, but it is also the main
risk surface. Raw tool outputs often contain:

* secrets and tokens from environment dumps, CLI auth failures, `.env` files, CI
  logs, package-manager diagnostics, or accidental command output;
* PII or customer data embedded in logs, database exports, issue bodies, or
  support artifacts;
* proprietary source and generated files from `Read`, `git diff`, MCP document
  retrieval, and large tool responses;
* one-time operational evidence such as gate verdicts, stack traces, failing job
  names, and review findings.

The local TokenMasterX CCR implementation stores exact originals in a SQLite file
as zlib-compressed blobs. It does not encrypt content, does not implement
per-entry access control, and does not automatically expire entries. Its LRU
`gc(max_bytes=500 * 1024 * 1024)` is opt-in and is intentionally not called
mid-request because evicting a live placeholder strands the model without the
original.

### Stash-before-reject flaw

The inspected router calls the selected compressor as
`_load(ctype)(content, stash=stash, **opts)` before checking whether the returned
compressed text is smaller in characters or tokens. The compressors can call
`stash(...)` during that step. Therefore a compression later rejected by the
router's never-expand guard can still persist the exact raw original in CCR even
though no `[[BR:...]]` placeholder is shown in the transcript.

This contradicts a safe "decline, not stash" model. For autoharness, the design
would need to change so secret/PII screening and the never-expand decision happen
**before** any durable stash, or so a rejected compression rolls back every stash
created during the attempt. Otherwise small, unhelpful, or security-sensitive
outputs can become orphaned raw originals with no visible transcript handle.

### Retention expectations

A safe autoharness design would need an explicit retention contract before any
implementation:

* default retention should be short and tied to the active session or a bounded
  time/window, not indefinite workspace history;
* retention must never be extended silently by deduplication or repeated access;
* large stores must have an operator-visible size cap and age-based purge policy;
* every visible compressed placeholder must remain recoverable for the active
  context window, or compression must be declined.

The inspected implementation has a size-based opt-in garbage collector, but no
TTL, no automatic session cleanup, no deletion audit trail, and no rollback for
stashes created by compression attempts that are later rejected. That is not
enough for autoharness as-is.

### Who can read originals

Anyone who can read the CCR SQLite/WAL files can read originals after simple
zlib decompression. Any agent with access to `brainspace_retrieve` and a
placeholder can request expansion through the MCP server. If the database is
accidentally committed or uploaded, every stashed raw output in it becomes
portable sensitive data.

The retrieval API accepts short hash prefixes: `CCR.retrieve()` sanitizes the
input, accepts prefixes as short as 6 hex characters, and uses `LIKE <prefix>%`
while refusing ambiguous matches. The short key does not reveal the secret by
itself, but it is a compact stable handle to retrieve local sensitive data.

### Reversibility limitation in the advertised MCP path

Direct `CCR.retrieve()` returns the full stored content when the hash is found,
but the advertised MCP tool `brainspace_retrieve` caps output at
`MAX_RETRIEVE_CHARS` (default `200000`) and returns a truncated preview with a
suffix for larger originals. It provides no pagination or chunked retrieval in
the inspected code. Therefore a benchmark that requires byte-equivalent recovery
cannot rely on the MCP path for large originals; it must either test direct CCR
recovery separately or require an MCP pagination/no-truncation design before any
pilot.

### Deletion expectations and risks

Deletion must cover more than `DELETE FROM ccr`:

* SQLite main-database free pages and WAL files may retain deleted blobs unless
  the implementation uses appropriate checkpointing, `secure_delete`, and
  `VACUUM`/compaction guidance; the inspected implementation does not call those;
* SHM files are SQLite shared-memory index/control files, not confirmed raw blob
  stores in this spike, so they should be covered by cleanup but not cited as the
  main raw-content retention mechanism;
* the inspected `gc(max_bytes=...)` measures `SUM(LENGTH(blob))` in rows, not the
  full SQLite/WAL on-disk footprint;
* OS backups, editor indexes, endpoint protection, and MCP logs may have copies;
* content-addressed dedup makes per-consumer deletion hard because several
  transcript placeholders can point to the same original;
* deleting while a placeholder is still in context breaks reversibility and can
  make the compressed transcript misleading.

A production design needs a first-class purge command, session-end cleanup,
SQLite checkpoint/compaction guidance, optional secure deletion where feasible,
and clear behavior for retrieval after purge.

### Secret scanning and accidental commits

A gitignored SQLite store is unlikely to be covered by normal text-oriented
secret scanning. If the database or WAL files are accidentally committed,
scanners may miss zlib-compressed blobs inside SQLite. If the store is not
gitignored, `git add .` can stage sensitive tool outputs directly.

Therefore CCR must be treated as sensitive-by-default local state. Compression
should be declined before durable storage when output is likely to contain
secrets or when a secret detector flags candidate material. The inspected
implementation does not currently guarantee that ordering; its stash-before-reject
behavior worsens the residual risk.

## 3. Storage location

| Candidate location | Workspace containment | Git hygiene | Sensitive-data assessment | Finding |
| --- | --- | --- | --- | --- |
| `.token-master/ccr.sqlite` | Only safe if resolved strictly under the current workspace. The inspected resolver can honor arbitrary `BRAINSPACE_CCR` paths and search upward through parent directories for `.token-master/ccr.sqlite`, so it can resolve outside cwd. | Must add `.token-master/`, `*.sqlite`, `*.sqlite-wal`, and related sidecar ignore rules. | TokenMaster-specific namespace would be new autoharness target output and could confuse ownership with Engram/backlog/autoharness state. | Acceptable for TokenMasterX, but not acceptable for autoharness without a containment-safe resolver. |
| `.autoharness/cache/brainspace/ccr.sqlite` or `.autoharness/ccr/` | **Least-bad only with a new resolver** that anchors to the workspace root/cwd, rejects `..`, symlink escapes, arbitrary absolute env paths, and upward parent search results outside cwd. | Must use a narrow ignore rule such as `.autoharness/cache/brainspace/` without hiding tracked `.autoharness/backlog-registry.yaml`, `config.yaml`, `harness-manifest.yaml`, or `workspace-profile.yaml`. | Keeps harness-managed runtime state under the harness namespace, but still stores sensitive exact originals beside tracked metadata. Requires purge, staged-file guards, and rollback for rejected compressions. | **Least-bad pilot location** if the feature is ever narrowed and accepted. |
| `.autoharness/metrics/` | Inside cwd and already gitignored in this repo. | Already ignored, but semantically wrong. | Raw outputs are not telemetry aggregates; mixing them with metrics invites accidental upload or analysis. | Reject. |
| `.git/` or another VCS-internal cache | Often inside cwd, but it mutates VCS internals and is hidden from normal review. | Not committed directly, but can corrupt or complicate repository maintenance. | Harder for operators and agents to inspect, purge, or reason about. | Reject. |
| User-home host cache such as `~/.claude/`, `~/.copilot/`, or a global CCR | Outside the target workspace in normal CLI mode and can mix workspaces. | Not part of repository git hygiene. | Violates autoharness CLI containment expectations and increases cross-project leakage risk. | Reject for generated autoharness workspace behavior. |
| OS temp directories | Usually outside cwd and volatile. | Not tracked, but not durable enough for reversible placeholders. | Violates the workspace-containment model and can lose originals while placeholders remain live. | Reject. |

**Storage recommendation:** no production CCR location is acceptable until the
operator accepts a data-retention and deletion policy. If a future pilot is
approved, use a repo-local, narrowly gitignored autoharness path such as
`.autoharness/cache/brainspace/`, never a user-home/global cache or OS temp. The
resolver must be rewritten to enforce Constitution IV containment: no arbitrary
absolute `BRAINSPACE_CCR`, no parent search outside cwd, and a hard resolved-path
check before every write. Add explicit ignore coverage for SQLite sidecars and a
guard that fails if CCR files are staged.

## 4. Representative benchmark tasks

A useful benchmark must prove two things at once: token/context savings and no
loss of required evidence. Each benchmark should measure raw tokens,
compressed tokens, projected area-under-curve savings over 1/3/5/10 turns,
visible inline evidence, CCR side effects, and retrieval behavior. The benchmark
must explicitly check that rejected/declined compression does **not** leave an
orphaned original in CCR.

### Compression-positive candidates

| Task | Output shape | Expected useful compression | Evidence that must remain visible |
| --- | --- | --- | --- |
| `pytest -vv` or `uv run python -m pytest -vv` on a passing or mostly passing run | Repetitive test log | Collapse repeated pass/progress lines; keep summary and counts. | Command, exit code, total passed/failed/skipped counts, slowest or failing tests. |
| `backlogit doctor` | Repeated backlog diagnostics; current baseline is about 62 pre-existing findings | Compress repeated finding bodies only if the final count and finding identifiers remain inline. | Overall verdict, finding count, any new-vs-baseline delta, item IDs, and remediation class. |
| Large `git --no-pager diff` or `git --no-pager diff --stat` plus patch | Patch/prose/code mix | Compress only orientation views or repeated generated hunks; avoid review-critical diffs unless retrieval is immediate. | File list, hunk headers, changed line counts, and any user-requested exact line. |
| Failed CI log from `gh run view --log-failed` | Verbose setup/install logs plus a small failure | Compress dependency-install noise and repeated framework output only if failure evidence is preserved. | Failing job, failing command, exit status, stderr, first actionable error, stack frame, annotation path/line, conclusion. |
| Verbose MCP JSON such as backlogit queue/list responses or GitHub check-run JSON | Structured JSON with repeated fields | Window arrays, summarize repeated records, and stash full JSON. | IDs, statuses, dependency/blocking fields, review/gate conclusions, pagination warnings. |
| Engram/graphtor-docs large search results | Long ranked result lists and document chunks | Keep top hits and stash long bodies or repeated metadata. | Source path/URL, chunk IDs, score/confidence, freshness/staleness warning, cited lines needed for the answer. |
| Workspace discovery or file inventory output | Large path lists | Summarize by directory/type and stash full listing. | Excluded paths, counts, and any paths selected for follow-up. |

### Compression-decline candidates

Compression must be declined for these cases even if a compressor could make the
text smaller:

* small outputs where placeholder/footer overhead loses the token-level
  never-expand check; the test must confirm no CCR row remains after the reject;
* security-sensitive outputs: tokens, `.env` content, auth output, environment
  dumps, private keys, or any output matching a secret detector;
* any tool result where failure evidence may live outside the one text field a
  hook captures, such as sibling `stderr`, `exit_code`, `status`, annotations, or
  structured error fields;
* gate verdicts and readiness blocks where the verdict itself is the artifact,
  such as local review readiness, CI aggregation verdicts, `autoharness gate ...`
  results, P0/P1 findings, or merge authorization summaries;
* active debugging stack traces when the first failure is the evidence the agent
  needs next;
* human/operator instructions and approval records, which must remain legible
  without tool-assisted expansion;
* any output whose source is not reproducible and whose CCR retention is not
  guaranteed for the current context window.

### Benchmark proof method

For each candidate, run raw and compressed variants against a predeclared task
question. A result counts as a safe win only when:

1. compressed tokens are lower under the selected tokenizer and under a cheap
   fallback estimator;
2. direct CCR retrieval is byte-equivalent for every visible placeholder, and the
   MCP `brainspace_retrieve` path either returns the full original or provides
   tested pagination/chunking for large originals;
3. rejected or declined compression attempts create no durable CCR rows;
4. the evidence oracle passes without retrieval for required inline facts,
   including stderr, exit status, and gate verdicts;
5. the model or evaluator can answer the task correctly from the compressed view,
   using retrieval only when the task explicitly needs hidden detail;
6. negative controls and decline cases are reported, not hidden.

This keeps savings honest: the benchmark is not allowed to win by hiding the
only stack trace, gate verdict, stderr line, exit status, or identifier needed to
make the decision.

## 5. Recommendation

**Recommendation: DEFER Brainspace-style compression for autoharness core.** If
the operator still wants exploration, narrow the next step to an opt-in pilot on
hosts with **current, verified** append-boundary output-rewrite support, or to a
benchmark-only prototype. Do not install transparent compression in the default
environment-agnostic harness.

Rationale:

* **Host parity is not solved.** TokenMasterX implements the full hook path for
  Claude Code and assumes Copilot CLI is MCP-only, but this spike did not verify
  current hook APIs for every supported host. Core autoharness behavior must
  remain environment-agnostic, and pilot scope must follow verified host support
  rather than stale assumptions.
* **The inspected full hook path can hide failure evidence.** The Claude hook
  extracts only one text field and does not preserve sibling `stderr` or exit
  status, so the only locally inspected transparent path still needs hardening.
* **CCR stores exact sensitive data, including rejected attempts.** Reversibility
  prevents information loss only when the placeholder remains visible and the
  store remains readable; the inspected stash-before-reject design can persist
  orphaned raw originals even when compression is not shown.
* **Reversibility is incomplete through the MCP surface.** Direct CCR retrieval
  can return full content, but `brainspace_retrieve` truncates large originals
  without pagination.
* **Storage is unresolved.** A repo-local `.autoharness/cache/brainspace/` store
  is the least-bad pilot path, but only with containment-safe path resolution,
  explicit gitignore, staged-file guardrails, purge tooling, and retention policy.
* **Measurement is required but 079-F/084-F are not hard gates for Option E.**
  Reuse their telemetry work if available, but the parent decision explicitly
  says final E scope depends on 086-F and not on 079-F. A standalone compression
  benchmark/measurement contract is sufficient if it proves savings, evidence
  preservation, retrieval, and no orphaned stashes.
* **Do not add a second graph stack.** Brainspace, if ever accepted, must be only
  a tool-output compression overlay. `agent-engram` remains the single graph
  authority; no TokenMaster graph supplier, graphify/codegraph abstraction, or
  duplicate structural-routing stack should be introduced.

Minimal acceptable future scope if the operator chooses to continue:

1. optional capability pack, disabled by default;
2. transparent mode only on hosts whose current APIs prove append-boundary
   output-rewrite support;
3. MCP/manual mode explicitly labeled degraded and not used to claim
   compression-on-write savings;
4. repo-local gitignored CCR store under `.autoharness/cache/brainspace/` with a
   containment-safe resolver, purge, TTL/size cap, SQLite checkpoint/compaction
   guidance, and staged-file checks;
5. decide-then-stash or stash-rollback-on-reject behavior;
6. full retrieval or paginated retrieval through the advertised MCP tool;
7. secret/PII detection plus conservative decline rules;
8. benchmark suite with positive and negative controls before any generated
   harness artifacts depend on it.

## Risks

* **Evidence hiding:** a compressed view can hide the one stack frame, gate
  verdict, review comment, stderr line, or exit status needed for safe action.
  The inspected Claude hook already has this class of defect because it selects
  one text field and ignores sibling failure fields.
* **Sensitive data persistence:** CCR intentionally stores exact originals, and
  the inspected stash-before-reject order can persist raw originals even when the
  compressed result is rejected and no placeholder is shown.
* **Incomplete advertised reversibility:** direct CCR retrieval returns full
  content, but MCP `brainspace_retrieve` truncates large originals without
  pagination, so large-output reversibility is not proven through the tool agents
  are told to use.
* **Containment escape:** the inspected resolver can honor arbitrary
  `BRAINSPACE_CCR` paths and parent-directory `.token-master/ccr.sqlite` files,
  which is not safe under autoharness CLI containment.
* **False parity claims:** MCP-only hosts can retrieve or explicitly compress but
  cannot be assumed to transparently rewrite arbitrary output before transcript
  entry. Current per-host hook APIs must be verified before scoping a pilot.
* **Deletion incompleteness:** row deletion and blob-size GC do not guarantee
  removal from SQLite free pages, WAL files, backups, or logs.
* **Operational complexity:** purge, retention, secret scanning, staged-file
  guards, per-host install logic, retrieval pagination, and hook payload fidelity
  all become part of the harness support burden.
* **Prompt-cache fragility:** placeholders must be deterministic and must not
  include timestamps or mutable counters, or compression can harm caching.
* **Benchmark overfitting:** repetitive logs and JSON may show large wins while
  prose, active debugging, and review-critical diffs should often decline.

## Open questions/preconditions

1. What current append-boundary/output-rewrite APIs exist for Claude Code,
   Copilot CLI, VS Code + Copilot, Codex, and Cursor? Pilot scope must follow
   verified host support, not TokenMasterX install-time assumptions.
2. What is the maximum allowed retention period and size for exact raw tool
   outputs, and who owns purge responsibility?
3. Must CCR be encrypted at rest, or are filesystem permissions and gitignore
   guardrails sufficient for local-only pilot data?
4. What secret/PII detection threshold should force compression decline before
   durable storage?
5. Should the implementation screen and decide before stashing, or create a
   transaction/rollback mechanism for stashes produced by rejected compression?
6. What retrieval API provides byte-equivalent recovery for large originals:
   no-cap MCP retrieval, pagination, chunked retrieval, or direct CCR-only tests?
7. What doctor/pre-commit/check should prove CCR SQLite, WAL, and related
   sidecar files are never staged or committed?
8. How should a compressed transcript behave when the CCR original has been
   purged but the placeholder remains in context?
9. What standalone compression benchmark/measurement contract is sufficient if
   079-F/084-F telemetry is unavailable or out of scope for Option E?
