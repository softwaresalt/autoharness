"""Tests for the benchmark corpus runner + report (088.006-T).

Exercises the hook + retrieval + measurement pipeline over representative
autoharness-shaped outputs and marks a case a SAFE WIN only when all six
spike proof-method criteria hold (docs/spikes/2026-07-15-...md §7.4):

1. compressed tokens are lower under both tokenizers;
2. retrieval is byte-equivalent;
3. rejected/declined attempts leave no durable store row;
4. the evidence oracle passes without retrieval;
5. the task is answerable from the compressed view without retrieval;
6. decline cases and negative controls are reported, not hidden.
"""

import pytest

from brainspace import config
from brainspace.benchmark import (
    BenchmarkCase,
    run_benchmark,
    render_markdown_report,
    render_json_report,
)
from brainspace.store import BrainspaceStore


@pytest.fixture(autouse=True)
def enable_experiment(monkeypatch):
    monkeypatch.setenv(config.ENABLED_ENV_VAR, "1")


@pytest.fixture
def store(tmp_path):
    s = BrainspaceStore(str(tmp_path))
    yield s
    s.close()


def _compressible_text(fact="exit code: 0"):
    return "noisy repeated log line\n" * 200 + fact


def test_compression_positive_case_is_marked_safe_win(store, monkeypatch):
    # Simulate a genuinely available model tokenizer (this environment has
    # no tiktoken installed) so the happy-path safe-win assertion below
    # tests real both-tokenizer proof rather than the tokenizer-unavailable
    # fallback path (see the dedicated inconclusive-path test below).
    #
    # Two independent things must be simulated as "tokenizer available"
    # here: the hook's OWN never-expand gate (P-018 round-6 finding —
    # without this the hook declines before ever returning a
    # ``modifiedResult``, so the benchmark would never reach its own
    # tokenizer-based criteria evaluation at all) and the benchmark's
    # separate ``measure_dual`` re-measurement used for detailed reporting.
    from brainspace import measurement as measurement_module
    from brainspace.measurement import MeasurementResult

    monkeypatch.setattr(
        "brainspace.hook.is_model_tokenizer_available", lambda: True
    )

    def fake_measure_dual(original, compressed_view, footer):
        fallback = MeasurementResult(
            raw_tokens=1000,
            compressed_tokens=100,
            net_savings_tokens=900,
            projected_savings_by_turn={1: 900, 3: 2700, 5: 4500, 10: 9000},
        )
        model = MeasurementResult(
            raw_tokens=800,
            compressed_tokens=90,
            net_savings_tokens=710,
            projected_savings_by_turn={1: 710, 3: 2130, 5: 3550, 10: 7100},
        )
        return {"fallback": fallback, "model": model}

    monkeypatch.setattr(measurement_module, "measure_dual", fake_measure_dual)

    case = BenchmarkCase(
        name="pytest-verbose-pass",
        tool_name="bash",
        text=_compressible_text("exit code: 0"),
        task_question="did the command succeed?",
        required_fact="exit code: 0",
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.category == "compression_positive"
    assert result.safe_win is True
    assert result.criteria["byte_equivalent_retrieval"] is True
    assert result.criteria["lower_tokens_fallback"] is True
    assert result.criteria["lower_tokens_model"] is True
    assert result.criteria["model_tokenizer_available"] is True
    assert result.criteria["evidence_oracle_passes"] is True
    assert result.criteria["task_answerable_from_compressed_view"] is True


def test_compression_case_is_inconclusive_when_model_tokenizer_unavailable(store, monkeypatch):
    # Finding #1 (P-018 review): when the model tokenizer is unavailable,
    # the case must never silently pass criterion 1 (lower tokens under
    # BOTH tokenizers) just because the fallback estimator shows savings.
    # It must be reported as inconclusive / not a safe win.
    #
    # This test exercises `_run_compression_case`'s own defensive reporting
    # logic in isolation: the hook's never-expand gate is simulated as
    # having confirmed a tokenizer is available (so it actually compresses
    # and returns a `modifiedResult`), while the benchmark's SEPARATE
    # `measure_dual` re-measurement (used only for detailed criteria
    # reporting) is simulated as finding no model tokenizer. In a real,
    # single-process run these two would never disagree (both ultimately
    # consult the same tokenizer loader), but this test protects the
    # reporting function against ever silently trusting fallback-only
    # evidence if that ever changed.
    from brainspace import measurement as measurement_module
    from brainspace.tokenizer_fallback import estimate_tokens

    monkeypatch.setattr(
        "brainspace.hook.is_model_tokenizer_available", lambda: True
    )

    def fake_measure_dual(original, compressed_view, footer):
        fallback = measurement_module.measure(
            original, compressed_view, footer, token_counter=estimate_tokens
        )
        return {"fallback": fallback, "model": None}

    monkeypatch.setattr(measurement_module, "measure_dual", fake_measure_dual)

    case = BenchmarkCase(
        name="pytest-verbose-pass",
        tool_name="bash",
        text=_compressible_text("exit code: 0"),
        task_question="did the command succeed?",
        required_fact="exit code: 0",
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.safe_win is False
    assert result.criteria["model_tokenizer_available"] is False
    assert result.criteria["lower_tokens_model"] is False
    assert result.criteria["lower_tokens_both"] is False
    assert "inconclusive" in result.notes.lower()


def test_capture_failed_case_is_never_a_safe_win_even_if_all_else_passes(store, monkeypatch):
    # Finding #15 (P-018 review): a non-zero-exit / misconfigured command
    # capture must never be reported as a compression-positive SAFE WIN,
    # even if the (unreliable) captured text happens to look compressible
    # and every other criterion would otherwise pass.
    from brainspace import measurement as measurement_module
    from brainspace.measurement import MeasurementResult

    monkeypatch.setattr(
        "brainspace.hook.is_model_tokenizer_available", lambda: True
    )

    def fake_measure_dual(original, compressed_view, footer):
        result = MeasurementResult(
            raw_tokens=1000,
            compressed_tokens=100,
            net_savings_tokens=900,
            projected_savings_by_turn={1: 900, 3: 2700, 5: 4500, 10: 9000},
        )
        return {"fallback": result, "model": result}

    monkeypatch.setattr(measurement_module, "measure_dual", fake_measure_dual)

    case = BenchmarkCase(
        name="pytest-vv-misconfigured",
        tool_name="bash",
        text=_compressible_text("exit code: 0"),
        task_question="did the command succeed?",
        required_fact="exit code: 0",
        capture_failed=True,
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.safe_win is False
    assert result.criteria["capture_succeeded"] is False
    assert "capture failed" in result.notes.lower()


def test_compression_case_fails_safe_win_when_required_fact_would_be_lost(store, monkeypatch):
    # A required fact buried only in the collapsed middle (not head/tail)
    # must cause the oracle to fail, and the case must NOT be a safe win.
    # Uses a PR reference (not an exit-code/failure pattern) so the policy
    # pre-screen still treats this as a compression candidate rather than
    # declining it outright as a failure-bearing output.
    monkeypatch.setattr(
        "brainspace.hook.is_model_tokenizer_available", lambda: True
    )
    text = ("padding line\n" * 100) + "see PR #427 for details\n" + ("padding line\n" * 100)
    case = BenchmarkCase(
        name="buried-pr-reference",
        tool_name="bash",
        text=text,
        task_question="which PR is referenced?",
        required_fact="PR #427",
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.safe_win is False
    assert result.criteria["evidence_oracle_passes"] is False


def test_decline_control_case_reports_no_durable_row(store):
    case = BenchmarkCase(
        name="secret-bearing-output",
        tool_name="bash",
        text="AKIAABCDEFGHIJKLMNOP\n" + ("padding line\n" * 50),
        task_question="n/a",
        expect_decline=True,
        decline_reason_label="secret_bearing",
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.category == "decline_control"
    # P-018 round-3 follow-up finding: a decline control passing its own two
    # checks (declined as expected, no durable row) is NOT the same thing as
    # a "SAFE WIN" under the module's six-criteria compression-positive bar
    # (module docstring, §7.4 of the spike) -- conflating the two silently
    # inflated `safe_win_count` even though zero compression-positive cases
    # met all six criteria. `safe_win` must stay False for every
    # decline_control result; decline correctness is tracked separately via
    # `decline_correct`.
    assert result.safe_win is False
    assert result.decline_correct is True
    assert result.criteria["declined_as_expected"] is True
    assert result.criteria["no_durable_row_on_decline"] is True


def test_decline_control_case_flags_when_it_unexpectedly_compresses(store, monkeypatch):
    # Sanity check: if a case marked expect_decline actually compresses,
    # that is NOT hidden — it is reported as a failed decline control.
    # Simulate a tokenizer being available so the hook's own never-expand
    # gate does not itself decline first (which would otherwise mask the
    # "mislabeled decline" scenario this test targets).
    monkeypatch.setattr(
        "brainspace.hook.is_model_tokenizer_available", lambda: True
    )
    case = BenchmarkCase(
        name="mislabeled-decline",
        tool_name="bash",
        text="repeated noisy log line\n" * 200,
        task_question="n/a",
        expect_decline=True,
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.safe_win is False
    assert result.decline_correct is False
    assert result.criteria["declined_as_expected"] is False


def test_unwritable_store_simulation_falls_back_to_passthrough(store):
    case = BenchmarkCase(
        name="unwritable-store-passthrough",
        tool_name="bash",
        text="repeated noisy log line\n" * 200,
        task_question="n/a",
        expect_decline=True,
        simulate_unwritable_store=True,
    )
    report = run_benchmark([case], store=store)
    result = report.results[0]
    assert result.safe_win is False
    assert result.decline_correct is True
    assert result.criteria["declined_as_expected"] is True
    assert result.criteria["no_durable_row_on_decline"] is True


def test_report_decline_correct_count_tracked_separately_from_safe_win_count(store):
    # P-018 round-3 follow-up finding regression test: `safe_win_count` must
    # reflect only genuine six-criteria compression-positive safe wins.
    # Correctly-behaving decline controls are counted via
    # `decline_correct_count`, never folded into `safe_win_count`.
    cases = [
        BenchmarkCase(
            name="win-case",
            tool_name="bash",
            text=_compressible_text(),
            task_question="q",
            required_fact="exit code: 0",
        ),
        BenchmarkCase(
            name="decline-case",
            tool_name="bash",
            text="tiny",
            task_question="n/a",
            expect_decline=True,
        ),
    ]
    report = run_benchmark(cases, store=store)
    assert report.decline_correct_count == 1
    # The compression-positive case above has no fake tokenizer stub, so it
    # is not proven a safe win either -- safe_win_count must be 0, not 1
    # (which the old bug would have reported by counting the decline too).
    assert report.safe_win_count == 0


def test_report_includes_both_compression_and_decline_cases_not_hidden(store):
    cases = [
        BenchmarkCase(
            name="win-case",
            tool_name="bash",
            text=_compressible_text(),
            task_question="q",
            required_fact="exit code: 0",
        ),
        BenchmarkCase(
            name="decline-case",
            tool_name="bash",
            text="tiny",
            task_question="n/a",
            expect_decline=True,
        ),
    ]
    report = run_benchmark(cases, store=store)
    names = {r.name for r in report.results}
    assert names == {"win-case", "decline-case"}
    assert report.compression_positive_count == 1
    assert report.decline_control_count == 1
    assert report.total_count == 2


def test_render_markdown_report_lists_every_case_including_declines(store):
    cases = [
        BenchmarkCase(
            name="win-case",
            tool_name="bash",
            text=_compressible_text(),
            task_question="q",
            required_fact="exit code: 0",
        ),
        BenchmarkCase(
            name="decline-case",
            tool_name="bash",
            text="tiny",
            task_question="n/a",
            expect_decline=True,
        ),
    ]
    report = run_benchmark(cases, store=store)
    markdown = render_markdown_report(report)
    assert "win-case" in markdown
    assert "decline-case" in markdown
    assert "SAFE WIN" in markdown or "safe_win" in markdown.lower()


def test_render_json_report_serializes_every_case_including_declines(store):
    cases = [
        BenchmarkCase(
            name="win-case",
            tool_name="bash",
            text=_compressible_text(),
            task_question="q",
            required_fact="exit code: 0",
        ),
        BenchmarkCase(
            name="decline-case",
            tool_name="bash",
            text="tiny",
            task_question="n/a",
            expect_decline=True,
        ),
    ]
    report = run_benchmark(cases, store=store)
    payload = render_json_report(report)
    assert payload["total_count"] == 2
    names = {c["name"] for c in payload["results"]}
    assert names == {"win-case", "decline-case"}
    assert "safe_win" in payload["results"][0]
