---
title: P-021 bounded fix-cycle scope containment plan hardening
description: P-006 hardening pass (H1-H13) over the P-021 scope-containment plan; adversarial guards for a policy change spanning agent role boundaries, shared instructions and the dogfood checksum set
doc_type: plan
source: docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-hardening.md
status: hardened
date: 2026-08-18
stash_source: B48A482A
deliberation: 019-DL
plan: docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-plan.md
feature: 134-F
shipment: 143-S
route: claude-opus-5/anthropic/high
---

<!-- markdownlint-disable-next-line MD025 -->
# Plan Hardening — P-021 Bounded Fix-Cycle Scope Containment & Deferred Expansion Capture

| Field | Value |
|---|---|
| Date | 2026-08-18 |
| Plan | `docs/plans/2026-08-18-bounded-fix-cycle-scope-containment-plan.md` |
| Deliberation | `019-DL` |
| Source stash | `B48A482A` |
| Trigger | P-006 — plan declares `Requires plan hardening: yes` (3 agent templates, 4 shared instructions, 8 dogfood artifacts, manifest variable + checksum set) |

## H1 — The Ship role-boundary carve-out must be minimal and enumerated, not a blanket unlock

**Risk.** Repairing the P-010 contradiction by simply deleting "stash
operations" from Ship's Forbidden column would silently grant Ship the full
stash surface — including triage, re-prioritization, and removal — which is
Stage-owned. That is a much larger authority change than the operator direction
requires, and it is exactly the kind of silent expansion P-021 exists to
prevent.

**Hardening.** Task 002 MUST express the carve-out as a *paired* edit:

* **Allowed** gains exactly one narrow verb: create a capture-only stash entry
  (deferred scope expansion under P-021, and the pre-existing follow-up capture
  at pre-merge Step 9 / post-merge Step 6).
* **Forbidden** MUST explicitly retain, by name: triage, prioritize/re-prioritize,
  re-classify, edit, harvest, deliberate on, and remove/archive stash entries.

A carve-out that leaves the Forbidden column silent on those verbs fails the
task's acceptance criteria. Task 011 MUST assert both halves.

## H2 — `backlogit_stash_remove` at Ship post-merge Step 7 is pre-existing and must be preserved, not swept into the carve-out

**Risk.** Ship's post-merge Step 7 already calls `backlogit_stash_remove` for
`custom_fields.source_stash_id`. H1 tells task 002 to keep "remove" in the
Forbidden column. Naively applied, that would contradict an existing, correct,
shipped behavior.

**Hardening.** Task 002 MUST distinguish the two by *provenance*, not by verb
alone: retiring the source stash entry that fed the shipped scope is a
manifest-derived closure operation and stays Allowed; discretionary removal of
any other stash entry stays Forbidden. Task 011 MUST assert that the post-merge
Step 7 source-artifact-cleanup language is still present and not weakened.

## H3 — Every dogfood edit is a three-part atomic unit

**Risk.** `tests/test_circuit_breaker_policy_contract.py` asserts the
LF-normalized rendered template is byte-identical to the dogfood output **and**
that the manifest checksum matches. Editing a template without re-rendering, or
re-rendering without refreshing the checksum, produces a red suite and a
misleading "template already done" state.

**Hardening.** For tasks 002, 003, 004, 005, 006, 008, 009, 010 the unit of work
is atomic and MUST be completed within the single task:

1. edit the source template,
2. re-render the dogfood artifact so it is byte-identical under LF
   normalization,
3. refresh `checksum:` in `.autoharness/harness-manifest.yaml`, computed from
   the **LF-normalized committed blob** via `git cat-file -p :<path> | sha256`
   per the procedure established in 115-S (the `.gitattributes` `eol=lf` pin
   keeps this deterministic regardless of local `autocrlf`),
4. append a provenance sentence to that artifact's manifest `note:` field
   naming the task ID and the P-021 change.

No task may leave a template edited with a stale dogfood or stale checksum.

## H4 — Task 004 and task 002 both edit `_ship.agent.md` — serialize them

**Risk.** Tasks 002 and 004 touch the same template, same dogfood, and the same
manifest checksum line. Executed out of order or concurrently they will clobber
each other's checksum.

**Hardening.** The dependency `004 → 002` is **mandatory and load-bearing**, not
advisory. Ship MUST complete 002 (including its checksum refresh) before
starting 004, and 004 MUST recompute the checksum from the post-002 blob rather
than assuming 002's value. Same rule applies to 003, which depends on 002 for
its normative reference even though it edits a different file.

## H5 — Fix the shared-instruction ordering hazard between 005 and 006

**Risk.** Task 006 (github-pr-automation) quotes the C1 scope test authored in
task 005 (circuit-breaker). If 006 lands first it will either duplicate the
normative text divergently or forward-reference a section that does not exist.

**Hardening.** The dependency `006 → 005` is mandatory. Carrier surfaces MUST
**reference** the normative text by policy ID and section name (`P-021 C1, see
the circuit-breaker Review-Fix Cycle Definition`) rather than restating it in
their own words. Exactly one surface — `workflow-policies.md.tmpl` (task 001) —
holds the authoritative wording; the circuit-breaker instruction holds the
operational restatement for the review-fix loop; everything else references.
This prevents seven divergent paraphrases of the same rule.

## H6 — The C1 ambiguity default must be stated as fail-safe, with a worked counter-example

**Risk.** "Same contract surface" is the crux judgment and is easy to read
loosely. Without a concrete counter-example, an agent under review pressure will
rationalize almost any finding as same-surface — which reproduces exactly the
failure mode PR #348 documented.

**Hardening.** Tasks 001 and 005 MUST both include the compound learning's
worked discrimination, in normative form:

* "the verifier doesn't require the field we just added" → **same surface** →
  fix it;
* "the regex doesn't handle an object-separated form" → **different surface** →
  defer, *even though it is the same function, same file, same PR, and was
  in scope for an earlier authorized cycle*;
* "a policy interaction is unresolved" → **different surface and different kind
  of work** (design decision) → defer.

Both tasks MUST cite
`docs/compound/2026-08-16-bounded-review-fix-cycle-scope-and-mechanical-consequence-judgment.md`
as the provenance. Task 011 MUST assert the "same function, same file, same PR
is not sufficient" clause is literally present.

## H7 — C2 capture must specify required fields, or it will produce unactionable stash entries

**Risk.** "Capture it as a stash entry" without a required-field list yields
one-line entries that Stage cannot triage months later — the deferred item
becomes as lost as a silently dropped comment, and the policy's whole value
evaporates.

**Hardening.** Task 001 MUST specify the minimum capture payload, and tasks 004,
006, 007 MUST reproduce it as a checklist:

1. `DEFERRED SCOPE EXPANSION` marker as a literal, greppable token in the entry
   text;
2. what the expansion is, in one sentence;
3. why it was judged out of scope, citing the C1 test;
4. source refs — PR number, review-thread ID (when applicable), task ID, feature
   ID, shipment ID;
5. `requires deliberation` flag, satisfying the operator's mandatory
   deliberation/research requirement;
6. `kind` and a provisional `priority`.

Ship sets the provisional priority as a capture attribute; **re-prioritizing it
later remains Stage-only** (consistent with H1).

## H8 — C6 must override shape-based routing explicitly, or Stage will short-circuit it

**Risk.** Stage Step 1 classifies entries as feature-shaped or task-shaped, and
task-shaped entries can flow to grouping and planning. A deferred-expansion
entry is frequently task-shaped and trivially small, so the existing routing
will happily carry it straight to a plan — defeating the operator's *mandatory*
deliberation requirement.

**Hardening.** Task 008 MUST state the override as a precedence rule: the
`DEFERRED SCOPE EXPANSION` marker is evaluated **before** shape classification
and forces the `deliberate` route regardless of shape, size, priority, or
apparent triviality. It MUST also state that Step 1.5 contextual grouping may
group such an entry only *after* its deliberation exists. Task 011 MUST assert
the precedence wording.

## H9 — Dark-mode non-bypass must be phrased as a P-017 relationship, matching the established P-018 pattern

**Risk.** A free-floating "dark mode doesn't allow this" sentence in the
Orchestrator will drift from the policy registry and carries no gate semantics.

**Hardening.** Task 001 MUST include a `**Relationship to P-017**` subsection
modeled on P-018's ("in dark factory mode, P-021 is preserved in full; a
`DARK_MODE_ACTIVE` activation record does not satisfy or waive it"). Task 009's
Orchestrator and dark-prompt edits MUST reference that subsection rather than
inventing parallel wording.

## H10 — Task 010 is a disclosed coherence correction, not a drive-by

**Risk.** `HARNESS_ENFORCED_SUMMARY` currently reads `P-001 through P-019`,
already stale by one policy (P-020). Bumping it to P-021 also silently fixes a
pre-existing defect. Under the very policy being authored, an undisclosed
adjacent fix is the failure mode.

**Hardening.** Task 010's description and the PR residual-risk record MUST
explicitly disclose that the range bump corrects a pre-existing P-020 omission
as a *mechanical consequence* of adding P-021 (the range literally must include
the new ID) — the C1 same-contract-surface test is satisfied. No other
`HARNESS_ENFORCED_SUMMARY` line may be touched.

## H11 — Verification must prove clause coverage, not just byte identity

**Risk.** A contract test that only checks byte identity and checksums will pass
even if a carrier surface silently omits its clause, because the dogfood would
faithfully mirror the omission.

**Hardening.** Task 011 MUST include a clause-coverage matrix assertion: for
each of C1–C7, at least one named carrier file contains its designated marker
text, and the specific pairings (C1 → circuit-breaker + workflow-policies;
C2 → ship + pr-lifecycle + fix-ci; C3 → github-pr-automation + pr-lifecycle;
C4 → orchestrator + dark prompt + ship Stop Conditions; C5 → ship Role Boundary + role-enforcement; C6 → stage; C7 → workflow-policies) are asserted
individually so a single missing carrier fails a distinct test.

## H12 — Guard against P-021 being read as a licence to stop fixing things

**Risk.** An over-broad reading ("if in doubt, defer") could let an agent defer
genuine, in-scope, mechanical completions of its own change and ship a
half-finished fix — trading silent scope expansion for silent scope *contraction*,
which is equally dishonest and harder to detect.

**Hardening.** Tasks 001 and 005 MUST state the symmetric obligation: C3
requires the original defect/comment to be resolved **as far as possible without
the expansion**, and a same-contract-surface completion of the authorized change
is **in scope and must be fixed**, not deferred. Deferral without a captured
entry and a residual-risk record is itself a C7 violation.

## H13 — Preserve unrelated operator working-tree state

**Risk.** The working tree carries staged, unrelated operator changes
(`.gitmodules`, `references/azd-backlogbuilder`, `references/azd-backlogloader`,
`references/skillopt`, `references/waza`, `references/witr`).
Any `git add -A` or `git commit -a` during execution would sweep them into this
shipment's PR.

**Hardening.** Every commit in this shipment MUST stage an explicit, enumerated
path list. `git add -A`, `git add .`, and `git commit -a` are prohibited for the
duration. Ship MUST verify with `git --no-pager diff --cached --name-only`
before each commit that only this feature's declared surfaces are staged.

**Inventory is illustrative; the allowlist is the control.** The path list above
records the unrelated staged entries observed when this hardening was authored
and was extended on 2026-08-19 to add `references/azd-backlogbuilder` and
`references/azd-backlogloader`, which were present but unlisted. That extension
does NOT change the safety rule, and the rule's protection does NOT depend on
the inventory being complete: because staging is an explicit enumerated
ALLOWLIST of this feature's own surfaces, any unrelated entry — listed here or
not, already present or appearing later — is excluded by construction. The
inventory exists to make the pre-commit `--name-only` verification concrete and
to help a reviewer recognize a sweep, never as a denylist to be matched against.
An out-of-date inventory is therefore a documentation defect, not a containment
failure.

## Hardening verdict

**PROCEED.** No task exceeds the 2-hour rule after hardening. H1/H2 tighten task
002 to a precise paired edit. H3 makes every dogfood task atomic. H4/H5 make two
implicit orderings explicit and load-bearing. H6/H7/H8/H12 close the four
substantive semantic gaps. H10/H13 keep the change honest at its own boundary.
H11 upgrades verification from byte identity to clause coverage.

No new tasks are required; all hardening lands as tightened acceptance criteria
on existing tasks 001–011.
