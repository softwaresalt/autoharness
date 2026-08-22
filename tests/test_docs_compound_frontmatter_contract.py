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

import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
COMPOUND_DIR = REPO_ROOT / "docs" / "compound"


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


if __name__ == "__main__":
    unittest.main()
