"""Contract tests for the shipment-reconcile Linked-Deliberation Disposition
step (P-015 INV-12) and its hand-offs, post-mode coverage and scenario matrix
(shipment 206-S, feature 200-F, slice 5 of 6 of umbrella 195-F).

The disposition step is documentation-as-contract: the Ship agent and the
``shipment-reconcile`` skill execute it from the prose, and the pure planner
``compute_linked_deliberation_disposition`` in
``src/autoharness/gates/shipment_closure.py`` is tested separately in
``tests/test_linked_deliberation_disposition_planner.py``. This module pins
the load-bearing skill text in both the product template and the installed
dogfood mirror, and proves the template renders the same edited regions as
the mirror.

Plan: ``docs/plans/2026-09-29-backlogit-1-11-cascade-alignment-plan.md``
(units U5a and U5b). Decision:
``docs/decisions/2026-09-29-backlogit-1-11-cascade-linked-deliberation-alignment-deliberation.md``.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from typing import ClassVar

try:
    from _assertion_render import render_source
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests._assertion_render import render_source

try:
    from test_flat_manifest_closure_docs import POLICY_PARITY_ALLOWLIST
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests.test_flat_manifest_closure_docs import POLICY_PARITY_ALLOWLIST

_ROOT = Path(__file__).resolve().parents[1]
_SKILL_TEMPLATE = _ROOT / "templates" / "skills" / "shipment-reconcile" / "SKILL.md.tmpl"
_SKILL_MIRROR = _ROOT / ".github" / "skills" / "shipment-reconcile" / "SKILL.md"

_SECTION_HEADING = "### Linked-Deliberation Disposition (P-015 INV-12)"
_NEXT_HEADING = "### Mixed-Role Detection Mode"
_HALT_DISPOSITION = "HALT — linked-deliberation disposition failed {id}"
# The Step 0(c) linked-deliberation matcher literal. The disposition step
# references it by name only, so this slice must not add an occurrence.
_MATCHER_LITERAL = r"\b(?:DL\d+|[0-9]+(?:\.[0-9]+)*-DL)\b"
_OUTCOMES = (
    "archived",
    "already-archived",
    "retained_read_error",
    "retained_ambiguous",
    "retained_engine_unverified",
    "retained_live_status",
    "retained_shared_reference",
    "retained_description_mention",
)


def _flatten(text: str) -> str:
    """Collapse whitespace so a phrase wrapped across lines still matches."""
    return re.sub(r"\s+", " ", text)


def _variants() -> tuple[tuple[str, str], ...]:
    return (
        ("template", _SKILL_TEMPLATE.read_text(encoding="utf-8")),
        ("mirror", _SKILL_MIRROR.read_text(encoding="utf-8")),
    )


def _must_index(text: str, marker: str, label: str, start: int = 0) -> int:
    try:
        return text.index(marker, start)
    except ValueError as exc:  # pragma: no cover - failure path exercised by tests
        raise AssertionError(f"marker not found for {label}: {marker!r}") from exc


def _scope_between(raw: str, start_marker: str, end_marker: str, label: str) -> str:
    start = _must_index(raw, start_marker, f"{label} start")
    end = _must_index(raw, end_marker, f"{label} end", start)
    return raw[start:end]


def _section(raw: str) -> str:
    """The raw text of the Linked-Deliberation Disposition section."""
    return _scope_between(raw, _SECTION_HEADING, _NEXT_HEADING, "disposition section")


def _numbered_step(region: str, number: int, *, final_number: int, label: str) -> str:
    """One numbered step from ``region``, failing if a non-final successor is absent."""
    start = _must_index(region, f"\n{number}. **", f"{label} step {number}")
    next_marker = f"\n{number + 1}. **"
    following = region.find(next_marker, start)
    if following == -1:
        if number == final_number:
            following = len(region)
        else:
            raise AssertionError(f"marker not found for {label} step {number + 1}: {next_marker!r}")
    return _flatten(region[start:following])


def _step(section: str, number: int) -> str:
    """One numbered step of the disposition section, flattened."""
    return _numbered_step(section, number, final_number=6, label="disposition")


class DispositionSectionAssertionsI(unittest.TestCase):
    """200.002-T: scenarios H-a, H-h and H-k."""

    def test_h_a_section_exists_in_template_and_mirror(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                self.assertEqual(raw.count(_SECTION_HEADING), 1)
                # The section sits after the Cascade Close Sub-Procedure,
                # where both close paths hand off to it, and before the
                # Mixed-Role Detection Mode section.
                self.assertLess(
                    raw.index("### Cascade Close Sub-Procedure"),
                    raw.index(_SECTION_HEADING),
                )
                self.assertLess(raw.index(_SECTION_HEADING), raw.index(_NEXT_HEADING))

    def test_h_h_engine_unverified_means_no_mutation(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                plan = _step(_section(raw), 1)
                self.assertIn("**Engine UNVERIFIED means no mutation.**", plan)
                self.assertIn("`retained_engine_unverified`", plan)
                self.assertIn("nothing is mutated, on every close path", plan)
                self.assertIn("`ENGINE_SEMANTICS_UNVERIFIED`", plan)

    def test_h_k_planner_is_cited_as_plan_source(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                plan = _step(_section(raw), 1)
                self.assertIn("`compute_linked_deliberation_disposition(", plan)
                self.assertIn("`src/autoharness/gates/shipment_closure.py`", plan)
                self.assertIn(
                    "Other workspaces apply the same stated rules and first-match "
                    "precedence over the eight `LinkedDeliberationOutcome` values",
                    plan,
                )


class DispositionSectionAssertionsII(unittest.TestCase):
    """200.003-T: scenarios H-e, H-g and H-l."""

    def test_h_e_disposition_baseline_definition(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                baseline = _step(_section(raw), 2)
                self.assertIn("**Disposition baseline.**", baseline)
                self.assertIn("(i) the path-specific set", baseline)
                self.assertIn("safe-close observation-set fingerprints", baseline)
                self.assertIn("out-of-manifest descendant fingerprints", baseline)
                self.assertIn("(ii) the disposition snapshot", baseline)
                self.assertRegex(
                    baseline,
                    r"\(iii\) a pre-disposition `git status --porcelain -- "
                    r"\"[^\"]+/\"` capture",
                )
                self.assertIn(
                    "minus the `closure_scope(S)` IDs this run already archived",
                    baseline,
                )
                # Porcelain status codes are not byte identity: the baseline also
                # fingerprints every non-exempt backlog path by location and hash.
                self.assertIn(
                    "together with a location-and-SHA-256 fingerprint of every path under",
                    baseline,
                )
                self.assertIn("porcelain status codes alone are not byte identity", baseline)
                self.assertIn(
                    "this run's own closure report path under",
                    baseline,
                )
                self.assertIn(
                    "This subtraction applies to the (iii) porcelain capture only",
                    baseline,
                )

    def test_gate_runs_final_invariance_after_report_write(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                gate = _step(_section(raw), 6)
                self.assertIn(
                    "a final disposition-baseline invariance check, run after the step 5 "
                    "report write, passes",
                    gate,
                )
                self.assertIn(
                    "A failure of that final invariance check halts with `HALT — "
                    "linked-deliberation disposition failed {id}`, where `{id}` is the "
                    "shipment ID",
                    gate,
                )
                self.assertIn(
                    "follow the D6 sequence of safe-close step 6, scoped to the diverging "
                    "paths plus this run's disposition archives (when the run archived "
                    "nothing, the scope is the diverging paths alone)",
                    gate,
                )
                # The proceed instruction belongs to the success bullet, before the
                # failure bullet, so it never reads as proceeding after the halt.
                self.assertLess(
                    gate.index("Proceed to post-mode."),
                    gate.index("A failure of that final"),
                )
                self.assertIn("Do not proceed to post-mode.", gate)

    def test_h_g_allowed_side_effect_paths_exclude_stash_files(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                baseline = _step(_section(raw), 2)
                self.assertIn("`v1.11.0` `internal/core/archive.go`", baseline)
                self.assertIn("the target deliberation's own queue→archive move", baseline)
                self.assertIn(
                    "frontmatter keys `status`, `archived_status`, and `archived_from`",
                    baseline,
                )
                self.assertRegex(baseline, r"gitignored item event log \(`[^`]+/logs/`\)")
                # Only backlogit's own index and its SQLite sidecars are exempt,
                # enumerated explicitly; a broad `*.db*` glob would hide
                # collateral changes to any other root-level database file.
                self.assertNotIn("*.db*", baseline)
                self.assertNotIn("*.db*", raw)
                self.assertRegex(
                    baseline,
                    r"backlogit's\s+own index, which is exactly `[^`]+/backlogit\.db` and its "
                    r"SQLite\s+sidecars `[^`]+/backlogit\.db-wal`, `[^`]+/backlogit\.db-shm`,"
                    r"\s+and `[^`]+/backlogit\.db-journal` at the backlog storage root",
                )
                self.assertIn(
                    "no other `.db` file, at the root or below it, is part of the index",
                    " ".join(baseline.split()),
                )
                self.assertIn(
                    "the four index paths enumerated above, lock and hook-queue files",
                    " ".join(baseline.split()),
                )
                self.assertNotIn("the index, lock and hook-queue files", " ".join(baseline.split()))
                self.assertIn("lock and hook-queue files", baseline)
                # v1.11.0 ArchiveItem calls ArchiveLinkedStashEntries, which can
                # rewrite stash files. Those writes are never allowed side effects;
                # the step 3 engine stash-link guard makes the call a no-op instead.
                self.assertNotIn("does **not** write", baseline)
                self.assertIn("`ArchiveItem` also calls `ArchiveLinkedStashEntries`", baseline)
                self.assertIn("That write is never an allowed side effect", baseline)
                self.assertIn("the step 3 engine stash-link guard", baseline)
                self.assertRegex(
                    baseline,
                    r"Any change to `[^`]+/stash\.jsonl` or `[^`]+/archive/stash\.jsonl`, "
                    r"or to any other path outside these allowed side effects, violates "
                    r"the disposition baseline",
                )

    def test_h_l_matcher_referenced_by_name_not_restated(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                section = _section(raw)
                self.assertIn("the Step 0(c) matcher", _flatten(section))
                self.assertNotIn(_MATCHER_LITERAL, section)
                # The plan text (U5a step 1) says the skill-wide count "stays
                # 2"; 199.007-T (205-S) later removed the second literal from a
                # Quality Criteria bullet, so the skill-wide count this slice
                # must leave unchanged is 1: the Step 0(c) snapshot definition.
                self.assertEqual(raw.count(_MATCHER_LITERAL), 1)


class DispositionSectionAssertionsIII(unittest.TestCase):
    """200.005-T: scenarios H-i, H-j and H-c."""

    def test_h_i_hash_and_guard_rerun_before_each_archive(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn("Immediately before each call, re-run the SHA-256 check", archive)
                self.assertIn("**and** the shared-reference guard for that ID", archive)
                self.assertIn("(TOCTOU)", archive)
                self.assertIn("A hash mismatch halts with", archive)
                self.assertIn(
                    "A new live referrer records `retained_shared_reference: "
                    "[referrer IDs]` for that ID with no mutation",
                    archive,
                )

    def test_h_j_archive_call_carries_no_cascade_flag(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                section = _section(raw)
                archive = _step(section, 3)
                self.assertIn("Pass **no cascade flag**", archive)
                self.assertIn("(CLI fallback `backlogit archive {id}`)", archive)
                self.assertIn("one at a time, in ascending ID order", archive)
                for forbidden in ("--cascade", "backlogit shipment ship", "ship_shipment", "OP_SHIP_SHIPMENT"):
                    self.assertNotIn(forbidden, section)

    def test_h_c_disposition_halt_string_present(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                section = _section(raw)
                self.assertIn(f"`{_HALT_DISPOSITION}`", _step(section, 4))
                self.assertIn(_HALT_DISPOSITION, _step(section, 6))


class DispositionSectionAssertionsIV(unittest.TestCase):
    """200.006-T: scenarios H-b, H-d and H-f."""

    def test_h_b_eight_outcomes_and_reason_code_path_fields(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                section = _flatten(_section(raw))
                for outcome in _OUTCOMES:
                    with self.subTest(outcome=outcome):
                        self.assertIn(f"`{outcome}`", section)
                report = _step(_section(raw), 5)
                self.assertIn(
                    "`reason_code` is always present and is copied verbatim from the "
                    "planner for every planner outcome other than the planned `archive` "
                    "(never re-derived; an unknown code is carried as-is)",
                    report,
                )
                # A verified archive reports the outcome-value default, never the
                # planner's pre-mutation `archive`; a planning_error synthesizes.
                self.assertIn(
                    "a verified `archived` outcome carries `reason_code: archived` (the "
                    "outcome-value default, replacing the planner's pre-mutation `archive`)",
                    report,
                )
                self.assertIn(
                    "a planned `archive` that the step 3 re-check settles as "
                    "`retained_shared_reference` carries `reason_code: "
                    "retained_shared_reference`",
                    report,
                )
                self.assertIn(
                    "an outcome preserved from the Step 0(c) disposition snapshot keeps "
                    "that snapshot's own `reason_code`",
                    report,
                )
                self.assertIn(
                    "an outcome synthesized for a `planning_error` (only the remaining "
                    "snapshot deliberations) carries `reason_code: planning_error`",
                    report,
                )
                self.assertNotIn(
                    "`reason_code` is always present and copied verbatim from the planner (",
                    report,
                )
                self.assertIn("`path` is present for `retained_read_error`", report)
                self.assertIn("`unresolved_references` (`{id, reason_code}`)", report)

    def test_h_d_linked_deliberation_disposition_report_field(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                report = _step(_section(raw), 5)
                self.assertIn(
                    "`linked_deliberation_disposition: [{id, link_kinds, "
                    "linking_members, outcome, reason_code, path, referrers, "
                    "pre_sha256, post_sha256, archived_status}]`",
                    report,
                )
                self.assertIn("`outcome` is a `LinkedDeliberationOutcome` value", report)
                self.assertIn("`ENGINE_SEMANTICS_UNVERIFIED`", report)
                self.assertIn("`ENGINE_LINE_UNVERIFIED_ADVISORY`", report)
                self.assertIn("`stranded_linked_deliberation` advisory", report)

    def test_h_f_semantic_frontmatter_and_byte_exact_body(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                verify = _step(_section(raw), 4)
                self.assertIn("**Verify-after-each** (immediately after each archive call)", verify)
                self.assertIn(
                    "the queue copy is absent, and the archive copy is present exactly once",
                    verify,
                )
                self.assertIn("the archive copy declares `status: archived`", verify)
                self.assertIn(
                    "its `archived_from` provenance is present and well-formed, naming the "
                    "deliberation's disposition-snapshot queue record path by exact string "
                    "match, workspace-relative with `/` separators (step 3 archives only "
                    "queue-resident targets, so that path always exists; missing or "
                    "ill-formed provenance fails verification)",
                    verify,
                )
                self.assertIn(
                    "the archive copy passes the Step 0(c) containment checks (lexical and "
                    "canonical containment in the backlog root, and no symlink, junction, "
                    "or other reparse point) before any of its bytes are read",
                    verify,
                )
                self.assertIn("compared **semantically** (parsed YAML", verify)
                self.assertIn(
                    "except for the three engine keys `status`, `archived_status`, "
                    "and `archived_from`",
                    verify,
                )
                self.assertIn("is **byte-exact**", verify)
                self.assertIn("disposition-baseline invariance holds", verify)


def _safe_close_region(raw: str) -> str:
    return _scope_between(raw, "### Safe-Close Mode", "### Cascade Close Sub-Procedure", "safe-close mode")


def _cascade_region(raw: str) -> str:
    return _scope_between(raw, "### Cascade Close Sub-Procedure", _SECTION_HEADING, "cascade close")


def _safe_close_step(raw: str, number: int) -> str:
    """One numbered Safe-Close Mode step (before the Cascade sub-procedure)."""
    return _numbered_step(_safe_close_region(raw), number, final_number=10, label="safe-close")


def _cascade_step(raw: str, number: int) -> str:
    """One numbered Cascade Close Sub-Procedure step."""
    return _numbered_step(_cascade_region(raw), number, final_number=7, label="cascade")


def _post_mode_step(raw: str, number: int) -> str:
    """One numbered Post-Mode step."""
    mode = _scope_between(raw, "### Post-Mode", "### Safe-Close Mode", "post-mode")
    return _numbered_step(mode, number, final_number=6, label="post-mode")


def _behavioral_constraints(raw: str) -> str:
    return _flatten(_scope_between(raw, "## Behavioral Constraints", "## Required Protocol", "behavioral constraints"))


def _vocabulary_line(raw: str, invariant: str) -> str:
    for line in raw.splitlines():
        if line.startswith(f"* `{invariant}` ("):
            return line
    raise AssertionError(f"{invariant} vocabulary line not found")


class HandOffScopingAndSelectedWordingAssertions(unittest.TestCase):
    """200.008-T: scenarios I-1, I-2 and I-3."""

    def test_i_1_safe_close_closed_hands_off_to_disposition_step(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                gate = _safe_close_step(raw, 10)
                self.assertIn(
                    "→ `recommendation: CLOSED`. Continue to the "
                    "Linked-Deliberation Disposition step, not directly to post-mode",
                    gate,
                )
                self.assertNotIn("Proceed to post-mode", gate)
                # The Step 0(c) CASCADE routing and Cascade step 7 hand off to
                # the same step, so both close paths converge on it.
                routing = _safe_close_step(raw, 0)
                cascade_gate = _cascade_step(raw, 7)
                self.assertIn(
                    "in place of steps 1–10, then continue to the "
                    "Linked-Deliberation Disposition step.",
                    routing,
                )
                self.assertIn(
                    "`recommendation: CLOSED`. Hand off to the "
                    "Linked-Deliberation Disposition step; proceed to post-mode "
                    "only after that step returns `recommendation: DISPOSITION_COMPLETE`.",
                    cascade_gate,
                )
                self.assertIn(
                    "only after that step returns "
                    "`recommendation: DISPOSITION_COMPLETE`",
                    gate,
                )

    def test_i_2_mutation_scoping_limited_to_safe_close_steps(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                constraints = _behavioral_constraints(raw)
                self.assertIn(
                    "**Manifest-scoped mutation only.** In `mode: safe-close`, the "
                    "ONLY artifacts safe-close steps 1–10 may move or archive are",
                    constraints,
                )
                self.assertIn(
                    "The INV-12 Linked-Deliberation Disposition step is separately "
                    "sanctioned",
                    constraints,
                )
                load = _safe_close_step(raw, 1)
                self.assertIn(
                    "are the **only** artifacts safe-close steps 1–10 may move or archive",
                    load,
                )
                self.assertIn(
                    "the INV-12 Linked-Deliberation Disposition step is separately "
                    "sanctioned",
                    load,
                )

    def test_i_3_selected_close_path_wording(self) -> None:
        selected = "while Step 0(c)'s **selected** close path is not `CASCADE`"
        for label, raw in _variants():
            with self.subTest(surface=label):
                record_close = _safe_close_step(raw, 8)
                self.assertIn(selected, record_close)
                self.assertNotIn("`CASCADE`-eligible under Step 0(c)", record_close)
                self.assertIn(
                    "classifier `CASCADE` with `ENGINE_SEMANTICS_UNVERIFIED` "
                    "selects `SAFE_CLOSE`",
                    record_close,
                )
                inv11 = _vocabulary_line(raw, "INV-11")
                self.assertIn(selected, inv11)
                self.assertNotIn("not cascade-eligible", inv11)


def _matrix_row(raw: str, row: str) -> str:
    """One linked-deliberation row of the Deterministic Safe-Close Scenario Matrix."""
    matrix = _scope_between(raw, "## Deterministic Safe-Close Scenario Matrix", "## Quality Criteria", "scenario matrix")
    prefix = f"* **Linked deliberation ({row}) — "
    rows = [line for line in matrix.splitlines() if line.startswith(prefix)]
    if len(rows) != 1:
        raise AssertionError(f"scenario-matrix row ({row}) matched {len(rows)} lines")
    return rows[0]


class ScenarioMatrixAssertionsI(unittest.TestCase):
    """200.010-T: scenarios I-5a, I-5b and I-5c."""

    def test_i_5a_engine_unverified_cascade_selects_safe_close_and_retains(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                row = _matrix_row(raw, "a")
                self.assertIn("the classifier returns `CASCADE`", row)
                self.assertIn("engine-semantics verdict is `UNVERIFIED`", row)
                self.assertIn(
                    "selects `SAFE_CLOSE` with reason `ENGINE_SEMANTICS_UNVERIFIED`", row
                )
                self.assertIn("safe-close steps 1–10 run", row)
                self.assertIn("as `retained_engine_unverified` and mutates none", row)
                # The row restates contract text the skill already carries.
                self.assertIn(
                    "| `CASCADE` | `UNVERIFIED` | `SAFE_CLOSE`, reason "
                    "`ENGINE_SEMANTICS_UNVERIFIED` |",
                    raw,
                )
                self.assertIn(
                    "This includes a classifier `CASCADE` that Step 0(c) routed to "
                    "`SAFE_CLOSE` with reason `ENGINE_SEMANTICS_UNVERIFIED`.",
                    _flatten(_section(raw)),
                )

    def test_i_5b_shared_reference_is_retained(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                row = _matrix_row(raw, "b")
                self.assertIn("still has a live referrer outside `closure_scope(S)`", row)
                self.assertIn("is recorded `retained_shared_reference` with its referrer IDs", row)
                self.assertIn("it is never archived and never halts", row)
                self.assertNotIn("HALT", row)

    def test_i_5c_engine_drift_halts(self) -> None:
        unexpected = "HALT — cascade archived unexpected artifact {id}"
        drift = "HALT — cascade modified linked deliberation {id} — engine semantics drift"
        for label, raw in _variants():
            with self.subTest(surface=label):
                row = _matrix_row(raw, "c")
                self.assertIn(
                    "a cascade that archives a non-manifest disposition-set linked "
                    "deliberation halts at Cascade Close Sub-Procedure step 3",
                    row,
                )
                self.assertIn(f"`{unexpected}`", row)
                self.assertIn(
                    "a cascade that modifies but does not archive one halts at step 5",
                    row,
                )
                self.assertIn(f"`{drift}`", row)
                self.assertIn(
                    "neither the Linked-Deliberation Disposition step nor post-mode runs", row
                )
                cascade = _cascade_region(raw)
                self.assertIn(f"halts with `{drift}`", cascade)
                self.assertIn(f"`{unexpected}`", cascade)


class ScenarioMatrixAssertionsII(unittest.TestCase):
    """200.011-T: scenarios I-5d, I-5e and I-5f."""

    def test_i_5d_description_only_mention_is_retained(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                row = _matrix_row(raw, "d")
                self.assertIn("mentioned only in a member's description", row)
                self.assertIn("never in `custom_fields.source_deliberation_id`", row)
                self.assertIn("is recorded `retained_description_mention`", row)
                self.assertIn("it is never archived and never halts", row)

    def test_i_5e_torn_deliberation_is_retained_ambiguous(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                row = _matrix_row(raw, "e")
                self.assertIn("resolves to more than one record", row)
                self.assertIn("is recorded `retained_ambiguous`", row)
                self.assertIn("it is never archived and never halts", row)

    def test_i_5f_read_error_is_retained_with_reason_code_and_path(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                row = _matrix_row(raw, "f")
                self.assertIn(
                    "an unreadable, malformed, or containment-failing deliberation "
                    "record or stash input",
                    row,
                )
                self.assertIn(
                    "is recorded `retained_read_error` with its `reason_code` and "
                    "workspace-relative `path`",
                    row,
                )
                # The non-halting rule covers only snapshot/plan-time read errors;
                # late containment drift fails closed through D6 (PR #477 cycle 5).
                self.assertIn("found by the Step 0(c) snapshot or the step 1 plan", row)
                self.assertIn("it is never archived and never halts", row)
                self.assertIn(
                    "A record that passed those checks but fails containment later, at "
                    "the step 3 pre-archive re-check or as a new or changed failure at the "
                    "step 4 or step 6 comparison, is not a read-error retention: it halts "
                    "with `HALT — linked-deliberation disposition failed {id}` through D6, "
                    "where `{id}` is that step's own halt ID (the re-checked or "
                    "just-archived deliberation at steps 3 and 4, the shipment ID at step 6).",
                    row,
                )
                self.assertLess(
                    row.index("it is never archived and never halts"),
                    row.index("fails containment later"),
                )


def _quality_criteria(raw: str) -> str:
    return _flatten(_scope_between(raw, "## Quality Criteria", "## Related Artifacts", "quality criteria"))


class PostModeAndQualityCriteriaAssertions(unittest.TestCase):
    """200.012-T: scenarios I-4 and I-11."""

    def test_i_4_post_mode_covers_disposition_outcomes(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                per_item = _post_mode_step(raw, 2)
                self.assertIn(
                    "The same per-item check covers every Linked-Deliberation "
                    "Disposition `archived` outcome: verify each such deliberation's "
                    "archive file exists and flag any absence in the report.",
                    per_item,
                )
                self.assertIn("Retained (`retained_*`) outcomes are not archive-checked.", per_item)
                guard = _post_mode_step(raw, 3)
                self.assertIn(
                    "The queue-to-archive moves made by the Linked-Deliberation "
                    "Disposition step's `archived` outcomes are expected: this guard "
                    "never flags them as deletions or unexpected changes.",
                    guard,
                )
                gate = _post_mode_step(raw, 5)
                self.assertIn(
                    "Retained (`retained_*`) Linked-Deliberation Disposition outcomes "
                    "never change this gate",
                    gate,
                )
                self.assertIn("are not missing archive files, and are not deletions", gate)

    def test_i_11_quality_criteria_bullets_present(self) -> None:
        bullets = (
            "the Linked-Deliberation Disposition step runs before post-mode; post-mode "
            "runs only after that step returns `recommendation: DISPOSITION_COMPLETE`, "
            "never directly after a close-path `CLOSED`",
            "\"Manifest-scoped mutation only\" and safe-close step 1 bound only "
            "safe-close steps 1–10; the INV-12 Linked-Deliberation Disposition step is "
            "separately sanctioned",
            "Safe-close step 8 and the INV-11 summary key the "
            "`RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION` halt on Step 0(c)'s "
            "**selected** close path",
            "Post-mode step 2 archive-checks every disposition `archived` outcome, the "
            "step 3 deleted-file guard treats their moves as expected, and retained "
            "outcomes never change the step 5 gate",
            "The Deterministic Safe-Close Scenario Matrix covers linked-deliberation "
            "rows (a)–(f): engine unverified, shared reference, engine drift, "
            "description-only mention, torn deliberation, and read error; row (c) "
            "halts, row (f) retains snapshot/plan-time read errors without halting but "
            "halts on a late containment or invariance failure, and every retained "
            "outcome is reported without halting",
        )
        for label, raw in _variants():
            criteria = _quality_criteria(raw)
            for bullet in bullets:
                with self.subTest(surface=label, bullet=bullet[:40]):
                    self.assertIn(bullet, criteria)
            with self.subTest(surface=label, bullet="no only-row-(c) claim"):
                self.assertNotIn("only row (c) halts", raw)


def _allowlisted(rendered: str) -> str:
    for template_text, mirror_text in POLICY_PARITY_ALLOWLIST:
        rendered = rendered.replace(template_text, mirror_text)
    return rendered


def _scope(raw: str, start: str, end: str) -> str:
    return _scope_between(raw, start, end, f"scope {start!r}")


def _list_indent(line: str) -> int | None:
    match = re.match(r"^(\s*)(?:[*+-]|\d+\.)\s+", line)
    return len(match.group(1)) if match else None


def _is_heading(line: str) -> bool:
    return bool(re.match(r"^#{1,6}\s+", line))


def _next_nonblank(lines: list[str], start: int) -> str | None:
    for line in lines[start:]:
        if line.strip():
            return line
    return None


def _anchored_region(text: str, anchor: str) -> str:
    """The anchor line plus continuation, including multi-paragraph list items."""
    lines = text.splitlines()
    hits = [idx for idx, line in enumerate(lines) if line.startswith(anchor)]
    if len(hits) != 1:
        raise AssertionError(f"anchor {anchor!r} matched {len(hits)} lines")
    start = hits[0]
    indent = _list_indent(lines[start])
    end = start + 1
    while end < len(lines):
        line = lines[end]
        if _is_heading(line):
            break
        if not line.strip():
            following_line = _next_nonblank(lines, end + 1)
            if following_line is None or _is_heading(following_line):
                break
            following_item = _list_indent(following_line)
            if indent is not None and following_item is not None and following_item <= indent:
                break
            end += 1
            continue
        following = _list_indent(line)
        if indent is not None and following is not None and following <= indent:
            break
        end += 1
    return "\n".join(lines[start:end])


# (scope start, scope end, anchor) for every region the U5b triples
# (200.007-T and 200.009-T) edited.
_U5B_REGIONS = (
    ("## Behavioral Constraints", "## Required Protocol", "* **Report-and-halt only.**"),
    ("## Behavioral Constraints", "## Required Protocol", "* **Manifest-scoped mutation only.**"),
    ("### Post-Mode", "### Safe-Close Mode", "2. **Per-item archive check**"),
    ("### Post-Mode", "### Safe-Close Mode", "   The queue-to-archive moves made by"),
    ("### Post-Mode", "### Safe-Close Mode", "5. **Gate decision**"),
    ("### Safe-Close Mode", "### Cascade Close Sub-Procedure", "1. **Load manifest**"),
    ("### Safe-Close Mode", "### Cascade Close Sub-Procedure", "   * If `backlogit move <shipment_id> --status shipped` is refused"),
    ("### Safe-Close Mode", "### Cascade Close Sub-Procedure", "10. **Gate decision**"),
    ("### Cascade Close Sub-Procedure", _SECTION_HEADING, "7. **Gate decision**"),
    ("## P-015 Vocabulary and Invariant Summary", "## Deterministic Safe-Close Scenario Matrix", "* `INV-11` ("),
    *(
        ("## Deterministic Safe-Close Scenario Matrix", "## Quality Criteria", f"* **Linked deliberation ({row}) — ")
        for row in "abcdef"
    ),
    ("## Quality Criteria", "## Related Artifacts", "* After the selected close path returns `recommendation: CLOSED`"),
    ("## Quality Criteria", "## Related Artifacts", "* \"Manifest-scoped mutation only\" and safe-close step 1"),
    ("## Quality Criteria", "## Related Artifacts", "* Safe-close step 8 and the INV-11 summary"),
    ("## Quality Criteria", "## Related Artifacts", "* Post-mode step 2 archive-checks"),
    ("## Quality Criteria", "## Related Artifacts", "* The Deterministic Safe-Close Scenario Matrix covers"),
)


class ReviewFixCycleOneAssertions(unittest.TestCase):
    """206-S review-fix cycle 1 hardening over the edited INV-12 prose."""

    def test_transition_window_record_removed_everywhere(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                self.assertNotIn("step-not-yet-on-main", raw)
                self.assertNotIn("transition window", raw)
                cascade_gate = _cascade_step(raw, 7)
                self.assertIn("Hand off to the Linked-Deliberation Disposition step", cascade_gate)
                self.assertIn("DISPOSITION_COMPLETE", cascade_gate)
                self.assertIn("Any verification failure above → the corresponding `HALT`", cascade_gate)

    def test_recommendation_tokens_include_disposition_results(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                output = _scope_between(raw, "## Output", "### Mixed-Role Detection Classification", "output")
                self.assertIn("`DISPOSITION_COMPLETE`", output)
                self.assertIn(f"`{_HALT_DISPOSITION}`", output)

    def test_mutation_scoping_pointers_and_halt_list_include_disposition(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                constraints = _behavioral_constraints(raw)
                self.assertIn(
                    "outside the safe-close mode's manifest-scoped archival and the "
                    "separately sanctioned INV-12 Linked-Deliberation Disposition step",
                    constraints,
                )
                self.assertIn("Do not commit backlog state if safe-close returns", constraints)
                self.assertIn("`HALT — linked-deliberation disposition failed {id}`", constraints)
                self.assertIn("Surface the report path to the operator", constraints)
                criteria = _quality_criteria(raw)
                self.assertIn(
                    "Report-and-halt in pre/post mode; safe-close mutation is strictly "
                    "manifest-scoped with no auto-prune, and the separately sanctioned "
                    "INV-12 Linked-Deliberation Disposition step is the only additional "
                    "queue/archive mutation",
                    criteria,
                )

    def test_planner_result_must_match_snapshot_before_mutation(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                step0 = _step(_section(raw), 0)
                self.assertIn("never substitutes a recomputed set for the snapshot", step0)
                plan = _step(_section(raw), 1)
                self.assertIn(
                    "Check `planning_error` first: when `planning_error` is present, it "
                    "is exempt from the planner-vs-snapshot equality check because the "
                    "planner returns `dispositions=()`; the equality check applies only "
                    "when the planner returns without `planning_error`.",
                    plan,
                )
                self.assertIn(
                    "Before any archive, when the planner returns without "
                    "`planning_error`, the planner's disposition set (deliberation IDs, "
                    "link kinds, linking members, record paths, and record hashes) MUST "
                    "equal the Step 0(c) disposition snapshot",
                    plan,
                )
                # Snapshot-settled outcome data joins the equality contract so a
                # fresh plan cannot upgrade retained evidence to an archive.
                self.assertIn(
                    "for every deliberation the snapshot already settled as "
                    "`retained_read_error`, `retained_ambiguous`, or `already-archived`, "
                    "the planner's outcome and `reason_code` (and, for "
                    "`retained_read_error`, its `path`) MUST equal the snapshot's "
                    "settled outcome data, and the planner's `unresolved_references` set "
                    "(exact `{id, reason_code}` pairs) MUST equal the snapshot's, so a "
                    "fresh plan never upgrades snapshot-settled evidence to a planned "
                    "`archive` or drops snapshot evidence.",
                    plan,
                )
                # planning_error returns no unresolved references, so the snapshot's
                # set is preserved in both the plan step and the report.
                self.assertIn(
                    "Also preserve the snapshot's `unresolved_references` set, because "
                    "the planner returns none on `planning_error`.",
                    plan,
                )
                self.assertIn(
                    "and report the snapshot's `unresolved_references` set",
                    _step(_section(raw), 5),
                )
                self.assertIn(
                    "Any difference halts with `HALT — linked-deliberation disposition "
                    "failed {id}`; emit **P-005** once; no mutation. `{id}` is the "
                    "first differing deliberation ID, or the shipment ID for a set-level "
                    "added/removed-ID difference.",
                    plan,
                )
                self.assertIn("The list below is the precedence order", plan)
                self.assertIn("other outcome enumerations in this skill are unordered", plan)

    def test_pre_archive_recheck_and_hash_halt_are_fully_scoped(self) -> None:
        expected = (
            "A hash mismatch halts with `HALT — linked-deliberation disposition failed {id}`; "
            "emit a **P-005** violation once through D6, scoped to the disposition archive "
            "of {id}; the completed close-path closure is never rolled back."
        )
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn("re-listing the deliberation ID's record paths under", archive)
                self.assertIn("require exactly the disposition snapshot's single path", archive)
                # The TOCTOU re-check reapplies containment before any byte read.
                self.assertIn(
                    "then reapply the Step 0(c) containment checks to that record path "
                    "before reading any of its bytes (lexical and canonical containment "
                    "in the backlog root, and no symlink, junction, or other reparse "
                    "point), then check that record path against its disposition-snapshot "
                    "hash",
                    archive,
                )
                self.assertIn(
                    "A containment failure at this re-check is never opened, hashed, or "
                    "archived; it halts identically with `HALT — linked-deliberation "
                    "disposition failed {id}`; emit a **P-005** violation once through D6, "
                    "scoped to the disposition archive of {id}; no mutation",
                    archive,
                )
                self.assertIn(
                    "A record-path re-list mismatch halts identically with `HALT — "
                    "linked-deliberation disposition failed {id}`; emit a **P-005** "
                    "violation once through D6, scoped to the disposition archive of "
                    "{id}; the completed close-path closure is never rolled back.",
                    archive,
                )
                self.assertIn(expected, archive)
                verify = _step(_section(raw), 4)
                self.assertNotIn("emit a **P-005** violation, and follow the D6 sequence", verify)
                self.assertIn("follow the D6 sequence of safe-close step 6", verify)

    def test_verify_after_each_allows_previously_verified_archives(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                verify = _step(_section(raw), 4)
                self.assertIn(
                    "except that call's allowed `ArchiveItem` side effects and the side "
                    "effects of earlier disposition archives in this step that already "
                    "passed verification",
                    verify,
                )

    def test_planning_error_reports_snapshot_retained_outcomes(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                report = _step(_section(raw), 5)
                self.assertIn("When the planner reports `planning_error`", report)
                self.assertIn("record the `planning_error`", report)
                self.assertIn(
                    "Preserve outcomes already settled by the Step 0(c) disposition "
                    "snapshot (`retained_read_error`, `retained_ambiguous`, and "
                    "`already-archived`); for every remaining snapshot deliberation, "
                    "report outcome `retained_ambiguous` with `reason_code: "
                    "planning_error`, and exclude `already-archived` deliberations from "
                    "the `stranded_linked_deliberation` advisory, and report the "
                    "snapshot's `unresolved_references` set.",
                    report,
                )
                gate = _step(_section(raw), 6)
                self.assertIn(
                    "`linked_deliberation_disposition: []` is valid only when the "
                    "Step 0(c) disposition snapshot is empty",
                    gate,
                )

    def test_small_clarity_clauses_are_present(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                baseline = _step(_section(raw), 2)
                self.assertIn("(disposition step 0)", baseline)
                report = _step(_section(raw), 5)
                self.assertIn(
                    "Report keys map to planner/code fields as follows: `id` → "
                    "`deliberation_id`, `linking_members` → `linking_member_ids`, "
                    "`referrers` → `referrer_ids`, and `pre_sha256` records one "
                    "pre-archive SHA-256 per record.",
                    report,
                )
                gate = _step(_section(raw), 6)
                self.assertIn(
                    "On a disposition HALT, keep the shipment lock held through the D6 "
                    "sequence (approval → REVALIDATE → approved rollback) and release it "
                    "only after D6 finishes — either the approved rollback is complete or "
                    "the operator declines — following pre-mode step 7's rule to release "
                    "the lock on pre-mode HALT while retaining it after `PROCEED` from "
                    "Ship Step 6 until post-mode completes.",
                    gate,
                )
                row_b = _matrix_row(raw, "b")
                self.assertIn("with the engine VERIFIED", row_b)
                row_d = _matrix_row(raw, "d")
                self.assertIn("with the engine VERIFIED", row_d)
                self.assertIn("no higher-precedence rule matched", row_d)
                self.assertIn("description/references", row_d)


class ReviewFixCycleFourAssertions(unittest.TestCase):
    """PR #477 review-fix cycle 4: engine stash-link guard, archive-resident
    retention, and containment for the all-path disposition fingerprint.
    """

    def test_engine_stash_link_guard_retains_before_archive(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn("**Engine stash-link guard.**", archive)
                self.assertIn("declare a `custom_fields.source_stash_id` key", archive)
                self.assertIn(
                    "record outcome `retained_shared_reference` with `reason_code: "
                    "engine_stash_link`",
                    archive,
                )
                self.assertIn("`GetStashLinksForItem`", archive)
                self.assertIn(
                    "Together, the two checks make the `ArchiveLinkedStashEntries` "
                    "call inside `ArchiveItem` a no-op",
                    archive,
                )
                # The guard runs before the archive call in the same step.
                self.assertLess(
                    archive.index("**Engine stash-link guard.**"),
                    archive.index("Otherwise archive that single artifact"),
                )
                report = _step(_section(raw), 5)
                self.assertIn("`reason_code: engine_stash_link`", report)

    def test_archive_resident_target_is_retained_before_archive(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn("**Archive-resident target.**", archive)
                self.assertIn(
                    "record outcome `retained_ambiguous` with `reason_code: "
                    "archive_resident_unarchived`",
                    archive,
                )
                self.assertIn("canonical queue restore path", archive)
                self.assertLess(
                    archive.index("**Archive-resident target.**"),
                    archive.index("Otherwise archive that single artifact"),
                )
                verify = _step(_section(raw), 4)
                self.assertIn("step 3 archives only queue-resident targets", verify)
                report = _step(_section(raw), 5)
                self.assertIn("`reason_code: archive_resident_unarchived`", report)

    def test_all_path_fingerprint_applies_containment_before_reads(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                baseline = _step(_section(raw), 2)
                self.assertIn(
                    "enumerate those paths without following any symlink, junction, or "
                    "other reparse point",
                    baseline,
                )
                self.assertIn(
                    "before reading any path's bytes, at this capture and at every later "
                    "invariance comparison in steps 4 and 6, apply the Step 0(c) "
                    "containment checks to it",
                    baseline,
                )
                self.assertIn(
                    "A path that fails those checks, or cannot be read, while capturing "
                    "this baseline is never opened or hashed and does not halt",
                    baseline,
                )
                self.assertIn(
                    "by its workspace-relative path and `reason_code` (`path_escape`, "
                    "`symlink_or_reparse_point`, or `unreadable_file`) instead of a SHA-256",
                    baseline,
                )
                self.assertIn(
                    "compare such a path by location and `reason_code` only, never by "
                    "following or reading it",
                    baseline,
                )
                self.assertIn(
                    "is never read or hashed and fails that step's verification (step 4 "
                    "or step 6)",
                    baseline,
                )
                # Scenario row (f): a containment failure is retained, never a halt.
                self.assertNotIn("A containment failure while capturing this baseline", baseline)

    def test_step_3_retention_rules_have_explicit_precedence(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn(
                    "These retention rules apply in the order listed, and the first "
                    "that applies settles the ID",
                    archive,
                )
                self.assertIn("deliberately retains every harvest-created deliberation", archive)


class HelperHardeningAssertions(unittest.TestCase):
    """The test slicers fail closed when their structural markers drift."""

    def test_numbered_step_helper_fails_when_non_final_successor_missing(self) -> None:
        with self.assertRaises(AssertionError):
            _numbered_step("\n1. **One**\nbody\n3. **Three**\n", 1, final_number=3, label="demo")

    def test_marker_lookup_helper_reports_label(self) -> None:
        with self.assertRaisesRegex(AssertionError, "demo-marker"):
            _must_index("abc", "missing", "demo-marker")

    def test_anchored_region_keeps_multi_paragraph_list_item(self) -> None:
        text = "* anchor line\n  first continuation\n\n  second paragraph\n* next item\n"
        region = _anchored_region(text, "* anchor line")
        self.assertIn("second paragraph", region)
        self.assertNotIn("* next item", region)


class RenderedRegionParityII(unittest.TestCase):
    """200.013-T: scenarios H-m and I-13. The product template, rendered by
    ``tests/_assertion_render.py::render_source``, matches the dogfood mirror
    over the U5a and U5b regions, modulo the policy parity allowlist.
    """

    rendered: ClassVar[str]
    mirror: ClassVar[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.rendered = render_source(".github/skills/shipment-reconcile/SKILL.md")
        cls.mirror = _SKILL_MIRROR.read_text(encoding="utf-8")

    def test_region_helper_detects_continuation_drift(self) -> None:
        template = "* anchor line\n  template continuation\n* next\n"
        mirror = "* anchor line\n  mirror continuation\n* next\n"
        self.assertNotEqual(
            _anchored_region(template, "* anchor line"), _anchored_region(mirror, "* anchor line")
        )

    def test_h_m_u5a_disposition_section_rendered_region_parity(self) -> None:
        self.assertEqual(
            _section(self.mirror),
            _allowlisted(_section(self.rendered)),
        )

    def test_i_13_u5b_rendered_region_parity(self) -> None:
        for start, end, anchor in _U5B_REGIONS:
            with self.subTest(anchor=anchor):
                expected = _anchored_region(_allowlisted(_scope(self.rendered, start, end)), anchor)
                actual = _anchored_region(_scope(self.mirror, start, end), anchor)
                self.assertEqual(actual, expected)


class ReviewFixCycleSevenAssertions(unittest.TestCase):
    """PR #477 review-fix cycle 7: the engine stash-link guard also runs the
    engine's exact active stash-link relation, read-only, before each archive.
    """

    _QUERY = (
        "`SELECT sl.stash_id FROM stash_links sl JOIN stash_entries se ON "
        "se.stash_id = sl.stash_id WHERE sl.item_id = ? AND se.state = 'active'`"
    )

    def test_guard_names_exact_relation_query(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn("*Exact relation check.*", archive)
                self.assertIn(self._QUERY, archive)
                self.assertIn("`TestArchiveItem_ArchivesLinkedStashEntries`", archive)
                self.assertIn("bound to the target ID", archive)
                # The key check stays first; the relation check runs after it
                # and before the archive call.
                self.assertLess(
                    archive.index("*Provenance key check.*"),
                    archive.index("*Exact relation check.*"),
                )
                self.assertLess(
                    archive.index("*Exact relation check.*"),
                    archive.index("Otherwise archive that single artifact"),
                )
                self.assertIn("immediately before the archive call", archive)

    def test_relation_query_is_read_only(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn("Open the index **read-only** through the SQLite URI", archive)
                self.assertRegex(archive, r"`file:[^`]*/backlogit\.db\?mode=ro`")
                self.assertIn(
                    "never write, migrate, sync, rehydrate, or hand-edit the index",
                    archive,
                )
                self.assertIn("reapply those checks to it before opening it", archive)

    def test_any_returned_row_retains(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn(
                    "If the query returns any row, the target is never archived: record "
                    "outcome `retained_shared_reference` with `reason_code: "
                    "engine_stash_link` and the returned stash IDs",
                    archive,
                )
                self.assertIn("Only an error-free query that returns zero rows clears", archive)
                report = _step(_section(raw), 5)
                self.assertIn("the stash IDs the exact relation check returned", report)

    def test_unreadable_index_retains_fail_closed(self) -> None:
        for label, raw in _variants():
            with self.subTest(surface=label):
                archive = _step(_section(raw), 3)
                self.assertIn(
                    "If the index is missing, fails the containment checks, cannot be "
                    "opened read-only, or lacks the `stash_links` or `stash_entries` "
                    "table or a queried column",
                    archive,
                )
                self.assertIn(
                    "archived (fail-closed): record outcome `retained_engine_unverified` "
                    "with `reason_code: engine_stash_link_unverifiable`",
                    archive,
                )
                report = _step(_section(raw), 5)
                self.assertIn("`reason_code: engine_stash_link_unverifiable`", report)
                baseline = _step(_section(raw), 2)
                self.assertIn(
                    "provenance key check and exact relation check together retain",
                    baseline,
                )


# 195.017-T (I-12): every realigned template/mirror pair. The policy,
# shipment-reconcile, Ship agent and operational-closure pairs must carry none
# of the withdrawn linked-deliberation cascade wording.
_STALE_WORDING_PAIRS = (
    (
        "policy",
        _ROOT / "templates" / "policies" / "workflow-policies.md.tmpl",
        _ROOT / ".github" / "policies" / "workflow-policies.md",
    ),
    ("shipment-reconcile", _SKILL_TEMPLATE, _SKILL_MIRROR),
    (
        "ship-agent",
        _ROOT / "templates" / "agents" / "_ship.agent.md.tmpl",
        _ROOT / ".github" / "agents" / "_ship.agent.md",
    ),
    (
        "operational-closure",
        _ROOT / "templates" / "skills" / "operational-closure" / "SKILL.md.tmpl",
        _ROOT / ".github" / "skills" / "operational-closure" / "SKILL.md",
    ),
)
_STALE_LITERALS = (
    "expected, in-scope cascade mutation",
    "may be live/required",
    "CASCADE` archiving it is expected",
    "appends, for every explicit qualifying feature member",
)
_LINKED_DELIBERATION_RE = re.compile(r"linked[ _-]deliberation", re.IGNORECASE)
_SAFE_CLOSE_RE = re.compile(r"SAFE_CLOSE|safe[- ]close", re.IGNORECASE)
# A close-path ``CLOSED`` (case-sensitive token) followed, with only markup or
# punctuation (and an optional "then"/"and"/"and then" connector) between them,
# by "proceed(s) to post-mode".
_CLOSED_THEN_POST_MODE_RE = re.compile(
    r"\bCLOSED\b[`*\"'.,;:)\s→—-]*(?:(?i:and\s+then|then|and)\s+)?"
    r"(?i:proceeds? to post-mode)"
)


def _sentences(flat: str) -> list[str]:
    return re.split(r"(?<=[.!?])\s+", flat)


def _stale_wording_findings(text: str) -> list[str]:
    """Every withdrawn linked-deliberation cascade phrase present in ``text``."""
    flat = _flatten(text)
    findings = [f"literal {literal!r}" for literal in _STALE_LITERALS if literal in flat]
    for sentence in _sentences(flat):
        if "correctly absent" in sentence and _LINKED_DELIBERATION_RE.search(sentence):
            findings.append(f"'correctly absent' naming a linked deliberation: {sentence!r}")
        if "always valid" in sentence and _SAFE_CLOSE_RE.search(sentence):
            findings.append(f"'always valid' applied to SAFE_CLOSE: {sentence!r}")
    for match in _CLOSED_THEN_POST_MODE_RE.finditer(flat):
        findings.append(f"'Proceed to post-mode' directly after CLOSED: {match.group(0)!r}")
    return findings


class ClosingNegativeGrepAssertions(unittest.TestCase):
    """195.017-T scenario I-12: the closing negative grep over every realigned pair."""

    def test_no_stale_linked_deliberation_cascade_wording(self) -> None:
        for pair, template, mirror in _STALE_WORDING_PAIRS:
            for surface, path in (("template", template), ("mirror", mirror)):
                with self.subTest(pair=pair, surface=surface):
                    self.assertEqual(
                        _stale_wording_findings(path.read_text(encoding="utf-8")), []
                    )

    def test_stale_wording_detector_catches_each_withdrawn_form(self) -> None:
        samples = (
            "This is an expected, in-scope cascade mutation of the record.",
            "The deliberation may be live/required at close.",
            "`CASCADE` archiving it is expected.",
            "The engine appends, for every explicit qualifying feature member, its links.",
            "A validated linked deliberation is correctly absent from `archived_ids`.",
            "SAFE_CLOSE is always valid.",
            "→ `recommendation: CLOSED`. Proceed to post-mode.",
            "returns `CLOSED`, then proceed to post-mode",
            "returns `CLOSED` and proceeds to post-mode",
            "returns `CLOSED`, and then proceeds to post-mode",
            "returns `CLOSED` and then proceed to post-mode",
        )
        for sample in samples:
            with self.subTest(sample=sample):
                self.assertNotEqual(_stale_wording_findings(sample), [])
        self.assertEqual(
            _stale_wording_findings(
                "A non-feature manifest member is correctly absent from `archived_ids`. "
                "→ `recommendation: CLOSED`. Hand off to the Linked-Deliberation "
                "Disposition step; proceed to post-mode only after it returns "
                "`DISPOSITION_COMPLETE`. The shipment is closed, then proceeds to "
                "post-mode only after the disposition step."
            ),
            [],
        )


if __name__ == "__main__":
    unittest.main()
