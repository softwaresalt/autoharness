"""154.003-T (SHIP-4, 7628C291): bounded one-hop review-family verifier.

Ships the H-b MANDATORY ACCEPTANCE test: ONE test in the existing tests/
suite performing STATIC TEXT INSPECTION of every `.github/skills/*/SKILL.md`
and `templates/skills/*/SKILL.md.tmpl` file, asserting exactly three
properties:

1. UNDECLARED SPAWNING — any skill whose text spawns a subagent without a
   conforming `## Subagent Depth Constraint` section is a FAILURE.
2. INVALID CONSTRAINT FORM — a constraint section missing either the depth
   bound or the leaf-executor clause is a FAILURE.
3. INVALID DEPTH — a declared depth other than 1 is a FAILURE.

This is BOUNDED BY CONSTRUCTION (H-c): no runtime interception, no
spawn-time enforcement, no new CLI surface, no new package, no agent-runtime
hook — one test performing static text inspection of SKILL.md files only.

RESIDUAL LIMITATION (H-d, mirrored verbatim in the amended instruction
text): this detector recognizes a skill as "spawning a subagent" only when
its own text uses the word "spawn(s)" in a positive (non-negated) sentence
naming a subagent — the same vocabulary the two current qualifying members
(`review`, `plan-review`) already use. A skill that spawns at runtime
without that spawn appearing declared in its SKILL.md, or that describes
subagent dispatch using different vocabulary, is not detected by this
document-layer check.

Demonstrates RED before GREEN (H7) via the `SubagentSpawnDetectorUnitTests`
class below, which proves the detector actually fails (goes RED) on three
synthetic non-conforming fixtures — one per property — before the
`RealSkillCorpusConformance` class asserts the real, live repository corpus
is fully conforming (GREEN).
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_INSTALLED_SKILLS_GLOB = ".github/skills/*/SKILL.md"
_TEMPLATE_SKILLS_GLOB = "templates/skills/*/SKILL.md.tmpl"

_CONSTRAINT_HEADING = "## Subagent Depth Constraint"

# A positive (non-negated) declaration that THIS skill spawns a subagent.
# Anchored on the literal vocabulary the two current qualifying members use
# ("spawn(s) ... subagent(s)") per the H-d residual limitation: this is a
# document-layer detector, not a semantic one, and deliberately does not
# match synonyms like "dispatch".
_POSITIVE_SPAWN_SENTENCE = re.compile(
    r"(?<![A-Za-z])spawns?\b[^.\n]{0,80}?\bsubagents?\b", re.IGNORECASE
)
_NEGATION_TOKENS = re.compile(
    r"\b(no|not|never|must not|n't|without)\b", re.IGNORECASE
)

_MAX_DEPTH_DECLARATION = re.compile(
    r"maximum(?:\s+spawn)?\s+depth\s*:?(?P<middle>[^.\n]{0,60}?)\b(?P<value>\d+)\s*hops?\b",
    re.IGNORECASE,
)
# A negation appearing between "maximum depth" and the numeric value means the
# sentence does NOT affirmatively declare that value as the bound (e.g.
# "Maximum depth is not 1 hop" must not be read as declaring depth 1).
_DEPTH_DECLARATION_NEGATION = re.compile(
    r"\b(not|never|no|isn't|is not|n't)\b", re.IGNORECASE
)
_LEAF_EXECUTOR_MUST_NOT_SPAWN = re.compile(
    r"leaf executors?[^.\n]{0,60}?must not spawn", re.IGNORECASE
)
# Clause boundaries used to scope negation detection to the clause that
# actually governs the spawn verb, rather than the whole sentence prefix
# (Copilot review, PR #446, thread PRRT_kwDORzpWpM6hulPM): a negation in an
# earlier, unrelated clause of a compound sentence (e.g. "This skill never
# edits files; it spawns reviewer subagents.") must not suppress a real,
# later, un-negated spawn declaration.
_CLAUSE_SPLIT = re.compile(r";|,\s+(?:but|and|or|however|although|while)\b", re.IGNORECASE)


def _sentences(text: str) -> list[str]:
    # Simple sentence splitter: adequate for the short declarative prose
    # used in SKILL.md capability descriptions.
    return re.split(r"(?<=[.!?])\s+", text)


def declares_subagent_spawning(text: str) -> bool:
    """Return True iff `text` contains a positive (non-negated) declaration
    that the skill spawns a subagent."""
    for sentence in _sentences(text):
        if not _POSITIVE_SPAWN_SENTENCE.search(sentence):
            continue
        spawn_match = re.search(r"spawns?\b", sentence, re.IGNORECASE)
        if spawn_match is None:
            continue
        # Scope the negation check to the CLAUSE governing the spawn verb,
        # not the entire sentence prefix (e.g. "No subagent spawning",
        # "MUST NOT spawn its own subagents").
        clause_boundaries = [
            m.end() for m in _CLAUSE_SPLIT.finditer(sentence) if m.end() <= spawn_match.start()
        ]
        clause_start = max(clause_boundaries) if clause_boundaries else 0
        clause_prefix = sentence[clause_start : spawn_match.start()]
        if _NEGATION_TOKENS.search(clause_prefix):
            continue
        return True
    return False


def find_constraint_section(text: str) -> str | None:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == _CONSTRAINT_HEADING:
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break
    return "\n".join(lines[start:end])


def evaluate_skill_text(text: str) -> list[str]:
    """Evaluate one SKILL.md's text against the three required properties.

    Returns a list of failure reasons; an empty list means the skill is
    conforming (either it does not spawn subagents at all, or it declares a
    valid one-hop constraint section).
    """
    failures: list[str] = []
    spawns = declares_subagent_spawning(text)
    section = find_constraint_section(text)

    if not spawns:
        # A skill that does not spawn subagents has nothing to satisfy here,
        # regardless of whether it happens to carry a same-named section
        # (e.g. a 0-hop leaf-executor declaration under the same heading).
        return failures

    if section is None:
        failures.append("UNDECLARED_SPAWNING: skill text spawns a subagent but declares no "
                         f"'{_CONSTRAINT_HEADING}' section")
        return failures

    # Anchor the depth check to an actual "maximum [spawn] depth: N hop(s)"
    # declaration rather than scanning the whole section for any bare "1 hop"
    # substring — an unrelated mention of "1 hop" elsewhere in the section
    # (e.g. describing a call chain, not declaring the bound) must not count.
    # A negation between "maximum depth" and the number (e.g. "Maximum depth
    # is not 1 hop") is not an affirmative declaration of that value and is
    # excluded rather than counted.
    declared_depths = {
        int(m.group("value"))
        for m in _MAX_DEPTH_DECLARATION.finditer(section)
        if not _DEPTH_DECLARATION_NEGATION.search(m.group("middle"))
    }
    has_leaf_clause = bool(_LEAF_EXECUTOR_MUST_NOT_SPAWN.search(section))
    has_depth_one = declared_depths == {1}

    if not declared_depths or not has_leaf_clause:
        failures.append(
            "INVALID_CONSTRAINT_FORM: constraint section is missing the depth bound and/or "
            "the leaf-executor must-not-spawn-further clause"
        )
    elif not has_depth_one:
        # A depth declaration exists but is not exactly {1} — either a single
        # non-1 value, or multiple conflicting declared values.
        failures.append("INVALID_DEPTH: constraint section declares a depth other than 1 hop")

    return failures


class SubagentSpawnDetectorUnitTests(unittest.TestCase):
    """Proves the detector can fail (RED) on each of the three properties
    using synthetic, deliberately non-conforming fixtures, before the real
    corpus is asserted conforming (GREEN) below."""

    def test_conforming_fixture_passes(self) -> None:
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents.\n\n"
            "## Subagent Depth Constraint\n\n"
            "This skill spawns reviewer subagents. Those subagents are leaf executors "
            "and MUST NOT spawn their own subagents. Maximum depth: skill -> persona "
            "subagent (1 hop).\n\n"
            "## Next Section\n"
        )
        self.assertEqual(evaluate_skill_text(text), [])

    def test_non_spawning_fixture_passes(self) -> None:
        text = (
            "# Some Skill\n\n"
            "This is a leaf executor. No subagent spawning. Maximum depth: 0.\n"
        )
        self.assertEqual(evaluate_skill_text(text), [])

    def test_red_case_1_undeclared_spawning(self) -> None:
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents to gather findings.\n\n"
            "## Next Section\n"
        )
        failures = evaluate_skill_text(text)
        self.assertTrue(any(f.startswith("UNDECLARED_SPAWNING") for f in failures), failures)

    def test_red_case_2_invalid_constraint_form_missing_leaf_clause(self) -> None:
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents.\n\n"
            "## Subagent Depth Constraint\n\n"
            "Maximum depth: 1 hop.\n\n"
            "## Next Section\n"
        )
        failures = evaluate_skill_text(text)
        self.assertTrue(any(f.startswith("INVALID_CONSTRAINT_FORM") for f in failures), failures)

    def test_red_case_2_invalid_constraint_form_missing_depth_bound(self) -> None:
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents.\n\n"
            "## Subagent Depth Constraint\n\n"
            "Those subagents are leaf executors and MUST NOT spawn their own subagents.\n\n"
            "## Next Section\n"
        )
        failures = evaluate_skill_text(text)
        self.assertTrue(any(f.startswith("INVALID_CONSTRAINT_FORM") for f in failures), failures)

    def test_red_case_3_invalid_depth(self) -> None:
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents.\n\n"
            "## Subagent Depth Constraint\n\n"
            "Those subagents are leaf executors and MUST NOT spawn their own subagents. "
            "Maximum depth: 2 hops.\n\n"
            "## Next Section\n"
        )
        failures = evaluate_skill_text(text)
        self.assertTrue(any(f.startswith("INVALID_DEPTH") for f in failures), failures)

    def test_red_case_unrelated_1_hop_mention_does_not_satisfy_the_depth_bound(self) -> None:
        # Copilot review (PR #446, thread PRRT_kwDORzpWpM6htobW): a bare "1 hop"
        # substring anywhere in the section must not satisfy the depth
        # requirement unless it appears as part of an actual "maximum [spawn]
        # depth: N hop(s)" declaration. This fixture's only depth-shaped
        # sentence declares an UNLIMITED bound while a separate, unrelated
        # sentence happens to mention "1 hop" describing a call chain.
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents.\n\n"
            "## Subagent Depth Constraint\n\n"
            "Those subagents are leaf executors and MUST NOT spawn their own subagents. "
            "The first reviewer is 1 hop away; maximum depth is unlimited.\n\n"
            "## Next Section\n"
        )
        failures = evaluate_skill_text(text)
        self.assertTrue(
            any(f.startswith("INVALID_CONSTRAINT_FORM") for f in failures),
            f"an unanchored '1 hop' substring incorrectly satisfied the depth bound: {failures}",
        )

    def test_red_case_negated_depth_declaration_does_not_satisfy_the_depth_bound(self) -> None:
        # Copilot review (PR #446, thread PRRT_kwDORzpWpM6htwgy, also flagged
        # at line 85 of this file): "Maximum depth is not 1 hop" must not be
        # read as an affirmative declaration of depth 1 merely because the
        # digit 1 appears between "maximum depth" and "hop".
        text = (
            "# Some Skill\n\n"
            "This skill spawns reviewer subagents.\n\n"
            "## Subagent Depth Constraint\n\n"
            "Those subagents are leaf executors and MUST NOT spawn their own subagents. "
            "Maximum depth is not 1 hop.\n\n"
            "## Next Section\n"
        )
        failures = evaluate_skill_text(text)
        self.assertTrue(
            any(f.startswith("INVALID_CONSTRAINT_FORM") for f in failures),
            f"a negated depth declaration incorrectly satisfied the depth bound: {failures}",
        )

    def test_negated_spawn_language_is_not_a_positive_declaration(self) -> None:
        self.assertFalse(declares_subagent_spawning("No subagent spawning (leaf executor)."))
        self.assertFalse(
            declares_subagent_spawning("This skill is a leaf executor. It MUST NOT spawn its own subagents.")
        )

    def test_hyphenated_sub_agent_example_text_is_not_a_positive_declaration(self) -> None:
        # templates/skills/harness-doctor/SKILL.md.tmpl documents a scanning
        # example using the hyphenated spelling "sub-agent", describing a
        # pattern harness-doctor looks FOR in other files, not a declaration
        # that harness-doctor itself spawns.
        self.assertFalse(
            declares_subagent_spawning(
                "Agent references (e.g., `spawns sub-agent: foo.agent.md`)"
            )
        )

    def test_unrelated_earlier_negation_does_not_suppress_a_real_spawn_declaration(self) -> None:
        # Copilot review (PR #446, thread PRRT_kwDORzpWpM6hulPM): a negation
        # governing an unrelated, earlier clause in a compound sentence must
        # not suppress detection of a real, later, un-negated spawn
        # declaration in the same sentence.
        self.assertTrue(
            declares_subagent_spawning(
                "This skill never edits files; it spawns reviewer subagents."
            )
        )


class RealSkillCorpusConformance(unittest.TestCase):
    """GREEN: every real, live SKILL.md in this repository conforms."""

    def _skill_files(self) -> list[Path]:
        installed = sorted(_REPO_ROOT.glob(_INSTALLED_SKILLS_GLOB))
        templated = sorted(_REPO_ROOT.glob(_TEMPLATE_SKILLS_GLOB))
        files = installed + templated
        self.assertGreater(len(files), 0, "no SKILL.md files found — glob patterns may be stale")
        return files

    def test_every_skill_file_conforms(self) -> None:
        offenders: dict[str, list[str]] = {}
        for path in self._skill_files():
            text = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
            failures = evaluate_skill_text(text)
            if failures:
                offenders[str(path.relative_to(_REPO_ROOT))] = failures
        self.assertEqual(offenders, {}, f"non-conforming skill files found: {offenders}")

    def test_known_qualifying_members_declare_a_conforming_section(self) -> None:
        # review and plan-review are the two current EXAMPLES (not the
        # definition) of the exception; confirm they still qualify.
        for relative in (
            ".github/skills/review/SKILL.md",
            ".github/skills/plan-review/SKILL.md",
            "templates/skills/review/SKILL.md.tmpl",
            "templates/skills/plan-review/SKILL.md.tmpl",
        ):
            path = _REPO_ROOT / relative
            with self.subTest(skill=relative):
                self.assertTrue(path.is_file())
                text = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
                self.assertTrue(declares_subagent_spawning(text), f"{relative} no longer declares spawning")
                section = find_constraint_section(text)
                self.assertIsNotNone(section, f"{relative} missing '{_CONSTRAINT_HEADING}' section")
                self.assertEqual(evaluate_skill_text(text), [])


class InstructionArtifactExceptionContract(unittest.TestCase):
    """Confirms the amended-artifact set exactly matches 154.003-T's binding
    scope: role-enforcement template + mirror amended, harness-architecture
    mirror amended directly with NO template counterpart authored."""

    def test_role_enforcement_template_and_mirror_agree(self) -> None:
        template = _REPO_ROOT / "templates" / "instructions" / "role-enforcement.instructions.md.tmpl"
        dogfood = _REPO_ROOT / ".github" / "instructions" / "role-enforcement.instructions.md"
        self.assertTrue(template.is_file())
        self.assertTrue(dogfood.is_file())
        template_text = template.read_bytes().replace(b"\r\n", b"\n")
        dogfood_text = dogfood.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(template_text, dogfood_text)
        self.assertIn(b"Bounded One-Hop Review-Family Exception", template_text)

    def test_no_template_counterpart_exists_for_harness_architecture(self) -> None:
        forbidden = _REPO_ROOT / "templates" / "instructions" / "harness-architecture.instructions.md.tmpl"
        self.assertFalse(
            forbidden.exists(),
            "templates/instructions/harness-architecture.instructions.md.tmpl must not exist "
            "(154.003-T binding: this artifact is amended directly, with no template counterpart)",
        )

    def test_harness_architecture_carries_the_exception_and_residual_limitation(self) -> None:
        dogfood = _REPO_ROOT / ".github" / "instructions" / "harness-architecture.instructions.md"
        text = dogfood.read_text(encoding="utf-8")
        self.assertIn("Bounded One-Hop Review-Family Exception", text)
        self.assertIn(
            "Enforcement is at the DOCUMENT LAYER ONLY", text
        )

    def test_residual_limitation_text_is_verbatim_identical_across_both_artifacts(self) -> None:
        role_enforcement = (
            _REPO_ROOT / ".github" / "instructions" / "role-enforcement.instructions.md"
        ).read_text(encoding="utf-8")
        harness_architecture = (
            _REPO_ROOT / ".github" / "instructions" / "harness-architecture.instructions.md"
        ).read_text(encoding="utf-8")
        marker = (
            "RESIDUAL LIMITATION: this exception's verifier checks DECLARATIONS IN SKILL TEXT; "
            "an agent that spawns a subagent at runtime without that spawn appearing declared "
            "in its `SKILL.md` is NOT detected by this check. Enforcement is at the DOCUMENT "
            "LAYER ONLY — this is a static text-conformance property, not a runtime "
            "spawn-time interception."
        )
        self.assertIn(marker, role_enforcement)
        self.assertIn(marker, harness_architecture)


if __name__ == "__main__":
    unittest.main()
