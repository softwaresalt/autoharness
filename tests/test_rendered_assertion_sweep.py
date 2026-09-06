"""Table-driven assertion sweep over rendered templates (151.004-T).

Task 3b of the SHIP-1 v1.5.0 guardrail-contract-restoration shipment
(`docs/plans/2026-08-31-ship1-v1_5_0-guardrail-contract-restoration-plan.md`).

Every entry in `PACK_ASSERTIONS`, `FOUNDATION_ASSERTIONS` and
`DARK_FACTORY_ASSERTIONS` is asserted against the **rendered source of truth**
resolved by the 3a harness (`tests/_assertion_render.py`), with **no exemption
list**. This is the test that would have blocked the v1.5.0 release: the
existing real-artifact test reads this repository's installed dogfood copies,
which legitimately lag their templates, so it cannot detect template-side drift.

Binding H3 -- red before green
------------------------------
Observed at the pre-fix tree state (branch
`feat/159-s-ship-1-v1-5-0-shipped-guardrail-contract-restoration`, before
`151.001-T` and `151.002-T` landed), this sweep failed on **exactly two**
assertions and nothing else::

    closure_source_artifact_cleanup
        source: templates/skills/operational-closure/SKILL.md.tmpl
        missing: ['Source artifact cleanup', 'source_stash_id',
                  'source_deliberation_id']

    ship_release_closure_sequence
        source: templates/agents/_ship.agent.md.tmpl
        missing: ['another top-level release unit may not begin yet']

    total failures: 2 of 71

Charter limit (plan review finding 4): this module **detects**, it does not
remediate. Any *additional* failing assertion it reveals is a P-021 deferred
scope expansion capture for a later run and MUST NOT be fixed here.

Freeze-scope (SHIP-1 plan H7): `tests/` only.

Cost (151.006-T deliverable 4): variable derivation 0.095 s, full corpus render
1.77 s, and only 29 distinct sources are actually touched. The budget is not
exceeded, so the sweep is expressed as one subtest per assertion rather than
collapsed to a single opaque case.
"""

from __future__ import annotations

import unittest

from _assertion_render import (
    VARIANT_BACKLOGIT,
    corpus_for,
    iter_assertions,
)

#: The two shipped v1.5.0 defects this shipment fixes. Recorded here as the
#: red-before-green evidence anchor (H3), NOT as an exemption list -- the sweep
#: below asserts every assertion unconditionally and this tuple is only used by
#: the provenance test to keep the recorded evidence honest once both fixes have
#: landed.
KNOWN_PRE_FIX_FAILURES = (
    "closure_source_artifact_cleanup",
    "ship_release_closure_sequence",
)


class RenderedAssertionSweepTests(unittest.TestCase):
    """Every table-driven assertion must hold against rendered output."""

    @classmethod
    def setUpClass(cls) -> None:
        # Rendered once per class and cached by the harness (finding 5).
        cls.corpus = corpus_for(VARIANT_BACKLOGIT)
        cls.assertions = iter_assertions()
        cls.results = [cls.corpus.evaluate(assertion) for assertion in cls.assertions]

    def test_every_table_driven_assertion_holds_against_rendered_source(self) -> None:
        for assertion, result in zip(self.assertions, self.results):
            with self.subTest(assertion=assertion.key, table=assertion.table):
                self.assertTrue(
                    result["ok"],
                    "assertion {key} is unsatisfiable by its source of truth "
                    "{source} ({kind}): missing={missing} "
                    "order_violations={order}".format(
                        key=assertion.key,
                        source=result["source"],
                        kind=result["kind"],
                        missing=result["missing"],
                        order=result["order_violations"],
                    ),
                )

    def test_sweep_covers_every_assertion_with_no_exemption_list(self) -> None:
        from autoharness.verify_workspace import (
            DARK_FACTORY_ASSERTIONS,
            FOUNDATION_ASSERTIONS,
            PACK_ASSERTIONS,
        )

        expected_keys = {entry["key"] for entries in PACK_ASSERTIONS.values() for entry in entries}
        expected_keys |= {entry["key"] for entry in FOUNDATION_ASSERTIONS}
        expected_keys |= {entry["key"] for entry in DARK_FACTORY_ASSERTIONS}
        swept_keys = {result["key"] for result in self.results}
        self.assertEqual(
            expected_keys,
            swept_keys,
            "the sweep must cover every live table entry; a divergence means an "
            "assertion was silently skipped",
        )

    def test_known_pre_fix_defects_are_now_green(self) -> None:
        """H3 provenance: the two assertions observed red pre-fix are green.

        This is not an exemption -- both keys are also swept unconditionally by
        `test_every_table_driven_assertion_holds_against_rendered_source`. It
        exists so the recorded red-before-green evidence in this module's
        docstring stays verifiable rather than becoming folklore.
        """
        by_key = {result["key"]: result for result in self.results}
        for key in KNOWN_PRE_FIX_FAILURES:
            with self.subTest(assertion=key):
                self.assertIn(key, by_key, f"{key} disappeared from the verifier tables")
                self.assertTrue(
                    by_key[key]["ok"],
                    f"{key} was observed RED pre-fix and must now be GREEN against "
                    f"its rendered source {by_key[key]['source']}: "
                    f"missing={by_key[key]['missing']}",
                )

    def test_sweep_reads_templates_not_dogfood_mirrors_where_one_exists(self) -> None:
        """Guard against the sweep degrading back into reading installed copies."""
        template_backed = [
            result for result in self.results if result["kind"] == "template"
        ]
        self.assertGreaterEqual(
            len(template_backed),
            len(self.results) - 13,
            "at most the 13 engine-artifact assertions may read an installed "
            "file; anything more means source-of-truth resolution regressed",
        )


if __name__ == "__main__":
    unittest.main()
