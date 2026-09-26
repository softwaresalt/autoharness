---
title: "IM-10 harness-architect render-parity release unit"
description: "Small release unit that closes IM-10. It re-renders the installed harness-architect skill from its template so the two match byte for byte, pins that one template to LF, and refreshes the skill's manifest checksum from raw staged-blob bytes. S(IM-10) runs after 195-S and before S(D)."
doc_type: plan
status: pending-review
created: 2026-09-26
supersedes: none
source_stash: 9144435A
operator_approval: OP-1
parent_plan: docs/plans/2026-09-25-ship-lifecycle-release-units-plan.md
requires_plan_hardening: "no"
---

# IM-10 harness-architect render-parity release unit

## Bottom Line

The installed `.github/skills/harness-architect/SKILL.md` differs from its template render by
a single line reflow in Step 5.2. It has no other content difference. This unit re-renders the
installed mirror from the template, adds a byte-exact parity test, pins that one template to
`eol=lf` and refreshes the manifest checksum under IM-12. The comparison stays byte-exact. The
unit is one feature and one shipment, S(IM-10), with two tasks. It sits behind 195-S and ahead
of S(D). Requires plan hardening: **no**. The change touches one skill mirror, one manifest
entry and one `.gitattributes` line, with no schema, CLI or multi-family template change.

## Problem

IM-10 (stash `9144435A`, approved by OP-1 on 2026-09-25T23:56:45-07:00): the byte-exact
render-parity resolver must not run against `harness-architect` at HEAD until the byte-4994
mismatch is reconciled in its own operator-approved unit. The byte comparison cannot be
loosened. Until IM-10 ships, the real resolver reports `STALE` for this surface, and D3
preflight (4) of the parent plan halts.

## Diagnosis

Diagnosed read-only at HEAD `530a4d26` from Git blobs. `_render_template` in
`src/autoharness/verify_workspace.py` was applied with the manifest's top-level
`variables_used` (41 keys), so the method matches Proof C run 4.

* Template: 7423 B, index `i/lf`, working tree `w/lf`, no `eol` attribute, no CRLF, no BOM.
* Installed: 7501 B, `attr/text eol=lf`, SHA-256 `39089629...9f36` (equals its manifest checksum).
* Render: 7501 B, SHA-256 `9ebaaaf8...d5b9`, 0 unresolved placeholders. The first difference is at byte 4994.

The template's line `` Run `{{TEST_COMMAND}}` for the harness tests, invoking exactly the ``
becomes a line of about 101 characters once rendered. The installed file was hand-reflowed to
about 72 characters. The unified diff (render, then installed) is the only hunk:

```diff
-Run `PYTHONPATH=src python -m unittest discover -s tests` for the harness tests, invoking exactly the
-resolved test command with no runner substitution. EVERY generated
-harness test MUST be discovered AND MUST fail with its own expected failure marker
-(raise NotImplementedError("...")); evaluate each test individually rather
-than relying on an aggregate non-zero exit code.
+Run `PYTHONPATH=src python -m unittest discover -s tests` for the harness tests,
+invoking exactly the resolved test command with no runner substitution.
+EVERY generated harness test MUST be discovered AND MUST fail with its
+own expected failure marker (raise NotImplementedError("...")); evaluate
+each test individually rather than relying on an aggregate non-zero
+exit code.
```

Both sides carry the same word sequence, so the gap is whitespace only.

## Decision

**Change the installed mirror, not the template.** Templates are the product. The installed
file is dogfood output and should be exactly `render(template, variables_used)`. A template-side
reflow would tie the product's line wraps to this repository's `TEST_COMMAND` length, which is
arbitrary for every other ecosystem, and it would need redoing whenever a variable changes.
`.markdownlint.json` enables only MD001, MD025 and MD041, so the long rendered line passes lint.

**Include only the narrow `eol=lf` pin.** Scope is the single line
`templates/skills/harness-architect/SKILL.md.tmpl text eol=lf` plus
`git add --renormalize` of that path. The parent plan's Risks row assigns the template pin to
IM-10, and the byte-exact test reads working-tree bytes. The blob is already `i/lf`, so
renormalize should change no blob. **The `templates/**` glob pin is deferred.** All 140
tracked templates are `i/lf`, but 134 are `w/crlf` in this Windows checkout
(`core.autocrlf=true`). A glob pin would churn the working tree and change line-ending policy
across the product, well beyond IM-10's one surface.

## Tasks

IM10-1 blocks IM10-2. Both are `harness-surface:none`: neither task's file budget contains a
Python production module under `src/`.

### IM10-1: Pin the harness-architect template to LF

| Field | Value |
|---|---|
| Files | `.gitattributes`; `tests/test_harness_architect_render_parity.py` (new) |
| Change | Add `templates/skills/harness-architect/SKILL.md.tmpl text eol=lf` with a comment naming IM-10 and the byte-exact surface. Run `git add --renormalize templates/skills/harness-architect/SKILL.md.tmpl`. If `git rev-parse :<tmpl>` differs from `git rev-parse HEAD:<tmpl>`, halt. Add a test asserting `git check-attr text eol` for the path reports `text: set` and `eol: lf` |
| Verification | `git ls-files --eol <tmpl>` shows `i/lf w/lf attr/text eol=lf`; the staged diff is `.gitattributes` plus the test only; the template blob is unchanged; full gate `PYTHONPATH=src python -m unittest discover -s tests` passes |
| Estimate | 40 min; size `S`; complexity `low` |

### IM10-2: Re-render the installed mirror and refresh its checksum

| Field | Value |
|---|---|
| Files | `.github/skills/harness-architect/SKILL.md`; `.autoharness/harness-manifest.yaml` (this entry's `checksum` and `note` only); `tests/test_harness_architect_render_parity.py` |
| Preflight (halt on any failure) | (a) The recorded checksum equals the SHA-256 of `HEAD:.github/skills/harness-architect/SKILL.md` (IM-12 drift check). (b) The render from the parent's template blob and top-level `variables_used` leaves 0 unresolved placeholders. (c) `render.split() == installed.split()` over bytes, so every difference is whitespace reflow. A non-whitespace difference is content drift and out of scope |
| Change | Write the installed file as exactly the render bytes: UTF-8, LF, no BOM, binary write. Add `test_installed_equals_template_render_byte_exact`. It reads raw working-tree bytes of both files, renders with the manifest's top-level `variables_used` through the verify renderer (`_render_template`, or `render_template` if B has landed it) and runs `assertEqual` on the bytes with no normalization. It also asserts that no placeholder is left and that the manifest checksum equals the SHA-256 of the installed bytes. Refresh the checksum from raw staged-blob bytes via a Python subprocess binary capture of `git cat-file -p :<path>` (no PowerShell text capture). Append an IM-10 note |
| Posture | Characterization-first. The new test's pre-edit failure, with its first-difference offset, is recorded as gap characterization, not RED |
| Verification | The new test and `tests/test_harness_architect_p004_contract.py` pass; after commit, the checksum equals the SHA-256 of `HEAD:<path>`; the template blob is unchanged; the full unittest gate passes; markdownlint passes on the installed file |
| Estimate | 60 min; size `S`; complexity `low` |

## Shipment Placement

* One feature, "IM-10 harness-architect render parity", holds IM10-1 and IM10-2. One shipment,
  S(IM-10), carries the feature, then IM10-1, then IM10-2.
* `backlogit dep add <S(IM-10)> 195-S --type blocks`. S(IM-10) gets no `dag-root` label, so
  192-S (S(A)) stays the only `dag-root` of the lifecycle DAG. Placing S(IM-10) after 195-S
  also puts it transitively after A2, which edits the same Step 5.2 section, so the re-render
  picks up A2's text. Preflight (c) guards against drift A2 might introduce.
* S(D) is harvested later with `blocks` edges from 195-S and from S(IM-10).

## Comparator Note

PE-ACTIVATE-01 / IM-08 comparator `08787a4b`: no manifest commit has landed since then (HEAD
`530a4d26`). For D3 preflight (1), this unit adds one manifest change: IM10-2's commit changes
the `.github/skills/harness-architect/SKILL.md` entry's `checksum` and `note`. The before and
after values are recorded in the task evidence. IM10-1 changes no manifest entry, because
`.gitattributes` is not checksummed. The Ship mirror entry is untouched.

## Risks

| Risk | Mitigation |
|---|---|
| A2 or a later edit adds non-whitespace template/mirror drift | IM10-2 preflight (c) halts, and the drift goes to the operator |
| Checkout leaves the pinned template CRLF | IM10-1 verifies `w/lf`, and the byte-exact test fails closed |
| Renderer renamed by B | The test uses whichever name exists. B asserts `render_template is _render_template` |
| A future template reflow breaks parity | That is intended. The byte-exact test fails and is never loosened |

## Out of Scope

A `templates/**` or other broad `eol=lf` pin; renderer or comparison changes; parity for any
other skill; resolver activation; S(D) harvest; archiving stash `9144435A`, which follows the
IM-10 harvest.

## Non-claim

This unit makes no claim of race, TOCTOU or hardlink-alias resistance. Its checks are
point-in-time byte comparisons over Git blobs and working-tree files.
