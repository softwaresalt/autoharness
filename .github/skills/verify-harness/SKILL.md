---
description: "Multi-model adversarial verification of installed or tuned harness artifacts using parallel reviewers with consensus-based finding assembly and auto-remediation"
---

## Adversarial Harness Verification

Dispatch multiple independent reviewer subagents — each using a different model —
to audit installed harness artifacts against their authoritative templates, overlay
coherence requirements, and cross-reference contracts. Assemble findings into a
confidence-weighted consensus report and auto-remediate confirmed defects.

This skill is the final guardrail after deterministic verification (template
variable sweep, cross-reference sweep, overlay coherence sweep, structural
validation). Deterministic checks catch mechanical defects; adversarial
verification catches semantic defects that mechanical checks miss: dropped
template content, stale references to deprecated agents, incomplete overlay
weaving, missing skills from discovery tables, and workspace-profile drift.

## When to Use

Invoke as the final step of:

* install-harness Phase 4 (after Step 4.4 structural validation)
* tune-harness Phase 5 (after the deterministic verification pass)

The skill is mandatory for `standard` and `full` presets. It may be skipped for
`starter` preset or when `--skip-adversarial` is explicitly passed.

## Inputs

* `autoharness_home`: (Required) Path to the autoharness installation.
* `workspace_path`: (Required) Path to the target workspace root.
* `manifest_path`: (Required) Path to `.autoharness/harness-manifest.yaml`.
* `reviewers`: (Optional, default 3) Number of parallel reviewer instances. Minimum 2.
* `auto_remediate`: (Optional, default true) Apply HIGH-confidence fixes automatically.
* `scope`: (Optional, default `all`) One of `all`, `new-only` (only artifacts
  created or modified in the current install/tune session), or a comma-separated
  artifact path list.

## Output

* Verification findings appended to the install/tune report
* Auto-remediated artifacts (when `auto_remediate` is true)
* Remaining findings requiring operator review

## Required Protocol

### Phase 1: Assemble Review Payload

1. Read `.autoharness/harness-manifest.yaml` to identify all installed artifacts,
   their source templates, capability packs, and overlay targets.
2. Read `.autoharness/config.yaml` and `.autoharness/workspace-profile.yaml` for
   the workspace context (language, packs, docs paths, prefix map).
3. Build the review payload — a structured map of:
   * Every installed artifact path and its source template path
   * Every enabled capability pack and its declared overlay targets
   * The skills table from `AGENTS.md` and `copilot-instructions.md`
   * The actual skill directories in `.github/skills/`
   * The actual agent files in `.github/agents/` and `.github/agents/review/`
   * The "Where to look next" or equivalent discovery table in `AGENTS.md`
   * The workspace profile's capability pack detection flags

### Phase 2: Define Review Domains

Split the review into three independent domains so each reviewer can be
dispatched in parallel:

| Domain | Focus | Key Checks |
|---|---|---|
| **Template Fidelity** | Compare every installed artifact against its source template | Dropped content, unresolved variables, missing sections, incorrect variable resolution, missing Model Routing sections |
| **Overlay Coherence** | Verify each enabled pack is consistently woven | Pack instruction file exists, foundation docs reference the pack, pipeline agents declare pack tools, skills reference pack instruction file, overlay targets contain pack behavior keywords |
| **Cross-Reference Integrity** | Verify all discovery tables, policy references, and agent→skill→reviewer chains resolve | Skills table complete vs actual skills, reviewer table complete vs actual reviewers, policy agents are installed agents (not skills), profile detection flags match installed packs, deprecated agent references cleaned up |

### Phase 3: Dispatch Parallel Reviewers

Launch one reviewer subagent per domain. Each reviewer MUST use a **different
model** to ensure genuine diversity of critique:

| Reviewer | Domain | Suggested Model Tier |
|---|---|---|
| Reviewer A | Template Fidelity | Tier 3 (Frontier) |
| Reviewer B | Overlay Coherence | Tier 2 (Standard, different vendor) |
| Reviewer C | Cross-Reference Integrity | Tier 1 or Tier 2 (different from A and B) |

Each reviewer receives:

* The review payload from Phase 1
* Read access to the workspace and autoharness template directories
* Instructions to return **structured JSON findings only**

Each reviewer produces a JSON array:

```json
[
  {
    "severity": "CRITICAL|MAJOR|MINOR",
    "domain": "template-fidelity|overlay-coherence|cross-reference",
    "file": "affected file path in workspace",
    "template": "source template path (if applicable)",
    "issue": "precise description of the defect",
    "fix": "specific remediation action",
    "auto_fixable": true|false
  }
]
```

Do not proceed to Phase 4 until all reviewers have returned results.

### Phase 4: Consensus Assembly

Collect all finding arrays. For each unique finding (keyed by `file` + `issue`
semantic match):

1. **Count agreement**: How many reviewers flagged this finding or a
   semantically equivalent one?
2. **Assign confidence tier**:
   * **HIGH**: Flagged by 2+ reviewers, or flagged by 1 reviewer and
     independently verifiable by reading the file (e.g., missing section,
     wrong path)
   * **MEDIUM**: Flagged by 1 reviewer with plausible evidence but not
     mechanically verifiable without reading both template and installed file
   * **LOW**: Flagged by 1 reviewer with weak or speculative evidence
3. **Resolve severity conflicts**: Use the most conservative (highest) severity
   when reviewers disagree.
4. **Verify before classifying HIGH**: For every finding a reviewer marks as
   CRITICAL or MAJOR, the assembler MUST read the actual file to confirm the
   defect exists. Downgrade to MEDIUM if the file content does not match the
   finding. This prevents hallucinated findings from triggering auto-remediation.

### Phase 5: Auto-Remediation

When `auto_remediate` is true, apply fixes for findings that meet ALL of these:

* Confidence: HIGH
* `auto_fixable`: true
* The fix is additive (adding missing content) or corrective (fixing a reference)
  — never destructive (deleting content the operator may have intentionally added)

For each auto-fix:

1. Back up the target file to `.autoharness/backups/{YYYY-MM-DD}/`
2. Apply the fix
3. Re-verify the fix did not introduce new issues (re-run the specific
   deterministic check that covers this artifact)
4. Record the fix in the verification report

Fixes that are destructive, ambiguous, or MEDIUM/LOW confidence are presented to
the operator for manual review.

### Phase 6: Produce Report

Append to the install/tune report:

```markdown
## Adversarial Verification

### Reviewer Dispatch
- Reviewer A (Template Fidelity): {model} — {finding_count} findings
- Reviewer B (Overlay Coherence): {model} — {finding_count} findings
- Reviewer C (Cross-Reference Integrity): {model} — {finding_count} findings

### Consensus Findings (ordered by confidence × severity)

#### HIGH Confidence
| # | Severity | Domain | File | Issue | Status |
|---|---|---|---|---|---|
| 1 | CRITICAL | {domain} | {file} | {issue} | AUTO-FIXED / NEEDS REVIEW |

#### MEDIUM Confidence
...

#### LOW Confidence
...

### Auto-Remediation Summary
- Findings auto-fixed: {count}
- Findings requiring manual review: {count}
- False positives dismissed: {count}

### Verification Result: {PASS|PASS WITH WARNINGS|FAIL}
```

**PASS**: Zero HIGH-confidence CRITICAL/MAJOR findings remaining after
auto-remediation.

**PASS WITH WARNINGS**: All HIGH-confidence findings resolved; MEDIUM findings
remain for operator review.

**FAIL**: HIGH-confidence CRITICAL or MAJOR findings remain that could not be
auto-remediated.

## Behavioral Constraints

* Never auto-fix a finding that removes content — only add or correct
* Never auto-fix based on a single reviewer's LOW-confidence finding
* Always read the actual file content before classifying a finding as HIGH
  confidence — do not trust reviewer claims without verification
* Back up every file before modification
* If fewer than 2 reviewer instances return results, halt and report the failure
  rather than proceeding with single-model findings

## Model Routing

This skill operates at **Tier 2 (Standard)** for consensus assembly. Individual
reviewers operate at their assigned tiers (one per tier when 3 reviewers are used).

## Subagent Depth

Maximum 1 hop. This skill dispatches reviewer subagents that are leaf executors
(no further subagent spawning).
