---
title: "Checkpoint authority: guarded create operation, bounded corpus classification, narrowed tool permission"
description: "Reduced current-state contract for the checkpoint defect. Replaces raw checkpoint creation reached through the backlogit/* tool wildcard with a guarded safe operation that validates resume_hint at author time, classifies the full 134-record historical corpus totally through the 185-S bounded reader including the two observed torn records, and narrows the Ship agent's tool wildcard to an enumerated set in the same activation commit that lands the guarded operation. Historical records are classified and never rewritten."
doc_type: plan
source: docs/plans/2026-09-18-checkpoint-authority-plan.md
date: 2026-09-18
plan_id: checkpoint-authority
plan_path: docs/plans/2026-09-18-checkpoint-authority-plan.md
plan_role: active
revision: 5
verdict: REMEDIATED-PENDING-REVIEW
verdict_note: "Revision 1 is a fresh document replacing the eight-attempt append history of checkpoint-resume-hint-contract at architecture level. Revision 2 bound decision D11 - the two manifest checksum refreshes the ACTIVATE commit requires - into the Rollout section as commit members rather than activation surfaces. Revision 3 stated and enumerated the activation arithmetic explicitly and added an owned fail-closed checksum verification contract in place of the generic verify-workspace command. Revision 4 remediates the independent manifest-contract review: (a) the ACTIVATE commit now includes the .mcp.json tool narrowing as an activation surface, because .mcp.json separately grants the backlogit server \"tools\": [\"*\"], which matches the raw checkpoint tool regardless of what the agent frontmatter enumerates - narrowing only the frontmatter leaves the P0 bypass open - so the arithmetic is SIX activation surfaces, SEVEN commit files, EXACTLY TWO refreshed manifest entries (.mcp.json is untracked), and a rollback unit covering all seven; and (b) the verification contract is now bound to the EXACT INDEX SNAPSHOT the commit records - it asserts the staged set equals exactly the seven intended members, rejects any unstaged difference for them, hashes each installed mirror from :<path>, parses the manifest from :.autoharness/harness-manifest.yaml, rejects missing/extra/duplicate/metadata/checksum divergence, freezes the index between verification and commit (git write-tree recorded, no intervening index mutation, git commit -a and path arguments prohibited), and exits non-zero before the commit is created. Declared-surface and digest inputs are preserved: the manifest is a commit member, not an activation surface. Broad .mcp.json redesign stays out of scope - only the backlogit grant narrows. No task is added and the live manifest is not edited: this is a future implementation contract. Revision 5 closes the terminal review finding that the post-commit tree comparison was described as preventing commit creation, which is impossible: the exact index prechecks (staged-set equality, no unstaged difference, index-read hashing, index-read manifest, total entry adjudication, recorded write-tree identity with re-staging prohibited) all run BEFORE the commit and are what fail closed and leave the commit uncreated; the commit is then created NORMALLY and git rev-parse HEAD^{tree} is compared against the recorded tree immediately afterwards as an ACCEPTANCE adjudication that claims no power to prevent local commit creation and makes no concurrency-proof claim - on mismatch the activation is NOT ACCEPTED and NOT PUBLISHABLE, it blocks the push and every downstream state token, verdict, manifest advance and handoff, and the local commit must be reverted or corrected and the whole contract re-run before proceeding. The arithmetic is unchanged at seven commit members. Revision 5 also pins the literal repo-relative path of the future operation registration as src/autoharness/ops/checkpoint.py at every site enumerating the seven commit members - the narrowest coherent path, since a safe operation is a Python function in src/autoharness/ops/ registered exactly once under a namespace/name pair per the 184-S operation substrate this plan already names as its registry producer; no vague 'src/ registration edit' reference remains. It still carries REMEDIATED-PENDING-REVIEW because it awaits its first independent plan-review attempt; Stage asserts no PASS and has performed no self-review."
awaiting_attempt: 1
review_manifest: docs/reviews/2026-09-18-checkpoint-authority-plan-review.md
source_decision: docs/decisions/2026-09-18-shared-execution-architecture-and-portfolio-reslicing-decision.md
decision_revision: 4
source_stash_ids:
  - 71200CBB
feature_id: 172-F
shipment_id: 180-S
unit_role: reduced-defect-unit
supersedes_plan: docs/plans/2026-09-17-checkpoint-resume-hint-contract-plan.md
depends_on_shipments:
  - 185-S
task_reharvest_gate: 185-S
requires_plan_hardening: true
hardening_rationale: "Narrows an agent tool permission and introduces a guarded write path over a 134-record live corpus containing known-torn records. A defect either re-opens the bypass or breaks recovery for historical records."
tags:
  - defect-unit
  - checkpoint
  - resume-hint
  - tool-permission
  - reduced-scope
---

# Checkpoint authority

## The P0: the guard is bypassable

Attempt-08 `A1` (P0): the plan adds a guarded checkpoint-creation path, but
`.github/agents/_ship.agent.md` frontmatter grants `'backlogit/*'`, which
matches the raw `backlogit_create_checkpoint` tool. `.mcp.json` additionally
grants `"tools": ["*"]` to the backlogit server.

A guard reachable only when the agent chooses not to use the unguarded tool
sitting beside it is a **convention**, not a guard.

Narrowing needs no research: the same frontmatter file already demonstrates
per-tool enumeration for another server (`ms-python.python/...` listed tool by
tool). The pattern exists; it simply was not applied to `backlogit`.

The narrowing and the guarded operation therefore land in the **same activation
commit**. Any ordering that lands one without the other produces a reachable
state that is either a bypassable guard or a removed capability with no
replacement.

## The corpus is real and already broken

134 checkpoint records exist (60 live, 74 archived, plus one operator-authored
record preserved untouched). Two are **torn mid-write**:

```text
checkpoint-20260821-203531.json   4975 B   truncates mid-'context'
checkpoint-20260901-002917.json   5445 B   truncates mid-'progress'
```

Both truncate at exactly their file length — partial writes from a non-atomic
writer, preserved in the record. Attempt-08 `B4` recorded the consequence: a
scanner that raises cannot complete a corpus scan, and one that skips silently
under-reports.

## Contract

1. **Guarded create operation.** A registered safe operation validates
   `resume_hint` at author time — non-empty, and sufficient to resume without
   reading any other record — and writes through the `185-S` atomic writer.
   Raw creation is not reachable from the agent surface.
2. **Total classification.** Every record in the corpus resolves to exactly one
   of `VALID`, `LEGACY_NO_SCHEMA_VERSION`, or `QUARANTINED` with a reason. No
   record is skipped and no record is silently dropped. Classification runs
   through the `185-S` bounded reader, so a torn record yields a typed
   quarantine record rather than an exception.
3. **Historical compatibility.** Records predating the contract are classified,
   reported, and **never rewritten**. The two torn records stay torn; they are
   evidence.
4. **Narrowed permission.** `'backlogit/*'` is replaced by an enumerated tool
   list that excludes raw checkpoint creation, **and** the backlogit server's
   `"tools": ["*"]` grant in `.mcp.json` is narrowed to the same enumerated
   set, both in the activation commit. Narrowing one without the other leaves
   the raw tool reachable through the surface that was not narrowed.

## Composed-state check

| Field | Value |
|---|---|
| Pass state | `CHECKPOINT_RECORDED` — `resume_hint` validated at author time and the record committed atomically |
| Fail state | `CHECKPOINT_REFUSED` — validation failed; nothing written, previous state intact |
| Scan states | `VALID` / `LEGACY_NO_SCHEMA_VERSION` / `QUARANTINED` — total over the corpus |
| Producer | `185-S` PR-1 atomic write and PR-4 bounded reader; `184-S` registry |
| Consumer | Ship and Stage checkpoint steps; the crash-resumption scan |
| Activation commit | one task: `src/autoharness/ops/checkpoint.py` registered **and** both wildcards narrowed (agent frontmatter **and** `.mcp.json`) **and** both agent mirrors updated — six activation surfaces, seven commit members with the manifest refresh |

`CHECKPOINT_RECORDED` is reachable for any record with a valid `resume_hint`;
`QUARANTINED` is reachable today, demonstrated by the two torn records.

## Known constraint: the closed create namespace

`backlogit_create_checkpoint` at `schema_version: 1` treats the top level and
`progress` as a **closed** namespace — legal top-level keys are
`schema_version`, `agent`, `session_id`, `phase`, `status`, `created_at`,
`updated_at`, `context`, `progress`, `resume_hint`, and `progress` admits only
`tasks_completed`, `tasks_remaining`, `files_modified`, `decisions`. `context`
is open. Disposition fields are reserved to the abandon operation.

The guarded operation therefore nests **all** domain data under `context` and
adds no top-level key. A design that carried validated fields at the top level
would be rejected by the very tool it wraps.

## Rollout

**PREPARE (inert).** Validator, classifier and guarded operation built and
tested against the pinned corpus while the wildcard remains in place and no
agent surface calls the operation. Live behaviour is unchanged.

**VERIFY.** Full corpus classified with zero unhandled exceptions and zero
unclassified records; both torn records observed as `QUARANTINED` with reasons;
`CHECKPOINT_REFUSED` observed leaving prior state intact.

**ACTIVATE.** One task, one commit across **six activation surfaces**:
register the guarded operation in `src/autoharness/ops/checkpoint.py`
(untracked), narrow the `'backlogit/*'`
frontmatter permission in the Ship template and its installed mirror, narrow
the backlogit server's `"tools": ["*"]` grant in **`.mcp.json`**, and update
the checkpoint procedure in the Ship and Stage templates and both installed
mirrors — together. `.mcp.json` is an activation surface, not an optional
follow-up: the frontmatter narrowing alone leaves the server-level wildcard
granting the raw tool, so the guard stays bypassable and the P0 is unfixed.

**Manifest parity is part of that same atomic unit (decision `D11`).** Both
installed mirrors — `.github/agents/_ship.agent.md`, whose frontmatter
permission this commit narrows, and `.github/agents/_stage.agent.md` — are
**manifest-tracked installed artifacts** with an `artifacts:` entry in
`.autoharness/harness-manifest.yaml` recording a `sha256` of their
pre-activation content. The two templates are not tracked, the operation
module `src/autoharness/ops/checkpoint.py` is not tracked, and **`.mcp.json`
is not tracked either**,
so the ACTIVATE commit refreshes **exactly
two** manifest entries and contains **exactly seven files while updating six
activation surfaces** — `templates/agents/_ship.agent.md.tmpl`,
`templates/agents/_stage.agent.md.tmpl`, `.github/agents/_ship.agent.md`,
`.github/agents/_stage.agent.md`, `src/autoharness/ops/checkpoint.py`,
`.mcp.json`,
and `.autoharness/harness-manifest.yaml`. In the **same commit** and the
**same rollback unit**, rewrite each of those two checksums to the `sha256` of
the installed file *as written by this commit*, then **verify checksum
parity** under the index-bound fail-closed contract below. A commit that
narrows the permission or
rewrites the procedure in either mirror without its
manifest refresh leaves the manifest asserting a digest of a file the same
commit has already rewritten — an installed-artifact parity hole — and is an
**immediate revert**, not a fixup commit. The refreshes are **commit members,
not activation surfaces**: they register no operation, narrow no permission,
leave the activation-surface count at **six**, and change no surface count
stated anywhere in this plan. This binds a **future implementation commit**;
it authorizes no staging-time edit to the live manifest, and none has
occurred. It rewrites no historical checkpoint and is therefore untouched by
the immutability rule below.

**Fail-closed verification bound to the exact index snapshot, not generic
`verify-workspace`.** Parity is adjudicated by a verification step this unit
owns, run **after all commit members are staged and before the commit is
created**, and bound to the **exact index snapshot the commit will record**.
The generic `verify-workspace` command is **not** that gate: it reports
whole-workspace install state read from the working tree, it does not
adjudicate a named staged digest against a named `artifacts:` entry, and its
exit status is therefore not a checksum assertion. The owned step:

1. **Asserts the staged set is exactly the intended commit members.**
   `git diff --cached --name-only` equals, as a set, the seven members
   enumerated above — the two templates, the two installed mirrors, the
   `src/autoharness/ops/checkpoint.py`, `.mcp.json` and
   `.autoharness/harness-manifest.yaml`. A **missing** member, an **extra**
   staged path, or a **duplicate** entry each fails.
2. **Rejects any unstaged difference for those members.** `git diff
   --name-only --` restricted to the seven members must be empty, and none
   may be untracked. If the working tree differs from the index for any
   commit member, the bytes verified are not the bytes committed, and the
   step fails rather than verifying the wrong content.
3. **Hashes the installed artifacts from the index.** For each of the two
   touched installed mirrors, recompute SHA-256 over the **staged blob read
   as `:<path>`** (`git cat-file -p :.github/agents/_ship.agent.md`,
   `git cat-file -p :.github/agents/_stage.agent.md`) — never a working-tree
   read.
4. **Parses the manifest from the index too**, as
   `:.autoharness/harness-manifest.yaml`, so the entries compared against are
   the entries this commit records rather than any the working tree may hold.
5. **Adjudicates the entry set totally.** For each touched installed mirror
   there is **exactly one** `artifacts:` entry whose literal `path` matches;
   its `primitive` and `template` metadata are exactly as required and
   unchanged by this commit; and its `checksum` equals the digest from (3)
   byte-for-byte. A **missing** entry, an **extra** entry — any `artifacts:`
   entry this commit adds or removes — a **duplicate** `path`, a **metadata**
   divergence, or a **checksum** mismatch each fails. This activation installs
   no new artifact — both templates, `src/autoharness/ops/checkpoint.py` and
   `.mcp.json` stay
   untracked — so **no new entry is required here**; where a future activation
   does install one, the same step asserts the new entry exists with exact
   `path`, `template` and `primitive` values before comparing its checksum.
6. **Records the index identity and forbids re-staging.** Record the index
   identity with `git write-tree` immediately after (5) passes, then create the
   commit with **no intervening index mutation** — no `git add`, `git rm`,
   `git stash`, checkout or restore. `git commit -a` and path arguments to
   `git commit` are **prohibited**, because both re-stage content after
   verification and would commit bytes the gate never adjudicated.
7. **Fails closed before the commit exists.** Steps (1)-(6) all run *before*
   the commit is created, so any failure among them, any unreadable input, or
   any digest mismatch **exits non-zero and the commit is not created**. This
   is the whole of the pre-commit gate.
8. **Adjudicates acceptance after the commit is created.** The commit is then
   created normally; this step does **not** prevent its creation and claims no
   such power. Immediately afterwards, compare `git rev-parse HEAD^{tree}`
   against the tree recorded in (6). On a match the activation is accepted. On
   a **mismatch** the commit records a tree the gate never adjudicated, so the
   activation is **NOT ACCEPTED and NOT PUBLISHABLE**: it **blocks the push**,
   blocks every downstream state token, verdict, manifest advance and handoff
   that would otherwise depend on this activation, and the local commit **must
   be reverted or corrected, and the whole contract re-run, before any further
   step proceeds**.

## Task re-harvest gate

Deferred until `185-S` fixes PR-1 and PR-4 signatures. Existing tasks under
`172-F` remain queued and are re-sliced against the delivered primitives.

## Out of scope

* Repairing, migrating or deleting any historical checkpoint. **Immutable
  history is never rewritten.**
* The operator-authored `checkpoint-20260916-064310.json`, which is preserved
  untouched and is read only as a classification fixture.
* Broad `.mcp.json` permission redesign. Only the backlogit server's
  `"tools": ["*"]` grant — the one this guard depends on — is narrowed; no
  other server's grant is touched.

## Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Narrowing the wildcard removes a tool Ship needs elsewhere | The enumerated list is derived from tools actually invoked in the Ship surfaces, and the VERIFY step records that inventory before activation. |
| R2 | Author-time `resume_hint` validation is too strict and blocks checkpointing | `CHECKPOINT_REFUSED` names the failing rule; a refusal never destroys prior state, so recovery is always possible. |
| R3 | Quarantine hides a record from recovery | Quarantined records are reported in the scan output with their reason, so they are visible rather than absent. |

## Hardening review

Adversarial pass over this unit's failure modes, blast radius and rollback.

### Adversarial questions

| # | Question | Answer |
|---|---|---|
| H1 | Is a guarded operation a control while `backlogit/*` is granted? | No. A guard reachable only when the agent declines to use the unguarded tool beside it is a convention. That is why narrowing and the guarded operation land in the **same** commit — and why **both** wildcards narrow there: the agent frontmatter grant and the `.mcp.json` server grant. Narrowing one leaves the raw tool reachable through the other. |
| H2 | Does narrowing require research? | No. The same frontmatter file already enumerates tools per server for another provider. The pattern exists and was simply not applied to `backlogit`. |
| H3 | Could narrowing remove a tool Ship needs? | The enumerated list is derived from tools actually invoked across the Ship surfaces, and that inventory is recorded in VERIFY before activation rather than discovered after it. |
| H4 | Can a torn record break the corpus scan? | No. The `185-S` bounded reader returns a typed quarantine record. A scanner that raised could not complete the scan, and one that skipped silently would under-report — both were attempt-08 `B4`. |
| H5 | Should the two torn records be repaired? | No. Immutable history is never rewritten. They are classified, reported, and retained as the evidence that motivated the atomic writer. |
| H6 | Why nest everything under `context`? | Because `backlogit_create_checkpoint` treats the top level and `progress` as a closed namespace at `schema_version: 1`. A design carrying validated fields at the top level would be rejected by the tool it wraps. |
| H7 | Is the operator-authored checkpoint at risk? | No. `checkpoint-20260916-064310.json` is read only as a classification fixture and is never written. |
| H8 | Does narrowing only the agent frontmatter close the bypass? | No, and treating it as sufficient was a defect. `.mcp.json` separately grants the backlogit server `"tools": ["*"]`, which matches `backlogit_create_checkpoint` regardless of what the agent frontmatter enumerates. Both grants narrow in the one commit — six activation surfaces, seven commit members — and a revert restores both together. |
| H9 | Could the verification pass on bytes the commit does not record? | No, and this is why the gate is bound to the index rather than the working tree. It asserts the staged set is exactly the seven intended members, rejects any unstaged difference for them, hashes each installed mirror from `:<path>`, parses the manifest from `:.autoharness/harness-manifest.yaml`, then records the index identity — `git write-tree`, no intervening `git add`/`git rm`/`git stash`/checkout, `git commit -a` and path arguments prohibited. Those prechecks run before the commit exists and are what make it fail closed. The post-commit `HEAD^{tree}` comparison is an **acceptance** check, not a prevention one: it cannot stop a local commit being created, so on mismatch the activation is simply not accepted or publishable and must be reverted or corrected. A working-tree-read gate would adjudicate content the commit never records. |

### Blast radius

Two agent tool permissions — the agent frontmatter grant and the `.mcp.json`
server grant — a guarded write path over a 134-record live corpus,
the checkpoint procedure in two agent templates and two installed mirrors, and
two refreshed manifest checksums carried as commit members of the same
activation. A defect either re-opens the bypass or breaks crash recovery.

### Rollback

PREPARE is inert; the wildcard stays and no surface calls the operation. The
ACTIVATE commit reverts as a unit across **all seven commit members** —
restoring both wildcards (agent frontmatter and `.mcp.json`), removing the
registration of `src/autoharness/ops/checkpoint.py`, returning the
checkpoint procedure in both templates
and both mirrors, **and** restoring both manifest checksums together. That is
the only revert that cannot leave the capability removed with no replacement,
one wildcard narrowed while the other is open, or the manifest asserting a
digest of a file the revert has already changed back.

### Verification floor

Full corpus classified with zero unhandled exceptions and zero unclassified
records; both torn records observed `QUARANTINED` with reasons; and
`CHECKPOINT_REFUSED` observed leaving prior state intact.
