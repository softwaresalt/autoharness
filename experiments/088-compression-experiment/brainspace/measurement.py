"""AUC token-savings measurement harness (088.005-T).

Single concern: measurement only. Given an (original, compressed_view,
footer) triple already produced by the hook/compressor, compute raw vs
compressed token counts under a model tokenizer when available (else the
cheap fallback estimator), and project net savings (after subtracting
placeholder + retrieval-footer overhead) over a fixed set of re-send turns.

This module does NOT orchestrate benchmarks and does NOT know about hook
internals — it is a pure function of three strings.
"""

from dataclasses import dataclass, field

from brainspace import config
from brainspace.tokenizer_fallback import estimate_tokens

#: Turn counts over which AUC-style projected savings are reported. The
#: model is assumed to re-send/re-read the same tool output each turn, so
#: projected savings scale linearly with turn count (a deliberately simple
#: AUC proxy — not a full decay/attention model).
PROJECTION_TURNS = (1, 3, 5, 10)


def _load_model_tokenizer():
    """Return a callable ``text -> int`` model tokenizer, or ``None``.

    Attempts an optional import of ``tiktoken``. No new dependency is added
    to the project — if ``tiktoken`` is not installed, this returns
    ``None`` and callers fall back to the cheap estimator. This keeps the
    experiment's declared "no new pip dependencies" constraint intact.
    """
    try:
        import tiktoken  # type: ignore
    except ImportError:
        return None

    try:
        encoding = tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None

    return lambda text: len(encoding.encode(text))


class ModelTokenizerUnavailable(Exception):
    """Raised when a real model tokenizer cannot be used to prove a token
    count for a specific text -- either because no tokenizer is importable,
    or because the tokenizer's own ``encode()`` call failed for this exact
    input (P-018 round-8 finding)."""


def count_tokens(text: str) -> int:
    """Count tokens in ``text`` using a model tokenizer if available."""
    if not text:
        return 0
    tokenizer = _load_model_tokenizer()
    if tokenizer is None:
        return estimate_tokens(text)
    try:
        return tokenizer(text)
    except Exception:
        return estimate_tokens(text)


def count_tokens_strict(text: str) -> int:
    """Count tokens using ONLY the real model tokenizer -- never falls back.

    Raises :class:`ModelTokenizerUnavailable` if no model tokenizer is
    importable/usable, or if the tokenizer's own ``encode()`` call fails for
    this specific text. ``is_model_tokenizer_available()`` only proves the
    tokenizer *loaded* successfully (``tiktoken.get_encoding(...)``
    succeeded) -- it does NOT prove ``encode()`` will succeed for every
    possible input. Callers that must PROVE an actual real-model token
    count was used to authorize a decision (e.g. the hook's never-expand
    guard) must use this, not :func:`count_tokens`, or a per-call encode
    failure on the actual input could be silently masked by the fallback
    estimator while the caller believes a real-model comparison was proven.
    """
    if not text:
        return 0
    tokenizer = _load_model_tokenizer()
    if tokenizer is None:
        raise ModelTokenizerUnavailable("no model tokenizer is available")
    try:
        return tokenizer(text)
    except Exception as exc:
        raise ModelTokenizerUnavailable(
            f"model tokenizer failed to encode this input: {exc}"
        ) from exc


def is_model_tokenizer_available() -> bool:
    """Return ``True`` if a real model tokenizer (e.g. ``tiktoken``) is
    importable and usable in this environment.

    Callers that must PROVE an actual token-count reduction (not merely
    estimate one) use this to distinguish "no real tokenizer to prove
    savings with" from "a real tokenizer was consulted and showed no
    savings" -- the two are not the same claim (P-018 round-6 finding).
    """
    return _load_model_tokenizer() is not None


@dataclass
class MeasurementResult:
    raw_tokens: int
    compressed_tokens: int
    net_savings_tokens: int
    projected_savings_by_turn: dict = field(default_factory=dict)
    exceeds_additional_context_cap: bool = False
    is_safe_win: bool = False


def measure(
    original: str, compressed_view: str, footer: str, token_counter=None
) -> MeasurementResult:
    """Measure raw vs compressed tokens and project net AUC savings.

    ``compressed_view`` and ``footer`` are measured together (the
    additionalContext actually sent to the model is the compressed view
    plus the retrieval footer), and compared against the raw original.

    ``token_counter`` optionally overrides the token-counting function
    (defaults to :func:`count_tokens`). The benchmark runner uses this to
    force a specific tokenizer so it can prove "lower tokens under both
    tokenizers" (spike proof-method criterion 1) rather than whichever one
    :func:`count_tokens` happens to pick.
    """
    counter = token_counter or count_tokens
    additional_context = compressed_view + footer
    raw_tokens = counter(original)
    compressed_tokens = counter(additional_context)
    net_savings_tokens = raw_tokens - compressed_tokens

    exceeds_cap = len(additional_context.encode("utf-8", errors="surrogatepass")) > (
        config.ADDITIONAL_CONTEXT_CAP_BYTES
    )

    projected = {
        turns: net_savings_tokens * turns for turns in PROJECTION_TURNS
    }

    is_safe_win = net_savings_tokens > 0 and not exceeds_cap

    return MeasurementResult(
        raw_tokens=raw_tokens,
        compressed_tokens=compressed_tokens,
        net_savings_tokens=net_savings_tokens,
        projected_savings_by_turn=projected,
        exceeds_additional_context_cap=exceeds_cap,
        is_safe_win=is_safe_win,
    )


def measure_dual(original: str, compressed_view: str, footer: str) -> dict:
    """Measure under BOTH the cheap fallback estimator and the model
    tokenizer (when available), so callers can prove lower-tokens-under-
    both-tokenizers independently of whichever one :func:`count_tokens`
    would have auto-selected.

    Returns ``{"fallback": MeasurementResult, "model": MeasurementResult | None}``.
    ``model`` is ``None`` when no model tokenizer is importable/available —
    callers must report this honestly rather than silently substituting
    the fallback result as if it were the model result.
    """
    fallback_result = measure(
        original, compressed_view, footer, token_counter=estimate_tokens
    )
    model_tokenizer = _load_model_tokenizer()
    model_result = None
    if model_tokenizer is not None:
        try:
            model_result = measure(
                original, compressed_view, footer, token_counter=model_tokenizer
            )
        except Exception:
            # A tokenizer that loaded successfully can still raise on a
            # specific input's encode() call -- that must be reported
            # honestly as "no model result" (P-018 round-8 finding), not
            # silently substituted with the fallback estimator's numbers or
            # allowed to crash the caller.
            model_result = None
    return {"fallback": fallback_result, "model": model_result}
