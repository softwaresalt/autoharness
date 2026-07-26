"""Byte-lossless codec for the local store (088.001-T).

Uses UTF-8 with ``errors="surrogatepass"`` — NOT ``errors="replace"`` — so
strings containing lone/unpaired surrogates (as can occur in tool JSON that
embedded non-round-trippable text) encode and decode back to the exact
original string, byte for byte. ``errors="replace"`` would silently corrupt
such input by substituting U+FFFD, which is exactly the defect 086-F flagged
and this experiment must not repeat.
"""

_CODEC_ERRORS = "surrogatepass"


def encode_lossless(text: str) -> bytes:
    """Encode ``text`` to bytes without lossy substitution."""
    return text.encode("utf-8", errors=_CODEC_ERRORS)


def decode_lossless(data: bytes) -> str:
    """Decode ``data`` back to the exact original string."""
    return data.decode("utf-8", errors=_CODEC_ERRORS)
