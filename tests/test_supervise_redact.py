"""Property/randomized tests for autoharness.supervise.redact (118.004-T).

Uses only the stdlib ``random``/``string`` modules (no hypothesis or other
third-party property-testing dependency), per shipment constraints.
"""

from __future__ import annotations

import random
import string
import unittest

from autoharness.supervise.redact import (
    PLACEHOLDER,
    Redactor,
    redact_record,
    register_secret,
)

_TRIALS_PER_CATEGORY = 100
_MIN_SURVIVING_SUBSTRING_LEN = 8

_rng = random.Random(20260812)


def _random_alnum(n: int) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(_rng.choice(alphabet) for _ in range(n))


def _gh_prefixed_token() -> str:
    prefix = "gh" + _rng.choice("pousr") + "_"
    return prefix + _random_alnum(_rng.randint(20, 40))


def _github_pat_token() -> str:
    alphabet = string.ascii_letters + string.digits + "_"
    body = "".join(_rng.choice(alphabet) for _ in range(_rng.randint(20, 40)))
    return "github_pat_" + body


def _arbitrary_registered_secret() -> str:
    # Deliberately avoid the gh*/github_pat_ prefixes so this only ever gets
    # redacted via explicit registration, never via the regex patterns.
    return "sekret-" + "".join(_rng.choice(string.ascii_lowercase) for _ in range(24))


def _assert_no_substring_survives(test: unittest.TestCase, secret: str, haystack: str) -> None:
    for start in range(0, len(secret) - _MIN_SURVIVING_SUBSTRING_LEN + 1):
        chunk = secret[start : start + _MIN_SURVIVING_SUBSTRING_LEN]
        test.assertNotIn(
            chunk,
            haystack,
            f"substring {chunk!r} of secret survived redaction in {haystack!r}",
        )


class GhTokenPatternPropertyTests(unittest.TestCase):
    def test_gh_prefixed_tokens_fully_redacted_in_text_contexts(self) -> None:
        redactor = Redactor()
        for _ in range(_TRIALS_PER_CATEGORY):
            secret = _gh_prefixed_token()
            for context in (
                secret,
                f"Authorization: Bearer {secret}",
                f"export GITHUB_TOKEN={secret}\nsome trailing text",
                f"[{secret}] embedded mid-sentence with {secret} repeated",
            ):
                redacted = redactor.redact_text(context)
                _assert_no_substring_survives(self, secret, redacted)
                self.assertIn(PLACEHOLDER, redacted)

    def test_gh_prefixed_tokens_fully_redacted_in_mapping_contexts(self) -> None:
        redactor = Redactor()
        for _ in range(_TRIALS_PER_CATEGORY):
            secret = _gh_prefixed_token()
            payload = {
                "message": f"resolved token {secret}",
                "nested": {"detail": f"value={secret}"},
                "list": [f"a-{secret}-b", {"inner": secret}],
            }
            redacted = redactor.redact_mapping(payload)
            _assert_no_substring_survives(self, secret, str(redacted))


class GithubPatPatternPropertyTests(unittest.TestCase):
    def test_github_pat_tokens_fully_redacted(self) -> None:
        redactor = Redactor()
        for _ in range(_TRIALS_PER_CATEGORY):
            secret = _github_pat_token()
            for context in (
                secret,
                f"GITHUB_PERSONAL_ACCESS_TOKEN={secret}",
                f"prefix-text {secret} suffix-text",
            ):
                redacted = redactor.redact_text(context)
                _assert_no_substring_survives(self, secret, redacted)


class RegisteredArbitrarySecretPropertyTests(unittest.TestCase):
    def test_registered_arbitrary_values_fully_redacted_despite_no_regex_match(self) -> None:
        for _ in range(_TRIALS_PER_CATEGORY):
            redactor = Redactor()
            secret = _arbitrary_registered_secret()
            redactor.register_secret(secret)

            # Sanity: this value must NOT be caught by either regex pattern,
            # so any redaction observed below is attributable to the
            # explicit registration mechanism, not the pattern set.
            unregistered = Redactor()
            self.assertIn(secret, unregistered.redact_text(f"context {secret} context"))

            for context in (
                secret,
                f"embedded value is {secret} inline",
                f"key=custom_field value={secret}",
            ):
                redacted = redactor.redact_text(context)
                _assert_no_substring_survives(self, secret, redacted)
                self.assertIn(PLACEHOLDER, redacted)

    def test_module_level_register_secret_affects_default_redactor_records(self) -> None:
        secret = _arbitrary_registered_secret()
        register_secret(secret)
        try:
            record, warning = redact_record(f"leaked value {secret} here")
            self.assertIsNone(warning)
            assert record is not None
            _assert_no_substring_survives(self, secret, record)
        finally:
            # Best-effort cleanup: the module-global default redactor has no
            # unregister API by design (secrets, once known-sensitive, stay
            # known-sensitive for the process lifetime), so nothing to undo.
            pass


class KeyNameMatchingTests(unittest.TestCase):
    def test_sensitive_key_names_are_fully_replaced_regardless_of_value_shape(self) -> None:
        redactor = Redactor()
        for _ in range(_TRIALS_PER_CATEGORY // 2):
            secret = _arbitrary_registered_secret()
            for key in ("TOKEN", "api_key", "Secret", "PASSWORD", "auth_token"):
                payload = {key: secret}
                redacted = redactor.redact_mapping(payload)
                self.assertEqual(redacted[key], PLACEHOLDER)


class WholeMatchOnlyTests(unittest.TestCase):
    def test_placeholder_never_reveals_partial_secret_characters(self) -> None:
        redactor = Redactor()
        secret = _gh_prefixed_token()
        redacted = redactor.redact_text(f"token={secret}")
        # The placeholder itself must not contain any part of the secret.
        self.assertNotIn(secret[:8], redacted.replace(PLACEHOLDER, ""))
        self.assertEqual(redacted, f"token={PLACEHOLDER}")


class FailClosedTests(unittest.TestCase):
    def test_unsupported_record_type_is_dropped_with_warning(self) -> None:
        record, warning = redact_record({1, 2, 3})  # a set: neither str nor Mapping

        self.assertIsNone(record)
        self.assertIsNotNone(warning)
        self.assertIn("dropped", warning)

    def test_supported_types_never_return_a_warning_on_success(self) -> None:
        record, warning = redact_record("plain text with no secrets")
        self.assertEqual(record, "plain text with no secrets")
        self.assertIsNone(warning)

        record, warning = redact_record({"note": "value"})
        self.assertEqual(record, {"note": "value"})
        self.assertIsNone(warning)

    def test_dropped_record_never_leaks_original_content_via_return_value(self) -> None:
        original = object()
        record, warning = redact_record(original)  # type: ignore[arg-type]
        self.assertIsNone(record)
        self.assertIsNotNone(warning)


if __name__ == "__main__":
    unittest.main()
