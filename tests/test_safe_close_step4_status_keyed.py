"""Guard: Safe-Close step 4 classifies manifest items by declared status (D16452D7).

Section-scoped over both the template and the dogfood mirror of the
shipment-reconcile skill. Location (queue/ or archive/) is a label only.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_COPIES = {
    "template": _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl",
    "mirror": _ROOT / ".github" / "skills" / "shipment-reconcile" / "SKILL.md",
}


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\r\n", "\n"))


def _step4(text: str) -> str:
    start = text.index("4. **Archive each manifest item individually**")
    end = text.index("5. **Verify-after-each invariant**", start)
    return _flat(text[start:end])


class SafeCloseStep4StatusKeyedTests(unittest.TestCase):
    def test_step4_is_status_keyed_in_both_copies(self) -> None:
        for name, path in _COPIES.items():
            with self.subTest(copy=name):
                body = _step4(path.read_text(encoding="utf-8"))
                self.assertIn("declared `status`", body)
                self.assertIn("location label only", body)
                self.assertIn("declared `status` is `archived`", body)
                self.assertIn("`pre-archived` and **skip**", body)
                self.assertIn("any other declared `status`, in either location", body)
                self.assertIn("explicit single-artifact archive", body)
                self.assertIn("HALT for operator review and never skip", body)
                self.assertIn("`missing`", body)
                self.assertIn("`RECONCILE_FAIL`", body)
                self.assertNotIn("is already in", body)

    def test_deferred_gap_wording_removed_in_both_copies(self) -> None:
        for name, path in _COPIES.items():
            with self.subTest(copy=name):
                text = _flat(path.read_text(encoding="utf-8"))
                self.assertNotIn("pre-existing and deferred to a durable active stash", text)
                self.assertNotIn("still keys its `pre-archived` skip on location", text)
                self.assertNotIn("still use `pre-archived` as a location label", text)

    def test_scenario_matrix_row_in_both_copies(self) -> None:
        for name, path in _COPIES.items():
            with self.subTest(copy=name):
                text = _flat(path.read_text(encoding="utf-8"))
                self.assertIn("archive/`-resident record declaring `done`", text)
    def test_p002_7_reciprocal_cross_references(self) -> None:
        for name, path in _COPIES.items():
            with self.subTest(copy=name):
                text = _flat(path.read_text(encoding="utf-8"))
                self.assertIn("that contract is P-002.7 (Post-Claim Member-Status Contract)", text)
        policies = (
            _ROOT / "templates" / "policies" / "workflow-policies.md.tmpl",
            _ROOT / ".github" / "policies" / "workflow-policies.md",
        )
        for path in policies:
            with self.subTest(policy=path.name):
                text = _flat(path.read_text(encoding="utf-8"))
                self.assertIn(
                    "skill's `Member-Class Status Contract` is the pre-close classification contract",
                    text,
                )


if __name__ == "__main__":
    unittest.main()
