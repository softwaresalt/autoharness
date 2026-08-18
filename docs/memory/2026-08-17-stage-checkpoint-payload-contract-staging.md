# Stage — Root-cause fix staged for checkpoint payload contract (130-F / 139-S)

Date: 2026-08-17
Agent: Stage
Route: claude-opus-5 / anthropic / high
Mode: normal sequential
Branch: `chore/stage-138-S`
Scope: staging only. No source, template, config or test file was modified. No
build, no claim, no publish, no PR, no merge.

## What this session did

Took stash bug `E0B80A6C` — filed earlier today when a malformed Stage checkpoint
was quarantined — through the full staging pipeline and sequenced it *ahead* of
the storage-root migration `138-S`.

## Root cause (confirmed, not assumed)

`backlogit checkpoint create --help` states that a dump is validated as V1 and has
`created_at` / `updated_at` / `status` auto-populated **only when it declares
`schema_version=1`**. A payload omitting that field is neither validated nor
completed — it is written through verbatim and fails later at `checkpoint get`,
i.e. precisely during crash recovery.

Two distinct defective surfaces, with different causes:

* **Templates (latent, affects future installs).** Four write sites —
  `_stage.agent.md.tmpl:773,780` and `_ship.agent.md.tmpl:956,970` — plus
  `backlogit.instructions.md.tmpl:129` enumerate checkpoint fields but never
  require `schema_version` and never mention `context` nesting. The malformed
  record's shape is exactly what following those instructions literally produces.
* **Installed dogfood mirrors (proximate cause).** `.github/agents/_stage.agent.md`
  and `_ship.agent.md` contain the crash-resumption *read* protocol but **no
  structured checkpoint-write guidance at all**, while `backlogit_create_checkpoint`
  is an exposed MCP tool. Capability with zero shape contract is how the actual
  failure happened in this repository.

Evidence for the shape: 34 of 35 records carry `schema_version: 1`; the well-formed
peer `checkpoint-20260815-224227.json` nests domain data under `context`, proving
`context` is a real V1 field.

## Key structural discovery

`.autoharness/harness-manifest.yaml:113-116` records the agent mirrors as
`template: "global agent definition"` — **not** a `.tmpl` path — unlike
`.github/instructions/backlogit.instructions.md`, which declares
`template: "instructions/backlogit.instructions.md.tmpl"`.

The agent mirrors are therefore hand-maintained, not rendered. "Regenerating" them
means a surgical parallel edit plus a checksum refresh, and running a generator
against them would be wrong. This removed a real execution hazard from the plan.

## Design chosen

One canonical `### Checkpoint Payload Contract` in the backlogit overlay
instruction (single source of truth, with a machine-checkable fenced JSON example),
plus a one-line non-negotiable minimum and a pointer at each of the four agent
write sites and the two mirror insertions. That one-line minimum is the entire
deliberate duplication budget — it keeps each write site actionable in isolation
and lets the tests assert per-site coverage.

Rejected: patching only the templates (leaves the proximate cause and breaks
existing parity tests); restating the full contract at all five sites (the exact
drift generator that caused this bug).

## Artifacts

| Artifact | Path |
|---|---|
| Deliberation | `docs/decisions/2026-08-17-checkpoint-payload-contract-deliberation.md` |
| Plan | `docs/plans/2026-08-17-checkpoint-payload-contract-plan.md` |
| Hardening | `docs/plans/2026-08-17-checkpoint-payload-contract-hardening.md` |
| Review | `docs/reviews/2026-08-17-checkpoint-payload-contract-review.md` |

Plan declared `Requires plan hardening: yes` (P-006) → hardening produced **H1-H14**.
Review: multi-persona adversarial, six personas → **PASS, 0 P0 / 0 P1**.

Three P1s were raised and each was resolved by amending the plan/hardening before
the verdict:

1. New mirror write guidance could flood the recovery scan with active candidates
   → **H13** carries the volume constraints forward.
2. The verification step creates a live active checkpoint → **H3** binds
   create → get → resolve → rescan, and prefers a scratch `--cwd` workspace.
3. The checksum artifact list was under-specified and mis-ordered — T6 changes a
   manifest-tracked registry template while T6 was declared "independent" of T5
   → T5 now enumerates actually-changed files and T6 was moved before it.

## Backlog created

Feature **130-F** — *Enforce backlogit checkpoint payload contract in Stage/Ship
instruction surfaces*.

| ID | Task | Size | Complexity |
|---|---|---|---|
| 130.001-T | Canonical contract in overlay instruction template | S | medium |
| 130.002-T | Mandate contract at both Stage template write sites | XS | low |
| 130.003-T | Mandate contract at both Ship template write sites | XS | low |
| 130.004-T | Insert contract into installed dogfood mirrors | S | medium |
| 130.005-T | Add `cli_command` fallback for `create_checkpoint` in registry | XS | trivial |
| 130.006-T | Refresh manifest checksums + overlay verification check | XS | low |
| 130.007-T | Contract tests across templates and mirrors | S | medium |

Shipment **139-S** (queued, high, 8 items, 3×S + 4×XS, 0 unsized).

Execution order (`blocks` edges):
`130.001-T → {130.002-T, 130.003-T} → 130.004-T → 130.006-T → 130.007-T`, with
`130.005-T` independent but required before `130.006-T`.

**`138-S depends_on 139-S`** — the checkpoint fix must ship first.

## Why the mirrors are in the predecessor shipment

Answering the operator's question explicitly: **yes, mandatory**, for three
independent reasons — (a) the mirrors are the proximate cause and carry no write
guidance today; (b) Ship reloads its instructions from the installed mirrors on
current `main`, so the contract must already be there when 138-S executes; (c)
`tests/test_crash_resumption_protocol.py` already asserts template/mirror content
parity *and* manifest checksum coherence, so a template-only change would fail the
existing suite.

## Why this must precede 138-S

138-S migrates the live backlog storage root. Its own hardening H7 directs Ship to
take a resumption checkpoint before task 129.005-T, during the window where MCP
tools are unavailable. Under the current contract-free instructions that checkpoint
can be silently schema-invalid, and the failure would surface only on attempted
resume — with the storage root partially migrated. H12 additionally requires Ship
to have *reloaded* instructions from the updated `main`, since shipping the fix but
executing from a stale session delivers none of the benefit.

## State at session end

* Checkpoint scan (unfiltered, no status filter): 32 records, **0 active,
  0 anomalies**.
* Stash `E0B80A6C` archived as consumed, promoted to 130-F / 139-S.
* 129-F / 138-S artifacts and the three prior Stage commits untouched; quarantined
  evidence untouched.
* Branch not published; no PR.

## Ship handoff order

1. **139-S first** — claim, execute 130.001-T → 130.007-T in dependency order, PR,
   merge to `main`. Honour H1-H14, especially H3 (never leave an active
   checkpoint), H1 (surgical mirror edits), H2/H6 (checksums last, registry
   parity), H7 (reinstall convergence).
2. **Reload instructions from the updated `main`** (H12) — this is a gate, not a
   formality.
3. **Then 138-S** — the storage-root migration, unchanged, under its own H1-H16.

Also pending: `chore/stage-138-S` currently holds the 129-F/138-S staging commits
plus this session's; Ship owns publishing it.

Environment note: `uv run` fails here with a TLS handshake failure fetching
`hatchling`. Run `pytest` via the installed interpreter (H11); that failure is not
a shipment defect.
