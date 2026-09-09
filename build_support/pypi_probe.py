"""Pre-publish PyPI probe for the release workflow.

Extracted from the inline ``python - <<'PY'`` heredoc previously embedded in
``.github/workflows/release.yml`` (task 152.002-T) so the probe logic is
importable and testable -- an inline heredoc in YAML is untestable by
construction.

Task 152.001-T (this task) changes the extracted helper's behavioural
contract to fail closed on an already-published version: "present" now
requires the final resolved response host to be ``pypi.org``, the response
HTTP status to be exactly 200, the body to decode as JSON, and the decoded
body to identify the requested version (binding H2a). Host and status are
validated before the response body is read, so an untrusted host cannot
stream an arbitrary body into the process before being rejected. A
response that decodes cleanly but names a *different* version is an
integrity anomaly, not evidence of absence, because the exact-version
endpoint queried here can only conform by returning 404 or a body naming
that exact version (binding H2b). See
``docs/plans/2026-08-31-ship2-release-ci-fail-closed-gates-plan.md`` for the
full rationale.

Invoked from ``release.yml`` as ``python -m build_support.pypi_probe``, with
the version supplied through the ``VERSION`` environment variable the
surrounding workflow step already sets.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlsplit

PYPI_HOST = "pypi.org"


class ProbeStatus(Enum):
    """The two non-error outcomes the probe can report."""

    ABSENT = "absent"
    PRESENT = "present"


@dataclass(frozen=True)
class ProbeResult:
    """The probe's typed, non-error return value."""

    status: ProbeStatus
    version: str


class ProbeError(Exception):
    """Common base for the probe's two named error outcomes."""


class ProbeIntegrityError(ProbeError):
    """A well-formed HTTP response whose content is wrong.

    Raised for a response that decoded successfully but identifies a
    different version than the one requested (task 152.001-T, binding H2b).
    """


class ProbeTransportError(ProbeError):
    """A transport-level failure.

    Raised for ``URLError``, non-404 ``HTTPError``, a successful response
    resolved to a host other than ``pypi.org`` after redirects, a
    successful-transport response whose HTTP status is not exactly 200, or
    a response body that cannot be decoded/does not have the expected shape
    (task 152.001-T, binding H2/H2a).
    """


def probe(version: str, url: str | None = None) -> ProbeResult:
    """Query PyPI's exact-version JSON endpoint for ``version``.

    Returns ``ProbeResult(status=ABSENT)`` on a 404 -- but only when that
    404's own resolved response host (after redirects) is ``pypi.org``
    (binding H2a); a redirect to a different host that itself returns 404
    is a transport anomaly, not proof of absence, and raises
    ``ProbeTransportError`` instead. Returns ``ProbeResult(status=PRESENT)``
    only when ALL of the following hold (binding H2a): the final resolved
    response host (after redirects) is ``pypi.org``; the response's HTTP
    status is exactly 200 (a non-200 successful-transport status such as
    203/206 is a transport anomaly, not "present" -- the documented
    exact-version contract permits only 200 or 404 from this endpoint); the
    body decodes as JSON; the decoded body identifies the requested
    version. The host and status checks run *before* the response body is
    read, so an untrusted host cannot stream an arbitrary body into the
    process before being rejected. Raises ``ProbeTransportError`` for a
    transport ``URLError``, a non-404 HTTP error, a response (or 404 error)
    resolved to a host other than ``pypi.org``, a non-200 status on an
    otherwise-successful response, or a body that cannot be decoded / lacks
    ``info.version``. Raises ``ProbeIntegrityError`` when the decoded body
    identifies a version different from the one requested -- the
    exact-version endpoint queried here can only conform by returning 404 or
    a body naming that exact version, so a mismatch is positive evidence of
    a cache, mirror, or interception anomaly, never evidence of absence
    (binding H2b). Absence is proved by a pypi.org-hosted 404 and nothing
    else.
    """
    if url is None:
        url = f"https://pypi.org/pypi/autoharness/{version}/json"

    try:
        with urllib.request.urlopen(url) as response:
            final_url = response.geturl()
            final_host = urlsplit(final_url).hostname
            if final_host != PYPI_HOST:
                # Validate the resolved host *before* consuming the body:
                # a wrong-host redirect is exactly the untrusted-response
                # case this check exists to reject, and reading the body
                # first would let that untrusted host stream an
                # arbitrarily large or non-terminating response into the
                # runner before rejection.
                raise ProbeTransportError(
                    f"PyPI probe response resolved to unexpected host "
                    f"{final_host!r} (expected {PYPI_HOST!r}); final URL: "
                    f"{final_url}"
                )
            status = response.status
            if status != 200:
                # The documented exact-version contract permits only 200
                # or 404 from this endpoint (binding H2a/H2b); any other
                # successful-transport status (e.g. 203, 206) is an
                # integrity/transport anomaly, never "present".
                raise ProbeTransportError(
                    f"PyPI probe response from {PYPI_HOST!r} returned "
                    f"unexpected HTTP status {status!r} (expected 200); "
                    f"final URL: {final_url}"
                )
            body_bytes = response.read()
    except urllib.error.HTTPError as exc:
        # HTTPError is caught before URLError: HTTPError is a subclass of
        # URLError, so if the URLError clause were checked first it would
        # swallow every 404 and every non-404 HTTP error and report them all
        # as transport failures, silently defeating the 404/non-404
        # distinction below.
        if exc.code == 404:
            # A 404 is only proof of absence if it actually came from
            # pypi.org. ``urlopen`` follows redirects transparently, so a
            # redirect to a different host that itself returns 404 must
            # not be accepted as absence (binding H2a) -- validate the
            # error's resolved URL host exactly as the success path above
            # validates ``response.geturl()``.
            error_host = urlsplit(exc.geturl()).hostname
            if error_host != PYPI_HOST:
                raise ProbeTransportError(
                    f"PyPI probe 404 response resolved to unexpected host "
                    f"{error_host!r} (expected {PYPI_HOST!r}); final URL: "
                    f"{exc.geturl()}"
                ) from exc
            return ProbeResult(status=ProbeStatus.ABSENT, version=version)
        raise ProbeTransportError(f"PyPI probe HTTP error {exc.code}: {exc}") from exc
    except urllib.error.URLError as exc:
        raise ProbeTransportError(f"PyPI probe transport error: {exc}") from exc

    try:
        decoded = json.loads(body_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProbeTransportError(f"PyPI probe response body was not valid JSON: {exc}") from exc

    try:
        body_version = decoded["info"]["version"]
    except (KeyError, TypeError) as exc:
        raise ProbeTransportError(
            "PyPI probe response body did not contain info.version"
        ) from exc

    if body_version != version:
        raise ProbeIntegrityError(
            f"PyPI probe requested version {version!r} but response body "
            f"identified version {body_version!r} -- exact-version endpoint "
            "integrity anomaly (cache, mirror, or interception proxy)"
        )

    return ProbeResult(status=ProbeStatus.PRESENT, version=version)


def already_published_message(version: str) -> str:
    """The message printed when the probe reports ``PRESENT``.

    Names the remedies actually available in this workflow's single-job
    structure (task 152.001-T, plan review finding 1): bump and re-tag is the
    only remedy that legitimately re-enters this workflow.
    """
    return (
        f"autoharness {version} is already on PyPI.\n"
        "Remedies:\n"
        "  (R1) Bump the version and re-tag -- the primary supported remedy.\n"
        "  (R2) If the upload already succeeded and only a later step"
        " failed, complete the remaining post-publish work out of band"
        " (for example, `gh release create` against the already-published"
        " artifacts) rather than re-running this job.\n"
        "  (R3) Never disable or bypass this gate."
    )


def main(argv: list[str] | None = None) -> int:
    """Thin CLI wrapper: no probe logic lives here.

    Mapping: ``ABSENT`` -> exit 0; ``PRESENT`` -> exit 2 (the fail-closed
    outcome, deliberately distinct from an error exit so an operator can
    tell "already published" from "the probe itself broke"), with the
    remedy message on stderr; ``ProbeError`` (``ProbeIntegrityError`` or
    ``ProbeTransportError``) -> exit 1, message on stderr.
    """
    del argv  # No CLI arguments; the version comes from the VERSION env var.
    version = os.environ["VERSION"]

    try:
        result = probe(version)
    except ProbeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if result.status is ProbeStatus.ABSENT:
        print(f"autoharness {version} not yet on PyPI.")
        return 0

    print(already_published_message(version), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
