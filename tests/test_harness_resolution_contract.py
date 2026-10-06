"""Unit B, task B1 (188.001-T): result contract, reason registry and schema mirrors.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "B1: Contracts, reason registry and schema mirrors".

* The 47-code registry is compared with a test-local constant parsed from the
  hash-pinned Stage candidate block (charter commit ``52c985cb``, lines
  717-749, SHA-256 pinned below). The governing 8 codes come from a second,
  separately pinned block (lines 696-716) and are never derived from the
  registry (FI-6, IM-03, IM-17).
* Counts are derived from the lists, never written by hand; the block's own
  reference counts are parsed from its text.
* Structural tests (``test_structural_*``) reach no stub and are recorded
  outside the expected-RED roster. ``ResultContractRosterTests`` is the
  roster; each roster test reaches its own ``NotImplementedError`` marker
  ``AHLC_B1_RESOLUTION_CONTRACT:<test method name>`` in the RED phase.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from autoharness import harness_surfaces as hs
from autoharness.harness_read import ReadErrorCode
from autoharness.schema_contracts import SCHEMA_CONTRACTS, resolve_contract_schema_path

REPO_ROOT = Path(__file__).resolve().parents[1]
ROOT_SCHEMA = REPO_ROOT / "schemas" / "harness-resolution.schema.json"
MIRROR_SCHEMA = REPO_ROOT / "schemas" / "harness-resolution" / "1.0.0.schema.json"
ROOT_SCHEMA_ID = "https://github.com/softwaresalt/autoharness/schemas/harness-resolution.schema.json"
MIRROR_SCHEMA_ID = "https://github.com/softwaresalt/autoharness/schemas/harness-resolution/1.0.0.schema.json"
# SHA-256 of the published 1.0.0 mirror over LF-normalized bytes. A change to the
# mirror is a new contract version, never an in-place edit
# (docs/compound/2026-08-08-schema-mirror-mutated-in-place-without-version-bump.md).
MIRROR_SHA256_LF = "d6b8f956c5d2cad98d466b6ee5facbaaa78195a75fc293b84bc347502ce4951a"

MARKER = "AHLC_B1_RESOLUTION_CONTRACT"

# Charter docs/decisions/2026-09-23-lifecycle-proof-entry-charter.md at 52c985cb,
# lines 717-749 (the Stage candidate), copied verbatim; LF-joined SHA-256 pinned.
CANDIDATE_BLOCK_SHA256 = "64c41cd150dde7273506e0a2b179a04187bb80139216b14b5fe898cb896b6847"
CANDIDATE_BLOCK = (
    '* **Stage candidate (PE-1.4; a proposal, not ratified API).** The run 2\n'
    '  candidate is the run 1 candidate enum (`c_schema.json`, SHA-256\n'
    '  `c80cab23bfae45ff34e799abb7d0be1787c1d89ceab0fce0f3cc2c70f89345ae`) with\n'
    '  `READ_BUDGET_EXHAUSTED` removed and the three class 1b codes added. The\n'
    '  listed order is the candidate precedence:\n'
    '\n'
    '  | Class | State / exit | Candidate codes, in order |\n'
    '  |---|---|---|\n'
    '  | 1 | `UNRESOLVED / 2` | `INPUT_CHANGED_DURING_RESOLUTION` |\n'
    '  | 1b | `UNRESOLVED / 2` | `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` (first occurrence selects; no fixed order among them) |\n'
    '  | 2 | `UNRESOLVED / 2` | `BACKLOG_ROOT_NOT_FOUND`, `BACKLOG_ROOT_AMBIGUOUS`, `SHIPMENT_ID_INVALID`, `SHIPMENT_NOT_FOUND`, `SHIPMENT_AMBIGUOUS`, `SHIPMENT_RECORD_INVALID`, `SHIPMENT_ID_MISMATCH`, `MEMBERS_INVALID`, `MEMBERS_EMPTY`, `MEMBERS_TOO_MANY`, `MEMBER_ID_INVALID`, `MEMBER_KIND_UNSUPPORTED`, `MEMBER_DUPLICATE`, `MEMBER_NOT_FOUND`, `MEMBER_AMBIGUOUS`, `MEMBER_RECORD_INVALID`, `MEMBER_ID_MISMATCH`, `NO_TASK_MEMBERS` |\n'
    '  | 3 | `UNRESOLVED / 2` | `FEATURE_DECLARES_SURFACE`, `DECLARATION_MISSING`, `DECLARATION_MALFORMED`, `DECLARATION_DUPLICATE`, `DECLARATION_MIXED`, `SURFACE_UNSUPPORTED` |\n'
    '  | 4 | `HARNESS_READY / 0` | `NO_SURFACES_REQUIRED` |\n'
    '  | 5 | `UNRESOLVED / 2` | `MANIFEST_NOT_FOUND`, `MANIFEST_UNREADABLE`, `MANIFEST_DECODE_INVALID`, `MANIFEST_YAML_INVALID`, `MANIFEST_DUPLICATE_KEY`, `MANIFEST_SHAPE_INVALID` |\n'
    '  | 6 | `UNRESOLVED / 2` (`INVALID` surface) | `MANIFEST_ENTRY_AMBIGUOUS`, `MANIFEST_TEMPLATE_MISMATCH`, `MANIFEST_ENTRY_INVALID`, `TEMPLATE_NOT_FOUND`, `TEMPLATE_UNREADABLE`, `TEMPLATE_VARIABLE_UNRESOLVED`, `INSTALLED_UNREADABLE` |\n'
    '  | 7 | `NO_HARNESS / 1` (`MISSING` or `STALE` surface) | `MANIFEST_ENTRY_NOT_FOUND`, `INSTALLED_NOT_FOUND`, `CHECKSUM_MISMATCH`, `RENDER_MISMATCH` |\n'
    '  | 8 | `HARNESS_READY / 0` | `ALL_SURFACES_PRESENT` |\n'
    '\n'
    '  Counts are not criteria. The fixture derives every count from these lists\n'
    '  and records it, and asserts no count written by hand. For reference only:\n'
    '  the run 1 enum had 45 codes, so this list has 45 - 1 + 3 = 47 (2\n'
    '  `HARNESS_READY`, 4 `NO_HARNESS` and 41 `UNRESOLVED`). If a derived count\n'
    '  differs from this reference, the list governs and the difference is\n'
    '  recorded. Not ratified by any source, and so proposals only: the codes\n'
    '  outside the governing set; the order within classes 2, 3 and 5 to 7; the\n'
    '  tie-break between declaration issues; and the shape of `declarations`\n'
    '  items. Plan revision 12 fixes only that `declarations` is a result field\n'
    "  sorted by task ID (lines 134 and 138). Run 1's\n"
    "  `{member_id, surface_id}` with `additionalProperties: false` was Ship's\n"
    '  assumption. The fixture may use it only when it is labelled as a candidate.\n'
    '  A run 2 `PASS` ratifies none of these proposals. The commit of this charter\n'
    '  version is the durable, hash-pinned candidate that the Proof C findings\n'
    '  asked for. Ship copies both constants from it and records the commit.'
)

# Same charter, lines 696-716 (the governing reason set); LF-joined SHA-256 pinned.
GOVERNING_BLOCK_SHA256 = "cba91a303c24edf4b88a0a907d5caf8ca6c695a33c2b5cd256e1b7cba7f9f0cf"
GOVERNING_BLOCK = (
    '* **Governing reason set (PE-1.4).** This set is fixed by this charter and by\n'
    "  ratified text. It does not depend on any fixture's own enum. The fixture\n"
    '  holds it as a separate constant copied from this table, and never derives\n'
    '  it from the candidate:\n'
    '\n'
    '  | Code | State / exit | Source |\n'
    '  |---|---|---|\n'
    '  | `FILE_COUNT_LIMIT`, `TOTAL_SIZE_LIMIT`, `FILE_SIZE_LIMIT` | `UNRESOLVED / 2`, class 1b (after class 1, before class 2) | Decision 2 items 1, 2 and 4; section 6.6 |\n'
    '  | `INPUT_CHANGED_DURING_RESOLUTION` | `UNRESOLVED / 2`, class 1 | Plan revision 12 reducer precedence (frozen diagnostic input); Decision 2 item 2 |\n'
    '  | `SURFACE_UNSUPPORTED` | `UNRESOLVED / 2` | This section; `PE-INTERFACE-03` |\n'
    '  | `MEMBERS_TOO_MANY` | `UNRESOLVED / 2` | Section 6.6 |\n'
    '  | `NO_SURFACES_REQUIRED` | `HARNESS_READY / 0`, class 4 | Plan revision 12 reducer precedence |\n'
    '  | `ALL_SURFACES_PRESENT` | `HARNESS_READY / 0`, class 8 | Plan revision 12 reducer precedence |\n'
    '\n'
    "  A class 1b result's `reason_code` is the triggering read-limit\n"
    '  `ReadErrorCode`, unchanged. It is the one that occurred first in\n'
    '  deterministic generation order, not the one ranked first by a fixed code\n'
    '  order. The diagnostics keep the native `ReadErrorCode` and the `ReadStage`\n'
    '  (Decision 2 item 4). No other code stands for a read-limit error.\n'
    '  `READ_BUDGET_EXHAUSTED`, or any other code outside the governing set and\n'
    '  the candidate below, is a defect.'
)

_BACKTICKED = re.compile(r"`([^`]+)`")
_STATE_EXIT = re.compile(r"^([A-Z_]+) / ([0-9])$")


def _table_rows(block: str) -> list[list[str]]:
    rows = []
    for line in block.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|") or stripped.startswith("|---"):
            continue
        rows.append([cell.strip() for cell in stripped.strip("|").split("|")])
    return rows[1:]  # drop the header row


def _state_exit(cell: str) -> tuple[str, int]:
    match = _STATE_EXIT.match(_BACKTICKED.findall(cell)[0])
    assert match is not None, cell
    return match.group(1), int(match.group(2))


def parse_candidate() -> list[tuple[str, str, str, int]]:
    """(code, class, state, exit) in listed order, from the pinned candidate block."""
    parsed = []
    for reason_class, state_cell, codes_cell in _table_rows(CANDIDATE_BLOCK):
        state, exit_code = _state_exit(state_cell)
        for code in _BACKTICKED.findall(codes_cell):
            parsed.append((code, reason_class, state, exit_code))
    return parsed


def parse_governing() -> dict[str, tuple[str, int, str | None]]:
    """code -> (state, exit, class or None), from the pinned governing block."""
    governing: dict[str, tuple[str, int, str | None]] = {}
    for codes_cell, outcome_cell, _source in _table_rows(GOVERNING_BLOCK):
        state, exit_code = _state_exit(outcome_cell)
        class_match = re.search(r"class (1b|[0-9])", outcome_cell)
        reason_class = class_match.group(1) if class_match else None
        for code in _BACKTICKED.findall(codes_cell):
            governing[code] = (state, exit_code, reason_class)
    return governing


def parse_reference_counts() -> tuple[int, dict[str, int]]:
    text = " ".join(CANDIDATE_BLOCK.split())
    match = re.search(
        r"= ([0-9]+) \(([0-9]+) `HARNESS_READY`, ([0-9]+) `NO_HARNESS` and ([0-9]+) `UNRESOLVED`\)",
        text,
    )
    assert match is not None
    total, ready, no_harness, unresolved = (int(group) for group in match.groups())
    return total, {"HARNESS_READY": ready, "NO_HARNESS": no_harness, "UNRESOLVED": unresolved}


# Per-code surface row state (plan B3; Proof C run 4 fixture), test-local.
SURFACE_ROW_STATES = {
    "MANIFEST_ENTRY_AMBIGUOUS": "INVALID",
    "MANIFEST_TEMPLATE_MISMATCH": "INVALID",
    "MANIFEST_ENTRY_INVALID": "INVALID",
    "TEMPLATE_NOT_FOUND": "INVALID",
    "TEMPLATE_UNREADABLE": "INVALID",
    "TEMPLATE_VARIABLE_UNRESOLVED": "INVALID",
    "INSTALLED_UNREADABLE": "INVALID",
    "MANIFEST_ENTRY_NOT_FOUND": "MISSING",
    "INSTALLED_NOT_FOUND": "MISSING",
    "CHECKSUM_MISMATCH": "STALE",
    "RENDER_MISMATCH": "STALE",
    "ALL_SURFACES_PRESENT": "PRESENT",
}

# The result field set of the proven Proof C fixture schema (FI-7), in order.
C3_FIELD_SET = (
    "schema_version",
    "state",
    "reason_code",
    "exit_code",
    "shipment_id",
    "backlog_root",
    "surfaces",
    "declarations",
    "inputs_sha256",
    "diagnostics",
)

READ_STAGE_TOKENS = {
    "SHIPMENT_CANDIDATE": "shipment_queue_or_archive_candidate",
    "MEMBER_CANDIDATE": "member_queue_or_archive_candidate",
    "MANIFEST": "manifest_read",
    "TEMPLATE": "template_read",
    "INSTALLED": "installed_file_read",
    "CANDIDATE_RECHECK": "candidate_ledger_recheck",
    "SURFACE_RECHECK": "surface_recheck",
}
READ_LIMIT_CODES = ("FILE_COUNT_LIMIT", "TOTAL_SIZE_LIMIT", "FILE_SIZE_LIMIT")
ROOT_CODES = ("BACKLOG_ROOT_NOT_FOUND", "BACKLOG_ROOT_AMBIGUOUS")


class _IntSubclass(int):
    """An ``int`` subclass that compares equal to a registry exit code but is not an exact ``int``."""


SURFACE_ROW = {
    "surface_id": "harness-architect",
    "installed_path": ".github/skills/harness-architect/SKILL.md",
    "template": "skills/harness-architect/SKILL.md.tmpl",
}
DIGEST = hashlib.sha256(b"B1 synthetic input").hexdigest()


def hand_document(code: str, *, stage: str = "manifest_read") -> dict[str, Any]:
    """A schema-shaped document built by hand from the pinned constants (no module call)."""
    outcome = {entry[0]: entry for entry in parse_candidate()}[code]
    row_state = SURFACE_ROW_STATES.get(code)
    surfaces = [] if row_state is None else [{**SURFACE_ROW, "state": row_state, "reason_code": code}]
    diagnostics = [] if code not in READ_LIMIT_CODES else [f"read_error_code={code}", f"read_stage={stage}"]
    return {
        "schema_version": "1.0.0",
        "state": outcome[2],
        "reason_code": code,
        "exit_code": outcome[3],
        "shipment_id": None if code == "SHIPMENT_ID_INVALID" else "999-S",
        "backlog_root": None if code in ROOT_CODES else ".backlogit",
        "surfaces": surfaces,
        "declarations": [{"member_id": "1.001-T", "surface_id": "harness-architect"}],
        "inputs_sha256": DIGEST,
        "diagnostics": diagnostics,
    }


def load_schema(path: Path) -> dict[str, Any]:
    return json.loads(path.read_bytes().decode("utf-8"))


class RegistryStructuralTests(unittest.TestCase):
    """Registry and table parity; structural, outside the roster."""

    def test_structural_pinned_blocks_hash(self) -> None:
        self.assertEqual(hashlib.sha256(CANDIDATE_BLOCK.encode("utf-8")).hexdigest(), CANDIDATE_BLOCK_SHA256)
        self.assertEqual(hashlib.sha256(GOVERNING_BLOCK.encode("utf-8")).hexdigest(), GOVERNING_BLOCK_SHA256)

    def test_structural_registry_equals_pinned_candidate(self) -> None:
        registry = [(s.code, s.reason_class, s.state.value, s.exit_code) for s in hs.REASON_REGISTRY]
        self.assertEqual(registry, parse_candidate())

    def test_structural_governing_codes_hold_governing_outcome(self) -> None:
        by_code = {spec.code: spec for spec in hs.REASON_REGISTRY}
        governing = parse_governing()
        self.assertEqual(len(governing), len(set(governing)))
        for code, (state, exit_code, reason_class) in governing.items():
            with self.subTest(code=code):
                self.assertIn(code, by_code)
                self.assertEqual(by_code[code].state.value, state)
                self.assertEqual(by_code[code].exit_code, exit_code)
                if reason_class is not None:
                    self.assertEqual(by_code[code].reason_class, reason_class)

    def test_structural_derived_counts_match_block_reference(self) -> None:
        total, split = parse_reference_counts()
        codes = [spec.code for spec in hs.REASON_REGISTRY]
        self.assertEqual(len(codes), len(set(codes)))
        self.assertEqual(len(codes), total)
        derived = {state: 0 for state in split}
        for spec in hs.REASON_REGISTRY:
            derived[spec.state.value] += 1
        self.assertEqual(derived, split)
        self.assertEqual(len(parse_governing()), len({c for c in parse_governing() if c in codes}))

    def test_structural_retired_code_absent(self) -> None:
        self.assertNotIn("READ_BUDGET_EXHAUSTED", {spec.code for spec in hs.REASON_REGISTRY})

    def test_structural_surface_state_bound_per_code(self) -> None:
        for spec in hs.REASON_REGISTRY:
            with self.subTest(code=spec.code):
                expected = SURFACE_ROW_STATES.get(spec.code)
                actual = None if spec.surface_state is None else spec.surface_state.value
                self.assertEqual(actual, expected)

    def test_structural_state_exit_table_and_read_stage(self) -> None:
        self.assertEqual(
            {state.value: code for state, code in hs.STATE_EXIT.items()},
            {"HARNESS_READY": 0, "NO_HARNESS": 1, "UNRESOLVED": 2},
        )
        for spec in hs.REASON_REGISTRY:
            self.assertEqual(hs.STATE_EXIT[spec.state], spec.exit_code)
        self.assertEqual({stage.name: stage.value for stage in hs.ReadStage}, READ_STAGE_TOKENS)
        self.assertEqual([stage.name for stage in hs.ReadStage], list(READ_STAGE_TOKENS))
        self.assertEqual(hs.SCHEMA_VERSION, "1.0.0")

    def test_structural_roster_markers_pairwise_distinct(self) -> None:
        names = sorted(name for name in dir(ResultContractRosterTests) if name.startswith("test_"))
        markers = [f"{MARKER}:{name}" for name in names]
        self.assertEqual(len(names), 5)
        self.assertEqual(len(set(markers)), len(markers))
        self.assertFalse(any(name.startswith("test_structural_") for name in names))


class SchemaMirrorStructuralTests(unittest.TestCase):
    """Schema files, mirror pin, branch-per-code and Proof C mutants; outside the roster."""

    def test_structural_schema_files_equal_except_id(self) -> None:
        root, mirror = load_schema(ROOT_SCHEMA), load_schema(MIRROR_SCHEMA)
        self.assertEqual(root.pop("$id"), ROOT_SCHEMA_ID)
        self.assertEqual(mirror.pop("$id"), MIRROR_SCHEMA_ID)
        self.assertEqual(root, mirror)

    def test_structural_mirror_sha256_pinned(self) -> None:
        data = MIRROR_SCHEMA.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(data).hexdigest(), MIRROR_SHA256_LF)

    def test_structural_contract_registered(self) -> None:
        contract = SCHEMA_CONTRACTS["harness-resolution"]
        self.assertEqual(contract["contract_name"], "harness-resolution")
        self.assertEqual(contract["schema_file"], "harness-resolution.schema.json")
        self.assertEqual(contract["versioned_schema_dir"], "harness-resolution")
        self.assertEqual(contract["current_version"], "1.0.0")
        self.assertEqual(tuple(contract["known_versions"]), ("1.0.0",))
        self.assertEqual(contract["compatibility_model"], "versioned-contract")
        resolved = resolve_contract_schema_path("harness-resolution", REPO_ROOT, {"schema_version": "1.0.0"})
        self.assertEqual(resolved, MIRROR_SCHEMA)

    def test_structural_closed_object_and_enums(self) -> None:
        schema = load_schema(MIRROR_SCHEMA)
        Draft202012Validator.check_schema(schema)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(tuple(schema["required"]), C3_FIELD_SET)
        self.assertEqual(tuple(schema["properties"]), C3_FIELD_SET)
        properties = schema["properties"]
        self.assertEqual(properties["schema_version"], {"const": "1.0.0"})
        self.assertEqual(properties["state"]["enum"], ["HARNESS_READY", "NO_HARNESS", "UNRESOLVED"])
        self.assertEqual(properties["reason_code"]["enum"], [entry[0] for entry in parse_candidate()])
        self.assertEqual(properties["exit_code"]["enum"], [0, 1, 2])
        row = properties["surfaces"]["items"]
        self.assertIs(row["additionalProperties"], False)
        self.assertEqual(row["properties"]["state"]["enum"], ["PRESENT", "MISSING", "STALE", "INVALID"])
        self.assertEqual(row["properties"]["reason_code"]["enum"], list(SURFACE_ROW_STATES))
        self.assertEqual(properties["surfaces"]["maxItems"], 1)
        item = properties["declarations"]["items"]
        self.assertIs(item["additionalProperties"], False)
        self.assertEqual(item["required"], ["member_id", "surface_id"])
        self.assertEqual(item["properties"], {"member_id": {"type": "string"}, "surface_id": {"type": "string"}})
        self.assertEqual(properties["inputs_sha256"]["pattern"], "^[0-9a-f]{64}$")

    def test_structural_one_branch_per_code_binds_state_and_exit(self) -> None:
        schema = load_schema(MIRROR_SCHEMA)
        branches = schema["oneOf"]
        candidate = parse_candidate()
        self.assertEqual(len(branches), len(candidate))
        for code, _reason_class, state, exit_code in candidate:
            with self.subTest(code=code):
                matching = [b for b in branches if b["properties"]["reason_code"] == {"const": code}]
                self.assertEqual(len(matching), 1)
                self.assertEqual(matching[0]["properties"]["state"], {"const": state})
                self.assertEqual(matching[0]["properties"]["exit_code"], {"const": exit_code})

    def test_structural_hand_built_document_per_code_validates(self) -> None:
        validator = Draft202012Validator(load_schema(MIRROR_SCHEMA))
        for code, *_rest in parse_candidate():
            stages = READ_STAGE_TOKENS.values() if code in READ_LIMIT_CODES else ("manifest_read",)
            for stage in stages:
                with self.subTest(code=code, stage=stage):
                    errors = [e.message for e in validator.iter_errors(hand_document(code, stage=stage))]
                    self.assertEqual(errors, [])

    def test_structural_proof_c_mutants_rejected(self) -> None:
        schema = load_schema(MIRROR_SCHEMA)
        validator = Draft202012Validator(schema)
        base = hand_document("FILE_COUNT_LIMIT", stage="manifest_read")
        self.assertEqual(list(validator.iter_errors(base)), [])
        mutants: list[tuple[str, dict[str, Any]]] = []

        def mutate(name: str, **changes: Any) -> None:
            mutant = copy.deepcopy(base)
            mutant.update(changes)
            mutants.append((name, mutant))

        mutate("retired_read_budget_code", reason_code="READ_BUDGET_EXHAUSTED")
        mutate("read_code_replaced_by_member_code", reason_code="MEMBERS_TOO_MANY")
        mutate("class_1b_missing_read_stage", diagnostics=["read_error_code=FILE_COUNT_LIMIT"])
        mutate("wrong_state", state="NO_HARNESS")
        mutate("wrong_exit", exit_code=1)
        mutate("extra_root_property", unexpected=True)
        mutate("unknown_read_stage", diagnostics=["read_error_code=FILE_COUNT_LIMIT", "read_stage=alien"])
        checksum = hand_document("CHECKSUM_MISMATCH")
        self.assertEqual(list(validator.iter_errors(checksum)), [])
        checksum["surfaces"][0]["state"] = "INVALID"
        mutants.append(("checksum_mismatch_invalid_surface", checksum))
        for name, mutant in mutants:
            with self.subTest(mutant=name):
                self.assertNotEqual(list(validator.iter_errors(mutant)), [])
        # The ninth control: deleting a code from the enum rejects an otherwise valid output.
        damaged = copy.deepcopy(schema)
        damaged["properties"]["reason_code"]["enum"].remove("ALL_SURFACES_PRESENT")
        valid = hand_document("ALL_SURFACES_PRESENT")
        self.assertEqual(list(validator.iter_errors(valid)), [])
        self.assertNotEqual(list(Draft202012Validator(damaged).iter_errors(valid)), [])
        self.assertEqual(len(mutants) + 1, 9)


class ResultContractRosterTests(unittest.TestCase):
    """Expected-RED roster: each test reaches its own B1 stub marker."""

    def test_reason_spec_binds_class_state_exit(self) -> None:
        candidate = parse_candidate()
        self.assertEqual(hs.reason_spec(candidate[0][0]).code, candidate[0][0])
        for code, reason_class, state, exit_code in candidate:
            with self.subTest(code=code):
                spec = hs.reason_spec(code)
                self.assertEqual(spec.code, code)
                self.assertEqual(spec.reason_class, reason_class)
                self.assertEqual(spec.state.value, state)
                self.assertEqual(spec.exit_code, exit_code)
        for unknown in ("READ_BUDGET_EXHAUSTED", "", "ALL_SURFACES_PRESENT "):
            with self.subTest(unknown=unknown), self.assertRaises(KeyError):
                hs.reason_spec(unknown)

    def test_read_limit_diagnostics_pairs_code_and_stage(self) -> None:
        self.assertEqual(
            hs.read_limit_diagnostics(ReadErrorCode.FILE_SIZE_LIMIT, hs.ReadStage.SHIPMENT_CANDIDATE),
            ("read_error_code=FILE_SIZE_LIMIT", "read_stage=shipment_queue_or_archive_candidate"),
        )
        for code in READ_LIMIT_CODES:
            for stage in hs.ReadStage:
                with self.subTest(code=code, stage=stage.name):
                    self.assertEqual(
                        hs.read_limit_diagnostics(ReadErrorCode[code], stage),
                        (f"read_error_code={code}", f"read_stage={READ_STAGE_TOKENS[stage.name]}"),
                    )
        for other in ("LEXICAL_INVALID", "OUTSIDE_TRUST_ROOT", "PATH_NOT_FOUND", "NOT_REGULAR_FILE", "IO"):
            with self.subTest(other=other), self.assertRaises(ValueError):
                hs.read_limit_diagnostics(ReadErrorCode[other], hs.ReadStage.MANIFEST)

    def test_task_id_sort_key_orders_by_numeric_parts(self) -> None:
        ids = ["10-T", "2.10-T", "2.9-T", "2-T", "2.009.1-T"]
        self.assertEqual(sorted(ids, key=hs.task_id_sort_key), ["2-T", "2.9-T", "2.009.1-T", "2.10-T", "10-T"])
        for invalid in ("", "2", "T-2", "2-t", "2..1-T", "2.x-T", "-T", "2-TT", 7):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                hs.task_id_sort_key(invalid)  # type: ignore[arg-type]

    def test_make_result_derives_outcome_and_enforces_contract(self) -> None:
        def build(code: str, **overrides: Any) -> hs.ResolutionResult:
            row_state = SURFACE_ROW_STATES.get(code)
            arguments: dict[str, Any] = {
                "shipment_id": None if code == "SHIPMENT_ID_INVALID" else "12-S",
                "backlog_root": None if code in ROOT_CODES else ".backlog",
                "inputs_sha256": DIGEST,
                "surfaces": ()
                if row_state is None
                else (hs.SurfaceRow(**SURFACE_ROW, state=hs.SurfaceState[row_state], reason_code=code),),
                "declarations": (
                    hs.Declaration("2-T", "none"),
                    hs.Declaration("10-T", "harness-architect"),
                ),
                "diagnostics": ()
                if code not in READ_LIMIT_CODES
                else hs.read_limit_diagnostics(ReadErrorCode[code], hs.ReadStage.INSTALLED),
            }
            arguments.update(overrides)
            return hs.make_result(code, **arguments)

        first = build("ALL_SURFACES_PRESENT")
        self.assertEqual((first.state, first.exit_code), (hs.ResolutionState.HARNESS_READY, 0))
        for code, _reason_class, state, exit_code in parse_candidate():
            with self.subTest(code=code):
                result = build(code)
                self.assertIsInstance(result, hs.ResolutionResult)
                self.assertEqual((result.reason_code, result.state.value, result.exit_code), (code, state, exit_code))
                self.assertEqual(result.schema_version, "1.0.0")
                self.assertEqual([d.member_id for d in result.declarations], ["2-T", "10-T"])
                self.assertIsInstance(result.surfaces, tuple)
                self.assertIsInstance(result.diagnostics, tuple)
        self.assertIsNone(build("BACKLOG_ROOT_NOT_FOUND", shipment_id=None).shipment_id)
        self.assertEqual(build("BACKLOG_ROOT_AMBIGUOUS", shipment_id="3-S").shipment_id, "3-S")
        self.assertEqual(build("MEMBER_NOT_FOUND", backlog_root=".backlogit").backlog_root, ".backlogit")

        row = hs.SurfaceRow(**SURFACE_ROW, state=hs.SurfaceState.STALE, reason_code="CHECKSUM_MISMATCH")
        rejected: list[tuple[str, str, dict[str, Any]]] = [
            ("unknown code", "READ_BUDGET_EXHAUSTED", {}),
            ("1b without diagnostics", "FILE_SIZE_LIMIT", {"diagnostics": ()}),
            ("1b wrong code diagnostics", "FILE_SIZE_LIMIT", {
                "diagnostics": hs.read_limit_diagnostics(ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.MANIFEST)
            }),
            ("read diagnostics on non-read code", "MEMBERS_TOO_MANY", {
                "diagnostics": hs.read_limit_diagnostics(ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.MANIFEST)
            }),
            ("stage-only diagnostic on non-read code", "MEMBERS_TOO_MANY", {"diagnostics": ("read_stage=manifest_read",)}),
            ("surface code without row", "CHECKSUM_MISMATCH", {"surfaces": ()}),
            ("row on a non-surface code", "NO_SURFACES_REQUIRED", {"surfaces": (row,)}),
            ("row state disagrees", "RENDER_MISMATCH", {"surfaces": (row,)}),
            ("two rows", "CHECKSUM_MISMATCH", {"surfaces": (row, row)}),
            ("unsupported surface row", "CHECKSUM_MISMATCH", {
                "surfaces": (hs.SurfaceRow("other", ".github/skills/other/SKILL.md", "skills/other/SKILL.md.tmpl",
                                           hs.SurfaceState.STALE, "CHECKSUM_MISMATCH"),)
            }),
            ("unsorted declarations", "NO_SURFACES_REQUIRED", {
                "declarations": (hs.Declaration("10-T", "none"), hs.Declaration("2-T", "none"))
            }),
            ("duplicate declaration", "NO_SURFACES_REQUIRED", {
                "declarations": (hs.Declaration("2-T", "none"), hs.Declaration("2-T", "none"))
            }),
            ("non-task declaration", "NO_SURFACES_REQUIRED", {"declarations": (hs.Declaration("2-F", "none"),)}),
            ("empty surface id", "NO_SURFACES_REQUIRED", {"declarations": (hs.Declaration("2-T", ""),)}),
            ("bad digest", "NO_SURFACES_REQUIRED", {"inputs_sha256": DIGEST.upper()}),
            ("short digest", "NO_SURFACES_REQUIRED", {"inputs_sha256": DIGEST[:-1]}),
            ("bad shipment id", "NO_SURFACES_REQUIRED", {"shipment_id": "12-T"}),
            ("null shipment id", "NO_SURFACES_REQUIRED", {"shipment_id": None}),
            ("id-invalid with id", "SHIPMENT_ID_INVALID", {"shipment_id": "12-S"}),
            ("null root", "NO_SURFACES_REQUIRED", {"backlog_root": None}),
            ("root on a root code", "BACKLOG_ROOT_NOT_FOUND", {"backlog_root": ".backlog"}),
            ("unknown root", "NO_SURFACES_REQUIRED", {"backlog_root": "backlog"}),
        ]
        for label, code, overrides in rejected:
            with self.subTest(rejected=label), self.assertRaises(ValueError):
                build(code, **overrides)

    def test_to_document_emits_schema_valid_document(self) -> None:
        def result_for(code: str, state: str, exit_code: int, expected: dict[str, Any]) -> hs.ResolutionResult:
            row_state = SURFACE_ROW_STATES.get(code)
            return hs.ResolutionResult(
                schema_version="1.0.0",
                state=hs.ResolutionState[state],
                reason_code=code,
                exit_code=exit_code,
                shipment_id=expected["shipment_id"],
                backlog_root=expected["backlog_root"],
                surfaces=()
                if row_state is None
                else (hs.SurfaceRow(**SURFACE_ROW, state=hs.SurfaceState[row_state], reason_code=code),),
                declarations=(hs.Declaration("1.001-T", "harness-architect"),),
                inputs_sha256=DIGEST,
                diagnostics=tuple(expected["diagnostics"]),
            )

        first = hand_document("ALL_SURFACES_PRESENT")
        self.assertEqual(result_for("ALL_SURFACES_PRESENT", "HARNESS_READY", 0, first).to_document(), first)
        validator = Draft202012Validator(load_schema(MIRROR_SCHEMA))
        for code, _reason_class, state, exit_code in parse_candidate():
            with self.subTest(code=code):
                expected = hand_document(code, stage="installed_file_read")
                document = result_for(code, state, exit_code, expected).to_document()
                self.assertEqual(list(document), list(C3_FIELD_SET))
                self.assertEqual(document, expected)
                self.assertEqual(json.loads(json.dumps(document)), document)
                self.assertEqual(list(validator.iter_errors(document)), [])


class ResultContractReviewFixTests(unittest.TestCase):
    """Local-review fixes (194-S): make_result output and the schema agree; direct construction is checked."""

    def build(self, code: str, **overrides: Any) -> hs.ResolutionResult:
        row_state = SURFACE_ROW_STATES.get(code)
        arguments: dict[str, Any] = {
            "shipment_id": None if code == "SHIPMENT_ID_INVALID" else "12-S",
            "backlog_root": None if code in ROOT_CODES else ".backlog",
            "inputs_sha256": DIGEST,
            "surfaces": ()
            if row_state is None
            else (hs.SurfaceRow(**SURFACE_ROW, state=hs.SurfaceState[row_state], reason_code=code),),
            "declarations": (hs.Declaration("2-T", "none"), hs.Declaration("10-T", "harness-architect")),
            "diagnostics": ()
            if code not in READ_LIMIT_CODES
            else hs.read_limit_diagnostics(ReadErrorCode[code], hs.ReadStage.SURFACE_RECHECK),
        }
        arguments.update(overrides)
        return hs.make_result(code, **arguments)

    def test_make_result_output_validates_against_mirror(self) -> None:
        validator = Draft202012Validator(load_schema(MIRROR_SCHEMA))
        for code, *_rest in parse_candidate():
            variants: list[dict[str, Any]] = [{}, {"backlog_root": ".backlogit"}] if code not in ROOT_CODES else [
                {"shipment_id": None},
                {"shipment_id": "3-S"},
            ]
            for overrides in variants:
                with self.subTest(code=code, overrides=overrides):
                    document = self.build(code, **overrides).to_document()
                    self.assertEqual(list(validator.iter_errors(document)), [])

    def test_contract_rejects_wrong_element_types_and_unknown_surfaces(self) -> None:
        row = hs.SurfaceRow(**SURFACE_ROW, state=hs.SurfaceState.STALE, reason_code="CHECKSUM_MISMATCH")
        rejected: list[tuple[str, str, dict[str, Any]]] = [
            ("row is a dict", "CHECKSUM_MISMATCH", {"surfaces": (dict(SURFACE_ROW),)}),
            ("declaration is a tuple", "NO_SURFACES_REQUIRED", {"declarations": (("2-T", "none"),)}),
            ("unsupported declared surface", "NO_SURFACES_REQUIRED", {"declarations": (hs.Declaration("2-T", "bogus"),)}),
            ("unhashable declared surface", "NO_SURFACES_REQUIRED", {"declarations": (hs.Declaration("2-T", ["x"]),)}),  # type: ignore[arg-type]
            ("diagnostic not a string", "NO_SURFACES_REQUIRED", {"diagnostics": (3,)}),
            ("unhashable code", "CHECKSUM_MISMATCH", {"surfaces": (row,)}),
        ]
        for label, code, overrides in rejected:
            with self.subTest(rejected=label), self.assertRaises(ValueError):
                if label == "unhashable code":
                    hs.make_result(["CHECKSUM_MISMATCH"], shipment_id="1-S", backlog_root=".backlog",  # type: ignore[arg-type]
                                   inputs_sha256=DIGEST, surfaces=(row,))
                else:
                    self.build(code, **overrides)

    def test_direct_construction_is_checked(self) -> None:
        valid = self.build("ALL_SURFACES_PRESENT")
        self.assertEqual(hs.ResolutionResult(**vars(valid)), valid)
        for field, value in (
            ("state", hs.ResolutionState.NO_HARNESS),
            ("exit_code", 1),
            # Copilot review (PR #498): an integral float, a bool or an int subclass equals the
            # registry integer but is not the JSON integer token the contract promises.
            ("exit_code", 0.0),
            ("exit_code", False),
            ("exit_code", _IntSubclass(0)),
            ("schema_version", "1.1.0"),
            ("surfaces", ()),
            ("inputs_sha256", "x"),
        ):
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                hs.ResolutionResult(**{**vars(valid), field: value})
        listed = hs.ResolutionResult(**{**vars(valid), "diagnostics": [], "declarations": list(valid.declarations)})
        self.assertIsInstance(listed.diagnostics, tuple)
        self.assertIsInstance(listed.declarations, tuple)
        hash(listed)


class SchemaRuntimeCouplingStructuralTests(unittest.TestCase):
    """The closed schema enums and every branch, rebuilt from test-local constants."""

    def test_structural_closed_enums_match_runtime_constants(self) -> None:
        properties = load_schema(MIRROR_SCHEMA)["properties"]
        self.assertEqual(properties["backlog_root"]["enum"], [*hs.BACKLOG_ROOT_NAMES, None])
        row = properties["surfaces"]["items"]["properties"]
        self.assertEqual(row["surface_id"]["enum"], list(hs.SUPPORTED_SURFACES))
        self.assertEqual(row["installed_path"]["enum"], [s.installed_path for s in hs.SUPPORTED_SURFACES.values()])
        self.assertEqual(row["template"]["enum"], [s.template for s in hs.SUPPORTED_SURFACES.values()])
        self.assertEqual(row["reason_code"]["enum"], [s.code for s in hs.REASON_REGISTRY if s.surface_state])
        self.assertEqual(properties["shipment_id"], {"type": ["string", "null"], "pattern": "^[0-9]+-S$"})

    def test_structural_every_branch_equals_expected(self) -> None:
        def expected(code: str, state: str, exit_code: int) -> dict[str, Any]:
            props: dict[str, Any] = {
                "reason_code": {"const": code},
                "state": {"const": state},
                "exit_code": {"const": exit_code},
            }
            if code == "SHIPMENT_ID_INVALID":
                props["shipment_id"] = {"const": None}
            elif code not in ROOT_CODES:
                props["shipment_id"] = {"type": "string"}
            props["backlog_root"] = {"const": None} if code in ROOT_CODES else {"type": "string"}
            row_state = SURFACE_ROW_STATES.get(code)
            props["surfaces"] = {"maxItems": 0} if row_state is None else {
                "minItems": 1,
                "maxItems": 1,
                "items": {"properties": {"state": {"const": row_state}, "reason_code": {"const": code}}},
            }
            if code in READ_LIMIT_CODES:
                props["diagnostics"] = {
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {"enum": [f"read_error_code={code}"] + [f"read_stage={t}" for t in READ_STAGE_TOKENS.values()]},
                    "allOf": [
                        {"contains": {"const": f"read_error_code={code}"}, "minContains": 1, "maxContains": 1},
                        {"contains": {"pattern": "^read_stage="}, "minContains": 1, "maxContains": 1},
                    ],
                }
            else:
                props["diagnostics"] = {"not": {"contains": {"pattern": "^read_(error_code|stage)="}}}
            return {"properties": props}

        branches = load_schema(MIRROR_SCHEMA)["oneOf"]
        self.assertEqual(branches, [expected(code, state, exit_code) for code, _c, state, exit_code in parse_candidate()])


if __name__ == "__main__":
    unittest.main()
