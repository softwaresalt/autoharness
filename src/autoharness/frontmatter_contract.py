"""Agent and skill frontmatter conformity contract (193-F / B1).

One canonical, read-only definition of which YAML frontmatter keys an agent
or a skill may, must, and must not carry, plus a deterministic parser and the
finding codes shared by ``verify_workspace`` (B2a/B2b) and the template
conformity test (B3/B4).

Design notes (plan ``docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md``):

* Routing keys are split into ``TIER_KEYS`` and ``ROUTE_VALUE_KEYS``. Profile
  key sets are computed at call time by :func:`agent_key_sets` and
  :func:`skill_key_sets`, never stored as module-level literals, so extending
  the contract (for example ``context_tier``) is a single edit to
  ``ROUTE_VALUE_KEYS`` (AS-F6).
* ``tier-routed`` agents require the full route; ``plugin-global`` agents
  (listed in the autoharness ``plugin.json`` ``agents[]``) carry only the tier
  keys and must not carry any route-value key (H-B1).
* Skills are leaf executors: no routing key and no bare ``model`` (P-013.5).
* This module imports no verify or tune code (INV-B3).
"""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Finding codes
# ---------------------------------------------------------------------------

FM_PARSE_ERROR = "FM_PARSE_ERROR"
FM_MISSING_REQUIRED = "FM_MISSING_REQUIRED"
FM_FORBIDDEN_KEY = "FM_FORBIDDEN_KEY"
FM_BARE_MODEL = "FM_BARE_MODEL"
FM_TYPE_INVALID = "FM_TYPE_INVALID"
FM_UNRESOLVED_PLACEHOLDER = "FM_UNRESOLVED_PLACEHOLDER"
FM_PATH_ESCAPE = "FM_PATH_ESCAPE"  # emitted only by verify_workspace (B2a)
FM_UNKNOWN_KEY = "FM_UNKNOWN_KEY"  # informational only (INV-B4)

NON_INFORMATIONAL_CODES = frozenset(
    {
        FM_PARSE_ERROR,
        FM_MISSING_REQUIRED,
        FM_FORBIDDEN_KEY,
        FM_BARE_MODEL,
        FM_TYPE_INVALID,
        FM_UNRESOLVED_PLACEHOLDER,
        FM_PATH_ESCAPE,
    }
)
INFORMATIONAL_CODES = frozenset({FM_UNKNOWN_KEY})

# ---------------------------------------------------------------------------
# Modes and profiles
# ---------------------------------------------------------------------------

MODE_TEMPLATE = "template"
MODE_INSTALLED = "installed"
MODES = frozenset({MODE_TEMPLATE, MODE_INSTALLED})

PROFILE_TIER_ROUTED = "tier-routed"
PROFILE_PLUGIN_GLOBAL = "plugin-global"
AGENT_PROFILES = frozenset({PROFILE_TIER_ROUTED, PROFILE_PLUGIN_GLOBAL})

# ---------------------------------------------------------------------------
# Key constants (the only source of truth; profile sets derive at call time)
# ---------------------------------------------------------------------------

TIER_KEYS: frozenset[str] = frozenset({"max_subagent_tier", "subagent_depth"})

REVIEW_ROUTE_KEY_PATTERN = r"^(anchor|alt)_review_(family|provider|reasoning_effort)$"

ROUTE_VALUE_KEYS: frozenset[str] = frozenset(
    {"model_family", "model_provider", "reasoning_effort", "context_tier"}
    | {
        f"{prefix}_review_{suffix}"
        for prefix in ("anchor", "alt")
        for suffix in ("family", "provider", "reasoning_effort")
    }
)

BARE_MODEL_KEY = "model"

# Resolved ``context_tier`` values (194-F, H-C5): the single enum source. The
# config schema's ``contextTier`` enum is ``["", *CONTEXT_TIER_VALUES]``, where
# ``""`` means unset/inherit and is legal only in config, never in rendered
# frontmatter. ``context_tier`` is a ``ROUTE_VALUE_KEYS`` member (C5a,
# 194.007-T): optional on tier-routed agents, forbidden elsewhere.
CONTEXT_TIER_VALUES: tuple[str, ...] = ("default", "long_context")

_AGENT_IDENTITY_KEYS = frozenset({"name", "description"})
_AGENT_BASE_ROUTE_KEYS = frozenset({"model_family", "model_provider", "reasoning_effort"})
_AGENT_NON_ROUTING_OPTIONAL = frozenset(
    {"id", "maturity", "tools", "argument-hint", "handoffs", "target"}
)

_SKILL_REQUIRED = frozenset({"name", "description"})
_SKILL_OPTIONAL = frozenset(
    {"argument-hint", "input", "license", "compatibility", "metadata", "allowed-tools"}
)

SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SKILL_NAME_MAX_LENGTH = 64


def routing_keys() -> frozenset[str]:
    """Return ``TIER_KEYS | ROUTE_VALUE_KEYS``, computed at call time."""
    return frozenset(TIER_KEYS | ROUTE_VALUE_KEYS)


@dataclass(frozen=True)
class KeySets:
    """Required, optional, and forbidden top-level keys for one artifact kind."""

    required: frozenset[str]
    optional: frozenset[str]
    forbidden: frozenset[str]


def agent_key_sets(profile: str) -> KeySets:
    """Return the key sets for an agent ``profile``, derived at call time."""
    route_value_keys = frozenset(ROUTE_VALUE_KEYS)
    if profile == PROFILE_TIER_ROUTED:
        required = _AGENT_IDENTITY_KEYS | TIER_KEYS | _AGENT_BASE_ROUTE_KEYS
        optional = _AGENT_NON_ROUTING_OPTIONAL | (route_value_keys - required)
        forbidden = frozenset({BARE_MODEL_KEY})
    elif profile == PROFILE_PLUGIN_GLOBAL:
        required = _AGENT_IDENTITY_KEYS | TIER_KEYS
        optional = _AGENT_NON_ROUTING_OPTIONAL - route_value_keys
        forbidden = route_value_keys | {BARE_MODEL_KEY}
    else:
        raise ValueError(f"unknown agent profile: {profile!r}")
    return KeySets(frozenset(required), frozenset(optional), frozenset(forbidden))


def skill_key_sets() -> KeySets:
    """Return the skill key sets, derived at call time."""
    return KeySets(
        required=_SKILL_REQUIRED,
        optional=_SKILL_OPTIONAL,
        forbidden=routing_keys() | {BARE_MODEL_KEY},
    )


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Finding:
    """One conformity finding. ``key`` is ``""`` for file-level findings."""

    code: str
    key: str
    message: str
    informational: bool = False


def _finding(code: str, key: str, message: str) -> Finding:
    return Finding(code=code, key=key, message=message, informational=code in INFORMATIONAL_CODES)


def _sorted(findings: Iterable[Finding]) -> list[Finding]:
    return sorted(findings, key=lambda item: (item.code, item.key))


def has_blocking_findings(findings: Iterable[Finding]) -> bool:
    """True when any finding is non-informational."""
    return any(not item.informational for item in findings)


# ---------------------------------------------------------------------------
# Validators (per-key registry)
# ---------------------------------------------------------------------------

Validator = Callable[[Any], "str | None"]


def _context_tier(value: Any) -> str | None:
    if not isinstance(value, str) or value not in CONTEXT_TIER_VALUES:
        return f"expected one of {list(CONTEXT_TIER_VALUES)}, got {type(value).__name__}: {value!r}"
    return None


def _non_empty_string(value: Any) -> str | None:
    if not isinstance(value, str) or value.strip() == "":
        return f"expected a non-empty string, got {type(value).__name__}: {value!r}"
    return None


def _string(value: Any) -> str | None:
    if not isinstance(value, str):
        return f"expected a string, got {type(value).__name__}: {value!r}"
    return None


def _tier_int(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return f"expected an integer 1-3, got {type(value).__name__}: {value!r}"
    if value < 1 or value > 3:
        return f"expected an integer 1-3, got {value!r}"
    return None


def _non_negative_int(value: Any) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return f"expected a non-negative integer, got {type(value).__name__}: {value!r}"
    if value < 0:
        return f"expected a non-negative integer, got {value!r}"
    return None


VALIDATORS: dict[str, Validator] = {
    "name": _non_empty_string,
    "description": _non_empty_string,
    "max_subagent_tier": _tier_int,
    "subagent_depth": _non_negative_int,
    "model_family": _non_empty_string,
    "model_provider": _string,
    "reasoning_effort": _string,
    # Review-route families may legitimately render empty (e.g. adversarial-review
    # with no alternate/anchor reviewer configured), so they share the
    # string-typed, empty-allowed rule of the provider keys.
    "anchor_review_family": _string,
    "anchor_review_provider": _string,
    "anchor_review_reasoning_effort": _string,
    "alt_review_family": _string,
    "alt_review_provider": _string,
    "alt_review_reasoning_effort": _string,
    "context_tier": _context_tier,
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

_PLACEHOLDER_TOKEN = re.compile(r"\{\{\s*[A-Za-z_][A-Za-z0-9_.\-]*\s*\}\}")
_PLACEHOLDER_ANY = re.compile(r"\{\{.*?\}\}", re.S)
_SENTINEL_PREFIX = "AHFMPLACEHOLDER"


class _DuplicateKeyError(yaml.YAMLError):
    pass


class _AliasForbiddenError(yaml.YAMLError):
    pass


class _MergeKeyForbiddenError(yaml.YAMLError):
    pass


_MERGE_TAG = "tag:yaml.org,2002:merge"


class _UniqueKeySafeLoader(yaml.SafeLoader):
    """A ``yaml.SafeLoader`` that rejects repeated keys (PY-F1) and anchors/aliases.

    Frontmatter has no legitimate use for anchors or aliases, and aliases
    enable billion-laughs style expansion and self-referential structures, so
    any anchor or alias event is a parse error.
    """

    def compose_node(self, parent: Any, index: Any) -> Any:
        event = self.peek_event()
        if isinstance(event, yaml.AliasEvent):
            raise _AliasForbiddenError(
                f"alias '*{event.anchor}' at line {event.start_mark.line + 1}"
            )
        if getattr(event, "anchor", None) is not None:
            raise _AliasForbiddenError(
                f"anchor '&{event.anchor}' at line {event.start_mark.line + 1}"
            )
        return super().compose_node(parent, index)

    def construct_mapping(self, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
        if isinstance(node, yaml.MappingNode):
            # Reject merge keys before flatten_mapping() can expand them, so
            # merged values never satisfy keys the frontmatter did not declare.
            for key_node, _value_node in node.value:
                if key_node.tag == _MERGE_TAG:
                    raise _MergeKeyForbiddenError(
                        f"merge key '<<' at line {key_node.start_mark.line + 1}"
                    )
            self.flatten_mapping(node)
            seen: set[Any] = set()
            for key_node, _value_node in node.value:
                key = self.construct_object(key_node, deep=True)
                try:
                    is_duplicate = key in seen
                except TypeError:
                    # Unhashable keys are rejected by the base constructor below.
                    continue
                if is_duplicate:
                    raise _DuplicateKeyError(
                        f"duplicate key {key!r} at line {key_node.start_mark.line + 1}"
                    )
                seen.add(key)
        return super().construct_mapping(node, deep=deep)


@dataclass(frozen=True)
class ParsedFrontmatter:
    """Result of :func:`parse_frontmatter`.

    ``data`` is the frontmatter mapping (placeholder tokens restored verbatim)
    or ``None`` when ``error`` is set. ``placeholder_keys`` lists the top-level
    keys whose value (recursively) or name carries a ``{{...}}`` token.
    """

    data: dict[str, Any] | None
    mode: str
    placeholder_keys: frozenset[str] = field(default_factory=frozenset)
    error: Finding | None = None


def _validate_mode(mode: str) -> None:
    if mode not in MODES:
        raise ValueError(f"unknown frontmatter mode: {mode!r}")


def _parse_error(mode: str, reason: str) -> ParsedFrontmatter:
    return ParsedFrontmatter(
        data=None,
        mode=mode,
        error=_finding(FM_PARSE_ERROR, "", f"frontmatter parse error: {reason}"),
    )


def _restore(value: Any, tokens: list[str], pattern: re.Pattern[str]) -> Any:
    if isinstance(value, str):

        def _token(match: re.Match[str]) -> str:
            index = int(match.group(1))
            # Bounds-checked: text that merely resembles a sentinel stays verbatim.
            return tokens[index] if index < len(tokens) else match.group(0)

        return pattern.sub(_token, value)
    if isinstance(value, dict):
        return {_restore(key, tokens, pattern): _restore(item, tokens, pattern) for key, item in value.items()}
    if isinstance(value, list):
        return [_restore(item, tokens, pattern) for item in value]
    return value


def _contains_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return bool(_PLACEHOLDER_ANY.search(value))
    if isinstance(value, Mapping):
        return any(_contains_placeholder(k) or _contains_placeholder(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_placeholder(item) for item in value)
    return False


def _placeholder_keys(data: Mapping[str, Any]) -> frozenset[str]:
    return frozenset(
        str(key) for key, value in data.items() if _contains_placeholder(key) or _contains_placeholder(value)
    )


def parse_frontmatter(text: str | bytes, mode: str) -> ParsedFrontmatter:
    """Parse the leading YAML frontmatter block of ``text`` deterministically (H-B6).

    Never raises for malformed input: missing, unclosed, invalid,
    duplicate-key, anchor/alias-bearing, too-deeply-nested, non-mapping, and
    undecodable frontmatter each return a :class:`ParsedFrontmatter` whose
    ``error`` is an ``FM_PARSE_ERROR`` finding with a sub-reason. Only
    ``UnicodeDecodeError``, ``yaml.YAMLError``, and ``RecursionError`` are
    caught; anything else is a programming error.

    Placeholder tokens (``{{NAME}}``) are replaced with an inert sentinel
    carrying a per-call random nonce before the YAML load in both modes (so an
    unquoted leading placeholder does not parse as a flow mapping, and literal
    sentinel-like text in the input is never mistaken for one) and restored
    verbatim afterwards; the keys carrying one are recorded in
    ``placeholder_keys``. ``mode`` is recorded on the result and decides, in
    :func:`check_agent` / :func:`check_skill`, whether those keys are
    tolerated or rejected.
    """
    _validate_mode(mode)
    if isinstance(text, (bytes, bytearray)):
        try:
            text = bytes(text).decode("utf-8")
        except UnicodeDecodeError as exc:
            return _parse_error(mode, f"undecodable (not UTF-8): {exc.reason}")
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n")

    lines = text.split("\n")
    # Opening and closing delimiters share one rule: exactly '---' plus optional
    # trailing spaces/tabs (a '----' line is never a delimiter).
    if not lines or lines[0].rstrip(" \t") != "---":
        return _parse_error(mode, "missing opening '---' delimiter on the first line")
    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].rstrip(" \t") == "---":
            closing_index = index
            break
    if closing_index is None:
        return _parse_error(mode, "unclosed frontmatter (no closing '---' line)")

    block = "\n".join(lines[1:closing_index])
    tokens: list[str] = []
    token_index: dict[str, int] = {}
    sentinel_prefix = f"{_SENTINEL_PREFIX}{secrets.token_hex(8)}N"
    while sentinel_prefix in block:  # pragma: no cover - 64-bit nonce collision
        sentinel_prefix = f"{_SENTINEL_PREFIX}{secrets.token_hex(8)}N"
    sentinel_pattern = re.compile(re.escape(sentinel_prefix) + r"(\d+)X")

    def _substitute(match: re.Match[str]) -> str:
        token = match.group(0)
        index = token_index.get(token)
        if index is None:
            index = len(tokens)
            tokens.append(token)
            token_index[token] = index
        return f"{sentinel_prefix}{index}X"

    block = _PLACEHOLDER_TOKEN.sub(_substitute, block)
    try:
        loaded = yaml.load(block, Loader=_UniqueKeySafeLoader)  # noqa: S506 - SafeLoader subclass
    except _DuplicateKeyError as exc:
        return _parse_error(mode, f"duplicate key: {exc}")
    except _AliasForbiddenError as exc:
        return _parse_error(mode, f"YAML anchors/aliases are not allowed: {exc}")
    except _MergeKeyForbiddenError as exc:
        return _parse_error(mode, f"YAML merge keys are not allowed: {exc}")
    except yaml.YAMLError as exc:
        return _parse_error(mode, f"invalid YAML: {exc}")
    except RecursionError:
        return _parse_error(mode, "frontmatter is nested too deeply")

    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        return _parse_error(mode, f"frontmatter is not a mapping (got {type(loaded).__name__})")
    non_string_keys = [key for key in loaded if not isinstance(key, str)]
    if non_string_keys:
        return _parse_error(mode, f"non-string top-level key(s): {non_string_keys!r}")

    try:
        data = _restore(loaded, tokens, sentinel_pattern)
        placeholder_keys = _placeholder_keys(data)
    except RecursionError:
        return _parse_error(mode, "frontmatter is nested too deeply")
    return ParsedFrontmatter(data=data, mode=mode, placeholder_keys=placeholder_keys)


def read_frontmatter(path: Path | str, mode: str) -> ParsedFrontmatter:
    """Read ``path`` as bytes and parse its frontmatter; ``OSError`` becomes ``FM_PARSE_ERROR``."""
    _validate_mode(mode)
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        return _parse_error(mode, f"unreadable file: {type(exc).__name__}: {exc}")
    return parse_frontmatter(raw, mode)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------


def _coerce(fm: ParsedFrontmatter | Mapping[str, Any], mode: str) -> ParsedFrontmatter:
    _validate_mode(mode)
    if isinstance(fm, ParsedFrontmatter):
        return fm
    if not isinstance(fm, Mapping):
        raise TypeError(f"expected ParsedFrontmatter or a mapping, got {type(fm).__name__}")
    data = dict(fm)
    return ParsedFrontmatter(data=data, mode=mode, placeholder_keys=_placeholder_keys(data))


def _check(
    parsed: ParsedFrontmatter,
    key_sets: KeySets,
    mode: str,
    extra_validators: Mapping[str, Validator] | None = None,
) -> list[Finding]:
    if parsed.error is not None:
        return [parsed.error]
    data = parsed.data or {}
    known = key_sets.required | key_sets.optional
    findings: list[Finding] = []

    for raw_key, value in data.items():
        key = str(raw_key)
        if key == BARE_MODEL_KEY:
            # Exactly one code per key: a bare model is never also FM_FORBIDDEN_KEY.
            findings.append(
                _finding(FM_BARE_MODEL, key, "bare 'model' key; use tier-routed keys (P-013.4/P-013.5)")
            )
            continue
        if key in key_sets.forbidden:
            findings.append(_finding(FM_FORBIDDEN_KEY, key, f"key '{key}' is forbidden for this artifact"))
            continue
        if key not in known:
            findings.append(_finding(FM_UNKNOWN_KEY, key, f"unknown key '{key}'"))
        if key in parsed.placeholder_keys:
            if mode == MODE_INSTALLED:
                findings.append(
                    _finding(FM_UNRESOLVED_PLACEHOLDER, key, f"unresolved '{{{{...}}}}' placeholder in '{key}'")
                )
            # Template mode: presence counts, type validation is skipped.
            continue
        if key not in known:
            continue
        validator = (extra_validators or {}).get(key) or VALIDATORS.get(key)
        if validator is None:
            continue
        problem = validator(value)
        if problem:
            findings.append(_finding(FM_TYPE_INVALID, key, f"invalid '{key}': {problem}"))

    for key in key_sets.required:
        if key not in data:
            findings.append(_finding(FM_MISSING_REQUIRED, key, f"missing required key '{key}'"))
    return _sorted(findings)


def check_agent(fm: ParsedFrontmatter | Mapping[str, Any], profile: str, mode: str) -> list[Finding]:
    """Check agent frontmatter against ``profile``; returns findings sorted by ``(code, key)``."""
    parsed = _coerce(fm, mode)
    return _check(parsed, agent_key_sets(profile), mode)


def check_skill(fm: ParsedFrontmatter | Mapping[str, Any], directory_name: str, mode: str) -> list[Finding]:
    """Check skill frontmatter; ``name`` must equal ``directory_name``."""
    parsed = _coerce(fm, mode)

    def _skill_name(value: Any) -> str | None:
        problem = _non_empty_string(value)
        if problem:
            return problem
        if len(value) > SKILL_NAME_MAX_LENGTH:
            return f"longer than {SKILL_NAME_MAX_LENGTH} characters"
        if not SKILL_NAME_PATTERN.match(value):
            return f"{value!r} does not match {SKILL_NAME_PATTERN.pattern}"
        if value != directory_name:
            return f"{value!r} does not equal the skill directory name {directory_name!r}"
        return None

    return _check(parsed, skill_key_sets(), mode, extra_validators={"name": _skill_name})


# ---------------------------------------------------------------------------
# Profile selection
# ---------------------------------------------------------------------------


def _normalize_relative(path: Path | str) -> str:
    text = str(path).replace("\\", "/")
    while text.startswith("./"):
        text = text[2:]
    return str(PurePosixPath(text))


def agent_profile_for(path: Path | str, plugin_agents: Iterable[str]) -> str:
    """Return ``plugin-global`` when ``path`` is listed in ``plugin_agents``, else ``tier-routed``.

    Both sides are compared as normalized POSIX workspace-relative strings.
    The caller (B2a / B3) decides which ``plugin.json`` is authoritative.
    """
    target = _normalize_relative(path)
    listed = {_normalize_relative(item) for item in plugin_agents if isinstance(item, str)}
    return PROFILE_PLUGIN_GLOBAL if target in listed else PROFILE_TIER_ROUTED


__all__ = [
    "AGENT_PROFILES",
    "BARE_MODEL_KEY",
    "FM_BARE_MODEL",
    "FM_FORBIDDEN_KEY",
    "FM_MISSING_REQUIRED",
    "FM_PARSE_ERROR",
    "FM_PATH_ESCAPE",
    "FM_TYPE_INVALID",
    "FM_UNKNOWN_KEY",
    "FM_UNRESOLVED_PLACEHOLDER",
    "INFORMATIONAL_CODES",
    "MODES",
    "MODE_INSTALLED",
    "MODE_TEMPLATE",
    "NON_INFORMATIONAL_CODES",
    "PROFILE_PLUGIN_GLOBAL",
    "PROFILE_TIER_ROUTED",
    "REVIEW_ROUTE_KEY_PATTERN",
    "ROUTE_VALUE_KEYS",
    "SKILL_NAME_MAX_LENGTH",
    "SKILL_NAME_PATTERN",
    "TIER_KEYS",
    "VALIDATORS",
    "Finding",
    "KeySets",
    "ParsedFrontmatter",
    "agent_key_sets",
    "agent_profile_for",
    "check_agent",
    "check_skill",
    "has_blocking_findings",
    "parse_frontmatter",
    "read_frontmatter",
    "routing_keys",
    "skill_key_sets",
]
