"""Unit B, task B4a (189.001-T): observation ledger, recheck and inputs_sha256 digest.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "B4a: Observation ledger, recheck and digest".

The private helpers under test are ``harness_surfaces._observe(reader, *,
workspace_root, shipment_id)``, which runs the records and surface phases with
a ledger and then re-observes that ledger through the same reader, and
``harness_surfaces._inputs_sha256(observed, projection)``. Every fixture is a
real temporary workspace named after the test method, written with LF bytes;
no test reads the real repository surface (IM-10). Each roster test first
observes its own workspace, so in the RED phase (where the ``_observe`` stub
derived its marker suffix from the workspace directory name) each reached its
own marker ``AHLC_B4A_LEDGER_DIGEST:<test>``. ``LedgerDigestRosterTests`` is the
expected-RED roster (the golden ``inputs_sha256`` test computes the digest
through the implementation, so it belongs to it); ``test_structural_*`` tests
reach no stub and are outside it.

``ResolverFixture`` is shared with the B4b and B5 test modules. It defines no
test method, so importing it there adds no test. Its ``reads`` helper wraps
``harness_read.Reader.read_bytes`` as a call-through spy: it records each
request and may change fixture files between requests (to arrange a recheck
disagreement or a later read-limit error), and it never alters what the
reader returns. It is a test observation hook, not a resolver patch point;
that stays ``_resolve``'s ``limits`` (IM-06).
"""

from __future__ import annotations

import dataclasses
import hashlib
import shutil
import tempfile
import unittest
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest import mock

from autoharness import harness_read
from autoharness import harness_surfaces as hs
from autoharness.harness_read import ReadErrorCode, ReadLimits, TrustRoot, open_reader

MARKER = "AHLC_B4A_LEDGER_DIGEST"
SHIPMENT_ID = "7-S"
INSTALLED = ".github/skills/harness-architect/SKILL.md"
TEMPLATE = "skills/harness-architect/SKILL.md.tmpl"
TEMPLATE_TEXT = b"# {{SKILL_NAME}}\n\nRun `{{TEST_COMMAND}}`.\n"
RENDERED = b"# Harness Architect\n\nRun `make test`.\n"

SHIPMENT_RECORD = (
    b"---\nid: 7-S\nartifact_type: shipment\ncustom_fields:\n    items:\n"
    b"        - 7-F\n        - 7.001-T\n        - 7.002-T\nstatus: active\n---\n\nShipment body.\n"
)
FEATURE_RECORD = b"---\nid: 7-F\nartifact_type: feature\nlabels: []\n---\n\nFeature body.\n"
TASK_RECORDS = {
    "7.001-T": b"---\nid: 7.001-T\nartifact_type: task\nlabels:\n    - harness-surface:harness-architect\n---\n\nB.\n",
    "7.002-T": b"---\nid: 7.002-T\nartifact_type: task\nlabels:\n    - harness-surface:none\n---\n\nC.\n",
}


def manifest_bytes(checksum: str | None = None, extra: bytes = b"") -> bytes:
    checksum = hashlib.sha256(RENDERED).hexdigest() if checksum is None else checksum
    return (
        b"schema_version: 1.0.0\nvariables_used:\n  SKILL_NAME: Harness Architect\n"
        b"  TEST_COMMAND: make test\nartifacts:\n  - path: " + INSTALLED.encode()
        + b"\n    template: " + TEMPLATE.encode() + b"\n    checksum: '" + checksum.encode() + b"'\n" + extra
    )


# Read order of the default fixture (first pass): both candidates of the
# shipment and of each member (queue, then archive), then the manifest, the
# template and the installed file. The recheck repeats the same order.
DEFAULT_READS: tuple[tuple[str, TrustRoot, str], ...] = (
    ("SHIPMENT_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/queue/7-S.md"),
    ("SHIPMENT_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/archive/7-S.md"),
    ("MEMBER_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/queue/7-F.md"),
    ("MEMBER_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/archive/7-F.md"),
    ("MEMBER_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/queue/7.001-T.md"),
    ("MEMBER_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/archive/7.001-T.md"),
    ("MEMBER_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/queue/7.002-T.md"),
    ("MEMBER_CANDIDATE", TrustRoot.WORKSPACE, ".backlogit/archive/7.002-T.md"),
    ("MANIFEST", TrustRoot.AUTOHARNESS, "harness-manifest.yaml"),
    ("TEMPLATE", TrustRoot.WORKSPACE, "templates/" + TEMPLATE),
    ("INSTALLED", TrustRoot.WORKSPACE, INSTALLED),
)

# The golden fixture's digest, with GOLDEN_PROJECTION as the result projection.
GOLDEN_PROJECTION: dict[str, Any] = {
    "schema_version": "1.0.0",
    "state": "HARNESS_READY",
    "reason_code": "ALL_SURFACES_PRESENT",
    "exit_code": 0,
    "shipment_id": "7-S",
    "backlog_root": ".backlogit",
    "surfaces": [
        {
            "surface_id": "harness-architect",
            "installed_path": INSTALLED,
            "template": TEMPLATE,
            "state": "PRESENT",
            "reason_code": "ALL_SURFACES_PRESENT",
        }
    ],
    "declarations": [
        {"member_id": "7.001-T", "surface_id": "harness-architect"},
        {"member_id": "7.002-T", "surface_id": "none"},
    ],
    "diagnostics": [],
}
GOLDEN_INPUTS_SHA256 = "37671c73e26cb3963be3b5c33e9d254f894e519e12d32e8e829c9bdaa4dd8606"


class ResolverFixture(unittest.TestCase):
    """A complete temporary workspace named after the running test (no test methods)."""

    def setUp(self) -> None:
        self.scratch = Path(tempfile.mkdtemp(prefix="ahlc-b4-"))
        self.addCleanup(shutil.rmtree, self.scratch, True)
        self.ws = self.scratch / self._testMethodName
        self.build(self.ws)

    def build(self, ws: Path) -> None:
        for folder in ("queue", "archive"):
            (ws / ".backlogit" / folder).mkdir(parents=True)
        (ws / ".autoharness").mkdir()
        self.write_record("7-S", SHIPMENT_RECORD, ws=ws)
        self.write_record("7-F", FEATURE_RECORD, ws=ws)
        for item_id, data in TASK_RECORDS.items():
            self.write_record(item_id, data, ws=ws)
        (ws / ".autoharness" / "harness-manifest.yaml").write_bytes(manifest_bytes())
        template = ws / "templates" / TEMPLATE
        template.parent.mkdir(parents=True)
        template.write_bytes(TEMPLATE_TEXT)
        installed = ws / INSTALLED
        installed.parent.mkdir(parents=True)
        installed.write_bytes(RENDERED)

    def fresh(self, name: str) -> Path:
        """Build another complete workspace under the scratch directory."""
        ws = self.scratch / name
        self.build(ws)
        return ws

    def fresh(self, name: str) -> Path:
        """Build another complete workspace under the scratch directory."""
        ws = self.scratch / name
        self.build(ws)
        return ws

    def path(self, relative: str, ws: Path | None = None) -> Path:
        return (self.ws if ws is None else ws) / relative

    def record_path(self, item_id: str, folder: str = "queue", ws: Path | None = None) -> Path:
        return self.path(f".backlogit/{folder}/{item_id}.md", ws)

    def write_record(self, item_id: str, data: bytes, folder: str = "queue", ws: Path | None = None) -> Path:
        path = self.record_path(item_id, folder, ws)
        path.write_bytes(data)
        return path

    def task_record(self, item_id: str, *labels: str) -> bytes:
        lines = "".join(f"    - {label}\n" for label in labels)
        return f"---\nid: {item_id}\nartifact_type: task\nlabels:\n{lines}---\n\nT.\n".encode()

    def shipment_record(self, *items: str, shipment_id: str = SHIPMENT_ID) -> bytes:
        lines = "".join(f"        - {item}\n" for item in items)
        return (
            f"---\nid: {shipment_id}\nartifact_type: shipment\ncustom_fields:\n    items:\n{lines}---\n\nS.\n"
        ).encode()

    def observe(
        self, shipment_id: Any = SHIPMENT_ID, limits: ReadLimits | None = None, ws: Path | None = None
    ) -> tuple[Any, Any]:
        ws = self.ws if ws is None else ws
        reader = open_reader(workspace_root=ws, limits=limits)
        return hs._observe(reader, workspace_root=ws, shipment_id=shipment_id), reader

    @contextmanager
    def reads(self, actions: dict[int, Callable[[], None]] | None = None) -> Iterator[list[Any]]:
        """Record every reader request; after the n-th (1-based) request run ``actions[n]``.

        Each record is ``(root, relative_path, error, usage after the request)``.
        """
        calls: list[Any] = []
        original = harness_read.Reader.read_bytes

        def wrapper(reader: Any, root: TrustRoot, relative_path: str) -> Any:
            result = original(reader, root, relative_path)
            calls.append((root, relative_path, result.error, reader.usage))
            action = (actions or {}).get(len(calls))
            if action is not None:
                action()
            return result

        with mock.patch.object(harness_read.Reader, "read_bytes", wrapper):
            yield calls

    def replace_with_directory(self, path: Path) -> Callable[[], None]:
        def action() -> None:
            path.unlink()
            path.mkdir()

        return action

    def overwrite(self, path: Path, data: bytes) -> Callable[[], None]:
        return lambda: path.write_bytes(data)


def outcome(entry: Any) -> tuple[bytes | None, ReadErrorCode | None]:
    return entry.data, entry.error


class LedgerDigestRosterTests(ResolverFixture):
    """Expected-RED roster: ledger, recheck and digest behavior (B4a)."""

    def test_ledger_records_every_candidate_and_surface_read(self) -> None:
        observed, _reader = self.observe()
        ledger = observed.ledger
        self.assertEqual(
            [(entry.stage.name, entry.root, entry.path) for entry in ledger], list(DEFAULT_READS)
        )
        # Stable absence is ledgered: every archive candidate is PATH_NOT_FOUND with no data.
        for entry in ledger[1:8:2]:
            self.assertEqual(outcome(entry), (None, ReadErrorCode.PATH_NOT_FOUND))
        self.assertEqual(outcome(ledger[0]), (SHIPMENT_RECORD, None))
        self.assertEqual(outcome(ledger[4]), (TASK_RECORDS["7.001-T"], None))
        self.assertEqual(outcome(ledger[8]), (manifest_bytes(), None))
        self.assertEqual(outcome(ledger[9]), (TEMPLATE_TEXT, None))
        self.assertEqual(outcome(ledger[10]), (RENDERED, None))
        self.assertEqual([entry.surface_id for entry in ledger[:9]], [None] * 9)
        self.assertEqual([entry.surface_id for entry in ledger[9:]], ["harness-architect"] * 2)
        self.assertEqual(observed.records.reason_code, None)
        self.assertEqual(observed.classification.reason_code, "ALL_SURFACES_PRESENT")

    def test_recheck_reobserves_the_ledger_with_new_claims(self) -> None:
        with self.reads() as calls:
            observed, reader = self.observe()
        recheck = observed.recheck
        self.assertIsNotNone(recheck)
        # FI-3: C(N=3, U=1, rho=1) = 4(N+1) + 3U(1+rho) = 22 file claims.
        self.assertEqual(reader.usage.files_claimed, 22)
        self.assertEqual([(root, path) for root, path, _e, _u in calls],
                         [(root, path) for _s, root, path in DEFAULT_READS] * 2)
        self.assertEqual([entry.index for entry in recheck.entries], list(range(11)))
        self.assertEqual(
            [entry.stage for entry in recheck.entries],
            [hs.ReadStage.CANDIDATE_RECHECK] * 8 + [hs.ReadStage.SURFACE_RECHECK] * 3,
        )
        for first, again in zip(observed.ledger, recheck.entries):
            self.assertEqual(outcome(first), outcome(again))
        self.assertEqual(recheck.facts, ())
        self.assertEqual(recheck.surface_codes, ())
        self.assertIsNone(recheck.read_limit)
        self.assertIsNone(recheck.changed_stage)
        self.assertEqual(hs._reduce(observed).reason_code, "ALL_SURFACES_PRESENT")

    def test_mutated_record_between_read_and_recheck_is_input_changed(self) -> None:
        changed = TASK_RECORDS["7.001-T"].replace(b"B.", b"B changed.")
        with self.reads({11: self.overwrite(self.record_path("7.001-T"), changed)}):
            observed, _reader = self.observe()
        recheck = observed.recheck
        self.assertEqual(hs._reduce(observed).reason_code, "INPUT_CHANGED_DURING_RESOLUTION")
        self.assertEqual(recheck.facts, ())
        self.assertEqual(recheck.changed_stage, hs.ReadStage.CANDIDATE_RECHECK)
        # Both observations are bound: the ledger keeps the first, the recheck the second.
        self.assertEqual(observed.ledger[4].data, TASK_RECORDS["7.001-T"])
        self.assertEqual(recheck.entries[4].data, changed)

    def test_mutated_surface_between_read_and_recheck_is_input_changed(self) -> None:
        with self.reads({11: self.overwrite(self.path(INSTALLED), RENDERED + b"x")}):
            observed, _reader = self.observe()
        self.assertEqual(observed.classification.reason_code, "ALL_SURFACES_PRESENT")
        self.assertEqual(hs._reduce(observed).reason_code, "INPUT_CHANGED_DURING_RESOLUTION")
        self.assertEqual(observed.recheck.changed_stage, hs.ReadStage.SURFACE_RECHECK)
        self.assertEqual(observed.recheck.entries[10].data, RENDERED + b"x")

    def test_absent_candidate_appearing_before_recheck_is_input_changed(self) -> None:
        appear = self.overwrite(self.record_path("7-S", "archive"), SHIPMENT_RECORD)
        with self.reads({11: appear}):
            observed, _reader = self.observe()
        self.assertEqual(outcome(observed.ledger[1]), (None, ReadErrorCode.PATH_NOT_FOUND))
        self.assertEqual(outcome(observed.recheck.entries[1]), (SHIPMENT_RECORD, None))
        self.assertEqual(observed.recheck.changed_stage, hs.ReadStage.CANDIDATE_RECHECK)
        self.assertEqual(hs._reduce(observed).reason_code, "INPUT_CHANGED_DURING_RESOLUTION")

    def test_recheck_not_completed_maps_to_the_original_stage_code(self) -> None:
        # A recheck read that ends in a non-limit, non-absence error has not
        # completed: it gives the original stage's code and is never agreement.
        actions = {
            11: lambda: (
                self.replace_with_directory(self.record_path("7.002-T"))(),
                self.replace_with_directory(self.path("templates/" + TEMPLATE))(),
            )
        }
        with self.reads(actions):
            observed, _reader = self.observe()
        recheck = observed.recheck
        self.assertIsNone(recheck.changed_stage)
        self.assertEqual(recheck.facts, ("MEMBER_RECORD_INVALID",))
        self.assertEqual(recheck.surface_codes, (("harness-architect", "TEMPLATE_UNREADABLE"),))
        self.assertEqual(recheck.entries[6].error, ReadErrorCode.NOT_REGULAR_FILE)
        self.assertEqual(hs._reduce(observed).reason_code, "MEMBER_RECORD_INVALID")

    def test_recheck_not_completed_manifest_is_manifest_unreadable(self) -> None:
        manifest = self.path(".autoharness/harness-manifest.yaml")
        with self.reads({11: self.replace_with_directory(manifest)}):
            observed, _reader = self.observe()
        self.assertEqual(observed.recheck.facts, ("MANIFEST_UNREADABLE",))
        self.assertIsNone(observed.recheck.changed_stage)

    def test_digest_is_lowercase_hex_and_stable_across_runs_and_locations(self) -> None:
        observed, _reader = self.observe()
        digest = hs._inputs_sha256(observed, GOLDEN_PROJECTION)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        again, _reader = self.observe()
        self.assertEqual(hs._inputs_sha256(again, GOLDEN_PROJECTION), digest)
        # No absolute path is bound: the same LF bytes elsewhere give the same digest.
        other = self.scratch / "elsewhere" / "nested-copy"
        other.parent.mkdir()
        self.build(other)
        moved, _reader = self.observe(ws=other)
        self.assertEqual(hs._inputs_sha256(moved, GOLDEN_PROJECTION), digest)

    def test_digest_golden_fixture(self) -> None:
        observed, _reader = self.observe()
        self.assertEqual(hs._inputs_sha256(observed, GOLDEN_PROJECTION), GOLDEN_INPUTS_SHA256)

    def test_every_bound_input_changes_the_digest(self) -> None:
        observed, _reader = self.observe()
        base = hs._inputs_sha256(observed, GOLDEN_PROJECTION)
        variants: dict[str, str] = {}

        def digest(**changes: Any) -> str:
            return hs._inputs_sha256(dataclasses.replace(observed, **changes), GOLDEN_PROJECTION)

        def outcomes(entry: Any) -> list[tuple[str, dict[str, Any]]]:
            if entry.data is None:
                return [("present-empty", {"data": b"", "error": None}), ("error", {"error": ReadErrorCode.IO})]
            return [("data", {"data": entry.data + b"!"}), ("absent", {"data": None, "error": ReadErrorCode.PATH_NOT_FOUND})]

        other_stage = {True: hs.ReadStage.INSTALLED, False: hs.ReadStage.TEMPLATE}
        for index, entry in enumerate(observed.ledger):
            changes: list[tuple[str, dict[str, Any]]] = [
                ("stage", {"stage": other_stage[entry.stage is hs.ReadStage.TEMPLATE]}),
                ("root", {"root": TrustRoot.AUTOHARNESS if entry.root is TrustRoot.WORKSPACE else TrustRoot.WORKSPACE}),
                ("path", {"path": entry.path + "x"}),
                ("surface", {"surface_id": None if entry.surface_id else "harness-architect"}),
                *outcomes(entry),
            ]
            for name, change in changes:
                ledger = list(observed.ledger)
                ledger[index] = dataclasses.replace(entry, **change)
                variants[f"ledger[{index}].{name}"] = digest(ledger=tuple(ledger))
        for index, entry in enumerate(observed.recheck.entries):
            changes = [
                ("stage", {"stage": hs.ReadStage.SURFACE_RECHECK if entry.stage is hs.ReadStage.CANDIDATE_RECHECK
                           else hs.ReadStage.CANDIDATE_RECHECK}),
                ("index", {"index": entry.index + 100}),
                *outcomes(entry),
            ]
            for name, change in changes:
                entries = list(observed.recheck.entries)
                entries[index] = dataclasses.replace(entry, **change)
                variants[f"recheck[{index}].{name}"] = digest(
                    recheck=dataclasses.replace(observed.recheck, entries=tuple(entries))
                )
        variants["request"] = digest(shipment_id="8-S")
        variants["request-type"] = digest(shipment_id=7)
        variants["recheck-not-run"] = digest(recheck=None)
        variants["ledger-entry-dropped"] = digest(ledger=observed.ledger[:-1])
        declarations = observed.records.declarations
        variants["declarations"] = digest(
            records=dataclasses.replace(observed.records, declarations=declarations[:1])
        )
        variants["declaration-surface"] = digest(
            records=dataclasses.replace(
                observed.records,
                declarations=(declarations[0], dataclasses.replace(declarations[1], surface_id="harness-architect")),
            )
        )
        for key in GOLDEN_PROJECTION:
            projection = dict(GOLDEN_PROJECTION)
            projection[key] = None if GOLDEN_PROJECTION[key] is not None else "x"
            variants[f"projection.{key}"] = hs._inputs_sha256(observed, projection)
        self.assertEqual([name for name, value in variants.items() if value == base], [])
        self.assertEqual(len(set(variants.values())), len(variants))

    def test_digest_binds_first_and_recheck_observations_on_mutation(self) -> None:
        def run(first: bytes, recheck: bytes) -> str:
            path = self.record_path("7.001-T")
            path.write_bytes(first)
            with self.reads({11: self.overwrite(path, recheck)}):
                observed, _reader = self.observe()
            self.assertEqual(observed.recheck.changed_stage, hs.ReadStage.CANDIDATE_RECHECK)
            return hs._inputs_sha256(observed, GOLDEN_PROJECTION)

        original = TASK_RECORDS["7.001-T"]
        x, y, z = original, original.replace(b"B.", b"Y."), original.replace(b"B.", b"Z.")
        w = original.replace(b"B.", b"W.")
        digests = {run(x, y), run(x, z), run(w, y)}
        self.assertEqual(len(digests), 3)

    def test_digest_preimage_is_domain_separated_and_length_framed(self) -> None:
        observed, _reader = self.observe()
        preimage = hs._digest_preimage(observed, GOLDEN_PROJECTION)
        self.assertTrue(preimage.startswith(len(hs._DIGEST_DOMAIN).to_bytes(8, "big") + hs._DIGEST_DOMAIN))
        self.assertEqual(hs._inputs_sha256(observed, GOLDEN_PROJECTION), hashlib.sha256(preimage).hexdigest())
        # Moving a byte across a field boundary changes the digest (fields are framed).
        entry = observed.ledger[0]
        left = dataclasses.replace(entry, path=entry.path + "a", data=b"b" + entry.data)
        right = dataclasses.replace(entry, path=entry.path + "ab", data=entry.data)
        digests = {
            hs._inputs_sha256(dataclasses.replace(observed, ledger=(left,) + observed.ledger[1:]), GOLDEN_PROJECTION),
            hs._inputs_sha256(dataclasses.replace(observed, ledger=(right,) + observed.ledger[1:]), GOLDEN_PROJECTION),
        }
        self.assertEqual(len(digests), 2)
        with self.assertRaises(ValueError):
            hs._inputs_sha256(observed, {**GOLDEN_PROJECTION, "inputs_sha256": "0" * 64})

    def test_empty_ledger_recheck_reads_nothing(self) -> None:
        shutil.rmtree(self.ws / ".backlogit")
        observed, reader = self.observe()
        self.assertEqual(observed.ledger, ())
        self.assertEqual(observed.recheck.entries, ())
        self.assertEqual(reader.usage.files_claimed, 0)
        self.assertEqual(observed.records.reason_code, "BACKLOG_ROOT_NOT_FOUND")
        # The surface union is empty: the surface phase reads nothing.
        self.assertEqual(observed.classification.rows, ())
        self.assertIsNone(observed.classification.reason_code)


class LedgerDigestStructuralTests(unittest.TestCase):
    def test_structural_roster_markers_pairwise_distinct(self) -> None:
        names = [name for name in dir(LedgerDigestRosterTests) if name.startswith("test_")]
        markers = [f"{MARKER}:{name}" for name in names]
        self.assertEqual(len(names), 13)
        self.assertEqual(len(set(markers)), len(markers))
        self.assertFalse(any(name.startswith("test_structural_") for name in names))
        self.assertEqual([name for name in dir(ResolverFixture) if name.startswith("test")], [])

    def test_structural_fixture_bytes_are_lf_only(self) -> None:
        for data in (SHIPMENT_RECORD, FEATURE_RECORD, *TASK_RECORDS.values(), manifest_bytes(), TEMPLATE_TEXT, RENDERED):
            self.assertNotIn(b"\r", data)
        for _stage, _root, path in DEFAULT_READS:
            self.assertNotIn("\\", path)


if __name__ == "__main__":
    unittest.main()
