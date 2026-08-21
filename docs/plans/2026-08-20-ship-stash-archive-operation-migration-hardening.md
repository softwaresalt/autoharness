---
title: "Plan hardening - Ship Step 7 stash-archive migration"
date: 2026-08-20
plan: docs/plans/2026-08-20-ship-stash-archive-operation-migration-plan.md
stash_id: 8D570CF8
status: "HARDENED (H1-H6); H1 mitigation superseded 2026-08-20 - atomic task restructure"
---

# Plan Hardening - Ship Step 7 stash-archive migration

Date: 2026-08-20
Agent: Stage (plan-harden gate, P-006)
Plan: `docs/plans/2026-08-20-ship-stash-archive-operation-migration-plan.md`
Stash source: `8D570CF8`
Status: **HARDENED (H1-H6)** - H1's mitigation superseded 2026-08-20 by the atomic
task restructure (see H1); H6 absorbed into the same atomic task.

Hardening was required because the change edits a **live policy clause**
(P-021 C5), a **shipped agent contract**, and the **verifier that enforces
them** - across five artifact families in one shipment. A careless rename here
can silently widen Ship's stash authority, which is the exact hazard C5 exists
to prevent.

---

## H1 (P1) - Task A and Task C are mutually breaking if split

> **Mitigation revised 2026-08-20** - see the superseding note at the end of this section.

`verify_workspace.py` asserts that `.github/agents/_ship.agent.md` **contains**
`backlogit_stash_remove`. So:

* Task A alone -> mirror no longer contains the marker -> verifier fails.
* Task C alone -> verifier demands a marker the mirror does not yet have -> fails.

Either ordering produces a red intermediate state.

~~**Mitigation**: Tasks A and C land **in the same commit**, or in adjacent commits
within a single PR that is never evaluated between them. Stated as an execution
condition on the plan. Ship must not split them across PRs.~~

> **MITIGATION SUPERSEDED 2026-08-20 (Stage review-fix) - the original mitigation
> was insufficient.** "Adjacent commits within a single PR that is never evaluated
> between them" does not hold: Ship evaluates the full configured suite before
> completing **each task**, not once per PR. Two tasks therefore means two gate
> evaluations, and one of them necessarily observes the red intermediate state.
> The same reasoning extends to Task D, which repaired assertions and a checksum
> that Tasks A and C invalidated, and so could not itself go green until they had
> landed - a deadlock.
>
> **Current mitigation: DISCHARGED BY CONSTRUCTION.** Tasks A, C and D are merged
> into a single atomic task (backlog `137.003-T`; `137.005-T` and `137.006-T`
> superseded and archived). With one task there is one gate, evaluated once, after
> every mutually-breaking edit has landed. No intermediate state is observable.
>
> **Standing constraint**: do **not** re-split `137.003-T`. Any future split must
> first show that each resulting task leaves the full configured suite green at its
> own completion gate.

## H2 (P1) - The rename must not collapse the C5 removal/archival distinction

P-021 C5 deliberately names removal **and** archival as *separately prohibited
discretionary dispositions*, because archival also takes a Stage-owned deferred
entry out of Stage's triage queue - a prohibition naming only removal would
leave the same loss reachable by another verb.

This migration renames the **allowed, manifest-derived** operation from remove to
archive. There is a real drafting hazard: after the rename, the clause says the
allowed exception is archival **and** that discretionary archival is prohibited.
That is correct and intended, but it reads as tension and invites a
"simplifying" edit that would delete the discretionary prohibition.

**Mitigation**: the plan states verbatim preservation of the distinction as an
acceptance criterion. Additionally, the DISCRETIONARY qualifier must remain
attached to **both** verbs, and the manifest-derived exception must remain
explicitly scoped to the post-merge Step 7 path. Any reviewer who proposes
removing the archival prohibition is to be refused with a pointer to this section.

## H3 (P1) - Historical records must not be swept up by a global rename

`backlogit_stash_remove` appears in four historical artifacts (two memory files,
one closure record, one shipped hardening record). A naive
find-and-replace-across-repo would falsify the historical record of what Ship
actually did on 143-S.

**Mitigation**: the plan enumerates the immutable set by name and adds a
verification step asserting `git diff --name-only` contains **no** path under
`docs/closure/` or `docs/memory/`. Ship must not use an unscoped global replace.

## H4 (P2) - The dogfood mirror asymmetry will look like a bug

The mirror carries the Role Boundary sentence (1 site) but **not** the full Step 7
block (which exists only in the template, 1 of its 2 sites). An executor
comparing site counts will see 2 template sites vs 1 mirror site and may
"fix" the mirror by back-porting the missing block.

That back-port is the `6D62077C` prose-drift problem and is explicitly out of
scope; doing it here would inject tens of lines of unreviewed agent contract into
the dogfood mirror under cover of a rename.

**Mitigation**: the plan states the asymmetry is expected and must not be
corrected. Recorded here as the rationale so the constraint is not mistaken for
an oversight.

## H5 (P2) - Registry deletion would misdescribe upstream reality

Deleting the `stash_remove` mapping from the registry template would state that
the operation does not exist. It does - the MCP tool is still exposed and still
functions, and the CLI retains `stash remove` as an alias of `stash archive`.

**Mitigation**: deprecate in place, do not delete (plan Task B). The registry's
job is to describe the tool truthfully, including its deprecated surface.

**Scope limit (added review-fix cycle 3)**: this mapping is retained for
**description only**. `backlogit_stash_archive` is exposed on MCP and
`backlogit stash archive` on CLI, so both P-012 legs resolve to the replacement.
H5 never authorises `stash_remove` as an execution fallback in any prescriptive
contract.

## H6 (P3) - Manifest checksum drift is a silent failure mode

Task A edits a file whose bytes are checksummed in `harness-manifest.yaml`, and
that checksum is asserted by the divergent-pair contract test. Forgetting the
refresh produces a failure whose message points at parity, not at this migration.

**Mitigation**: the checksum refresh is an explicit acceptance criterion of Task D,
and the plan's verification step restates it. Note the compound learning
`docs/compound/2026-08-15-checksum-drift-fix-correctly-surfaces-preexisting-self-hosted-customization.md`:
refresh the checksum **because the bytes legitimately changed here**, not to
silence an unexplained drift - if any *other* checksum is also stale, that is a
separate finding to capture, not to absorb.

---

## Residual risk accepted

* The `.autoharness/backlog-registry.yaml` (installed) declares neither stash
  operation while the template registry declares both. Pre-existing drift on a
  different artifact; recorded in the deliberation as noted-not-actioned.
* Newly surfaced unrelated findings during execution are to be captured under
  P-021 C1, not absorbed.

---

## ADDENDUM (Stage review-fix, 2026-08-20) - H1 was under-scoped; H6 absorbed

**H1 named the wrong boundary.** It framed the hazard as "same commit / same PR",
but the binding constraint is Ship's **per-task** quality gate. A red state
between two tasks in one PR is still a red gate. H1 should have concluded that
the mutually-breaking set must be **one task**, not merely one PR.

**H1 was also incomplete.** It named only Tasks A and C. Task D belonged to the
same mutually-breaking set: it repaired the `test_verify_workspace.py` fixtures
invalidated by C, the policy-contract assertion and manifest checksum invalidated
by A, and could not go green before either. The set is {A, C, D}.

**H6 is absorbed, not dropped.** With the checksum refresh in the same task as
the byte change, the "forgot to refresh, got a parity-shaped failure message"
mode is unreachable. The H6 discipline still applies: refresh the checksum
because the bytes legitimately changed, never to silence unexplained drift, and
capture any *other* stale checksum as a separate deferred entry.

**A factual error is also corrected here** (same correction applied to archived
stash record `8D570CF8`): backlogit v1.10.0 does **not** lack a `stash remove`
CLI subcommand. Its canonical help lists `archive`, and `backlogit stash remove`
remains reachable as a **deprecated alias** resolving to the same archive
handler. Canonical execution stays MCP `backlogit_stash_archive` with CLI
`backlogit stash archive`; the deprecated alias is descriptive context only and
is never prescribed. This corrects a premise, not the conclusion - the migration
is still warranted, because the operation is deprecated.

**No new hardening findings.** Scope is unchanged; only task boundaries moved.
