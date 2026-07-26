"""Tests for the secret/PII pre-screen (088.002-T).

A detector hit MUST force decline before any durable write (decide-then-stash
hard invariant, plan hardening §Secret screening precedes durable storage).
"""

from brainspace.secret_screen import contains_secret


def test_detects_aws_access_key():
    text = "some log line\nAKIAABCDEFGHIJKLMNOP\nmore log"
    assert contains_secret(text) is True


def test_detects_github_token():
    text = "auth header: ghp_" + "a" * 36
    assert contains_secret(text) is True


def test_detects_fine_grained_github_pat():
    text = "auth header: github_pat_11ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghij"
    assert contains_secret(text) is True


def test_detects_private_key_header():
    text = "-----BEGIN RSA PRIVATE KEY-----\nMIIB...\n-----END RSA PRIVATE KEY-----"
    assert contains_secret(text) is True


def test_detects_dotenv_style_secret_assignment():
    text = "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwxyz1234567890ABCD"
    assert contains_secret(text) is True


def test_detects_generic_bearer_token():
    text = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.payload.sig"
    assert contains_secret(text) is True


def test_plain_prose_is_not_flagged():
    text = "The build succeeded and all 42 tests passed in 3.2 seconds."
    assert contains_secret(text) is False


def test_plain_json_without_secrets_is_not_flagged():
    text = '{"status": "ok", "count": 42, "items": ["a", "b", "c"]}'
    assert contains_secret(text) is False
