---
title: "Read the full text of every stash entry that names a shipment before claiming it: a hold written as stash prose was invisible to the gates"
problem_type: process-gap
category: workflow
root_cause: "A safety-critical hold on shipment 208-S was written at the tail of a long free-text stash entry. Claim eligibility, dag-readiness, and pre_claim read backlog data only, so none of them could see the hold. The eligibility judgement read the first part of each entry, and Ship's discovery grep stopped at 25 hits, so the hold was not read before the shipment was claimed and nine tasks were implemented."
tags: [stash, hold, eligibility, claim, dag-readiness, pre-claim, discovery, truncation, p-021, orchestrator, ship]
shipment: 208-S
date: 2026-10-10
source: docs/compound/2026-10-10-read-full-stash-text-for-holds-before-eligibility-or-claim.md
doc_type: learning
---

## Problem

Stash entry `3FC709F9` (kind bug, priority high) records a Copilot finding on the
201-F disposition-marker rule. It was captured on 2026-10-09 by Stage, in PR #510
(branch `chore/stage-3fc709f9-capture`, merged to `main` as `26446a68`). Stage's
portfolio PR #509 (`chore/stage-208s-213s-portfolio`, merged as `cf646ce0`) stages
208-S through 213-S, and its body records the same hold.

The hold is at the tail of the entry, about 3.2 KB into an entry of roughly 4 KB. It
reads:

> HOLD: shipment 208-S must not be claimed, and 201.002-T, 201.003-T, 201.005-T,
> 201.006-T and 201.008-T must not be implemented, until this entry is triaged through
> the deliberate skill (P-021 C6) and the plan and tasks are amended, or the operator
> explicitly accepts the weaker rule.

The hold exists only as stash text. Backlogit claim eligibility, `dag-readiness`, and
`pre_claim` read backlog data and cannot see free text in a stash entry. The gates
therefore could not block the claim.

What happened:

* The Orchestrator's eligibility assessment judged 208-S claimable from the DAG data
  and the first ~760 characters of each stash entry (the Orchestrator's own report).
  It never reached the tail of `3FC709F9`.
* Ship's P-021 discovery grep was `Select-Object -First 25`, so the output was
  truncated. A full scan of the 239 active stash entries (performed on 2026-10-10)
  finds 11 matches for hold and eligibility terms, and `3FC709F9` is among them. The
  truncated grep missed it.
* Ship claimed 208-S. Nine tasks were implemented (201.001-T through 201.009-T), five
  of which the hold names.
* Copilot flagged the conflict on PR #511 (thread `PRRT_kwDORzpWpM6rB1WB`, left open
  as a merge blocker).

Consequence at capture time (historical): 208-S was active and held, the nine tasks were done, PR #511 was a draft,
and the operator must decide. Accept the weaker rule in writing, direct a Stage
triage of `3FC709F9`, or abandon and re-queue.

Outcome (2026-10-10T08:09:29Z): the operator accepted the association-only disposition-marker rule in writing for 208-S (PR #511 comment 6095553824) and kept `3FC709F9` as the hardening follow-up. That acceptance lifts the hold on 208-S. PR #511 carries the 208-S implementation. The lesson above still applies: a hold written only as free text stays invisible to gates until someone reads it in full.

## Root causes

* **Truncated reads of long free text.** Both the eligibility read and the discovery
  grep stopped before the hold. A truncated read looked complete.
* **A safety-critical hold living only in free text.** Gates consume backlog data.
  A hold written as prose is invisible to them, so it can only be found by a human
  or an agent that reads the whole entry.
* **No fail-closed on truncation.** When a read is cut short, the result should be
  "unknown", not "no hold found". Both readers treated a cut-short result as complete.

## Solution

Prevention rules, in order of priority:

1. **Read in full before any eligibility judgement or claim.** Paginate through every
   active stash entry that names the target shipment, feature, or task ID. Search for
   the hold terms (`HOLD`, `must not be claimed`, `do not claim`). If any read is
   truncated, fail closed: report "unknown" and stop.
2. **Represent holds as backlog data that the gates can read.** Prose cannot block a
   claim. Use a hold-gate shipment, as shipment `207-S` does for `168-S`: its title is
   "HOLD GATE - 168-S distribution re-plan (039-DL): not claimable; Stage disposes after
   deliberation". The title states the hold, but it is not yet a machine-consumed
   blocking edge. The proposed follow-up `FCC31BAB` asks that `dag-readiness` and
   `pre_claim` read such a hold, so a gate can refuse the claim without any reader
   remembering to look.
3. **Ship intake runs the untruncated stash scan before the claim.** The scan is part of
   Ship Step 0.5, before `pre_claim`. Its result is recorded, and a hit halts the intake.
4. **Orchestrator eligibility tables list holds as a distinct blocking cause.** A
   shipment with a hold is ineligible, whatever its DAG position, until the hold is
   cleared by its named disposition.

## Discovery record and the duplicate

* **Duplicate:** Ship's capture `F373C349` (filed during the pre-PR local review, before
  PR #511 existed, "harden Copilot review-body marker trust beyond association") is a
  duplicate of `3FC709F9`. It is the same expansion: an effective-permission check on
  the marker author in place of the association filter. Stage triage should archive
  `F373C349`. Ship cannot archive it, and it did not reuse `3FC709F9` because the
  discovery grep had missed the entry.
* **Related, not duplicates:** `2940EA5F` (the `168-S` manifest declares only `[166-S]`,
  so eligibility can report it claimable), `039-DL` (a prose hold on `168-S`), and
  `FE136189` (a queue-wide readiness audit).
* **New follow-up:** `FCC31BAB`, a capture-only entry (kind task, provisional priority
  high). It proposes machine-readable holds consumed by `dag-readiness` and `pre_claim`,
  plus the untruncated stash scan in Orchestrator Step 0 and Ship Step 0.5.

## Checklist for the next intake

* [ ] Count every stash entry that names the target ID, and read each in full.
* [ ] Search for the hold terms in the full text, and report any hit by entry ID.
* [ ] If any read was truncated, or a count is uncertain, stop and report "unknown".
* [ ] Check the backlog for a hold-gate shipment or a blocking edge on the target.
* [ ] Record the scan result in the intake record before the claim.

## References

* Stash `3FC709F9` (the hold) and PR #509, PR #510, PR #511.
* Stash `F373C349` (duplicate), `FCC31BAB` (new follow-up), `039-DL`, and `2940EA5F`.
* Shipment `207-S` (the HOLD GATE pattern) and `168-S`.
* Companion learning: `docs/compound/2026-10-10-operator-staged-config-carry-forward-and-route-pin-cascade.md`.
