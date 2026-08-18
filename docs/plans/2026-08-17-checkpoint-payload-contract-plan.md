# Implementation Plan — Checkpoint payload contract (stash E0B80A6C)

Date: 2026-08-17
Agent: Stage (planning only — Ship executes)
Deliberation: `docs/decisions/2026-08-17-checkpoint-payload-contract-deliberation.md`
Sequencing: predecessor of `138-S`

## Goal

Make it structurally impossible for a Stage or Ship agent, following its
instructions literally, to write a schema-invalid backlogit checkpoint. Prevention
at the instruction surface, proven by tests, on both the template surface (future
installs) and the installed dogfood surface (this repository, before 138-S runs).

## Non-goals

* No change to backlogit itself (external tool; behavior is correct as documented).
* No retroactive rewrite of historical checkpoints. The one malformed record is
  already quarantined with evidence preserved.
* No `harness-doctor` detection scan — deferred follow-up.
* No migration work; 138-S is untouched by this plan except for sequencing.

## The contract (normative text to be introduced once)

A backlogit structured checkpoint payload MUST:

1. declare `"schema_version": 1` as a top-level field — without it backlogit skips
   V1 validation and auto-population entirely and writes the payload through
   unvalidated;
2. be written through the official create operation — MCP
   `backlogit_create_checkpoint` (`state_dump`) or CLI
   `backlogit checkpoint create --state-dump` — never by writing a file into the
   checkpoints directory directly;
3. carry `agent` (`stage` or `ship`), `session_id`, `phase`, and a `resume_hint`
   specific enough to support a later recovery decision;
4. nest all domain data (feature/shipment/stash IDs, artifact paths, branch state,
   completed/blocked items, mode, route) inside the `context` object — these MUST
   NOT be hoisted to the top level;
5. rely on backlogit to populate `created_at`, `updated_at`, and `status`, which it
   does only when rule 1 is satisfied.

Applies to backlogit structured checkpoints only. The markdown `docs/memory/`
continuity artifact is a separate mechanism and takes no `schema_version`.

Canonical example to embed (fenced, literal values, no `{{VARIABLE}}` tokens so it
stays inert to the placeholder scanners):

```json
{
  "schema_version": 1,
  "agent": "stage",
  "session_id": "stage-2026-08-17-example",
  "phase": "harvest",
  "resume_hint": "Harvest complete; next step is shipment assembly.",
  "context": {
    "feature_id": "130-F",
    "shipment_id": "139-S",
    "artifacts": { "plan": "docs/plans/example-plan.md" }
  }
}
```

## Work breakdown

### T1 — Canonical contract in the overlay instruction template

Surface: `templates/instructions/backlogit.instructions.md.tmpl`,
`## Continuity Protocol` (currently lines 124-131).

Add a `### Checkpoint Payload Contract` subsection carrying rules 1-5 and the
fenced example. Amend existing item 2 ("persist a concise structured summary
through backlogit") to require conformance to that subsection. Keep the existing
"no raw transcript logs" rule intact.

### T2 — Stage template write sites

Surface: `templates/agents/_stage.agent.md.tmpl` lines 773 and 780.

At each site, add the non-negotiable minimum (`schema_version: 1`, official create
operation, domain fields under `context`, never top-level) and a pointer to the
canonical contract section. Do not restate rules 1-5 in full. Preserve existing
field enumerations but relocate them explicitly as `context` members.

### T3 — Ship template write sites

Surface: `templates/agents/_ship.agent.md.tmpl` lines 956 and 970. Same treatment
as T2, preserving Ship's own enumeration (shipment/feature IDs, completed and
blocked item IDs, branch state) and relocating it under `context`.

### T4 — Installed dogfood agent mirrors

Surfaces: `.github/agents/_stage.agent.md`, `.github/agents/_ship.agent.md`.

These are `template: "global agent definition"` in the manifest — hand-maintained,
not rendered. They currently contain **no** structured checkpoint-write guidance,
so this is an additive, surgical insertion of the same minimum + pointer next to
each mirror's existing session-continuity guidance (Stage: `### Step 6: Session
Continuity`, ~line 397; Ship: session memory step, ~line 636). Do not restructure
or reflow the mirrors; keep the diff minimal so existing crash-resumption parity
tests continue to pass.

Also render the overlay mirror `.github/instructions/backlogit.instructions.md`
from T1 (this one *is* template-derived; keep it in exact parity).

### T5 — Manifest checksums and verification checks

Surface: `.autoharness/harness-manifest.yaml`.

Recompute `checksum` (sha256 of on-disk bytes) for **every manifest-tracked
artifact whose bytes changed in this shipment**. At minimum that is:
`.github/agents/_stage.agent.md`, `.github/agents/_ship.agent.md`,
`.github/instructions/backlogit.instructions.md`, and — if T6 alters its bytes —
`backlog/registries/backlogit.registry.yaml` (manifest line ~112). Do not treat
the artifact list as fixed at three; enumerate changed files and hash what
actually changed. Keep the single-`checksum` shape — do not introduce
`installed_checksum` / `source_checksum`. Add a `backlogit` overlay
`verification_checks` entry naming the Checkpoint Payload Contract.

Must run after T1-T4 **and T6** land, since it hashes their output.

### T6 — Registry CLI fallback for create_checkpoint

Surface: `.autoharness/backlog-registry.yaml` (~line 108) and the corresponding
registry template `backlog/registries/backlogit.registry.yaml`.

`create_checkpoint` declares only `mcp_tool: backlogit_create_checkpoint` with no
`cli_command`. Add `cli_command: "backlogit checkpoint create"` so a degraded-mode
agent has a declared official fallback instead of being cornered into hand-writing
JSON. Independent of T1-T5.

### T7 — Contract tests

Surface: new `tests/test_checkpoint_payload_contract.py`, following the structure
of `tests/test_crash_resumption_protocol.py` (module-level path constants,
`_read` helper, per-surface test classes). Reuse that pattern; do not duplicate
its manifest-checksum helper logic beyond the small `_assert_checksum_matches`
idiom it already establishes.

Assertions:

1. **Contract present** — the canonical `Checkpoint Payload Contract` section
   exists in the overlay template *and* its installed mirror.
2. **`schema_version: 1` mandated** — asserted at all four agent-template write
   sites and in both agent mirrors.
3. **Official create path** — each write site references the official create
   operation (MCP `backlogit_create_checkpoint` / `backlogit checkpoint create`)
   and prohibits direct file writes.
4. **`context` nesting required** — each surface requires domain fields under
   `context`.
5. **Negative / anti-regression** — the exact malformed shape cannot be produced
   by following the text: assert no surface instructs top-level `feature_id`,
   `shipment_id`, `stash_source`, `mode`, `route`, or `artifacts` placement.
6. **Fenced example is conformant** — parse the JSON example out of the overlay
   template and mirror, `json.loads` it, and assert `schema_version == 1`,
   `context` is a dict, and none of the domain keys appear at top level. This is
   the test that would have caught the original defect.
7. **Manifest coherence** — checksums match on-disk bytes for the three touched
   artifacts, and the single-`checksum` shape is preserved.

## Dependency order

```
T1 ──> T2 ──┐
       T3 ──┴──> T4 ──┐
                      ├──> T5 ──> T7
T6 ───────────────────┘
```

T1 first (defines the referent). T2/T3 add pointers to it. T4 mirrors the result.
T6 is independent of T1-T4 but MUST precede T5, because T6 may change the bytes of
the manifest-tracked registry template and T5 is the single checksum-refresh point.
T5 therefore hashes the output of both T4 and T6. T7 last, since it asserts
against all of the above.

## Verification

* `pytest tests/test_checkpoint_payload_contract.py` — new contract tests.
* `pytest tests/test_crash_resumption_protocol.py` — must stay green, proving the
  mirror edits did not disturb existing parity or checksum coherence.
* `autoharness verify-workspace` — zero unresolved `{{VARIABLE}}` placeholders in
  installed artifacts.
* Manual: `backlogit checkpoint create --state-dump '<the documented example>'`
  followed by `backlogit checkpoint get <file>` must validate, then resolve the
  created checkpoint so it does not linger as an active recovery candidate.

**Environment note:** `uv run` currently fails here with a TLS handshake failure
fetching `hatchling`. Use the installed interpreter / `pytest` directly rather
than a `uv`-built environment.

## Rollback

All changes are additive documentation, config, and test edits with no runtime
component. Rollback is `git revert` of the shipment's commits followed by
recomputing the three manifest checksums. No data migration, no destructive step.

## Requires plan hardening

**yes** — the change set touches installed agent instruction surfaces that govern
crash recovery for both roles, edits the harness manifest, and is a gating
predecessor to the storage-root migration. Blast radius spans multiple template
families plus registry config.
