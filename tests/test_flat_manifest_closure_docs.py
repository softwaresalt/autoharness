"""Doc-contract tests for flat-manifest shipment closure surfaces."""

from __future__ import annotations

from pathlib import Path
import re
import unittest


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

INVARIANT_TOKENS = tuple(f"INV-{index}" for index in range(1, 12))


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


if __name__ == "__main__":
    unittest.main()
