"""Producer/consumer non-drift guard for the closure-evidence contract (167.009-T, plan U9).

Makes prose/code drift a test failure instead of a future incident: decision
D1 ("no second definition anywhere") machine-enforced. Every scan root and the
registered set come from the contract module itself -- this module hard-codes
no scan root and no exclusion list. Narrative ``docs/`` prose and test code
are outside the scan by construction; ``docs/closure/`` is never touched.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from autoharness.gates import closure_contract
from autoharness.gates.closure_contract import (
    CANONICAL_CLOSURE_FILENAME_TEMPLATE,
    CANONICAL_CLOSURE_PATTERN_DOC,
    CLOSURE_DIR_PLACEHOLDER,
    CLOSURE_PREDICATE_REQUIREMENT_DOC,
    CONSUMER_SITES,
    CONTRACT_DEFINITION_SITE,
    DEFAULT_CLOSURE_DIR,
    RUNTIME_SCAN_ROOTS,
    _render_pattern_doc,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]

# Consumer sites, looked up by role so the pairs below are read from the
# registry rather than restated. Each pair is (template, installed mirror).
_PRODUCER_SKILL_PAIR = tuple(site for site in CONSUMER_SITES if "operational-closure/" in site)
_SHIP_AGENT_PAIR = tuple(site for site in CONSUMER_SITES if site.endswith(("_ship.agent.md", "_ship.agent.md.tmpl")))

# A closure-filename pattern definition: any literal closure filename, escaped
# closure-filename regex (``closure.md`` / ``closure\.md`` / ``closure\\.md``),
# or the canonical ``post-merge-closure`` stem. This is a literal-restatement
# heuristic: an identifier assembled at runtime from fragments is out of reach
# of a text scan and is instead prevented by review against the contract.
_CLOSURE_FILENAME_DEFINITION = re.compile(r"closure(?:\\+)?\.md|post-merge-closure", re.IGNORECASE)

_OUTPUT_BULLET = re.compile(r"^\* Closure artifact at `(?P<pattern>[^`]+)`\s*$", re.MULTILINE)
_SHIP_CONTRACT_MARKER = "**Closure-evidence contract**"
_STEP_3A_HEADING = "### Step 3a: Validate the Closure Artifact with the Closure-Evidence Gate"
# Every canonical-shaped path a documentation site restates, and every gate
# invocation it documents; each must equal the contract-derived form.
_CANONICAL_PATH_MENTION = re.compile(r"[^\s`\"']*post-merge-closure\.md")
# Flags are parsed independently so a reordered invocation is still checked.
_GATE_INVOCATION = re.compile(r"autoharness gate closure-evidence(?P<args>[^`\n]*)")


def _flag(args: str, flag: str) -> str | None:
    match = re.search(rf"(?:^|\s){re.escape(flag)}\s+(\S+)", args)
    return match.group(1) if match else None
_DOC_SITES = tuple(site for site in CONSUMER_SITES if not site.endswith(".py"))


def _read(relative: str) -> str:
    return (_REPO_ROOT / relative).read_text(encoding="utf-8")


def _rendered(text: str) -> str:
    """Apply the single permitted template -> installed substitution."""
    return text.replace(CLOSURE_DIR_PLACEHOLDER, DEFAULT_CLOSURE_DIR.as_posix())


def _expected_pattern(site: str) -> str:
    return CANONICAL_CLOSURE_PATTERN_DOC if site.endswith(".tmpl") else _rendered(CANONICAL_CLOSURE_PATTERN_DOC)


def _section(text: str, heading: str, *, site: str = "") -> str:
    """Return ``heading`` and its body up to the next heading of equal or higher level."""
    lines = text.splitlines()
    if heading not in lines:
        raise AssertionError(f"{site}: heading {heading!r} not found (was it renamed?)")
    level = len(heading) - len(heading.lstrip("#"))
    start = lines.index(heading)
    end = len(lines)
    in_fence = False
    for index in range(start + 1, len(lines)):
        if lines[index].lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        match = None if in_fence else re.match(r"^(#+) ", lines[index])
        if match and len(match.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def _template_and_installed(pair: tuple[str, ...]) -> tuple[str, str]:
    template = next(site for site in pair if site.endswith(".tmpl"))
    installed = next(site for site in pair if not site.endswith(".tmpl"))
    return template, installed


class ClosureContractNonDriftTests(unittest.TestCase):
    def test_documented_pattern_equals_code_constant(self) -> None:
        self.assertEqual(len(_PRODUCER_SKILL_PAIR), 2, _PRODUCER_SKILL_PAIR)
        template, installed = _template_and_installed(_PRODUCER_SKILL_PAIR)
        expected = {
            template: CANONICAL_CLOSURE_PATTERN_DOC,
            installed: _rendered(CANONICAL_CLOSURE_PATTERN_DOC),
        }
        for site, pattern in expected.items():
            with self.subTest(site=site):
                output = _section(_read(site), "## Output", site=site)
                bullets = _OUTPUT_BULLET.findall(output)
                self.assertEqual(bullets, [pattern])
                # The producer quotes the consumer's acceptance requirement from the
                # contract verbatim, so a predicate restatement cannot drift.
                self.assertIn(CLOSURE_PREDICATE_REQUIREMENT_DOC, output)
        # Every canonical-shaped path and every documented gate invocation in
        # every documentation consumer site is the contract-derived form.
        for site in _DOC_SITES:
            text = _read(site)
            with self.subTest(site=site, check="canonical path mentions"):
                mentions = _CANONICAL_PATH_MENTION.findall(text)
                self.assertTrue(mentions, f"{site}: no canonical closure path documented")
                self.assertEqual(set(mentions), {_expected_pattern(site)})
            with self.subTest(site=site, check="gate invocations"):
                invocations = [
                    {"path": _flag(match.group("args"), "--path"), "shipment": _flag(match.group("args"), "--shipment")}
                    for match in _GATE_INVOCATION.finditer(text)
                    if "--" in match.group("args")
                ]
                self.assertTrue(invocations, f"{site}: no closure-evidence gate invocation documented")
                for invocation in invocations:
                    self.assertEqual(invocation["path"], _expected_pattern(site))
                    self.assertEqual(invocation["shipment"], "{shipment_id}")

    def test_template_and_installed_mirror_parity(self) -> None:
        # Producer skill: the contract-bearing sections agree modulo the placeholder.
        template, installed = _template_and_installed(_PRODUCER_SKILL_PAIR)
        template_text, installed_text = _read(template), _read(installed)
        self.assertNotIn(CLOSURE_DIR_PLACEHOLDER, installed_text)
        for heading in ("## Output", _STEP_3A_HEADING):
            with self.subTest(site="producer skill", section=heading):
                self.assertEqual(
                    _rendered(_section(template_text, heading, site=template)),
                    _section(installed_text, heading, site=installed),
                )
        # Ship agent: the closure-evidence contract paragraph agrees modulo the
        # placeholder, and names the canonical pattern and both gate keys.
        self.assertEqual(len(_SHIP_AGENT_PAIR), 2, _SHIP_AGENT_PAIR)
        template, installed = _template_and_installed(_SHIP_AGENT_PAIR)
        paragraphs = {}
        for site in (template, installed):
            matches = [line.strip() for line in _read(site).splitlines() if _SHIP_CONTRACT_MARKER in line]
            self.assertEqual(len(matches), 1, f"{site}: expected one closure-evidence contract paragraph")
            paragraphs[site] = matches[0]
        self.assertEqual(_rendered(paragraphs[template]), paragraphs[installed])
        self.assertIn(CANONICAL_CLOSURE_PATTERN_DOC, paragraphs[template])
        for key in ("`closure_status`", "`compaction_status`", "autoharness gate closure-evidence"):
            self.assertIn(key, paragraphs[template])

    def test_consumer_site_registry_is_complete_for_runtime_surfaces(self) -> None:
        registered = (CONTRACT_DEFINITION_SITE,) + CONSUMER_SITES
        for site in registered:
            with self.subTest(registered=site):
                self.assertTrue((_REPO_ROOT / site).is_file(), f"registered site missing: {site}")
                self.assertTrue(
                    any(site.startswith(root) for root in RUNTIME_SCAN_ROOTS),
                    f"registered site {site} lies outside every RUNTIME_SCAN_ROOTS entry",
                )
        self.assertEqual(
            (_REPO_ROOT / CONTRACT_DEFINITION_SITE).resolve(), Path(closure_contract.__file__).resolve()
        )
        registered_set = set(registered)
        offenders: list[str] = []
        for root in RUNTIME_SCAN_ROOTS:
            base = _REPO_ROOT / root
            self.assertTrue(base.is_dir(), f"scan root missing: {root}")
            for path in sorted(base.rglob("*")):
                if not path.is_file():
                    continue
                relative = path.relative_to(_REPO_ROOT).as_posix()
                if relative in registered_set:
                    continue
                data = path.read_bytes()
                if b"\x00" in data:  # binary artifact (e.g. bytecode), not a source surface
                    continue
                text = data.decode("utf-8", errors="replace")
                if _CLOSURE_FILENAME_DEFINITION.search(text):
                    offenders.append(relative)
        self.assertEqual(
            offenders,
            [],
            "closure-filename pattern defined outside the contract's registered set "
            "(register the site in closure_contract.CONSUMER_SITES or derive from the contract)",
        )

    def test_pattern_doc_is_derived_from_the_machine_template(self) -> None:
        self.assertEqual(
            CANONICAL_CLOSURE_PATTERN_DOC, _render_pattern_doc(CANONICAL_CLOSURE_FILENAME_TEMPLATE)
        )
        self.assertTrue(CANONICAL_CLOSURE_PATTERN_DOC.endswith("/" + CANONICAL_CLOSURE_FILENAME_TEMPLATE))


if __name__ == "__main__":
    unittest.main()
