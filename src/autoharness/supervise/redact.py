"""Single secret-redaction choke point (118.004-T).

Every place the supervisor might emit text or structured data (journal
entries, telemetry, approval summaries, error messages) MUST route through
this module before leaving the process. There is exactly one choke point so
new emission call sites cannot accidentally bypass redaction.

Two complementary redaction mechanisms:

1. **Pattern-based** — regexes for well-known secret shapes (GitHub PAT/App
   token prefixes, ``github_pat_`` tokens) plus key-name matching
   (``TOKEN``/``SECRET``/``KEY``/``PASSWORD``, case-insensitive) for
   structured mapping input.
2. **Registered-value based** — a caller-populated registry of concrete,
   already-resolved secret values (e.g. the literal token a sidecar tool
   resolved at runtime) that are redacted by exact whole-match substring
   replacement wherever they appear in text, even when they match no regex.

Redaction is always **whole-match**: a matched secret is replaced entirely
with a fixed placeholder, never partially masked (no "show first/last N
characters"), because partial masking of a token-shaped secret can still
leak enough entropy to be useful to an attacker.

:func:`redact_record` is the fail-closed entry point: a record that cannot
be safely processed is DROPPED (returns ``None`` alongside a warning
string) rather than ever emitted unredacted. There is no degraded
pass-through path.

This module is pure: no I/O, no subprocess invocation, no logging handlers
configured here (callers decide what to do with the returned warning).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, TypeVar

#: Fixed replacement text. Whole-match only -- never a partial reveal.
PLACEHOLDER = "***REDACTED***"

# Key names that mark a mapping value as sensitive regardless of its shape.
_SECRET_KEY_PATTERN = re.compile(r"(TOKEN|SECRET|KEY|PASSWORD)", re.IGNORECASE)

# Well-known secret value shapes.
#   - GitHub fine-grained/classic token prefixes: ghp_, gho_, ghu_, ghs_, ghr_
#   - github_pat_ tokens (new GitHub PAT format)
_VALUE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]+"),
)


class RedactionFailure(Exception):
    """Raised internally when a record cannot be safely redacted.

    Callers of :func:`redact_record` never see this exception directly --
    it is caught at the choke point and converted into the fail-closed
    ``(None, warning)`` return contract. It is exported for direct callers
    of :class:`Redactor` methods who want a named failure type.
    """


@dataclass
class Redactor:
    """Holds registered secret values and applies pattern + registry redaction."""

    _registered_secrets: list[str] = field(default_factory=list)

    def register_secret(self, value: str) -> None:
        """Register a concrete, already-resolved secret value for exact
        whole-match substring redaction, independent of the regex patterns."""

        if not value:
            return
        self._registered_secrets.append(value)

    def redact_text(self, text: str) -> str:
        """Redact a plain string: registered secrets first, then patterns."""

        if not isinstance(text, str):
            raise RedactionFailure(f"redact_text requires str, got {type(text)!r}")

        redacted = text
        # Longest-first so a registered secret that is a substring of another
        # registered secret does not leave a partial remainder behind.
        for secret in sorted(self._registered_secrets, key=len, reverse=True):
            if secret and secret in redacted:
                redacted = redacted.replace(secret, PLACEHOLDER)
        for pattern in _VALUE_PATTERNS:
            redacted = pattern.sub(PLACEHOLDER, redacted)
        return redacted

    def redact_value(self, value: Any) -> Any:
        """Recursively redact a value of unknown shape (str/Mapping/list/other)."""

        if isinstance(value, str):
            return self.redact_text(value)
        if isinstance(value, Mapping):
            return self.redact_mapping(value)
        if isinstance(value, (list, tuple)):
            return type(value)(self.redact_value(item) for item in value)
        return value

    def redact_mapping(self, data: Mapping[str, Any]) -> dict[str, Any]:
        """Redact a mapping: sensitive-named keys are fully replaced; every
        other value is redacted recursively."""

        result: dict[str, Any] = {}
        for key, value in data.items():
            if _SECRET_KEY_PATTERN.search(str(key)):
                # A sensitive-named key is fully replaced regardless of value
                # shape (str, int, float, list, nested dict, ...). Gating this
                # on isinstance(value, str) would silently leak a non-string
                # secret (e.g. a numeric token, or a list/dict payload) nested
                # under a TOKEN/SECRET/KEY/PASSWORD-named key.
                result[key] = PLACEHOLDER
            else:
                result[key] = self.redact_value(value)
        return result


# Process-global default redactor. Most callers should use the module-level
# register_secret()/redact_record() functions rather than constructing their
# own Redactor, so a secret registered anywhere is redacted everywhere.
_DEFAULT_REDACTOR = Redactor()


def register_secret(value: str) -> None:
    """Register a resolved secret value with the process-global redactor."""

    _DEFAULT_REDACTOR.register_secret(value)


T = TypeVar("T")


def redact_record(
    record: T, redactor: Optional[Redactor] = None
) -> tuple[Optional[T], Optional[str]]:
    """Redact ``record`` (a ``str`` or a ``Mapping``), failing closed on error.

    Returns a ``(value, warning)`` pair:

    * On success: ``value`` is the redacted record and ``warning`` is
      ``None``.
    * On failure (unsupported type, or any exception raised while pattern
      matching): ``value`` is ``None`` -- the record is DROPPED -- and
      ``warning`` carries a short, human-readable reason. Callers MUST NOT
      fall back to emitting the raw/unredacted record in this case; there
      is no degraded pass-through path.
    """

    active = redactor if redactor is not None else _DEFAULT_REDACTOR
    try:
        if isinstance(record, str):
            return active.redact_text(record), None  # type: ignore[return-value]
        if isinstance(record, Mapping):
            return active.redact_mapping(record), None  # type: ignore[return-value]
        raise RedactionFailure(f"unsupported record type: {type(record)!r}")
    except Exception as exc:  # fail closed: drop, never pass through raw content
        return None, f"redaction failed, record dropped: {exc}"
