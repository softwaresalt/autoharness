"""Pre-review detector contracts and runtime helpers."""

from .contract import (
    ApplicabilitySpec,
    DETECTOR_STATUS_VALUES,
    Evidence,
    NodeResult,
    NodeSpec,
    ProducerSpec,
    RemediationSpec,
    ValidatorSpec,
    status_exit_code,
)

__all__ = [
    "ApplicabilitySpec",
    "DETECTOR_STATUS_VALUES",
    "Evidence",
    "NodeResult",
    "NodeSpec",
    "ProducerSpec",
    "RemediationSpec",
    "ValidatorSpec",
    "status_exit_code",
]
