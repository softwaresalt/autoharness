---
title: "Operator-editable P-011 carry-forward configuration"
description: "Implementation plan for .autoharness/carry-forward.yaml: schema, HEAD-blob loader, gate wiring, default template/install/manifest, wording mirrors, docs. Stash D2F399C9, feature 210-F, shipment 217-S."
date: 2026-10-15
status: draft
deliberation: "docs/decisions/2026-10-15-p011-carry-forward-config-deliberation.md (open operator questions Q1-Q4)"
stash_entries: [D2F399C9]
requires_plan_hardening: "yes"
plan_hardening_status: "not-run"
plan_review_verdict: "not-run"
tags: [plan, p-011, carry-forward, gates, schema, parity]
---

## Hardening signals

Requires plan hardening: **yes** (new schema, gate security behaviour, multiple template families). `plan-harden` and
`plan-review` were NOT run in this Stage session. Run them before Ship claims 217-S.

## Task graph (shipment 217-S, feature 210-F)

| Task | Size / complexity | Depends on | Surface |
|---|---|---|---|
| 210.001-T schema | S / low | - | `schemas/carry-forward.schema.json` |
| 210.002-T loader + unit tests | M / medium | 210.001-T | `src/autoharness/gates/` |
| 210.003-T gate wiring + gate tests | M / medium | 210.002-T | `topology.py`, `tests/test_gates_topology.py` |
| 210.004-T template, dogfood file, install/tune, manifest | M / medium | 210.001-T | templates, `.autoharness/`, install/tune |
| 210.005-T policy/agent wording + `.github` mirrors | S / low | 210.003-T | policies, agents |
| 210.006-T docs + CHANGELOG | S / trivial | 210.003-T | `docs/gates-reference.md` |

## Key implementation notes

- Exact-file entries need a separate `path == entry` branch; the existing normalisation appends `/` to every prefix.
- Effective set is read from `git show HEAD:.autoharness/carry-forward.yaml` (D3.2); built-ins are the backlog dir
  prefix and `.autoharness/carry-forward.yaml` itself, always present.
- Any validation failure yields built-ins only plus a warning in check details; never widens.
- Keep `stash_referenced_paths` as an independent class.
- Do not modify the operator's uncommitted `.autoharness/config.yaml` at any point.

## Test plan

Canonical gate: `PYTHONPATH=src python -m unittest discover -s tests` (PowerShell: set `$env:PYTHONPATH='src'`).
Cases: see 210.002-T and 210.003-T; plus manifest/parity tests for 210.004-T and 210.005-T. Include a regression
test that a dirty `src/` file plus a working-tree-only widening of the carry-forward file still yields `WORKTREE_DIRTY`.

## Ordering

No blocks edge to 212-S. A Ship claim of 217-S is itself blocked by the dirty `.autoharness/config.yaml` until the
operator clears it (see deliberation, Ordering).
