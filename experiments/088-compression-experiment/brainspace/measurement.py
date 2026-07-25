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


@dataclass
class MeasurementResult:
    raw_tokens: int
    compressed_tokens: int
    net_savings_tokens: int
    projected_savings_by_turn: dict = field(default_factory=dict)
    exceeds_additional_context_cap: bool = False
    is_safe_win: bool = False


def measure(original: str, compressed_view: str, footer: str) -> MeasurementResult:
    """Measure raw vs compressed tokens and project net AUC savings.

    ``compressed_view`` and ``footer`` are measured together (the
    additionalContext actually sent to the model is the compressed view
    plus the retrieval footer), and compared against the raw original.
    """
    additional_context = compressed_view + footer
    raw_tokens = count_tokens(original)
    compressed_tokens = count_tokens(additional_context)
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
