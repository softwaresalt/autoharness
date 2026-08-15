"""Tests for the CI topology-check entrypoint script (109.011-T / Shipment C,
gate C of the staged A->B->C ``autoharness gate pipeline-topology`` rollout).

Protects the acceptance criteria for ``templates/ci/ci-topology-check.sh.tmpl``:

* the entrypoint invokes ``autoharness gate pipeline-topology --mode ci
  --phase ambient`` with NO human-supplied ``--shipment`` (non-shipment-scoped,
  deterministic target resolution reused from the local ambient hooks);
* it is fail-closed with NO advisory-degrade toggle (unlike the local
  pre-commit/pre-push hooks): a missing ``autoharness`` binary is a
  configuration failure (exit 1), not a warn-and-skip;
* it propagates the gate's raw exit code unmodified -- no exit-code
  translation, no swallowed failures;
* it documents (does not depend on) the local-worktree-state limitation and
  the detect-at-sync (not a lock/lease) contract;
* no unresolved ``{{VARIABLE}}`` placeholders survive;
* it is a single deterministic pass with no retry loop (circuit-breaker
  compatible).

A behavioral subprocess-execution test class (skipped on native Windows, since
bash there is WSL with its own path/CRLF quirks -- mirroring the existing
``DeployHarnessShOptInTests`` convention in ``test_deploy_harness_scripts.py``)
proves the real fail-closed exit-code propagation end to end against a stubbed
``autoharness`` on ``PATH``.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ENTRYPOINT = _REPO_ROOT / "templates" / "ci" / "ci-topology-check.sh.tmpl"
_UNRESOLVED_VAR = re.compile(r"\{\{\s*[A-Za-z][A-Za-z0-9_]*\s*\}\}")
_BASH = shutil.which("bash")


def _read() -> str:
    return _ENTRYPOINT.read_text(encoding="utf-8").replace("\r\n", "\n")


class CiTopologyCheckEntrypointStructureTests(unittest.TestCase):
    def test_template_exists(self) -> None:
        self.assertTrue(_ENTRYPOINT.exists(), f"missing template: {_ENTRYPOINT}")

    def test_no_unresolved_template_variables(self) -> None:
        leftover = _UNRESOLVED_VAR.findall(_read())
        self.assertEqual(leftover, [], f"unresolved template vars {leftover!r}")

    def test_invokes_ci_mode_ambient_phase_non_shipment_scoped(self) -> None:
        text = _read()
        self.assertIn("gate pipeline-topology", text)
        self.assertIn("--mode ci", text)
        self.assertIn("--phase ambient", text)
        invocation_line = next(
            line for line in text.splitlines() if "gate pipeline-topology --mode" in line
        )
        self.assertNotIn("--shipment", invocation_line)

    def test_fail_closed_no_advisory_degrade_toggle(self) -> None:
        # Unlike the local hooks, the CI entrypoint must NOT expose an
        # AUTOHARNESS_TOPOLOGY_GATE_BLOCKING-style advisory-degrade escape
        # hatch -- the required-vs-advisory decision belongs to the CI
        # workflow job (C2), not this entrypoint.
        text = _read()
        self.assertNotIn("AUTOHARNESS_TOPOLOGY_GATE_BLOCKING", text)

    def test_propagates_raw_exit_code_unmodified(self) -> None:
        text = _read()
        self.assertIn('exit_code=$?', text)
        self.assertIn('exit "$exit_code"', text)
        # No exit-code rewriting (e.g. forcing exit 0 on failure).
        self.assertNotIn("exit 0\nfi", text)

    def test_missing_autoharness_is_configuration_failure_not_advisory_skip(self) -> None:
        text = _read()
        command_probe_idx = text.index("command -v autoharness")
        snippet = text[command_probe_idx : command_probe_idx + 300]
        self.assertIn("exit 1", snippet)
        self.assertNotIn("exit 0", snippet)

    def test_documents_detect_at_sync_not_a_lock(self) -> None:
        text = _read()
        self.assertIn("DETECT-AT-SYNC", text)
        self.assertIn("NOT a lock", text)

    def test_documents_no_dependency_on_local_worktree_state(self) -> None:
        text = _read()
        self.assertIn("DOES NOT DEPEND ON MACHINE-LOCAL WORKTREE STATE", text)

    def test_documents_required_vs_advisory_toggle_lives_in_workflow(self) -> None:
        text = _read()
        self.assertIn("PIPELINE_TOPOLOGY_GATE_REQUIRED", text)

    def test_resolves_storage_root_with_shared_precedence(self) -> None:
        text = _read()
        self.assertIn("BACKLOGIT_WORKSPACE_DIR", text)
        self.assertIn("[ -d .backlog ]", text)
        self.assertIn("[ -d .backlogit ]", text)
        self.assertIn("resolved backlog root", text)

    def test_fails_closed_on_invalid_override_and_dual_root_ambiguity(self) -> None:
        text = _read()
        self.assertIn("BACKLOGIT_WORKSPACE_DIR is set but empty", text)
        self.assertIn("points to a missing directory", text)
        self.assertIn("both .backlog and .backlogit are present", text)
        self.assertIn("resolve the ambiguity", text)

    def test_override_must_be_exact_literal_candidate_name(self) -> None:
        # PR #344 Copilot review round 2, thread PRRT_kwDORzpWpM6ZihN-: the
        # override is not an arbitrary filesystem path; it must be exactly
        # ".backlog" or ".backlogit" (mirrors backlogit 1.9.0's
        # validateWorkspaceDirOverride). A single exact-string comparison
        # against both literals rejects separators, absolute paths, "."/"..",
        # and case aliases in one step.
        text = _read()
        self.assertIn('"$BACKLOGIT_WORKSPACE_DIR" != ".backlog"', text)
        self.assertIn('"$BACKLOGIT_WORKSPACE_DIR" != ".backlogit"', text)
        self.assertIn("must be exactly .backlog or .backlogit", text)

    def test_single_pass_no_retry_loop(self) -> None:
        text = _read().lower()
        self.assertNotIn("while true", text)
        self.assertNotIn("for ((", text)

    def test_reuses_gate_core_no_new_gate_logic(self) -> None:
        text = _read()
        self.assertIn("Reuses the gate core built in Shipment A", text)


def _stub_autoharness_path(tmp_dir: Path, exit_code: int) -> Path:
    """Write a minimal stub ``autoharness`` executable on a directory that can
    be prepended to PATH, so the real CLI/backlogit state never has to be
    exercised for this pure exit-code-propagation contract test."""
    stub = tmp_dir / "autoharness"
    stub.write_text(
        "#!/usr/bin/env bash\n"
        "echo '{\"stub\": true}'\n"
        f"exit {exit_code}\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    return tmp_dir


@unittest.skipIf(sys.platform == "win32", "bash on Windows is WSL; run bash on POSIX/CI")
@unittest.skipUnless(_BASH, "bash not available")
class CiTopologyCheckEntrypointBehaviorTests(unittest.TestCase):
    """Real subprocess-execution proof of fail-closed exit-code propagation."""

    def _run(self, exit_code: int, *, autoharness_present: bool = True):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # LF-normalise: the committed template may carry CRLF, which
            # corrupts bash tokens on POSIX (same rationale as
            # DeployHarnessShOptInTests).
            script = tmp_path / "ci-topology-check.sh"
            script.write_text(_read(), encoding="utf-8", newline="\n")
            script.chmod(0o755)

            env = dict(os.environ)
            if autoharness_present:
                stub_dir = tmp_path / "stub-bin"
                stub_dir.mkdir()
                _stub_autoharness_path(stub_dir, exit_code)
                env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"
            else:
                # Keep standard POSIX bin dirs so `git`/`bash` still resolve,
                # but exclude any component that might carry an installed
                # `autoharness` console script (e.g. a venv's bin/Scripts dir).
                env["PATH"] = "/usr/bin:/bin"

            return subprocess.run(
                [_BASH, str(script)],
                cwd=_REPO_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )

    def test_pass_propagates_exit_0(self) -> None:
        result = self._run(0)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_block_propagates_exit_1(self) -> None:
        result = self._run(1)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_invalid_propagates_exit_2(self) -> None:
        result = self._run(2)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_missing_autoharness_fails_closed_exit_1(self) -> None:
        result = self._run(0, autoharness_present=False)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("not found on PATH", result.stdout + result.stderr)

    def _run_in_isolated_workspace(
        self,
        *,
        exit_code: int = 0,
        backlog_dirs: tuple = (),
        override_env: dict = None,
    ):
        """Run the entrypoint against a real, isolated git repository (never
        this repository's own single `.backlogit` root) so the new
        BACKLOGIT_WORKSPACE_DIR / dual-root resolution branches are actually
        exercised end to end (Copilot review, PR #344 thread
        PRRT_kwDORzpWpM6ZiZHb): the pre-existing subprocess tests above only
        assert the branch strings exist in the template text, never that the
        shell control flow for empty-override, missing-override, or
        dual-root-ambiguity actually resolves/fails correctly."""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            subprocess.run(
                ["git", "init", "-q"], cwd=tmp_path, check=True, timeout=30
            )
            for name in backlog_dirs:
                (tmp_path / name).mkdir(parents=True, exist_ok=True)

            script = tmp_path / "ci-topology-check.sh"
            script.write_text(_read(), encoding="utf-8", newline="\n")
            script.chmod(0o755)

            stub_dir = tmp_path / "stub-bin"
            stub_dir.mkdir()
            _stub_autoharness_path(stub_dir, exit_code)

            env = dict(os.environ)
            env["PATH"] = f"{stub_dir}{os.pathsep}{env.get('PATH', '')}"
            if override_env:
                env.update(override_env)
            else:
                env.pop("BACKLOGIT_WORKSPACE_DIR", None)

            return subprocess.run(
                [_BASH, str(script)],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )

    def test_dot_backlog_only_workspace_resolves_and_passes(self) -> None:
        result = self._run_in_isolated_workspace(exit_code=0, backlog_dirs=(".backlog",))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("resolved backlog root: .backlog", result.stdout)

    def test_legacy_dot_backlogit_only_workspace_resolves_and_passes(self) -> None:
        result = self._run_in_isolated_workspace(exit_code=0, backlog_dirs=(".backlogit",))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("resolved backlog root: .backlogit", result.stdout)

    def test_dual_root_present_with_no_override_fails_closed(self) -> None:
        result = self._run_in_isolated_workspace(
            exit_code=0, backlog_dirs=(".backlog", ".backlogit")
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "both .backlog and .backlogit are present", result.stdout + result.stderr
        )

    def test_empty_override_fails_closed(self) -> None:
        result = self._run_in_isolated_workspace(
            exit_code=0, backlog_dirs=(".backlog",), override_env={"BACKLOGIT_WORKSPACE_DIR": ""}
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "BACKLOGIT_WORKSPACE_DIR is set but empty", result.stdout + result.stderr
        )

    def test_override_naming_missing_directory_fails_closed(self) -> None:
        # A valid literal override name (.backlogit) that does not exist on
        # disk still fails closed on the missing-directory branch, distinct
        # from the exact-literal-name rejection branch below.
        result = self._run_in_isolated_workspace(
            exit_code=0,
            backlog_dirs=(".backlog",),
            override_env={"BACKLOGIT_WORKSPACE_DIR": ".backlogit"},
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "points to a missing directory", result.stdout + result.stderr
        )

    def test_override_naming_non_literal_value_fails_closed(self) -> None:
        # PR #344 Copilot review round 2, thread PRRT_kwDORzpWpM6ZihN-: an
        # override value that is not exactly ".backlog" or ".backlogit" --
        # even if it names a directory that actually exists on disk -- must
        # be rejected before any directory-existence check runs, since the
        # override is not an arbitrary filesystem path.
        result = self._run_in_isolated_workspace(
            exit_code=0,
            backlog_dirs=(".backlog", "custom-root"),
            override_env={"BACKLOGIT_WORKSPACE_DIR": "custom-root"},
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(
            "must be exactly .backlog or .backlogit", result.stdout + result.stderr
        )

    def test_valid_override_takes_precedence_over_dual_root_ambiguity(self) -> None:
        # A valid, literal BACKLOGIT_WORKSPACE_DIR override (one of the two
        # supported candidate names) resolves the root even when both
        # .backlog and .backlogit also happen to exist -- the override
        # branch is checked first and short-circuits the dual-root ambiguity
        # branch entirely (Copilot review, PR #344 threads
        # PRRT_kwDORzpWpM6ZiZHP / PRRT_kwDORzpWpM6ZiZHZ: the ambiguity rule
        # must not fire when a valid override already resolves the root).
        # Round 2 (thread PRRT_kwDORzpWpM6ZihN-) tightened the override to
        # only the two literal names, so this now overrides to .backlogit
        # rather than an arbitrary "custom-root" name.
        result = self._run_in_isolated_workspace(
            exit_code=0,
            backlog_dirs=(".backlog", ".backlogit"),
            override_env={"BACKLOGIT_WORKSPACE_DIR": ".backlogit"},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("resolved backlog root: .backlogit", result.stdout)


_INSTALL_SKILL = _REPO_ROOT / ".github" / "skills" / "install-harness" / "SKILL.md"


class CiTopologyCheckInstallWiringTests(unittest.TestCase):
    """109.011-T: install-harness must wire the new entrypoint into the
    installed-artifact map and the verify-workspace check registry."""

    def test_install_harness_copies_entrypoint_script(self) -> None:
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        self.assertIn("ci-topology-check.sh.tmpl", text)
        self.assertIn("scripts/ci-topology-check.sh", text)

    def test_install_harness_verify_step_checks_entrypoint(self) -> None:
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        marker_index = text.index("When present, confirm")
        snippet = text[marker_index : marker_index + 900]
        self.assertIn("scripts/ci-topology-check.sh", snippet)
        self.assertIn("--mode ci", snippet)
        self.assertIn("--phase ambient", snippet)
        self.assertIn("PIPELINE_TOPOLOGY_GATE_REQUIRED", snippet)

    def test_install_harness_verify_step_gates_on_feature_shipments(self) -> None:
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6WzLkw):
        # FilesystemTopologyReaders reads only `.backlogit`, so installing the
        # topology-check job/entrypoint unconditionally would leave
        # backlog-md/manual workspaces permanently BACKLOG_UNAVAILABLE once the
        # job is promoted to required. Both the artifact-map rows and the
        # Phase 4 verification step must condition presence on
        # `{{FEATURE_SHIPMENTS}}`.
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        ci_workflow_row_index = text.index("Includes the always-running `topology-check` job")
        ci_workflow_row = text[ci_workflow_row_index : ci_workflow_row_index + 700]
        self.assertIn("{{FEATURE_SHIPMENTS}}", ci_workflow_row)
        self.assertIn("BACKLOG_UNAVAILABLE", ci_workflow_row)

        entrypoint_row_index = text.index("CI topology-check entrypoint (109.011-T / C1")
        entrypoint_row = text[entrypoint_row_index : entrypoint_row_index + 200]
        self.assertIn("{{FEATURE_SHIPMENTS}}", entrypoint_row)

        verify_step_index = text.index("confirm the `topology-check` job's presence matches")
        verify_step = text[verify_step_index : verify_step_index + 2200]
        self.assertIn("{{FEATURE_SHIPMENTS}}", verify_step)
        self.assertIn("Report FAIL for", verify_step)

    def test_install_harness_verify_step_requires_atomic_needs_results_strip(self) -> None:
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6Wzfxk): omitting
        # the topology-check job for non-backlogit workspaces must also strip
        # ci-gate's `needs:` entry and `results=` reference to it atomically —
        # otherwise ci-gate is left with a dangling reference to an undefined
        # job, breaking all of CI for every non-backlogit install.
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        verify_step_index = text.index("confirm the `topology-check` job's presence matches")
        verify_step = text[verify_step_index : verify_step_index + 2200]
        self.assertIn("needs", verify_step)
        self.assertIn("results=", verify_step)
        self.assertIn("dangling reference to an undefined job", verify_step)
        self.assertIn("dangling `needs`/`results`", verify_step)

    def test_install_harness_verify_step_rejects_unresolved_default_branch_guess(self) -> None:
        # Copilot review finding (PR #302 thread PRRT_kwDORzpWpM6W0M_t):
        # silently guessing `main` when {{CI_DEFAULT_BRANCH}} cannot be
        # resolved would install a workflow that never triggers at all on a
        # master/trunk-default repo's actual default branch, silently
        # disabling the CI backstop (and every other CI job in the file).
        # The verify step must report FAIL if installation proceeded past an
        # unresolved default branch rather than halting to ask the operator.
        text = _INSTALL_SKILL.read_text(encoding="utf-8")
        verify_step_index = text.index("confirm the `topology-check` job's presence matches")
        verify_step = text[verify_step_index : verify_step_index + 2800]
        self.assertIn("{{CI_DEFAULT_BRANCH}}", verify_step)
        self.assertIn("halting to ask the operator", verify_step)

        variable_row_index = text.index("The target workspace's actual default branch name")
        variable_row = text[variable_row_index : variable_row_index + 1400]
        self.assertIn("Never guess `main`", variable_row)
        self.assertIn("halt installation", variable_row)


if __name__ == "__main__":
    unittest.main()
