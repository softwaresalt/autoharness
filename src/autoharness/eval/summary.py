"""Comparative baseline summary for the eval runner (task 055.006-T).

Summarizes the comparable baseline metrics produced by
:func:`autoharness.eval.runner.run_matrix` across the matrix's model
configurations and, when available, folds in deterministic reviewer-matrix
quality scores keyed by config name.

This module **consumes** reviewer scores; it does not compute them (that is the
deterministic grader in :mod:`autoharness.eval.reviewer`). The summary is a pure
function of the run report and the optional reviews — no models, no network.
Comparative selectors break ties by config name so output is fully reproducible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from autoharness.eval.reviewer import ReviewMatrixResult
from autoharness.eval.runner import EvalRunReport
from autoharness.telemetry.aggregation import UNAVAILABLE, aggregate_epochs, derived_efficiency_metrics


@dataclass(frozen=True)
class ConfigSummary:
    """One config's comparable baseline row (economics + optional quality)."""

    config_name: str
    primary_model: str | None
    models: tuple[str, ...]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cogs_usd: float
    duration_seconds: float
    context_area_tokens: int
    net_offload_tokens: int | str
    consumption_generation_ratio: float | str
    expected_tool_gap_rate: float | str
    task_size_label: str | None
    feature_planned_size_label: str | None
    shipment_planned_size_label: str | None
    gate_exit_codes: tuple[int, ...]
    blocked: bool
    quality_overall: float | None
    quality_dimensions: dict[str, float] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "config_name": self.config_name,
            "primary_model": self.primary_model,
            "models": list(self.models),
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cogs_usd": self.cogs_usd,
            "duration_seconds": self.duration_seconds,
            "context_area_tokens": self.context_area_tokens,
            "net_offload_tokens": self.net_offload_tokens,
            "consumption_generation_ratio": self.consumption_generation_ratio,
            "expected_tool_gap_rate": self.expected_tool_gap_rate,
            "task_size_label": self.task_size_label,
            "feature_planned_size_label": self.feature_planned_size_label,
            "shipment_planned_size_label": self.shipment_planned_size_label,
            "gate_exit_codes": list(self.gate_exit_codes),
            "blocked": self.blocked,
            "quality_overall": self.quality_overall,
            "quality_dimensions": (
                dict(self.quality_dimensions) if self.quality_dimensions is not None else None
            ),
        }


@dataclass(frozen=True)
class BaselineSummary:
    """The comparative summary across every config in a frozen baseline run."""

    frozen_base: str | None
    frozen_head: str | None
    frozen_sha: str | None
    configs: tuple[ConfigSummary, ...]
    cheapest_config: str | None
    costliest_config: str | None
    fastest_config: str | None
    lowest_token_config: str | None
    highest_quality_config: str | None
    blocked_configs: tuple[str, ...]
    total_cogs_usd: float
    total_tokens: int
    cost_per_successful_epoch: float | str
    planned_vs_composition: str
    cost_per_size_point: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "frozen_state": {
                "base": self.frozen_base,
                "head": self.frozen_head,
                "resolved_sha": self.frozen_sha,
            },
            "configs": [config.to_dict() for config in self.configs],
            "cheapest_config": self.cheapest_config,
            "costliest_config": self.costliest_config,
            "fastest_config": self.fastest_config,
            "lowest_token_config": self.lowest_token_config,
            "highest_quality_config": self.highest_quality_config,
            "blocked_configs": list(self.blocked_configs),
            "total_cogs_usd": self.total_cogs_usd,
            "total_tokens": self.total_tokens,
            "cost_per_successful_epoch": self.cost_per_successful_epoch,
            "planned_vs_composition": self.planned_vs_composition,
            "cost_per_size_point": self.cost_per_size_point,
        }


def _select(
    configs: tuple[ConfigSummary, ...],
    key: Callable[[ConfigSummary], float | None],
    *,
    largest: bool = False,
) -> str | None:
    """Return the config name with the extreme ``key``; ties break by name."""
    ranked = [c for c in configs if key(c) is not None]
    if not ranked:
        return None
    sign = -1.0 if largest else 1.0
    chosen = min(ranked, key=lambda c: (sign * float(key(c)), c.config_name))  # type: ignore[arg-type]
    return chosen.config_name


def _config_summary(
    config_name: str,
    epoch,
    review: ReviewMatrixResult | None,
) -> ConfigSummary:
    economics = epoch.economics
    record = epoch.to_record()
    derived = derived_efficiency_metrics([record])
    sizing = epoch.sizing
    outcome = epoch.outcome
    expected = epoch.operations.expected_tool_count
    missing = epoch.operations.missing_expected_tool_count
    gap_rate: float | str = UNAVAILABLE if expected == 0 else missing / expected
    quality_overall = review.overall if review is not None else None
    quality_dimensions = (
        {dim: score.score for dim, score in review.dimensions.items()}
        if review is not None
        else None
    )
    return ConfigSummary(
        config_name=config_name,
        primary_model=epoch.route.primary_model,
        models=epoch.route.models,
        input_tokens=economics.input_tokens,
        output_tokens=economics.output_tokens,
        total_tokens=economics.total_tokens,
        cogs_usd=economics.cogs_usd,
        duration_seconds=economics.duration_seconds,
        context_area_tokens=economics.context_area_tokens,
        net_offload_tokens=derived["net_offload_tokens"],
        consumption_generation_ratio=derived["consumption_generation_ratio"],
        expected_tool_gap_rate=gap_rate,
        task_size_label=sizing.task_size_label if sizing is not None else None,
        feature_planned_size_label=(
            sizing.feature_planned_size_label if sizing is not None else None
        ),
        shipment_planned_size_label=(
            sizing.shipment_planned_size_label if sizing is not None else None
        ),
        gate_exit_codes=outcome.gate_exit_codes,
        blocked=outcome.blocked,
        quality_overall=quality_overall,
        quality_dimensions=quality_dimensions,
    )


def summarize_baseline(
    report: EvalRunReport,
    *,
    reviews: Mapping[str, ReviewMatrixResult] | None = None,
) -> BaselineSummary:
    """Build the comparative baseline summary from a run report.

    ``reviews`` maps a config name to its deterministic reviewer result. Configs
    without a review carry ``quality_overall = None`` and are excluded from the
    ``highest_quality_config`` selection.
    """
    reviews = reviews or {}
    configs = tuple(
        _config_summary(run.config_name, run.epoch, reviews.get(run.config_name))
        for run in report.runs
    )

    frozen = report.frozen_state
    blocked_configs = tuple(c.config_name for c in configs if c.blocked)
    telemetry_aggregate = aggregate_epochs([epoch.to_record() for epoch in report.epochs])

    return BaselineSummary(
        frozen_base=frozen.base if frozen else None,
        frozen_head=frozen.head if frozen else None,
        frozen_sha=frozen.resolved_sha if frozen else None,
        configs=configs,
        cheapest_config=_select(configs, lambda c: c.cogs_usd),
        costliest_config=_select(configs, lambda c: c.cogs_usd, largest=True),
        fastest_config=_select(configs, lambda c: c.duration_seconds),
        lowest_token_config=_select(configs, lambda c: c.total_tokens),
        highest_quality_config=_select(configs, lambda c: c.quality_overall, largest=True),
        blocked_configs=blocked_configs,
        total_cogs_usd=round(sum(c.cogs_usd for c in configs), 6),
        total_tokens=sum(c.total_tokens for c in configs),
        cost_per_successful_epoch=telemetry_aggregate.derived["cost_per_successful_epoch"],
        planned_vs_composition=UNAVAILABLE,
        cost_per_size_point=UNAVAILABLE,
    )
