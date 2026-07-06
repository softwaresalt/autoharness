"""Thin CLI for autoharness — resolves installation paths for AI coding agents."""

from __future__ import annotations

import json
import os
import platform
import shutil
import sys
from pathlib import Path

from autoharness.verify_workspace import verify_workspace

# The data directory is bundled inside the package at build time.
# In a dev/editable install, fall back to the repo root.
_PACKAGE_DIR = Path(__file__).resolve().parent
_DATA_DIR = _PACKAGE_DIR / "data"

if not _DATA_DIR.exists():
    # Editable / dev install — repo root is two levels up from src/autoharness/
    _DATA_DIR = _PACKAGE_DIR.parent.parent


def _home() -> Path:
    """Return the autoharness home directory containing templates, schemas, etc."""
    return _DATA_DIR


def _version() -> str:
    from autoharness import __version__
    return __version__


USAGE = """\
autoharness — agent harness framework

Usage:
  autoharness home              Print the autoharness installation path
  autoharness version           Print the installed version
  autoharness verify-workspace  Deterministically verify an installed workspace harness
  autoharness gate check        Run deterministic validation gates on modified files
  autoharness telemetry record  Record an execution epoch to the configured sink(s)
  autoharness eval              Headless evaluation (frozen-state runner + reviewer matrix)
  autoharness setup-vscode      Write agent discovery entries to VS Code user settings
  autoharness setup-copilot-cli Copy agents/skills into Copilot CLI (deprecated — use plugin)
  autoharness setup-claude      Copy agents and skills into the Claude Code global config dir
  autoharness setup-codex       Copy skills into the Codex global config dir
  autoharness help              Show this message

Install (Copilot CLI plugin — recommended, no Python needed):
    copilot plugin marketplace add softwaresalt/autoharness
    copilot plugin install autoharness@autoharness

Install (Python CLI — stable releases on PyPI):
  python -m pip install autoharness

Install (Python CLI — unreleased snapshots from GitHub):
  python -m pip install git+https://github.com/softwaresalt/autoharness.git

Update:
  copilot plugin update autoharness          # plugin
  python -m pip install --upgrade autoharness  # Python CLI from PyPI

The AI coding assistant is the runtime. This CLI primarily helps agents
resolve the autoharness home path via `autoharness home`, and also
provides user-facing setup and verification commands.
"""


def _parse_verify_workspace_args(args: list[str]) -> tuple[Path, Path, Path | None, bool]:
    """Parse arguments for the verify-workspace command."""
    workspace_path: Path | None = None
    autoharness_home: Path = _home()
    staging_dir: Path | None = None
    emit_json = False

    index = 0
    while index < len(args):
        arg = args[index]
        if arg in ("--workspace", "-w"):
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --workspace")
            workspace_path = Path(args[index])
        elif arg == "--autoharness-home":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --autoharness-home")
            autoharness_home = Path(args[index])
        elif arg == "--staging-dir":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --staging-dir")
            staging_dir = Path(args[index])
        elif arg == "--json":
            emit_json = True
        else:
            raise ValueError(f"Unknown verify-workspace argument: {arg}")
        index += 1

    if workspace_path is None:
        raise ValueError("verify-workspace requires --workspace <path>")

    return workspace_path, autoharness_home, staging_dir, emit_json


def _report_has_failures(report: dict) -> bool:
    """Return True when the verification report contains failing conditions."""
    if report.get("strict_schema_blockers"):
        return True
    if report.get("blockers"):
        return True
    if report.get("unresolved"):
        return True
    targeted_checks = report.get("targeted_checks", {})
    return any(not check.get("ok", False) for check in targeted_checks.values())


def _verify_workspace_command(args: list[str]) -> None:
    """Run deterministic workspace verification and emit a report."""
    try:
        workspace_path, autoharness_home, staging_dir, emit_json = _parse_verify_workspace_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(2)

    report = verify_workspace(
        workspace_path=workspace_path,
        autoharness_home=autoharness_home,
        staging_dir=staging_dir,
    )

    if emit_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Workspace: {report['workspace_path']}")
        print(f"Staging dir: {report['staging_dir']}")
        print(f"Markdown report: {report['report_paths']['markdown']}")
        print(f"JSON report: {report['report_paths']['json']}")
        print()
        print(f"Strict schema blockers: {len(report['strict_schema_blockers'])}")
        print(f"Blockers: {len(report['blockers'])}")
        warning_count = len(report["warnings"])
        warning_instances = int(report.get("warning_instances", warning_count))
        if warning_instances > warning_count:
            print(f"Warnings: {warning_count} grouped summaries ({warning_instances} findings)")
        else:
            print(f"Warnings: {warning_count}")
        print(f"Migration proposals: {len(report['migration_proposals'])}")
        print(f"Unresolved placeholders: {len(report['unresolved'])}")
        print(f"Rendered artifacts: {len(report['rendered'])}")
        print(f"Skipped artifacts: {len(report['skipped'])}")

    if _report_has_failures(report):
        sys.exit(1)


GATE_USAGE = """\
autoharness gate check — run deterministic validation gates on modified files

Usage:
  autoharness gate check --base <ref> [--task <id>] [--head <ref>]
                         [--workspace <path>] [--json] [--force] [--no-count]

Options:
  --base <ref>        Git ref to diff against (the task branch base). Required.
  --task <id>         Active backlog task ID (interpolated as {task_id}).
  --head <ref>        Git ref for the modified side of the diff. Default: HEAD.
  --workspace, -w     Workspace root containing .autoharness/config.yaml. Default: .
  --json              Emit the correction report as JSON.
  --force             Operator-only bypass of a failing gate. Audited. Never
                      reachable from an agent surface. Cannot be combined with
                      --no-count.
  --no-count          Advisory/manual pre-check mode. Do not increment or reset
                      the repeated-failure counter. Cannot be combined with
                      --force.

Exit codes:
  0  all matched gates passed, or no gates configured, or no files matched.
  1  at least one matched file failed its gate (blocked), unless advisory.
  2  invalid arguments or invalid gate configuration.
"""


def _parse_gate_check_args(args: list[str]) -> dict:
    parsed: dict = {
        "base": None,
        "task": None,
        "head": "HEAD",
        "workspace": Path("."),
        "emit_json": False,
        "force": False,
        "no_count": False,
    }
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--base":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --base")
            parsed["base"] = args[index]
        elif arg == "--task":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --task")
            parsed["task"] = args[index]
        elif arg == "--head":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --head")
            parsed["head"] = args[index]
        elif arg in ("--workspace", "-w"):
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --workspace")
            parsed["workspace"] = Path(args[index])
        elif arg == "--json":
            parsed["emit_json"] = True
        elif arg == "--force":
            parsed["force"] = True
        elif arg == "--no-count":
            parsed["no_count"] = True
        else:
            raise ValueError(f"Unknown gate check argument: {arg}")
        index += 1

    if parsed["base"] is None:
        raise ValueError("gate check requires --base <ref>")
    if parsed["force"] and parsed["no_count"]:
        raise ValueError("--force and --no-count cannot be combined")
    return parsed


def _load_gate_config(workspace: Path):
    """Load and validate the workspace gate configuration (fail-open when absent)."""
    import yaml

    from autoharness.schema_contracts import load_lifecycle_hooks_config

    config_path = workspace / ".autoharness" / "config.yaml"
    config_data: dict = {}
    if config_path.exists():
        loaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            config_data = loaded
    return load_lifecycle_hooks_config(config_data, _home())


def _gate_command(args: list[str]) -> None:
    """Dispatch `autoharness gate <subcommand>`."""
    if not args or args[0] in ("help", "--help", "-h"):
        print(GATE_USAGE)
        return

    subcommand = args[0]
    if subcommand != "check":
        print(f"Unknown gate subcommand: {subcommand}", file=sys.stderr)
        print(GATE_USAGE, file=sys.stderr)
        sys.exit(2)

    if any(flag in ("help", "--help", "-h") for flag in args[1:]):
        print(GATE_USAGE)
        return

    try:
        parsed = _parse_gate_check_args(args[1:])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(GATE_USAGE, file=sys.stderr)
        sys.exit(2)

    from autoharness.gates import gate as gate_mod
    from autoharness.gates.config import GatesConfigError

    try:
        config = _load_gate_config(parsed["workspace"])
    except GatesConfigError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)

    if not config.enabled or not config.validation_gates:
        print("No validation gates configured; nothing to check.")
        return

    report = gate_mod.check(
        config,
        parsed["base"],
        parsed["head"],
        task_id=parsed["task"],
        cwd=parsed["workspace"],
    )

    from autoharness.gates.feedback import build_correction_report, enforce

    outcome = enforce(
        report,
        config.policy,
        task_id=parsed["task"],
        workspace=parsed["workspace"],
        force=parsed["force"],
        count_failures=not parsed["no_count"],
    )
    print(build_correction_report(report, outcome, emit_json=parsed["emit_json"]))

    if outcome.exit_code != 0:
        sys.exit(outcome.exit_code)


TELEMETRY_USAGE = """\
autoharness telemetry record — record an execution epoch to the configured sink(s)

Usage:
  autoharness telemetry record [--from-json <path>] [--workspace <path>] [--json]

Options:
  --from-json <path>  Read the epoch payload (a JSON object) from a file.
                      When omitted, the payload is read from stdin.
  --workspace, -w     Workspace root containing .autoharness/config.yaml. Default: .
  --json              Emit the dispatch summary as JSON.

The epoch payload is the serialized shape produced by the harness runtime at
task close (route/economics/operations/outcome + task_id). See
docs/telemetry-reference.md for the emission contract.

Telemetry is fail-open and observational: an absent or `mode: none` telemetry
block is a no-op (exit 0), and a failing sink is reported without blocking.

Exit codes:
  0  epoch recorded, or telemetry disabled (no-op), or sink failed (fail-open).
  2  invalid arguments or an invalid/malformed epoch payload.
"""


def _parse_telemetry_record_args(args: list[str]) -> dict:
    parsed: dict = {"from_json": None, "workspace": Path("."), "emit_json": False}
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--from-json":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --from-json")
            parsed["from_json"] = Path(args[index])
        elif arg in ("--workspace", "-w"):
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --workspace")
            parsed["workspace"] = Path(args[index])
        elif arg == "--json":
            parsed["emit_json"] = True
        else:
            raise ValueError(f"Unknown telemetry record argument: {arg}")
        index += 1
    return parsed


def _telemetry_command(args: list[str]) -> None:
    """Dispatch `autoharness telemetry <subcommand>`."""
    if not args or args[0] in ("help", "--help", "-h"):
        print(TELEMETRY_USAGE)
        return

    subcommand = args[0]
    if subcommand != "record":
        print(f"Unknown telemetry subcommand: {subcommand}", file=sys.stderr)
        print(TELEMETRY_USAGE, file=sys.stderr)
        sys.exit(2)

    if any(flag in ("help", "--help", "-h") for flag in args[1:]):
        print(TELEMETRY_USAGE)
        return

    try:
        parsed = _parse_telemetry_record_args(args[1:])
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(TELEMETRY_USAGE, file=sys.stderr)
        sys.exit(2)

    from autoharness.telemetry.epoch import EpochError, ExecutionEpoch
    from autoharness.telemetry.record import (
        RecordSummary,
        load_workspace_telemetry_config,
        record_epoch,
    )

    # Load telemetry config FIRST. It is fail-open and never raises: an absent or
    # `mode: none` block, or ANY config-parse failure, yields a disabled config.
    config = load_workspace_telemetry_config(parsed["workspace"])

    # When telemetry is disabled the command is a no-op SUCCESS (exit 0) — the
    # payload is never read or validated.
    if not config.enabled:
        if parsed["emit_json"]:
            print(json.dumps(RecordSummary(enabled=False).to_dict(), indent=2, ensure_ascii=False))
        else:
            print("Telemetry disabled (mode: none or absent); epoch not recorded.")
        return

    # Read the epoch payload from a file or stdin.
    if parsed["from_json"] is not None:
        try:
            raw = parsed["from_json"].read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"Could not read epoch payload: {exc}", file=sys.stderr)
            sys.exit(2)
    else:
        try:
            raw = sys.stdin.read()
        except UnicodeDecodeError as exc:
            print(f"Could not read epoch payload from stdin: {exc}", file=sys.stderr)
            sys.exit(2)

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Invalid epoch payload — not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)

    # All payload shape/coercion failures are normalized to EpochError → exit 2.
    try:
        epoch = ExecutionEpoch.from_mapping(payload)
    except EpochError as exc:
        print(f"Invalid epoch payload: {exc}", file=sys.stderr)
        sys.exit(2)

    summary = record_epoch(epoch, config)

    if parsed["emit_json"]:
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
    else:
        sinks = []
        if summary.sqlite_written:
            sinks.append("sqlite")
        if summary.jsonl_written:
            sinks.append("jsonl")
        print(f"Recorded epoch {epoch.epoch_id} to: {', '.join(sinks) or 'no sink'}")
        for err in summary.errors:
            print(f"  warning (fail-open): {err}", file=sys.stderr)


EVAL_USAGE = """\
autoharness eval — headless evaluation (frozen-state runner + reviewer matrix)

Usage:
  autoharness eval run --matrix <path> [--base <ref>] [--head <ref>]
                       [--review] [--workspace <path>] [--json]
  autoharness eval review --base <ref> [--head <ref>] [--workspace <path>] [--json]

Subcommands:
  run     Execute a frozen-state baseline across the matrix's model configs,
          persist one comparable ExecutionEpoch per config via the configured
          telemetry sink(s), and print a comparative baseline summary.
  review  Run the deterministic rule-based reviewer matrix over a git diff and
          print per-dimension scores with line-number-cited penalties.

Options:
  --matrix <path>     Eval model-config matrix (.yaml/.yml/.json). Required for run.
  --base <ref>        Git ref for the frozen-state base of the diff. Required for
                      review; overrides the matrix frozen_state.base for run.
  --head <ref>        Git ref for the head side of the diff. Default: HEAD.
  --review            (run) Also grade the frozen diff and fold quality scores
                      into the comparative summary.
  --workspace, -w     Workspace root containing .autoharness/config.yaml. Default: .
  --json              Emit the result as JSON.

The eval runner performs NO live model or network calls: model economics are
replayed from each config's recorded `baseline` block, and the reviewer is a
deterministic rule-based grader. See docs/telemetry-reference.md.

Exit codes:
  0  evaluation completed (summary/review emitted).
  2  invalid arguments or an invalid/malformed matrix.
"""


def _parse_eval_review_args(args: list[str]) -> dict:
    parsed: dict = {
        "base": None,
        "head": "HEAD",
        "workspace": Path("."),
        "emit_json": False,
    }
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--base":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --base")
            parsed["base"] = args[index]
        elif arg == "--head":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --head")
            parsed["head"] = args[index]
        elif arg in ("--workspace", "-w"):
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --workspace")
            parsed["workspace"] = Path(args[index])
        elif arg == "--json":
            parsed["emit_json"] = True
        else:
            raise ValueError(f"Unknown eval review argument: {arg}")
        index += 1
    if parsed["base"] is None:
        raise ValueError("Missing required argument: --base")
    return parsed


def _print_review_result(result) -> None:
    print(f"Reviewer matrix (ruleset {result.ruleset_version}) — overall {result.overall:.2f}/10")
    if result.files:
        print(f"Files reviewed: {len(result.files)}")
    for dimension, score in result.dimensions.items():
        print(f"  {dimension:<16} {score.score:>5.2f}/{score.max_score:.0f}")
        for penalty in score.penalties:
            print(
                f"    - {penalty.path}:{penalty.line} "
                f"[{penalty.rule} -{penalty.points}] {penalty.message}"
            )


def _eval_review_command(args: list[str]) -> None:
    """Run the deterministic reviewer matrix over a git diff (055.002-T)."""
    try:
        parsed = _parse_eval_review_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(EVAL_USAGE, file=sys.stderr)
        sys.exit(2)

    from autoharness.eval.reviewer import review_git_diff

    result = review_git_diff(
        parsed["base"], parsed["head"], cwd=parsed["workspace"]
    )

    if parsed["emit_json"]:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_review_result(result)


def _parse_eval_run_args(args: list[str]) -> dict:
    parsed: dict = {
        "matrix": None,
        "base": None,
        "head": None,
        "review": False,
        "workspace": Path("."),
        "emit_json": False,
    }
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--matrix":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --matrix")
            parsed["matrix"] = Path(args[index])
        elif arg == "--base":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --base")
            parsed["base"] = args[index]
        elif arg == "--head":
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --head")
            parsed["head"] = args[index]
        elif arg == "--review":
            parsed["review"] = True
        elif arg in ("--workspace", "-w"):
            index += 1
            if index >= len(args):
                raise ValueError("Missing value for --workspace")
            parsed["workspace"] = Path(args[index])
        elif arg == "--json":
            parsed["emit_json"] = True
        else:
            raise ValueError(f"Unknown eval run argument: {arg}")
        index += 1
    if parsed["matrix"] is None:
        raise ValueError("Missing required argument: --matrix")
    return parsed


def _print_baseline_summary(summary) -> None:
    frozen = summary.frozen_sha or summary.frozen_head or "?"
    print(f"Eval baseline summary — frozen {summary.frozen_base or '?'}...{frozen}")
    print(f"Configs: {len(summary.configs)}  "
          f"total tokens: {summary.total_tokens}  "
          f"total COGS: ${summary.total_cogs_usd:.4f}")
    for config in summary.configs:
        quality = (
            f"  quality {config.quality_overall:.2f}/10"
            if config.quality_overall is not None
            else ""
        )
        flag = "  [BLOCKED]" if config.blocked else ""
        print(
            f"  {config.config_name:<18} "
            f"tokens={config.total_tokens:<8} "
            f"cogs=${config.cogs_usd:<7.4f} "
            f"dur={config.duration_seconds:.1f}s{quality}{flag}"
        )
    print("Comparative:")
    print(f"  cheapest={summary.cheapest_config}  costliest={summary.costliest_config}")
    print(f"  fastest={summary.fastest_config}  lowest-tokens={summary.lowest_token_config}")
    if summary.highest_quality_config is not None:
        print(f"  highest-quality={summary.highest_quality_config}")
    if summary.blocked_configs:
        print(f"  blocked={', '.join(summary.blocked_configs)}")


def _eval_run_command(args: list[str]) -> None:
    """Run a frozen-state baseline across the matrix (055.005-T + 055.006-T)."""
    try:
        parsed = _parse_eval_run_args(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        print(EVAL_USAGE, file=sys.stderr)
        sys.exit(2)

    from autoharness.eval.matrix import EvalMatrixError, load_matrix_file
    from autoharness.eval.reviewer import review_git_diff
    from autoharness.eval.runner import run_matrix
    from autoharness.eval.summary import summarize_baseline
    from autoharness.telemetry.record import load_workspace_telemetry_config

    try:
        matrix = load_matrix_file(parsed["matrix"])
    except EvalMatrixError as exc:
        print(f"Invalid eval matrix: {exc}", file=sys.stderr)
        sys.exit(2)

    telemetry_config = load_workspace_telemetry_config(parsed["workspace"])

    report = run_matrix(
        matrix,
        telemetry_config,
        base_override=parsed["base"],
        head_override=parsed["head"],
        cwd=parsed["workspace"],
    )

    reviews = None
    if parsed["review"]:
        frozen = report.frozen_state
        if frozen is None:
            print(
                "warning: --review requested but no frozen base is available "
                "(matrix frozen_state.base or --base); skipping reviewer matrix.",
                file=sys.stderr,
            )
        else:
            result = review_git_diff(
                frozen.base, frozen.head, cwd=parsed["workspace"]
            )
            reviews = {config.name: result for config in matrix.configs}

    summary = summarize_baseline(report, reviews=reviews)

    if parsed["emit_json"]:
        print(json.dumps(summary.to_dict(), indent=2, ensure_ascii=False))
    else:
        _print_baseline_summary(summary)


def _eval_wants_help(rest: list[str]) -> bool:
    if rest and rest[0] == "help":
        return True
    return any(flag in ("--help", "-h") for flag in rest)


def _eval_command(args: list[str]) -> None:
    """Dispatch `autoharness eval <subcommand>`."""
    if not args or args[0] in ("help", "--help", "-h"):
        print(EVAL_USAGE)
        return

    subcommand = args[0]
    rest = args[1:]

    if subcommand == "review":
        if _eval_wants_help(rest):
            print(EVAL_USAGE)
            return
        _eval_review_command(rest)
    elif subcommand == "run":
        if _eval_wants_help(rest):
            print(EVAL_USAGE)
            return
        _eval_run_command(rest)
    else:
        print(f"Unknown eval subcommand: {subcommand}", file=sys.stderr)
        print(EVAL_USAGE, file=sys.stderr)
        sys.exit(2)


def _vscode_user_settings_path() -> Path | None:
    """Return the platform-appropriate VS Code user settings path (no tilde)."""
    system = platform.system()
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None
        return Path(appdata) / "Code" / "User" / "settings.json"
    elif system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "Code" / "User" / "settings.json"


def _strip_jsonc(text: str) -> str:
    """Strip JSONC comments and trailing commas without touching quoted strings.

    Uses a character-level state machine that tracks string boundaries so that
    comment-like sequences inside string values are never removed.
    """
    # Phase 1: strip comments
    result: list[str] = []
    i = 0
    in_string = False
    escape = False
    in_line_comment = False
    in_block_comment = False

    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""

        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
                result.append(ch)
            i += 1
            continue

        if in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        if in_string:
            result.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            result.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        result.append(ch)
        i += 1

    if in_string:
        raise ValueError("Invalid JSONC: unterminated string literal in VS Code settings.")
    if in_block_comment:
        raise ValueError("Invalid JSONC: unterminated block comment in VS Code settings.")

    # Phase 2: strip trailing commas before } or ]
    stripped = "".join(result)
    cleaned: list[str] = []
    in_string = False
    escape = False
    i = 0

    while i < len(stripped):
        ch = stripped[i]

        if in_string:
            cleaned.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            i += 1
            continue

        if ch == '"':
            in_string = True
            cleaned.append(ch)
            i += 1
            continue

        if ch == ",":
            j = i + 1
            while j < len(stripped) and stripped[j] in " \t\r\n":
                j += 1
            if j < len(stripped) and stripped[j] in "}]":
                i += 1
                continue

        cleaned.append(ch)
        i += 1

    if in_string:
        raise ValueError("Invalid JSONC: unterminated string literal in VS Code settings.")

    return "".join(cleaned)


def _setup_vscode() -> None:
    """Write autoharness agent discovery entries into VS Code user settings."""
    home = _home()
    settings_path = _vscode_user_settings_path()

    if settings_path is None:
        print("Error: could not determine VS Code user settings path for this OS.", file=sys.stderr)
        sys.exit(1)

    # Build path keys using fully-resolved absolute paths — no tilde, no variables.
    # Use POSIX (forward-slash) paths so the same key works on all platforms and
    # avoids duplicate entries if the user already has forward-slash keys.
    agents_path  = home / ".github" / "agents"
    skills_path  = home / ".github" / "skills"
    prompts_path = home / ".github" / "prompts"

    entries = [
        ("chat.agentFilesLocations",  agents_path.as_posix()),
        ("chat.agentSkillsLocations", skills_path.as_posix()),
        ("chat.promptFilesLocations", prompts_path.as_posix()),
    ]

    # Read existing settings, tolerating JSONC comments.
    if settings_path.exists():
        raw = settings_path.read_text(encoding="utf-8")
        try:
            settings: dict = json.loads(raw)
        except json.JSONDecodeError:
            settings = json.loads(_strip_jsonc(raw))
    else:
        settings = {}
        settings_path.parent.mkdir(parents=True, exist_ok=True)

    added: list[str] = []
    skipped: list[str] = []

    for setting_key, entry_key in entries:
        existing = settings.get(setting_key)
        if existing is None:
            settings[setting_key] = {}
        elif not isinstance(existing, dict):
            print(
                f"Error: '{setting_key}' in {settings_path} is not an object "
                f"(found {type(existing).__name__}). "
                f"Fix or remove that key manually, then re-run this command.",
                file=sys.stderr,
            )
            sys.exit(1)
        bucket: dict = settings[setting_key]
        if entry_key in bucket:
            skipped.append(f"  {setting_key}  (already present)")
        else:
            bucket[entry_key] = True
            added.append(f"  {setting_key}")

    settings_path.write_text(
        json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"VS Code user settings: {settings_path}")
    if added:
        print("Added:")
        for line in added:
            print(line)
    if skipped:
        print("Already present (skipped):")
        for line in skipped:
            print(line)
    if not added:
        print("No changes needed — all entries were already present.")
    else:
        print("\nReload your VS Code window (Ctrl+Shift+P → 'Reload Window') for the")
        print("Auto-MergeInstall agent to appear in the agents dropdown.")


def _copilot_cli_config_dir() -> Path:
    """Return the Copilot CLI global config directory.

    Mirrors the resolution order in copilot.exe:
      1. COPILOT_HOME environment variable
      2. ~/.copilot/ (default)
    """
    env = os.environ.get("COPILOT_HOME")
    if env:
        return Path(env)
    return Path.home() / ".copilot"


def _setup_copilot_cli() -> None:
    """Copy autoharness agents and skills into the Copilot CLI global config dir.

    Copilot CLI discovers agents from {config_dir}/agents/ and skills from
    {config_dir}/skills/ at session start.  This command copies the autoharness
    .github/agents/ and .github/skills/ trees into those directories so the
    Auto-MergeInstall and Auto-Tune agents are available in every session.

    Re-run this command after upgrading autoharness to pick up new agents or
    updated skill files.

    DEPRECATED: Use the marketplace install flow instead.
    """
    print("NOTE: setup-copilot-cli is deprecated.")
    print("      Prefer: copilot plugin marketplace add softwaresalt/autoharness")
    print("              copilot plugin install autoharness@autoharness")
    print("      The plugin provides the same agents and skills with built-in")
    print("      versioning and no Python dependency.")
    print()

    home = _home()
    config_dir = _copilot_cli_config_dir()
    src_agents = home / ".github" / "agents"
    src_skills = home / ".github" / "skills"
    dst_agents = config_dir / "agents"
    dst_skills = config_dir / "skills"

    print(f"Copilot CLI config dir: {config_dir}")
    print()

    a, u = _copy_tree(src_agents, dst_agents, "*.md")
    _report_copy("Agents", a, u)

    a, u = _copy_tree(src_skills, dst_skills, "SKILL.md")
    _report_copy("Skills", a, u)

    print("Done. Start a new Copilot CLI session to pick up the changes.")
    print("Run this command again after upgrading autoharness.")



def _copy_tree(src_dir: Path, dst_dir: Path, glob: str) -> tuple[list[str], list[str]]:
    """Copy files matching glob from src_dir into dst_dir, preserving structure.

    Returns (added, updated) lists of relative paths.
    """
    added: list[str] = []
    updated: list[str] = []
    for src_file in sorted(src_dir.rglob(glob)):
        rel = src_file.relative_to(src_dir)
        dst_file = dst_dir / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        existed = dst_file.exists()
        shutil.copy2(src_file, dst_file)
        (updated if existed else added).append(f"  {rel}")
    return added, updated


def _report_copy(label: str, added: list[str], updated: list[str]) -> None:
    if added:
        print(f"{label} added:")
        print("\n".join(added))
    if updated:
        print(f"{label} updated:")
        print("\n".join(updated))
    if not added and not updated:
        print(f"{label}: nothing to copy (source directory empty or missing)")
    print()


def _claude_config_dir() -> Path:
    """Return the Claude Code global config directory.

    Resolution order (mirrors Claude Code):
      1. CLAUDE_CONFIG_DIR environment variable
      2. ~/.claude/ (default)
    """
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        return Path(env)
    return Path.home() / ".claude"


def _setup_claude() -> None:
    """Copy autoharness agents and skills into the Claude Code global config dir.

    Claude Code discovers agents from {config_dir}/agents/ and skills from
    {config_dir}/skills/ at session start.
    """
    home = _home()
    config_dir = _claude_config_dir()
    print(f"Claude Code config dir: {config_dir}")
    print()

    a, u = _copy_tree(home / ".github" / "agents", config_dir / "agents", "*.md")
    _report_copy("Agents", a, u)

    a, u = _copy_tree(home / ".github" / "skills", config_dir / "skills", "SKILL.md")
    _report_copy("Skills", a, u)

    print("Done. Restart Claude Code to pick up the changes.")
    print("Run this command again after upgrading autoharness.")


def _codex_config_dir() -> Path:
    """Return the Codex global config directory.

    Resolution order (mirrors Codex):
      1. CODEX_HOME environment variable
      2. ~/.codex/ (default)
    """
    env = os.environ.get("CODEX_HOME")
    if env:
        return Path(env)
    return Path.home() / ".codex"


def _setup_codex() -> None:
    """Copy autoharness skills into the Codex global skills directory.

    Codex discovers skills from {config_dir}/skills/<skill-name>/SKILL.md.
    Codex does not have a separate agents directory — skills serve as the
    agent entry points. The skill directory name becomes the skill name
    (e.g. install-harness, tune-harness).

    Note: Codex SKILL.md files use the same frontmatter format as autoharness.
    If the frontmatter lacks a top-level 'name:' field, Codex infers the name
    from the directory.
    """
    home = _home()
    config_dir = _codex_config_dir()
    print(f"Codex config dir: {config_dir}")
    print()

    a, u = _copy_tree(home / ".github" / "skills", config_dir / "skills", "SKILL.md")
    _report_copy("Skills", a, u)

    print("Done. Restart Codex to pick up the changes.")
    print("Run this command again after upgrading autoharness.")


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]

    if not args or args[0] in ("help", "--help", "-h"):
        print(USAGE)
        return

    command = args[0]

    if command == "home":
        print(_home())
    elif command == "version":
        print(_version())
    elif command == "verify-workspace":
        _verify_workspace_command(args[1:])
    elif command == "gate":
        _gate_command(args[1:])
    elif command == "telemetry":
        _telemetry_command(args[1:])
    elif command == "eval":
        _eval_command(args[1:])
    elif command == "setup-vscode":
        _setup_vscode()
    elif command == "setup-copilot-cli":
        _setup_copilot_cli()
    elif command == "setup-claude":
        _setup_claude()
    elif command == "setup-codex":
        _setup_codex()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print(USAGE, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
