---
title: "Multiple implementation worktrees blocks the pipeline-topology gate globally, regardless of shipment target"
date: 2026-08-16
tags: [ship, topology-gate, worktree, P-016]
---

## Problem

`autoharness gate pipeline-topology --mode agent --shipment {id} --phase
lifecycle --json` blocked with `MULTIPLE_IMPLEMENTATION_WORKTREES` when
attempting to close shipment `136-S`, even though `136-S`'s own work had
nothing to do with the second worktree. The gate's `worktree_topology` check
(`src/autoharness/gates/topology.py::_worktree_uniqueness_check`) enumerates
**every** git worktree attached to the repository on the current machine —
not scoped to the target shipment, not scoped to which worktree the
invoking process is running from — and requires exactly one non-spike/
non-research "implementation" worktree across the whole checkout. A worktree
qualifies for the spike/research exemption only if its branch name starts
with `spike/` or `research/` **and** it carries a valid, unexpired
`role: spike-research` marker file; a normal `feat/*` or `chore/*` worktree
never qualifies, no matter how unrelated its content is to the shipment
currently being gated.

## Root cause

A second worktree (`C:/Source/GitHub/autoharness-116-s`, branch
`feat/circuit-breaker-diagnostic-escalation-policy`, the head branch of a
separate, unrelated, still-open PR #348) had been left attached from prior
session setup. Ship's own protocol never creates a second worktree for its
own branch switching (Step 0.5's Branch Creation Gate always operates by
checking out branches in place within a single worktree); only Stage may
create short-lived, explicitly-marked `spike/`/`research/` worktrees. Any
second, unmarked implementation worktree — however it got there — trips this
gate for **every** subsequent `pre_claim`/`post_claim`/`lifecycle` gate
invocation targeting **any** shipment, not just the one associated with that
worktree's branch.

## Resolution

1. Verify the extra worktree is clean and byte-identical to its own remote
   tracking branch (`git status --short`; compare local HEAD to
   `git rev-parse origin/{branch}` after `git fetch`) — this proves no work
   will be lost.
2. Remove it with `git worktree remove {path}` (never `--force` unless the
   clean/identical check above already passed) — this only detaches the
   worktree *directory*; the branch itself, and its remote copy, are
   untouched and can be checked out again later, including back in the same
   single remaining worktree.
3. Re-run the topology gate — with exactly one implementation worktree
   remaining, `worktree_topology` now reports `WORKTREE_TOPOLOGY_OK`.
4. Resume work on the removed worktree's branch (e.g. PR #348) by checking
   it out directly in the single remaining worktree once the *other*,
   unrelated shipment's closure work currently occupying that worktree is
   complete — sequential single-worktree operation, never parallel
   worktrees, is what both P-001 (one active release unit) and P-016 (no
   parallel worktree execution) actually require.

## Generalization

Before invoking **any** `pipeline-topology` gate call (`pre_claim`,
`post_claim`, or `lifecycle`, for any shipment), run `git worktree list
--porcelain` first and confirm exactly one non-spike/research worktree
exists on the machine. If more than one is attached, the gate will block
regardless of which shipment is being processed. Resolving this is a
pre-condition of Ship's Step 0.0/2 pipeline gates, not a token the gate lets
you route around per-shipment — there is no `--shipment`-scoped bypass in
the check itself.
