"""Rendering + structure tests for the unified CI + local-gating primitive.

Protects the required-check contract and the unresolved-variable guarantee for
``templates/ci/ci.yml.tmpl`` (069.002) and the pre-push hook templates (069.003):

* the template renders to valid YAML with valid GitHub Actions job IDs for the
  Rust / TypeScript / Python profiles;
* the three-job shape is preserved (fail-closed ``changes`` detection, a guarded
  expensive gate, and an always-running aggregation gate);
* the expensive gate is gated SOLELY on path impact (no fail-open PR-title guard);
* the aggregation gate always runs and treats a skipped expensive job as OK;
* no ``{{UPPER_SNAKE}}`` template variable survives resolution.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CI_TEMPLATE = _REPO_ROOT / "templates" / "ci" / "ci.yml.tmpl"
_HOOK_SH = _REPO_ROOT / "templates" / "scripts" / "pre-push-quality-gates.sh.tmpl"
_HOOK_PS1 = _REPO_ROOT / "templates" / "scripts" / "pre-push-quality-gates.ps1.tmpl"

# Any {{UPPER_SNAKE}} placeholder not preceded by '$' (i.e. not a ${{ }} GitHub
# expression). Used to assert full variable resolution.
_UNRESOLVED_VAR = re.compile(r"(?<!\$)\{\{\s*[A-Z][A-Z0-9_]*\s*\}\}")
# Valid GitHub Actions job-ID grammar.
_JOB_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")

_PROFILES = {
    "rust": {
        "CI_EXPENSIVE_JOB_NAME": "build",
        "CI_REQUIRED_CHECK_NAME": "ci gate",
        "CI_RUNNER_OS": "ubuntu-latest",
        "CI_DEFAULT_BRANCH": "main",
        "CI_DOCS_ONLY_PATHS": "              - '!docs/**'",
        "CI_SETUP_STEPS": (
            "      - uses: actions/checkout@df4cb1c # v6.0.3\n"
            "      - run: rustup show"
        ),
        "LINT_COMMAND": "cargo clippy -- -D warnings",
        "FORMAT_CHECK_COMMAND": "cargo fmt --all -- --check",
        "TYPECHECK_COMMAND": "",
        "TEST_COMMAND": "cargo test",
        "BUILD_CHECK_COMMAND": "cargo check --all-targets",
        "CI_AUTOHARNESS_INSTALL_COMMAND": "pip install autoharness",
    },
    "typescript": {
        "CI_EXPENSIVE_JOB_NAME": "test",
        "CI_REQUIRED_CHECK_NAME": "ci gate",
        "CI_RUNNER_OS": "ubuntu-latest",
        "CI_DEFAULT_BRANCH": "main",
        "CI_DOCS_ONLY_PATHS": "              - '!docs/**'\n              - '!.backlogit/**'",
        "CI_SETUP_STEPS": (
            "      - uses: actions/checkout@df4cb1c # v6.0.3\n"
            "      - run: npm ci"
        ),
        "LINT_COMMAND": "npm run lint",
        "FORMAT_CHECK_COMMAND": "npx prettier --check .",
        "TYPECHECK_COMMAND": "tsc --noEmit",
        "TEST_COMMAND": "npm test",
        "BUILD_CHECK_COMMAND": "tsc --noEmit",
        "CI_AUTOHARNESS_INSTALL_COMMAND": "pip install autoharness",
    },
    "python": {
        "CI_EXPENSIVE_JOB_NAME": "test",
        "CI_REQUIRED_CHECK_NAME": "build",
        "CI_RUNNER_OS": "ubuntu-latest",
        "CI_DEFAULT_BRANCH": "main",
        "CI_DOCS_ONLY_PATHS": (
            "              - '!docs/**'\n"
            "              - '!.backlogit/**'\n"
            "              - '!.autoharness/**'"
        ),
        "CI_SETUP_STEPS": (
            "      - uses: actions/checkout@df4cb1c # v6.0.3\n"
            "      - run: pip install -e ."
        ),
        "LINT_COMMAND": "ruff check .",
        "FORMAT_CHECK_COMMAND": "ruff format --check .",
        "TYPECHECK_COMMAND": "mypy src/",
        "TEST_COMMAND": "pytest",
        "BUILD_CHECK_COMMAND": 'python -m py_compile src/pkg.py',
        "CI_AUTOHARNESS_INSTALL_COMMAND": "pip install -e .",
    },
    "go_non_main_default_branch": {
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6W0BCD): the
        # workflow's own `on: push:`/`on: pull_request:` trigger filters must
        # not hard-code `main`, or the job never starts at all for a
        # `master`/`trunk`-default repo -- topology.py's non-main default
        # branch fallback is moot if GitHub never triggers the workflow in
        # the first place. This profile renders with a non-`main` default
        # branch (backlogit's own convention) to cover that case directly.
        "CI_EXPENSIVE_JOB_NAME": "build",
        "CI_REQUIRED_CHECK_NAME": "ci gate",
        "CI_RUNNER_OS": "ubuntu-latest",
        "CI_DEFAULT_BRANCH": "master",
        "CI_DOCS_ONLY_PATHS": "              - '!docs/**'",
        "CI_SETUP_STEPS": (
            "      - uses: actions/checkout@df4cb1c # v6.0.3\n"
            "      - run: go build ./..."
        ),
        "LINT_COMMAND": "golangci-lint run",
        "FORMAT_CHECK_COMMAND": "gofmt -l .",
        "TYPECHECK_COMMAND": "",
        "TEST_COMMAND": "go test ./...",
        "BUILD_CHECK_COMMAND": "go build ./...",
        "CI_AUTOHARNESS_INSTALL_COMMAND": "pip install autoharness",
    },
}


def _render(profile: dict[str, str]) -> str:
    text = _CI_TEMPLATE.read_text(encoding="utf-8")
    for key, value in profile.items():
        text = text.replace("{{%s}}" % key, value)
    # Drop optional gate steps whose command resolved empty (installer behavior:
    # never leave a bare `run:` with no command).
    lines = [
        line
        for line in text.splitlines()
        if not re.fullmatch(r"\s*run:\s*", line)
    ]
    return "\n".join(lines)


def _evaluate_continue_on_error(expression: str, *, gate_required: str) -> bool:
    """Evaluate the fixed `${{ vars.PIPELINE_TOPOLOGY_GATE_REQUIRED != 'true' }}`
    GitHub Actions expression string for a given repository-variable value.

    This mirrors the GitHub Actions expression engine's behavior for a simple
    string `!=` comparison: an unset repository variable resolves to an empty
    string in expression context, not a YAML null. Only this one fixed
    comparison shape is supported; this is a targeted test helper, not a
    general expression evaluator.
    """
    match = re.fullmatch(
        r"\$\{\{\s*vars\.PIPELINE_TOPOLOGY_GATE_REQUIRED\s*!=\s*'true'\s*\}\}",
        expression.strip(),
    )
    if not match:
        raise AssertionError(
            "unrecognized continue-on-error expression shape: %r" % expression
        )
    return gate_required != "true"


class CiTemplateRenderingTests(unittest.TestCase):
    def test_renders_valid_yaml_for_each_profile(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                self.assertIsInstance(doc, dict)
                self.assertIn("jobs", doc)

    def test_trigger_filters_use_resolved_default_branch_not_hardcoded_main(self) -> None:
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6W0BCD): the
        # workflow's own `on: push:`/`on: pull_request:` trigger filters must
        # track the workspace's actual default branch via
        # {{CI_DEFAULT_BRANCH}} -- previously hard-coded to `main`, which
        # means the workflow never starts at all for a `master`/`trunk`
        # -default repo, making topology.py's non-main default-branch
        # fallback moot (the job simply never runs).
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                # PyYAML 1.1 resolves the bare `on` key as the boolean `True`
                # (the classic "Norway problem" GitHub Actions workflows are
                # famous for triggering) -- not the string `"on"`.
                triggers = doc[True]
                expected = [profile["CI_DEFAULT_BRANCH"]]
                self.assertEqual(triggers["push"]["branches"], expected)
                self.assertEqual(triggers["pull_request"]["branches"], expected)

    def test_no_unresolved_template_variables(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                leftover = _UNRESOLVED_VAR.findall(_render(profile))
                self.assertEqual(
                    leftover, [], f"{name}: unresolved template vars {leftover!r}"
                )

    def test_job_ids_are_fixed_valid_slugs(self) -> None:
        # Job IDs must be valid GH Actions identifiers and decoupled from the
        # human-facing check `name:` (which may contain spaces).
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                ids = list(doc["jobs"].keys())
                self.assertEqual(set(ids), {"changes", "expensive", "topology-check", "ci-gate"})
                for job_id in ids:
                    self.assertRegex(job_id, _JOB_ID)

    def test_changes_job_is_fail_closed(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                changes = doc["jobs"]["changes"]
                step = next(s for s in changes["steps"] if s.get("id") == "filter")
                self.assertEqual(
                    step["with"]["predicate-quantifier"],
                    "every",
                    "fail-closed detection requires predicate-quantifier: every",
                )
                self.assertIn("code", changes["outputs"])

    def test_expensive_job_gates_solely_on_path_impact(self) -> None:
        # No fail-open PR-title guard: the only condition is the code path output.
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                cond = str(doc["jobs"]["expensive"]["if"])
                self.assertIn("needs.changes.outputs.code == 'true'", cond)
                self.assertNotIn("title", cond.lower())
                self.assertNotIn("chore:", cond)
                self.assertNotIn("docs:", cond)

    def test_aggregation_gate_always_runs_and_needs_both_jobs(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                gate = doc["jobs"]["ci-gate"]
                self.assertEqual(str(gate["if"]).strip(), "always()")
                self.assertEqual(set(gate["needs"]), {"changes", "expensive", "topology-check"})

    def test_required_check_name_matches_profile(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                self.assertEqual(
                    doc["jobs"]["ci-gate"]["name"],
                    profile["CI_REQUIRED_CHECK_NAME"],
                )

    def test_least_privilege_permissions(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                self.assertEqual(doc.get("permissions"), {"contents": "read"})


class TopologyCheckJobTests(unittest.TestCase):
    """109.014-T (Shipment C / Gate C): the always-running pipeline-topology
    CI backstop job and its required-vs-advisory operator toggle."""

    def test_topology_check_job_present_for_every_profile(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                self.assertIn("topology-check", doc["jobs"])

    def test_topology_check_always_runs_not_gated_on_changes(self) -> None:
        # Unlike `expensive`, this job has no `if:` condition tying it to the
        # `changes` path-filter output -- the ambient check is inexpensive and
        # non-shipment-scoped and must not be skippable via a docs-only PR.
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                job = doc["jobs"]["topology-check"]
                self.assertNotIn("if", job)
                self.assertNotIn("needs", job)

    def test_topology_check_toggle_is_a_repository_variable_not_a_template_var(self) -> None:
        # The required-vs-advisory decision must be an OPERATOR TOGGLE
        # (repository variable), not a {{TEMPLATE_VAR}} resolved at install
        # time -- flipping it must never require a workflow re-render.
        text = _CI_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("PIPELINE_TOPOLOGY_GATE_REQUIRED", text)
        self.assertNotIn("{{CI_TOPOLOGY_GATE_REQUIRED}}", text)
        self.assertNotIn("{{PIPELINE_TOPOLOGY_GATE_REQUIRED}}", text)

    def test_topology_check_continue_on_error_defaults_advisory(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                job = doc["jobs"]["topology-check"]
                coe = str(job["continue-on-error"])
                self.assertIn("vars.PIPELINE_TOPOLOGY_GATE_REQUIRED", coe)
                self.assertIn("!= 'true'", coe)

    def test_topology_check_invokes_entrypoint_script(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                steps = doc["jobs"]["topology-check"]["steps"]
                run_steps = " ".join(s.get("run", "") for s in steps)
                self.assertIn("scripts/ci-topology-check.sh", run_steps)

    def test_topology_check_installs_autoharness_via_resolved_variable(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                steps = doc["jobs"]["topology-check"]["steps"]
                install_step = next(
                    s for s in steps if s.get("name") == "Install autoharness"
                )
                self.assertEqual(install_step["run"], profile["CI_AUTOHARNESS_INSTALL_COMMAND"])

    def test_ci_gate_includes_topology_check_in_results_aggregation(self) -> None:
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                gate_run = doc["jobs"]["ci-gate"]["steps"][0]["run"]
                self.assertIn("needs['topology-check'].result", gate_run)

    def test_ci_gate_needs_only_reference_defined_jobs(self) -> None:
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6Wzfxk):
        # install-harness omits the topology-check job entirely for
        # non-backlogit workspaces ({{FEATURE_SHIPMENTS}} == false), and that
        # omission must be a single atomic composition step that also strips
        # the corresponding `needs:` entry and `needs['topology-check'].result`
        # reference from ci-gate -- otherwise the rendered workflow references
        # an undefined job, which is invalid GitHub Actions YAML and breaks
        # ci-gate (all of CI) for that install, not merely the absent
        # backstop. This test documents the invariant on the always-shipped
        # (FEATURE_SHIPMENTS == true) template: every job named in ci-gate's
        # `needs:` array must correspond to an actual job key, and the
        # results= aggregation line's `needs[...]` bracket references must be
        # a subset of that same needs list.
        bracket_ref = re.compile(r"needs\[['\"]([\w-]+)['\"]\]")
        dotted_ref = re.compile(r"needs\.([A-Za-z0-9_]+)")
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                job_ids = set(doc["jobs"].keys())
                gate = doc["jobs"]["ci-gate"]
                needs = set(gate["needs"])
                self.assertTrue(needs.issubset(job_ids), f"dangling needs: {needs - job_ids}")
                gate_run = gate["steps"][0]["run"]
                referenced = set(bracket_ref.findall(gate_run)) | set(dotted_ref.findall(gate_run))
                self.assertTrue(
                    referenced.issubset(needs),
                    f"results= references a job not in needs:: {referenced - needs}",
                )
                self.assertIn("topology-check", needs)
                self.assertIn("topology-check", referenced)

    def test_topology_check_job_does_not_overclaim_non_bypassable(self) -> None:
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6WzvN-): a
        # `pull_request`-triggered workflow loads and runs its OWN definition
        # (and any script it invokes) from the PR's proposed head, so the
        # same PR that violates a topology invariant can also edit this job
        # or its entrypoint to trivially report success. The template must
        # not claim the job is a "NON-BYPASSABLE" backstop; any mention of
        # non-bypassability must be explicitly negated (documenting the
        # limitation), never an unqualified affirmative claim.
        rendered = _render(_PROFILES["rust"])
        self.assertNotIn("NON-BYPASSABLE", rendered)
        self.assertIn("NOT a non-bypassable backstop", rendered)
        self.assertIn("Threat Model & CODEOWNERS Hardening", rendered)

    def test_continue_on_error_expression_evaluates_both_toggle_states(self) -> None:
        # 109.012-T (C3) acceptance criterion: "CI entrypoint tests pass
        # (advisory and required modes)". The rendered `continue-on-error`
        # string is a fixed GitHub Actions expression:
        #   ${{ vars.PIPELINE_TOPOLOGY_GATE_REQUIRED != 'true' }}
        # This test evaluates that exact comparison directly (mirroring what
        # the GitHub Actions expression engine does for a simple `!=` string
        # comparison) under both toggle states, so both the advisory
        # (unset/anything-but-'true') and required ('true') branches are
        # exercised, not merely asserted-present as a substring.
        for name, profile in _PROFILES.items():
            with self.subTest(profile=name):
                doc = yaml.safe_load(_render(profile))
                coe = doc["jobs"]["topology-check"]["continue-on-error"]
                # unset repository variable resolves to an empty string in
                # GitHub Actions expression context.
                self.assertTrue(_evaluate_continue_on_error(coe, gate_required=""))
                self.assertTrue(_evaluate_continue_on_error(coe, gate_required="false"))
                self.assertFalse(_evaluate_continue_on_error(coe, gate_required="true"))


class HookTemplateStructureTests(unittest.TestCase):
    def test_sh_hook_has_explicit_probe_tool_call_sites(self) -> None:
        text = _HOOK_SH.read_text(encoding="utf-8")
        for gate, tool_var, cmd_var in (
            ("Lint", "LINT_TOOL", "LINT_COMMAND"),
            ("Format", "FORMAT_TOOL", "FORMAT_CHECK_COMMAND"),
            ("Typecheck", "TYPECHECK_TOOL", "TYPECHECK_COMMAND"),
            ("Test", "TEST_TOOL", "TEST_COMMAND"),
            ("Build", "BUILD_TOOL", "BUILD_CHECK_COMMAND"),
        ):
            self.assertIn(
                'run_gate "%s" "{{%s}}" "{{%s}}"' % (gate, tool_var, cmd_var),
                text,
            )

    def test_ps1_hook_has_explicit_probe_tool_call_sites(self) -> None:
        text = _HOOK_PS1.read_text(encoding="utf-8")
        for gate, tool_var, cmd_var in (
            ("Lint", "LINT_TOOL", "LINT_COMMAND"),
            ("Format", "FORMAT_TOOL", "FORMAT_CHECK_COMMAND"),
            ("Typecheck", "TYPECHECK_TOOL", "TYPECHECK_COMMAND"),
            ("Test", "TEST_TOOL", "TEST_COMMAND"),
            ("Build", "BUILD_TOOL", "BUILD_CHECK_COMMAND"),
        ):
            self.assertIn(
                'Invoke-Gate "%s" "{{%s}}" "{{%s}}"' % (gate, tool_var, cmd_var),
                text,
            )

    def test_hooks_are_single_pass_no_retry_loop(self) -> None:
        # Circuit-breaker safety: a pre-push hook must not spin.
        for path in (_HOOK_SH, _HOOK_PS1):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("while true", text)
            self.assertNotIn("for ((", text)


_TOPOLOGY_PRECOMMIT_SH = _REPO_ROOT / "templates" / "scripts" / "pre-commit-pipeline-topology.sh.tmpl"
_TOPOLOGY_PRECOMMIT_PS1 = _REPO_ROOT / "templates" / "scripts" / "pre-commit-pipeline-topology.ps1.tmpl"
_UNRESOLVED_ANY_VAR = re.compile(r"\{\{\s*[A-Za-z][A-Za-z0-9_]*\s*\}\}")


class PipelineTopologyHookTemplateTests(unittest.TestCase):
    """109.007-T / 109.008-T / 109.015-T: pipeline-topology hook templates."""

    def test_pre_push_hooks_invoke_ambient_gate_non_shipment_scoped(self) -> None:
        for path in (_HOOK_SH, _HOOK_PS1):
            text = path.read_text(encoding="utf-8")
            self.assertIn("gate pipeline-topology", text)
            self.assertIn("--phase ambient", text)
            invocation_line = next(
                line for line in text.splitlines() if "gate pipeline-topology --mode" in line
            )
            self.assertNotIn("--shipment", invocation_line)

    def test_pre_commit_topology_hooks_exist_and_invoke_ambient_gate(self) -> None:
        for path in (_TOPOLOGY_PRECOMMIT_SH, _TOPOLOGY_PRECOMMIT_PS1):
            self.assertTrue(path.exists(), f"missing template: {path}")
            text = path.read_text(encoding="utf-8")
            self.assertIn("gate pipeline-topology", text)
            self.assertIn("--phase ambient", text)
            invocation_line = next(
                line for line in text.splitlines() if "gate pipeline-topology --mode" in line
            )
            self.assertNotIn("--shipment", invocation_line)

    def test_pre_commit_topology_hooks_no_unresolved_placeholders(self) -> None:
        for path in (_TOPOLOGY_PRECOMMIT_SH, _TOPOLOGY_PRECOMMIT_PS1):
            text = path.read_text(encoding="utf-8")
            leftover = _UNRESOLVED_ANY_VAR.findall(text)
            self.assertEqual(leftover, [], f"{path.name}: unresolved template vars {leftover!r}")

    def test_pre_commit_topology_hooks_document_no_verify_bypass(self) -> None:
        for path in (_TOPOLOGY_PRECOMMIT_SH, _TOPOLOGY_PRECOMMIT_PS1):
            text = path.read_text(encoding="utf-8")
            self.assertIn("--no-verify", text)

    def test_pre_commit_topology_hooks_advisory_first_default(self) -> None:
        # Advisory-first: absent an explicit blocking toggle, a gate failure
        # must not translate into an unconditional non-zero exit.
        sh_text = _TOPOLOGY_PRECOMMIT_SH.read_text(encoding="utf-8")
        self.assertIn("AUTOHARNESS_TOPOLOGY_GATE_BLOCKING", sh_text)
        ps1_text = _TOPOLOGY_PRECOMMIT_PS1.read_text(encoding="utf-8")
        self.assertIn("AUTOHARNESS_TOPOLOGY_GATE_BLOCKING", ps1_text)

    def test_pre_commit_topology_hooks_single_pass_no_retry_loop(self) -> None:
        for path in (_TOPOLOGY_PRECOMMIT_SH, _TOPOLOGY_PRECOMMIT_PS1):
            text = path.read_text(encoding="utf-8").lower()
            self.assertNotIn("while true", text)
            self.assertNotIn("for ((", text)

    def test_pre_commit_topology_hooks_absent_tool_warns_and_skips(self) -> None:
        sh_text = _TOPOLOGY_PRECOMMIT_SH.read_text(encoding="utf-8")
        self.assertIn("command -v autoharness", sh_text)
        self.assertIn("exit 0", sh_text)
        ps1_text = _TOPOLOGY_PRECOMMIT_PS1.read_text(encoding="utf-8")
        self.assertIn("Get-Command autoharness", ps1_text)


_INSTALL_SKILL = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"
_TUNE_SKILL = _REPO_ROOT / ".github" / "skills" / "tune-harness" / "SKILL.md"


class PipelineTopologyInstallWiringTests(unittest.TestCase):
    """109.013-T / 109.015-T: opt-in install/tune wiring for the topology hooks."""

    def test_install_harness_never_silently_overwrites_git_hooks(self) -> None:
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        self.assertIn("pre-commit-pipeline-topology.sh.tmpl", text)
        self.assertIn("pre-commit-pipeline-topology.ps1.tmpl", text)
        # The row documenting the new hook must carry the same opt-in,
        # never-overwrite contract as the existing pre-push hook row.
        marker_index = text.index("Pipeline-topology pre-commit hook")
        row_text = text[marker_index : marker_index + 800]
        self.assertIn("Opt-in", row_text)
        self.assertIn("never overwrite", row_text)
        self.assertIn(".git/hooks/pre-commit", row_text)
        self.assertNotIn("core.hooksPath` automatically\n", row_text)

    def test_install_harness_step_4_4_verifies_pipeline_topology_hooks(self) -> None:
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        self.assertIn("Pipeline-topology hook verification", text)
        self.assertIn("--phase ambient", text)

    def test_tune_harness_flags_pipeline_topology_hook_drift(self) -> None:
        text = _TUNE_SKILL.read_text(encoding="utf-8")
        self.assertIn("Pipeline-topology hook drift", text)
        self.assertIn("pre-commit-pipeline-topology.sh", text)
        self.assertIn("AUTOHARNESS_TOPOLOGY_GATE_BLOCKING", text)


if __name__ == "__main__":
    unittest.main()
