"""Tests for the byte-lossless codec (088.001-T).

Must NOT use UTF-8 errors="replace" — lone/unpaired surrogates and other
non-round-trippable text (as can appear in raw tool JSON) must recover
exactly, byte for byte.
"""

from brainspace.codec import decode_lossless, encode_lossless


def test_round_trip_plain_ascii():
    text = "hello world\nline two\ttab"
    assert decode_lossless(encode_lossless(text)) == text


def test_round_trip_unicode():
    text = "café — 日本語 — emoji 🎉"
    assert decode_lossless(encode_lossless(text)) == text


def test_round_trip_lone_surrogate():
    # A lone high surrogate, as can appear in malformed/truncated JSON
    # decoded with surrogatepass by an upstream tool. Plain UTF-8 encoding
    # (errors="strict") raises; errors="replace" silently corrupts data.
    # The codec must recover it exactly.
    text = "before\ud800after"
    encoded = encode_lossless(text)
    assert decode_lossless(encoded) == text


def test_round_trip_unpaired_low_surrogate():
    text = "x\udc00y"
    assert decode_lossless(encode_lossless(text)) == text


def test_encode_returns_bytes():
    assert isinstance(encode_lossless("abc"), bytes)


def test_round_trip_empty_string():
    assert decode_lossless(encode_lossless("")) == ""


def test_encode_does_not_use_replace_semantics():
    # errors="replace" would turn a lone surrogate into U+FFFD on encode,
    # which is detectable because decode would then differ from the input.
    text = "\ud83d"  # lone high surrogate half of an emoji pair
    encoded = encode_lossless(text)
    decoded = decode_lossless(encoded)
    assert decoded == text
    assert "\ufffd" not in decoded
