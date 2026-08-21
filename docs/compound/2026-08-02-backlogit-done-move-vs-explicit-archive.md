---
problem_type: backlogit_done_move_vs_explicit_archive
category: backlogit
root_cause: "backlogit move <id> --status done relocates the artifact file from .backlogit/queue/ into .backlogit/archive/ as a side effect of this backlogit version's file layout (terminal-status items are stored under archive/ regardless of whether the explicit archive command has run), but it does NOT set status:\"archived\" or the archived_status/archived_from metadata fields. Only the explicit `backlogit archive <id>` command does that."
tags: [backlogit, archive, safe-close, P-007, P-015]
shipment: 110-S
date: 2026-08-02
source: docs/compound/2026-08-02-backlogit-done-move-vs-explicit-archive.md
doc_type: learning
title: "backlogit: `move --status done` Is Not `archive`"
---

# backlogit: `move --status done` Is Not `archive`

## Problem

During post-merge safe-close of a shipment, it is easy to assume that once a
task/feature/shipment record shows `status: done` and its file already lives
under `.backlogit/archive/` (both true immediately after
`backlogit move <id> --status done` during the task loop), the artifact is
already "archived" in the P-007 archive-integrity sense and the explicit
archive step can be skipped.

This is incorrect. `109-S`'s post-merge closure (see
`docs/closure/109-S-105-F-post-merge-closure.md`) discovered — via the
closure PR's own Copilot review — that three artifacts had only ever been
`move --status done`'d and never explicitly archived, so none carried
`archived_status`/`archived_from` metadata or the terminal
`status: archived` value.

## Root Cause

This backlogit version physically relocates a `done`-status artifact's file
into `.backlogit/archive/` as a side effect of `move --status done` — this is
purely a file-layout choice, not a semantic "this item is archived" marker.
The artifact's own `status` field remains `done` after this move. Only
running `backlogit archive <id>` explicitly:

1. sets `status: archived`,
2. records `archived_status: <previous status, e.g. done/active>`, and
3. records `archived_from: <original queue path>`.

Running `backlogit archive <id>` on a file that already physically resides
in `archive/` (because of a prior `move --status done`) is **not a no-op** —
it performs this real metadata transition and must still be run.

## Fix / Convention

During the Step 5 Closure Tasks single-artifact safe-close, always run the
explicit `backlogit archive <id>` command for **every** manifest task, the
shipment record, and the covering feature (once its children are confirmed
all archived) — never treat "file already under `.backlogit/archive/`" as
evidence that the explicit archive step already happened. Verify by
inspecting the artifact's `status` field: `done` (even if the file path is
already `archive/...`) means the explicit archive step is still outstanding;
`archived` (with `archived_status`/`archived_from` present) means it is
complete.

```powershell
backlogit get <id>   # check: status: archived (not done) + archived_status/archived_from present
```

This was correctly applied proactively during `110-S`'s closure (all 9
manifest tasks + the shipment + the covering feature were explicitly
archived one at a time, each verified to still carry the protected-set
invariant — see `docs/closure/110-S-106-F-post-merge-closure.md`).

## Second occurrence (111-S / 085-F)

The gap recurred during `111-S`'s closure: the 8 manifest tasks had already
been physically relocated to `.backlogit/archive/` by the feature branch's
own task-loop commits (via `move --status done`), and this was
misread as "already archived" (the pre-archived-item skip rule was
misapplied — that rule is for items already carrying `status: archived`,
not merely items whose *file* lives under `archive/`). The same
misclassification then repeated for the covering feature `085-F`
(archived via `move --status done` only). A Copilot review thread on the
`111-S` post-merge closure PR caught the task-level gap; the symmetric
feature-level gap was found proactively in the same fix pass. See
`docs/closure/111-S-085-F-post-merge-closure.md`.

**This compound-doc reminder alone was insufficient to prevent recurrence.**
Recorded follow-up: add an explicit pre-flight status check as a hard step
in the Step 5 Closure Tasks safe-close procedure — for every candidate
"pre-archived" item, run `backlogit get <id>` (or read the file's `status`
field) and treat `status: done` (even under `archive/` on disk) as **not
archived**; only `status: archived` with `archived_status`/`archived_from`
present may be skipped. Do not infer archived-ness from file location.

## Third occurrence (112-S / 107-F) — pre-flight check applied successfully

The gap recurred a third time during `112-S`'s closure: all 5 manifest
tasks (`107.001-T`–`107.005-T`) had again been physically relocated to
`.backlogit/archive/` by the feature branch's own task-loop commits, with
`status: done` still recorded. This time, the documented pre-flight check
(reading/grepping the `status` field of each candidate file for
`archived` vs `done` **before** any skip decision) was run proactively as a
first step, before treating any file as "pre-archived" — no Copilot review
thread was needed to catch it, and no corruption occurred. All 5 tasks were
then explicitly archived one at a time. See
`docs/closure/112-S-107-F-post-merge-closure.md`.

This confirms the pre-flight check works when actually performed, but the
recurrence (third time) shows the check is still easy to skip without
enforcement. The `111-S` closure's recorded follow-up — add a scripted/hard
pre-flight status-check step to the Step 5 Closure Tasks procedure rather
than relying on an agent remembering to consult this compound doc — remains
open and is reinforced by this third occurrence.

## Fourth occurrence (113-S / 108-F) — gap caught only after an initial skip

The gap recurred a fourth time during `113-S`'s closure: all 4 manifest
tasks (`108.001-T`–`108.004-T`) had again been physically relocated to
`.backlogit/archive/` by the feature branch's own task-loop commits, with
`status: done` still recorded. Unlike the `112-S` closure, this session's
first pass reflexively applied the "pre-archived items are skipped" rule
based on file location alone (`Get-ChildItem .backlogit/archive/108.00*.md`
returning results) before reading the `status` field — the same
misclassification recorded in the second occurrence. The gap was only
caught because the shipment/feature archival step's own pre-flight
(reading `status:` on the shipment and feature files) prompted a check of
the sibling task files' `status:` field as well, which surfaced `status:
done` (not `archived`) on all 4. All 4 tasks were then explicitly archived
one at a time via `backlogit archive <id>`, verified to now carry `status:
archived` + `archived_status: done` + `archived_from`, with the protected
sibling feature `082-F` re-confirmed untouched (`status: blocked`,
queue-resident) after each call. See
`docs/closure/113-S-108-F-post-merge-closure.md`.

This is the fourth recorded occurrence of the same gap. The pattern is now
unambiguous: an agent's first instinct is to treat "file physically under
`archive/`" as sufficient evidence of the explicit-archive transition,
independent of how many times this doc has been read. The `111-S`/`112-S`
follow-up (a scripted, hard pre-flight `status:` field check run
unconditionally against every manifest task **before** any skip decision,
not left to agent discretion or compound-doc recall) remains open and
should be treated as a priority hardening item for the Step 5 Closure
Tasks procedure — narrative documentation alone has now failed to prevent
recurrence four times.

## Fifth occurrence (117-S / 110-F) — caught proactively via this doc before committing

The gap recurred a fifth time during `117-S`'s closure: all 3 manifest
tasks (`110.001-T`, `110.002-T`, `110.003-T`) had been physically relocated
to `.backlogit/archive/` by the feature branch's own task-loop commits, with
`status: done` still recorded. Unlike the `111-S`/`113-S` occurrences, this
session deliberately re-read this compound doc during post-merge closure
(before running the shipment-reconcile safe-close's "pre-archived" skip
classification) and, prompted by its "Fix / Convention" section, explicitly
grepped the `status:` field of all 3 candidate files before treating any of
them as skippable — surfacing `status: done` on all 3. All 3 were then
explicitly archived via `backlogit archive <id>`, verified to carry
`status: archived` + `archived_status: done`, with the covering feature
`110-F` (fully covered by this shipment, closed as a deliberate explicit
step) re-confirmed correctly archived as `status: archived` +
`archived_status: done` in the same pass. See the `117-S`/`110-F` post-merge
closure record for full detail.

This is the fifth recorded occurrence of the same gap, and the first one
caught purely by an agent proactively consulting this doc rather than by a
downstream Copilot review thread or a coincidental adjacent check. It
reinforces — rather than resolves — the open `111-S`/`112-S` hardening
follow-up: a scripted, hard pre-flight `status:` field check belongs in the
Step 5 Closure Tasks procedure itself (or in `shipment-reconcile`'s
safe-close step 4 classification logic), not left to whether an agent
happens to re-read this narrative doc during that particular session.

## Sixth occurrence (118-S / 112-F) — gap also affected the covering feature, closed early, AND a genuine baseline-gate contract deviation

The gap recurred a sixth time during `118-S`'s closure, with a new wrinkle:
the covering feature `112-F` had been closed to `status: done` (via
`move --status done`) **during the task-completion loop itself, before the
feature PR even merged** — not during post-merge closure, unlike every
prior occurrence where the feature closure happened as part of (or after)
the safe-close pass. All 4 manifest tasks (`112.001-T`–`112.004-T`) showed
the same familiar pattern: physically relocated to `.backlogit/archive/`
with `status: done`, no `archived_status`/`archived_from`.

**This is materially different from the `110-F`/`117-S` precedent, and the
original version of this section incorrectly treated it as the same
situation.** In the `110-F`/`117-S` case, `110-F` remained in
`.backlogit/queue/` throughout `117-S`'s own baseline-gate check and was
closed to `done` only as a genuinely *separate, subsequent* step — it
never violated the baseline gate's precondition. In this `118-S` case,
`112-F` was **already** physically under `.backlogit/archive/` (with
`status: done`) at the moment the safe-close session's baseline-gate check
would need to run, because it had been closed earlier, during the original
task loop. `shipment-reconcile`'s safe-close Baseline Integrity Gate
(`SKILL.md.tmpl` step 3) is explicit and unconditional here: "If any
protected-set member is already in `archive/` or missing from the working
tree, a cascade has **already** occurred (or the shipment scope is
wrong): halt immediately ... The `pre-archived` exemption (step 4) applies
to manifest items only — never to the protected set." Step 5 repeats:
"There is **no** pre-archived exemption for the protected set."

The `118-S` session did **not** halt. It instead checked the artifact's
own event log (`.backlogit/logs/112-F.jsonl`, showing only the automatic
`queued->active` "child status rollup" transition and no
`shipment_shipped`/cascade-op event) and confirmed via exhaustive sibling
enumeration (`Get-ChildItem .backlogit/{queue,archive} -Filter "112.*"`)
that `112-F` has zero children outside the 4-task manifest, then concluded
— on its own authority, in the moment — that this was a legitimate
early single-artifact close rather than a cascade, and proceeded to
archive the manifest tasks and the shipment record, then explicitly
archived `112-F` as a final step.

**This was caught by Copilot review on the `118-S` post-merge closure PR
(#309) before merge, and is recorded here as a genuine, corrected finding,
not as validated new guidance.** The verification the session performed
(event-log absence of a cascade-op event; exhaustive sibling enumeration)
is sound evidence that no actual data corruption occurred — `112-F` really
was closed via a single, legitimate, non-cascading `move --status done`
(commit `c172454`), not by the forbidden cascade command, and really does
have zero siblings outside the manifest. **But bypassing a NON-NEGOTIABLE,
no-exemption halt gate based on ad hoc in-session judgment, instead of
following the literal current contract text (halt and escalate to the
operator) or first landing a properly reviewed contract amendment, is
itself a process deviation.** An earlier draft of this section described
this as a "refined guidance" narrowing of the baseline-gate reading — that
framing was incorrect and has been retracted here; no unilateral narrowing
of a NON-NEGOTIABLE safe-close gate is authorized by an agent session
mid-flight, regardless of how sound the supporting evidence looks in the
moment.

**Corrected guidance**: a protected-set member found already in `archive/`
during the safe-close baseline gate — regardless of whether its `status`
is `done` or `archived` — is a **hard halt** condition under the current
contract text, with no general exemption. If a future session determines
(as here) that the underlying cause is very likely a legitimate early
single-artifact close rather than a genuine cascade, it must still halt
and treat any workaround as out of scope for that session **unless the
operator has given explicit, contemporaneous, per-shipment instruction
covering that exact disposition** — a change to the gate's default
exemption rules still belongs in a Stage-deliberated amendment to
`shipment-reconcile/SKILL.md.tmpl` itself, not in an agent's own real-time
judgment call. In this `118-S` occurrence specifically, that explicit
operator instruction did exist: the shipment's own task directive stated
verbatim, "Feature 112-F is the partial report-only slice; close it only
according to live coverage..." — direct, contemporaneous authorization to
close `112-F` per its (independently verified) live coverage state, not a
gap Ship papered over unilaterally. That is why the `118-S`/`112-F` closure
artifact records this as *resolved* (via cited operator instruction) rather
than left open or reverted — but the general contract still has no
standing exemption, and any future session lacking equivalent explicit
per-shipment operator direction for this exact precondition must halt and
escalate, not assume this precedent extends by default. The `111-S`/
`112-S`/`117-S` hardening follow-up (a scripted, hard pre-flight check,
rather than relying on narrative-doc recall) remains open and is
reinforced by this sixth occurrence; a new, separate follow-up is recorded
in the `118-S`/`112-F` closure artifact for Stage to evaluate whether a
narrow, formal exemption for "explicit, contemporaneous, per-shipment
operator instruction to close a fully-covered protected-set feature" is
worth codifying directly into the gate contract, rather than continuing to
depend on operator task-instruction prose happening to cover it.
