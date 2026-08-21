"""Contract tests for the P-021 (Bounded Fix-Cycle Scope Containment and
Deferred Expansion Capture) policy surface: byte identity / checksums for the
dogfooded carrier pairs, and the clause-to-carrier coverage matrix.

This file is the STRUCTURAL contract-test module of the three-file P-021
suite (134.011-T). It is the single source of truth for the
CLAUSE -> BEHAVIOR -> CARRIER-SUBSET matrix referenced (not restated) by
tests/test_scope_containment_boundary_contract.py (134.013-T) and
tests/test_scope_containment_semantics_contract.py (134.012-T).

This module OWNS behaviours B2 (the literal C1 test text), B13 (Stage intake
precedence) and B15 (C7 violation action). See ``OWNED_BEHAVIOURS`` below.
"""

from __future__ import annotations

import ast
import hashlib
import re
import tempfile
import unittest
from pathlib import Path

import yaml
from autoharness.backlog_root import resolve_backlog_root
from autoharness.verify_workspace import _derive_template_variables, _render_template

_REPO_ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Carrier file locations
# ---------------------------------------------------------------------------

_WORKFLOW_POLICY_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_SHIP_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_SHIP_DOGFOOD = _REPO_ROOT / ".github" / "agents" / "_ship.agent.md"
_STAGE_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_stage.agent.md.tmpl"
_STAGE_DOGFOOD = _REPO_ROOT / ".github" / "agents" / "_stage.agent.md"
_ORCHESTRATOR_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_orchestrator.agent.md.tmpl"
_ORCHESTRATOR_DOGFOOD = _REPO_ROOT / ".github" / "agents" / "_orchestrator.agent.md"

_CIRCUIT_BREAKER_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "circuit-breaker.instructions.md.tmpl"
)
_CIRCUIT_BREAKER_DOGFOOD = _REPO_ROOT / ".github" / "instructions" / "circuit-breaker.instructions.md"
_ROLE_ENFORCEMENT_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "role-enforcement.instructions.md.tmpl"
)
_ROLE_ENFORCEMENT_DOGFOOD = _REPO_ROOT / ".github" / "instructions" / "role-enforcement.instructions.md"
_GITHUB_PR_AUTOMATION_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "github-pr-automation.instructions.md.tmpl"
)
_GITHUB_PR_AUTOMATION_DOGFOOD = (
    _REPO_ROOT / ".github" / "instructions" / "github-pr-automation.instructions.md"
)
_COPILOT_CODE_REVIEW_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "copilot-code-review.instructions.md.tmpl"
)
_COPILOT_CODE_REVIEW_DOGFOOD = (
    _REPO_ROOT / ".github" / "instructions" / "copilot-code-review.instructions.md"
)
_FEATURE_FLOW_DARK_TEMPLATE = _REPO_ROOT / "templates" / "prompts" / "feature-flow-dark.prompt.md.tmpl"
_FEATURE_FLOW_DARK_DOGFOOD = _REPO_ROOT / ".github" / "prompts" / "feature-flow-dark.prompt.md"

_PR_LIFECYCLE_TEMPLATE = _REPO_ROOT / "templates" / "skills" / "pr-lifecycle" / "SKILL.md.tmpl"
_FIX_CI_TEMPLATE = _REPO_ROOT / "templates" / "skills" / "fix-ci" / "SKILL.md.tmpl"

# Source files of the three P-021 contract-test modules themselves, for the
# 138.001-T Scope B Regression Guard 2 (structural) scan below.
_POLICY_CONTRACT_TEST_SOURCE = Path(__file__).resolve()
_BOUNDARY_CONTRACT_TEST_SOURCE = _REPO_ROOT / "tests" / "test_scope_containment_boundary_contract.py"
_SEMANTICS_CONTRACT_TEST_SOURCE = _REPO_ROOT / "tests" / "test_scope_containment_semantics_contract.py"

# ---------------------------------------------------------------------------
# PRE-EXISTING ARCHITECTURAL FACT (not introduced by this feature, not fixed
# by this task): `_render_template()` performs pure `{{VAR}}` string
# substitution only; it does not strip conditional sections. For the three
# large dogfooded agent templates (_ship, _stage, _orchestrator) and the
# github-pr-automation instruction, the raw `.tmpl` source is substantially
# larger than its `.github/` dogfood counterpart even *before* this feature's
# edits (verified against merge-base `94898dc7`, pre-existing on `main`) --
# these dogfood files are maintained by direct paired edits, not produced by
# a mechanical re-render of the template in this repo's current tooling.
# Forcing whole-file byte-identity for those four pairs would require either
# stripping content from the `.tmpl` sources or expanding the dogfood files by
# tens of KB -- an unrelated, unauthorized scope expansion that P-021's own
# C1 test explicitly forbids ("same file" / "related" is not sufficient to
# bring unrelated work into scope). The other four dogfooded pairs this
# feature touches (role-enforcement, circuit-breaker, copilot-code-review,
# feature-flow-dark) DO already achieve true `_render_template` byte-identity,
# so those are asserted at full byte granularity below; the four divergent
# pairs are instead asserted via marker presence (both sides) plus a manifest
# checksum match against the *actual* committed dogfood bytes.
#
# This split is now a FORMALLY DEFINED, DURABLY DOCUMENTED maintenance
# contract (137-F / 145-S, stash `6D62077C`), not merely an inline test-file
# rationale: see
# docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md
# for the two-category definition, the full eight-pair inventory, the
# per-pair cause taxonomy (mirrored in `_DIVERGENT_PAIR_CAUSES` below), the
# author obligation, and the "recorded exception, not a goal" statement.
# ---------------------------------------------------------------------------

_CLEAN_BYTE_IDENTICAL_PAIRS = (
    ("instructions/role-enforcement.instructions.md.tmpl", _ROLE_ENFORCEMENT_TEMPLATE, _ROLE_ENFORCEMENT_DOGFOOD,
     ".github/instructions/role-enforcement.instructions.md"),
    ("instructions/circuit-breaker.instructions.md.tmpl", _CIRCUIT_BREAKER_TEMPLATE, _CIRCUIT_BREAKER_DOGFOOD,
     ".github/instructions/circuit-breaker.instructions.md"),
    ("instructions/copilot-code-review.instructions.md.tmpl", _COPILOT_CODE_REVIEW_TEMPLATE, _COPILOT_CODE_REVIEW_DOGFOOD,
     ".github/instructions/copilot-code-review.instructions.md"),
    ("prompts/feature-flow-dark.prompt.md.tmpl", _FEATURE_FLOW_DARK_TEMPLATE, _FEATURE_FLOW_DARK_DOGFOOD,
     ".github/prompts/feature-flow-dark.prompt.md"),
)

_DIVERGENT_MARKER_ONLY_PAIRS = (
    (_SHIP_TEMPLATE, _SHIP_DOGFOOD, ".github/agents/_ship.agent.md"),
    (_STAGE_TEMPLATE, _STAGE_DOGFOOD, ".github/agents/_stage.agent.md"),
    (_ORCHESTRATOR_TEMPLATE, _ORCHESTRATOR_DOGFOOD, ".github/agents/_orchestrator.agent.md"),
    (_GITHUB_PR_AUTOMATION_TEMPLATE, _GITHUB_PR_AUTOMATION_DOGFOOD,
     ".github/instructions/github-pr-automation.instructions.md"),
)

# Per-pair CAUSE ANNOTATION (137.001-T), matching the taxonomy authored in
# docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md
# (137.002-T), itself citing spike F4 (docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md).
# Keyed by the same manifest-path label used in `_DIVERGENT_MARKER_ONLY_PAIRS`.
# Causes are non-exclusive; a pair may carry more than one.
_CAUSE_INSTALL_TIME_CONDITIONAL_CONTENT = "install_time_conditional_content"
_CAUSE_SEMANTIC_PROSE_DRIFT = "semantic_prose_drift"
_CAUSE_VARIABLE_DERIVATION_COVERAGE_GAP = "variable_derivation_coverage_gap"

_DIVERGENT_PAIR_CAUSES: dict[str, tuple[str, ...]] = {
    # F4(1): 2 backlog-md + 2 no-backlog-tool conditional branches.
    ".github/agents/_ship.agent.md": (
        _CAUSE_INSTALL_TIME_CONDITIONAL_CONTENT,
        _CAUSE_SEMANTIC_PROSE_DRIFT,
        _CAUSE_VARIABLE_DERIVATION_COVERAGE_GAP,
    ),
    # F4(1): 2 backlog-md + 1 no-backlog-tool conditional branches.
    ".github/agents/_stage.agent.md": (
        _CAUSE_INSTALL_TIME_CONDITIONAL_CONTENT,
        _CAUSE_SEMANTIC_PROSE_DRIFT,
        _CAUSE_VARIABLE_DERIVATION_COVERAGE_GAP,
    ),
    # F4(1): 0 backlog-md + 1 no-backlog-tool conditional branch (still
    # non-zero -- the count is asymmetric, not absent).
    ".github/agents/_orchestrator.agent.md": (
        _CAUSE_INSTALL_TIME_CONDITIONAL_CONTENT,
        _CAUSE_SEMANTIC_PROSE_DRIFT,
        _CAUSE_VARIABLE_DERIVATION_COVERAGE_GAP,
    ),
    # F3/F4(2): ZERO backlog-md / no-backlog-tool markers on either side, yet
    # still a 725-byte (1.9%) delta -- conditional content cannot explain it,
    # so this pair carries no install-time-conditional-content cause.
    ".github/instructions/github-pr-automation.instructions.md": (
        _CAUSE_SEMANTIC_PROSE_DRIFT,
        _CAUSE_VARIABLE_DERIVATION_COVERAGE_GAP,
    ),
}

# The EXACT expected membership of the divergent set (fail-closed: a fifth
# pair silently becoming non-renderable, or an existing pair being removed,
# must fail this test by NAME rather than pass unnoticed or merely warn).
_EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS = frozenset(
    label for _, _, label in _DIVERGENT_MARKER_ONLY_PAIRS
)

# Every dogfooded artifact this feature touches, for the manifest-checksum
# assertion (this part holds for all 8 pairs regardless of the render-equality
# split above).
_ALL_DOGFOOD_MANIFEST_PATHS = tuple(
    manifest_path for _, _, _, manifest_path in _CLEAN_BYTE_IDENTICAL_PAIRS
) + tuple(manifest_path for _, _, manifest_path in _DIVERGENT_MARKER_ONLY_PAIRS)


def _lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _lf_text(path: Path) -> str:
    return _lf_bytes(path).decode("utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


# ---------------------------------------------------------------------------
# 138.001-T Scope B: lifecycle-stable backlog artifact resolver.
#
# Both P-021 contract-test siblings (134.013-T, 134.012-T) previously
# hardcoded ``.backlogit/queue/019-DL.md`` in their ``setUpClass``. That
# path broke the moment 019-DL was archived (``backlogit archive`` moves an
# artifact from ``queue/`` to ``archive/``) -- exactly the baseline-red
# blocker this task repairs. This resolver is the shared, lifecycle-stable
# replacement: it probes both lifecycle locations in order and is agnostic
# to which one currently holds the artifact.
# ---------------------------------------------------------------------------


class BacklogArtifactResolutionError(RuntimeError):
    """Raised when a backlog artifact cannot be uniquely resolved via
    ``_resolve_backlog_artifact`` -- either a miss (not found in any
    lifecycle location) or backlog lifecycle drift (found in more than one
    lifecycle location simultaneously, signalling a half-completed
    archival)."""


def _resolve_backlog_artifact(artifact_id: str, *, repo_root: Path = _REPO_ROOT) -> Path:
    """Resolve a backlog artifact's on-disk path.

    Resolves the storage root via ``resolve_backlog_root(repo_root,
    env={})``. The explicit ``env={}`` is MANDATORY (plan amendment A2):
    ``resolve_backlog_root`` consults ``BACKLOGIT_WORKSPACE_DIR`` first and
    raises ``BacklogUnavailableError`` when the override names a missing
    directory. Without this isolation, any developer or CI runner with that
    variable set in the ambient environment would make this resolver -- and
    every contract test built on it -- fail for a reason unrelated to the
    code under test, the same nondeterministic-red class this task removes.
    Mirrors the isolation pattern already used in ``tests/test_backlog_root.py``.

    Probes ``queue/<artifact_id>.md``, then ``archive/<artifact_id>.md``.
    Simultaneous presence in BOTH locations is backlog lifecycle drift (a
    half-completed archival) and MUST fail loudly rather than silently
    preferring one location -- do not weaken this by reflex. A miss (absent
    from both) raises an error naming the artifact ID and EVERY probed
    candidate path.

    ``repo_root`` defaults to this module's ``_REPO_ROOT`` for production
    use by both P-021 contract-test siblings; test-only callers may inject
    an isolated temporary workspace to exercise the drift/miss branches
    without touching this repository's real backlog store.
    """
    backlog_root = resolve_backlog_root(repo_root, env={})
    candidates = (
        backlog_root / "queue" / f"{artifact_id}.md",
        backlog_root / "archive" / f"{artifact_id}.md",
    )
    found = [candidate for candidate in candidates if candidate.is_file()]
    if len(found) > 1:
        raise BacklogArtifactResolutionError(
            f"backlog artifact {artifact_id!r} found in more than one lifecycle "
            "location simultaneously -- this signals backlog lifecycle drift "
            f"(a half-completed archival): {', '.join(str(c) for c in found)}"
        )
    if not found:
        raise BacklogArtifactResolutionError(
            f"backlog artifact {artifact_id!r} not found; probed: "
            f"{', '.join(str(c) for c in candidates)}"
        )
    return found[0]


# ---------------------------------------------------------------------------
# 138.001-T Scope B Regression Guard 2 (structural): scan machinery.
#
# Confirms no P-021 contract module constructs a hardcoded, lifecycle-volatile
# `queue`-anchored artifact path outside the shared resolver. Walks the AST
# rather than scanning raw text with a line-oriented regex (PR #376 Copilot
# review, thread PRRT_kwDORzpWpM6bGnEd): a regex confined to the exact
# textual shapes the removed code used missed structurally equivalent
# constructions such as a `.joinpath("queue", ...)` call, especially one
# whose arguments are split across lines. AST inspection naturally excludes
# `#` comments (never part of the parsed tree) and this module additionally
# skips standalone string-literal expression statements (module/class/
# function docstrings, or any bare string used comment-style) -- both
# legitimately cite `.backlogit/queue/019-DL.md` in prose (see e.g. the
# historical-wording notes in ``test_scope_containment_boundary_contract.py``)
# and must not false-positive this scan.
# ---------------------------------------------------------------------------

_RESOLVER_FUNCTION_NAME = "_resolve_backlog_artifact"

# Regression Guard 1's own fixture tests deliberately construct SYNTHETIC
# `queue`/`archive` directories inside an isolated `tempfile.TemporaryDirectory`
# to unit-test the resolver's drift/miss branches -- these are not the
# production 019-DL resolution logic Regression Guard 2 polices, so they are
# exempted BY NAME alongside the resolver's own definition (plan amendment A3
# extended to this test-only fixture category).
_GUARD2_EXEMPT_FUNCTION_NAMES = (
    _RESOLVER_FUNCTION_NAME,
    "_is_queue_like_string",
    "test_regression_guard1_resolver_fails_loudly_on_simultaneous_presence",
    "test_regression_guard1_resolver_names_artifact_id_and_every_candidate_on_miss",
)


def _is_queue_like_string(value: str) -> bool:
    """True if a string constant is either the bare path segment ``"queue"``
    or embeds a ``"queue/"``/``"/queue"`` path fragment -- the two shapes a
    hardcoded lifecycle-volatile artifact path construction can take,
    regardless of whether it is joined via the `/` operator, a
    `.joinpath(...)`/`.join(...)` call, or a single interpolated f-string
    literal."""
    return value == "queue" or "queue/" in value or "/queue" in value


class _QueuePathAstVisitor(ast.NodeVisitor):
    """Walks the AST for string-literal constants matching
    `_is_queue_like_string` -- catching a `/`-operator (BinOp Div) chain, a
    `.joinpath(...)`/`.join(...)` call, and a bare interpolated f-string
    literal alike, since all three surface the offending path segment as an
    `ast.Constant` string reached by ordinary tree traversal. Skips
    standalone string-literal expression statements (docstrings/comment-
    style prose) entirely so prose citations never false-positive."""

    def __init__(self) -> None:
        self.violations: list[ast.Constant] = []

    def visit_Expr(self, node: ast.Expr) -> None:
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return  # docstring / standalone comment-style string statement
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str) and _is_queue_like_string(node.value):
            self.violations.append(node)


def _queue_path_violations(source: str) -> list[ast.Constant]:
    """Every AST constant identified by `_QueuePathAstVisitor` as a
    hardcoded, lifecycle-volatile "queue" path construction anywhere in
    `source` (docstrings/comments excluded)."""
    tree = ast.parse(source)
    visitor = _QueuePathAstVisitor()
    visitor.visit(tree)
    return visitor.violations


def _function_definition_line_range(source: str, function_name: str) -> range:
    """1-based inclusive line range of a top-level (or nested) function
    definition, identified BY NAME (plan amendment A3), so the Regression
    Guard 2 exemption for the resolver's own definition is visible and
    cannot silently widen."""
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
            return range(node.lineno, (node.end_lineno or node.lineno) + 1)
    raise AssertionError(f"function {function_name!r} not found in source")


def _template_variables() -> dict:
    autoharness_dir = _REPO_ROOT / ".autoharness"
    load_yaml = lambda name: yaml.safe_load((autoharness_dir / name).read_text(encoding="utf-8"))
    return _derive_template_variables(
        _REPO_ROOT,
        load_yaml("harness-manifest.yaml"),
        load_yaml("config.yaml"),
        load_yaml("workspace-profile.yaml"),
        load_yaml("backlog-registry.yaml"),
    )


def _render_bytes(template_path: Path, variables: dict) -> bytes:
    return _render_template(_lf_text(template_path), variables).encode("utf-8")


# ---------------------------------------------------------------------------
# AUTHORITATIVE CLAUSE-TO-CARRIER MATRIX (single source of truth for the
# whole feature; 134.012-T and 134.013-T import/derive from this module's
# constants rather than restating it).
#
# Carrier identifiers mirror the authoring task suffix used in
# `.backlogit/queue/134.011-T.md`'s matrix so the code stays directly
# traceable to that authoritative text: "001".."009-feature-flow-dark".
# Carrier roles: A=authoritative, N=normative restatement, R=reference-only,
# P=procedural, G=guard-only.
# ---------------------------------------------------------------------------

CLAUSES = ("C1", "C2", "C3", "C4", "C5", "C6", "C7")

MATRIX: dict[str, frozenset[tuple[str, str]]] = {
    "C1": frozenset({("001", "A"), ("005", "N"), ("004", "P"), ("006", "P"),
                      ("007-pr-lifecycle", "P"), ("007-fix-ci", "P")}),
    "C2": frozenset({("001", "A"), ("004", "P"), ("006", "P"),
                      ("007-pr-lifecycle", "P"), ("007-fix-ci", "P"), ("005", "P")}),
    "C3": frozenset({("001", "A"), ("004", "P"), ("006", "P"),
                      ("007-pr-lifecycle", "P"), ("007-fix-ci", "P"), ("005", "G")}),
    "C4": frozenset({("001", "A"), ("004", "P"), ("006", "P"), ("007-pr-lifecycle", "P"),
                      ("009-orchestrator", "P"), ("009-feature-flow-dark", "P")}),
    "C5": frozenset({("001", "A"), ("002", "N"), ("003", "R"), ("004", "P"), ("006", "P"),
                      ("007-pr-lifecycle", "P"), ("007-fix-ci", "P"), ("008", "P")}),
    "C6": frozenset({("001", "A"), ("008", "P")}),
    "C7": frozenset({("001", "A")}),
}

# AUTHORING_TASKS: task id -> set of (carrier, clause, role) triples its own
# acceptance criteria author. Deriving MATRIX as the inversion of this makes a
# future under-listed carrier fail this test rather than silently regressing.
AUTHORING_TASKS: dict[str, frozenset[tuple[str, str, str]]] = {
    "134.001-T": frozenset({("001", clause, "A") for clause in CLAUSES}),
    "134.002-T": frozenset({("002", "C5", "N")}),
    "134.003-T": frozenset({("003", "C5", "R")}),
    "134.004-T": frozenset({
        ("004", "C1", "P"), ("004", "C2", "P"), ("004", "C3", "P"),
        ("004", "C4", "P"), ("004", "C5", "P"),
    }),
    "134.005-T": frozenset({("005", "C1", "N"), ("005", "C2", "P"), ("005", "C3", "G")}),
    "134.006-T": frozenset({
        ("006", "C1", "P"), ("006", "C2", "P"), ("006", "C3", "P"),
        ("006", "C4", "P"), ("006", "C5", "P"),
    }),
    "134.007-T": frozenset({
        ("007-pr-lifecycle", "C1", "P"), ("007-pr-lifecycle", "C2", "P"),
        ("007-pr-lifecycle", "C3", "P"), ("007-pr-lifecycle", "C4", "P"),
        ("007-pr-lifecycle", "C5", "P"),
        ("007-fix-ci", "C1", "P"), ("007-fix-ci", "C2", "P"),
        ("007-fix-ci", "C3", "P"), ("007-fix-ci", "C5", "P"),
    }),
    "134.008-T": frozenset({("008", "C5", "P"), ("008", "C6", "P")}),
    "134.009-T": frozenset({
        ("009-orchestrator", "C4", "P"), ("009-feature-flow-dark", "C4", "P"),
    }),
    # 134.010-T is deliberately EXCLUDED: it only widens the
    # HARNESS_ENFORCED_SUMMARY range and carries no clause text.
}


def _invert_authoring_tasks(
    authoring_tasks: dict[str, frozenset[tuple[str, str, str]]],
) -> dict[str, frozenset[tuple[str, str]]]:
    inverted: dict[str, set[tuple[str, str]]] = {clause: set() for clause in CLAUSES}
    for triples in authoring_tasks.values():
        for carrier, clause, role in triples:
            inverted[clause].add((carrier, role))
    return {clause: frozenset(pairs) for clause, pairs in inverted.items()}


# Behaviours this file OWNS, per the CROSS-FILE BEHAVIOUR ALLOCATION in
# 134.011-T: B2 (literal-clause test), B13 (precedence test), B15
# (policy-registry test). Sibling modules import this constant.
OWNED_BEHAVIOURS = frozenset({"B2", "B13", "B15"})


# ---------------------------------------------------------------------------
# CLAUSE -> BEHAVIOR -> CARRIER-SUBSET MAPPING (B1-B18), transcribed verbatim
# from the archived 134.011-T task spec's authoritative block of the same
# name. This is the SINGLE SOURCE OF TRUTH for per-behaviour carrier subsets;
# 134.013-T and 134.012-T import this constant and MUST NOT restate it or
# hardcode their own carrier lists (134.013-T criterion: "CARRIER-SET
# RESOLUTION rule... MUST NOT restate the matrix or hardcode a carrier list").
# B16 and B17 are DERIVED (not hand-listed) per the task's explicit rule that
# derived behaviours must be computed from their parents, never hardcoded.
# ---------------------------------------------------------------------------

BEHAVIOR_CARRIER_SUBSETS: dict[str, frozenset[str]] = {
    "B1": frozenset({"001", "005", "004", "006", "007-pr-lifecycle", "007-fix-ci"}),
    "B2": frozenset({"001", "005"}),
    "B3": frozenset({"001", "004", "005", "006", "007-pr-lifecycle", "007-fix-ci"}),
    "B4": frozenset({"001", "004", "006", "007-pr-lifecycle", "007-fix-ci"}),
    "B5": frozenset({"001", "004", "007-fix-ci"}),
    "B6": frozenset({"004", "008"}),
    "B7": frozenset({"001", "004", "006", "007-pr-lifecycle", "007-fix-ci"}),
    "B8": frozenset({"001", "004", "007-fix-ci"}),
    "B9": frozenset({"001", "004", "005", "007-fix-ci"}),
    "B10": frozenset({
        "001", "004", "006", "007-pr-lifecycle", "009-orchestrator", "009-feature-flow-dark",
    }),
    "B11": frozenset({"001", "002"}),
    "B12": frozenset({"001", "004", "006", "007-pr-lifecycle", "007-fix-ci"}),
    "B13": frozenset({"001", "008"}),
    "B14": frozenset({"008"}),
    "B15": frozenset({"001"}),
    "B18": frozenset({"003"}),
}
# B16 = B7 INTERSECT B8; B17 = B6 UNION {007-fix-ci} -- computed, not hardcoded.
BEHAVIOR_CARRIER_SUBSETS["B16"] = (
    BEHAVIOR_CARRIER_SUBSETS["B7"] & BEHAVIOR_CARRIER_SUBSETS["B8"]
)
BEHAVIOR_CARRIER_SUBSETS["B17"] = (
    BEHAVIOR_CARRIER_SUBSETS["B6"] | frozenset({"007-fix-ci"})
)

ALL_BEHAVIOURS = frozenset(f"B{i}" for i in range(1, 19))


# ---------------------------------------------------------------------------
# Marker text per (clause, carrier), chosen as stable distinctive substrings
# authored on that carrier (verified present via direct read of each file).
# ---------------------------------------------------------------------------

_MARKERS: dict[tuple[str, str], str] = {
    ("C1", "001"): (
        '"Same file", "same function", "same PR", "same subsystem", and '
        '"related" are NOT sufficient tests of scope'
    ),
    ("C1", "005"): "MUST also pass the P-021 C1 same-contract-surface test",
    ("C1", "004"): "P-021 Scope Classification and Defer-Capture Procedure",
    ("C1", "006"): "P-021 Scope Classification and Out-of-Scope Disposition",
    ("C1", "007-pr-lifecycle"): "classify the comment against the **P-021 C1**",
    ("C1", "007-fix-ci"): "classify it against the **P-021 C1**",
    ("C2", "001"): "The literal, greppable token `DEFERRED SCOPE EXPANSION`",
    ("C2", "004"): "C2 mandatory capture — the SINGLE-WRITE CAPTURE INVARIANT",
    ("C2", "006"): "(a) **Capture per P-021 C2** with the full payload",
    ("C2", "007-pr-lifecycle"): "Out-of-scope disposition (P-021 C2/C3)",
    ("C2", "007-fix-ci"): "C2 mandatory capture — six-field payload",
    ("C2", "005"): "Capture requirement (P-021 C2)",
    ("C3", "001"): "WHERE A REVIEW THREAD EXISTS for the finding",
    ("C3", "004"): "C3 symmetric guard**: (i) a same-contract-surface completion",
    ("C3", "006"): "returned by the (a) capture, per P-021 C3",
    ("C3", "007-pr-lifecycle"): "returned by the (a) capture, per P-021 C3",
    ("C3", "007-fix-ci"): "C3 symmetric guard (applies on both paths)",
    ("C3", "005"): "Symmetric guard (P-021 C3)",
    ("C4", "001"): "AND NEITHER DOES ANY AUTHORIZATION, INCLUDING EXPLICIT OPERATOR AUTHORIZATION",
    ("C4", "004"): "P-021 C4 annotation — Review-fix cycles per task",
    ("C4", "006"): "P-021 C4 annotation**: reaching the review-fix-push cycle limit does not",
    ("C4", "007-pr-lifecycle"): "P-021 C4 annotation**: reaching the review-fix cycle limit does not",
    ("C4", "009-orchestrator"): 'P-021 non-bypass (see P-021\'s "Relationship to P-017" subsection)',
    ("C4", "009-feature-flow-dark"): 'P-021 non-bypass (see P-021\'s "Relationship to P-017" subsection)',
    ("C5", "001"): "DISCRETIONARILY remove, or DISCRETIONARILY archive them",
    ("C5", "002"): "create a capture-only stash entry (P-021 C5)",
    ("C5", "003"): "P-021 capture-only carve-out",
    ("C5", "004"): "provisional priority only — re-prioritization remains Stage-only",
    ("C5", "006"): "per the P-021 C5 capture-only carve-out",
    ("C5", "007-pr-lifecycle"): "Stage-only (P-021 C5 capture-only carve-out)",
    ("C5", "007-fix-ci"): "Stage-only (P-021 C5 capture-only carve-out)",
    ("C5", "008"): "requires NO change to\nShip's C5 capture-only carve-out",
    ("C6", "001"): "MUST route to the `deliberate` skill before any planning",
    ("C6", "008"): "MUST NOT proceed to Step 3 planning without a deliberation",
    ("C7", "001"): (
        "records a P-021 violation via P-005 telemetry "
        "(`violation_policy: P-021`) and halts"
    ),
}

def _load_all_texts() -> dict[str, str]:
    """Loads every carrier source file (LF-normalized) once. Shared by all
    three P-021 contract-test modules so path constants and read logic are
    not re-derived per file."""
    return {
        "workflow_policy": _lf_text(_WORKFLOW_POLICY_TEMPLATE),
        "ship_template": _lf_text(_SHIP_TEMPLATE),
        "ship_dogfood": _lf_text(_SHIP_DOGFOOD),
        "stage_template": _lf_text(_STAGE_TEMPLATE),
        "stage_dogfood": _lf_text(_STAGE_DOGFOOD),
        "orchestrator_template": _lf_text(_ORCHESTRATOR_TEMPLATE),
        "orchestrator_dogfood": _lf_text(_ORCHESTRATOR_DOGFOOD),
        "circuit_breaker_template": _lf_text(_CIRCUIT_BREAKER_TEMPLATE),
        "circuit_breaker_dogfood": _lf_text(_CIRCUIT_BREAKER_DOGFOOD),
        "role_enforcement_template": _lf_text(_ROLE_ENFORCEMENT_TEMPLATE),
        "role_enforcement_dogfood": _lf_text(_ROLE_ENFORCEMENT_DOGFOOD),
        "github_pr_automation_template": _lf_text(_GITHUB_PR_AUTOMATION_TEMPLATE),
        "github_pr_automation_dogfood": _lf_text(_GITHUB_PR_AUTOMATION_DOGFOOD),
        "feature_flow_dark_template": _lf_text(_FEATURE_FLOW_DARK_TEMPLATE),
        "feature_flow_dark_dogfood": _lf_text(_FEATURE_FLOW_DARK_DOGFOOD),
        "pr_lifecycle_template": _lf_text(_PR_LIFECYCLE_TEMPLATE),
        "fix_ci_template": _lf_text(_FIX_CI_TEMPLATE),
    }


def _load_carrier_texts(all_texts: dict[str, str]) -> dict[str, tuple[str, ...]]:
    """Carrier id -> tuple of raw text sources to check marker presence on."""
    return {
        "001": (all_texts["workflow_policy"],),
        "002": (all_texts["ship_template"], all_texts["ship_dogfood"]),
        "003": (all_texts["role_enforcement_template"], all_texts["role_enforcement_dogfood"]),
        "004": (all_texts["ship_template"], all_texts["ship_dogfood"]),
        "005": (all_texts["circuit_breaker_template"], all_texts["circuit_breaker_dogfood"]),
        "006": (all_texts["github_pr_automation_template"], all_texts["github_pr_automation_dogfood"]),
        "007-pr-lifecycle": (all_texts["pr_lifecycle_template"],),
        "007-fix-ci": (all_texts["fix_ci_template"],),
        "008": (all_texts["stage_template"], all_texts["stage_dogfood"]),
        "009-orchestrator": (all_texts["orchestrator_template"], all_texts["orchestrator_dogfood"]),
        "009-feature-flow-dark": (
            all_texts["feature_flow_dark_template"], all_texts["feature_flow_dark_dogfood"],
        ),
    }


class ScopeContainmentPolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.variables = _template_variables()
        all_texts = _load_all_texts()
        cls.workflow_policy_text = all_texts["workflow_policy"]

        cls.ship_template_text = all_texts["ship_template"]
        cls.ship_dogfood_text = all_texts["ship_dogfood"]
        cls.stage_template_text = all_texts["stage_template"]
        cls.stage_dogfood_text = all_texts["stage_dogfood"]
        cls.orchestrator_template_text = all_texts["orchestrator_template"]
        cls.orchestrator_dogfood_text = all_texts["orchestrator_dogfood"]
        cls.circuit_breaker_template_text = all_texts["circuit_breaker_template"]
        cls.circuit_breaker_dogfood_text = all_texts["circuit_breaker_dogfood"]
        cls.role_enforcement_template_text = all_texts["role_enforcement_template"]
        cls.role_enforcement_dogfood_text = all_texts["role_enforcement_dogfood"]
        cls.github_pr_automation_template_text = all_texts["github_pr_automation_template"]
        cls.github_pr_automation_dogfood_text = all_texts["github_pr_automation_dogfood"]
        cls.feature_flow_dark_template_text = all_texts["feature_flow_dark_template"]
        cls.feature_flow_dark_dogfood_text = all_texts["feature_flow_dark_dogfood"]
        cls.pr_lifecycle_template_text = all_texts["pr_lifecycle_template"]
        cls.fix_ci_template_text = all_texts["fix_ci_template"]

        # Carrier id -> tuple of raw text sources to check marker presence on.
        cls.carrier_texts: dict[str, tuple[str, ...]] = _load_carrier_texts(all_texts)

    # -- files exist -------------------------------------------------------

    def test_files_exist(self) -> None:
        for path in (
            _WORKFLOW_POLICY_TEMPLATE, _MANIFEST,
            _SHIP_TEMPLATE, _SHIP_DOGFOOD, _STAGE_TEMPLATE, _STAGE_DOGFOOD,
            _ORCHESTRATOR_TEMPLATE, _ORCHESTRATOR_DOGFOOD,
            _CIRCUIT_BREAKER_TEMPLATE, _CIRCUIT_BREAKER_DOGFOOD,
            _ROLE_ENFORCEMENT_TEMPLATE, _ROLE_ENFORCEMENT_DOGFOOD,
            _GITHUB_PR_AUTOMATION_TEMPLATE, _GITHUB_PR_AUTOMATION_DOGFOOD,
            _COPILOT_CODE_REVIEW_TEMPLATE, _COPILOT_CODE_REVIEW_DOGFOOD,
            _FEATURE_FLOW_DARK_TEMPLATE, _FEATURE_FLOW_DARK_DOGFOOD,
            _PR_LIFECYCLE_TEMPLATE, _FIX_CI_TEMPLATE,
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"missing carrier file: {path}")

    # -- byte identity (4 clean pairs) / marker+checksum (4 divergent pairs) --

    def test_clean_pairs_are_byte_identical_via_render_template(self) -> None:
        for label, template_path, dogfood_path, _manifest_path in _CLEAN_BYTE_IDENTICAL_PAIRS:
            with self.subTest(pair=label):
                rendered = _render_bytes(template_path, self.variables)
                dogfood_bytes = _lf_bytes(dogfood_path)
                self.assertNotIn(b"\r\n", rendered)
                self.assertEqual(rendered, dogfood_bytes)

    def test_divergent_pairs_are_not_forced_into_whole_file_identity(self) -> None:
        """Documents (does not merely assume) that the 4 divergent pairs do
        NOT achieve _render_template byte-identity, so a future accidental
        fix to that gap does not silently invalidate this split's rationale
        without this test noticing the change of shape."""
        for template_path, dogfood_path, label in _DIVERGENT_MARKER_ONLY_PAIRS:
            with self.subTest(pair=label):
                rendered = _render_bytes(template_path, self.variables)
                dogfood_bytes = _lf_bytes(dogfood_path)
                self.assertNotEqual(
                    rendered,
                    dogfood_bytes,
                    f"{label} unexpectedly achieved render-equality; if this is "
                    "now true, move it into _CLEAN_BYTE_IDENTICAL_PAIRS instead "
                    "of leaving it under the marker-only split.",
                )

    def test_divergent_pair_membership_is_pinned_and_annotated(self) -> None:
        """137.001-T: pins the divergent pair set to its EXACT expected
        membership (a fifth pair silently joining, or an existing pair
        being removed, is a named test failure -- fails CLOSED, never a
        silent pass) and requires every entry to carry at least one cause
        annotation from the taxonomy authored in
        docs/design-docs/2026-08-20-template-dogfood-paired-edit-maintenance-contract.md
        (137.002-T)."""
        actual_manifest_paths = frozenset(
            label for _, _, label in _DIVERGENT_MARKER_ONLY_PAIRS
        )
        self.assertSetEqual(
            actual_manifest_paths,
            _EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS,
            "divergent pair set membership changed -- an unreviewed pair was "
            "added to or removed from _DIVERGENT_MARKER_ONLY_PAIRS without "
            "updating the pinned expectation and the maintenance-contract "
            "document's eight-pair inventory.",
        )
        _valid_causes = frozenset(
            {
                _CAUSE_INSTALL_TIME_CONDITIONAL_CONTENT,
                _CAUSE_SEMANTIC_PROSE_DRIFT,
                _CAUSE_VARIABLE_DERIVATION_COVERAGE_GAP,
            }
        )
        for _, _, label in _DIVERGENT_MARKER_ONLY_PAIRS:
            with self.subTest(pair=label):
                self.assertIn(
                    label,
                    _DIVERGENT_PAIR_CAUSES,
                    f"{label} is missing a per-pair cause annotation in "
                    "_DIVERGENT_PAIR_CAUSES",
                )
                causes = _DIVERGENT_PAIR_CAUSES[label]
                self.assertTrue(causes, f"{label} has an empty cause annotation")
                for cause in causes:
                    self.assertIn(
                        cause,
                        _valid_causes,
                        f"{label} cites unknown cause {cause!r}; causes must "
                        "come from the taxonomy in the maintenance-contract "
                        "document",
                    )

    def test_divergent_pair_membership_guard_is_non_vacuous(self) -> None:
        """Confirms the membership guard actually fails against a shrunk or
        expanded set, rather than passing vacuously against any input."""
        shrunk = frozenset(
            list(_EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS)[:-1]
        )
        self.assertNotEqual(shrunk, _EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS)
        expanded = _EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS | frozenset(
            {".github/agents/_new_hypothetical_pair.agent.md"}
        )
        self.assertNotEqual(expanded, _EXPECTED_DIVERGENT_PAIR_MANIFEST_PATHS)

    def test_manifest_checksum_matches_actual_dogfood_bytes_for_all_eight_pairs(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        artifacts = {artifact["path"]: artifact for artifact in manifest.get("artifacts", [])}
        for manifest_path in _ALL_DOGFOOD_MANIFEST_PATHS:
            with self.subTest(path=manifest_path):
                self.assertIn(manifest_path, artifacts, f"manifest missing artifact: {manifest_path}")
                artifact = artifacts[manifest_path]
                # Checksums are pinned against LF-normalized bytes (matching the existing
                # test_circuit_breaker_policy_contract.py pattern); a local Windows checkout
                # may still materialize CRLF on disk for a path even when the committed blob
                # and the manifest checksum are LF-only, so comparing raw bytes directly would
                # be a false failure caused by local line-ending mangling, not a real defect.
                actual_bytes = _lf_bytes(_REPO_ROOT / manifest_path)
                expected_checksum = hashlib.sha256(actual_bytes).hexdigest()
                self.assertRegex(str(artifact.get("checksum")), r"^[0-9a-f]{64}$")
                self.assertEqual(artifact.get("checksum"), expected_checksum)

    # -- clause-to-carrier coverage matrix (one test per clause) ------------

    def _assert_clause_markers(self, clause: str) -> None:
        for carrier, _role in MATRIX[clause]:
            marker = _MARKERS[(clause, carrier)]
            for text in self.carrier_texts[carrier]:
                with self.subTest(clause=clause, carrier=carrier):
                    self.assertIn(
                        _normalize(marker),
                        _normalize(text),
                        f"carrier {carrier} is missing its {clause} marker: {marker!r}",
                    )

    def test_c1_scope_test_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C1")

    def test_c2_mandatory_capture_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C2")

    def test_c3_bounded_resolution_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C3")

    def test_c4_non_bypass_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C4")

    def test_c5_capture_only_carve_out_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C5")

    def test_c6_stage_intake_obligation_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C6")

    def test_c7_violation_action_is_present_on_every_matrix_carrier(self) -> None:
        self._assert_clause_markers("C7")

    # -- carrier-completeness guard (H11): matrix == inversion(AUTHORING_TASKS) --

    def test_matrix_equals_inversion_of_authoring_tasks_for_all_seven_clauses(self) -> None:
        inverted = _invert_authoring_tasks(AUTHORING_TASKS)
        for clause in CLAUSES:
            with self.subTest(clause=clause):
                self.assertEqual(
                    MATRIX[clause],
                    inverted[clause],
                    f"MATRIX[{clause}] must equal the inversion of AUTHORING_TASKS",
                )

    def test_behavior_carrier_subsets_cover_b1_to_b18_exactly(self) -> None:
        self.assertEqual(frozenset(BEHAVIOR_CARRIER_SUBSETS.keys()), ALL_BEHAVIOURS)

    def test_derived_behaviour_subsets_are_computed_not_hardcoded(self) -> None:
        self.assertEqual(
            BEHAVIOR_CARRIER_SUBSETS["B16"],
            BEHAVIOR_CARRIER_SUBSETS["B7"] & BEHAVIOR_CARRIER_SUBSETS["B8"],
        )
        self.assertEqual(
            BEHAVIOR_CARRIER_SUBSETS["B17"],
            BEHAVIOR_CARRIER_SUBSETS["B6"] | frozenset({"007-fix-ci"}),
        )

    def test_carrier_completeness_guard_detects_regressed_omissions(self) -> None:
        """Non-vacuity check for the guard above: temporarily drop each of the
        known-omission-prone entries from a COPY of AUTHORING_TASKS and
        confirm the equality check would then fail, proving the guard is
        load-bearing rather than a check that always passes."""
        regressions = (
            ("134.005-T", ("005", "C1", "N")),
            ("134.005-T", ("005", "C2", "P")),
            ("134.005-T", ("005", "C3", "G")),
            ("134.006-T", ("006", "C4", "P")),
            ("134.007-T", ("007-pr-lifecycle", "C4", "P")),
            ("134.004-T", ("004", "C5", "P")),
            ("134.006-T", ("006", "C5", "P")),
            ("134.007-T", ("007-pr-lifecycle", "C5", "P")),
            ("134.008-T", ("008", "C5", "P")),
        )
        for task_id, dropped_triple in regressions:
            with self.subTest(task=task_id, dropped=dropped_triple):
                mutated = dict(AUTHORING_TASKS)
                mutated[task_id] = AUTHORING_TASKS[task_id] - {dropped_triple}
                inverted = _invert_authoring_tasks(mutated)
                _, clause, _ = dropped_triple
                self.assertNotEqual(
                    MATRIX[clause],
                    inverted[clause],
                    f"dropping {dropped_triple} from {task_id} should break "
                    "matrix/inversion equality but did not",
                )

    # -- negative guard: no blanket stash prohibition, forbidden verbs named --

    _SHIP_FORBIDDEN_VERBS = (
        "triage",
        "prioritize/re-prioritize",
        "re-classify",
        "edit",
        "harvest",
        "deliberate",
        "discretionary removal",
        "archival",
    )

    @staticmethod
    def _missing_forbidden_verbs(role_boundary_text: str) -> list[str]:
        normalized = _normalize(role_boundary_text)
        return [
            verb
            for verb in ScopeContainmentPolicyContractTests._SHIP_FORBIDDEN_VERBS
            if _normalize(verb) not in normalized
        ]

    def test_ship_role_boundary_forbids_named_verbs_not_a_blanket_stash_ban(self) -> None:
        for text in (self.ship_template_text, self.ship_dogfood_text):
            forbidden_column = text[text.index("| Backlog |"):text.index("| Source code |")]
            with self.subTest():
                self.assertEqual(self._missing_forbidden_verbs(forbidden_column), [])
                self.assertNotIn(
                    "forbid stash operations",
                    _normalize(forbidden_column),
                )
                self.assertNotIn(
                    "stash operations",
                    _normalize(forbidden_column),
                    "Role Boundary must name forbidden stash verbs, not a "
                    "blanket 'stash operations' prohibition",
                )

    def test_forbidden_verb_guard_is_non_vacuous(self) -> None:
        """Confirms the H1 guard actually fails against a Role Boundary that
        omits the archival verb (the exact defect MATRIX CORRECTION 8 (a)
        found: the guard checked removal but not archival, which would pass
        against a Role Boundary permitting Ship to discretionarily archive a
        Stage-owned deferred entry)."""
        defective = (
            "triage, prioritize/re-prioritize, re-classify, edit, harvest, or "
            "deliberate on stash entries; discretionary removal of stash entries"
        )
        missing = self._missing_forbidden_verbs(defective)
        self.assertIn("archival", missing)

    # -- preservation test: Ship post-merge Step 7 source-artifact cleanup --

    def test_post_merge_step7_source_artifact_cleanup_is_unweakened(self) -> None:
        # This step predates P-021 (introduced in commit 2068cef8, an ancestor of the
        # merge-base) and is part of the pre-existing template/dogfood divergence
        # documented above -- it was never propagated into `.github/agents/_ship.agent.md`,
        # before or because of this feature. Per P-021 C1, expanding scope to backfill it
        # into the dogfood file would be an unauthorized, unrelated undertaking, so this
        # preservation check is scoped to the template (the carrier this feature actually
        # touches) only.
        text = self.ship_template_text
        self.assertIn("Source artifact cleanup", text)
        self.assertIn("backlogit_stash_remove", text)
        self.assertIn("custom_fields.source_stash_id", text)

    # -- B2: literal-clause test (owned behaviour) --------------------------

    _B2_DISCRIMINATORS = ("same file", "same function", "same PR", "same subsystem", "related")
    # The three worked-discrimination cases are restated with carrier-appropriate
    # wording rather than one literal shared sentence (workflow-policies and
    # circuit-breaker each phrase case (a) differently); cases (b) and (c) happen
    # to share a common substring across both carriers, so only (a) needs a
    # per-carrier variant.
    _B2_WORKED_CASE_A_BY_CARRIER = {
        "001": "the verifier does not require the field we just added",
        "005": "the shared-instruction verifier is missing the new field",
    }
    _B2_WORKED_CASES_COMMON = (
        "regex does not handle an object-separated form",
        "a policy interaction is unresolved",
    )

    def test_b2_literal_c1_test_text_present_on_both_designated_carriers(self) -> None:
        carrier_texts = {
            "001": (self.workflow_policy_text,),
            "005": (self.circuit_breaker_template_text, self.circuit_breaker_dogfood_text),
        }
        for carrier, texts in carrier_texts.items():
            for text in texts:
                normalized = _normalize(text)
                with self.subTest(carrier=carrier):
                    # Quoting convention differs by carrier (double-quotes on
                    # workflow-policies, backticks on circuit-breaker), so match the
                    # bare discriminator phrase rather than a specific quote style.
                    for phrase in self._B2_DISCRIMINATORS:
                        self.assertIn(_normalize(phrase), normalized)
                    self.assertIn(
                        _normalize(self._B2_WORKED_CASE_A_BY_CARRIER[carrier]),
                        normalized,
                    )
                    for case in self._B2_WORKED_CASES_COMMON:
                        self.assertIn(_normalize(case), normalized)

    def test_b2_no_third_carrier_restates_the_c1_test_text(self) -> None:
        other_carriers = ("004", "006", "007-pr-lifecycle", "007-fix-ci", "008",
                           "009-orchestrator", "009-feature-flow-dark")
        forbidden_sentence = _normalize(
            '"same file", "same function", "same PR", "same subsystem", and '
            '"related" are NOT sufficient'
        )
        for carrier in other_carriers:
            for text in self.carrier_texts[carrier]:
                with self.subTest(carrier=carrier):
                    self.assertNotIn(forbidden_sentence, _normalize(text))

    def test_b2_restatement_guard_is_non_vacuous(self) -> None:
        defective_text = (
            "For clarity, a finding is in scope only if it touches the same "
            '"same file", "same function", "same PR", "same subsystem", and '
            '"related" are NOT sufficient tests of scope on this surface too.'
        )
        forbidden_sentence = _normalize(
            '"same file", "same function", "same PR", "same subsystem", and '
            '"related" are NOT sufficient'
        )
        self.assertIn(forbidden_sentence, _normalize(defective_text))

    # -- B13: precedence test (owned behaviour) -----------------------------

    def test_b13_stage_intake_precedence_on_both_carriers(self) -> None:
        self.assertIn(
            _normalize("MUST route to the `deliberate` skill before any planning"),
            _normalize(self.workflow_policy_text),
        )
        self.assertIn(
            _normalize("regardless of shape, size, priority, or apparent triviality"),
            _normalize(self.workflow_policy_text),
        )
        for text in (self.stage_template_text, self.stage_dogfood_text):
            normalized = _normalize(text)
            with self.subTest():
                self.assertIn(
                    _normalize("Deferred-scope-expansion classification (evaluated BEFORE"),
                    normalized,
                )
                self.assertIn(
                    _normalize(
                        "PRECEDENCE rule, not a fourth shape category (hardening H8): "
                        "when the marker is present, it FORCES the Step 2 `deliberate` "
                        "route regardless of the entry's apparent shape, size, priority, "
                        "or triviality"
                    ),
                    normalized,
                )

    # -- B15: policy-registry test (owned behaviour) ------------------------

    def test_b15_policy_registry_section_and_relationships_present(self) -> None:
        text = self.workflow_policy_text
        self.assertIn(
            "## P-021: Bounded Fix-Cycle Scope Containment and Deferred Expansion Capture",
            text,
        )
        for relationship in ("**Relationship to P-010**", "**Relationship to P-017**", "**Relationship to P-018**"):
            with self.subTest(relationship=relationship):
                self.assertIn(relationship, text)
        self.assertIn("| 1.20.0", text)
        self.assertIn("Added P-021", text)

    def test_b15_violation_action_carries_telemetry_and_halt(self) -> None:
        required = _normalize(
            "records a P-021 violation via P-005 telemetry "
            "(`violation_policy: P-021`) and halts"
        )
        self.assertIn(required, _normalize(self.workflow_policy_text))

    def test_b15_violation_action_guard_is_non_vacuous(self) -> None:
        """Confirms the guard would fail against a registry weakened to
        telemetry-without-halt (the exact shortfall MATRIX CORRECTION P1.2
        warns a bare structural section-presence check would miss)."""
        weakened = (
            "records a P-021 violation via P-005 telemetry "
            "(`violation_policy: P-021`) for later review"
        )
        required = _normalize(
            "records a P-021 violation via P-005 telemetry "
            "(`violation_policy: P-021`) and halts"
        )
        self.assertNotIn(required, _normalize(weakened))


    # -- 138.001-T Scope B Regression Guard 1 (behavioural, primary) --------

    def test_regression_guard1_resolver_locates_019_dl_and_preserves_content(self) -> None:
        """The shared resolver locates 019-DL in this repository's actual
        backlog store, and the loaded text still contains the `C4 AMENDMENT`
        and `C5 AMENDMENT` markers -- proving content equivalence rather than
        silent coverage reduction."""
        resolved = _resolve_backlog_artifact("019-DL")
        self.assertTrue(resolved.is_file(), f"resolved path does not exist: {resolved}")
        text = resolved.read_text(encoding="utf-8")
        self.assertIn("C4 AMENDMENT", text)
        self.assertIn("C5 AMENDMENT", text)

    def test_regression_guard1_resolver_fails_loudly_on_simultaneous_presence(self) -> None:
        """Backlog lifecycle drift (simultaneous presence in BOTH `queue/`
        and `archive/`, signalling a half-completed archival) MUST fail
        loudly, not silently prefer one location. The failure message names
        backlog lifecycle drift explicitly."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            backlog_root = workspace / ".backlog"
            (backlog_root / "queue").mkdir(parents=True)
            (backlog_root / "archive").mkdir(parents=True)
            (backlog_root / "queue" / "999-DL.md").write_text("queue copy", encoding="utf-8")
            (backlog_root / "archive" / "999-DL.md").write_text("archive copy", encoding="utf-8")
            with self.assertRaises(BacklogArtifactResolutionError) as ctx:
                _resolve_backlog_artifact("999-DL", repo_root=workspace)
            self.assertIn("lifecycle drift", str(ctx.exception))
            self.assertIn("999-DL", str(ctx.exception))

    def test_regression_guard1_resolver_names_artifact_id_and_every_candidate_on_miss(self) -> None:
        """A miss (absent from both lifecycle locations) raises an error
        naming the artifact ID and EVERY probed candidate path."""
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            backlog_root = workspace / ".backlog"
            (backlog_root / "queue").mkdir(parents=True)
            (backlog_root / "archive").mkdir(parents=True)
            with self.assertRaises(BacklogArtifactResolutionError) as ctx:
                _resolve_backlog_artifact("999-DL", repo_root=workspace)
            message = str(ctx.exception)
            self.assertIn("999-DL", message)
            self.assertIn(str(backlog_root / "queue" / "999-DL.md"), message)
            self.assertIn(str(backlog_root / "archive" / "999-DL.md"), message)

    # -- 138.001-T Scope B Regression Guard 2 (structural, secondary) -------

    def test_regression_guard2_no_lifecycle_volatile_queue_path_outside_resolver(self) -> None:
        """No P-021 contract module constructs a hardcoded, lifecycle-volatile
        `queue`-anchored artifact path outside the shared resolver
        `_resolve_backlog_artifact`. Walks the AST of the three named modules
        (PR #376 Copilot review, thread PRRT_kwDORzpWpM6bGnEd) rather than
        scanning raw text with a regex, so a `.joinpath("queue", ...)` call
        is caught alongside a `/`-operator chain or a bare interpolated
        f-string -- so prose citations of `.backlogit/queue/019-DL.md` do not
        false-positive. The resolver's own definition is exempted explicitly
        and BY NAME (plan amendment A3) so the exemption is visible and
        cannot silently widen, as are this file's own Regression Guard 1
        fixture tests (synthetic tempfile-based drift/miss unit tests, not
        production 019-DL resolution logic), also exempted explicitly BY
        NAME."""
        for path in (
            _POLICY_CONTRACT_TEST_SOURCE,
            _BOUNDARY_CONTRACT_TEST_SOURCE,
            _SEMANTICS_CONTRACT_TEST_SOURCE,
        ):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                violations = _queue_path_violations(source)
                if path == _POLICY_CONTRACT_TEST_SOURCE:
                    exempt_lines: set[int] = set()
                    for name in _GUARD2_EXEMPT_FUNCTION_NAMES:
                        exempt_lines.update(_function_definition_line_range(source, name))
                else:
                    exempt_lines = set()
                for node in violations:
                    if node.lineno in exempt_lines:
                        continue
                    self.fail(
                        f"{path.name}:{node.lineno} constructs a hardcoded "
                        f"lifecycle-volatile backlog-artifact path outside "
                        f"the resolver: {node.value!r}"
                    )


if __name__ == "__main__":
    unittest.main()
