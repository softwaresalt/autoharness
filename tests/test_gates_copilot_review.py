"""Tests for the deterministic Copilot-review merge gate (068.001-T / 068-F).

Scope: a pure verdict classifier over a parsed PR review state, a fail-safe GraphQL
query wrapper, and a bounded poll loop. The gate is FAIL-CLOSED: when Copilot review
is enabled and completion/resolution is incomplete or unverifiable, it BLOCKS.

No live models, no network, no real subprocess: ``query_fn`` / ``run_fn`` / ``sleep_fn``
/ ``clock_fn`` are injected so every test is fully hermetic and deterministic.
"""

from __future__ import annotations

import unittest

from autoharness.gates.copilot_review import (
    COPILOT_LOGIN,
    PASS_VERDICTS,
    CopilotReviewResult,
    ReviewRecord,
    ReviewState,
    Verdict,
    build_query_argv,
    classify,
    evaluate,
    parse_graphql_response,
    query_pr_review_state,
)

_HEAD = "a" * 40
_OLD_HEAD = "b" * 40


def _state(
    *,
    head=_HEAD,
    requested=False,
    reviews=(),
    unresolved=(),
    parse_ok=True,
) -> ReviewState:
    return ReviewState(
        head_ref_oid=head,
        copilot_requested=requested,
        copilot_reviews=tuple(reviews),
        copilot_unresolved_thread_ids=tuple(unresolved),
        parse_ok=parse_ok,
    )


def _review(commit=_HEAD, state="COMMENTED") -> ReviewRecord:
    return ReviewRecord(state=state, commit_oid=commit)


# ---------------------------------------------------------------------------
# Pure classifier
# ---------------------------------------------------------------------------


class ClassifyTests(unittest.TestCase):
    def test_disabled_is_not_applicable(self) -> None:
        # Even a fully engaged, unresolved state passes when enforcement is disabled.
        st = _state(requested=True, reviews=[_review()], unresolved=["T1"])
        self.assertEqual(classify(st, "disabled"), Verdict.NOT_APPLICABLE)

    def test_auto_no_engagement_is_not_applicable(self) -> None:
        st = _state(requested=False, reviews=[])
        self.assertEqual(classify(st, "auto"), Verdict.NOT_APPLICABLE)

    def test_auto_requested_but_no_review_waits(self) -> None:
        st = _state(requested=True, reviews=[])
        self.assertEqual(classify(st, "auto"), Verdict.WAITING_FOR_REVIEW)

    def test_review_for_stale_head_waits(self) -> None:
        st = _state(requested=True, reviews=[_review(commit=_OLD_HEAD)])
        self.assertEqual(classify(st, "auto"), Verdict.WAITING_FOR_REVIEW)

    def test_pending_review_for_head_waits(self) -> None:
        st = _state(requested=True, reviews=[_review(state="PENDING")])
        self.assertEqual(classify(st, "auto"), Verdict.WAITING_FOR_REVIEW)

    def test_completed_with_unresolved_threads_blocks(self) -> None:
        st = _state(requested=True, reviews=[_review()], unresolved=["T1", "T2"])
        self.assertEqual(classify(st, "auto"), Verdict.UNRESOLVED_THREADS)

    def test_completed_and_resolved_is_satisfied(self) -> None:
        st = _state(requested=True, reviews=[_review()], unresolved=[])
        self.assertEqual(classify(st, "auto"), Verdict.SATISFIED)

    def test_engagement_via_existing_review_only(self) -> None:
        # Not a requested reviewer, but a Copilot review exists -> engaged.
        st = _state(requested=False, reviews=[_review()])
        self.assertEqual(classify(st, "auto"), Verdict.SATISFIED)

    def test_required_forces_hold_before_request(self) -> None:
        # required mode holds even with no engagement signal at all.
        st = _state(requested=False, reviews=[])
        self.assertEqual(classify(st, "required"), Verdict.WAITING_FOR_REVIEW)

    def test_timed_out_escalates_to_review_timeout(self) -> None:
        st = _state(requested=True, reviews=[])
        self.assertEqual(
            classify(st, "auto", timed_out=True), Verdict.REVIEW_TIMEOUT
        )

    def test_timed_out_does_not_override_satisfied(self) -> None:
        st = _state(requested=True, reviews=[_review()], unresolved=[])
        self.assertEqual(classify(st, "auto", timed_out=True), Verdict.SATISFIED)

    def test_verify_failed_blocks_in_every_mode(self) -> None:
        for mode in ("auto", "required"):
            self.assertEqual(
                classify(None, mode, verify_failed=True), Verdict.VERIFY_FAILED
            )

    def test_missing_head_is_ambiguous(self) -> None:
        st = _state(head=None, requested=True)
        self.assertEqual(classify(st, "auto"), Verdict.DETECTION_AMBIGUOUS)

    def test_unparseable_state_is_ambiguous(self) -> None:
        st = _state(parse_ok=False)
        self.assertEqual(classify(st, "auto"), Verdict.DETECTION_AMBIGUOUS)

    def test_none_state_is_ambiguous(self) -> None:
        self.assertEqual(classify(None, "auto"), Verdict.DETECTION_AMBIGUOUS)

    def test_invalid_enforcement_raises(self) -> None:
        with self.assertRaises(ValueError):
            classify(_state(), "sometimes")

    def test_only_satisfied_and_na_pass(self) -> None:
        self.assertEqual(PASS_VERDICTS, {Verdict.SATISFIED, Verdict.NOT_APPLICABLE})


# ---------------------------------------------------------------------------
# Result mapping / fail-closed invariant
# ---------------------------------------------------------------------------


class ResultTests(unittest.TestCase):
    def test_pass_verdicts_exit_zero(self) -> None:
        for v in (Verdict.SATISFIED, Verdict.NOT_APPLICABLE):
            r = CopilotReviewResult(v, "auto")
            self.assertFalse(r.blocked)
            self.assertEqual(r.exit_code, 0)

    def test_all_block_verdicts_exit_nonzero(self) -> None:
        # Fail-closed regression guard: no enabled-but-incomplete verdict passes.
        for v in (
            Verdict.WAITING_FOR_REVIEW,
            Verdict.UNRESOLVED_THREADS,
            Verdict.REVIEW_TIMEOUT,
            Verdict.DETECTION_AMBIGUOUS,
            Verdict.VERIFY_FAILED,
        ):
            r = CopilotReviewResult(v, "auto")
            self.assertTrue(r.blocked, f"{v} must block")
            self.assertEqual(r.exit_code, 1)

    def test_force_overrides_block(self) -> None:
        r = CopilotReviewResult(Verdict.REVIEW_TIMEOUT, "auto", forced=True)
        self.assertFalse(r.blocked)
        self.assertEqual(r.exit_code, 0)

    def test_to_dict_is_serializable(self) -> None:
        import json

        r = CopilotReviewResult(
            Verdict.UNRESOLVED_THREADS, "auto",
            head_ref_oid=_HEAD, unresolved_thread_ids=("T1",),
        )
        payload = json.loads(json.dumps(r.to_dict()))
        self.assertEqual(payload["verdict"], "UNRESOLVED_THREADS")
        self.assertEqual(payload["exit_code"], 1)
        self.assertEqual(payload["unresolved_thread_ids"], ["T1"])


# ---------------------------------------------------------------------------
# GraphQL parsing
# ---------------------------------------------------------------------------


def _graphql(head=_HEAD, requested=False, reviews=(), threads=()):
    return {
        "data": {
            "repository": {
                "pullRequest": {
                    "headRefOid": head,
                    "reviewRequests": {
                        "nodes": [
                            {"requestedReviewer": {"__typename": "Bot", "login": COPILOT_LOGIN}}
                        ]
                        if requested
                        else []
                    },
                    "reviews": {
                        "nodes": [
                            {
                                "author": {"login": author},
                                "state": st,
                                "commit": {"oid": oid},
                            }
                            for author, st, oid in reviews
                        ]
                    },
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": tid,
                                "isResolved": resolved,
                                "comments": {"nodes": [{"author": {"login": author}}]},
                            }
                            for tid, resolved, author in threads
                        ]
                    },
                }
            }
        }
    }


class ParseTests(unittest.TestCase):
    def test_parse_full_state(self) -> None:
        raw = _graphql(
            requested=True,
            reviews=[(COPILOT_LOGIN, "COMMENTED", _HEAD), ("human", "APPROVED", _HEAD)],
            threads=[
                ("PRRT_1", False, COPILOT_LOGIN),
                ("PRRT_2", True, COPILOT_LOGIN),
                ("PRRT_3", False, "human"),
            ],
        )
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertTrue(st.copilot_requested)
        # Only the Copilot review is retained (human review filtered out).
        self.assertEqual(len(st.copilot_reviews), 1)
        # Only the unresolved Copilot thread is retained.
        self.assertEqual(st.copilot_unresolved_thread_ids, ("PRRT_1",))
        self.assertTrue(st.completed_for_head())

    def test_parse_missing_pullrequest_is_not_ok(self) -> None:
        st = parse_graphql_response({"data": {"repository": {"pullRequest": None}}})
        self.assertFalse(st.parse_ok)

    def test_parse_tolerates_missing_envelope(self) -> None:
        raw = _graphql()["data"]  # no top-level "data"
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)


# ---------------------------------------------------------------------------
# Injection safety (acceptance-blocking negative test)
# ---------------------------------------------------------------------------


class InjectionSafetyTests(unittest.TestCase):
    def test_argv_is_fixed_arity_and_confines_repo(self) -> None:
        hostile = "owner/name"  # valid; the point is arity + confinement
        argv = build_query_argv(123, hostile)
        # Fixed number of elements regardless of input.
        self.assertEqual(len(argv), 11)
        self.assertEqual(argv[0], "gh")
        self.assertIn("owner=owner", argv)
        self.assertIn("repo=name", argv)
        self.assertIn("pr=123", argv)

    def test_malicious_repo_is_rejected(self) -> None:
        for bad in (
            "owner/name; rm -rf /",
            "owner/name && curl evil",
            "$(whoami)/x",
            "owner name",
            "onlyname",
            "owner/na`me`",
        ):
            with self.assertRaises(ValueError, msg=bad):
                query_pr_review_state(1, bad, run_fn=lambda *a, **k: None)

    def test_malicious_pr_is_rejected(self) -> None:
        for bad in ("1; rm -rf /", "abc", "-5", "0", "1 2"):
            with self.assertRaises(ValueError, msg=bad):
                query_pr_review_state(bad, "owner/name", run_fn=lambda *a, **k: None)

    def test_query_runs_with_shell_false(self) -> None:
        captured = {}

        def fake_run(argv, **kwargs):
            captured["argv"] = argv
            captured["shell"] = kwargs.get("shell")
            return type("P", (), {"returncode": 0, "stdout": "{\"data\":{}}", "stderr": ""})()

        query_pr_review_state(7, "owner/name", run_fn=fake_run)
        self.assertFalse(captured["shell"])
        self.assertIsInstance(captured["argv"], list)


# ---------------------------------------------------------------------------
# Query fail-safe
# ---------------------------------------------------------------------------


class QueryFailSafeTests(unittest.TestCase):
    def test_nonzero_exit_raises(self) -> None:
        def fake_run(argv, **kwargs):
            return type("P", (), {"returncode": 1, "stdout": "", "stderr": "boom"})()

        with self.assertRaises(RuntimeError):
            query_pr_review_state(1, "owner/name", run_fn=fake_run)

    def test_bad_json_raises(self) -> None:
        def fake_run(argv, **kwargs):
            return type("P", (), {"returncode": 0, "stdout": "not json", "stderr": ""})()

        with self.assertRaises(RuntimeError):
            query_pr_review_state(1, "owner/name", run_fn=fake_run)


# ---------------------------------------------------------------------------
# Bounded poll loop + multi-round re-arm
# ---------------------------------------------------------------------------


class EvaluateTests(unittest.TestCase):
    def test_disabled_short_circuits(self) -> None:
        calls = []

        def q():
            calls.append(1)
            return _state()

        r = evaluate(1, "owner/name", enforcement="disabled", query_fn=q)
        self.assertEqual(r.verdict, Verdict.NOT_APPLICABLE)
        self.assertEqual(calls, [])  # never queried

    def test_satisfied_first_round(self) -> None:
        st = _state(requested=True, reviews=[_review()], unresolved=[])
        r = evaluate(1, "owner/name", query_fn=lambda: st)
        self.assertEqual(r.verdict, Verdict.SATISFIED)
        self.assertEqual(r.rounds, 1)
        self.assertFalse(r.blocked)

    def test_multi_round_rearm_stale_then_current(self) -> None:
        # Round 1: review targets an OLD head -> WAITING; round 2: current -> SATISFIED.
        states = [
            _state(requested=True, reviews=[_review(commit=_OLD_HEAD)]),
            _state(requested=True, reviews=[_review(commit=_HEAD)], unresolved=[]),
        ]
        clock = iter([0.0, 0.0, 5.0, 5.0, 5.0])
        r = evaluate(
            1, "owner/name",
            max_wait=100.0,
            poll_interval=1.0,
            query_fn=lambda: states.pop(0),
            sleep_fn=lambda s: None,
            clock_fn=lambda: next(clock),
        )
        self.assertEqual(r.verdict, Verdict.SATISFIED)
        self.assertEqual(r.rounds, 2)

    def test_waiting_times_out_and_blocks(self) -> None:
        st = _state(requested=True, reviews=[])
        # First clock() = start=0; second (elapsed check) = 30 >= max_wait 10.
        clock = iter([0.0, 30.0])
        r = evaluate(
            1, "owner/name",
            max_wait=10.0,
            poll_interval=1.0,
            query_fn=lambda: st,
            sleep_fn=lambda s: None,
            clock_fn=lambda: next(clock),
        )
        self.assertEqual(r.verdict, Verdict.REVIEW_TIMEOUT)
        self.assertTrue(r.blocked)
        self.assertEqual(r.exit_code, 1)

    def test_unresolved_threads_block_without_waiting(self) -> None:
        st = _state(requested=True, reviews=[_review()], unresolved=["PRRT_1"])
        r = evaluate(1, "owner/name", query_fn=lambda: st)
        self.assertEqual(r.verdict, Verdict.UNRESOLVED_THREADS)
        self.assertEqual(r.unresolved_thread_ids, ("PRRT_1",))
        self.assertTrue(r.blocked)

    def test_query_exception_is_verify_failed(self) -> None:
        def boom():
            raise RuntimeError("gh missing")

        r = evaluate(1, "owner/name", query_fn=boom)
        self.assertEqual(r.verdict, Verdict.VERIFY_FAILED)
        self.assertTrue(r.blocked)

    def test_required_before_request_blocks(self) -> None:
        st = _state(requested=False, reviews=[])
        r = evaluate(1, "owner/name", enforcement="required", query_fn=lambda: st)
        self.assertEqual(r.verdict, Verdict.WAITING_FOR_REVIEW)
        self.assertTrue(r.blocked)

    def test_invalid_enforcement_raises(self) -> None:
        with self.assertRaises(ValueError):
            evaluate(1, "owner/name", enforcement="bogus", query_fn=lambda: _state())


# ---------------------------------------------------------------------------
# Fail-closed hardening (068-F Copilot review findings)
# ---------------------------------------------------------------------------


def _pr(**overrides):
    """Build a minimal-but-complete pullRequest dict, then apply overrides."""
    pr = {
        "headRefOid": _HEAD,
        "reviewRequests": {"nodes": []},
        "reviews": {"nodes": []},
        "reviewThreads": {"nodes": []},
    }
    pr.update(overrides)
    return {"data": {"repository": {"pullRequest": pr}}}


class ParseHardeningTests(unittest.TestCase):
    def test_missing_head_is_ambiguous(self) -> None:
        self.assertFalse(parse_graphql_response(_pr(headRefOid=None)).parse_ok)

    def test_missing_review_connections_are_ambiguous(self) -> None:
        for key in ("reviewRequests", "reviews", "reviewThreads"):
            pr = _pr()["data"]["repository"]["pullRequest"]
            del pr[key]
            raw = {"data": {"repository": {"pullRequest": pr}}}
            self.assertFalse(parse_graphql_response(raw).parse_ok, msg=key)

    def test_truncated_connections_are_ambiguous(self) -> None:
        # A truncated thread/review/request list could hide the only disqualifying signal.
        cases = [
            {"reviewThreads": {"nodes": [], "pageInfo": {"hasNextPage": True}}},
            {"reviews": {"nodes": [], "pageInfo": {"hasPreviousPage": True}}},
            {"reviewRequests": {"nodes": [], "pageInfo": {"hasNextPage": True}}},
        ]
        for override in cases:
            self.assertFalse(parse_graphql_response(_pr(**override)).parse_ok, msg=override)

    def test_unknown_review_state_is_ambiguous(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "state": "WAT", "commit": {"oid": _HEAD}}
        ]})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_missing_review_state_is_ambiguous(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "commit": {"oid": _HEAD}}
        ]})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_non_boolean_isresolved_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [
            {"id": "PRRT_x", "isResolved": None,
             "comments": {"nodes": [{"author": {"login": COPILOT_LOGIN}}]}}
        ]})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_dismissed_review_does_not_complete_head(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "state": "DISMISSED", "commit": {"oid": _HEAD}}
        ]})
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertFalse(st.completed_for_head())

    def test_pending_review_does_not_complete_head(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "state": "PENDING", "commit": {"oid": _HEAD}}
        ]})
        self.assertFalse(parse_graphql_response(raw).completed_for_head())


class QueryHardeningTests(unittest.TestCase):
    def test_graphql_errors_array_raises(self) -> None:
        # gh can exit 0 with a partial-data errors payload; must fail closed.
        def fake_run(argv, **kwargs):
            body = '{"data": {"repository": null}, "errors": [{"message": "boom"}]}'
            return type("P", (), {"returncode": 0, "stdout": body, "stderr": ""})()

        with self.assertRaises(RuntimeError):
            query_pr_review_state(1, "owner/name", run_fn=fake_run)

    def test_evaluate_errors_array_is_verify_failed(self) -> None:
        def fake_run(argv, **kwargs):
            body = '{"data": {}, "errors": [{"message": "boom"}]}'
            return type("P", (), {"returncode": 0, "stdout": body, "stderr": ""})()

        r = evaluate(1, "owner/name", run_fn=fake_run)
        self.assertEqual(r.verdict, Verdict.VERIFY_FAILED)
        self.assertTrue(r.blocked)


class EvaluateHardeningTests(unittest.TestCase):
    def test_nan_max_wait_is_single_shot_not_infinite(self) -> None:
        st = _state(requested=True, reviews=[])
        r = evaluate(
            1, "owner/name",
            max_wait=float("nan"),
            query_fn=lambda: st,
            sleep_fn=lambda s: (_ for _ in ()).throw(AssertionError("must not sleep")),
        )
        self.assertEqual(r.verdict, Verdict.WAITING_FOR_REVIEW)
        self.assertTrue(r.blocked)

    def test_inf_max_wait_is_single_shot_not_infinite(self) -> None:
        st = _state(requested=True, reviews=[])
        r = evaluate(
            1, "owner/name",
            max_wait=float("inf"),
            query_fn=lambda: st,
            sleep_fn=lambda s: (_ for _ in ()).throw(AssertionError("must not sleep")),
        )
        self.assertEqual(r.verdict, Verdict.WAITING_FOR_REVIEW)

    def test_evaluate_validates_repo_before_querying(self) -> None:
        # With no injected query_fn, a hostile repo must raise ValueError up front
        # (CLI exit 2) rather than being swallowed as VERIFY_FAILED.
        with self.assertRaises(ValueError):
            evaluate(1, "owner/name; rm -rf /")

    def test_evaluate_validates_pr_before_querying(self) -> None:
        with self.assertRaises(ValueError):
            evaluate("1; rm", "owner/name")


if __name__ == "__main__":
    unittest.main()
