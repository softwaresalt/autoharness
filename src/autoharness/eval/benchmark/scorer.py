"""Benchmark correctness scorer (085.003-T).

Grades a single arm's **produced target set** against a scenario's gold answer
on a separate axis (precision / recall / exact-match) from efficiency. This
module has **no coupling to efficiency metrics** — it accepts only two plain
string sets and returns a score; it never sees tokens, cost, or telemetry
(axis separation, R3/H3: a benchmark must never let token savings imply
correctness, or vice versa).

Set semantics (order-independent, duplicate-insensitive):

- **exact_match**: produced == gold, exactly (including both empty — a
  negative scenario correctly reporting nothing is an exact match).
- **precision**: ``|produced ∩ gold| / |produced|`` (``None`` when produced is
  empty — precision is undefined, not zero, when nothing was produced).
- **recall**: ``|produced ∩ gold| / |gold|`` (``None`` when gold is empty —
  recall is undefined, not zero/one, when there is nothing to recall; see
  ``negative`` scenarios).
- **classification**: ``"exact"`` | ``"partial"`` | ``"miss"`` — ``"exact"``
  when ``exact_match`` is True; ``"miss"`` when the intersection is empty
  (and produced/gold are not both empty); ``"partial"`` otherwise.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

Classification = str  # "exact" | "partial" | "miss"


def _as_frozen(value: Iterable[str]) -> frozenset[str]:
    return frozenset(str(item) for item in value)


@dataclass(frozen=True)
class CorrectnessScore:
    """A single arm's correctness score against a scenario's gold answer.

    Carries no token/cost fields (axis separation enforced by construction —
    there is nowhere on this dataclass to put one).
    """

    scenario_id: str
    arm: str
    produced: tuple[str, ...]
    gold: tuple[str, ...]
    exact_match: bool
    precision: float | None
    recall: float | None
    classification: Classification

    def to_dict(self) -> dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "arm": self.arm,
            "produced": list(self.produced),
            "gold": list(self.gold),
            "exact_match": self.exact_match,
            "precision": self.precision,
            "recall": self.recall,
            "classification": self.classification,
        }


def score_arm(
    scenario_id: str,
    arm: str,
    produced: Iterable[str],
    gold: Iterable[str],
) -> CorrectnessScore:
    """Score one arm's produced target set against the scenario's gold answer.

    Deterministic and order-independent: ``produced``/``gold`` are treated as
    sets (duplicates and ordering never affect the score).
    """
    produced_set = _as_frozen(produced)
    gold_set = _as_frozen(gold)
    intersection = produced_set & gold_set

    exact_match = produced_set == gold_set
    precision = (len(intersection) / len(produced_set)) if produced_set else None
    recall = (len(intersection) / len(gold_set)) if gold_set else None

    if exact_match:
        classification: Classification = "exact"
    elif not intersection:
        classification = "miss"
    else:
        classification = "partial"

    return CorrectnessScore(
        scenario_id=scenario_id,
        arm=arm,
        produced=tuple(sorted(produced_set)),
        gold=tuple(sorted(gold_set)),
        exact_match=exact_match,
        precision=precision,
        recall=recall,
        classification=classification,
    )


def regressed(baseline: CorrectnessScore, treatment: CorrectnessScore) -> bool:
    """True when the treatment arm is correctness-worse than the baseline arm.

    Regression is defined structurally, not just by classification label: the
    treatment's produced set must be a **strict subset** of what would be
    needed to match the baseline's correctness, i.e. the treatment recalls
    strictly less of the gold answer than the baseline while the baseline was
    at least as good. This keeps H3 (no efficiency win when correctness
    regresses) decidable purely from two :class:`CorrectnessScore` values.
    """
    baseline_hits = len(_as_frozen(baseline.produced) & _as_frozen(baseline.gold))
    treatment_hits = len(_as_frozen(treatment.produced) & _as_frozen(treatment.gold))
    if treatment_hits < baseline_hits:
        return True
    # Equal hit-count but the baseline was an exact match and treatment is not:
    # still a regression (e.g. baseline correctly found nothing, treatment
    # spuriously produced something extra).
    return baseline.exact_match and not treatment.exact_match
