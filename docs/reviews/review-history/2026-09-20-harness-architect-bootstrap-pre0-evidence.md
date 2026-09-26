---
title: "PRE-0 execution evidence — BOOTSTRAP-0 harness-architect bootstrap (188-S)"
description: "Immutable, write-once record of the PRE-0 producer-side execution for 188-S. Records the two P-004 channels executed directly from templates/skills/harness-architect/SKILL.md.tmpl, their verbatim commands, their exit codes, the full failure set with its expected marker, the assertion source and its digest, the labels-absent base commit the run was taken against, and both unscoped observations including the one that disagreed. This artifact is the durable P-004 postcondition carrier for this unit. It is never edited after it is written."
doc_type: evidence-record
source: docs/reviews/review-history/2026-09-20-harness-architect-bootstrap-pre0-evidence.md
date: 2026-09-20
artifact_class: immutable
plan_id: harness-architect-bootstrap
plan_path: docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
plan_revision: 5
feature_id: 182-F
shipment_id: 188-S
executed_by: stage
executed_at_utc: 2026-09-20T22:46:47.2721888Z
labels_absent_base: 3ad5fcc7fec87e5306df0f899025a8a1a3cdbbe4
procedure_source: templates/skills/harness-architect/SKILL.md.tmpl
procedure_source_sha256: 0e0726fdac474c3e649f651d5b093e63ba1af0d06fd62506f83d9daaf5464517
declared_harness_set:
  - test_harness_architect_surface.py
harness_source_sha256: 9c5ac57b984d557b64c350b91629e44a4febfc245ddfa197e41a73e13f237178
expected_failure_marker: HARNESS_ARCHITECT_SURFACE_ABSENT
compilation_channel: PASS
red_phase_channel: CONFIRMED
tags:
  - evidence-record
  - bootstrap
  - harness-architect
  - p-004
  - pre-0
---

# `PRE-0` execution evidence — `188-S`

```text
PRE0_STATE: PRE0_EVIDENCE_RECORDED | compilation=PASS | red_phase=CONFIRMED | marker=HARNESS_ARCHITECT_SURFACE_ABSENT | labels_absent_base=3ad5fcc7fec87e5306df0f899025a8a1a3cdbbe4 | harness_sha256=9c5ac57b984d557b64c350b91629e44a4febfc245ddfa197e41a73e13f237178 | checked=2026-09-20T22:46:47Z
```

Exactly one `PRE0_STATE:` line exists in this file, and the fenced block above
is it. Anything not affirmatively matching the token `PRE0_EVIDENCE_RECORDED`
is not a pass.

## Postcondition

| Field | Value |
|---|---|
| `Compilation` | **PASS** |
| `Red Phase` | **CONFIRMED** |
| Expected failure marker | `HARNESS_ARCHITECT_SURFACE_ABSENT` |
| Procedure source | `templates/skills/harness-architect/SKILL.md.tmpl` |
| Procedure source `sha256` | `0e0726fdac474c3e649f651d5b093e63ba1af0d06fd62506f83d9daaf5464517` |
| Labels-absent base commit | `3ad5fcc7fec87e5306df0f899025a8a1a3cdbbe4` |
| Executed by | Stage, producer side |
| Executed at | `2026-09-20T22:46:40Z` – `2026-09-20T22:53:45Z` (UTC) |

## Why this file exists, and why it is not the harness manifest

Decision `D11` states that it "authorizes **no** edit to
`.autoharness/harness-manifest.yaml` by any staging session". `PRE-0` is a
staging-side producer act, so the manifest could never have carried the
postcondition earlier revisions of the plan assigned to it: a postcondition its
own author is forbidden to write is not a postcondition. This committed,
immutable artifact is the carrier instead. `.autoharness/harness-manifest.yaml`
is untouched at staging time and is written only by `182.003-T`, in its own
ACTIVATE commit, under `D11`.

## Ordering — established by construction, re-derivable by anyone

`PRE-0` was executed against a tree in which the four `harness-ready` labels
were **absent**, and the labels were applied only afterwards.

| # | Fact | Re-derivation |
|---|---|---|
| O1 | At base `3ad5fcc7`, none of `182.001-T`, `182.002-T`, `182.003-T`, `182.004-T` carries `harness-ready` in its `labels:` list. | `git show 3ad5fcc7:.backlogit/queue/182.001-T.md` (and the other three) |
| O2 | Both P-004 channels were executed against that base; this file records them verbatim. | the two channel sections below |
| O3 | The labels were re-applied in a commit **descended from** `3ad5fcc7`. | `git log --oneline -S"harness-ready" -- .backlogit/queue/182.001-T.md` |

Label-list state observed at the base commit:

```text
182.001-T    labels=['bootstrap', 'red', 'harness-architect']            harness-ready_in_labels=False
182.002-T    labels=['bootstrap', 'p-004', 'gate']                       harness-ready_in_labels=False
182.003-T    labels=['bootstrap', 'activate', 'harness-architect']       harness-ready_in_labels=False
182.004-T    labels=['bootstrap', 'gate', 'composed-state']              harness-ready_in_labels=False
LABELS_ABSENT_AT_BASE: True base: 3ad5fcc7fec87e5306df0f899025a8a1a3cdbbe4
```

## Template Step 1 — harness generation

The harness was authored in a scratch location **outside the repository working
tree**. Stage writes no test or source file; `182.001-T` is the task that
authors this module into `tests/` and commits it, byte-identical to the source
below.

* Declared harness set: `test_harness_architect_surface.py`, and only that.
* `sha256` of the authored source:
  `9c5ac57b984d557b64c350b91629e44a4febfc245ddfa197e41a73e13f237178`

Verbatim source, as executed:

```python
"""Harness-surface conformance assertion for the harness-architect actor.

Authored at PRE-0 of 188-S directly from the authoritative procedure at
templates/skills/harness-architect/SKILL.md.tmpl (Step 1 harness generation).

Declared harness set for 188-S: this module, and only this module.

Expected failure marker: HARNESS_ARCHITECT_SURFACE_ABSENT
"""

import os
import re
import unittest

SKILL_PATH = os.path.join(".github", "skills", "harness-architect", "SKILL.md")
MARKER = "HARNESS_ARCHITECT_SURFACE_ABSENT"
DOUBLE_BRACE = re.compile(r"\{\{[^}]+\}\}")
SINGLE_BRACE_SUFFIX = re.compile(r"\{SUFFIX_(?:FEATURE|TASK)\}")


def _read():
    with open(SKILL_PATH, "r", encoding="utf-8") as handle:
        return handle.read()


def _frontmatter(text):
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return parts[1]


class HarnessArchitectSurfaceConformance(unittest.TestCase):
    """Five limbs, evaluated independently, all against the installed surface."""

    def test_limb1_installed_surface_exists(self):
        self.assertTrue(
            os.path.isfile(SKILL_PATH),
            "%s: %s does not exist" % (MARKER, SKILL_PATH),
        )

    def test_limb2_yaml_frontmatter_block_present(self):
        if not os.path.isfile(SKILL_PATH):
            self.fail("%s: %s does not exist" % (MARKER, SKILL_PATH))
        self.assertIsNotNone(
            _frontmatter(_read()),
            "%s: no YAML frontmatter block" % MARKER,
        )

    def test_limb3_declares_name_harness_architect(self):
        if not os.path.isfile(SKILL_PATH):
            self.fail("%s: %s does not exist" % (MARKER, SKILL_PATH))
        front = _frontmatter(_read()) or ""
        self.assertRegex(
            front,
            r"(?m)^name:\s*harness-architect\s*$",
            "%s: frontmatter does not declare name: harness-architect" % MARKER,
        )

    def test_limb4_no_unresolved_double_brace_variable(self):
        if not os.path.isfile(SKILL_PATH):
            self.fail("%s: %s does not exist" % (MARKER, SKILL_PATH))
        found = DOUBLE_BRACE.findall(_read())
        self.assertEqual(
            found, [], "%s: unresolved double-brace variables %r" % (MARKER, found)
        )

    def test_limb5_no_unresolved_single_brace_suffix_placeholder(self):
        if not os.path.isfile(SKILL_PATH):
            self.fail("%s: %s does not exist" % (MARKER, SKILL_PATH))
        found = SINGLE_BRACE_SUFFIX.findall(_read())
        self.assertEqual(
            found, [], "%s: unresolved suffix placeholders %r" % (MARKER, found)
        )


if __name__ == "__main__":
    unittest.main()
```

## Template Step 5.1 — compilation channel

```text
cmd: python -m py_compile src/autoharness/cli.py
COMPILATION_EXIT=0
TS_UTC=2026-09-20T22:46:40.2451873Z
```

**`Compilation: PASS`.** Exit `0`, as P-004's precondition requires.

## Template Step 5.2 — red-phase channel, scoped to the declared harness set

This is the form the template itself names: *"Run `{{TEST_COMMAND}}` for the
harness tests."*

```text
cmd: PYTHONPATH=src python -m unittest discover -s <declared-harness-set>
TS_START_UTC=2026-09-20T22:46:46.8511810Z

test_limb1_installed_surface_exists ... FAIL
test_limb2_yaml_frontmatter_block_present ... FAIL
test_limb3_declares_name_harness_architect ... FAIL
test_limb4_no_unresolved_double_brace_variable ... FAIL
test_limb5_no_unresolved_single_brace_suffix_placeholder ... FAIL

AssertionError: False is not true : HARNESS_ARCHITECT_SURFACE_ABSENT: .github\skills\harness-architect\SKILL.md does not exist
AssertionError: HARNESS_ARCHITECT_SURFACE_ABSENT: .github\skills\harness-architect\SKILL.md does not exist
AssertionError: HARNESS_ARCHITECT_SURFACE_ABSENT: .github\skills\harness-architect\SKILL.md does not exist
AssertionError: HARNESS_ARCHITECT_SURFACE_ABSENT: .github\skills\harness-architect\SKILL.md does not exist
AssertionError: HARNESS_ARCHITECT_SURFACE_ABSENT: .github\skills\harness-architect\SKILL.md does not exist

Ran 5 tests in 0.004s
FAILED (failures=5)
SCOPED_RED_EXIT=1
TS_END_UTC=2026-09-20T22:46:47.2721888Z
```

**`Red Phase: CONFIRMED`.** Exit non-zero; **5 failures, 0 errors**; every
failure carries the expected marker `HARNESS_ARCHITECT_SURFACE_ABSENT`; the
failure reason is the intended one — the skill is absent — and there is no
collection error, no import error and no syntax error.

## The unscoped reading, recorded without softening

P-004's precondition **as literally written** reads the whole discovered suite.
Two unscoped observations were taken, and they **disagreed**.

| Observation | Command | Result |
|---|---|---|
| U1 | `PYTHONPATH=src python -m unittest discover -s tests` | exit `1`; `Ran 2344 tests in 616.954s`; `FAILED (errors=1, skipped=54)`. The single error is a Windows temp-directory teardown race — `PermissionError: [WinError 32] ... 'tmpf8bae7dg\workspace'` raised inside `shutil.rmtree`. It carries **no** `HARNESS_ARCHITECT_SURFACE_ABSENT` marker. |
| U2 | `PYTHONPATH=src python -m unittest discover -s tests` | exit `0`; `Ran 2344 tests in 401.417s`; `OK (skipped=54)`. |

**Adjudication, against the convenient direction.** Neither U1 nor U2 is
counted as red-phase evidence for this unit.

* **U1 is not evidence** even though it is non-zero, because the evidence rule
  is *marker-carrying*, not merely non-zero. A flaky teardown race is not a
  harness failure, and accepting it would be accepting a false red.
* **U2 is the stable reading, and it is green** — which is **expected, not a
  contradiction**. `PRE-0` authored the assertion outside the working tree, so
  `discover -s tests` cannot see it. The whole suite is green precisely because
  this unit's harness is not on the branch yet.

**The consequence is stated rather than smoothed over.** At `PRE-0`, the
whole-suite form of P-004's precondition is **not** satisfied, and no carrier
claims it is. What is satisfied at `PRE-0` is the form the harness-architect
template prescribes at Step 5.2 — the harness tests — and that reading is
non-zero with the expected marker. The whole-suite form becomes observable and
is gated at `182.002-T`, which re-runs both commands verbatim against the tree
`182.001-T` has committed the assertion into.

## What this evidence does and does not authorize

* It **does** record that both P-004 channels, in the forms named above, were
  executed and observed, and that the `harness-ready` label was applied only
  afterwards.
* It **does** supply the authorization half of this unit's admission contract,
  which `182.001-T` reads fail-closed as its first action.
* It **does not** confer a claim, a shipment execution, a Ship authorization or
  a review verdict. It is an execution record, not a gate result.
* It **does not** waive, suspend, lower or scope any policy. P-002 and P-004
  are unedited; the installed Ship agent is unedited; no gate, grant, `--force`
  or force-audit entry is involved anywhere on this path.
* It **does not** describe anything performed inside installed Ship. `PRE-0` is
  a Stage-side producer act. No phase of `.github/agents/_ship.agent.md`
  performs it and no installed automation invokes it.

## Immutability

This artifact is **write-once**. It is not edited, amended or re-scoped. A
subsequent `PRE-0` execution — if one is ever needed — is recorded in a new
artifact alongside this one, and this file remains as the record of what was
observed on `2026-09-20` against base `3ad5fcc7`.
