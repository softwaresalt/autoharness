"""Default benchmark corpus over REAL autoharness commands (088.006-T).

Captures live, read-only command output for the compression-positive
candidates listed in the spike (§7.3): `pytest -vv`, `backlogit doctor`,
a large `git --no-pager diff`/history command, a verbose MCP-shaped JSON
listing, and a workspace file inventory. All captured commands are
read-only — none mutate the workspace, the git index, or backlogit state.

Where a live surface is not available in the current benchmark environment
(e.g. Engram/graphtor MCP search indices, which are not running inside
this sandboxed benchmark run), a clearly-labeled synthetic representative
sample is used instead — see ``BenchmarkCase.provenance``. This keeps the
report honest: no positive-savings claim is presented as a live
measurement when it is a representative stand-in.

Decline/negative-control fixtures are deliberately synthetic (never real
secrets, never a real operator-approval prompt) so the corpus never risks
leaking sensitive material.
"""

import subprocess
from typing import Callable, List, Optional

from brainspace.benchmark import BenchmarkCase

#: Truncation cap for very large captured command output, to keep benchmark
#: runtime bounded. Still large enough to be a realistic stress case.
_MAX_CAPTURE_CHARS = 60_000

#: Prefix marking a labeled capture-failure placeholder (tool not installed,
#: non-zero exit, or timeout) so downstream corpus building can flag the
#: resulting case as ``capture_failed`` rather than a real sample.
_CAPTURE_FAILED_MARKER = "[corpus capture failed for "


def last_nonblank_line(text: str) -> str:
    """Return the final non-blank line of ``text`` (or ``""``)."""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _first_nonblank_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def _default_command_runner(args: List[str], cwd: str) -> str:
    """Run a read-only command and capture combined stdout+stderr text.

    On any failure (tool not installed, non-zero exit, timeout), returns a
    clearly-labeled placeholder string rather than raising — a missing
    local tool must not crash the benchmark run. A non-zero exit is a
    CAPTURE FAILURE, not a real command-output sample: the returned text is
    prefixed with ``_CAPTURE_FAILED_MARKER`` so ``build_default_corpus`` can
    mark the resulting case ``capture_failed=True`` and the benchmark
    runner can guarantee it is never reported as a SAFE WIN (finding #15).
    """
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="surrogatepass",
        )
        combined = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            return (
                f"{_CAPTURE_FAILED_MARKER}{' '.join(args)} exited with code "
                f"{proc.returncode}]\n{combined}"
            )
        return combined
    except Exception as exc:  # pragma: no cover - environment-dependent
        return f"{_CAPTURE_FAILED_MARKER}{' '.join(args)}: {exc}]"


def _is_capture_failure(text: str) -> bool:
    """True when ``text`` is a labeled capture-failure placeholder."""
    return text.startswith(_CAPTURE_FAILED_MARKER)


def _truncate_preserving_tail(
    text: str, max_chars: int = _MAX_CAPTURE_CHARS, tail_chars: int = 2000
) -> str:
    """Truncate ``text`` to at most ``max_chars`` while preserving its tail.

    Captured command output frequently carries its most important evidence
    at the END of the output -- a pass/fail summary line, a final doctor
    finding count, the last file in an inventory listing. Prefix-only
    truncation silently discards that evidence while the resulting case is
    still treated as a complete live sample: a 60+ KB ``pytest -vv``
    capture could lose its own final summary line entirely, and any
    ``required_fact`` derived from the truncated text would then come from
    an arbitrary mid-output line instead of the real summary, letting the
    task-answerability criterion pass without ever proving the actual fact
    survived (P-018 round-8 finding). Keep a head prefix plus a tail suffix
    (where such summaries live) instead of a prefix-only cut.
    """
    if len(text) <= max_chars:
        return text
    tail_chars = min(tail_chars, max_chars // 2)
    head_chars = max_chars - tail_chars
    head = text[:head_chars]
    tail = text[-tail_chars:] if tail_chars else ""
    omitted = len(text) - head_chars - tail_chars
    marker = f"\n... [corpus capture truncated; {omitted} chars omitted] ...\n"
    return f"{head}{marker}{tail}"


def build_default_corpus(
    repo_root: str,
    command_runner: Optional[Callable[[List[str], str], str]] = None,
) -> List[BenchmarkCase]:
    """Build the default benchmark corpus.

    ``command_runner`` is injectable so tests do not depend on external
    tools (git, backlogit, pytest) being installed/available.
    """
    run = command_runner or _default_command_runner
    cases: List[BenchmarkCase] = []

    # --- Compression-positive: live-captured real autoharness commands ---

    pytest_output = run(
        ["python", "-m", "pytest", "experiments/088-compression-experiment/tests", "-vv"],
        repo_root,
    )
    truncated_pytest = _truncate_preserving_tail(pytest_output)
    cases.append(
        BenchmarkCase(
            name="pytest-vv-experiment-suite",
            tool_name="bash",
            text=truncated_pytest,
            task_question="did the experiment test suite pass, and what is the summary?",
            required_fact=last_nonblank_line(pytest_output),
            capture_failed=_is_capture_failure(pytest_output),
        )
    )

    doctor_output = run(["backlogit", "doctor"], repo_root)
    truncated_doctor = _truncate_preserving_tail(doctor_output)
    cases.append(
        BenchmarkCase(
            name="backlogit-doctor-findings",
            tool_name="bash",
            text=truncated_doctor,
            task_question="how many doctor issues were found?",
            required_fact=last_nonblank_line(doctor_output),
            capture_failed=_is_capture_failure(doctor_output),
        )
    )

    diff_output = run(
        ["git", "--no-pager", "log", "--stat", "-20"],
        repo_root,
    )
    truncated_diff = _truncate_preserving_tail(diff_output)
    cases.append(
        BenchmarkCase(
            name="git-log-stat-history",
            tool_name="bash",
            text=truncated_diff,
            task_question="what is the most recent commit summary?",
            required_fact=_first_nonblank_line(diff_output),
            capture_failed=_is_capture_failure(diff_output),
        )
    )

    mcp_json_output = run(["backlogit", "list", "--json"], repo_root)
    truncated_mcp_json = _truncate_preserving_tail(mcp_json_output)
    cases.append(
        BenchmarkCase(
            name="backlogit-list-json-mcp-shaped",
            tool_name="backlogit_mcp",
            text=truncated_mcp_json,
            task_question="what does the first record in this JSON listing look like?",
            required_fact=_first_nonblank_line(mcp_json_output),
            capture_failed=_is_capture_failure(mcp_json_output),
        )
    )

    inventory_output = run(["git", "ls-files"], repo_root)
    truncated_inventory = _truncate_preserving_tail(inventory_output)
    cases.append(
        BenchmarkCase(
            name="workspace-file-inventory",
            tool_name="bash",
            text=truncated_inventory,
            task_question="what is the last file listed in the inventory?",
            required_fact=last_nonblank_line(inventory_output),
            capture_failed=_is_capture_failure(inventory_output),
        )
    )

    # Engram/graphtor large search results: not available as a live surface
    # inside this sandboxed benchmark run (no MCP server session). Use a
    # clearly-labeled synthetic representative sample shaped like a large,
    # repetitive symbol/search-hit listing.
    representative_search_hits = "\n".join(
        f'{{"file": "src/autoharness/module_{i}.py", "symbol": "helper_{i}", '
        f'"line": {i * 7}, "snippet": "def helper_{i}(...): ..."}}'
        for i in range(300)
    )
    representative_search_hits += '\n{"file": "src/autoharness/cli.py", "symbol": "main", "line": 1, "snippet": "def main(...): ..."}'
    cases.append(
        BenchmarkCase(
            name="graphtor-search-results-representative",
            tool_name="graphtor_mcp",
            text=representative_search_hits,
            task_question="which file/symbol is the final search hit?",
            required_fact='"symbol": "main"',
            provenance=(
                "synthetic-representative: Engram/graphtor MCP search "
                "surface not running in this benchmark environment"
            ),
        )
    )

    # --- Decline / negative controls (deliberately synthetic) ---

    cases.append(
        BenchmarkCase(
            name="tiny-output-decline",
            tool_name="bash",
            text="ok",
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="tiny_output",
        )
    )

    cases.append(
        BenchmarkCase(
            name="unwritable-store-passthrough",
            tool_name="bash",
            text="repeated noisy log line\n" * 200,
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="unwritable_store",
            simulate_unwritable_store=True,
        )
    )

    cases.append(
        BenchmarkCase(
            name="secret-bearing-output-decline",
            tool_name="bash",
            text="AKIAABCDEFGHIJKLMNOP\n" + ("padding line\n" * 50),
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="secret_bearing",
        )
    )

    cases.append(
        BenchmarkCase(
            name="gate-readiness-verdict-decline",
            tool_name="bash",
            text="P-014 GATE PASSED: local readiness verified at HEAD=abc123\n"
            + ("padding\n" * 60),
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="gate_readiness_verdict",
        )
    )

    cases.append(
        BenchmarkCase(
            name="failure-bearing-gh-run-view-representative",
            tool_name="bash",
            text="gh run view --log-failed\ncommand output\nexit code: 1\n"
            "stderr: step 'Run tests' failed\n" + ("padding\n" * 60),
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="failure_bearing_success",
            provenance=(
                "synthetic-representative: emulates a failed `gh run view "
                "--log-failed` without depending on a live failed CI run"
            ),
        )
    )

    cases.append(
        BenchmarkCase(
            name="active-stack-trace-decline",
            tool_name="bash",
            text="Traceback (most recent call last):\n"
            + ("  File \"x.py\", line 1, in <module>\n" * 60),
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="active_stack_trace",
        )
    )

    cases.append(
        BenchmarkCase(
            name="operator-approval-text-decline",
            tool_name="bash",
            text="Do you approve this destructive operation? (y/n)\n"
            + ("padding\n" * 60),
            task_question="n/a",
            expect_decline=True,
            decline_reason_label="operator_approval_text",
        )
    )

    return cases
