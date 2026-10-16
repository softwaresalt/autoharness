"""Fixture proof for the marker_contract_v1 decision table (P-002.8 rules M3-M6).

The evaluator below is a test-local reference model, not an execution trace: it proves the
decision table yields the acceptance outcomes. The contract-text tests in
tests/test_p002_8_marker_consumption_contract.py prove the policy and Ship carry that table.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "marker_contract_v1" / "scenarios.json"
_POLICY_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"

TERMINAL_SUCCESS = ("done", "archived")

def is_claim_event(event: Dict[str, Any]) -> bool:
    delta = event.get("delta") or {}
    return (
        event.get("event_type") == "status_changed"
        and delta.get("to") == "active"
        and delta.get("reason") == "shipment claimed"
    )


def _load() -> Dict[str, Any]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


def _resolve_log(fixture: Dict[str, Any], ref: Any) -> Optional[List[Dict[str, Any]]]:
    if ref is None:
        return None
    if isinstance(ref, str):
        return fixture["log_templates"].get(ref)
    return ref


def start_epoch(log: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    last = None
    for index, event in enumerate(log):
        if is_claim_event(event):
            last = index
    return log if last is None else log[last + 1 :]


def has_claim_event(log: List[Dict[str, Any]]) -> bool:
    return any(is_claim_event(e) for e in log)


def first_line(body: str) -> str:
    line = body.split("\n", 1)[0]
    return line[:-1] if line.endswith("\r") else line


def has_valid_start_record(epoch: List[Dict[str, Any]], shipment: str) -> bool:
    expected = "WORK_STARTED: " + shipment
    return any(
        e.get("event_type") == "comment"
        and e.get("actor") == "ship"
        and first_line((e.get("delta") or {}).get("comment", "")) == expected
        for e in epoch
    )


def evaluate(fixture: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    shipment = scenario["shipment"]
    members: Dict[str, Dict[str, Any]] = scenario["members"]
    indeterminate: List[str] = []
    residuals: List[str] = []
    claim_assigned: List[str] = []

    if scenario["active_shipments"] != [shipment]:
        indeterminate.append("shipment")
    reads = scenario["manifest_reads"]
    if reads[0] != reads[1]:
        indeterminate.append("manifest")
    manifest = reads[0]

    for member_id in manifest:
        record = members[member_id]
        if record.get("read_error") or record.get("status_reread", record["status"]) != record["status"]:
            indeterminate.append(member_id)
            continue
        if record["status"] != "active":
            continue
        if record.get("marker") != shipment:
            residuals.append(member_id)
            continue
        log = _resolve_log(fixture, scenario.get("logs", {}).get(member_id))
        if log is None or not has_claim_event(log):
            indeterminate.append(member_id)
            continue
        if has_valid_start_record(start_epoch(log), shipment):
            residuals.append(member_id)
        else:
            claim_assigned.append(member_id)

    result: Dict[str, Any] = {
        "halt": None,
        "admitted": [],
        "claim_assigned_waiting": [],
        "active_residuals": residuals,
        "indeterminate": indeterminate,
    }
    if indeterminate:
        result["halt"] = "WAVE_CLAIM_STATE_INDETERMINATE"
        return result
    if residuals:
        result["halt"] = "WAVE_NO_PROGRESS"
        return result

    for member_id in manifest:
        record = members[member_id]
        if record["status"] != "queued" and member_id not in claim_assigned:
            continue
        ready = all(members[d]["status"] in TERMINAL_SUCCESS for d in record["deps"])
        key = "admitted" if ready else (
            "claim_assigned_waiting" if member_id in claim_assigned else None
        )
        if key:
            result[key].append(member_id)
    return result


class MarkerContractV1FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.fixture = _load()
        cls.scenarios = {s["id"]: s for s in cls.fixture["scenarios"]}

    def _assert_scenario(self, scenario_id: str) -> None:
        scenario = self.scenarios[scenario_id]
        self.assertEqual(evaluate(self.fixture, scenario), scenario["expected"], scenario_id)

    def test_f1_acceptance_1_wave_one_admission_without_residuals(self) -> None:
        self._assert_scenario("F1")
        self.assertEqual(self.scenarios["F1"]["expected"]["active_residuals"], [])
        self._assert_scenario("F9")

    def test_f2_f3_missing_or_foreign_marker_is_residual(self) -> None:
        for scenario_id in ("F2", "F3"):
            with self.subTest(scenario=scenario_id):
                self._assert_scenario(scenario_id)

    def test_f4_f5_f6_indeterminate_outranks_residual(self) -> None:
        for scenario_id in ("F4", "F5", "F6"):
            with self.subTest(scenario=scenario_id):
                self._assert_scenario(scenario_id)
        self.assertEqual(self.scenarios["F4"]["expected"]["active_residuals"], ["300.002-T"])

    def test_f7_f8_start_epoch_rules_and_contract_version(self) -> None:
        for scenario_id in ("F7", "F8", "F10", "F11", "F12"):
            with self.subTest(scenario=scenario_id):
                self._assert_scenario(scenario_id)
        policy = _POLICY_TEMPLATE.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        block = policy[policy.index("<!-- P-002.8:BEGIN") : policy.index("<!-- P-002.8:END -->")]
        match = re.search(r"marker_contract_version: (\d+)", block)
        self.assertIsNotNone(match)
        self.assertEqual(self.fixture["marker_contract_version"], int(match.group(1)))


if __name__ == "__main__":
    unittest.main()
