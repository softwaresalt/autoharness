# Deliberation — Checkpoint payload contract (stash E0B80A6C)

Date: 2026-08-17
Agent: Stage
Stash: E0B80A6C (bug, medium)
Predecessor of: 138-S (`.backlogit` → `.backlog` storage-root migration)

## Problem frame

A Stage checkpoint (`checkpoint-20260817-234318.json`) was written schema-invalid
and had to be quarantined. It omitted `schema_version` and hoisted domain fields
(`feature_id`, `shipment_id`, `stash_source`, `mode`, `route`, `artifacts`) to the
top level instead of nesting them under `context`.

The mechanism is not a backlogit bug. Per `backlogit checkpoint create --help`:

> When the dump declares `schema_version=1`, it is validated as a V1 checkpoint
> and missing `created_at`, `updated_at`, and `status` fields are auto-populated.

Validation and auto-population are **conditional on `schema_version` being
declared**. A payload that omits it is neither validated nor completed — it is
written through verbatim and only fails later, at `checkpoint get`, when recovery
is actually needed. The failure is therefore *silent at write time and surfaces at
the worst possible moment*: during crash recovery.

## Evidence gathered (no invention)

Two distinct defective surfaces, with different causes:

**Surface A — agent templates (latent, affects installed workspaces).**
Four checkpoint-write sites instruct a structured checkpoint but never require
`schema_version` and never mention `context` nesting:

| File | Line | Site |
|---|---|---|
| `templates/agents/_stage.agent.md.tmpl` | 773 | mid-session |
| `templates/agents/_stage.agent.md.tmpl` | 780 | session end (item 2) |
| `templates/agents/_ship.agent.md.tmpl` | 956 | mid-session |
| `templates/agents/_ship.agent.md.tmpl` | 970 | session end (item 2) |

Each enumerates exactly the fields the malformed record carried (phase, feature/
stash IDs, artifact IDs, next step, `resume_hint`) — the malformed shape is what
you get by following these instructions literally.

A fifth site, `templates/instructions/backlogit.instructions.md.tmpl:129`
(`## Continuity Protocol`), says "persist a concise structured summary through
backlogit" with no shape contract at all.

**Surface B — installed dogfood mirrors (proximate cause of the actual failure).**
`.github/agents/_stage.agent.md` and `_ship.agent.md` contain the crash-resumption
*read* protocol but **no structured checkpoint-write guidance whatsoever** — grep
for `create_checkpoint` / "phase-tagged" returns zero hits in both. Yet
`backlogit_create_checkpoint` is an exposed MCP tool. An agent therefore has the
capability with zero shape contract, which is precisely how the malformed record
was produced in this repository.

**Regeneration semantics.** `.autoharness/harness-manifest.yaml:113-116` records
`.github/agents/_stage.agent.md` with `template: "global agent definition"` — not
a `.tmpl` path. Contrast `.github/instructions/backlogit.instructions.md`, which
declares `template: "instructions/backlogit.instructions.md.tmpl"`. The agent
mirrors are hand-maintained global agent definitions, not rendered artifacts. So
"regenerate the mirrors" means a **surgical parallel edit plus checksum update**,
not running a generator. This removes the risk of a generator flattening the
condensed mirrors, and it makes the mirror edit an explicit, reviewable task.

**Existing enforcement to extend, not duplicate.**
`tests/test_crash_resumption_protocol.py` already establishes the pattern:
template + installed-mirror content parity, plus
`ManifestChecksumCoherenceTests` asserting each mirror's manifest `checksum`
equals the sha256 of its on-disk bytes, and asserting `installed_checksum` /
`source_checksum` are absent.

## Options considered

**Option 1 — Patch only the four agent-template write sites.**
Rejected. It leaves Surface B untouched, so this repository's own Stage and Ship
agents (the ones that produced the failure) stay uncorrected, and Ship would
execute 138-S under the same defective contract. It also breaks the existing
template/mirror parity tests.

**Option 2 — Restate the full contract at all five write sites.**
Rejected. Five near-identical copies across three files is exactly the drift
generator that produced this bug; the operator explicitly asked to avoid
duplicating logic.

**Option 3 (chosen) — One canonical contract in the backlogit overlay
instruction; short mandatory pointers at each agent write site.**
Put the normative "Checkpoint Payload Contract" once in
`templates/instructions/backlogit.instructions.md.tmpl` under
`## Continuity Protocol`, including a machine-checkable fenced JSON example. Each
of the four agent write sites then states the non-negotiable minimum
(`schema_version: 1`, official create operation, domain data under `context`) and
points at the canonical section. The overlay is already backlogit-pack-
conditioned, and every write site is already gated on the same pack, so the
reference can never dangle.

**Option 4 — Add a `harness-doctor` scan for schema-invalid checkpoints.**
Deferred, not rejected. It is detection after the fact; this shipment is about
prevention, and the quarantine verb already gives a clean remediation path.
Recorded as a follow-up rather than expanded scope.

## Chosen direction

Option 3, scoped to the minimal complete set:

1. Canonical contract in the overlay instruction template + its rendered mirror.
2. Mandatory pointer + minimum at all four agent-template write sites.
3. Surgical insertion of the same contract into both dogfood agent mirrors
   (which today carry no write guidance at all).
4. Manifest checksum refresh for the three touched mirrors, plus a backlogit
   overlay `verification_checks` entry.
5. Registry gap: `create_checkpoint` declares only `mcp_tool` and **no**
   `cli_command`. In MCP-degraded mode an agent has no declared official
   fallback — which is the exact condition that invites hand-written JSON. Adding
   `backlogit checkpoint create` closes the loop and is in-scope for reliability.
6. Contract tests, extending the existing crash-resumption pattern.

## Why this must precede 138-S

138-S migrates this repository's live backlog storage root — the highest-risk
operation currently staged, and the one most likely to need a mid-flight
resumption checkpoint. Its hardening (H7) explicitly anticipates MCP tools being
unavailable between tasks 129.005-T and 129.009-T and directs Ship to take a
resumption checkpoint before 129.005-T. If that checkpoint is written under the
current contract-free instructions, it can be silently schema-invalid, and the
failure would surface only when Ship tries to resume mid-migration — with the
storage root in a partially migrated state. Sequencing the fix first is a
reliability requirement, not tidiness.

## Open questions / risks

* `uv run autoharness` currently fails in this environment (TLS handshake failure
  fetching `hatchling`), so verification must use the installed interpreter/pytest
  rather than a `uv`-built environment. Carried into hardening.
* The contract must not imply that a *file-based* `docs/memory/` checkpoint needs
  `schema_version` — that field applies only to backlogit structured checkpoints.
  Carried into hardening as an ambiguity guard.
