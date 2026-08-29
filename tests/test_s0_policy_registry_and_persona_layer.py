"""Verification and regression tests for both S0 gaps (156-S/148.008-T, U8, 336F3AB7).

Five scenarios per the plan
(``docs/plans/2026-08-27-policy-registry-and-review-persona-layer-plan.md``):

1. Policy registry content + D9-A value-level binding assertion, under the
   ``EXEMPT_POLICY_PROSE_META_TOKEN`` (D9-B) placeholder rule.
2. Persona route-resolution with a DECLARED placeholder-handling branch
   (EXPAND, the preferred branch here) for ``{{PRIMARY_LANGUAGE_LOWER}}``.
3. Named-reader (Law-2 / 031-DL) assertions -- INVERTED: asserts presence of a
   reader for every installed persona, never absence of a persona.
4. ``_resolve_policy_registry`` precedence, exercised against the real,
   installed repository state (installed-first). The temp-directory
   installed-vs-template precedence matrix itself is characterized in
   ``tests/test_policy_registry_resolution.py`` (U2) and is not duplicated here.
5. Pinned-binding (D8) conformance: the five D8 variables must appear verbatim
   in the installed artifacts; the two source templates must remain
   unmodified (D8-C); the concurrency pin must equal the live resolver value.

Plus a placeholder scan across all 14 newly installed artifacts (1 registry +
13 personas) under exactly the two named, commented exemption rules
(``EXEMPT_OUTPUT_SCHEMA_EXEMPLARS`` D8-D and ``EXEMPT_POLICY_PROSE_META_TOKEN``
D9-B) and no others.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from autoharness.verify_workspace import _language_defaults, _resolve_policy_registry

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SUBAGENTS_DIR = _REPO_ROOT / ".github" / "agents" / "subagents"
_POLICY_REGISTRY = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"

# The 13 personas installed by U4-U6 (156-S/336F3AB7).
_ALWAYS_ON_PERSONAS = [
    "constitution-reviewer",
    "scope-boundary-auditor",
    "architecture-strategist",
    "learnings-researcher",
    "correctness-reviewer",
    "maintainability-reviewer",
]
_CONDITIONAL_PERSONAS = [
    "python-reviewer",
    "security-reviewer",
    "security-lens-reviewer",
    "agent-native-parity-reviewer",
    "template-integrity-reviewer",
    "schema-cli-docs-coupling-reviewer",
    "concurrency-reviewer",
]
_ALL_13_PERSONAS = _ALWAYS_ON_PERSONAS + _CONDITIONAL_PERSONAS

# Rule 1: EXEMPT_OUTPUT_SCHEMA_EXEMPLARS (D8-D). Closed 3-token allow-list.
# Applies ONLY to the 13 persona artifacts, and only when the token sits
# inside a fenced output-schema code block (verified explicitly below, not
# merely assumed from allow-list membership).
_EXEMPT_OUTPUT_SCHEMA_EXEMPLARS = {"{{file_path}}", "{{line_number}}", "{{principle_number}}"}

# Rule 2: EXEMPT_POLICY_PROSE_META_TOKEN (D9-B). Closed 1-token allow-list.
# Applies ONLY to the policy registry (the bare ellipsis carried from
# template L359, P-013.5 fail-closed-verification prose).
_EXEMPT_POLICY_PROSE_META_TOKEN = "{{...}}"

_PLACEHOLDER_RE = re.compile(r"\{\{[^}]*\}\}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class Scenario1PolicyRegistryContentTests(unittest.TestCase):
    """Registry content + D9-A value-level binding + D9-B exemption."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.content = _read(_POLICY_REGISTRY)

    def test_registry_exists(self) -> None:
        self.assertTrue(_POLICY_REGISTRY.exists())

    def test_all_21_top_level_principles_present(self) -> None:
        for n in range(1, 22):
            token = f"P-{n:03d}"
            with self.subTest(principle=token):
                self.assertIn(token, self.content)

    def test_dark_factory_policy_contract_must_contain_tokens(self) -> None:
        must_contain = [
            "P-017",
            "Run pipeline in dark mode",
            "DARK_MODE_ACTIVE",
            "BRAINSTORM_HANDOFF_READY",
            "DARK_MODE_COMPLETE",
        ]
        for token in must_contain:
            with self.subTest(token=token):
                self.assertIn(token, self.content)

    def test_d9a_build_check_command_value_is_the_compile_check_not_the_install_command(
        self,
    ) -> None:
        """D9-A: a wrong-but-resolved value cannot be caught by a placeholder
        scan, so this asserts the rendered VALUE directly. The realized
        cycle-3 P1 defect bound {{BUILD_CHECK_COMMAND}} to the manifest's
        separate BUILD_COMMAND (`pip install -e .`) instead of the compile
        check -- this assertion is what makes that class of defect visible.
        """
        self.assertIn("python -m py_compile src/autoharness/cli.py", self.content)
        self.assertNotIn("pip install -e .", self.content)
        # The compile-check value must appear at both binding sites: the
        # harness-architect postcondition ("the harness compiles") and the
        # red-phase precondition ("exits 0 AND ... exits non-zero").
        occurrences = self.content.count("python -m py_compile src/autoharness/cli.py")
        self.assertGreaterEqual(
            occurrences,
            2,
            "expected the compile-check value at both the postcondition and "
            "red-phase precondition binding sites (template L48, L88)",
        )

    def test_zero_unresolved_placeholders_except_the_named_ellipsis_meta_token(self) -> None:
        """D9-B: EXEMPT_POLICY_PROSE_META_TOKEN is a closed 1-token allow-list
        for the bare ellipsis carried from template L359. A bare
        zero-placeholder assertion is impossible as written for this file and
        would fail permanently; every OTHER `{{...}}` match must still fail.
        """
        matches = _PLACEHOLDER_RE.findall(self.content)
        non_exempt = [m for m in matches if m != _EXEMPT_POLICY_PROSE_META_TOKEN]
        self.assertEqual(
            non_exempt,
            [],
            f"unresolved, non-exempt placeholders found in policy registry: {non_exempt}",
        )
        self.assertIn(
            _EXEMPT_POLICY_PROSE_META_TOKEN,
            matches,
            "expected the single exempt ellipsis meta-token to survive the render",
        )


class Scenario2RouteResolutionTests(unittest.TestCase):
    """Every persona path cited by an installed skill/agent under
    .github/agents/subagents/ RESOLVES, testing a PROPERTY rather than a
    hardcoded list so it will not rot as skills change.

    PLACEHOLDER-HANDLING BRANCH DECLARED: EXPAND (preferred branch, per U8's
    plan). `{{PRIMARY_LANGUAGE_LOWER}}` is substituted from
    `.autoharness/harness-manifest.yaml` `variables.PRIMARY_LANGUAGE_LOWER`
    (= "python") BEFORE resolution is attempted, so the
    `install-harness/SKILL.md` L1203 citation
    `.github/agents/subagents/{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md`
    resolves to the real installed `python-reviewer.agent.md`. This is
    strictly stronger than the EXEMPT fallback: it also proves the L1203
    render mapping itself is satisfied, not merely that the citation was
    skipped.

    Asserting raw resolution of an un-expanded placeholder path would be an
    impossible assertion and is deliberately not written here.
    """

    _CITATION_RE = re.compile(
        r"\.github/agents/subagents/([A-Za-z0-9_{}.-]+\.agent\.md)"
    )
    _PRIMARY_LANGUAGE_LOWER = "python"  # cross-checked against the manifest below

    @classmethod
    def setUpClass(cls) -> None:
        manifest_text = _read(_REPO_ROOT / ".autoharness" / "harness-manifest.yaml")
        match = re.search(r'PRIMARY_LANGUAGE_LOWER:\s*"([^"]+)"', manifest_text)
        assert match is not None, "PRIMARY_LANGUAGE_LOWER not found in harness-manifest.yaml"
        cls.primary_language_lower = match.group(1)
        # Cross-check the hardcoded expectation against the live manifest value.
        assert cls.primary_language_lower == cls._PRIMARY_LANGUAGE_LOWER

        cls.citations: set[str] = set()
        for skills_dir in ("skills", "agents"):
            search_root = _REPO_ROOT / ".github" / skills_dir
            if not search_root.exists():
                continue
            for path in search_root.rglob("*"):
                if not path.is_file():
                    continue
                if _SUBAGENTS_DIR in path.parents:
                    continue  # do not scan the personas themselves as citation sources
                text = _read(path)
                for m in cls._CITATION_RE.finditer(text):
                    cls.citations.add(m.group(1))

    def test_at_least_one_citation_was_found(self) -> None:
        self.assertGreater(
            len(self.citations), 0, "expected to find persona path citations under .github/"
        )

    def test_every_citation_resolves_after_expanding_primary_language_lower(self) -> None:
        unresolved: list[str] = []
        for filename in sorted(self.citations):
            # EXPAND branch: substitute the placeholder before resolving.
            expanded_filename = filename.replace(
                "{{PRIMARY_LANGUAGE_LOWER}}", self.primary_language_lower
            )
            resolved_path = _SUBAGENTS_DIR / expanded_filename
            if not resolved_path.exists():
                unresolved.append(f"{filename} -> {expanded_filename}")
        self.assertEqual(unresolved, [], f"citations failed to resolve: {unresolved}")

    def test_the_primary_language_lower_citation_is_present_and_expands_to_python_reviewer(
        self,
    ) -> None:
        """Guards against the citation-scan regressing to miss the literal
        placeholder token entirely (a silent regex that happens to miss it is
        not acceptable per the plan)."""
        placeholder_citations = [c for c in self.citations if "{{PRIMARY_LANGUAGE_LOWER}}" in c]
        self.assertTrue(
            placeholder_citations,
            "expected at least one {{PRIMARY_LANGUAGE_LOWER}}-templated citation "
            "(install-harness/SKILL.md L1203)",
        )
        for citation in placeholder_citations:
            expanded = citation.replace("{{PRIMARY_LANGUAGE_LOWER}}", "python")
            self.assertEqual(expanded, "python-reviewer.agent.md")
            self.assertTrue((_SUBAGENTS_DIR / expanded).exists())


class Scenario3NamedReaderLawTwoTests(unittest.TestCase):
    """Law-2 (031-DL): no artifact without a named reader.

    INVERTED from the superseded revision: this asserts PRESENCE of a reader
    for every installed persona. It MUST NOT assert absence of
    correctness-reviewer, maintainability-reviewer, or technology-reviewer --
    doing so would freeze the corrected S0's false premise into a permanent
    regression.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.corpus_text = ""
        for skills_dir in ("skills", "agents", "instructions"):
            search_root = _REPO_ROOT / ".github" / skills_dir
            if not search_root.exists():
                continue
            for path in search_root.rglob("*"):
                if not path.is_file():
                    continue
                if _SUBAGENTS_DIR in path.parents:
                    continue
                cls.corpus_text += _read(path) + "\n"

    def test_all_13_personas_are_installed(self) -> None:
        for name in _ALL_13_PERSONAS:
            with self.subTest(persona=name):
                self.assertTrue((_SUBAGENTS_DIR / f"{name}.agent.md").exists())

    def test_correctness_and_maintainability_reviewer_present(self) -> None:
        """These MUST be present so the tune-harness L462-L469 local-first
        review drift condition does not trigger against this workspace."""
        self.assertTrue((_SUBAGENTS_DIR / "correctness-reviewer.agent.md").exists())
        self.assertTrue((_SUBAGENTS_DIR / "maintainability-reviewer.agent.md").exists())

    def test_every_installed_persona_has_a_named_reader(self) -> None:
        """A named reader is EITHER an installed-path citation OR a bare
        bare-filename citation in the install/tune drift contract (RK-H: the
        original defect was a measurement-SHAPE defect -- a path-shaped grep
        cannot see a bare-filename citation -- so this checks both shapes)."""
        missing_readers: list[str] = []
        for name in _ALL_13_PERSONAS:
            filename = f"{name}.agent.md"
            installed_path_citation = f".github/agents/subagents/{filename}" in self.corpus_text
            bare_filename_citation = filename in self.corpus_text
            # python-reviewer is additionally, legitimately read via its
            # source-template basename in the install-harness render mapping.
            technology_reviewer_alias = (
                name == "python-reviewer"
                and "{{PRIMARY_LANGUAGE_LOWER}}-reviewer.agent.md" in self.corpus_text
            )
            if not (installed_path_citation or bare_filename_citation or technology_reviewer_alias):
                missing_readers.append(name)
        self.assertEqual(missing_readers, [], f"personas with no named reader: {missing_readers}")

    def test_python_reviewer_present_and_manifest_records_technology_reviewer_template(
        self,
    ) -> None:
        self.assertTrue((_SUBAGENTS_DIR / "python-reviewer.agent.md").exists())
        manifest_text = _read(_REPO_ROOT / ".autoharness" / "harness-manifest.yaml")
        match = re.search(
            r'path:\s*"\.github/agents/subagents/python-reviewer\.agent\.md"\s*\n'
            r"\s*primitive:\s*\d+\s*\n"
            r'\s*template:\s*"([^"]+)"',
            manifest_text,
        )
        self.assertIsNotNone(match, "python-reviewer.agent.md manifest entry not found")
        assert match is not None
        self.assertEqual(match.group(1), "agents/review/technology-reviewer.agent.md.tmpl")


class Scenario4ResolutionPrecedenceTests(unittest.TestCase):
    """`_resolve_policy_registry`: installed-first, exercised against the
    real, installed repository state (installed-first branch). The full
    installed-vs-template precedence matrix, including the template-fallback
    and neither-present branches, is characterized against synthetic
    temp-directory workspaces in `tests/test_policy_registry_resolution.py`
    (U2) and is intentionally not duplicated here.
    """

    def test_installed_registry_wins_in_the_real_workspace(self) -> None:
        resolved = _resolve_policy_registry(_REPO_ROOT, None)
        self.assertEqual(resolved, _POLICY_REGISTRY)
        self.assertTrue(resolved.exists())


class Scenario5PinnedBindingConformanceTests(unittest.TestCase):
    """The five D8 values must appear VERBATIM in the installed artifacts;
    the concurrency pin must equal the live `_language_defaults("python")`
    value (cross-check); both source templates must remain UNMODIFIED
    (D8-C -- proves no template was hard-coded with language-specific
    content). Scenario 5 inverts polarity vs. the placeholder scan: installed
    side has zero placeholders (mod the named rules), template side must
    STILL carry all five placeholders unresolved.
    """

    _D8B_LANGUAGE_SAFETY_CHECKS = (
        "* Prefer typed, explicit Python over dynamic shortcuts that hide failure modes.\n"
        "* Silent failures are forbidden; every failure path must be explicit and observable.\n"
        "* Prefer the standard library and existing project dependencies over new ones.\n"
        "* Lint and format failures block the change until corrected."
    )
    _D8B_LANGUAGE_IDIOM_CHECKS = (
        "* Use snake_case for modules, functions, and variables; PascalCase for classes.\n"
        "* Use docstrings for public modules, classes, and functions.\n"
        "* Prefer standard-library constructs over hand-rolled equivalents.\n"
        "* Keep each module to a single responsibility."
    )
    _D8B_LANGUAGE_ERROR_HANDLING_CHECKS = (
        "* Raise specific exceptions and handle them at clear boundaries.\n"
        "* Use explicit exceptions with contextual messages; avoid bare `except` blocks.\n"
        "* Do not swallow exceptions \u2014 a caught exception must be handled, re-raised, "
        "or logged with context.\n"
        "* Preserve the original error context when wrapping or re-raising."
    )
    _D8B_LANGUAGE_PERFORMANCE_CHECKS = (
        "* Return minimal, targeted data; avoid bulk file reads or directory scans where a "
        "structured query suffices.\n"
        "* Prefer a structured query over directory scanning when both are available.\n"
        "* Avoid repeated I/O or re-parsing inside loops; read once and reuse.\n"
        "* Flag unbounded in-memory accumulation over workspace-sized inputs."
    )
    _D8A_CONCURRENCY_PATTERNS = "asyncio, task, queue, thread, process"

    def test_python_reviewer_carries_all_four_language_checks_verbatim(self) -> None:
        content = _read(_SUBAGENTS_DIR / "python-reviewer.agent.md")
        self.assertIn(self._D8B_LANGUAGE_SAFETY_CHECKS, content)
        self.assertIn(self._D8B_LANGUAGE_IDIOM_CHECKS, content)
        self.assertIn(self._D8B_LANGUAGE_ERROR_HANDLING_CHECKS, content)
        self.assertIn(self._D8B_LANGUAGE_PERFORMANCE_CHECKS, content)

    def test_concurrency_reviewer_carries_the_pinned_concurrency_patterns_and_it_matches_the_live_resolver(
        self,
    ) -> None:
        content = _read(_SUBAGENTS_DIR / "concurrency-reviewer.agent.md")
        self.assertIn(self._D8A_CONCURRENCY_PATTERNS, content)
        live_value = _language_defaults("python")["concurrency_patterns"]
        self.assertEqual(
            live_value,
            self._D8A_CONCURRENCY_PATTERNS,
            "HARD STOP: the live _language_defaults('python') concurrency_patterns "
            "value has diverged from the D8-A pin -- this is a resolver change under "
            "the plan, not a license to improvise",
        )

    def test_technology_reviewer_source_template_unmodified_and_still_carries_all_five_placeholders(
        self,
    ) -> None:
        template_content = _read(
            _REPO_ROOT / "templates" / "agents" / "review" / "technology-reviewer.agent.md.tmpl"
        )
        for placeholder in (
            "{{PRIMARY_LANGUAGE}}",
            "{{PRIMARY_LANGUAGE_LOWER}}",
            "{{LANGUAGE_SAFETY_CHECKS}}",
            "{{LANGUAGE_IDIOM_CHECKS}}",
            "{{LANGUAGE_ERROR_HANDLING_CHECKS}}",
            "{{LANGUAGE_PERFORMANCE_CHECKS}}",
        ):
            with self.subTest(placeholder=placeholder):
                self.assertIn(placeholder, template_content)
        # D8-C: the template must NOT have been hard-coded with the bound values.
        self.assertNotIn(self._D8B_LANGUAGE_SAFETY_CHECKS, template_content)

    def test_concurrency_reviewer_source_template_unmodified_and_still_carries_the_placeholder(
        self,
    ) -> None:
        template_content = _read(
            _REPO_ROOT / "templates" / "agents" / "review" / "concurrency-reviewer.agent.md.tmpl"
        )
        self.assertIn("{{CONCURRENCY_PATTERNS}}", template_content)
        self.assertNotIn(self._D8A_CONCURRENCY_PATTERNS, template_content)


class PlaceholderScanAllFourteenInstalledArtifactsTests(unittest.TestCase):
    """Placeholder scan across ALL 14 newly installed artifacts (1 registry +
    13 personas), under exactly the two named, commented exemption rules and
    NO OTHERS. This is separate from Scenario 2's route-resolution EXPAND/
    EXEMPT branch, which operates on citations inside skill/agent PROSE, not
    on installed artifact BODIES -- the scenario-2 branch does not relax this
    scan.
    """

    def test_policy_registry_placeholder_scan(self) -> None:
        content = _read(_POLICY_REGISTRY)
        matches = _PLACEHOLDER_RE.findall(content)
        non_exempt = [m for m in matches if m != _EXEMPT_POLICY_PROSE_META_TOKEN]
        self.assertEqual(non_exempt, [])

    def test_all_13_personas_placeholder_scan_under_closed_three_token_allowlist(self) -> None:
        failures: dict[str, list[str]] = {}
        for name in _ALL_13_PERSONAS:
            content = _read(_SUBAGENTS_DIR / f"{name}.agent.md")
            matches = _PLACEHOLDER_RE.findall(content)
            non_exempt = [m for m in matches if m not in _EXEMPT_OUTPUT_SCHEMA_EXEMPLARS]
            if non_exempt:
                failures[name] = non_exempt
        self.assertEqual(failures, {}, f"non-exempt unresolved placeholders found: {failures}")

    def test_exempt_persona_tokens_are_confirmed_inside_a_fenced_json_output_schema_block(
        self,
    ) -> None:
        """Membership in the allow-list alone is not sufficient (D8-D):
        confirm each surviving exempt token is textually inside a fenced
        ```json ... ``` block, i.e. it is intended literal output-schema
        content and not merely un-substituted."""
        fence_re = re.compile(r"```json\n(.*?)```", re.DOTALL)
        for name in _ALL_13_PERSONAS:
            content = _read(_SUBAGENTS_DIR / f"{name}.agent.md")
            all_matches = set(_PLACEHOLDER_RE.findall(content))
            exempt_present = all_matches & _EXEMPT_OUTPUT_SCHEMA_EXEMPLARS
            if not exempt_present:
                continue
            fenced_blocks = fence_re.findall(content)
            fenced_text = "\n".join(fenced_blocks)
            for token in exempt_present:
                with self.subTest(persona=name, token=token):
                    self.assertIn(
                        token,
                        fenced_text,
                        f"{token} found in {name}.agent.md but not inside a fenced "
                        "json output-schema block",
                    )


class ManifestChecksumRoundTripTests(unittest.TestCase):
    """Every manifest checksum for the 14 newly installed artifacts
    recomputed from the installed file matches (INV-5)."""

    def test_checksums_round_trip(self) -> None:
        import hashlib

        import yaml

        manifest_path = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"
        with manifest_path.open(encoding="utf-8") as fh:
            manifest = yaml.safe_load(fh)

        new_paths = [".github/policies/workflow-policies.md"] + [
            f".github/agents/subagents/{name}.agent.md" for name in _ALL_13_PERSONAS
        ]
        by_path = {entry["path"]: entry for entry in manifest["artifacts"]}
        mismatches: list[str] = []
        for path in new_paths:
            entry = by_path.get(path)
            self.assertIsNotNone(entry, f"manifest entry missing for {path}")
            assert entry is not None
            file_bytes = (_REPO_ROOT / path).read_bytes()
            self.assertNotIn(b"\r\n", file_bytes, f"{path} is not LF-only")
            actual = hashlib.sha256(file_bytes).hexdigest()
            if actual != entry["checksum"]:
                mismatches.append(f"{path}: manifest={entry['checksum']} actual={actual}")
        self.assertEqual(mismatches, [])


if __name__ == "__main__":
    unittest.main()
