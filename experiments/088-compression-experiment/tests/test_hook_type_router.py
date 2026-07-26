"""Tests for the type router (088.002-T review finding #14).

The compressor must route by content type (json / log / diff / prose) and
preserve required inline evidence (e.g. PR/issue reference numbers embedded
in commit messages, or diff/hunk headers) no matter where in the text it
appears -- not only at the head or tail. This directly addresses the
``git-log-stat-history`` benchmark evidence-loss finding: a pure
head/tail-only strategy drops PR references buried in the omitted middle
of a 20-commit ``git log --stat`` capture.
"""

import json

from brainspace.hook import _compress_view, _detect_content_type


def _fake_git_log_stat(n_commits: int, pr_ref_at_commit: int) -> str:
    """Build a synthetic ``git --no-pager log --stat`` capture.

    One commit in the middle references a PR (``pr_ref_at_commit``) so a
    naive head/tail-5 compressor drops it while an evidence-preserving
    router must keep it.
    """
    blocks = []
    for i in range(n_commits):
        message = f"Routine commit {i}"
        if i == pr_ref_at_commit:
            message = f"Merge pull request #{1000 + i} from feature/x"
        blocks.append(
            "\n".join(
                [
                    f"commit {'a' * 33}{i:07d}",
                    "Author: Someone <someone@example.com>",
                    "Date:   Sat Jul 25 10:00:00 2026 +0000",
                    "",
                    f"    {message}",
                    "",
                    f" experiments/088-compression-experiment/brainspace/hook.py | {i + 1} +-",
                    f" 1 file changed, {i + 1} insertions(+), 0 deletions(-)",
                    "",
                ]
            )
        )
    return "\n".join(blocks)


def _fake_unified_diff(n_context_lines: int, pr_ref_at_line: int) -> str:
    lines = [
        "diff --git a/foo.py b/foo.py",
        "--- a/foo.py",
        "+++ b/foo.py",
        f"@@ -1,{n_context_lines} +1,{n_context_lines} @@",
    ]
    for i in range(n_context_lines):
        if i == pr_ref_at_line:
            lines.append(f"+# addresses review comment for PR #{2000 + i}")
        else:
            lines.append(f"+padding context line {i}")
    return "\n".join(lines)


def test_detect_content_type_json():
    text = json.dumps({"records": [{"id": i} for i in range(50)]}, indent=2)
    assert _detect_content_type(text) == "json"


def test_detect_content_type_diff():
    assert _detect_content_type(_fake_unified_diff(30, 15)) == "diff"


def test_detect_content_type_log():
    assert _detect_content_type(_fake_git_log_stat(20, 10)) == "log"


def test_detect_content_type_prose_fallback():
    text = "repeated noisy log line\n" * 200
    assert _detect_content_type(text) == "prose"


def test_git_log_stat_preserves_middle_pr_reference():
    # 20 commits, the PR reference is on commit #10 -- well outside a
    # naive head-5/tail-5 window.
    text = _fake_git_log_stat(20, pr_ref_at_commit=10)
    compressed = _compress_view(text)
    assert len(compressed) < len(text)
    assert "#1010" in compressed


def test_unified_diff_preserves_middle_pr_reference():
    text = _fake_unified_diff(200, pr_ref_at_line=100)
    compressed = _compress_view(text)
    assert len(compressed) < len(text)
    assert "#2100" in compressed
    # Header/hunk structure evidence is preserved too.
    assert "diff --git a/foo.py b/foo.py" in compressed


def test_json_preserves_middle_issue_reference():
    records = [{"id": i, "note": "routine"} for i in range(200)]
    records[100]["note"] = "see #3456 for context"
    text = json.dumps({"records": records}, indent=2)
    compressed = _compress_view(text)
    assert len(compressed) < len(text)
    assert "#3456" in compressed


def test_prose_fallback_still_collapses_middle_unconditionally():
    # Prose has no evidence markers, so the original simple head/tail
    # strategy still applies unchanged.
    text = "repeated noisy log line\n" * 200
    compressed = _compress_view(text)
    assert len(compressed) < len(text)
    assert "lines omitted by 088-F compression experiment" in compressed


def test_short_text_below_edge_threshold_is_unchanged():
    text = "line one\nline two\nline three"
    assert _compress_view(text) == text
