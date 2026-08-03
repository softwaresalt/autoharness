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
  Correctness is scored across **every** repeat, not just one (review-fix):
  scoring only repeat 0 while the efficiency delta aggregates *all* repeats
  could let a later repeat's regression slip past this rule; any
  cross-repeat disagreement fails closed
  (:class:`RepeatCorrectnessVarianceError`) instead of silently reporting
  one repeat as representative.
- **H5 (retain degraded/negative runs)**: every scenario in the corpus is
  included in the report — including negative-class and degraded/cold-index
  scenarios — never filtered out because the run "failed".
- **H6 (same-run identity, review-fix)**: ``corpus``, ``results``,
  ``manifest``, and ``read_result`` are four independently-suppliable
  objects with nothing upstream binding them together. :func:`build_report`
  fails closed (raises :class:`ReportIdentityError`) unless it can verify
  they all describe **one** run: the corpus hash, scenario/repeat counts,
  exact-cardinality sink-record presence, and a unique per-run ``run_id``
  (stamped onto every epoch's ``session_id`` at write time — distinct from
  the possibly-reused ``workspace_id``) all must agree. This is a
  whole-run identity check, not a field-level provenance label — a
  mismatch is a caller programming error and must surface loudly rather
  than silently blend two runs into one plausible report (H1 governs
  missing/uncertain *field* data, not whole-run mixing).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from autoharness.eval.benchmark.controls import RunManifest
from autoharness.eval.benchmark.harness import ARMS, BENCHMARK_NAMESPACE_PREFIX
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


class ReportIdentityError(ValueError):
    """Raised when ``build_report``'s inputs are not verifiably one run (H6).

    ``corpus``/``results``/``manifest``/``read_result`` are independently
    supplied; this is raised instead of silently composing a report from a
    mismatched combination (e.g. a stale ``results`` from a prior run, a
    ``corpus`` revision that no longer matches ``manifest``, or a
    ``read_result`` read from a different sink).
    """


class RepeatCorrectnessVarianceError(ValueError):
    """Raised when a scenario's correctness score varies across repeats (H3, review-fix).

    ``compose_scenario_report`` assumes every repeat scores identically for
    correctness (the shipped executor is deterministic on that axis); a
    caller-supplied executor that legitimately varies correctness by
    ``repeat_index`` violates that assumption and is refused rather than
    silently reported from a single, possibly-non-representative repeat.
    """


def _validate_run_identity(
    corpus: ScenarioCorpus,
    results: Mapping[str, tuple],
    manifest: RunManifest,
    read_result: TelemetryReadResult,
) -> None:
    """Fail closed unless ``corpus``/``results``/``manifest``/``read_result`` are one run (H6).

    Five checks, each raising :class:`ReportIdentityError` on failure:

    1. ``corpus.manifest_hash == manifest.corpus_hash`` — the corpus
       revision matches the one the manifest was recorded against.
    2. ``results`` and ``manifest.scenario_classifications`` cover exactly
       ``corpus``'s scenario ids — no missing or extra scenarios.
    3. Every scenario's repeat-run count in ``results`` equals
       ``manifest.repeats``.
    4. ``read_result`` actually holds this run's sink records: for every
       expected ``benchmark:<scenario_id>:<repeat_index>:<arm>`` epoch,
       **exactly one** matching record is present (never zero, never more
       than one — a duplicate/extra matching record would otherwise be
       silently summed into the aggregate by
       :func:`~autoharness.eval.benchmark.metrics.scenario_arm_records`).
    5. Every one of those records carries ``session_id == manifest.run_id``
       (review-fix; see ``run_id`` below) and, as a secondary check,
       ``workspace_id == manifest.workspace_id``.

    A failed/unavailable/disabled read, a missing record, a duplicate
    record, or any run_id/workspace_id mismatch is refused outright rather
    than silently rendered as an ``unavailable`` field (whole-run mixing is
    not a field-level provenance gap governed by H1).

    Why ``run_id`` and not just ``workspace_id``: ``workspace_id`` defaults
    to a fixed constant (``DEFAULT_WORKSPACE_ID``) unless a caller supplies
    a distinct value per call, so two separate ``run_benchmark`` invocations
    against the same corpus/repeat shape (e.g. different seeds) can share
    an identical ``workspace_id`` — a ``workspace_id``-only check would not
    catch a ``results``/``read_result`` pair silently swapped between them.
    ``run_id`` is a fresh ``uuid4`` hex minted once per ``run_benchmark``
    call (never reused, never caller-suppliable) and stamped onto every
    epoch's ``session_id`` field, so it is a positive, run-unique
    correlation key rather than a caller-controlled, possibly-shared label.
    """
    if corpus.manifest_hash != manifest.corpus_hash:
        raise ReportIdentityError(
            f"corpus.manifest_hash ({corpus.manifest_hash!r}) does not match "
            f"manifest.corpus_hash ({manifest.corpus_hash!r}); results/manifest were not "
            "produced from this corpus revision."
        )

    corpus_ids = {scenario.id for scenario in corpus.scenarios}
    result_ids = set(results.keys())
    if corpus_ids != result_ids:
        raise ReportIdentityError(
            "results does not cover exactly corpus's scenarios "
            f"(missing={sorted(corpus_ids - result_ids)}, extra={sorted(result_ids - corpus_ids)})."
        )

    classification_ids = {c.scenario_id for c in manifest.scenario_classifications}
    if classification_ids != corpus_ids:
        raise ReportIdentityError(
            "manifest.scenario_classifications does not cover exactly corpus's scenarios "
            f"(missing={sorted(corpus_ids - classification_ids)}, "
            f"extra={sorted(classification_ids - corpus_ids)})."
        )

    for scenario_id, repeat_runs in results.items():
        if len(repeat_runs) != manifest.repeats:
            raise ReportIdentityError(
                f"results[{scenario_id!r}] has {len(repeat_runs)} repeat run(s); "
                f"manifest.repeats={manifest.repeats}."
            )

    if read_result.status not in ("ok", "empty"):
        raise ReportIdentityError(
            f"read_result.status={read_result.status!r} is not a successful telemetry read; "
            "refusing to compose a report from a failed/unavailable/disabled read."
        )

    records_by_backlog_id: dict[str, list[Mapping[str, object]]] = {}
    for record in read_result.records:
        backlog_item_id = record.get("backlog_item_id")
        if isinstance(backlog_item_id, str) and backlog_item_id.startswith(BENCHMARK_NAMESPACE_PREFIX):
            records_by_backlog_id.setdefault(backlog_item_id, []).append(record)

    missing: list[str] = []
    duplicated: list[str] = []
    mismatched_run_id: list[str] = []
    mismatched_workspace: list[str] = []
    for scenario_id in corpus_ids:
        for repeat_index in range(manifest.repeats):
            for arm in ARMS:
                backlog_item_id = f"{BENCHMARK_NAMESPACE_PREFIX}{scenario_id}:{repeat_index}:{arm}"
                matches = records_by_backlog_id.get(backlog_item_id, [])
                if not matches:
                    missing.append(backlog_item_id)
                    continue
                if len(matches) > 1:
                    duplicated.append(backlog_item_id)
                    continue
                (record,) = matches
                if record.get("session_id") != manifest.run_id:
                    mismatched_run_id.append(backlog_item_id)
                if record.get("workspace_id") != manifest.workspace_id:
                    mismatched_workspace.append(backlog_item_id)

    if missing:
        raise ReportIdentityError(
            f"read_result is missing {len(missing)} epoch record(s) expected for this run "
            f"(e.g. {missing[:3]}); read_result does not appear to be this run's sink."
        )
    if duplicated:
        raise ReportIdentityError(
            f"read_result has more than one record for {len(duplicated)} expected epoch "
            f"identity/identities (e.g. {duplicated[:3]}); refusing to silently sum "
            "duplicate/extra records into the aggregate."
        )
    if mismatched_run_id:
        raise ReportIdentityError(
            f"{len(mismatched_run_id)} epoch record(s) matched this run's scenario/repeat/arm "
            f"identity but carry a session_id other than manifest.run_id ({manifest.run_id!r}) "
            f"(e.g. {mismatched_run_id[:3]}); read_result appears to mix records from a "
            "different run."
        )
    if mismatched_workspace:
        raise ReportIdentityError(
            f"{len(mismatched_workspace)} epoch record(s) matched this run's scenario/repeat/arm "
            f"identity but carry a workspace_id other than manifest.workspace_id "
            f"({manifest.workspace_id!r}) (e.g. {mismatched_workspace[:3]}); read_result appears to "
            "mix records from a different run."
        )


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
    baseline_produced_by_repeat: tuple[tuple[str, ...], ...],
    treatment_produced_by_repeat: tuple[tuple[str, ...], ...],
    delta: ScopeDelta,
) -> ScenarioReport:
    """Compose one scenario's report from every repeat's produced answers + a precomputed delta.

    Correctness is scored for **every** repeat (review-fix, H3+H6), not just
    a single representative one: the shipped
    :func:`~autoharness.eval.benchmark.harness.default_arm_executor` is
    deterministic across repeats for correctness (only economics fields
    disperse per repeat via seeded jitter), so every repeat's score is
    *expected* to agree — but ``build_report``/``run_benchmark`` accept an
    arbitrary ``ArmExecutor``, and a live-mode executor may legitimately
    vary correctness by ``repeat_index``. Scoring only repeat 0 would let a
    later repeat's regression go undetected while the aggregate efficiency
    delta (computed across *all* repeats) still claims a "win" — violating
    H3.

    Two safeguards, both fail-closed:

    1. If any repeat's baseline or treatment score disagrees with repeat
       0's, this raises :class:`RepeatCorrectnessVarianceError` rather than
       silently reporting only one (possibly non-representative) repeat's
       score — the deterministic-core assumption above is enforced, not
       merely asserted in a docstring.
    2. Independently of (1) — belt-and-suspenders — the efficiency win is
       suppressed whenever *any* repeat's baseline/treatment pair regressed,
       not just repeat 0's.

    Raises:
        RepeatCorrectnessVarianceError: a treatment/baseline pair's
            correctness score differs across repeats (see above).
    """
    baseline_scores = tuple(
        score_arm(scenario.id, "baseline", produced, scenario.gold_answer)
        for produced in baseline_produced_by_repeat
    )
    treatment_scores = tuple(
        score_arm(scenario.id, "treatment", produced, scenario.gold_answer)
        for produced in treatment_produced_by_repeat
    )
    if any(score != baseline_scores[0] for score in baseline_scores[1:]) or any(
        score != treatment_scores[0] for score in treatment_scores[1:]
    ):
        raise RepeatCorrectnessVarianceError(
            f"scenario {scenario.id!r}: correctness score varies across repeats — the "
            "deterministic-core assumption (every repeat scores identically) does not hold "
            "for this run's executor. Refusing to report only one repeat's score as "
            "representative; a live-mode/varying-correctness executor is out of scope "
            "(deferred) for this reporting path."
        )
    baseline_score = baseline_scores[0]
    treatment_score = treatment_scores[0]
    regression = any(regressed(b, t) for b, t in zip(baseline_scores, treatment_scores))

    if regression:
        verdict: Verdict = "no-win-correctness-regression"
        reason: str | None = (
            "correctness regressed under treatment on at least one repeat "
            "(scorer.regressed()==True); efficiency win suppressed regardless of any "
            "favorable token delta (H3)"
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

    Raises:
        ReportIdentityError: ``corpus``/``results``/``manifest``/``read_result``
            are not verifiably the same run (H6) — see
            :func:`_validate_run_identity` for the specific checks.
        RepeatCorrectnessVarianceError: a scenario's correctness score
            varies across repeats (H3) — see :func:`compose_scenario_report`.
    """
    _validate_run_identity(corpus, results, manifest, read_result)
    scenario_ids = tuple(scenario.id for scenario in corpus.scenarios)
    per_scenario_deltas = compute_corpus_deltas(read_result, scenario_ids)
    aggregate_delta = compute_aggregate_delta(read_result, scenario_ids)
    classification_by_id = {c.scenario_id: c for c in manifest.scenario_classifications}

    reports = []
    for scenario in corpus.scenarios:
        repeat_runs = results[scenario.id]
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
                baseline_produced_by_repeat=tuple(run.baseline.produced_answer for run in repeat_runs),
                treatment_produced_by_repeat=tuple(run.treatment.produced_answer for run in repeat_runs),
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
