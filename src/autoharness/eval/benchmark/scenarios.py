"""Benchmark scenario corpus model + loader (085.001-T).

A structural-navigation benchmark scenario declares a navigation task, a gold
answer (the correct target set), a scenario class (``positive`` / ``neutral`` /
``negative``), and an index-state precondition (``warm`` / ``cold`` / ``stale``)
that a run harness (:mod:`autoharness.eval.benchmark.harness`) replays under two
arms.

This module is a **pure, deterministic loader/validator** — it does not run any
scenario and does not score anything. It mirrors the existing
:mod:`autoharness.eval.matrix` conventions (frozen dataclasses, a single
``*Error`` exception, a mapping-first loader plus a file-loader wrapper).

The loader enforces the **balanced-class invariant**: a corpus must declare at
least one scenario of each class (``positive``, ``neutral``, ``negative``) so a
published benchmark result cannot cherry-pick only favorable cases (H2/R2). It
also computes a canonical, deterministic **corpus manifest hash** over the
sorted scenario ids so a published result is independently reproducible.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

SCENARIO_CLASSES = ("positive", "neutral", "negative")
INDEX_STATES = ("warm", "cold", "stale")


class CorpusError(ValueError):
    """Raised when a scenario corpus is missing, malformed, or fails validation."""


def _require_nonempty_str(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CorpusError(f"'{field}' must be a non-empty string.")
    return value


def _require_str_tuple(value: Any, field: str) -> tuple[str, ...]:
    """Coerce a JSON/YAML array of strings into a tuple.

    Unlike :func:`autoharness.eval.matrix._require_str_list`, an **empty** array
    is permitted here: a ``negative`` scenario's gold answer is legitimately
    empty (the correct behavior is to find nothing).
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise CorpusError(f"'{field}' must be an array of strings (possibly empty).")
    return tuple(str(item) for item in value)


@dataclass(frozen=True)
class Scenario:
    """A single structural-navigation benchmark scenario."""

    id: str
    scenario_class: str
    task: str
    gold_answer: tuple[str, ...]
    index_state: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "scenario_class": self.scenario_class,
            "task": self.task,
            "gold_answer": list(self.gold_answer),
            "index_state": self.index_state,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ScenarioCorpus:
    """A validated, balanced scenario corpus plus its deterministic manifest hash."""

    scenarios: tuple[Scenario, ...]
    manifest_hash: str
    version: str = "1.0.0"

    def by_class(self, scenario_class: str) -> tuple[Scenario, ...]:
        return tuple(s for s in self.scenarios if s.scenario_class == scenario_class)

    def get(self, scenario_id: str) -> Scenario:
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        raise CorpusError(f"No scenario with id {scenario_id!r} in this corpus.")


def _parse_scenario(raw: Any, index: int) -> Scenario:
    if not isinstance(raw, Mapping):
        raise CorpusError(f"scenarios[{index}] must be a mapping.")

    scenario_id = _require_nonempty_str(raw.get("id"), f"scenarios[{index}].id")
    scenario_class = raw.get("scenario_class")
    if scenario_class not in SCENARIO_CLASSES:
        raise CorpusError(
            f"scenarios[{index}].scenario_class must be one of {SCENARIO_CLASSES}; "
            f"got {scenario_class!r}."
        )
    task = _require_nonempty_str(raw.get("task"), f"scenarios[{index}].task")
    gold_answer = _require_str_tuple(raw.get("gold_answer", []), f"scenarios[{index}].gold_answer")
    index_state = raw.get("index_state")
    if index_state not in INDEX_STATES:
        raise CorpusError(
            f"scenarios[{index}].index_state must be one of {INDEX_STATES}; "
            f"got {index_state!r}."
        )
    rationale = _require_nonempty_str(raw.get("rationale"), f"scenarios[{index}].rationale")

    return Scenario(
        id=scenario_id,
        scenario_class=str(scenario_class),
        task=task,
        gold_answer=gold_answer,
        index_state=str(index_state),
        rationale=rationale,
    )


def _canonical_manifest_json(scenarios: tuple[Scenario, ...]) -> str:
    """Canonical JSON of ``scenarios`` sorted by id — the manifest-hash input.

    Sorting by id (rather than corpus declaration order) makes the hash
    independent of input ordering while remaining sensitive to scenario
    *content*, so a corpus edit (not just a reorder) changes the hash.
    """
    ordered = sorted((s.to_dict() for s in scenarios), key=lambda item: item["id"])
    return json.dumps(ordered, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_manifest_hash(scenarios: tuple[Scenario, ...]) -> str:
    """Deterministic sha256 hex digest over the sorted-by-id scenario set."""
    return hashlib.sha256(_canonical_manifest_json(scenarios).encode("utf-8")).hexdigest()


def _validate_balanced_classes(scenarios: tuple[Scenario, ...]) -> None:
    present = {s.scenario_class for s in scenarios}
    missing = [c for c in SCENARIO_CLASSES if c not in present]
    if missing:
        raise CorpusError(
            "Unbalanced corpus: missing scenario class(es) "
            f"{missing} — a corpus requires >=1 scenario of each of {SCENARIO_CLASSES} "
            "(balanced-class invariant, R2/H2)."
        )


def load_corpus(data: Any) -> ScenarioCorpus:
    """Validate and load a scenario corpus from a parsed mapping.

    Raises:
        CorpusError: when the mapping is malformed, ``scenarios`` is absent or
            empty, scenario ids collide, any scenario is invalid, or the
            balanced-class invariant is not satisfied.
    """
    if not isinstance(data, Mapping):
        raise CorpusError("Scenario corpus must be a mapping (object).")

    raw_scenarios = data.get("scenarios")
    if not isinstance(raw_scenarios, (list, tuple)) or not raw_scenarios:
        raise CorpusError("Scenario corpus requires a non-empty 'scenarios' array.")

    scenarios: list[Scenario] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_scenarios):
        scenario = _parse_scenario(raw, index)
        if scenario.id in seen:
            raise CorpusError(f"Duplicate scenario id {scenario.id!r}; ids must be unique.")
        seen.add(scenario.id)
        scenarios.append(scenario)

    scenarios_tuple = tuple(scenarios)
    _validate_balanced_classes(scenarios_tuple)

    version = str(data.get("version", "1.0.0"))
    return ScenarioCorpus(
        scenarios=scenarios_tuple,
        manifest_hash=compute_manifest_hash(scenarios_tuple),
        version=version,
    )


def load_corpus_file(path: Path | str) -> ScenarioCorpus:
    """Load a scenario corpus from a ``.yaml``/``.yml`` or ``.json`` file.

    Raises:
        CorpusError: when the file is missing, unreadable, not valid YAML/JSON,
            or fails corpus validation.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise CorpusError(f"Could not read scenario corpus {file_path}: {exc}") from exc

    suffix = file_path.suffix.lower()
    try:
        if suffix == ".json":
            data = json.loads(text)
        else:
            import yaml

            data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001 - normalize any parse error
        raise CorpusError(f"Could not parse scenario corpus {file_path}: {exc}") from exc

    return load_corpus(data)


DEFAULT_CORPUS_PATH = Path(__file__).parent / "fixtures" / "corpus.yaml"


def load_default_corpus() -> ScenarioCorpus:
    """Load the shipped representative corpus fixture."""
    return load_corpus_file(DEFAULT_CORPUS_PATH)
