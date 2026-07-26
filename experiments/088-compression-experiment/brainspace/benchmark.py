"""Benchmark corpus runner + report (088.006-T).

Exercises the hook + retrieval + measurement pipeline over representative
autoharness-shaped tool outputs and marks each case a SAFE WIN only when
all six spike proof-method criteria hold
(docs/spikes/2026-07-15-copilot-cli-output-compression-experiment.md §7.4):

1. compressed tokens are lower under both tokenizers;
2. retrieval is byte-equivalent for every visible placeholder;
3. rejected/declined attempts leave no durable store row (decide-then-stash);
4. the evidence oracle passes WITHOUT retrieval for required inline facts;
5. the task is answerable from the compressed view without retrieval;
6. decline cases and negative controls are reported, not hidden.

Single concern: benchmark orchestration + report. This module does not
implement compression, retrieval, or measurement logic itself — it wires
together ``hook``, ``store``, ``evidence_oracle``, and ``measurement``.
"""

import re
from dataclasses import dataclass, field
from typing import Optional

from brainspace import measurement
from brainspace.evidence_oracle import evaluate_oracle
from brainspace.hook import process_post_tool_use
from brainspace.store import BrainspaceStore

_HANDLE_RE = re.compile(r'output_retrieve\(handle="([0-9a-f]+)"\)')


@dataclass
class BenchmarkCase:
    """A single benchmark corpus entry.

    ``required_fact`` is the predeclared substring that must remain visible
    (in the compressed view, without retrieval) for the task_question to be
    answerable — this is the deterministic proxy used for proof-method
    criterion 5 in place of a live model/evaluator call.

    ``expect_decline`` marks a decline/negative-control case (tiny outputs,
    secret-bearing output, gate verdicts, stack traces, failure-bearing
    output, operator/approval text, or a simulated unwritable store).

    ``simulate_unwritable_store`` forces ``store.put`` to raise for the
    duration of this single case, to exercise the fail-safe passthrough
    path without permanently breaking the shared store fixture.

    ``provenance`` documents where ``text`` came from: ``"live"`` for text
    captured from a real, locally-run autoharness command, or a short
    description (e.g. ``"synthetic-representative: engram MCP surface not
    running in this benchmark environment"``) when a live capture was not
    possible. This is surfaced in the report so no positive-savings claim
    can be mistaken for a live measurement it isn't.

    ``capture_failed`` marks a live command capture that itself failed
    (non-zero exit / misconfigured tool) rather than produced a real
    sample — such a case can never be reported as a SAFE WIN.
    """

    name: str
    tool_name: str
    text: str
    task_question: str
    required_fact: Optional[str] = None
    expect_decline: bool = False
    decline_reason_label: Optional[str] = None
    simulate_unwritable_store: bool = False
    provenance: str = "live"
    capture_failed: bool = False


@dataclass
class CaseResult:
    name: str
    category: str  # "compression_positive" | "decline_control"
    safe_win: bool
    criteria: dict = field(default_factory=dict)
    notes: str = ""
    decline_correct: Optional[bool] = None


@dataclass
class BenchmarkReport:
    results: list = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.results)

    @property
    def safe_win_count(self) -> int:
        return sum(1 for r in self.results if r.safe_win)

    @property
    def decline_control_count(self) -> int:
        return sum(1 for r in self.results if r.category == "decline_control")

    @property
    def decline_correct_count(self) -> int:
        """Decline-control cases that behaved correctly (declined, no
        durable row). Tracked separately from ``safe_win_count`` -- a
        correctly-behaving decline control is not the same thing as meeting
        the six-criteria compression-positive safe-win bar (P-018 round-3
        follow-up finding: conflating the two silently inflated the reported
        SAFE WIN count).
        """
        return sum(
            1
            for r in self.results
            if r.category == "decline_control" and r.decline_correct
        )

    @property
    def compression_positive_count(self) -> int:
        return sum(1 for r in self.results if r.category == "compression_positive")


def _payload(tool_name: str, text: str) -> dict:
    return {
        "sessionId": "benchmark",
        "timestamp": 0,
        "cwd": "/workspace",
        "toolName": tool_name,
        "toolArgs": {},
        "toolResult": {"resultType": "success", "textResultForLlm": text},
    }


def _run_decline_case(case: BenchmarkCase, store: BrainspaceStore) -> CaseResult:
    rows_before = store.row_count()
    unwritable_store_path_exercised = None

    if case.simulate_unwritable_store:
        original_put = BrainspaceStore.put
        invocations = {"count": 0}

        def _boom(self, _text):
            invocations["count"] += 1
            raise RuntimeError("simulated unwritable store")

        BrainspaceStore.put = _boom
        try:
            result = process_post_tool_use(_payload(case.tool_name, case.text), store)
        finally:
            BrainspaceStore.put = original_put
        # P-018 round-9 finding: in a tokenizer-less environment the hook's
        # never-expand guard declines BEFORE ever calling store.put(), so
        # the injected failure above is never actually reached -- track
        # whether it was, so this control cannot silently claim to have
        # proven fail-safe passthrough on a store-write error when it
        # never actually exercised that code path this run.
        unwritable_store_path_exercised = invocations["count"] > 0
    else:
        result = process_post_tool_use(_payload(case.tool_name, case.text), store)

    rows_after = store.row_count()
    declined = result == {}
    no_new_row = rows_after == rows_before

    notes = case.decline_reason_label or ""
    if case.provenance != "live":
        notes = f"{notes} [{case.provenance}]".strip()

    criteria = {
        "declined_as_expected": declined,
        "no_durable_row_on_decline": no_new_row,
    }
    decline_correct = declined and no_new_row
    if case.simulate_unwritable_store:
        criteria["unwritable_store_path_exercised"] = bool(unwritable_store_path_exercised)
        if not unwritable_store_path_exercised:
            # The hook declined for a DIFFERENT, earlier reason (e.g. no
            # real model tokenizer available) -- this control has NOT
            # proven the store-write fail-safe passthrough behavior it
            # claims to test. Report this honestly instead of silently
            # counting it as a correctly-proven decline control (the same
            # honesty bar this module already applies to the model-
            # tokenizer-unavailable INCONCLUSIVE reporting).
            decline_correct = False
            notes = (
                f"{notes} [INCONCLUSIVE: hook declined before store.put() was "
                "reached; unwritable-store passthrough not exercised this run]"
            ).strip()

    return CaseResult(
        name=case.name,
        category="decline_control",
        # A correctly-declined control is NOT a "safe win" under the
        # module's six-criteria compression-positive bar (module docstring,
        # spike §7.4) -- it never attempted compression at all. Conflating
        # "declined correctly" with `safe_win=True` silently inflated the
        # reported SAFE WIN count (P-018 round-3 follow-up finding).
        # `safe_win` is therefore always False here; decline correctness is
        # reported via the dedicated `decline_correct` field/count instead.
        safe_win=False,
        decline_correct=decline_correct,
        criteria=criteria,
        notes=notes,
    )


def _run_compression_case(case: BenchmarkCase, store: BrainspaceStore) -> CaseResult:
    rows_before = store.row_count()
    result = process_post_tool_use(_payload(case.tool_name, case.text), store)
    rows_after = store.row_count()

    if "modifiedResult" not in result:
        return CaseResult(
            name=case.name,
            category="compression_positive",
            safe_win=False,
            criteria={"compressed_at_all": False},
            notes="hook declined this case; not a compression candidate",
        )

    compressed_text = result["modifiedResult"]["textResultForLlm"]
    match = _HANDLE_RE.search(compressed_text)
    handle = match.group(1) if match else None

    # Criterion 2: byte-equivalent retrieval.
    retrieved = store.get(handle) if handle else None
    byte_equivalent = retrieved == case.text

    # Criterion 3: decide-then-stash — at most one new row (dedup-safe).
    no_extra_rows = rows_after in (rows_before, rows_before + 1)

    # Criterion 1: lower tokens under both tokenizers. An unavailable model
    # tokenizer must NEVER silently satisfy this criterion just because the
    # fallback estimator shows savings -- the case is INCONCLUSIVE (not a
    # safe win) until proven under a real model tokenizer too.
    dual = measurement.measure_dual(case.text, compressed_text, "")
    lower_fallback = dual["fallback"].compressed_tokens < dual["fallback"].raw_tokens
    if dual["model"] is not None:
        lower_model = dual["model"].compressed_tokens < dual["model"].raw_tokens
        model_tokenizer_available = True
        model_caveat = ""
    else:
        lower_model = False
        model_tokenizer_available = False
        model_caveat = (
            "INCONCLUSIVE: model tokenizer unavailable -- criterion 1 "
            "(lower tokens under both tokenizers) cannot be proven, so this "
            "case is never reported as a safe win on fallback-only evidence"
        )

    # Criterion 4: evidence oracle passes WITHOUT retrieval.
    oracle = evaluate_oracle(case.text, compressed_text)

    # Criterion 5: task answerable from compressed view without retrieval
    # (deterministic proxy: the predeclared required_fact substring).
    if case.required_fact:
        answerable = case.required_fact in compressed_text
    else:
        answerable = True

    criteria = {
        "byte_equivalent_retrieval": byte_equivalent,
        "no_extra_rows_beyond_stash": no_extra_rows,
        "lower_tokens_fallback": lower_fallback,
        "lower_tokens_model": lower_model,
        "lower_tokens_both": lower_fallback and lower_model,
        "model_tokenizer_available": model_tokenizer_available,
        "evidence_oracle_passes": oracle.passed,
        "task_answerable_from_compressed_view": answerable,
        "capture_succeeded": not case.capture_failed,
        "raw_tokens_fallback": dual["fallback"].raw_tokens,
        "compressed_tokens_fallback": dual["fallback"].compressed_tokens,
        "net_savings_tokens_fallback": dual["fallback"].net_savings_tokens,
        "projected_savings_10_turns_fallback": dual["fallback"].projected_savings_by_turn.get(10),
    }
    if dual["model"] is not None:
        criteria["raw_tokens_model"] = dual["model"].raw_tokens
        criteria["compressed_tokens_model"] = dual["model"].compressed_tokens
        criteria["net_savings_tokens_model"] = dual["model"].net_savings_tokens

    safe_win = all(
        [
            criteria["byte_equivalent_retrieval"],
            criteria["no_extra_rows_beyond_stash"],
            criteria["lower_tokens_both"],
            criteria["evidence_oracle_passes"],
            criteria["task_answerable_from_compressed_view"],
            criteria["capture_succeeded"],
        ]
    )

    notes = model_caveat
    if case.capture_failed:
        capture_note = (
            "capture failed (non-zero exit / misconfigured command); "
            "never a safe win regardless of other criteria"
        )
        notes = f"{capture_note} {notes}".strip()
    if case.provenance != "live":
        notes = f"{notes} [{case.provenance}]".strip()

    return CaseResult(
        name=case.name,
        category="compression_positive",
        safe_win=safe_win,
        criteria=criteria,
        notes=notes,
    )


def run_benchmark(cases, store: BrainspaceStore) -> BenchmarkReport:
    """Run every case in ``cases`` against ``store`` and return a report.

    Decline-control cases and compression-positive cases are both always
    included in the returned report (proof-method criterion 6: decline
    cases and negative controls are reported, not hidden).
    """
    results = []
    for case in cases:
        if case.expect_decline:
            results.append(_run_decline_case(case, store))
        else:
            results.append(_run_compression_case(case, store))
    return BenchmarkReport(results=results)


def render_json_report(report: BenchmarkReport) -> dict:
    """Render a consolidated JSON-serializable report listing every case."""
    return {
        "total_count": report.total_count,
        "compression_positive_count": report.compression_positive_count,
        "decline_control_count": report.decline_control_count,
        "safe_win_count": report.safe_win_count,
        "decline_correct_count": report.decline_correct_count,
        "results": [
            {
                "name": r.name,
                "category": r.category,
                "safe_win": r.safe_win,
                "decline_correct": r.decline_correct,
                "criteria": r.criteria,
                "notes": r.notes,
            }
            for r in report.results
        ],
    }


def render_markdown_report(report: BenchmarkReport) -> str:
    """Render a consolidated Markdown report listing every case."""
    lines = [
        "# 088-F Compression Experiment — Benchmark Report",
        "",
        f"- Total cases: {report.total_count}",
        f"- Compression-positive cases: {report.compression_positive_count}",
        f"- Decline-control cases: {report.decline_control_count}",
        f"- SAFE WIN count (six-criteria compression-positive bar): {report.safe_win_count}",
        f"- Decline-control-correct count: {report.decline_correct_count} of {report.decline_control_count}",
        "",
        "| Case | Category | Verdict | Notes |",
        "|---|---|---|---|",
    ]
    for r in report.results:
        if r.category == "decline_control":
            if r.decline_correct:
                verdict = "DECLINE CORRECT"
            elif r.criteria.get("unwritable_store_path_exercised") is False:
                verdict = "INCONCLUSIVE (mechanism not exercised)"
            else:
                verdict = "DECLINE FAILED (compressed unexpectedly)"
        elif r.safe_win:
            verdict = "SAFE WIN"
        elif r.criteria.get("model_tokenizer_available") is False:
            verdict = "INCONCLUSIVE (model tokenizer unavailable)"
        else:
            verdict = "NOT a safe win"
        lines.append(f"| {r.name} | {r.category} | {verdict} | {r.notes} |")

    lines.append("")
    lines.append("## Per-case criteria detail")
    for r in report.results:
        lines.append(f"\n### {r.name} ({r.category})")
        for key, value in r.criteria.items():
            lines.append(f"- `{key}`: {value}")
    return "\n".join(lines)
