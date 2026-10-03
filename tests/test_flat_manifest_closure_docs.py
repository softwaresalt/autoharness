"""Doc-contract tests for flat-manifest shipment closure surfaces."""

from __future__ import annotations

from pathlib import Path
import re
import unittest

from autoharness.shipment_close import runner as _runner

try:
    from _assertion_render import render_source
except ModuleNotFoundError:  # pragma: no cover - module path differs by runner
    from tests._assertion_render import render_source

_REPO_ROOT = Path(__file__).resolve().parents[1]

CONTRACT_FILES = (
    Path(".github") / "policies" / "workflow-policies.md",
    Path("templates") / "policies" / "workflow-policies.md.tmpl",
    Path(".github") / "skills" / "shipment-reconcile" / "SKILL.md",
    Path("templates") / "skills" / "shipment-reconcile" / "SKILL.md.tmpl",
)

# The Ship agent files are deliberate "thin pointer" surfaces: they reference
# the authoritative P-015/shipment-reconcile contract rather than re-deriving
# its full invariant/vocabulary set (D1A_TERMS, INVARIANT_TOKENS, the exact
# parsed-scalar rule, etc. are intentionally NOT restated here). They are kept
# out of CONTRACT_FILES for that reason, but they still embed a summary of the
# close-path decision and MUST NOT retain the withdrawn fully-covered-root
# predicate that summary once described — see
# ``test_ship_agent_files_omit_withdrawn_fully_covered_root_claims`` below.
SHIP_AGENT_CONTRACT_FILES = (
    Path(".github") / "agents" / "_ship.agent.md",
    Path("templates") / "agents" / "_ship.agent.md.tmpl",
)

D1A_TERMS = (
    "manifest_scope",
    "closure_scope",
    "allowed_ids",
    "required_ids",
    "validated_linked_deliberations",
)

INVARIANT_TOKENS = tuple(f"INV-{index}" for index in range(1, 13))


class FlatManifestClosureDocContractTests(unittest.TestCase):
    def _read_contract_texts(self) -> list[tuple[str, str]]:
        repo_root = Path.cwd().resolve(strict=True)
        return [
            (str(path).replace("\\", "/"), (repo_root / path).read_text(encoding="utf-8"))
            for path in CONTRACT_FILES
        ]

    def _read_ship_agent_texts(self) -> list[tuple[str, str]]:
        repo_root = Path.cwd().resolve(strict=True)
        return [
            (str(path).replace("\\", "/"), (repo_root / path).read_text(encoding="utf-8"))
            for path in SHIP_AGENT_CONTRACT_FILES
        ]

    def test_ship_agent_files_omit_withdrawn_fully_covered_root_claims(self) -> None:
        """The Ship agent's own closure-tasks summary must reflect the P-015
        flat-manifest/engine-inertness model, never the withdrawn
        fully-covered-root children-walk predicate it previously described."""

        for label, text in self._read_ship_agent_texts():
            with self.subTest(path=label):
                self.assertNotIn("VERIFIED FULLY-COVERED-ROOT EXCEPTION", text)
                self.assertNotIn("fully covered", text.casefold())
                self.assertNotRegex(
                    text,
                    re.compile(r"(?i)P-015 (?:verified )?fully-covered-root"),
                )
                self.assertIn("classify_shipment_close_path", text)
                self.assertIn("CASCADE", text)
                self.assertIn("SAFE_CLOSE", text)

    def test_contract_files_define_scope_vocabulary_and_invariants(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                for term in D1A_TERMS:
                    self.assertIn(term, text)
                for token in INVARIANT_TOKENS:
                    self.assertIn(token, text)

    def test_contract_files_define_flat_scope_and_split_delivery_limit(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                self.assertIn("closure_scope(S)", text)
                self.assertIn("items(S) ∪ {S}", text)
                self.assertRegex(text, r"Ancestry[^\n]+(?:never|NOT)")
                self.assertIn("contract-complete", text)
                self.assertIn("operationally blocked", text)
                if label.endswith(".tmpl"):
                    # Generic templates MUST NOT hardcode a workspace-local stash
                    # ID: target workspaces will not have `7F9CB5E9`, so the
                    # tracking reference must instead be resolvable/generic.
                    self.assertNotIn("7F9CB5E9", text)
                    self.assertIn(
                        "durable active stash entry local to this workspace's own backlog",
                        text,
                    )
                else:
                    self.assertIn("7F9CB5E9", text)
                self.assertRegex(text, r"INV-8[^\n]+(?:assembly convention|Stage assembly)")
                self.assertRegex(text, r"INV-8[^\n]+NOT a closure precondition")

    def test_contract_files_define_exact_parsed_scalar_rule(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                self.assertIn('isinstance(status, str) and status == "archived"', text)
                self.assertIn("status: yes", text)
                self.assertIn("status:", text)
                self.assertIn("fail closed", text)
                self.assertIn("no .lower()", text)
                self.assertIn("no .strip()", text)
                self.assertIn("casefold", text)
                self.assertIn("alias", text)
                self.assertIn("str()", text)

    def test_contract_files_define_torn_duplicate_rule_and_rollback_sequence(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                self.assertRegex(text, r"SAFE_CLOSE")
                self.assertRegex(text, r"more than one record|torn|duplicate")
                self.assertIn("capture evidence", text.casefold())
                self.assertIn("HALT", text)
                self.assertIn("P-005", text)
                self.assertIn("EXPLICIT operator approval", text)
                self.assertIn("REVALIDATE", text)
                self.assertIn("ONLY the approved rollback", text)

    def test_contract_files_define_refused_transition_halt_without_substitution(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                self.assertIn("RECONCILE_FAIL_NO_SAFE_RECORD_TRANSITION", text)
                self.assertRegex(text, r"must NOT be substituted|no substitution")
                self.assertIn("archived_status: shipped", text)

    def test_cascade_procedure_defines_baseline_fingerprint_invariance_check(self) -> None:
        """The Cascade Close Sub-Procedure's INV-7/INV-10 baseline-fingerprint
        capture-and-verify pair must be present, in full, in BOTH the
        installed ``SKILL.md`` and its ``.tmpl`` mirror. This guards against
        exactly the divergence Copilot review flagged on PR #454 (round 5):
        a fix landed in the installed copy without being mirrored into the
        generic template, so freshly-installed workspaces would silently
        lack the post-invocation invariance gate entirely."""

        skill_paths = tuple(
            path for path in CONTRACT_FILES if "shipment-reconcile" in str(path)
        )
        self.assertEqual(len(skill_paths), 2)
        repo_root = Path.cwd().resolve(strict=True)
        for path in skill_paths:
            label = str(path).replace("\\", "/")
            text = (repo_root / path).read_text(encoding="utf-8")
            with self.subTest(path=label):
                self.assertIn("Baseline-fingerprint capture (INV-7, before invocation)", text)
                self.assertIn(
                    "Verify out-of-manifest descendant baseline invariance (INV-7/INV-10,",
                    text,
                )
                self.assertIn(
                    "HALT — cascade modified out-of-manifest descendant {id}, revert",
                    text,
                )
                self.assertIn("byte-identical to its step-5 baseline fingerprint", text)
                # The withdrawn claim that CASCADE-qualifying manifests have
                # "no protected set" and therefore need no descendant
                # safeguard is no longer true under the flat-manifest
                # engine-inertness model (Copilot review, PR #454, round 6):
                # CASCADE can now qualify precisely when out-of-manifest
                # descendants exist but are already archived, and those
                # descendants are safeguarded by the baseline-fingerprint
                # capture/verify pair above, not left unprotected.
                self.assertNotIn("so no protected set arises\non this path", text)
                self.assertIn("no protected set **in the Safe-Close\nsense**", text)
                self.assertIn(
                    "this is not the same as saying no\nout-of-manifest state requires safeguarding here",
                    text,
                )

    def test_contract_files_omit_withdrawn_or_unsound_claims(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                self.assertNotIn("VERIFIED FULLY-COVERED-ROOT EXCEPTION", text)
                self.assertNotIn("fully covered", text.casefold())
                self.assertNotRegex(
                    text,
                    re.compile(r"(?i)P-015 (?:verified )?fully-covered-root"),
                )
                self.assertNotIn("git show --stat e4ca20e5", text)
                self.assertNotIn("close-only", text)
                self.assertNotRegex(text, re.compile(r"(?i)fixture[^\n]{0,120}prove[^\n]{0,120}engine"))
                self.assertNotRegex(text, re.compile(r"(?i)operationally complete|end-to-end supported"))
                self.assertNotRegex(
                    text,
                    re.compile(r"(?i)(?:automatic|immediate|notification-only)[^\n]{0,120}git (?:restore|revert)"),
                )
                if "TERMINAL_CLOSE" in text:
                    self.assertIn("SUPERSEDED PROVENANCE ONLY", text)


# P-015 policy-only assertions (195-F slice 2, 197-F). These iterate ONLY the
# two policy files; the shared CONTRACT_FILES invariant token sweep above now
# covers policy and shipment-reconcile skill files through INV-12.
POLICY_FILES = tuple(path for path in CONTRACT_FILES if "workflow-policies" in str(path))


class FlatSetPolicyContractTests(unittest.TestCase):
    """197.008-T scenarios A-b, A-c, A-d."""

    def _read_policy_texts(self) -> list[tuple[str, str]]:
        repo_root = Path.cwd().resolve(strict=True)
        self.assertEqual(len(POLICY_FILES), 2)
        return [
            (str(path).replace("\\", "/"), (repo_root / path).read_text(encoding="utf-8"))
            for path in POLICY_FILES
        ]

    def test_a_b_allowed_ids_row_is_flat_closure_scope(self) -> None:
        for label, text in self._read_policy_texts():
            with self.subTest(path=label):
                self.assertIn("| **`allowed_ids(S)`** | `closure_scope(S)` |", text)
                self.assertIn("x ∈ items(S) : x is not already truly archived", text)
                self.assertIn("over every manifest item regardless of its `artifact_type`", text)

    def test_a_c_linked_deliberation_union_is_absent(self) -> None:
        for label, text in self._read_policy_texts():
            with self.subTest(path=label):
                self.assertNotIn("closure_scope(S) ∪ validated_linked_deliberations(S)", text)

    def test_a_d_cascade_requires_verified_engine_semantics(self) -> None:
        for label, text in self._read_policy_texts():
            with self.subTest(path=label):
                self.assertIn("select_close_path", text)
                self.assertIn("ENGINE_SEMANTICS_UNVERIFIED", text)
                self.assertIn("assess_cascade_engine_semantics", text)
                self.assertIn("Verified engine-semantics lines: `1.11`", text)
                self.assertIn("depends on `archive_item` semantics", text)
                self.assertNotRegex(text, re.compile(r"(?i)SAFE_CLOSE[^\n]{0,80}always valid"))


LINKED_DELIBERATION_OUTCOMES = (
    "archived",
    "already-archived",
    "retained_read_error",
    "retained_engine_unverified",
    "retained_ambiguous",
    "retained_live_status",
    "retained_shared_reference",
    "retained_description_mention",
)


class Inv12PolicyContractTests(unittest.TestCase):
    """197.010-T scenarios A-a, A-f, A-g (policy files only)."""

    _read_policy_texts = FlatSetPolicyContractTests._read_policy_texts

    def _inv12_bullet(self, text: str) -> str:
        match = re.search(
            r"^\* \*\*INV-12 \(Linked-deliberation disposition\)\.\*\*[^\n]+", text, re.MULTILINE
        )
        self.assertIsNotNone(match)
        return match.group(0)

    def test_a_a_policy_files_define_inv_12(self) -> None:
        for label, text in self._read_policy_texts():
            with self.subTest(path=label):
                self.assertIn("INV-12", text)
                bullet = self._inv12_bullet(text)
                self.assertIn("`LinkedDeliberationOutcome` is the closed enum", bullet)
                self.assertIn("single-artifact, non-cascading archive", bullet)
                self.assertIn("never widens `closure_scope(S)`", bullet)
                self.assertIn("SUPERSESSION NOTE (2026-09-29)", text)
                self.assertIn("`5a4b70dd`", text)
                self.assertIn("TestUArchiveCandidateFlat_UnlistedLinkedDeliberationIsUntouched", text)
                self.assertRegex(text, r"\| 1\.28\.0 +\| [^|]+\| Corrected P-015")

    def test_a_f_disposition_set_excludes_closure_scope_h10(self) -> None:
        for label, text in self._read_policy_texts():
            with self.subTest(path=label):
                self.assertIn(
                    "The disposition set excludes self-references and every ID in "
                    "`closure_scope(S)` (H10)",
                    text,
                )

    def test_a_g_outcome_vocabulary_and_reason_code_sentence(self) -> None:
        for label, text in self._read_policy_texts():
            with self.subTest(path=label):
                bullet = self._inv12_bullet(text)
                for outcome in LINKED_DELIBERATION_OUTCOMES:
                    self.assertIn(f"`{outcome}`", bullet)
                self.assertIn(
                    "Each outcome carries a `reason_code`, which defaults to the outcome value",
                    bullet,
                )
                for reason_code in (
                    "path_escape",
                    "symlink_or_reparse_point",
                    "unreadable_file",
                    "malformed_frontmatter",
                    "body_unseparable",
                    "malformed_stash_entry",
                ):
                    self.assertIn(f"`{reason_code}`", bullet)


# 198.007-T rendered-region parity (A-i). Every tolerated template/mirror
# divergence in the compared regions is named here. `{{FEATURE_SHIPMENTS}}`,
# `{{BACKLOG_DIRECTORY}}` and `{{DATE}}` are tolerated by rendering the
# template with `render_source`; the workspace-local stash IDs are tolerated
# by mapping the template's generic wording onto the mirror's concrete ID
# (`8928EC67` is the engine-behavior registry the U2a SAFE_CLOSE reliance
# paragraph already names in the mirror). Longest pattern first.
POLICY_PARITY_ALLOWLIST = (
    (
        "a durable active stash entry local to this workspace's own backlog "
        "(the backlogit engine-behavior compatibility registry)",
        "general registry `8928EC67`",
    ),
    (
        "a durable active stash entry local to this workspace's own backlog",
        "durable active stash entry `7F9CB5E9`",
    ),
)

# Stable line anchors of the P-015 paragraphs edited by U2a (197.007-T and
# 197.009-T, which was 198.001-T).
U2A_PARITY_ANCHORS = (
    "**SUPERSESSION NOTE (2026-09-29).**",
    "| **`allowed_ids(S)`**",
    "| **`required_ids(S)`**",
    "`validated_linked_deliberations(S)` is the **disposition set**",
    "**Engine-semantics precondition (CASCADE).**",
    "**SAFE_CLOSE reliance.**",
    "* **INV-1 (",
    "* **INV-6 (",
    "* **INV-12 (",
)


class PolicyU2aRenderedRegionParityTests(unittest.TestCase):
    """198.007-T scenario A-i: the U2a paragraphs of the rendered policy
    template match the installed mirror, modulo the named allowlist."""

    def test_a_i_u2a_paragraphs_rendered_region_parity(self) -> None:
        rendered = render_source(".github/policies/workflow-policies.md")
        mirror = (_REPO_ROOT / ".github" / "policies" / "workflow-policies.md").read_text(
            encoding="utf-8"
        )
        for anchor in U2A_PARITY_ANCHORS:
            with self.subTest(anchor=anchor):
                expected = [line for line in rendered.splitlines() if line.startswith(anchor)]
                actual = [line for line in mirror.splitlines() if line.startswith(anchor)]
                self.assertEqual(len(expected), 1)
                self.assertEqual(len(actual), 1)
                region = expected[0]
                for template_text, mirror_text in POLICY_PARITY_ALLOWLIST:
                    region = region.replace(template_text, mirror_text)
                self.assertEqual(actual[0], region)


# 192.021-T (plan unit A5c): closure-routing doc assertions over the A5
# (192.008-T, shipment-reconcile) and A5b (192.020-T, operational-closure)
# edits. Every assertion runs against both the template and its installed
# mirror, so removing a pinned phrase from either one fails.
RECONCILE_INSTALLED = ".github/skills/shipment-reconcile/SKILL.md"
RECONCILE_FILES = (
    Path(".github") / "skills" / "shipment-reconcile" / "SKILL.md",
    Path("templates") / "skills" / "shipment-reconcile" / "SKILL.md.tmpl",
)
CLOSURE_SKILL_INSTALLED = ".github/skills/operational-closure/SKILL.md"
CLOSURE_SKILL_FILES = (
    Path(".github") / "skills" / "operational-closure" / "SKILL.md",
    Path("templates") / "skills" / "operational-closure" / "SKILL.md.tmpl",
)

ROUTING_MARKERS = ("step-0c", "cascade-sub-procedure", "disposition-inputs")
STEP_0C_START = "   c. **Classify the close path**"
STEP_0C_END = "1. **Load manifest** via"
CASCADE_SUB_PROCEDURE_HEADING = "### Cascade Close Sub-Procedure (P-015 `CASCADE` exception ONLY)"
DISPOSITION_HEADING = "### Linked-Deliberation Disposition (P-015 INV-12)"
CLOSURE_OUTPUT_HEADING = "## Output"
CLOSURE_STEP_3A_HEADING = "### Step 3a: Validate the Closure Artifact with the Closure-Evidence Gate"

CLASSIFY_ONLY_INVOCATION = (
    "`autoharness shipment cascade-close --classify-only --shipment <shipment_id> "
    "--feature <feature_id> --sha <merge_commit_sha> --json`"
)
MUTATING_INVOCATION = (
    "`autoharness shipment cascade-close --shipment <shipment_id> --feature <feature_id> "
    "--sha <merge_commit_sha> --message <merge_commit_message> --author "
    "<merge_commit_author> --json`"
)
ROUTING_TABLE_ROWS = (
    "| Mode | Exit | Skill action |",
    "| `--classify-only` | 0 (`CASCADE`) | Obtain destructive-command approval, then run the mutating `cascade-close`",
    "| `--classify-only` | 3 (`SAFE_CLOSE` selected: classifier `SAFE_CLOSE`, or engine `UNVERIFIED`) | Safe-close steps 1–10, then the Linked-Deliberation Disposition step, citing the verdict record as `close_evidence` |",
    "| mutating | 0 | Run the Linked-Deliberation Disposition step with its inputs from the evidence record, then write the closure artifact with `close_path: cascade` and `close_evidence` |",
    "| mutating | 3 | Reached only when no `cascade`-selected `--classify-only` record preceded the run",
    "| either | 2, 4 | HALT. Nothing was mutated.",
    "| either | 5, 6, 7, 8 | HALT. Operator review. No commit of the backlog root, no retry, no direct call |",
)
PRE_CLOSE_FIELDS = (
    "`pre_close.engine_semantics`",
    "`pre_close.close_path_selection`",
    "`pre_close.linked_deliberation_disposition`",
)
# Every tolerated rendered-template/mirror divergence inside the compared
# shipment-reconcile regions, named explicitly (template text -> mirror text).
# Both pre-date A5: the mirror pins this workspace's own verified commits and
# its concrete stash ID where the template stays generic.
RECONCILE_PARITY_ALLOWLIST = (
    (
        "verify via a path-scoped `git diff --stat <verified-commit-a> <verified-commit-b> -- "
        "<archived-artifact-path-a> <archived-artifact-path-b>` returning empty, and "
        "`git rev-parse <verified-commit-a>:<path>` / `git rev-parse <verified-commit-b>:<path>` "
        "returning identical blob OIDs for each path in this workspace's own history.",
        "path-scoped `git diff --stat 358b63b4 e4ca20e5 -- .backlogit/archive/165.007-T.md "
        ".backlogit/archive/165.010-T.md` is empty, and `git rev-parse 358b63b4:<path>` / "
        "`git rev-parse e4ca20e5:<path>` return identical blob OIDs for both paths.",
    ),
    (
        "tracked by a durable active stash entry local to this workspace's own backlog",
        "tracked by durable active stash entry `7F9CB5E9`",
    ),
)

# A closure-filename restatement (same heuristic as the closure-contract
# non-drift test): edited surfaces must not define a closure filename.
_CLOSURE_FILENAME_RESTATEMENT = re.compile(r"closure(?:\\+)?\.md|post-merge-closure", re.IGNORECASE)


def _evidence_path_doc() -> str:
    """The documented evidence path, derived from the A1 contract constants so a
    drift between the docs and `build_evidence_path` fails here."""
    from autoharness.gates.cascade_evidence import EVIDENCE_DIR, EVIDENCE_FILENAME_TEMPLATE

    return f"{EVIDENCE_DIR.as_posix()}/{EVIDENCE_FILENAME_TEMPLATE}"


def _lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def _read_pair(paths: tuple[Path, ...]) -> list[tuple[str, str]]:
    return [
        (str(path).replace("\\", "/"), _lf((_REPO_ROOT / path).read_text(encoding="utf-8")))
        for path in paths
    ]


def _marker_region(text: str, name: str) -> str:
    begin = f"<!-- cascade-close-routing:BEGIN {name} -->"
    end = f"<!-- cascade-close-routing:END {name} -->"
    assert text.count(begin) == 1 and text.count(end) == 1, f"marker {name} must appear exactly once"
    start = text.index(begin)
    return text[start : text.index(end, start) + len(end)]


def _line_region(text: str, start_prefix: str, end_prefix: str) -> str:
    lines = text.split("\n")
    starts = [index for index, line in enumerate(lines) if line.startswith(start_prefix)]
    assert len(starts) == 1, f"{start_prefix!r} must start exactly one line"
    for index in range(starts[0] + 1, len(lines)):
        if lines[index].startswith(end_prefix):
            return "\n".join(lines[starts[0] : index])
    raise AssertionError(f"{end_prefix!r} not found after {start_prefix!r}")


def _heading_section(text: str, heading: str) -> str:
    level = len(heading) - len(heading.lstrip("#"))
    lines = text.split("\n")
    assert lines.count(heading) == 1, f"heading {heading!r} must appear exactly once"
    start = lines.index(heading)
    for index in range(start + 1, len(lines)):
        match = re.match(r"^(#+) ", lines[index])
        if match and len(match.group(1)) <= level:
            return "\n".join(lines[start:index])
    return "\n".join(lines[start:])


class ClosureRoutingStructuralTests(unittest.TestCase):
    """192.021-T scenario 1: structural assertions over the A5 and A5b edits."""

    def test_shipment_reconcile_step_0c_routes_through_classify_only(self) -> None:
        for label, text in _read_pair(RECONCILE_FILES):
            with self.subTest(path=label):
                block = _marker_region(text, "step-0c")
                self.assertIn(block, _line_region(text, STEP_0C_START, STEP_0C_END))
                self.assertIn("Every close, on either path, first runs", block)
                self.assertIn(CLASSIFY_ONLY_INVOCATION, block)
                for field in PRE_CLOSE_FIELDS:
                    self.assertIn(field, block)
                self.assertIn(f"`{_evidence_path_doc()}`", block)
                self.assertIn("stays the specification the command implements", block)
                for row in ROUTING_TABLE_ROWS:
                    self.assertIn(row, block)

    def test_destructive_approval_and_p005_wording(self) -> None:
        for label, text in _read_pair(RECONCILE_FILES):
            with self.subTest(path=label):
                block = _marker_region(text, "step-0c")
                self.assertIn(
                    "Plain `--classify-only` needs no operator approval: it is no-clobber", block
                )
                self.assertIn(
                    "`--classify-only --replace-pre-close` overwrites\n      an existing "
                    "`pre_close` record and needs the same destructive-command\n      approval",
                    block,
                )
                self.assertIn("**is** the destructive command", block)
                self.assertIn("that a direct `backlogit shipment ship` call needs", block)
                self.assertIn("MCP or `backlogit shipment ship` CLI call is", block)
                self.assertIn("a **P-005 deviation** on either path", block)

    def test_cascade_sub_procedure_routes_through_mutating_command(self) -> None:
        for label, text in _read_pair(RECONCILE_FILES):
            with self.subTest(path=label):
                section = _heading_section(text, CASCADE_SUB_PROCEDURE_HEADING)
                block = _marker_region(text, "cascade-sub-procedure")
                self.assertIn(block, section)
                self.assertIn(MUTATING_INVOCATION, block)
                self.assertIn("engine-semantics\nre-probe), the baseline-fingerprint capture, step 1's invocation, and\nsteps 2–6", block)
                self.assertIn("exits 4 with nothing mutated", block)
                self.assertIn("never a `SAFE_CLOSE` substitution", block)
                self.assertIn("**P-005 deviation**", block)
                self.assertIn("the Linked-Deliberation Disposition step stays its only\narchiver", block)
                self.assertIn("1. The mutating `autoharness shipment cascade-close` invokes the cascade", section)
                self.assertIn("It is the only invoker; Ship never issues this\n   call directly.", section)
                self.assertNotIn("directly\n   (CLI: `backlogit shipment ship", section)

    def test_disposition_inputs_come_from_the_evidence_record(self) -> None:
        for label, text in _read_pair(RECONCILE_FILES):
            with self.subTest(path=label):
                section = _heading_section(text, DISPOSITION_HEADING)
                block = _marker_region(text, "disposition-inputs")
                self.assertIn(block, section)
                self.assertIn("It takes every input from the evidence record", block)
                self.assertIn(f"`{_evidence_path_doc()}`", block)
                self.assertIn("never\n   from in-session Step 0(c) state, and never recomputes one", block)
                for source in (
                    "from `pre_close.close_path_selection`",
                    "from `pre_close.engine_semantics`",
                    "`engine_semantics_from_record`",
                    "`pre_close.linked_deliberation_disposition`",
                    "from `pre_close.observation_set` (`SAFE_CLOSE`)",
                    "from `pre_close.out_of_manifest_descendants` (`CASCADE`)",
                ):
                    self.assertIn(source, section)
                self.assertIn("steps 1–6 below run exactly as stated", section)

    def test_operational_closure_records_close_path_and_close_evidence(self) -> None:
        for label, text in _read_pair(CLOSURE_SKILL_FILES):
            with self.subTest(path=label):
                output = _heading_section(text, CLOSURE_OUTPUT_HEADING)
                keys = [line for line in output.split("\n") if line.startswith("  * **Close-path keys (192-F)**")]
                self.assertEqual(len(keys), 1)
                self.assertIn("`close_path` (`cascade` or `safe_close`)", keys[0])
                self.assertIn(f"`close_evidence`, the workspace-relative path `{_evidence_path_doc()}`", keys[0])
                self.assertIn("committed in the same commit as the closure artifact", keys[0])
                step_3a = _heading_section(text, CLOSURE_STEP_3A_HEADING)
                self.assertIn("* **`close_path` and `close_evidence` (192-F)**", step_3a)
                self.assertIn("`failed_check`\n  `close_path`", step_3a)
                self.assertIn("(`failed_check` `close_evidence`)", step_3a)

    def test_no_edited_surface_places_a_linked_deliberation_in_the_flat_sets(self) -> None:
        regions = []
        for label, text in _read_pair(RECONCILE_FILES):
            for name in ROUTING_MARKERS:
                regions.append((f"{label}:{name}", _marker_region(text, name)))
        for label, text in _read_pair(CLOSURE_SKILL_FILES):
            regions.append((f"{label}:output", _heading_section(text, CLOSURE_OUTPUT_HEADING)))
            regions.append((f"{label}:step-3a", _heading_section(text, CLOSURE_STEP_3A_HEADING)))
        for label, region in regions:
            with self.subTest(region=label):
                for line in region.split("\n"):
                    if "allowed_ids" in line or "required_ids" in line:
                        self.assertNotIn("deliberation", line.casefold())
                self.assertNotIn("validated_linked_deliberations(S)", region)


class ClosureRoutingRenderedParityTests(unittest.TestCase):
    """192.021-T scenario 2 (AN-F05): LF-normalized rendered-template/mirror
    parity for every edited section, modulo the named allowlist."""

    @staticmethod
    def _reconcile_pair() -> tuple[str, str]:
        rendered = _lf(render_source(RECONCILE_INSTALLED))
        mirror = _lf((_REPO_ROOT / RECONCILE_INSTALLED).read_text(encoding="utf-8"))
        return rendered, mirror

    def test_step_0c_block_parity(self) -> None:
        rendered, mirror = self._reconcile_pair()
        expected = _line_region(rendered, STEP_0C_START, STEP_0C_END)
        for template_text, mirror_text in RECONCILE_PARITY_ALLOWLIST:
            expected = expected.replace(template_text, mirror_text)
        self.assertEqual(_line_region(mirror, STEP_0C_START, STEP_0C_END), expected)

    def test_cascade_sub_procedure_and_marker_region_parity(self) -> None:
        rendered, mirror = self._reconcile_pair()
        self.assertEqual(
            _heading_section(mirror, CASCADE_SUB_PROCEDURE_HEADING),
            _heading_section(rendered, CASCADE_SUB_PROCEDURE_HEADING),
        )
        for name in ROUTING_MARKERS:
            with self.subTest(marker=name):
                self.assertEqual(_marker_region(mirror, name), _marker_region(rendered, name))

    def test_operational_closure_frontmatter_block_parity(self) -> None:
        rendered = _lf(render_source(CLOSURE_SKILL_INSTALLED))
        mirror = _lf((_REPO_ROOT / CLOSURE_SKILL_INSTALLED).read_text(encoding="utf-8"))
        for heading in (CLOSURE_OUTPUT_HEADING, CLOSURE_STEP_3A_HEADING):
            with self.subTest(section=heading):
                self.assertEqual(_heading_section(mirror, heading), _heading_section(rendered, heading))


class ClosureRoutingNonDriftTests(unittest.TestCase):
    """192.021-T scenario 3: the Step 3a heading stays verbatim and no edited
    surface restates a closure filename outside the contract-derived form.
    ``tests/test_closure_contract_nondrift.py`` stays green unchanged."""

    def test_step_3a_heading_is_verbatim(self) -> None:
        for label, text in _read_pair(CLOSURE_SKILL_FILES):
            with self.subTest(path=label):
                self.assertEqual(text.split("\n").count(CLOSURE_STEP_3A_HEADING), 1)

    def test_edited_surfaces_restate_no_closure_filename(self) -> None:
        regions = []
        for label, text in _read_pair(RECONCILE_FILES):
            for name in ROUTING_MARKERS:
                regions.append((f"{label}:{name}", _marker_region(text, name)))
        for label, text in _read_pair(CLOSURE_SKILL_FILES):
            output = _heading_section(text, CLOSURE_OUTPUT_HEADING)
            keys = [line for line in output.split("\n") if line.startswith("  * **Close-path keys (192-F)**")]
            regions.append((f"{label}:close-path-keys", "\n".join(keys)))
            step_3a = _heading_section(text, CLOSURE_STEP_3A_HEADING)
            regions.append(
                (f"{label}:step-3a-close-keys", step_3a[step_3a.index("* **`close_path` and `close_evidence`"):])
            )
        for label, region in regions:
            with self.subTest(region=label):
                self.assertTrue(region.strip())
                self.assertIsNone(_CLOSURE_FILENAME_RESTATEMENT.search(region))


# 192.026-T (A8d): the cascade-close --timeout range, default and sizing rule
# are pinned to the runner constants on whitespace-collapsed text, so neither
# docs/gates-reference.md nor the shipment-reconcile sizing note can drift
# from MIN/DEFAULT/MAX_TIMEOUT_SECONDS again.
GATES_REFERENCE = Path("docs") / "gates-reference.md"
TIMEOUT_SIZING_HEADING = "### Timeout sizing"
_SIZING_FORMULA = "B = ceil(1.5 * (F + P * N))"
_RANGE_TOKEN = (
    f"`--timeout` is {_runner.MIN_TIMEOUT_SECONDS}-{_runner.MAX_TIMEOUT_SECONDS} seconds "
    f"(default {_runner.DEFAULT_TIMEOUT_SECONDS})"
)


def _collapse(text: str) -> str:
    return " ".join(text.split())


class CascadeCloseTimeoutDocPinTests(unittest.TestCase):
    """192.026-T: the documented --timeout range, default and sizing rule match the runner."""

    def test_gates_reference_timeout_range_and_sizing_section(self) -> None:
        text = _lf((_REPO_ROOT / GATES_REFERENCE).read_text(encoding="utf-8"))
        self.assertIn(_RANGE_TOKEN, _collapse(text))
        self.assertNotIn("30-900", text)
        self.assertNotIn("default 120", text)
        self.assertEqual(text.split("\n").count(TIMEOUT_SIZING_HEADING), 1)
        section = _collapse(_heading_section(text, TIMEOUT_SIZING_HEADING))
        self.assertIn(_SIZING_FORMULA, section)
        self.assertRegex(section, rf"B > {_runner.MAX_TIMEOUT_SECONDS}: HALT\b")

    def test_shipment_reconcile_sizing_note(self) -> None:
        for label, text in _read_pair(RECONCILE_FILES):
            with self.subTest(path=label):
                region = _collapse(_marker_region(text, "cascade-sub-procedure"))
                self.assertIn(_SIZING_FORMULA, region)
                self.assertIn(_RANGE_TOKEN, region)
                self.assertRegex(region, rf"B > {_runner.MAX_TIMEOUT_SECONDS}[^.]*HALT")
                self.assertIn("stays attached to the run until the command exits", region)
                self.assertIn("the most specific applicable limit governs", region)
                self.assertNotIn("30-900", text)
                self.assertNotIn("docs/gates-reference.md", text)


if __name__ == "__main__":
    unittest.main()
