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
import unittest
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PS1_INSTANCE = _REPO_ROOT / "scripts" / "deploy-harness.ps1"
_SH_INSTANCE = _REPO_ROOT / "scripts" / "deploy-harness.sh"
_PS1_TEMPLATE = _REPO_ROOT / "templates" / "scripts" / "deploy-harness.ps1.tmpl"
_SH_TEMPLATE = _REPO_ROOT / "templates" / "scripts" / "deploy-harness.sh.tmpl"

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


if __name__ == "__main__":
    unittest.main()
