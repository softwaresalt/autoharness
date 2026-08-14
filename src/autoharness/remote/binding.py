"""Plan 2 V1 cryptographic workspace/session binding (121.004-T).

Every remote request must be bound to a specific ``(workspace_root,
session_id)`` pair via an HMAC-derived token. This prevents two classes of
attack called out in the design doc's threat model: workspace confusion
(a token issued for one workspace being replayed against another) and
cross-session command delivery (a stale or foreign session receiving a
command meant for a different session).

:meth:`WorkspaceSessionBinding.verify` is fail-closed and raises exactly
one exception type, :class:`BindingMismatchError`, for every failure mode
-- there is no partial-success path a caller could branch on.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass

from autoharness.remote.contracts import RemoteRequest
from autoharness.remote.errors import BindingMismatchError

DEFAULT_MAX_AGE_SECONDS = 300.0
SECRET_LENGTH_BYTES = 32


def generate_binding_secret() -> bytes:
    """Generate a fresh, cryptographically random 32-byte binding secret."""

    return secrets.token_bytes(SECRET_LENGTH_BYTES)


@dataclass(frozen=True)
class WorkspaceSessionBinding:
    """Binds a workspace root + session id pair to a shared secret.

    ``issue_token()`` derives a deterministic HMAC-SHA256 digest of the
    binding's own ``(workspace_root, session_id)`` -- it never derives from
    request data, so a token issued for workspace A can never validate
    against workspace B's binding by construction.
    """

    workspace_root: str
    session_id: str
    secret: bytes

    def _digest_input(self) -> bytes:
        return f"{self.workspace_root}\x00{self.session_id}".encode("utf-8")

    def issue_token(self) -> str:
        """Return the deterministic binding token for this workspace/session."""

        return hmac.new(self.secret, self._digest_input(), hashlib.sha256).hexdigest()

    def verify(
        self,
        request: RemoteRequest,
        token: str,
        *,
        now: float | None = None,
        max_age_seconds: float = DEFAULT_MAX_AGE_SECONDS,
    ) -> None:
        """Verify ``request`` and ``token`` against this binding.

        Verification order: workspace id match, session id match, token
        presence, constant-time token comparison, then request freshness
        (rejecting both stale and future-dated ``issued_at`` values as
        ambiguous). Every failure mode raises the single
        :class:`BindingMismatchError` type -- there is no partial-success
        return value.
        """

        if now is None:
            now = time.time()

        if not request.workspace_id or request.workspace_id != self.workspace_root:
            raise BindingMismatchError(
                f"request workspace_id {request.workspace_id!r} does not match "
                f"bound workspace_root {self.workspace_root!r}"
            )
        if not request.session_id or request.session_id != self.session_id:
            raise BindingMismatchError(
                f"request session_id {request.session_id!r} does not match "
                f"bound session_id {self.session_id!r}"
            )
        if not token:
            raise BindingMismatchError("no binding token was supplied")

        expected_token = self.issue_token()
        if not hmac.compare_digest(token, expected_token):
            raise BindingMismatchError("binding token does not match this workspace/session")

        if request.issued_at > now:
            raise BindingMismatchError(
                f"request issued_at {request.issued_at!r} is in the future relative to "
                f"now={now!r}; future-dated requests are treated as invalid, not extra-fresh"
            )
        age = now - request.issued_at
        if age > max_age_seconds:
            raise BindingMismatchError(
                f"request is {age:.1f}s old, exceeding the {max_age_seconds:.1f}s freshness window"
            )
