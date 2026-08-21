---
title: "Are the four divergent template/dogfood pairs mechanically renderable, or paired-edit maintained?"
source: docs/decisions/2026-08-20-template-dogfood-render-parity-spike.md
doc_type: decision
stash_id: 6D62077C
docline:
  type: spike
  date: 2026-08-20
  time_box: "single Stage session, read-only"
  conclusion: "adopt paired-edit contract; do not extend the renderer"
  confidence: "high"
  linked_parent_work_item: null
  promoted_to: ["docs/plans/2026-08-20-template-dogfood-paired-edit-contract-plan.md"]
  tags:
    - "templates"
    - "dogfood"
    - "verification"
    - "maintenance-contract"
---

# Spike - template/dogfood render parity (`6D62077C`)

Date: 2026-08-20
Agent: Stage (read-only investigation; planning only - Ship executes)
Stash source: `6D62077C` (medium, spike, P-021 C2 `DEFERRED SCOPE EXPANSION`)
Source refs: task `134.011-T`, feature `134-F`, shipment `143-S`, PR #373 (reconciled), merge-base `94898dc7`
Route: claude-opus-5 / anthropic / high (P-013.5, inherited)

## Question

Four pairs do not achieve whole-file byte-identity through
`autoharness.verify_workspace._render_template`:

* `templates/agents/_ship.agent.md.tmpl` <-> `.github/agents/_ship.agent.md`
* `templates/agents/_stage.agent.md.tmpl` <-> `.github/agents/_stage.agent.md`
* `templates/agents/_orchestrator.agent.md.tmpl` <-> `.github/agents/_orchestrator.agent.md`
* `templates/instructions/github-pr-automation.instructions.md.tmpl` <-> `.github/instructions/github-pr-automation.instructions.md`

Should we (a) extend the renderer so these are mechanically reproducible, or
(b) formally define them as paired-edit maintained?

## Conclusion

**(b) - formally define them as paired-edit maintained. Do not extend the
renderer.** Confidence: **high**. The evidence is stronger and more decisive
than the stash entry anticipated, and it **falsifies the entry's own stated
premise**.

## Findings

### F1 - `_render_template` is pure substitution (confirms the entry)

`src/autoharness/verify_workspace.py:1147`:

```python
def _render_template(content: str, variables: dict[str, str]) -> str:
    rendered = content
    for key, value in variables.items():
        rendered = rendered.replace("{{" + key + "}}", value)
    return rendered
```

No conditional-block handling of any kind. Confirmed as stated.

### F2 - Measured byte deltas: the four pairs are NOT a homogeneous set

| Pair | template bytes | dogfood bytes | delta | delta % |
|---|---:|---:|---:|---:|
| `_ship` | 95,669 | 68,360 | 27,309 | 28.5% |
| `_stage` | 64,859 | 41,420 | 23,439 | 36.1% |
| `_orchestrator` | 53,147 | 35,954 | 17,193 | 32.4% |
| `github-pr-automation` | 38,396 | 37,671 | 725 | **1.9%** |

The stash entry's "tens of KB" characterisation holds for the three **agent**
pairs but is wrong for the fourth by two orders of magnitude. Any disposition
must not assume one cause covers all four.

### F3 - The divergence is BIDIRECTIONAL, which falsifies the entry's premise

The stash entry frames the fix as *"stripping tens of KB from the .tmpl sources
or expanding the dogfood files by tens of KB"* - i.e. it assumes the dogfood file
is a **subset** of the rendered template (classic conditional stripping). It is not.

Rendering each template with the workspace's own derived variables and comparing
non-empty lines in **both** directions:

| Pair | dogfood lines | dogfood lines absent from rendered | rendered lines | rendered lines absent from dogfood |
|---|---:|---:|---:|---:|
| `_ship` | 692 | **508 (73%)** | 880 | **697 (79%)** |
| `_stage` | 467 | 319 (68%) | - | - |
| `_orchestrator` | 216 | 87 (40%) | - | - |
| `github-pr-automation` | 635 | 54 (8.5%) | - | - |

Pure conditional stripping would yield **~0** dogfood lines absent from the
rendered output. Instead, for `_ship`, 73% of the dogfood file does not appear
in the rendered template **and** 79% of the rendered template does not appear in
the dogfood file. These are two substantially independently-authored documents
sharing a common ancestor and a common section structure - not a template and
its rendering.

### F4 - Three distinct causes, not one

1. **Install-time conditional content** (3 agent pairs). Templates carry
   `backlog-md` and "no backlog tool" branches (`_ship`: 2 and 2; `_stage`: 2
   and 1; `_orchestrator`: 0 and 1) that the backlogit-installed dogfood copies
   correctly do not contain. Real, by design, not reproducible by substitution.
2. **Semantic prose drift** (all four, dominant in `github-pr-automation`). The
   `github-pr-automation` pair has **zero** `backlog-md` / "no backlog tool"
   markers on either side, so conditional content cannot explain its 725-byte
   delta. Diffing shows genuine normative drift, e.g. the template says a hard
   gate that misses **"operator-visible review data"** is unsafe while the
   dogfood copy says **"blocking data"**; the template requires a **"fresh"**
   local review readiness record, the dogfood copy merely requires one. These
   are meaning-bearing differences, and the dogfood copy is the **stale** side.
3. **Variable-derivation coverage gap** (see F5).

### F5 - `_derive_template_variables` does not cover the variables the templates use

Rendering with the workspace's own manifest/config/profile/registry leaves
unresolved `{{...}}` placeholders in the output:

| Pair | unresolved vars remaining | examples |
|---|---:|---|
| `_ship` | 6 | `{{ESCALATION_FAMILY}}`, `{{ESCALATION_PROVIDER}}`, `{{DEFAULT_BRANCH}}`, `{{CONTINUOUS_LEARNING_PROMOTION_THRESHOLD}}` |
| `_stage` | 4 | `{{ESCALATION_FAMILY}}`, `{{ESCALATION_PROVIDER}}`, `{{ESCALATION_REASONING_EFFORT}}` |
| `_orchestrator` | 10 | `{{ORCHESTRATOR_FAMILY}}`, `{{ORCHESTRATOR_PROVIDER}}`, `{{DEFAULT_BRANCH}}` |
| `github-pr-automation` | 1 | `{{FORMAT_CHECK_COMMAND}}` |

`FORMAT_CHECK_COMMAND` is absent from the derived variable map entirely;
`LINT_COMMAND` derives to the empty string. Yet the escalation route
(`gpt-5.6-sol` / `openai` / `high`) and the default branch are both plainly
present in `.autoharness/config.yaml`.

Per this project's own contract - *"Unresolved variables in output files
indicate an installation error"* - this is a **genuine defect in its own right**,
and it is **independent of** the parity question.

**It is NOT folded into this shipment.** It was discovered during Stage's own
spike, was not part of the authorised scope, and touches a different surface
(`src/autoharness/verify_workspace.py` variable derivation, i.e. install
correctness). Per P-021 C1 it is captured as a **new deferred stash entry** and
deliberately excluded here.

## Why not extend the renderer

Making these four pairs mechanically reproducible would require **all** of:

1. Building a conditional-block template engine (pack-aware / backlog-tool-aware
   stripping) where none exists today.
2. Closing the `_derive_template_variables` coverage gap (F5).
3. Reconciling roughly **1,200 lines** of bidirectional semantic drift (F3) -
   and for every drifted normative sentence, **deciding which side wins**.

Step 3 is the disqualifier. It is not mechanical work; it is a correctness-bearing
editorial decision per sentence, on the harness's own governing agent contracts,
at a volume no bounded shipment can responsibly absorb. Attempting it inside a
"parity" change would silently rewrite live agent policy under cover of a
refactor. That is precisely the failure mode P-021 exists to prevent.

`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`
is directly on point: when a check flags long-standing intentional customisation,
the answer is to describe reality accurately, not to bend the artifacts to satisfy
the check.

## Chosen direction

Formally define the maintenance contract that already exists in practice:

1. **Declare** the divergent pairs paired-edit maintained, in a durable document,
   with the F4 cause taxonomy recorded per pair.
2. **Pin** the set. `tests/test_scope_containment_policy_contract.py` already
   asserts marker-presence-plus-manifest-checksum for these four and full byte
   identity for the four clean pairs. Keep that split, but make the divergent
   set an explicit, named, reviewed inventory so a **new** pair silently joining
   it is a test failure rather than a shrug.
3. **State the obligation**: editing either side of a paired-edit file obliges the
   author to consider the other side in the same change, and to refresh the
   manifest checksum.

This changes no agent behaviour. It documents and enforces the status quo.

## Explicitly out of scope

* Reconciling the semantic prose drift found in F3/F4(2) - a large, separate,
  correctness-bearing effort. The `github-pr-automation` drift is the smallest
  and most tractable instance and is the natural first candidate, but it is
  **not** authorised here.
* Fixing the F5 variable-coverage gap - captured as a new deferred stash entry.
* Any change to `_render_template` itself.

## Traceability

* Stash `6D62077C` - reconciled in place (PR #373 recovered; review-thread
  confirmed legitimately absent). Duplicate scan: CLEAN.
* Plan: `docs/plans/2026-08-20-template-dogfood-paired-edit-contract-plan.md`
