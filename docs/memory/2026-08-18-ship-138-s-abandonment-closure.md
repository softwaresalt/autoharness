---
date: 2026-08-18
agent: ship
shipment: 138-S
feature: 129-F
disposition: cancelled
type: cancellation-closure
---

# Ship — 138-S / 129-F Cancellation Closure Session Memory

## What happened

Executed the complete, traceable cancellation lifecycle for shipment
`138-S` ("Migrate live Backlogit storage root `.backlogit` -> `.backlog`")
per an explicit operator scope correction: `.backlogit` remains an
acceptable, permanently supported storage root; `.backlog` is the default
only for new workspaces; existing workspaces (including this repository)
need no migration. `129-F` and its 9 child tasks were already `rejected`
by Stage in a prior session. This session's job was solely to bring
`138-S` to a durable terminal `abandoned` state and produce full closure
evidence — no implementation, no migration, nothing built.

## Key decisions

* Did **not** use the installed `autoharness.exe` CLI's `gate` subcommand
  (absent in this install). Used the source-tree gate directly via
  `PYTHONPATH=src; python -c "from autoharness import cli; cli.main([...])"`
  — this worked and gave full JSON gate output.
* Pre-claim topology gate passed cleanly (exit 0) while still on the
  previously-checked-out `post-merge/131-f-...` branch. After creating the
  dedicated `chore/abandon-138-s` cancellation branch, the same gate
  returned `BRANCH_MISMATCH` (exit 1). **Corrected characterization**
  (Copilot review on PR #362 caught an inaccurate first-draft framing of
  this as a "cancellation gate coverage gap"): the gate is purpose-agnostic
  and accepts only canonical `feat/{slug}` / `chore/{slug}` or
  `feat/{shipment-id}-{slug}` / `chore/{shipment-id}-{slug}` branch forms
  (`_branch_aliases`, `src/autoharness/gates/topology.py:1040-1048`) — the
  shipment ID, when present, must be a *leading* token. `chore/abandon-138-s`
  reverses that order and matches neither form, so this is a genuine,
  correctly-detected `BRANCH_MISMATCH`, not a missing feature. The branch
  name was used anyway because the **operator's own current-session
  instructions explicitly named `chore/abandon-138-s`**, superseding both
  the gate's naming convention and Stage's earlier "Ship MUST NOT create a
  branch for 138-S" instruction (disclosed and cited in the decision doc's
  §8 append). The other four gate checks (active-shipment invariant,
  worktree topology, shipment readiness) are branch-name-independent and
  were independently reconfirmed unchanged after the branch switch. Never
  used `--force` (operator-only, not agent-reachable, and unneeded — the
  invariants were already independently proven and the branch name was
  operator-authorized, not gate-bypassed).
* Created the cancellation branch from `main` rather than reusing the
  already-merged `post-merge/131-f-...` branch, since the two trees are
  byte-identical (`git diff main HEAD --stat` empty) — so the switch was
  provably a no-op for tracked content, while giving a clean dedicated
  branch for the cancellation commit.
* Verified byte-for-byte preservation of unrelated operator-staged changes
  (`.gitmodules`, `references/skillopt`, `references/waza`,
  `references/witr`) across the branch switch via full `git ls-files -s`
  index diff (zero differences) and individual staged-blob-hash
  re-verification.
* `.backlogit/stash.jsonl` showing ` M` in `git status` is a stale
  stat/CRLF artifact, not real drift — confirmed via
  `git hash-object` == `git rev-parse HEAD:<path>` before and after.
* Backlogit's `queued -> abandoned` is not a direct transition; claimed
  first (`queued -> active`) purely as the mechanical state-machine
  prerequisite, then immediately abandoned (`active -> abandoned`). No
  implementation task was ever touched.
* `.backlogit/registry.yaml` has no directory-routing condition for
  `abandoned` (only `done/accepted/rejected/archived` -> `archive/`, and
  `queued/active/blocked/review` -> `queue/`) — so the abandoned shipment
  record correctly stays at `.backlogit/queue/138-S.md`. Status field is
  the source of truth, not file location, for this terminal state.
* Compaction (P-020): `docs/memory/` has 68 files / ~573 KB, over both
  manual thresholds. Given this task's explicit bounded scope, deferred
  full consolidation rather than expanding this PR's diff; recorded
  `compaction: degraded` (invocation mandatory and satisfied, depth
  deferred) — explicitly allowed by the operator's own instructions.

## Follow-ups (not created as backlog items — out of this task's bounded scope)

* `BED0DDED` stash archival is Stage-owned and intentionally left
  untouched; both §6 closure conditions in the operator decision doc are
  now satisfied, so Stage can archive it in a future session.
* A full `docs/memory/` compaction pass (68 files, ~573 KB) remains
  outstanding as a separate, larger effort — not filed as a P-015 item per
  this task's explicit bounded-stop instruction.

## Evidence

Full detail in `docs/closure/138-S-129-F-cancellation-closure.md` and the
append to `docs/decisions/2026-08-18-backlogit-legacy-root-support-operator-scope-correction.md`.
