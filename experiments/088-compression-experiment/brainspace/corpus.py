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
    local tool must not crash the benchmark run.
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
        return (proc.stdout or "") + (proc.stderr or "")
    except Exception as exc:  # pragma: no cover - environment-dependent
        return f"[corpus capture unavailable for {' '.join(args)}: {exc}]"


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
    cases.append(
        BenchmarkCase(
            name="pytest-vv-experiment-suite",
            tool_name="bash",
            text=pytest_output[:_MAX_CAPTURE_CHARS],
            task_question="did the experiment test suite pass, and what is the summary?",
            required_fact=last_nonblank_line(pytest_output[:_MAX_CAPTURE_CHARS]),
        )
    )

    doctor_output = run(["backlogit", "doctor"], repo_root)
    cases.append(
        BenchmarkCase(
            name="backlogit-doctor-findings",
            tool_name="bash",
            text=doctor_output[:_MAX_CAPTURE_CHARS],
            task_question="how many doctor issues were found?",
            required_fact=last_nonblank_line(doctor_output[:_MAX_CAPTURE_CHARS]),
        )
    )

    diff_output = run(
        ["git", "--no-pager", "log", "--stat", "-20"],
        repo_root,
    )
    cases.append(
        BenchmarkCase(
            name="git-log-stat-history",
            tool_name="bash",
            text=diff_output[:_MAX_CAPTURE_CHARS],
            task_question="what is the most recent commit summary?",
            required_fact=_first_nonblank_line(diff_output[:_MAX_CAPTURE_CHARS]),
        )
    )

    mcp_json_output = run(["backlogit", "list", "--json"], repo_root)
    truncated_mcp_json = mcp_json_output[:_MAX_CAPTURE_CHARS]
    cases.append(
        BenchmarkCase(
            name="backlogit-list-json-mcp-shaped",
            tool_name="backlogit_mcp",
            text=truncated_mcp_json,
            task_question="what does the first record in this JSON listing look like?",
            required_fact=_first_nonblank_line(truncated_mcp_json),
        )
    )

    inventory_output = run(["git", "ls-files"], repo_root)
    cases.append(
        BenchmarkCase(
            name="workspace-file-inventory",
            tool_name="bash",
            text=inventory_output[:_MAX_CAPTURE_CHARS],
            task_question="what is the last file listed in the inventory?",
            required_fact=last_nonblank_line(inventory_output[:_MAX_CAPTURE_CHARS]),
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
