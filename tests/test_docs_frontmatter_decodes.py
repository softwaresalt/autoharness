"""Regression guard: every docs/ frontmatter block must decode as YAML.

Protects the 136-F / 144-S fix (stash 395EBE60): a single malformed YAML
frontmatter block under ``docs/`` used to abort ``backlogit docs lint`` on
its first decode error, silently suppressing the workspace-wide docline
report for the *entire* repository -- one bad file masked conformance
checking across all of ``docs/``.

The known instance -- an unquoted plain scalar containing ``": "`` in
``docs/plans/2026-08-02-structural-navigation-benchmark-suite-plan.md``
(line 12, ``blast_radius``) -- was repaired by ``138.001-T`` (feature
``138-F``, shipment ``146-S``) as the gate-atomic baseline repair that
unblocked this shipment. ``136.002-T`` (this shipment, ``144-S``) swept the
rest of ``docs/`` for the same hazard and found no further confirmed hits.

This test is the failure-class guard called for by ``136.003-T``: it
dynamically discovers every ``docs/**/*.md`` file so a newly added doc is
covered with no test edit, and asserts that every frontmatter block present
decodes as YAML. Files with no frontmatter block are skipped, not failed --
frontmatter is not universally required.

See:
* docs/plans/2026-08-20-docline-lint-restoration-plan.md
* docs/decisions/2026-08-20-docline-lint-hard-abort-malformed-frontmatter-deliberation.md
* .backlogit/queue/136.002-T.md, .backlogit/queue/136.003-T.md

Does NOT modify or import from ``tests/test_verify_workspace.py`` or
``tests/test_spike_template_docline_frontmatter.py``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOCS_DIR = _REPO_ROOT / "docs"

# Matches a leading '---' delimiter line, captures everything up to (but not
# including) the next '---' delimiter line. Anchored to the start of the
# file so a horizontal rule appearing later in the document body can never
# be mistaken for the closing delimiter of a frontmatter block that was
# never actually opened.
_FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?\r?\n)---\r?\n", re.DOTALL)


def _discover_doc_files() -> List[Path]:
    """Dynamically enumerate every markdown file under docs/.

    Discovery is dynamic (glob-based, not a fixed list) so that a newly
    added doc is covered by this guard with no test edit required.
    """
    return sorted(_DOCS_DIR.rglob("*.md"))


def _extract_frontmatter_text(text: str) -> Optional[str]:
    """Return the raw YAML text of a leading frontmatter block, or ``None``
    if the file has no frontmatter block at all (which is not an error --
    such files are skipped by this guard)."""
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        return None
    return match.group(1)


class DocsFrontmatterDecodeTests(unittest.TestCase):
    """Assert that every docs/**/*.md frontmatter block decodes as YAML."""

    def test_docs_directory_is_discoverable(self) -> None:
        # Sanity check on the discovery mechanism itself, independent of the
        # decode assertion below -- a silently empty file list would let the
        # main test pass vacuously.
        doc_files = _discover_doc_files()
        self.assertGreater(
            len(doc_files),
            0,
            "expected to discover at least one docs/**/*.md file",
        )

    def test_every_docs_frontmatter_block_decodes(self) -> None:
        doc_files = _discover_doc_files()
        failures: List[str] = []
        checked = 0
        skipped = 0
        for path in doc_files:
            # utf-8-sig transparently strips a leading UTF-8 BOM (if
            # present) so a BOM-prefixed file is still recognized as
            # opening with '---' rather than silently mis-skipped as
            # having no frontmatter block.
            text = path.read_text(encoding="utf-8-sig")
            frontmatter_text = _extract_frontmatter_text(text)
            if frontmatter_text is None:
                # No frontmatter block present -- skipped, not failed.
                skipped += 1
                continue
            checked += 1
            try:
                yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as exc:
                rel = path.relative_to(_REPO_ROOT)
                mark = getattr(exc, "problem_mark", None)
                if mark is not None:
                    # +2 accounts for the leading '---' delimiter line
                    # consumed by the regex before the captured group
                    # begins, plus the 0-indexed -> 1-indexed conversion.
                    line = mark.line + 2
                    location = f"{rel}:{line}"
                else:
                    location = str(rel)
                failures.append(f"{location} -> {exc}")

        self.assertGreater(
            checked,
            0,
            "expected to check at least one docs/**/*.md frontmatter block "
            f"(discovered {len(doc_files)} files, all skipped as having no "
            "frontmatter)",
        )
        self.assertEqual(
            failures,
            [],
            "Malformed YAML frontmatter detected under docs/ (path:line -> "
            "error):\n" + "\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
