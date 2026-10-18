---
title: "Requirements: shell-capable adversarial review in the autoharness harness"
description: "Requirements for giving the adversarial-review pipeline verified build/test access and real multi-reviewer fan-out, carried over to autoharness"
status: draft
date: 2026-10-16
source: "intercom-go dark-mode run of shipments 047-S, 048-S, 049-S"
target_workspace: autoharness
---

# Requirements: shell-capable adversarial review

## 1. Problem

During the dark-factory run of 047-S, 048-S and 049-S, the operator required
multi-persona adversarial review of all code before each PR. In practice:

* The `Adversarial Review` agent declares `tools: read, agent, search, edit`
  (no terminal). Every reviewer persona declares `tools: read, search`.
  Only `Security Sentinel` has `terminal`.
* Reviewers could not run `go build`, `go vet`, `gofmt`, `go test`, or
  `git diff`, and had only partial file access. Findings were produced by
  reading, not by executing.
* The orchestrating Ship agent ran the quality gates itself and the
  adversarial agent and security reviewer were not counted as coverage.
  Effective review was a single reviewer (code-review) plus the Ship agent's
  own gate runs. The multi-model consensus the `adversarial-review`
  capability pack promises was not delivered.
* The review does produce value when it works (it found a P1 on 049-S: a
  skipped test masking a failure in a cascade smoke subtest), so the gap is
  one of capability, not of design.

## 2. Goals

1. Adversarial review findings are backed by executed evidence (build, vet,
   format, test results), not only by reading.
2. The reviewer pool genuinely fans out to at least 3 independent reviewers
   across model tiers, and consensus assembly is real.
3. Least privilege is preserved: reviewers cannot mutate the workspace or
   reach outside it.
4. The harness detects and reports a degraded review rather than silently
   accepting single-reviewer coverage.

## 3. Requirements

### R1. Verification evidence input (preferred path)

* The `review` skill and `Adversarial Review` agent MUST accept a
  "verification evidence" input supplied by the caller: gate commands, exit
  codes, bounded redacted output, the reviewed HEAD SHA, and a path to the
  diff.
* The caller (Ship) runs the quality gates once, before dispatch, and
  passes the same evidence to every reviewer.
* Reviewers remain `read, search`. They MUST cite the evidence for any claim
  about build, test, or format state.
* A review with no evidence input MUST be marked `evidence: absent` in its
  report.

### R2. Optional restricted execution tool

* The orchestrating `Adversarial Review` agent MAY be granted a terminal
  tool, restricted to read-only verification commands via an allowlist:
  `go build`, `go vet`, `gofmt -l`, `go test`, `git diff`, `git show`,
  `git log`, `git status`.
* The allowlist is declared in the agent template, resolved per workspace
  profile (language toolchain commands come from the workspace profile, not
  hardcoded to Go).
* No `edit`-capable terminal commands, no network commands, no commands that
  write outside the workspace (Constitution III, IV, VII).
* Reviewer personas MUST NOT receive a terminal tool.
* Output capture is bounded (size and line limits) and redacted, consistent
  with the circuit-breaker logging rules.

### R3. Reviewer fan-out must be real and verifiable

* The `Adversarial Review` agent MUST dispatch at least 3 reviewers (plus the
  anchor reviewer when configured) and record, per reviewer: agent name,
  resolved model route, tools actually available, files actually read, and
  whether it completed.
* A reviewer that returns without reading the diff or evidence MUST NOT be
  counted toward consensus.
* If fewer than 3 reviewers complete, the report MUST carry
  `REVIEW_DEGRADED: reviewer-count` with the actual count. The caller MUST
  treat this as a non-passing gate unless the operator explicitly accepts it.
* Template and runtime checks MUST confirm the runtime can spawn the
  declared depth-2 and depth-3 reviewers with the declared model overrides
  (`verify-harness`).

### R4. Degradation reporting

* The review report MUST include a header block:
  `reviewers_requested`, `reviewers_completed`, `evidence: present|absent`,
  `tools_per_reviewer`, `degradations: []`.
* Ship MUST copy this block into the PR "Local Review Readiness" section so a
  single-reviewer or evidence-free review cannot read as full coverage.
* Dark mode MUST NOT treat `REVIEW_DEGRADED` as satisfying the
  adversarial-review escalation gate.

### R5. Template and generation changes (autoharness)

* Update the subagent templates under `templates/` that generate:
  `adversarial-review.agent.md`, the persona reviewers, and the `review`
  skill, to add the evidence input, the optional allowlisted terminal for the
  orchestrating agent, and the report header.
* Add tool declarations as template variables so each workspace can set
  `adversarial_review.terminal: none | allowlisted` in
  `.autoharness/config.yaml` (default `none` with evidence input, safe by
  default).
* Add schema coverage in `harness-config.schema.json` for the new settings.
* Add `verify-harness` and `harness-doctor` checks that flag (a) reviewers
  with unexpected tools, (b) an allowlist containing mutating commands, and
  (c) missing evidence-input wiring in Ship.
* Regeneration must not hand-edit generated files in installed workspaces;
  changes flow through templates and `tune-harness`.

### R6. Ship integration

* In the Ship build/review step, run quality gates first, persist bounded
  evidence, then invoke review with that evidence.
* Escalate to adversarial review under the existing triggers (3+ P0/P1, or
  security-sensitive) and always include the evidence input.
* Record the review report header in the PR body readiness block.

## 4. Non-goals

* Giving reviewers write access or the ability to apply fixes.
* Changing consensus assembly rules or severity definitions.
* Removing the standard code-review path.

## 5. Acceptance criteria

1. A review run with evidence input produces findings that cite the evidence
   and a report header showing at least 3 completed reviewers.
2. A run where a reviewer cannot be spawned yields `REVIEW_DEGRADED` and a
   non-passing readiness result in Ship.
3. `verify-harness` fails if any persona declares a terminal tool or the
   allowlist contains a mutating command.
4. With `adversarial_review.terminal: allowlisted`, the orchestrating agent
   can run the allowlisted gates and cannot run anything else (negative test
   with a disallowed command).
5. The PR readiness block shows reviewers requested/completed and evidence
   state for every PR in a dark run.

## 6. Risks and open questions

* Tool naming differs by runtime (`terminal`, `execute`, `shell`); the
  template needs a per-environment mapping.
* Allowlist enforcement may be runtime-dependent; if the runtime cannot
  enforce it, R1 (evidence input) is the only safe path and R2 must be off.
* Cost and latency of 3+ reviewers per PR in long dark runs; consider
  scoping the full panel to escalation triggers only.
* Related observation from the same run: Copilot review can land after merge
  (PR #145). The P-018 gate returned `NOT_APPLICABLE` because Copilot had not
  yet engaged. Consider a separate requirement: when `copilot_review` is
  enabled, require an explicit request plus a bounded wait or an audited
  override before merge, instead of passing on silence.
