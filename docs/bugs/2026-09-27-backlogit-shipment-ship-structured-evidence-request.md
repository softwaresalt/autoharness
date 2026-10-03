---
chunk_strategy: h1-h2-h3
description: "Portable, non-blocking upstream feature request for backlogit: a native --json result and an optional --evidence-out envelope on shipment ship that emit the engine's own pre-close candidate set and post-close result, plus an opt-in workspace setting that refuses a direct shipment ship without an evidence path. autoharness already captures this evidence itself through autoharness shipment cascade-close and does not depend on this request."
doc_type: guide
docline:
  author: Ship
  date: 2026-09-27
  status: draft-for-transfer
schema_version: "1.0"
source: docs/bugs/2026-09-27-backlogit-shipment-ship-structured-evidence-request.md
title: "backlogit feature request — structured, engine-native evidence for shipment ship"
kind: "feature-request"
severity: "low"
blocking: false
target_repository: "softwaresalt/backlogit (EXTERNAL, separate repository and owner)"
related_feature: "192-F (autoharness shipment cascade-close evidence capture)"
tags:
  - "feature-request"
  - "backlogit"
  - "shipment-ship"
  - "evidence"
  - "cross-tool-integration"
---

> **Transfer note.** This request is written to be self-contained so it can be
> copied verbatim into the `backlogit` workspace as an issue or backlog item. It
> asks for changes in `backlogit` only. **autoharness does not depend on it**: the
> autoharness half of the work (192-F) already ships and captures close evidence
> on its own. Nothing here blocks any autoharness shipment, and no autoharness
> behavior changes if the request is declined.

## Summary

`backlogit shipment ship` (and the `backlogit_ship_shipment` MCP tool) archives a
shipment and cascades over its scope in one call. Today a caller that needs proof
of what the cascade touched must reconstruct it from outside the engine: snapshot
the backlog before the call, parse the human-readable result, and diff the backlog
afterwards. That reconstruction cannot be repeated after the fact, because the
cascade mutates the same `status` fields the snapshot records.

This request asks `backlogit` to emit that evidence itself, from the engine's own
view of the close, in a documented machine-readable envelope.

## Background

During one autoharness shipment close, the caller kept none of the raw evidence of
a cascade. The closure review halted and needed an operator deviation, because the
evidence could not be rebuilt once the cascade had run.

autoharness addressed its own half with `autoharness shipment cascade-close`. That
command re-runs its classifier, probes the engine version, records a pre-close
snapshot, invokes `backlogit shipment ship`, and checks the result against its
postconditions. It writes everything to a committed evidence record. That record is
still an outside observer's view. Only `backlogit` knows exactly which IDs its own
cascade considered, so only `backlogit` can report them authoritatively.

## Requested changes

1. **Native `--json` result on `shipment ship`.** Emit one JSON object on stdout
   carrying at least the shipment ID, the resulting shipment status, the archived
   IDs, the IDs returned to the queue (if any), and the backlog commit SHA (or
   `null`). The object has a stable, versioned shape, so a caller never parses
   prose.
2. **Optional `--evidence-out <path>`.** When supplied, write an evidence envelope
   to `<path>` containing:
   * the engine's own **pre-close candidate set**, the IDs that
     `collectArchiveCandidateIDs` computed before any mutation, each with its
     pre-close `status` and storage location;
   * the **post-close result**: the same fields as the `--json` result, plus each
     candidate's post-close `status` and location;
   * the engine version and commit that produced it.

   The envelope is written atomically. If it cannot be written, `shipment ship`
   fails before mutating anything, never after.
3. **A documented envelope.** Publish the `--json` and `--evidence-out` shapes,
   with a `schema_version`, in the `backlogit` documentation, and treat a shape
   change as a versioned, announced change.
4. **Opt-in mutation-boundary enforcement.** Add a workspace setting (off by
   default) under which `backlogit` refuses a direct `shipment ship` CLI call or a
   `backlogit_ship_shipment` MCP call unless an evidence path is supplied. Only the
   engine can enforce this at the mutation boundary; a caller-side tool such as
   autoharness can detect a missing record after the fact, but cannot prevent the
   call.

## Non-goals

* No change to the cascade's selection semantics or to which items it archives.
* No dependency from `backlogit` on autoharness, and no autoharness-specific
  field names in the envelope.
* No requirement that existing callers adopt `--json` or `--evidence-out`; both are
  additive and opt-in.

## Compatibility and adoption

Every requested change is additive. Existing `shipment ship` output and behavior
stay unchanged unless the caller passes the new flags or the workspace opts in to
the enforcement setting.

If `backlogit` ships this, autoharness may later record the engine envelope beside
its own evidence record and cross-check the two. That is an optional follow-up and
would be planned separately. Until then, and permanently if the request is
declined, autoharness keeps capturing its own evidence through
`autoharness shipment cascade-close`.

## Acceptance criteria

* `backlogit shipment ship <id> --json` prints exactly one JSON object with a
  `schema_version` and the fields in item 1.
* `--evidence-out <path>` writes the envelope in item 2 atomically, and a write
  failure leaves the backlog unmutated.
* The envelope is documented with its `schema_version`.
* With the enforcement setting on, a `shipment ship` call or a
  `backlogit_ship_shipment` call without an evidence path is refused before any
  mutation, with a non-zero exit and a clear message. With the setting off, the
  behavior is unchanged.
