"""Contract test: every docs/compound/**/*.md file carries non-empty
`source` and `doc_type` frontmatter keys, per the docline base frontmatter
contract (140.001-T / 148-S).

`docs/compound/` is mapped by the active docline scope (`backlogit docs
scope`) to `doc_type: learning`. `backlogit docs lint --path docs/compound`
enforces the full required-field set (see AC7 / amendment C1 in
docs/plans/2026-08-21-docs-compound-docline-conformance-plan.md); this test
enforces the two fields the task's test-first requirement names explicitly:
`source` and `doc_type`. Scope is `*.md` only (amendment C2) -- `.gitkeep`
and any future non-markdown asset under docs/compound/ are excluded. The
scan is recursive: the compound authoring template writes new learnings to
a `{category}/` subdirectory under `{{DOCS_COMPOUND}}/`, so a non-recursive
scan would silently stop enforcing this contract for any such file.

Frontmatter values are checked for SEMANTIC emptiness via a YAML parse
(`yaml.safe_load` over the delimited block), not a raw regex match on the
scalar text -- a YAML null (`source: null` / `source: ~`) or a comment-only
value must not be treated as populated.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOUND_DIR = REPO_ROOT / "docs" / "compound"

# 146.002-T (026-DL, amendment A2): value-shape exemption allowlist.
#
# Exempts a file from the VALUE-SHAPE assertion below only -- never from the
# non-emptiness assertion above. EMPTY here because 146.001-T re-measured
# recursively at execution HEAD and found exactly one non-conforming file
# (the expected known outlier), which that task corrected. Per the plan's
# amendment A2, the allowlist is populated ONLY when 146.001-T records
# additional non-conforming files beyond the expected one; each such entry
# must be annotated with its deferring P-021 capture ID and may only shrink
# (per the precedent of 141.002-T), never grow, without new Stage
# authorization.
SOURCE_VALUE_SHAPE_EXEMPTIONS: frozenset[str] = frozenset()


def _value_shape_matches_path(source_value: object, expected_rel_posix: str) -> bool:
    """Return True iff `source_value`, with surrounding quotes stripped and
    whitespace trimmed, equals `expected_rel_posix` exactly.

    `source_value` is expected to already be YAML-parsed (quotes resolved by
    `yaml.safe_load`); the extra quote-stripping here is defense in depth for
    any raw scalar text that still carries literal quote characters.
    """
    if not isinstance(source_value, str):
        return False
    candidate = source_value.strip()
    if len(candidate) >= 2 and candidate[0] == candidate[-1] and candidate[0] in ('"', "'"):
        candidate = candidate[1:-1].strip()
    return candidate == expected_rel_posix


def _frontmatter_block(text: str):
    """Return the raw text of the frontmatter block (between the opening
    and closing ``---`` delimiters), or None if the file has no frontmatter
    block at all."""
    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        return None
    lines = normalized.split("\n")
    end_idx = None
    for i in range(1, len(lines)):
        if lines[i] == "---":
            end_idx = i
            break
    if end_idx is None:
        return None
    return "\n".join(lines[1:end_idx])


def _frontmatter_value(text: str, key: str):
    """Return the SEMANTIC value for a top-level frontmatter key, or None
    if the key is absent or its value is semantically empty.

    Parses the frontmatter block as YAML rather than matching the raw
    scalar text, so a YAML null (``source: null`` / ``source: ~``), a
    comment-only value (``source: # missing``), or an empty string all
    correctly evaluate as "not populated" instead of round-tripping the
    literal (non-empty) source text of the scalar.
    """
    block = _frontmatter_block(text)
    if block is None:
        return None
    try:
        parsed = yaml.safe_load(block)
    except yaml.YAMLError:
        return None
    if not isinstance(parsed, dict):
        return None
    value = parsed.get(key)
    if value is None:
        return None
    if isinstance(value, str) and not value.strip():
        return None
    return value


class TestDocsCompoundFrontmatterContract(unittest.TestCase):
    """Every *.md file under docs/compound/ must carry non-empty `source`
    and `doc_type` frontmatter keys (docline base frontmatter contract)."""

    def test_all_compound_docs_have_source_and_doc_type(self) -> None:
        # Recursive: the compound authoring template
        # (templates/skills/compound/SKILL.md.tmpl) writes new learnings to
        # {{DOCS_COMPOUND}}/{category}/{slug}-{date}.md, a category
        # subdirectory. A non-recursive glob would silently stop enforcing
        # this contract the moment any file lands in such a subdirectory.
        md_files = sorted(COMPOUND_DIR.rglob("*.md"))
        self.assertGreater(
            len(md_files), 0, "expected docs/compound/**/*.md files to exist"
        )

        missing_source: list[str] = []
        missing_doc_type: list[str] = []

        for path in md_files:
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(REPO_ROOT).as_posix()

            source_value = _frontmatter_value(text, "source")
            if not source_value:
                missing_source.append(rel)

            doc_type_value = _frontmatter_value(text, "doc_type")
            if not doc_type_value:
                missing_doc_type.append(rel)

        failures: list[str] = []
        if missing_source:
            failures.append(
                "missing/empty `source` in "
                + str(len(missing_source))
                + " file(s): "
                + ", ".join(missing_source)
            )
        if missing_doc_type:
            failures.append(
                "missing/empty `doc_type` in "
                + str(len(missing_doc_type))
                + " file(s): "
                + ", ".join(missing_doc_type)
            )

        self.assertFalse(failures, "\n".join(failures))

    def test_no_non_markdown_assets_are_in_scope(self) -> None:
        """Amendment C2: scope is `*.md` only. A `.gitkeep` (or any future
        non-markdown asset) under docs/compound/ must not be matched by the
        glob this test (or the migration) uses."""
        non_md = [
            p.name
            for p in COMPOUND_DIR.iterdir()
            if p.is_file() and not p.name.endswith(".md")
        ]
        matched_by_glob = {p.name for p in COMPOUND_DIR.glob("*.md")}
        for name in non_md:
            self.assertNotIn(
                name,
                matched_by_glob,
                f"{name} is non-markdown but was matched by the *.md scope",
            )

    def test_source_value_matches_own_repo_relative_path(self) -> None:
        """146.002-T (026-DL, amendments A1/A2): ratchet from non-emptiness
        to a location-derived value-shape assertion.

        `source` MUST equal the file's own repo-relative POSIX path (quotes
        stripped, whitespace trimmed). The expected path is derived from the
        file's ACTUAL location via `relative_to(...).as_posix()` -- never a
        hard-coded flat `docs/compound/` prefix -- so a legal future
        `{category}/` subdirectory (already modeled by the authoring
        template) does not become a false failure.

        This assertion is ADDITIVE: `test_all_compound_docs_have_source_and_doc_type`
        above and `test_no_non_markdown_assets_are_in_scope` above are both
        unchanged and still enforced in full.
        """
        md_files = sorted(COMPOUND_DIR.rglob("*.md"))
        self.assertGreater(
            len(md_files), 0, "expected docs/compound/**/*.md files to exist"
        )

        mismatches: list[str] = []
        for path in md_files:
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel in SOURCE_VALUE_SHAPE_EXEMPTIONS:
                continue
            text = path.read_text(encoding="utf-8")
            source_value = _frontmatter_value(text, "source")
            if not _value_shape_matches_path(source_value, rel):
                mismatches.append(f"{rel}: source={source_value!r} expected={rel!r}")

        self.assertFalse(
            mismatches,
            "source value-shape mismatch (expected self-referential "
            "repo-relative path) in:\n" + "\n".join(mismatches),
        )

    def test_source_value_shape_exemption_allowlist_is_empty(self) -> None:
        """AC2.7: the exemption allowlist MUST be EMPTY in the expected
        exactly-one-outlier case (146.001-T re-measured recursively and
        found exactly one, matching the expected outlier, which it
        corrected). Asserted explicitly so the allowlist cannot silently
        grow without this assertion catching it."""
        self.assertEqual(
            SOURCE_VALUE_SHAPE_EXEMPTIONS,
            frozenset(),
            "exemption allowlist must be empty for this shipment's measured "
            "baseline; if additional non-conforming files were recorded by "
            "146.001-T, each entry here must be annotated with its "
            "deferring P-021 capture ID",
        )

    def test_value_shape_predicate_discriminates_wrong_source_isolated_fixture(
        self,
    ) -> None:
        """AC2.2 (amendment A1): discriminating power proven with an
        ISOLATED FIXTURE only. No tracked file under docs/ is mutated (nor
        mutated-then-reverted) for this purpose -- see
        docs/compound/2026-08-15-torn-archive-log-entry-without-file-mutation-must-not-be-committed.md.
        """
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            fixture_file = tmp_root / "compound" / "2099-01-01-fixture.md"
            fixture_file.parent.mkdir(parents=True, exist_ok=True)
            fixture_file.write_text(
                "---\n"
                'title: "fixture"\n'
                "date: 2099-01-01\n"
                'source: "999-S / 000-F (fixture provenance, not a path)"\n'
                "tags: [fixture]\n"
                "doc_type: learning\n"
                "---\n\n# Fixture\n\nBody text.\n",
                encoding="utf-8",
            )

            text = fixture_file.read_text(encoding="utf-8")
            source_value = _frontmatter_value(text, "source")
            expected_rel = fixture_file.relative_to(tmp_root).as_posix()

            # The predicate itself must correctly discriminate: the wrong
            # (provenance-string) value must NOT match the fixture's own path.
            self.assertFalse(
                _value_shape_matches_path(source_value, expected_rel),
                "fixture's non-path source value must not match its own path",
            )

            # And an assertion built on the predicate must actually fail
            # (recorded failure output) when the value is wrong, proving the
            # ratchet has real discriminating power rather than being
            # green-by-construction.
            with self.assertRaises(AssertionError) as ctx:
                self.assertTrue(
                    _value_shape_matches_path(source_value, expected_rel),
                    f"expected source {source_value!r} to equal {expected_rel!r}",
                )
            self.assertIn(expected_rel, str(ctx.exception))
            self.assertIn(str(source_value), str(ctx.exception))

    def test_frontmatter_value_negative_cases_still_treated_as_missing(self) -> None:
        """AC2.3: negative-case table proving every pre-existing failure
        mode of `_frontmatter_value` is unchanged by the ratchet -- YAML
        null, `~` null, comment-only, and empty-string `source` values must
        all still evaluate as "not populated". Isolated in-memory fixtures
        only; no tracked file is touched.

        The remaining two pre-existing behaviours -- corpus-wide
        non-emptiness and the `*.md`-only scope guard -- are covered by
        `test_all_compound_docs_have_source_and_doc_type` and
        `test_no_non_markdown_assets_are_in_scope` above, both left
        unmodified by this ratchet.
        """
        cases = {
            "yaml_null": "---\nsource: null\ndoc_type: learning\n---\n\nbody\n",
            "tilde_null": "---\nsource: ~\ndoc_type: learning\n---\n\nbody\n",
            "comment_only": "---\nsource: # missing\ndoc_type: learning\n---\n\nbody\n",
            "empty_string": '---\nsource: ""\ndoc_type: learning\n---\n\nbody\n',
        }
        for label, text in cases.items():
            with self.subTest(case=label):
                self.assertIsNone(
                    _frontmatter_value(text, "source"),
                    f"{label} must still evaluate as missing/not-populated",
                )


if __name__ == "__main__":
    unittest.main()
