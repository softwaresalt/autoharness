"""Cheap fallback token estimator (088.005-T).

Used when no model tokenizer is importable/available. Deliberately simple
and dependency-free: approximates GPT-family tokenization at roughly 4
characters per token, which is a widely used rule-of-thumb approximation
for English/code-mixed text. This is a fallback, not a substitute for a
real tokenizer — callers should prefer a model tokenizer when available.
"""

import math

#: Rough characters-per-token ratio for a cheap, dependency-free estimate.
_CHARS_PER_TOKEN = 4.0


def estimate_tokens(text: str) -> int:
    """Return a deterministic, cheap token-count estimate for ``text``."""
    if not text:
        return 0
    return max(1, math.ceil(len(text) / _CHARS_PER_TOKEN))
