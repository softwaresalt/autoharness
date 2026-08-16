"""Contract tests for the circuit-breaker instruction template and dogfood output."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "circuit-breaker.instructions.md.tmpl"
)
_DOGFOOD = _REPO_ROOT / ".github" / "instructions" / "circuit-breaker.instructions.md"
_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"

_DOGFOOD_VALUES = {
    "DOCS_MEMORY": "docs/memory",
    "STATUS_BLOCKED": "blocked",
    "STATUS_DONE": "done",
    "CIRCUIT_BREAKER_COOLDOWN": "5 minutes",
}
_EXPECTED_TEMPLATE_PLACEHOLDERS = {"{{" + key + "}}" for key in _DOGFOOD_VALUES}
_DOUBLE_BRACE_TOKEN = re.compile(r"(?<!\$)\{\{[^{}\n]+\}\}")
_CODE_FENCE = re.compile(r"^\s*```")


def _lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _render_template_bytes() -> bytes:
    rendered = _lf_bytes(_TEMPLATE).decode("utf-8")
    for key, value in _DOGFOOD_VALUES.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered.encode("utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _double_brace_tokens_outside_fences(text: str) -> list[str]:
    tokens: list[str] = []
    in_code_fence = False
    for line in text.splitlines():
        if _CODE_FENCE.match(line):
            in_code_fence = not in_code_fence
            continue
        if not in_code_fence:
            tokens.extend(match.group(0) for match in _DOUBLE_BRACE_TOKEN.finditer(line))
    return tokens


def _frontmatter_and_body(text: str) -> tuple[dict[str, object], str]:
    parts = text.split("---\n", 2)
    if len(parts) != 3 or parts[0] != "":
        raise AssertionError("Markdown file must start with YAML frontmatter")
    frontmatter = yaml.safe_load(parts[1])
    if not isinstance(frontmatter, dict):
        raise AssertionError("YAML frontmatter must parse to a mapping")
    return frontmatter, parts[2]


class CircuitBreakerPolicyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.template_text = _lf_bytes(_TEMPLATE).decode("utf-8")
        cls.rendered_bytes = _render_template_bytes()
        cls.rendered_text = cls.rendered_bytes.decode("utf-8")
        cls.dogfood_bytes = _lf_bytes(_DOGFOOD)
        cls.dogfood_text = cls.dogfood_bytes.decode("utf-8")

    def assertClause(self, text: str, clause: str, *, source: str) -> None:
        self.assertIn(
            _normalize(clause),
            _normalize(text),
            f"{source} is missing behavioral clause: {clause}",
        )

    def test_files_exist(self) -> None:
        self.assertTrue(_TEMPLATE.is_file(), f"missing template: {_TEMPLATE}")
        self.assertTrue(_DOGFOOD.is_file(), f"missing dogfood output: {_DOGFOOD}")
        self.assertTrue(_MANIFEST.is_file(), f"missing manifest: {_MANIFEST}")

    def test_frontmatter_and_markdown_shape_are_valid(self) -> None:
        for source, text in (
            ("template", self.template_text),
            ("dogfood", self.dogfood_text),
        ):
            with self.subTest(source=source):
                frontmatter, body = _frontmatter_and_body(text)
                self.assertIn("Circuit breaker protocol", str(frontmatter.get("description", "")))
                self.assertEqual(frontmatter.get("applyTo"), "**")
                self.assertTrue(
                    body.lstrip().startswith("# Circuit Breaker Instructions"),
                    "body must start with the expected H1",
                )
                self.assertIn("## Universal Retry Threshold", body)
                self.assertIn("## Escalation Protocol", body)
                self.assertIn("## Cooldown Delay (No Auto-Reset)", body)

    def test_template_placeholders_are_limited_to_dogfood_values(self) -> None:
        placeholders = set(_double_brace_tokens_outside_fences(self.template_text))
        self.assertEqual(placeholders, _EXPECTED_TEMPLATE_PLACEHOLDERS)

    def test_lf_normalized_rendered_template_is_byte_identical_to_dogfood_output(self) -> None:
        self.assertNotIn(b"\r\n", self.rendered_bytes)
        self.assertEqual(self.rendered_bytes, self.dogfood_bytes)

    def test_rendered_outputs_have_no_unresolved_placeholders(self) -> None:
        for source, text in (
            ("rendered template", self.rendered_text),
            ("dogfood", self.dogfood_text),
        ):
            with self.subTest(source=source):
                self.assertEqual(_double_brace_tokens_outside_fences(text), [])

    def test_required_behavioral_clauses_are_present(self) -> None:
        clauses = {
            "threshold-three": (
                "The threshold is exactly three counted failures for the same operation.",
                "If any single operation (command execution, code fix attempt, file generation, tool invocation, or equivalent workflow action) fails three counted times with substantially the same error, the agent MUST STOP executing that operation immediately.",
                "If the same error recurs on the third counted same-operation attempt within the loop, the universal circuit breaker applies: STOP and escalate.",
            ),
            "next-counted-diagnostics": (
                "Changing diagnostic transport is allowed only below the threshold and only as the next counted attempt.",
                "The next counted diagnostic consumes the next attempt. If it returns non-zero or times out, it increments the same-operation counter immediately.",
                "Diagnostic escalation is never a side channel, preflight replay, parallel counter, reset, or free probe.",
                "If the next counted diagnostic is attempt three and observes the same operation failing, the circuit trips.",
            ),
            "no-fourth-reset-pause-parallel-counter": (
                "Agents MUST NOT make a fourth attempt for the same operation after the third counted same-operation failure.",
                "A pause, cooldown, context compaction, model switch, shell restart, worktree switch, or parallel work item MUST NOT reset the same-operation counter.",
                "No reset, pause, parallel counter, or fourth run exists for a tripped same-operation circuit.",
                "After the third counted same-operation failure, cooldown MUST NOT reset/retry a tripped same-operation circuit. There is no post-trip probe and no fourth attempt.",
                "do not attempt the operation again, do not schedule a post-trip probe, and do not route the same operation through a parallel counter.",
            ),
            "provisional-concrete-identity": (
                "When output truncation hides the concrete failure details, same-operation identity MAY be provisional.",
                "Compute a provisional same-operation fingerprint over the normalized command/target, cwd, relevant environment, and workflow phase",
                "Once concrete details are observable, record identity from native process exit or timeout, stable target/code, normalized message, affected path, workflow phase",
                "Escalation records MUST link each counted attempt to concrete operation evidence without recounting prior attempts.",
                "Linking provisional attempts to a later concrete identity is bookkeeping only; it never restarts the threshold.",
            ),
            "genuinely-different-observable-error": (
                "Only a genuinely different observable error, with distinct stable evidence, may break the same-error chain and continue a skill-managed exploration loop.",
                "only for genuinely different observable errors within their loop scope",
                "Hidden or truncated output does not prove a different error.",
            ),
            "bounded-redacted-logs-and-retention": (
                "All workspace logs MUST be bounded: every diagnostic artifact written under the workspace MUST have explicit byte, line, and time limits; be redacted before persistence; exclude secrets, credentials, tokens, sensitive output, and raw payload content; and use bounded extraction retention",
                "only the minimum useful excerpt is retained for the shortest useful duration.",
                "Keep captured output bounded and redacted; include summaries or links to bounded artifacts rather than full raw output.",
                "Logging controls: {byte limit, line limit, time limit, redaction, retention}",
            ),
            "native-exit": (
                "Count every non-zero native process exit, tool failure, validation failure, and timeout immediately when it is observed.",
                "For each attempt: native process exit code or timeout marker",
                "The timeout marker is part of the same-operation evidence, just like a native process exit code.",
            ),
            "immediate-de-escalation": (
                "After diagnosis or success, diagnostic verbosity MUST return to normal logging with immediate de-escalation.",
                "return to normal logging with immediate de-escalation. Do not keep high-volume capture, expanded tracing, or diagnostic transports enabled beyond the bounded diagnosis window.",
                "Stall diagnostics follow the same workspace-log bounds, redaction, raw-payload exclusion, bounded extraction retention, and immediate de-escalation rules",
            ),
        }
        for source, text in (
            ("rendered template", self.rendered_text),
            ("dogfood", self.dogfood_text),
        ):
            for behavior, behavior_clauses in clauses.items():
                for clause in behavior_clauses:
                    with self.subTest(source=source, behavior=behavior, clause=clause):
                        self.assertClause(text, clause, source=source)

    def test_legacy_auto_reset_probe_language_is_absent(self) -> None:
        forbidden_clauses = (
            "On circuit trip, record `circuit_open_until",
            "When the cooldown expires, auto-reset the circuit state and allow",
            "The probe retry is a one-shot test",
            "After **3 circuit trips**",
        )
        for source, text in (
            ("rendered template", self.rendered_text),
            ("dogfood", self.dogfood_text),
        ):
            normalized = _normalize(text)
            for clause in forbidden_clauses:
                with self.subTest(source=source, forbidden_clause=clause):
                    self.assertNotIn(_normalize(clause), normalized)

    def test_manifest_checksum_matches_lf_normalized_generated_bytes(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        artifacts = manifest.get("artifacts", [])
        matches = [
            artifact
            for artifact in artifacts
            if artifact.get("path") == ".github/instructions/circuit-breaker.instructions.md"
        ]
        self.assertEqual(len(matches), 1)
        artifact = matches[0]
        self.assertEqual(
            artifact.get("template"),
            "instructions/circuit-breaker.instructions.md.tmpl",
        )
        expected_checksum = hashlib.sha256(self.rendered_bytes).hexdigest()
        self.assertRegex(str(artifact.get("checksum")), r"^[0-9a-f]{64}$")
        self.assertEqual(artifact.get("checksum"), expected_checksum)


if __name__ == "__main__":
    unittest.main()
