---
title: "Stage session memory — 188-S / 187-S attempt-02 remediation"
date: 2026-09-20
agent: stage
session_kind: remediation-only
branch: chore/stage-176-s-workflow-defects
entry_head: da8f890a
shipments: [188-S, 187-S]
plans:
  - docs/plans/2026-09-20-harness-architect-bootstrap-plan.md
  - docs/plans/2026-09-18-ship-harness-lifecycle-foundation-plan.md
findings_remediated: [B2, S7, S8, S9]
findings_preserved_non_blocking: [B4]
stash_created: [1D0033E0, 703B6FAF]
---

# Stage — attempt-02 remediation for `188-S` and `187-S`

Remediation-only session. No push, no PR interaction, no shipment claim, no
Ship execution, no branch switch, no worktree. No source or template file was
written — Stage produced plans and backlog records only.

## Outcome

| Finding | Sev | Shipment | Disposition |
|---|---|---|---|
| `B2` | P2 | `188-S` | Remediated at plan revision 3 |
| `B4` | P3 | `188-S` | Preserved non-blocking, stash `1D0033E0` |
| `S7` | P1 | `187-S` | Remediated at plan revision 4 |
| `S8` | P2 | `187-S` | Remediated at plan revision 4 |
| `S9` | P2 | `187-S` | Remediated at plan revision 4 |

Nothing is **closed**. All five move to `findings_addressed_pending_review`;
only independent attempt 03 may close them. Both manifests carry `verdict: null`
and `gate_result: null` with `latest_disposition: REMEDIATED-PENDING-REVIEW`.

## `B2` — the real `UNIMPLEMENTED_MARKER` derivation

The attempt-02 finding was right that the plan cited a *nonexistent* "row for
that language". The two install-harness surfaces do different jobs:

* **`:335`** (Review Persona Variables table, header `:327`, columns
  `Template Variable | Source | Purpose`) is keyed **one row per variable** and
  has **no language rows**. It supplies only the keying rule
  *"Derived from `languages.primary`"*. Its `e.g.` list is illustrative and is
  **never** a value source.
* **`:130`** (table headed `:100`, columns `… | Example (Rust) | Example
  (TypeScript) | Example (Python)`) is the **only** per-language carrier, and is
  therefore the **value source**.

`languages.primary: "python"` (`.autoharness/workspace-profile.yaml:7`) selects
the `Example (Python)` column, giving the literal `raise NotImplementedError("...")`,
bound by **verbatim transcription**. The `"..."` message slot is *not* a prompt
to invent text — the parallel Rust/TS cells show the same placeholder, so filling
it would be improvisation. The two surfaces do not disagree: both carry the
detectable token `NotImplementedError`, which is what `182.002-T`'s red-phase
check asserts. Five fail-closed triggers `F1`–`F5` were added, including
unsupported/ambiguous language mapping; none fires for this workspace.

## `S7` — the inverted parity premise

Verified live state (and re-verified at commit time):

| Gate | Surface | Expected | Observed |
|---|---|---|---|
| `G1` | template `### Step 2: Harness Generation (P-002 / P-004)` | 1 | **1** |
| `G2` | mirror `### Step 2: Harness Generation*` | 0 | **0** |
| `G3` | mirror `### Step 1: Pre-Flight Checks` / `### Step 2: Task Execution Loop` | 1 / 1 | **1 / 1** |

The mirror has **zero** occurrences of `harness-ready` or `harness-architect`.
So the drift runs **template-ahead-of-mirror** — the exact inverse of what the
plan claimed. `181.005-T` now **updates the existing template section in place**
(never duplicates it) and **inserts** the mirror section, in one commit.

**Mirror heading is `### Step 1.5:`, not `### Step 2:`** — the mirror's own
Step 2 is the Task Execution Loop and **ten** passages reference it (lines 184,
214, 275, 283, 302, 305, 326, 336, 377, 748). Renumbering is forbidden.
Fractional numbering is already that file's convention (`0.1b`, `0.1c`, `0.5`).

The atomicity argument was rewritten: a split commit **widens** or **reverses**
the drift rather than creating it. Rollback is a single-commit revert whose
post-revert state is the *known pre-existing drift*, not a novel broken state.

## `S8` — `181.003-T` is not a `src/` task

Resolved in favour of the live record: an **inert agent-template / procedure
design task** producing **no Python**. Made exact by adopting the workspace's own
`169.011-T` precedent — it authors the canonical phase text as test-owned fixture
data at two named paths under `tests/fixtures/ship_harness_phase/`, which
`181.005-T` later transcribes.

This also makes *"inert"* literally true: the template's Step 2 is an **executed**
step, so editing it early would both break inertness and destroy `181.005-T`'s
atomicity.

Size/complexity re-derived against the **changed** scope: `M`/`high` → `S`/`medium`
(two separate `backlogit_update_item` calls, since `size` and `complexity` are
mutually exclusive mutation seams). `181.005-T` re-derived and **held** at
`M`/`high` — an atomic multi-file live-surface edit stays high-uncertainty even
when specified precisely. Final sizing: `S`/`S`/`S`/`XS`/`M`, `unsized: 0`.

## `S9` — provenance

Corrected to `source_stash_ids: [76EBDE6D]`. **Single-source**, verified against
the decision's portfolio table: line 993 assigns `76EBDE6D` to `P4 | 187-S |
181-F`; line 995 assigns `3EF5AAF2` to `177-S | 169-F`. `3EF5AAF2` was simply
another unit's ID. `76EBDE6D` is **archived** (`.backlogit/archive/stash.jsonl`
line 234), so every citation now records that path.

**Mid-session self-correction worth remembering.** My first P3 draft asserted
that `188-S` "has no source stash ID at all" and that attempt 02 had
mischaracterized the entry. Direct verification showed the `188-S` plan
frontmatter *does* declare `76EBDE6D` (pre-existing, untouched by this session),
so attempt 02's phrasing was grounded and defensible. Stash `703B6FAF` was
rewritten to the truthful **multi-consumer** finding. The `S9` remedy is
unaffected — `187-S`'s claim rests on line 993 alone.

A second self-correction: an earlier `P5` parity criterion claimed
`{{STATUS_QUEUED}}` binds from `harness-manifest.yaml` → `variables_used`. It is
**not** there; it binds from `.autoharness/backlog-registry.yaml` →
`status_values.queued` (line 249).

## Invariants re-verified

* `188-S` keeps the `dag-root` label and has **no** dependencies — a true source
  node, so the graph is acyclic.
* All **seven** `188-S` edges intact: `184-S` (archived, conditional D10),
  `185-S`, `186-S`, `187-S`, `176-S`, `178-S`, `180-S`.
* `187-S` dependencies are exactly `[188-S]`.
* D9 claim carve-out untouched; no waiver, no grant, no `--force`, no
  force-audit entry. `.autoharness/bootstrap-grants/` does not exist — the
  negative assertion is real.
* Immutable attempt artifacts under `docs/reviews/review-history/` **untouched**
  (git-clean).
* Stash diff is **2 insertions, 0 deletions** — 17 prior P3 follow-ups, `002-C`,
  the scratch bug report, the repaired checkpoint and untracked notes all
  preserved.
* Plans rewritten **coherently in place**; no append-log or correction-log
  headings anywhere.

## Next step

Both manifests await **independent attempt 03** — `188-S` against plan revision 3,
`187-S` against plan revision 4. Stage asserts no `PASS` and closes no finding.
