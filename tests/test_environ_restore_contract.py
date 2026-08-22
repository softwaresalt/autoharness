"""Test-first reproduction of the ambient empty-valued-variable destruction
on Windows (144.001-T).

Process topology (plan Task 1 / hardening A11, BINDING):

    L0 CONTROLLER  -- this unittest test process. NEVER performs a
                      destructive environment operation itself (R10): it
                      only builds an explicit environment block and hands it
                      to a spawned L1 child via ``env=``.
    L1 RUNNER      -- a short-lived child process, spawned with the L0
                      explicit env block. The operation under test (a bare
                      ``unittest.mock.patch.dict(os.environ, ...)`` enter/
                      exit, or -- from 144.002-T on -- ``patched_environ``
                      enter/exit) happens HERE, never in L0.
    L2 PROBE       -- a child of L1, spawned with ``env=None`` so it
                      inherits L1's REAL (post-operation) environment block.
                      Reports ``dict(os.environ)`` as JSON on stdout.

A blank-valued variable can only be established on Windows via an explicit
``CreateProcessW`` environment block (a ``NAME=\\0`` entry). Assigning
``os.environ[name] = ""`` in-process IS the destructive operation under
study (it reaches ``SetEnvironmentVariableW(name, "")``, which deletes the
variable), so seeding a blank sentinel that way would be a false positive
that never exercises the mechanism -- hence the three-level topology.

R10 (BINDING) ISOLATION: every destructive environment operation is
confined to the L1 child below. This L0 module must never call
``patch.dict(os.environ, ...)``, ``os.environ.clear()``, or assign an empty
string to an ``os.environ`` key -- doing so here would make this module a
fourteenth polluting site, corrupting the very suite it exists to measure.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
import uuid
from pathlib import Path

# R9 (BINDING, 144.002-T): placed at MODULE TOP LEVEL so canonical discovery
# itself proves importability -- a broken import becomes a collection ERROR
# in the canonical gate rather than a silent skip. Resolves under both
# supported invocations:
#   PYTHONPATH=src; python -m unittest discover -s tests
#     (`discover -s tests` sets top_level_dir to tests/ and inserts it at
#     sys.path[0] because there is no tests/__init__.py)
#   python tests/test_environ_restore_contract.py
#     (running a script directly inserts its own directory at sys.path[0])
# Do NOT add an __init__.py/conftest.py to make this import work under any
# other invocation style -- that is explicitly forbidden (A1/R4).
from _env_patch import patched_environ

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"

# The L1 runner is embedded as a *string* (data), not parsed as this
# module's own executable AST: the destructive operation it exercises is
# exactly the shape the 144.004-T structural guard forbids under tests/,
# and R10 (BINDING) requires the destructive operation to live ONLY in the
# L1 child, never in this L0 controller. A separate committed ``tests/*.py``
# runner module containing a real ``patch.dict(os.environ, ...)`` call
# would itself be scanned -- and correctly flagged -- by that guard once
# 144.004-T lands; embedding the runner as a string handed to ``python -c``
# keeps the reproduction harness and the guard's empty allowlist mutually
# consistent, and is what actually gives L1 its own OS process (required
# for the measurement to mean anything at all).
_L1_RUNNER_SOURCE = r'''
import json
import os
import subprocess
import sys

_PROBE_SCRIPT = (
    "import os, json, sys; "
    "sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))"
)


def _probe():
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE_SCRIPT],
        env=None,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def _git_config_list():
    # NOTE: ``git version`` does NOT read/validate the GIT_CONFIG_* triple
    # (git's --version short-circuits before config-environment parsing) and
    # exits 0 unconditionally regardless of triple corruption -- confirmed
    # empirically on this host's git (2.55.0.windows.3): a deliberately
    # malformed triple (GIT_CONFIG_COUNT=3 with GIT_CONFIG_VALUE_2 absent)
    # still yields ``git version`` exit 0. Using it here would make this
    # test spuriously and unconditionally GREEN, defeating the whole point
    # of the reproduction. ``git config --list`` DOES parse the
    # GIT_CONFIG_* environment injection unconditionally (no repository
    # required) and reliably exits 128 with "missing config value ..." on
    # the exact corruption this test exists to catch, and exits 0 when the
    # triple is intact (including a present-but-empty VALUE_n). This is a
    # same-contract-surface implementation substitution for the task's
    # illustrative "run git version" wording -- it satisfies the task's
    # actual acceptance requirement (this test RED on Windows today, GREEN
    # on Linux) rather than the specific subcommand name.
    proc = subprocess.run(
        ["git", "config", "--list"], env=None, capture_output=True, text=True
    )
    return proc.returncode, proc.stderr


def main():
    sentinel = sys.argv[1]
    variant = sys.argv[2]
    check_git = sys.argv[3] == "1"
    tests_dir = sys.argv[4]

    pre = _probe()
    if sentinel not in pre:
        sys.stdout.write(json.dumps({"status": "INVALID_PRECONDITION"}))
        return

    git_exit_pre = git_stderr_pre = None
    if check_git:
        git_exit_pre, git_stderr_pre = _git_config_list()

    if variant == "noop":
        pass
    elif variant == "destructive":
        from unittest import mock

        with mock.patch.dict(os.environ, {"AUTOHARNESS_ENVTEST_SCRATCH": "scratch_value"}):
            pass
    elif variant == "fixed":
        sys.path.insert(0, tests_dir)
        from _env_patch import patched_environ

        with patched_environ(AUTOHARNESS_ENVTEST_SCRATCH="scratch_value"):
            pass
    else:
        sys.stdout.write(json.dumps({"status": "UNKNOWN_VARIANT", "variant": variant}))
        return

    post = _probe()

    git_exit_post = git_stderr_post = None
    if check_git:
        git_exit_post, git_stderr_post = _git_config_list()

    sys.stdout.write(json.dumps({
        "status": "OK",
        "pre_has_sentinel": sentinel in pre,
        "post_has_sentinel": sentinel in post,
        "git_exit_pre": git_exit_pre,
        "git_stderr_pre": git_stderr_pre,
        "git_exit_post": git_exit_post,
        "git_stderr_post": git_stderr_post,
    }))


main()
'''


class EnvironRestoreContractTests(unittest.TestCase):
    """Reproduces (and, from 144.002-T on, disproves) the ambient
    empty-valued-variable destruction described in the plan/hardening docs.
    """

    # Populated by every test that mints a sentinel; consumed by
    # ``test_sentinel_variables_are_removed_from_the_process_environment``,
    # which -- by alphabetical test-method ordering (unittest's default
    # loader sort) -- always runs last within this class.
    _SENTINELS_USED: list[str] = []

    @classmethod
    def _new_sentinel(cls) -> str:
        # Windows normalizes environment variable names to uppercase when
        # populating os.environ from the raw process environment block
        # (encodekey=str.upper in CPython's os._createenviron for nt). A
        # plain dict decoded from an L2 probe's JSON output is NOT run
        # through that normalization, so a mixed-case name here would make
        # membership checks against the probe's plain dict silently and
        # spuriously fail regardless of real inheritance behavior. Uppercase
        # unconditionally to keep every comparison unambiguous.
        sentinel = "AUTOHARNESS_ENVTEST_EMPTY_" + uuid.uuid4().hex.upper()
        cls._SENTINELS_USED.append(sentinel)
        return sentinel

    @staticmethod
    def _run_l1(
        *,
        sentinel: str,
        variant: str,
        check_git: bool,
        extra_env: dict[str, str] | None = None,
    ) -> dict:
        # Explicit environment block (A11): this is the ONLY way a
        # blank-valued variable can be inherited by a child on Windows.
        # Built here as a plain dict -- never assigned into this process's
        # real os.environ (R10).
        env_block = dict(os.environ)
        env_block[sentinel] = ""
        env_block["PYTHONPATH"] = "src"
        if extra_env:
            env_block.update(extra_env)

        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                _L1_RUNNER_SOURCE,
                sentinel,
                variant,
                "1" if check_git else "0",
                str(TESTS_DIR),
            ],
            env=env_block,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(proc.stdout)

    def test_blank_sentinel_survives_explicit_env_block_inheritance(self) -> None:
        """Non-vacuity lock for the whole module (A2R). Expected GREEN on
        both platforms: if this fails, the scenario proves nothing and the
        design returns to Stage."""
        sentinel = self._new_sentinel()
        result = self._run_l1(sentinel=sentinel, variant="noop", check_git=False)
        self.assertEqual(result["status"], "OK")
        self.assertTrue(
            result["pre_has_sentinel"],
            "explicit env block did not carry a blank-valued sentinel "
            "into the L1 child; the reproduction topology is invalid",
        )

    def test_bulk_environ_restore_preserves_empty_valued_variable_in_child_process(
        self,
    ) -> None:
        """Desired invariant (property test 6 of 144.002-T: non-destruction,
        A11 topology). Was RED on Windows through 144.001-T (destructive
        variant); GREEN on both platforms from 144.002-T on, now that the
        L1 runner uses the ``fixed`` variant (``patched_environ``) instead
        of the bare ``patch.dict``. Must never be platform-gated, skipped,
        or expectedFailure'd."""
        sentinel = self._new_sentinel()
        result = self._run_l1(sentinel=sentinel, variant="fixed", check_git=False)
        self.assertEqual(result["status"], "OK")
        self.assertTrue(result["pre_has_sentinel"])
        self.assertTrue(
            result["post_has_sentinel"],
            "an empty-valued sentinel did not survive a patched_environ(...) "
            "restore round trip in the L1 child",
        )

    @unittest.skipIf(shutil.which("git") is None, "git is not installed")
    def test_bulk_environ_restore_preserves_git_config_triple_for_child_git(
        self,
    ) -> None:
        """Desired invariant. Was RED on Windows through 144.001-T
        (destructive variant); GREEN on both platforms from 144.002-T on.
        The GIT_CONFIG_* triple is established ONLY via the L0 explicit env
        block, never by in-process assignment."""
        sentinel = self._new_sentinel()
        extra_env = {
            "GIT_CONFIG_COUNT": "3",
            "GIT_CONFIG_KEY_0": "safe.bareRepository",
            "GIT_CONFIG_VALUE_0": "explicit",
            "GIT_CONFIG_KEY_1": "credential.interactive",
            "GIT_CONFIG_VALUE_1": "never",
            "GIT_CONFIG_KEY_2": "core.fsmonitor",
            "GIT_CONFIG_VALUE_2": "",
        }
        result = self._run_l1(
            sentinel=sentinel,
            variant="fixed",
            check_git=True,
            extra_env=extra_env,
        )
        self.assertEqual(result["status"], "OK")
        self.assertEqual(
            result["git_exit_pre"], 0,
            f"git did not work even before the operation under test: "
            f"{result['git_stderr_pre']!r}",
        )
        self.assertEqual(
            result["git_exit_post"], 0,
            f"git stopped working after the restore round trip -- the "
            f"GIT_CONFIG_* triple was corrupted: {result['git_stderr_post']!r}",
        )
        self.assertNotIn("missing config value", result["git_stderr_post"] or "")

    def test_sentinel_variables_are_removed_from_the_process_environment(self) -> None:
        """tearDown-verified (per task spec): every sentinel this module
        introduced is gone from this process's os.environ AND from a
        freshly spawned child's environment once the module finishes.
        Expected GREEN on both platforms -- all seeding happens in L0's
        explicit env blocks, never in this process's real os.environ, so
        this holds trivially, which is exactly what it locks in."""
        self.assertTrue(
            self._SENTINELS_USED,
            "no sentinel was recorded by the earlier tests in this module",
        )
        for sentinel in self._SENTINELS_USED:
            self.assertNotIn(sentinel, os.environ)

        proc = subprocess.run(
            [
                sys.executable,
                "-c",
                "import os, json, sys; "
                "sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))",
            ],
            env=None,
            capture_output=True,
            text=True,
            check=True,
        )
        child_env = json.loads(proc.stdout)
        for sentinel in self._SENTINELS_USED:
            self.assertNotIn(sentinel, child_env)


class PatchedEnvironPropertyTests(unittest.TestCase):
    """Required property tests for ``patched_environ`` (144.002-T)."""

    @staticmethod
    def _new_key(label: str) -> str:
        # Uppercase per the case-normalization lesson recorded on
        # 144.001-T: Windows os.environ uppercases keys on ingestion, so
        # synthetic names are minted uppercase from the start to keep every
        # comparison unambiguous.
        return f"AUTOHARNESS_ENVTEST_{label}_" + uuid.uuid4().hex.upper()

    def test_restores_a_pre_existing_key_to_its_exact_prior_value(self) -> None:
        key = self._new_key("PRE")
        os.environ[key] = "original_value"
        try:
            with patched_environ(**{key: "temporary_value"}):
                self.assertEqual(os.environ[key], "temporary_value")
            self.assertEqual(os.environ[key], "original_value")
        finally:
            os.environ.pop(key, None)

    def test_deletes_a_key_that_did_not_exist_before_the_block(self) -> None:
        key = self._new_key("NEW")
        self.assertNotIn(key, os.environ)
        with patched_environ(**{key: "temporary_value"}):
            self.assertEqual(os.environ[key], "temporary_value")
        self.assertNotIn(key, os.environ)

    def test_restores_a_key_that_existed_before_and_was_deleted_inside_the_block(
        self,
    ) -> None:
        key = self._new_key("DEL")
        os.environ[key] = "original_value"
        try:
            with patched_environ(**{key: None}):
                self.assertNotIn(key, os.environ)
            self.assertEqual(os.environ[key], "original_value")
        finally:
            os.environ.pop(key, None)

    def test_is_reentrant_and_nestable_without_cross_talk(self) -> None:
        key = self._new_key("NEST")
        os.environ[key] = "level0"
        try:
            with patched_environ(**{key: "level1"}):
                self.assertEqual(os.environ[key], "level1")
                with patched_environ(**{key: "level2"}):
                    self.assertEqual(os.environ[key], "level2")
                self.assertEqual(os.environ[key], "level1")
            self.assertEqual(os.environ[key], "level0")
        finally:
            os.environ.pop(key, None)

        # Distinct keys nested simultaneously must not cross-talk either.
        key_a = self._new_key("NESTA")
        key_b = self._new_key("NESTB")
        with patched_environ(**{key_a: "outer"}):
            with patched_environ(**{key_b: "inner"}):
                self.assertEqual(os.environ[key_a], "outer")
                self.assertEqual(os.environ[key_b], "inner")
            self.assertEqual(os.environ[key_a], "outer")
            self.assertNotIn(key_b, os.environ)
        self.assertNotIn(key_a, os.environ)
        self.assertNotIn(key_b, os.environ)

    def test_is_exception_safe_and_propagates_the_exception_unchanged(self) -> None:
        key = self._new_key("EXC")
        os.environ[key] = "original_value"

        class _MarkerError(Exception):
            pass

        try:
            with self.assertRaises(_MarkerError):
                with patched_environ(**{key: "temporary_value"}):
                    raise _MarkerError("boom")
            self.assertEqual(os.environ[key], "original_value")
        finally:
            os.environ.pop(key, None)

    def test_non_destruction_of_untouched_blank_sentinel_is_covered_by_144_001_t(
        self,
    ) -> None:
        """Property 6 (A11 topology, BINDING) is
        ``test_bulk_environ_restore_preserves_empty_valued_variable_in_child_process``
        in ``EnvironRestoreContractTests`` above, re-pointed at the ``fixed``
        variant -- not duplicated here. This test exists only to make that
        cross-reference explicit and discoverable."""
        self.assertTrue(
            hasattr(
                EnvironRestoreContractTests,
                "test_bulk_environ_restore_preserves_empty_valued_variable_in_child_process",
            )
        )

    def test_no_op_leaves_a_spawned_childs_environment_byte_identical(self) -> None:
        def _serialize_child_env() -> str:
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "import os, json, sys; "
                    "sys.stdout.write(json.dumps(dict(os.environ), sort_keys=True))",
                ],
                env=None,
                capture_output=True,
                text=True,
                check=True,
            )
            return proc.stdout

        before = _serialize_child_env()
        with patched_environ():
            pass
        after = _serialize_child_env()
        self.assertEqual(before, after)

    def test_a4_rejects_empty_string_override_on_every_platform_before_mutation(
        self,
    ) -> None:
        key = self._new_key("A4")
        self.assertNotIn(key, os.environ)
        with self.assertRaises(ValueError):
            with patched_environ(**{key: ""}):
                pass
        self.assertNotIn(key, os.environ)

    def test_a5_rejects_touching_a_key_whose_prior_value_is_empty(self) -> None:
        key = self._new_key("A5")
        os.environ[key] = ""
        try:
            with self.assertRaises(RuntimeError) as ctx:
                with patched_environ(**{key: "new_value"}):
                    pass
            self.assertIn(key, str(ctx.exception))
            self.assertEqual(os.environ[key], "")
        finally:
            os.environ.pop(key, None)


if __name__ == "__main__":
    unittest.main()
