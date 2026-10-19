"""Guard for the removed ``agent-intercom`` capability pack (209-F U1).

The pack is being removed from the product and from the dogfood harness one
family at a time (plan docs/plans/2026-10-14-remove-agent-intercom-pack-plan.md).
This guard scans every git-tracked file for the case-insensitive token and
classifies each match as exactly one of:

* HISTORICAL_ALLOWLIST - records that are never rewritten (plan D-9);
* FROZEN_MIRRORS - published schema mirrors that must stay byte-identical;
* TELEMETRY_VOCAB - the retained ``route_kind`` telemetry vocabulary (D-6);
* TOMBSTONES - exact paths that must name the retired value to handle it, each
  scoped to the permitted occurrences (predicate plus maximum count);
* PENDING_SURFACES - the shrinking ledger of live surfaces still to be swept.

Each later unit deletes its own surfaces from the ledger; a stale entry fails.
``LEDGER_ENFORCED`` is flipped to True by the final unit (U23), which also
requires the ledger to be empty. ``tests/`` is not blanket-excluded: existing
tests that merely assume the pack are exact-file ledger entries and tests that
intentionally name the retired value are exact-path tombstones.
"""

from __future__ import annotations

import fnmatch
import subprocess
import unittest
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
TOKEN = "intercom"

# Flipped to True by U23 (final enforcement): the ledger must then be empty.
LEDGER_ENFORCED = False

Predicate = Callable[[Sequence[str], int], bool]


def any_line(_lines: Sequence[str], _index: int) -> bool:
    return True


def line_contains(*snippets: str) -> Predicate:
    """Permit an occurrence only on a line containing one of the snippets."""

    def predicate(lines: Sequence[str], index: int) -> bool:
        return any(snippet in lines[index] for snippet in snippets)

    return predicate


def in_section(heading: str) -> Predicate:
    """Permit an occurrence only inside the Markdown section starting at ``heading``.

    The section runs from the exact heading line to the next heading of the same
    or a higher level.
    """
    level = len(heading) - len(heading.lstrip("#"))

    def predicate(lines: Sequence[str], index: int) -> bool:
        start = next((i for i in range(index, -1, -1) if lines[i].strip() == heading.strip()), None)
        if start is None:
            return False
        for line in lines[start + 1 : index + 1]:
            stripped = line.lstrip()
            hashes = len(stripped) - len(stripped.lstrip("#"))
            if 0 < hashes <= level and stripped[hashes : hashes + 1] == " ":
                return False
        return True

    return predicate


@dataclass(frozen=True)
class Tombstone:
    rationale: str
    permitted: Predicate
    max_count: int


# Plan D-9: records that are never rewritten (prefixes of tracked paths).
HISTORICAL_ALLOWLIST: Mapping[str, str] = {
    "references/": "vendored reference submodules are not part of the product",
    ".backlogit/": "operational backlog state, archive, checkpoints and stash are historical records",
    "docs/archive/": "archived documentation is a historical record",
    "docs/memory/": "dated session memory is a historical record",
    "docs/reviews/": "dated review artifacts are historical records",
    "docs/research/": "dated research notes are historical records",
    "docs/spikes/": "dated spike findings are historical records",
    "docs/decisions/": "recorded decisions are historical records",
    "docs/plans/": "dated plans are historical records",
    "docs/closure/": "closure artifacts are historical records",
    "docs/exec-plans/": "execution plans are historical records",
    "docs/bugs/": "bug records are historical records",
    "docs/audits/": "dated audits are historical records",
    "docs/compound/": "compound learnings are historical records",
    "docs/design-docs/": "dated design documents are historical records",
    "CHANGELOG.md": "changelog history is never rewritten; only new entries are added",
}

# Published schema mirrors: immutable snapshots, byte-pinned by their own tests.
FROZEN_MIRRORS: Mapping[str, str] = {
    "schemas/harness-config/0.9.0.schema.json": "published harness-config 0.9.0 mirror is immutable",
    "schemas/harness-config/1.0.0.schema.json": "published harness-config 1.0.0 mirror is immutable",
    "schemas/harness-config/1.1.0.schema.json": "published harness-config 1.1.0 mirror is immutable",
    "schemas/harness-config/1.2.0.schema.json": "published harness-config 1.2.0 mirror is immutable",
    "schemas/harness-manifest/0.9.0.schema.json": "published harness-manifest 0.9.0 mirror is immutable",
    "schemas/harness-manifest/1.0.0.schema.json": "published harness-manifest 1.0.0 mirror is immutable",
    "schemas/workspace-profile/0.9.0.schema.json": "published workspace-profile 0.9.0 mirror is immutable",
    "schemas/workspace-profile/1.0.0.schema.json": "published workspace-profile 1.0.0 mirror is immutable",
}

# Plan D-6: telemetry route_kind vocabulary of versioned published contracts.
TELEMETRY_VOCAB: Mapping[str, str] = {
    "schemas/execution-epoch*": "execution-epoch route_kind vocabulary is a published contract value (D-6)",
    "schemas/tool-telemetry-event*": "tool-telemetry-event route_kind vocabulary is a published contract value (D-6)",
    "src/autoharness/telemetry/tool_event.py": "well-known route_kind set mirrors the published telemetry contract (D-6)",
}

# Exact path -> permitted occurrences. Later units add their own entries.
TOMBSTONES: Mapping[str, Tombstone] = {
    "tests/test_removed_pack_surface_guard.py": Tombstone(
        rationale="the guard names the retired value because scanning for it is its purpose",
        permitted=any_line,
        max_count=200,
    ),
    "tests/test_schema_contract_removed_pack_profile.py": Tombstone(
        rationale="proves legacy 1.0.0 profiles listing the retired value still validate and that 1.1.0 rejects it",
        permitted=any_line,
        max_count=12,
    ),
    "src/autoharness/schema_contracts.py": Tombstone(
        rationale="contract metadata names the retired value to document the version bump and migrate legacy documents",
        permitted=line_contains("agent-intercom", "agent_intercom"),
        max_count=15,
    ),
    "tests/test_removed_pack_legacy_tolerance.py": Tombstone(
        rationale="proves documents listing the retired value degrade to a removed-capability-pack warning and migration proposal instead of failing",
        permitted=any_line,
        max_count=12,
    ),
    "tests/test_schema_contract_removed_pack_manifest.py": Tombstone(
        rationale="proves legacy 1.0.0 manifests listing the retired value still validate and that 1.1.0 rejects it",
        permitted=any_line,
        max_count=6,
    ),
    "tests/test_schema_contract_removed_pack_config.py": Tombstone(
        rationale="proves configs pinned to earlier versions listing the retired value still validate and that 1.3.0 rejects it",
        permitted=any_line,
        max_count=6,
    ),
    "tests/test_dogfood_removed_pack_state.py": Tombstone(
        rationale="proves the dogfood install no longer lists the retired value in its config, manifest or profile",
        permitted=any_line,
        max_count=6,
    ),
    "tests/test_verify_workspace.py": Tombstone(
        rationale="proves an install that kept the retired heading in copilot-instructions still passes copilot_remote_operator_guidance",
        permitted=line_contains("### agent-intercom"),
        max_count=1,
    ),
    "tests/test_skills_session_output_contract.py": Tombstone(
        rationale="proves the swept skills carry no remote-channel text by asserting the retired value is absent",
        permitted=line_contains('"intercom"'),
        max_count=4,
    ),
    ".github/skills/install-harness/SKILL.md": Tombstone(
        rationale="the Retired capability packs note names the retired value to explain how an explicit selection is ignored",
        permitted=in_section("#### Retired capability packs"),
        max_count=1,
    ),
    "tests/test_install_harness_retired_pack.py": Tombstone(
        rationale="proves the install surfaces name the retired value only in the retired-pack note and carry no pack remnants",
        permitted=any_line,
        max_count=6,
    ),
}

# Shrinking ledger: live surface -> unit that sweeps it. Entries are exact files.
PENDING_SURFACES: Mapping[str, str] = {
    # U18 - discovery, tune, verify-harness skills
    ".github/skills/workspace-discovery/SKILL.md": "U18",
    ".github/skills/tune-harness/SKILL.md": "U18",
    ".github/skills/verify-harness/SKILL.md": "U18",
    # U19 - docs
    "README.md": "U19",
    "docs/capability-packs.md": "U19",
    "docs/getting-started.md": "U19",
    "docs/tuning-guide.md": "U19",
    "docs/primitives.md": "U19",
    # U20 - telemetry docs and deferred-doc deletion
    "docs/telemetry/backlogit-evidence-map.md": "U20",
    "docs/telemetry/backlogit-sensitivity-guardrails.md": "U20",
    "docs/telemetry/cross-pack-adapter-gap-report.md": "U20",
    "docs/deferred/agent-intercom-opt-in-nonmcp.md": "U20",
    "docs/deferred/agent-intercom-opt-in-nonmcp.patch": "U20",
    # U21 - deploy wrapper tolerance
    "tests/test_deploy_harness_scripts.py": "U21",
    # U22 - pack definition removal
    "templates/packs/capability-pack-registry.yaml": "U22",
    "schemas/capability-pack-registry.schema.json": "U22",
    "templates/instructions/agent-intercom.instructions.md.tmpl": "U22",
    ".github/instructions/agent-intercom.instructions.md": "U22",
    ".autoharness/harness-manifest.yaml": "U22",
    "tests/test_capability_pack_registry.py": "U22",
    "tests/test_graphtor_docs_full_suite.py": "U22",
}


def git_tracked_files(root: Path = _REPO_ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [entry.decode("utf-8") for entry in result.stdout.split(b"\0") if entry]


def read_repo_file(path: str, root: Path = _REPO_ROOT) -> bytes | None:
    target = root / path
    if not target.is_file():
        return None
    return target.read_bytes()


def token_lines(data: bytes | None) -> list[str] | None:
    """Return the decoded lines, or None for missing/binary content."""
    if data is None or b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="ignore").splitlines()


def _matches_prefix(path: str, entry: str) -> bool:
    return path == entry or (entry.endswith("/") and path.startswith(entry))


def _is_historical(path: str, historical: Mapping[str, str]) -> bool:
    return any(_matches_prefix(path, entry) for entry in historical)


@dataclass
class ScanReport:
    uncovered: list[str]
    tombstone_violations: list[str]
    stale_pending: list[str]
    stale_allowlist: list[str]
    unrationalized: list[str]
    pending_live: list[str]


def scan(
    tracked: Sequence[str],
    read: Callable[[str], bytes | None],
    *,
    historical: Mapping[str, str] = HISTORICAL_ALLOWLIST,
    frozen: Mapping[str, str] = FROZEN_MIRRORS,
    telemetry: Mapping[str, str] = TELEMETRY_VOCAB,
    tombstones: Mapping[str, Tombstone] = TOMBSTONES,
    pending: Mapping[str, str] = PENDING_SURFACES,
) -> ScanReport:
    tracked_set = set(tracked)
    uncovered: list[str] = []
    tombstone_violations: list[str] = []
    pending_live: list[str] = []
    frozen_hit: set[str] = set()
    telemetry_hit: set[str] = set()
    tombstone_hit: set[str] = set()
    pending_hit: set[str] = set()

    for path in sorted(tracked_set):
        if _is_historical(path, historical):
            continue
        lines = token_lines(read(path))
        if lines is None:
            continue
        hits = [i for i, line in enumerate(lines) if TOKEN in line.casefold()]
        if not hits:
            continue
        if path in frozen:
            frozen_hit.add(path)
            continue
        glob = next((g for g in telemetry if fnmatch.fnmatchcase(path, g)), None)
        if glob is not None:
            telemetry_hit.add(glob)
            continue
        tomb = tombstones.get(path)
        if tomb is not None:
            tombstone_hit.add(path)
            bad = [i + 1 for i in hits if not tomb.permitted(lines, i)]
            if bad:
                tombstone_violations.append(f"{path}: occurrence outside permitted scope at line(s) {bad}")
            if len(hits) > tomb.max_count:
                tombstone_violations.append(f"{path}: {len(hits)} occurrences exceed the permitted {tomb.max_count}")
            continue
        entry = next((e for e in pending if _matches_prefix(path, e)), None)
        if entry is not None:
            pending_hit.add(entry)
            pending_live.append(path)
            continue
        uncovered.append(path)

    stale_allowlist = [
        f"historical:{entry}" for entry in historical if not any(_matches_prefix(p, entry) for p in tracked_set)
    ]
    stale_allowlist += [f"frozen:{p}" for p in frozen if p not in frozen_hit]
    stale_allowlist += [f"telemetry:{g}" for g in telemetry if g not in telemetry_hit]
    stale_allowlist += [f"tombstone:{p}" for p in tombstones if p not in tombstone_hit]
    unrationalized = [
        name
        for name, rationale in (
            *((f"historical:{k}", v) for k, v in historical.items()),
            *((f"frozen:{k}", v) for k, v in frozen.items()),
            *((f"telemetry:{k}", v) for k, v in telemetry.items()),
            *((f"tombstone:{k}", v.rationale) for k, v in tombstones.items()),
        )
        if not rationale or not rationale.strip()
    ]
    return ScanReport(
        uncovered=uncovered,
        tombstone_violations=tombstone_violations,
        stale_pending=[e for e in pending if e not in pending_hit],
        stale_allowlist=stale_allowlist,
        unrationalized=unrationalized,
        pending_live=pending_live,
    )


class RemovedPackSurfaceGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.report = scan(git_tracked_files(), read_repo_file)

    def test_every_live_match_is_classified(self) -> None:
        self.assertEqual(self.report.uncovered, [], "live files name the retired pack outside every class")
        self.assertEqual(self.report.tombstone_violations, [])

    def test_pending_ledger_has_no_stale_entries(self) -> None:
        self.assertEqual(
            self.report.stale_pending,
            [],
            "remove swept surfaces from PENDING_SURFACES (or move them to a tombstone/frozen class)",
        )

    def test_allowlist_and_tombstone_entries_exist_with_rationale(self) -> None:
        self.assertEqual(self.report.stale_allowlist, [])
        self.assertEqual(self.report.unrationalized, [])
        for entry, unit in PENDING_SURFACES.items():
            self.assertRegex(unit, r"^U\d+$", entry)
            self.assertFalse(entry.endswith("/"), f"ledger entries are exact files: {entry}")

    def test_ledger_is_empty_once_enforced(self) -> None:
        if not LEDGER_ENFORCED:
            self.skipTest("LEDGER_ENFORCED is flipped to True by U23")
        self.assertEqual(dict(PENDING_SURFACES), {})
        self.assertEqual(self.report.pending_live, [])


class GuardMachineryTests(unittest.TestCase):
    """Synthetic trees prove the guard fails where the acceptance criteria say it must."""

    @staticmethod
    def _scan(files: dict[str, bytes], **kwargs: object) -> ScanReport:
        return scan(list(files), files.get, **kwargs)  # type: ignore[arg-type]

    def test_new_live_file_naming_the_pack_is_uncovered(self) -> None:
        files = {"src/new_module.py": b"# wires the Agent-Intercom pack\n", "src/clean.py": b"x = 1\n"}
        report = self._scan(files, historical={}, frozen={}, telemetry={}, tombstones={}, pending={})
        self.assertEqual(report.uncovered, ["src/new_module.py"])

    def test_pending_entry_covers_live_file_and_stale_entry_fails(self) -> None:
        files = {"docs/live.md": b"mentions intercom\n", "docs/clean.md": b"nothing\n"}
        report = self._scan(
            files,
            historical={},
            frozen={},
            telemetry={},
            tombstones={},
            pending={"docs/live.md": "U9", "docs/clean.md": "U9"},
        )
        self.assertEqual(report.uncovered, [])
        self.assertEqual(report.stale_pending, ["docs/clean.md"])

    def test_historical_prefix_is_not_scanned(self) -> None:
        files = {"docs/archive/old.md": b"intercom\n"}
        report = self._scan(files, historical={"docs/archive/": "why"}, frozen={}, telemetry={}, tombstones={}, pending={})
        self.assertEqual(report.uncovered, [])
        self.assertEqual(report.stale_allowlist, [])

    def test_unmatched_allowlist_entries_are_stale(self) -> None:
        files = {"a.md": b"clean\n"}
        report = self._scan(
            files,
            historical={"gone/": "why"},
            frozen={"schemas/x/1.0.0.json": "why"},
            telemetry={"schemas/t*": "why"},
            tombstones={"a.md": Tombstone("why", any_line, 1)},
            pending={},
        )
        self.assertEqual(
            sorted(report.stale_allowlist),
            ["frozen:schemas/x/1.0.0.json", "historical:gone/", "telemetry:schemas/t*", "tombstone:a.md"],
        )

    def test_blank_rationale_is_reported(self) -> None:
        files = {"a.md": b"intercom\n"}
        report = self._scan(
            files, historical={}, frozen={}, telemetry={}, tombstones={"a.md": Tombstone(" ", any_line, 1)}, pending={}
        )
        self.assertEqual(report.unrationalized, ["tombstone:a.md"])

    def test_tombstone_rejects_occurrence_outside_the_permitted_snippet(self) -> None:
        text = b"## Presets\n| full | intercom |\n\nRETIRED_PACK: intercom ignored\n"
        tomb = Tombstone("handler", line_contains("RETIRED_PACK"), 2)
        report = self._scan(
            {"skill.md": text}, historical={}, frozen={}, telemetry={}, tombstones={"skill.md": tomb}, pending={}
        )
        self.assertEqual(len(report.tombstone_violations), 1)
        self.assertIn("line(s) [2]", report.tombstone_violations[0])

    def test_tombstone_rejects_more_occurrences_than_the_maximum(self) -> None:
        text = b"RETIRED_PACK: intercom\nRETIRED_PACK: intercom again\n"
        tomb = Tombstone("handler", line_contains("RETIRED_PACK"), 1)
        report = self._scan(
            {"skill.md": text}, historical={}, frozen={}, telemetry={}, tombstones={"skill.md": tomb}, pending={}
        )
        self.assertEqual(len(report.tombstone_violations), 1)
        self.assertIn("exceed", report.tombstone_violations[0])

    def test_section_predicate_scopes_to_the_named_heading(self) -> None:
        text = (
            b"# Guide\n## Retired capability packs\nintercom is retired\n### Detail\nintercom detail\n"
            b"## Presets\nintercom row\n"
        )
        tomb = Tombstone("retired note", in_section("## Retired capability packs"), 5)
        report = self._scan(
            {"guide.md": text}, historical={}, frozen={}, telemetry={}, tombstones={"guide.md": tomb}, pending={}
        )
        self.assertEqual(len(report.tombstone_violations), 1)
        self.assertIn("line(s) [7]", report.tombstone_violations[0])

    def test_crlf_and_binary_content_are_handled(self) -> None:
        files = {"crlf.md": b"line\r\nIntercom\r\n", "blob.bin": b"\0\0intercom"}
        report = self._scan(files, historical={}, frozen={}, telemetry={}, tombstones={}, pending={})
        self.assertEqual(report.uncovered, ["crlf.md"])

    def test_telemetry_glob_covers_nested_mirrors(self) -> None:
        files = {"schemas/execution-epoch/1.1.0.schema.json": b'{"route_kind": "intercom"}\n'}
        report = self._scan(
            files, historical={}, frozen={}, telemetry={"schemas/execution-epoch*": "why"}, tombstones={}, pending={}
        )
        self.assertEqual(report.uncovered, [])
        self.assertEqual(report.stale_allowlist, [])


if __name__ == "__main__":
    unittest.main()
