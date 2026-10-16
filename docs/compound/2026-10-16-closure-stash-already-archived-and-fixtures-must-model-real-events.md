---
title: "Closure: harvest already archives the source stash entry, and fixtures must model real backlogit events"
date: 2026-10-16
problem_type: workflow
category: closure
root_cause: assumption-drift
tags: [closure, stash, cascade-close, fixtures, claim-marker, 212-S, 205-F]
source: docs/compound/2026-10-16-closure-stash-already-archived-and-fixtures-must-model-real-events.md
doc_type: learning
---

# Closure: harvest already archives the source stash entry, and fixtures must model real backlogit events

## Problem

Two assumptions drifted from backlogit's real behavior during 212-S / 205-F.

1. Closure instructions say to retire the source stash entry. `backlogit stash archive 21F8C04A` failed with `stash entry not found`.
2. Marker-consumption fixtures modeled backlogit events by assumption. Copilot review found the fixture model had drifted from the real event shape. Real log events carry `event_type` and the comment text under `delta.comment`.

## Learnings

* Harvest archives the source stash entry. 21F8C04A was already in `.backlogit/archive/stash.jsonl` (`archived_at` 2026-10-08, harvest time). At closure the correct check is a lookup in `archive/stash.jsonl`. A `not found` from `stash archive` means already retired, not failure. Matches of the ID in `.backlogit/stash.jsonl` are text mentions in other entries, not the entry itself.
* Cascade-close re-archives tasks that already sit in `archive/` declaring `status: done`. They are not truly archived, so they are `required_ids`. All nine IDs (feature, seven tasks, shipment) appeared in `archived_ids`.
* A shipment whose manifest includes the covering feature still gets verdict CASCADE when every descendant is engine-inert. The plan-linked deliberation lived only under `docs/decisions/`, not in the backlog, so the disposition snapshot was empty.
* Derive fixtures from real log output (`event_type`, `delta.comment`), never from the spec prose. Re-check the model against a captured event before relying on a fixture.
