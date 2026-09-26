---
type: decision
date: 2026-09-16
agent: Stage
subject: "autoharness bug report — pipeline-topology branch_ownership ignores custom_fields.implementation_branch"
status: OPEN
kind: bug-report
target_workspace: autoharness
severity: high
related_shipments: ["025-S", "020-S"]
related_policies: ["P-022"]
precedent: docs/decisions/2026-09-15-stage-020f-reslice-and-024s-disposition.md#9
---

# autoharness bug — pipeline-topology `branch_ownership` ignores explicit `implementation_branch`

## TL;DR

The installed `autoharness gate pipeline-topology` `branch_ownership` check derives its
`expected_branches` set **only from the shipment `title`** and ignores the authoritative
`custom_fields.implementation_branch` contract. A shipment sitting on its own valid P-022
release-unit branch is therefore **false-blocked** with `BRANCH_MISMATCH`, and because the
block is fail-closed with no honored explicit contract, agents can neither claim nor legitimately
force past it. Resolution requires an explicit-contract-first resolution precedence in the
topology resolver, applied uniformly across all phases.

This report is filed for the **autoharness workspace** (the gate implementation lives in the
installed `autoharness` package, `autoharness/gates/topology.py`). It is not a defect in this
product repository's backlog data.

## Severity and impact

- **Severity: high. Impact: false fail-closed block of a valid P-022 branch.**
- The gate returns `blocked: true`, `token: BRANCH_MISMATCH`, `exit_code: 1` while the working
  tree is checked out on exactly the branch named in the shipment's authoritative
  `custom_fields.implementation_branch`.
- The block is **not forceable in good conscience**: there is no honored explicit-contract path,
  so an agent's only escapes are (a) an unsafe `--force` that bypasses a legitimate check, or
  (b) renaming the branch away from its authoritative P-022 contract to satisfy a title-derived
  slug. Both are wrong. The correct P-022 branch is punished for not matching a generic
  title-derived alias.
- Blast radius: **every** story-slice / ADO-ID-led release-unit shipment whose descriptive
  prose title does not slugify to its explicit branch name. On this feature that is at least
  020-S (see precedent) and 025-S.

## Exact reproduction

Environment: `autoharness` (installed), gate `pipeline-topology`; shipment `025-S`; current
branch `feat/20966-retry-failure-dead-letter`.

Authoritative facts on `025-S` (from `backlogit get 025-S`):

- `custom_fields.implementation_branch: feat/20966-retry-failure-dead-letter`
- Current git branch: `feat/20966-retry-failure-dead-letter` (exact match to the contract).

Command:

```text
autoharness gate pipeline-topology --mode agent --shipment 025-S --phase pre_claim --json
```

Actual result (pre-fix, with the original descriptive prose title
`NVD consumer: retry, failure, and dead-letter handling + NV-F4 feature close (AB#20966)`):

```json
{
  "phase": "pre_claim",
  "target_shipment_id": "025-S",
  "blocked": true,
  "message": "BRANCH_MISMATCH: current branch feat/20966-retry-failure-dead-letter does not match target 025-S",
  "checks": [
    {
      "name": "branch_ownership",
      "status": "blocked",
      "token": "BRANCH_MISMATCH",
      "details": {
        "current_branch": "feat/20966-retry-failure-dead-letter",
        "expected_branches": [
          "feat/025-s-nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close",
          "feat/025-s-nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close-ab-20966",
          "feat/nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close",
          "feat/nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close-ab-20966",
          "chore/025-s-nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close",
          "chore/025-s-nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close-ab-20966",
          "chore/nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close",
          "chore/nvd-consumer-retry-failure-and-dead-letter-handling-nv-f4-feature-close-ab-20966"
        ]
      }
    }
  ],
  "token": "BRANCH_MISMATCH"
}
```

**Expected behavior:** because the checked-out branch equals the shipment's explicit
`custom_fields.implementation_branch`, `branch_ownership` must PASS regardless of what the
title slugifies to. `expected_branches` (or a superseding resolved value) must include the
explicit contract branch, and the JSON must report that the branch was resolved from the
explicit contract.

## Root cause

In `autoharness/gates/topology.py`, the acceptable-branch set is computed purely from the
shipment title:

```text
_branch_aliases(shipment):
    base = _strip_parenthetical(shipment.title) or shipment.title
    aliases = { _slugify(title), _slugify(base),
                _slugify(f"{id} {title}"), _slugify(f"{id} {base}") }

# canonical = feat/<alias> + chore/<alias> for each alias
```

`branch_ownership` compares the current branch against this title-only `canonical` set. The
resolver **never reads `custom_fields.implementation_branch`**, even though that field is the
authoritative P-022 branch contract. When the descriptive prose title does not slugify to the
explicit branch (the normal case for ADO-ID-led story-slice branches), no alias matches and the
gate false-blocks. The title aliases are a reasonable *fallback*, but they are being used as the
*only* source of truth.

## Required resolution — precedence (P-022)

The topology resolver must resolve the expected branch with this strict precedence, stopping at
the first tier that yields a value:

1. **Explicit contract (highest):** `custom_fields.implementation_branch` when present and
   well-formed. When present, it is authoritative and, on an exact match to the current branch,
   `branch_ownership` PASSES irrespective of the title.
2. **Configured naming convention:** a workspace/customer-configured branch naming rule (e.g., an
   `implementation_branch_rule` / configured convention) when no explicit branch is set.
3. **Generic title-derived aliases (lowest / fallback only):** the existing
   `feat/`-`chore/` title + `<id> title` slug aliases, used **only** when neither an explicit
   branch nor a configured convention is available.

This mirrors P-022 precedence: explicit shipment/release-unit branch contract first, configured
convention second, generic title-derived fallback last.

## Fail-closed behavior for malformed explicit values

- When `custom_fields.implementation_branch` **is present but malformed** (empty, whitespace,
  not a valid ref, contains illegal characters, or is otherwise unparseable), the gate MUST
  **fail closed with a distinct token** (e.g., `IMPLEMENTATION_BRANCH_MALFORMED`) and MUST NOT
  silently fall back to the title-derived aliases. A present-but-broken explicit contract is an
  authoring error that must surface, not be masked by a generic slug that might accidentally
  match some branch.
- Only a **genuinely absent** explicit field advances to tier 2, then tier 3. Absence is not
  malformation.

## Implementation guidance (topology resolver)

- Introduce a single `resolve_expected_branches(shipment, config)` helper that returns both the
  ordered candidate branch set **and** the `resolution_source` tier that produced it.
- Tier 1 reads `shipment.custom_fields["implementation_branch"]`, normalizes (`refs/heads/`
  stripping, trim), validates, and on validation failure raises the malformed fail-closed path.
- Keep `_branch_aliases` as the tier-3 fallback generator only.
- Route **every** phase branch-ownership evaluation through this one helper so behavior is
  identical for `pre_claim`, `post_claim`, `lifecycle`, and `ambient`. Today each phase builds
  `canonical` from `_branch_aliases`; all such call sites must switch to the shared resolver so
  no phase retains the title-only path.
- Preserve the existing CI-env / default-branch fallbacks unchanged; this change concerns only
  how the *expected target-shipment branch* is derived.

## JSON diagnostics requirements

The gate JSON `details` for `branch_ownership` must additionally emit:

- `resolution_source`: one of `explicit_implementation_branch` | `configured_convention` |
  `title_alias_fallback` (and the malformed path emits the fail-closed token).
- `selected_branch`: the single expected branch chosen by precedence (when explicit/convention
  resolves), alongside the existing `current_branch`.
- `expected_branches`: the ordered candidate list actually compared against, so operators can see
  precedence applied rather than an opaque title-only set.

## Regression matrix

| # | Scenario | Expected outcome |
|---|---|---|
| 1 | Explicit `implementation_branch` matches current branch; **title mismatches** | PASS; `resolution_source: explicit_implementation_branch` |
| 2 | Explicit `implementation_branch` set, but the **derived title alias branch** is the one checked out | BLOCK `BRANCH_MISMATCH` (explicit contract is authoritative; the title-alias branch is not the contract) |
| 3 | Explicit `implementation_branch` present but **malformed** | FAIL CLOSED `IMPLEMENTATION_BRANCH_MALFORMED`; no title fallback |
| 4 | **No** explicit branch; configured naming convention present and matches current | PASS; `resolution_source: configured_convention` |
| 5 | No explicit branch, no convention; current matches a generic title alias | PASS; `resolution_source: title_alias_fallback` |
| 6 | Explicit branch nested under `custom_fields:` in YAML frontmatter is parsed correctly | Tier-1 value read from nested `custom_fields.implementation_branch`, not only top-level keys |
| 7 | `025-S` fixture: title `20966 Retry failure dead letter (AB#20966)` OR any prose title, explicit `feat/20966-retry-failure-dead-letter`, current branch `feat/20966-retry-failure-dead-letter` | PASS; `resolution_source: explicit_implementation_branch` |

Row 6 is called out because the resolver must read the branch from the **nested**
`custom_fields` map, matching how `backlogit` frontmatter stores shipment contract fields.

## Acceptance criteria

- With the fix installed, running the pre_claim reproduction against an **unaliased** descriptive
  prose title on `025-S` (explicit `implementation_branch` = current branch) PASSES
  `branch_ownership` with no `BRANCH_MISMATCH`.
- All seven regression rows pass.
- The gate JSON emits `resolution_source`, `selected_branch`, and an ordered `expected_branches`.
- Malformed explicit values fail closed with a distinct token and never fall through to title
  aliases.
- All four phases (`pre_claim`, `post_claim`, `lifecycle`, `ambient`) share one resolver and
  exhibit identical precedence behavior.

## Non-goals

- Not changing branch **naming policy** itself, nor auto-renaming any branch.
- Not altering the CI-env branch fallback, default-branch resolution, `worktree_uniqueness`,
  `active_invariant`, `consistency`, or `shipment_readiness` / predecessor-closure checks.
- Not changing `backlogit` frontmatter schema; the explicit field already exists.
- Not weakening fail-closed semantics — this makes the gate *more* correct, not more permissive.

## Local workaround (in effect now) and removal criteria

Until the autoharness fix ships, the local workaround (mirroring the 020-S precedent in
`docs/decisions/2026-09-15-stage-020f-reslice-and-024s-disposition.md` section 9) is an
**ADO-ID-led title compatibility alias** on the queued shipment, leaving the explicit branch
contract authoritative and unchanged:

- `025-S` title set to `20966 Retry failure dead letter (AB#20966)` via the official
  `backlogit update 025-S --title ...` mutation surface. Under the current title-only resolver
  this deterministically derives (`_strip_parenthetical` -> `_slugify`)
  `20966-retry-failure-dead-letter`, so `feat/20966-retry-failure-dead-letter` is included in
  `expected_branches` and `branch_ownership` passes.
- `custom_fields.implementation_branch: feat/20966-retry-failure-dead-letter` is **unchanged and
  remains authoritative**. The branch was **not** renamed or recreated.
- A gate-compatibility note is recorded in the `025-S` body flagging the title as temporary.

**Removal criteria:** once this fix (explicit `implementation_branch` precedence) is installed and
regression row 7 passes with a descriptive prose title, retire the alias and restore the
descriptive title on `025-S` (and 020-S). The alias exists solely to satisfy the title-only
resolver and carries no authoritative meaning.

## Precedent

See `docs/decisions/2026-09-15-stage-020f-reslice-and-024s-disposition.md` section 9 for the
first application of this ADO-ID-led title alias workaround (shipment 020-S). This report does
not duplicate that history; it generalizes the underlying defect and specifies the autoharness
resolver fix that will let both aliases be retired.
