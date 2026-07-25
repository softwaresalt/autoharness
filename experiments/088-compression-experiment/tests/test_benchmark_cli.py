"""Tests for the benchmark CLI entrypoint (088.006-T).

Verifies the CLI wires build_default_corpus -> run_benchmark -> report
rendering -> file output, using an injectable corpus builder so the test
does not depend on external tools or a live repo checkout.
"""

import json
import os

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

    monkeypatch.delenv(config.ENABLED_ENV_VAR, raising=False)
    monkeypatch.setattr(benchmark_cli, "build_default_corpus", _fake_corpus_builder)
    out_dir = tmp_path / "reports"

    benchmark_cli.main(["--repo-root", str(tmp_path), "--out-dir", str(out_dir)])

    # The CLI enables the flag only for its own run; it must not leak into
    # the ambient environment for later, unrelated processes/tests.
    assert os.environ.get(config.ENABLED_ENV_VAR) != "1"
