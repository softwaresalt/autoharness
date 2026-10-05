"""Contract tests for attempt-08 review finding S14/P0 (PR #457).

The installed dogfood ``harness-architect`` actor (``.github/skills/harness-architect/SKILL.md``,
structurally installed by commit 07b4be79) hard-codes ``pytest`` as its Step 5.2
red-phase test command, while the authoritative P-004 policy
(``.github/policies/workflow-policies.md``) and the harness manifest's
``variables_used.TEST_COMMAND`` both require exactly
``PYTHONPATH=src python -m unittest discover -s tests`` -- this repository's real
CI gate (``.github/workflows/ci.yml``, "Run unittest suite" step). autoharness has
no pytest configuration at all (no ``[tool.pytest]`` in ``pyproject.toml``), so the
installed actor's command has never matched anything this repository can actually
run.

``src/autoharness/verify_workspace.py::_derive_template_variables`` already treats
``manifest["variables_used"]`` as authoritative (it seeds the ``variables`` dict
from the manifest FIRST, and every profile-derived default uses
``.setdefault(...)``, which is a no-op once a key already exists -- see
line ~2958, ``variables.setdefault("TEST_COMMAND", str(test["command"]))``). The
manifest's own recorded note (artifacts block, near ``FORMAT_CHECK_COMMAND``)
already documents that ``workspace-profile.yaml``'s ``test.command`` field
(``"pytest"``) is KNOWN-STALE against this repository's real gates, and that
re-running workspace-discovery to correct the profile itself was DELIBERATELY
deferred as an out-of-scope follow-up. This test suite does not reopen that
follow-up (P-021 C1: same-contract-surface only) -- it treats the actually
observed CI command in ``.github/workflows/ci.yml`` as the fourth, independent
"profile canonical test command" signal, precisely because the stored
``workspace-profile.yaml`` field is knowingly excluded from the parity set by
that existing deferral.

The fix corrects only the installed actor's Step 5.2 text (and its manifest
checksum) to the canonical, already-authoritative command, and strengthens the
Step 5.2 red-phase guardrail prose (installed copy AND the source template) so
red-phase evidence requires each generated harness test to fail individually with
its own expected marker -- rejecting zero-discovery, wrong-reason failures,
collection/import/syntax failures, skips/xfails, and passes as valid red
evidence. The template keeps its runner command as a placeholder
(``{{TEST_COMMAND}}`` / ``{{UNIMPLEMENTED_MARKER}}``); no ecosystem runner is
hard-coded into it.

192-S (186-F, Unit A of docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md)
extends this module: ``PolicyQuantifierCoherenceTests`` gains the A1 checks for the
per-task expected-RED roster wording of P-002/P-004, and
``HarnessArchitectPerTaskSemanticsTests`` holds the A2 checks for the actor's
per-task semantics. Both run over the installed file and its source template,
over LF-normalized text.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]

_INSTALLED_ACTOR = _REPO_ROOT / ".github" / "skills" / "harness-architect" / "SKILL.md"
_SOURCE_TEMPLATE = _REPO_ROOT / "templates" / "skills" / "harness-architect" / "SKILL.md.tmpl"
_POLICY_REGISTRY = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"
_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

_ACTOR_MANIFEST_PATH_KEY = ".github/skills/harness-architect/SKILL.md"
_POLICY_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"

# The canonical, authoritative command per P-004 / the manifest / CI ground truth.
_CANONICAL_TEST_COMMAND = "PYTHONPATH=src python -m unittest discover -s tests"
_CANONICAL_BUILD_CHECK_COMMAND = "python -m py_compile src/autoharness/cli.py"

# 192-S / 186-F (Unit A): the Marker Convention, copied verbatim from the
# "Marker Convention" section of docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
# (revision 9, blob b7a77c76). Held here as a constant so a later plan revision
# cannot silently change what the policy and actor texts are checked against.
_MARKER_CONVENTION = (
    "Each task's `Marker` value is a **prefix**. Every roster test `t` has its "
    "own marker `<prefix>:<t>`, where `<t>` is its Proof G case ID or test "
    "method name. It reaches a RED-phase stub that raises exactly "
    '`NotImplementedError("<prefix>:<t>")`. The stub is either per behavior, or '
    "derives the suffix deterministically from the test's distinct request. "
    "The harness asserts the roster's markers are pairwise distinct, and the RED "
    "record maps each roster test to its marker. Two roster tests sharing one "
    "marker is a cross-test marker, which FI-9 refuses. Structural tests that "
    "reach no stub (API, docstring, schema parity, pinned hash, alias, audit) "
    "are recorded outside the roster, like characterization tests."
)

# IM-14 / PE-SAFETY-06 detector (plan "Non-Claim Audit Inventory"), applied to
# normalized text: lowercased, `_` and `-` as spaces, whitespace runs collapsed.
_NON_CLAIM_DETECTOR = re.compile(
    r"\b(?:rac(?:e[sd]?|ing|y)|toctt?ous?|time of check|hard ?link\w*|symlink ?swap\w*)\b"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_lf(path: Path) -> str:
    """Strict UTF-8 decode with CRLF/CR normalized to LF (the templates are not eol=lf pinned)."""
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _non_claim_hits(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.lower().replace("_", " ").replace("-", " "))
    return [m.group(0) for m in _NON_CLAIM_DETECTOR.finditer(normalized)]


def _render_policy(section: str) -> str:
    """Substitute the policy template placeholders the P-002/P-004 entries use."""
    return section.replace("{{BUILD_CHECK_COMMAND}}", _CANONICAL_BUILD_CHECK_COMMAND).replace(
        "{{TEST_COMMAND}}", _CANONICAL_TEST_COMMAND
    )


def _load_manifest() -> dict:
    return yaml.safe_load(_read(_MANIFEST))


def _step_5_2_section(content: str) -> str:
    """Extract the 'Step 5.2: Red phase check' section body."""
    match = re.search(
        r"#### Step 5\.2: Red phase check\s*\n(.*?)(?=\n#### |\n### |\Z)",
        content,
        re.DOTALL,
    )
    assert match, "Step 5.2: Red phase check section not found"
    return match.group(1)


def _p004_section(content: str) -> str:
    """Extract the '## P-004: Red Phase Before Implementation' policy entry body."""
    match = re.search(
        r"## P-004: Red Phase Before Implementation.*?(?=\n## P-005|\Z)",
        content,
        re.DOTALL,
    )
    assert match, "P-004 policy entry not found"
    return match.group(0)


def _p002_section(content: str) -> str:
    """Extract the '## P-002: TDD Gate' policy entry body (regression guard only)."""
    match = re.search(
        r"## P-002: TDD Gate \(Harness-Ready Precondition\).*?(?=\n## P-003|\Z)",
        content,
        re.DOTALL,
    )
    assert match, "P-002 policy entry not found"
    return match.group(0)


class TemplateEnvironmentAgnosticTests(unittest.TestCase):
    """The source template keeps the runner command as a placeholder: no runner
    name or resolved command is hard-coded into Step 5.2. (The literal
    Python-unittest RED vocabulary that 192-S states verbatim from plan FI-9 --
    `ERROR`, `NotImplementedError`, `AssertionError` -- is intentional; its
    portability to non-Python consumers is deferred to stash EC980E56.)"""

    def test_template_exists(self) -> None:
        self.assertTrue(_SOURCE_TEMPLATE.exists())

    def test_template_step_5_2_uses_test_command_placeholder(self) -> None:
        content = _read(_SOURCE_TEMPLATE)
        section = _step_5_2_section(content)
        self.assertIn("{{TEST_COMMAND}}", section)

    def test_template_never_hard_codes_pytest_or_unittest(self) -> None:
        content = _read(_SOURCE_TEMPLATE)
        section = _step_5_2_section(content)
        self.assertNotIn("pytest", section)
        self.assertNotIn("unittest", section)
        self.assertNotIn(_CANONICAL_TEST_COMMAND, section)


class FourSourceParityTests(unittest.TestCase):
    """Installed actor, P-004, manifest variable, and CI ground truth agree."""

    def test_installed_actor_step_5_2_contains_canonical_command(self) -> None:
        content = _read(_INSTALLED_ACTOR)
        section = _step_5_2_section(content)
        self.assertIn(_CANONICAL_TEST_COMMAND, section)
        self.assertNotIn("pytest", section)

    def test_installed_p004_precondition_requires_canonical_command(self) -> None:
        content = _read(_POLICY_REGISTRY)
        # Find the P-004 entry specifically, not just anywhere in the file.
        match = re.search(r"## P-004: Red Phase Before Implementation.*?(?=\n## P-005|\Z)", content, re.DOTALL)
        self.assertIsNotNone(match, "P-004 entry not found in policy registry")
        p004_text = match.group(0)
        self.assertIn(_CANONICAL_TEST_COMMAND, p004_text)
        self.assertNotIn("pytest", p004_text)

    def test_manifest_variables_used_test_command_is_canonical(self) -> None:
        manifest = _load_manifest()
        variables_used = manifest.get("variables_used") or {}
        self.assertEqual(variables_used.get("TEST_COMMAND"), _CANONICAL_TEST_COMMAND)

    def test_ci_workflow_observed_command_is_canonical(self) -> None:
        content = _read(_CI_WORKFLOW)
        self.assertIn(_CANONICAL_TEST_COMMAND, content)
        self.assertIn("Run unittest suite", content)

    def test_all_four_sources_agree_verbatim(self) -> None:
        actor_section = _step_5_2_section(_read(_INSTALLED_ACTOR))
        policy_match = re.search(
            r"## P-004: Red Phase Before Implementation.*?(?=\n## P-005|\Z)",
            _read(_POLICY_REGISTRY),
            re.DOTALL,
        )
        assert policy_match
        manifest = _load_manifest()
        manifest_value = (manifest.get("variables_used") or {}).get("TEST_COMMAND")
        ci_content = _read(_CI_WORKFLOW)

        sources = {
            "installed actor Step 5.2": _CANONICAL_TEST_COMMAND in actor_section,
            "installed P-004": _CANONICAL_TEST_COMMAND in policy_match.group(0),
            "manifest variables_used.TEST_COMMAND": manifest_value == _CANONICAL_TEST_COMMAND,
            "CI workflow (profile canonical/ground-truth command)": _CANONICAL_TEST_COMMAND in ci_content,
        }
        failing = [name for name, ok in sources.items() if not ok]
        self.assertEqual(
            failing,
            [],
            f"sources disagree with canonical command {_CANONICAL_TEST_COMMAND!r}: {failing}",
        )


class ExactInvocationTests(unittest.TestCase):
    """The actor invokes exactly the resolved TEST_COMMAND -- no runner substitution."""

    def test_actor_invokes_exact_resolved_command_no_substitution(self) -> None:
        content = _read(_INSTALLED_ACTOR)
        section = _step_5_2_section(content)
        match = re.search(r"Run `([^`]+)` for the harness tests", section)
        self.assertIsNotNone(match, "expected 'Run `<command>` for the harness tests' in Step 5.2")
        invoked_command = match.group(1)
        self.assertEqual(
            invoked_command,
            _CANONICAL_TEST_COMMAND,
            "actor must invoke exactly the resolved TEST_COMMAND, not a substituted runner",
        )


class RedEvidenceMarkerCorrelationTests(unittest.TestCase):
    """P-004 red evidence requires each test to fail with its own marker."""

    _REJECTED_CONCEPTS = [
        "zero-discovery",
        "wrong-reason",
        "collection/import/syntax",
        "skip",
        "xfail",
        "unexpectedsuccess",
    ]

    def test_installed_actor_step_5_2_requires_per_test_marker(self) -> None:
        section = _step_5_2_section(_read(_INSTALLED_ACTOR)).lower()
        self.assertIn("own expected failure marker", section)

    def test_installed_actor_step_5_2_rejects_degenerate_red_evidence(self) -> None:
        section = _step_5_2_section(_read(_INSTALLED_ACTOR)).lower()
        missing = [c for c in self._REJECTED_CONCEPTS if c not in section]
        self.assertEqual(missing, [], f"Step 5.2 does not reject: {missing}")
        # "pass" as a rejected outcome, distinct from the prose verb "passes".
        self.assertIn("false positive", section)

    def test_template_step_5_2_requires_per_test_marker_and_stays_generic(self) -> None:
        section = _step_5_2_section(_read(_SOURCE_TEMPLATE)).lower()
        self.assertIn("own expected failure marker", section)
        missing = [c for c in self._REJECTED_CONCEPTS if c not in section]
        self.assertEqual(missing, [], f"template Step 5.2 does not reject: {missing}")
        self.assertIn("{{test_command}}", section)
        self.assertIn("{{unimplemented_marker}}", section)


class ChecksumAndSingleEntryTests(unittest.TestCase):
    """The installed actor's bytes match its manifest checksum; no duplicates."""

    def test_manifest_has_exactly_one_actor_entry(self) -> None:
        manifest = _load_manifest()
        artifacts = [a for a in (manifest.get("artifacts") or []) if isinstance(a, dict)]
        matches = [a for a in artifacts if a.get("path") == _ACTOR_MANIFEST_PATH_KEY]
        self.assertEqual(
            len(matches),
            1,
            f"expected exactly one manifest artifact entry for {_ACTOR_MANIFEST_PATH_KEY}, found {len(matches)}",
        )

    def test_installed_actor_bytes_match_manifest_checksum(self) -> None:
        import hashlib

        manifest = _load_manifest()
        artifacts = [a for a in (manifest.get("artifacts") or []) if isinstance(a, dict)]
        matches = [a for a in artifacts if a.get("path") == _ACTOR_MANIFEST_PATH_KEY]
        self.assertEqual(len(matches), 1)
        expected_checksum = matches[0].get("checksum")
        actual_checksum = hashlib.sha256(_INSTALLED_ACTOR.read_bytes()).hexdigest()
        self.assertEqual(
            actual_checksum,
            expected_checksum,
            "installed actor bytes do not match the manifest-recorded checksum",
        )


class PolicyQuantifierCoherenceTests(unittest.TestCase):
    """PR #457 follow-up: P-004's precondition previously required expected failure
    markers "in the output for every test function" -- read literally, this is a
    global whole-suite quantifier that is unsatisfiable in a healthy repository with
    established passing tests, and would forever block any future task once the
    real red-phase evidence (this task's generated harness tests only) exists
    alongside the rest of the suite. The already-remediated harness-architect actor
    (Step 5.2, fixed in a prior PR #457 commit) correctly scopes red-phase evidence
    to "EVERY generated harness test", never to the full historical test
    population. This test class proves the P-004 policy statement is now scoped
    identically and stays coherent with the actor across both the installed policy
    file and its source template, without disturbing P-002's role-separation
    semantics (only harness-architect applies `harness-ready`; ship never bypasses
    the gate).
    """

    def test_installed_p004_does_not_quantify_over_every_test_function(self) -> None:
        section = _p004_section(_read(_POLICY_REGISTRY)).lower()
        self.assertNotIn(
            "for every test function",
            section,
            "P-004 must not require expected markers for every test function "
            "in the whole suite -- unsatisfiable once established tests exist",
        )

    def test_template_p004_does_not_quantify_over_every_test_function(self) -> None:
        section = _p004_section(_read(_POLICY_TEMPLATE)).lower()
        self.assertNotIn("for every test function", section)

    def test_installed_p004_states_compilation_succeeds(self) -> None:
        section = _p004_section(_read(_POLICY_REGISTRY))
        self.assertIn(_CANONICAL_BUILD_CHECK_COMMAND, section)
        self.assertIn("exits 0", section)

    def test_installed_p004_states_whole_suite_exits_nonzero_because_current_task_red(self) -> None:
        section = _p004_section(_read(_POLICY_REGISTRY)).lower()
        self.assertIn("canonical whole-suite test command", section)
        self.assertIn("current task", section)
        self.assertIn("exits non-zero", section)

    def test_installed_p004_states_every_generated_harness_test_discovered_and_marked(self) -> None:
        section = _p004_section(_read(_POLICY_REGISTRY)).lower()
        self.assertIn("every generated harness test", section)
        self.assertIn("own expected failure marker", section)

    def test_installed_p004_states_unrelated_established_tests_may_pass(self) -> None:
        section = _p004_section(_read(_POLICY_REGISTRY)).lower()
        self.assertIn("unrelated established tests", section)
        self.assertIn("may pass", section)

    def test_installed_p004_rejects_all_five_required_outcomes(self) -> None:
        section = _p004_section(_read(_POLICY_REGISTRY)).lower()
        required = [
            "zero-discovery",
            "collection/import/syntax",
            "missing, wrong, or cross-test markers",
            "expectedfailure",
            "unexpectedsuccess",
        ]
        missing = [r for r in required if r not in section]
        self.assertEqual(missing, [], f"P-004 does not reject: {missing}")

    def test_template_p004_uses_environment_agnostic_variables_not_hardcoded(self) -> None:
        section = _p004_section(_read(_POLICY_TEMPLATE))
        self.assertIn("{{BUILD_CHECK_COMMAND}}", section)
        self.assertIn("{{TEST_COMMAND}}", section)
        self.assertNotIn(_CANONICAL_BUILD_CHECK_COMMAND, section)
        self.assertNotIn(_CANONICAL_TEST_COMMAND, section)

    def test_template_and_installed_p004_agree_after_variable_substitution(self) -> None:
        template_section = _p004_section(_read(_POLICY_TEMPLATE))
        installed_section = _p004_section(_read(_POLICY_REGISTRY))
        rendered = template_section.replace("{{BUILD_CHECK_COMMAND}}", _CANONICAL_BUILD_CHECK_COMMAND).replace(
            "{{TEST_COMMAND}}", _CANONICAL_TEST_COMMAND
        )
        self.assertEqual(
            rendered,
            installed_section,
            "template P-004 (with variables substituted) must match the installed P-004 verbatim",
        )

    def test_p002_role_separation_semantics_untouched(self) -> None:
        """Regression guard: this fix must not touch P-002's role-separation
        semantics -- only harness-architect applies `harness-ready`, ship never
        bypasses the gate."""
        section = _p002_section(_read(_POLICY_REGISTRY))
        self.assertIn(
            "The ship agent may only claim and implement a task after the "
            "harness-architect has confirmed",
            section,
        )
        self.assertIn("`harness-ready`", section)

    def test_actor_and_policy_both_reject_unexpected_success(self) -> None:
        """Coherence check: the actor's rejection list and the policy's rejection
        list both name unexpectedSuccess as invalid red-phase evidence."""
        actor_section = _step_5_2_section(_read(_INSTALLED_ACTOR)).lower()
        policy_section = _p004_section(_read(_POLICY_REGISTRY)).lower()
        self.assertIn("unexpectedsuccess", actor_section)
        self.assertIn("unexpectedsuccess", policy_section)

    # ------------------------------------------------------------------
    # 192-S / 186.001-T (A1): P-002 and P-004 per-task expected-RED roster
    # wording. Each check runs over both the installed policy file and its
    # source template, over LF-normalized text.
    # ------------------------------------------------------------------

    _POLICY_SOURCES = {"installed": _POLICY_REGISTRY, "template": _POLICY_TEMPLATE}

    def _p002(self, which: str) -> str:
        return _p002_section(_read_lf(self._POLICY_SOURCES[which]))

    def _p004(self, which: str) -> str:
        return _p004_section(_read_lf(self._POLICY_SOURCES[which]))

    def test_p002_scopes_red_obligation_to_current_task_roster(self) -> None:
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                section = self._p002(which)
                self.assertNotIn("all tests fail", section)
                self.assertIn("current task's expected-RED roster", section)
                postcondition = re.search(r"\*\*Postcondition\*\* \(harness-architect\):(.*)", section)
                self.assertIsNotNone(postcondition, "P-002 harness-architect Postcondition not found")
                self.assertIn("expected-RED roster", postcondition.group(1))
                self.assertIn("P-004", postcondition.group(1))

    def test_template_and_installed_p002_agree_after_variable_substitution(self) -> None:
        self.assertEqual(_render_policy(self._p002("template")), self._p002("installed"))

    def test_p004_defines_roster_excluding_characterization_tests(self) -> None:
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                section = _collapse_ws(self._p004(which))
                self.assertIn(
                    "The current task's expected-RED roster is the current task's generated "
                    "harness tests, excluding characterization tests.",
                    section,
                )
                self.assertIn(
                    "Characterization tests are recorded separately, outside the roster, and may pass.",
                    section,
                )
                self.assertIn("Structural tests that reach no stub are likewise outside the roster", section)

    def test_p004_precondition_binds_every_task_except_harness_surface_none(self) -> None:
        """No empty-roster escape: the Precondition applies to every task except a
        `harness-surface:none` task."""
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                section = _collapse_ws(self._p004(which))
                self.assertIn(
                    "**Precondition** (every task except a `harness-surface:none` task, which has "
                    "no roster and no RED obligation): All of the following must be true:",
                    section,
                )
                self.assertNotIn("for a task with an expected-RED roster", section)

    def test_p004_red_is_error_with_own_not_implemented_marker_roster_relative(self) -> None:
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                section = _collapse_ws(self._p004(which))
                self.assertIn(
                    "RED for a roster test is that test reported as `ERROR` in the canonical "
                    "command's output with its own unique `NotImplementedError` marker",
                    section,
                )
                self.assertIn("roster-relative (R2)", section)
                self.assertIn(
                    "A roster test absent from the named `ERROR` set, or named with a different "
                    "marker, is refused.",
                    section,
                )

    def test_p004_refuses_marker_bearing_assertion_error(self) -> None:
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                section = self._p004(which)
                refused = section.split("NEVER valid red-phase evidence", 1)
                self.assertEqual(len(refused), 2, "P-004 refused-outcome list not found")
                self.assertIn("Marker-bearing `AssertionError`", refused[1])

    def test_p004_harness_surface_none_has_no_roster_and_is_bounded(self) -> None:
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                section = _collapse_ws(self._p004(which))
                self.assertIn(
                    "A task declaring `harness-surface:none` has no roster and no RED obligation.",
                    section,
                )
                self.assertIn(
                    "`harness-surface:none` is allowed only for a task whose file budget contains "
                    "no Python production module under `src/`.",
                    section,
                )
                self.assertIn(
                    "A declaration outside this limit is invalid, and the harness-architect does not "
                    "apply `harness-ready`.",
                    section,
                )

    def test_p004_states_marker_convention_verbatim(self) -> None:
        for which in self._POLICY_SOURCES:
            with self.subTest(source=which):
                self.assertIn(_collapse_ws(_MARKER_CONVENTION), _collapse_ws(self._p004(which)))

    def test_p004_states_canonical_command_verbatim(self) -> None:
        self.assertIn(f"`{_CANONICAL_TEST_COMMAND}`", self._p004("installed"))
        self.assertIn("`{{TEST_COMMAND}}`", self._p004("template"))
        self.assertIn("no added flags such as `-v`", self._p004("installed"))

    def test_version_history_records_p002_p004_roster_change(self) -> None:
        for which, path in self._POLICY_SOURCES.items():
            with self.subTest(source=which):
                rows = [
                    line
                    for line in _read_lf(path).splitlines()
                    if line.startswith("| 1.32.0 ")
                ]
                self.assertEqual(len(rows), 1, "expected exactly one 1.32.0 version-history row")
                self.assertIn("P-002", rows[0])
                self.assertIn("P-004", rows[0])
                self.assertIn("186.001-T", rows[0])

    def test_p002_and_p004_make_no_race_toctou_or_hardlink_claim(self) -> None:
        """IM-14: the edited policy entries and the 1.32.0 history row carry no race,
        TOCTOU or hardlink-alias wording at all."""
        for which, path in self._POLICY_SOURCES.items():
            with self.subTest(source=which):
                self.assertEqual(_non_claim_hits(self._p002(which)), [])
                self.assertEqual(_non_claim_hits(self._p004(which)), [])
                rows = [line for line in _read_lf(path).splitlines() if line.startswith("| 1.32.0 ")]
                self.assertEqual(len(rows), 1)
                self.assertEqual(_non_claim_hits(rows[0]), [])

    def test_installed_policy_bytes_match_manifest_checksum(self) -> None:
        """IM-12 replay for the policy entry: the recorded checksum equals the SHA-256
        of the installed file's bytes (the file is eol=lf pinned, so the working-tree
        bytes equal the committed blob)."""
        import hashlib

        artifacts = [a for a in (_load_manifest().get("artifacts") or []) if isinstance(a, dict)]
        matches = [a for a in artifacts if a.get("path") == ".github/policies/workflow-policies.md"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(hashlib.sha256(_POLICY_REGISTRY.read_bytes()).hexdigest(), matches[0].get("checksum"))


def _actor_step_section(content: str, heading: str) -> str:
    """Extract one '### Step N: ...' section of the actor (up to the next '### ' heading)."""
    match = re.search(rf"^### {re.escape(heading)}\s*\n(.*?)(?=^### |^## |\Z)", content, re.DOTALL | re.MULTILINE)
    if match is None:
        raise AssertionError(f"actor section {heading!r} not found")
    return match.group(1)


def _actor_h2_section(content: str, heading: str) -> str:
    """Extract one '## <heading>' section of the actor (up to the next '## ' heading)."""
    match = re.search(rf"^## {re.escape(heading)}\s*\n(.*?)(?=^## |\Z)", content, re.DOTALL | re.MULTILINE)
    if match is None:
        raise AssertionError(f"actor section {heading!r} not found")
    return match.group(1)


def _frontmatter(content: str) -> dict:
    match = re.match(r"---\n(.*?)\n---\n", content, re.DOTALL)
    if match is None:
        raise AssertionError("actor frontmatter not found")
    return yaml.safe_load(match.group(1))


class NonClaimDetectorControlTests(unittest.TestCase):
    """Positive and negative controls for ``_non_claim_hits`` so the IM-14 checks
    below cannot pass because the detector itself is broken."""

    def test_detector_hits_claim_forms(self) -> None:
        for text in (
            "race",
            "races",
            "racing",
            "race_free",
            "TOCTOU",
            "TOCTTOU",
            "test_toctou_safe",
            "time-of-check",
            "hard-link",
            "hardlinks",
            "hard-linked",
            "symlink_swap",
        ):
            with self.subTest(text=text):
                self.assertNotEqual(_non_claim_hits(text), [])

    def test_detector_ignores_non_claim_words(self) -> None:
        for text in ("trace-free", "embrace-safe", "grace period", "bracket"):
            with self.subTest(text=text):
                self.assertEqual(_non_claim_hits(text), [])


class HarnessArchitectPerTaskSemanticsTests(unittest.TestCase):
    """192-S / 186.002-T (A2): the harness-architect actor operates on exactly one
    caller-supplied current task, records characterization-first harnesses outside
    the expected-RED roster, states A1's roster/ERROR/R2/refusal rules and the
    Marker Convention in Step 5.2, and records a per-task harness-ready evidence
    record in Step 6. Each check runs over both the installed actor and its source
    template, over LF-normalized text. The installed file is edited in parallel
    hunks and is never re-rendered (its existing line-reflow mismatch with the
    template is left for the IM-10 unit), so Step 5.2 is compared clause by clause
    rather than whole-section.
    """

    _ACTOR_SOURCES = {"installed": _INSTALLED_ACTOR, "template": _SOURCE_TEMPLATE}
    _STEP_1 = "Step 1: Select the current task"
    _STEP_2 = "Step 2: Read task intent"
    _STEP_3 = "Step 3: Determine execution posture"
    _STEP_6 = "Step 6: Apply harness-ready label to the current task"

    def _text(self, which: str) -> str:
        return _read_lf(self._ACTOR_SOURCES[which])

    def _step(self, which: str, heading: str) -> str:
        return _collapse_ws(_actor_step_section(self._text(which), heading))

    def _step_5_2(self, which: str) -> str:
        return _collapse_ws(_step_5_2_section(self._text(which)))

    def test_step_1_selects_exactly_one_caller_supplied_task_and_never_claims(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                text = self._text(which)
                self.assertNotIn("### Step 1: Claim the ready task set", text)
                step = self._step(which, self._STEP_1)
                self.assertIn("exactly one current task supplied by the caller", step)
                self.assertIn("The actor never claims backlog work", step)
                self.assertIn("never defaults to a ready-task set", step)

    def test_inputs_describe_one_current_task_not_all_ready_tasks(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                text = self._text(which)
                self.assertNotIn("defaults to all ready tasks", text)
                self.assertNotIn("use all ready tasks under the feature", text)
                self.assertNotIn("{task_count}", text)
                inputs = _collapse_ws(_actor_h2_section(text, "Inputs"))
                self.assertIn("`${input:tasks}`: (Required) Exactly one current task ID", inputs)
                frontmatter = _frontmatter(text)
                self.assertEqual(frontmatter["input"]["required"], ["feature", "tasks"])
                self.assertTrue(
                    frontmatter["input"]["properties"]["tasks"]["description"].startswith(
                        "Exactly one current task ID"
                    )
                )

    def test_step_3_records_characterization_tests_outside_roster(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                step = self._step(which, self._STEP_3)
                self.assertIn(
                    "In a characterization-first posture, the characterization tests are recorded "
                    "outside the expected-RED roster",
                    step,
                )
                self.assertIn("Tests for new or changed behavior remain roster tests, except structural "
                              "tests that reach no stub, which stay outside the roster", step)

    def test_step_5_2_states_roster_rule(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                section = self._step_5_2(which)
                self.assertIn(
                    "The current task's expected-RED roster is the current task's generated "
                    "harness tests, excluding characterization tests.",
                    section,
                )
                self.assertIn(
                    "Characterization tests are recorded separately, outside the roster, and may pass.",
                    section,
                )
                self.assertIn("Structural tests that reach no stub are likewise outside the roster", section)
                self.assertIn(
                    "A task declaring `harness-surface:none` has no roster and no RED obligation.",
                    section,
                )
                self.assertIn(
                    "`harness-surface:none` is allowed only for a task whose file budget contains "
                    "no Python production module under `src/`; if the current task declares it but "
                    "its file budget contains one, halt and report without applying `harness-ready`.",
                    section,
                )

    def test_step_5_2_states_error_classification_and_r2_attribution(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                section = self._step_5_2(which)
                self.assertIn(
                    "RED for a roster test is that test reported as `ERROR` in the canonical "
                    "command's output with its own unique `NotImplementedError` marker",
                    section,
                )
                self.assertIn("roster-relative (R2)", section)
                self.assertIn(
                    "A roster test absent from the named `ERROR` set, or named with a different "
                    "marker, is refused.",
                    section,
                )

    def test_step_5_2_refuses_marker_bearing_assertion_error(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                section = self._step_5_2(which)
                refused = section.split("NEVER valid red-phase evidence", 1)
                self.assertEqual(len(refused), 2, "Step 5.2 refused-outcome list not found")
                self.assertIn("**Marker-bearing `AssertionError`**", refused[1])
                self.assertIn("**Cross-test marker**", refused[1])

    def test_step_5_2_refused_outcomes_are_scoped_to_roster_tests(self) -> None:
        """A passing characterization test is never a harness defect: the refused list,
        its bullets and the closing fix-until rule all speak of roster tests only."""
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                section = self._step_5_2(which)
                self.assertIn("NEVER valid red-phase evidence for a roster test", section)
                for bullet in (
                    "**Wrong-reason failure**: a roster test fails",
                    "**Skip or expected-failure (xfail)**: a roster test reported",
                    "**Pass or unexpectedSuccess**: a roster test that passes",
                ):
                    self.assertIn(bullet, section)
                self.assertIn(
                    "If any roster test exhibits one of these outcomes, fix the harness until every "
                    "roster test is discovered and is reported as `ERROR` with its own marker.",
                    section,
                )
                self.assertIn("Passing characterization tests are not harness defects.", section)
                self.assertNotIn("If any test exhibits", section)
                self.assertNotIn("every test is discovered", section)

    def test_step_5_2_states_marker_convention_verbatim(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                self.assertIn(_collapse_ws(_MARKER_CONVENTION), self._step_5_2(which))

    def test_step_5_2_cites_a1_policy_wording(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                section = self._step_5_2(which)
                self.assertIn("every test in the current task's expected-RED roster, as P-004 defines it", section)
                self.assertIn("**Marker Convention** (P-004, stated verbatim", section)

    def test_step_6_harness_ready_applies_to_current_task_only_with_evidence_record(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                step = self._step(which, self._STEP_6)
                self.assertIn("`harness-ready` applies to the current task only", step)
                self.assertIn("Never label another task, the parent feature, or a shipment.", step)
                for field in (
                    "the task ID",
                    "the exact command",
                    "its native exit code",
                    "each roster test's outcome and marker",
                    "the characterization tests, listed apart from the roster",
                ):
                    self.assertIn(field, step)

    def test_completion_criteria_scope_red_to_roster(self) -> None:
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                section = _collapse_ws(_actor_h2_section(self._text(which), "Completion Criteria"))
                self.assertIn("The skill is complete only when the current task has:", section)
                self.assertNotIn("all harness tests failing with the expected marker", section)
                self.assertIn("every roster test reported as `ERROR` with its own marker", section)

    def test_template_and_installed_edited_steps_are_identical(self) -> None:
        """Steps 1, 2, 3 and 6 carry no placeholders, so the parallel hunks are identical."""
        for heading in (self._STEP_1, self._STEP_2, self._STEP_3, self._STEP_6):
            with self.subTest(step=heading):
                self.assertEqual(
                    _actor_step_section(self._text("template"), heading),
                    _actor_step_section(self._text("installed"), heading),
                )

    def test_actor_edited_sections_make_no_race_toctou_or_hardlink_claim(self) -> None:
        """IM-14: the sections A2 edits carry no race, TOCTOU or hardlink-alias wording at all."""
        for which in self._ACTOR_SOURCES:
            with self.subTest(source=which):
                text = self._text(which)
                edited = [
                    _actor_step_section(text, heading)
                    for heading in (self._STEP_1, self._STEP_2, self._STEP_3, self._STEP_6)
                ]
                edited.append(_step_5_2_section(text))
                edited.append(_actor_h2_section(text, "Inputs"))
                edited.append(_actor_h2_section(text, "Completion Criteria"))
                for section in edited:
                    self.assertEqual(_non_claim_hits(section), [])

if __name__ == "__main__":
    unittest.main()
