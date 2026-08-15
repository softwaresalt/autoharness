---
title: "Plan Review — Adopt the backlogit `.backlog` storage root"
date: "2026-08-14"
description: "Adversarial plan review of the .backlog storage-root adoption plan and its P-006 hardening. Verdict PASS with 0 P0 and 0 P1 outstanding after one fix cycle."
doc_type: review
source: docs/reviews/2026-08-14-backlog-storage-root-adoption-review.md
review_id: "PLAN-BACKLOG-ROOT-R"
verdict: "PASS"
stash_ids: ["BED0DDED"]
model_route:
  model_family: claude-opus-5
  model_provider: anthropic
  reasoning_effort: high
linked_artifacts:
  - "docs/plans/2026-08-14-backlog-storage-root-adoption-plan.md"
  - "docs/plans/2026-08-14-backlog-storage-root-adoption-hardening.md"
  - ".backlogit/queue/018-DL.md"
---

# Plan Review — `.backlog` storage-root adoption

**Verdict: PASS.** 0 P0 outstanding, 0 P1 outstanding. 1 of 3 review cycles used.

## Findings

### P0-1 — Unblocker claim must rest on primary evidence, not release notes — RESOLVED

*Finding:* this stash was deferred twice on the strength of read-only source
verification. Reversing that on CLI help text alone would be weaker evidence than
the deferrals it overturns.

*Resolution:* the plan cites primary source at v1.9.0 / HEAD 39528a41 for every
unblocker element — `workspaceRootCandidates` at `workspace.go:25`, the override
constant at `:27`, the ambiguity branch at `:310-316`, `migrate_workspace_dir.go`,
and four upstream regression test files. Evidence strength now exceeds that of the
deferrals. **Closed.**

### P0-2 — Dark-mode rename hazard — RESOLVED

*Finding:* the stash's own text forbids any change that could split backlog state.
A harvested task that renamed this repository's `.backlogit` would do precisely
that, and would do it while the pipeline holds the directory open.

*Resolution:* hardening **H5** excludes the live rename from all automation and
requires the exclusion to be restated verbatim in every task's acceptance
criteria so it survives per-task context isolation. Plan section 2 lists it as
out-of-scope item 1. **Closed.**

### P1-1 — Registry would misdescribe the workspace — RESOLVED

*Finding:* flipping `.autoharness/backlog-registry.yaml` `directory:` to
`.backlog` while the physical directory is still `.backlogit` would break every
registry-routed operation in this repository.

*Resolution:* out-of-scope item 2 pins the registry to reality; it changes only
when the operator performs the migration. **Closed.**

### P1-2 — Silent precedence divergence — RESOLVED

*Finding:* a follower resolver that "prefers the one that exists" instead of
following the upstream order would appear to work until both roots exist.

*Resolution:* **H2** makes exact precedence a P0 invariant with an explicit
test against the upstream candidate table, and forbids fall-through when an
explicit override names a missing directory. **H3** requires fail-closed
behaviour on ambiguity. **Closed.**

### P1-3 — Schema narrowing risk — RESOLVED

*Finding:* "update the schemas to `.backlog`" could be implemented as a
replacement, invalidating every existing legacy workspace.

*Resolution:* **H4** requires additive widening plus a version bump and forbids
removing `.backlogit` from any enum or example set. **Closed.**

*Post-merge correction (PR #339 Copilot review, comment 3788712399).* The
narrowing risk this item guarded against cannot arise, because there is no
validation to narrow: all three occurrences are unconstrained strings or prose
(see the revised T3 in the plan). The forbid-removal half of **H4** still stands;
the mandatory-version-bump half is now **conditional** on T1 finding a real
validation constraint, and a genuine bump additionally requires a versioned schema
mirror plus a `src/autoharness/schema_contracts.py` update.

### P2-1 — Doc surface is broad but low-risk — ACCEPTED

13 doc references are prose. T7 is sequenced last so documentation describes
shipped behaviour. Accepted as-is.

## Decomposition check

Seven tasks, each confined to a single concern and template family:
inventory / resolver / schemas / templates+instructions / CI scripts / tune rule
/ docs. No task mixes schema work with CLI work or template work. All are inside
the 2-hour envelope. Dependency chain `T1 -> T2 -> {T3, T5} -> T4 -> T6 -> T7`
is acyclic.

## Gate result

**PASS — cleared for harvest.**
