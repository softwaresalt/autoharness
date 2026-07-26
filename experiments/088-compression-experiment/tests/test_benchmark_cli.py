"""Tests for the benchmark CLI entrypoint (088.006-T).

Verifies the CLI wires build_default_corpus -> run_benchmark -> report
rendering -> file output, using an injectable corpus builder so the test
does not depend on external tools or a live repo checkout.
"""

import json
import os

import pytest

from brainspace import benchmark_cli
from brainspace.benchmark import BenchmarkCase


def _fake_corpus_builder(repo_root, command_runner=None):
    return [
        BenchmarkCase(
            name="fake-win",
            tool_name="bash",
            text="repeated noisy log line\n" * 200 + "exit code: 0",
            task_question="q",
            required_fact="exit code: 0",
        ),
        BenchmarkCase(
            name="fake-decline",
            tool_name="bash",
            text="tiny",
            task_question="n/a",
            expect_decline=True,
        ),
    ]


def test_main_writes_markdown_and_json_reports(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    out_dir = tmp_path / "reports"

    exit_code = benchmark_cli.main(
        ["--repo-root", str(tmp_path), "--out-dir", str(out_dir)]
    )

    assert exit_code == 0
    md_path = out_dir / "benchmark-report.md"
    json_path = out_dir / "benchmark-report.json"
    assert md_path.exists()
    assert json_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["total_count"] == 2
    markdown = md_path.read_text(encoding="utf-8")
    assert "fake-win" in markdown
    assert "fake-decline" in markdown


def test_main_does_not_leave_experiment_flag_enabled_globally(tmp_path, monkeypatch):
    from brainspace import config

    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv(config.ENABLED_ENV_VAR, raising=False)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    out_dir = tmp_path / "reports"

    benchmark_cli.main(["--repo-root", str(tmp_path), "--out-dir", str(out_dir)])

    # The CLI enables the flag only for its own run; it must not leak into
    # the ambient environment for later, unrelated processes/tests.
    assert os.environ.get(config.ENABLED_ENV_VAR) != "1"


def test_ephemeral_store_is_anchored_under_repo_root_not_os_temp(tmp_path, monkeypatch):
    # P-018 re-review finding #3 (round 2): tempfile.TemporaryDirectory()
    # defaults to the OS temp area, violating the containment requirement
    # (config.py: the store must be repo-local, never OS temp) even though
    # the directory is ephemeral. Capture the root actually passed to
    # BrainspaceStore and prove it is a descendant of the given repo root.
    captured = {}
    original_store_cls = benchmark_cli.BrainspaceStore

    class _CapturingStore(original_store_cls):
        def __init__(self, root, *args, **kwargs):
            captured["root"] = root
            super().__init__(root, *args, **kwargs)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark_cli, "BrainspaceStore", _CapturingStore)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    out_dir = tmp_path / "reports"

    benchmark_cli.main(["--repo-root", str(tmp_path), "--out-dir", str(out_dir)])

    assert "root" in captured
    common = os.path.commonpath([captured["root"], str(tmp_path)])
    assert common == str(tmp_path)


def test_out_dir_outside_repo_root_is_rejected(tmp_path, monkeypatch):
    # P-018 round-3 finding #4: --out-dir is used directly for makedirs and
    # report writes with no containment validation. An absolute path or a
    # path escaping via `..` must be rejected -- resolve it against the
    # workspace root and never write anything outside it.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    unrelated_out_dir = tmp_path / "unrelated-out-dir"

    with pytest.raises(ValueError):
        benchmark_cli.main(
            ["--repo-root", str(repo_root), "--out-dir", str(unrelated_out_dir)]
        )

    assert not unrelated_out_dir.exists()


def test_out_dir_relative_traversal_outside_repo_root_is_rejected(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    with pytest.raises(ValueError):
        benchmark_cli.main(
            ["--repo-root", str(repo_root), "--out-dir", "../escaped-reports"]
        )


def test_out_dir_relative_to_repo_root_is_allowed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    exit_code = benchmark_cli.main(
        ["--repo-root", str(repo_root), "--out-dir", "reports"]
    )
    assert exit_code == 0
    assert (repo_root / "reports" / "benchmark-report.md").exists()


def test_repo_root_unrelated_to_process_cwd_is_rejected(tmp_path, monkeypatch):
    # P-018 round-3 follow-up finding: --out-dir was contained only relative
    # to --repo-root, but --repo-root itself was trusted verbatim with no
    # validation against the process's actual working directory --
    # `--repo-root /unrelated/path` would create the cache and reports
    # outside the current working tree, bypassing the containment rule this
    # round is meant to enforce.
    session_dir = tmp_path / "session"
    session_dir.mkdir()
    monkeypatch.chdir(session_dir)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    unrelated_repo_root = tmp_path / "completely-unrelated-project"
    unrelated_repo_root.mkdir()

    exit_code = benchmark_cli.main(["--repo-root", str(unrelated_repo_root)])

    assert exit_code != 0
    assert not (unrelated_repo_root / "reports").exists()
