"""Render-aware template resolution harness for verifier assertions (151.003-T).

Task 3a of the SHIP-1 v1.5.0 guardrail-contract-restoration shipment
(`docs/plans/2026-08-31-ship1-v1_5_0-guardrail-contract-restoration-plan.md`).
Consumes all four deliverables of the de-risking prerequisite `151.006-T`
(`docs/spikes/2026-09-05-verify-workspace-assertion-table-enumeration.md`).

Why this exists
---------------
`verify_workspace._add_text_check` evaluates every table-driven assertion
against ``workspace_path / assertion["path"]`` -- the *installed* copy. In this
repository the installed copies are dogfood mirrors that legitimately lag the
templates, so a guardrail can be satisfied by a mirror while being
**unsatisfiable by the template that generates it** in a fresh install. That is
exactly how the two v1.5.0 shipped defects escaped.

This harness resolves each assertion to its **source of truth** per binding
plan hardening item H2 -- the ``.tmpl`` when one exists, the installed file only
when it does not -- and renders it with the verifier's **own** variable tables.

Constraints honoured
--------------------
* **H2** -- no parallel substitution path. `_derive_template_variables`,
  `_render_template`, `_resolve_artifact_role` and `_compose_artifact_variables`
  are imported from `autoharness.verify_workspace` and used verbatim.
* **Plan review finding 6** -- substitution is pure string replacement from
  fixed variable tables. No ``eval``, no shell, no network.
* **Plan review finding 5** -- renders are cached per variable set (module-level
  memo), so a test class renders once regardless of how many assertions consume
  it. Measured cost: full corpus 1.77 s, variable derivation 0.095 s
  (151.006-T deliverable 4).

Freeze-scope: this module reads templates and installed artifacts. It never
writes to the repository.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from autoharness.verify_workspace import (
    DARK_FACTORY_ASSERTIONS,
    FOUNDATION_ASSERTIONS,
    PACK_ASSERTIONS,
    _compose_artifact_variables,
    _derive_template_variables,
    _render_template,
    _resolve_artifact_role,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

#: Resolution kinds recorded per assertion so an installed-file fallback is
#: always explicit and auditable rather than accidental (151.006-T finding 2).
KIND_TEMPLATE = "template"
KIND_INSTALLED = "installed"

#: Variable-set identifiers.
VARIANT_BACKLOGIT = "backlogit"
VARIANT_NON_BACKLOGIT = "non-backlogit"


@dataclass(frozen=True)
class Assertion:
    """One entry from a verifier assertion table, with its resolved source."""

    table: str
    pack: str | None
    key: str
    path: str
    must_contain: tuple[str, ...]
    must_precede: tuple[tuple[str, str], ...]
    required: bool
    requires_pack: str | None
    source_path: Path
    source_kind: str

    @property
    def source_relative(self) -> str:
        return self.source_path.relative_to(REPO_ROOT).as_posix()


def _template_candidate(installed_path: str) -> str | None:
    """Convention map from an installed artifact path to its template path.

    151.006-T deliverable 2 established that `_resolve_source_template` cannot
    drive this mapping: manifest ``template`` fields are prose labels
    (``"global agent definition"``) for the highest-value assertion targets, and
    7 of the 29 assertion paths are absent from the dogfood manifest entirely
    because their packs are not installed here. A deterministic convention map
    covers all 29 with no residue.
    """
    path = installed_path.replace("\\", "/")
    name = path.rsplit("/", 1)[-1]
    if path == "AGENTS.md":
        return "templates/foundation/AGENTS.md.tmpl"
    if path == ".github/copilot-instructions.md":
        return "templates/foundation/copilot-instructions.md.tmpl"
    if path.startswith(".github/agents/"):
        return f"templates/agents/{name}.tmpl"
    if path.startswith(".github/instructions/"):
        return f"templates/instructions/{name}.tmpl"
    if path.startswith(".github/prompts/"):
        return f"templates/prompts/{name}.tmpl"
    if path.startswith(".github/policies/"):
        return f"templates/policies/{name}.tmpl"
    if path.startswith(".github/skills/"):
        return "templates/skills/" + "/".join(path.split("/")[2:]) + ".tmpl"
    return None


def resolve_source_of_truth(installed_path: str) -> tuple[Path, str]:
    """Resolve an assertion ``path`` to (source file, resolution kind) per H2.

    The ``.tmpl`` wins when it exists; the installed file is used only when no
    template exists (the 5 autoharness *engine* artifacts -- install-harness,
    tune-harness, workspace-discovery, auto-tune, harness-architecture -- which
    are not generated from templates at all).
    """
    candidate = _template_candidate(installed_path)
    if candidate:
        template_path = REPO_ROOT / candidate
        if template_path.is_file():
            return template_path, KIND_TEMPLATE
    return REPO_ROOT / installed_path.replace("\\", "/"), KIND_INSTALLED


def _build(table: str, pack: str | None, entry: dict[str, Any]) -> Assertion:
    source_path, source_kind = resolve_source_of_truth(str(entry["path"]))
    return Assertion(
        table=table,
        pack=pack,
        key=str(entry["key"]),
        path=str(entry["path"]).replace("\\", "/"),
        must_contain=tuple(str(item) for item in entry.get("must_contain") or ()),
        must_precede=tuple(
            (str(pair[0]), str(pair[1])) for pair in entry.get("must_precede") or ()
        ),
        required=bool(entry.get("required")),
        requires_pack=(
            str(entry["requires_pack"]) if entry.get("requires_pack") else None
        ),
        source_path=source_path,
        source_kind=source_kind,
    )


def iter_assertions() -> list[Assertion]:
    """Every table-driven assertion, in table order. No exemption list.

    The three tables are imported live from `verify_workspace`; this module
    keeps no local copy, so an assertion added upstream is swept automatically.
    """
    assertions: list[Assertion] = []
    for pack, entries in PACK_ASSERTIONS.items():
        for entry in entries:
            assertions.append(_build(f"PACK_ASSERTIONS[{pack}]", pack, entry))
    for entry in FOUNDATION_ASSERTIONS:
        assertions.append(_build("FOUNDATION_ASSERTIONS", None, entry))
    for entry in DARK_FACTORY_ASSERTIONS:
        assertions.append(_build("DARK_FACTORY_ASSERTIONS", None, entry))
    return assertions


def load_live_fixtures() -> tuple[dict, dict, dict, dict]:
    """Load this repository's own harness fixtures.

    Same loading convention as
    ``tests/test_template_variable_derivation_contract.py::_load_live_fixtures``
    so the suite keeps one convention.
    """
    autoharness_dir = REPO_ROOT / ".autoharness"
    load = lambda name: yaml.safe_load(  # noqa: E731
        (autoharness_dir / name).read_text(encoding="utf-8")
    )
    return (
        load("harness-manifest.yaml"),
        load("config.yaml"),
        load("workspace-profile.yaml"),
        load("backlog-registry.yaml"),
    )


def _non_backlogit_fixtures() -> tuple[dict, dict, dict, dict]:
    """Live fixtures rewritten to a ``backlog-md`` composition.

    ``BACKLOG_DIRECTORY`` resolves at `verify_workspace.py:3018` from
    ``registry["directory"] -> config["backlog"]["directory"] ->
    variables["BACKLOG_DIRECTORY"]``, and every later assignment in
    `_derive_template_variables` is a ``setdefault`` seeded from the manifest's
    ``variables_used``. The manifest backlog entries are therefore removed so
    they cannot shadow the override (151.006-T deliverable 3).
    """
    manifest, config, profile, registry = load_live_fixtures()
    manifest = copy.deepcopy(manifest)
    config = copy.deepcopy(config)
    registry = copy.deepcopy(registry)

    variables_used = manifest.get("variables_used") or {}
    for key in ("BACKLOG_DIRECTORY", "BACKLOG_TOOL_NAME", "BACKLOG_TOOLS", "BACKLOG_TOOL_TYPE"):
        variables_used.pop(key, None)
    manifest["variables_used"] = variables_used

    backlog_config = config.get("backlog") or {}
    backlog_config["tool"] = "backlog-md"
    backlog_config["directory"] = "backlog"
    config["backlog"] = backlog_config

    registry["tool_name"] = "backlog-md"
    registry["directory"] = "backlog"
    return manifest, config, profile, registry


def _fixtures_for(variant: str) -> tuple[dict, dict, dict, dict]:
    if variant == VARIANT_BACKLOGIT:
        return load_live_fixtures()
    if variant == VARIANT_NON_BACKLOGIT:
        return _non_backlogit_fixtures()
    raise ValueError(f"unknown variable-set variant: {variant!r}")


class RenderedCorpus:
    """Lazily rendered, cached view of assertion source-of-truth files.

    One instance per variable set. `render` memoises per source path, so the
    71 assertions (29 distinct paths) cost at most 29 renders, and a test class
    that calls `for_variant` repeatedly re-uses one instance.
    """

    def __init__(self, variant: str) -> None:
        manifest, config, profile, registry = _fixtures_for(variant)
        model_routing = config.get("model_routing") or {}
        if not isinstance(model_routing, dict):
            model_routing = {}
        self.variant = variant
        self.variables = _derive_template_variables(
            REPO_ROOT, manifest, config, profile, registry
        )
        self._model_routing = model_routing
        self._cache: dict[tuple[str, str], str] = {}

    def variables_for(self, installed_path: str) -> dict[str, str]:
        """Variable table for one artifact, with the role-scoped overlay.

        `_compose_artifact_variables` overlays the role-scoped
        ``{{ESCALATION_FAMILY/PROVIDER/REASONING_EFFORT}}`` triple for the two
        role-bearing agent artifacts and returns the base map unchanged for
        everything else.
        """
        role = _resolve_artifact_role(installed_path.replace("\\", "/"))
        return _compose_artifact_variables(self.variables, self._model_routing, role)

    def render(self, source_path: Path, installed_path: str) -> str:
        """Rendered text of one source-of-truth file (cached).

        An installed-only source is returned verbatim: it is not a template and
        contains no placeholders to resolve.
        """
        cache_key = (str(source_path), installed_path.replace("\\", "/"))
        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached
        content = source_path.read_text(encoding="utf-8")
        if source_path.suffix == ".tmpl":
            content = _render_template(content, self.variables_for(installed_path))
        self._cache[cache_key] = content
        return content

    def render_assertion(self, assertion: Assertion) -> str:
        return self.render(assertion.source_path, assertion.path)

    def evaluate(self, assertion: Assertion) -> dict[str, Any]:
        """Reproduce `_add_text_check` semantics against rendered text.

        Returns the same shape the verifier records in ``targeted_checks``:
        ``ok``, ``missing`` and ``order_violations``.
        """
        if not assertion.source_path.exists():
            return {
                "key": assertion.key,
                "source": assertion.source_relative,
                "kind": assertion.source_kind,
                "ok": False,
                "missing": list(assertion.must_contain),
                "order_violations": [],
                "reason": "missing file",
            }
        content = self.render_assertion(assertion)
        missing = [needle for needle in assertion.must_contain if needle not in content]
        order_violations = []
        for first, second in assertion.must_precede:
            first_index = content.find(first)
            second_index = content.find(second)
            if first_index == -1 or second_index == -1 or first_index >= second_index:
                order_violations.append({"before": first, "after": second})
        return {
            "key": assertion.key,
            "source": assertion.source_relative,
            "kind": assertion.source_kind,
            "ok": not missing and not order_violations,
            "missing": missing,
            "order_violations": order_violations,
        }


_CORPUS_CACHE: dict[str, RenderedCorpus] = {}


def corpus_for(variant: str = VARIANT_BACKLOGIT) -> RenderedCorpus:
    """Return the cached `RenderedCorpus` for a variable set.

    Cached at module level so ``setUpClass`` in any number of test classes
    renders at most once per variant for the whole process (plan review
    finding 5).
    """
    corpus = _CORPUS_CACHE.get(variant)
    if corpus is None:
        corpus = RenderedCorpus(variant)
        _CORPUS_CACHE[variant] = corpus
    return corpus


def render_source(installed_path: str, variant: str = VARIANT_BACKLOGIT) -> str:
    """Convenience: render one installed artifact's source of truth."""
    source_path, _kind = resolve_source_of_truth(installed_path)
    return corpus_for(variant).render(source_path, installed_path)


def unresolved_placeholders(text: str) -> list[str]:
    """Every ``{{VARIABLE}}`` token still present in rendered text.

    Used by the placeholder-hygiene acceptance criteria: a template edit must
    not introduce a variable that no variable set resolves.
    """
    import re

    return re.findall(r"\{\{[A-Z0-9_]+\}\}", text)
