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
proves the core safety invariants hold and that honest, evidence-preserving
token savings are achievable on several real autoharness command outputs —
but it also surfaces one concrete correctness gap (a naive compressor is not
safe for every output shape) and one unverifiable claim (real model-tokenizer
savings) that must be closed before any wider pilot. This recommendation is
consistent with the 2026-07-15 spike's own conclusion ("PROCEED to a bounded,
opt-in experiment/benchmark; keep production/default install DEFERRED") and
with 086-F's original caution about host parity, retention, and safe
reversible storage.

**Preconditions for a narrow pilot** (see [Preconditions](#preconditions-for-a-narrow-pilot)):

1. Replace the naive head/tail compressor with a genuine type-aware router
   (JSON / log / diff / prose) so structured outputs (diffs, stat summaries)
   don't lose facts that live outside the first/last N lines.
2. Verify real token savings under an actual model tokenizer (e.g. add
   `tiktoken` as an optional pilot dependency) rather than the fallback
   char/4 estimator alone.
3. Replace the deterministic "required_fact substring" proxy for
   task-answerability with either a wider fact-extraction ruleset or a real
   model/evaluator pass, since the current oracle only catches facts it was
   told to look for.
4. Any pilot remains flag-gated, disabled by default, and confined to the
   `experiments/088-compression-experiment/` layout (or an equivalent
   clearly-isolated module) until a separate plan/review promotes it.

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
| Secret screening precedes durable storage | `secret_screen.py` + `policy.py` | `test_secret_screen.py`, `test_policy_decline_cases.py` |
| Fail-safe passthrough on any store/screen/guard error | `hook.py` | `test_hook_decide_then_stash.py::test_store_error_falls_back_to_byte_identical_passthrough` |
| Byte-equivalent retrieval (full + paginated, no silent truncation) | `retrieval.py` | `test_retrieval_byte_equivalent.py` |
| Staged-file guard fails if store sidecars are staged | `staged_guard.py` | `test_staged_file_guard.py` |
| Evidence oracle catches dropped required facts | `evidence_oracle.py` | `test_evidence_oracle.py` |

All 110 experiment tests pass (`python -m pytest
experiments/088-compression-experiment/tests -q`).

**Two findings from local adversarial review were fixed before this memo was
finalized** (see the shipment's Step 3 review record):

* **P0 (containment/gitignore gap):** the store is anchored to the Copilot
  CLI session `cwd`, which may be any subdirectory of the repo, not just the
  repo root. The original `.gitignore` patterns and `staged_guard.py`'s
  matcher only recognized a repo-root-relative store path, so a store
  nested under a subdirectory could be gitignore-missed and git-staged
  undetected. Fixed by making both the gitignore patterns (`**/` prefix) and
  `staged_guard.find_staged_store_violations` match the store directory at
  any nesting depth; verified live against the exact reproduction the
  reviewer supplied.
* **P1 (TTL silently extended on dedup):** `BrainspaceStore.put()` used
  `INSERT OR REPLACE`, which reset `stored_at` on every re-put of identical
  content — contradicting the store's own documented retention invariant
  ("never silently extended on dedup/access", carried forward from 086-F).
  Fixed by switching to `INSERT OR IGNORE` so a dedup re-put is a true no-op
  on the existing row's timestamp. A regression test
  (`test_dedup_put_does_not_extend_ttl_clock`) now proves this.

### Benchmark corpus results

`experiments/088-compression-experiment/reports/benchmark-report.{md,json}`
is the actual, live-generated report from this repository (not a mock-up).
13 cases were run: 6 compression-positive candidates and 7 decline/
negative-controls, applying all six spike proof-method criteria
(§7.4 of the 2026-07-15 spike) to every case.

**Compression-positive candidates (5 of 6 are genuine SAFE WINs):**

| Case | Provenance | Raw tokens (fallback) | Compressed tokens (fallback) | Net savings | Verdict |
|---|---|---:|---:|---:|---|
| `pytest-vv-experiment-suite` | live (`python -m pytest ... -vv`) | 3,782 | 218 | 3,564 (94%) | SAFE WIN |
| `backlogit-doctor-findings` | live (`backlogit doctor`) | 3,654 | 401 | 3,253 (89%) | SAFE WIN |
| `git-log-stat-history` | live (`git --no-pager log --stat -20`) | 6,258 | 150 | 6,108 (98%) | **NOT a safe win** — evidence oracle fails |
| `backlogit-list-json-mcp-shaped` | live (`backlogit list --json`, truncated to 60 KB) | 15,000 | 250 | 14,750 (98%) | SAFE WIN |
| `workspace-file-inventory` | live (`git ls-files`) | 13,224 | 118 | 13,106 (99%) | SAFE WIN |
| `graphtor-search-results-representative` | **synthetic-representative** (no live Engram/graphtor MCP index in this benchmark run) | 8,827 | 323 | 8,504 (96%) | SAFE WIN (representative only) |

*Exact token counts drift slightly between benchmark runs because several
cases capture genuinely live command output (test counts, git history
length, file inventory) that changes as the repository itself changes — the
percentages and safe-win/not-safe-win verdicts are stable across runs.
Numbers above match `reports/benchmark-report.json` as of the reviewed HEAD.*

**The one honest negative finding matters most:** `git-log-stat-history`
fails the evidence oracle because the naive head/tail compressor
(`hook.py::_compress_view`) can drop required facts (e.g. a commit hash or a
`#issue` reference) that fall in the collapsed middle of a large `git log
--stat` output rather than the head or tail. This is **not hidden** — it is
reported plainly as `NOT a safe win` in both the Markdown and JSON report.
It is the direct evidence behind precondition #1 above: the compressor needs
real type-awareness (a diff/log-specific strategy that preserves commit
boundaries, hashes, and file-change summaries) before any output shaped like
a diff or commit log can be trusted to compress safely.

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
  constraints). Every reported token count above is the cheap fallback
  estimator (~4 chars/token), not a real GPT-family tokenizer. The
  `lower_tokens_model` criterion is reported as vacuously `True` (not
  disprovable without a tokenizer) rather than fabricated — this is called
  out explicitly in every report row's notes column. **This is precondition
  #2**: no pilot should claim verified token savings without a real
  tokenizer check.
* **`graphtor-search-results-representative` is synthetic**, not a live
  capture — no Engram/graphtor MCP server was running inside this benchmark
  process. It is a representative repetitive-JSON shape, clearly labeled via
  `BenchmarkCase.provenance`, and its savings numbers should not be read as
  measured production behavior.
* **Task-answerability is a deterministic proxy**, not a live model/evaluator
  judgment: each case declares a `required_fact` substring, and the oracle
  checks whether that substring survives compression. This is honest and
  reproducible, but it can only catch facts it was told to look for —
  precondition #3 addresses this gap directly.

## Scope decisions carried into this recommendation

* The prototype was built entirely under
  `experiments/088-compression-experiment/`, imported by nothing in
  `src/autoharness`, and is trivially removable (delete the directory,
  optionally purge `.autoharness/cache/brainspace/`).
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

1. **Type-aware compressor.** Replace `_compress_view`'s naive head/tail
   strategy with routing by output shape (JSON, log, diff/git-stat, prose),
   preserving diff hunks/commit boundaries and structural markers, not just
   the first/last N lines.
2. **Real tokenizer verification.** Add `tiktoken` (or an equivalent) as an
   explicit, isolated optional dependency for the pilot only, and re-run the
   benchmark corpus to confirm savings hold under a real tokenizer, not just
   the fallback estimator.
3. **Stronger task-answerability proof.** Extend the evidence oracle's fact
   patterns and/or add a real model-graded answerability check for a
   broader sample of benchmark cases, rather than relying solely on
   predeclared substrings.
4. **Wider, more adversarial corpus.** Add more real command captures
   (additional `git diff` shapes, large multi-file JSON, nested error
   payloads) specifically targeting the type-router gap found here.
5. **Explicit product/security sign-off** on retention (TTL/size-cap
   defaults), before even a narrow pilot is enabled by default for any
   contributor — the flag must stay opt-in.

## Disposition

Recommend the shipment proceed to PR/review with this memo attached as the
experiment's findings record. The flag (`BRAINSPACE_EXPERIMENT_ENABLED`)
stays **disabled by default**; no base-harness behavior depends on this
code; the entire `experiments/088-compression-experiment/` tree remains
trivially removable if the operator instead chooses REJECT.
