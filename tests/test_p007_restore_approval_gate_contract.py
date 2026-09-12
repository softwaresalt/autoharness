"""Contract tests for 154.002-T (SHIP-4, C0EA1175 / 701073F9):

* Part 1 — P-007's `git restore` remediation step must be gated behind a
  fresh, live, non-synthesizable operator approval (Decision G1-G9), never
  issued unconditionally, never satisfiable by an agent-writable artifact.
* Part 2 — the constitution-reviewer persona's principle checklist must
  include Principle X and Principle XI (with its NON-NEGOTIABLE marker
  verbatim).

These are DETERMINISTIC STATIC TEXT assertions over the rendered template and
its installed dogfood mirror, per the binding VERIFICATION SEAM recorded on
154.002-T: no approval broker, remediation executor, or `git restore` call
site exists in this product, so nothing here asserts a runtime exit code or
process outcome.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

_WORKFLOW_POLICY_TEMPLATE = _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
_WORKFLOW_POLICY_DOGFOOD = _REPO_ROOT / ".github" / "policies" / "workflow-policies.md"

_CONSTITUTION_REVIEWER_TEMPLATE = (
    _REPO_ROOT / "templates" / "agents" / "review" / "constitution-reviewer.agent.md.tmpl"
)
_CONSTITUTION_REVIEWER_DOGFOOD = (
    _REPO_ROOT / ".github" / "agents" / "subagents" / "constitution-reviewer.agent.md"
)

# Known variable resolution for this dogfood workspace (.autoharness/harness-manifest.yaml
# variables_used), used to normalize the template source to the same text the installed
# mirror carries, without invoking the full renderer (which also resolves the live
# {{DATE}} token elsewhere in the same file and would make the two files diverge on
# unrelated grounds).
_TEMPLATE_SUBSTITUTIONS = {
    "{{BACKLOG_DIRECTORY}}": ".backlogit",
    "{{OP_SHIP_SHIPMENT_MCP}}": "backlogit_ship_shipment",
    "{{FEATURE_SHIPMENTS}}": "true",
    "{{BACKLOG_TOOL_NAME}}": "backlogit",
}


def _lf_text(path: Path) -> str:
    return path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")


def _normalize_template(text: str) -> str:
    for token, value in _TEMPLATE_SUBSTITUTIONS.items():
        text = text.replace(token, value)
    return text


def _extract_section(text: str, heading: str, next_heading_prefix: str = "## ") -> str:
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index
            break
    if start is None:
        raise AssertionError(f"missing heading: {heading!r}")
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].startswith(next_heading_prefix):
            end = index
            break
    return "\n".join(lines[start:end])


class P007RestoreApprovalGateContract(unittest.TestCase):
    """G7 deterministic static contract: four required observables over the
    P-007 policy text, asserted identically against the template (with the
    workspace's own variable resolution applied) and the installed dogfood
    mirror."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.template_section = _extract_section(
            _normalize_template(_lf_text(_WORKFLOW_POLICY_TEMPLATE)),
            "## P-007: Backlogit Archive Integrity After Shipment",
        )
        cls.dogfood_section = _extract_section(
            _lf_text(_WORKFLOW_POLICY_DOGFOOD),
            "## P-007: Backlogit Archive Integrity After Shipment",
        )

    def test_files_exist(self) -> None:
        self.assertTrue(_WORKFLOW_POLICY_TEMPLATE.is_file())
        self.assertTrue(_WORKFLOW_POLICY_DOGFOOD.is_file())

    def test_g7_case_i_no_unconditional_restore(self) -> None:
        """(i) NO-APPROVAL CONDITION: no unconditional `git restore` instruction.

        Every IMPERATIVE `git restore` instruction (a "run `git restore ...`"
        construct, case-insensitive on "run" so a future lowercase rephrasing
        cannot slip past) must fall STRICTLY WITHIN the gated Recovery
        procedure sub-block (bounded by its own heading and the section end),
        not merely somewhere textually after an arbitrary gate phrase. This
        scans and classifies EVERY such occurrence, not just the first, per
        Copilot review (PR #446, threads PRRT_kwDORzpWpM6ht-ZZ and
        PRRT_kwDORzpWpM6huu3Z): binding occurrences to "after the
        approval-obtain phrase" alone would not catch a genuine unconditional
        restore inserted anywhere else in the section that happens to sit
        after that phrase textually without actually being inside the gated
        procedure block.
        """
        imperative_restore = re.compile(r"\brun\s+`git restore\b", re.IGNORECASE)
        negation_before_run = re.compile(r"\b(not|never|n't|no)\s*$", re.IGNORECASE)
        recovery_heading = re.compile(r"\*\*Recovery procedure")
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                # The withdrawn pre-fix wording started the violation action
                # with an unconditional numbered restore step. That exact
                # unconditional shape must not reappear.
                self.assertNotRegex(
                    section,
                    r"\*\*Violation Action\*\*:\s*\n\n1\. Run `git restore",
                    "found an unconditional git restore as the first violation-action step",
                )
                g1_index = section.find("G1")
                self.assertGreater(g1_index, -1, "G1 gate clause is missing")

                recovery_match = recovery_heading.search(section)
                self.assertIsNotNone(recovery_match, "Recovery procedure sub-block is missing")
                recovery_start = recovery_match.start()
                # The Recovery procedure block runs from its own heading to
                # the end of the extracted P-007 section (it is the last
                # sub-block before the trailing "---" already stripped by
                # _extract_section).
                recovery_block = section[recovery_start:]
                self.assertIn(
                    "Obtain a live G1 approval result",
                    recovery_block,
                    "recovery procedure does not gate the restore behind an obtained G1 result",
                )

                all_matches = list(imperative_restore.finditer(section))
                self.assertGreater(
                    len(all_matches), 0, "no imperative 'run `git restore' instruction found at all"
                )
                # A negation word (not/never/n't/no) immediately before "run"
                # means this is a PROHIBITION ("do not run `git restore`"),
                # never an actual instruction to execute it — exclude those,
                # but still require at least one genuine (non-negated)
                # imperative occurrence to exist and be gated.
                genuine_instructions = [
                    m for m in all_matches
                    if not negation_before_run.search(section[max(0, m.start() - 15):m.start()])
                ]
                self.assertGreater(
                    len(genuine_instructions), 0,
                    "no genuine (non-negated) imperative 'run `git restore' instruction found",
                )
                for match in genuine_instructions:
                    self.assertGreaterEqual(
                        match.start(),
                        recovery_start,
                        "found a genuine imperative 'run `git restore' instruction at offset "
                        f"{match.start()} that falls OUTSIDE the gated Recovery procedure "
                        f"sub-block (which starts at offset {recovery_start}); every "
                        "occurrence must be bound to the gated procedure, not merely "
                        "positioned after some gate phrase",
                    )
                # The default path is halt/report, tree untouched, P-005 telemetry.
                self.assertIn(
                    "halt, do not run `git restore`, record it through P-005 telemetry",
                    section,
                    "default path is not detect-halt-report-with-P-005-telemetry",
                )
                self.assertIn("leave the working tree untouched", section)

    def test_revalidation_gates_against_stale_approval(self) -> None:
        """Mandatory static coverage for the immediate pre-restore revalidation
        step: a G1 approval matched against deletions observed before the
        operator request must be re-checked against a fresh status read
        immediately before the restore executes, and any drift (a path
        recreated/modified, or the deletion set otherwise changed) must be
        treated as a stale approval requiring a fresh G1 result rather than
        being used to restore. Copilot review (PR #446, thread
        PRRT_kwDORzpWpM6hu4p5): the mismatch test (case ii) only covers
        shipment-ID/path matching at approval time, not this immediate
        second status read, so removing the revalidation step alone would
        not be caught without this dedicated coverage."""
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                self.assertIn(
                    "Revalidate immediately before restoring",
                    section,
                    "no explicit immediate pre-restore revalidation step",
                )
                self.assertIn(
                    "re-run `git status",
                    section,
                    "revalidation does not re-run the status check",
                )
                self.assertIn(
                    "at the moment restoration is about to begin",
                    section,
                    "revalidation is not anchored to the moment restoration begins",
                )
                self.assertIn(
                    "the approval is STALE and MUST NOT be used",
                    section,
                    "no explicit stale-approval refusal",
                )
                self.assertIn(
                    "recreated, modified, or otherwise changed since the approval was matched",
                    section,
                    "stale-approval condition does not name recreated/modified/changed paths",
                )
                self.assertIn(
                    "require a fresh G1 approval matched to the newly-observed state (return to step 1)",
                    section,
                    "no fresh-approval loop back to step 1 on staleness",
                )
                self.assertIn(
                    "never proceed to step 3 with a stale approval",
                    section,
                    "no explicit prohibition on proceeding with a stale approval",
                )
                # Revalidation must appear textually between "obtain" (step 1)
                # and the actual restore command (step 3), inside the same
                # Recovery procedure block.
                obtain_index = section.find("Obtain a live G1 approval result")
                revalidate_index = section.find("Revalidate immediately before restoring")
                restore_index = section.find("Run `git restore --")
                self.assertGreater(obtain_index, -1)
                self.assertGreater(revalidate_index, -1)
                self.assertGreater(restore_index, -1)
                self.assertLess(obtain_index, revalidate_index)
                self.assertLess(revalidate_index, restore_index)

    def test_g7_case_ii_mismatch_is_refusal(self) -> None:
        """(ii) MISMATCH CONDITION: approval result must match shipment ID and
        exact archive paths; mismatch/ambiguity/timeout/unreadable is a refusal."""
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                self.assertIn("CURRENT shipment ID", section)
                self.assertIn("EXACT archive paths", section)
                self.assertRegex(
                    section,
                    r"Mismatch, absence, ambiguity, timeout, or an unreadable channel is a REFUSAL",
                )

    def test_g7_case_iii_self_authorization_negative_and_affirmative(self) -> None:
        """(iii) SELF-AUTHORIZATION NEGATIVE COVERAGE: no clause treats an
        agent-writable artifact as an authorization source, and the
        affirmative G2 clause states the backlog comment is evidence only."""
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                # Affirmative half: G2 explicitly excludes the comment as authority.
                self.assertIn(
                    "This record exists for audit and traceability only. It is NOT read back as authorization",
                    section,
                )
                self.assertIn("is NOT a substitute for a live G1 result", section)
                # Negative half: no clause anywhere in the section grants an
                # agent-writable artifact (comment, telemetry record, file,
                # agent-callable operation) authorization power. Scan every
                # sentence containing "authoriz" and require each one to be
                # part of the permitted negative/affirmative vocabulary.
                permitted_patterns = [
                    r"authorization to run the restore MUST be a LIVE approval RESULT",
                    r"is NOT read back as authorization",
                    r"is NOT a substitute for a live G1 result",
                    r"authorization source",
                    r"is NOT an authorization source",
                    r"gains no new authority",
                    r"destructive-command preauthorization",
                    r"No admin authority is invented",
                    r"No new approval store, file format, or CLI",
                    r"authorized by this policy",
                    r"cannot create it, cannot mark it satisfied",
                    r"Self-authorization negative coverage",
                    r"names the missing authorization channel",
                ]
                sentences = re.split(r"(?<=[.:])\s+", section)
                for sentence in sentences:
                    if "authoriz" not in sentence.lower():
                        continue
                    matched = any(re.search(pattern, sentence) for pattern in permitted_patterns)
                    self.assertTrue(
                        matched,
                        f"sentence mentions authorization outside the permitted vocabulary: {sentence!r}",
                    )
                self.assertIn(
                    "a backlog comment is evidence only and is NOT an authorization source",
                    section,
                )

    def test_g7_case_iv_no_channel_halts_in_all_modes(self) -> None:
        """(iv) NO-CHANNEL CONDITION: halt-without-restore when no independent
        channel is available, in ALL modes, dark-factory/AFK named as an
        instance rather than an exception."""
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                self.assertIn("No independent channel means halt, do not restore", section)
                self.assertIn(
                    "NO independent approval channel is available",
                    section,
                )
                self.assertIn(
                    "dark mode is the specific case of the general G3 rule, not an exception to it",
                    section,
                )
                self.assertIn("Dark-mode / AFK is fail-closed", section)

    def test_g8_refusal_names_channel_and_command(self) -> None:
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                self.assertIn(
                    "the refusal message names the missing authorization channel and the exact command",
                    section,
                )

    def test_g9_no_new_approval_infrastructure(self) -> None:
        for label, section in (("template", self.template_section), ("dogfood", self.dogfood_section)):
            with self.subTest(surface=label):
                self.assertIn("No new approval store, file format, or CLI", section)
                self.assertIn(
                    "No new approval broker, remediation executor, or CLI surface is authorized by this policy",
                    section,
                )

    def test_template_and_dogfood_sections_agree_after_variable_resolution(self) -> None:
        self.assertEqual(
            self.template_section.strip(),
            self.dogfood_section.strip(),
            "template (with known variable resolution) and installed mirror have diverged for P-007",
        )


class ConstitutionReviewerPrincipleChecklistContract(unittest.TestCase):
    """Part 2 (701073F9): the constitution-reviewer checklist must include
    Principle X and Principle XI, with Principle XI's NON-NEGOTIABLE marker
    carried verbatim."""

    def _checklist(self, path: Path) -> str:
        text = _lf_text(path)
        return _extract_section(text, "## Review Focus", next_heading_prefix="## ")

    def test_files_exist(self) -> None:
        self.assertTrue(_CONSTITUTION_REVIEWER_TEMPLATE.is_file())
        self.assertTrue(_CONSTITUTION_REVIEWER_DOGFOOD.is_file())

    def test_principle_x_and_xi_present_in_template_and_dogfood(self) -> None:
        for label, path in (
            ("template", _CONSTITUTION_REVIEWER_TEMPLATE),
            ("dogfood", _CONSTITUTION_REVIEWER_DOGFOOD),
        ):
            with self.subTest(surface=label):
                checklist = self._checklist(path)
                self.assertIn("**Principle X**", checklist, "Principle X missing from checklist")
                self.assertRegex(
                    checklist,
                    r"\*\*Principle XI \(NON-NEGOTIABLE\)\*\*",
                    "Principle XI must carry its NON-NEGOTIABLE marker verbatim",
                )
                # Principles I-IX must remain present (nothing dropped).
                for numeral in ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]:
                    self.assertIn(f"**Principle {numeral}**", checklist)

    def test_template_and_dogfood_checklists_agree(self) -> None:
        self.assertEqual(
            self._checklist(_CONSTITUTION_REVIEWER_TEMPLATE).strip(),
            self._checklist(_CONSTITUTION_REVIEWER_DOGFOOD).strip(),
        )


if __name__ == "__main__":
    unittest.main()
