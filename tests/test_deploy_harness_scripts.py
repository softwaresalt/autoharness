"""Rendering + parity + behavior tests for the scripted deploy-harness family.

Protects the 070-F cross-platform deploy scripts (``deploy-harness.ps1`` /
``deploy-harness.sh``) and their templates:

* every ``{{UPPER_SNAKE}}`` variable resolves (no placeholder survives);
* rendering a template with the dogfood variable map reproduces the committed
  instance byte-for-byte (template <-> instance parity — the mirror cannot drift);
* the deterministic six-phase contract is preserved (preflight, bootstrap,
  register, scaffold, compose, verify);
* compose is HANDOFF-ONLY (prints ``/install-harness``; never resolves templates);
* ``--dry-run`` / ``-DryRun`` previews without requiring the ``--bootstrap`` gate
  (dry-run early-return precedes the bootstrap authorization gate);
* the verify phase skips gracefully when no harness manifest exists yet;
* ``plugin`` is not offered as a bootstrap ``--install-method`` (it cannot yield a
  resolvable ``autoharness_home``).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PS1_INSTANCE = _REPO_ROOT / "scripts" / "deploy-harness.ps1"
_SH_INSTANCE = _REPO_ROOT / "scripts" / "deploy-harness.sh"
_PS1_TEMPLATE = _REPO_ROOT / "templates" / "scripts" / "deploy-harness.ps1.tmpl"
_SH_TEMPLATE = _REPO_ROOT / "templates" / "scripts" / "deploy-harness.sh.tmpl"
_REGISTRY = _REPO_ROOT / "templates" / "packs" / "capability-pack-registry.yaml"

_UNRESOLVED_VAR = re.compile(r"\{\{\s*[A-Z][A-Z0-9_]*\s*\}\}")

# The dogfood variable map: the concrete values the installer resolves for the
# autoharness self-install. Rendering each template with this map MUST reproduce
# the committed instance.
_DOGFOOD_VARS = {
    "PROJECT_NAME": "autoharness",
    "DEFAULT_PRESET": "full",
    "DEFAULT_REGISTER_ENV": "copilot-cli",
    "DEFAULT_INSTALL_METHOD": "pip",
    "AUTOHARNESS_HOME_DEFAULT": "$HOME/.autoharness",
    "PACK_REGISTRY_PATH": "templates/packs/capability-pack-registry.yaml",
}

_PAIRS = (
    ("ps1", _PS1_TEMPLATE, _PS1_INSTANCE),
    ("sh", _SH_TEMPLATE, _SH_INSTANCE),
)


def _read(path: Path) -> str:
    # Normalise line endings so the checks are indifferent to core.autocrlf.
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def _render(template: Path) -> str:
    text = _read(template)
    for key, value in _DOGFOOD_VARS.items():
        text = text.replace("{{%s}}" % key, value)
    return text


class DeployHarnessRenderingTests(unittest.TestCase):
    def test_no_unresolved_variables_after_render(self) -> None:
        for name, template, _ in _PAIRS:
            with self.subTest(script=name):
                leftover = _UNRESOLVED_VAR.findall(_render(template))
                self.assertEqual(
                    leftover, [], f"{name}: unresolved template vars {leftover!r}"
                )

    def test_template_renders_to_committed_instance(self) -> None:
        # Parity guard: the dogfood instance is exactly the template rendered with
        # the dogfood variable map. This makes template/instance drift a test
        # failure rather than a silent divergence.
        for name, template, instance in _PAIRS:
            with self.subTest(script=name):
                self.assertEqual(
                    _render(template),
                    _read(instance),
                    f"{name}: rendered template diverges from committed instance",
                )

    def test_instances_have_no_placeholders(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                leftover = _UNRESOLVED_VAR.findall(_read(instance))
                self.assertEqual(
                    leftover, [], f"{name}: instance still contains {leftover!r}"
                )


class DeployHarnessBehaviorTests(unittest.TestCase):
    def test_six_phase_contract_present(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                for phase in (
                    "preflight",
                    "bootstrap",
                    "register",
                    "scaffold",
                    "compose",
                    "verify",
                ):
                    self.assertIn(
                        phase, text, f"{name}: missing phase '{phase}'"
                    )

    def test_compose_is_handoff_only(self) -> None:
        # Compose prints the /install-harness command and never resolves templates.
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                self.assertIn("/install-harness", _read(instance))

    def test_dry_run_previews_without_bootstrap_gate(self) -> None:
        # The dry-run early return must appear BEFORE the bootstrap authorization
        # gate so a plain --dry-run previews the plan without exiting 2.
        markers = {
            "ps1": (
                '[dry-run] would install autoharness globally',
                'requires the explicit -Bootstrap opt-in',
            ),
            "sh": (
                '[dry-run] would install autoharness globally',
                'requires the explicit --bootstrap opt-in',
            ),
        }
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                dry_marker, gate_marker = markers[name]
                dry_idx = text.find(dry_marker)
                gate_idx = text.find(gate_marker)
                self.assertNotEqual(dry_idx, -1, f"{name}: dry-run marker missing")
                self.assertNotEqual(gate_idx, -1, f"{name}: bootstrap gate missing")
                self.assertLess(
                    dry_idx,
                    gate_idx,
                    f"{name}: dry-run early-return must precede the bootstrap gate",
                )

    def test_verify_skips_when_no_manifest(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                self.assertIn("harness-manifest.yaml", text)
                self.assertIn("no harness manifest yet", text)

    def test_plugin_is_not_a_bootstrap_install_method(self) -> None:
        # `plugin` cannot resolve an autoharness_home; it must not be a valid
        # --install-method value. (The register phase still uses `copilot plugin
        # install` for copilot-cli, which is a separate concern.)
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                self.assertNotIn("pip|clone|plugin", text)
                self.assertNotIn('"pip", "clone", "plugin"', text)

    def test_register_adds_marketplace_before_install(self) -> None:
        # The copilot-cli register path must add the marketplace before installing
        # the plugin, matching the documented install sequence.
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                mk = text.find("copilot plugin marketplace add softwaresalt/autoharness")
                inst = text.find("copilot plugin install autoharness@autoharness")
                self.assertNotEqual(mk, -1, f"{name}: marketplace add missing")
                self.assertNotEqual(inst, -1, f"{name}: plugin install missing")
                self.assertLess(
                    mk, inst, f"{name}: marketplace add must precede plugin install"
                )

class DeployHarnessScaffoldSymlinkTests(unittest.TestCase):
    def test_scaffold_enforces_symlink_containment(self) -> None:
        markers = {
            "ps1": "reparse point/symlink (cwd containment)",
            "sh": "is a symlink (cwd containment)",
        }
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                self.assertIn(markers[name], _read(instance))


# ── Capability-pack runtime detection + pre-merge-install checklist ─────────
# (114.001-T / 114.002-T / 114.003-T, 47971057 bounded)
#
# Guards the bounded detection/checklist/report increment from
# docs/decisions/2026-08-07-capability-pack-runtime-installer-deliberation.md:
# per-pack presence+version detection, a REPORT-ONLY recommended-action
# checklist (retain-present / needs-install[deferred] / unsupported-
# undetectable), a non-interactive-by-default CI-safe fallback, and the
# explicit provision-before-compose ordering statement. NO install/upgrade/
# provisioning execution may ever be introduced by this increment.
class DeployHarnessCapabilityPackChecklistTests(unittest.TestCase):
    def test_detection_helper_present(self) -> None:
        markers = {"ps1": "Get-PackDetectionStatus", "sh": "pack_detect_status"}
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                self.assertIn(markers[name], _read(instance))

    def test_checklist_phase_present(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                self.assertIn(
                    "checklist (pre-merge-install; report only)", _read(instance)
                )

    def test_recommended_action_categories_present(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                for category in (
                    "retain-present",
                    "needs-install (deferred)",
                    "unsupported-undetectable",
                ):
                    self.assertIn(category, text, f"{name}: missing '{category}'")

    def test_report_only_no_provisioning_wording(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                self.assertIn("REPORT ONLY", text)
                self.assertIn("no install/upgrade is executed", text)

    def test_provision_before_compose_ordering_statement(self) -> None:
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                self.assertIn(
                    "MUST occur BEFORE merge-install composition", text
                )
                self.assertIn(
                    "docs/decisions/2026-08-07-capability-pack-runtime-installer-deliberation.md",
                    text,
                )

    def test_interactive_flag_present_and_opt_in(self) -> None:
        markers = {"ps1": "[switch]$Interactive", "sh": "--interactive"}
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                self.assertIn(markers[name], _read(instance))

    def test_checklist_runs_between_preflight_and_bootstrap(self) -> None:
        # The checklist phase must run after preflight (it consumes detection
        # results) and before bootstrap in the orchestration order.
        markers = {
            "ps1": (
                "if (-not (Invoke-Preflight)) { exit 1 }",
                "Invoke-PreMergeInstallChecklist",
                "$homePath = Invoke-Bootstrap",
            ),
            "sh": (
                "invoke_preflight || exit 1",
                "invoke_checklist",
                "invoke_bootstrap || exit 2",
            ),
        }
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                preflight_marker, checklist_marker, bootstrap_marker = markers[name]
                # Search within the orchestration section (after the function
                # definitions) so the CALL order is checked, not incidental
                # earlier occurrences of the checklist function/name in its
                # own definition.
                preflight_idx = text.find(preflight_marker)
                self.assertNotEqual(preflight_idx, -1)
                checklist_idx = text.find(checklist_marker, preflight_idx)
                self.assertNotEqual(checklist_idx, -1)
                bootstrap_idx = text.find(bootstrap_marker, checklist_idx)
                self.assertNotEqual(bootstrap_idx, -1)
                self.assertLess(preflight_idx, checklist_idx)
                self.assertLess(checklist_idx, bootstrap_idx)

    def test_no_provisioning_execution_verbs_introduced(self) -> None:
        # Bounded-increment guard: this scope must never introduce actual
        # install/upgrade EXECUTION for capability packs (detection/report
        # only). The pre-existing bootstrap install of autoharness ITSELF
        # (pip install / git clone of autoharness_home) is a different,
        # already-existing concern and is excluded from this guard.
        forbidden = ("pip install", "npm install", "brew install", "choco install")
        for name, _, instance in _PAIRS:
            with self.subTest(script=name):
                text = _read(instance)
                checklist_start = text.find("checklist (pre-merge-install")
                self.assertNotEqual(checklist_start, -1)
                # Slice from the checklist phase heading to the bootstrap
                # phase heading; only the checklist's own body is scoped here.
                bootstrap_heading = (
                    "Phase 2: bootstrap" if name == "ps1" else "Phase 2: bootstrap"
                )
                checklist_end = text.find(bootstrap_heading, checklist_start)
                self.assertNotEqual(checklist_end, -1)
                checklist_body = text[checklist_start:checklist_end]
                for verb in forbidden:
                    self.assertNotIn(verb, checklist_body)


# ── Opt-in pack-selection precedence (096.002-T / 096.003-T) ─────────────────
#
# These tests EXECUTE the real deploy wrappers in a throwaway workspace and read
# the ``.autoharness/config.yaml`` they scaffold, asserting the uniform
# precedence contract:
#   1. EXPLICIT pack input is honored on every preset (including starter).
#   2. OMITTED pack input resolves to the preset's ``default_in_preset`` members
#      (starter -> empty), so an opt-in add-on such as ``agent-intercom``
#      (``default_in_preset: []``) is never written by a default deploy.
# The precedence mirrors the installer contract in
# ``.github/skills/install-harness/SKILL.md:551`` (explicit capability_packs used
# as-is regardless of preset; omitted resolves to preset defaults) and guards the
# 082-S FU-1 regression (``docs/memory/082-S-closure.md:72``) where an explicit
# starter selection was discarded.

_PWSH = shutil.which("pwsh") or shutil.which("powershell")
_BASH = shutil.which("bash")


def _parse_registry() -> "tuple[list[str], dict[str, set[str]]]":
    """Return (ordered pack ids, id -> set of presets from default_in_preset)."""
    text = _read(_REGISTRY)
    ids: list[str] = []
    defaults: dict[str, set[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        m = re.match(r'^\s*-\s*id:\s*"([^"]+)"', line)
        if m:
            current = m.group(1)
            ids.append(current)
            defaults[current] = set()
            continue
        m = re.match(r"^\s*default_in_preset:\s*\[(.*)\]\s*$", line)
        if m and current is not None:
            defaults[current] = set(re.findall(r'"([^"]+)"', m.group(1)))
            current = None
    return ids, defaults


def _all_registry_packs() -> list[str]:
    return _parse_registry()[0]


def _preset_default_packs(preset: str) -> list[str]:
    ids, defaults = _parse_registry()
    return [pid for pid in ids if preset in defaults[pid]]


def _read_scaffolded_packs(workspace: Path) -> "list[str] | None":
    """Parse capability_packs from a scaffolded .autoharness/config.yaml."""
    cfg = workspace / ".autoharness" / "config.yaml"
    if not cfg.exists():
        return None
    text = cfg.read_text(encoding="utf-8").replace("\r\n", "\n")
    packs: list[str] = []
    in_list = False
    for line in text.splitlines():
        if re.match(r"^capability_packs:\s*\[\s*\]\s*$", line):
            return []
        if re.match(r"^capability_packs:\s*$", line):
            in_list = True
            continue
        if in_list:
            m = re.match(r"^\s+-\s*(\S+)\s*$", line)
            if m:
                packs.append(m.group(1))
            else:
                in_list = False
    return packs


class _DeployWrapperOptInMixin:
    """Shared opt-in precedence assertions, run once per interpreter."""

    interpreter: str = ""

    def _scaffold(self, preset: str, packs: "str | None"):  # noqa: ANN001
        raise NotImplementedError

    def _run_and_read(self, preset: str, packs: "str | None") -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            proc = self._scaffold(preset, packs, workspace)
            result = _read_scaffolded_packs(workspace)
            self.assertIsNotNone(  # type: ignore[attr-defined]
                result,
                f"{self.interpreter}: no config.yaml scaffolded "
                f"(preset={preset}, packs={packs}); "
                f"exit={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            return result

    # --- OMITTED input -> preset defaults --------------------------------
    def test_omitted_full_excludes_agent_intercom(self) -> None:
        packs = self._run_and_read("full", None)
        self.assertNotIn("agent-intercom", packs)  # type: ignore[attr-defined]
        self.assertEqual(  # type: ignore[attr-defined]
            set(packs), set(_preset_default_packs("full"))
        )

    def test_omitted_standard_excludes_agent_intercom(self) -> None:
        packs = self._run_and_read("standard", None)
        self.assertNotIn("agent-intercom", packs)  # type: ignore[attr-defined]
        self.assertEqual(  # type: ignore[attr-defined]
            set(packs), set(_preset_default_packs("standard"))
        )

    def test_omitted_starter_selects_no_packs(self) -> None:
        packs = self._run_and_read("starter", None)
        self.assertEqual(packs, [])  # type: ignore[attr-defined]

    # --- EXPLICIT input -> honored regardless of preset ------------------
    def test_explicit_all_full_includes_agent_intercom(self) -> None:
        packs = self._run_and_read("full", "all")
        self.assertIn("agent-intercom", packs)  # type: ignore[attr-defined]
        self.assertEqual(  # type: ignore[attr-defined]
            set(packs), set(_all_registry_packs())
        )

    def test_explicit_all_starter_includes_every_pack(self) -> None:
        # starter must NOT discard an explicit selection (guards 082-S FU-1).
        packs = self._run_and_read("starter", "all")
        self.assertIn("agent-intercom", packs)  # type: ignore[attr-defined]
        self.assertEqual(  # type: ignore[attr-defined]
            set(packs), set(_all_registry_packs())
        )

    def test_explicit_subset_starter_keeps_exact_subset(self) -> None:
        # The critical 082-S FU-1 regression guard: starter + explicit subset
        # must yield EXACTLY that subset, not an empty pack set.
        subset = ["backlogit", "strict-safety"]
        packs = self._run_and_read("starter", ",".join(subset))
        self.assertEqual(set(packs), set(subset))  # type: ignore[attr-defined]

    def test_explicit_subset_full_keeps_exact_subset(self) -> None:
        subset = ["agent-intercom", "backlogit"]
        packs = self._run_and_read("full", ",".join(subset))
        self.assertEqual(set(packs), set(subset))  # type: ignore[attr-defined]


@unittest.skipUnless(_PWSH, "PowerShell (pwsh/powershell) not available")
class DeployHarnessPs1OptInTests(_DeployWrapperOptInMixin, unittest.TestCase):
    interpreter = "ps1"

    def _scaffold(self, preset, packs, workspace):  # noqa: ANN001
        args = [
            _PWSH,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(_PS1_INSTANCE),
            "-Home",
            str(_REPO_ROOT),
            "-Register",
            "none",
            "-Preset",
            preset,
        ]
        if packs is not None:
            args += ["-Packs", packs]
        return subprocess.run(
            args, cwd=workspace, capture_output=True, text=True, timeout=180
        )


@unittest.skipIf(sys.platform == "win32", "bash on Windows is WSL; run sh on POSIX/CI")
@unittest.skipUnless(_BASH, "bash not available")
class DeployHarnessShOptInTests(_DeployWrapperOptInMixin, unittest.TestCase):
    interpreter = "sh"

    def _scaffold(self, preset, packs, workspace):  # noqa: ANN001
        # The committed script is CRLF; a CRLF bash script fails on POSIX
        # (stray \r corrupts tokens). Run an LF-normalised copy instead.
        lf_script = workspace / "_deploy-harness.sh"
        lf_script.write_bytes(_read(_SH_INSTANCE).encode("utf-8"))
        lf_script.chmod(0o755)
        args = [
            _BASH,
            str(lf_script),
            "--home",
            str(_REPO_ROOT),
            "--register",
            "none",
            "--preset",
            preset,
        ]
        if packs is not None:
            args += ["--packs", packs]
        return subprocess.run(
            args, cwd=workspace, capture_output=True, text=True, timeout=180
        )


class DeployWrapperRegistryEnumerationTests(unittest.TestCase):
    """The registry parse the wrappers rely on is structurally sound."""

    def test_agent_intercom_is_not_a_preset_default(self) -> None:
        _, defaults = _parse_registry()
        self.assertEqual(defaults.get("agent-intercom"), set())

    def test_default_in_preset_is_parseable_for_every_pack(self) -> None:
        ids, defaults = _parse_registry()
        self.assertIn("agent-intercom", ids)
        for pid in ids:
            self.assertIn(pid, defaults)

    def test_full_defaults_are_all_packs_except_opt_in_add_ons(self) -> None:
        full_defaults = set(_preset_default_packs("full"))
        self.assertNotIn("agent-intercom", full_defaults)
        self.assertLess(full_defaults, set(_all_registry_packs()))


# ── Checklist phase EXECUTION tests (non-interactive default; no hang) ──────
# Guards that the default (no -Interactive/--interactive) run never blocks on
# stdin and always prints the REPORT-ONLY per-pack recommended action.
class _ChecklistExecutionMixin:
    interpreter: str = ""

    def _run(self, workspace: Path):  # noqa: ANN001
        raise NotImplementedError

    def test_checklist_report_prints_non_interactively(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            proc = self._run(workspace)
            self.assertEqual(  # type: ignore[attr-defined]
                proc.returncode,
                0,
                f"{self.interpreter}: non-zero exit {proc.returncode}\n"  # type: ignore[attr-defined]
                f"STDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}",
            )
            combined = proc.stdout + proc.stderr
            self.assertIn(  # type: ignore[attr-defined]
                "checklist (pre-merge-install; report only)", combined
            )
            self.assertIn("REPORT ONLY", combined)  # type: ignore[attr-defined]
            # At least one recommended-action category must appear (packs are
            # typically absent in a throwaway CI/test workspace).
            self.assertTrue(  # type: ignore[attr-defined]
                any(
                    cat in combined
                    for cat in (
                        "retain-present",
                        "needs-install (deferred)",
                        "unsupported-undetectable",
                    )
                ),
                f"no recommended-action category found:\n{combined}",
            )


@unittest.skipUnless(_PWSH, "PowerShell (pwsh/powershell) not available")
class DeployHarnessPs1ChecklistExecutionTests(
    _ChecklistExecutionMixin, unittest.TestCase
):
    interpreter = "ps1"

    def _run(self, workspace):  # noqa: ANN001
        args = [
            _PWSH,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(_PS1_INSTANCE),
            "-Home",
            str(_REPO_ROOT),
            "-Register",
            "none",
            "-Preset",
            "starter",
            "-DryRun",
        ]
        return subprocess.run(
            args, cwd=workspace, capture_output=True, text=True, timeout=180
        )


@unittest.skipIf(sys.platform == "win32", "bash on Windows is WSL; run sh on POSIX/CI")
@unittest.skipUnless(_BASH, "bash not available")
class DeployHarnessShChecklistExecutionTests(
    _ChecklistExecutionMixin, unittest.TestCase
):
    interpreter = "sh"

    def _run(self, workspace):  # noqa: ANN001
        lf_script = workspace / "_deploy-harness.sh"
        lf_script.write_bytes(_read(_SH_INSTANCE).encode("utf-8"))
        lf_script.chmod(0o755)
        args = [
            _BASH,
            str(lf_script),
            "--home",
            str(_REPO_ROOT),
            "--register",
            "none",
            "--preset",
            "starter",
            "--dry-run",
        ]
        return subprocess.run(
            args, cwd=workspace, capture_output=True, text=True, timeout=180
        )


if __name__ == "__main__":
    unittest.main()
