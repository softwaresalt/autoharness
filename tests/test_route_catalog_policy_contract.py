"""Structural tests for 215-S B10 (208.012-T): the P-013.5 'Route catalog and site
bindings' amendment, its fail-closed verification items, and the Amendment Log row.

Plan: docs/plans/2026-10-11-model-routing-catalog-bindings-plan.md (### B10).
Deliberation: docs/decisions/2026-10-11-model-routing-v2-deliberation.md (040-DL D10, D12).
"""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST = _ROOT / ".autoharness" / "harness-manifest.yaml"
_POLICY_TEMPLATE = "templates/policies/workflow-policies.md.tmpl"
_POLICY_MIRROR = ".github/policies/workflow-policies.md"
_P0135_HEADING = "### P-013.5 — Invocation-Time Model-Routing Enforcement"
_CLAUSE_LEAD = "**Route catalog and site bindings**"
_FAIL_CLOSED_LEAD = "**Fail-closed verification**"
_ROW_MARKER = "208.012-T"
_LAST_ROW_BEFORE_B10 = (1, 35, 0)
# Core Rule 3: the amendment names no vendor, model, or token count.
_FORBIDDEN_VENDOR_TERMS = ("anthropic", "openai", "claude", "gpt", "gemini", "grok", "token")


def _read(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def _section(text: str, heading: str) -> str:
    """Body under ``heading`` up to the next heading of the same or higher level."""
    lines = text.split("\n")
    level = len(heading) - len(heading.lstrip("#"))
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break
    if start is None:
        return ""
    body: list[str] = []
    for line in lines[start:]:
        match = re.match(r"^(#{1,6}) ", line)
        if match and len(match.group(1)) <= level:
            break
        body.append(line)
    return "\n".join(body)


def _paragraph(section: str, lead: str) -> str:
    for paragraph in section.split("\n\n"):
        if paragraph.strip().startswith(lead):
            return re.sub(r"\s+", " ", paragraph.strip())
    return ""


def _version_rows(text: str) -> list[tuple[tuple[int, ...], str]]:
    rows = []
    for match in re.finditer(r"^\| (\d+\.\d+\.\d+) +\| (.*)$", text, flags=re.MULTILINE):
        rows.append((tuple(int(part) for part in match.group(1).split(".")), match.group(0)))
    return rows


def _sha256_lf(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


class RouteCatalogClauseTests(unittest.TestCase):
    """The P-013.5 clause exists, identically, in the template and the installed mirror."""

    def setUp(self) -> None:
        self.texts = {rel: _read(rel) for rel in (_POLICY_TEMPLATE, _POLICY_MIRROR)}

    def _clause(self, rel: str) -> str:
        clause = _paragraph(_section(self.texts[rel], _P0135_HEADING), _CLAUSE_LEAD)
        self.assertTrue(clause, f"{rel}: P-013.5 {_CLAUSE_LEAD} paragraph is missing")
        return clause

    def test_clause_markers(self) -> None:
        for rel in self.texts:
            with self.subTest(path=rel):
                clause = self._clause(rel)
                for token in (
                    "tier delta",
                    "not a parallel taxonomy",
                    "`config.model_routing.routes`",
                    "`config.model_routing.bindings`",
                    "`agent:<id>`",
                    "never mixed",
                    "`config.overrides`",
                    "render-time layer",
                    "outside the resolver",
                    "composed with explicit overrides",
                    "rendered default",
                    "anchors, aliases, and merge keys",
                    "`model_routing`",
                    "unknown sites fail verification",
                    "`autoharness routing resolve`",
                    "normative executable definition",
                    "inherit",
                    "not sites",
                ):
                    self.assertIn(token, clause)

    def test_unbound_and_bound_branches_stated(self) -> None:
        for rel in self.texts:
            with self.subTest(path=rel):
                clause = self._clause(rel)
                unbound = re.search(r"\*\*Unbound\*\*[^.]*template default tier", clause)
                bound = re.search(r"\*\*Bound\*\*[^.]*binding's route", clause)
                self.assertIsNotNone(unbound, "unbound branch (template default tier) is not stated")
                self.assertIsNotNone(bound, "bound branch (binding's route) is not stated")
                self.assertIn("never consults the site default tier, not even as a field-level fallback", clause)

    def test_unresolved_default_rejection(self) -> None:
        for rel in self.texts:
            with self.subTest(path=rel):
                clause = self._clause(rel)
                self.assertIn("`ROUTING_BINDING_UNRESOLVED_SITE`", clause)
                self.assertIn("template default tier cannot be established", clause)
                self.assertIn("rejected", clause)

    def test_clause_has_no_vendor_terms_or_placeholders(self) -> None:
        for rel in self.texts:
            with self.subTest(path=rel):
                clause = self._clause(rel)
                lowered = clause.lower()
                for term in _FORBIDDEN_VENDOR_TERMS:
                    self.assertNotIn(term, lowered)
                self.assertEqual(re.findall(r"\{\{[^}]*\}\}", clause), [])

    def test_clause_precedes_fail_closed_verification(self) -> None:
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                section = _section(text, _P0135_HEADING)
                self.assertLess(section.index(_CLAUSE_LEAD), section.index(_FAIL_CLOSED_LEAD))

    def test_verification_list_carries_new_fail_closed_items(self) -> None:
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                paragraph = _paragraph(_section(text, _P0135_HEADING), _FAIL_CLOSED_LEAD)
                self.assertTrue(paragraph)
                for token in (
                    "`routing_catalog_integrity`",
                    "`routing_unknown_keys`",
                    "`routing_anchor_alias_free`",
                    "`routing_inert_keys`",
                    "`subagent_route_drift`",
                    "`ROUTING_BINDING_UNRESOLVED_SITE`",
                    "`ROUTING_SITE_DEFAULT_UNRESOLVED`",
                    "`SUBAGENT_ROUTE_DRIFT`",
                    "`ROUTING_UNKNOWN_SITE`",
                ):
                    self.assertIn(token, paragraph)
                # The original (a)-(d) items stay; the new items continue the lettering.
                for letter in ("(a)", "(b)", "(c)", "(d)", "(e)", "(f)", "(g)"):
                    self.assertIn(letter, paragraph)

    def test_section_has_no_new_placeholders(self) -> None:
        """Only the intentional `{{...}}` prose meta-token (EXEMPT_POLICY_PROSE_META_TOKEN) may appear."""
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                tokens = set(re.findall(r"\{\{[^}]*\}\}", _section(text, _P0135_HEADING)))
                self.assertLessEqual(tokens, {"{{...}}"})

    def test_p013_7_is_not_claimed(self) -> None:
        for rel, text in self.texts.items():
            with self.subTest(path=rel):
                self.assertNotRegex(text, r"^#{2,4} P-013\.7\b")

    def test_p0135_section_identical_in_template_and_mirror(self) -> None:
        self.assertEqual(
            _section(self.texts[_POLICY_TEMPLATE], _P0135_HEADING),
            _section(self.texts[_POLICY_MIRROR], _P0135_HEADING),
        )


class RouteCatalogAmendmentRowTests(unittest.TestCase):
    """The Amendment Log row is the next minor version after the latest earlier row."""

    def setUp(self) -> None:
        self.texts = {rel: _read(rel) for rel in (_POLICY_TEMPLATE, _POLICY_MIRROR)}

    def _row_index(self, rel: str) -> int:
        rows = _version_rows(self.texts[rel])
        indices = [i for i, (_, line) in enumerate(rows) if _ROW_MARKER in line]
        self.assertEqual(len(indices), 1, f"{rel}: expected exactly one {_ROW_MARKER} row")
        return indices[0]

    def test_row_present_and_highest_when_added(self) -> None:
        for rel in self.texts:
            with self.subTest(path=rel):
                rows = _version_rows(self.texts[rel])
                index = self._row_index(rel)
                version, _ = rows[index]
                earlier = [v for v, _ in rows[:index]]
                self.assertGreater(version, max(earlier))
                self.assertGreater(version, _LAST_ROW_BEFORE_B10)
                # Next minor: same major, minor + 1 over the latest earlier row, patch 0.
                latest = max(earlier)
                self.assertEqual(version, (latest[0], latest[1] + 1, 0))
                self.assertEqual([v for v, _ in rows], sorted(set(v for v, _ in rows)))

    def test_row_content(self) -> None:
        for rel in self.texts:
            with self.subTest(path=rel):
                row = _version_rows(self.texts[rel])[self._row_index(rel)][1]
                for token in ("Amended P-013.5", "215-S", "208-F", "route catalog", "site bindings", "`ROUTING_BINDING_UNRESOLVED_SITE`"):
                    self.assertIn(token, row)
                self.assertNotIn("P-013.7", row)

    def test_row_date_is_placeholder_in_template_and_utc_date_in_mirror(self) -> None:
        template_row = _version_rows(self.texts[_POLICY_TEMPLATE])[self._row_index(_POLICY_TEMPLATE)][1]
        mirror_row = _version_rows(self.texts[_POLICY_MIRROR])[self._row_index(_POLICY_MIRROR)][1]
        self.assertEqual(template_row.split("|")[2].strip(), "{{DATE}}")
        self.assertRegex(mirror_row.split("|")[2].strip(), r"^\d{4}-\d{2}-\d{2}$")

    def test_row_versions_match_between_template_and_mirror(self) -> None:
        self.assertEqual(
            _version_rows(self.texts[_POLICY_TEMPLATE])[self._row_index(_POLICY_TEMPLATE)][0],
            _version_rows(self.texts[_POLICY_MIRROR])[self._row_index(_POLICY_MIRROR)][0],
        )


class RouteCatalogManifestTests(unittest.TestCase):
    def test_mirror_manifest_checksum_matches_lf_normalized_blob(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        by_path = {item.get("path"): item for item in manifest.get("artifacts") or []}
        self.assertIn(_POLICY_MIRROR, by_path)
        entry = by_path[_POLICY_MIRROR]
        self.assertEqual(entry.get("checksum"), _sha256_lf(_ROOT / _POLICY_MIRROR))
        self.assertEqual(entry.get("template"), "policies/workflow-policies.md.tmpl")
        self.assertIn(_ROW_MARKER, entry.get("note", ""))


if __name__ == "__main__":
    unittest.main()
