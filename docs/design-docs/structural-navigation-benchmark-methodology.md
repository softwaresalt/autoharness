# Structural-Navigation Benchmark Suite — Methodology & Interpretation Guide

**Status:** Deterministic core — implemented and reproducible. Live-run mode — deferred, additive
opt-in (not implemented by this shipment).

**Source (085-F / 111-S):**
[`docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md`](../plans/2026-08-02-structural-navigation-benchmark-suite-plan.md)

**Code:** `src/autoharness/eval/benchmark/` — `scenarios.py`, `harness.py`, `scorer.py`,
`metrics.py`, `controls.py`, `reporting.py`.

**Tests:** `tests/test_benchmark_{scenarios,harness,scorer,metrics,controls,reporting}.py`.

## 1. Purpose

This benchmark answers one question, honestly: *does routed (Engram-first) structural
navigation actually offload cost relative to raw read/grep, without making the agent wrong more
often?* It is deliberately narrow — a **deterministic replay core** over a small, hand-curated
scenario corpus — not a live, model-driven evaluation. The deterministic core exists so that a
published result is exactly reproducible by anyone with the same corpus, seed, and commit; it is
the foundation a future live-mode extension would build on, not a substitute for one.

## 2. Scenario classes and rationale

Every scenario in a corpus (`autoharness.eval.benchmark.scenarios.Scenario`) declares a
`scenario_class` of `positive`, `neutral`, or `negative`, and an `index_state` of `warm`, `cold`,
or `stale`. The loader enforces a **balanced-class invariant**: a corpus must contain at least one
scenario of each class, or `load_corpus`/`load_corpus_file` raises `CorpusError`. This exists to
guard against R2 (a cherry-picked corpus that only reports favorable cases):

- **`positive`** — a clean, answerable navigation task with a single unambiguous gold target.
  Establishes the case where an efficiency win is possible without correctness risk.
- **`neutral`** — an intentionally ambiguous or multi-target task (more than one plausible correct
  answer). This class's defining trait is the query's inherent ambiguity/multi-target nature, not
  guaranteed partial recall — under a warm index both arms can still be exact (the shipped fixture's
  `neutral-ambiguous-term-warm` scenario is exactly this case). The correctness scorer's
  partial-match axis is specifically exercised by pairing the `neutral` class with a degraded index
  state instead (the shipped fixture's `neutral-stale-partial-recall` scenario, under a `stale`
  index).
- **`negative`** — the gold answer is the **empty set** — there is no such symbol/module. Correctly
  reporting "not found" is the success condition here. Without this class, a corpus could reward
  an arm purely for producing *something*, regardless of whether nothing was the right answer.

`index_state` is a second, orthogonal axis: `warm` (a fully populated index), `cold` (empty/absent
index), and `stale` (partially populated or outdated). The shipped fixture
(`src/autoharness/eval/benchmark/fixtures/corpus.yaml`) deliberately pairs a `positive`-class
scenario with a `cold` index state (`pos-cold-index-miss`) — an otherwise-clean task exercised
under a degraded precondition — so the suite can demonstrate H5 (a degraded run is captured, never
dropped) and H3 (a correctness regression suppresses any efficiency-win claim) without needing a
fourth scenario class. Every scenario carries a documented `rationale` field explaining why it is
in the corpus — required by the loader, not optional prose.

## 3. Baseline / treatment arm definitions

Each scenario runs under exactly two arms (`autoharness.eval.benchmark.harness.Arm`):

- **`baseline`** — routing OFF. An exhaustive raw-read/grep oracle: expensive (high token/tool
  cost), but by construction it always recalls the scenario's gold answer exactly. This is a
  deliberate, documented simplification (R4): the baseline is defined as *always correct* so that
  only the treatment arm can regress, giving a clean, decidable ground truth for the correctness
  axis without needing a second live oracle.
- **`treatment`** — Engram-first routing ON. Cheap, but its recall is tied directly to the
  scenario's `index_state`: exact recall under `warm`, partial recall (drops the last gold target)
  under `stale`, and a full miss under `cold` — the deterministic proxy for a real routed-lookup
  failure under a degraded index.

Both arms are driven by `default_arm_executor()` — a **pure, deterministic function of
(scenario, arm, repeat_index, seed)**, not a live model call. Every synthesized economics/
operations value it produces is explicitly labeled `metric_quality: estimated` (H4) — the
methodology never lets a synthesized proxy masquerade as an `observed` measurement.

Each arm run emits exactly **one `ExecutionEpoch`** through the shipped, unmodified
`telemetry begin`/`telemetry record` path (`autoharness.telemetry.record.record_epoch`),
correlated by a synthetic `backlog_item_id` of the form
`benchmark:<scenario_id>:<repeat_index>:<arm>` (and `phase` of `benchmark-baseline` /
`benchmark-treatment`). One repeat therefore always produces **exactly two correlated epochs**
(one per arm) — **2×N epochs total for N repeats** — each with a unique per-repeat identity, so
repeats are always independently readable and never overwrite or collapse before persistence.

**Sink isolation (mandatory invariant):** every benchmark run targets an isolated
`TelemetryConfig` built by `isolated_benchmark_telemetry_config()`, which *refuses* to build a
config pointed at the repository's authoritative `.autoharness/metrics` store. Benchmark epochs
can never pollute production telemetry aggregates, and a benchmark reader is provably scoped to
only its own run-local sink.

## 4. Measures and their provenance rules

Every measure this suite reports maps to one of two axes, kept structurally separate
(`scorer.py` has no fields for tokens/cost; `metrics.py`/`reporting.py` never see the produced
answer set):

### 4.1 Correctness axis (`autoharness.eval.benchmark.scorer`)

| Measure | Definition | Provenance rule |
|---|---|---|
| `exact_match` | produced set == gold set (both empty counts as a match) | boolean, always defined |
| `precision` | `|produced ∩ gold| / |produced|` | `None` (undefined, not `0`) when nothing was produced |
| `recall` | `|produced ∩ gold| / |gold|` | `None` (undefined, not `0`/`1`) when the gold set is empty (negative scenarios) |
| `classification` | `exact` \| `partial` \| `miss` | derived structurally from the above |
| `regressed(baseline, treatment)` | treatment recalls strictly less than baseline, or baseline was exact and treatment is not | boolean; the sole correctness-regression signal `reporting.py` acts on |

### 4.2 Efficiency axis (`autoharness.eval.benchmark.metrics`)

Every efficiency field is a **`FieldDelta`**: `baseline_total`, `treatment_total`,
`delta = treatment_total - baseline_total`, and a `quality` label. Deltas are always computed from
**aggregate-total slices** (the sum of a field across every repeat in an arm) — **never** from
averaging per-epoch ratios; a delta's denominator is always an aggregate total, matching the
shipped `aggregate_epochs` contract.

Tracked fields: `input_tokens`, `output_tokens`, `cogs_usd`, `duration_seconds`,
`context_area_tokens`, `avoided_read_estimated_tokens`, `tool_output_estimated_tokens`
(economics); `routed_lookup_count`, `raw_file_read_count`, `raw_search_count` (operations); and
the derived `net_offload_tokens` (`avoided_read_estimated_tokens - tool_output_estimated_tokens`,
via the shipped `derived_efficiency_metrics`).

**The quality label is least-certain-wins across every operand** (`observed` < `derived` <
`estimated` < `not_applicable` < `unavailable`, in increasing uncertainty): a delta between an
`observed` baseline total and an `estimated` treatment total is itself `estimated`; if *any*
operand across every repeat epoch in either arm is `unavailable`, the whole delta is
`unavailable`; if the missing-ness is instead `not_applicable` (the metric genuinely does not
apply to this scope) and no `unavailable` operand is present, the delta is `not_applicable` — a
distinct sentinel, not collapsed into `unavailable`. **An empty record set — no epochs at all for
a scenario/arm — is `unavailable`, never a false-precision `observed` zero.** A populated,
unlabeled nonzero value is treated as a genuine provenance gap (`unavailable`), never assumed
`observed`; only an explicit zero-valued, unlabeled field is a legitimate `observed` zero-count
(a real "nothing happened here," not a missing measurement).

### 4.3 Reproducibility controls (`autoharness.eval.benchmark.controls`)

A `RunManifest` records: `workspace_id`, `commit_sha` (resolved via the existing eval frozen-state
seam, `autoharness.eval.runner.resolve_frozen_state` — `None`, never an exception, outside a git
checkout), `corpus_hash` (the scenario corpus's deterministic manifest hash — sha256 over the
sorted-by-id canonical JSON of every scenario), `route` (pinned to the deterministic-replay
identity), `seed`, `repeats`, the isolated sink paths, and roll-ups of
`degraded_tool_count_total` / `stale_or_unavailable_index_count_total` across every run. Two
identical `(corpus, seed, repeats)` runs reproduce identical dispersion values — dispersion is a
hash-seeded jitter, never a source of nondeterminism.

**Degraded/cold-index capture (H5, mandatory invariant):** a scenario whose treatment run degraded
is never dropped. `classify_scenario_runs()` always retains it (`ScenarioClassification.retained`
is always `True`) and demotes its **outcome classification** — never its underlying
`scenario_class` — from `positive` to `negative` (a real correctness failure, reported honestly)
or leaves any other class at `neutral`; it is never promoted back to `positive`.

## 5. Honest-reporting rules (`autoharness.eval.benchmark.reporting`)

The renderer composes the correctness and efficiency axes per scenario and in aggregate, and
enforces the following rules — these are the rules every measure above ultimately serves:

1. **Unavailable is never rendered as zero.** A sentinel field delta (`unavailable` /
   `not_applicable`) is displayed literally as that string in both the structured report and the
   plain-text rendering — never coerced to `0` or silently omitted.
2. **Provenance is always surfaced.** Every rendered field delta is shown alongside its
   `quality` label, so a reader can see at a glance how certain a number is; `estimated`/`derived`
   aggregates are never presented as plain observed fact.
3. **No efficiency win when correctness regressed (H3, the suite's central precedence rule).**
   When `scorer.regressed(baseline_score, treatment_score)` is `True` for a scenario, its verdict
   is forced to `"no-win-correctness-regression"` **unconditionally** — regardless of any favorable
   token delta the treatment arm shows. A cheaper-but-wrong run is never reported as a win. This is
   verified end to end for both the `cold`-index full-miss scenario and the `stale`-index
   partial-recall scenario in `tests/test_benchmark_reporting.py`.
4. **A sentinel token delta never manufactures a false win/loss.** When correctness did not
   regress, the efficiency verdict (`win` / `loss` / `neutral` / `inconclusive`) is decided from the
   `input_tokens`/`output_tokens` deltas; if either operand is `unavailable`/`not_applicable` or
   non-numeric, the verdict is `"inconclusive"` with an explicit reason — never a manufactured
   `win` or `loss` from missing data.
5. **Every corpus scenario is retained in the report** — including negative-class scenarios and
   degraded/cold-index runs — never filtered out because a run "failed." The aggregate delta is
   computed from the combined aggregate-total record pool across every scenario, never by
   averaging the per-scenario deltas.

**Correctness-over-efficiency precedence, stated plainly:** this benchmark's efficiency claims
are only meaningful in the absence of a correctness regression. An efficiency win is never a
mitigating factor for a correctness loss, and the reporting rules above make that unconditional
precedence structurally difficult to violate (rule 3), not just documented as guidance.

## 6. How to run

```python
from pathlib import Path
from autoharness.eval.benchmark.scenarios import load_default_corpus
from autoharness.eval.benchmark.controls import run_benchmark
from autoharness.eval.benchmark.reporting import build_report, render_honest_report
from autoharness.telemetry.config import TelemetryConfig
from autoharness.telemetry.reader import read_epoch_records

corpus = load_default_corpus()
results, manifest = run_benchmark(
    corpus,
    sink_root=Path("./benchmark-runs/example"),  # isolated sink — never .autoharness/metrics
    repeats=3,
    seed=0,
)

config = TelemetryConfig(
    enabled=True,
    mode="sqlite",
    database_path=Path(manifest.sink_database_path),
    emit_jsonl=True,
    jsonl_path=Path(manifest.sink_jsonl_path) if manifest.sink_jsonl_path else None,
)
read_result = read_epoch_records(config)
report = build_report(corpus, results, manifest, read_result)
print(render_honest_report(report))
```

A custom corpus can be supplied via `autoharness.eval.benchmark.scenarios.load_corpus_file(path)`
in place of `load_default_corpus()`; the loader enforces the same balanced-class invariant on any
corpus. The published `manifest.corpus_hash` lets a reader independently verify which exact corpus
content produced a given result.

## 7. Deterministic core vs. live mode

Everything above — the executor, the scoring, the deltas, the controls, and the reporting rules —
operates entirely on synthesized, deterministic proxy data (`default_arm_executor`); no task in
this shipment calls a live model or a live Engram/routing backend. This is the **deterministic
core**, and it is the reproducible unit this methodology guarantees: identical corpus + seed +
commit always reproduce an identical report.

**Live-run mode — replacing `default_arm_executor` with a real routed-navigation call against a
live index and a live grep/read baseline — is explicitly deferred and out of scope for this
shipment.** It is designed as an **additive opt-in extension point**: the `ArmExecutor` callable
type (`(Scenario, Arm, int, int) -> ArmOutcome`) is the seam a future live executor would
implement and pass to `run_scenario`/`run_corpus`/`run_benchmark` in place of the default, without
changing the scorer, metrics adapter, controls, or reporting renderer. A live executor is
expected to be non-deterministic run-to-run (real tool timing, real index staleness); this
methodology's reproducibility guarantee — corpus hash + pinned route/seed reproduce dispersion
exactly — is a property of the deterministic core specifically, and does not apply to a future
live-mode run. Determinism here is a controlled proxy for realism (R4), not a claim that the
underlying routed-navigation behavior itself is deterministic in production.
