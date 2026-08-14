"""Plan 2 V1 token-bucket rate limiter (121.002-T/121.008-T).

Enforces the security requirement of 30 requests/minute with a burst of 5.
The limiter never blocks or queues a caller: it either grants a token
immediately or raises :class:`RateLimitExceededError` immediately. This is
deliberate -- a slow or aggressive remote consumer must never stall the
locally supervised session (see the design doc's backpressure
requirements).
"""

from __future__ import annotations

import time
from typing import Callable

from autoharness.remote.contracts import RATE_LIMIT_BURST, RATE_LIMIT_PER_MINUTE
from autoharness.remote.errors import RateLimitExceededError


class TokenBucketRateLimiter:
    """A simple, non-blocking token-bucket rate limiter.

    ``clock`` is injectable (defaults to :func:`time.monotonic`) so tests
    can drive refill deterministically without real sleeps.
    """

    def __init__(
        self,
        capacity: int = RATE_LIMIT_BURST,
        refill_per_minute: int = RATE_LIMIT_PER_MINUTE,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.capacity = capacity
        self.refill_per_minute = refill_per_minute
        self._clock = clock
        self._tokens: float = float(capacity)
        self._refill_rate_per_second = refill_per_minute / 60.0
        self._last_refill = clock()

    def _refill(self) -> None:
        now = self._clock()
        elapsed = now - self._last_refill
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self._refill_rate_per_second)
            self._last_refill = now

    def acquire(self) -> None:
        """Consume a single token, or fail closed immediately.

        Raises:
            RateLimitExceededError: no token is currently available. This
                never blocks/sleeps -- the caller must fail closed rather
                than stall.
        """

        self._refill()
        if self._tokens < 1.0:
            raise RateLimitExceededError(
                "Plan 2 remote rate limit exceeded "
                f"({self.refill_per_minute} req/min, burst {self.capacity})"
            )
        self._tokens -= 1.0
