"""Unit B, task B4b (189.002-T): reducer, FI-5 early return and resolver entry.

Governing plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
(blob b7a77c76), section "B4b: Reducer, early return and resolver entry".

The entry under test is ``harness_surfaces.resolve_shipment(*, workspace_root,
shipment_id)`` and the private ``_resolve(*, workspace_root, shipment_id,
limits)``, whose ``limits`` is the only B patch point (IM-06). The IM-16 and
IM-04 tests call ``_resolve`` with small ``ReadLimits`` so every read-limit
code is reachable. Every fixture is a real temporary workspace
(``ResolverFixture``, shared with the B4a module); no test reads the real
repository surface (IM-10). Every roster test resolves its own workspace
first, so in the RED phase (where the ``_resolve`` stub derived its marker
suffix from the workspace directory name) each reached its own marker
``AHLC_B4B_REDUCER_EARLY_RETURN:<test>``. ``ReducerRosterTests`` is the
expected-RED roster. ``ReducerPrecedenceCharacterizationTests`` (added by the
195-S local review over the green reducer) and the ``test_structural_*``
tests (the API signatures and the roster check) are outside it.
"""

from __future__ import annotations

import dataclasses
import inspect
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any
from unittest import mock

from test_harness_surfaces_digest import (
    DEFAULT_READS,
    INSTALLED,
    RENDERED,
    SHIPMENT_ID,
    SHIPMENT_RECORD,
    TEMPLATE,
    ResolverFixture,
)

from autoharness import harness_surfaces as hs
from autoharness.harness_read import ReadErrorCode, ReadLimits, ReadUsage, TrustRoot, open_reader

MARKER = "AHLC_B4B_REDUCER_EARLY_RETURN"
LIMIT_CODES = (ReadErrorCode.FILE_COUNT_LIMIT, ReadErrorCode.TOTAL_SIZE_LIMIT, ReadErrorCode.FILE_SIZE_LIMIT)
FIRST_PASS = len(DEFAULT_READS)  # 11 reads, then the recheck repeats them (22 in all).

# The 1-based request at which each ReadStage first occurs in the default fixture.
STAGE_READ: dict[hs.ReadStage, int] = {
    hs.ReadStage.SHIPMENT_CANDIDATE: 1,
    hs.ReadStage.MEMBER_CANDIDATE: 3,
    hs.ReadStage.MANIFEST: 9,
    hs.ReadStage.TEMPLATE: 10,
    hs.ReadStage.INSTALLED: 11,
    hs.ReadStage.CANDIDATE_RECHECK: 12,
    hs.ReadStage.SURFACE_RECHECK: 20,
}

# IM-16 (b) infeasible sub-cases, with the reason and the limits that would
# otherwise raise the code; the roster runs each one.
INFEASIBLE: dict[tuple[str, str], tuple[str, ReadLimits]] = {
    ("FILE_SIZE_LIMIT", "absent candidate"): (
        "a missing candidate is PATH_NOT_FOUND before any size check or reservation",
        ReadLimits(max_file_bytes=0),
    ),
    ("TOTAL_SIZE_LIMIT", "absent candidate"): (
        "a missing candidate is PATH_NOT_FOUND before any size check or reservation",
        ReadLimits(max_total_bytes=0),
    ),
}

# Byte sizes for the size-limit arrangements: every default fixture file is
# smaller than SMALL_FILE_BOUND; a target padded to GROWN_FILE exceeds it.
SMALL_FILE_BOUND = 4 * 1024
GROWN_FILE = 2 * SMALL_FILE_BOUND
TOTAL_HEADROOM = 32 * 1024  # fits every recheck read before the grown file
GROWN_PAST_HEADROOM = 2 * TOTAL_HEADROOM


class ReducerFixture(ResolverFixture):
    def resolve(self, limits: ReadLimits | None = None, ws: Path | None = None, shipment_id: Any = SHIPMENT_ID) -> Any:
        return hs._resolve(
            workspace_root=self.ws if ws is None else ws,
            shipment_id=shipment_id,
            limits=ReadLimits() if limits is None else limits,
        )

    def assert_baseline(self) -> None:
        """Resolve the test's own workspace first (in RED this reaches the test's marker)."""
        result, usage = self.resolve()
        self.assertEqual(result.reason_code, "ALL_SURFACES_PRESENT")
        self.assertEqual(usage.files_claimed, 22)

    def file_for(self, ws: Path, read_index: int) -> Path:
        """The file behind the ``read_index``-th (1-based) request of the default fixture."""
        _stage, root, relative = DEFAULT_READS[(read_index - 1) % FIRST_PASS]
        return ws / (".autoharness/" + relative if root is TrustRoot.AUTOHARNESS else relative)

    def sizes(self, ws: Path) -> list[int]:
        out = []
        for index in range(1, FIRST_PASS + 1):
            path = self.file_for(ws, index)
            out.append(path.stat().st_size if path.is_file() else 0)
        return out

    def pad(self, path: Path, to: int) -> None:
        """Append filler so ``path`` holds ``to`` bytes: LF, filler, LF (``#`` keeps YAML a comment)."""
        data = path.read_bytes()
        filler = b"#" if path.name.endswith(".yaml") else b"x"
        path.write_bytes(data + b"\n" + filler * max(0, to - len(data) - 2) + b"\n")

    def assert_limit(self, result: Any, code: ReadErrorCode, stage: hs.ReadStage) -> None:
        self.assertEqual(result.reason_code, code.value)
        self.assertEqual((result.state, result.exit_code), (hs.ResolutionState.UNRESOLVED, 2))
        self.assertEqual(result.diagnostics, (f"read_error_code={code.value}", f"read_stage={stage.value}"))
        self.assertEqual(result.surfaces, ())

    def assert_stopped(self, calls: list[Any], usage: ReadUsage, code: ReadErrorCode, at: int) -> None:
        """The ``at``-th request returned ``code`` and no request followed it (FI-5)."""
        self.assertEqual(len(calls), at)
        self.assertEqual(calls[-1][2], code)
        self.assertEqual(usage.files_claimed, calls[-1][3].files_claimed)
        self.assertEqual(usage.files_claimed, at - 1 if code is ReadErrorCode.FILE_COUNT_LIMIT else at)

    def limits_for(self, code: ReadErrorCode, ws: Path, at: int, target: Path) -> ReadLimits:
        """Limits under which request ``at`` (1-based) is the first to fail with ``code``.

        For ``FILE_SIZE_LIMIT`` at a first-pass request the target is padded
        past the bound here; at a recheck request the caller grows it after the
        first pass (:meth:`grow_then`).
        """
        if code is ReadErrorCode.FILE_COUNT_LIMIT:
            return ReadLimits(max_files=at - 1)
        if code is ReadErrorCode.TOTAL_SIZE_LIMIT:
            sizes = self.sizes(ws)
            before = sum(sizes[(index - 1) % FIRST_PASS] for index in range(1, at))
            return ReadLimits(max_total_bytes=before + sizes[(at - 1) % FIRST_PASS] - 1)
        if at <= FIRST_PASS:
            self.pad(target, GROWN_FILE)
        return ReadLimits(max_file_bytes=SMALL_FILE_BOUND)

    def grow_then(self, target: Path, code: ReadErrorCode, then: Callable[[], None]) -> Callable[[], None]:
        """After the first pass: grow ``target`` past the file bound (``FILE_SIZE_LIMIT`` only), then ``then``."""

        def action() -> None:
            if code is ReadErrorCode.FILE_SIZE_LIMIT:
                self.pad(target, GROWN_FILE)
            then()

        return action


class ReducerRosterTests(ReducerFixture):
    """Expected-RED roster: reducer, early return and the resolver entry (B4b)."""

    def test_resolve_returns_the_result_and_the_reader_usage(self) -> None:
        result, usage = self.resolve()
        self.assertEqual(result.reason_code, "ALL_SURFACES_PRESENT")
        self.assertEqual((result.state, result.exit_code), (hs.ResolutionState.HARNESS_READY, 0))
        self.assertEqual(usage.files_claimed, 22)
        self.assertEqual(usage.bytes_reserved, 2 * sum(self.sizes(self.ws)))
        self.assertEqual(
            result.surfaces,
            (hs.SurfaceRow("harness-architect", INSTALLED, TEMPLATE, hs.SurfaceState.PRESENT, "ALL_SURFACES_PRESENT"),),
        )
        self.assertEqual(
            result.declarations,
            (hs.Declaration("7.001-T", "harness-architect"), hs.Declaration("7.002-T", "none")),
        )
        self.assertEqual((result.shipment_id, result.backlog_root, result.diagnostics), ("7-S", ".backlogit", ()))
        # inputs_sha256 is the B4a digest over this resolution and its own projection.
        observed = hs._observe(open_reader(workspace_root=self.ws), workspace_root=self.ws, shipment_id=SHIPMENT_ID)
        projection = result.to_document()
        del projection["inputs_sha256"]
        self.assertEqual(result.inputs_sha256, hs._inputs_sha256(observed, projection))
        self.assertEqual(hs.resolve_shipment(workspace_root=self.ws, shipment_id=SHIPMENT_ID), result)

    def test_resolve_shipment_calls_resolve_with_the_fi2_defaults(self) -> None:
        with mock.patch.object(hs, "_resolve", wraps=hs._resolve) as spy:
            result = hs.resolve_shipment(workspace_root=self.ws, shipment_id=SHIPMENT_ID)
        spy.assert_called_once_with(
            workspace_root=self.ws,
            shipment_id=SHIPMENT_ID,
            limits=ReadLimits(max_files=256, max_file_bytes=4 * 1024 * 1024, max_total_bytes=32 * 1024 * 1024),
        )
        self.assertIsInstance(result, hs.ResolutionResult)

    def test_no_surfaces_required_reads_no_surface(self) -> None:
        self.assert_baseline()
        self.write_record("7.001-T", self.task_record("7.001-T", "harness-surface:none"))
        with self.reads() as calls:
            result, usage = self.resolve()
        self.assertEqual(result.reason_code, "NO_SURFACES_REQUIRED")
        self.assertEqual((result.state, result.exit_code), (hs.ResolutionState.HARNESS_READY, 0))
        self.assertEqual(usage.files_claimed, 16)  # 4(N+1), no surface read
        self.assertFalse(any(root is TrustRoot.AUTOHARNESS for root, *_rest in calls))

    def test_higher_class_beats_lower_class_without_short_circuit(self) -> None:
        self.assert_baseline()
        # Class 2 over class 3: the class 3 fact comes first in encounter and task-ID order.
        ws = self.fresh("c2-over-c3")
        self.write_record("7.001-T", self.task_record("7.001-T"), ws=ws)
        self.record_path("7.002-T", ws=ws).unlink()
        observed = hs._observe(open_reader(workspace_root=ws), workspace_root=ws, shipment_id=SHIPMENT_ID)
        self.assertEqual(observed.records.facts, ("DECLARATION_MISSING", "MEMBER_NOT_FOUND"))
        self.assertEqual(self.resolve(ws=ws)[0].reason_code, "MEMBER_NOT_FOUND")
        # Class 3 over class 7: the surface phase still runs (facts are not short-circuited).
        ws = self.fresh("c3-over-c7")
        self.write_record("7.002-T", self.task_record("7.002-T", "harness-surface:Bad"), ws=ws)
        self.path(INSTALLED, ws).unlink()
        observed = hs._observe(open_reader(workspace_root=ws), workspace_root=ws, shipment_id=SHIPMENT_ID)
        self.assertEqual(observed.classification.reason_code, "INSTALLED_NOT_FOUND")
        result, usage = self.resolve(ws=ws)
        self.assertEqual(result.reason_code, "DECLARATION_MALFORMED")
        self.assertEqual(usage.files_claimed, 22)
        self.assertEqual(result.surfaces, ())
        # Class 3 over class 4: one task declares none, the other declares nothing.
        ws = self.fresh("c3-over-c4")
        self.write_record("7.001-T", self.task_record("7.001-T"), ws=ws)
        self.assertEqual(self.resolve(ws=ws)[0].reason_code, "DECLARATION_MISSING")
        # Lower classes met in the first pass, a higher-class code met later, in the recheck.
        cases = (
            ("c2-recheck-over-c8", "7.001-T", "MEMBER_RECORD_INVALID"),
            ("c5-recheck-over-c8", "manifest", "MANIFEST_UNREADABLE"),
            ("c6-recheck-over-c8", "template", "TEMPLATE_UNREADABLE"),
        )
        for name, target, code in cases:
            with self.subTest(case=name):
                ws = self.fresh(name)
                path = {
                    "7.001-T": self.record_path("7.001-T", ws=ws),
                    "manifest": self.path(".autoharness/harness-manifest.yaml", ws),
                    "template": self.path("templates/" + TEMPLATE, ws),
                }[target]
                with self.reads({FIRST_PASS: self.replace_with_directory(path)}):
                    result, _usage = self.resolve(ws=ws)
                self.assertEqual(result.reason_code, code)
                if code == "TEMPLATE_UNREADABLE":
                    self.assertEqual(result.surfaces[0].state, hs.SurfaceState.INVALID)
                else:
                    self.assertEqual(result.surfaces, ())
        # Class 6 over class 7: CHECKSUM_MISMATCH in the first pass, then a template recheck that does not complete.
        ws = self.fresh("c6-recheck-over-c7")
        self.path(INSTALLED, ws).write_bytes(RENDERED + b"stale\n")
        with self.reads({FIRST_PASS: self.replace_with_directory(self.path("templates/" + TEMPLATE, ws))}):
            result, _usage = self.resolve(ws=ws)
        self.assertEqual(result.reason_code, "TEMPLATE_UNREADABLE")

    def test_class_1_and_1b_beat_every_lower_class(self) -> None:
        self.assert_baseline()
        lower: dict[str, Callable[[Path], object]] = {
            "c2": lambda ws: self.record_path("7.002-T", ws=ws).unlink(),  # MEMBER_NOT_FOUND
            "c3": lambda ws: self.write_record("7.002-T", self.task_record("7.002-T"), ws=ws),  # DECLARATION_MISSING
            "c4": lambda ws: self.write_record(
                "7.001-T", self.task_record("7.001-T", "harness-surface:none"), ws=ws
            ),  # NO_SURFACES_REQUIRED
            "c5": lambda ws: self.path(".autoharness/harness-manifest.yaml", ws).write_bytes(b"[\n"),
            "c6": lambda ws: self.path("templates/" + TEMPLATE, ws).write_bytes(b"{{MISSING}}\n"),
            "c7": lambda ws: self.path(INSTALLED, ws).write_bytes(RENDERED + b"stale\n"),
            "c8": lambda ws: None,  # ALL_SURFACES_PRESENT
        }
        for name, arrange in lower.items():
            with self.subTest(lower=name):
                ws = self.fresh(f"{name}-then-class-1")
                arrange(ws)
                with self.reads() as calls:
                    plain = self.resolve(ws=ws)[0].reason_code
                self.assertNotIn(plain, ("INPUT_CHANGED_DURING_RESOLUTION", *(c.value for c in LIMIT_CODES)))
                first_pass = len(calls) // 2
                shipment = self.record_path("7-S", ws=ws)
                with self.reads({first_pass: self.overwrite(shipment, SHIPMENT_RECORD + b"changed\n")}):
                    result, _usage = self.resolve(ws=ws)
                self.assertEqual(result.reason_code, "INPUT_CHANGED_DURING_RESOLUTION")
                shipment.write_bytes(SHIPMENT_RECORD)
                result, _usage = self.resolve(ws=ws, limits=ReadLimits(max_files=first_pass))
                self.assert_limit(result, ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.CANDIDATE_RECHECK)

    def test_im16_a_completed_disagreement_before_a_read_limit_is_input_changed(self) -> None:
        self.assert_baseline()
        cases = (
            # A completed disagreeing ledger (candidate) recheck: the absent archive
            # candidate of 7-S appears, seen at request 13; the limit hits at 14.
            ("ledger", ".backlogit/archive/7-S.md", lambda path: path.write_bytes(b"x"), 13),
            # A completed disagreeing surface (manifest) recheck at request 20; the limit hits at 21.
            (
                "surface",
                ".autoharness/harness-manifest.yaml",
                lambda path: path.write_bytes(path.read_bytes() + b"# changed\n"),
                20,
            ),
        )
        for name, relative, mutate, disagree_at in cases:
            for code in LIMIT_CODES:
                with self.subTest(case=name, code=code.value):
                    ws = self.fresh(f"im16a-{name}-{code.value}")
                    target, next_path = ws / relative, self.file_for(ws, disagree_at + 1)
                    self.assertTrue(next_path.is_file())
                    limits, grow_to = {
                        ReadErrorCode.FILE_COUNT_LIMIT: (ReadLimits(max_files=disagree_at), 0),
                        ReadErrorCode.FILE_SIZE_LIMIT: (ReadLimits(max_file_bytes=SMALL_FILE_BOUND), GROWN_FILE),
                        ReadErrorCode.TOTAL_SIZE_LIMIT: (
                            ReadLimits(max_total_bytes=sum(self.sizes(ws)) + TOTAL_HEADROOM),
                            GROWN_PAST_HEADROOM,
                        ),
                    }[code]

                    def action(
                        target: Path = target,
                        next_path: Path = next_path,
                        grow_to: int = grow_to,
                        mutate: Callable[[Path], object] = mutate,
                    ) -> None:
                        mutate(target)
                        if grow_to:
                            self.pad(next_path, grow_to)

                    with self.reads({FIRST_PASS: action}) as calls:
                        result, usage = self.resolve(ws=ws, limits=limits)
                    self.assertEqual(result.reason_code, "INPUT_CHANGED_DURING_RESOLUTION")
                    self.assertEqual(result.diagnostics, ())
                    self.assertIsNone(calls[disagree_at - 1][2])  # the disagreeing recheck completed
                    self.assert_stopped(calls, usage, code, disagree_at + 1)

    def test_im16_b_read_limit_first_gives_that_code_and_stops(self) -> None:
        self.assert_baseline()
        for code in LIMIT_CODES:
            for stage, at in STAGE_READ.items():
                with self.subTest(code=code.value, stage=stage.name):
                    ws = self.fresh(f"im16b-{code.value}-{stage.name}")
                    target = self.file_for(ws, at)
                    limits = self.limits_for(code, ws, at, target)
                    # A later recheck is arranged to disagree: right after the error (or,
                    # for a recheck stage, right after the first pass) a ledgered file
                    # changes, which only a further recheck request would see.
                    if at <= FIRST_PASS:
                        shipment = self.record_path("7-S", ws=ws)
                        actions = {at: self.overwrite(shipment, SHIPMENT_RECORD + b"changed\n")}
                    else:
                        installed = self.overwrite(self.path(INSTALLED, ws), RENDERED + b"changed\n")
                        actions = {FIRST_PASS: self.grow_then(target, code, installed)}
                    with self.reads(actions) as calls:
                        result, usage = self.resolve(ws=ws, limits=limits)
                    self.assert_limit(result, code, stage)
                    self.assert_stopped(calls, usage, code, at)
        # Infeasible sub-cases: byte codes at an absent candidate.
        ws = self.fresh("im16b-absent")
        self.record_path("7-S", ws=ws).rename(self.record_path("7-S", "archive", ws=ws))
        for (code, _case), (_reason, limits) in INFEASIBLE.items():
            with self.subTest(infeasible=code):
                with self.reads() as calls:
                    result, _usage = self.resolve(ws=ws, limits=limits)
                # The absent queue candidate is PATH_NOT_FOUND; the present archive candidate hits the limit.
                self.assertEqual(calls[0][2], ReadErrorCode.PATH_NOT_FOUND)
                self.assert_limit(result, ReadErrorCode(code), hs.ReadStage.SHIPMENT_CANDIDATE)
                self.assertEqual(len(calls), 2)

    def test_im04_read_limit_injection_at_each_read_stage(self) -> None:
        self.assert_baseline()
        matrix = {}
        for stage, at in STAGE_READ.items():
            ws = self.fresh(f"im04-{stage.name}")
            with self.reads() as calls:
                result, usage = self.resolve(ws=ws, limits=ReadLimits(max_files=at - 1))
            self.assert_limit(result, ReadErrorCode.FILE_COUNT_LIMIT, stage)
            self.assert_stopped(calls, usage, ReadErrorCode.FILE_COUNT_LIMIT, at)
            matrix[stage] = result.reason_code
        self.assertEqual(set(matrix), set(hs.ReadStage))

    def test_im04_two_read_limit_errors_select_the_first_occurring_code(self) -> None:
        self.assert_baseline()
        observed = hs._observe(open_reader(workspace_root=self.ws), workspace_root=self.ws, shipment_id=SHIPMENT_ID)
        first = hs.ReadLimitHit(ReadErrorCode.FILE_SIZE_LIMIT, hs.ReadStage.MEMBER_CANDIDATE)
        second = hs.ReadLimitHit(ReadErrorCode.TOTAL_SIZE_LIMIT, hs.ReadStage.SURFACE_RECHECK)
        for a, b in ((first, second), (second, first)):
            with self.subTest(first=a.code.value):
                both = dataclasses.replace(
                    observed,
                    records=dataclasses.replace(observed.records, read_limit=a),
                    recheck=dataclasses.replace(observed.recheck, read_limit=b),
                )
                self.assert_limit(hs._reduce(both), a.code, a.stage)
                both = dataclasses.replace(
                    observed,
                    classification=dataclasses.replace(observed.classification, read_limit=a),
                    recheck=dataclasses.replace(observed.recheck, read_limit=b),
                )
                self.assert_limit(hs._reduce(both), a.code, a.stage)
        # End to end, the first error stops the run, so no second error is ever requested.
        for code in (ReadErrorCode.FILE_SIZE_LIMIT, ReadErrorCode.TOTAL_SIZE_LIMIT):
            with self.subTest(end_to_end=code.value):
                ws = self.fresh(f"two-{code.value}")
                limits = self.limits_for(code, ws, 1, self.file_for(ws, 1))
                with self.reads() as calls:
                    result, usage = self.resolve(ws=ws, limits=limits)
                self.assert_limit(result, code, hs.ReadStage.SHIPMENT_CANDIDATE)
                self.assert_stopped(calls, usage, code, 1)

    def test_im04_byte_codes_never_raised_at_an_absent_candidate(self) -> None:
        self.assert_baseline()
        self.record_path("7-S").unlink()
        for limits in (ReadLimits(max_file_bytes=0), ReadLimits(max_total_bytes=0)):
            result, usage = self.resolve(limits=limits)
            self.assertEqual(result.reason_code, "SHIPMENT_NOT_FOUND")
            self.assertEqual(usage, ReadUsage(files_claimed=4, bytes_reserved=0))
        record = self.shipment_record("9.001-T")
        self.write_record("7-S", record)
        # The budget fits the shipment record twice (first pass and recheck), so the
        # absent member candidates are requested with no byte budget left at the recheck.
        with self.reads() as calls:
            result, usage = self.resolve(
                limits=ReadLimits(max_file_bytes=len(record), max_total_bytes=2 * len(record))
            )
        self.assertEqual(result.reason_code, "MEMBER_NOT_FOUND")
        self.assertEqual(usage, ReadUsage(files_claimed=8, bytes_reserved=2 * len(record)))
        self.assertEqual([call[2] for call in calls].count(ReadErrorCode.PATH_NOT_FOUND), 6)

    def test_early_return_issues_no_recheck_after_a_first_pass_read_limit(self) -> None:
        self.assert_baseline()
        observed = hs._observe(
            open_reader(workspace_root=self.ws, limits=ReadLimits(max_files=10)),
            workspace_root=self.ws,
            shipment_id=SHIPMENT_ID,
        )
        self.assertIsNone(observed.recheck)
        self.assertEqual(observed.classification.read_limit.stage, hs.ReadStage.INSTALLED)
        result = hs._reduce(observed)
        self.assert_limit(result, ReadErrorCode.FILE_COUNT_LIMIT, hs.ReadStage.INSTALLED)
        self.assertEqual(result.declarations[0], hs.Declaration("7.001-T", "harness-architect"))


# IM-04 pairs whose lower-class fact cannot come first in encounter order, with the reason.
INFEASIBLE_ORDER: dict[str, str] = {
    "3 over 4 to 8": "class 3 facts come only from the records phase, which always runs before the "
    "surface phase, and NO_SURFACES_REQUIRED is derived after both (no recheck yields a class 3 code)",
    "2 over 4": "NO_SURFACES_REQUIRED is derived after every phase",
    "4 over 5 to 8": "NO_SURFACES_REQUIRED means an empty surface union, which yields no class 5 to 8 fact",
    "7 over 8": "one supported surface (FI-8) yields one row, and no recheck yields a class 7 code",
}


class ReducerPrecedenceCharacterizationTests(ReducerFixture):
    """IM-04 precedence pairs not covered by the roster (195-S local review; outside the roster).

    Each case collects a lower-class fact and a higher-class fact in one
    resolution; the higher class is selected and the lower-class fact is still
    collected (no short-circuit). Where it is feasible the lower-class fact
    comes first (class 5 over 6 and 7 through a manifest recheck that does not
    complete, and class 2 over 5 to 8 through a member recheck that does not
    complete); the infeasible orders are listed in INFEASIBLE_ORDER.
    """

    def arrange_lower(self, ws: Path, lower: str) -> None:
        if lower == "c5":
            self.path(".autoharness/harness-manifest.yaml", ws).write_bytes(b"[\n")
        elif lower == "c6":
            self.path("templates/" + TEMPLATE, ws).write_bytes(b"{{MISSING}}\n")
        elif lower == "c7":
            self.path(INSTALLED, ws).write_bytes(RENDERED + b"stale\n")

    def test_records_classes_beat_every_surface_class(self) -> None:
        higher = {
            "c2": ("MEMBER_NOT_FOUND", lambda ws: self.record_path("7.002-T", ws=ws).unlink()),
            "c3": ("DECLARATION_MISSING", lambda ws: self.write_record("7.002-T", self.task_record("7.002-T"), ws=ws)),
        }
        lower_codes = {"c5": "MANIFEST_YAML_INVALID", "c6": "TEMPLATE_VARIABLE_UNRESOLVED",
                       "c7": "CHECKSUM_MISMATCH", "c8": "ALL_SURFACES_PRESENT"}
        for high, (high_code, arrange_high) in higher.items():
            for low, low_code in lower_codes.items():
                with self.subTest(higher=high, lower=low):
                    ws = self.fresh(f"pair-{high}-{low}")
                    arrange_high(ws)
                    self.arrange_lower(ws, low)
                    observed = hs._observe(open_reader(workspace_root=ws), workspace_root=ws, shipment_id=SHIPMENT_ID)
                    self.assertEqual(observed.classification.reason_code, low_code)  # collected, not short-circuited
                    self.assertEqual(hs._reduce(observed).reason_code, high_code)
        # Class 2 over class 4: the union is empty, so NO_SURFACES_REQUIRED is derived too.
        ws = self.fresh("pair-c2-c4")
        self.write_record("7.001-T", self.task_record("7.001-T", "harness-surface:none"), ws=ws)
        self.record_path("7.002-T", ws=ws).unlink()
        self.assertEqual(self.resolve(ws=ws)[0].reason_code, "MEMBER_NOT_FOUND")

    def test_recheck_codes_beat_surface_facts_met_first(self) -> None:
        cases = [
            ("c5", "c6", "TEMPLATE_VARIABLE_UNRESOLVED", ".autoharness/harness-manifest.yaml", "MANIFEST_UNREADABLE"),
            ("c5", "c7", "CHECKSUM_MISMATCH", ".autoharness/harness-manifest.yaml", "MANIFEST_UNREADABLE"),
            ("c2", "c5", "MANIFEST_YAML_INVALID", ".backlogit/queue/7.001-T.md", "MEMBER_RECORD_INVALID"),
            ("c2", "c6", "TEMPLATE_VARIABLE_UNRESOLVED", ".backlogit/queue/7.001-T.md", "MEMBER_RECORD_INVALID"),
            ("c2", "c7", "CHECKSUM_MISMATCH", ".backlogit/queue/7.001-T.md", "MEMBER_RECORD_INVALID"),
        ]
        for high, low, low_code, target, code in cases:
            with self.subTest(higher=high, lower=low):
                ws = self.fresh(f"pair-{high}-{low}-recheck")
                self.arrange_lower(ws, low)
                with self.reads() as calls:
                    self.assertEqual(self.resolve(ws=ws)[0].reason_code, low_code)
                first_pass = len(calls) // 2
                with self.reads({first_pass: self.replace_with_directory(ws / target)}):
                    observed = hs._observe(
                        open_reader(workspace_root=ws), workspace_root=ws, shipment_id=SHIPMENT_ID
                    )
                    result = hs._reduce(observed)
                self.assertEqual(observed.classification.reason_code, low_code)  # met first, still collected
                self.assertEqual(observed.recheck.facts, (code,))
                self.assertEqual(result.reason_code, code)
                self.assertEqual(result.surfaces, ())

    def test_infeasible_orders_hold_for_the_recheck_codes(self) -> None:
        self.assertTrue(all(reason for reason in INFEASIBLE_ORDER.values()))
        recheck_classes = {hs.reason_spec(code).reason_class for _stage, code in hs._RECHECK.values()}
        # No recheck code is class 3, 4, 7 or 8, so those classes are met only in their own phase.
        self.assertEqual(recheck_classes, {"2", "5", "6"})


class ReducerRosterStructuralTests(unittest.TestCase):
    def test_structural_roster_markers_pairwise_distinct(self) -> None:
        names = [name for name in dir(ReducerRosterTests) if name.startswith("test_")]
        markers = [f"{MARKER}:{name}" for name in names]
        self.assertEqual(len(names), 11)
        self.assertEqual(len(set(markers)), len(markers))
        self.assertFalse(any(name.startswith("test_structural_") for name in names))
        self.assertEqual([name for name in dir(ReducerFixture) if name.startswith("test")], [])

    def test_structural_resolver_entry_signatures(self) -> None:
        keyword = inspect.Parameter.KEYWORD_ONLY
        public = inspect.signature(hs.resolve_shipment).parameters
        self.assertEqual(
            [(name, p.kind) for name, p in public.items()], [("workspace_root", keyword), ("shipment_id", keyword)]
        )
        private = inspect.signature(hs._resolve).parameters
        self.assertEqual(
            [(name, p.kind) for name, p in private.items()],
            [("workspace_root", keyword), ("shipment_id", keyword), ("limits", keyword)],
        )
        self.assertIn("resolve_shipment", hs.__all__)
        self.assertNotIn("_resolve", hs.__all__)

    def test_structural_no_public_callable_accepts_limits(self) -> None:
        for name in hs.__all__:
            value = getattr(hs, name)
            if inspect.isfunction(value):
                self.assertNotIn("limits", inspect.signature(value).parameters, name)


if __name__ == "__main__":
    unittest.main()
