---
title: "Copilot CLI Tool-Output Compression Experiment — Findings & Operator Decision Memo"
date: "2026-07-25"
description: "Findings from the 088-F throwaway, flag-gated Copilot CLI postToolUse compression experiment (shipment 093-S): benchmark results, hooks-contract re-verification, safety-invariant test evidence, and an ACCEPT/NARROW-PILOT/REJECT recommendation."
topic: "Should autoharness accept, narrow-pilot, or reject Copilot-CLI postToolUse tool-output compression as a future capability, based on the 088-F experiment's evidence?"
depth: "experiment-findings"
decision_status: "recommended"
doc_type: decision
source: docs/decisions/2026-07-25-copilot-cli-output-compression-experiment-findings.md
backlog_items:
  - "088-F"
  - "093-S"
  - "086-F"
linked_artifacts:
  - "docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md"
  - "docs/spikes/2026-07-15-copilot-cli-output-compression-experiment.md"
  - "docs/spikes/2026-07-13-brainspace-compression-feasibility.md"
  - ".backlogit/archive/086-F.md"
  - "experiments/088-compression-experiment/reports/benchmark-report.md"
  - "experiments/088-compression-experiment/reports/benchmark-report.json"
  - "https://docs.github.com/en/copilot/reference/hooks-reference"
tags:
  - "token-economics"
  - "brainspace"
  - "compression"
  - "primitive-1"
  - "primitive-7"
  - "operator-decision"
---

# Copilot CLI Tool-Output Compression Experiment — Findings & Operator Decision Memo

## Recommendation: **NARROW-PILOT**

Do **not** accept this prototype for a default/production capability-pack
install, and do **not** reject the underlying idea outright. The experiment
proves the core safety invariants hold — including several invariants that a
P-018 review round found genuinely incomplete and required real fixes for
(TTL dedup-on-expiry, size-cap dangling handles, MCP conformance, decline
coverage, secret-pattern coverage, containment of the `-journal` sidecar, and
a real type-aware compressor) — but it does **not currently prove any
positive token-savings claim** under the full six-criterion evidence
standard, because a real model tokenizer is unavailable in this environment.
This is a materially more conservative finding than an earlier draft of this
memo reported (see [Revision history](#revision-history)), and it is
consistent with the 2026-07-15 spike's own conclusion ("PROCEED to a bounded,
opt-in experiment/benchmark; keep production/default install DEFERRED") and
with 086-F's original caution about host parity, retention, and safe
reversible storage.

**Preconditions for a narrow pilot** (see [Preconditions](#preconditions-for-a-narrow-pilot)):

1. **Real model-tokenizer verification is now the single blocking
   precondition.** Add `tiktoken` (or an equivalent) as an explicit, isolated
   optional pilot dependency and re-run the benchmark corpus. Until this
   happens, the live hook cannot attempt compression on any case at all (a
   round-6 fix requires a confirmed real model tokenizer before the
   never-expand guard will authorize compression), so **zero** corpus cases
   can be reported as a proven safe win — see
   [Benchmark corpus results](#benchmark-corpus-results).
2. Replace the deterministic "required_fact substring" proxy for
   task-answerability with either a wider fact-extraction ruleset or a real
   model/evaluator pass, since the current oracle only catches facts it was
   told to look for.
3. Widen the benchmark corpus with additional real diff/log/JSON shapes now
   that a type-aware compressor exists (precondition #1 from the prior
   revision is **complete** — see below), so the type router's evidence
   preservation can be exercised on a live corpus case, not only unit tests.
4. Any pilot remains flag-gated, disabled by default, and confined to the
   `experiments/088-compression-experiment/` layout (or an equivalent
   clearly-isolated module) until a separate plan/review promotes it.

## Revision history

This memo was revised during a P-018 Copilot-review remediation round on
PR #229. The original benchmark run (HEAD `e7db334`) reported `SAFE WIN
count: 12` (of 13), including 5 of 6 compression-positive candidates. Two
review findings, once genuinely fixed, changed that materially:

* **Finding #1 (model-tokenizer-unavailable was silently treated as a pass).**
  `benchmark.py` previously set `lower_tokens_model = True` whenever no model
  tokenizer was available, making `lower_tokens_both` (and thus `safe_win`)
  vacuously achievable on fallback-estimator evidence alone. Fixed: an
  unavailable model tokenizer now forces `model_tokenizer_available = False`
  and `lower_tokens_both = False`, and the case is reported as **INCONCLUSIVE**
  rather than a safe win.
* **Finding #13 (decline-verdict patterns were incomplete).** `policy.py`'s
  decline patterns did not recognize `Blocking findings: P0=X, P1=Y`,
  `CI aggregation: <status>`, or bare `**P0**`/`**P1**` finding lines as
  gate/readiness verdicts. Once added, the live `git --no-pager log --stat
  -20` corpus capture — which, in this repository's real history, contains
  commit messages referencing P0/P1 review findings from prior fix rounds —
  is now correctly **declined outright** (no compression attempted at all),
  superseding the earlier "NOT a safe win — evidence oracle fails" verdict
  with an earlier, safer decline.
* **Finding #14 (type-aware compressor).** `hook.py::_compress_view` now
  routes JSON / git-log / unified-diff content through an evidence-preserving
  compressor (`_compress_lines_preserving_evidence`) that keeps every line
  matching a required-evidence pattern (commit/diff headers, PR/issue
  references, exit/stderr markers) regardless of position, instead of only
  the first/last 5 lines. This directly closes precondition #1 from the
  original memo. It is proven by dedicated unit tests
  (`test_hook_type_router.py`) showing a PR reference buried in the middle of
  a 20-commit synthetic `git log --stat` capture, and a similarly buried
  issue reference in a 200-line JSON payload, both survive compression.
  **It could not be demonstrated on the live corpus case**, because that case
  is now declined before compression is ever attempted (finding #13, above)
  — a strictly safer outcome than a compression attempt that might still
  need the type router's help.

Net effect: the compression-positive candidates achieving a genuine safe win
dropped from 5/6 to **0/6**, and the original run's "SAFE WIN count: 12"
figure is not comparable to later runs at all, for a second reason beyond
findings #1/#13/#14: a later round-3 follow-up finding (see below) found that
`safe_win_count` itself conflated two different things -- genuine
six-criteria compression-positive safe wins, and decline controls that
merely behaved correctly (declined, no durable row). The corrected report
now shows **0/6 six-criteria safe wins** and a separately-tracked
**7/7 decline-control-correct** count. This is reported here in full, not
softened — it is the honest, current state of the evidence.

### Round 2 (same PR, HEAD `1c400fe` → later): additional safety/protocol fixes

A fresh Copilot re-review, triggered automatically after the round-1 push,
found five more genuine issues. None of them changed the benchmark verdicts
above (still 0/6 six-criteria safe wins, 7/7 decline controls correct) — they
are safety/protocol/containment correctness fixes, not measurement changes:

* **Never-expand guard was char-count-only.** `hook.py`'s never-expand
  decision compared character counts only, so a structured result with many
  protected evidence lines could remain shorter than the original in chars
  while still exceeding the 10 KB `additionalContext` cap
  (`config.ADDITIONAL_CONTEXT_CAP_BYTES`). Fixed: the guard now also checks
  the UTF-8 encoded byte length of the compressed view + footer against the
  cap and declines if either check fails.
* **Hook/server workspace-pin consistency was undocumented.** The MCP
  server's example config pins `BRAINSPACE_WORKSPACE` in its own `env` block,
  but the hook's example config had no corresponding pin, so a tool run from
  a subdirectory could still diverge. Fixed: `hooks.json.example` now
  includes the same pin, and the README documents exporting
  `BRAINSPACE_WORKSPACE` in the session shell as the mechanism guaranteed to
  reach both subprocesses.
* **`benchmark_cli.py` used the OS temp area.** `tempfile.TemporaryDirectory()`
  with no `dir=` kwarg defaults to the OS temp area, violating the
  containment requirement that the store never live outside the
  repo-local, gitignored tree. Fixed: the ephemeral benchmark store is now
  anchored under `<repo-root>/.autoharness/cache/brainspace/`.
* **`purge_cli.py --repo-root` was silently overridden by the ambient env
  pin.** `resolve_workspace_root()` gave `BRAINSPACE_WORKSPACE` precedence
  over an explicit CLI argument, so `--mode all --repo-root X` could purge a
  different workspace's live rows than the one the operator named. Fixed:
  `resolve_workspace_root()` gained an `explicit_root` parameter that now
  takes the highest precedence, used by `purge_cli.py`'s `--repo-root`.
* **MCP server mishandled JSON-RPC notifications.** `notifications/initialized`
  (no `"id"` field) was answered with a method-not-found error carrying
  `id: null`, which JSON-RPC 2.0 / MCP forbid for notifications. Fixed:
  `handle_request` now returns `None` for any request without an `"id"`, and
  the stdio loop skips printing when the response is `None`.

### Round 3 (same PR, HEAD `2899834` → later): a third auto-triggered re-review

A third Copilot re-review triggered automatically after a subsequent, purely
non-code (backlog-tracking) push found twelve more issues across three
comment batches, all safety/containment/evidence-integrity-critical. None
change the **0/6 six-criteria safe wins** conclusion — they are correctness
fixes to code paths the benchmark corpus does not exercise, plus one fix to
the report's own metric definitions and one documentation-accuracy fix
(below):

* **MCP `output_retrieve` defaulted to a truncating page.** A handle-only
  call (no `offset`/`limit`) went through `retrieve_chunk`'s default
  65536-character page instead of the full byte-equivalent retrieval,
  silently truncating any original longer than the default page. Fixed:
  `dispatch_tool_call` now uses `retrieve_full` whenever neither `offset` nor
  `limit` was supplied, and only uses `retrieve_chunk` when pagination
  arguments are explicit.
* **Secret screening missed structured JSON/YAML key-value secrets.**
  `secret_screen.py`'s generic key-name detector only matched dotenv-style
  `KEY=value` lines, missing `{"password": "..."}` / `{"api_key": "..."}` /
  `client_secret: ...` forms that appear routinely in tool output (API
  responses, config dumps). Fixed: added a pattern that matches the common
  key names with either `:` or `=` and quoted or unquoted values.
* **Workspace resolution accepted an unrelated root with no containment
  check.** `resolve_workspace_root()`'s `explicit_root` and
  `BRAINSPACE_WORKSPACE` env-pin branches returned the candidate path
  without validating it against the process's actual working directory,
  so an arbitrary, unrelated absolute path could be honored. Fixed: both
  branches now validate the candidate is related to `os.getcwd()` (an
  ancestor, descendant, or the same directory) via a new
  `WorkspaceContainmentError`-raising check; genuinely unrelated trees
  (including cross-drive paths on Windows) are rejected.
* **`benchmark_cli.py --out-dir` had no containment validation.** The
  argument was passed directly to `os.makedirs`/report writers, so an
  absolute path or a `..`-relative path could write benchmark reports
  outside `--repo-root`. Fixed: `--out-dir` is now resolved against
  `--repo-root` (if relative) and validated to stay contained within it;
  an escaping path raises `ValueError` before anything is created.
* **`explicit_root` truthiness discarded an explicitly-supplied empty
  string.** `resolve_workspace_root()` used `if explicit_root:` instead of
  `if explicit_root is not None:`, so `purge_cli.py --repo-root ""
  --mode all` silently fell through to an ambient `BRAINSPACE_WORKSPACE`
  pin instead of being rejected -- changing which workspace's rows got
  purged despite the operator's explicit (if malformed) argument. Fixed: an
  explicitly-supplied empty root is now rejected outright rather than
  treated as "not supplied".
* **Staged-file guard failed open on a `git diff --cached` error.**
  `staged_guard.main()` ignored the subprocess's returncode/stderr; if the
  git invocation itself failed (not a git repo, git not on PATH, index
  issues), stdout was empty, no violations were found, and the guard
  exited 0 as if the index had been inspected and was clean. A pre-commit
  control protecting raw stored output must fail **closed**, not open.
  Fixed: a nonzero `git diff --cached` returncode now exits 1 with a clear
  message instead of silently reporting "no violations".
* **`test_purge_cli.py`'s expired-mode test did not actually exercise the
  CLI's purge path.** The test created rows with a 1-second TTL, but
  `purge_cli.main()` reopened the store with the (4-hour) default TTL, so
  `purge_expired()` purged zero rows; the test's own `store.get()`
  verification call lazily deleted the "expired" row as a side effect of
  reading it, masking that the CLI's purge path was never truly exercised.
  Fixed: added a `--ttl-seconds` override to `purge_cli.py` so tests (and
  operators with a non-default TTL store) can align the CLI's TTL with the
  store's, and the test now asserts the reported `Purged 1` count.
* **PR readiness block went stale again after a bookkeeping-only push.**
  A backlogit tracking commit advanced the PR HEAD without refreshing the
  `## Local Review Readiness` block, leaving mandatory current-HEAD review
  evidence stale. Addressed procedurally: the readiness block is refreshed
  to the final HEAD of this round before requesting re-review.
* **`safe_win_count` conflated two different things.** A decline control
  that behaved correctly (declined, left no durable row) was marked
  `safe_win=True` using only its own two checks, even though the module's
  documented standard requires **all six** spike proof-method criteria
  (§7.4) for a genuine compression-positive safe win. This meant every one
  of the corpus's 7 correctly-declining controls inflated `safe_win_count`
  to 7, even though 0 of the 6 compression-positive candidates met the full
  six-criteria standard -- a materially misleading headline number. Fixed:
  `CaseResult` now carries a separate `decline_correct` field (and
  `BenchmarkReport.decline_correct_count`); `safe_win` is always `False`
  for `decline_control` results. The regenerated report now correctly shows
  **`safe_win_count: 0`** and **`decline_correct_count: 7` (of 7)** — the
  underlying facts are unchanged (0/6 genuine compression-positive safe
  wins, all 7 decline controls behave correctly), only the metric that was
  conflating the two is fixed.
* **Third comment batch (arrived after the round-3 push): the payload-cwd
  resolution branch had NO containment check at all.**
  `resolve_workspace_root()` validated `explicit_root` and
  `BRAINSPACE_WORKSPACE`, but the third branch — `payload["cwd"]`, used by
  the hook when neither of those is set — returned the payload's cwd
  verbatim. A crafted or stale hook payload could carry an arbitrary
  absolute cwd unrelated to the process's actual working directory, so
  `hook_cli.py` would create the SQLite store outside the workspace despite
  the containment already claimed for the other two branches. Fixed: the
  payload-cwd branch now runs the same containment check; `hook_cli.py`
  catches `WorkspaceContainmentError` and fails safe to a no-op passthrough
  (`{}`) rather than crashing or writing outside the workspace.
* **`benchmark_cli.py --repo-root` was trusted without validation.**
  The previous round's `--out-dir` containment fix only validated `--out-dir`
  *relative to* `--repo-root` — but `--repo-root` itself was accepted
  verbatim from the operator with no check against the process's actual
  working directory, so `--repo-root /unrelated/path` would still create the
  cache and reports outside the current working tree. Fixed: `--repo-root`
  is now resolved through the same `resolve_workspace_root(explicit_root=…)`
  containment check used by every other 088-F entry point; an unrelated root
  now exits with an error before anything is created.
* **Benchmark corpus figures cited in this memo's table had drifted from the
  committed report.** Two live-command cases (`pytest-vv-experiment-suite`,
  `workspace-file-inventory`) capture genuinely live output whose exact
  token counts shift between runs (test counts, file inventory size); the
  table below had not been refreshed after a later report regeneration, so
  it no longer matched `reports/benchmark-report.json` as this memo itself
  promises. Fixed: the table was refreshed to the exact figures in the
  final regenerated report for this round.

### Round 4 (same PR, HEAD `91f939e` → later): a fourth auto-triggered re-review

A fourth Copilot re-review triggered automatically after Round 3's completion
push found two more safety-critical issues, both fixed:

* **Secret/PII screen had zero PII detectors despite its name.**
  `secret_screen.py`'s module docstring claimed "Secret/PII pre-screen", but
  every pattern in `_PATTERNS` targeted credential/token forms (API keys,
  passwords, PATs, JWTs, connection strings) — none detected common PII such
  as email addresses. Ordinary tool output (e.g. `git log` author lines like
  `Someone <someone@example.com>`) would pass the screen and be durably
  stored with no PII protection, contradicting the module's own claimed
  contract. Fixed: added an email-address pattern
  (`[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}`) to `_PATTERNS`, so any
  detected email address forces a decline before durable storage, and
  narrowed the module docstring to state explicitly that email addresses are
  the only PII family covered (not a general-purpose PII scanner) — avoiding
  an over-broad claim of protection this prototype does not implement (no
  phone numbers, SSNs, physical addresses, or names).
* **`purge_cli.py --ttl-seconds` accepted negative values, causing
  `--mode expired` to delete every live row.** The round-3 fix added a
  `--ttl-seconds` override for test alignment, but did not validate its
  sign. `purge_expired()` computes `cutoff = now - ttl_seconds`; a negative
  `ttl_seconds` therefore pushes `cutoff` into the *future*, so every row —
  including rows written moments earlier — is treated as "expired" and
  deleted. This turned the documented safe cleanup mode into a data-loss
  vector. Fixed: `purge_cli.main()` now rejects any `--ttl-seconds < 0` with
  a clear error message and a non-zero exit *before* the store is opened, so
  no purge runs at all on invalid input. Regression-tested: a store with a
  live row survives a `--ttl-seconds -5 --mode expired` invocation
  unchanged, and the CLI reports the rejection on stderr.

Neither Round 4 finding touches a code path the benchmark corpus exercises
for a compression-positive candidate (the email-PII fix only *narrows* what
the secret/PII screen accepts, which can only ever turn an existing
decline-control case into a decline, or turn a would-be compression case into
a decline — it cannot manufacture a new safe win). Regenerating the report
after this round confirms the **0/6 six-criteria safe wins** and
**7/7 correctly-behaving decline controls** conclusion is unchanged; only the
two non-deterministic live-command token counts shifted (test-suite growth
from the two new regression tests added this round), and the table below was
refreshed accordingly.

### Round 5 (2 findings from a fifth auto-triggered re-review): a required-invariant fix, not a cosmetic one

A fifth Copilot re-review triggered automatically after the round-4 push.
Both findings are genuine and one touches a plan hard invariant directly:

* **`hooks.json.example` used a bare `"command"` field.** The Copilot CLI
  hooks reference documents `command` as a valid cross-platform fallback
  (copied to both `bash` and `powershell` when those fields are absent), but
  the reviewer flagged the documented opt-in path as unverified/fragile
  against the current schema with only the fallback field set. Fixed:
  the template now sets explicit `bash` and `powershell` fields (both
  invoking the same Python entrypoint), removing any ambiguity about
  fallback-copying behavior. A new `test_config_templates.py` regression
  suite parses the template and pins both fields so this cannot silently
  regress again.
* **The "never-expand token+char guard" was character-count-only, not a
  real token comparison.** `hook.py`'s never-expand guard (088.002-T /
  088.004-T's documented decide-then-stash contract) compared only
  `len(candidate)` against `len(text)` before the round-3 byte-cap addition,
  and even after that addition it never compared actual token counts. A
  char-shorter candidate is not guaranteed to tokenize to fewer tokens
  (dense punctuation/unicode can tokenize less efficiently than the prose
  it replaced), so an enabled hook could still expand model context in a
  case that satisfies the char and byte checks but not a genuine token
  count reduction — directly contradicting the plan's non-negotiable
  "never-expand token+char guard" decide-then-stash invariant. Fixed:
  the guard now also compares `count_tokens(candidate)` against
  `count_tokens(text)` using the same tokenizer selection (`tiktoken` model
  tokenizer when available, else the cheap fallback estimator) the
  088.005-T measurement harness already uses, and declines (return `{}`,
  no store write) whenever tokens cannot be shown to decrease. A new
  regression test forces an adversarial token counter (fewer chars, more
  tokens) to prove the guard is genuinely token-aware, not char-count-only.

Regenerating the benchmark report after round 5 confirms the categorization
is unchanged (0/6 six-criteria safe wins, 7/7 correct decline controls) —
in this environment `count_tokens` falls back to the cheap char/4 estimator
(no `tiktoken` installed), which stays proportional to character count for
the corpus's existing cases, so no case's decline/compression outcome
flipped. Only the non-deterministic `pytest -vv` live-command token count
shifted again from the additional regression tests this round added, and
the table below was refreshed to match.

### Round 6 (2 findings from a sixth auto-triggered re-review): closing the gap between honest reporting and live hook behavior

A sixth Copilot re-review triggered automatically after the round-5 push.
Both findings are genuine; the first directly hardens the same never-expand
invariant round 5 touched, and materially changes what the benchmark corpus
can currently demonstrate:

* **The live hook could still stash/rewrite on an unproven fallback-only
  token estimate.** Round 5 added a real token-count comparison to the
  never-expand guard, but `count_tokens()` silently falls back to the cheap
  char/4 estimator whenever no real model tokenizer (`tiktoken`) is
  available — the same fallback this memo's own benchmark reporting already
  refuses to treat as proof (Round 1 finding #1: an unavailable model
  tokenizer is INCONCLUSIVE, never a pass). The live hook was not held to
  that same evidence bar: it would still stash the original and rewrite the
  tool output based on the fallback estimate alone, which cannot prove the
  replacement uses fewer *actual* Copilot-model tokens — a candidate that
  looks shorter by character count is not guaranteed to be shorter in real
  model tokens. Fixed: added a public
  `measurement.is_model_tokenizer_available()` helper, and the never-expand
  guard now declines (returns `{}`, no `store.put()`) whenever no real model
  tokenizer is available, rather than authorizing compression on the
  fallback estimate. This makes the live hook's behavior consistent with the
  benchmark's own honest INCONCLUSIVE reporting, at the cost of the
  prototype being a **complete no-op in any environment without a real model
  tokenizer installed** — see the updated
  [Benchmark corpus results](#benchmark-corpus-results) below. Regression
  tests cover both directions: a new test proves the guard declines
  dramatically-compressible content when no tokenizer is simulated as
  available, and the existing compression-path tests (previously exercised
  by the environment's real char/4 fallback) now explicitly simulate an
  available model tokenizer via monkeypatching, so they remain meaningful
  regression coverage independent of whether `tiktoken` happens to be
  installed wherever the suite runs.
* **Opportunistic purge cleanup was not fail-safe.** `hook_cli.py` called
  `store.purge_expired()` unguarded, in the same `try` block as
  `process_post_tool_use()`. A purge failure (lock contention, I/O error)
  after a result had already been decided — and potentially after a durable
  row had already been stashed with a retrieval handle already embedded in
  that decided result — would raise out of `main()` before the result was
  ever printed, silently dropping an already-created handle from the
  caller's point of view. Fixed: the purge call is now wrapped in its own
  `try/except`, treating a purge failure as non-fatal (best-effort cleanup)
  so it can never prevent the hook's already-computed `result` from being
  emitted. Two regression tests cover this: one confirms the hook still
  emits a valid result when purge raises, and a stronger one confirms this
  holds even when a durable row and retrieval handle were already created
  before the (simulated) purge failure.

Regenerating the benchmark report after round 6 shows a materially different
(and more conservative) result than every prior round: **all 6
compression-positive candidates now decline outright** ("hook declined this
case; not a compression candidate"), because this benchmark environment has
no real model tokenizer installed — matching the live hook's new,
stricter-but-honest behavior. The **headline conclusion is unchanged** (0/6
six-criteria safe wins, 7/7 correct decline controls — this memo's
recommendation was already predicated on zero proven safe wins), but the
*evidence detail* underneath it changed: rounds 1–5 could still show
detailed per-tokenizer fallback figures and label the state "INCONCLUSIVE";
round 6 shows the prototype cannot even attempt compression at all without a
real tokenizer. This strengthens (does not weaken) precondition #1: adding a
real model tokenizer is no longer merely required to *prove* savings — it is
now required for the prototype to *do anything at all*. The type-aware
compressor (round-3 finding #14) and the wider decline-verdict coverage
(round-3 finding #13) remain proven correct by their dedicated unit tests
(`test_hook_type_router.py`, `test_policy_decline_cases.py`); they are simply
never reached by the live corpus run now, one gate earlier than before.

### Round 7 (1 finding from a seventh auto-triggered re-review): closing a containment-boundary gap

* **The workspace-root resolver trusted any ancestor of `cwd`, unbounded.**
  `workspace.py`'s `_validate_related_to_process_cwd()` accepted any ancestor
  of the process `cwd` as a valid workspace-root candidate purely because
  `os.path.commonpath([candidate, cwd]) == candidate` — with no bound on how
  broad an ancestor could be (e.g. a filesystem root or a home directory).
  This is a genuine Constitution IV containment gap: an attacker-influenced
  or misconfigured explicit root could walk arbitrarily far up the tree and
  still be accepted. Fixed: added `_discover_repo_root()` (walks up from the
  real `cwd` looking for a `.git` marker) and `_is_ancestor_or_equal()`;
  ancestor-of-`cwd` candidates are now only trusted if they are bounded
  within the discovered repository root — an unbounded ancestor (no `.git`
  marker found, or broader than the discovered root) is rejected outright.
  Three new regression tests cover the unbounded-ancestor-without-repo-root
  rejection, the ancestor-broader-than-repo-root rejection, and the positive
  case (ancestor exactly at the repo root is still accepted, preserving the
  legitimate "pin repo root, `cd` into a subdirectory" use case this
  validation exists for).

Regenerating the benchmark report after round 7 shows no change — the
containment-resolver fix affects root discovery only, not the corpus content
or compression outcomes, so the round-6 figures (0/6 safe wins, 7/7 correct
decline controls, all six compression-positive candidates declining outright
for lack of a real tokenizer) stand unchanged.

### Round 8 (3 findings from an eighth auto-triggered re-review): closing an honesty gap and an evidence-loss gap

* **A loadable tokenizer could still silently fall back mid-encode.**
  `measurement.is_model_tokenizer_available()` only proves the tokenizer
  *loaded* (`tiktoken.get_encoding(...)` succeeded) — it does not prove
  `encode()` will succeed for a *specific* piece of text. `hook.py`'s
  never-expand guard called the fallback-tolerant `count_tokens()`, which
  would silently fall back to the char/4 estimator if the real tokenizer's
  `encode()` raised for that text, even though the guard's own gate believed
  a real-model token comparison had been proven. This could let a rewrite be
  authorized on fallback-only counts while reporting/believing the
  never-expand invariant held on real model tokens. Fixed: added a
  `ModelTokenizerUnavailable` exception and a new `count_tokens_strict()`
  that never silently falls back — it raises if no tokenizer is available OR
  if `encode()` fails for the given input — and the never-expand guard now
  calls `count_tokens_strict()`, declining (`return {}`, no store write)
  whenever it raises. `measure_dual()` (report-only) is separately hardened
  to catch the same exception and report `model: None` rather than crash.
  `count_tokens()` itself is unchanged and still intentionally
  fallback-tolerant for non-decision-authorizing callers (a dedicated
  regression test now pins down that this fallback tolerance is deliberate,
  not an oversight).
* **Corpus truncation could silently discard the fact a case was built to
  test.** `corpus.py`'s real-capture cases truncated captured command output
  with a prefix-only `text[:_MAX_CAPTURE_CHARS]`, then derived
  `required_fact` (via `last_nonblank_line`) from that *truncated* text. For
  outputs where the fact of interest — e.g. `pytest -vv`'s final pass/fail
  summary line — lives past the truncation boundary, this let the
  task-answerability criterion pass trivially without the real fact ever
  surviving truncation, silently masking evidence loss the criterion exists
  to catch (affected the `pytest -vv`, `backlogit doctor`, and
  workspace-file-inventory cases). Fixed: added `_truncate_preserving_tail()`
  (keeps a head prefix plus a tail suffix with an omission marker between
  them, mirroring the same head/tail strategy `hook.py`'s own prose
  compressor already uses) and all five real-capture cases now use it for
  `text` while deriving `required_fact` from the full, untruncated captured
  output.
* **The PR's own readiness block had gone stale across several rounds** (not
  a code defect) — flagged and corrected as part of this round's PR body
  update rather than a source change.

Regenerating the benchmark report after round 8 shows **no change** from
round 6/7's figures (0/6 six-criteria safe wins, 7/7 correct decline
controls) — in this benchmark environment there is still no real `tiktoken`
tokenizer installed, so every real-capture compression-positive case
continues to decline outright at the hook's never-expand guard before ever
reaching the corpus's truncation/required-fact logic, regardless of the
`count_tokens_strict()` rename or the head+tail truncation change. Both
round-8 fixes strengthen the harness's own honesty guarantees (never
authorizing a rewrite on an unproven token count; never letting a required
fact silently vanish under truncation) rather than changing what this
tokenizer-less environment can currently observe. The **headline
recommendation is unchanged**: zero proven safe wins, precondition #1 (a
real model tokenizer) still required before the prototype can compress
anything at all, let alone prove a net savings.

## Evidence summary

### Copilot CLI `postToolUse` hooks contract re-verification (plan condition #4)

**CONFIRMED — no material drift.** The 2026-07-15 spike's [CONFIRMED] claims
about the `postToolUse` hook contract were re-verified live against
[GitHub's hooks reference documentation](https://docs.github.com/en/copilot/reference/hooks-reference)
during this shipment:

* `postToolUse` receives `toolResult.textResultForLlm` and may return
  `modifiedResult` (replacing the transcript-visible result) or
  `additionalContext` (capped at 10 KB), matching the spike's contract.
* The matcher is compiled as `^(?:PATTERN)$` and must match the entire tool
  name — confirmed unchanged, and mirrored exactly in `hook.py`'s
  `_MATCHER_RE`.
* `postToolUseFailure` outputs cannot be rewritten by the hook contract —
  confirmed, and `process_post_tool_use_failure` always returns `{}}`.

The spike was written against locally observed CLI version `1.0.71`; the CLI
installed in this environment reports `1.0.72`/`1.0.75`. No schema or
semantic change was found between these point releases for the surfaces this
experiment depends on. **Residual caveat:** the hooks feature is explicitly
called out by GitHub as recent/evolving — any future pilot must re-run this
verification step before relying on the contract again, since no long-term
stability guarantee was found in the documentation.

### Safety invariants — proven by tests before any savings claim

Per plan condition #3 ("byte-equivalent retrieval and decide-then-stash are
validated by tests before any positive savings result is reported"), all of
the following were proven by passing tests *before* the benchmark corpus was
run:

| Invariant | Proof | Test evidence |
|---|---|---|
| Containment (Constitution IV) — resolver rejects `..`, absolute overrides, symlink escape, and `BRAINSPACE_CCR`-style env overrides | `resolver.py` | `test_resolver_containment.py` |
| Byte-lossless codec (`surrogatepass`, not `errors="replace"`) | `codec.py` | `test_codec_byte_lossless.py` |
| Decide-then-stash — no durable row for any declined attempt | `hook.py` + `policy.py` | `test_hook_decide_then_stash.py`, `test_policy_decline_cases.py` |
| Secret screening precedes durable storage, including fine-grained GitHub PATs | `secret_screen.py` + `policy.py` | `test_secret_screen.py`, `test_policy_decline_cases.py` |
| Fail-safe passthrough on any store/screen/guard error | `hook.py` | `test_hook_decide_then_stash.py::test_store_error_falls_back_to_byte_identical_passthrough` |
| Byte-equivalent retrieval (full + paginated, with strict offset/limit validation — no silent truncation) | `retrieval.py` | `test_retrieval_byte_equivalent.py` |
| Staged-file guard fails if store sidecars (including the rollback-journal `-journal` sidecar) are staged | `staged_guard.py` | `test_staged_file_guard.py` |
| Evidence oracle catches dropped required facts | `evidence_oracle.py` | `test_evidence_oracle.py` |
| TTL dedup refresh on re-put of expired content; no dangling handle on size-cap eviction | `store.py` | `test_store_roundtrip.py` |
| Disabled invocation makes zero durable writes | `hook_cli.py` | `test_hook_cli_entrypoint.py` |
| Consistent hook/server workspace-root resolution (subdirectory case) | `workspace.py` | `test_workspace_resolution.py` |
| MCP 2024-11-05 conformant `initialize`/`tools/call` results | `mcp_server.py` | `test_mcp_server_dispatch.py` |
| Type-aware compression preserves evidence outside head/tail (JSON/log/diff) | `hook.py` | `test_hook_type_router.py` |
| Real purge command + capture-failure honesty (non-zero returncode is never a safe win) | `purge_cli.py`, `corpus.py`, `benchmark.py` | `test_purge_cli.py`, `test_corpus_builder.py`, `test_benchmark_runner.py` |

All experiment tests pass (`python -m pytest
experiments/088-compression-experiment/tests -q`); see the shipment record
for the current pass count.

**A P-018 Copilot-review round on PR #229 found 15 issues, all fixed with
regression tests** (superseding the two findings fixed in an earlier local
adversarial review pass): honesty of the model-tokenizer criterion (#1),
rollback-journal sidecar containment (#2), pagination boundary validation
(#7), fine-grained PAT detection (#8), disabled-invocation zero-write (#9),
consistent hook/server workspace resolution (#12), MCP result conformance
(#5, #6), broader gate/readiness decline coverage (#13), a real type-aware
compressor (#14), and non-zero-returncode capture-failure honesty (#15),
plus TTL-dedup-of-expired-content refresh (#4), no-dangling-handle-on-
size-cap-eviction (#10), a real purge command (#11), and a corrected README
command reference (#3).

### Benchmark corpus results

`experiments/088-compression-experiment/reports/benchmark-report.{md,json}`
is the actual, live-generated report from this repository (not a mock-up),
regenerated after all review fixes through round 6 above (including the
type router, the `safe_win`/`decline_correct` metric split, and the round-6
no-model-tokenizer decline). 13 cases were run: 6 compression-positive
candidates and 7 decline/negative-controls, applying all six spike
proof-method criteria (§7.4 of the 2026-07-15 spike) to every case.

**Compression-positive candidates (0 of 6 currently prove a safe win — and,
as of round 6, none currently reach the hook's compression path at all):**

| Case | Provenance | Verdict |
|---|---|---|
| `pytest-vv-experiment-suite` | live (`python -m pytest ... -vv`) | **NOT a safe win** — hook declined this case; not a compression candidate |
| `backlogit-doctor-findings` | live (`backlogit doctor`) | **NOT a safe win** — hook declined this case; not a compression candidate |
| `git-log-stat-history` | live (`git --no-pager log --stat -20`) | **NOT a safe win** — hook declined this case; not a compression candidate |
| `backlogit-list-json-mcp-shaped` | live (`backlogit list --json`, truncated to 60 KB) | **NOT a safe win** — hook declined this case; not a compression candidate |
| `workspace-file-inventory` | live (`git ls-files`) | **NOT a safe win** — hook declined this case; not a compression candidate |
| `graphtor-search-results-representative` | **synthetic-representative** (no live Engram/graphtor MCP index in this benchmark run) | **NOT a safe win** — hook declined this case; not a compression candidate |

*As of the round-6 fix, the live hook's own never-expand guard requires an
available real model tokenizer (`measurement.is_model_tokenizer_available()`)
before it will authorize any compression at all — this benchmark environment
has no `tiktoken` installed, so every compression-positive candidate above now
declines before `_compress_view` or `store.put()` is ever reached, and no
per-tokenizer token-count figures are produced for this run. Rounds 1–5 of
this memo reported detailed fallback-estimator token counts for 5 of these 6
cases (labeled INCONCLUSIVE); those figures are no longer produced by a live
run and are superseded by this table. The historical per-round figures remain
readable in this document's git history and in
[Revision history](#revision-history) for anyone auditing how the evidence
narrowed round over round.*

**Why `git-log-stat-history` was already a decline before round 6, and why
that is unaffected by the round-6 change:** the broadened decline-verdict
patterns (finding #13) already recognize gate/readiness verdict text
(`P0`/`P1` finding markers) that this repository's own real commit history
contains, from prior review-fix rounds — this case declines via the
decline-case policy pre-screen, before the never-expand guard is ever
reached, both before and after round 6. The **type-aware compressor built to
fix a related evidence-loss category (finding #14) is proven by dedicated
unit tests** (`test_hook_type_router.py`) rather than by any live corpus case
now, since every compression-positive case in this run declines before the
compressor is ever invoked (the other 5 via round 6's no-tokenizer gate, this
one via the pre-existing policy pre-screen). Precondition #3 (below) asks for
a wider corpus that can exercise the type router on a live, non-declined
capture once a real tokenizer is available.

**Decline/negative controls (7 of 7 correctly declined, zero durable rows):**

| Case | Decline reason | Result |
|---|---|---|
| `tiny-output-decline` | tiny output | declined, no row |
| `unwritable-store-passthrough` | simulated store failure (fail-safe passthrough) | declined, no row |
| `secret-bearing-output-decline` | secret detector hit (AWS key pattern) | declined, no row |
| `gate-readiness-verdict-decline` | P-014 gate verdict text | declined, no row |
| `failure-bearing-gh-run-view-representative` | synthetic representative of a failed `gh run view --log-failed` | declined, no row |
| `active-stack-trace-decline` | Python traceback | declined, no row |
| `operator-approval-text-decline` | operator y/n approval prompt | declined, no row |

No decline case was hidden or omitted from the report (proof-method
criterion 6).

### Honesty caveats on the reported numbers

* **Model tokenizer unavailable in this environment** (`tiktoken` is not
  installed, and no new pip dependency was added per the plan's scope
  constraints). As of the round-6 fix, this is no longer merely a reporting
  caveat on token-count figures — it now means the **live hook itself
  declines to compress anything at all** (`is_model_tokenizer_available()`
  gates the never-expand guard before any candidate is even considered), so
  no token counts are produced by a live run in this environment at all,
  fallback or otherwise. **This is now precondition #1 (the single blocking
  precondition), strengthened**: no pilot should claim verified token
  savings without a real tokenizer check, and currently the prototype cannot
  attempt compression — let alone claim savings — without one.
* **`graphtor-search-results-representative` is synthetic**, not a live
  capture — no Engram/graphtor MCP server was running inside this benchmark
  process. It is a representative repetitive-JSON shape, clearly labeled via
  `BenchmarkCase.provenance`, and its savings numbers should not be read as
  measured production behavior (and, as of round 6, it currently declines
  outright rather than producing any savings numbers at all).
* **Task-answerability is a deterministic proxy**, not a live model/evaluator
  judgment: each case declares a `required_fact` substring, and the oracle
  checks whether that substring survives compression. This is honest and
  reproducible, but it can only catch facts it was told to look for —
  precondition #2 addresses this gap directly. This criterion currently
  cannot even be exercised by a live corpus run for the same reason as
  above (every compression-positive case declines before it is reached).
* **A non-zero command-capture returncode can never be a safe win** (finding
  #15, fixed): `corpus.py`'s command runner now labels a non-zero exit as a
  capture failure, and `benchmark.py` unconditionally forces `safe_win =
  False` for any capture-failed case, regardless of other criteria. No
  corpus case in this run hit this path, but the honesty guarantee is now
  covered by tests (`test_corpus_builder.py`, `test_benchmark_runner.py`).

## Scope decisions carried into this recommendation

* The prototype was built entirely under
  `experiments/088-compression-experiment/`, imported by nothing in
  `src/autoharness`, and is trivially removable (delete the directory,
  optionally purge `.autoharness/cache/brainspace/` via the new
  `purge_cli.py --mode all`).
  `hooks.json.example` and `mcp.json.example` were deliberately **not**
  wired into `.github/hooks/` or the committed root `.mcp.json` — they
  remain opt-in templates so the experiment never auto-activates for every
  contributor's CLI session (see the experiment README for the rationale).
* No schema changes, no CLI-distribution changes, and no new pip
  dependencies were introduced (plan condition #2).
* `agent-engram` remains the sole graph authority; this experiment does not
  introduce a second graph stack (consistent with the 2026-07-13 TokenMasterX
  decision's rejection of option C).

## Preconditions for a narrow pilot

Before any follow-up feature considers widening this beyond the current
throwaway experiment:

1. **Real tokenizer verification (blocking).** Add `tiktoken` (or an
   equivalent) as an explicit, isolated optional dependency for the pilot
   only, and re-run the benchmark corpus to determine whether savings hold
   under a real tokenizer. Until this happens, this experiment has proven
   **zero** cases meeting the full six-criterion safe-win standard, and, as
   of the round-6 fix, the live hook cannot attempt compression on any case
   at all without one (`is_model_tokenizer_available()` gates the
   never-expand guard before any candidate is considered).
2. **Stronger task-answerability proof.** Extend the evidence oracle's fact
   patterns and/or add a real model-graded answerability check for a
   broader sample of benchmark cases, rather than relying solely on
   predeclared substrings.
3. **Wider, more adversarial corpus that can exercise the type router live.**
   The type-aware compressor (precondition from the prior revision, now
   complete and unit-tested) has not yet been proven against a live,
   non-declined corpus capture, because the one corpus case it targeted
   (`git-log-stat-history`) is now declined outright by the broadened
   decline-verdict patterns. Add a real capture (e.g. a `git diff` on a
   feature branch without gate/readiness text in its messages, or a
   `git log --stat` window from a period without review-finding
   references) to prove the type router's evidence preservation in
   production-shaped, non-synthetic conditions.
4. **Explicit product/security sign-off** on retention (TTL/size-cap
   defaults), before even a narrow pilot is enabled by default for any
   contributor — the flag must stay opt-in.

## Disposition

Recommend the shipment proceed to PR/review with this memo attached as the
experiment's findings record. The flag (`BRAINSPACE_EXPERIMENT_ENABLED`)
stays **disabled by default**; no base-harness behavior depends on this
code; the entire `experiments/088-compression-experiment/` tree remains
trivially removable if the operator instead chooses REJECT. The current
state of the evidence is: **safety mechanism proven; savings unproven** —
this is precisely the situation a narrow, precondition-gated pilot exists to
resolve, not a reason to accept or reject outright.
