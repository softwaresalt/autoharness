---
title: Claim-Marker Consumption Operator Guide
description: Operator guide for the opt-in features.scheduler_baseline_claim registry flag, which turns on the P-002.8 claim-marker consumption contract in Ship, and the operator-only follow-up after release
doc_type: guide
source: docs/claim-marker-consumption.md
---

> **Navigation**: [README](../README.md) · [Backlog Integration](backlog-integration.md) · [Validation Gates Reference](gates-reference.md) · [Tuning Guide](tuning-guide.md)

## Overview

backlogit stamps a claim marker on every shipment member its shipment claim activates. The
workflow policy registry publishes the consumer contract for that marker as **P-002.8**
(`marker_contract_version: 1`). This guide covers only how an operator opts in and what to
expect. The rules themselves live in P-002.8 and are cited, never restated, here.

The producer contract is `scheduler-baseline-marker/v1`, published by backlogit at
`https://github.com/softwaresalt/backlogit/blob/main/docs/design-docs/scheduler-baseline-marker-contract.md`.

## The `features.scheduler_baseline_claim` flag

The flag sits beside the other registry features in `.autoharness/backlog-registry.yaml`
and is declared in `schemas/backlog-tool-registry.schema.json`.

| Value | Effect |
|---|---|
| `false` or absent (default) | No behavior change. Ship Step 3 and Step 4.1 run exactly as before. |
| `true` | Ship applies P-002.8 in Step 3 (admission) and Step 4.1 (start record). |

Opt in only when the installed backlogit stamps the marker (the `154-S` producer,
`scheduler-baseline-marker/v1`).

### Fail-closed behavior

Enabling the flag against a backend that does not stamp the marker makes every claimed
shipment halt at Step 3 as an active residual (`WAVE_NO_PROGRESS`). Ambiguous or unreadable
claim state halts `WAVE_CLAIM_STATE_INDETERMINATE`, which outranks the residual halt.
Repeated halts on freshly claimed shipments mean the producer is absent or older. Roll back
by setting the flag to `false`; start-record comments already written are inert when the
flag is off.

## Operator follow-up after release

1. Install the release and run `autoharness verify-workspace`.
2. Set `features.scheduler_baseline_claim: true` in the backlogit registry.
3. The **operator alone** may then post `CONDITION_B_ATTESTED` on `154-S`, citing the release
   and the `tests/test_marker_contract_v1_fixtures.py` proof, to replace the 2026-10-07
   substitution attestation. No agent originates this attestation.

The fixture suite is a reference model of the decision table; the live-claim proof happens in
backlogit after install, on the first shipment claimed after the flag is enabled.

## Related

* P-002.8 in `templates/policies/workflow-policies.md.tmpl` (installed at `.github/policies/workflow-policies.md`)
* [Carryover requirements](design-docs/2026-10-07-autoharness-requirements-carryover.md)
