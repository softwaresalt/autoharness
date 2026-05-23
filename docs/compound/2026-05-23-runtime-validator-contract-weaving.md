---
id: compound-2026-05-23-runtime-validator-contract-weaving
title: "Runtime validator contracts must be woven across schema, verifier, and workflow artifacts together"
problem_type: cross-artifact-contract
category: autoharness-runtime-validation
root_cause: "Runtime validation semantics span schemas, installed workflow docs, overlay instructions, and verifier assertions; updating only one layer produces drift and incomplete installs."
tags: [runtime-validation, releasability, schema-drift, verify-workspace, workflow-weaving]
created: 2026-05-23
shipment: 050-S
merge_sha: be70c8c51831976723c7c094e92fe5a6420a423f
---

# Runtime validator contracts must be woven across schema, verifier, and workflow artifacts together

## Problem

The runtime validator / releasability model is not a single-file feature. It
introduces a cross-cutting contract that touches the workspace profile,
verification logic, Ship handoff language, runtime verification guidance,
operational closure guidance, and capability-pack overlays. If only one layer is
updated, the harness becomes internally inconsistent.

## Solution

When adding or changing a runtime-validation contract:

1. Update both workspace-profile schemas (versioned and unversioned).
2. Update the dogfood profile so the contract exists in a real workspace instance.
3. Extend `verify_workspace` assertions and tests to prove the contract is woven.
4. Update Ship, runtime-verification, and operational-closure artifacts together.
5. Re-check overlay instructions (`browser-verification`, release observability,
   architecture guidance) for terminology drift.

## Practical Guardrail

Treat runtime-validation changes as a **weaving task**, not a docs-only or
schema-only task. A good completion check is: "Can discovery emit the contract,
can install/tune preserve it, can verifier assert it, and can Ship/closure use
it without placeholder terminology drift?"
