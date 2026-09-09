"""Hermetic tests for ``build_support.pypi_probe`` (task 152.002-T).

All cases are hermetic (binding H4): every ``urllib.request.urlopen`` call is
patched with an injected fake response or a raised error, and no test
performs network I/O.

Sequencing note (plan H5, binding): this test module is written FIRST,
against the extraction task's (152.002-T) behaviour-preserving helper, which
mirrors the pre-fix ``.github/workflows/release.yml`` ``else:`` branch (any
successful response is treated as "present" without validating response host
or body). At that point, C2, C4, C5, and C6 below are EXPECTED TO FAIL (red)
-- observed and recorded in the task 152.002-T commit -- because the pre-fix
helper never distinguishes a legitimate "present" response from a wrong-host
redirect, a malformed body, or a mismatched version, and its CLI wrapper
exits 0 in all of those cases. Task 152.001-T then changes the helper's
behavioural contract (host + body identity validation, and the CLI's
PRESENT -> exit 2 mapping), which turns C2, C4, C5, and C6 green without any
change to this test module.
"""

from __future__ import annotations

import contextlib
import io
import json
import unittest
import urllib.error

from _env_patch import patched_environ

from build_support.pypi_probe import (
    ProbeIntegrityError,
    ProbeResult,
    ProbeStatus,
    ProbeTransportError,
    already_published_message,
    main,
    probe,
)

REQUESTED_VERSION = "1.2.3"
MISMATCHED_VERSION = "9.9.9"
PROBE_URL = f"https://pypi.org/pypi/autoharness/{REQUESTED_VERSION}/json"


class _FakeHTTPResponse:
    """A minimal stand-in for the object ``urllib.request.urlopen`` returns.

    Supports the calls ``probe()`` makes on a successful response:
    ``.status`` for the HTTP status code, ``.geturl()`` for the final
    resolved URL after redirects, and ``.read()`` for the body. ``.read()``
    raises ``AssertionError`` when ``forbid_read=True`` so tests can prove
    the host/status checks reject a response *before* the body is ever
    consumed (task 152.001-T review finding: host validated before body
    read).
    """

    def __init__(
        self,
        body: bytes,
        url: str = PROBE_URL,
        status: int = 200,
        forbid_read: bool = False,
    ) -> None:
        self._body = body
        self._url = url
        self.status = status
        self._forbid_read = forbid_read

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def read(self) -> bytes:
        if self._forbid_read:
            raise AssertionError(
                "response.read() must not be called before the host/status "
                "checks reject an untrusted response"
            )
        return self._body

    def geturl(self) -> str:
        return self._url


def _json_body(version: str) -> bytes:
    return json.dumps({"info": {"version": version}}).encode("utf-8")


class _PatchedUrlopen:
    """Context manager that patches ``build_support.pypi_probe``'s
    ``urllib.request.urlopen`` to return a fixed value or raise a fixed
    exception, restoring the original afterward. Records every URL the
    patched ``urlopen`` was called with in ``requested_urls`` so tests can
    assert the probe requests the exact-version endpoint (binding H2b)."""

    def __init__(self, *, result=None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self._original = None
        self.requested_urls: list[str] = []

    def __enter__(self) -> "_PatchedUrlopen":
        import build_support.pypi_probe as module

        self._original = module.urllib.request.urlopen

        def _fake_urlopen(url, *args, **kwargs):
            self.requested_urls.append(url)
            if self._error is not None:
                raise self._error
            return self._result

        module.urllib.request.urlopen = _fake_urlopen
        return self

    def __exit__(self, *exc_info: object) -> bool:
        import build_support.pypi_probe as module

        module.urllib.request.urlopen = self._original
        return False


class ProbeCaseTableTests(unittest.TestCase):
    """The six hermetic cases from the plan's case table."""

    def test_c1_http_404_proceeds_absent(self) -> None:
        error = urllib.error.HTTPError(PROBE_URL, 404, "Not Found", {}, None)
        with _PatchedUrlopen(error=error):
            result = probe(REQUESTED_VERSION)
        self.assertEqual(result, ProbeResult(status=ProbeStatus.ABSENT, version=REQUESTED_VERSION))

    def test_c2_present_matching_version_is_present(self) -> None:
        response = _FakeHTTPResponse(_json_body(REQUESTED_VERSION))
        with _PatchedUrlopen(result=response):
            result = probe(REQUESTED_VERSION)
        self.assertEqual(result, ProbeResult(status=ProbeStatus.PRESENT, version=REQUESTED_VERSION))

    def test_probe_requests_exact_version_endpoint_url(self) -> None:
        """Binding H2b: ``probe()`` must query the EXACT-VERSION PyPI
        endpoint for the requested version, not a latest-version or
        wrong-package endpoint. The fake previously accepted the requested
        URL but discarded it, so a production regression pointing at the
        wrong endpoint would leave every injected-response case green;
        record the URL the patched ``urlopen`` was actually called with
        and assert it matches the documented exact-version endpoint."""
        response = _FakeHTTPResponse(_json_body(REQUESTED_VERSION))
        with _PatchedUrlopen(result=response) as patched:
            probe(REQUESTED_VERSION)
        self.assertEqual(patched.requested_urls, [PROBE_URL])

    def test_non_200_success_status_raises_transport_error_not_present(self) -> None:
        """The documented exact-version contract permits only 200 or 404
        from this endpoint (binding H2a/H2b). ``urlopen`` does not raise
        ``HTTPError`` for other 2xx statuses, so a 203/206 response with an
        otherwise-matching body must not be classified ``PRESENT`` -- it is
        a transport/integrity anomaly."""
        response = _FakeHTTPResponse(_json_body(REQUESTED_VERSION), status=203)
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_wrong_host_response_rejected_before_body_is_read(self) -> None:
        """The host check must run *before* ``response.read()`` -- reading
        first would let an untrusted host stream an arbitrarily large or
        non-terminating body into the process before rejection. The fake
        response raises ``AssertionError`` from ``.read()`` when
        ``forbid_read=True``, so this test fails loudly (rather than just
        raising the wrong exception type) if the ordering regresses."""
        response = _FakeHTTPResponse(
            _json_body(REQUESTED_VERSION),
            url=f"https://mirror.example.com/pypi/autoharness/{REQUESTED_VERSION}/json",
            forbid_read=True,
        )
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_non_200_status_response_rejected_before_body_is_read(self) -> None:
        """As above, for the status check: a non-200 status from the
        trusted host must be rejected before the body is consumed."""
        response = _FakeHTTPResponse(
            _json_body(REQUESTED_VERSION),
            status=203,
            forbid_read=True,
        )
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_c3_url_error_propagates(self) -> None:
        error = urllib.error.URLError("connection refused")
        with _PatchedUrlopen(error=error):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_c4_wrong_host_redirect_raises_transport_error(self) -> None:
        """A 200 whose FINAL resolved URL host is not pypi.org (e.g. a
        mirror or an interception proxy) must be re-raised as a transport
        error, never reported as "present". Asserted on the final response
        URL after redirects, not the requested URL."""
        response = _FakeHTTPResponse(
            _json_body(REQUESTED_VERSION),
            url=f"https://mirror.example.com/pypi/autoharness/{REQUESTED_VERSION}/json",
        )
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_c4_wrong_host_404_raises_transport_error_not_absent(self) -> None:
        """A 404 whose OWN resolved URL host (after redirects) is not
        pypi.org must never be accepted as proof of absence: ``urlopen``
        follows redirects transparently, so a redirect to a different host
        that itself returns 404 is a transport anomaly, not evidence the
        version is absent from PyPI (binding H2a). Must raise
        ``ProbeTransportError`` and must NOT return ``ABSENT``."""
        error = urllib.error.HTTPError(
            f"https://mirror.example.com/pypi/autoharness/{REQUESTED_VERSION}/json",
            404,
            "Not Found",
            {},
            None,
        )
        with _PatchedUrlopen(error=error):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_c5_undecodable_body_raises_transport_error(self) -> None:
        response = _FakeHTTPResponse(b"\xff\xfe not valid json or utf-8 \x00")
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_c5_valid_json_missing_info_version_raises_transport_error(self) -> None:
        response = _FakeHTTPResponse(json.dumps({"info": {}}).encode("utf-8"))
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)

    def test_c6_mismatched_version_raises_integrity_error(self) -> None:
        """The exact-version endpoint can only return 404 or a body
        identifying the requested version; a 200 naming a DIFFERENT version
        is a protocol-violating response and is positive evidence of a
        cache, mirror, or interception anomaly -- not evidence of absence.
        Must raise, must NOT return PRESENT, and must NOT be treated as
        absent (binding H2b)."""
        response = _FakeHTTPResponse(_json_body(MISMATCHED_VERSION))
        with _PatchedUrlopen(result=response):
            with self.assertRaises(ProbeIntegrityError):
                probe(REQUESTED_VERSION)


class ExceptionOrderingTests(unittest.TestCase):
    def test_http_error_is_caught_before_url_error(self) -> None:
        """``urllib.error.HTTPError`` is a subclass of ``URLError``. If the
        ``URLError`` clause were checked first, it would swallow every 404
        and every non-404 HTTP error, reporting them all as transport
        failures. A 404 must reach the C1 (absent/proceed) outcome, never
        the C3 (transport error) outcome."""
        self.assertTrue(issubclass(urllib.error.HTTPError, urllib.error.URLError))
        error = urllib.error.HTTPError(PROBE_URL, 404, "Not Found", {}, None)
        with _PatchedUrlopen(error=error):
            result = probe(REQUESTED_VERSION)
        self.assertEqual(result.status, ProbeStatus.ABSENT)

    def test_non_404_http_error_raises_transport_error_not_swallowed(self) -> None:
        error = urllib.error.HTTPError(PROBE_URL, 500, "Server Error", {}, None)
        with _PatchedUrlopen(error=error):
            with self.assertRaises(ProbeTransportError):
                probe(REQUESTED_VERSION)


class AlreadyPublishedMessageTests(unittest.TestCase):
    def test_message_names_bump_and_retag_and_out_of_band_remedies(self) -> None:
        message = already_published_message(REQUESTED_VERSION)
        self.assertIn(REQUESTED_VERSION, message)
        self.assertIn("bump", message.lower())
        self.assertIn("re-tag", message.lower())
        self.assertIn("out of band", message.lower())

    def test_message_does_not_instruct_rerunning_post_publish_jobs(self) -> None:
        """Plan review finding 1 (P0): ``.github/workflows/release.yml``
        declares exactly one job, so "re-run only the post-publish jobs" is
        not an available remedy and must never appear in the message."""
        message = already_published_message(REQUESTED_VERSION).lower()
        self.assertNotIn("re-run post-publish", message)
        self.assertNotIn("rerun post-publish", message)
        self.assertNotIn("re-run only the post-publish jobs", message)


class CliExitCodeMappingTests(unittest.TestCase):
    """One case per exit code asserting the CLI mapping -- no test should
    have to guess whether a row means "raises" or "exits"."""

    def test_cli_exit_code_zero_for_absent(self) -> None:
        error = urllib.error.HTTPError(PROBE_URL, 404, "Not Found", {}, None)
        with _PatchedUrlopen(error=error), patched_environ(VERSION=REQUESTED_VERSION):
            exit_code = main()
        self.assertEqual(exit_code, 0)

    def test_cli_exit_code_two_for_present_with_remedy_message(self) -> None:
        """The name promises a remedy message, so this must assert the
        message content on stderr -- not just the exit code. A regression
        that removed the message, or emitted it to stdout instead of
        stderr, would previously stay green here."""
        response = _FakeHTTPResponse(_json_body(REQUESTED_VERSION))
        captured_stderr = io.StringIO()
        with (
            _PatchedUrlopen(result=response),
            patched_environ(VERSION=REQUESTED_VERSION),
            contextlib.redirect_stderr(captured_stderr),
        ):
            exit_code = main()
        self.assertEqual(exit_code, 2)
        stderr_text = captured_stderr.getvalue()
        self.assertIn(REQUESTED_VERSION, stderr_text)
        self.assertIn("bump", stderr_text.lower())
        self.assertIn("re-tag", stderr_text.lower())

    def test_cli_exit_code_one_for_transport_error(self) -> None:
        error = urllib.error.URLError("connection refused")
        with _PatchedUrlopen(error=error), patched_environ(VERSION=REQUESTED_VERSION):
            exit_code = main()
        self.assertEqual(exit_code, 1)

    def test_cli_exit_code_one_for_integrity_error(self) -> None:
        response = _FakeHTTPResponse(_json_body(MISMATCHED_VERSION))
        with _PatchedUrlopen(result=response), patched_environ(VERSION=REQUESTED_VERSION):
            exit_code = main()
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()
