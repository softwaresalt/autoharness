"""Regression tests for the opt-in config templates (P-018 round-5 finding).

``hooks.json.example`` previously used a bare ``"command"`` field for its
single command-hook entry. The Copilot CLI hooks reference documents
``command`` as a valid cross-platform fallback (copied to both ``bash`` and
``powershell`` when those fields are absent), but the reviewer flagged that
relying on the fallback alone made the documented opt-in path fragile and
unverified against the current schema. These tests pin the template to
explicit, unambiguous ``bash``/``powershell`` fields so copying the example
into ``.github/hooks/`` reliably invokes the prototype on both platforms.
"""

import json
import os

import pytest

_EXPERIMENT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_HOOKS_EXAMPLE_PATH = os.path.join(_EXPERIMENT_ROOT, "hooks.json.example")


@pytest.fixture()
def hooks_example():
    with open(_HOOKS_EXAMPLE_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def test_hooks_example_is_valid_json_with_version_1(hooks_example):
    assert hooks_example["version"] == 1


def test_hooks_example_post_tool_use_entry_declares_bash_command(hooks_example):
    entry = hooks_example["hooks"]["postToolUse"][0]
    assert entry.get("bash"), "postToolUse entry must set 'bash' for Unix invocation"
    assert "hook_cli.py" in entry["bash"]


def test_hooks_example_post_tool_use_entry_declares_powershell_command(hooks_example):
    entry = hooks_example["hooks"]["postToolUse"][0]
    assert entry.get(
        "powershell"
    ), "postToolUse entry must set 'powershell' for Windows invocation"
    assert "hook_cli.py" in entry["powershell"]


def test_hooks_example_entry_type_is_command(hooks_example):
    entry = hooks_example["hooks"]["postToolUse"][0]
    assert entry["type"] == "command"
