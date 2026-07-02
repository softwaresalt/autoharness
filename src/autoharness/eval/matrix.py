"""Eval model-config matrix loader (Phase 2, U8 sub-unit, task 055.004-T).

Loads and validates the eval model-configuration matrix used to drive a frozen
baseline run. This module does **not** run models and does **not** perform any
reviewer scoring — it is a pure, deterministic loader/validator.

The matrix declares the frozen git state to evaluate against and one or more
model configurations. Each config may optionally carry a ``baseline`` block of
recorded run data (economics / operations / outcome) so the default eval runner
can replay a comparable baseline **without invoking any model** (see
:mod:`autoharness.eval.runner`).

Example (YAML)::

    version: "1.0.0"
    frozen_state:
      base: main
      head: HEAD
    configs:
      - name: baseline-opus
        models: [claude-opus-4.6]
      - name: baseline-sonnet
        models: [claude-sonnet-4.5]
        baseline:
          economics: {input_tokens: 1200, output_tokens: 800, cogs_usd: 0.05, duration_seconds: 90}
          operations: {cli_tools: [git, pytest]}
          outcome: {gate_exit_codes: [0]}
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

DEFAULT_HEAD = "HEAD"


class EvalMatrixError(ValueError):
    """Raised when the eval matrix is missing, malformed, or fails validation."""


def _require_str_list(value: Any, field: str) -> tuple[str, ...]:
    """Coerce a JSON/YAML array of strings into a tuple, rejecting bare strings.

    A bare string is iterable, so ``tuple("abc")`` would silently yield
    ``('a', 'b', 'c')``. Reject that (and any non-array) as a controlled
    :class:`EvalMatrixError` rather than nonsense config.
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise EvalMatrixError(f"'{field}' must be a non-empty array of strings.")
    if not value:
        raise EvalMatrixError(f"'{field}' must be a non-empty array of strings.")
    items = tuple(str(item) for item in value)
    return items


@dataclass(frozen=True)
class ModelConfig:
    """A single model configuration within the eval matrix."""

    name: str
    models: tuple[str, ...]
    baseline: Mapping[str, Any] | None = None

    @property
    def primary_model(self) -> str | None:
        return self.models[0] if self.models else None


@dataclass(frozen=True)
class FrozenState:
    """The frozen git state the eval runs are executed against."""

    base: str
    head: str = DEFAULT_HEAD


@dataclass(frozen=True)
class EvalMatrix:
    """A validated eval matrix: an ordered set of configs + a frozen state."""

    configs: tuple[ModelConfig, ...]
    frozen_state: FrozenState | None = None
    version: str = "1.0.0"


def _parse_config(raw: Any, index: int) -> ModelConfig:
    if not isinstance(raw, Mapping):
        raise EvalMatrixError(f"configs[{index}] must be a mapping.")
    name = raw.get("name")
    if not name or not isinstance(name, str):
        raise EvalMatrixError(f"configs[{index}] is missing a non-empty string 'name'.")
    models = _require_str_list(raw.get("models"), f"configs[{index}].models")

    baseline = raw.get("baseline")
    if baseline is not None and not isinstance(baseline, Mapping):
        raise EvalMatrixError(f"configs[{index}].baseline must be a mapping when present.")

    return ModelConfig(name=name, models=models, baseline=baseline)


def _parse_frozen_state(raw: Any) -> FrozenState | None:
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise EvalMatrixError("'frozen_state' must be a mapping when present.")
    base = raw.get("base")
    if not base or not isinstance(base, str):
        raise EvalMatrixError("'frozen_state' requires a non-empty string 'base'.")
    head = raw.get("head") or DEFAULT_HEAD
    return FrozenState(base=base, head=str(head))


def load_matrix(data: Any) -> EvalMatrix:
    """Validate and load an eval matrix from a parsed mapping.

    Raises:
        EvalMatrixError: when the mapping is malformed, ``configs`` is absent or
            empty, config names collide, or any config is invalid.
    """
    if not isinstance(data, Mapping):
        raise EvalMatrixError("Eval matrix must be a mapping (object).")

    raw_configs = data.get("configs")
    if not isinstance(raw_configs, (list, tuple)) or not raw_configs:
        raise EvalMatrixError("Eval matrix requires a non-empty 'configs' array.")

    configs: list[ModelConfig] = []
    seen: set[str] = set()
    for index, raw in enumerate(raw_configs):
        config = _parse_config(raw, index)
        if config.name in seen:
            raise EvalMatrixError(f"Duplicate config name {config.name!r}; names must be unique.")
        seen.add(config.name)
        configs.append(config)

    frozen_state = _parse_frozen_state(data.get("frozen_state"))
    version = str(data.get("version", "1.0.0"))

    return EvalMatrix(configs=tuple(configs), frozen_state=frozen_state, version=version)


def load_matrix_file(path: Path | str) -> EvalMatrix:
    """Load an eval matrix from a ``.yaml``/``.yml`` or ``.json`` file.

    Raises:
        EvalMatrixError: when the file is missing, unreadable, not valid
            YAML/JSON, or fails matrix validation.
    """
    file_path = Path(path)
    try:
        text = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise EvalMatrixError(f"Could not read eval matrix {file_path}: {exc}") from exc

    suffix = file_path.suffix.lower()
    try:
        if suffix == ".json":
            import json

            data = json.loads(text)
        else:
            import yaml

            data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001 - normalize any parse error
        raise EvalMatrixError(f"Could not parse eval matrix {file_path}: {exc}") from exc

    return load_matrix(data)
