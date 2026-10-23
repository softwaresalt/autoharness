"""RED harness for 217.001-T: every version site reads 1.6.0 and divergence is detected."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from autoharness.version_sites import collect_version_sites

REPO_ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = "1.6.0"
ROSTER = ("test_every_site_reads_target_version", "test_divergent_site_is_detected")


class VersionConsistencyTests(unittest.TestCase):
    def test_every_site_reads_target_version(self) -> None:
        sites = collect_version_sites(REPO_ROOT, case="test_every_site_reads_target_version")
        self.assertTrue(sites)
        for name, found in sites.items():
            self.assertEqual(found, TARGET_VERSION, name)

    def test_divergent_site_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sites = collect_version_sites(Path(tmp), case="test_divergent_site_is_detected")
        self.assertGreater(len(set(sites.values())), 1)

    def test_roster_markers_are_pairwise_distinct(self) -> None:
        markers = [f"217.001-T:{name}" for name in ROSTER]
        self.assertEqual(len(markers), len(set(markers)))


if __name__ == "__main__":
    unittest.main()
