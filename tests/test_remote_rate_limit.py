"""Tests for autoharness.remote.rate_limit -- the token-bucket rate limiter
backing the Plan 2 V1 protocol's 30 req/min, burst-5 security requirement
(exercised as contract tests from 121.002-T/121.008-T's harness scope).
"""

from __future__ import annotations

import unittest

from autoharness.remote.errors import RateLimitExceededError
from autoharness.remote.rate_limit import TokenBucketRateLimiter


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class BurstCapacityTests(unittest.TestCase):
    def test_burst_of_five_succeeds_then_sixth_is_rejected(self) -> None:
        clock = _FakeClock()
        limiter = TokenBucketRateLimiter(capacity=5, refill_per_minute=30, clock=clock)
        for _ in range(5):
            limiter.acquire()  # must not raise
        with self.assertRaises(RateLimitExceededError):
            limiter.acquire()

    def test_default_construction_matches_security_requirement(self) -> None:
        limiter = TokenBucketRateLimiter()
        self.assertEqual(limiter.capacity, 5)
        self.assertEqual(limiter.refill_per_minute, 30)


class RefillTests(unittest.TestCase):
    def test_tokens_refill_over_time_at_the_declared_rate(self) -> None:
        clock = _FakeClock()
        limiter = TokenBucketRateLimiter(capacity=5, refill_per_minute=30, clock=clock)
        for _ in range(5):
            limiter.acquire()
        with self.assertRaises(RateLimitExceededError):
            limiter.acquire()

        # 30/min == 0.5 tokens/sec; after 2 seconds exactly one token refills.
        clock.advance(2.0)
        limiter.acquire()  # must not raise
        with self.assertRaises(RateLimitExceededError):
            limiter.acquire()

    def test_refill_never_exceeds_capacity(self) -> None:
        clock = _FakeClock()
        limiter = TokenBucketRateLimiter(capacity=5, refill_per_minute=30, clock=clock)
        clock.advance(10_000.0)  # a very long idle period
        for _ in range(5):
            limiter.acquire()  # must not raise -- still capped at capacity
        with self.assertRaises(RateLimitExceededError):
            limiter.acquire()


class NoQueueingFailClosedTests(unittest.TestCase):
    def test_exceeding_the_limit_raises_immediately_rather_than_blocking(self) -> None:
        """The rate limiter must never block/queue a caller -- it fails
        closed immediately, per the design doc's backpressure requirement
        that a slow/aggressive remote consumer never stalls the local
        session."""

        clock = _FakeClock()
        limiter = TokenBucketRateLimiter(capacity=1, refill_per_minute=30, clock=clock)
        limiter.acquire()
        start = clock.now
        with self.assertRaises(RateLimitExceededError):
            limiter.acquire()
        self.assertEqual(clock.now, start)  # no time passed -- no internal sleep/wait


if __name__ == "__main__":
    unittest.main()
