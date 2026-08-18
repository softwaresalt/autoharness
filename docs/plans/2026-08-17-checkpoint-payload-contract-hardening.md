# Plan Hardening — Checkpoint payload contract (stash E0B80A6C)

Date: 2026-08-17
Agent: Stage
Plan: `docs/plans/2026-08-17-checkpoint-payload-contract-plan.md`
Trigger: plan declares `Requires plan hardening: yes` (P-006)

Hardening constraints H1-H12. All are binding on Ship during execution.

## H1 — Mirror edits are additive and surgical, never a reflow

`.github/agents/_stage.agent.md` and `_ship.agent.md` are hand-maintained global
agent definitions, not rendered artifacts. T4 MUST be a localized insertion next
to existing session-continuity guidance. Do not restructure, reorder, reflow, or
re-wrap surrounding text. A mirror diff that touches materially more than the
inserted block is a signal the edit went wrong — stop and re-scope rather than
accept a large diff. `tests/test_crash_resumption_protocol.py` must remain green
throughout as the parity tripwire.

## H2 — Checksum recomputation is strictly last and single-shaped

T5 runs only after T1-T4 are byte-final. Recompute sha256 over actual on-disk
bytes for all three touched artifacts:
`.github/agents/_stage.agent.md`, `.github/agents/_ship.agent.md`,
`.github/instructions/backlogit.instructions.md`. Preserve the single `checksum`
key — introducing `installed_checksum` or `source_checksum` is an explicit test
failure in `ManifestChecksumCoherenceTests`. If any of T1-T4 is amended after T5,
T5 must be redone.

## H3 — Verification MUST NOT leave an active checkpoint (highest-severity)

The plan's manual verification creates a real checkpoint via
`backlogit checkpoint create`. A created checkpoint is an **active recovery
candidate**. Leaving one behind would:

* seed a false candidate into the mandatory unfiltered startup scan, and
* directly contradict the rule that completed work must never leave an active
  recovery candidate.

Binding sequence: create → `checkpoint get` to prove it validates → immediately
`backlogit checkpoint resolve <filename>` → re-run the unfiltered
`checkpoint list` and confirm **zero active and zero anomalies** before handoff.
If the verification checkpoint cannot be resolved, HALT — do not proceed to 138-S.
Prefer performing this verification in a scratch workspace via `--cwd` so the live
workspace is never touched at all.

## H4 — Do not disturb 129-F / 138-S artifacts or quarantine evidence

Out of bounds for this shipment: the 129-F/138-S plan, hardening, review and
memory artifacts; the three prior Stage commits; and
`.backlogit/archive/checkpoints/checkpoint-20260817-234318.json` plus its
`.disposition.json` sidecar and the disposition audit log. The quarantined bytes
are evidence and are byte-identical by design — never rewrite, re-quarantine, or
"clean up" any of them.

## H5 — Contract scope is backlogit structured checkpoints only

The normative text MUST state that `schema_version` applies to backlogit
structured checkpoints and NOT to the markdown `docs/memory/` continuity artifact.
Without this, agents may start emitting YAML/JSON front matter into memory files
or, worse, treat the markdown file as satisfying the structured-checkpoint
requirement. Both roles' write sites mention both mechanisms in adjacent prose, so
the distinction must be explicit at the point of instruction.

## H6 — Registry parity: installed and template together

T6 must update **both** `.autoharness/backlog-registry.yaml` and the registry
template `backlog/registries/backlogit.registry.yaml`. Updating only the installed
copy creates drift that a reinstall silently reverts; updating only the template
leaves this repository's own degraded-mode path uncovered before 138-S. The
registry template is manifest-tracked (`checksum` at manifest line ~112), so if
its bytes change, its checksum is recomputed under H2 as well.

## H7 — Reinstall convergence

Because the agent mirrors are labeled `template: "global agent definition"` rather
than a `.tmpl` path, a future harness reinstall could overwrite them. The
normative sentences inserted into the mirrors (T4) MUST be semantically identical
to those introduced into the corresponding templates (T2/T3), so a reinstall
converges on the same contract instead of regressing it. After T4, diff the
contract sentences across template and mirror and confirm they agree in substance.
If they cannot be made to agree, HALT and escalate rather than shipping a fix that
a reinstall silently undoes.

## H8 — Negative test must be precise, not keyword-brittle

The anti-regression assertion (plan T7 item 5) must match *instructional patterns*
that would place domain fields at the top level — not bare occurrences of words
like `artifacts`, `mode`, or `route`, which legitimately appear throughout both
agent files in unrelated prose. A keyword-only test will produce false failures
and will be disabled by the next engineer, destroying the guard. Anchor the
assertions to the contract block and the fenced example rather than scanning the
whole document for substrings.

## H9 — Fenced example must remain parseable and placeholder-free

The embedded JSON example must use literal values with no `{{VARIABLE}}` tokens,
so that (a) `json.loads` succeeds in T7 item 6, and (b) placeholder scanners
behave identically whether or not they strip fenced blocks. Note that both
`verify_workspace` and the existing mirror placeholder test strip fenced code
blocks before scanning, so the example is inert to them — but it must still parse.

## H10 — Commit hygiene: explicit paths only

`.backlogit/` is git-tracked in this repository and carries a multi-megabyte
SQLite `db` + `wal`. Never use `git add -A`. Stage only enumerated paths, exactly
as the 129-F/138-S work did. Also prohibited for the duration: `git clean -x`/`-X`.

## H11 — Verification runs on the installed interpreter

`uv run` currently fails in this environment with a TLS handshake failure fetching
`hatchling`, so a `uv`-built environment is not available. Run `pytest` via the
installed interpreter. A `uv` failure is an environment condition and MUST NOT be
reported as a test failure of this shipment.

## H12 — Sequencing is a hard gate, not a preference

Ship MUST NOT claim 138-S until this predecessor shipment is merged to `main`
**and** Ship has reloaded its instructions from that updated `main`. Shipping the
fix but executing 138-S from a session that loaded pre-fix instructions delivers
none of the benefit: the migration's own H7 resumption checkpoint — taken before
129.005-T while MCP tools are unavailable — is exactly the checkpoint this
contract is meant to protect, and a stale session would still write it unvalidated.
The `blocks` dependency encodes the ordering; this constraint encodes the reload.

## H13 — Adding write guidance must not increase active-candidate pressure

The dogfood mirrors today contain **no** structured checkpoint-write guidance, so
T4 introduces a capability instruction where none existed. If written carelessly,
Stage and Ship would begin emitting structured checkpoints at every milestone and
leaving them active — which would seed multiple candidates into the mandatory
unfiltered startup scan, force operator selection on every session start, and
degrade exactly the recovery path this shipment is meant to protect. That would
trade a rare malformed record for a chronic noise problem.

The inserted mirror guidance MUST therefore carry the existing volume constraints
alongside the shape contract:

* resolve any still-active checkpoints from the current session at session end;
* leave **at most one** final best-effort checkpoint, and only when the next
  action must survive a context-window shutdown;
* never leave an active recovery candidate for completed work.

After T4, a Stage or Ship session run under the new guidance must still end with
zero active checkpoints. Verify this before handoff, together with H3.

## H14 — Predecessor cannot permanently strand 138-S

The `blocks` edge makes 138-S unshippable until this shipment completes. If this
shipment is later abandoned or indefinitely deferred, 138-S must not be silently
stranded. The dependency may be removed only by explicit operator decision,
recorded in the backlog; Ship must not remove it unilaterally to unblock itself.
