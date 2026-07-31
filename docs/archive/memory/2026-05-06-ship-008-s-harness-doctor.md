---
session: ship-008-s
date: 2026-05-06
shipment: 008-S
pr: 34
merge_sha: 87ad630386909e9130fdca493b6250cf39b4f100
branch: feat/harness-doctor-skill
---

# Ship Session: 008-S — Harness Health-Check Skill

## Summary

Executed 008-S (Harness Health-Check Skill) from claimed state through
merged PR. Also closed the previously-stale 006-S shipment on the same branch
(administrative-only change, no new templates).

## Tasks Completed

| Task | Title | Result |
|---|---|---|
| 006-S | Close stale shipment (administrative) | Archived — `7d0074c` |
| 008.001-T | Create harness-doctor skill template | Done |
| 008.002-T | Register health-check variables in install-harness | Done |

## Files Changed

* `templates/skills/harness-doctor/SKILL.md.tmpl` — New. 7-phase health-check
  skill. Variables: `{{HARNESS_MANIFEST_PATH}}`, `{{AUTOHARNESS_VERSION}}`.
* `.github/skills/install-harness/SKILL.md` — Added Health-Check Variables
  section (~312–325), moved harness-doctor to new "Always-installed skills"
  subsection (Step 2.5 item 3), added to Primitive 1 + 5 mappings.

## Key Decisions

1. **mode:fix uses quarantine, not deletion** — Phase 6 of harness-doctor
   moves orphaned `.tmpl` files to `.autoharness/quarantine/` rather than
   deleting. Consistent with Primitive 5 destructive-action approval
   requirement. Operator must review quarantine before permanent removal.

2. **Manifest field is `artifacts`, not `entries_added`** — harness-doctor
   Phase 1 reads `artifacts[*].path` from the manifest. `entries_added` is
   a VS Code settings sub-field only.

3. **Cross-reference links in templates are file-relative** — template files
   live in `templates/skills/harness-doctor/SKILL.md.tmpl`; installed output
   lives in `.github/skills/harness-doctor/SKILL.md`. Links must resolve from
   the *installed* output location, not the template source path.

4. **harness-doctor is always-installed** — Must appear in its own
   "Always-installed skills" subsection in install-harness, separate from the
   conditional "Universal skills" block, to avoid a logical contradiction.

## PR Review Notes

5 Copilot review threads on PR #34. All fixed in commit `34f1160`:
1. `entries_added` → `artifacts` in template (schema confusion)
2. File-relative links fixed (template vs installed path)
3. mode:fix deletion → quarantine (destructive action policy)
4. harness-doctor moved to Always-installed subsection (contradiction fix)
5. 008-S active status acknowledged (correct for in-flight PR; archived post-merge)

All 5 threads replied to. All 5 resolved programmatically via
`resolveReviewThread` GraphQL mutation.

## Backlogit State After Closure

* 008-S: `shipped` (SHA: `87ad630`)
* 008-F, 008.001-T, 008.002-T: `archived`
* Next shipment: **009-S** (Agent Session Discipline and Workflow Boundaries — high priority)

## Compound Learnings Written

* `docs/compound/2026-05-06-harness-manifest-artifacts-vs-entries-added.md`
* `docs/compound/2026-05-06-template-variable-escaping-in-docs.md`
* `docs/compound/2026-05-06-github-review-comment-id-types.md`
