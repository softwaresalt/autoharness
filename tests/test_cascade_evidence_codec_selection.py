"""engine_semantics and close_path_selection codec tests (192.018-T, plan unit A1e).

Three table-driven scenarios (plan ``### A1e``):

1. engine-semantics round trips over decisions built by
   ``assess_cascade_engine_semantics``, every value stored verbatim
   (re-plan cycle-1 R6);
2. close-path-selection round trips over ``select_close_path`` results;
3. malformed engine records, raised by the decoder and rejected by
   ``validate_evidence_record``.
"""

from __future__ import annotations

import unittest

from autoharness.gates.cascade_evidence import (
    CascadeEvidenceError,
    close_path_selection_from_record,
    close_path_selection_to_record,
    engine_semantics_from_record,
    engine_semantics_to_record,
    validate_evidence_record,
)
from autoharness.gates.shipment_closure import (
    ClosePath,
    ClosePathDecision,
    assess_cascade_engine_semantics,
    select_close_path,
)
from test_cascade_evidence_contract import cascade_record, safe_close_record


def _assess(version: object, *, commit: object = "0123abc", surface: str = "cli"):
    return assess_cascade_engine_semantics(
        version, probe_surface=surface, invocation_surface=surface, probed_commit=commit
    )


class EngineRoundTripTests(unittest.TestCase):
    """Scenario 1: engine decisions round-trip with every value verbatim."""

    def test_engine_round_trip_table(self) -> None:
        rows = [
            ("VERIFIED 1.11.0 cli/cli", _assess("1.11.0"), "VERIFIED", [1, 11]),
            ("UNVERIFIED, no probed version", _assess(None, commit=None), "UNVERIFIED", None),
            ("UNVERIFIED 1.10.1", _assess("1.10.1"), "UNVERIFIED", [1, 10]),
            ("UNVERIFIED with an unsanitized commit", _assess("1.10.1", commit="abc token=x"), "UNVERIFIED", [1, 10]),
        ]
        for label, decision, verdict, minor_line in rows:
            with self.subTest(label):
                record = engine_semantics_to_record(decision, invocation_surface="cli")
                self.assertEqual(
                    set(record),
                    {
                        "verdict",
                        "reason",
                        "probed_version",
                        "minor_line",
                        "probed_commit",
                        "probe_surface",
                        "invocation_surface",
                    },
                )
                self.assertEqual(record["verdict"], verdict)
                self.assertEqual(record["minor_line"], minor_line)
                # Verbatim: the codec never redacts (re-plan cycle-1 R6).
                self.assertEqual(record["reason"], decision.reason)
                self.assertEqual(record["probed_version"], decision.probed_version)
                self.assertEqual(record["probed_commit"], decision.probed_commit)
                self.assertEqual(record["probe_surface"], decision.probe_surface)
                self.assertEqual(record["invocation_surface"], "cli")
                decoded, surface = engine_semantics_from_record(record)
                self.assertEqual(decoded, decision)
                self.assertEqual(surface, "cli")
                self.assertEqual(engine_semantics_to_record(decoded, invocation_surface=surface), record)


class ClosePathSelectionRoundTripTests(unittest.TestCase):
    """Scenario 2: both ``select_close_path`` results round-trip."""

    def test_close_path_round_trip_table(self) -> None:
        cascade = ClosePathDecision(close_path=ClosePath.CASCADE, reason="all inert", qualifying_feature_ids=("192-F",))
        safe = ClosePathDecision(close_path=ClosePath.SAFE_CLOSE, reason="no qualifying root")
        rows = [
            ("CASCADE x VERIFIED", select_close_path(cascade, _assess("1.11.0")), "cascade"),
            ("CASCADE x UNVERIFIED", select_close_path(cascade, _assess("1.10.1")), "safe_close"),
            ("SAFE_CLOSE x VERIFIED", select_close_path(safe, _assess("1.11.0")), "safe_close"),
        ]
        for label, selection, selected in rows:
            with self.subTest(label):
                record = close_path_selection_to_record(selection)
                self.assertEqual(record, {"selected_close_path": selected, "reason": selection[1]})
                self.assertEqual(close_path_selection_from_record(record), selection)
                self.assertEqual(close_path_selection_to_record(close_path_selection_from_record(record)), record)
        for label, bad in (
            ("unknown selected_close_path", {"selected_close_path": "cascade_all", "reason": "x"}),
            ("missing reason", {"selected_close_path": "cascade"}),
            ("non-string reason", {"selected_close_path": "safe_close", "reason": 3}),
        ):
            with self.subTest(label):
                with self.assertRaises(CascadeEvidenceError):
                    close_path_selection_from_record(bad)


class MalformedEngineTests(unittest.TestCase):
    """Scenario 3: a malformed engine record raises and rejects the record."""

    def test_malformed_engine_table(self) -> None:
        def drop(key: str):
            return lambda engine: engine.pop(key)

        def set_value(key: str, value: object):
            return lambda engine: engine.__setitem__(key, value)

        rows = [
            ("missing reason key", drop("reason")),
            ("missing invocation_surface key", drop("invocation_surface")),
            ("minor_line of length 3", set_value("minor_line", [1, 11, 0])),
            ("minor_line of type str", set_value("minor_line", "1.11")),
            ("minor_line of bools", set_value("minor_line", [True, False])),
            ("unknown verdict", set_value("verdict", "MAYBE")),
        ]
        for label, mutation in rows:
            for builder, close_path in ((safe_close_record, "safe_close"), (cascade_record, "cascade")):
                with self.subTest(label, close_path=close_path):
                    engine = engine_semantics_to_record(_assess("1.11.0"), invocation_surface="cli")
                    mutation(engine)
                    with self.assertRaises(CascadeEvidenceError):
                        engine_semantics_from_record(engine)
                    record = builder()
                    mutation(record["pre_close"]["engine_semantics"])
                    errors = validate_evidence_record(
                        record, shipment_id="198-S", feature_id="192-F", close_path=close_path
                    )
                    self.assertNotEqual(errors, [], f"{label} was accepted")


if __name__ == "__main__":
    unittest.main()
