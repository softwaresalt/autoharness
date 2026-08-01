"""Tests for the ToolTelemetryEvent runtime model (U1, 084.001-T)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from autoharness.telemetry.epoch import WorkSizingSnapshot
from autoharness.telemetry.tool_event import (
    SCHEMA_VERSION,
    ToolTelemetryEvent,
    ToolTelemetryEventError,
)

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas" / "tool-telemetry-event.schema.json"


def _minimal_kwargs(**overrides):
    kwargs = dict(
        tool_surface="cli",
        tool_name="pytest",
        operation="run_tests",
        status="success",
        sensitivity="internal",
        backlog_item_id="084.001-T",
    )
    kwargs.update(overrides)
    return kwargs


class ToolTelemetryEventRequiredFieldsTests(unittest.TestCase):
    def test_minimal_construction_defaults_event_id_and_timestamp(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs())
        self.assertTrue(event.event_id)
        self.assertEqual(len(event.event_id), 32)
        self.assertTrue(event.timestamp)
        self.assertEqual(event.schema_version, SCHEMA_VERSION)
        self.assertEqual(event.retry_count, 0)
        self.assertFalse(event.degraded_mode)
        self.assertFalse(event.redaction_applied)

    def test_from_mapping_requires_core_fields(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent.from_mapping({"tool_name": "grep"})

    def test_from_mapping_rejects_unknown_field(self) -> None:
        payload = _minimal_kwargs()
        payload["not_a_real_field"] = True
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent.from_mapping(payload)

    def test_schema_version_is_pinned_const(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent.from_mapping({**_minimal_kwargs(), "schema_version": "9.9.9"})


class ToolTelemetryEventCorrelationTests(unittest.TestCase):
    def test_requires_epoch_id_or_backlog_item_id(self) -> None:
        kwargs = _minimal_kwargs()
        kwargs.pop("backlog_item_id")
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**kwargs)

    def test_epoch_id_correlation_alone_is_sufficient(self) -> None:
        kwargs = _minimal_kwargs()
        kwargs.pop("backlog_item_id")
        event = ToolTelemetryEvent(epoch_id="a" * 32, **kwargs)
        self.assertEqual(event.epoch_id, "a" * 32)

    def test_epoch_id_must_be_canonical_32_hex(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(epoch_id="not-hex-32", **_minimal_kwargs())

    def test_from_mapping_normalizes_hyphenated_epoch_id_to_hex32(self) -> None:
        hyphenated = "11111111-1111-4111-8111-111111111111"
        event = ToolTelemetryEvent.from_mapping({**_minimal_kwargs(), "epoch_id": hyphenated})
        self.assertEqual(event.epoch_id, "11111111111141118111111111111111")

    def test_empty_backlog_item_id_does_not_satisfy_correlation(self) -> None:
        kwargs = _minimal_kwargs()
        kwargs["backlog_item_id"] = ""
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**kwargs)


class ToolTelemetryEventEnumTests(unittest.TestCase):
    def test_rejects_invalid_tool_surface(self) -> None:
        kwargs = _minimal_kwargs(tool_surface="invalid")
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**kwargs)

    def test_rejects_invalid_status(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**_minimal_kwargs(status="not-a-status"))

    def test_rejects_invalid_sensitivity(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**_minimal_kwargs(sensitivity="not-a-level"))

    def test_route_kind_accepts_well_known_and_x_extension(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs(route_kind="structural_graph"))
        self.assertEqual(event.route_kind, "structural_graph")
        event2 = ToolTelemetryEvent(**_minimal_kwargs(route_kind="x-custom-pack"))
        self.assertEqual(event2.route_kind, "x-custom-pack")

    def test_route_kind_rejects_unknown_non_extension_value(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**_minimal_kwargs(route_kind="bogus"))

    def test_freshness_state_accepts_well_known_and_x_extension(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs(freshness_state="stale"))
        self.assertEqual(event.freshness_state, "stale")

    def test_secret_scan_status_rejects_invalid_value(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**_minimal_kwargs(secret_scan_status="bogus"))


class ToolTelemetryEventNonnegQuantityTests(unittest.TestCase):
    def test_rejects_negative_retry_count(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**_minimal_kwargs(retry_count=-1))

    def test_rejects_negative_input_tokens(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(
                **_minimal_kwargs(
                    input_tokens=-5,
                    metric_sources={"input_tokens": "host_reported"},
                    metric_quality={"input_tokens": "observed"},
                )
            )

    def test_from_mapping_rejects_bool_as_int(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent.from_mapping({**_minimal_kwargs(), "retry_count": True})

    def test_null_metric_is_treated_as_unavailable_not_observed_zero(self) -> None:
        event = ToolTelemetryEvent.from_mapping({**_minimal_kwargs(), "input_tokens": None})
        self.assertIsNone(event.input_tokens)
        self.assertEqual(event.missing_provenance(), ())


class ToolTelemetryEventProvenanceTests(unittest.TestCase):
    def test_populated_metric_without_provenance_fails_closed(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(**_minimal_kwargs(input_tokens=100))

    def test_populated_metric_with_only_source_fails_closed(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(
                **_minimal_kwargs(input_tokens=100, metric_sources={"input_tokens": "host_reported"})
            )

    def test_populated_metric_with_complete_provenance_succeeds(self) -> None:
        event = ToolTelemetryEvent(
            **_minimal_kwargs(
                input_tokens=100,
                metric_sources={"input_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed"},
            )
        )
        self.assertTrue(event.has_complete_provenance)

    def test_zero_valued_metric_requires_no_provenance(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs(input_tokens=0))
        self.assertTrue(event.has_complete_provenance)

    def test_metric_sources_rejects_invalid_vocabulary(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(
                **_minimal_kwargs(
                    input_tokens=1,
                    metric_sources={"input_tokens": "made_up"},
                    metric_quality={"input_tokens": "observed"},
                )
            )

    def test_metric_quality_rejects_invalid_vocabulary(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent(
                **_minimal_kwargs(
                    input_tokens=1,
                    metric_sources={"input_tokens": "host_reported"},
                    metric_quality={"input_tokens": "made_up"},
                )
            )


class ToolTelemetryEventExpectationSemanticsTests(unittest.TestCase):
    def test_expect_skipped_is_expectation_only(self) -> None:
        event = ToolTelemetryEvent(
            **_minimal_kwargs(operation="expect", status="skipped", expected_tool="engram.map_code")
        )
        self.assertTrue(event.is_expectation_only)

    def test_real_invocation_is_not_expectation_only(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs())
        self.assertFalse(event.is_expectation_only)


class ToolTelemetryEventRoundTripTests(unittest.TestCase):
    def test_round_trip_to_dict_and_from_mapping(self) -> None:
        event = ToolTelemetryEvent(
            **_minimal_kwargs(
                epoch_id="b" * 32,
                input_tokens=42,
                metric_sources={"input_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed"},
                artifact_refs=("docs/telemetry-reference.md",),
                work_sizing_snapshot=WorkSizingSnapshot(task_size_label="M"),
            )
        )
        rebuilt = ToolTelemetryEvent.from_mapping(event.to_dict())
        self.assertEqual(rebuilt.to_dict(), event.to_dict())
        self.assertEqual(rebuilt.event_id, event.event_id)
        self.assertEqual(rebuilt.work_sizing_snapshot.task_size_label, "M")

    def test_to_dict_contains_every_required_schema_key(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs())
        record = event.to_dict()
        for key in (
            "schema_version",
            "event_id",
            "timestamp",
            "tool_surface",
            "server_name",
            "tool_name",
            "operation",
            "status",
            "retry_count",
            "degraded_mode",
            "sensitivity",
            "redaction_applied",
            "metric_sources",
            "metric_quality",
            "artifact_refs",
        ):
            self.assertIn(key, record)

    def test_default_event_id_is_unique_per_instance(self) -> None:
        first = ToolTelemetryEvent(**_minimal_kwargs())
        second = ToolTelemetryEvent(**_minimal_kwargs())
        self.assertNotEqual(first.event_id, second.event_id)


class ToolTelemetryEventTimestampTests(unittest.TestCase):
    def test_rejects_timezone_naive_timestamp(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent.from_mapping({**_minimal_kwargs(), "timestamp": "2026-07-31T10:00:00"})

    def test_accepts_z_suffixed_timestamp(self) -> None:
        event = ToolTelemetryEvent.from_mapping(
            {**_minimal_kwargs(), "timestamp": "2026-07-31T10:00:00Z"}
        )
        self.assertEqual(event.timestamp, "2026-07-31T10:00:00Z")

    def test_rejects_malformed_timestamp(self) -> None:
        with self.assertRaises(ToolTelemetryEventError):
            ToolTelemetryEvent.from_mapping({**_minimal_kwargs(), "timestamp": "not-a-date"})


class ToolTelemetryEventSchemaConformanceTests(unittest.TestCase):
    """Cross-check ``to_dict()`` output against the ratified JSON schema."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            import jsonschema  # noqa: F401
        except ImportError:  # pragma: no cover - environment dependent
            raise unittest.SkipTest("jsonschema package not installed")
        with _SCHEMA_PATH.open(encoding="utf-8") as handle:
            cls.schema = json.load(handle)

    def _validate(self, payload: dict) -> None:
        import jsonschema

        jsonschema.validate(payload, self.schema)

    def test_minimal_event_validates_against_schema(self) -> None:
        event = ToolTelemetryEvent(**_minimal_kwargs())
        self._validate(event.to_dict())

    def test_event_with_populated_metrics_validates_against_schema(self) -> None:
        event = ToolTelemetryEvent(
            **_minimal_kwargs(
                epoch_id="c" * 32,
                input_tokens=10,
                output_tokens=5,
                metric_sources={"input_tokens": "host_reported", "output_tokens": "host_reported"},
                metric_quality={"input_tokens": "observed", "output_tokens": "observed"},
                work_sizing_snapshot=WorkSizingSnapshot(task_size_label="S"),
            )
        )
        self._validate(event.to_dict())

    def test_expectation_only_event_validates_against_schema(self) -> None:
        event = ToolTelemetryEvent(
            tool_surface="mcp",
            tool_name="map_code",
            operation="expect",
            status="skipped",
            sensitivity="internal",
            backlog_item_id="084.001-T",
            expected_tool="map_code",
        )
        self._validate(event.to_dict())


if __name__ == "__main__":
    unittest.main()
