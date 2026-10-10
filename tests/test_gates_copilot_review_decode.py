"""Locale-independent UTF-8 decoding of ``gh`` output for the copilot-review gate.

``gh`` writes JSON as UTF-8 by contract. The gate once used ``subprocess.run(..., text=True)``,
which decodes with the locale codec. On a Windows cp1252 default locale, a review body that
contains a non-BMP character (for example U+1D4B3, whose UTF-8 bytes include 0x9D, undefined in
cp1252) raised UnicodeDecodeError during the subprocess call, which failed closed on every
such PR. The contract row asserts that the gate requests raw bytes, with no text mode. The real-subprocess row drives the
production ``subprocess.run`` path through a fake ``gh`` that emits UTF-8 bytes. Its assertion is
on the parsed outcome, so it holds under any host locale. Malformed bytes must still BLOCK.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from autoharness.gates.copilot_review import Verdict, evaluate, query_pr_review_state
from test_gates_copilot_review import COPILOT_LOGIN, _HEAD, _graphql


def _emoji_payload() -> dict:
    """A Copilot GraphQL response whose review body carries the overview icons, a check mark,
    and a non-BMP character (U+1D4B3, bytes F0 9D 92 B3)."""
    payload = _graphql(head=_HEAD, reviews=((COPILOT_LOGIN, "COMMENTED", _HEAD),))
    body = (
        "<!-- ccr-overview-v2 -->\n"
        "### \U0001F535 Needs a closer look\n\n"
        "**0 open findings** \u2705 \U0001F9E0 \U0001D4B3\n"
    )
    payload["data"]["repository"]["pullRequest"]["reviews"]["nodes"][0]["body"] = body
    return payload


def _fake_gh_script(tmp: Path, stdout_bytes: bytes, *, exit_code: int = 0, stderr: bytes = b"") -> Path:
    """Write a stand-in ``gh`` that emits the given raw bytes, exactly as the real CLI would."""
    payload = tmp / "payload.bin"
    payload.write_bytes(stdout_bytes)
    error_file = tmp / "stderr.bin"
    error_file.write_bytes(stderr)
    script = tmp / "fake_gh.py"
    script.write_text(
        "import sys\nfrom pathlib import Path\n"
        f"sys.stderr.buffer.write(Path({str(error_file)!r}).read_bytes())\n"
        f"sys.stdout.buffer.write(Path({str(payload)!r}).read_bytes())\n"
        f"sys.exit({exit_code})\n",
        encoding="utf-8",
    )
    return script


def _run_via_fake_gh(script: Path):
    """A run_fn that delegates to the real subprocess.run with the kwargs the gate passes.

    The argv is replaced by the fake script, so these rows cover the decode path, not the argv.
    """

    def run(argv, **kwargs):
        return subprocess.run([sys.executable, str(script)], **kwargs)

    return run


class GhOutputDecodingContractTests(unittest.TestCase):
    def test_gate_requests_raw_bytes_and_never_the_locale_text_mode(self) -> None:
        seen: list[dict] = []

        def fake_run(argv, **kwargs):
            seen.append(kwargs)
            body = json.dumps(_emoji_payload(), ensure_ascii=False).encode("utf-8")
            return type("P", (), {"returncode": 0, "stdout": body, "stderr": b""})()

        state = query_pr_review_state(7, "owner/name", run_fn=fake_run)
        self.assertEqual(state.head_ref_oid, _HEAD)
        kwargs = seen[0]
        self.assertFalse(kwargs.get("text", False), "text=True decodes with the locale codec")
        self.assertFalse(kwargs.get("universal_newlines", False))
        self.assertNotIn("encoding", kwargs, "decoding is explicit UTF-8 in the gate, not in run")


class GhOutputDecodingRealSubprocessTests(unittest.TestCase):
    def test_utf8_emoji_payload_through_real_subprocess_is_satisfied(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            script = _fake_gh_script(
                Path(tmp), json.dumps(_emoji_payload(), ensure_ascii=False).encode("utf-8")
            )
            result = evaluate(7, "owner/name", run_fn=_run_via_fake_gh(script))
        self.assertEqual(result.verdict, Verdict.SATISFIED)
        self.assertFalse(result.blocked)

    def test_malformed_utf8_stdout_blocks_fail_closed(self) -> None:
        malformed = b'{"data": "\xff\xfe\x80 not utf-8"}'
        with tempfile.TemporaryDirectory() as tmp:
            script = _fake_gh_script(Path(tmp), malformed)
            result = evaluate(7, "owner/name", run_fn=_run_via_fake_gh(script))
        self.assertTrue(result.blocked)
        self.assertEqual(result.verdict, Verdict.VERIFY_FAILED)

    def test_malformed_utf8_stderr_on_nonzero_exit_raises_with_the_message(self) -> None:
        def fake_run(argv, **kwargs):
            return type("P", (), {"returncode": 1, "stdout": b"", "stderr": b"gh failed \xff\xfe"})()

        with self.assertRaises(RuntimeError) as ctx:
            query_pr_review_state(7, "owner/name", run_fn=fake_run)
        self.assertIn("gh failed", str(ctx.exception))

    def test_malformed_utf8_stdout_raises_runtime_error_not_a_codec_error(self) -> None:
        def fake_run(argv, **kwargs):
            return type("P", (), {"returncode": 0, "stdout": b'{"data": "\xff"}', "stderr": b""})()

        with self.assertRaises(RuntimeError) as ctx:
            query_pr_review_state(7, "owner/name", run_fn=fake_run)
        self.assertIsInstance(ctx.exception.__cause__, UnicodeDecodeError)


if __name__ == "__main__":
    unittest.main()
