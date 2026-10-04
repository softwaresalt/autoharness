"""verify_workspace frontmatter-conformity migration proposals (193-F B2b, 193.005-T).

Ordered action rules 1-8 (first match wins), the complete proposal payload,
status/severity per class, rendered-candidate validation in installed mode
(AS-F8, AN-F10), community template containment (AS-F9), community
idempotence (AS-F7), Markdown parity (AN-F2), and no writes outside staging.

Plan: docs/plans/2026-09-27-agent-skill-frontmatter-conformity-plan.md (### B2b).
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

import yaml

from autoharness import verify_workspace as vw

PAYLOAD_FIELDS = {
    "contract",
    "path",
    "from_version",
    "to_version",
    "status",
    "severity",
    "changed_fields",
    "action",
    "manual_review",
    "evidence",
    "code",
    "from_key",
    "to_keys",
    "value",
    "summary",
}

AGENT_BASE = (
    "name: Demo\n"
    "description: A demo agent\n"
    "max_subagent_tier: 2\n"
    "subagent_depth: 0\n"
)
ROUTE = "model_family: fam\nmodel_provider: prov\nreasoning_effort: high\n"


def _agent(extra: str = "", route: str = ROUTE, base: str = AGENT_BASE) -> str:
    return f"---\n{base}{route}{extra}---\n\n# Demo\n"


def _skill(name: str | None, extra: str = "") -> str:
    name_line = f"name: {name}\n" if name is not None else ""
    return f"---\n{name_line}description: A demo skill\n{extra}---\n\n# Skill\n"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_permissive_schemas(autoharness_home: Path) -> None:
    schema = json.dumps({"$schema": "http://json-schema.org/draft-07/schema#", "type": "object"})
    for name in ("harness-manifest", "harness-config", "workspace-profile"):
        (autoharness_home / "schemas" / name).mkdir(parents=True, exist_ok=True)
        (autoharness_home / "schemas" / f"{name}.schema.json").write_text(schema, encoding="utf-8")
        (autoharness_home / "schemas" / name / "1.0.0.schema.json").write_text(schema, encoding="utf-8")


class _Fixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.home = self.root / "home"
        self.ws = self.root / "ws"
        self.staging = self.root / "staging"
        (self.home / "templates").mkdir(parents=True)
        (self.ws / ".autoharness").mkdir(parents=True)
        _write_permissive_schemas(self.home)
        self.artifacts: list[dict[str, Any]] = []
        self.community: list[dict[str, Any]] = []
        self.manifest_extra: dict[str, Any] = {}
        self.variables: dict[str, str] = {"PROJECT_NAME": "demo"}

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, rel: str, text: str, base: Path | None = None) -> Path:
        path = (base or self.ws) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def template(self, rel: str, text: str) -> Path:
        return self.write(rel, text, base=self.home / "templates")

    def track(self, rel: str, label: str, *, unchanged: bool = True) -> None:
        data = (self.ws / rel).read_bytes()
        self.artifacts.append(
            {"path": rel, "template": label, "checksum": _sha(data) if unchanged else "0" * 64, "primitive": 1}
        )

    def track_community(
        self, rel: str, template_path: str, *, unchanged: bool = True, source_checksum: str = ""
    ) -> None:
        data = (self.ws / rel).read_bytes()
        self.community.append(
            {
                "template_id": Path(rel).stem,
                "template_path": template_path,
                "installed_path": rel,
                "installed_checksum": _sha(data) if unchanged else "0" * 64,
                "source_checksum": source_checksum,
            }
        )

    def run_verify(self) -> dict[str, Any]:
        manifest: dict[str, Any] = {
            "schema_version": "1.0.0",
            "installed_at": "2026-09-28T00:00:00Z",
            "autoharness_version": "0.0.0",
            "profile_hash": "abc",
            "primitives_installed": [1],
            "capability_packs": [],
            "artifacts": self.artifacts,
            "variables_used": self.variables,
        }
        if self.community:
            manifest["community_templates"] = self.community
        manifest.update(self.manifest_extra)
        self.write(".autoharness/harness-manifest.yaml", yaml.safe_dump(manifest, sort_keys=False))
        self.write(".autoharness/config.yaml", yaml.safe_dump({"schema_version": "1.0.0"}))
        self.write(".autoharness/workspace-profile.yaml", yaml.safe_dump({"schema_version": "1.0.0"}))
        return vw.verify_workspace(self.ws, self.home, self.staging)

    @staticmethod
    def proposals(report: dict[str, Any], path: str | None = None) -> list[dict[str, Any]]:
        return [
            p
            for p in report["migration_proposals"]
            if p.get("contract") == "frontmatter-conformity" and (path is None or p["path"] == path)
        ]

    def one(self, report: dict[str, Any], path: str) -> dict[str, Any]:
        found = self.proposals(report, path)
        self.assertEqual(len(found), 1, found)
        return found[0]

    def assert_payload(self, proposal: dict[str, Any]) -> None:
        self.assertEqual(set(proposal), PAYLOAD_FIELDS)
        self.assertIsNone(proposal["from_version"])
        self.assertEqual(proposal["to_version"], "fc-1")
        self.assertIsInstance(proposal["evidence"]["codes"], list)
        self.assertTrue(proposal["evidence"]["citation"].startswith("P-013."))
        self.assertEqual(
            proposal["manual_review"], proposal["action"] not in ("rerender", "reinstall-community")
        )
        expected_summary = (
            f"{proposal['path']}: {proposal['action']} {proposal['from_key'] or '-'} -> "
            f"[{', '.join(proposal['to_keys'])}]"
            + (" [manual review]" if proposal["manual_review"] else "")
        )
        self.assertEqual(proposal["summary"], expected_summary)


# ---------------------------------------------------------------------------
# Rule 1 — source regeneration gated on the rendered candidate
# ---------------------------------------------------------------------------


class Rule1SourceRegenerationTests(_Fixture):
    def test_managed_rendered_unchanged_passing_candidate_gets_rerender(self) -> None:
        # Runtime proof 4 shape: an unchanged installed agent lacking model_family.
        self.template("agents/demo.agent.md.tmpl", _agent())
        self.write(".github/agents/demo.agent.md", _agent(route="model_provider: prov\nreasoning_effort: high\n"))
        self.track(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl")
        report = self.run_verify()
        self.assertFalse(report["targeted_checks"]["frontmatter_conformity"]["ok"])
        proposal = self.one(report, ".github/agents/demo.agent.md")
        self.assert_payload(proposal)
        self.assertEqual(proposal["action"], "rerender")
        self.assertFalse(proposal["manual_review"])
        self.assertEqual(proposal["code"], "FM_MISSING_REQUIRED")
        self.assertEqual(proposal["from_key"], "model_family")
        self.assertEqual((proposal["status"], proposal["severity"]), ("nonconformant-managed", "P1"))

    def test_managed_rendered_user_modified_passing_candidate_gets_key_level(self) -> None:
        self.template("agents/demo.agent.md.tmpl", _agent())
        self.write(".github/agents/demo.agent.md", _agent(extra="model: gpt-x\n"))
        self.track(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl", unchanged=False)
        proposal = self.one(self.run_verify(), ".github/agents/demo.agent.md")
        self.assert_payload(proposal)
        self.assertEqual(proposal["action"], "migrate-key")  # rule 2: differs from model_family
        self.assertIsNone(proposal["value"])
        self.assertTrue(proposal["manual_review"])

    def test_unchanged_managed_with_failing_candidate_gets_source_repair(self) -> None:
        # AS-F8 / AN-F10: passes template mode, renders a non-int max_subagent_tier.
        template = _agent(base="name: Demo\ndescription: A demo agent\nmax_subagent_tier: {{TIER_X}}\nsubagent_depth: 0\n")
        self.template("agents/demo.agent.md.tmpl", template)
        self.variables["TIER_X"] = "high"
        self.write(".github/agents/demo.agent.md", template.replace("{{TIER_X}}", "high"))
        self.track(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl")
        proposal = self.one(self.run_verify(), ".github/agents/demo.agent.md")
        self.assert_payload(proposal)
        self.assertEqual(proposal["action"], "source-repair")
        self.assertTrue(proposal["manual_review"])
        self.assertIsNone(proposal["value"])
        self.assertTrue(proposal["evidence"]["template_path"].endswith("demo.agent.md.tmpl"))
        self.assertIn("FM_TYPE_INVALID max_subagent_tier", proposal["evidence"]["candidate_findings"])

    def test_managed_community_unchanged_passing_candidate_gets_reinstall(self) -> None:
        self.template("community/agents/adr.agent.md.tmpl", _agent(route="model_family: {{FAM}}\nmodel_provider: prov\nreasoning_effort: high\n"))
        self.variables["FAM"] = "fam"
        self.write(".github/agents/adr.agent.md", _agent(route="model_provider: prov\nreasoning_effort: high\n"))
        self.track_community(".github/agents/adr.agent.md", "templates/community/agents/adr.agent.md.tmpl")
        report = self.run_verify()
        proposal = self.one(report, ".github/agents/adr.agent.md")
        self.assert_payload(proposal)
        self.assertEqual(proposal["action"], "reinstall-community")
        self.assertFalse(proposal["manual_review"])
        self.assertEqual(proposal["status"], "nonconformant-managed")

    def test_managed_community_user_modified_gets_key_level(self) -> None:
        self.template("community/agents/adr.agent.md.tmpl", _agent())
        self.write(".github/agents/adr.agent.md", _agent(extra="model: fam\n"))
        self.track_community(".github/agents/adr.agent.md", "templates/community/agents/adr.agent.md.tmpl", unchanged=False)
        proposal = self.one(self.run_verify(), ".github/agents/adr.agent.md")
        self.assert_payload(proposal)
        self.assertEqual(proposal["action"], "remove-key")  # rule 2: model == model_family
        self.assertTrue(proposal["manual_review"])

    def test_community_unchanged_with_failing_candidate_gets_source_repair(self) -> None:
        self.template("community/agents/adr.agent.md.tmpl", _agent(route=""))
        self.write(".github/agents/adr.agent.md", _agent(route=""))
        self.track_community(".github/agents/adr.agent.md", "templates/community/agents/adr.agent.md.tmpl")
        found = self.proposals(self.run_verify(), ".github/agents/adr.agent.md")
        self.assertTrue(found)
        self.assertEqual({p["action"] for p in found}, {"source-repair"})

    def test_community_template_path_escaping_templates_is_never_read(self) -> None:
        # AS-F9: inside autoharness_home but outside templates/, empty source_checksum.
        outside = self.write("schemas/evil.agent.md.tmpl", _agent(), base=self.home)
        self.write(".github/agents/adr.agent.md", _agent(route=""))
        self.track_community(".github/agents/adr.agent.md", "schemas/evil.agent.md.tmpl", source_checksum="")
        reads: list[Path] = []
        real = vw._fc_read_bytes

        def _spy(path: Path) -> bytes:
            reads.append(Path(path).resolve())
            return real(path)

        with mock.patch.object(vw, "_fc_read_bytes", side_effect=_spy):
            report = self.run_verify()
        self.assertNotIn(outside.resolve(), reads)
        found = self.proposals(report, ".github/agents/adr.agent.md")
        self.assertTrue(found)
        self.assertEqual({p["action"] for p in found}, {"source-repair"})
        self.assertIn("containment", found[0]["evidence"]["candidate_reason"])
        self.assertFalse(report["targeted_checks"]["frontmatter_conformity"]["ok"])

    def test_community_idempotent_after_reinstall(self) -> None:
        # AS-F7: conformant installed file, both checksums refreshed -> no proposal, no drift.
        template = _agent(route="model_family: {{FAM}}\nmodel_provider: prov\nreasoning_effort: high\n")
        source = self.template("community/agents/adr.agent.md.tmpl", template)
        self.variables["FAM"] = "fam"
        self.write(".github/agents/adr.agent.md", template.replace("{{FAM}}", "fam"))
        self.track_community(
            ".github/agents/adr.agent.md",
            "templates/community/agents/adr.agent.md.tmpl",
            source_checksum=_sha(source.read_bytes()),
        )
        report = self.run_verify()
        self.assertEqual(self.proposals(report), [])
        self.assertTrue(report["targeted_checks"]["frontmatter_conformity"]["ok"])
        self.assertEqual(len(report["community_templates"]), 1)
        self.assertTrue(report["community_templates"][0]["ok"], report["community_templates"])


# ---------------------------------------------------------------------------
# Rules 2-8 — table-driven across classes
# ---------------------------------------------------------------------------


class KeyLevelRuleTests(_Fixture):
    def _setup(self, cls: str, rel: str, text: str) -> None:
        self.write(rel, text)
        if cls == "managed-source":
            label = "global skill definition" if rel.endswith("SKILL.md") else "global agent definition"
            self.track(rel, label)
        elif cls == "managed-rendered-user-modified":
            tmpl = "skills/demo/SKILL.md.tmpl" if rel.endswith("SKILL.md") else "agents/demo.agent.md.tmpl"
            good = _skill(Path(rel).parent.name) if rel.endswith("SKILL.md") else _agent()
            self.template(tmpl, good)
            self.track(rel, tmpl, unchanged=False)
        elif cls == "unknown-provenance":
            self.track(rel, "workspace-discovery output")
        elif cls == "workspace-authored":
            pass
        else:  # pragma: no cover - table guard
            raise AssertionError(cls)

    CLASS_STATUS = {
        "managed-source": ("nonconformant-managed", "P1"),
        "managed-rendered-user-modified": ("nonconformant-managed", "P1"),
        "workspace-authored": ("nonconformant-workspace", "P2"),
        "unknown-provenance": ("nonconformant-unknown", "P2"),
    }

    CASES = [
        # (case, rel, text, code, action, from_key, to_keys, value)
        ("rule2-migrate-copy", ".github/agents/a.agent.md", _agent(route="model_provider: p\nreasoning_effort: h\n", extra="model: gpt-x\n"),
         "FM_BARE_MODEL", "migrate-key", "model", ["model_family"], "gpt-x"),
        ("rule2-equal-remove", ".github/agents/a.agent.md", _agent(extra="model: fam\n"),
         "FM_BARE_MODEL", "remove-key", "model", [], None),
        ("rule2-differs-null", ".github/agents/a.agent.md", _agent(extra="model: other\n"),
         "FM_BARE_MODEL", "migrate-key", "model", ["model_family"], None),
        ("rule2-list-null", ".github/agents/a.agent.md", _agent(route="model_provider: p\nreasoning_effort: h\n", extra="model: [a, b]\n"),
         "FM_BARE_MODEL", "migrate-key", "model", ["model_family"], None),
        ("rule3-skill-remove", ".github/skills/demo/SKILL.md", _skill("demo", "model: gpt-x\n"),
         "FM_BARE_MODEL", "remove-key", "model", [], None),
        ("rule4-skill-forbidden", ".github/skills/demo/SKILL.md", _skill("demo", "model_family: fam\n"),
         "FM_FORBIDDEN_KEY", "remove-key", "model_family", [], None),
        ("rule5-skill-name", ".github/skills/demo/SKILL.md", _skill(None),
         "FM_MISSING_REQUIRED", "add-key", "name", ["name"], "demo"),
        ("rule5-agent-null", ".github/agents/a.agent.md", _agent(route="model_family: fam\nmodel_provider: p\n"),
         "FM_MISSING_REQUIRED", "add-key", "reasoning_effort", ["reasoning_effort"], None),
        ("rule6-skill-mismatch", ".github/skills/demo/SKILL.md", _skill("other"),
         "FM_TYPE_INVALID", "replace-value", "name", ["name"], "demo"),
        ("rule6-agent-null", ".github/agents/a.agent.md", _agent(base="name: Demo\ndescription: d\nmax_subagent_tier: true\nsubagent_depth: 0\n"),
         "FM_TYPE_INVALID", "replace-value", "max_subagent_tier", ["max_subagent_tier"], None),
        ("rule7-placeholder", ".github/agents/a.agent.md", _agent(route='model_family: "{{FAM}}"\nmodel_provider: p\nreasoning_effort: h\n'),
         "FM_UNRESOLVED_PLACEHOLDER", "replace-value", "model_family", ["model_family"], None),
        ("rule8-parse-error", ".github/skills/demo/SKILL.md", "no frontmatter here\n",
         "FM_PARSE_ERROR", "manual-fix", None, [], None),
    ]

    def test_rules_2_to_8_across_classes(self) -> None:
        for cls, (status, severity) in self.CLASS_STATUS.items():
            for case, rel, text, code, action, from_key, to_keys, value in self.CASES:
                with self.subTest(cls=cls, case=case):
                    self.tearDown()
                    self.setUp()
                    self._setup(cls, rel, text)
                    report = self.run_verify()
                    found = [p for p in self.proposals(report, rel) if p["code"] == code]
                    self.assertEqual(len(found), 1, self.proposals(report, rel))
                    proposal = found[0]
                    self.assert_payload(proposal)
                    self.assertEqual(
                        (proposal["action"], proposal["from_key"], proposal["to_keys"], proposal["value"]),
                        (action, from_key, to_keys, value),
                    )
                    self.assertTrue(proposal["manual_review"])
                    self.assertEqual((proposal["status"], proposal["severity"]), (status, severity))
                    managed = cls.startswith("managed")
                    self.assertEqual(report["targeted_checks"]["frontmatter_conformity"]["ok"], not managed)

    def test_plugin_global_bare_model_gets_remove_key_never_migrate(self) -> None:
        self.manifest_extra = {"install_mode": "self-install"}
        self.write("plugin.json", json.dumps({"name": "autoharness", "agents": [".github/agents/auto-tune.agent.md"]}))
        self.write(".github/agents/auto-tune.agent.md", _agent(route="", extra="model: gpt-x\n"))
        self.track(".github/agents/auto-tune.agent.md", "global agent definition")
        proposal = self.one(self.run_verify(), ".github/agents/auto-tune.agent.md")
        self.assert_payload(proposal)
        self.assertEqual((proposal["code"], proposal["action"], proposal["to_keys"]), ("FM_BARE_MODEL", "remove-key", []))
        self.assertIn("P-013.4", proposal["evidence"]["citation"])

    def test_skill_forbidden_key_cites_leaf_executor_rule(self) -> None:
        self.write(".github/skills/demo/SKILL.md", _skill("demo", "max_subagent_tier: 2\n"))
        proposal = self.one(self.run_verify(), ".github/skills/demo/SKILL.md")
        self.assertIn("P-013.5", proposal["evidence"]["citation"])
        self.assertIn("leaf", proposal["evidence"]["citation"])

    def test_workspace_authored_bare_model_migrates_without_provider(self) -> None:
        # Runtime proof 2 shape.
        self.write(".github/agents/hand.agent.md", "---\nname: Hand\ndescription: h\nmodel: gpt-x\n---\n")
        report = self.run_verify()
        found = [p for p in self.proposals(report, ".github/agents/hand.agent.md") if p["code"] == "FM_BARE_MODEL"]
        self.assertEqual(len(found), 1)
        proposal = found[0]
        self.assertEqual((proposal["action"], proposal["to_keys"], proposal["value"]), ("migrate-key", ["model_family"], "gpt-x"))
        self.assertNotIn("model_provider", proposal["to_keys"])
        provider_values = [p["value"] for p in self.proposals(report) if p["from_key"] == "model_provider"]
        self.assertEqual(provider_values, [None])  # add-key with no inferred provider
        self.assertTrue(report["targeted_checks"]["frontmatter_conformity"]["ok"])

    def test_managed_source_skill_without_name_add_key_dir(self) -> None:
        self.write(".github/skills/tune-harness/SKILL.md", _skill(None))
        self.track(".github/skills/tune-harness/SKILL.md", "global skill definition")
        proposal = self.one(self.run_verify(), ".github/skills/tune-harness/SKILL.md")
        self.assertEqual((proposal["action"], proposal["value"], proposal["manual_review"]), ("add-key", "tune-harness", True))

    def test_invalid_skill_dir_name_proposes_null_value(self) -> None:
        cases = (
            ("Bad_Dir", None, "add-key"),
            ("Bad_Dir2", "bad-dir2", "replace-value"),
        )
        for directory, name, action in cases:
            with self.subTest(directory=directory):
                rel = f".github/skills/{directory}/SKILL.md"
                self.write(rel, _skill(name))
                proposals = [p for p in self.proposals(self.run_verify()) if p["path"] == rel and p["from_key"] == "name"]
                self.assertEqual(len(proposals), 1, proposals)
                self.assertEqual(proposals[0]["action"], action)
                self.assertIsNone(proposals[0]["value"])

    def test_informational_only_file_gets_no_proposal(self) -> None:
        self.write(".github/agents/a.agent.md", _agent(extra="custom_key: 1\n"))
        self.assertEqual(self.proposals(self.run_verify()), [])


# ---------------------------------------------------------------------------
# Markdown parity and write discipline
# ---------------------------------------------------------------------------


class ProposalReportTests(_Fixture):
    def test_each_summary_appears_in_markdown_report(self) -> None:
        self.write(".github/agents/hand.agent.md", "---\nname: Hand\ndescription: h\nmodel: gpt-x\n---\n")
        self.write(".github/skills/demo/SKILL.md", _skill(None, "model_family: f\n"))
        self.track(".github/skills/demo/SKILL.md", "global skill definition")
        report = self.run_verify()
        proposals = self.proposals(report)
        self.assertGreaterEqual(len(proposals), 3)
        markdown = Path(report["report_paths"]["markdown"]).read_text(encoding="utf-8")
        for proposal in proposals:
            self.assertIn(proposal["summary"], markdown)

    def test_verify_writes_nothing_outside_staging(self) -> None:
        self.template("agents/demo.agent.md.tmpl", _agent())
        self.write(".github/agents/demo.agent.md", _agent(route=""))
        self.track(".github/agents/demo.agent.md", "agents/demo.agent.md.tmpl")
        self.template("community/agents/adr.agent.md.tmpl", _agent())
        self.write(".github/agents/adr.agent.md", _agent(route=""))
        self.track_community(".github/agents/adr.agent.md", "templates/community/agents/adr.agent.md.tmpl")
        self.write(".github/agents/hand.agent.md", "---\nname: Hand\ndescription: h\nmodel: gpt-x\n---\n")
        self.run_verify()  # writes the manifest/config; establishes the baseline

        def _snapshot() -> dict[str, tuple[int, bytes]]:
            return {
                p.relative_to(self.root).as_posix(): (p.stat().st_mtime_ns, p.read_bytes())
                for p in sorted(self.root.rglob("*"))
                if p.is_file() and not p.resolve().is_relative_to(self.staging.resolve())
            }

        before = _snapshot()
        report = vw.verify_workspace(self.ws, self.home, self.staging)
        self.assertTrue(self.proposals(report))
        self.assertEqual(_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
