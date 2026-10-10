"""Tests for the pure Copilot review-body threadless-finding detector (201.001-T / 201-F U1).

A Copilot review can carry a valid finding ONLY in its body (``Previously missed (N)``,
``Suppressed comments (N)``, or open findings with no ``#discussion_r`` anchor). The
detector counts those findings as ``max(S, PM) + U``. Fixtures are trimmed verbatim
excerpts of real Copilot review bodies with icon/image markup removed, except rows
labelled SYNTHETIC, which cover shapes that have no real example yet.

Sources (read-only ``gh api``): PR #506 reviews 5450344631 (round 1), 5450565731
(round 2), 5451503039 (round 6); PR #444 review 5177043616 (legacy ``Suppressed
comments (1)``).

No network and no subprocess: the detector is pure.
"""

from __future__ import annotations

import unittest

from autoharness.gates.copilot_review import (
    DISPOSITION_MARKER,
    KNOWN_OVERVIEW_VERSION,
    BodyFindings,
    detect_body_findings,
)

# PR #506 round 2 (review 5450565731): "Previously missed (1)" under a "0 open findings"
# headline, plus a resolved-since-last-review section whose anchor must not be counted.
_PR506_ROUND2 = """<!-- ccr-overview-v2 -->

### 🔵 Needs a closer look

The checks govern irreversible archival and need human validation of recovery-state consistency and cross-invocation agreement.

**0 open findings**

<details>
<summary><strong>1 resolved since last review</strong></summary>

- [Defer recording until the agreement check succeeds](#discussion_r4213707256)
</details>

<details>
<summary><strong>Previously missed (1)</strong></summary>

In code that hasn't changed since last review

<details>
<summary>Refresh or resolve stale checkpoint after task disposition</summary>

`.backlogit/checkpoints/checkpoint-20261008-004836.json:1`

This active checkpoint still lists 161.007-T in `blocked_task` and `tasks_remaining`.
</details>
</details>

🧠 **Review effort:** Balanced
"""

# PR #506 round 1 (review 5450344631): one anchored open finding, which is not a body finding.
_PR506_ROUND1 = """<!-- ccr-overview-v2 -->

### 🔵 Needs a closer look

Changes to destructive closure preconditions and agreement-check integration require final human validation.

<details open>
<summary><strong>1 open finding</strong></summary>

- [Defer recording until the agreement check succeeds](#discussion_r4213707256) · New
</details>

<details>
<summary><strong>What changed in this PR</strong></summary>

Updates shipment reconciliation so qualifying feature members can pass pre-close checks without weakening task-status validation.
</details>
"""

# PR #506 round 6 (review 5451503039): clean.
_PR506_ROUND6 = """<!-- ccr-overview-v2 -->

### 🔵 Needs a closer look

The change relaxes checks before irreversible archival and retains documented integration risks requiring human acceptance.

**0 open findings**

🧠 **Review effort:** Balanced
"""

# SYNTHETIC: "2 open findings" with two anchored items, one wrapping a nested
# per-finding <details><summary><picture> block. The nested summary is not a section
# header, so the span is not truncated and both anchors are counted: U = 0.
_SYNTHETIC_NESTED_ANCHORED = """<!-- ccr-overview-v2 -->

### 🔵 Needs a closer look

<details open>
<summary><strong>2 open findings</strong></summary>

- <details>
  <summary><picture><img alt="Medium severity"></picture> Guard the empty-page branch</summary>

  Nested per-finding detail that must not end the section.
  </details>
  [Guard the empty-page branch](#discussion_r9000000001)
- [Tighten the timeout branch](#discussion_r9000000002)
</details>
"""

# PR #444 review 5177043616: legacy format, "### Suppressed comments (1)" inside Review details.
_PR444_LEGACY_SUPPRESSED = """### 🟡 Changes recommended

Current-head readiness is stale, and unresolved containment, token-output, and lock-path consistency defects remain.

<details>
<summary>Review details</summary>

### Suppressed comments (1)

**.autoharness/harness-manifest.yaml:210**
* The PR currently points at head `08e045a39fbd2a3779027d50d419aee686926b8f`, but its Local Review Readiness block still records an older head. Re-run local review after the remaining fixes land.

- **Files reviewed:** 31/31 changed files
- **Comments generated:** 7
- **Review effort level:** Balanced
</details>
"""

# SYNTHETIC (legacy shape from the plan): Suppressed comments (5) with a nested
# Previously missed (2). count = max(S, PM) + U = max(5, 2) + 0 = 5.
_SYNTHETIC_LEGACY_NESTED = """### Changes recommended

<details>
<summary>Review details</summary>

### Suppressed comments (5)

<details>
<summary>Previously missed (2)</summary>

**tests/test_example.py:12**
* Synthetic finding one.

**tests/test_example.py:40**
* Synthetic finding two.
</details>
</details>
"""

# SYNTHETIC: unanchored open findings with no list. U = 2 - 0 = 2.
_SYNTHETIC_UNANCHORED = """<!-- ccr-overview-v2 -->

**2 open findings**

No review thread or anchor follows this headline.
"""

_OVERVIEW_V3 = """<!-- ccr-overview-v3 -->

### 🔵 Needs a closer look

**0 open findings**
"""

_NO_MARKERS = "Looks good to me. No findings in this review.\n"


class BodyFindingsContractTests(unittest.TestCase):
    """Structural tests: they reach no stub, so they sit outside the RED roster."""

    def test_body_findings_is_a_frozen_dataclass(self) -> None:
        findings = BodyFindings(count=0, markers=(), overview_version=None)
        with self.assertRaises(Exception):
            findings.count = 1  # type: ignore[misc]

    def test_exported_constants_have_the_contract_values(self) -> None:
        self.assertEqual(DISPOSITION_MARKER, "Copilot-Review-Body-Disposition:")
        self.assertEqual(KNOWN_OVERVIEW_VERSION, 2)


class BodyFindingsCcrOverviewV2Tests(unittest.TestCase):
    """Roster 1: ``ccr-overview-v2`` bodies."""

    def test_ccr_overview_v2_bodies(self) -> None:
        cases = (
            # (label, body, count, markers, overview_version)
            ("pr506_round2_previously_missed", _PR506_ROUND2, 1, ("previously_missed",), 2),
            ("pr506_round1_anchored_open", _PR506_ROUND1, 0, (), 2),
            ("pr506_round6_clean", _PR506_ROUND6, 0, (), 2),
            ("synthetic_nested_anchored_open", _SYNTHETIC_NESTED_ANCHORED, 0, (), 2),
        )
        for label, body, count, markers, version in cases:
            with self.subTest(case=label):
                findings = detect_body_findings(body)
                self.assertEqual(findings.count, count)
                self.assertEqual(findings.markers, markers)
                self.assertEqual(findings.overview_version, version)


class BodyFindingsLegacyAndUnanchoredTests(unittest.TestCase):
    """Roster 2: legacy and unanchored bodies."""

    def test_legacy_and_unanchored_bodies(self) -> None:
        cases = (
            # (label, body, count, markers)
            ("pr444_legacy_suppressed_1", _PR444_LEGACY_SUPPRESSED, 1, ("suppressed",)),
            ("synthetic_legacy_nested_5", _SYNTHETIC_LEGACY_NESTED, 5, ("previously_missed", "suppressed")),
            ("synthetic_unanchored_open_2", _SYNTHETIC_UNANCHORED, 2, ("unanchored_open",)),
        )
        for label, body, count, markers in cases:
            with self.subTest(case=label):
                findings = detect_body_findings(body)
                self.assertEqual(findings.count, count)
                self.assertEqual(findings.markers, markers)


class BodyFindingsVersionAndEmptyTests(unittest.TestCase):
    """Roster 3: overview version, no-marker, and empty bodies."""

    def test_overview_version_and_empty_bodies(self) -> None:
        cases = (
            # (label, body, count, overview_version)
            ("overview_v3", _OVERVIEW_V3, 0, 3),
            ("no_markers", _NO_MARKERS, 0, None),
            ("empty_string", "", 0, None),
        )
        for label, body, count, version in cases:
            with self.subTest(case=label):
                findings = detect_body_findings(body)
                self.assertEqual(findings.count, count)
                self.assertEqual(findings.overview_version, version)


if __name__ == "__main__":
    unittest.main()
