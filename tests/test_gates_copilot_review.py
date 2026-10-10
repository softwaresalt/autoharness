"""Tests for the deterministic Copilot-review merge gate (068.001-T / 068-F).

Scope: a pure verdict classifier over a parsed PR review state, a fail-safe GraphQL
query wrapper, and a bounded poll loop. The gate is FAIL-CLOSED: when Copilot review
is enabled and completion/resolution is incomplete or unverifiable, it BLOCKS.

No live models, no network, no real subprocess: ``query_fn`` / ``run_fn`` / ``sleep_fn``
/ ``clock_fn`` are injected so every test is fully hermetic and deterministic.
"""

from __future__ import annotations

import json
import unittest

from autoharness.gates.copilot_review import (
    COPILOT_LOGIN,
    DISPOSITION_MARKER,
    PASS_VERDICTS,
    TRUSTED_DISPOSITION_ASSOCIATIONS,
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
        # 201-F U3 invariant I1: the body-finding BLOCK verdict is never a pass.
        self.assertNotIn(Verdict.UNDISPOSITIONED_BODY_FINDINGS, PASS_VERDICTS)


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
            Verdict.UNDISPOSITIONED_BODY_FINDINGS,
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
                        else [],
                        "pageInfo": {"hasNextPage": False},
                    },
                    "reviews": {
                        "nodes": [
                            {
                                "author": {"login": author},
                                "state": st,
                                "commit": {"oid": oid},
                                "body": "",
                            }
                            for author, st, oid in reviews
                        ],
                        "pageInfo": {"hasPreviousPage": False},
                    },
                    "reviewThreads": {
                        "nodes": [
                            {
                                "id": tid,
                                "isResolved": resolved,
                                "comments": {"nodes": [{"author": {"login": author}}]},
                            }
                            for tid, resolved, author in threads
                        ],
                        "pageInfo": {"hasNextPage": False},
                    },
                    # 201-F U2: the real query always requests PR conversation comments.
                    "comments": {"nodes": [], "pageInfo": {"hasPreviousPage": False}},
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
    """Build a minimal-but-complete pullRequest dict, then apply overrides.

    Every connection carries an explicit, non-truncated ``pageInfo`` because the real
    GraphQL query always requests one and the parser now fails closed without it.
    The PR conversation ``comments`` connection (201-F U2) is empty and complete by
    default.
    """
    pr = {
        "headRefOid": _HEAD,
        "reviewRequests": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "reviews": {"nodes": [], "pageInfo": {"hasPreviousPage": False}},
        "reviewThreads": {"nodes": [], "pageInfo": {"hasNextPage": False}},
        "comments": {"nodes": [], "pageInfo": {"hasPreviousPage": False}},
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
        ], "pageInfo": {"hasPreviousPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_missing_review_state_is_ambiguous(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "commit": {"oid": _HEAD}}
        ], "pageInfo": {"hasPreviousPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_non_boolean_isresolved_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [
            {"id": "PRRT_x", "isResolved": None,
             "comments": {"nodes": [{"author": {"login": COPILOT_LOGIN}}]}}
        ], "pageInfo": {"hasNextPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_dismissed_review_does_not_complete_head(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "state": "DISMISSED", "commit": {"oid": _HEAD}, "body": ""}
        ], "pageInfo": {"hasPreviousPage": False}})
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertFalse(st.completed_for_head())

    def test_pending_review_does_not_complete_head(self) -> None:
        raw = _pr(reviews={"nodes": [
            {"author": {"login": COPILOT_LOGIN}, "state": "PENDING", "commit": {"oid": _HEAD}, "body": ""}
        ], "pageInfo": {"hasPreviousPage": False}})
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertFalse(st.completed_for_head())

    # --- round-2 fail-closed hardening (strict pagination / nodes / thread identity) --

    def test_missing_pageinfo_is_ambiguous(self) -> None:
        # A connection with no pageInfo cannot be proven complete -> fail closed.
        for key, field in (
            ("reviewRequests", "hasNextPage"),
            ("reviews", "hasPreviousPage"),
            ("reviewThreads", "hasNextPage"),
        ):
            raw = _pr(**{key: {"nodes": []}})
            self.assertFalse(parse_graphql_response(raw).parse_ok, msg=key)

    def test_non_boolean_pageinfo_field_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [], "pageInfo": {"hasNextPage": "false"}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_missing_nodes_array_is_ambiguous(self) -> None:
        # pageInfo present and complete, but nodes field absent -> unverifiable.
        raw = _pr(reviewRequests={"pageInfo": {"hasNextPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_non_array_nodes_is_ambiguous(self) -> None:
        raw = _pr(reviews={"nodes": "oops", "pageInfo": {"hasPreviousPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_non_object_node_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={
            "nodes": ["not-an-object"], "pageInfo": {"hasNextPage": False}
        })
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_unresolved_thread_malformed_comments_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [
            {"id": "PRRT_x", "isResolved": False, "comments": "nope"}
        ], "pageInfo": {"hasNextPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_unresolved_thread_empty_comments_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [
            {"id": "PRRT_x", "isResolved": False, "comments": {"nodes": []}}
        ], "pageInfo": {"hasNextPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_unresolved_thread_missing_author_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [
            {"id": "PRRT_x", "isResolved": False, "comments": {"nodes": [{}]}}
        ], "pageInfo": {"hasNextPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_unresolved_copilot_thread_non_string_id_is_ambiguous(self) -> None:
        raw = _pr(reviewThreads={"nodes": [
            {"id": 123, "isResolved": False,
             "comments": {"nodes": [{"author": {"login": COPILOT_LOGIN}}]}}
        ], "pageInfo": {"hasNextPage": False}})
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_unresolved_non_copilot_thread_is_ignored(self) -> None:
        # A determinable human-authored unresolved thread does not block this gate.
        raw = _pr(reviewThreads={"nodes": [
            {"id": "PRRT_h", "isResolved": False,
             "comments": {"nodes": [{"author": {"login": "human"}}]}}
        ], "pageInfo": {"hasNextPage": False}})
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertEqual(st.copilot_unresolved_thread_ids, ())

    # --- round-3 fail-closed hardening (reviewer/author identity) --------------------

    def test_malformed_requested_reviewer_is_ambiguous(self) -> None:
        raw = _pr(reviewRequests={
            "nodes": [{"requestedReviewer": None}],
            "pageInfo": {"hasNextPage": False},
        })
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_requested_reviewer_missing_typename_is_ambiguous(self) -> None:
        raw = _pr(reviewRequests={
            "nodes": [{"requestedReviewer": {"login": COPILOT_LOGIN}}],
            "pageInfo": {"hasNextPage": False},
        })
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_bot_reviewer_without_login_is_ambiguous(self) -> None:
        raw = _pr(reviewRequests={
            "nodes": [{"requestedReviewer": {"__typename": "Bot"}}],
            "pageInfo": {"hasNextPage": False},
        })
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_team_review_request_is_determinable_not_copilot(self) -> None:
        # A pending Team (or human) review request must NOT block or go ambiguous.
        raw = _pr(reviewRequests={
            "nodes": [{"requestedReviewer": {"__typename": "Team"}}],
            "pageInfo": {"hasNextPage": False},
        })
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertFalse(st.copilot_requested)

    def test_copilot_bot_request_is_detected(self) -> None:
        raw = _pr(reviewRequests={
            "nodes": [{"requestedReviewer": {"__typename": "Bot", "login": COPILOT_LOGIN}}],
            "pageInfo": {"hasNextPage": False},
        })
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertTrue(st.copilot_requested)

    def test_authorless_review_is_ambiguous(self) -> None:
        raw = _pr(reviews={
            "nodes": [{"state": "COMMENTED", "commit": {"oid": _HEAD}}],
            "pageInfo": {"hasPreviousPage": False},
        })
        self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_human_review_is_determinable_and_ignored(self) -> None:
        raw = _pr(reviews={
            "nodes": [{"author": {"login": "human"}, "state": "APPROVED",
                       "commit": {"oid": _HEAD}}],
            "pageInfo": {"hasPreviousPage": False},
        })
        st = parse_graphql_response(raw)
        self.assertTrue(st.parse_ok)
        self.assertEqual(st.copilot_reviews, ())


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

    def test_sleep_never_exceeds_remaining_budget(self) -> None:
        # poll_interval (15) is larger than the leftover window, so the loop must sleep
        # only the remaining budget rather than overshooting the advertised max-wait.
        st = _state(requested=True, reviews=[])
        slept: list[float] = []
        clock = iter([0.0, 0.0, 10.0])  # start, round-1 elapsed=0, round-2 elapsed=10
        r = evaluate(
            1, "owner/name",
            max_wait=10.0,
            poll_interval=15.0,
            query_fn=lambda: st,
            sleep_fn=slept.append,
            clock_fn=lambda: next(clock),
        )
        self.assertEqual(r.verdict, Verdict.REVIEW_TIMEOUT)
        self.assertEqual(slept, [10.0])  # not 15.0 — bounded to the remaining window

    def test_evaluate_has_no_forced_bypass_parameter(self) -> None:
        # Evaluation is purely blocking; only the CLI applies an audited --force.
        with self.assertRaises(TypeError):
            evaluate(1, "owner/name", query_fn=lambda: _state(), forced=True)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# 201-F U2: Copilot review bodies and trusted disposition-marker comments
# ---------------------------------------------------------------------------

_PM_BODY = "<summary><strong>Previously missed (1)</strong></summary>\n\nSynthetic finding.\n"


def _copilot_review_node(database_id, body, state="COMMENTED", commit=_HEAD):
    return {
        "databaseId": database_id,
        "author": {"login": COPILOT_LOGIN},
        "state": state,
        "commit": {"oid": commit},
        "body": body,
    }


def _comment_node(login, association, body):
    node = {"author": {"login": login}, "body": body}
    if association is not _MISSING:
        node["authorAssociation"] = association
    return node


_MISSING = object()


def _body_pr(review_nodes, comment_nodes=()):
    return _pr(
        reviews={"nodes": list(review_nodes), "pageInfo": {"hasPreviousPage": False}},
        comments={"nodes": list(comment_nodes), "pageInfo": {"hasPreviousPage": False}},
    )


class BodyFindingParseTests(unittest.TestCase):
    """201-F U2: review-body parse and trusted disposition-marker parse."""

    def test_marker_recognition_scopes_trusted_comments(self) -> None:
        review = _copilot_review_node(101, _PM_BODY)
        marker = f"{DISPOSITION_MARKER} 101"
        cases = (
            # (label, comment nodes, expected undispositioned review ids)
            ("no_comments", [], (101,)),
            ("member_marker_clears", [_comment_node("maintainer", "MEMBER", marker)], ()),
            ("owner_marker_clears", [_comment_node("owner", "OWNER", marker)], ()),
            ("collaborator_marker_clears", [_comment_node("collab", "COLLABORATOR", marker)], ()),
            ("bot_author_cannot_clear", [_comment_node(COPILOT_LOGIN, "MEMBER", marker)], (101,)),
            ("none_association_ignored", [_comment_node("outsider", "NONE", marker)], (101,)),
            ("contributor_association_ignored", [_comment_node("c", "CONTRIBUTOR", marker)], (101,)),
            (
                "first_time_contributor_ignored",
                [_comment_node("c", "FIRST_TIME_CONTRIBUTOR", marker)],
                (101,),
            ),
            ("missing_association_ignored", [_comment_node("c", _MISSING, marker)], (101,)),
            ("non_string_association_ignored", [_comment_node("c", 7, marker)], (101,)),
            ("trailing_text_is_not_a_marker", [_comment_node("maintainer", "MEMBER", f"{marker} later")], (101,)),
            ("leading_zero_is_not_canonical", [_comment_node("maintainer", "MEMBER", f"{DISPOSITION_MARKER} 0101")], (101,)),
            (
                "non_ascii_digits_are_not_a_marker",
                [_comment_node("maintainer", "MEMBER", f"{DISPOSITION_MARKER} \u0661\u0660\u0661")],
                (101,),
            ),
        )
        for label, comments, expected in cases:
            with self.subTest(case=label):
                state = parse_graphql_response(_body_pr([review], comments))
                self.assertEqual(state.undispositioned_body_finding_review_ids, expected)

    def test_null_author_comment_is_skipped_not_ambiguous(self) -> None:
        # A deleted account's comment cannot clear a disposition, so it is ignored. It
        # must not wedge a PR into DETECTION_AMBIGUOUS when nothing else is wrong.
        with self.subTest(case="clean_pr_with_null_author_comment"):
            null_author = {"author": None, "authorAssociation": "MEMBER", "body": "x"}
            state = parse_graphql_response(_body_pr([], [null_author]))
            self.assertTrue(state.parse_ok)
            self.assertEqual(state.undispositioned_body_finding_review_ids, ())
        with self.subTest(case="null_author_marker_does_not_clear"):
            marker_comment = {
                "author": None,
                "authorAssociation": "MEMBER",
                "body": f"{DISPOSITION_MARKER} 101",
            }
            state = parse_graphql_response(
                _body_pr([_copilot_review_node(101, _PM_BODY)], [marker_comment])
            )
            self.assertTrue(state.parse_ok)
            self.assertEqual(state.undispositioned_body_finding_review_ids, (101,))

    def test_fail_closed_body_and_comment_shapes(self) -> None:
        absent_body = _copilot_review_node(101, _PM_BODY)
        del absent_body["body"]
        cases = (
            ("non_string_body", _body_pr([_copilot_review_node(101, 42)])),
            ("null_body", _body_pr([_copilot_review_node(101, None)])),
            ("absent_body", _body_pr([absent_body])),
            ("body_finding_without_int_database_id", _body_pr([_copilot_review_node("101", _PM_BODY)])),
            ("body_finding_with_bool_database_id", _body_pr([_copilot_review_node(True, _PM_BODY)])),
            (
                "digit_run_beyond_int_conversion_limit",
                _body_pr([_copilot_review_node(101, "<summary><strong>Previously missed (" + "9" * 5000 + ")</strong></summary>")]),
            ),
            ("missing_comments_connection", _body_pr([_copilot_review_node(101, _PM_BODY)])),
        )
        for label, raw in cases:
            with self.subTest(case=label):
                if label == "missing_comments_connection":
                    del raw["data"]["repository"]["pullRequest"]["comments"]
                self.assertFalse(parse_graphql_response(raw).parse_ok)

    def test_review_state_scope_dismissed_and_stale_head(self) -> None:
        dismissed = _body_pr([_copilot_review_node(101, _PM_BODY, state="DISMISSED")])
        stale = _body_pr([_copilot_review_node(102, _PM_BODY, commit=_OLD_HEAD)])
        with self.subTest(case="dismissed_not_counted"):
            state = parse_graphql_response(dismissed)
            self.assertTrue(state.parse_ok)
            self.assertEqual(state.undispositioned_body_finding_review_ids, ())
        with self.subTest(case="stale_head_commented_counted"):
            state = parse_graphql_response(stale)
            self.assertTrue(state.parse_ok)
            self.assertEqual(state.undispositioned_body_finding_review_ids, (102,))


def _finding_review(database_id=101, state="COMMENTED", commit=_HEAD, overview=2):
    return ReviewRecord(
        state=state,
        commit_oid=commit,
        database_id=database_id,
        body_findings=1,
        overview_version=overview,
    )


def _body_state(*, reviews, unresolved=(), comments_complete=True, dispositioned=()):
    return ReviewState(
        head_ref_oid=_HEAD,
        copilot_requested=True,
        copilot_reviews=tuple(reviews),
        copilot_unresolved_thread_ids=tuple(unresolved),
        dispositioned_review_ids=frozenset(dispositioned),
        comments_complete=comments_complete,
    )


class BodyFindingVerdictTests(unittest.TestCase):
    """201-F U3: verdict, truncation, and payload."""

    def test_undispositioned_body_findings_block_after_resolved_threads(self) -> None:
        with self.subTest(case="undispositioned_blocks"):
            st = _body_state(reviews=[_finding_review()])
            self.assertEqual(classify(st, "auto"), Verdict.UNDISPOSITIONED_BODY_FINDINGS)
            result = CopilotReviewResult(
                Verdict.UNDISPOSITIONED_BODY_FINDINGS,
                "auto",
                undispositioned_body_finding_review_ids=(101,),
            )
            self.assertTrue(result.blocked)
            self.assertEqual(result.exit_code, 1)
        with self.subTest(case="trusted_disposition_clears"):
            st = _body_state(reviews=[_finding_review()], dispositioned=[101])
            self.assertEqual(classify(st, "auto"), Verdict.SATISFIED)

    def test_truncated_comments_with_undispositioned_findings_are_ambiguous(self) -> None:
        st = _body_state(reviews=[_finding_review()], comments_complete=False)
        self.assertEqual(classify(st, "auto"), Verdict.DETECTION_AMBIGUOUS)

    def test_payload_and_advisory_reach_the_result(self) -> None:
        with self.subTest(case="overview_v3_advisory"):
            state = _body_state(reviews=[_finding_review(overview=3)], dispositioned=[101])
            result = evaluate(1, "owner/name", query_fn=lambda: state, enforcement="auto")
            self.assertTrue(result.advisory)
        with self.subTest(case="to_dict_round_trip"):
            result = CopilotReviewResult(
                Verdict.UNDISPOSITIONED_BODY_FINDINGS,
                "auto",
                undispositioned_body_finding_review_ids=(101,),
            )
            payload = json.loads(json.dumps(result.to_dict()))
            self.assertEqual(payload["undispositioned_body_finding_review_ids"], [101])
            self.assertIn("advisory", payload)


class BodyFindingVerdictCharacterizationTests(unittest.TestCase):
    """Characterization: pre-existing ordering and PASS semantics that must hold."""

    def test_unresolved_threads_precede_body_findings(self) -> None:
        st = _body_state(reviews=[_finding_review()], unresolved=["T1"])
        self.assertEqual(classify(st, "auto"), Verdict.UNRESOLVED_THREADS)

    def test_review_timeout_with_body_findings_stays_timeout(self) -> None:
        st = _body_state(reviews=[_finding_review(commit=_OLD_HEAD)])
        self.assertEqual(classify(st, "auto", timed_out=True), Verdict.REVIEW_TIMEOUT)

    def test_empty_undispositioned_with_incomplete_comments_stays_satisfied(self) -> None:
        st = _body_state(
            reviews=[ReviewRecord(state="COMMENTED", commit_oid=_HEAD, database_id=101)],
            comments_complete=False,
        )
        self.assertEqual(classify(st, "auto"), Verdict.SATISFIED)

    def test_every_verdict_member_passes_or_blocks(self) -> None:
        for verdict in Verdict:
            with self.subTest(verdict=verdict.value):
                result = CopilotReviewResult(verdict, "auto")
                self.assertEqual(result.blocked, verdict not in PASS_VERDICTS)
                self.assertEqual(result.exit_code, 0 if verdict in PASS_VERDICTS else 1)


class BodyFindingContractConstantTests(unittest.TestCase):
    """Structural contract checks for the body-finding constants and dataclass defaults."""

    def test_trusted_disposition_associations_is_the_contract_set(self) -> None:
        self.assertEqual(
            TRUSTED_DISPOSITION_ASSOCIATIONS, frozenset({"OWNER", "MEMBER", "COLLABORATOR"})
        )

    def test_review_record_body_fields_default_to_empty(self) -> None:
        record = ReviewRecord(state="COMMENTED", commit_oid=_HEAD)
        self.assertIsNone(record.database_id)
        self.assertEqual(record.body_findings, 0)
        self.assertIsNone(record.overview_version)


if __name__ == "__main__":
    unittest.main()
