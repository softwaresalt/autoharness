"""A5 (214-S): the Orchestrator declares Stage/Ship routes from `routing resolve`, with a declared fallback."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "templates" / "agents" / "_orchestrator.agent.md.tmpl"
MIRROR = ROOT / ".github" / "agents" / "_orchestrator.agent.md"
MANIFEST = ROOT / ".autoharness" / "harness-manifest.yaml"

CONTEXT_TIER_TOKENS = ("context_tier", "ROUTING_DEGRADED: context_tier")
VERSIONED_CLAUSE = "schema version matching the document's own `schema_version`"


def lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def site_line(path: Path, role: str) -> str:
    marker = f"**Resolve {role}'s routed model (P-013.5, NON-NEGOTIABLE)**"
    matches = [line for line in lines(path) if marker in line]
    assert len(matches) == 1, f"{path.name}: expected one {role} invocation site, found {len(matches)}"
    return matches[0]


class OrchestratorRoutingCliDirectiveTests(unittest.TestCase):
    def test_both_sites_name_the_cli_and_the_declared_fallback(self):
        for path in (TEMPLATE, MIRROR):
            for role, site in (("Stage", "stage"), ("Ship", "ship")):
                with self.subTest(file=path.name, site=site):
                    line = site_line(path, role)
                    self.assertIn(f"autoharness routing resolve --workspace . --site {site} --json", line)
                    self.assertIn("TOOL_OK: routing-resolver-cli", line)
                    self.assertIn("TOOL_DEGRADED: routing-resolver-cli", line)

    def test_exit_codes_are_stated_at_both_sites(self):
        for path in (TEMPLATE, MIRROR):
            for role in ("Stage", "Ship"):
                with self.subTest(file=path.name, site=role):
                    line = site_line(path, role)
                    self.assertIn("exit `2`", line)
                    self.assertIn("HALT", line)
                    self.assertIn("exit `1` is not a failure", line)

    def test_existing_directive_tokens_survive_at_both_sites(self):
        for path in (TEMPLATE, MIRROR):
            for role in ("Stage", "Ship"):
                for token in CONTEXT_TIER_TOKENS:
                    with self.subTest(file=path.name, site=role, token=token):
                        self.assertIn(token, site_line(path, role))
                self.assertIn("ROUTING_DEGRADED:", site_line(path, role))

    def test_versioned_schema_clause_in_template_and_mirror(self):
        for path in (TEMPLATE, MIRROR):
            with self.subTest(file=path.name):
                text = " ".join(path.read_text(encoding="utf-8").split())
                self.assertIn(VERSIONED_CLAUSE, text)

    def test_manifest_checksum_matches_the_committed_mirror(self):
        manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
        entry = next(a for a in manifest["artifacts"] if a["path"] == ".github/agents/_orchestrator.agent.md")
        blob = MIRROR.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(entry["checksum"], hashlib.sha256(blob).hexdigest())


if __name__ == "__main__":
    unittest.main()
