---
title: "Copilot CLI Tool-Output Compression Experiment — Implementation Plan"
date: "2026-07-15"
description: "Plan for a bounded, opt-in experiment/benchmark validating postToolUse-based tool-output compression on GitHub Copilot CLI. Prototype is throwaway and flag-gated; no default install."
doc_type: plan
source: docs/plans/2026-07-15-copilot-cli-output-compression-experiment-plan.md
spike_source: "docs/spikes/2026-07-15-copilot-cli-output-compression-experiment.md"
stash_source: "AF767A44"
feature: "088-F"
relates_to:
  - "086-F"
requires_plan_hardening: "yes"
plan_review_verdict: "approved-with-conditions"
tags:
  - "copilot-cli"
  - "hooks"
  - "compression"
  - "experiment"
  - "primitive-5"
  - "primitive-7"
---

<!-- markdownlint-disable MD013 -->

<!-- markdownlint-disable-next-line MD025 -->
# Copilot CLI Tool-Output Compression Experiment — Implementation Plan

## Scope and non-goals

**In scope:** a throwaway, flag-gated experiment that proves or disproves honest
AUC token savings from `postToolUse`-based tool-output compression on GitHub
Copilot CLI, with lossless byte-equivalent retrieval and a containment-safe
store. Deliverable is an evidence-backed operator decision memo.

**Explicit non-goals (deferred until the experiment succeeds):**

* No default or production install of a compression capability pack.
* No generated-harness artifacts that depend on compression.
* No second graph stack — `agent-engram` remains the graph authority.
* No changes to environment-agnostic base behavior; the overlay must be optional
  and disabled by default.

## Source of truth

* Feasibility + interception-surface findings: the 2026-07-15 spike.
* CCR store / retention / storage / benchmark-safety analysis: 086-F spike
  (2026-07-13). Reused, not re-derived.
* `postToolUse` contract: GitHub Copilot hooks reference (CONFIRMED).

## Work breakdown (2-hour rule, width-isolated)

| Task | Concern | ~Effort | Depends on |
| --- | --- | --- | --- |
| 088.001-T Containment-safe local store + resolver | storage/security | ~2h | — |
| 088.002-T `postToolUse` compression hook prototype | hook logic | ~2h | 088.001-T |
| 088.003-T Byte-equivalent retrieval MCP tool | retrieval | ~2h | 088.001-T |
| 088.004-T Decline-case policy + evidence oracle | safety policy | ~2h | 088.002-T, 088.003-T |
| 088.005-T AUC token-savings measurement harness | measurement | ~2h | 088.002-T, 088.003-T |
| 088.006-T Benchmark corpus runner + report | benchmark | ~2h | 088.004-T, 088.005-T |
| 088.007-T Findings write-up + operator decision memo | analysis/doc | ~2h | 088.006-T |

Each task targets a single concern; no task mixes store, hook, retrieval,
measurement, and analysis work.

### Task detail

* **088.001-T** — Local store under `.autoharness/cache/brainspace/` with a
  resolver enforcing Constitution IV (anchor to cwd; reject `..`, symlink escape,
  arbitrary absolute env paths, upward parent search). Byte-lossless codec (no
  UTF-8 `errors="replace"`). TTL + size cap + purge command + session-end
  cleanup + SQLite checkpoint/compaction guidance. Gitignore SQLite/`-wal`/`-shm`
  sidecars; add a staged-file guard that fails if store files are staged.
* **088.002-T** — `postToolUse` command hook (matcher-scoped to noisy tools):
  parse payload, secret/PII pre-screen, type router (JSON/log/diff/prose),
  never-expand token+char guard, **decide-then-stash** (screen and never-expand
  decision before any durable write; or rollback on reject), deterministic
  placeholder (no timestamps/mutable counters), return `modifiedResult` or `{}`.
* **088.003-T** — Retrieval MCP tool returning byte-equivalent originals; full or
  tested pagination/chunking; **no silent truncation**; direct-store recovery
  path for large originals.
* **088.004-T** — Decline-case + negative-control policy and evidence oracle:
  tiny outputs, unwritable-CCR passthrough, secret-bearing output, gate/readiness
  verdicts, active stack traces, operator/approval text; confirm no store row
  remains after a reject; confirm failure outputs are untouched.
* **088.005-T** — AUC measurement harness: raw vs compressed tokens under model
  tokenizer + cheap fallback estimator; project savings over 1/3/5/10 turns; net
  of placeholder/footer overhead.
* **088.006-T** — Benchmark corpus runner over real autoharness commands
  (`pytest -vv`, `backlogit doctor`, `git --no-pager diff`,
  `gh run view --log-failed`, verbose MCP JSON, engram/graphtor search results,
  workspace inventories); emit a safe-win/decline report per the spike proof
  method.
* **088.007-T** — Write findings + an operator decision memo
  (accept / narrow-pilot / reject) referencing 086-F and the 2026-07-15 spike.

## Plan Hardening (P-006)

Triggered: the experiment introduces a local store of exact raw tool outputs
(sensitive-data + containment blast radius) and a mechanism that rewrites what the
model sees (evidence-integrity blast radius). Hardening measures:

* **Fail-safe defaults:** disabled by default; any store/screen/guard error →
  pass original through byte-identically (never placeholder-free elision).
* **Decide-then-stash is a hard invariant**, not an optimization — no orphaned raw
  originals from rejected/declined attempts.
* **Containment is a hard invariant** — resolver rejects every escape vector;
  covered by tests before the hook writes anything.
* **Secret screening precedes durable storage** — a detector hit forces decline.
* **Evidence oracle gates every "safe win"** — a benchmark cannot pass by hiding a
  stack frame, exit status, stderr line, gate verdict, or identifier.
* **Reversibility proof required** — byte-equivalent retrieval (full/paginated)
  is a precondition for reporting any positive result.
* **Rollback:** the prototype is throwaway and flag-gated; disabling the flag and
  purging `.autoharness/cache/brainspace/` fully removes the experiment. No
  base-harness behavior depends on it.
* **Scope containment:** experiment only; no schema changes, no CLI-distribution
  changes, no default capability-pack install.

## Plan Review (multi-lens)

* **Safety/security lens:** APPROVED — decide-then-stash, containment resolver,
  secret-screen-before-store, and gitignore/staged-file guard directly address the
  086 CCR risks; failure outputs are structurally out of reach.
* **Evidence-integrity lens:** APPROVED — single `textResultForLlm` field plus the
  evidence oracle and conservative decline prevent the 086 "lose sibling failure
  fields" class; residual in-string elision risk is explicitly a decline case.
* **Environment-agnostic lens:** APPROVED — overlay is opt-in, Copilot-CLI-first,
  degrades to MCP/manual elsewhere; base behavior coherent when disabled.
* **Granularity lens:** APPROVED — 7 width-isolated ~2h tasks with a clean
  dependency chain.
* **Conditions (must hold before Ship executes):**
  1. Prototype stays flag-gated and disabled by default; it is throwaway, not a
     production capability-pack install.
  2. No schema or CLI-distribution changes in this experiment.
  3. Byte-equivalent retrieval and decide-then-stash are validated by tests before
     any positive savings result is reported.
  4. Re-verify the Copilot CLI hooks contract against the target CLI version
     before relying on it (feature is recent/evolving).

**Verdict: APPROVED WITH CONDITIONS.** Proceed to harvest.
