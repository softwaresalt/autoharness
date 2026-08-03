"""Honest reporting renderer (085.006-T).

Composes correctness (:mod:`autoharness.eval.benchmark.scorer`) and
efficiency (:mod:`autoharness.eval.benchmark.metrics`) results into one
per-scenario + aggregate report and a plain-text rendering, enforcing the
plan's honest-reporting rules:

- **H1 (unavailable is never zero)**: a sentinel field delta
  (``"unavailable"`` / ``"not_applicable"``) is rendered literally as that
  string — never coerced to ``0`` or omitted.
- **H2 (surface provenance)**: every rendered field delta is shown alongside
  its :class:`~autoharness.eval.benchmark.metrics.FieldDelta.quality` label
  (``observed`` / ``derived`` / ``estimated`` / ``not_applicable`` /
  ``unavailable``) so a reader can see how certain a number is.
  ``estimated``/``derived`` aggregates are explicitly flagged, never
  presented as plain ``observed`` fact.
- **H3 (no efficiency win on regression)**: when
  :func:`~autoharness.eval.benchmark.scorer.regressed` is True for a
  scenario, the efficiency verdict is forced to
  ``"no-win-correctness-regression"`` **regardless of any favorable token
  delta** — a cheaper-but-wrong treatment run is never reported as a win.
- **H5 (retain degraded/negative runs)**: every scenario in the corpus is
  included in the report — including negative-class and degraded/cold-index
  scenarios — never filtered out because the run "failed".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from autoharness.eval.benchmark.controls import RunManifest
from autoharness.eval.benchmark.metrics import (
    AGGREGATE_SCOPE,
    NOT_APPLICABLE,
    FieldDelta,
    ScopeDelta,
    compute_aggregate_delta,
    compute_corpus_deltas,
)
from autoharness.eval.benchmark.scenarios import Scenario, ScenarioCorpus
from autoharness.eval.benchmark.scorer import CorrectnessScore, regressed, score_arm
from autoharness.telemetry.aggregation import UNAVAILABLE
from autoharness.telemetry.reader import TelemetryReadResult

_SENTINELS = (UNAVAILABLE, NOT_APPLICABLE)

#: The pair of economics fields used to decide the efficiency verdict when
#: correctness did not regress — token cost is the plan's primary economics
#: signal. A sentinel or non-numeric value on either field makes the verdict
#: "inconclusive" rather than a false-precision win/loss claim (H1).
_VERDICT_FIELDS: tuple[str, str] = ("input_tokens", "output_tokens")

Verdict = str  # "win" | "loss" | "neutral" | "inconclusive" | "no-win-correctness-regression"


def _efficiency_verdict(delta: ScopeDelta) -> tuple[Verdict, str | None]:
    """Decide the efficiency verdict from a scope's token deltas alone.

    Never claims a win/loss from a sentinel or non-numeric operand — that
    would silently manufacture a favorable/unfavorable ``0`` from missing
    data (H1).
    """
    total = 0.0
    for name in _VERDICT_FIELDS:
        field_delta = delta.fields.get(name)
        if field_delta is None:
            return "inconclusive", f"missing '{name}' delta"
        if field_delta.quality in _SENTINELS or isinstance(field_delta.delta, str):
            return (
                "inconclusive",
                f"'{name}' delta is {field_delta.delta} (quality={field_delta.quality}) — "
                "cannot claim an efficiency outcome from missing/inapplicable data",
            )
        total += float(field_delta.delta)  # type: ignore[arg-type]

    if total < 0:
        return "win", None
    if total > 0:
        return "loss", None
    return "neutral", None


@dataclass(frozen=True)
class ScenarioReport:
    """One scenario's composed correctness + efficiency report."""

    scenario_id: str
    scenario_class: str
    index_state: str
    outcome_classification: str
    degraded: bool
    baseline_score: CorrectnessScore
    treatment_score: CorrectnessScore
    correctness_regressed: bool
    delta: ScopeDelta
    verdict: Verdict
    verdict_reason: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "scenario_class": self.scenario_class,
            "index_state": self.index_state,
            "outcome_classification": self.outcome_classification,
            "degraded": self.degraded,
            "baseline_score": self.baseline_score.to_dict(),
            "treatment_score": self.treatment_score.to_dict(),
            "correctness_regressed": self.correctness_regressed,
            "delta": self.delta.to_dict(),
            "verdict": self.verdict,
            "verdict_reason": self.verdict_reason,
        }


@dataclass(frozen=True)
class BenchmarkReport:
    """The whole-corpus honest report: every scenario + the aggregate delta."""

    manifest: RunManifest
    scenario_reports: tuple[ScenarioReport, ...]
    aggregate_delta: ScopeDelta

    def to_dict(self) -> dict[str, object]:
        return {
            "manifest": self.manifest.to_dict(),
            "scenario_reports": [r.to_dict() for r in self.scenario_reports],
            "aggregate_delta": self.aggregate_delta.to_dict(),
        }


def compose_scenario_report(
    scenario: Scenario,
    *,
    outcome_classification: str,
    degraded: bool,
    baseline_produced: tuple[str, ...],
    treatment_produced: tuple[str, ...],
    delta: ScopeDelta,
) -> ScenarioReport:
    """Compose one scenario's report from its produced answers + precomputed delta.

    Correctness scoring is representative (repeat 0's produced answers) —
    the shipped :func:`~autoharness.eval.benchmark.harness.default_arm_executor`
    is deterministic across repeats for correctness (only economics fields
    disperse per repeat via seeded jitter), so scoring any single repeat is
    equivalent to scoring every repeat. A live-mode executor that varies
    correctness per repeat is explicitly out of scope (deferred).
    """
    baseline_score = score_arm(scenario.id, "baseline", baseline_produced, scenario.gold_answer)
    treatment_score = score_arm(scenario.id, "treatment", treatment_produced, scenario.gold_answer)
    regression = regressed(baseline_score, treatment_score)

    if regression:
        verdict: Verdict = "no-win-correctness-regression"
        reason: str | None = (
            "correctness regressed under treatment (scorer.regressed()==True); "
            "efficiency win suppressed regardless of any favorable token delta (H3)"
        )
    else:
        verdict, reason = _efficiency_verdict(delta)

    return ScenarioReport(
        scenario_id=scenario.id,
        scenario_class=scenario.scenario_class,
        index_state=scenario.index_state,
        outcome_classification=outcome_classification,
        degraded=degraded,
        baseline_score=baseline_score,
        treatment_score=treatment_score,
        correctness_regressed=regression,
        delta=delta,
        verdict=verdict,
        verdict_reason=reason,
    )


def build_report(
    corpus: ScenarioCorpus,
    results: Mapping[str, tuple],
    manifest: RunManifest,
    read_result: TelemetryReadResult,
) -> BenchmarkReport:
    """Build the whole-corpus :class:`BenchmarkReport` from a completed run.

    ``results`` is the ``run_corpus``/``run_benchmark`` return value
    (``scenario_id -> tuple[RepeatRun, ...]``); ``read_result`` is a
    :func:`~autoharness.telemetry.reader.read_epoch_records` read of the same
    isolated sink the run wrote to. Every scenario in ``corpus`` is included
    in the output, regardless of class or outcome (H5) — nothing is filtered.
    """
    scenario_ids = tuple(scenario.id for scenario in corpus.scenarios)
    per_scenario_deltas = compute_corpus_deltas(read_result, scenario_ids)
    aggregate_delta = compute_aggregate_delta(read_result, scenario_ids)
    classification_by_id = {c.scenario_id: c for c in manifest.scenario_classifications}

    reports = []
    for scenario in corpus.scenarios:
        repeat_runs = results[scenario.id]
        representative = repeat_runs[0]
        classification = classification_by_id.get(scenario.id)
        outcome_classification = (
            classification.outcome_classification if classification is not None else scenario.scenario_class
        )
        degraded = classification.degraded if classification is not None else False
        reports.append(
            compose_scenario_report(
                scenario,
                outcome_classification=outcome_classification,
                degraded=degraded,
                baseline_produced=representative.baseline.produced_answer,
                treatment_produced=representative.treatment.produced_answer,
                delta=per_scenario_deltas[scenario.id],
            )
        )

    return BenchmarkReport(
        manifest=manifest,
        scenario_reports=tuple(reports),
        aggregate_delta=aggregate_delta,
    )


def _render_field_delta(field_delta: FieldDelta) -> str:
    return (
        f"      {field_delta.field}: baseline={field_delta.baseline_total} "
        f"treatment={field_delta.treatment_total} delta={field_delta.delta} "
        f"(quality={field_delta.quality})"
    )


def _render_scenario(report: ScenarioReport) -> list[str]:
    lines = [
        f"- {report.scenario_id} "
        f"[class={report.scenario_class} outcome={report.outcome_classification} "
        f"index_state={report.index_state} degraded={report.degraded}]",
        f"    baseline: classification={report.baseline_score.classification} "
        f"exact_match={report.baseline_score.exact_match} "
        f"precision={report.baseline_score.precision} recall={report.baseline_score.recall}",
        f"    treatment: classification={report.treatment_score.classification} "
        f"exact_match={report.treatment_score.exact_match} "
        f"precision={report.treatment_score.precision} recall={report.treatment_score.recall}",
        f"    correctness_regressed={report.correctness_regressed}",
        f"    verdict={report.verdict}"
        + (f" ({report.verdict_reason})" if report.verdict_reason else ""),
        "    deltas:",
    ]
    lines.extend(_render_field_delta(fd) for fd in report.delta.fields.values())
    return lines


def render_honest_report(report: BenchmarkReport) -> str:
    """Render a :class:`BenchmarkReport` as honest, provenance-labeled plain text.

    Every scenario is listed (including negative-class and degraded runs —
    H5); every field delta is rendered with its literal value (sentinel
    strings shown verbatim, never coerced to ``0`` — H1) and its quality
    label (H2/H4); any regressed scenario's verdict is forced to
    ``no-win-correctness-regression`` regardless of token deltas (H3).
    """
    lines = [
        "Structural Navigation Benchmark — Honest Report",
        "=" * 48,
        f"workspace_id={report.manifest.workspace_id} commit_sha={report.manifest.commit_sha}",
        f"corpus_hash={report.manifest.corpus_hash} route={list(report.manifest.route)} "
        f"seed={report.manifest.seed} repeats={report.manifest.repeats}",
        f"degraded_tool_count_total={report.manifest.degraded_tool_count_total} "
        f"stale_or_unavailable_index_count_total={report.manifest.stale_or_unavailable_index_count_total}",
        "",
        "Per-scenario results:",
    ]
    for scenario_report in report.scenario_reports:
        lines.extend(_render_scenario(scenario_report))
        lines.append("")

    lines.append(f"Aggregate ({AGGREGATE_SCOPE}):")
    lines.extend(_render_field_delta(fd) for fd in report.aggregate_delta.fields.values())

    regressed_scenarios = [r.scenario_id for r in report.scenario_reports if r.correctness_regressed]
    lines.append("")
    lines.append(
        "Correctness-regressed scenarios (efficiency win suppressed, H3): "
        + (", ".join(regressed_scenarios) if regressed_scenarios else "none")
    )
    return "\n".join(lines)
