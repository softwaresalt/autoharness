---
title: "FOUNDATION_ASSERTIONS must be anchored to section-specific phrases, not filenames"
problem_type: assertion-too-weak
category: verify_workspace
root_cause: "A filename-only assertion (e.g., 'browser-automation/SKILL.md') passes even when the filename survives in overlay prose after the manifest entry is deleted. Assertions must include surrounding section-specific text to confirm the target is in the right location."
tags: [verify_workspace, FOUNDATION_ASSERTIONS, assertion-anchoring, regression-coverage]
shipment: 007-S
date: 2026-05-05
---

## Problem

When adding `FOUNDATION_ASSERTIONS` for new skill manifest entries, the naive approach searches for the bare filename:

```python
{
    "name": "install_harness_browser_skill_manifest",
    "file": ".github/skills/install-harness/SKILL.md",
    "must_contain": ["browser-automation/SKILL.md", "iterative-experiment/SKILL.md"],
}
```

This assertion passes as long as those strings appear anywhere in the file. If the manifest bullet is deleted but the filename still appears in overlay prose (e.g., "The browser-automation/SKILL.md overlay..."), the assertion reports success even though the manifest regression it was meant to detect has occurred.

## Fix

Anchor assertions to section-specific surrounding text that cannot survive from prose alone:

```python
"must_contain": [
    "`browser-automation/SKILL.md` — Install when `browser-verification` is enabled",
    "`iterative-experiment/SKILL.md` — Install when `iterative-experiment` is enabled",
]
```

The surrounding backtick-em-dash pattern is unique to the manifest bullet format and will not appear in overlay prose.

## Note on backtick rendering

When the must_contain string contains Markdown inline code (backticks), be precise about the exact rendered text. The closing backtick before the em-dash must be included in the assertion substring. Test the assertion against the actual file content before committing.

## Pattern

For any FOUNDATION_ASSERTION verifying that a file is listed in a specific section:
- Include enough surrounding context to identify the section (table row phrase, list item format, heading prefix)
- Never rely on a bare filename that could appear in unrelated prose
