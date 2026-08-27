---
title: "Orchestrator session memory — PR #411 adversarial review, remediation, and merge"
date: 2026-08-26
agent: orchestrator
route: gpt-5.6-sol / openai / xhigh
session_id: orchestrator-2026-08-26-pr411-adversarial-review-merge
source: docs/memory/2026-08-26-orchestrator-pr411-adversarial-review-merge.md
doc_type: memory
---

# Orchestrator session memory — PR #411 adversarial review and merge

## Context

The Copilot shadow reviewer stalled on PR #411 (`chore/p020-context-compaction`)
and could not resume. The operator authorized an **operator-directed review
substitution**: perform an independent adversarial review, and merge only if
everything checked out.

## What was done

Two independent hostile `code-review` agents ran against the branch (one framed
on content loss, one on integrity), plus a separate non-overlapping pass. Every
finding was then **independently verified against evidence rather than accepted
on assertion**, and each was subjected to a **fairness test**: *is this a
regression this PR introduces, or the repository's pre-existing ambient state?*

Because real P0/P1 findings came back, the operator's merge precondition
initially **failed**. Remediation followed, then merge.

## The fairness test was the highest-leverage technique

It materially reduced **three** separate findings, two of them headline:

| Claim | Verified reality |
|---|---|
| "25 of 26 decided-plans assert false status" | Joined all 32 plans against the authoritative backlog (957 items). **15 provably shipped**, 2 mixed, **9 genuinely open — status was already correct.** |
| "73 new lint violations with invented `doc_type` values" | **40** were genuine missing required fields. The other **33** are `unknown_doc_type` against a **closed vocabulary already stale relative to the repo** — it also rejects pre-existing `audit`, `deliberation`, `plan-hardening`, `plan-review`. `decided-plan` has **6 precedents on `main` and is prescribed by the compact-context SKILL**. |
| "127 dangling references" | **14** on live surfaces. The larger count included immutable append-only history, which was correctly excluded. |

The lesson generalizes: **a reviewer's severity and count are themselves claims
requiring verification.** Accepting them uncritically would have caused three
wrong "fixes" — including renaming `decided-plan`, which would have *created*
inconsistency with `main` and contradicted the governing skill.

## Root cause of the P0/P1 class

Compaction **flattened dated subdirectories**:
`docs/memory/<date>/x.md` → `docs/archive/memory/x.md`. A naive
`docs/X` → `docs/archive/X` substitution cannot express that mapping, which is
exactly why a set of references survived the original commit unrepointed.

## Self-review caught a defect the external reviewers missed

Reviewing my **own** fix commits surfaced three dangling references in stash
entry `34D50F2D`. The fairness test showed `main=1, head=1` — they exist
identically on `origin/main` and this PR never touched those lines. They were
left by an **earlier merged PR** (the supervisor-design quarantine), a different
contract surface. Per **P-021 C1**, genuine ambiguity resolves OUT of scope as
the fail-safe default, so it was **captured as `99E4CF94`**, not fixed in flight.

## Failed / non-viable approaches

* **Re-engaging the Copilot reviewer.** Re-requested review via REST, then polled
  the full §1.2 back-off (2/2/3/3/5 min = 15 min). Copilot's last review stayed
  pinned at `3aa53bcf` while HEAD advanced. This reproduces the documented
  **P-018 deadlock**: once the review request is satisfied, a review-fix push
  moves HEAD but triggers no new review, so the gate can never self-clear.
  Resolved via the audited `--force` override (precedent: PR #337, same verdict),
  logged to `.autoharness/gates/copilot-review-force-audit.log`.
* **`--json` on `backlogit docs lint`.** Suppresses output entirely; the bare
  command already emits JSON. The `--json` flag silently produced an empty
  result that read as "0 findings" — a false all-clear.
* **`subprocess` default encoding on Windows.** `cp1252` raised
  `UnicodeDecodeError` on `git diff` output; must pass `encoding="utf-8",
  errors="replace"`.

## Outcome

Merged as **`be97deb4`** (true merge commit, two parents — P-009 satisfied)
after all findings were remediated and verified:

* decided-plan false status → **0 remaining**
* required-field lint gaps on new files → **0 remaining** (73 → 33 findings, all
  residual are the stale-vocabulary class shared with `main`)
* dangling references on live surfaces → **0 remaining**
* both content-fidelity losses restored; overstated "verbatim" claim corrected
* CI green; **0** unresolved review threads

## Follow-ups captured

`11BCE865`, `1BDBD08B`, `99E4CF94`.
