---
title: "Operator-editable P-011 carry-forward configuration (deliberation)"
description: "Deliberation of the design constraints for moving P-011 pre_claim carry-forward paths from hard-coded code into an operator-editable YAML, adding .autoharness/config.yaml, and the self-reference security model."
date: 2026-10-15
status: draft-awaiting-operator-confirmation
stash_entries: [D2F399C9]
tags: [deliberation, p-011, carry-forward, gates, topology, security]
---

## Problem

`FilesystemTopologyReaders.carry_forward_prefixes()` (`src/autoharness/gates/topology.py`) returns only
`f"{backlog_dir.name}/"`. `_worktree_cleanliness_check` treats dirty paths under it as
`CARRY_FORWARD_ELIGIBLE`; stash-referenced new `docs/` files are a second, separate class
(`stash_referenced_paths`). A dirty `.autoharness/config.yaml` (routinely edited when models change) is
therefore `WORKTREE_DIRTY` for every shipment, today including 212-S.

Operator asks: (1) carry `.autoharness/config.yaml` forward; (2) make the set operator-editable YAML, not
code; (3) the YAML file is itself always carried forward when dirty, and must not be a vector to bypass P-011.

## Decisions (recommended; D2 and D3 need explicit operator confirmation)

| # | Question | Recommendation | Rationale |
|---|---|---|---|
| D1 | Location / schema | `.autoharness/carry-forward.yaml`, `schemas/carry-forward.schema.json` (`schema_version: 1`, `additionalProperties: false`), default shipped from a template. Keys: `schema_version`, `files: [exact repo-relative paths]`, `directories: [repo-relative prefixes]`. | Separate from `config.yaml` so the gate never has to trust the file it is deciding about (see D3). Matches the existing schemas/ + manifest pattern. |
| D2 | Exact path vs glob/prefix | Exact `files` plus explicit `directories` (each must end in `/`). NO globs, no `**`, no negation. Max 32 entries. | Prefix normalisation today appends `/`, which would turn `.autoharness/config.yaml` into `.autoharness/config.yaml/`; exact paths need their own match branch (`path == entry`). Globs widen unpredictably and are hard to contain-check. |
| D3 | Self-reference and widening (security) | See next section. Self-entry is IMPLICIT and BUILT-IN; the effective configured set is read from the COMMITTED `HEAD` blob, never the working tree; entries are confined to an allowlist root. | An agent that edits the file in the working tree must not be able to make that same edit (or any other dirt) pass P-011 in the same run. |
| D4 | Containment / traversal | Reuse `_stash_reference_path_lexically_contained` rules: no empty/`.`/`..` segment, drive, colon, backslash, absolute path, `.git`; and the filesystem predicate (resolves inside workspace, no symlink/reparse point in file or parents) at match time. Any invalid entry invalidates the whole file (not just the entry). | Constitution III/IV: path handling is validated, fail closed. Whole-file invalidation avoids a partially-trusted file. |
| D5 | Fail closed | Missing / unreadable / malformed / schema-invalid / oversize / not-in-HEAD file => effective set = built-ins only (backlog dir + the file's own path) and a `carry_forward_config_warning` in the check `details`. Never widens, never drops the backlog dir. A `git show` failure is treated as unreadable. | Fail closed means narrower, never wider. Built-ins keep backlog carry-forward working under any corruption. |
| D6 | Divergence | Unchanged semantics: a configured path whose staged content differs from both HEAD and the working tree is reported in `divergent_paths` and blocks (`WORKTREE_DIRTY`), exactly like backlog state. Applies equally to `config.yaml` and the carry-forward file. | Staging the working tree would discard the staged content; same data-loss rule as today. |
| D7 | Default content | Shipped default lists `.autoharness/config.yaml` under `files`. Built-ins (non-removable, not listed in the file): backlog dir prefix and `.autoharness/carry-forward.yaml`. | The built-in set is the safety floor; the file only adds operator-trusted routine-edit files. |
| D8 | Install / tune / manifest | New template `templates/foundation/carry-forward.yaml.tmpl` (no variables), installed to `.autoharness/carry-forward.yaml` by install-harness, recorded in `harness-manifest.yaml` as an operator-owned artifact; tune never overwrites an existing file and treats checksum drift as expected operator edit. Details to confirm in implementation. | Same lifecycle as `config.yaml`. |
| D9 | Parity | Template plus dogfood copy (`.autoharness/carry-forward.yaml`), and the P-011 wording mirrors: `templates/policies/workflow-policies.md.tmpl` <-> `.github/policies/workflow-policies.md`, and the `_ship` / `_orchestrator` agent template <-> `.github/agents` mirrors where P-011 carry-forward is described. | Repo template-vs-dogfood parity tests. |
| D10 | Ordering vs 212-S | No `blocks` edge. See Ordering. | Avoids coupling an unrelated claim-marker contract to this change. |

## D3 security analysis (self-reference)

Threat: carry-forward admits dirty paths without blocking. If the carry-forward file is both (a) read from the
working tree and (b) carry-forward eligible when dirty, an agent can in one run add `src/` to the file, leave
`src/` dirty, and the gate passes: a P-011 bypass.

Controls (all required):

1. Implicit built-in self-entry. `.autoharness/carry-forward.yaml` is always eligible when dirty, whether or
   not the file lists itself, and even if the file is missing or invalid (so the operator's repair edit of a broken
   file is not itself blocked). Listing it in the file is a no-op and is rejected as redundant-or-ignored with
   no effect on the set.
2. Trust the committed blob. The effective configured set is parsed from `git show HEAD:.autoharness/carry-forward.yaml`.
   A dirty working-tree edit is carried forward as content but cannot influence the current gate decision. It takes
   effect only after it is committed (the carry-forward commit on the shipment branch merges later). Cost: an
   operator who adds a path must commit that change before it is honored. This is the central trade-off (OPEN, see Q1).
3. Allowlist root. Configured `files` must be under `.autoharness/`; `directories` must be under `.autoharness/`
   or equal to nothing else. `src/`, `templates/`, `schemas/`, `.github/`, `tests/`, `scripts/`, `docs/` (stash-referenced docs have their own class), and `.git/` can never be configured; they are rejected at validation. The backlog dir is built-in, not configured.
4. Bounded and inert. No globs, size cap, no includes, nothing executed, no extraction from file text beyond the schema.
5. Visible. Every decision lists `carry_forward_paths`, `carry_forward_prefixes`, effective source (`head` or `builtin-fallback`), and any config warning in the check details.

Residual risk: carrying `config.yaml` forward means an agent could change model routing and have it committed in the
carry-forward commit. Accepted by the operator's request, mitigated by it appearing as a named carry-forward path
in the Ship report and by the operator-owned review of the first commit; flag for confirmation (Q3).

## Ordering relative to 212-S

212-S is blocked today by dirty `.autoharness/config.yaml`. The same dirt blocks a Ship claim of THIS shipment, so
the new code cannot unblock itself. The operator must first clear the dirt by a route that is not Stage's or an
agent's (commit the Ship-route change via PR, or stash it), then claim 212-S and/or this shipment in either order.
No code dependency exists between them. Recommended: land this shipment after 212-S unless the operator expects
more config edits before then.

## Open questions for the operator

- Q1. Confirm HEAD-blob trust (D3.2) versus working-tree trust. HEAD is recommended; working-tree trust is unsafe unless the file is excluded from carry-forward, which contradicts the self-reference request.
- Q2. Confirm the `.autoharness/`-only allowlist (D3.3). Wider roots (for example `docs/`) re-open the bypass.
- Q3. Accept carrying model-routing edits (`config.yaml`) through an agent-driven commit.
- Q4. Reference "HEAD" of the current branch (as proposed) versus the remote default branch for the trusted blob.

## Stage record

- Source stash: D2F399C9. Late-identifier/duplicate scan: not a deferred-scope-expansion entry; N/A.
- plan-harden and plan-review have NOT been run (see plan). Learnings search of `docs/compound/` not performed against a subagent.
