"""Pure model_routing resolver: the single definition of route resolution.

A deterministic function over parsed config data. It performs no filesystem,
environment, subprocess, or network access (enforced by
``tests/_resolver_purity_guard.py``), and it must not import
``verify_workspace`` (cycle). ``config.overrides`` is deliberately not an
input: it is a render-time layer applied outside this module.

Rules reproduce the behavior pinned by
``tests/fixtures/model_routing/existing-semantics.json``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from autoharness.frontmatter_contract import CONTEXT_TIER_VALUES

ROUTE_FIELDS = ("model_family", "model_provider", "reasoning_effort", "context_tier")
ROLE_DEFAULT_TIER = MappingProxyType({"orchestrator": "tier2", "stage": "tier3", "ship": "tier2"})
ESCALATION_ROLES = ("stage", "ship")
ESCALATION_FALLBACK_TIER = "tier3"
ORCHESTRATOR_DEFAULT_FAMILY = "gpt-5.4"
# Each tier's own documented default model_family, used when the tier is absent.
TIER_OWN_FAMILY_DEFAULT = MappingProxyType(
    {
        "tier1": "gpt-5.4-mini",
        "tier2": "claude-sonnet-5",
        "tier3": "claude-opus-5",
    }
)
_ESCALATION_ROUTE_FIELDS = ("model_family", "model_provider", "reasoning_effort")
_SITES = ("stage", "ship", "orchestrator")
_KINDS = ("route", "escalation")


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def tier_dict(model_routing: Mapping[str, Any], tier_key: str) -> Mapping[str, Any]:
    """Normalise `model_routing.<tier_key>` (plain string or mapping) to a mapping."""
    tier = model_routing.get(tier_key)
    if isinstance(tier, str) and tier.strip():
        return {"model": tier, "model_family": tier}
    if isinstance(tier, Mapping):
        return tier
    return {}


def tier_fallback_dict(model_routing: Mapping[str, Any], tier_key: str) -> dict[str, Any]:
    """Tier mapping whose `model_family` defaults to the tier's own documented family."""
    result = dict(tier_dict(model_routing, tier_key))
    if not _nonblank(result.get("model_family")):
        own_default = TIER_OWN_FAMILY_DEFAULT.get(tier_key)
        if own_default:
            result["model_family"] = result.get("model") or own_default
    return result


def _route_field(
    route: Any, tier_fallback: Any, field: str, route_label: str, tier_label: str
) -> tuple[Any, str | None]:
    value = route.get(field) if isinstance(route, Mapping) else None
    if _nonblank(value):
        return value, f"{route_label}.{field}"
    if isinstance(tier_fallback, str) and tier_fallback.strip():
        tier: Mapping[str, Any] = {"model": tier_fallback, "model_family": tier_fallback}
    elif isinstance(tier_fallback, Mapping):
        tier = tier_fallback
    else:
        tier = {}
    fallback_value = tier.get(field)
    if field != "context_tier" and isinstance(fallback_value, str) and not fallback_value.strip():
        fallback_value = None
    label = f"{tier_label}.{field}"
    if field == "model_family" and not _nonblank(fallback_value):
        fallback_value = tier.get("model")
        label = f"{tier_label}.model"
    return fallback_value, (label if fallback_value else None)


def resolve_route_field(route: Any, tier_fallback: Any, field: str) -> Any:
    """Raw per-field resolution: the route's own value, else the tier's."""
    return _route_field(route, tier_fallback, field, "", "")[0]


def _context_tier(route: Any, tier_fallback: Any, route_label: str, tier_label: str) -> tuple[str, str]:
    value, label = _route_field(route, tier_fallback, "context_tier", route_label, tier_label)
    if _nonblank(value) and label is not None:
        return value, label
    return "default", "default.context_tier"


def resolve_context_tier(route: Any, tier_fallback: Any) -> str:
    """The route's `context_tier`, then the tier's, then `"default"` (never empty)."""
    return _context_tier(route, tier_fallback, "", "")[0]


def escalation_route_has_any_field(route: Any) -> bool:
    """True when a route declares at least one non-empty family/provider/effort."""
    if not isinstance(route, Mapping):
        return False
    return any(_nonblank(route.get(field)) for field in _ESCALATION_ROUTE_FIELDS)


def _escalation_blocks(model_routing: Mapping[str, Any]) -> tuple[Mapping[str, Any], dict[str, Mapping[str, Any]]]:
    flat = _mapping(model_routing.get("escalation"))
    nested = {role: _mapping(_mapping(model_routing.get(role)).get("escalation")) for role in ESCALATION_ROLES}
    return flat, nested


def nested_escalation_declared(model_routing: Mapping[str, Any]) -> bool:
    """Any nested `<role>.escalation` declares a family, provider, or effort."""
    return any(escalation_route_has_any_field(block) for block in _escalation_blocks(model_routing)[1].values())


def is_escalation_ambiguous(model_routing: Mapping[str, Any]) -> bool:
    """Legacy flat and any nested `<role>.escalation` both declare a field."""
    flat = _escalation_blocks(model_routing)[0]
    return escalation_route_has_any_field(flat) and nested_escalation_declared(model_routing)


def effective_escalation_route(model_routing: Mapping[str, Any], role: str) -> tuple[str, str, str]:
    """Effective (family, provider, effort) escalation route for one role."""
    flat, nested = _escalation_blocks(model_routing)
    block = nested.get(role) or _mapping(_mapping(model_routing.get(role)).get("escalation"))
    source = block if escalation_route_has_any_field(block) else flat
    fallback = tier_fallback_dict(model_routing, ESCALATION_FALLBACK_TIER)
    family, provider, effort = (
        _text(resolve_route_field(source, fallback, field)) for field in _ESCALATION_ROUTE_FIELDS
    )
    return family, provider, effort


def effective_escalation_context_tier(model_routing: Mapping[str, Any], role: str) -> str:
    """Nested `context_tier`, else flat only when flat is the source, else tier3, else default."""
    return _escalation_context_tier(model_routing, role)[0]


def _escalation_context_tier(model_routing: Mapping[str, Any], role: str) -> tuple[str, str]:
    flat, nested = _escalation_blocks(model_routing)
    block = nested.get(role) or _mapping(_mapping(model_routing.get(role)).get("escalation"))
    nested_value = block.get("context_tier")
    if _nonblank(nested_value):
        return nested_value, f"{role}.escalation.context_tier"
    source = {} if escalation_route_has_any_field(block) else flat
    fallback = tier_fallback_dict(model_routing, ESCALATION_FALLBACK_TIER)
    return _context_tier(source, fallback, "escalation", ESCALATION_FALLBACK_TIER)


@dataclass(frozen=True)
class ResolvedRoute:
    site: str
    kind: str
    model_family: str
    model_provider: str
    reasoning_effort: str
    context_tier: str
    tier_class: str | None
    resolution_chain: tuple[str, ...]
    degraded: tuple[str, ...]
    errors: tuple[str, ...]
    source: str = ""

    def to_document(self) -> dict[str, Any]:
        return {
            "site": self.site,
            "kind": self.kind,
            "resolved": {
                "model_family": self.model_family,
                "model_provider": self.model_provider,
                "reasoning_effort": self.reasoning_effort,
                "context_tier": self.context_tier,
                "tier_class": self.tier_class,
            },
            "resolution_chain": list(self.resolution_chain),
            "degraded": list(self.degraded),
            "errors": list(self.errors),
        }


def _error_route(site: str, kind: str, error: str) -> ResolvedRoute:
    return ResolvedRoute(site, kind, "", "", "", "", None, (), (), (error,))


def _finish(
    site: str,
    kind: str,
    values: Mapping[str, str],
    tier_class: str | None,
    chain: list[str],
    degraded: tuple[str, ...],
    errors: list[str],
    source: str = "",
) -> ResolvedRoute:
    if not _nonblank(values["model_family"]):
        errors.append("ROUTING_UNRESOLVED: model_family")
    if values["context_tier"] not in CONTEXT_TIER_VALUES:
        errors.append("ROUTING_INVALID: context_tier")
    return ResolvedRoute(
        site=site,
        kind=kind,
        model_family=values["model_family"],
        model_provider=values["model_provider"],
        reasoning_effort=values["reasoning_effort"],
        context_tier=values["context_tier"],
        tier_class=tier_class,
        resolution_chain=tuple(chain),
        degraded=degraded,
        errors=tuple(errors),
        source=source,
    )


def _resolve_fields(route: Any, tier: Any, route_label: str, tier_label: str) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    chain: list[str] = []
    for field in _ESCALATION_ROUTE_FIELDS:
        value, label = _route_field(route, tier, field, route_label, tier_label)
        values[field] = _text(value)
        if label is not None and values[field]:
            chain.append(label)
    values["context_tier"], context_label = _context_tier(route, tier, route_label, tier_label)
    chain.append(context_label)
    return values, chain


def _resolve_role_route(model_routing: Mapping[str, Any], role: str) -> ResolvedRoute:
    tier_key = ROLE_DEFAULT_TIER[role]
    values, chain = _resolve_fields(_mapping(model_routing.get(role)), model_routing.get(tier_key), role, tier_key)
    return _finish(role, "route", values, tier_key, chain, (), [])


def _resolve_orchestrator_route(model_routing: Mapping[str, Any]) -> ResolvedRoute:
    orchestrator = model_routing.get("orchestrator")
    if isinstance(orchestrator, str) and orchestrator.strip():
        route: Mapping[str, Any] = {"model_family": orchestrator}
    else:
        route = _mapping(orchestrator)
    tier2 = model_routing.get("tier2")
    values, chain = _resolve_fields(route, tier2, "orchestrator", "tier2")
    # Family never falls back to tier2: it keeps its own default.
    if _nonblank(route.get("model_family")):
        values["model_family"] = route["model_family"]
        family_label = "orchestrator.model_family"
    else:
        values["model_family"] = ORCHESTRATOR_DEFAULT_FAMILY
        family_label = "default.model_family"
    chain = [item for item in chain if not item.endswith(".model_family") and not item.endswith(".model")]
    chain.insert(0, family_label)
    return _finish("orchestrator", "route", values, "tier2", chain, (), [])


def _escalation_family_label(model_routing: Mapping[str, Any], label: str | None) -> str | None:
    if label != "tier3.model_family":
        return label
    raw = tier_dict(model_routing, ESCALATION_FALLBACK_TIER)
    if _nonblank(raw.get("model_family")):
        return label
    return "tier3.model" if _nonblank(raw.get("model")) else "tier3.default.model_family"


def _resolve_escalation(
    model_routing: Mapping[str, Any], role: str, installed_roles: frozenset[str]
) -> ResolvedRoute:
    if is_escalation_ambiguous(model_routing):
        return _error_route(
            role,
            "escalation",
            "AMBIGUOUS_ESCALATION_CONFIG: both the legacy flat "
            "model_routing.escalation and at least one nested "
            "<role>.escalation are declared -- fail closed, never "
            "auto-pick a winner (F02FD596/H2). Remove the legacy flat "
            "model_routing.escalation once migrated to nested per-role "
            "escalation, or remove the nested override(s) to keep the "
            "legacy shared route.",
        )
    flat, nested = _escalation_blocks(model_routing)
    block = nested[role]
    if escalation_route_has_any_field(block):
        source, route_label = "nested", f"{role}.escalation"
        route: Mapping[str, Any] = block
    else:
        source = "legacy_flat" if escalation_route_has_any_field(flat) else "tier3_fallback"
        route_label = "escalation"
        route = flat
    fallback = tier_fallback_dict(model_routing, ESCALATION_FALLBACK_TIER)
    values: dict[str, str] = {}
    chain: list[str] = []
    for field in _ESCALATION_ROUTE_FIELDS:
        value, label = _route_field(route, fallback, field, route_label, ESCALATION_FALLBACK_TIER)
        values[field] = _text(value)
        if field == "model_family":
            label = _escalation_family_label(model_routing, label)
        if label is not None and values[field]:
            chain.append(label)
    values["context_tier"], context_label = _escalation_context_tier(model_routing, role)
    chain.append(context_label)

    degraded: tuple[str, ...] = ()
    if role in model_routing or role in installed_roles:
        role_route = _resolve_role_route(model_routing, role)
        provider_conflicts = (
            bool(role_route.model_provider)
            and bool(values["model_provider"])
            and role_route.model_provider != values["model_provider"]
        )
        effort_conflicts = (
            bool(role_route.reasoning_effort)
            and bool(values["reasoning_effort"])
            and role_route.reasoning_effort != values["reasoning_effort"]
        )
        if (
            _nonblank(role_route.model_family)
            and role_route.model_family == values["model_family"]
            and not provider_conflicts
            and not effort_conflicts
        ):
            degraded = ("ESCALATION_DEGRADED: same-route",)
    return _finish(role, "escalation", values, ESCALATION_FALLBACK_TIER, chain, degraded, [], source)


def resolve_site(
    config: Mapping[str, Any],
    site: str,
    *,
    kind: str = "route",
    installed_roles: frozenset[str] = frozenset(),
) -> ResolvedRoute:
    """Resolve one invocation site's route (or its escalation route) from parsed config."""
    if site not in _SITES:
        return _error_route(site, kind, f"UNKNOWN_SITE: {site}")
    if kind not in _KINDS:
        return _error_route(site, kind, f"UNKNOWN_KIND: {kind}")
    model_routing = _mapping(_mapping(config).get("model_routing"))
    if kind == "route":
        if site == "orchestrator":
            return _resolve_orchestrator_route(model_routing)
        return _resolve_role_route(model_routing, site)
    if site not in ESCALATION_ROLES:
        return _error_route(site, kind, f"UNSUPPORTED: escalation is not defined for site {site}")
    return _resolve_escalation(model_routing, site, frozenset(installed_roles))
