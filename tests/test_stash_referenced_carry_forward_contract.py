"""Contract tests for the stash-referenced companion-document carry-forward text
(P-011 carry-forward set, Ship carry-forward and mid-cycle intake, Stage commit
guidance, and the pipeline-topology gate documentation).

These tests pin the load-bearing instruction text in BOTH each template and its
installed dogfood mirror (four scenarios):

1. P-011 (``workflow-policies``) names the stash-referenced carry-forward set
   (new ``docs/`` file, exact whole-token membership, containment, fail-closed on
   an unreadable stash) and states that carry-forward is intake only.
2. The Ship agent's carry-forward commit consumes ``details.carry_forward_paths``
   including ``details.stash_referenced_paths``, keeps the backlog-only porcelain
   fallback, and defines the isolated ``chore(backlog): carry forward stash
   intake`` mid-cycle commit (never a dedicated branch or PR, never triaged).
3. The Stage agent commits each entry's referenced companion documents in the
   same commit as the entry.
4. The gate documentation names the new ``details`` keys and the qualifying rules,
   and the harness manifest checksums of the touched mirrors match their
   LF-normalized content.
"""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_MANIFEST_PATH = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_POLICIES = {
    "template": _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl",
    "mirror": _REPO_ROOT / ".github" / "policies" / "workflow-policies.md",
}
_SHIPS = {
    "template": _REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl",
    "mirror": _REPO_ROOT / ".github" / "agents" / "_ship.agent.md",
}
_STAGES = {
    "template": _REPO_ROOT / "templates" / "agents" / "_stage.agent.md.tmpl",
    "mirror": _REPO_ROOT / ".github" / "agents" / "_stage.agent.md",
}
_GATE_DOC = _REPO_ROOT / "docs" / "pipeline-topology-gate.md"
_TOUCHED_MIRRORS = (
    ".github/policies/workflow-policies.md",
    ".github/agents/_ship.agent.md",
    ".github/agents/_stage.agent.md",
)


def _read(path: Path) -> str:
    """Read UTF-8 text with CRLF working-tree endings normalized to LF."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _between(text: str, start: str, end: str, where: Path) -> str:
    start_at = text.find(start)
    if start_at < 0:
        raise AssertionError(f"anchor {start!r} not found in {where}")
    end_at = text.find(end, start_at + len(start))
    if end_at < 0:
        raise AssertionError(f"anchor {end!r} not found after {start!r} in {where}")
    return text[start_at:end_at]


class PolicyContractTests(unittest.TestCase):
    def test_p011_names_stash_referenced_carry_forward_set(self) -> None:
        for kind, path in _POLICIES.items():
            with self.subTest(surface=kind):
                text = _read(path)
                p011 = _between(text, "## P-011: Branch-Before-Mutation", "\n## P-012", path)
                for needle in (
                    "stash-referenced companion document",
                    "NEW file (untracked or staged as added) under `docs/`",
                    "whole token",
                    "exact membership only",
                    "no glob, prefix, or directory widening",
                    "the full containment predicate",
                    "Windows reparse point (directory junction)",
                    "unreadable or malformed",
                    "intake only",
                    "P-021 triage stays with Stage",
                    "details.stash_referenced_paths",
                    "chore(backlog): carry forward stash intake",
                ):
                    self.assertIn(needle, p011, f"{needle!r} missing from P-011 in {path}")
                self.assertIn("Commit already-captured stash entries", text, f"P-010 carve-out missing in {path}")


class ShipContractTests(unittest.TestCase):
    def test_carry_forward_consumes_stash_referenced_paths_and_defines_intake(self) -> None:
        for kind, path in _SHIPS.items():
            with self.subTest(surface=kind):
                text = _read(path)
                for needle in (
                    "`details.stash_referenced_paths`",
                    "this fallback never evaluates stash references",
                    "**Mid-cycle stash intake (active shipment branch)**",
                    "chore(backlog): carry forward stash intake",
                    "Never use a dedicated branch or PR for intake",
                    "never triage, prioritize, or add intake to the shipment's scope",
                    "complete P-011 containment predicate",
                ):
                    self.assertIn(needle, text, f"{needle!r} missing from {path}")
                intake = _between(
                    text,
                    "**Mid-cycle stash intake (active shipment branch)**",
                    "git commands above are run as separate sequential steps",
                    path,
                )
                self.assertIn("literal pathspecs", intake)
                self.assertIn("byte-exact", intake)


class StageContractTests(unittest.TestCase):
    def test_stage_commits_companion_documents_with_their_entries(self) -> None:
        for kind, path in _STAGES.items():
            with self.subTest(surface=kind):
                text = _read(path)
                section = _between(
                    text,
                    "### Stash Commit Guidance — Companion Documents (P-011 carry-forward)",
                    "\n##",
                    path,
                )
                for needle in (
                    "**same commit**",
                    "exact repo-relative path",
                    "Archiving an entry",
                    "never triages the entry or changes any shipment's scope",
                    "complete P-011 containment predicate",
                ):
                    self.assertIn(needle, section, f"{needle!r} missing from {path}")


class GateDocAndManifestContractTests(unittest.TestCase):
    def test_gate_doc_and_manifest_checksums(self) -> None:
        doc = _read(_GATE_DOC)
        section = _between(doc, "### Stash-referenced companion documents", "\n## ", _GATE_DOC)
        for needle in (
            "details.stash_referenced_paths",
            "details.stash_reference_warning",
            "New file under `docs/`",
            "Exact whole-token reference",
            "Containment",
            "intake only",
        ):
            self.assertIn(needle, section, f"{needle!r} missing from the gate doc section")
        manifest = yaml.safe_load(_MANIFEST_PATH.read_text(encoding="utf-8"))
        by_path = {entry["path"]: entry for entry in manifest["artifacts"]}
        for rel in _TOUCHED_MIRRORS:
            with self.subTest(mirror=rel):
                self.assertIn(rel, by_path, f"{rel} missing from the harness manifest")
                data = _read(_REPO_ROOT / rel).encode("utf-8")
                self.assertEqual(by_path[rel].get("checksum"), hashlib.sha256(data).hexdigest())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
