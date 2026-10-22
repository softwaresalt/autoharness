"""Interaction and cross-document contract tests for the docs-only route (216.007-T)."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from _docs_only_repo import BACKLOG, DOCS, ShipmentRepo
from autoharness import harness_surfaces as hs
from test_docs_only_check_cli import run_cli
from test_harness_surfaces_digest import SHIPMENT_ID, ResolverFixture

ROOT = Path(__file__).resolve().parents[1]
CODE_LABEL = "harness-ready"
DOCS_LABEL = "harness-verification-gated"
NONE_LABEL = "harness-surface:none"
EXCLUSIVITY = re.compile(
    r"never|exclusive|not both|\bnot\b|neither|either|instead|without|excluded|excludes", re.IGNORECASE
)

CONTRACT_DOCS = {
    "policy template": ROOT / "templates" / "policies" / "workflow-policies.md.tmpl",
    "policy mirror": ROOT / ".github" / "policies" / "workflow-policies.md",
    "ship template": ROOT / "templates" / "agents" / "_ship.agent.md.tmpl",
    "ship mirror": ROOT / ".github" / "agents" / "_ship.agent.md",
    "harness-architect template": ROOT / "templates" / "skills" / "harness-architect" / "SKILL.md.tmpl",
    "harness-architect mirror": ROOT / ".github" / "skills" / "harness-architect" / "SKILL.md",
    "build-feature template": ROOT / "templates" / "skills" / "build-feature" / "SKILL.md.tmpl",
    "harvest template": ROOT / "templates" / "skills" / "harvest" / "SKILL.md.tmpl",
    "stage template": ROOT / "templates" / "agents" / "_stage.agent.md.tmpl",
}

# Code-route sentences that existed before the docs route and must stay verbatim.
CODE_ROUTE_TEXT = {
    "policy template": (
        "**Precondition** (ship): The task carries the `harness-ready` label.",
        "**Violation Action**: Do NOT apply `harness-ready` label. Halt and report the failure.",
    ),
    "policy mirror": (
        "**Precondition** (ship): The task carries the `harness-ready` label.",
        "**Violation Action**: Halt and suggest running the harness-architect.",
    ),
    "ship template": (
        "* **Already harnessed**: tasks carrying the `harness-ready` label — skip these.",
        "2. List all tasks with `harness-ready` label and `{{STATUS_QUEUED}}` status for the target feature or chore.",
    ),
    "harness-architect template": (
        "1. Apply the `harness-ready` label to the current task only, using the",
        "* Do not apply the harness-ready label until both compilation and red",
    ),
    "build-feature template": ("Invoked by the ship agent when a task has the `harness-ready` label",),
}


def text_of(path: Path) -> str:
    return path.read_bytes().decode("utf-8").replace("\r\n", "\n")


class ResolverInteractionTests(ResolverFixture):
    def test_none_plus_docs_label_resolves_with_no_surface_required(self) -> None:
        task = "7-T"
        self.write_record(task, self.task_record(task, NONE_LABEL, DOCS_LABEL))
        self.write_record(SHIPMENT_ID_RECORD, self.shipment_record(task))
        result = hs.resolve_shipment(workspace_root=self.ws, shipment_id=SHIPMENT_ID_RECORD)
        document = result.to_document()
        self.assertEqual(result.exit_code, 0, document)
        self.assertEqual(document["state"], "HARNESS_READY")
        self.assertEqual(document["surfaces"], [])
        self.assertEqual(
            [(d["member_id"], d["surface_id"]) for d in document["declarations"]], [("7-T", "none")]
        )

    def test_docs_label_alone_does_not_change_a_none_declaration(self) -> None:
        task = "7-T"
        self.write_record(task, self.task_record(task, NONE_LABEL))
        self.write_record(SHIPMENT_ID_RECORD, self.shipment_record(task))
        plain = hs.resolve_shipment(workspace_root=self.ws, shipment_id=SHIPMENT_ID_RECORD).to_document()
        self.write_record(task, self.task_record(task, NONE_LABEL, DOCS_LABEL))
        labelled = hs.resolve_shipment(workspace_root=self.ws, shipment_id=SHIPMENT_ID_RECORD).to_document()
        for key in ("state", "reason_code", "exit_code", "surfaces"):
            self.assertEqual(plain[key], labelled[key])


SHIPMENT_ID_RECORD = SHIPMENT_ID


class CrossDocumentContractTests(unittest.TestCase):
    def test_labels_never_coexist_in_any_contract_document(self) -> None:
        for name, path in CONTRACT_DOCS.items():
            with self.subTest(document=name):
                offenders = []
                for paragraph in re.split(r"\n\s*\n", text_of(path)):
                    flat = re.sub(r"\s+", " ", paragraph)
                    if CODE_LABEL in flat and DOCS_LABEL in flat and not EXCLUSIVITY.search(flat):
                        offenders.append(flat[:160])
                self.assertEqual(offenders, [])

    def test_every_route_document_states_the_docs_label_and_exclusivity(self) -> None:
        for name in ("policy template", "ship template", "harness-architect template", "build-feature template"):
            with self.subTest(document=name):
                self.assertIn(DOCS_LABEL, text_of(CONTRACT_DOCS[name]))
        for name in ("policy template", "harness-architect template"):
            flat = re.sub(r"\s+", " ", text_of(CONTRACT_DOCS[name]))
            self.assertRegex(flat, r"mutually exclusive|never both")

    def test_code_route_text_unchanged(self) -> None:
        for name, needles in CODE_ROUTE_TEXT.items():
            text = text_of(CONTRACT_DOCS[name])
            for needle in needles:
                with self.subTest(document=name, needle=needle[:50]):
                    self.assertIn(needle, text)

    def test_stage_and_harvest_never_apply_a_route_label(self) -> None:
        for name in ("harvest template", "stage template"):
            flat = re.sub(r"\s+", " ", text_of(CONTRACT_DOCS[name]))
            self.assertIn("Never apply either route label", flat)


class ShipSequenceCliEndToEndTests(unittest.TestCase):
    """The Ship-described docs-route sequence, driven through the CLI on a two-task shipment."""

    def setUp(self) -> None:
        self.repo = ShipmentRepo()
        self.addCleanup(self.repo.cleanup)
        self.t1, self.t2 = self.repo.TASKS
        self.record_file = self.repo.root.parent / f"{self.repo.root.name}-record.json"
        self.addCleanup(lambda: self.record_file.unlink(missing_ok=True))

    def args(self, phase: str, owned: str, task: str) -> list[str]:
        argv = [
            "harness", "docs-only-check", "--phase", phase, "--owned", owned, "--docs-root", DOCS,
            "--backlog-root", BACKLOG, "--task", task, "--feature", self.repo.FEATURE,
            "--shipment", self.repo.SHIPMENT, "--json",
        ]
        if phase == "completion":
            argv += ["--baseline", str(self.record_file)]
        return argv

    def baseline(self, owned: str, task: str) -> None:
        status, out, _ = run_cli(self.repo.root, self.args("baseline", owned, task))
        self.assertEqual(status, 0, out)
        self.record_file.write_text(out, encoding="utf-8")

    def completion(self, owned: str, task: str) -> tuple[int, dict]:
        status, out, _ = run_cli(self.repo.root, self.args("completion", owned, task))
        return status, json.loads(out)

    def test_two_task_sequence_passes(self) -> None:
        repo = self.repo
        repo.claim_all()
        repo.add_label(self.t1)
        self.baseline("docs/a.md", self.t1)
        repo.write("docs/a.md", "a edited by task 1\n")
        repo.save(self.t1, updated="2026-02-02T00:00:00Z")
        status, record = self.completion("docs/a.md", self.t1)
        self.assertEqual(status, 0, record)
        repo.close_out(self.t1, "docs: task 1", ("docs/a.md",))
        repo.add_label(self.t2)
        self.baseline("docs/b.md", self.t2)
        repo.write("docs/b.md", "b edited by task 2\n")
        status, record = self.completion("docs/b.md", self.t2)
        self.assertEqual(status, 0, record)
        self.assertIn("docs/b.md", record["delta_paths"])
        self.assertNotIn("docs/memory/session.md", record["delta_paths"])

    def test_unrelated_edits_are_rejected(self) -> None:
        cases = {
            "item outside the manifest": lambda r: r.write(f"{BACKLOG}/queue/777-T.md", "---\nid: 777-T\n---\nchanged\n"),
            "stash file": lambda r: r.write(f"{BACKLOG}/stash.jsonl", '{"edited":true}\n'),
            "sibling edited during the task": lambda r: r.save(self.t2, updated="2026-09-09T00:00:00Z"),
            "src file": lambda r: r.write("src/mod.py", "x = 2\n"),
            "non-owned docs file": lambda r: r.write("docs/b.md", "not owned\n"),
        }
        for name, mutate in cases.items():
            with self.subTest(name):
                self.repo.git("checkout", "--", ".")
                self.repo.git("clean", "-fdq")
                self.repo.claim_all()
                self.repo.add_label(self.t1)
                self.baseline("docs/a.md", self.t1)
                self.repo.write("docs/a.md", "edited\n")
                mutate(self.repo)
                status, record = self.completion("docs/a.md", self.t1)
                self.assertEqual(status, 1, record)
                self.assertEqual(record["result"], "violation")


if __name__ == "__main__":
    unittest.main()
