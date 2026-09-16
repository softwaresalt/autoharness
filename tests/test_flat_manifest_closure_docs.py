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

    def test_contract_files_omit_withdrawn_or_unsound_claims(self) -> None:
        for label, text in self._read_contract_texts():
            with self.subTest(path=label):
                self.assertNotIn("VERIFIED FULLY-COVERED-ROOT EXCEPTION", text)
                self.assertNotIn("fully covered", text.casefold())
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
