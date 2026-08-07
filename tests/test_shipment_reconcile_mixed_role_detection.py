"""Shipment-reconcile `mode: detect-mixed-role` contract tests (112-F / 118-S).

Read-only DETECTION + REPORT-ONLY diagnostics + operator-remediation guidance
for the queued-with-active-work / mixed-role "silently-dropped-claim"
signature (936C68F3 part 2, re-scoped per 013-DL Addendum G / Copilot PR #304
finding 1). This mode NEVER mutates, NEVER calls a shipment claim operation,
and needs no lock, because nothing is ever written.

Distinct from the existing `record-consistent` / `record-queued-with-active-
work` / `record-blocked-with-active-work` / `record-blocked-with-done-work`
record-scope classification (105-F/109-S, covered by
`test_shipment_reconcile_record_status.py`): that check compares a single
shipment record's own status against the *aggregate* active/done state of its
manifest tasks. This mode instead classifies *each* manifest task
individually by per-task ROLE (`live-queued` / `live-active` /
`archived-completed(done)` in either valid archive representation) and flags
per-item ANOMALIES (`duplicate` / `conflicting` / `missing` /
`malformed-provenance` / `any-other-archived-status` / `orphan` /
`out-of-role` / `torn-partial`), used ONLY to DESCRIBE the inconsistency in a
report-only diagnostic -- NEVER to gate a mutation.

`templates/skills/shipment-reconcile/SKILL.md.tmpl` is a template-only skill
with no installed `.github/skills/shipment-reconcile` dogfood mirror, so this
contract is verified against the template alone (same convention as the
existing record-status classification test module).
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl"

_ROLES = (
    "live-queued",
    "live-active",
    "archived-completed(done)",
)

_ANOMALIES = (
    "duplicate",
    "conflicting",
    "missing",
    "malformed-provenance",
    "any-other-archived-status",
    "orphan",
    "out-of-role",
    "torn-partial",
)

_OUTCOMES = ("DETECTED", "REPORTED", "DEGRADED")

_MODE_ANCHOR = "detect-mixed-role"
_CLASSIFICATION_ANCHOR = "Mixed-Role Detection Classification"
_PROTOCOL_ANCHOR = "Mixed-Role Detection Mode (`mode: detect-mixed-role`"
_REMEDIATION_ANCHOR = "#### Operator-Remediation Guidance"
_AUDIT_ANCHOR = "#### Mixed-Role Detection Audit + Telemetry"


def _content() -> str:
    return _TEMPLATE.read_text(encoding="utf-8")


class MixedRoleDetectionModePresenceTests(unittest.TestCase):
    """(a) Detection fires: the mode, its inputs, and the mixed-role
    silently-dropped-claim signature (live-active/live-queued AND
    archived-completed present simultaneously under a queued record) are all
    documented and wired into the Inputs table and When-to-Use section."""

    def test_mode_declared_in_inputs_table(self) -> None:
        content = _content()
        self.assertIn(_MODE_ANCHOR, content)
        inputs_idx = content.index("## Inputs")
        output_idx = content.index("## Output")
        inputs_region = content[inputs_idx:output_idx]
        self.assertIn(_MODE_ANCHOR, inputs_region)
        self.assertIn("shipment_id", inputs_region)

    def test_when_to_use_documents_operator_invoked_read_only(self) -> None:
        content = _content()
        when_idx = content.index("## When to Use")
        inputs_idx = content.index("## Inputs")
        region = content[when_idx:inputs_idx]
        self.assertIn(_MODE_ANCHOR, region)
        self.assertIn("READ-ONLY", region)
        self.assertIn("operator-invoked", region.lower())
        self.assertIn("936C68F3", region)
        self.assertIn("013-DL", region)

    def test_mixed_role_signature_defined(self) -> None:
        content = _content()
        self.assertIn("Mixed-role signature", content)
        sig_idx = content.index("Mixed-role signature")
        region = content[sig_idx : sig_idx + 900]
        self.assertIn("live-active", region)
        self.assertIn("archived-completed(done)", region)
        self.assertIn("silently-dropped-claim", region)

    def test_classification_section_present_and_distinct_from_record_scope(self) -> None:
        content = _content()
        self.assertIn(_CLASSIFICATION_ANCHOR, content)
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        region = content[class_idx : class_idx + 1200]
        self.assertIn("separate", region.lower())
        self.assertIn("record-scope classification", region)


class MixedRoleDetectionRolePredicateTests(unittest.TestCase):
    """Per-task ALLOWED ROLE predicate: unique, non-conflicting record for
    exactly one of {live-queued, live-active, archived-completed(done)},
    with the completed role admitting EITHER valid archive representation."""

    def test_all_three_roles_present(self) -> None:
        content = _content()
        for role in _ROLES:
            with self.subTest(role=role):
                self.assertIn(role, content)

    def test_completed_role_admits_both_archive_representations(self) -> None:
        content = _content()
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        region = content[class_idx : class_idx + 3000]
        self.assertIn("TERMINAL RELOCATION", region)
        self.assertIn("EXPLICIT ARCHIVAL", region)
        self.assertIn("archived_status", region)
        self.assertIn("archived_from", region)
        # Terminal relocation must NOT require provenance.
        self.assertIn("NOT required", region)

    def test_live_queued_and_live_active_require_no_archive_copy(self) -> None:
        content = _content()
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        region = content[class_idx : class_idx + 2500]
        occurrences = [m.start() for m in re.finditer(r"NO archive record", region)]
        self.assertGreaterEqual(len(occurrences), 2)


class MixedRoleDetectionAnomalyTests(unittest.TestCase):
    """(b) Detection correctly DESCRIBES per-item anomalies."""

    def test_all_eight_anomalies_present(self) -> None:
        content = _content()
        for anomaly in _ANOMALIES:
            with self.subTest(anomaly=anomaly):
                self.assertIn(anomaly, content)

    def test_anomalies_fail_closed_report_and_halt(self) -> None:
        content = _content()
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        report_idx = content.index("Mixed-role signature", class_idx)
        region = content[class_idx:report_idx]
        self.assertIn("fail closed", region.lower())
        self.assertIn("REPORT and HALT", region)

    def test_conflicting_excludes_live_done_in_queue(self) -> None:
        content = _content()
        self.assertIn("live `status: {{STATUS_DONE}}` record is found in the QUEUE", content)

    def test_malformed_provenance_distinguishes_legitimate_done_no_provenance(self) -> None:
        content = _content()
        idx = content.index("malformed-provenance")
        # The anomaly table row must clarify that a bare `status: done` archive
        # record legitimately carries no provenance and is NOT malformed.
        region = content[idx : idx + 400]
        self.assertIn("legitimately carries no provenance", region)
        self.assertIn("NOT malformed", region)


class MixedRoleDetectionMalformedLegacyTests(unittest.TestCase):
    """(d) A legacy/malformed `blocked` shipment record is DESCRIBED as
    malformed-legacy with NO fabricated transition."""

    def test_malformed_legacy_shipment_record_documented(self) -> None:
        content = _content()
        self.assertIn("malformed-legacy", content)
        idx = content.index("Malformed-legacy shipment record")
        region = content[idx : idx + 700]
        self.assertIn("NO", region)
        self.assertIn("blocked", region)
        self.assertIn("never fabricate", region.lower())

    def test_protocol_handles_malformed_legacy_candidate_without_halting_whole_scan(self) -> None:
        content = _content()
        protocol_idx = content.index(_PROTOCOL_ANCHOR)
        region = content[protocol_idx : protocol_idx + 2500]
        self.assertIn("malformed-legacy", region)
        self.assertIn("never fabricate a transition", region.lower())

    def test_no_blocked_to_queued_or_active_to_queued_fabrication_anywhere(self) -> None:
        content = _content()
        self.assertIn("never\n  fabricates a `blocked`→`{{STATUS_QUEUED}}` or", content)
        self.assertIn("`{{STATUS_ACTIVE}}`→`{{STATUS_QUEUED}}` transition", content)


class MixedRoleDetectionOutcomeTests(unittest.TestCase):
    """(e) DEGRADED (backlogit unreachable) => REPORTS the degraded condition
    and HALTS. Outcomes are exactly DETECTED / REPORTED / DEGRADED."""

    def test_all_three_outcomes_present(self) -> None:
        content = _content()
        for outcome in _OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, content)

    def test_no_repair_succeeded_refused_or_two_active_outcome(self) -> None:
        content = _content()
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        outcomes_idx = content.index("Detection outcomes", class_idx)
        region = content[outcomes_idx : outcomes_idx + 700]
        self.assertIn("NO**", region)
        self.assertIn("succeeded", region)
        self.assertIn("repaired", region)
        self.assertIn("refused", region)
        self.assertIn("two-active", region)

    def test_degraded_reports_and_halts(self) -> None:
        content = _content()
        protocol_idx = content.index(_PROTOCOL_ANCHOR)
        region = content[protocol_idx : protocol_idx + 3500]
        self.assertIn("DEGRADED", region)
        degraded_idx = region.index("backlogit is unreachable")
        tail = region[degraded_idx : degraded_idx + 300]
        self.assertIn("HALT", tail)
        self.assertIn("Do not guess", tail)


class MixedRoleDetectionNoMutationTests(unittest.TestCase):
    """(c) NO test asserts mutation; the skill NEVER calls a claim/status-
    write operation on the detection path, and needs no lock because nothing
    is written. This also serves as the required explicit
    never-mutates/never-claims regression assertion for 112.002-T AC 3."""

    def test_mode_never_calls_claim_shipment(self) -> None:
        content = _content()
        protocol_idx = content.index(_PROTOCOL_ANCHOR)
        # Bound the search to the detect-mixed-role protocol + its
        # sub-sections (remediation guidance + audit/telemetry), ending
        # before the next top-level "### Lock-Conflict Scenario" section.
        lock_conflict_idx = content.index("### Lock-Conflict Scenario", protocol_idx)
        region = content[protocol_idx:lock_conflict_idx]
        self.assertNotIn("{{OP_CLAIM_SHIPMENT_MCP}}(", region)
        self.assertIn("NO mutation of any kind", region)

    def test_mode_requires_no_lock(self) -> None:
        content = _content()
        protocol_idx = content.index(_PROTOCOL_ANCHOR)
        region = content[protocol_idx : protocol_idx + 400]
        self.assertIn("No lock is acquired", region)

    def test_behavioral_constraints_declares_strictly_read_only(self) -> None:
        content = _content()
        constraints_idx = content.index("## Behavioral Constraints")
        protocol_idx = content.index("## Required Protocol")
        region = content[constraints_idx:protocol_idx]
        self.assertIn(_MODE_ANCHOR, region)
        self.assertIn("strictly READ-ONLY", region)
        self.assertIn("NEVER mutates", region)
        self.assertIn("NEVER calls", region)

    def test_quality_criteria_reiterates_no_mutation_no_claim(self) -> None:
        content = _content()
        quality_idx = content.index("## Quality Criteria")
        related_idx = content.index("## Related Artifacts")
        region = content[quality_idx:related_idx]
        self.assertIn(_MODE_ANCHOR, region)
        self.assertIn("NEVER mutates", region)
        self.assertIn("NEVER calls", region)
        self.assertIn("NO", region)

    def test_no_confirm_flag_anywhere_for_this_mode(self) -> None:
        """There must be no `--confirm` mutation-gate flag for detect-mixed-
        role -- nothing is mutated, so no confirmation gate is needed."""
        content = _content()
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        region = content[class_idx : class_idx + 1000]
        self.assertIn("no `--confirm` flag", region)
        self.assertNotIn("--confirm", content.replace("no `--confirm` flag", ""))


class MixedRoleDetectionAuditTelemetryTests(unittest.TestCase):
    """112.004-T (B2): audit-log + telemetry for detection/report outcomes,
    mirroring the pipeline-topology force-audit pattern, with NO repair/
    mutation/confirm/post-condition field."""

    def test_audit_section_present_and_mirrors_pipeline_topology_pattern(self) -> None:
        content = _content()
        self.assertIn(_AUDIT_ANCHOR, content)
        idx = content.index(_AUDIT_ANCHOR)
        region = content[idx : idx + 1200]
        self.assertIn("pipeline-topology", region)
        self.assertIn("_audit_pipeline_topology_force", region)
        self.assertIn("_emit_pipeline_topology_telemetry", region)

    def test_audit_log_path_mirrors_gates_convention(self) -> None:
        content = _content()
        self.assertIn(".autoharness/gates/shipment-reconcile-detection-audit.log", content)

    def test_audit_entry_fields_present_and_no_repair_fields(self) -> None:
        content = _content()
        idx = content.index(_AUDIT_ANCHOR)
        region = content[idx : idx + 2200]
        for field in (
            "timestamp",
            "actor",
            "shipment_id",
            "record_status",
            "outcome",
            "per_task_roles",
            "remediation_guidance_emitted",
            "report_path",
        ):
            with self.subTest(field=field):
                self.assertIn(field, region)
        self.assertIn("NO `repair`, `mutation`,\n   `confirm`, or `post_condition` field", region)

    def test_telemetry_event_shape_mirrors_schema_and_pipeline_topology_mapping(self) -> None:
        content = _content()
        idx = content.index(_AUDIT_ANCHOR)
        region = content[idx : idx + 2500]
        self.assertIn("ToolTelemetryEvent", region)
        self.assertIn("schemas/tool-telemetry-event.schema.json", region)
        self.assertIn('tool_surface: "skill"', region)
        self.assertIn('tool_name: "shipment-reconcile"', region)
        self.assertIn('operation: "detect-mixed-role"', region)
        self.assertIn("DETECTED", region)
        self.assertIn("REPORTED", region)
        self.assertIn("DEGRADED", region)

    def test_telemetry_degrades_gracefully_without_blocking(self) -> None:
        content = _content()
        idx = content.index(_AUDIT_ANCHOR)
        region = content[idx : idx + 2600]
        self.assertIn("context_ref", region)
        self.assertIn("skipped", region)
        self.assertIn("fail-open", region)
        self.assertIn("NEVER blocks detection", region)

    def test_every_outcome_produces_audit_entry(self) -> None:
        content = _content()
        idx = content.index(_AUDIT_ANCHOR)
        region = content[idx : idx + 500]
        self.assertIn("EVERY candidate outcome", region)
        for outcome in _OUTCOMES:
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, region)


class MixedRoleDetectionOperatorRemediationGuidanceTests(unittest.TestCase):
    """112.001-T AC 4 / 112-F DoD (2): operator-remediation guidance points
    to the supported manual remediation and explicitly documents that a
    record-only forward re-claim is unsupported, with the read-only source
    evidence, and never fabricates a transition."""

    def test_remediation_guidance_section_present(self) -> None:
        content = _content()
        self.assertIn(_REMEDIATION_ANCHOR, content)

    def test_remediation_explicitly_states_no_auto_repair_and_unsupported_reclaim(self) -> None:
        content = _content()
        idx = content.index(_REMEDIATION_ANCHOR)
        region = content[idx : idx + 2200]
        self.assertIn("NO auto-repair", region)
        self.assertIn("UNSUPPORTED", region)
        self.assertIn("manifest-wide", region.lower())
        self.assertIn("STRICTLY SINGLE-SHOT", region)
        self.assertIn("ErrShipmentConflict", region)

    def test_remediation_cites_read_only_source_evidence(self) -> None:
        content = _content()
        idx = content.index(_REMEDIATION_ANCHOR)
        region = content[idx : idx + 2200]
        self.assertIn("NOT mutated", region)
        self.assertIn("shipment_lifecycle.go", region)
        self.assertIn("shipment.go", region)

    def test_remediation_never_fabricates_transition_and_points_to_supported_path(self) -> None:
        content = _content()
        idx = content.index(_REMEDIATION_ANCHOR)
        region = content[idx : idx + 2200]
        self.assertIn("SUPPORTED\n> manual remediation path", region)
        self.assertIn("never expect or fabricate", region.lower())
        self.assertIn("this skill never performs any of these steps\n> itself", region)


class MixedRoleDetectionStrayTokenTests(unittest.TestCase):
    """No stray unresolved template variable is introduced by the new
    prose -- every {{...}} token must already be one of the established,
    resolvable placeholder families."""

    def test_new_sections_only_use_established_placeholder_families(self) -> None:
        content = _content()
        class_idx = content.index(_CLASSIFICATION_ANCHOR)
        audit_idx = content.index(_AUDIT_ANCHOR)
        region = content[class_idx : audit_idx + 3000]
        for token in re.findall(r"\{\{[^}]+\}\}", region):
            with self.subTest(token=token):
                self.assertRegex(
                    token,
                    r"^\{\{(STATUS|OP|BACKLOG_DIRECTORY|SUFFIX)[A-Z_]*\}\}$",
                )


if __name__ == "__main__":
    unittest.main()
