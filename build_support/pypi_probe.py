"""Pre-publish PyPI probe for the release workflow.

Extracted from the inline ``python - <<'PY'`` heredoc previously embedded in
``.github/workflows/release.yml`` (task 152.002-T) so the probe logic is
importable and testable -- an inline heredoc in YAML is untestable by
construction. This extraction is behaviour-preserving: the workflow keeps
calling the probe from the same step, at the same point, with the same
inputs, and this module's initial logic mirrors the pre-fix ``else:`` branch
exactly (any successful HTTP response is treated as "present" without
validating the response host or body). Task 152.001-T changes this module's
behavioural contract to fail closed on an already-published version; see that
task and ``docs/plans/2026-08-31-ship2-release-ci-fail-closed-gates-plan.md``
for the full rationale.

Invoked from ``release.yml`` as ``python -m build_support.pypi_probe``, with
the version supplied through the ``VERSION`` environment variable the
surrounding workflow step already sets.
"""

from __future__ import annotations

import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from enum import Enum

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

    Raised for ``URLError``, non-404 ``HTTPError``, a response resolved to a
    host other than ``pypi.org`` after redirects, or a response body that
    cannot be decoded/does not have the expected shape (task 152.001-T,
    binding H2/H2a).
    """


def probe(version: str, url: str | None = None) -> ProbeResult:
    """Query PyPI's exact-version JSON endpoint for ``version``.

    Pre-fix behaviour (this task, 152.002-T): a 404 means the version is
    absent and the probe proceeds; any other HTTP error or a transport
    ``URLError`` propagates; any successful (2xx) response is treated as
    "present" without further validation of the response host or body --
    this mirrors the pre-fix ``else:`` branch exactly and is intentionally
    fail-open pending task 152.001-T's fix.
    """
    if url is None:
        url = f"https://pypi.org/pypi/autoharness/{version}/json"

    try:
        with urllib.request.urlopen(url) as response:
            response.read()
    except urllib.error.HTTPError as exc:
        # HTTPError is caught before URLError: HTTPError is a subclass of
        # URLError, so if the URLError clause were checked first it would
        # swallow every 404 and every non-404 HTTP error and report them all
        # as transport failures, silently defeating the 404/non-404
        # distinction below.
        if exc.code == 404:
            return ProbeResult(status=ProbeStatus.ABSENT, version=version)
        raise ProbeTransportError(f"PyPI probe HTTP error {exc.code}: {exc}") from exc
    except urllib.error.URLError as exc:
        raise ProbeTransportError(f"PyPI probe transport error: {exc}") from exc

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

    Pre-fix mapping (this task, 152.002-T): ``ABSENT`` -> exit 0; ``PRESENT``
    -> exit 0 (matches the pre-fix workflow's fail-open behaviour, which
    never raised or exited non-zero on a successful response);
    ``ProbeError`` -> exit 1, message on stderr.
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

    print(
        f"autoharness {version} is already on PyPI; "
        "publish will skip existing files on reruns."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
