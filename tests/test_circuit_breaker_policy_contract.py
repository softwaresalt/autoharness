"""Contract tests for the circuit-breaker instruction template and dogfood output."""

from __future__ import annotations

import hashlib
import re
import unittest
from pathlib import Path

import yaml
from autoharness.verify_workspace import _derive_template_variables, _render_template

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "circuit-breaker.instructions.md.tmpl"
)
_DOGFOOD = _REPO_ROOT / ".github" / "instructions" / "circuit-breaker.instructions.md"
_MANIFEST = _REPO_ROOT / ".autoharness" / "harness-manifest.yaml"
_INSTALL_SKILL = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
_GITATTRIBUTES = _REPO_ROOT / ".gitattributes"
_ESCALATION_TEMPLATE = (
    _REPO_ROOT / "templates" / "instructions" / "escalation-protocol.instructions.md.tmpl"
)
_ESCALATION_DOGFOOD = (
    _REPO_ROOT / ".github" / "instructions" / "escalation-protocol.instructions.md"
)
_WORKFLOW_POLICY_TEMPLATE = (
    _REPO_ROOT / "templates" / "policies" / "workflow-policies.md.tmpl"
)
_SHIP_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_ship.agent.md.tmpl"
_SHIP_DOGFOOD = _REPO_ROOT / ".github" / "agents" / "_ship.agent.md"
_STAGE_TEMPLATE = _REPO_ROOT / "templates" / "agents" / "_stage.agent.md.tmpl"
_STAGE_DOGFOOD = _REPO_ROOT / ".github" / "agents" / "_stage.agent.md"
_BUILD_FEATURE_TEMPLATE = (
    _REPO_ROOT / "templates" / "skills" / "build-feature" / "SKILL.md.tmpl"
)

_EXPECTED_TEMPLATE_PLACEHOLDERS = {
    "{{DOCS_MEMORY}}",
    "{{STATUS_BLOCKED}}",
    "{{STATUS_DONE}}",
    "{{CIRCUIT_BREAKER_COOLDOWN}}",
}
_DOUBLE_BRACE_TOKEN = re.compile(r"(?<!\$)\{\{[^{}\n]+\}\}")
_CODE_FENCE = re.compile(r"^\s*```")


def _lf_bytes(path: Path) -> bytes:
    return path.read_bytes().replace(b"\r\n", b"\n")


def _render_template_bytes() -> bytes:
    autoharness_dir = _REPO_ROOT / ".autoharness"
    load_yaml = lambda name: yaml.safe_load(
        (autoharness_dir / name).read_text(encoding="utf-8")
    )
    variables = _derive_template_variables(
        _REPO_ROOT,
        load_yaml("harness-manifest.yaml"),
        load_yaml("config.yaml"),
        load_yaml("workspace-profile.yaml"),
        load_yaml("backlog-registry.yaml"),
    )
    rendered = _render_template(
        _lf_bytes(_TEMPLATE).decode("utf-8"),
        variables,
    )
    return rendered.encode("utf-8")


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _markdown_section(text: str, heading: str) -> str:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError as error:
        raise AssertionError(f"missing Markdown heading: {heading}") from error
    level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    in_code_fence = False
    for index in range(start + 1, len(lines)):
        candidate = lines[index]
        if _CODE_FENCE.match(candidate):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        candidate_level = len(candidate) - len(candidate.lstrip("#"))
        if candidate_level and candidate_level <= level:
            end = index
            break
    return "\n".join(lines[start:end])


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
        self.assertTrue(_INSTALL_SKILL.is_file(), f"missing install skill: {_INSTALL_SKILL}")

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
            "## Universal Retry Threshold": {
                "threshold-three": (
                "The threshold is exactly three counted failures for the same operation.",
                "Count every non-zero native process exit, tool failure, validation failure, and timeout immediately when it is observed.",
                "If any single operation (command execution, code fix attempt, file generation, tool invocation, or equivalent workflow action) fails three counted times with substantially the same error, the agent MUST STOP executing that operation immediately.",
                "If the same error recurs on the third counted same-operation attempt within the loop, the universal circuit breaker applies: STOP and escalate.",
                ),
                "next-counted-diagnostics": (
                "Changing diagnostic transport is allowed only below the threshold and only as the next counted attempt.",
                "The next counted diagnostic consumes the next attempt.",
                "If it returns non-zero or times out, increment the same-operation counter immediately.",
                "A zero exit MUST NOT erase prior counted failures.",
                "Masking or replacing the native exit status does not create a successful attempt.",
                "Diagnostic escalation is never a side channel, preflight replay, parallel counter, reset, or free probe.",
                "If the next counted diagnostic is attempt three and observes the same operation failing, the circuit trips.",
                ),
                "no-fourth-reset-pause-parallel-counter": (
                "Agents MUST NOT make a fourth attempt for the same operation after the third counted same-operation failure.",
                "A pause, cooldown, context compaction, model switch, shell restart, worktree switch, or parallel work item MUST NOT reset the same-operation counter.",
                "No reset, pause, parallel counter, or fourth run exists for a tripped same-operation circuit.",
                ),
                "provisional-concrete-identity": (
                "Never fingerprint or persist the environment wholesale, secret-bearing values, or raw command payloads.",
                "When output truncation hides the concrete failure details, same-operation identity MAY be provisional.",
                "While details remain hidden, another failed invocation with that fingerprint counts against the same operation.",
                "Once concrete details are observable, record identity from native process exit or timeout, stable target/code, normalized message, affected path, workflow phase",
                "Escalation records MUST link each counted attempt to concrete operation evidence without recounting prior attempts.",
                "Linking provisional attempts to a later concrete identity is bookkeeping only; it never restarts the threshold.",
                ),
                "genuinely-different-observable-error": (
                "Only a genuinely different observable error, with distinct stable evidence, may break the same-error chain and continue a skill-managed exploration loop.",
                "only for genuinely different observable errors within their loop scope",
                "Hidden or truncated output does not prove a different error.",
                ),
            },
            "## Cooldown Delay (No Auto-Reset)": {
                "no-post-trip-cooldown": (
                "After the third counted same-operation failure, cooldown MUST NOT reset/retry a tripped same-operation circuit. There is no post-trip probe and no fourth attempt.",
                ),
            },
            "## Escalation Protocol": {
                "bounded-redacted-logs-and-retention": (
                "Canonicalize the workspace root and candidate diagnostics path before any raw capture.",
                "Write workspace diagnostics only below an ignored `logs/diagnostics/` path after verifying the ignore rule and confirming the canonicalized diagnostics path stays inside the canonicalized workspace root.",
                "If canonicalization fails, or the resolved diagnostics path escapes the workspace root (including through a symlink/junction/reparse point), omit the raw capture and retain only the bounded, redacted checkpoint evidence below.",
                "Never write captures outside the workspace.",
                "Capture combined stdout and stderr only up to 1 MiB or 10,000 lines, whichever is reached first, and never beyond the command timeout.",
                "Inspect at most the final 64 KiB or 500 lines, or a smaller identified failure block.",
                "Persist only a redacted summary and evidence link; exclude secrets, credentials, tokens, sensitive output, raw payload content, and raw environment values.",
                "Apply bounded extraction retention: retain the ignored raw capture only for the active diagnostic session, then use the repository-approved log disposition path.",
                ),
                "native-exit": (
                "For each attempt: native process exit code or timeout marker",
                ),
                "immediate-de-escalation": (
                "return to normal logging with immediate de-escalation. Do not keep high-volume capture, expanded tracing, or diagnostic transports enabled beyond the bounded diagnosis window.",
                ),
            },
            "## Log Format": {
                "checkpoint-bounds": (
                "Logging controls: {byte limit, line limit, time limit, redaction, retention}",
                ),
            },
            "## Stall Detection": {
                "timeout-identity": (
                "The timeout marker is part of the same-operation evidence, just like a native process exit code.",
                "Stall diagnostics follow the same workspace-log bounds, redaction, raw-payload exclusion, bounded extraction retention, and immediate de-escalation rules",
                ),
            },
        }
        for source, text in (
            ("rendered template", self.rendered_text),
            ("dogfood", self.dogfood_text),
        ):
            for heading, section_clauses in clauses.items():
                section = _markdown_section(text, heading)
                for behavior, behavior_clauses in section_clauses.items():
                    for clause in behavior_clauses:
                        with self.subTest(source=source, behavior=behavior, clause=clause):
                            self.assertClause(section, clause, source=source)

    def test_legacy_auto_reset_probe_language_is_absent(self) -> None:
        forbidden_clauses = (
            "On circuit trip, record `circuit_open_until",
            "When the cooldown expires, auto-reset the circuit state and allow",
            "The probe retry is a one-shot test",
            "After **3 circuit trips**",
            "operating-system temporary location outside the worktree",
        )
        for source, text in (
            ("rendered template", self.rendered_text),
            ("dogfood", self.dogfood_text),
        ):
            normalized = _normalize(text)
            for clause in forbidden_clauses:
                with self.subTest(source=source, forbidden_clause=clause):
                    self.assertNotIn(_normalize(clause), normalized)

    def test_install_skill_does_not_reintroduce_auto_reset(self) -> None:
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        normalized = _normalize(text)
        self.assertNotIn("optional cooldown/auto-reset guidance", normalized)
        self.assertNotIn("auto-reset guidance before a single retry", normalized)
        self.assertIn(
            "below-threshold cooldown delay with no auto-reset or post-trip probe",
            normalized,
        )

    def test_open_breaker_handoff_never_reexecutes_the_failed_operation(self) -> None:
        escalation_surfaces = (
            _ESCALATION_TEMPLATE,
            _ESCALATION_DOGFOOD,
            _WORKFLOW_POLICY_TEMPLATE,
            _SHIP_TEMPLATE,
            _SHIP_DOGFOOD,
            _STAGE_TEMPLATE,
            _STAGE_DOGFOOD,
        )
        required = (
            "MUST NOT re-execute the failing operation after its circuit is open",
            "handoff is for asynchronous or operator review, not a fourth attempt",
        )
        forbidden = (
            "re-attempts before falling back",
            "Re-attempt the failing",
            "successful re-attempt",
            "interposes an auto-escalation attempt",
        )
        for path in escalation_surfaces:
            text = _normalize(path.read_text(encoding="utf-8"))
            for clause in required:
                with self.subTest(path=path, clause=clause):
                    self.assertIn(_normalize(clause), text)
            for clause in forbidden:
                with self.subTest(path=path, forbidden=clause):
                    self.assertNotIn(_normalize(clause), text)

    def test_build_loop_uses_per_operation_failure_count(self) -> None:
        text = _normalize(_BUILD_FEATURE_TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn(
            _normalize(
                "if the same error reaches its third counted failure for the same operation"
            ),
            text,
        )
        self.assertIn(
            _normalize("Track same-operation counters across the entire loop."),
            text,
        )
        self.assertIn(
            _normalize(
                "A recurrence can match any prior attempt in that operation's failure chain, not only the immediately previous iteration."
            ),
            text,
        )
        self.assertIn(
            _normalize("Distinct errors advance distinct per-operation counters."),
            text,
        )
        self.assertNotIn(_normalize("same error recurs on attempts 3+"), text)
        self.assertNotIn(
            _normalize("If error is substantially identical to previous attempt"),
            text,
        )

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

    def test_manifest_managed_policy_artifacts_are_lf_pinned(self) -> None:
        manifest = yaml.safe_load(_MANIFEST.read_text(encoding="utf-8"))
        artifacts = {
            artifact["path"]: artifact
            for artifact in manifest.get("artifacts", [])
        }
        attributes = _GITATTRIBUTES.read_text(encoding="utf-8")
        for relative_path in (
            ".github/instructions/circuit-breaker.instructions.md",
            ".github/skills/install-harness/SKILL.md",
        ):
            with self.subTest(path=relative_path):
                path = _REPO_ROOT / relative_path
                raw_bytes = path.read_bytes()
                self.assertNotIn(b"\r\n", raw_bytes)
                self.assertIn(f"{relative_path} text eol=lf", attributes)
                self.assertEqual(
                    artifacts[relative_path]["checksum"],
                    hashlib.sha256(raw_bytes).hexdigest(),
                )


if __name__ == "__main__":
    unittest.main()
